"""A cab's position reaches the riders on its trip, not only the supervisor's map.

`websocket-protocol.md` section 4 lists `vehicle.location` on `operator.{id}.vehicles` **and**
`trip.{id}`, and the employee's live-tracking screen subscribes to `trip.{id}` for it. The ingestor
only ever published the first, so a rider's map never moved (found while load testing, 2026-11-03).
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.domain.enums import Direction, VehicleType
from app.domain.state_machines import TripStatus, VehicleStatus
from app.modules.dispatch.models import Trip
from app.modules.fleet.models import Driver, Vehicle
from app.modules.tracking.service import TRIP_MAP_REFRESH_SECONDS, GpsIngestor
from tests.builders import make_client, make_office, make_operator, make_user, unique_phone

pytestmark = pytest.mark.requires_db

NOW = datetime(2026, 11, 3, 6, 0, tzinfo=UTC)


class RecordingRedis:
    def __init__(self) -> None:
        self.published: list[tuple[str, dict[str, Any]]] = []

    async def set(self, *args: Any, **kwargs: Any) -> None:
        return None

    async def publish(self, channel: str, message: str) -> None:
        self.published.append((channel, json.loads(message)))

    def channels(self) -> list[str]:
        return [channel for channel, _ in self.published]


@pytest_asyncio.fixture
async def world(db_session: AsyncSession) -> dict[str, Any]:
    operator = make_operator()
    db_session.add(operator)
    await db_session.flush()
    customer = make_client(operator.id)
    db_session.add(customer)
    await db_session.flush()
    office = make_office(operator.id, customer.id)
    db_session.add(office)
    vehicle = Vehicle(
        operator_id=operator.id,
        registration_no="UP16TC0001",
        vehicle_type=VehicleType.sedan_4,
        seat_capacity=4,
        status=VehicleStatus.on_trip,
    )
    driver_user = make_user(name="Driver", phone=unique_phone())
    db_session.add_all([vehicle, driver_user])
    await db_session.flush()
    driver = Driver(
        operator_id=operator.id,
        user_id=driver_user.id,
        name="Driver",
        phone=unique_phone(),
        default_vehicle_id=vehicle.id,
    )
    db_session.add(driver)
    await db_session.flush()
    return {
        "operator": operator,
        "office": office,
        "vehicle": vehicle,
        "driver": driver,
    }


async def add_trip(session: AsyncSession, world: dict[str, Any], status: TripStatus) -> Trip:
    trip = Trip(
        operator_id=world["operator"].id,
        vehicle_id=world["vehicle"].id,
        driver_id=world["driver"].id,
        direction=Direction.to_office,
        office_id=world["office"].id,
        status=status,
        planned_start=NOW,
        mode_used="manual",
    )
    session.add(trip)
    await session.flush()
    return trip


def ping(second: int) -> dict[str, Any]:
    return {
        "v": 1,
        "ts": (NOW + timedelta(seconds=second)).isoformat(),
        "lat": 28.57 + second * 0.0001,
        "lng": 77.32,
        "spd": 8.0,
        "acc": 5.0,
        "src": "app",
    }


async def ingest(
    session: AsyncSession,
    world: dict[str, Any],
    redis: RecordingRedis,
    clock: FakeClock,
    second: int,
) -> GpsIngestor:
    ingestor = GpsIngestor(session, clock, redis)  # type: ignore[arg-type]
    await ingestor.ingest(world["vehicle"].id, world["operator"].id, ping(second))
    return ingestor


async def test_riders_on_a_live_trip_get_the_position_on_the_trip_channel(
    db_session: AsyncSession, world: dict[str, Any]
) -> None:
    planned = await add_trip(db_session, world, TripStatus.planned)
    started = await add_trip(db_session, world, TripStatus.in_progress)
    redis = RecordingRedis()

    await ingest(db_session, world, redis, FakeClock(NOW + timedelta(seconds=10)), 5)

    operator_channel = f"operator.{world['operator'].id}.vehicles"
    assert set(redis.channels()) == {operator_channel, f"trip.{planned.id}", f"trip.{started.id}"}
    for channel, frame in redis.published:
        assert frame["event"] == "vehicle.location"
        assert frame["channel"] == channel
        assert frame["data"]["vehicle_id"] == str(world["vehicle"].id)


async def test_a_finished_trip_gets_nothing(
    db_session: AsyncSession, world: dict[str, Any]
) -> None:
    for status in (TripStatus.completed, TripStatus.cancelled, TripStatus.aborted):
        await add_trip(db_session, world, status)
    redis = RecordingRedis()

    await ingest(db_session, world, redis, FakeClock(NOW + timedelta(seconds=10)), 5)

    assert redis.channels() == [f"operator.{world['operator'].id}.vehicles"]


async def test_another_cabs_trip_gets_nothing(
    db_session: AsyncSession, world: dict[str, Any]
) -> None:
    other = Vehicle(
        operator_id=world["operator"].id,
        registration_no="UP16TC0002",
        vehicle_type=VehicleType.sedan_4,
        seat_capacity=4,
    )
    db_session.add(other)
    await db_session.flush()
    elsewhere = await add_trip(db_session, world, TripStatus.in_progress)
    elsewhere.vehicle_id = other.id
    await db_session.flush()
    redis = RecordingRedis()

    await ingest(db_session, world, redis, FakeClock(NOW + timedelta(seconds=10)), 5)

    assert redis.channels() == [f"operator.{world['operator'].id}.vehicles"]


async def test_the_trip_map_is_refreshed_on_an_interval_not_per_ping(
    db_session: AsyncSession, world: dict[str, Any]
) -> None:
    clock = FakeClock(NOW + timedelta(seconds=10))
    redis = RecordingRedis()
    ingestor = GpsIngestor(db_session, clock, redis)  # type: ignore[arg-type]

    await ingestor.ingest(world["vehicle"].id, world["operator"].id, ping(5))
    trip = await add_trip(db_session, world, TripStatus.planned)
    await ingestor.ingest(world["vehicle"].id, world["operator"].id, ping(6))
    assert f"trip.{trip.id}" not in redis.channels(), "the map is a few seconds old by design"

    clock.advance(timedelta(seconds=TRIP_MAP_REFRESH_SECONDS + 1))
    await ingestor.ingest(world["vehicle"].id, world["operator"].id, ping(7))
    assert redis.channels().count(f"trip.{trip.id}") == 1
    assert uuid.UUID(str(trip.id)) == trip.id
