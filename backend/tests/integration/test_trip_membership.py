"""Who is on a trip, answered from the database (B13).

The other half of trip-channel authorisation. `tests/unit/test_channels.py` proves the
rule given a membership; this proves the membership the rule is given is the truth.
Kept apart from the socket tests because those run the app on their own event loop.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.geo import to_point
from app.domain.enums import Direction, Role, Urgency, VehicleType
from app.domain.state_machines import RequestStatus, TripStatus, VehicleStatus
from app.modules.dispatch.models import Trip
from app.modules.fleet.models import Driver, Vehicle
from app.modules.realtime.channels import Subscriber
from app.modules.realtime.service import MembershipService
from app.modules.requests.models import RideRequest
from tests.builders import (
    make_client,
    make_employee,
    make_office,
    make_operator,
    make_user,
    unique_phone,
)

NOW = datetime(2026, 9, 25, 9, 0, tzinfo=UTC)
OFFICE = (28.5000, 77.4000)
HOME = (28.5300, 77.4000)


@pytest_asyncio.fixture
async def world(db_session: AsyncSession) -> dict[str, Any]:
    operator = make_operator()
    db_session.add(operator)
    await db_session.flush()

    customer = make_client(operator.id)
    db_session.add(customer)
    await db_session.flush()

    office = make_office(operator.id, customer.id)
    office.location = to_point(*OFFICE)
    db_session.add(office)
    await db_session.flush()

    users = {}
    for label in ("rider", "bystander", "driver", "other_driver", "supervisor"):
        user = make_user(name=label, phone=unique_phone())
        db_session.add(user)
        users[label] = user
    await db_session.flush()

    employees = {}
    for label in ("rider", "bystander"):
        employee = make_employee(operator.id, customer.id, office.id, name=label)
        employee.home_location = to_point(*HOME)
        employee.user_id = users[label].id
        db_session.add(employee)
        employees[label] = employee
    await db_session.flush()

    vehicle = Vehicle(
        operator_id=operator.id,
        registration_no="UP16MB0001",
        vehicle_type=VehicleType.sedan_4,
        seat_capacity=4,
        status=VehicleStatus.on_trip,
    )
    db_session.add(vehicle)
    await db_session.flush()

    drivers = {}
    for label in ("driver", "other_driver"):
        driver = Driver(
            operator_id=operator.id,
            user_id=users[label].id,
            name=label,
            phone=unique_phone(),
            default_vehicle_id=vehicle.id,
        )
        db_session.add(driver)
        drivers[label] = driver
    await db_session.flush()

    trip = Trip(
        operator_id=operator.id,
        vehicle_id=vehicle.id,
        driver_id=drivers["driver"].id,
        direction=Direction.to_office,
        office_id=office.id,
        status=TripStatus.planned,
        planned_start=NOW,
        mode_used="manual",
    )
    db_session.add(trip)
    await db_session.flush()

    request = RideRequest(
        operator_id=operator.id,
        client_id=customer.id,
        employee_id=employees["rider"].id,
        direction=Direction.to_office,
        office_id=office.id,
        location=employees["rider"].home_location,
        requested_time=NOW + timedelta(minutes=10),
        urgency=Urgency.medium,
        status=RequestStatus.assigned,
        trip_id=trip.id,
        expires_at=NOW + timedelta(hours=2),
    )
    db_session.add(request)
    await db_session.flush()

    return {
        "operator_id": operator.id,
        "client_id": customer.id,
        "trip_id": trip.id,
        "users": users,
        "request": request,
    }


def subscriber(world: dict[str, Any], label: str, role: Role) -> Subscriber:
    return Subscriber(
        user_id=world["users"][label].id,
        role=str(role),
        operator_id=world["operator_id"],
        client_id=world["client_id"] if role is Role.employee else None,
    )


async def membership(db_session: AsyncSession, world: dict[str, Any], who: Subscriber) -> Any:
    return await MembershipService(db_session).trip_membership(world["trip_id"], who)


async def test_the_rider_is_found(db_session: AsyncSession, world: dict[str, Any]) -> None:
    found = await membership(db_session, world, subscriber(world, "rider", Role.employee))

    assert found is not None
    assert found.is_rider is True
    assert found.rider_finished is False


async def test_another_employee_is_not_on_the_trip(
    db_session: AsyncSession, world: dict[str, Any]
) -> None:
    found = await membership(db_session, world, subscriber(world, "bystander", Role.employee))

    assert found is not None
    assert found.is_rider is False


@pytest.mark.parametrize(
    "status", [RequestStatus.dropped, RequestStatus.cancelled, RequestStatus.no_show]
)
async def test_a_finished_ride_is_marked_finished(
    db_session: AsyncSession, world: dict[str, Any], status: RequestStatus
) -> None:
    """The employee's window closes at their own drop, not at the trip's end."""
    world["request"].status = status
    await db_session.flush()

    found = await membership(db_session, world, subscriber(world, "rider", Role.employee))

    assert found is not None
    assert found.is_rider is True
    assert found.rider_finished is True


async def test_a_picked_up_rider_is_still_riding(
    db_session: AsyncSession, world: dict[str, Any]
) -> None:
    world["request"].status = RequestStatus.picked_up
    await db_session.flush()

    found = await membership(db_session, world, subscriber(world, "rider", Role.employee))

    assert found is not None
    assert found.rider_finished is False


async def test_the_assigned_driver_is_found(
    db_session: AsyncSession, world: dict[str, Any]
) -> None:
    found = await membership(db_session, world, subscriber(world, "driver", Role.driver))

    assert found is not None
    assert found.is_assigned_driver is True


async def test_another_driver_is_not(db_session: AsyncSession, world: dict[str, Any]) -> None:
    found = await membership(db_session, world, subscriber(world, "other_driver", Role.driver))

    assert found is not None
    assert found.is_assigned_driver is False


async def test_a_supervisor_is_operator_staff(
    db_session: AsyncSession, world: dict[str, Any]
) -> None:
    found = await membership(db_session, world, subscriber(world, "supervisor", Role.supervisor))

    assert found is not None
    assert found.is_operator_staff is True


async def test_another_operators_trip_is_invisible(
    db_session: AsyncSession, world: dict[str, Any]
) -> None:
    """`None`, exactly like a trip that does not exist: the id must not be a probe."""
    stranger = Subscriber(
        user_id=world["users"]["supervisor"].id,
        role=str(Role.supervisor),
        operator_id=uuid.uuid4(),
        client_id=None,
    )

    assert await membership(db_session, world, stranger) is None


async def test_an_unknown_trip_is_none(db_session: AsyncSession, world: dict[str, Any]) -> None:
    found = await MembershipService(db_session).trip_membership(
        uuid.uuid4(), subscriber(world, "supervisor", Role.supervisor)
    )
    assert found is None


async def test_a_user_with_no_employee_record_is_not_a_rider(
    db_session: AsyncSession, world: dict[str, Any]
) -> None:
    """A login that is not linked to anyone must not inherit someone else's trip."""
    orphan = make_user(name="orphan", phone=unique_phone())
    db_session.add(orphan)
    await db_session.flush()

    found = await MembershipService(db_session).trip_membership(
        world["trip_id"],
        Subscriber(
            user_id=orphan.id,
            role=str(Role.employee),
            operator_id=world["operator_id"],
            client_id=world["client_id"],
        ),
    )

    assert found is not None
    assert found.is_rider is False
