"""`make seed-demo`: the data a phone test runs on, loaded twice without harm."""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import demo_seed
from app.core.clock import FakeClock
from app.core.settings import Settings
from app.domain.enums import Role
from app.modules.auth.models import AppUser, UserRole
from app.modules.config.service import ConfigService
from app.modules.fleet.models import Driver, Vehicle
from app.modules.people.models import Employee
from app.modules.tenancy.models import ClientPolicy
from tests.integration.worlds import NOW

pytestmark = pytest.mark.requires_db


async def _count(session: AsyncSession, model: Any, operator_id: uuid.UUID) -> int:
    """Rows of this demo operator only: a developer's own database may hold other data."""
    return int(
        await session.scalar(
            select(func.count()).select_from(model).where(model.operator_id == operator_id)
        )
        or 0
    )


async def test_the_demo_world_has_what_the_brief_asks_for(db_session: AsyncSession) -> None:
    summary = await demo_seed.seed(db_session)

    assert await _count(db_session, Vehicle, summary.operator_id) == 5
    assert await _count(db_session, Driver, summary.operator_id) == 5
    employees = (
        (
            await db_session.execute(
                select(Employee).where(Employee.operator_id == summary.operator_id)
            )
        )
        .scalars()
        .all()
    )
    assert len(employees) == 20
    women = [e for e in employees if e.gender == "female"]
    men = [e for e in employees if e.gender == "male"]
    assert len(women) == 10 and len(men) == 10, "some women for the night window, and men to share"
    rate = await ConfigService(db_session, FakeClock(NOW)).get(
        summary.operator_id, "billing_rate_per_km"
    )
    assert rate == 8
    policy = await db_session.scalar(
        select(ClientPolicy).where(ClientPolicy.client_id == summary.client_id)
    )
    assert policy is not None and policy.night_safety_enabled is True


async def test_every_role_has_a_known_login(db_session: AsyncSession) -> None:
    await demo_seed.seed(db_session)

    roles = {row.role for row in (await db_session.execute(select(UserRole))).scalars()}
    assert {
        Role.operator_admin,
        Role.supervisor,
        Role.client_admin,
        Role.driver,
        Role.employee,
    } <= {Role(role) for role in roles}
    phones = {u.phone for u in (await db_session.execute(select(AppUser))).scalars()}
    assert {demo_seed.OPERATOR_ADMIN, demo_seed.SUPERVISOR, demo_seed.CLIENT_ADMIN} <= phones
    assert demo_seed.driver_phone(1) in phones and demo_seed.employee_phone(20) in phones


async def test_running_it_twice_changes_nothing(db_session: AsyncSession) -> None:
    first = await demo_seed.seed(db_session)
    second = await demo_seed.seed(db_session)

    assert second.created == {name: 0 for name in second.created}
    assert second.operator_id == first.operator_id
    assert await _count(db_session, UserRole, first.operator_id) == 3 + 5 + 20


async def test_it_refuses_to_run_against_staging() -> None:
    settings = Settings(
        app_env="staging",
        jwt_secret="x" * 40,
        osm_contact_email="ops@example.com",
        database_url="postgresql+asyncpg://t:t@localhost:5432/t",
    )

    with pytest.raises(SystemExit):
        demo_seed.refuse_outside_dev(settings)


def test_the_runbook_lists_the_numbers_the_seed_creates() -> None:
    from pathlib import Path

    runbook = (Path(__file__).resolve().parents[3] / "docs" / "runbook-phone-testing.md").read_text(
        encoding="utf-8"
    )
    for phone in (
        demo_seed.OPERATOR_ADMIN,
        demo_seed.SUPERVISOR,
        demo_seed.CLIENT_ADMIN,
        demo_seed.driver_phone(1),
        demo_seed.employee_phone(1),
        demo_seed.employee_phone(2),
    ):
        assert phone in runbook
