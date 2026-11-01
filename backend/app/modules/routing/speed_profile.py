"""Learning speeds from completed trips, and serving them to `approx` (B37, OQ-22).

Two halves of one idea, kept apart because they run in different places:

* **The learner** (`SpeedProfileService`) runs as a nightly job. It reads the legs drivers
  actually drove - the time from one stop being finished to the next being reached - and
  folds them into per-hour-of-week totals. It remembers how far it has read, so running it
  twice reads nothing twice.
* **The view** (`LearnedSpeeds`) lives inside the routing provider. It holds the profile in
  memory, refreshed on a timer from the injected `Clock`, and answers one question: what is
  the speed in this slot, if we have learned one we trust?

A slot we have not learned (or have too few samples for) answers "don't know", and
`approx` falls back to its constant. That is the whole degradation story: a fresh
deployment behaves exactly as Phase 1 did and improves as trips accumulate.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.clock import Clock
from app.core.geo import coords
from app.core.logging import get_logger
from app.domain.geo import LatLng, haversine_km
from app.domain.speed_profile import (
    AREA_WAY_ID,
    Leg,
    SlotStat,
    accumulate,
    speeds,
)
from app.domain.state_machines import TripStatus
from app.modules.dispatch.models import Trip, TripStop
from app.modules.routing.speed_models import RoadSpeedProfile, SpeedProfileState

logger = get_logger(__name__)

#: The platform slots are the operator wall clock; the pilot is in India (`approx` uses
#: the same constant for its time-of-day table).
PROFILE_TIMEZONE = "Asia/Kolkata"
EPOCH = datetime(2000, 1, 1, tzinfo=UTC)


class LearnedSpeeds:
    """The profile as `approx` sees it: slot -> kph, refreshed on a timer."""

    def __init__(
        self,
        clock: Clock,
        loader: Callable[[], Awaitable[dict[int, float]]] | None = None,
        refresh: timedelta = timedelta(hours=1),
    ) -> None:
        self._clock = clock
        self._loader = loader
        self._refresh = refresh
        self._speeds: dict[int, float] = {}
        self._loaded_at: datetime | None = None

    @classmethod
    def fixed(cls, clock: Clock, by_slot: dict[int, float]) -> LearnedSpeeds:
        """A profile that never reloads - for tests and for a pinned profile."""
        view = cls(clock)
        view._speeds = dict(by_slot)
        view._loaded_at = clock.now()
        return view

    async def ensure_fresh(self) -> None:
        """Reload if it is time. A failed reload keeps what we had.

        The load is attempted at most once per refresh interval, success or not: a database
        that is down must not be asked again on every route request.
        """
        if self._loader is None:
            return
        now = self._clock.now()
        if self._loaded_at is not None and now - self._loaded_at < self._refresh:
            return
        self._loaded_at = now
        try:
            self._speeds = await self._loader()
        except Exception:  # noqa: BLE001 - routing must never fail because the profile did
            logger.exception("speed_profile_load_failed")

    def speed_kph(self, slot: int) -> float | None:
        return self._speeds.get(slot)

    @property
    def slots_known(self) -> int:
        return len(self._speeds)


def database_loader(
    sessions: async_sessionmaker[AsyncSession], min_samples: int
) -> Callable[[], Awaitable[dict[int, float]]]:
    """A loader that reads the aggregate profile, keeping only slots with enough samples."""

    async def load() -> dict[int, float]:
        async with sessions() as session:
            rows = await session.execute(
                select(RoadSpeedProfile).where(RoadSpeedProfile.osm_way_id == AREA_WAY_ID)
            )
            stats = {
                row.slot: SlotStat(row.distance_m, row.seconds, row.samples)
                for row in rows.scalars()
            }
        return speeds(stats, min_samples)

    return load


@dataclass(frozen=True, slots=True)
class LearnResult:
    trips: int = 0
    legs: int = 0
    usable_legs: int = 0
    slots_updated: int = 0
    processed_until: datetime | None = None


class SpeedProfileService:
    def __init__(self, session: AsyncSession, clock: Clock, road_factor: float = 1.4) -> None:
        self.session = session
        self.clock = clock
        #: Must equal the `approx` provider, or the learned speed lives in a different
        #: frame from the formula that divides by it.
        self.road_factor = road_factor

    async def learn(self, limit_trips: int = 5000) -> LearnResult:
        """Fold every trip completed since the last run into the profile."""
        state = await self.session.get(SpeedProfileState, 1)
        watermark = state.processed_until if state is not None else EPOCH

        trips = list(
            (
                await self.session.execute(
                    select(Trip)
                    .where(Trip.status == str(TripStatus.completed))
                    .where(Trip.completed_at > watermark)
                    .order_by(Trip.completed_at)
                    .limit(limit_trips)
                )
            ).scalars()
        )
        if not trips:
            return LearnResult(processed_until=watermark if state else None)

        stops_by_trip = await self._stops([trip.id for trip in trips])
        legs: list[Leg] = []
        for trip in trips:
            legs.extend(self._legs_of(stops_by_trip.get(trip.id, [])))

        existing = await self._existing()
        updated = accumulate(existing, legs, PROFILE_TIMEZONE)
        changed = {slot: stat for slot, stat in updated.items() if existing.get(slot) != stat}
        await self._write(changed)

        until = max(trip.completed_at for trip in trips if trip.completed_at is not None)
        await self._remember(until)
        usable = sum(
            updated[slot].samples - existing.get(slot, SlotStat()).samples for slot in changed
        )
        logger.info(
            "speed_profile_learned",
            trips=len(trips),
            legs=len(legs),
            usable=usable,
            slots=len(changed),
        )
        return LearnResult(len(trips), len(legs), usable, len(changed), until)

    def _legs_of(self, stops: list[TripStop]) -> list[Leg]:
        """From each stop being finished to the next being reached: driving, not waiting."""
        ordered = sorted(stops, key=lambda stop: stop.sequence)
        legs: list[Leg] = []
        for before, after in zip(ordered, ordered[1:], strict=False):
            if before.done_at is None or after.arrived_at is None:
                continue
            a, b = coords(before.location), coords(after.location)
            metres = haversine_km(LatLng(*a), LatLng(*b)) * 1000.0 * self.road_factor
            legs.append(Leg(before.done_at, after.arrived_at, metres))
        return legs

    async def _stops(self, trip_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[TripStop]]:
        grouped: dict[uuid.UUID, list[TripStop]] = {}
        rows = await self.session.execute(select(TripStop).where(TripStop.trip_id.in_(trip_ids)))
        for stop in rows.scalars():
            grouped.setdefault(stop.trip_id, []).append(stop)
        return grouped

    async def _existing(self) -> dict[int, SlotStat]:
        rows = await self.session.execute(
            select(RoadSpeedProfile).where(RoadSpeedProfile.osm_way_id == AREA_WAY_ID)
        )
        return {
            row.slot: SlotStat(row.distance_m, row.seconds, row.samples) for row in rows.scalars()
        }

    async def _write(self, changed: dict[int, SlotStat]) -> None:
        for slot, stat in changed.items():
            speed = stat.speed_kph()
            if speed is None:
                continue
            statement = insert(RoadSpeedProfile).values(
                osm_way_id=AREA_WAY_ID,
                slot=slot,
                speed_kph=speed,
                samples=stat.samples,
                distance_m=stat.metres,
                seconds=stat.seconds,
            )
            await self.session.execute(
                statement.on_conflict_do_update(
                    index_elements=["osm_way_id", "slot"],
                    set_={
                        "speed_kph": statement.excluded.speed_kph,
                        "samples": statement.excluded.samples,
                        "distance_m": statement.excluded.distance_m,
                        "seconds": statement.excluded.seconds,
                    },
                )
            )

    async def _remember(self, until: datetime) -> None:
        state = await self.session.get(SpeedProfileState, 1)
        if state is None:
            self.session.add(SpeedProfileState(id=1, processed_until=until))
        else:
            state.processed_until = until
        await self.session.flush()
