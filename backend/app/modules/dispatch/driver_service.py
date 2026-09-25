"""What the driver does to a trip (B15, DRV-03/05, `trip-lifecycle.md`).

Start, arrive, pick up, drop, complete. Every one of them arrives from a phone that may
have been offline for an hour, so two properties matter more than anything else here:

* **Idempotent.** Every action carries a device-generated `client_event_id`. A retry
  after a timeout must not pick the same rider up twice. The key is stored on
  `trip_event` under a unique index, so the guarantee is the database's, not a race
  between two workers.
* **Two clocks.** `occurred_at` is when the driver tapped; `Clock.now()` is when we heard.
  The business time is the driver's, validated in `app/domain/driver_actions.py`; the
  audit time is ours. Conflating them would have a trip that finished at 18:04 recorded as
  finishing at 19:30 because the phone found signal on the motorway.

Every status change goes through `app/domain/state_machines.py` (CLAUDE.md hard rule 5).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.events import Event, EventPublisher, NullEventPublisher, trip_channel, user_channel
from app.core.geo import to_point
from app.core.logging import get_logger
from app.domain.driver_actions import StopAction, check_occurred_at, effective_time
from app.domain.errors import Conflict, Forbidden, NotFound, ValidationFailed
from app.domain.state_machines import (
    Actor,
    RequestContext,
    RequestStatus,
    StopKind,
    StopStatus,
    TripStatus,
    VehicleStatus,
    actor_type_for,
    request_status_for_stop_done,
    transition_request,
    transition_stop,
    transition_trip,
    transition_vehicle,
)
from app.modules.config.service import ConfigService
from app.modules.dispatch.models import Trip, TripEvent, TripStop
from app.modules.fleet.models import Driver, Vehicle
from app.modules.requests.models import RideRequest, RideRequestEvent

logger = get_logger(__name__)

#: Trips a driver still has work to do on.
OPEN_TRIP_STATUSES = (TripStatus.planned, TripStatus.dispatched, TripStatus.in_progress)
FINISHED_TRIP_STATUSES = (TripStatus.completed, TripStatus.cancelled, TripStatus.aborted)


@dataclass(frozen=True, slots=True)
class DriverEvent:
    """One tap, as the device recorded it."""

    client_event_id: uuid.UUID
    occurred_at: datetime
    lat: float | None = None
    lng: float | None = None


class DriverTripService:
    def __init__(
        self,
        session: AsyncSession,
        clock: Clock,
        config: ConfigService | None = None,
        events: EventPublisher | None = None,
    ) -> None:
        self.session = session
        self.clock = clock
        self.config = config or ConfigService(session, clock)
        self.events = events or NullEventPublisher()

    # --- reading -------------------------------------------------------------------

    async def trips(self, user_id: uuid.UUID, scope: str = "active") -> list[Trip]:
        """The driver's own trips (DRV-03). Never anyone else's."""
        driver = await self._driver(user_id)
        wanted = {
            "active": [TripStatus.dispatched, TripStatus.in_progress],
            "upcoming": [TripStatus.planned, TripStatus.dispatched],
            "history": list(FINISHED_TRIP_STATUSES),
        }.get(scope)
        if wanted is None:
            raise ValidationFailed(f"Unknown scope: {scope}", {"scope": scope})

        order = Trip.planned_start.desc() if scope == "history" else Trip.planned_start.asc()
        result = await self.session.execute(
            select(Trip)
            .where(Trip.driver_id == driver.id)
            .where(Trip.status.in_([str(status) for status in wanted]))
            .order_by(order)
        )
        return list(result.scalars().all())

    async def stops_of(self, trip_id: uuid.UUID) -> list[TripStop]:
        result = await self.session.execute(
            select(TripStop).where(TripStop.trip_id == trip_id).order_by(TripStop.sequence)
        )
        return list(result.scalars().all())

    # --- trip actions ----------------------------------------------------------------

    async def start(self, user_id: uuid.UUID, trip_id: uuid.UUID, event: DriverEvent) -> Trip:
        """DRV-05: "Start trip". The first stop becomes en route."""
        trip, driver, at = await self._prepare(user_id, trip_id, event)
        done = await self._already_applied(event.client_event_id)
        if done:
            return trip

        if trip.status == str(TripStatus.in_progress):
            # A retry whose acknowledgement was lost. Already true, so say so quietly.
            return trip

        if trip.status == str(TripStatus.planned):
            # The driver starting is proof they were notified, which is what
            # `trip-lifecycle.md` means by dispatched. Recorded rather than skipped, so
            # the trip's history has no gap. It carries no client_event_id: the key
            # identifies the driver's *action*, and one tap is one key.
            self._apply_trip(trip, TripStatus.dispatched, Actor.driver, driver.user_id, at, None)

        self._apply_trip(trip, TripStatus.in_progress, Actor.driver, driver.user_id, at, event)
        trip.started_at = at

        first = await self._next_pending_stop(trip_id)
        if first is not None:
            self._apply_stop(first, StopStatus.en_route, at, event)

        await self.session.flush()
        await self._publish(trip, "trip.started", {"started_at": at.isoformat()})
        return trip

    async def complete(self, user_id: uuid.UUID, trip_id: uuid.UUID, event: DriverEvent) -> Trip:
        """DRV-05: "Complete trip". Only once every stop is finished."""
        trip, driver, at = await self._prepare(user_id, trip_id, event)
        if await self._already_applied(event.client_event_id):
            return trip
        if trip.status == str(TripStatus.completed):
            return trip

        unfinished = [
            stop
            for stop in await self.stops_of(trip_id)
            if stop.status not in {str(StopStatus.done), str(StopStatus.skipped)}
        ]
        if unfinished:
            raise Conflict(
                "The trip still has unfinished stops",
                {"unfinished": [str(stop.id) for stop in unfinished]},
            )

        self._apply_trip(trip, TripStatus.completed, Actor.driver, driver.user_id, at, event)
        trip.completed_at = at
        await self._release_vehicle(trip, Actor.driver)

        await self.session.flush()
        await self._publish(trip, "trip.completed", {"completed_at": at.isoformat()})
        return trip

    # --- stop actions -------------------------------------------------------------------

    async def stop_action(
        self, user_id: uuid.UUID, stop_id: uuid.UUID, action: StopAction, event: DriverEvent
    ) -> Trip:
        stop = await self.session.scalar(select(TripStop).where(TripStop.id == stop_id))
        if stop is None:
            raise NotFound("Stop not found")

        trip, driver, at = await self._prepare(user_id, stop.trip_id, event)
        if await self._already_applied(event.client_event_id):
            return trip
        if trip.status != str(TripStatus.in_progress):
            raise Conflict("Start the trip before updating its stops", {"trip_status": trip.status})

        if action is StopAction.arrived:
            await self._arrive(stop, at, event)
        elif action is StopAction.done:
            await self._finish(trip, stop, driver, at, event)
        else:
            await self._no_show(trip, stop, driver, at, event)

        self._record_trip_event(
            trip,
            from_status=trip.status,
            to_status=trip.status,
            actor=Actor.driver,
            actor_user_id=driver.user_id,
            at=self.clock.now(),
            occurred_at=at,
            client_event_id=event.client_event_id,
            data={"action": str(action), "stop_id": str(stop.id)},
        )
        await self.session.flush()
        return trip

    async def _arrive(self, stop: TripStop, at: datetime, event: DriverEvent) -> None:
        if stop.status == str(StopStatus.arrived):
            return
        if stop.status == str(StopStatus.pending):
            # `trip-lifecycle.md` section 3 is pending -> en_route -> arrived, and the
            # driver arriving somewhere is proof they were on their way. Drivers also
            # take stops out of order when a road is shut, so this must not need a
            # separate "I have set off" tap that no button sends.
            self._apply_stop(stop, StopStatus.en_route, at, event)
        self._apply_stop(stop, StopStatus.arrived, at, event)
        stop.arrived_at = at
        await self._publish_stop(stop, "stop.arrived", {"arrived_at": at.isoformat()})

    async def _finish(
        self, trip: Trip, stop: TripStop, driver: Driver, at: datetime, event: DriverEvent
    ) -> None:
        """Picked up or dropped: the stop finishes and its request moves with it."""
        if stop.status == str(StopStatus.done):
            return
        if stop.status != str(StopStatus.arrived):
            # `trip-lifecycle.md` section 3: arrive before you finish. Recording a
            # pickup from three streets away is how a rider gets left behind.
            raise Conflict("Mark the stop arrived first", {"stop_status": stop.status})

        self._apply_stop(stop, StopStatus.done, at, event)
        stop.done_at = at

        kind = StopKind(stop.stop_type)
        target = request_status_for_stop_done(kind)
        await self._move_request(stop.request_id, target, driver, at, event)
        await self._head_for_the_next_stop(stop, at, event)
        await self._publish_stop(
            stop, "stop.done", {"done_at": at.isoformat(), "stop_type": str(kind)}
        )

    async def _head_for_the_next_stop(
        self, finished: TripStop, at: datetime, event: DriverEvent
    ) -> None:
        """Leaving one stop means being on the way to the next.

        Without this only the first stop of a trip is ever `en_route`, and the rest can
        never legally reach `arrived`.
        """
        following = await self._next_pending_stop(finished.trip_id)
        if following is not None:
            self._apply_stop(following, StopStatus.en_route, at, event)

    async def _no_show(
        self, trip: Trip, stop: TripStop, driver: Driver, at: datetime, event: DriverEvent
    ) -> None:
        """DRV-05: only after waiting `no_show_wait_minutes` at an arrived stop."""
        if StopKind(stop.stop_type) is not StopKind.pickup:
            raise Conflict("Only a pickup can be a no-show", {"stop_id": str(stop.id)})
        if stop.status == str(StopStatus.skipped):
            return

        wait_minutes = int(await self.config.get(trip.operator_id, "no_show_wait_minutes"))
        request = await self._request(stop.request_id)
        # The state machine owns the wait rule; it needs the stop's facts to apply it.
        transition = transition_request(
            RequestStatus(request.status),
            RequestStatus.no_show,
            RequestContext(
                actor=Actor.driver,
                stop_status=StopStatus(stop.status),
                stop_arrived_at=stop.arrived_at,
                now=at,
                no_show_wait_minutes=wait_minutes,
            ),
        )
        self._apply_stop(stop, StopStatus.skipped, at, event)
        self._commit_request(request, transition, driver.user_id, at, extra={"no_show": True})

        # A rider who never got in cannot be dropped. Without skipping their drop too,
        # the stop sits pending forever and the driver can never complete the trip.
        for other in await self.stops_of(stop.trip_id):
            if (
                other.request_id == stop.request_id
                and other.id != stop.id
                and other.status not in {str(StopStatus.done), str(StopStatus.skipped)}
            ):
                self._apply_stop(other, StopStatus.skipped, at, event)

        await self._head_for_the_next_stop(stop, at, event)
        await self._publish_stop(stop, "stop.no_show", {"at": at.isoformat()})

    # --- shared plumbing --------------------------------------------------------------

    async def _prepare(
        self, user_id: uuid.UUID, trip_id: uuid.UUID, event: DriverEvent
    ) -> tuple[Trip, Driver, datetime]:
        """Load the trip, check it is this driver's, and settle on the business time."""
        driver = await self._driver(user_id)
        trip = await self.session.scalar(select(Trip).where(Trip.id == trip_id))
        if trip is None:
            raise NotFound("Trip not found")
        if trip.driver_id != driver.id:
            # Another driver's trip is not theirs to touch, even to read.
            raise Forbidden("That trip belongs to another driver")

        now = self.clock.now()
        bad = check_occurred_at(event.occurred_at, now)
        if bad is not None:
            raise ValidationFailed(
                f"occurred_at is not usable: {bad.detail}", {"reason": bad.reason}
            )
        return trip, driver, effective_time(event.occurred_at, now)

    async def _driver(self, user_id: uuid.UUID) -> Driver:
        driver = await self.session.scalar(select(Driver).where(Driver.user_id == user_id))
        if driver is None:
            raise Forbidden("This account is not linked to a driver record")
        return driver

    async def _already_applied(self, client_event_id: uuid.UUID) -> bool:
        """Has this exact tap already been processed? (`coding-standards.md` section 5.)"""
        seen = await self.session.scalar(
            select(TripEvent.id).where(TripEvent.client_event_id == client_event_id)
        )
        if seen is not None:
            logger.info("driver_event_ignored_duplicate", client_event_id=str(client_event_id))
        return seen is not None

    async def _next_pending_stop(self, trip_id: uuid.UUID) -> TripStop | None:
        stop: TripStop | None = await self.session.scalar(
            select(TripStop)
            .where(TripStop.trip_id == trip_id)
            .where(TripStop.status == str(StopStatus.pending))
            .order_by(TripStop.sequence)
            .limit(1)
        )
        return stop

    async def _request(self, request_id: uuid.UUID) -> RideRequest:
        request = await self.session.scalar(select(RideRequest).where(RideRequest.id == request_id))
        if request is None:
            raise NotFound("Ride request not found")
        return request

    async def _move_request(
        self,
        request_id: uuid.UUID,
        target: RequestStatus,
        driver: Driver,
        at: datetime,
        event: DriverEvent,
    ) -> None:
        request = await self._request(request_id)
        if request.status == str(target):
            return
        transition = transition_request(
            RequestStatus(request.status), target, RequestContext(actor=Actor.driver)
        )
        self._commit_request(request, transition, driver.user_id, at)

    def _commit_request(
        self,
        request: RideRequest,
        transition: Any,
        actor_user_id: uuid.UUID | None,
        at: datetime,
        extra: dict[str, Any] | None = None,
    ) -> None:
        request.status = transition.to_status
        self.session.add(
            RideRequestEvent(
                operator_id=request.operator_id,
                request_id=request.id,
                from_status=transition.from_status,
                to_status=transition.to_status,
                actor_type=actor_type_for(Actor.driver),
                actor_user_id=actor_user_id,
                at=at,
                data={
                    "notify": [str(recipient) for recipient in transition.notify],
                    **(extra or {}),
                },
            )
        )

    def _apply_trip(
        self,
        trip: Trip,
        target: TripStatus,
        actor: Actor,
        actor_user_id: uuid.UUID | None,
        at: datetime,
        event: DriverEvent | None,
    ) -> None:
        """Move the trip and log it. `event` is None for a step the driver did not tap."""
        transition = transition_trip(TripStatus(trip.status), target, actor=actor)
        trip.status = transition.to_status
        self._record_trip_event(
            trip,
            from_status=transition.from_status,
            to_status=transition.to_status,
            actor=actor,
            actor_user_id=actor_user_id,
            at=self.clock.now(),
            occurred_at=at,
            client_event_id=event.client_event_id if event is not None else None,
        )

    def _apply_stop(
        self, stop: TripStop, target: StopStatus, at: datetime, event: DriverEvent
    ) -> None:
        transition = transition_stop(StopStatus(stop.status), target, actor=Actor.driver)
        stop.status = transition.to_status
        if event.lat is not None and event.lng is not None:
            # Where the driver actually was when they tapped, for disputes.
            stop.event_location = to_point(event.lat, event.lng)

    async def _release_vehicle(self, trip: Trip, actor: Actor) -> None:
        vehicle = await self.session.scalar(select(Vehicle).where(Vehicle.id == trip.vehicle_id))
        if vehicle is None or vehicle.status != str(VehicleStatus.on_trip):
            return
        transition = transition_vehicle(VehicleStatus.on_trip, VehicleStatus.available, actor=actor)
        vehicle.status = transition.to_status

    def _record_trip_event(
        self,
        trip: Trip,
        from_status: str | None,
        to_status: str,
        actor: Actor,
        actor_user_id: uuid.UUID | None,
        at: datetime,
        occurred_at: datetime | None = None,
        client_event_id: uuid.UUID | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        self.session.add(
            TripEvent(
                operator_id=trip.operator_id,
                trip_id=trip.id,
                from_status=from_status,
                to_status=to_status,
                actor_type=actor_type_for(actor),
                actor_user_id=actor_user_id,
                at=at,
                occurred_at=occurred_at,
                client_event_id=client_event_id,
                data=data,
            )
        )

    # --- events --------------------------------------------------------------------------

    async def _publish(self, trip: Trip, name: str, payload: dict[str, Any]) -> None:
        body = {"trip_id": str(trip.id), **payload}
        await self.events.publish(Event(name, trip_channel(trip.id), body))

    async def _publish_stop(self, stop: TripStop, name: str, payload: dict[str, Any]) -> None:
        body = {
            "trip_id": str(stop.trip_id),
            "stop_id": str(stop.id),
            "request_id": str(stop.request_id),
            **payload,
        }
        await self.events.publish(Event(name, trip_channel(stop.trip_id), body))
        employee_user_id = await self._rider_user_id(stop.request_id)
        if employee_user_id is not None:
            await self.events.publish(Event(name, user_channel(employee_user_id), body))

    async def _rider_user_id(self, request_id: uuid.UUID) -> uuid.UUID | None:
        from app.modules.people.models import Employee

        return await self.session.scalar(
            select(Employee.user_id)
            .join(RideRequest, RideRequest.employee_id == Employee.id)
            .where(RideRequest.id == request_id)
        )
