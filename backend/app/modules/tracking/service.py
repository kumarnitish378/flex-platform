"""GPS ingestion (B12).

The hot path of the whole product: at pilot scale this runs ~40 times a second, forever,
and every supervisor's map depends on it. Three jobs, in order of how much they matter:

1. **Reject nonsense** before it reaches anyone (`mqtt-topics.md`, Ingestor validation).
2. **Keep the latest position fresh in Redis**, which is what the live map reads.
3. **Persist everything in batches**, because one INSERT per ping would spend the
   database on round trips.

Deliberately transport-agnostic: MQTT hands it payloads, and so does the `/driver/location`
HTTPS fallback. The rules must not differ between the two, or a driver on a bad connection
would get different validation from one on a good one.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from geoalchemy2.shape import from_shape
from shapely.geometry import Point as ShapelyPoint
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.logging import get_logger
from app.core.redis import RedisLike
from app.domain.gps import DropReason, Ping, Rejected, check_ping, is_newer, parse_payload
from app.modules.tracking.models import LocationPing

logger = get_logger(__name__)

#: Redis key for a vehicle's latest position, and how long it survives without updates.
POSITION_KEY = "veh:{vehicle_id}:pos"
POSITION_TTL_SECONDS = 600
#: The channel the WebSocket hub subscribes to. Named by `websocket-protocol.md`, not
#: invented here: a private name would publish into a feed nobody is listening on.
EVENT_CHANNEL = "operator.{operator_id}.vehicles"
EVENT_NAME = "vehicle.location"

#: Flush at least this often, or once this many pings are queued — whichever first.
FLUSH_INTERVAL_SECONDS = 5
FLUSH_MAX_ROWS = 1000


@dataclass
class IngestResult:
    accepted: int = 0
    dropped: int = 0
    reasons: dict[str, int] = field(default_factory=dict)
    latest_moved: bool = False

    def drop(self, rejection: Rejected) -> None:
        self.dropped += 1
        self.reasons[str(rejection.reason)] = self.reasons.get(str(rejection.reason), 0) + 1


class GpsIngestor:
    """Validates, caches and buffers pings. Flushing is explicit, so tests control it."""

    def __init__(
        self,
        session: AsyncSession,
        clock: Clock,
        redis: RedisLike | None = None,
    ) -> None:
        self.session = session
        self.clock = clock
        self.redis = redis
        self._buffer: list[dict[str, Any]] = []
        self._last_flush = clock.now()
        #: Last accepted ping per vehicle, for the jump check and ordering.
        self._latest: dict[uuid.UUID, Ping] = {}

    # --- ingestion ----------------------------------------------------------

    async def ingest(
        self, vehicle_id: uuid.UUID, operator_id: uuid.UUID, payload: Any
    ) -> IngestResult:
        """Handle one MQTT message or one HTTPS batch."""
        result = IngestResult()
        parsed = parse_payload(payload)
        for rejection in parsed.rejected:
            result.drop(rejection)

        now = self.clock.now()
        # Oldest first, so a reconnect batch is judged in the order it happened rather
        # than tripping the jump check against its own newest ping.
        for ping in sorted(parsed.pings, key=lambda p: p.recorded_at):
            previous = self._latest.get(vehicle_id)
            dropped = check_ping(ping, now, previous)
            if dropped is not None:
                result.drop(dropped)
                continue

            self._buffer.append(self._row(vehicle_id, operator_id, ping, now))
            result.accepted += 1

            # Out-of-order pings are stored but must not move the marker backwards.
            if is_newer(ping, previous):
                self._latest[vehicle_id] = ping
                await self._publish_latest(vehicle_id, operator_id, ping)
                result.latest_moved = True

        if result.dropped:
            logger.info(
                "gps_pings_dropped",
                vehicle_id=str(vehicle_id),
                dropped=result.dropped,
                reasons=result.reasons,
            )
        await self.flush_if_due()
        return result

    def _row(
        self, vehicle_id: uuid.UUID, operator_id: uuid.UUID, ping: Ping, received_at: datetime
    ) -> dict[str, Any]:
        return {
            "vehicle_id": vehicle_id,
            "operator_id": operator_id,
            "recorded_at": ping.recorded_at,
            "received_at": received_at,
            "location": from_shape(ShapelyPoint(ping.lng, ping.lat), srid=4326),
            "speed_mps": ping.speed_mps,
            "heading_deg": ping.heading_deg,
            "accuracy_m": ping.accuracy_m,
            "battery_pct": ping.battery_pct,
            "source": ping.source,
        }

    # --- Redis ---------------------------------------------------------------

    async def _publish_latest(
        self, vehicle_id: uuid.UUID, operator_id: uuid.UUID, ping: Ping
    ) -> None:
        """Write the live position and tell the WebSocket hub.

        Redis being down must not stop ingestion: the map goes stale, but the pings still
        reach the database, so nothing is lost permanently.
        """
        if self.redis is None:
            return

        payload = {
            "vehicle_id": str(vehicle_id),
            "lat": ping.lat,
            "lng": ping.lng,
            "ts": ping.recorded_at.isoformat(),
            "spd": ping.speed_mps,
            "hdg": ping.heading_deg,
        }
        try:
            await self.redis.set(
                POSITION_KEY.format(vehicle_id=vehicle_id),
                json.dumps(payload),
                ex=POSITION_TTL_SECONDS,
            )
            publish = getattr(self.redis, "publish", None)
            if publish is not None:
                channel = EVENT_CHANNEL.format(operator_id=operator_id)
                await publish(
                    channel,
                    json.dumps(
                        {"type": "event", "event": EVENT_NAME, "channel": channel, "data": payload}
                    ),
                )
        except Exception as exc:  # noqa: BLE001 - a stale map beats a dropped ping
            logger.warning("gps_latest_write_failed", error=type(exc).__name__)

    async def latest_position(self, vehicle_id: uuid.UUID) -> dict[str, Any] | None:
        if self.redis is None:
            return None
        try:
            raw = await self.redis.get(POSITION_KEY.format(vehicle_id=vehicle_id))
        except Exception as exc:  # noqa: BLE001
            logger.warning("gps_latest_read_failed", error=type(exc).__name__)
            return None
        if raw is None:
            return None
        try:
            loaded: dict[str, Any] = json.loads(raw)
            return loaded
        except (TypeError, ValueError):
            return None

    # --- persistence ----------------------------------------------------------

    @property
    def pending(self) -> int:
        return len(self._buffer)

    async def flush_if_due(self) -> int:
        """Flush on the interval or when the buffer is full."""
        due = (self.clock.now() - self._last_flush) >= timedelta(seconds=FLUSH_INTERVAL_SECONDS)
        if self._buffer and (due or len(self._buffer) >= FLUSH_MAX_ROWS):
            return await self.flush()
        return 0

    async def flush(self) -> int:
        """Write the buffer in one statement."""
        if not self._buffer:
            return 0
        rows, self._buffer = self._buffer, []
        # One multi-row INSERT rather than len(rows) round trips.
        await self.session.execute(insert(LocationPing), rows)
        await self.session.flush()
        self._last_flush = self.clock.now()
        logger.info("gps_batch_persisted", rows=len(rows))
        return len(rows)

    # --- stale detection --------------------------------------------------------

    async def stale_vehicles(
        self, operator_id: uuid.UUID, stale_after_seconds: int
    ) -> list[uuid.UUID]:
        """On-duty vehicles whose last ping is older than `stale_gps_seconds`.

        Read from the database rather than Redis: a vehicle that has gone quiet has no
        Redis key at all once the TTL lapses, and "no key" is exactly the case we are
        looking for, so Redis cannot answer the question.
        """
        from app.modules.fleet.duty_models import DutySession

        cutoff = self.clock.now() - timedelta(seconds=stale_after_seconds)
        on_duty = (
            (
                await self.session.execute(
                    select(DutySession.vehicle_id)
                    .where(DutySession.operator_id == operator_id)
                    .where(DutySession.ended_at.is_(None))
                )
            )
            .scalars()
            .all()
        )

        stale: list[uuid.UUID] = []
        for vehicle_id in on_duty:
            last = (
                (
                    await self.session.execute(
                        select(LocationPing.recorded_at)
                        .where(LocationPing.vehicle_id == vehicle_id)
                        .order_by(LocationPing.recorded_at.desc())
                        .limit(1)
                    )
                )
                .scalars()
                .first()
            )
            if last is None or last < cutoff:
                stale.append(vehicle_id)
        return stale


def drop_reasons() -> list[str]:
    """Every reason a ping can be dropped, for metrics registration."""
    return [str(reason) for reason in DropReason]
