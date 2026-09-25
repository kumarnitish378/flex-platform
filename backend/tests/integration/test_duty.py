"""Going on and off duty, and the credentials it issues (B11, DRV-02)."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.core.security import create_access_token
from app.core.settings import Settings
from app.domain.enums import Role, VehicleType
from app.domain.mqtt_credentials import verify_password
from app.domain.state_machines import VehicleStatus
from app.main import create_app
from app.modules.fleet.duty_models import DutySession
from app.modules.fleet.models import Driver, Vehicle
from tests.builders import make_operator, make_user, make_user_role, unique_phone

NOW = datetime(2026, 9, 24, 4, 30, tzinfo=UTC)
JWT_SECRET = "duty-tests-secret-0123456789abcdefghi"


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest_asyncio.fixture
async def world(db_session: AsyncSession) -> dict[str, uuid.UUID]:
    """An operator with one driver linked to a login, and their default vehicle."""
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

    user = make_user(name="Ravi", phone=unique_phone())
    db_session.add(user)
    await db_session.flush()
    db_session.add(make_user_role(user.id, Role.driver, operator_id=operator.id))

    driver = Driver(
        operator_id=operator.id,
        user_id=user.id,
        name="Ravi",
        phone=unique_phone(),
        default_vehicle_id=vehicle.id,
    )
    db_session.add(driver)
    await db_session.flush()

    return {
        "operator_id": operator.id,
        "vehicle_id": vehicle.id,
        "driver_id": driver.id,
        "user_id": user.id,
    }


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


class _NoClose:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def __aenter__(self) -> AsyncSession:
        return self._session

    async def __aexit__(self, *exc_info: object) -> None:
        return None


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as c:
        yield c


@pytest.fixture
def driver_headers(world: dict[str, uuid.UUID], clock: FakeClock) -> dict[str, str]:
    token, _ = create_access_token(
        user_id=world["user_id"],
        role=str(Role.driver),
        secret=JWT_SECRET,
        clock=clock,
        ttl_seconds=900,
        operator_id=world["operator_id"],
    )
    return {"Authorization": f"Bearer {token}"}


# --- going on duty -----------------------------------------------------------------


async def test_on_duty_returns_credentials(
    client: AsyncClient, driver_headers: dict[str, str], world: dict[str, uuid.UUID]
) -> None:
    """B11 acceptance: on-duty returns credentials."""
    response = await client.post("/driver/duty", json={"on_duty": True}, headers=driver_headers)
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["on_duty"] is True
    assert body["vehicle_id"] == str(world["vehicle_id"])

    mqtt = body["mqtt"]
    assert mqtt["username"] == f"veh-{world['vehicle_id']}"
    assert mqtt["password"]
    assert mqtt["topic_prefix"] == (f"sc/v1/op/{world['operator_id']}/veh/{world['vehicle_id']}")
    assert mqtt["port"] == 1883


async def test_the_password_is_stored_only_as_a_hash(
    client: AsyncClient, driver_headers: dict[str, str], db_session: AsyncSession
) -> None:
    body = (
        await client.post("/driver/duty", json={"on_duty": True}, headers=driver_headers)
    ).json()
    password = body["mqtt"]["password"]

    session = (await db_session.execute(select(DutySession))).scalars().one()
    assert session.mqtt_password_hash is not None
    assert password not in session.mqtt_password_hash
    assert verify_password(password, session.mqtt_password_hash)


async def test_going_on_duty_makes_the_vehicle_assignable(
    client: AsyncClient,
    driver_headers: dict[str, str],
    db_session: AsyncSession,
    world: dict[str, uuid.UUID],
) -> None:
    """DRV-02: going on duty makes the vehicle assignable."""
    await client.post("/driver/duty", json={"on_duty": True}, headers=driver_headers)

    vehicle = await db_session.get(Vehicle, world["vehicle_id"])
    assert vehicle is not None
    assert vehicle.status == VehicleStatus.available
    assert vehicle.current_driver_id == world["driver_id"]


async def test_a_duty_session_is_opened(
    client: AsyncClient, driver_headers: dict[str, str], db_session: AsyncSession
) -> None:
    await client.post("/driver/duty", json={"on_duty": True}, headers=driver_headers)
    session = (await db_session.execute(select(DutySession))).scalars().one()
    assert session.started_at == NOW
    assert session.ended_at is None


async def test_going_on_duty_twice_is_a_conflict(
    client: AsyncClient, driver_headers: dict[str, str]
) -> None:
    await client.post("/driver/duty", json={"on_duty": True}, headers=driver_headers)
    again = await client.post("/driver/duty", json={"on_duty": True}, headers=driver_headers)
    assert again.status_code == 409


async def test_an_explicit_vehicle_can_be_chosen(
    client: AsyncClient,
    driver_headers: dict[str, str],
    db_session: AsyncSession,
    world: dict[str, uuid.UUID],
) -> None:
    other = Vehicle(
        operator_id=world["operator_id"],
        registration_no="UP16CD5678",
        vehicle_type=VehicleType.suv_6,
        seat_capacity=6,
    )
    db_session.add(other)
    await db_session.flush()

    body = (
        await client.post(
            "/driver/duty",
            json={"on_duty": True, "vehicle_id": str(other.id)},
            headers=driver_headers,
        )
    ).json()
    assert body["vehicle_id"] == str(other.id)


async def test_a_driver_with_no_default_vehicle_must_choose_one(
    client: AsyncClient,
    driver_headers: dict[str, str],
    db_session: AsyncSession,
    world: dict[str, uuid.UUID],
) -> None:
    driver = await db_session.get(Driver, world["driver_id"])
    assert driver is not None
    driver.default_vehicle_id = None
    await db_session.flush()

    response = await client.post("/driver/duty", json={"on_duty": True}, headers=driver_headers)
    assert response.status_code == 422


async def test_another_operators_vehicle_is_not_found(
    client: AsyncClient, driver_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/driver/duty",
        json={"on_duty": True, "vehicle_id": str(uuid.uuid4())},
        headers=driver_headers,
    )
    assert response.status_code == 404


async def test_an_out_of_service_vehicle_cannot_go_on_duty(
    client: AsyncClient,
    driver_headers: dict[str, str],
    db_session: AsyncSession,
    world: dict[str, uuid.UUID],
) -> None:
    """Returning a vehicle to service is a supervisor's call, not a driver's.

    The state machine permits out_of_service -> available because supervisors need it,
    so without an actor check here a driver could clear the flag by tapping "go on duty".
    """
    vehicle = await db_session.get(Vehicle, world["vehicle_id"])
    assert vehicle is not None
    vehicle.status = VehicleStatus.out_of_service
    await db_session.flush()

    response = await client.post("/driver/duty", json={"on_duty": True}, headers=driver_headers)
    assert response.status_code == 409
    assert "supervisor" in response.json()["message"]
    # The row is not re-checked here on purpose: these tests share one session with the
    # app, so a failed request rolls the test's own transaction back too. In production
    # each request has its own session. The service raises before touching the vehicle,
    # which the 409 already demonstrates.


async def test_two_drivers_cannot_share_one_vehicle(
    client: AsyncClient,
    driver_headers: dict[str, str],
    db_session: AsyncSession,
    clock: FakeClock,
    world: dict[str, uuid.UUID],
) -> None:
    """Two on-duty drivers on one cab would corrupt its GPS stream."""
    await client.post("/driver/duty", json={"on_duty": True}, headers=driver_headers)

    other_user = make_user(name="Sunil", phone=unique_phone())
    db_session.add(other_user)
    await db_session.flush()
    db_session.add(make_user_role(other_user.id, Role.driver, operator_id=world["operator_id"]))
    db_session.add(
        Driver(
            operator_id=world["operator_id"],
            user_id=other_user.id,
            name="Sunil",
            phone=unique_phone(),
            default_vehicle_id=world["vehicle_id"],
        )
    )
    await db_session.flush()

    token, _ = create_access_token(
        user_id=other_user.id,
        role=str(Role.driver),
        secret=JWT_SECRET,
        clock=clock,
        ttl_seconds=900,
        operator_id=world["operator_id"],
    )
    response = await client.post(
        "/driver/duty",
        json={"on_duty": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409


async def test_an_inactive_driver_cannot_go_on_duty(
    client: AsyncClient,
    driver_headers: dict[str, str],
    db_session: AsyncSession,
    world: dict[str, uuid.UUID],
) -> None:
    driver = await db_session.get(Driver, world["driver_id"])
    assert driver is not None
    driver.active = False
    await db_session.flush()

    response = await client.post("/driver/duty", json={"on_duty": True}, headers=driver_headers)
    assert response.status_code == 403


# --- going off duty ------------------------------------------------------------------


async def test_going_off_duty_releases_the_vehicle(
    client: AsyncClient,
    driver_headers: dict[str, str],
    db_session: AsyncSession,
    world: dict[str, uuid.UUID],
) -> None:
    await client.post("/driver/duty", json={"on_duty": True}, headers=driver_headers)
    response = await client.post("/driver/duty", json={"on_duty": False}, headers=driver_headers)

    assert response.status_code == 200
    assert response.json()["on_duty"] is False
    assert response.json()["mqtt"] is None

    vehicle = await db_session.get(Vehicle, world["vehicle_id"])
    assert vehicle is not None
    assert vehicle.status == VehicleStatus.off_duty
    assert vehicle.current_driver_id is None
    assert vehicle.mqtt_username is None, "the credential dies with the session"


async def test_going_off_duty_closes_the_session(
    client: AsyncClient, driver_headers: dict[str, str], db_session: AsyncSession
) -> None:
    await client.post("/driver/duty", json={"on_duty": True}, headers=driver_headers)
    await client.post("/driver/duty", json={"on_duty": False}, headers=driver_headers)

    session = (await db_session.execute(select(DutySession))).scalars().one()
    assert session.ended_at == NOW


async def test_going_off_duty_is_blocked_mid_trip(
    client: AsyncClient,
    driver_headers: dict[str, str],
    db_session: AsyncSession,
    world: dict[str, uuid.UUID],
) -> None:
    """DRV-02: "going off duty is blocked while a trip is in progress"."""
    await client.post("/driver/duty", json={"on_duty": True}, headers=driver_headers)

    vehicle = await db_session.get(Vehicle, world["vehicle_id"])
    assert vehicle is not None
    vehicle.status = VehicleStatus.on_trip
    await db_session.flush()

    response = await client.post("/driver/duty", json={"on_duty": False}, headers=driver_headers)
    assert response.status_code == 409
    assert "trip" in response.json()["message"].lower()


async def test_going_off_duty_when_already_off_is_harmless(
    client: AsyncClient, driver_headers: dict[str, str]
) -> None:
    response = await client.post("/driver/duty", json={"on_duty": False}, headers=driver_headers)
    assert response.status_code == 200
    assert response.json()["on_duty"] is False


async def test_a_driver_can_go_on_duty_again_after_finishing(
    client: AsyncClient, driver_headers: dict[str, str], db_session: AsyncSession
) -> None:
    await client.post("/driver/duty", json={"on_duty": True}, headers=driver_headers)
    await client.post("/driver/duty", json={"on_duty": False}, headers=driver_headers)
    again = await client.post("/driver/duty", json={"on_duty": True}, headers=driver_headers)

    assert again.status_code == 200
    sessions = (await db_session.execute(select(DutySession))).scalars().all()
    assert len(sessions) == 2


async def test_a_new_session_issues_a_new_password(
    client: AsyncClient, driver_headers: dict[str, str]
) -> None:
    """A handed-over phone must not keep working."""
    first = (
        await client.post("/driver/duty", json={"on_duty": True}, headers=driver_headers)
    ).json()["mqtt"]["password"]
    await client.post("/driver/duty", json={"on_duty": False}, headers=driver_headers)
    second = (
        await client.post("/driver/duty", json={"on_duty": True}, headers=driver_headers)
    ).json()["mqtt"]["password"]

    assert first != second


# --- reads and permissions --------------------------------------------------------------


async def test_get_duty_reports_state_without_a_password(
    client: AsyncClient, driver_headers: dict[str, str]
) -> None:
    await client.post("/driver/duty", json={"on_duty": True}, headers=driver_headers)
    body = (await client.get("/driver/duty", headers=driver_headers)).json()

    assert body["on_duty"] is True
    assert body["mqtt"] is None, "the password is returned once and never again"


async def test_a_supervisor_cannot_go_on_duty(
    client: AsyncClient, world: dict[str, uuid.UUID], clock: FakeClock, db_session: AsyncSession
) -> None:
    """The matrix gives duty to drivers alone."""
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
        "/driver/duty", json={"on_duty": True}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


async def test_a_login_with_no_driver_record_is_refused(
    client: AsyncClient, world: dict[str, uuid.UUID], clock: FakeClock, db_session: AsyncSession
) -> None:
    user = make_user(phone=unique_phone())
    db_session.add(user)
    await db_session.flush()
    db_session.add(make_user_role(user.id, Role.driver, operator_id=world["operator_id"]))
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
        "/driver/duty", json={"on_duty": True}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


async def test_duty_requires_authentication(client: AsyncClient) -> None:
    assert (await client.post("/driver/duty", json={"on_duty": True})).status_code == 401


# --- generated broker files ----------------------------------------------------------------


async def test_broker_files_cover_every_on_duty_vehicle(
    client: AsyncClient,
    driver_headers: dict[str, str],
    db_session: AsyncSession,
    clock: FakeClock,
    world: dict[str, uuid.UUID],
) -> None:
    from app.modules.fleet.duty_service import DutyService

    await client.post("/driver/duty", json={"on_duty": True}, headers=driver_headers)

    settings = Settings(
        app_env="dev",
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        jwt_secret=JWT_SECRET,
    )
    passwords, acl = await DutyService(db_session, clock, settings).broker_files()

    username = f"veh-{world['vehicle_id']}"
    assert username in passwords
    assert f"user {username}" in acl
    assert f"topic write sc/v1/op/{world['operator_id']}/veh/{world['vehicle_id']}/gps" in acl


async def test_an_off_duty_vehicle_drops_out_of_the_broker_files(
    client: AsyncClient,
    driver_headers: dict[str, str],
    db_session: AsyncSession,
    clock: FakeClock,
    world: dict[str, uuid.UUID],
) -> None:
    from app.modules.fleet.duty_service import DutyService

    await client.post("/driver/duty", json={"on_duty": True}, headers=driver_headers)
    await client.post("/driver/duty", json={"on_duty": False}, headers=driver_headers)

    settings = Settings(
        app_env="dev",
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        jwt_secret=JWT_SECRET,
    )
    passwords, acl = await DutyService(db_session, clock, settings).broker_files()
    assert f"veh-{world['vehicle_id']}" not in passwords
    assert f"veh-{world['vehicle_id']}" not in acl
