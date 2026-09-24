"""Operator config service and `/admin/config` (B05).

Acceptance: out-of-range values are rejected with 422, and a history row is written on
every change.
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
from app.domain import config_keys
from app.domain.config_keys import CONFIG_KEYS, PER_CLIENT_KEYS, STRICTER_ONLY_KEYS
from app.domain.enums import CLIENT_SCOPED_ROLES, Role
from app.domain.errors import ValidationFailed
from app.main import create_app
from app.modules.config.models import OperatorConfig, OperatorConfigHistory
from app.modules.config.service import ConfigService
from tests.builders import make_client, make_operator, make_user, make_user_role

NOW = datetime(2026, 9, 24, 4, 30, tzinfo=UTC)
JWT_SECRET = "config-tests-secret-0123456789abcdefgh"


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest_asyncio.fixture
async def operator_id(db_session: AsyncSession) -> uuid.UUID:
    operator = make_operator()
    db_session.add(operator)
    await db_session.flush()
    return operator.id


@pytest.fixture
def service(db_session: AsyncSession, clock: FakeClock) -> ConfigService:
    return ConfigService(db_session, clock)


# --- the registry (pure) ------------------------------------------------------


def test_every_documented_key_has_a_default() -> None:
    values = config_keys.defaults()
    assert set(values) == set(CONFIG_KEYS)
    assert values["candidate_max_eta_minutes"] == 20
    assert values["max_detour_factor"] == 1.5
    assert values["failsafe_action"] == "auto_assign"
    assert values["night_safety_enabled"] is False
    assert values["night_safety_start"] == "20:00"


def test_defaults_match_allocation_rules() -> None:
    """Spot-check the table against the doc; a typo here mis-tunes the whole system."""
    expected = {
        "pickup_window_minutes": 10,
        "hold_window_min_minutes": 10,
        "hold_window_max_minutes": 30,
        "max_detour_minutes": 15,
        "enroute_reuse_max_eta_minutes": 5,
        "batch_window_seconds": 45,
        "failsafe_timeout_seconds": 180,
        "alert_wait_minutes": 20,
        "request_expiry_minutes": 120,
        "no_show_wait_minutes": 5,
        "stale_gps_seconds": 60,
        "weight_wait": 1.0,
        "weight_empty_km": 2.0,
        "cost_new_vehicle": 15.0,
        "urgency_factor_high": 3.0,
        "urgency_factor_medium": 1.5,
        "urgency_factor_low": 1.0,
    }
    defaults = config_keys.defaults()
    assert {k: defaults[k] for k in expected} == expected


def test_per_client_keys_match_the_doc() -> None:
    assert {
        "pickup_window_minutes",
        "hold_window_min_minutes",
        "hold_window_max_minutes",
        "max_detour_factor",
        "max_detour_minutes",
        "no_show_wait_minutes",
        "night_safety_enabled",
        "night_safety_start",
        "night_safety_end",
    } == PER_CLIENT_KEYS


def test_stricter_only_keys_match_the_doc() -> None:
    assert {"max_detour_factor", "max_detour_minutes"} == STRICTER_ONLY_KEYS


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("candidate_max_eta_minutes", 4),  # min 5
        ("candidate_max_eta_minutes", 61),  # max 60
        ("max_detour_factor", 0.9),
        ("max_detour_factor", 3.1),
        ("no_show_wait_minutes", 0),
        ("no_show_wait_minutes", 16),
        ("request_expiry_minutes", 29),
        ("urgency_factor_low", 0.05),
        ("stale_gps_seconds", 19),
    ],
)
def test_out_of_range_values_are_rejected(key: str, value: float) -> None:
    with pytest.raises(ValidationFailed):
        config_keys.validate(key, value)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("candidate_max_eta_minutes", 5),
        ("candidate_max_eta_minutes", 60),
        ("max_detour_factor", 1.0),
        ("max_detour_factor", 3.0),
        ("no_show_wait_minutes", 1),
        ("no_show_wait_minutes", 15),
    ],
)
def test_range_boundaries_are_inclusive(key: str, value: float) -> None:
    assert config_keys.validate(key, value) == value


def test_unknown_key_is_rejected() -> None:
    with pytest.raises(ValidationFailed, match="Unknown config key"):
        config_keys.validate("make_it_faster", 1)


def test_wrong_type_is_rejected() -> None:
    with pytest.raises(ValidationFailed, match="must be a number"):
        config_keys.validate("alert_wait_minutes", "twenty")


def test_boolean_key_rejects_a_number() -> None:
    """`True == 1` in Python; a bool key must not silently accept 1."""
    with pytest.raises(ValidationFailed, match="true or false"):
        config_keys.validate("night_safety_enabled", 1)


def test_numeric_key_rejects_a_boolean() -> None:
    with pytest.raises(ValidationFailed, match="must be a number"):
        config_keys.validate("alert_wait_minutes", True)


def test_enum_key_rejects_an_unknown_choice() -> None:
    with pytest.raises(ValidationFailed, match="must be one of"):
        config_keys.validate("failsafe_action", "panic")


def test_enum_key_accepts_both_documented_choices() -> None:
    assert config_keys.validate("failsafe_action", "auto_assign") == "auto_assign"
    assert config_keys.validate("failsafe_action", "escalate") == "escalate"


def test_time_key_validation() -> None:
    assert config_keys.validate("night_safety_start", "21:30") == "21:30"
    with pytest.raises(ValidationFailed, match="HH:MM"):
        config_keys.validate("night_safety_start", "half past nine")


def test_integer_keys_stay_integers() -> None:
    assert config_keys.validate("alert_wait_minutes", 25.0) == 25
    assert isinstance(config_keys.validate("alert_wait_minutes", 25.0), int)


def test_validate_all_reports_every_problem_at_once() -> None:
    """A half-applied patch would leave an operator misconfigured."""
    with pytest.raises(ValidationFailed) as raised:
        config_keys.validate_all(
            {"alert_wait_minutes": 999, "max_detour_factor": 9.9, "nonsense": 1}
        )
    errors = raised.value.details["errors"]
    assert len(errors) == 3


# --- the service --------------------------------------------------------------


async def test_unset_keys_read_their_defaults(
    service: ConfigService, operator_id: uuid.UUID
) -> None:
    values = await service.all_values(operator_id)
    assert values == config_keys.defaults()


async def test_update_then_read_back(service: ConfigService, operator_id: uuid.UUID) -> None:
    await service.update(operator_id, {"alert_wait_minutes": 25})
    assert await service.get(operator_id, "alert_wait_minutes") == 25


async def test_other_keys_keep_their_defaults(
    service: ConfigService, operator_id: uuid.UUID
) -> None:
    await service.update(operator_id, {"alert_wait_minutes": 25})
    values = await service.all_values(operator_id)
    assert values["alert_wait_minutes"] == 25
    assert values["request_expiry_minutes"] == 120


async def test_history_row_is_written(
    service: ConfigService, operator_id: uuid.UUID, db_session: AsyncSession
) -> None:
    """B05 acceptance."""
    await service.update(operator_id, {"alert_wait_minutes": 25})

    rows = (
        (
            await db_session.execute(
                select(OperatorConfigHistory).where(
                    OperatorConfigHistory.key == "alert_wait_minutes"
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1
    assert rows[0].old_value is None
    assert rows[0].new_value == 25
    assert rows[0].version == 1


async def test_history_records_the_previous_value(
    service: ConfigService, operator_id: uuid.UUID, db_session: AsyncSession
) -> None:
    await service.update(operator_id, {"alert_wait_minutes": 25})
    await service.update(operator_id, {"alert_wait_minutes": 30})

    rows = (
        (
            await db_session.execute(
                select(OperatorConfigHistory)
                .where(OperatorConfigHistory.key == "alert_wait_minutes")
                .order_by(OperatorConfigHistory.version)
            )
        )
        .scalars()
        .all()
    )
    assert [(r.old_value, r.new_value, r.version) for r in rows] == [
        (None, 25, 1),
        (25, 30, 2),
    ]


async def test_setting_the_same_value_writes_no_history(
    service: ConfigService, operator_id: uuid.UUID, db_session: AsyncSession
) -> None:
    """History should record changes, not every PATCH that happened to be sent."""
    await service.update(operator_id, {"alert_wait_minutes": 25})
    await service.update(operator_id, {"alert_wait_minutes": 25})

    count = await db_session.scalar(select(func.count()).select_from(OperatorConfigHistory))
    assert count == 1


async def test_version_increments(
    service: ConfigService, operator_id: uuid.UUID, db_session: AsyncSession
) -> None:
    await service.update(operator_id, {"alert_wait_minutes": 25})
    await service.update(operator_id, {"alert_wait_minutes": 30})

    row = (
        (
            await db_session.execute(
                select(OperatorConfig).where(OperatorConfig.key == "alert_wait_minutes")
            )
        )
        .scalars()
        .one()
    )
    assert row.version == 2


async def test_changed_by_is_recorded(
    service: ConfigService, operator_id: uuid.UUID, db_session: AsyncSession
) -> None:
    user = make_user()
    db_session.add(user)
    await db_session.flush()

    await service.update(operator_id, {"alert_wait_minutes": 25}, changed_by=user.id)
    row = (await db_session.execute(select(OperatorConfigHistory))).scalars().one()
    assert row.changed_by == user.id


async def test_invalid_patch_writes_nothing(
    service: ConfigService, operator_id: uuid.UUID, db_session: AsyncSession
) -> None:
    """Atomicity: a bad key must not let the good ones through."""
    with pytest.raises(ValidationFailed):
        await service.update(operator_id, {"alert_wait_minutes": 25, "max_detour_factor": 99})

    assert await db_session.scalar(select(func.count()).select_from(OperatorConfig)) == 0
    assert await service.get(operator_id, "alert_wait_minutes") == 20


async def test_empty_patch_is_rejected(service: ConfigService, operator_id: uuid.UUID) -> None:
    with pytest.raises(ValidationFailed, match="No config values"):
        await service.update(operator_id, {})


async def test_config_is_per_operator(
    service: ConfigService, operator_id: uuid.UUID, db_session: AsyncSession
) -> None:
    other = make_operator("Other Cabs")
    db_session.add(other)
    await db_session.flush()

    await service.update(operator_id, {"alert_wait_minutes": 25})

    assert await service.get(operator_id, "alert_wait_minutes") == 25
    assert await service.get(other.id, "alert_wait_minutes") == 20


async def test_history_is_queryable_per_key(service: ConfigService, operator_id: uuid.UUID) -> None:
    await service.update(operator_id, {"alert_wait_minutes": 25, "stale_gps_seconds": 90})
    await service.update(operator_id, {"alert_wait_minutes": 30})

    assert len(await service.history(operator_id)) == 3
    assert len(await service.history(operator_id, key="alert_wait_minutes")) == 2


async def test_get_rejects_an_unknown_key(service: ConfigService, operator_id: uuid.UUID) -> None:
    with pytest.raises(ValidationFailed, match="Unknown config key"):
        await service.get(operator_id, "nope")


# --- the endpoints --------------------------------------------------------------


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


async def token_for(
    role: Role,
    operator_id: uuid.UUID | None,
    clock: FakeClock,
    db_session: AsyncSession,
) -> str:
    """Mint a token for a user that really exists.

    `operator_config.updated_by` is a real foreign key, so a token carrying an invented
    user id fails on write - which is exactly what production would do.
    """
    user = make_user()
    db_session.add(user)
    await db_session.flush()

    if operator_id is not None:
        # client_admin and employee roles must carry a client_id - the CHECK constraint
        # from B02 enforces it, so the fixture has to create one.
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
    return access


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as c:
        yield c


async def test_get_config_returns_defaults(
    client: AsyncClient, operator_id: uuid.UUID, clock: FakeClock, db_session: AsyncSession
) -> None:
    token = await token_for(Role.operator_admin, operator_id, clock, db_session)
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/admin/config", headers=headers)
    assert response.status_code == 200
    assert response.json()["alert_wait_minutes"] == 20


async def test_patch_config_applies_and_returns_the_new_state(
    client: AsyncClient, operator_id: uuid.UUID, clock: FakeClock, db_session: AsyncSession
) -> None:
    token = await token_for(Role.operator_admin, operator_id, clock, db_session)
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.patch("/admin/config", json={"alert_wait_minutes": 25}, headers=headers)
    assert response.status_code == 200
    assert response.json()["alert_wait_minutes"] == 25


async def test_patch_rejects_out_of_range_with_422(
    client: AsyncClient, operator_id: uuid.UUID, clock: FakeClock, db_session: AsyncSession
) -> None:
    """B05 acceptance."""
    token = await token_for(Role.operator_admin, operator_id, clock, db_session)
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.patch(
        "/admin/config", json={"alert_wait_minutes": 999}, headers=headers
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_error"
    assert body["details"]["errors"][0]["key"] == "alert_wait_minutes"


async def test_patch_rejects_an_unknown_key(
    client: AsyncClient, operator_id: uuid.UUID, clock: FakeClock, db_session: AsyncSession
) -> None:
    token = await token_for(Role.operator_admin, operator_id, clock, db_session)
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.patch("/admin/config", json={"go_faster": 1}, headers=headers)
    assert response.status_code == 422


async def test_supervisor_cannot_change_config(
    client: AsyncClient, operator_id: uuid.UUID, clock: FakeClock, db_session: AsyncSession
) -> None:
    """The matrix gives config to operator_admin and above, not to supervisors."""
    token = await token_for(Role.supervisor, operator_id, clock, db_session)
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.patch("/admin/config", json={"alert_wait_minutes": 25}, headers=headers)
    assert response.status_code == 403


async def test_employee_cannot_read_config(
    client: AsyncClient, operator_id: uuid.UUID, clock: FakeClock, db_session: AsyncSession
) -> None:
    token = await token_for(Role.employee, operator_id, clock, db_session)
    headers = {"Authorization": f"Bearer {token}"}
    assert (await client.get("/admin/config", headers=headers)).status_code == 403


async def test_config_requires_authentication(client: AsyncClient) -> None:
    assert (await client.get("/admin/config")).status_code == 401


async def test_operator_admin_without_an_operator_is_refused(
    client: AsyncClient, clock: FakeClock, db_session: AsyncSession
) -> None:
    token = await token_for(Role.platform_admin, None, clock, db_session)
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/admin/config", headers=headers)
    assert response.status_code == 403


async def test_patch_is_audited_through_history(
    client: AsyncClient, operator_id: uuid.UUID, clock: FakeClock, db_session: AsyncSession
) -> None:
    token = await token_for(Role.operator_admin, operator_id, clock, db_session)
    headers = {"Authorization": f"Bearer {token}"}
    await client.patch("/admin/config", json={"stale_gps_seconds": 90}, headers=headers)

    row = (
        (
            await db_session.execute(
                select(OperatorConfigHistory).where(
                    OperatorConfigHistory.key == "stale_gps_seconds"
                )
            )
        )
        .scalars()
        .one()
    )
    assert row.new_value == 90
