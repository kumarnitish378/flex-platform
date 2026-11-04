"""Employee endpoints and CSV import (B07).

Acceptance: a 500-row import reports errors per row, and a dry run writes nothing.
The scope tests matter just as much — a client_admin must never reach another client's
roster.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.core.security import create_access_token
from app.core.settings import Settings
from app.domain.enums import CLIENT_SCOPED_ROLES, Role
from app.main import create_app
from app.modules.people.models import Employee
from tests.builders import make_client, make_office, make_operator, make_user, make_user_role

NOW = datetime(2026, 9, 24, 4, 30, tzinfo=UTC)
JWT_SECRET = "employee-tests-secret-0123456789abcd"

HEADER = "name,phone,office_name,home_lat,home_lng,landmark,priority,is_vip"


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest_asyncio.fixture
async def world(db_session: AsyncSession) -> dict[str, uuid.UUID]:
    """One operator, one client, one office called B200."""
    operator = make_operator()
    db_session.add(operator)
    await db_session.flush()
    corporate = make_client(operator.id, "Acme")
    db_session.add(corporate)
    await db_session.flush()
    office = make_office(operator.id, corporate.id, "B200")
    db_session.add(office)
    await db_session.flush()
    return {"operator_id": operator.id, "client_id": corporate.id, "office_id": office.id}


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
    operator_id: uuid.UUID,
    clock: FakeClock,
    db_session: AsyncSession,
    client_id: uuid.UUID | None = None,
) -> dict[str, str]:
    user = make_user()
    db_session.add(user)
    await db_session.flush()
    scope = client_id if role in CLIENT_SCOPED_ROLES else None
    db_session.add(make_user_role(user.id, role, operator_id=operator_id, client_id=scope))
    await db_session.flush()

    token, _ = create_access_token(
        user_id=user.id,
        role=str(role),
        secret=JWT_SECRET,
        clock=clock,
        ttl_seconds=900,
        operator_id=operator_id,
        client_id=scope,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin(
    world: dict[str, uuid.UUID], clock: FakeClock, db_session: AsyncSession
) -> dict[str, str]:
    return await headers_for(Role.operator_admin, world["operator_id"], clock, db_session)


def employee_payload(office_id: uuid.UUID, phone: str = "+919812345678") -> dict[str, object]:
    return {
        "name": "Asha",
        "phone": phone,
        "office_id": str(office_id),
        "home_location": {"lat": 28.5123, "lng": 77.3910},
        "home_landmark": "Near temple",
        "priority": 3,
    }


def upload(content: str) -> dict[str, tuple[str, bytes, str]]:
    return {"file": ("employees.csv", content.encode("utf-8"), "text/csv")}


# --- CRUD -----------------------------------------------------------------------


async def test_create_and_list_employees(
    client: AsyncClient, world: dict[str, uuid.UUID], admin: dict[str, str]
) -> None:
    created = await client.post(
        f"/admin/clients/{world['client_id']}/employees",
        json=employee_payload(world["office_id"]),
        headers=admin,
    )
    assert created.status_code == 201
    body = created.json()
    assert body["name"] == "Asha"
    assert body["priority"] == 3
    assert body["zone_id"] is None, "zone derivation is a stub until zones exist"
    assert body["home_location"]["lat"] == pytest.approx(28.5123, abs=1e-4)

    listed = await client.get(f"/admin/clients/{world['client_id']}/employees", headers=admin)
    assert [e["name"] for e in listed.json()["items"]] == ["Asha"]


async def test_defaults_are_applied(
    client: AsyncClient, world: dict[str, uuid.UUID], admin: dict[str, str]
) -> None:
    payload = employee_payload(world["office_id"])
    del payload["priority"]
    created = await client.post(
        f"/admin/clients/{world['client_id']}/employees", json=payload, headers=admin
    )
    body = created.json()
    assert body["priority"] == 5
    assert body["is_vip"] is False
    assert body["active"] is True


async def test_duplicate_phone_in_a_client_is_rejected(
    client: AsyncClient, world: dict[str, uuid.UUID], admin: dict[str, str]
) -> None:
    payload = employee_payload(world["office_id"])
    await client.post(f"/admin/clients/{world['client_id']}/employees", json=payload, headers=admin)
    again = await client.post(
        f"/admin/clients/{world['client_id']}/employees", json=payload, headers=admin
    )
    assert again.status_code == 409


async def test_office_must_belong_to_the_client(
    client: AsyncClient, world: dict[str, uuid.UUID], admin: dict[str, str]
) -> None:
    payload = employee_payload(uuid.uuid4())
    response = await client.post(
        f"/admin/clients/{world['client_id']}/employees", json=payload, headers=admin
    )
    assert response.status_code == 404


async def test_update_an_employee(
    client: AsyncClient, world: dict[str, uuid.UUID], admin: dict[str, str]
) -> None:
    employee_id = (
        await client.post(
            f"/admin/clients/{world['client_id']}/employees",
            json=employee_payload(world["office_id"]),
            headers=admin,
        )
    ).json()["id"]

    response = await client.patch(
        f"/admin/employees/{employee_id}", json={"priority": 1, "is_vip": True}, headers=admin
    )
    assert response.status_code == 200
    assert response.json()["priority"] == 1
    assert response.json()["is_vip"] is True
    assert response.json()["name"] == "Asha", "an omitted field keeps its value"


async def test_deactivate_an_employee(
    client: AsyncClient, world: dict[str, uuid.UUID], admin: dict[str, str]
) -> None:
    employee_id = (
        await client.post(
            f"/admin/clients/{world['client_id']}/employees",
            json=employee_payload(world["office_id"]),
            headers=admin,
        )
    ).json()["id"]
    response = await client.patch(
        f"/admin/employees/{employee_id}", json={"active": False}, headers=admin
    )
    assert response.json()["active"] is False


async def test_priority_bounds_are_enforced(
    client: AsyncClient, world: dict[str, uuid.UUID], admin: dict[str, str]
) -> None:
    payload = {**employee_payload(world["office_id"]), "priority": 11}
    response = await client.post(
        f"/admin/clients/{world['client_id']}/employees", json=payload, headers=admin
    )
    assert response.status_code == 422


# --- client scoping ---------------------------------------------------------------


async def test_client_admin_sees_only_their_own_client(
    client: AsyncClient,
    world: dict[str, uuid.UUID],
    clock: FakeClock,
    db_session: AsyncSession,
    admin: dict[str, str],
) -> None:
    other = make_client(world["operator_id"], "Other Corp")
    db_session.add(other)
    await db_session.flush()

    scoped = await headers_for(
        Role.client_admin, world["operator_id"], clock, db_session, client_id=world["client_id"]
    )

    assert (
        await client.get(f"/admin/clients/{world['client_id']}/employees", headers=scoped)
    ).status_code == 200
    forbidden = await client.get(f"/admin/clients/{other.id}/employees", headers=scoped)
    assert forbidden.status_code == 403


async def test_client_admin_cannot_add_to_another_client(
    client: AsyncClient,
    world: dict[str, uuid.UUID],
    clock: FakeClock,
    db_session: AsyncSession,
) -> None:
    other = make_client(world["operator_id"], "Other Corp")
    db_session.add(other)
    await db_session.flush()

    scoped = await headers_for(
        Role.client_admin, world["operator_id"], clock, db_session, client_id=world["client_id"]
    )
    response = await client.post(
        f"/admin/clients/{other.id}/employees",
        json=employee_payload(world["office_id"]),
        headers=scoped,
    )
    assert response.status_code == 403


async def test_client_admin_cannot_edit_another_clients_employee(
    client: AsyncClient,
    world: dict[str, uuid.UUID],
    clock: FakeClock,
    db_session: AsyncSession,
    admin: dict[str, str],
) -> None:
    employee_id = (
        await client.post(
            f"/admin/clients/{world['client_id']}/employees",
            json=employee_payload(world["office_id"]),
            headers=admin,
        )
    ).json()["id"]

    other = make_client(world["operator_id"], "Other Corp")
    db_session.add(other)
    await db_session.flush()
    scoped = await headers_for(
        Role.client_admin, world["operator_id"], clock, db_session, client_id=other.id
    )

    response = await client.patch(
        f"/admin/employees/{employee_id}", json={"priority": 1}, headers=scoped
    )
    assert response.status_code == 403


async def test_supervisor_cannot_manage_employees(
    client: AsyncClient,
    world: dict[str, uuid.UUID],
    clock: FakeClock,
    db_session: AsyncSession,
) -> None:
    supervisor = await headers_for(Role.supervisor, world["operator_id"], clock, db_session)
    response = await client.get(
        f"/admin/clients/{world['client_id']}/employees", headers=supervisor
    )
    assert response.status_code == 403


# --- CSV import ---------------------------------------------------------------------


async def test_dry_run_reports_without_writing(
    client: AsyncClient,
    world: dict[str, uuid.UUID],
    admin: dict[str, str],
    db_session: AsyncSession,
) -> None:
    """B07 acceptance: a dry run writes nothing."""
    content = f"{HEADER}\nAsha,+919812345678,B200,28.5,77.3,,3,no\n"
    response = await client.post(
        f"/admin/clients/{world['client_id']}/employees/import",
        files=upload(content),
        headers=admin,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total_rows"] == 1
    assert body["valid_rows"] == 1
    assert body["created"] == 0

    count = await db_session.scalar(select(func.count()).select_from(Employee))
    assert count == 0


async def test_dry_run_is_the_default(
    client: AsyncClient,
    world: dict[str, uuid.UUID],
    admin: dict[str, str],
    db_session: AsyncSession,
) -> None:
    """The safe option should need no thought - omitting the flag must not write."""
    content = f"{HEADER}\nAsha,+919812345678,B200,28.5,77.3,,3,no\n"
    await client.post(
        f"/admin/clients/{world['client_id']}/employees/import",
        files=upload(content),
        headers=admin,
    )
    assert await db_session.scalar(select(func.count()).select_from(Employee)) == 0


async def test_applying_the_import_creates_employees(
    client: AsyncClient,
    world: dict[str, uuid.UUID],
    admin: dict[str, str],
    db_session: AsyncSession,
) -> None:
    content = (
        f"{HEADER}\n"
        "Asha,+919812345678,B200,28.5,77.3,Near temple,3,yes\n"
        "Ravi,+919812345679,B200,28.6,77.4,,5,no\n"
    )
    response = await client.post(
        f"/admin/clients/{world['client_id']}/employees/import?dry_run=false",
        files=upload(content),
        headers=admin,
    )
    assert response.status_code == 200
    assert response.json()["created"] == 2

    employees = (await db_session.execute(select(Employee))).scalars().all()
    assert {e.name for e in employees} == {"Asha", "Ravi"}
    assert next(e for e in employees if e.name == "Asha").is_vip is True
    assert all(e.zone_id is None for e in employees), "zone derivation is a stub"


async def test_re_importing_updates_rather_than_duplicates(
    client: AsyncClient,
    world: dict[str, uuid.UUID],
    admin: dict[str, str],
    db_session: AsyncSession,
) -> None:
    first = f"{HEADER}\nAsha,+919812345678,B200,28.5,77.3,,5,no\n"
    second = f"{HEADER}\nAsha Kumar,+919812345678,B200,28.5,77.3,,1,yes\n"
    url = f"/admin/clients/{world['client_id']}/employees/import?dry_run=false"

    await client.post(url, files=upload(first), headers=admin)
    response = await client.post(url, files=upload(second), headers=admin)

    assert response.json() == {
        **response.json(),
        "created": 0,
        "updated": 1,
    }
    employee = (await db_session.execute(select(Employee))).scalars().one()
    assert employee.name == "Asha Kumar"
    assert employee.priority == 1
    assert employee.is_vip is True


async def test_unknown_office_is_reported_per_row(
    client: AsyncClient, world: dict[str, uuid.UUID], admin: dict[str, str]
) -> None:
    content = (
        f"{HEADER}\n"
        "Asha,+919812345678,B200,28.5,77.3,,3,no\n"
        "Ravi,+919812345679,Nowhere,28.6,77.4,,5,no\n"
    )
    response = await client.post(
        f"/admin/clients/{world['client_id']}/employees/import",
        files=upload(content),
        headers=admin,
    )
    body = response.json()
    assert body["valid_rows"] == 1
    assert body["errors"][0]["field"] == "office_name"
    assert body["errors"][0]["row"] == 3


async def test_bad_rows_do_not_block_good_ones_when_applied(
    client: AsyncClient,
    world: dict[str, uuid.UUID],
    admin: dict[str, str],
    db_session: AsyncSession,
) -> None:
    content = (
        f"{HEADER}\n"
        "Asha,+919812345678,B200,28.5,77.3,,3,no\n"
        "Broken,not-a-phone,B200,28.6,77.4,,5,no\n"
    )
    response = await client.post(
        f"/admin/clients/{world['client_id']}/employees/import?dry_run=false",
        files=upload(content),
        headers=admin,
    )
    assert response.json()["created"] == 1
    assert len(response.json()["errors"]) == 1
    assert await db_session.scalar(select(func.count()).select_from(Employee)) == 1


async def test_a_500_row_import_reports_errors_per_row(
    client: AsyncClient, world: dict[str, uuid.UUID], admin: dict[str, str]
) -> None:
    """B07 acceptance, through the endpoint."""
    rows = []
    for index in range(500):
        if index % 10 == 0:
            # Distinct bad values: identical ones would also trip the in-file
            # duplicate-phone check and double-count the errors.
            rows.append(f"Broken {index},not-a-phone-{index},B200,28.5,77.3,,5,no")
        else:
            rows.append(f"Person {index},+9198{index:08d},B200,28.5,77.3,,5,no")
    content = HEADER + "\n" + "\n".join(rows) + "\n"

    response = await client.post(
        f"/admin/clients/{world['client_id']}/employees/import",
        files=upload(content),
        headers=admin,
    )

    body = response.json()
    assert body["total_rows"] == 500
    assert body["valid_rows"] == 450
    assert len(body["errors"]) == 50
    assert all(error["field"] == "phone" for error in body["errors"])
    assert body["errors"][0]["row"] == 2


async def test_missing_column_is_a_422(
    client: AsyncClient, world: dict[str, uuid.UUID], admin: dict[str, str]
) -> None:
    content = "name,phone\nAsha,+919812345678\n"
    response = await client.post(
        f"/admin/clients/{world['client_id']}/employees/import",
        files=upload(content),
        headers=admin,
    )
    assert response.status_code == 422
    assert "office_name" in response.json()["message"]


async def test_empty_file_is_a_422(
    client: AsyncClient, world: dict[str, uuid.UUID], admin: dict[str, str]
) -> None:
    response = await client.post(
        f"/admin/clients/{world['client_id']}/employees/import",
        files=upload(""),
        headers=admin,
    )
    assert response.status_code == 422


async def test_non_utf8_file_is_a_422(
    client: AsyncClient, world: dict[str, uuid.UUID], admin: dict[str, str]
) -> None:
    files = {"file": ("employees.csv", b"\xff\xfe\x00bad", "text/csv")}
    response = await client.post(
        f"/admin/clients/{world['client_id']}/employees/import", files=files, headers=admin
    )
    assert response.status_code == 422
    assert "UTF-8" in response.json()["message"]


async def test_client_admin_cannot_import_into_another_client(
    client: AsyncClient,
    world: dict[str, uuid.UUID],
    clock: FakeClock,
    db_session: AsyncSession,
) -> None:
    other = make_client(world["operator_id"], "Other Corp")
    db_session.add(other)
    await db_session.flush()
    scoped = await headers_for(
        Role.client_admin, world["operator_id"], clock, db_session, client_id=world["client_id"]
    )

    response = await client.post(
        f"/admin/clients/{other.id}/employees/import",
        files=upload(f"{HEADER}\nAsha,+919812345678,B200,28.5,77.3,,3,no\n"),
        headers=scoped,
    )
    assert response.status_code == 403


async def test_import_requires_authentication(
    client: AsyncClient, world: dict[str, uuid.UUID]
) -> None:
    response = await client.post(
        f"/admin/clients/{world['client_id']}/employees/import",
        files=upload(f"{HEADER}\n"),
    )
    assert response.status_code == 401
