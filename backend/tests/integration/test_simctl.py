"""Simulator control endpoints (B19, ADR-0008).

Acceptance: 404 in dev; in sim, advancing the clock triggers expiry deterministically.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.core.settings import Settings
from app.main import create_app
from app.modules.auth.models import AppUser
from app.modules.fleet.models import Driver, Vehicle
from app.modules.people.models import Employee
from app.modules.requests.models import RideRequest
from app.modules.simctl.service import EMPLOYEE_COUNT, OFFICES, SEED_USERS, VEHICLES, ZONES
from app.modules.tenancy.models import Office, Operator, Zone

NOW = datetime(2026, 9, 24, 4, 30, tzinfo=UTC)
JWT_SECRET = "simctl-tests-secret-0123456789abcdefg"


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


def sim_settings() -> Settings:
    return Settings(
        app_env="sim",
        simctl_enabled=True,
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        jwt_secret=JWT_SECRET,
    )


def dev_settings() -> Settings:
    return Settings(
        app_env="dev",
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        jwt_secret=JWT_SECRET,
    )


class _NoClose:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def __aenter__(self) -> AsyncSession:
        return self._session

    async def __aexit__(self, *exc_info: object) -> None:
        return None


def build(settings: Settings, session: AsyncSession, clock: FakeClock) -> FastAPI:
    app = create_app(settings=settings, clock=clock)

    class _Factory:
        def __call__(self) -> object:
            return _NoClose(session)

    app.state.session_factory = _Factory()
    return app


@pytest_asyncio.fixture
async def sim_client(
    database_ready: bool, db_session: AsyncSession, clock: FakeClock
) -> AsyncIterator[AsyncClient]:
    app = build(sim_settings(), db_session, clock)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as c:
        yield c


@pytest_asyncio.fixture
async def dev_client(
    database_ready: bool, db_session: AsyncSession, clock: FakeClock
) -> AsyncIterator[AsyncClient]:
    app = build(dev_settings(), db_session, clock)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as c:
        yield c


# --- environment gating -----------------------------------------------------------


async def test_clock_is_404_in_dev(dev_client: AsyncClient) -> None:
    """B19 acceptance: the endpoints do not exist outside sim."""
    assert (await dev_client.get("/simctl/clock")).status_code == 404
    assert (await dev_client.put("/simctl/clock", json={"advance_seconds": 60})).status_code == 404


async def test_reset_is_404_in_dev(dev_client: AsyncClient) -> None:
    assert (await dev_client.post("/simctl/reset", json={})).status_code == 404


async def test_the_routes_are_absent_not_merely_guarded() -> None:
    """A flag can be flipped by accident; an unregistered route cannot."""
    dev = create_app(settings=dev_settings(), clock=FakeClock(NOW))
    assert not [p for p in dev.openapi()["paths"] if "simctl" in p]


async def test_the_routes_exist_in_sim(sim_client: AsyncClient) -> None:
    assert (await sim_client.get("/simctl/clock")).status_code == 200


# --- the clock ----------------------------------------------------------------------


async def test_get_returns_the_current_sim_time(sim_client: AsyncClient) -> None:
    body = (await sim_client.get("/simctl/clock")).json()
    assert body["now"].startswith("2026-09-24T04:30")


async def test_advance_moves_the_clock(sim_client: AsyncClient, clock: FakeClock) -> None:
    response = await sim_client.put("/simctl/clock", json={"advance_seconds": 3600})
    assert response.status_code == 200
    assert clock.now() == NOW + timedelta(hours=1)
    assert response.json()["now"].startswith("2026-09-24T05:30")


async def test_setting_an_absolute_time(sim_client: AsyncClient, clock: FakeClock) -> None:
    target = NOW + timedelta(days=1)
    response = await sim_client.put("/simctl/clock", json={"now": target.isoformat()})
    assert response.status_code == 200
    assert clock.now() == target


async def test_both_fields_at_once_is_rejected(sim_client: AsyncClient) -> None:
    response = await sim_client.put(
        "/simctl/clock", json={"now": NOW.isoformat(), "advance_seconds": 60}
    )
    assert response.status_code == 422


async def test_neither_field_is_rejected(sim_client: AsyncClient) -> None:
    assert (await sim_client.put("/simctl/clock", json={})).status_code == 422


async def test_negative_advance_is_rejected(sim_client: AsyncClient) -> None:
    response = await sim_client.put("/simctl/clock", json={"advance_seconds": -60})
    assert response.status_code == 422


async def test_a_naive_time_is_rejected(sim_client: AsyncClient) -> None:
    response = await sim_client.put("/simctl/clock", json={"now": "2026-09-25T00:00:00"})
    assert response.status_code == 422
    assert "timezone" in response.json()["message"]


async def test_the_clock_never_runs_backwards_on_advance(
    sim_client: AsyncClient, clock: FakeClock
) -> None:
    await sim_client.put("/simctl/clock", json={"advance_seconds": 60})
    await sim_client.put("/simctl/clock", json={"advance_seconds": 60})
    assert clock.now() == NOW + timedelta(minutes=2)


# --- due work runs synchronously ------------------------------------------------------


async def test_advancing_the_clock_expires_due_requests(
    sim_client: AsyncClient, db_session: AsyncSession, clock: FakeClock
) -> None:
    """B19 acceptance: advancing the clock triggers expiry, deterministically.

    The PUT returns only after the sweep, so the simulator never races a worker.
    """
    reset = (await sim_client.post("/simctl/reset", json={})).json()

    from app.domain.enums import Direction, Role, Urgency
    from app.modules.requests.service import RideRequestService

    rider = next(u for u in reset["users"] if u["role"] == "employee")
    service = RideRequestService(db_session, clock)
    await service.create(
        operator_id=uuid.UUID(reset["operator_id"]),
        actor_role=Role.employee,
        actor_user_id=uuid.UUID(rider["user_id"]),
        direction=Direction.to_office,
        requested_time=clock.now() + timedelta(hours=1),
        urgency=Urgency.medium,
    )

    # request_expiry_minutes defaults to 120.
    response = await sim_client.put("/simctl/clock", json={"advance_seconds": 121 * 60})

    assert response.status_code == 200
    assert response.json()["expired"] == 1

    statuses = (await db_session.execute(select(RideRequest.status))).scalars().all()
    assert statuses == ["expired"]


async def test_the_response_reports_near_expiry_alerts(
    sim_client: AsyncClient, db_session: AsyncSession, clock: FakeClock
) -> None:
    reset = (await sim_client.post("/simctl/reset", json={})).json()

    from app.domain.enums import Direction, Role
    from app.modules.requests.service import RideRequestService

    rider = next(u for u in reset["users"] if u["role"] == "employee")
    await RideRequestService(db_session, clock).create(
        operator_id=uuid.UUID(reset["operator_id"]),
        actor_role=Role.employee,
        actor_user_id=uuid.UUID(rider["user_id"]),
        direction=Direction.to_office,
        requested_time=clock.now() + timedelta(hours=1),
    )

    body = (await sim_client.put("/simctl/clock", json={"advance_seconds": 110 * 60})).json()
    assert body["near_expiry_alerts"] == 1
    assert body["expired"] == 0


# --- reset ------------------------------------------------------------------------------


async def test_reset_seeds_the_documented_fixture(
    sim_client: AsyncClient, db_session: AsyncSession
) -> None:
    """testing-strategy.md section 4: 2 offices, 3 zones, 20 employees, 6 vehicles."""
    response = await sim_client.post("/simctl/reset", json={})
    assert response.status_code == 200

    body = response.json()
    assert len(body["office_ids"]) == len(OFFICES) == 2
    assert len(body["zone_ids"]) == len(ZONES) == 3
    assert len(body["employee_ids"]) == EMPLOYEE_COUNT == 20
    assert len(body["vehicle_ids"]) == len(VEHICLES) == 6
    assert len(body["driver_ids"]) == 6

    assert await db_session.scalar(select(func.count()).select_from(Employee)) == 20
    assert await db_session.scalar(select(func.count()).select_from(Vehicle)) == 6
    assert await db_session.scalar(select(func.count()).select_from(Office)) == 2
    assert await db_session.scalar(select(func.count()).select_from(Zone)) == 3


async def test_reset_returns_a_usable_token_per_role(sim_client: AsyncClient) -> None:
    body = (await sim_client.post("/simctl/reset", json={})).json()
    roles = {user["role"] for user in body["users"]}
    assert roles == {"operator_admin", "supervisor", "client_admin", "driver", "employee"}

    # The tokens must actually work, or every agent stalls at start-up.
    supervisor = next(u for u in body["users"] if u["role"] == "supervisor")
    me = await sim_client.get(
        "/auth/me", headers={"Authorization": f"Bearer {supervisor['access_token']}"}
    )
    assert me.status_code == 200
    assert me.json()["roles"][0]["role"] == "supervisor"


async def test_reset_is_deterministic(sim_client: AsyncClient) -> None:
    """simulator-spec.md section 13: same inputs, same run - including the ids."""
    first = (await sim_client.post("/simctl/reset", json={})).json()
    second = (await sim_client.post("/simctl/reset", json={})).json()

    assert first["operator_id"] == second["operator_id"]
    assert first["employee_ids"] == second["employee_ids"]
    assert first["vehicle_ids"] == second["vehicle_ids"]


async def test_reset_truncates_previous_data(
    sim_client: AsyncClient, db_session: AsyncSession, clock: FakeClock
) -> None:
    reset = (await sim_client.post("/simctl/reset", json={})).json()

    from app.domain.enums import Direction, Role
    from app.modules.requests.service import RideRequestService

    rider = next(u for u in reset["users"] if u["role"] == "employee")
    await RideRequestService(db_session, clock).create(
        operator_id=uuid.UUID(reset["operator_id"]),
        actor_role=Role.employee,
        actor_user_id=uuid.UUID(rider["user_id"]),
        direction=Direction.to_office,
        requested_time=clock.now() + timedelta(hours=1),
    )
    assert await db_session.scalar(select(func.count()).select_from(RideRequest)) == 1

    await sim_client.post("/simctl/reset", json={})
    assert await db_session.scalar(select(func.count()).select_from(RideRequest)) == 0
    assert await db_session.scalar(select(func.count()).select_from(Operator)) == 1


async def test_reset_can_set_the_start_time(sim_client: AsyncClient, clock: FakeClock) -> None:
    start = datetime(2026, 10, 5, 0, 30, tzinfo=UTC)
    body = (await sim_client.post("/simctl/reset", json={"start_time": start.isoformat()})).json()
    assert clock.now() == start
    assert body["now"].startswith("2026-10-05T00:30")


async def test_scenario_yaml_is_refused_rather_than_ignored(
    sim_client: AsyncClient,
) -> None:
    """Half-honouring the field would be worse than not accepting it."""
    response = await sim_client.post("/simctl/reset", json={"scenario_yaml": "name: x"})
    assert response.status_code == 422
    assert "not supported yet" in response.json()["message"]


async def test_the_fixture_has_one_vip_vehicle_and_one_vip_employee(
    sim_client: AsyncClient, db_session: AsyncSession
) -> None:
    """S07 (vip_burst) needs both to exist."""
    await sim_client.post("/simctl/reset", json={})
    vehicles = (await db_session.execute(select(Vehicle))).scalars().all()
    employees = (await db_session.execute(select(Employee))).scalars().all()
    assert sum(1 for v in vehicles if v.vehicle_type == "vip") == 1
    assert sum(1 for e in employees if e.is_vip) == 1


async def test_the_seeded_rider_is_linked_to_an_employee(
    sim_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Without the link the rider agent cannot create a request."""
    body = (await sim_client.post("/simctl/reset", json={})).json()
    rider = next(u for u in body["users"] if u["role"] == "employee")

    employee = (
        (
            await db_session.execute(
                select(Employee).where(Employee.user_id == uuid.UUID(rider["user_id"]))
            )
        )
        .scalars()
        .one_or_none()
    )
    assert employee is not None


async def test_the_seeded_driver_is_linked_to_a_driver_record(
    sim_client: AsyncClient, db_session: AsyncSession
) -> None:
    body = (await sim_client.post("/simctl/reset", json={})).json()
    seeded = next(u for u in body["users"] if u["role"] == "driver")
    driver = (
        (
            await db_session.execute(
                select(Driver).where(Driver.user_id == uuid.UUID(seeded["user_id"]))
            )
        )
        .scalars()
        .one_or_none()
    )
    assert driver is not None
    assert driver.default_vehicle_id is not None


async def test_every_seeded_user_exists(sim_client: AsyncClient, db_session: AsyncSession) -> None:
    """One login per role, plus one more per cab beyond the first.

    The extra driver accounts exist because a driver may hold only one open duty session
    (B11), so a simulated fleet cannot share an account (M04).
    """
    body = (await sim_client.post("/simctl/reset", json={})).json()

    expected = len(SEED_USERS) + len(body["vehicle_ids"]) - 1
    assert await db_session.scalar(select(func.count()).select_from(AppUser)) == expected
    assert len(body["users"]) == expected


async def test_every_cab_has_its_own_driver_login(
    sim_client: AsyncClient, db_session: AsyncSession
) -> None:
    """A fleet sharing one account cannot all go on duty."""
    body = (await sim_client.post("/simctl/reset", json={})).json()

    drivers = [user for user in body["users"] if user["role"] == "driver"]
    assert len(drivers) == len(body["vehicle_ids"])
    assert len({user["access_token"] for user in drivers}) == len(drivers)
