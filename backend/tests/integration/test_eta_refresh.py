"""The stop-ETA refresh job (B15, `architecture.md` section 3.2 step 4).

Driven by a FakeClock, never by sleeping: the job does work that is *due*, so advancing
simulated time refreshes ETAs exactly as wall-clock time would.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.core.events import RecordingEventPublisher
from app.core.geo import to_point
from app.domain.enums import Direction, Urgency, VehicleType
from app.domain.state_machines import RequestStatus, StopKind, StopStatus, TripStatus, VehicleStatus
from app.modules.dispatch.eta_refresh import REFRESH_INTERVAL, EtaRefresher
from app.modules.dispatch.models import Trip, TripStop
from app.modules.fleet.models import Driver, Vehicle
from app.modules.requests.models import RideRequest
from app.modules.routing.approx import ApproxRoutingProvider
from app.modules.routing.service import EtaService
from app.modules.tracking.models import LocationPing
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
HOME = (28.5600, 77.4000)
PARKED = (28.5700, 77.4000)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest.fixture
def events() -> RecordingEventPublisher:
    return RecordingEventPublisher()


def refresher(
    session: AsyncSession, clock: FakeClock, events: RecordingEventPublisher
) -> EtaRefresher:
    return EtaRefresher(session, clock, EtaService(ApproxRoutingProvider(clock), clock), events)


@pytest_asyncio.fixture
async def world(db_session: AsyncSession) -> dict[str, Any]:
    """One in-progress trip with a pickup and a drop, and a cab that has pinged."""
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

    employee = make_employee(operator.id, customer.id, office.id)
    employee.home_location = to_point(*HOME)
    db_session.add(employee)
    await db_session.flush()

    user = make_user(name="Ravi", phone=unique_phone())
    db_session.add(user)
    await db_session.flush()

    vehicle = Vehicle(
        operator_id=operator.id,
        registration_no="UP16ET0001",
        vehicle_type=VehicleType.sedan_4,
        seat_capacity=4,
        status=VehicleStatus.on_trip,
    )
    db_session.add(vehicle)
    await db_session.flush()

    driver = Driver(
        operator_id=operator.id,
        user_id=user.id,
        name="Ravi",
        phone=unique_phone(),
        default_vehicle_id=vehicle.id,
    )
    db_session.add(driver)
    await db_session.flush()

    db_session.add(
        LocationPing(
            operator_id=operator.id,
            vehicle_id=vehicle.id,
            recorded_at=NOW - timedelta(seconds=5),
            received_at=NOW - timedelta(seconds=5),
            location=to_point(*PARKED),
            source="sim",
        )
    )

    trip = Trip(
        operator_id=operator.id,
        vehicle_id=vehicle.id,
        driver_id=driver.id,
        direction=Direction.to_office,
        office_id=office.id,
        status=TripStatus.in_progress,
        planned_start=NOW,
        started_at=NOW,
        mode_used="manual",
    )
    db_session.add(trip)
    await db_session.flush()

    request = RideRequest(
        operator_id=operator.id,
        client_id=customer.id,
        employee_id=employee.id,
        direction=Direction.to_office,
        office_id=office.id,
        location=employee.home_location,
        requested_time=NOW + timedelta(minutes=15),
        urgency=Urgency.medium,
        status=RequestStatus.assigned,
        trip_id=trip.id,
        expires_at=NOW + timedelta(hours=2),
    )
    db_session.add(request)
    await db_session.flush()

    pickup = TripStop(
        operator_id=operator.id,
        trip_id=trip.id,
        sequence=1,
        stop_type=StopKind.pickup,
        request_id=request.id,
        location=employee.home_location,
        status=StopStatus.en_route,
    )
    drop = TripStop(
        operator_id=operator.id,
        trip_id=trip.id,
        sequence=2,
        stop_type=StopKind.drop,
        request_id=request.id,
        location=office.location,
        status=StopStatus.pending,
    )
    db_session.add_all([pickup, drop])
    await db_session.flush()

    return {
        "operator_id": operator.id,
        "trip": trip,
        "vehicle": vehicle,
        "pickup_id": pickup.id,
        "drop_id": drop.id,
    }


async def stop_of(session: AsyncSession, stop_id: uuid.UUID) -> TripStop:
    return (await session.execute(select(TripStop).where(TripStop.id == stop_id))).scalars().one()


# --- refreshing ---------------------------------------------------------------------


async def test_a_moving_trip_gets_its_etas(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    events: RecordingEventPublisher,
) -> None:
    result = await refresher(db_session, clock, events).refresh_due()

    assert result.trips == 1
    assert result.stops == 2
    pickup = await stop_of(db_session, world["pickup_id"])
    assert pickup.latest_eta is not None
    assert pickup.latest_eta > NOW


async def test_later_stops_wait_behind_the_earlier_ones(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    events: RecordingEventPublisher,
) -> None:
    """A rider three stops down must see the queue ahead of them, not a direct time."""
    await refresher(db_session, clock, events).refresh_due()

    pickup = await stop_of(db_session, world["pickup_id"])
    drop = await stop_of(db_session, world["drop_id"])
    assert pickup.latest_eta is not None
    assert drop.latest_eta is not None
    assert drop.latest_eta > pickup.latest_eta


async def test_an_approximate_eta_is_flagged(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    events: RecordingEventPublisher,
) -> None:
    """ADR-0010: a straight-line estimate must never be shown as a routed one."""
    result = await refresher(db_session, clock, events).refresh_due()

    assert result.approximate == 2
    assert (await stop_of(db_session, world["pickup_id"])).eta_approximate is True


async def test_the_refresh_is_announced(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    events: RecordingEventPublisher,
) -> None:
    await refresher(db_session, clock, events).refresh_due()

    assert events.names().count("stop.eta") == 2
    assert f"trip.{world['trip'].id}" in events.channels_for("stop.eta")


# --- doing only what is due -------------------------------------------------------------


async def test_a_second_run_straight_away_does_nothing(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    events: RecordingEventPublisher,
) -> None:
    """Recomputing every few seconds would spend the shared OSRM budget for nothing."""
    job = refresher(db_session, clock, events)
    await job.refresh_due()

    assert (await job.refresh_due()).stops == 0


async def test_the_interval_makes_it_due_again(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    events: RecordingEventPublisher,
) -> None:
    job = refresher(db_session, clock, events)
    await job.refresh_due()

    clock.advance(REFRESH_INTERVAL)
    assert (await job.refresh_due()).stops == 2


async def test_a_trip_that_has_not_started_is_left_alone(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    events: RecordingEventPublisher,
) -> None:
    """A cab that has not set off has nothing to estimate from."""
    world["trip"].status = TripStatus.planned
    await db_session.flush()

    assert (await refresher(db_session, clock, events).refresh_due()).stops == 0


async def test_finished_stops_are_not_re_estimated(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    events: RecordingEventPublisher,
) -> None:
    pickup = await stop_of(db_session, world["pickup_id"])
    pickup.status = StopStatus.done
    await db_session.flush()

    assert (await refresher(db_session, clock, events).refresh_due()).stops == 1


async def test_a_completed_trip_is_ignored(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    events: RecordingEventPublisher,
) -> None:
    world["trip"].status = TripStatus.completed
    await db_session.flush()

    assert (await refresher(db_session, clock, events).refresh_due()).trips == 0


async def test_a_vehicle_with_no_recent_ping_keeps_its_last_eta(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    events: RecordingEventPublisher,
) -> None:
    """An invented ETA is worse than a stale one; the stale-GPS alert covers the gap."""
    job = refresher(db_session, clock, events)
    await job.refresh_due()
    before = (await stop_of(db_session, world["pickup_id"])).latest_eta

    clock.advance(timedelta(hours=3))
    assert (await job.refresh_due()).stops == 0
    assert (await stop_of(db_session, world["pickup_id"])).latest_eta == before


async def test_another_operators_trips_can_be_excluded(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    events: RecordingEventPublisher,
) -> None:
    result = await refresher(db_session, clock, events).refresh_due(operator_id=uuid.uuid4())
    assert result.stops == 0
