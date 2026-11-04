"""The queries behind the business gauges.

Run once per Prometheus scrape, from the `/metrics` route. Everything here is a single
aggregate query over an indexed column, so a 15-second scrape costs the database almost
nothing; the one exception is the stale-vehicle count, which reuses the same
whole-fleet query the stale sweep uses (`GpsIngestor.stale_vehicles`) rather than asking
per vehicle - that per-vehicle version was the slowest thing in a simulated clock jump
(OQ-26) and must not come back through a metrics endpoint.

Gauges are **cleared before each pass**. A gauge with an `operator_id` label keeps its
last value forever otherwise, so an operator that is deactivated, or a severity that no
longer has open alerts, would go on reporting its final number as though it were current.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import metrics
from app.core.clock import Clock
from app.core.logging import get_logger
from app.domain.enums import AlertStatus
from app.domain.state_machines import RequestStatus, TripStatus
from app.modules.alerts.models import Alert
from app.modules.config.service import ConfigService
from app.modules.dispatch.models import Trip
from app.modules.fleet.duty_models import DutySession
from app.modules.requests.models import RideRequest
from app.modules.tracking.service import GpsIngestor

logger = get_logger(__name__)

#: A request in one of these has been asked for and nobody is driving towards it yet.
#: `suggested` is included deliberately: in Phase 2 a suggestion still needs a human to
#: approve it, so a rider sitting in `suggested` is still a rider waiting.
PENDING_STATUSES = (
    str(RequestStatus.requested),
    str(RequestStatus.queued),
    str(RequestStatus.suggested),
)

#: A trip someone is currently on, or about to be.
ACTIVE_TRIP_STATUSES = (str(TripStatus.dispatched), str(TripStatus.in_progress))


@dataclass
class BusinessGaugeCollector:
    """Fills the gauges in `app.core.metrics` from the current database state."""

    session: AsyncSession
    clock: Clock

    async def collect(self) -> None:
        """One pass. A failure is logged and swallowed - a scrape must not 500."""
        try:
            await self._pending_requests()
            await self._duty_and_staleness()
            await self._open_alerts()
            await self._trips_in_progress()
        except Exception as exc:  # noqa: BLE001 - metrics must never break the service
            logger.warning("business_gauges_failed", error=type(exc).__name__, detail=str(exc))

    # --- individual gauges ---------------------------------------------------

    async def _pending_requests(self) -> None:
        metrics.pending_requests.clear()
        metrics.longest_pending_wait.clear()

        rows = (
            await self.session.execute(
                select(
                    RideRequest.operator_id,
                    func.count().label("pending"),
                    func.min(RideRequest.queued_at).label("oldest"),
                )
                .where(RideRequest.status.in_(PENDING_STATUSES))
                .group_by(RideRequest.operator_id)
            )
        ).all()

        now = self.clock.now()
        for operator_id, pending, oldest in rows:
            label = str(operator_id)
            metrics.pending_requests.labels(operator_id=label).set(pending)
            # `queued_at` is the Clock-set wait origin, not the database `now()` default
            # that B09 found every wait being measured from.
            waited = (now - oldest).total_seconds() if oldest is not None else 0.0
            metrics.longest_pending_wait.labels(operator_id=label).set(max(waited, 0.0))

    async def _duty_and_staleness(self) -> None:
        metrics.vehicles_on_duty.clear()
        metrics.stale_vehicles.clear()

        rows = (
            await self.session.execute(
                select(DutySession.operator_id, func.count())
                .where(DutySession.ended_at.is_(None))
                .group_by(DutySession.operator_id)
            )
        ).all()

        config = ConfigService(self.session, self.clock)
        ingestor = GpsIngestor(self.session, self.clock)
        for operator_id, on_duty in rows:
            label = str(operator_id)
            metrics.vehicles_on_duty.labels(operator_id=label).set(on_duty)
            stale_after = int(await config.get(operator_id, "stale_gps_seconds"))
            stale = await ingestor.stale_vehicles(uuid.UUID(label), stale_after)
            metrics.stale_vehicles.labels(operator_id=label).set(len(stale))

    async def _open_alerts(self) -> None:
        metrics.open_alerts.clear()

        rows = (
            await self.session.execute(
                select(Alert.operator_id, Alert.severity, func.count())
                .where(Alert.status != str(AlertStatus.resolved))
                .group_by(Alert.operator_id, Alert.severity)
            )
        ).all()

        for operator_id, severity, count in rows:
            metrics.open_alerts.labels(operator_id=str(operator_id), severity=severity).set(count)

    async def _trips_in_progress(self) -> None:
        metrics.trips_in_progress.clear()

        rows = (
            await self.session.execute(
                select(Trip.operator_id, func.count())
                .where(Trip.status.in_(ACTIVE_TRIP_STATUSES))
                .group_by(Trip.operator_id)
            )
        ).all()

        for operator_id, count in rows:
            metrics.trips_in_progress.labels(operator_id=str(operator_id)).set(count)
