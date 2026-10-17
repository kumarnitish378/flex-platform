"""Mode settings end to end (B24).

The precedence itself is proved exhaustively in `tests/unit/test_modes.py`, against the
pure resolver. This file proves the parts that need a database: that settings persist
with their scoping intact, that a real `RideRequest` resolves through them, that the
emergency pause still beats everything once it is a column rather than an argument, and
that the overlap warning reaches the screen.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.core.geo import to_point
from app.core.security import create_access_token
from app.core.settings import Settings
from app.domain.enums import CLIENT_SCOPED_ROLES, Direction, Role, Urgency
from app.domain.modes import Mode, ModeReason
from app.domain.state_machines import RequestStatus
from app.main import create_app
from app.modules.requests.models import RideRequest
from tests.builders import (
    make_client,
    make_employee,
    make_office,
    make_operator,
    make_user,
    make_user_role,
    unique_phone,
)

pytestmark = pytest.mark.requires_db

#: Thursday 09:00.
NOW = datetime(2026, 10, 15, 9, 0, tzinfo=UTC)
#: 19:00 and 09:00 in Asia/Kolkata, the timezone `make_operator` gives an operator.
#: Mode windows are written in the operator's wall clock, so a test that states its
#: times in UTC is testing a different hour than the one it reads like.
IST_EVENING = datetime(2026, 10, 15, 13, 30, tzinfo=UTC)
IST_MORNING = datetime(2026, 10, 15, 3, 30, tzinfo=UTC)
JWT_SECRET = "mode-tests-secret-0123456789abcdefgh"
HOME = (28.5300, 77.4000)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest_asyncio.fixture
async def world(db_session: AsyncSession) -> dict[str, object]:
    operator = make_operator()
    db_session.add(operator)
    await db_session.flush()
    corporate = make_client(operator.id)
    db_session.add(corporate)
    await db_session.flush()
    office = make_office(operator.id, corporate.id)
    db_session.add(office)
    await db_session.flush()
    employee = make_employee(operator.id, corporate.id, office.id, phone=unique_phone())
    db_session.add(employee)
    await db_session.flush()
    return {
        "operator": operator,
        "client": corporate,
        "office": office,
        "employee": employee,
    }


async def make_ride_request(
    db_session: AsyncSession, world: dict[str, object], *, at: datetime | None = None
) -> RideRequest:
    operator = world["operator"]
    request = RideRequest(
        id=uuid.uuid4(),
        operator_id=operator.id,  # type: ignore[attr-defined]
        client_id=world["client"].id,  # type: ignore[attr-defined]
        employee_id=world["employee"].id,  # type: ignore[attr-defined]
        direction=str(Direction.to_office),
        office_id=world["office"].id,  # type: ignore[attr-defined]
        location=to_point(*HOME),
        requested_time=at or NOW,
        urgency=str(Urgency.medium),
        status=str(RequestStatus.queued),
        queued_at=NOW,
        expires_at=NOW + timedelta(hours=2),
    )
    db_session.add(request)
    await db_session.flush()
    return request


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


async def token_for(
    role: Role, operator_id: uuid.UUID, clock: FakeClock, db_session: AsyncSession
) -> dict[str, str]:
    user = make_user()
    db_session.add(user)
    await db_session.flush()
    client_id = None
    if role in CLIENT_SCOPED_ROLES:
        corporate = make_client(operator_id)
        db_session.add(corporate)
        await db_session.flush()
        client_id = corporate.id
    db_session.add(make_user_role(user.id, role, operator_id=operator_id, client_id=client_id))
    await db_session.flush()
    access, _ = create_access_token(
        user_id=user.id,
        role=str(role),
        secret=JWT_SECRET,
        clock=clock,
        ttl_seconds=900,
        operator_id=operator_id,
    )
    return {"Authorization": f"Bearer {access}"}


# --- CRUD ---------------------------------------------------------------------


async def test_a_setting_round_trips_with_its_scoping_intact(
    client: AsyncClient, world: dict[str, object], clock: FakeClock, db_session: AsyncSession
) -> None:
    operator = world["operator"]
    headers = await token_for(Role.operator_admin, operator.id, clock, db_session)  # type: ignore[attr-defined]

    created = await client.post(
        "/admin/mode-settings",
        json={
            "mode": "semi_auto",
            "client_id": str(world["client"].id),  # type: ignore[attr-defined]
            "direction": "from_office",
            "weekdays": [5, 1, 1],
            "start_time": "18:00:00",
            "end_time": "22:00:00",
            "note": "evening peak for Acme",
        },
        headers=headers,
    )

    assert created.status_code == 201
    body = created.json()
    assert body["mode"] == "semi_auto"
    assert body["direction"] == "from_office"
    # Deduplicated and sorted on the way in, so the screen renders it the same every time.
    assert body["weekdays"] == [1, 5]
    assert body["note"] == "evening peak for Acme"

    listed = (await client.get("/admin/mode-settings", headers=headers)).json()
    assert [item["id"] for item in listed["items"]] == [body["id"]]


async def test_a_half_written_time_window_is_refused(
    client: AsyncClient, world: dict[str, object], clock: FakeClock, db_session: AsyncSession
) -> None:
    """Guessing midnight for the missing end would stop a "from 18:00" rule at
    midnight, which is exactly when an evening shift is still running."""
    headers = await token_for(Role.operator_admin, world["operator"].id, clock, db_session)  # type: ignore[attr-defined]

    response = await client.post(
        "/admin/mode-settings",
        json={"mode": "semi_auto", "start_time": "18:00:00"},
        headers=headers,
    )

    assert response.status_code == 422


async def test_a_weekday_outside_the_week_is_refused(
    client: AsyncClient, world: dict[str, object], clock: FakeClock, db_session: AsyncSession
) -> None:
    headers = await token_for(Role.operator_admin, world["operator"].id, clock, db_session)  # type: ignore[attr-defined]

    response = await client.post(
        "/admin/mode-settings",
        json={"mode": "semi_auto", "weekdays": [0]},
        headers=headers,
    )

    assert response.status_code == 422


async def test_a_setting_can_be_replaced_and_deleted(
    client: AsyncClient, world: dict[str, object], clock: FakeClock, db_session: AsyncSession
) -> None:
    headers = await token_for(Role.operator_admin, world["operator"].id, clock, db_session)  # type: ignore[attr-defined]
    created = (
        await client.post("/admin/mode-settings", json={"mode": "manual"}, headers=headers)
    ).json()

    updated = await client.put(
        f"/admin/mode-settings/{created['id']}",
        json={"mode": "full_auto"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["mode"] == "full_auto"

    deleted = await client.delete(f"/admin/mode-settings/{created['id']}", headers=headers)
    assert deleted.status_code == 204
    assert (await client.get("/admin/mode-settings", headers=headers)).json()["items"] == []


async def test_one_operators_settings_are_invisible_to_another(
    client: AsyncClient, world: dict[str, object], clock: FakeClock, db_session: AsyncSession
) -> None:
    """Tenancy, on a table whose rows decide how the platform behaves."""
    mine = await token_for(Role.operator_admin, world["operator"].id, clock, db_session)  # type: ignore[attr-defined]
    await client.post("/admin/mode-settings", json={"mode": "full_auto"}, headers=mine)

    stranger = make_operator("Rival Cabs")
    db_session.add(stranger)
    await db_session.flush()
    theirs = await token_for(Role.operator_admin, stranger.id, clock, db_session)

    assert (await client.get("/admin/mode-settings", headers=theirs)).json()["items"] == []


# --- resolution ----------------------------------------------------------------


async def test_with_no_settings_a_request_is_on_manual(
    client: AsyncClient, world: dict[str, object], clock: FakeClock, db_session: AsyncSession
) -> None:
    """Phase 1's behaviour, and the right thing to inherit: an upgrade must not
    silently start assigning."""
    headers = await token_for(Role.supervisor, world["operator"].id, clock, db_session)  # type: ignore[attr-defined]
    request = await make_ride_request(db_session, world)

    body = (await client.get(f"/dispatch/requests/{request.id}/mode", headers=headers)).json()

    assert body["mode"] == str(Mode.manual)
    assert body["reason"] == str(ModeReason.operator_default)


async def test_a_client_rule_governs_that_clients_request(
    client: AsyncClient, world: dict[str, object], clock: FakeClock, db_session: AsyncSession
) -> None:
    admin = await token_for(Role.operator_admin, world["operator"].id, clock, db_session)  # type: ignore[attr-defined]
    supervisor = await token_for(Role.supervisor, world["operator"].id, clock, db_session)  # type: ignore[attr-defined]
    created = (
        await client.post(
            "/admin/mode-settings",
            json={"mode": "semi_auto", "client_id": str(world["client"].id)},  # type: ignore[attr-defined]
            headers=admin,
        )
    ).json()
    request = await make_ride_request(db_session, world)

    body = (await client.get(f"/dispatch/requests/{request.id}/mode", headers=supervisor)).json()

    assert body["mode"] == str(Mode.semi_auto)
    assert body["reason"] == str(ModeReason.client)
    assert body["setting_id"] == created["id"]


async def test_the_emergency_pause_overrides_every_setting(
    client: AsyncClient, world: dict[str, object], clock: FakeClock, db_session: AsyncSession
) -> None:
    """The one switch an operator reaches for when the system misbehaves."""
    admin = await token_for(Role.operator_admin, world["operator"].id, clock, db_session)  # type: ignore[attr-defined]
    supervisor = await token_for(Role.supervisor, world["operator"].id, clock, db_session)  # type: ignore[attr-defined]
    await client.post(
        "/admin/mode-settings",
        json={"mode": "full_auto", "client_id": str(world["client"].id)},  # type: ignore[attr-defined]
        headers=admin,
    )
    request = await make_ride_request(db_session, world)

    world["operator"].automation_paused = True  # type: ignore[attr-defined]
    await db_session.flush()

    body = (await client.get(f"/dispatch/requests/{request.id}/mode", headers=supervisor)).json()

    assert body["mode"] == str(Mode.manual)
    assert body["reason"] == str(ModeReason.automation_paused)


async def test_a_vip_resolves_to_full_auto(
    client: AsyncClient, world: dict[str, object], clock: FakeClock, db_session: AsyncSession
) -> None:
    """§2 level 2. Whether a VIP vehicle is free is dispatch's question, not this one's."""
    supervisor = await token_for(Role.supervisor, world["operator"].id, clock, db_session)  # type: ignore[attr-defined]
    world["employee"].is_vip = True  # type: ignore[attr-defined]
    await db_session.flush()
    request = await make_ride_request(db_session, world)

    body = (await client.get(f"/dispatch/requests/{request.id}/mode", headers=supervisor)).json()

    assert body["mode"] == str(Mode.full_auto)
    assert body["reason"] == str(ModeReason.vip)


async def test_the_window_is_judged_on_the_requested_time_not_now(
    client: AsyncClient, world: dict[str, object], clock: FakeClock, db_session: AsyncSession
) -> None:
    """A rule for "evenings" must govern a ride booked at lunchtime for 19:00.

    Judging it by the clock instead would govern the morning bookings and miss the
    evening ones - the exact inverse of what the operator wrote.

    **The times here are the operator's, not UTC**, which is the second half of the
    same point: `18:00-22:00` is a wall clock in Asia/Kolkata, so the evening ride is
    stored as 13:30 UTC and the morning one as 03:30. Written in UTC this test passed
    while the implementation compared a UTC time of day against a local window - five
    and a half hours out, which made the rule govern 00:30 to 04:30 local (B28).
    """
    admin = await token_for(Role.operator_admin, world["operator"].id, clock, db_session)  # type: ignore[attr-defined]
    supervisor = await token_for(Role.supervisor, world["operator"].id, clock, db_session)  # type: ignore[attr-defined]
    await client.post(
        "/admin/mode-settings",
        json={"mode": "semi_auto", "start_time": "18:00:00", "end_time": "22:00:00"},
        headers=admin,
    )

    # It is early afternoon now; the ride is for 19:00 **local**, which is 13:30 UTC.
    evening = await make_ride_request(db_session, world, at=IST_EVENING)
    morning = await make_ride_request(db_session, world, at=IST_MORNING)

    evening_body = (
        await client.get(f"/dispatch/requests/{evening.id}/mode", headers=supervisor)
    ).json()
    morning_body = (
        await client.get(f"/dispatch/requests/{morning.id}/mode", headers=supervisor)
    ).json()

    assert evening_body["mode"] == str(Mode.semi_auto)
    assert morning_body["mode"] == str(Mode.manual)


# --- overlap warning ------------------------------------------------------------


async def test_overlapping_settings_are_reported_to_the_screen(
    client: AsyncClient, world: dict[str, object], clock: FakeClock, db_session: AsyncSession
) -> None:
    """§2 resolves them by update time, which is a deterministic answer to a question
    the operator probably did not mean to ask."""
    headers = await token_for(Role.operator_admin, world["operator"].id, clock, db_session)  # type: ignore[attr-defined]
    client_id = str(world["client"].id)  # type: ignore[attr-defined]
    first = (
        await client.post(
            "/admin/mode-settings",
            json={"mode": "manual", "client_id": client_id},
            headers=headers,
        )
    ).json()
    second = (
        await client.post(
            "/admin/mode-settings",
            json={"mode": "full_auto", "client_id": client_id},
            headers=headers,
        )
    ).json()

    listed = (await client.get("/admin/mode-settings", headers=headers)).json()

    assert listed["overlapping"] == [[first["id"], second["id"]]]


async def test_rules_for_different_clients_do_not_warn(
    client: AsyncClient, world: dict[str, object], clock: FakeClock, db_session: AsyncSession
) -> None:
    """A warning on every pair of client rules is a warning nobody reads."""
    headers = await token_for(Role.operator_admin, world["operator"].id, clock, db_session)  # type: ignore[attr-defined]
    other = make_client(world["operator"].id, name="Other Co")  # type: ignore[attr-defined]
    db_session.add(other)
    await db_session.flush()

    for client_id in (world["client"].id, other.id):  # type: ignore[attr-defined]
        await client.post(
            "/admin/mode-settings",
            json={"mode": "semi_auto", "client_id": str(client_id)},
            headers=headers,
        )

    listed = (await client.get("/admin/mode-settings", headers=headers)).json()

    assert listed["overlapping"] == []
