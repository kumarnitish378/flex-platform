"""Core schema and tenant isolation (B02).

`testing-strategy.md` §3: "a user of operator A can never read or write operator B data,
for every repository". That is the point of this file — the CRUD checks are incidental.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import ClientStatus, OperatorStatus, Role
from app.domain.errors import NotFound
from app.modules.auth.repository import (
    AppUserRepository,
    DeviceRepository,
    OtpChallengeRepository,
    RefreshTokenRepository,
    UserRoleRepository,
)
from app.modules.people.models import Employee
from app.modules.people.repository import EmployeeRepository, SavedPlaceRepository
from app.modules.tenancy.models import Client
from app.modules.tenancy.repository import (
    ClientPolicyRepository,
    ClientRepository,
    OfficeRepository,
    OperatorRepository,
    ZoneRepository,
)
from tests.builders import (
    make_client,
    make_client_policy,
    make_device,
    make_employee,
    make_office,
    make_operator,
    make_otp_challenge,
    make_refresh_token,
    make_saved_place,
    make_user,
    make_user_role,
    make_zone,
    unique_phone,
)


async def two_tenants(session: AsyncSession) -> tuple[uuid.UUID, uuid.UUID]:
    """Two operators, each with a client and an office. The setup for isolation tests."""
    a, b = make_operator("Operator A"), make_operator("Operator B")
    session.add_all([a, b])
    await session.flush()
    return a.id, b.id


# --- the schema itself -------------------------------------------------------


async def test_migration_created_every_table(db_session: AsyncSession) -> None:
    """B02 acceptance: the Alembic migration creates the tables."""
    expected = {
        "operator",
        "client",
        "office",
        "client_policy",
        "zone",
        "app_user",
        "user_role",
        "refresh_token",
        "otp_challenge",
        "device",
        "employee",
        "saved_place",
    }
    result = await db_session.execute(
        text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
    )
    assert expected <= set(result.scalars().all())


async def test_postgis_geography_columns_exist(db_session: AsyncSession) -> None:
    result = await db_session.execute(
        text(
            "SELECT f_table_name, type, srid FROM geography_columns "
            "WHERE f_table_name IN ('office', 'employee', 'zone', 'saved_place')"
        )
    )
    columns = {row[0]: (row[1], row[2]) for row in result.all()}
    assert columns["office"] == ("Point", 4326)
    assert columns["zone"] == ("Polygon", 4326)
    assert columns["employee"] == ("Point", 4326)


async def test_timestamps_are_populated_by_the_database(db_session: AsyncSession) -> None:
    operator = make_operator()
    db_session.add(operator)
    await db_session.flush()
    await db_session.refresh(operator)
    assert operator.created_at is not None
    assert operator.updated_at is not None
    assert operator.created_at.tzinfo is not None


async def test_defaults_match_the_spec(db_session: AsyncSession) -> None:
    operator = make_operator()
    db_session.add(operator)
    await db_session.flush()
    await db_session.refresh(operator)
    assert operator.status == OperatorStatus.active
    assert operator.timezone == "Asia/Kolkata"
    assert operator.automation_paused is False


# --- tenant isolation, repository by repository ------------------------------


async def test_client_repository_isolation(db_session: AsyncSession) -> None:
    a, b = await two_tenants(db_session)
    repo = ClientRepository(db_session)

    client_a = await repo.add(make_client(a, "A's client"))
    await repo.add(make_client(b, "B's client"))

    assert await repo.get(a, client_a.id) is not None
    assert await repo.get(b, client_a.id) is None, "operator B must not read A's client"
    assert [c.name for c in await repo.list(a)] == ["A's client"]
    assert [c.name for c in await repo.list(b)] == ["B's client"]


async def test_foreign_id_is_indistinguishable_from_a_missing_one(
    db_session: AsyncSession,
) -> None:
    """A probe must not learn that someone else's row exists."""
    a, b = await two_tenants(db_session)
    repo = ClientRepository(db_session)
    client_a = await repo.add(make_client(a))

    assert await repo.get(b, client_a.id) is None
    assert await repo.get(b, uuid.uuid4()) is None

    with pytest.raises(NotFound):
        await repo.get_or_raise(b, client_a.id)


async def test_office_repository_isolation(db_session: AsyncSession) -> None:
    a, b = await two_tenants(db_session)
    clients = ClientRepository(db_session)
    offices = OfficeRepository(db_session)

    client_a = await clients.add(make_client(a))
    client_b = await clients.add(make_client(b))
    office_a = await offices.add(make_office(a, client_a.id))
    await offices.add(make_office(b, client_b.id))

    assert await offices.get(b, office_a.id) is None
    assert await offices.list_for_client(b, client_a.id) == []
    assert len(await offices.list_for_client(a, client_a.id)) == 1


async def test_client_policy_repository_isolation(db_session: AsyncSession) -> None:
    a, b = await two_tenants(db_session)
    clients = ClientRepository(db_session)
    policies = ClientPolicyRepository(db_session)

    client_a = await clients.add(make_client(a))
    await policies.add(make_client_policy(a, client_a.id))

    assert await policies.for_client(a, client_a.id) is not None
    assert await policies.for_client(b, client_a.id) is None


async def test_zone_repository_isolation(db_session: AsyncSession) -> None:
    a, b = await two_tenants(db_session)
    zones = ZoneRepository(db_session)

    zone_a = await zones.add(make_zone(a, "A zone"))
    await zones.add(make_zone(b, "B zone"))

    assert await zones.get(b, zone_a.id) is None
    assert [z.name for z in await zones.active(a)] == ["A zone"]


async def test_employee_repository_isolation(db_session: AsyncSession) -> None:
    a, b = await two_tenants(db_session)
    clients, offices = ClientRepository(db_session), OfficeRepository(db_session)
    employees = EmployeeRepository(db_session)

    client_a = await clients.add(make_client(a))
    office_a = await offices.add(make_office(a, client_a.id))
    phone = unique_phone()
    employee_a = await employees.add(make_employee(a, client_a.id, office_a.id, phone=phone))

    assert await employees.get(a, employee_a.id) is not None
    assert await employees.get(b, employee_a.id) is None
    assert await employees.by_phone(b, client_a.id, phone) is None
    assert await employees.by_phone(a, client_a.id, phone) is not None
    assert await employees.active_for_client(b, client_a.id) == []


async def test_saved_place_repository_isolation(db_session: AsyncSession) -> None:
    a, b = await two_tenants(db_session)
    clients, offices = ClientRepository(db_session), OfficeRepository(db_session)
    employees, places = EmployeeRepository(db_session), SavedPlaceRepository(db_session)

    client_a = await clients.add(make_client(a))
    office_a = await offices.add(make_office(a, client_a.id))
    employee_a = await employees.add(make_employee(a, client_a.id, office_a.id))
    place = await places.add(make_saved_place(a, employee_a.id))

    assert await places.get(a, place.id) is not None
    assert await places.get(b, place.id) is None


async def test_delete_cannot_cross_tenants(db_session: AsyncSession) -> None:
    a, b = await two_tenants(db_session)
    repo = ClientRepository(db_session)
    client_a = await repo.add(make_client(a))

    assert await repo.delete(b, client_a.id) is False
    assert await repo.get(a, client_a.id) is not None, "B's delete must not touch A's row"
    assert await repo.delete(a, client_a.id) is True
    assert await repo.get(a, client_a.id) is None


async def test_count_is_scoped(db_session: AsyncSession) -> None:
    a, b = await two_tenants(db_session)
    repo = ClientRepository(db_session)
    await repo.add(make_client(a, "one"))
    await repo.add(make_client(a, "two"))
    await repo.add(make_client(b, "three"))

    assert await repo.count(a) == 2
    assert await repo.count(b) == 1


async def test_filters_are_applied_on_top_of_the_tenant_scope(
    db_session: AsyncSession,
) -> None:
    a, b = await two_tenants(db_session)
    repo = ClientRepository(db_session)
    await repo.add(make_client(a, "active one"))
    suspended = make_client(a, "suspended one")
    suspended.status = ClientStatus.suspended
    await repo.add(suspended)
    await repo.add(make_client(b, "b client"))

    found = await repo.list(a, status=ClientStatus.suspended)
    assert [c.name for c in found] == ["suspended one"]


async def test_scoped_query_always_carries_the_filter(db_session: AsyncSession) -> None:
    """The base query is the only way to build one, and it is already filtered."""
    operator_id = uuid.uuid4()
    query = str(ClientRepository(db_session).scoped(operator_id))
    assert "WHERE client.operator_id" in query


# --- constraints that protect tenancy ----------------------------------------


async def test_platform_admin_has_no_operator(db_session: AsyncSession) -> None:
    user = make_user()
    db_session.add(user)
    await db_session.flush()

    db_session.add(make_user_role(user.id, Role.platform_admin, operator_id=None))
    await db_session.flush()  # allowed


async def test_platform_admin_with_an_operator_is_rejected(db_session: AsyncSession) -> None:
    a, _ = await two_tenants(db_session)
    user = make_user()
    db_session.add(user)
    await db_session.flush()

    db_session.add(make_user_role(user.id, Role.platform_admin, operator_id=a))
    with pytest.raises(IntegrityError, match="ck_user_role_operator_scope"):
        await db_session.flush()


async def test_non_platform_role_requires_an_operator(db_session: AsyncSession) -> None:
    user = make_user()
    db_session.add(user)
    await db_session.flush()

    db_session.add(make_user_role(user.id, Role.supervisor, operator_id=None))
    with pytest.raises(IntegrityError, match="ck_user_role_operator_scope"):
        await db_session.flush()


async def test_employee_role_requires_a_client(db_session: AsyncSession) -> None:
    a, _ = await two_tenants(db_session)
    user = make_user()
    db_session.add(user)
    await db_session.flush()

    db_session.add(make_user_role(user.id, Role.employee, operator_id=a, client_id=None))
    with pytest.raises(IntegrityError, match="ck_user_role_client_scope"):
        await db_session.flush()


async def test_supervisor_role_must_not_carry_a_client(db_session: AsyncSession) -> None:
    a, _ = await two_tenants(db_session)
    client = make_client(a)
    user = make_user()
    db_session.add_all([client, user])
    await db_session.flush()

    db_session.add(make_user_role(user.id, Role.supervisor, operator_id=a, client_id=client.id))
    with pytest.raises(IntegrityError, match="ck_user_role_client_scope"):
        await db_session.flush()


async def test_phone_must_be_e164(db_session: AsyncSession) -> None:
    db_session.add(make_user(phone="9812345678"))
    with pytest.raises(IntegrityError, match="ck_app_user_phone_e164"):
        await db_session.flush()


async def test_phone_is_unique_across_users(db_session: AsyncSession) -> None:
    phone = unique_phone()
    db_session.add(make_user(phone=phone))
    await db_session.flush()
    db_session.add(make_user(name="Someone else", phone=phone))
    with pytest.raises(IntegrityError, match="uq_app_user_phone"):
        await db_session.flush()


async def test_employee_priority_range_is_enforced(db_session: AsyncSession) -> None:
    a, _ = await two_tenants(db_session)
    clients, offices = ClientRepository(db_session), OfficeRepository(db_session)
    client = await clients.add(make_client(a))
    office = await offices.add(make_office(a, client.id))

    db_session.add(make_employee(a, client.id, office.id, priority=11))
    with pytest.raises(IntegrityError, match="ck_employee_priority_range"):
        await db_session.flush()


async def test_same_phone_may_work_for_two_clients(db_session: AsyncSession) -> None:
    """A driver's spouse at another company is not a duplicate."""
    a, _ = await two_tenants(db_session)
    clients, offices = ClientRepository(db_session), OfficeRepository(db_session)
    employees = EmployeeRepository(db_session)

    client_one = await clients.add(make_client(a, "One"))
    client_two = await clients.add(make_client(a, "Two"))
    office_one = await offices.add(make_office(a, client_one.id, "O1"))
    office_two = await offices.add(make_office(a, client_two.id, "O2"))

    phone = unique_phone()
    await employees.add(make_employee(a, client_one.id, office_one.id, phone=phone))
    await employees.add(make_employee(a, client_two.id, office_two.id, phone=phone))
    await db_session.flush()  # allowed


async def test_duplicate_phone_within_a_client_is_rejected(db_session: AsyncSession) -> None:
    a, _ = await two_tenants(db_session)
    clients, offices = ClientRepository(db_session), OfficeRepository(db_session)
    employees = EmployeeRepository(db_session)

    client = await clients.add(make_client(a))
    office = await offices.add(make_office(a, client.id))
    phone = unique_phone()
    await employees.add(make_employee(a, client.id, office.id, phone=phone))

    db_session.add(make_employee(a, client.id, office.id, name="Twin", phone=phone))
    with pytest.raises(IntegrityError, match="uq_employee_client_phone"):
        await db_session.flush()


async def test_client_policy_is_one_per_client(db_session: AsyncSession) -> None:
    a, _ = await two_tenants(db_session)
    clients = ClientRepository(db_session)
    policies = ClientPolicyRepository(db_session)
    client = await clients.add(make_client(a))
    await policies.add(make_client_policy(a, client.id))

    db_session.add(make_client_policy(a, client.id))
    with pytest.raises(IntegrityError, match="uq_client_policy_client"):
        await db_session.flush()


async def test_client_policy_detour_factor_range(db_session: AsyncSession) -> None:
    a, _ = await two_tenants(db_session)
    client = await ClientRepository(db_session).add(make_client(a))
    policy = make_client_policy(a, client.id)
    policy.max_detour_factor = 5.0
    db_session.add(policy)
    with pytest.raises(IntegrityError, match="ck_client_policy_detour_factor_range"):
        await db_session.flush()


# --- non-tenant repositories --------------------------------------------------


async def test_user_lookup_by_phone(db_session: AsyncSession) -> None:
    repo = AppUserRepository(db_session)
    phone = unique_phone()
    await repo.add(make_user(phone=phone))
    found = await repo.by_phone(phone)
    assert found is not None and found.phone == phone
    assert await repo.by_phone(unique_phone()) is None


async def test_roles_are_listed_per_user_and_operator(db_session: AsyncSession) -> None:
    a, b = await two_tenants(db_session)
    users, roles = AppUserRepository(db_session), UserRoleRepository(db_session)
    user = await users.add(make_user())

    await roles.add(make_user_role(user.id, Role.supervisor, operator_id=a))
    await roles.add(make_user_role(user.id, Role.driver, operator_id=b))

    assert len(await roles.for_user(user.id)) == 2
    assert [r.role for r in await roles.for_user_in_operator(user.id, a)] == [Role.supervisor]


async def test_one_person_can_hold_roles_at_two_operators(db_session: AsyncSession) -> None:
    """app_user is not tenant-scoped; user_role is. This is why."""
    a, b = await two_tenants(db_session)
    users, roles = AppUserRepository(db_session), UserRoleRepository(db_session)
    user = await users.add(make_user())
    await roles.add(make_user_role(user.id, Role.supervisor, operator_id=a))
    await roles.add(make_user_role(user.id, Role.supervisor, operator_id=b))
    await db_session.flush()  # allowed


async def test_duplicate_role_in_the_same_scope_is_rejected(db_session: AsyncSession) -> None:
    a, _ = await two_tenants(db_session)
    users, roles = AppUserRepository(db_session), UserRoleRepository(db_session)
    user = await users.add(make_user())
    await roles.add(make_user_role(user.id, Role.supervisor, operator_id=a))

    db_session.add(make_user_role(user.id, Role.supervisor, operator_id=a))
    with pytest.raises(IntegrityError, match="uq_user_role_scope"):
        await db_session.flush()


async def test_refresh_token_lookup_by_hash(db_session: AsyncSession) -> None:
    users, tokens = AppUserRepository(db_session), RefreshTokenRepository(db_session)
    user = await users.add(make_user())
    token = await tokens.add(make_refresh_token(user.id, token_hash="abc123"))

    found = await tokens.by_hash("abc123")
    assert found is not None and found.id == token.id
    assert await tokens.by_hash("nope") is None


async def test_otp_challenge_defaults(db_session: AsyncSession) -> None:
    repo = OtpChallengeRepository(db_session)
    challenge = await repo.add(make_otp_challenge())
    await db_session.refresh(challenge)
    assert challenge.attempts == 0
    assert challenge.consumed_at is None


async def test_device_push_token_is_unique(db_session: AsyncSession) -> None:
    users, devices = AppUserRepository(db_session), DeviceRepository(db_session)
    user = await users.add(make_user())
    await devices.add(make_device(user.id, token="same-token"))

    db_session.add(make_device(user.id, token="same-token"))
    with pytest.raises(IntegrityError, match="uq_device_push_token"):
        await db_session.flush()


async def test_operator_repository_round_trip(db_session: AsyncSession) -> None:
    repo = OperatorRepository(db_session)
    operator = await repo.add(make_operator("Round Trip Cabs"))
    fetched = await repo.get(operator.id)
    assert fetched is not None and fetched.name == "Round Trip Cabs"

    with pytest.raises(NotFound):
        await repo.get_or_raise(uuid.uuid4())


# --- geography round-trip -----------------------------------------------------


async def test_point_survives_a_round_trip(db_session: AsyncSession) -> None:
    a, _ = await two_tenants(db_session)
    client = await ClientRepository(db_session).add(make_client(a))
    office = await OfficeRepository(db_session).add(make_office(a, client.id))

    result = await db_session.execute(
        text("SELECT ST_X(location::geometry), ST_Y(location::geometry) FROM office WHERE id = :i"),
        {"i": office.id},
    )
    lng, lat = result.one()
    assert (round(lng, 4), round(lat, 4)) == (77.3218, 28.5703)


async def test_distance_between_two_points_is_in_metres(db_session: AsyncSession) -> None:
    """geography (not geometry) means ST_Distance returns metres, no projection needed."""
    result = await db_session.execute(
        text(
            "SELECT ST_Distance("
            "  ST_GeogFromText('POINT(77.3218 28.5703)'),"
            "  ST_GeogFromText('POINT(77.3910 28.5123)'))"
        )
    )
    metres = result.scalar_one()
    assert 8_000 < metres < 11_000


async def test_employee_zone_starts_null(db_session: AsyncSession) -> None:
    """Zone derivation is a stub until B07; the column must allow that."""
    a, _ = await two_tenants(db_session)
    client = await ClientRepository(db_session).add(make_client(a))
    office = await OfficeRepository(db_session).add(make_office(a, client.id))
    employee = await EmployeeRepository(db_session).add(make_employee(a, client.id, office.id))
    assert employee.zone_id is None


async def test_employee_defaults(db_session: AsyncSession) -> None:
    a, _ = await two_tenants(db_session)
    client = await ClientRepository(db_session).add(make_client(a))
    office = await OfficeRepository(db_session).add(make_office(a, client.id))
    employee = await EmployeeRepository(db_session).add(make_employee(a, client.id, office.id))
    await db_session.refresh(employee)

    assert employee.priority == 5
    assert employee.is_vip is False
    assert employee.night_escort_required is False
    assert employee.active is True
    assert employee.user_id is None, "an employee exists before the person ever logs in"


async def test_models_are_distinct_types(db_session: AsyncSession) -> None:
    assert Client.__tablename__ == "client"
    assert Employee.__tablename__ == "employee"
