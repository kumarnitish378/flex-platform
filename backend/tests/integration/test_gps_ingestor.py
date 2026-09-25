"""GPS ingestion against a real database (B12).

Acceptance: invalid pings dropped, out-of-order handled, batch payloads persisted, and
200 vehicles at a 5-second interval processed with lag under 2 seconds.
"""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.core.security import create_access_token
from app.core.settings import Settings
from app.domain.enums import Role, VehicleType
from app.domain.gps import MAX_BATCH
from app.main import create_app
from app.modules.fleet.duty_models import DutySession
from app.modules.fleet.models import Driver, Vehicle
from app.modules.tracking.ingestor import parse_topic
from app.modules.tracking.models import LocationPing
from app.modules.tracking.service import FLUSH_MAX_ROWS, GpsIngestor
from tests.builders import make_operator, make_user, make_user_role, unique_phone
from tests.fakes import FakeRedis

NOW = datetime(2026, 9, 24, 4, 30, tzinfo=UTC)
JWT_SECRET = "gps-tests-secret-0123456789abcdefghij"


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest_asyncio.fixture
async def world(db_session: AsyncSession) -> dict[str, uuid.UUID]:
    operator = make_operator()
    db_session.add(operator)
    await db_session.flush()

    vehicle = Vehicle(
        operator_id=operator.id,
        registration_no="UP16AB1234",
        vehicle_type=VehicleType.sedan_4,
        seat_capacity=4,
    )
    db_session.add(vehicle)
    await db_session.flush()
    return {"operator_id": operator.id, "vehicle_id": vehicle.id}


def ping(offset: float = 0, lat: float = 28.5, lng: float = 77.3, **extra: Any) -> dict[str, Any]:
    body = {
        "v": 1,
        "ts": (NOW + timedelta(seconds=offset)).isoformat().replace("+00:00", "Z"),
        "lat": lat,
        "lng": lng,
        "spd": 8.0,
        "hdg": 90,
        "acc": 5.0,
        "bat": 80,
        "src": "sim",
    }
    body.update(extra)
    return body


# --- persistence ----------------------------------------------------------------------


async def test_a_ping_is_persisted(
    db_session: AsyncSession, clock: FakeClock, world: dict[str, uuid.UUID]
) -> None:
    ingestor = GpsIngestor(db_session, clock)
    result = await ingestor.ingest(world["vehicle_id"], world["operator_id"], ping())
    await ingestor.flush()

    assert result.accepted == 1
    row = (await db_session.execute(select(LocationPing))).scalars().one()
    assert row.vehicle_id == world["vehicle_id"]
    assert row.speed_mps == 8.0
    assert row.source == "sim"
    assert row.received_at == NOW


async def test_writes_are_buffered_until_flushed(
    db_session: AsyncSession, clock: FakeClock, world: dict[str, uuid.UUID]
) -> None:
    """One INSERT per ping would spend the database on round trips."""
    ingestor = GpsIngestor(db_session, clock)
    await ingestor.ingest(world["vehicle_id"], world["operator_id"], ping())

    assert ingestor.pending == 1
    assert await db_session.scalar(select(func.count()).select_from(LocationPing)) == 0

    await ingestor.flush()
    assert await db_session.scalar(select(func.count()).select_from(LocationPing)) == 1


async def test_the_buffer_flushes_on_the_interval(
    db_session: AsyncSession, clock: FakeClock, world: dict[str, uuid.UUID]
) -> None:
    ingestor = GpsIngestor(db_session, clock)
    await ingestor.ingest(world["vehicle_id"], world["operator_id"], ping())

    clock.advance(timedelta(seconds=6))
    await ingestor.ingest(world["vehicle_id"], world["operator_id"], ping(offset=6))

    assert ingestor.pending == 0
    assert await db_session.scalar(select(func.count()).select_from(LocationPing)) == 2


async def test_the_buffer_flushes_when_full(
    db_session: AsyncSession, clock: FakeClock, world: dict[str, uuid.UUID]
) -> None:
    """A quiet clock must not let the buffer grow without bound.

    Filled with two protocol-legal batches: one message may carry at most MAX_BATCH
    pings, which is half the flush threshold.
    """
    ingestor = GpsIngestor(db_session, clock)
    for half in range(2):
        batch = {
            "batch": [
                ping(offset=(half * MAX_BATCH + i) * 0.001, lat=28.5) for i in range(MAX_BATCH)
            ]
        }
        await ingestor.ingest(world["vehicle_id"], world["operator_id"], batch)

    assert 2 * MAX_BATCH >= FLUSH_MAX_ROWS, "the threshold must be reachable in two batches"
    assert ingestor.pending == 0
    assert await db_session.scalar(select(func.count()).select_from(LocationPing)) == 2 * MAX_BATCH


async def test_a_batch_payload_is_persisted(
    db_session: AsyncSession, clock: FakeClock, world: dict[str, uuid.UUID]
) -> None:
    ingestor = GpsIngestor(db_session, clock)
    batch = {"batch": [ping(offset=0), ping(offset=5), ping(offset=10)]}
    result = await ingestor.ingest(world["vehicle_id"], world["operator_id"], batch)
    await ingestor.flush()

    assert result.accepted == 3
    assert await db_session.scalar(select(func.count()).select_from(LocationPing)) == 3


async def test_the_ping_lands_in_the_right_partition(
    db_session: AsyncSession, clock: FakeClock, world: dict[str, uuid.UUID]
) -> None:
    """Partitioning is invisible to the query but must actually route the row."""
    from sqlalchemy import text

    ingestor = GpsIngestor(db_session, clock)
    await ingestor.ingest(world["vehicle_id"], world["operator_id"], ping())
    await ingestor.flush()

    partition = await db_session.scalar(
        text("SELECT tableoid::regclass::text FROM location_ping LIMIT 1")
    )
    assert partition == "location_ping_2026_09"


# --- rejection ------------------------------------------------------------------------


async def test_an_inaccurate_ping_is_dropped(
    db_session: AsyncSession, clock: FakeClock, world: dict[str, uuid.UUID]
) -> None:
    ingestor = GpsIngestor(db_session, clock)
    result = await ingestor.ingest(world["vehicle_id"], world["operator_id"], ping(acc=500))
    await ingestor.flush()

    assert result.accepted == 0
    assert result.reasons == {"inaccurate": 1}
    assert await db_session.scalar(select(func.count()).select_from(LocationPing)) == 0


async def test_an_impossible_jump_is_dropped(
    db_session: AsyncSession, clock: FakeClock, world: dict[str, uuid.UUID]
) -> None:
    ingestor = GpsIngestor(db_session, clock)
    await ingestor.ingest(world["vehicle_id"], world["operator_id"], ping(lat=28.50))
    result = await ingestor.ingest(
        world["vehicle_id"], world["operator_id"], ping(offset=5, lat=28.90)
    )
    await ingestor.flush()

    assert result.accepted == 0
    assert result.reasons == {"impossible_jump": 1}
    assert await db_session.scalar(select(func.count()).select_from(LocationPing)) == 1


async def test_good_pings_survive_a_bad_neighbour(
    db_session: AsyncSession, clock: FakeClock, world: dict[str, uuid.UUID]
) -> None:
    ingestor = GpsIngestor(db_session, clock)
    batch = {"batch": [ping(offset=0), {"v": 1, "ts": "broken"}, ping(offset=5)]}
    result = await ingestor.ingest(world["vehicle_id"], world["operator_id"], batch)
    await ingestor.flush()

    assert result.accepted == 2
    assert result.dropped == 1


# --- out-of-order handling ------------------------------------------------------------


async def test_an_out_of_order_ping_is_stored_but_does_not_move_the_marker(
    db_session: AsyncSession, clock: FakeClock, world: dict[str, uuid.UUID]
) -> None:
    """mqtt-topics.md: stored, but the live marker must not go backwards."""
    redis = FakeRedis(clock)
    ingestor = GpsIngestor(db_session, clock, redis)

    await ingestor.ingest(world["vehicle_id"], world["operator_id"], ping(offset=60, lat=28.55))
    late = await ingestor.ingest(
        world["vehicle_id"], world["operator_id"], ping(offset=10, lat=28.50)
    )
    await ingestor.flush()

    assert late.accepted == 1
    assert late.latest_moved is False
    assert await db_session.scalar(select(func.count()).select_from(LocationPing)) == 2

    latest = await ingestor.latest_position(world["vehicle_id"])
    assert latest is not None
    assert latest["lat"] == 28.55, "the marker was dragged back by a late ping"


async def test_a_reconnect_batch_is_processed_oldest_first(
    db_session: AsyncSession, clock: FakeClock, world: dict[str, uuid.UUID]
) -> None:
    """Otherwise the batch trips the jump check against its own newest ping."""
    redis = FakeRedis(clock)
    ingestor = GpsIngestor(db_session, clock, redis)

    batch = {
        "batch": [
            ping(offset=30, lat=28.5030),
            ping(offset=10, lat=28.5010),
            ping(offset=20, lat=28.5020),
        ]
    }
    result = await ingestor.ingest(world["vehicle_id"], world["operator_id"], batch)
    await ingestor.flush()

    assert result.accepted == 3
    latest = await ingestor.latest_position(world["vehicle_id"])
    assert latest is not None
    assert latest["lat"] == 28.5030


# --- Redis ----------------------------------------------------------------------------


async def test_the_latest_position_is_cached(
    db_session: AsyncSession, clock: FakeClock, world: dict[str, uuid.UUID]
) -> None:
    redis = FakeRedis(clock)
    ingestor = GpsIngestor(db_session, clock, redis)
    await ingestor.ingest(world["vehicle_id"], world["operator_id"], ping(lat=28.51))

    stored = await redis.get(f"veh:{world['vehicle_id']}:pos")
    assert stored is not None
    assert json.loads(stored)["lat"] == 28.51


async def test_the_cached_position_expires(
    db_session: AsyncSession, clock: FakeClock, world: dict[str, uuid.UUID]
) -> None:
    """A 10-minute TTL means a silent vehicle disappears from the live map by itself."""
    redis = FakeRedis(clock)
    ingestor = GpsIngestor(db_session, clock, redis)
    await ingestor.ingest(world["vehicle_id"], world["operator_id"], ping())

    clock.advance(timedelta(minutes=11))
    assert await ingestor.latest_position(world["vehicle_id"]) is None


async def test_ingestion_survives_redis_being_down(
    db_session: AsyncSession, clock: FakeClock, world: dict[str, uuid.UUID]
) -> None:
    """A stale map is survivable; a lost ping is not."""
    redis = FakeRedis(clock, fail_on={"set"})
    ingestor = GpsIngestor(db_session, clock, redis)

    result = await ingestor.ingest(world["vehicle_id"], world["operator_id"], ping())
    await ingestor.flush()

    assert result.accepted == 1
    assert await db_session.scalar(select(func.count()).select_from(LocationPing)) == 1


# --- topics ---------------------------------------------------------------------------


def test_the_topic_parser_matches_the_spec() -> None:
    operator, vehicle = uuid.uuid4(), uuid.uuid4()
    assert parse_topic(f"sc/v1/op/{operator}/veh/{vehicle}/gps") == (operator, vehicle)


@pytest.mark.parametrize(
    "topic",
    [
        "sc/v1/op/not-a-uuid/veh/also-not/gps",
        "sc/v2/op/x/veh/y/gps",
        "sc/v1/op/x/gps",
        "",
        "#",
    ],
)
def test_a_bad_topic_is_refused(topic: str) -> None:
    assert parse_topic(topic) is None


# --- stale detection ------------------------------------------------------------------


async def test_an_on_duty_vehicle_with_no_pings_is_stale(
    db_session: AsyncSession, clock: FakeClock, world: dict[str, uuid.UUID]
) -> None:
    driver = Driver(operator_id=world["operator_id"], name="Ravi", phone=unique_phone())
    db_session.add(driver)
    await db_session.flush()
    db_session.add(
        DutySession(
            operator_id=world["operator_id"],
            driver_id=driver.id,
            vehicle_id=world["vehicle_id"],
            started_at=NOW,
        )
    )
    await db_session.flush()

    ingestor = GpsIngestor(db_session, clock)
    assert await ingestor.stale_vehicles(world["operator_id"], 60) == [world["vehicle_id"]]


async def test_a_recently_pinging_vehicle_is_not_stale(
    db_session: AsyncSession, clock: FakeClock, world: dict[str, uuid.UUID]
) -> None:
    driver = Driver(operator_id=world["operator_id"], name="Ravi", phone=unique_phone())
    db_session.add(driver)
    await db_session.flush()
    db_session.add(
        DutySession(
            operator_id=world["operator_id"],
            driver_id=driver.id,
            vehicle_id=world["vehicle_id"],
            started_at=NOW,
        )
    )
    await db_session.flush()

    ingestor = GpsIngestor(db_session, clock)
    await ingestor.ingest(world["vehicle_id"], world["operator_id"], ping())
    await ingestor.flush()

    assert await ingestor.stale_vehicles(world["operator_id"], 60) == []


async def test_a_vehicle_goes_stale_after_the_threshold(
    db_session: AsyncSession, clock: FakeClock, world: dict[str, uuid.UUID]
) -> None:
    driver = Driver(operator_id=world["operator_id"], name="Ravi", phone=unique_phone())
    db_session.add(driver)
    await db_session.flush()
    db_session.add(
        DutySession(
            operator_id=world["operator_id"],
            driver_id=driver.id,
            vehicle_id=world["vehicle_id"],
            started_at=NOW,
        )
    )
    await db_session.flush()

    ingestor = GpsIngestor(db_session, clock)
    await ingestor.ingest(world["vehicle_id"], world["operator_id"], ping())
    await ingestor.flush()

    clock.advance(timedelta(seconds=61))
    assert await ingestor.stale_vehicles(world["operator_id"], 60) == [world["vehicle_id"]]


async def test_an_off_duty_vehicle_is_never_stale(
    db_session: AsyncSession, clock: FakeClock, world: dict[str, uuid.UUID]
) -> None:
    """Off duty means no GPS by design, not a fault to alert on."""
    ingestor = GpsIngestor(db_session, clock)
    assert await ingestor.stale_vehicles(world["operator_id"], 60) == []


# --- throughput -----------------------------------------------------------------------


@pytest.mark.slow
async def test_two_hundred_vehicles_at_five_seconds(
    db_session: AsyncSession, clock: FakeClock, world: dict[str, uuid.UUID]
) -> None:
    """B12 acceptance: 200 vehicles at a 5 s interval, processed with lag under 2 s.

    One cycle is 200 pings, which the fleet produces every 5 seconds. Processing it must
    take well under that, or the ingestor falls behind and never catches up.
    """
    vehicles = []
    for index in range(200):
        vehicle = Vehicle(
            operator_id=world["operator_id"],
            registration_no=f"SIM{index:05d}",
            vehicle_type=VehicleType.sedan_4,
            seat_capacity=4,
        )
        db_session.add(vehicle)
        vehicles.append(vehicle)
    await db_session.flush()

    ingestor = GpsIngestor(db_session, clock)

    started = time.perf_counter()
    for cycle in range(3):
        for index, vehicle in enumerate(vehicles):
            await ingestor.ingest(
                vehicle.id,
                world["operator_id"],
                ping(offset=cycle * 5, lat=28.5 + index * 0.0001),
            )
        clock.advance(timedelta(seconds=5))
    await ingestor.flush()
    elapsed = time.perf_counter() - started

    stored = await db_session.scalar(select(func.count()).select_from(LocationPing))
    assert stored == 600, "every ping must be persisted"

    per_cycle = elapsed / 3
    assert per_cycle < 2.0, (
        f"one 200-vehicle cycle took {per_cycle:.2f}s; the fleet produces one every 5s, "
        "so anything approaching that means the ingestor falls behind"
    )


# --- the HTTPS fallback ---------------------------------------------------------------


class _NoClose:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def __aenter__(self) -> AsyncSession:
        return self._session

    async def __aexit__(self, *exc_info: object) -> None:
        return None


@pytest_asyncio.fixture
async def app(
    database_ready: bool, db_session: AsyncSession, clock: FakeClock
) -> AsyncIterator[FastAPI]:
    settings = Settings(
        app_env="dev",
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        jwt_secret=JWT_SECRET,
    )
    application = create_app(settings=settings, clock=clock)

    class _Factory:
        def __call__(self) -> object:
            return _NoClose(db_session)

    application.state.session_factory = _Factory()
    yield application


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as c:
        yield c


@pytest_asyncio.fixture
async def on_duty_driver(
    db_session: AsyncSession, clock: FakeClock, world: dict[str, uuid.UUID]
) -> dict[str, str]:
    user = make_user(phone=unique_phone())
    db_session.add(user)
    await db_session.flush()
    db_session.add(make_user_role(user.id, Role.driver, operator_id=world["operator_id"]))

    driver = Driver(
        operator_id=world["operator_id"],
        user_id=user.id,
        name="Ravi",
        phone=unique_phone(),
        default_vehicle_id=world["vehicle_id"],
    )
    db_session.add(driver)
    await db_session.flush()
    db_session.add(
        DutySession(
            operator_id=world["operator_id"],
            driver_id=driver.id,
            vehicle_id=world["vehicle_id"],
            started_at=NOW,
        )
    )
    await db_session.flush()

    token, _ = create_access_token(
        user_id=user.id,
        role=str(Role.driver),
        secret=JWT_SECRET,
        clock=clock,
        ttl_seconds=900,
        operator_id=world["operator_id"],
    )
    return {"Authorization": f"Bearer {token}"}


def http_ping(offset: float = 0, lat: float = 28.5) -> dict[str, object]:
    return {
        "ts": (NOW + timedelta(seconds=offset)).isoformat(),
        "lat": lat,
        "lng": 77.3,
        "speed_mps": 8.0,
        "accuracy_m": 5.0,
    }


async def test_the_https_fallback_persists_a_batch(
    client: AsyncClient, on_duty_driver: dict[str, str], db_session: AsyncSession
) -> None:
    response = await client.post(
        "/driver/location",
        json=[http_ping(0), http_ping(5, 28.5005)],
        headers=on_duty_driver,
    )
    assert response.status_code == 202
    assert await db_session.scalar(select(func.count()).select_from(LocationPing)) == 2


async def test_the_fallback_applies_the_same_rules(
    client: AsyncClient, on_duty_driver: dict[str, str], db_session: AsyncSession
) -> None:
    """A driver on a bad connection must not get different validation."""
    bad = {**http_ping(), "accuracy_m": 500.0}
    response = await client.post("/driver/location", json=[bad], headers=on_duty_driver)

    assert response.status_code == 202, "a dropped ping is not a client error"
    assert await db_session.scalar(select(func.count()).select_from(LocationPing)) == 0


async def test_the_fallback_needs_an_open_duty_session(
    client: AsyncClient, world: dict[str, uuid.UUID], clock: FakeClock, db_session: AsyncSession
) -> None:
    """non-functional.md: driver GPS is collected only while on duty."""
    user = make_user(phone=unique_phone())
    db_session.add(user)
    await db_session.flush()
    db_session.add(make_user_role(user.id, Role.driver, operator_id=world["operator_id"]))
    db_session.add(
        Driver(
            operator_id=world["operator_id"],
            user_id=user.id,
            name="Idle",
            phone=unique_phone(),
        )
    )
    await db_session.flush()

    token, _ = create_access_token(
        user_id=user.id,
        role=str(Role.driver),
        secret=JWT_SECRET,
        clock=clock,
        ttl_seconds=900,
        operator_id=world["operator_id"],
    )
    response = await client.post(
        "/driver/location",
        json=[http_ping()],
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


async def test_the_fallback_uses_the_duty_vehicle_not_the_body(
    client: AsyncClient,
    on_duty_driver: dict[str, str],
    db_session: AsyncSession,
    world: dict[str, uuid.UUID],
) -> None:
    """A driver must not be able to post positions for a cab they are not driving."""
    await client.post("/driver/location", json=[http_ping()], headers=on_duty_driver)
    row = (await db_session.execute(select(LocationPing))).scalars().one()
    assert row.vehicle_id == world["vehicle_id"]


async def test_the_fallback_rejects_an_oversized_batch(
    client: AsyncClient, on_duty_driver: dict[str, str]
) -> None:
    response = await client.post(
        "/driver/location", json=[http_ping()] * 501, headers=on_duty_driver
    )
    assert response.status_code == 422


async def test_the_fallback_requires_authentication(client: AsyncClient) -> None:
    assert (await client.post("/driver/location", json=[http_ping()])).status_code == 401


async def test_a_supervisor_cannot_post_locations(
    client: AsyncClient, world: dict[str, uuid.UUID], clock: FakeClock, db_session: AsyncSession
) -> None:
    user = make_user(phone=unique_phone())
    db_session.add(user)
    await db_session.flush()
    db_session.add(make_user_role(user.id, Role.supervisor, operator_id=world["operator_id"]))
    await db_session.flush()

    token, _ = create_access_token(
        user_id=user.id,
        role=str(Role.supervisor),
        secret=JWT_SECRET,
        clock=clock,
        ttl_seconds=900,
        operator_id=world["operator_id"],
    )
    response = await client.post(
        "/driver/location", json=[http_ping()], headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
