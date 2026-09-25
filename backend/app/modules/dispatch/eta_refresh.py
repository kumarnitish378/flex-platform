"""Keeping stop ETAs honest (B15, `architecture.md` section 3.2 step 4).

Every 30 seconds, recompute `latest_eta` for the stops of trips that are actually moving
and tell whoever is watching. This is the number a rider stares at, so two things matter:

* **Bounded routing.** One ETA call per pending stop of an *in-progress* trip, and nothing
  at all when no trip is moving. A sweep that walked every planned trip would burn the
  shared OSRM budget on cabs that have not left yet (ADR-0010).
* **Clock-driven, not timer-driven.** The sweep does work that is *due* rather than
  sleeping, so `/simctl/clock` advancing simulated time really does refresh ETAs.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.events import Event, EventPublisher, NullEventPublisher, trip_channel
from app.core.geo import coords
from app.core.logging import get_logger
from app.domain.geo import LatLng
from app.domain.state_machines import StopStatus, TripStatus
from app.modules.dispatch.models import Trip, TripStop
from app.modules.dispatch.service import DispatchService

logger = get_logger(__name__)

#: `architecture.md` section 3.2: "ETA worker recomputes active stop ETAs every 30 s".
REFRESH_INTERVAL = timedelta(seconds=30)

#: Stops still ahead of the driver.
PENDING_STATUSES = (StopStatus.pending, StopStatus.en_route)


@dataclass(frozen=True, slots=True)
class RefreshResult:
    trips: int = 0
    stops: int = 0
    approximate: int = 0


class EtaRefresher:
    def __init__(
        self,
        session: AsyncSession,
        clock: Clock,
        eta_service: Any,
        events: EventPublisher | None = None,
    ) -> None:
        self.session = session
        self.clock = clock
        self.eta = eta_service
        self.events = events or NullEventPublisher()

    async def refresh_due(self, operator_id: uuid.UUID | None = None) -> RefreshResult:
        """Refresh every stop whose ETA is older than the interval.

        Called by the Celery beat loop in production and by `/simctl/clock` in sim, like
        the request-expiry sweep, so simulated time drives it too.
        """
        now = self.clock.now()
        query = (
            select(Trip)
            .where(Trip.status == str(TripStatus.in_progress))
            .order_by(Trip.planned_start)
        )
        if operator_id is not None:
            query = query.where(Trip.operator_id == operator_id)
        trips = list((await self.session.execute(query)).scalars().all())

        result = RefreshResult()
        for trip in trips:
            refreshed = await self._refresh_trip(trip)
            if refreshed.stops:
                result = RefreshResult(
                    trips=result.trips + 1,
                    stops=result.stops + refreshed.stops,
                    approximate=result.approximate + refreshed.approximate,
                )

        if result.stops:
            logger.info(
                "stop_eta_refreshed",
                trips=result.trips,
                stops=result.stops,
                approximate=result.approximate,
                at=now.isoformat(),
            )
        return result

    async def _refresh_trip(self, trip: Trip) -> RefreshResult:
        stops = list(
            (
                await self.session.execute(
                    select(TripStop)
                    .where(TripStop.trip_id == trip.id)
                    .where(TripStop.status.in_([str(status) for status in PENDING_STATUSES]))
                    .order_by(TripStop.sequence)
                )
            )
            .scalars()
            .all()
        )
        if not stops:
            return RefreshResult()

        now = self.clock.now()
        if not any(_is_due(stop, now) for stop in stops):
            return RefreshResult()

        position = (
            await DispatchService(self.session, self.clock, self.eta).latest_positions(
                trip.operator_id
            )
        ).get(trip.vehicle_id)
        if position is None:
            # No idea where the cab is, so any ETA would be invented. Leave the last one
            # standing and let the stale-GPS alert do its job.
            return RefreshResult()

        origin = LatLng(position.lat, position.lng)
        # Walk the remaining stops in order, each leg starting where the last ended, so a
        # rider three stops down sees the queue ahead of them rather than a direct time.
        elapsed = 0.0
        approximate_count = 0
        for stop in stops:
            latitude, longitude = coords(stop.location)
            leg = await self.eta.eta(origin, LatLng(latitude, longitude))
            elapsed += leg.seconds
            origin = LatLng(latitude, longitude)

            stop.latest_eta = now + timedelta(seconds=elapsed)
            stop.eta_approximate = leg.approximate
            stop.eta_updated_at = now
            if leg.approximate:
                approximate_count += 1
            await self.events.publish(
                Event(
                    "stop.eta",
                    trip_channel(trip.id),
                    {
                        "trip_id": str(trip.id),
                        "stop_id": str(stop.id),
                        "request_id": str(stop.request_id),
                        "latest_eta": stop.latest_eta.isoformat(),
                        "eta_approximate": leg.approximate,
                    },
                )
            )

        await self.session.flush()
        return RefreshResult(trips=1, stops=len(stops), approximate=approximate_count)


def _is_due(stop: TripStop, now: datetime) -> bool:
    """Due if never computed, or if the last computation is older than the interval.

    Measured against `eta_updated_at`, not `latest_eta`: the latter is a future arrival
    time, which says nothing about how stale the estimate is.
    """
    return stop.eta_updated_at is None or (now - stop.eta_updated_at) >= REFRESH_INTERVAL
