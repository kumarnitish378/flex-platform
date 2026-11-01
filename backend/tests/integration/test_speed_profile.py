"""Learning speeds from completed trips, against a database (B37, OQ-22)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.core.geo import to_point
from app.domain.geo import LatLng, haversine_km
from app.domain.speed_profile import AREA_WAY_ID, slot_of
from app.domain.state_machines import StopKind, StopStatus, TripStatus
from app.modules.dispatch.models import Trip, TripStop
from app.modules.routing.approx import ApproxConfig, ApproxRoutingProvider
from app.modules.routing.speed_models import RoadSpeedProfile, SpeedProfileState
from app.modules.routing.speed_profile import (
    PROFILE_TIMEZONE,
    LearnedSpeeds,
    SpeedProfileService,
    database_loader,
)
from tests.integration.worlds import OFFICE, build_world, near

pytestmark = pytest.mark.requires_db

# Monday 2026-10-05 09:00 IST, which is hour 9 of the week.
MONDAY_9AM = datetime(2026, 10, 5, 3, 30, tzinfo=UTC)
HOME = near(*OFFICE, north_km=-6.0)


async def completed_trip(
    session: AsyncSession,
    world: object,
    *,
    drive_minutes: float,
    finished_at: datetime,
) -> tuple[Trip, float]:
    """A finished trip: pick up at HOME, drive `drive_minutes`, arrive at the office.

    Returns the trip and the road metres `approx` would charge for that leg.
    """
    from app.domain.state_machines import RequestStatus
    from tests.integration.worlds import World, add_cab, add_employee, add_request

    assert isinstance(world, World)
    cab = await add_cab(session, world, HOME)
    request = await add_request(
        session, world, await add_employee(session, world, HOME), status=RequestStatus.dropped
    )
    trip = Trip(
        id=uuid.uuid4(),
        operator_id=world.operator_id,
        vehicle_id=cab.id,
        driver_id=(await _driver_of(session, cab.id)),
        direction=str(request.direction),
        office_id=world.office.id,
        status=str(TripStatus.completed),
        planned_start=finished_at - timedelta(hours=1),
        completed_at=finished_at,
        mode_used="manual",
    )
    session.add(trip)
    await session.flush()
    left_home = finished_at - timedelta(minutes=drive_minutes + 2)
    arrived = left_home + timedelta(minutes=drive_minutes)
    session.add_all(
        [
            TripStop(
                operator_id=world.operator_id,
                trip_id=trip.id,
                sequence=1,
                stop_type=StopKind.pickup,
                request_id=request.id,
                location=to_point(*HOME),
                status=StopStatus.done,
                arrived_at=left_home - timedelta(minutes=1),
                done_at=left_home,
            ),
            TripStop(
                operator_id=world.operator_id,
                trip_id=trip.id,
                sequence=2,
                stop_type=StopKind.drop,
                request_id=request.id,
                location=to_point(*OFFICE),
                status=StopStatus.done,
                arrived_at=arrived,
                done_at=arrived + timedelta(minutes=1),
            ),
        ]
    )
    await session.flush()
    metres = haversine_km(LatLng(*HOME), LatLng(*OFFICE)) * 1000.0 * ApproxConfig().road_factor
    return trip, metres


async def _driver_of(session: AsyncSession, vehicle_id: uuid.UUID) -> uuid.UUID:
    from app.modules.fleet.duty_models import DutySession

    driver_id = await session.scalar(
        select(DutySession.driver_id).where(DutySession.vehicle_id == vehicle_id)
    )
    assert driver_id is not None
    return driver_id


async def test_completed_trips_become_a_speed_for_their_hour_of_the_week(
    db_session: AsyncSession,
) -> None:
    world = await build_world(db_session, FakeClock(MONDAY_9AM), None)
    _, metres = await completed_trip(
        db_session, world, drive_minutes=40, finished_at=MONDAY_9AM + timedelta(minutes=50)
    )

    result = await SpeedProfileService(db_session, world.clock).learn()

    assert result.trips == 1 and result.legs == 1 and result.slots_updated == 1
    row = await db_session.get(
        RoadSpeedProfile, (AREA_WAY_ID, slot_of(MONDAY_9AM, PROFILE_TIMEZONE))
    )
    assert row is not None and row.samples == 1
    assert row.speed_kph == pytest.approx(metres / (40 * 60) * 3.6, rel=1e-6)


async def test_a_second_run_reads_nothing_twice(db_session: AsyncSession) -> None:
    world = await build_world(db_session, FakeClock(MONDAY_9AM), None)
    await completed_trip(
        db_session, world, drive_minutes=40, finished_at=MONDAY_9AM + timedelta(minutes=50)
    )
    service = SpeedProfileService(db_session, world.clock)
    await service.learn()

    again = await service.learn()

    assert again.trips == 0
    row = await db_session.get(RoadSpeedProfile, (AREA_WAY_ID, 9))
    assert row is not None and row.samples == 1, "the same trip was not folded in twice"
    state = await db_session.get(SpeedProfileState, 1)
    assert state is not None


async def test_later_trips_are_folded_into_what_was_learned(db_session: AsyncSession) -> None:
    world = await build_world(db_session, FakeClock(MONDAY_9AM), None)
    _, metres = await completed_trip(
        db_session, world, drive_minutes=40, finished_at=MONDAY_9AM + timedelta(minutes=50)
    )
    service = SpeedProfileService(db_session, world.clock)
    await service.learn()
    await completed_trip(
        db_session, world, drive_minutes=20, finished_at=MONDAY_9AM + timedelta(minutes=55)
    )

    await service.learn()

    row = await db_session.get(RoadSpeedProfile, (AREA_WAY_ID, 9))
    assert row is not None and row.samples == 2
    assert row.speed_kph == pytest.approx(2 * metres / (60 * 60) * 3.6, rel=1e-6), (
        "total distance over total time, not the mean of two speeds"
    )


async def test_the_loader_trusts_only_slots_with_enough_legs(db_session: AsyncSession) -> None:
    world = await build_world(db_session, FakeClock(MONDAY_9AM), None)
    await completed_trip(
        db_session, world, drive_minutes=40, finished_at=MONDAY_9AM + timedelta(minutes=50)
    )
    await SpeedProfileService(db_session, world.clock).learn()

    class Sessions:
        def __call__(self) -> object:
            return _Borrowed(db_session)

    few = await database_loader(Sessions(), min_samples=2)()  # type: ignore[arg-type]
    enough = await database_loader(Sessions(), min_samples=1)()  # type: ignore[arg-type]

    assert few == {} and set(enough) == {9}


class _Borrowed:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def __aenter__(self) -> AsyncSession:
        return self._session

    async def __aexit__(self, *exc_info: object) -> None:
        return None


async def test_what_was_learned_changes_what_approx_estimates(db_session: AsyncSession) -> None:
    """The acceptance criterion: a profile built from real trips moves an `approx` ETA."""
    world = await build_world(db_session, FakeClock(MONDAY_9AM), None)
    await completed_trip(
        db_session, world, drive_minutes=60, finished_at=MONDAY_9AM + timedelta(minutes=70)
    )
    await SpeedProfileService(db_session, world.clock).learn()

    class Sessions:
        def __call__(self) -> object:
            return _Borrowed(db_session)

    learned = LearnedSpeeds(world.clock, database_loader(Sessions(), 1))  # type: ignore[arg-type]
    origin, destination = LatLng(*HOME), LatLng(*OFFICE)

    before = await ApproxRoutingProvider(world.clock, ApproxConfig()).route(origin, destination)
    after = await ApproxRoutingProvider(world.clock, ApproxConfig(), learned).route(
        origin, destination
    )

    # The drivers took an hour over this leg at 09:00 on a Monday; the constant said less.
    assert after.duration_seconds == pytest.approx(60 * 60, rel=0.02)
    assert abs(after.duration_seconds - before.duration_seconds) > 5 * 60
