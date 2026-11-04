"""Builders for report and billing tests: finished rides with exactly the numbers a test states.

The reports are computed from rows, so a test of them is only as good as its fixture. These
write the rows directly (a request, its trip, its stops and events) rather than driving the
dispatch service, because a report test must be able to say "this trip drove 20 km and
carried two people" without first persuading a router to produce that.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.geo import to_point
from app.domain.enums import ActorType, Direction
from app.domain.state_machines import RequestStatus, StopKind, StopStatus, TripStatus
from app.modules.dispatch.models import Trip, TripStop
from app.modules.fleet.models import Vehicle
from app.modules.people.models import Employee
from app.modules.requests.models import RideRequest, RideRequestEvent
from tests.integration.worlds import OFFICE, World, add_cab, add_employee, near


async def make_trip(
    session: AsyncSession,
    world: World,
    vehicle: Vehicle,
    *,
    when: datetime,
    km: float | None,
    mode: str = "manual",
) -> Trip:
    from sqlalchemy import select

    from app.modules.fleet.duty_models import DutySession

    driver_id = await session.scalar(
        select(DutySession.driver_id).where(DutySession.vehicle_id == vehicle.id)
    )
    assert driver_id is not None
    trip = Trip(
        id=uuid.uuid4(),
        operator_id=world.operator_id,
        vehicle_id=vehicle.id,
        driver_id=driver_id,
        direction=str(Direction.to_office),
        office_id=world.office.id,
        status=str(TripStatus.completed),
        planned_start=when - timedelta(minutes=50),
        started_at=when - timedelta(minutes=40),
        completed_at=when,
        actual_distance_m=None if km is None else km * 1000.0,
        mode_used=mode,
    )
    session.add(trip)
    await session.flush()
    return trip


async def make_ride(
    session: AsyncSession,
    world: World,
    employee: Employee,
    *,
    asked_at: datetime,
    status: RequestStatus,
    trip: Trip | None = None,
    wait_minutes: float | None = None,
    assigned_by: ActorType | None = None,
    sequence: int = 1,
) -> RideRequest:
    """One request in a state, with the stops and events that state implies."""
    request = RideRequest(
        id=uuid.uuid4(),
        operator_id=world.operator_id,
        client_id=employee.client_id,
        employee_id=employee.id,
        direction=str(Direction.to_office),
        office_id=employee.office_id,
        location=employee.home_location,
        requested_time=asked_at,
        urgency="medium",
        status=str(status),
        queued_at=asked_at,
        expires_at=asked_at + timedelta(hours=2),
        trip_id=trip.id if trip else None,
    )
    session.add(request)
    await session.flush()
    if trip is not None:
        picked = wait_minutes is not None and status in (
            RequestStatus.dropped,
            RequestStatus.picked_up,
        )
        pickup_at = asked_at + timedelta(minutes=wait_minutes or 0)
        session.add_all(
            [
                TripStop(
                    operator_id=world.operator_id,
                    trip_id=trip.id,
                    sequence=sequence * 2 - 1,
                    stop_type=StopKind.pickup,
                    request_id=request.id,
                    location=employee.home_location,
                    status=StopStatus.done if picked else StopStatus.skipped,
                    arrived_at=pickup_at if picked else None,
                    done_at=pickup_at if picked else None,
                ),
                TripStop(
                    operator_id=world.operator_id,
                    trip_id=trip.id,
                    sequence=sequence * 2,
                    stop_type=StopKind.drop,
                    request_id=request.id,
                    location=to_point(*OFFICE),
                    status=StopStatus.done if picked else StopStatus.skipped,
                    done_at=(pickup_at + timedelta(minutes=30)) if picked else None,
                ),
            ]
        )
    if assigned_by is not None:
        session.add(
            RideRequestEvent(
                operator_id=world.operator_id,
                request_id=request.id,
                from_status=str(RequestStatus.queued),
                to_status=str(RequestStatus.assigned),
                actor_type=str(assigned_by),
                at=asked_at + timedelta(minutes=1),
            )
        )
    await session.flush()
    return request


async def employee_at(session: AsyncSession, world: World, name: str, **kwargs: object) -> Employee:
    return await add_employee(session, world, near(*OFFICE, north_km=-5.0), name, **kwargs)  # type: ignore[arg-type]


async def cab(session: AsyncSession, world: World) -> Vehicle:
    return await add_cab(session, world, OFFICE)
