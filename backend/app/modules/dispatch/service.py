"""Dispatch: the board, candidate vehicles, and manual assignment (B14).

This is the screen that replaces the phone call. A supervisor sees the queue, sees which
cabs could take it and what that would cost the people already on board, and presses a
button. Everything here serves that loop.

Three rules shape the code:

* **The pure part is pure.** Sequencing and the hard-rule checks live in
  `app/domain/dispatch.py` and take a duration callable, so this module's job is loading
  facts and persisting the result.
* **One routing call per question.** Candidates ask for one ETA matrix covering every
  vehicle, not one call per vehicle; an insertion asks for one matrix covering the trip's
  stops. On the shared public OSRM that difference is the whole rate-limit budget
  (ADR-0010).
* **Violations are reported, capacity is refused** (ADR-0011). A supervisor overriding the
  optimizer is the purpose of manual mode; five people in a four-seat car is not an
  override, it is a stranded rider.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.events import (
    Event,
    EventPublisher,
    NullEventPublisher,
    operator_channel,
    trip_channel,
    user_channel,
)
from app.core.geo import coords as _coords
from app.core.geo import to_point as _point
from app.core.logging import get_logger
from app.domain.dispatch import (
    AssignmentFacts,
    DetourLimits,
    Duration,
    Insertion,
    Place,
    Rider,
    Violation,
    best_insertion,
    build_plan,
    check_hard_rules,
    pickup_time,
    stricter,
)
from app.domain.enums import Direction
from app.domain.errors import Conflict, NotFound
from app.domain.geo import LatLng
from app.domain.state_machines import (
    Actor,
    RequestContext,
    RequestStatus,
    StopStatus,
    TripStatus,
    VehicleStatus,
    actor_type_for,
    transition_request,
    transition_vehicle,
)
from app.modules.config.service import ConfigService
from app.modules.dispatch.models import MODE_MANUAL, Trip, TripEvent, TripStop
from app.modules.fleet.duty_models import DutySession
from app.modules.fleet.models import Vehicle
from app.modules.people.models import Employee
from app.modules.requests.models import RideRequest, RideRequestEvent
from app.modules.tenancy.models import ClientPolicy, Office

logger = get_logger(__name__)

#: Trips a vehicle can still be busy with.
LIVE_TRIP_STATUSES = (TripStatus.planned, TripStatus.dispatched, TripStatus.in_progress)
#: Requests that still occupy a seat.
ON_BOARD_STATUSES = (RequestStatus.assigned, RequestStatus.picked_up)
#: Requests a supervisor can still assign.
ASSIGNABLE_STATUSES = (RequestStatus.queued, RequestStatus.suggested)

#: How far back to look for a vehicle's last ping. Anything older is stale several times
#: over, and the bound keeps the query off older partitions of `location_ping`.
POSITION_LOOKBACK = timedelta(hours=1)


@dataclass(frozen=True, slots=True)
class Position:
    lat: float
    lng: float
    recorded_at: datetime

    @property
    def place(self) -> Place:
        return Place(self.lat, self.lng)


@dataclass(slots=True)
class VehicleLive:
    vehicle: Vehicle
    position: Position | None
    stale: bool
    active_trip_id: uuid.UUID | None
    seats_free: int


@dataclass(slots=True)
class Candidate:
    vehicle: Vehicle
    trip_id: uuid.UUID | None
    eta_to_pickup_seconds: float
    eta_approximate: bool
    seats_free_after: int
    added_minutes: dict[uuid.UUID, float] = field(default_factory=dict)
    new_trip: bool = True
    violations: list[Violation] = field(default_factory=list)

    @property
    def sort_key(self) -> tuple[int, float]:
        """Best first: everything clean, then by how soon it can be at the pickup."""
        return (1 if self.violations else 0, self.eta_to_pickup_seconds)


class DispatchService:
    def __init__(
        self,
        session: AsyncSession,
        clock: Clock,
        eta_service: Any,
        config: ConfigService | None = None,
        events: EventPublisher | None = None,
    ) -> None:
        self.session = session
        self.clock = clock
        self.eta = eta_service
        self.config = config or ConfigService(session, clock)
        self.events = events or NullEventPublisher()

    # --- the board ------------------------------------------------------------

    async def requests(
        self,
        operator_id: uuid.UUID,
        statuses: list[str] | None = None,
        client_id: uuid.UUID | None = None,
    ) -> list[RideRequest]:
        """The queue. Defaults to everything still open, oldest first (SUP-02)."""
        wanted = statuses or [
            RequestStatus.requested,
            RequestStatus.queued,
            RequestStatus.suggested,
            RequestStatus.assigned,
            RequestStatus.picked_up,
        ]
        query = (
            select(RideRequest)
            .where(RideRequest.operator_id == operator_id)
            .where(RideRequest.status.in_([str(status) for status in wanted]))
            .order_by(RideRequest.created_at)
        )
        if client_id is not None:
            query = query.where(RideRequest.client_id == client_id)
        return list((await self.session.execute(query)).scalars().all())

    async def live_vehicles(self, operator_id: uuid.UUID) -> list[VehicleLive]:
        """Every vehicle with its last known position and load (SUP-01)."""
        vehicles = list(
            (
                await self.session.execute(
                    select(Vehicle)
                    .where(Vehicle.operator_id == operator_id)
                    .order_by(Vehicle.registration_no)
                )
            )
            .scalars()
            .all()
        )
        positions = await self.latest_positions(operator_id)
        trips = await self._live_trips(operator_id)
        loads = await self._riders_by_trip(operator_id)
        stale_after = int(await self.config.get(operator_id, "stale_gps_seconds"))
        now = self.clock.now()

        live: list[VehicleLive] = []
        for vehicle in vehicles:
            position = positions.get(vehicle.id)
            trip = trips.get(vehicle.id)
            on_board = len(loads.get(trip.id, [])) if trip else 0
            live.append(
                VehicleLive(
                    vehicle=vehicle,
                    position=position,
                    stale=_is_stale(position, now, stale_after),
                    active_trip_id=trip.id if trip else None,
                    seats_free=max(0, vehicle.seat_capacity - on_board),
                )
            )
        return live

    async def automation_paused(self, operator_id: uuid.UUID) -> bool:
        paused = await self.session.scalar(
            text("SELECT automation_paused FROM operator WHERE id = :id").bindparams(id=operator_id)
        )
        if paused is None:
            raise NotFound("Operator not found")
        return bool(paused)

    async def set_automation_paused(
        self, operator_id: uuid.UUID, paused: bool, reason_code: str, note: str | None = None
    ) -> bool:
        """SUP-05: one switch, visible to every supervisor."""
        await self.session.execute(
            text("UPDATE operator SET automation_paused = :paused WHERE id = :id").bindparams(
                paused=paused, id=operator_id
            )
        )
        logger.info(
            "automation_pause_changed",
            operator_id=str(operator_id),
            paused=paused,
            reason_code=reason_code,
        )
        await self.events.publish(
            Event(
                name="automation.changed",
                channel=operator_channel(operator_id, "requests"),
                payload={"automation_paused": paused, "reason_code": reason_code, "note": note},
            )
        )
        return paused

    # --- candidates -------------------------------------------------------------

    async def candidates(self, operator_id: uuid.UUID, request_id: uuid.UUID) -> list[Candidate]:
        """Vehicles that could take this request, best first (`allocation-rules.md` 3).

        On-duty vehicles only: an `off_duty` or `out_of_service` cab has no driver to send.
        Everything else is listed **with** its violations rather than filtered out, because
        an empty candidate list tells a supervisor nothing, and "the nearest cab is 35
        minutes away, over the limit" is exactly what they need to decide what to do next.

        A vehicle with no recent ping is skipped: its ETA is not unknown-but-guessable, it
        is unknowable, and a made-up number here becomes a promise to a rider.
        """
        request = await self._request(operator_id, request_id)
        office = await self._office(operator_id, request.office_id)
        employee = await self._employee(operator_id, request.employee_id)
        settings = await self.config.all_values(operator_id)

        vehicles = list(
            (
                await self.session.execute(
                    select(Vehicle)
                    .where(Vehicle.operator_id == operator_id)
                    .where(
                        Vehicle.status.in_(
                            [str(VehicleStatus.available), str(VehicleStatus.on_trip)]
                        )
                    )
                )
            )
            .scalars()
            .all()
        )
        positions = await self.latest_positions(operator_id)
        usable = [vehicle for vehicle in vehicles if vehicle.id in positions]
        if not usable:
            return []

        pickup = _pickup_place(request, office)
        # One table call for every vehicle, not one route call each (ADR-0010).
        matrix = await self.eta.eta_matrix(
            [LatLng(positions[vehicle.id].lat, positions[vehicle.id].lng) for vehicle in usable],
            [LatLng(pickup.lat, pickup.lng)],
        )

        trips = await self._live_trips(operator_id)
        loads = await self._riders_by_trip(operator_id)
        now = self.clock.now()

        candidates: list[Candidate] = []
        for index, vehicle in enumerate(usable):
            eta = matrix[index][0]
            trip = trips.get(vehicle.id)
            on_board = loads.get(trip.id, []) if trip else []
            insertion = None
            if trip is not None and on_board:
                insertion = await self._insertion_for(trip, on_board, request, office)

            facts = await self._facts(
                request=request,
                employee=employee,
                vehicle=vehicle,
                trip=trip,
                other_riders=bool(on_board),
                position=positions[vehicle.id],
                eta_seconds=eta.seconds,
                settings=settings,
                now=now,
            )
            limits, direct = await self._detour_inputs(operator_id, request, on_board, office)
            candidates.append(
                Candidate(
                    vehicle=vehicle,
                    trip_id=trip.id if trip is not None else None,
                    eta_to_pickup_seconds=eta.seconds,
                    eta_approximate=eta.approximate,
                    seats_free_after=vehicle.seat_capacity - len(on_board) - 1,
                    added_minutes=insertion.added_minutes if insertion else {},
                    new_trip=trip is None,
                    violations=check_hard_rules(facts, insertion, limits, direct),
                )
            )

        candidates.sort(key=lambda candidate: candidate.sort_key)
        return candidates

    # --- assignment ---------------------------------------------------------------

    async def assign(
        self,
        operator_id: uuid.UUID,
        request_id: uuid.UUID,
        vehicle_id: uuid.UUID,
        actor: Actor,
        actor_user_id: uuid.UUID | None,
        trip_id: uuid.UUID | None = None,
        reason_code: str | None = None,
        note: str | None = None,
    ) -> Trip:
        """Put a request on a vehicle: a new trip, or a seat on an existing one (SUP-03).

        Refuses on capacity, on an unknown id, and on any transition the state machine
        does not allow. Everything else is recorded as an accepted violation (ADR-0011).
        """
        request = await self._request(operator_id, request_id)
        vehicle = await self._vehicle(operator_id, vehicle_id)
        office = await self._office(operator_id, request.office_id)
        employee = await self._employee(operator_id, request.employee_id)
        settings = await self.config.all_values(operator_id)
        now = self.clock.now()

        if request.status not in [str(status) for status in ASSIGNABLE_STATUSES]:
            # The state machine would refuse too, but this says why in the supervisor's
            # language rather than as an edge that does not exist.
            raise Conflict(
                f"A {request.status} request cannot be assigned",
                {"request_id": str(request_id), "status": request.status},
            )

        trip = await self._target_trip(operator_id, trip_id, vehicle)
        on_board = await self._riders_of(trip) if trip is not None else []

        seats_needed = len(on_board) + 1
        if seats_needed > vehicle.seat_capacity:
            raise Conflict(
                "The vehicle does not have a free seat",
                {
                    "vehicle_id": str(vehicle_id),
                    "seat_capacity": vehicle.seat_capacity,
                    "riders_after": seats_needed,
                },
            )

        driver_id = await self._driver_on_duty(vehicle_id)
        if driver_id is None:
            raise Conflict("The vehicle has no driver on duty", {"vehicle_id": str(vehicle_id)})

        position = (await self.latest_positions(operator_id)).get(vehicle_id)
        eta_seconds, eta_approximate = await self._eta_to_pickup(position, request, office)

        insertion = (
            await self._insertion_for(trip, on_board, request, office)
            if trip is not None and on_board
            else None
        )
        facts = await self._facts(
            request=request,
            employee=employee,
            vehicle=vehicle,
            trip=trip,
            other_riders=bool(on_board),
            position=position,
            eta_seconds=eta_seconds,
            settings=settings,
            now=now,
        )
        limits, direct = await self._detour_inputs(operator_id, request, on_board, office)
        violations = check_hard_rules(facts, insertion, limits, direct)

        created = trip is None
        if trip is None:
            trip = Trip(
                operator_id=operator_id,
                vehicle_id=vehicle_id,
                driver_id=driver_id,
                direction=request.direction,
                office_id=request.office_id,
                status=TripStatus.planned,
                pooling_blocked=request.no_sharing or employee.is_vip,
                planned_start=now,
                mode_used=MODE_MANUAL,
            )
            self.session.add(trip)
            await self.session.flush()

        riders = [*on_board, Rider(request.id, _rider_place(request))]
        if insertion is not None:
            riders = list(insertion.plan.order)
        await self._write_stops(trip, riders, office, eta_seconds, eta_approximate, now)

        # The request moves through the state machine; nothing writes `status` directly.
        event = transition_request(
            RequestStatus(request.status),
            RequestStatus.assigned,
            RequestContext(actor=actor, is_locked=request.is_locked, changes_vehicle=True),
        )
        request.status = event.to_status
        request.trip_id = trip.id
        self.session.add(
            RideRequestEvent(
                operator_id=operator_id,
                request_id=request.id,
                from_status=event.from_status,
                to_status=event.to_status,
                actor_type=actor_type_for(actor),
                actor_user_id=actor_user_id,
                reason=note,
                at=now,
                data={
                    "trip_id": str(trip.id),
                    "vehicle_id": str(vehicle_id),
                    "notify": [str(recipient) for recipient in event.notify],
                },
            )
        )

        if vehicle.status == str(VehicleStatus.available):
            vehicle_event = transition_vehicle(
                VehicleStatus.available, VehicleStatus.on_trip, actor=actor
            )
            vehicle.status = vehicle_event.to_status

        self._record_trip_event(
            trip,
            from_status=None if created else trip.status,
            to_status=trip.status,
            actor=actor,
            actor_user_id=actor_user_id,
            now=now,
            reason=note,
            data={
                "action": "trip_created" if created else "rider_added",
                "request_id": str(request.id),
                "reason_code": reason_code,
                # Recorded so an override against the rules stays visible (ADR-0011).
                "violations_accepted": [str(violation) for violation in violations],
            },
        )
        await self.session.flush()

        await self._notify_assigned(trip, request, employee, vehicle, driver_id, eta_seconds)
        logger.info(
            "request_assigned",
            request_id=str(request.id),
            trip_id=str(trip.id),
            vehicle_id=str(vehicle_id),
            new_trip=created,
            violations=[str(violation) for violation in violations],
        )
        return trip

    async def _notify_assigned(
        self,
        trip: Trip,
        request: RideRequest,
        employee: Employee,
        vehicle: Vehicle,
        driver_id: uuid.UUID,
        eta_seconds: float,
    ) -> None:
        """SUP-03: the employee and the driver hear about it within 10 seconds.

        `trip-lifecycle.md` section 6 names the recipients; the state machine returns
        them, and these are the channels they listen on (`architecture.md` section 4).
        """
        payload = {
            "trip_id": str(trip.id),
            "request_id": str(request.id),
            "vehicle_id": str(vehicle.id),
            "registration_no": vehicle.registration_no,
            "driver_id": str(driver_id),
            "pickup_eta_seconds": int(eta_seconds),
        }
        await self.events.publish(Event("request.assigned", trip_channel(trip.id), payload))
        if employee.user_id is not None:
            await self.events.publish(
                Event("request.assigned", user_channel(employee.user_id), payload)
            )
        driver_user_id = await self._driver_user_id(driver_id)
        if driver_user_id is not None:
            await self.events.publish(Event("trip.assigned", user_channel(driver_user_id), payload))
        await self.events.publish(
            Event("trip.assigned", operator_channel(trip.operator_id, "requests"), payload)
        )

    # --- stops --------------------------------------------------------------------

    async def _write_stops(
        self,
        trip: Trip,
        riders: list[Rider],
        office: Office,
        eta_seconds: float,
        eta_approximate: bool,
        now: datetime,
    ) -> None:
        """Rewrite the trip's stops from the rider order.

        Rewriting rather than patching keeps `sequence` contiguous and unique without a
        renumbering dance. Stops that already happened are left exactly as they were: a
        driver who has arrived somewhere cannot have that undone by a later insertion.
        """
        existing = list(
            (
                await self.session.execute(
                    select(TripStop).where(TripStop.trip_id == trip.id).order_by(TripStop.sequence)
                )
            )
            .scalars()
            .all()
        )
        done = {
            (stop.request_id, stop.stop_type): stop
            for stop in existing
            if stop.status != str(StopStatus.pending)
        }
        plan = build_plan(
            Direction(trip.direction),
            Place(*_coords(office.location)),
            riders,
            self._planner_duration(),
        )

        for stop in existing:
            if (stop.request_id, stop.stop_type) not in done:
                await self.session.delete(stop)
        await self.session.flush()

        eta_at = now + timedelta(seconds=eta_seconds)
        for planned in plan.stops:
            kept = done.get((planned.request_id, str(planned.kind)))
            if kept is not None:
                kept.sequence = planned.sequence
                continue
            self.session.add(
                TripStop(
                    operator_id=trip.operator_id,
                    trip_id=trip.id,
                    sequence=planned.sequence,
                    stop_type=planned.kind,
                    request_id=planned.request_id,
                    location=_point(planned.place.lat, planned.place.lng),
                    status=StopStatus.pending,
                    planned_eta=eta_at,
                    latest_eta=eta_at,
                    eta_approximate=eta_approximate,
                )
            )
        await self.session.flush()

    @staticmethod
    def _planner_duration() -> Duration:
        """A duration callable for `build_plan` that needs no network.

        Writing the stops does not re-decide the order - `best_insertion` already did that
        with real ETAs - so this only has to be consistent, not accurate. Asking OSRM again
        here would spend rate-limit budget reproducing an answer we already have.
        """
        return _haversine_seconds

    # --- fact loading -----------------------------------------------------------------

    async def latest_positions(self, operator_id: uuid.UUID) -> dict[uuid.UUID, Position]:
        """Each vehicle's most recent ping.

        Read from `location_ping` rather than Redis: Redis holds the live map's hot path,
        but it expires and can be cold after a restart, and a dispatch decision made from
        a missing key would silently be a dispatch decision made from no information.
        """
        rows = await self.session.execute(
            text(
                """
                SELECT DISTINCT ON (vehicle_id)
                       vehicle_id,
                       recorded_at,
                       ST_Y(location::geometry) AS lat,
                       ST_X(location::geometry) AS lng
                FROM location_ping
                WHERE operator_id = :operator_id AND recorded_at >= :since
                ORDER BY vehicle_id, recorded_at DESC
                """
            ).bindparams(operator_id=operator_id, since=self.clock.now() - POSITION_LOOKBACK)
        )
        return {
            row.vehicle_id: Position(lat=row.lat, lng=row.lng, recorded_at=row.recorded_at)
            for row in rows
        }

    async def _live_trips(self, operator_id: uuid.UUID) -> dict[uuid.UUID, Trip]:
        """The open trip per vehicle, if any."""
        trips = (
            (
                await self.session.execute(
                    select(Trip)
                    .where(Trip.operator_id == operator_id)
                    .where(Trip.status.in_([str(status) for status in LIVE_TRIP_STATUSES]))
                )
            )
            .scalars()
            .all()
        )
        return {trip.vehicle_id: trip for trip in trips}

    async def _riders_by_trip(self, operator_id: uuid.UUID) -> dict[uuid.UUID, list[Rider]]:
        """Riders still occupying a seat, grouped by trip."""
        rows = (
            (
                await self.session.execute(
                    select(RideRequest)
                    .where(RideRequest.operator_id == operator_id)
                    .where(RideRequest.trip_id.is_not(None))
                    .where(RideRequest.status.in_([str(s) for s in ON_BOARD_STATUSES]))
                )
            )
            .scalars()
            .all()
        )
        grouped: dict[uuid.UUID, list[Rider]] = {}
        for row in rows:
            assert row.trip_id is not None
            grouped.setdefault(row.trip_id, []).append(Rider(row.id, _rider_place(row)))
        return grouped

    async def _riders_of(self, trip: Trip) -> list[Rider]:
        by_trip = await self._riders_by_trip(trip.operator_id)
        return by_trip.get(trip.id, [])

    async def _insertion_for(
        self, trip: Trip, on_board: list[Rider], request: RideRequest, office: Office
    ) -> Insertion:
        """Where the new rider fits, and what it costs the others.

        One matrix call covering every stop place, then pure arithmetic over every
        insertion position.
        """
        newcomer = Rider(request.id, _rider_place(request))
        places = _unique_places(
            [rider.place for rider in [*on_board, newcomer]] + [Place(*_coords(office.location))]
        )
        duration = await self._duration_table(places)
        return best_insertion(
            Direction(trip.direction),
            Place(*_coords(office.location)),
            on_board,
            newcomer,
            duration,
        )

    async def _duration_table(self, places: list[Place]) -> Duration:
        """A `duration(a, b)` callable backed by one pre-fetched matrix."""
        points = [LatLng(place.lat, place.lng) for place in places]
        matrix = await self.eta.eta_matrix(points, points)
        lookup: dict[tuple[Place, Place], float] = {
            (places[row], places[column]): matrix[row][column].seconds
            for row in range(len(places))
            for column in range(len(places))
        }

        def duration(first: Place, second: Place) -> float:
            return lookup.get((first, second), _haversine_seconds(first, second))

        return duration

    async def _facts(
        self,
        request: RideRequest,
        employee: Employee,
        vehicle: Vehicle,
        trip: Trip | None,
        other_riders: bool,
        position: Position | None,
        eta_seconds: float,
        settings: dict[str, Any],
        now: datetime,
    ) -> AssignmentFacts:
        return AssignmentFacts(
            vehicle_id=vehicle.id,
            vehicle_status=vehicle.status,
            vehicle_type=vehicle.vehicle_type,
            gps_age_seconds=(
                (now - position.recorded_at).total_seconds() if position is not None else None
            ),
            stale_gps_seconds=int(settings["stale_gps_seconds"]),
            eta_to_pickup_seconds=eta_seconds,
            candidate_max_eta_minutes=int(settings["candidate_max_eta_minutes"]),
            pickup_window_minutes=int(settings["pickup_window_minutes"]),
            requested_time=request.requested_time,
            pickup_at=pickup_time(now, eta_seconds),
            direction=Direction(request.direction),
            office_id=request.office_id,
            employee_is_vip=employee.is_vip,
            request_no_sharing=request.no_sharing,
            lock_vehicle_id=request.lock_vehicle_id,
            trip_direction=Direction(trip.direction) if trip is not None else None,
            trip_office_id=trip.office_id if trip is not None else None,
            trip_pooling_blocked=trip.pooling_blocked if trip is not None else False,
            trip_has_other_riders=other_riders,
        )

    async def _detour_inputs(
        self,
        operator_id: uuid.UUID,
        request: RideRequest,
        on_board: list[Rider],
        office: Office,
    ) -> tuple[dict[uuid.UUID, DetourLimits], dict[uuid.UUID, float]]:
        """Per-rider detour limits and direct times.

        Limits come from operator config tightened by the rider's client policy, because
        `allocation-rules.md` section 2 rule 7 uses the **stricter** of the two.
        """
        settings = await self.config.all_values(operator_id)
        operator_limits = DetourLimits(
            max_detour_factor=float(settings["max_detour_factor"]),
            max_detour_minutes=float(settings["max_detour_minutes"]),
        )

        request_ids = [rider.request_id for rider in on_board] + [request.id]
        rows = list(
            (await self.session.execute(select(RideRequest).where(RideRequest.id.in_(request_ids))))
            .scalars()
            .all()
        )
        policies = {
            policy.client_id: policy
            for policy in (
                await self.session.execute(
                    select(ClientPolicy).where(
                        ClientPolicy.client_id.in_({row.client_id for row in rows})
                    )
                )
            )
            .scalars()
            .all()
        }

        limits: dict[uuid.UUID, DetourLimits] = {}
        for row in rows:
            policy = policies.get(row.client_id)
            limits[row.id] = (
                stricter(
                    operator_limits,
                    DetourLimits(
                        max_detour_factor=float(
                            policy.max_detour_factor or operator_limits.max_detour_factor
                        ),
                        max_detour_minutes=float(
                            policy.max_detour_minutes
                            if policy.max_detour_minutes is not None
                            else operator_limits.max_detour_minutes
                        ),
                    ),
                )
                if policy is not None
                else operator_limits
            )

        office_place = Place(*_coords(office.location))
        direct: dict[uuid.UUID, float] = {}
        for row in rows:
            direct[row.id] = _haversine_seconds(_rider_place(row), office_place)
        return limits, direct

    async def _eta_to_pickup(
        self, position: Position | None, request: RideRequest, office: Office
    ) -> tuple[float, bool]:
        """Zero when the vehicle's position is unknown; `gps_stale` already flags that."""
        if position is None:
            return 0.0, True
        pickup = _pickup_place(request, office)
        estimate = await self.eta.eta(
            LatLng(position.lat, position.lng), LatLng(pickup.lat, pickup.lng)
        )
        return estimate.seconds, estimate.approximate

    # --- loading and refusals ------------------------------------------------------

    async def _request(self, operator_id: uuid.UUID, request_id: uuid.UUID) -> RideRequest:
        request = await self.session.scalar(
            select(RideRequest)
            .where(RideRequest.id == request_id)
            .where(RideRequest.operator_id == operator_id)
        )
        if request is None:
            # Another operator's id is a 404, not a 403: a 403 confirms it exists.
            raise NotFound("Ride request not found")
        return request

    async def _vehicle(self, operator_id: uuid.UUID, vehicle_id: uuid.UUID) -> Vehicle:
        vehicle = await self.session.scalar(
            select(Vehicle)
            .where(Vehicle.id == vehicle_id)
            .where(Vehicle.operator_id == operator_id)
        )
        if vehicle is None:
            raise NotFound("Vehicle not found")
        return vehicle

    async def _office(self, operator_id: uuid.UUID, office_id: uuid.UUID) -> Office:
        office = await self.session.scalar(
            select(Office).where(Office.id == office_id).where(Office.operator_id == operator_id)
        )
        if office is None:
            raise NotFound("Office not found")
        return office

    async def _employee(self, operator_id: uuid.UUID, employee_id: uuid.UUID) -> Employee:
        employee = await self.session.scalar(
            select(Employee)
            .where(Employee.id == employee_id)
            .where(Employee.operator_id == operator_id)
        )
        if employee is None:
            raise NotFound("Employee not found")
        return employee

    async def _target_trip(
        self, operator_id: uuid.UUID, trip_id: uuid.UUID | None, vehicle: Vehicle
    ) -> Trip | None:
        """The trip to add to: the one asked for, or the vehicle's open trip, or none."""
        if trip_id is None:
            return (await self._live_trips(operator_id)).get(vehicle.id)

        trip = await self.session.scalar(
            select(Trip).where(Trip.id == trip_id).where(Trip.operator_id == operator_id)
        )
        if trip is None:
            raise NotFound("Trip not found")
        if trip.vehicle_id != vehicle.id:
            raise Conflict(
                "That trip belongs to a different vehicle",
                {"trip_id": str(trip_id), "trip_vehicle_id": str(trip.vehicle_id)},
            )
        if trip.status not in [str(status) for status in LIVE_TRIP_STATUSES]:
            raise Conflict(
                f"A {trip.status} trip cannot take a new rider", {"trip_id": str(trip_id)}
            )
        return trip

    async def _driver_on_duty(self, vehicle_id: uuid.UUID) -> uuid.UUID | None:
        driver_id: uuid.UUID | None = await self.session.scalar(
            select(DutySession.driver_id)
            .where(DutySession.vehicle_id == vehicle_id)
            .where(DutySession.ended_at.is_(None))
        )
        return driver_id

    async def _driver_user_id(self, driver_id: uuid.UUID) -> uuid.UUID | None:
        from app.modules.fleet.models import Driver

        user_id: uuid.UUID | None = await self.session.scalar(
            select(Driver.user_id).where(Driver.id == driver_id)
        )
        return user_id

    def _record_trip_event(
        self,
        trip: Trip,
        from_status: str | None,
        to_status: str,
        actor: Actor,
        actor_user_id: uuid.UUID | None,
        now: datetime,
        reason: str | None = None,
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
                reason=reason,
                at=now,
                data=data,
            )
        )

    async def stops_of(self, trip_id: uuid.UUID) -> list[TripStop]:
        return list(
            (
                await self.session.execute(
                    select(TripStop).where(TripStop.trip_id == trip_id).order_by(TripStop.sequence)
                )
            )
            .scalars()
            .all()
        )


# --- helpers ------------------------------------------------------------------------


def _rider_place(request: RideRequest) -> Place:
    """The rider's own end of the journey: home for `to_office`, the drop otherwise."""
    return Place(*_coords(request.location))


def _pickup_place(request: RideRequest, office: Office) -> Place:
    """Where the vehicle collects them."""
    if request.direction == str(Direction.to_office):
        return Place(*_coords(request.location))
    return Place(*_coords(office.location))


def _is_stale(position: Position | None, now: datetime, stale_after_seconds: int) -> bool:
    if position is None:
        return True
    return (now - position.recorded_at).total_seconds() > stale_after_seconds


#: Fallback speed for planning arithmetic when no matrix entry covers a pair. Matches the
#: `approx` provider's assumption (ADR-0010, OQ-22) rather than inventing a second number.
FALLBACK_SPEED_MPS = 24_000 / 3600
DETOUR_FACTOR = 1.4


def _haversine_seconds(first: Place, second: Place) -> float:
    from app.domain.gps import distance_m

    metres = distance_m(first.lat, first.lng, second.lat, second.lng) * DETOUR_FACTOR
    return metres / FALLBACK_SPEED_MPS


def _unique_places(places: list[Place]) -> list[Place]:
    seen: dict[Place, None] = {}
    for place in places:
        seen.setdefault(place, None)
    return list(seen)
