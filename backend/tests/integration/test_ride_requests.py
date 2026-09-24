"""Ride requests: creation, validation, cancellation and expiry (B09).

Acceptance: integration tests for every acceptance criterion, and expiry fires when the
fake clock advances — no sleeping, which is the whole point of the injected Clock.
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
from app.core.security import create_access_token
from app.core.settings import Settings
from app.domain.enums import CLIENT_SCOPED_ROLES, AlertType, Direction, Role, Urgency
from app.domain.state_machines import RequestStatus
from app.main import create_app
from app.modules.alerts.models import Alert
from app.modules.config.service import ConfigService
from app.modules.requests.models import RideRequest, RideRequestEvent
from app.modules.requests.service import RideRequestService
from tests.builders import (
    make_client,
    make_employee,
    make_office,
    make_operator,
    make_user,
    make_user_role,
    unique_phone,
)

NOW = datetime(2026, 9, 24, 4, 30, tzinfo=UTC)
JWT_SECRET = "ride-request-tests-secret-0123456789ab"


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest_asyncio.fixture
async def world(db_session: AsyncSession) -> dict[str, uuid.UUID]:
    """An operator, a client, an office, an employee linked to a login."""
    operator = make_operator()
    db_session.add(operator)
    await db_session.flush()

    corporate = make_client(operator.id, "Acme")
    db_session.add(corporate)
    await db_session.flush()

    office = make_office(operator.id, corporate.id, "B200")
    db_session.add(office)
    await db_session.flush()

    rider_user = make_user(name="Asha", phone=unique_phone())
    db_session.add(rider_user)
    await db_session.flush()
    db_session.add(
        make_user_role(
            rider_user.id, Role.employee, operator_id=operator.id, client_id=corporate.id
        )
    )

    employee = make_employee(operator.id, corporate.id, office.id, name="Asha")
    employee.user_id = rider_user.id
    db_session.add(employee)
    await db_session.flush()

    return {
        "operator_id": operator.id,
        "client_id": corporate.id,
        "office_id": office.id,
        "employee_id": employee.id,
        "rider_user_id": rider_user.id,
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


def token_headers(
    role: Role,
    operator_id: uuid.UUID,
    clock: FakeClock,
    user_id: uuid.UUID,
    client_id: uuid.UUID | None = None,
) -> dict[str, str]:
    token, _ = create_access_token(
        user_id=user_id,
        role=str(role),
        secret=JWT_SECRET,
        clock=clock,
        ttl_seconds=900,
        operator_id=operator_id,
        client_id=client_id if role in CLIENT_SCOPED_ROLES else None,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def rider(world: dict[str, uuid.UUID], clock: FakeClock) -> dict[str, str]:
    return token_headers(
        Role.employee,
        world["operator_id"],
        clock,
        world["rider_user_id"],
        world["client_id"],
    )


@pytest_asyncio.fixture
async def supervisor(
    world: dict[str, uuid.UUID], clock: FakeClock, db_session: AsyncSession
) -> dict[str, str]:
    user = make_user(name="Sita", phone=unique_phone())
    db_session.add(user)
    await db_session.flush()
    db_session.add(make_user_role(user.id, Role.supervisor, operator_id=world["operator_id"]))
    await db_session.flush()
    return token_headers(Role.supervisor, world["operator_id"], clock, user.id)


def payload(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "direction": "to_office",
        "requested_time": (NOW + timedelta(hours=2)).isoformat(),
    }
    body.update(overrides)
    return body


# --- creation -------------------------------------------------------------------


async def test_employee_creates_a_request_for_themselves(
    client: AsyncClient, rider: dict[str, str], world: dict[str, uuid.UUID]
) -> None:
    response = await client.post("/ride-requests", json=payload(), headers=rider)
    assert response.status_code == 201, response.text

    body = response.json()
    assert body["employee_id"] == str(world["employee_id"])
    assert body["status"] == "queued", "a validated request goes straight to queued"
    assert body["urgency"] == "medium"
    assert body["no_sharing"] is False


async def test_location_defaults_to_the_employees_home(
    client: AsyncClient, rider: dict[str, str]
) -> None:
    body = (await client.post("/ride-requests", json=payload(), headers=rider)).json()
    # tests.builders puts home at Sector 135.
    assert body["location"]["lat"] == pytest.approx(28.5123, abs=1e-4)


async def test_an_explicit_location_overrides_home(
    client: AsyncClient, rider: dict[str, str]
) -> None:
    body = (
        await client.post(
            "/ride-requests",
            json=payload(location={"lat": 28.6000, "lng": 77.4000}),
            headers=rider,
        )
    ).json()
    assert body["location"]["lat"] == pytest.approx(28.6, abs=1e-4)


async def test_employee_id_in_the_body_is_ignored_for_a_rider(
    client: AsyncClient, rider: dict[str, str], world: dict[str, uuid.UUID]
) -> None:
    """api-spec: "ignored for employee role" - a rider cannot request for someone else."""
    response = await client.post(
        "/ride-requests", json=payload(employee_id=str(uuid.uuid4())), headers=rider
    )
    assert response.status_code == 201
    assert response.json()["employee_id"] == str(world["employee_id"])


async def test_supervisor_creates_on_behalf(
    client: AsyncClient, supervisor: dict[str, str], world: dict[str, uuid.UUID]
) -> None:
    response = await client.post(
        "/ride-requests",
        json=payload(employee_id=str(world["employee_id"])),
        headers=supervisor,
    )
    assert response.status_code == 201
    assert response.json()["employee_id"] == str(world["employee_id"])


async def test_on_behalf_requires_an_employee_id(
    client: AsyncClient, supervisor: dict[str, str]
) -> None:
    response = await client.post("/ride-requests", json=payload(), headers=supervisor)
    assert response.status_code == 422
    assert "employee_id" in response.json()["message"]


async def test_unknown_employee_is_not_found(
    client: AsyncClient, supervisor: dict[str, str]
) -> None:
    response = await client.post(
        "/ride-requests", json=payload(employee_id=str(uuid.uuid4())), headers=supervisor
    )
    assert response.status_code == 404


async def test_inactive_employee_is_rejected(
    client: AsyncClient,
    supervisor: dict[str, str],
    world: dict[str, uuid.UUID],
    db_session: AsyncSession,
) -> None:
    from app.modules.people.models import Employee

    employee = await db_session.get(Employee, world["employee_id"])
    assert employee is not None
    employee.active = False
    await db_session.flush()

    response = await client.post(
        "/ride-requests", json=payload(employee_id=str(world["employee_id"])), headers=supervisor
    )
    assert response.status_code == 422


async def test_a_request_writes_its_events(
    client: AsyncClient, rider: dict[str, str], db_session: AsyncSession
) -> None:
    """trip-lifecycle.md: every transition writes an event row."""
    request_id = (await client.post("/ride-requests", json=payload(), headers=rider)).json()["id"]

    events = (
        (
            await db_session.execute(
                select(RideRequestEvent)
                .where(RideRequestEvent.request_id == uuid.UUID(request_id))
                .order_by(RideRequestEvent.at)
            )
        )
        .scalars()
        .all()
    )

    assert [e.to_status for e in events] == ["requested", "queued"]
    assert events[0].actor_type == "employee"


# --- time validation ----------------------------------------------------------------


async def test_a_time_in_the_past_is_rejected(client: AsyncClient, rider: dict[str, str]) -> None:
    response = await client.post(
        "/ride-requests",
        json=payload(requested_time=(NOW - timedelta(hours=1)).isoformat()),
        headers=rider,
    )
    assert response.status_code == 422
    assert "past" in response.json()["message"]


async def test_now_is_accepted(client: AsyncClient, rider: dict[str, str]) -> None:
    response = await client.post(
        "/ride-requests", json=payload(requested_time=NOW.isoformat()), headers=rider
    )
    assert response.status_code == 201


async def test_a_moment_ago_is_tolerated(client: AsyncClient, rider: dict[str, str]) -> None:
    """A slow client or a little clock skew must not lose a legitimate 'now'."""
    response = await client.post(
        "/ride-requests",
        json=payload(requested_time=(NOW - timedelta(minutes=2)).isoformat()),
        headers=rider,
    )
    assert response.status_code == 201


async def test_seven_days_ahead_is_accepted(client: AsyncClient, rider: dict[str, str]) -> None:
    response = await client.post(
        "/ride-requests",
        json=payload(requested_time=(NOW + timedelta(days=6, hours=23)).isoformat()),
        headers=rider,
    )
    assert response.status_code == 201


async def test_beyond_seven_days_is_rejected(client: AsyncClient, rider: dict[str, str]) -> None:
    """EMP-02: "a time up to 7 days ahead"."""
    response = await client.post(
        "/ride-requests",
        json=payload(requested_time=(NOW + timedelta(days=8)).isoformat()),
        headers=rider,
    )
    assert response.status_code == 422
    assert "7 days" in response.json()["message"]


# --- the duplicate window ------------------------------------------------------------


async def test_duplicate_within_the_hour_is_rejected(
    client: AsyncClient, rider: dict[str, str]
) -> None:
    """EMP-02: no two active same-direction requests within 60 minutes."""
    await client.post("/ride-requests", json=payload(), headers=rider)
    response = await client.post(
        "/ride-requests",
        json=payload(requested_time=(NOW + timedelta(hours=2, minutes=30)).isoformat()),
        headers=rider,
    )
    assert response.status_code == 409
    assert "within an hour" in response.json()["message"]


async def test_more_than_an_hour_apart_is_allowed(
    client: AsyncClient, rider: dict[str, str]
) -> None:
    await client.post("/ride-requests", json=payload(), headers=rider)
    response = await client.post(
        "/ride-requests",
        json=payload(requested_time=(NOW + timedelta(hours=3, minutes=1)).isoformat()),
        headers=rider,
    )
    assert response.status_code == 201


async def test_the_other_direction_is_allowed_at_the_same_time(
    client: AsyncClient, rider: dict[str, str]
) -> None:
    """A rider goes to the office and comes back; only same-direction clashes count."""
    await client.post("/ride-requests", json=payload(), headers=rider)
    response = await client.post(
        "/ride-requests", json=payload(direction="from_office"), headers=rider
    )
    assert response.status_code == 201


async def test_a_cancelled_request_frees_the_window(
    client: AsyncClient, rider: dict[str, str]
) -> None:
    first = (await client.post("/ride-requests", json=payload(), headers=rider)).json()["id"]
    await client.post(f"/ride-requests/{first}/cancel", json={}, headers=rider)

    response = await client.post("/ride-requests", json=payload(), headers=rider)
    assert response.status_code == 201


# --- reads ----------------------------------------------------------------------------


async def test_list_mine_returns_only_my_requests(
    client: AsyncClient,
    rider: dict[str, str],
    supervisor: dict[str, str],
    world: dict[str, uuid.UUID],
    db_session: AsyncSession,
) -> None:
    await client.post("/ride-requests", json=payload(), headers=rider)

    other_employee = make_employee(
        world["operator_id"], world["client_id"], world["office_id"], name="Ravi"
    )
    db_session.add(other_employee)
    await db_session.flush()
    await client.post(
        "/ride-requests",
        json=payload(employee_id=str(other_employee.id)),
        headers=supervisor,
    )

    mine = (await client.get("/ride-requests/mine", headers=rider)).json()["items"]
    assert len(mine) == 1
    assert mine[0]["employee_id"] == str(world["employee_id"])


async def test_get_my_own_request(client: AsyncClient, rider: dict[str, str]) -> None:
    request_id = (await client.post("/ride-requests", json=payload(), headers=rider)).json()["id"]
    response = await client.get(f"/ride-requests/{request_id}", headers=rider)
    assert response.status_code == 200
    assert response.json()["id"] == request_id


async def test_a_rider_cannot_read_someone_elses_request(
    client: AsyncClient,
    rider: dict[str, str],
    supervisor: dict[str, str],
    world: dict[str, uuid.UUID],
    db_session: AsyncSession,
) -> None:
    """Not 403: a rider should not learn that another request exists at all."""
    other = make_employee(world["operator_id"], world["client_id"], world["office_id"], name="Ravi")
    db_session.add(other)
    await db_session.flush()
    other_id = (
        await client.post(
            "/ride-requests", json=payload(employee_id=str(other.id)), headers=supervisor
        )
    ).json()["id"]

    response = await client.get(f"/ride-requests/{other_id}", headers=rider)
    assert response.status_code == 404


async def test_a_supervisor_can_read_any_request_in_their_operator(
    client: AsyncClient, rider: dict[str, str], supervisor: dict[str, str]
) -> None:
    request_id = (await client.post("/ride-requests", json=payload(), headers=rider)).json()["id"]
    assert (await client.get(f"/ride-requests/{request_id}", headers=supervisor)).status_code == 200


async def test_an_unknown_request_is_404(client: AsyncClient, supervisor: dict[str, str]) -> None:
    response = await client.get(f"/ride-requests/{uuid.uuid4()}", headers=supervisor)
    assert response.status_code == 404


# --- cancellation -----------------------------------------------------------------------


async def test_a_rider_cancels_their_own_request(
    client: AsyncClient, rider: dict[str, str]
) -> None:
    request_id = (await client.post("/ride-requests", json=payload(), headers=rider)).json()["id"]
    response = await client.post(f"/ride-requests/{request_id}/cancel", json={}, headers=rider)

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert response.json()["cancel_reason"] == "Cancelled by employee"


async def test_a_supplied_reason_is_kept(client: AsyncClient, rider: dict[str, str]) -> None:
    request_id = (await client.post("/ride-requests", json=payload(), headers=rider)).json()["id"]
    response = await client.post(
        f"/ride-requests/{request_id}/cancel", json={"reason": "Took the metro"}, headers=rider
    )
    assert response.json()["cancel_reason"] == "Took the metro"


async def test_cancelling_twice_is_rejected(client: AsyncClient, rider: dict[str, str]) -> None:
    """The state machine has no cancelled -> cancelled edge."""
    request_id = (await client.post("/ride-requests", json=payload(), headers=rider)).json()["id"]
    await client.post(f"/ride-requests/{request_id}/cancel", json={}, headers=rider)

    again = await client.post(f"/ride-requests/{request_id}/cancel", json={}, headers=rider)
    assert again.status_code == 409
    assert again.json()["code"] == "invalid_transition"


async def test_cancellation_writes_an_event(
    client: AsyncClient, rider: dict[str, str], db_session: AsyncSession
) -> None:
    request_id = (await client.post("/ride-requests", json=payload(), headers=rider)).json()["id"]
    await client.post(
        f"/ride-requests/{request_id}/cancel", json={"reason": "Plans changed"}, headers=rider
    )

    events = (
        (
            await db_session.execute(
                select(RideRequestEvent)
                .where(RideRequestEvent.request_id == uuid.UUID(request_id))
                .order_by(RideRequestEvent.at)
            )
        )
        .scalars()
        .all()
    )
    assert events[-1].to_status == "cancelled"
    assert events[-1].reason == "Plans changed"
    data = events[-1].data
    assert data is not None
    assert data["notify"] == ["driver", "supervisor"]


async def test_a_rider_cannot_cancel_someone_elses_request(
    client: AsyncClient,
    rider: dict[str, str],
    supervisor: dict[str, str],
    world: dict[str, uuid.UUID],
    db_session: AsyncSession,
) -> None:
    other = make_employee(world["operator_id"], world["client_id"], world["office_id"], name="Ravi")
    db_session.add(other)
    await db_session.flush()
    other_id = (
        await client.post(
            "/ride-requests", json=payload(employee_id=str(other.id)), headers=supervisor
        )
    ).json()["id"]

    response = await client.post(f"/ride-requests/{other_id}/cancel", json={}, headers=rider)
    assert response.status_code == 404


# --- expiry, driven by the clock ------------------------------------------------------


async def test_expiry_fires_when_the_clock_advances(
    client: AsyncClient,
    rider: dict[str, str],
    clock: FakeClock,
    db_session: AsyncSession,
    world: dict[str, uuid.UUID],
) -> None:
    """B09 acceptance: expiry fires with a FakeClock advance, with no sleeping."""
    request_id = (await client.post("/ride-requests", json=payload(), headers=rider)).json()["id"]

    service = RideRequestService(db_session, clock)
    assert (await service.run_due_expiries()).expired == 0, "nothing is due yet"

    # request_expiry_minutes defaults to 120.
    clock.advance(timedelta(minutes=121))
    sweep = await service.run_due_expiries()

    assert sweep.expired == 1
    request = await db_session.get(RideRequest, uuid.UUID(request_id))
    assert request is not None
    assert request.status == RequestStatus.expired


async def test_expiry_writes_a_system_event(
    client: AsyncClient, rider: dict[str, str], clock: FakeClock, db_session: AsyncSession
) -> None:
    request_id = (await client.post("/ride-requests", json=payload(), headers=rider)).json()["id"]
    clock.advance(timedelta(minutes=121))
    await RideRequestService(db_session, clock).run_due_expiries()

    events = (
        (
            await db_session.execute(
                select(RideRequestEvent)
                .where(RideRequestEvent.request_id == uuid.UUID(request_id))
                .order_by(RideRequestEvent.at)
            )
        )
        .scalars()
        .all()
    )
    assert events[-1].to_status == "expired"
    assert events[-1].actor_type == "system"


async def test_a_cancelled_request_does_not_expire(
    client: AsyncClient, rider: dict[str, str], clock: FakeClock, db_session: AsyncSession
) -> None:
    request_id = (await client.post("/ride-requests", json=payload(), headers=rider)).json()["id"]
    await client.post(f"/ride-requests/{request_id}/cancel", json={}, headers=rider)

    clock.advance(timedelta(days=1))
    assert (await RideRequestService(db_session, clock).run_due_expiries()).expired == 0


async def test_the_expiry_window_comes_from_config(
    client: AsyncClient,
    rider: dict[str, str],
    clock: FakeClock,
    db_session: AsyncSession,
    world: dict[str, uuid.UUID],
) -> None:
    """`request_expiry_minutes` is a config key, not a constant."""
    await ConfigService(db_session, clock).update(
        world["operator_id"], {"request_expiry_minutes": 30}
    )
    await client.post("/ride-requests", json=payload(), headers=rider)

    service = RideRequestService(db_session, clock)
    clock.advance(timedelta(minutes=31))
    assert (await service.run_due_expiries()).expired == 1


async def test_near_expiry_raises_one_alert(
    client: AsyncClient,
    rider: dict[str, str],
    clock: FakeClock,
    db_session: AsyncSession,
) -> None:
    """trip-lifecycle.md section 6: supervisor warned 15 minutes before expiry."""
    await client.post("/ride-requests", json=payload(), headers=rider)
    service = RideRequestService(db_session, clock)

    assert (await service.run_due_expiries()).warned == 0
    clock.advance(timedelta(minutes=110))  # 10 minutes left of the 120
    assert (await service.run_due_expiries()).warned == 1

    alerts = (await db_session.execute(select(Alert))).scalars().all()
    assert len(alerts) == 1
    assert alerts[0].type == AlertType.request_near_expiry
    assert alerts[0].status == "open"


async def test_the_near_expiry_alert_does_not_repeat(
    client: AsyncClient, rider: dict[str, str], clock: FakeClock, db_session: AsyncSession
) -> None:
    """The sweep runs every minute; a supervisor must not get 15 identical alerts."""
    await client.post("/ride-requests", json=payload(), headers=rider)
    service = RideRequestService(db_session, clock)

    clock.advance(timedelta(minutes=110))
    await service.run_due_expiries()
    clock.advance(timedelta(minutes=2))
    await service.run_due_expiries()

    count = await db_session.scalar(select(func.count()).select_from(Alert))
    assert count == 1


async def test_a_sweep_is_scoped_to_one_operator_when_asked(
    client: AsyncClient,
    rider: dict[str, str],
    clock: FakeClock,
    db_session: AsyncSession,
) -> None:
    await client.post("/ride-requests", json=payload(), headers=rider)
    other = make_operator("Rival Cabs")
    db_session.add(other)
    await db_session.flush()

    clock.advance(timedelta(minutes=121))
    service = RideRequestService(db_session, clock)
    assert (await service.run_due_expiries(operator_id=other.id)).expired == 0


async def test_an_expired_request_frees_the_duplicate_window(
    client: AsyncClient,
    rider: dict[str, str],
    clock: FakeClock,
    db_session: AsyncSession,
    world: dict[str, uuid.UUID],
) -> None:
    await client.post("/ride-requests", json=payload(), headers=rider)
    clock.advance(timedelta(minutes=121))
    await RideRequestService(db_session, clock).run_due_expiries()

    # The original token was minted two hours ago and has legitimately expired by now
    # (access tokens last 15 minutes), so mint a fresh one rather than assert a 401.
    fresh = token_headers(
        Role.employee,
        world["operator_id"],
        clock,
        world["rider_user_id"],
        world["client_id"],
    )
    response = await client.post(
        "/ride-requests",
        json=payload(requested_time=(clock.now() + timedelta(hours=1)).isoformat()),
        headers=fresh,
    )
    assert response.status_code == 201


# --- permissions -------------------------------------------------------------------------


async def test_a_driver_cannot_create_a_request(
    client: AsyncClient, world: dict[str, uuid.UUID], clock: FakeClock, db_session: AsyncSession
) -> None:
    user = make_user(phone=unique_phone())
    db_session.add(user)
    await db_session.flush()
    db_session.add(make_user_role(user.id, Role.driver, operator_id=world["operator_id"]))
    await db_session.flush()

    headers = token_headers(Role.driver, world["operator_id"], clock, user.id)
    response = await client.post("/ride-requests", json=payload(), headers=headers)
    assert response.status_code == 403


async def test_creating_a_request_requires_authentication(client: AsyncClient) -> None:
    assert (await client.post("/ride-requests", json=payload())).status_code == 401


async def test_a_user_with_no_employee_record_cannot_request(
    client: AsyncClient, world: dict[str, uuid.UUID], clock: FakeClock, db_session: AsyncSession
) -> None:
    user = make_user(phone=unique_phone())
    db_session.add(user)
    await db_session.flush()
    db_session.add(
        make_user_role(
            user.id, Role.employee, operator_id=world["operator_id"], client_id=world["client_id"]
        )
    )
    await db_session.flush()

    headers = token_headers(Role.employee, world["operator_id"], clock, user.id, world["client_id"])
    response = await client.post("/ride-requests", json=payload(), headers=headers)
    assert response.status_code == 403


async def test_direction_and_urgency_are_validated(
    client: AsyncClient, rider: dict[str, str]
) -> None:
    assert (
        await client.post("/ride-requests", json=payload(direction="sideways"), headers=rider)
    ).status_code == 422
    assert (
        await client.post("/ride-requests", json=payload(urgency="extreme"), headers=rider)
    ).status_code == 422


async def test_landmark_length_is_capped(client: AsyncClient, rider: dict[str, str]) -> None:
    """EMP-02: landmark max 200 characters."""
    response = await client.post("/ride-requests", json=payload(landmark="x" * 201), headers=rider)
    assert response.status_code == 422


async def test_high_urgency_and_no_sharing_round_trip(
    client: AsyncClient, rider: dict[str, str]
) -> None:
    body = (
        await client.post(
            "/ride-requests",
            json=payload(
                urgency=str(Urgency.high), no_sharing=True, direction=str(Direction.from_office)
            ),
            headers=rider,
        )
    ).json()
    assert body["urgency"] == "high"
    assert body["no_sharing"] is True
    assert body["direction"] == "from_office"
