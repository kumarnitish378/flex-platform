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
from app.domain.notifications import NotificationType
from app.domain.state_machines import StopKind, StopStatus, TripStatus
from app.modules.dispatch.models import Trip, TripStop
from app.modules.dispatch.service import DispatchService
from app.modules.notifications.service import Audience, NotificationService

logger = get_logger(__name__)

#: `architecture.md` section 3.2: "ETA worker recomputes active stop ETAs every 30 s".
REFRESH_INTERVAL = timedelta(seconds=30)

#: Stops still ahead of the driver.
PENDING_STATUSES = (StopStatus.pending, StopStatus.en_route)

#: EMP-05: "cab 5 minutes away". A product-stated figure rather than one of the tuning
#: knobs in `allocation-rules.md` section 1, so it lives here and not in operator config.
NEAR_THRESHOLD = timedelta(minutes=5)


@dataclass(frozen=True, slots=True)
class RefreshResult:
    trips: int = 0
    stops: int = 0
    approximate: int = 0
    #: "Cab 5 minutes away" notifications this sweep fired (EMP-05).
    near_alerts: int = 0


class EtaRefresher:
    def __init__(
        self,
        session: AsyncSession,
        clock: Clock,
        eta_service: Any,
        events: EventPublisher | None = None,
        notifications: NotificationService | None = None,
    ) -> None:
        self.session = session
        self.clock = clock
        self.eta = eta_service
        self.events = events or NullEventPublisher()
        self.notifications = notifications or NotificationService(session, clock)

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

        # Positions once for the whole fleet, not once per trip. Re-reading them inside
        # the loop made this O(trips) DISTINCT ON scans of `location_ping` every 30
        # seconds, which was most of a ten-second sim clock jump (OQ-26).
        positions = (
            await DispatchService(self.session, self.clock, self.eta).latest_positions(
                trips[0].operator_id
            )
            if trips
            else {}
        )

        result = RefreshResult()
        for trip in trips:
            refreshed = await self._refresh_trip(trip, positions)
            if refreshed.stops:
                result = RefreshResult(
                    trips=result.trips + 1,
                    stops=result.stops + refreshed.stops,
                    approximate=result.approximate + refreshed.approximate,
                    near_alerts=result.near_alerts + refreshed.near_alerts,
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

    async def _refresh_trip(self, trip: Trip, positions: dict[uuid.UUID, Any]) -> RefreshResult:
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

        near = 0
        for stop in stops:
            near += await self._warn_if_nearly_there(trip, stop, now)

        await self.session.flush()
        return RefreshResult(
            trips=1, stops=len(stops), approximate=approximate_count, near_alerts=near
        )

    async def _warn_if_nearly_there(self, trip: Trip, stop: TripStop, now: datetime) -> int:
        """EMP-05: tell the rider once when their cab is about five minutes out.

        Once, not every sweep: an ETA hovering either side of five minutes would otherwise
        buzz a phone every thirty seconds, which is how people turn notifications off.
        """
        if StopKind(stop.stop_type) is not StopKind.pickup:
            return 0
        if stop.near_alert_sent_at is not None or stop.latest_eta is None:
            return 0
        if stop.latest_eta - now > NEAR_THRESHOLD:
            return 0

        rider_user_id = await self._rider_user_id(stop.request_id)
        if rider_user_id is None:
            # Nobody to tell; do not burn the one-shot flag on a rider with no login.
            return 0

        minutes = max(1, round((stop.latest_eta - now).total_seconds() / 60))
        await self.notifications.notify(
            NotificationType.cab_nearby,
            Audience(employee=rider_user_id, operator_id=trip.operator_id),
            {
                "trip_id": str(trip.id),
                "stop_id": str(stop.id),
                "request_id": str(stop.request_id),
                "minutes_away": minutes,
            },
        )
        stop.near_alert_sent_at = now
        return 1

    async def _rider_user_id(self, request_id: uuid.UUID) -> uuid.UUID | None:
        from app.modules.people.models import Employee
        from app.modules.requests.models import RideRequest

        user_id: uuid.UUID | None = await self.session.scalar(
            select(Employee.user_id)
            .join(RideRequest, RideRequest.employee_id == Employee.id)
            .where(RideRequest.id == request_id)
        )
        return user_id


def _is_due(stop: TripStop, now: datetime) -> bool:
    """Due if never computed, or if the last computation is older than the interval.

    Measured against `eta_updated_at`, not `latest_eta`: the latter is a future arrival
    time, which says nothing about how stale the estimate is.
    """
    return stop.eta_updated_at is None or (now - stop.eta_updated_at) >= REFRESH_INTERVAL
