"""Admin CRUD for clients, offices, vehicles, drivers and invites (B06).

Acceptance: CRUD endpoints pass contract and permission tests. The permission half
matters most — `roles-and-permissions.md` wants a denied test per endpoint, and the
supervisor "status only" row is the one that needs a field-level check, not just a
route-level one.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.core.security import create_access_token
from app.core.settings import Settings
from app.domain.enums import CLIENT_SCOPED_ROLES, Role
from app.main import create_app
from tests.builders import make_client, make_operator, make_user, make_user_role, unique_phone

NOW = datetime(2026, 9, 24, 4, 30, tzinfo=UTC)
JWT_SECRET = "admin-tests-secret-0123456789abcdefgh"

NOIDA = {"lat": 28.5703, "lng": 77.3218}


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest_asyncio.fixture
async def operator_id(db_session: AsyncSession) -> uuid.UUID:
    operator = make_operator()
    db_session.add(operator)
    await db_session.flush()
    return operator.id


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


async def headers_for(
    role: Role,
    operator_id: uuid.UUID | None,
    clock: FakeClock,
    db_session: AsyncSession,
    client_id: uuid.UUID | None = None,
) -> dict[str, str]:
    user = make_user()
    db_session.add(user)
    await db_session.flush()
    if operator_id is not None:
        scope = client_id
        if role in CLIENT_SCOPED_ROLES and scope is None:
            corporate = make_client(operator_id, f"Scope {uuid.uuid4().hex[:6]}")
            db_session.add(corporate)
            await db_session.flush()
            scope = corporate.id
        db_session.add(make_user_role(user.id, role, operator_id=operator_id, client_id=scope))
        await db_session.flush()

    token, _ = create_access_token(
        user_id=user.id,
        role=str(role),
        secret=JWT_SECRET,
        clock=clock,
        ttl_seconds=900,
        operator_id=operator_id,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin(
    operator_id: uuid.UUID, clock: FakeClock, db_session: AsyncSession
) -> dict[str, str]:
    return await headers_for(Role.operator_admin, operator_id, clock, db_session)


# --- clients --------------------------------------------------------------------


async def test_create_and_list_clients(client: AsyncClient, admin: dict[str, str]) -> None:
    created = await client.post("/admin/clients", json={"name": "Acme Corp"}, headers=admin)
    assert created.status_code == 201
    assert created.json()["name"] == "Acme Corp"

    listed = await client.get("/admin/clients", headers=admin)
    assert listed.status_code == 200
    assert [c["name"] for c in listed.json()["items"]] == ["Acme Corp"]


async def test_duplicate_client_name_is_rejected(
    client: AsyncClient, admin: dict[str, str]
) -> None:
    await client.post("/admin/clients", json={"name": "Acme Corp"}, headers=admin)
    again = await client.post("/admin/clients", json={"name": "Acme Corp"}, headers=admin)
    assert again.status_code == 409
    assert again.json()["code"] == "conflict"


async def test_client_contact_phone_must_be_e164(
    client: AsyncClient, admin: dict[str, str]
) -> None:
    response = await client.post(
        "/admin/clients", json={"name": "Acme", "contact_phone": "9812345678"}, headers=admin
    )
    assert response.status_code == 422


async def test_clients_are_scoped_to_the_operator(
    client: AsyncClient, clock: FakeClock, db_session: AsyncSession, admin: dict[str, str]
) -> None:
    await client.post("/admin/clients", json={"name": "Acme Corp"}, headers=admin)

    other = make_operator("Rival Cabs")
    db_session.add(other)
    await db_session.flush()
    rival = await headers_for(Role.operator_admin, other.id, clock, db_session)

    listed = await client.get("/admin/clients", headers=rival)
    assert listed.json()["items"] == []


# --- offices ---------------------------------------------------------------------


async def test_create_and_list_offices(client: AsyncClient, admin: dict[str, str]) -> None:
    client_id = (await client.post("/admin/clients", json={"name": "Acme"}, headers=admin)).json()[
        "id"
    ]

    created = await client.post(
        f"/admin/clients/{client_id}/offices",
        json={"name": "B200", "location": NOIDA, "address_text": "Sector 62"},
        headers=admin,
    )
    assert created.status_code == 201
    assert created.json()["location"] == NOIDA

    listed = await client.get(f"/admin/clients/{client_id}/offices", headers=admin)
    assert [o["name"] for o in listed.json()["items"]] == ["B200"]


async def test_office_location_round_trips_through_postgis(
    client: AsyncClient, admin: dict[str, str]
) -> None:
    client_id = (await client.post("/admin/clients", json={"name": "Acme"}, headers=admin)).json()[
        "id"
    ]
    await client.post(
        f"/admin/clients/{client_id}/offices",
        json={"name": "B200", "location": NOIDA},
        headers=admin,
    )
    listed = await client.get(f"/admin/clients/{client_id}/offices", headers=admin)
    location = listed.json()["items"][0]["location"]
    assert round(location["lat"], 4) == NOIDA["lat"]
    assert round(location["lng"], 4) == NOIDA["lng"]


async def test_office_for_another_operators_client_is_not_found(
    client: AsyncClient, clock: FakeClock, db_session: AsyncSession, admin: dict[str, str]
) -> None:
    """Guessing a UUID must not let an admin attach an office to a foreign client."""
    other = make_operator("Rival Cabs")
    db_session.add(other)
    await db_session.flush()
    foreign_client = make_client(other.id, "Rival's customer")
    db_session.add(foreign_client)
    await db_session.flush()

    response = await client.post(
        f"/admin/clients/{foreign_client.id}/offices",
        json={"name": "Sneaky", "location": NOIDA},
        headers=admin,
    )
    assert response.status_code == 404


async def test_office_requires_a_location(client: AsyncClient, admin: dict[str, str]) -> None:
    client_id = (await client.post("/admin/clients", json={"name": "Acme"}, headers=admin)).json()[
        "id"
    ]
    response = await client.post(
        f"/admin/clients/{client_id}/offices", json={"name": "B200"}, headers=admin
    )
    assert response.status_code == 422


async def test_office_rejects_an_impossible_coordinate(
    client: AsyncClient, admin: dict[str, str]
) -> None:
    client_id = (await client.post("/admin/clients", json={"name": "Acme"}, headers=admin)).json()[
        "id"
    ]
    response = await client.post(
        f"/admin/clients/{client_id}/offices",
        json={"name": "B200", "location": {"lat": 128.0, "lng": 77.0}},
        headers=admin,
    )
    assert response.status_code == 422


# --- vehicles ----------------------------------------------------------------------


VEHICLE = {"registration_no": "UP16AB1234", "vehicle_type": "sedan_4", "seat_capacity": 4}


async def test_create_and_list_vehicles(client: AsyncClient, admin: dict[str, str]) -> None:
    created = await client.post("/admin/vehicles", json=VEHICLE, headers=admin)
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "off_duty", "a new vehicle is not on duty"
    assert body["tracker_type"] == "app"

    listed = await client.get("/admin/vehicles", headers=admin)
    assert [v["registration_no"] for v in listed.json()["items"]] == ["UP16AB1234"]


async def test_duplicate_registration_is_rejected(
    client: AsyncClient, admin: dict[str, str]
) -> None:
    await client.post("/admin/vehicles", json=VEHICLE, headers=admin)
    again = await client.post("/admin/vehicles", json=VEHICLE, headers=admin)
    assert again.status_code == 409


async def test_seat_capacity_bounds(client: AsyncClient, admin: dict[str, str]) -> None:
    too_big = {**VEHICLE, "seat_capacity": 13}
    assert (await client.post("/admin/vehicles", json=too_big, headers=admin)).status_code == 422
    too_small = {**VEHICLE, "registration_no": "X", "seat_capacity": 0}
    assert (await client.post("/admin/vehicles", json=too_small, headers=admin)).status_code == 422


async def test_unknown_vehicle_type_is_rejected(client: AsyncClient, admin: dict[str, str]) -> None:
    response = await client.post(
        "/admin/vehicles", json={**VEHICLE, "vehicle_type": "hovercraft"}, headers=admin
    )
    assert response.status_code == 422


async def test_vehicles_can_be_filtered_by_status(
    client: AsyncClient, admin: dict[str, str]
) -> None:
    await client.post("/admin/vehicles", json=VEHICLE, headers=admin)
    assert (
        len((await client.get("/admin/vehicles?status=off_duty", headers=admin)).json()["items"])
        == 1
    )
    assert (
        len((await client.get("/admin/vehicles?status=on_trip", headers=admin)).json()["items"])
        == 0
    )


async def test_update_a_vehicle(client: AsyncClient, admin: dict[str, str]) -> None:
    vehicle_id = (await client.post("/admin/vehicles", json=VEHICLE, headers=admin)).json()["id"]
    response = await client.patch(
        f"/admin/vehicles/{vehicle_id}",
        json={"model": "Dzire", "seat_capacity": 5},
        headers=admin,
    )
    assert response.status_code == 200
    assert response.json()["model"] == "Dzire"
    assert response.json()["seat_capacity"] == 5


async def test_patch_only_changes_what_was_sent(client: AsyncClient, admin: dict[str, str]) -> None:
    """An omitted field must keep its value, not become null."""
    vehicle_id = (
        await client.post("/admin/vehicles", json={**VEHICLE, "model": "Dzire"}, headers=admin)
    ).json()["id"]
    response = await client.patch(
        f"/admin/vehicles/{vehicle_id}", json={"seat_capacity": 5}, headers=admin
    )
    assert response.json()["model"] == "Dzire"


async def test_empty_patch_is_rejected(client: AsyncClient, admin: dict[str, str]) -> None:
    vehicle_id = (await client.post("/admin/vehicles", json=VEHICLE, headers=admin)).json()["id"]
    response = await client.patch(f"/admin/vehicles/{vehicle_id}", json={}, headers=admin)
    assert response.status_code == 422


async def test_updating_another_operators_vehicle_is_not_found(
    client: AsyncClient, clock: FakeClock, db_session: AsyncSession, admin: dict[str, str]
) -> None:
    other = make_operator("Rival Cabs")
    db_session.add(other)
    await db_session.flush()
    rival = await headers_for(Role.operator_admin, other.id, clock, db_session)

    vehicle_id = (await client.post("/admin/vehicles", json=VEHICLE, headers=admin)).json()["id"]

    response = await client.patch(
        f"/admin/vehicles/{vehicle_id}", json={"model": "Stolen"}, headers=rival
    )
    assert response.status_code == 404


# --- drivers -----------------------------------------------------------------------


async def test_create_and_list_drivers(client: AsyncClient, admin: dict[str, str]) -> None:
    phone = unique_phone()
    created = await client.post(
        "/admin/drivers",
        json={"name": "Ravi", "phone": phone, "licence_last4": "4F2A"},
        headers=admin,
    )
    assert created.status_code == 201
    assert created.json()["active"] is True

    listed = await client.get("/admin/drivers", headers=admin)
    assert [d["name"] for d in listed.json()["items"]] == ["Ravi"]


async def test_duplicate_driver_phone_is_rejected(
    client: AsyncClient, admin: dict[str, str]
) -> None:
    phone = unique_phone()
    await client.post("/admin/drivers", json={"name": "Ravi", "phone": phone}, headers=admin)
    again = await client.post(
        "/admin/drivers", json={"name": "Ravi Twin", "phone": phone}, headers=admin
    )
    assert again.status_code == 409


async def test_licence_last4_format_is_enforced(client: AsyncClient, admin: dict[str, str]) -> None:
    response = await client.post(
        "/admin/drivers",
        json={"name": "Ravi", "phone": unique_phone(), "licence_last4": "toolong"},
        headers=admin,
    )
    assert response.status_code == 422


async def test_default_vehicle_must_belong_to_the_operator(
    client: AsyncClient, admin: dict[str, str]
) -> None:
    response = await client.post(
        "/admin/drivers",
        json={"name": "Ravi", "phone": unique_phone(), "default_vehicle_id": str(uuid.uuid4())},
        headers=admin,
    )
    assert response.status_code == 404


async def test_deactivate_a_driver(client: AsyncClient, admin: dict[str, str]) -> None:
    driver_id = (
        await client.post(
            "/admin/drivers", json={"name": "Ravi", "phone": unique_phone()}, headers=admin
        )
    ).json()["id"]
    response = await client.patch(
        f"/admin/drivers/{driver_id}", json={"active": False}, headers=admin
    )
    assert response.status_code == 200
    assert response.json()["active"] is False


async def test_assigning_a_vehicle_to_a_driver(client: AsyncClient, admin: dict[str, str]) -> None:
    vehicle_id = (await client.post("/admin/vehicles", json=VEHICLE, headers=admin)).json()["id"]
    driver_id = (
        await client.post(
            "/admin/drivers", json={"name": "Ravi", "phone": unique_phone()}, headers=admin
        )
    ).json()["id"]

    response = await client.patch(
        f"/admin/drivers/{driver_id}", json={"default_vehicle_id": vehicle_id}, headers=admin
    )
    assert response.status_code == 200
    assert response.json()["default_vehicle_id"] == vehicle_id


# --- invites ------------------------------------------------------------------------


async def test_invite_a_supervisor(client: AsyncClient, admin: dict[str, str]) -> None:
    response = await client.post(
        "/admin/users/invite",
        json={"phone": unique_phone(), "name": "Sita", "role": "supervisor"},
        headers=admin,
    )
    assert response.status_code == 201
    assert response.json()["role"] == "supervisor"


async def test_inviting_the_same_role_twice_conflicts(
    client: AsyncClient, admin: dict[str, str]
) -> None:
    phone = unique_phone()
    payload = {"phone": phone, "name": "Sita", "role": "supervisor"}
    await client.post("/admin/users/invite", json=payload, headers=admin)
    again = await client.post("/admin/users/invite", json=payload, headers=admin)
    assert again.status_code == 409


async def test_an_existing_user_gains_a_role_rather_than_a_duplicate_account(
    client: AsyncClient, admin: dict[str, str], db_session: AsyncSession
) -> None:
    """Login is phone-based, so a second account on the same number would be unusable."""
    from sqlalchemy import func, select

    from app.modules.auth.models import AppUser

    phone = unique_phone()
    await client.post(
        "/admin/users/invite",
        json={"phone": phone, "name": "Sita", "role": "supervisor"},
        headers=admin,
    )
    await client.post(
        "/admin/users/invite",
        json={"phone": phone, "name": "Sita", "role": "operator_admin"},
        headers=admin,
    )

    count = await db_session.scalar(
        select(func.count()).select_from(AppUser).where(AppUser.phone == phone)
    )
    assert count == 1


async def test_client_admin_invite_requires_a_client(
    client: AsyncClient, admin: dict[str, str]
) -> None:
    response = await client.post(
        "/admin/users/invite",
        json={"phone": unique_phone(), "name": "Meera", "role": "client_admin"},
        headers=admin,
    )
    assert response.status_code == 422


async def test_client_admin_invite_with_a_client(
    client: AsyncClient, admin: dict[str, str]
) -> None:
    client_id = (await client.post("/admin/clients", json={"name": "Acme"}, headers=admin)).json()[
        "id"
    ]
    response = await client.post(
        "/admin/users/invite",
        json={
            "phone": unique_phone(),
            "name": "Meera",
            "role": "client_admin",
            "client_id": client_id,
        },
        headers=admin,
    )
    assert response.status_code == 201
    assert response.json()["client_id"] == client_id


async def test_drivers_cannot_be_invited(client: AsyncClient, admin: dict[str, str]) -> None:
    """Drivers are created as driver records, not invited as users."""
    response = await client.post(
        "/admin/users/invite",
        json={"phone": unique_phone(), "name": "Ravi", "role": "driver"},
        headers=admin,
    )
    assert response.status_code == 422


# --- permissions -----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("get", "/admin/clients", None),
        ("post", "/admin/clients", {"name": "X"}),
        ("get", "/admin/vehicles", None),
        ("post", "/admin/vehicles", VEHICLE),
        ("get", "/admin/drivers", None),
        ("post", "/admin/drivers", {"name": "R", "phone": "+919812345678"}),
        (
            "post",
            "/admin/users/invite",
            {"phone": "+919812345678", "name": "S", "role": "supervisor"},
        ),
    ],
)
async def test_every_admin_endpoint_rejects_an_employee(
    client: AsyncClient,
    operator_id: uuid.UUID,
    clock: FakeClock,
    db_session: AsyncSession,
    method: str,
    path: str,
    payload: dict[str, object] | None,
) -> None:
    """roles-and-permissions.md: every endpoint has a denied test."""
    headers = await headers_for(Role.employee, operator_id, clock, db_session)
    # httpx's get() takes no json argument, so only pass a body where there is one.
    kwargs: dict[str, object] = {"headers": headers}
    if payload is not None:
        kwargs["json"] = payload
    response = await getattr(client, method)(path, **kwargs)
    assert response.status_code == 403


async def test_supervisor_may_change_vehicle_status(
    client: AsyncClient,
    operator_id: uuid.UUID,
    clock: FakeClock,
    db_session: AsyncSession,
    admin: dict[str, str],
) -> None:
    vehicle_id = (await client.post("/admin/vehicles", json=VEHICLE, headers=admin)).json()["id"]
    supervisor = await headers_for(Role.supervisor, operator_id, clock, db_session)

    response = await client.patch(
        f"/admin/vehicles/{vehicle_id}", json={"status": "out_of_service"}, headers=supervisor
    )
    assert response.status_code == 200
    assert response.json()["status"] == "out_of_service"


async def test_supervisor_may_not_change_other_vehicle_fields(
    client: AsyncClient,
    operator_id: uuid.UUID,
    clock: FakeClock,
    db_session: AsyncSession,
    admin: dict[str, str],
) -> None:
    """ "Manage vehicles: supervisor = status only" is a field-level rule, not a route one."""
    vehicle_id = (await client.post("/admin/vehicles", json=VEHICLE, headers=admin)).json()["id"]
    supervisor = await headers_for(Role.supervisor, operator_id, clock, db_session)

    response = await client.patch(
        f"/admin/vehicles/{vehicle_id}", json={"seat_capacity": 6}, headers=supervisor
    )
    assert response.status_code == 403
    assert response.json()["details"]["fields"] == ["seat_capacity"]


async def test_supervisor_cannot_add_a_vehicle(
    client: AsyncClient, operator_id: uuid.UUID, clock: FakeClock, db_session: AsyncSession
) -> None:
    supervisor = await headers_for(Role.supervisor, operator_id, clock, db_session)
    response = await client.post("/admin/vehicles", json=VEHICLE, headers=supervisor)
    assert response.status_code == 403


async def test_supervisor_cannot_manage_clients(
    client: AsyncClient, operator_id: uuid.UUID, clock: FakeClock, db_session: AsyncSession
) -> None:
    supervisor = await headers_for(Role.supervisor, operator_id, clock, db_session)
    assert (await client.get("/admin/clients", headers=supervisor)).status_code == 403


async def test_supervisor_cannot_invite_users(
    client: AsyncClient, operator_id: uuid.UUID, clock: FakeClock, db_session: AsyncSession
) -> None:
    supervisor = await headers_for(Role.supervisor, operator_id, clock, db_session)
    response = await client.post(
        "/admin/users/invite",
        json={"phone": unique_phone(), "name": "S", "role": "supervisor"},
        headers=supervisor,
    )
    assert response.status_code == 403


async def test_admin_endpoints_require_authentication(client: AsyncClient) -> None:
    assert (await client.get("/admin/vehicles")).status_code == 401
    assert (await client.get("/admin/clients")).status_code == 401
