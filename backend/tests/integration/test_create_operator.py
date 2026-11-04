"""`make create-operator`: the first operator and admin of a real pilot."""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.create_operator import CreateOperatorError, create_operator
from app.domain.enums import Role
from app.modules.auth.models import AppUser, UserRole
from app.modules.config.service import ConfigService
from app.modules.tenancy.models import Operator
from tests.integration.worlds import NOW

pytestmark = pytest.mark.requires_db

CLOCK = FakeClock(NOW)
ARGS: dict[str, Any] = {
    "name": "Pilot Cabs Test",
    "admin_name": "Pilot Admin",
    "admin_phone": "+919877700001",
}


async def test_it_creates_the_operator_and_an_admin_who_can_log_in(
    db_session: AsyncSession,
) -> None:
    result = await create_operator(db_session, CLOCK, **ARGS, rate_per_km=8)
    assert result.operator_created and result.admin_created

    operator = await db_session.get(Operator, result.operator_id)
    assert operator is not None and operator.timezone == "Asia/Kolkata"
    roles = (
        (await db_session.execute(select(UserRole).where(UserRole.user_id == result.admin_user_id)))
        .scalars()
        .all()
    )
    assert [(r.role, r.operator_id, r.client_id) for r in roles] == [
        (Role.operator_admin, result.operator_id, None)
    ]
    assert (
        await ConfigService(db_session, CLOCK).get(result.operator_id, "billing_rate_per_km") == 8
    )


async def test_running_it_again_changes_nothing(db_session: AsyncSession) -> None:
    first = await create_operator(db_session, CLOCK, **ARGS)
    again = await create_operator(db_session, CLOCK, **{**ARGS, "name": "pilot cabs test"})

    assert (again.operator_id, again.admin_user_id) == (first.operator_id, first.admin_user_id)
    assert not again.operator_created and not again.admin_created
    users = await db_session.scalar(
        select(func.count()).select_from(AppUser).where(AppUser.phone == ARGS["admin_phone"])
    )
    roles = await db_session.scalar(
        select(func.count()).select_from(UserRole).where(UserRole.user_id == first.admin_user_id)
    )
    assert (users, roles) == (1, 1)


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"admin_phone": "9877700001"}, "international"),
        ({"name": "  "}, "must not be empty"),
        ({"timezone": "Mars/Base"}, "Unknown timezone"),
        ({"rate_per_km": -1.0}, "negative"),
    ],
)
async def test_bad_arguments_are_refused_before_anything_is_written(
    db_session: AsyncSession, changes: dict[str, Any], message: str
) -> None:
    with pytest.raises(CreateOperatorError, match=message):
        await create_operator(db_session, CLOCK, **{**ARGS, **changes})
    assert await db_session.scalar(select(Operator).where(Operator.name == ARGS["name"])) is None


async def test_a_phone_that_belongs_to_another_operator_is_refused(
    db_session: AsyncSession,
) -> None:
    await create_operator(db_session, CLOCK, **ARGS)
    with pytest.raises(CreateOperatorError, match="another operator"):
        await create_operator(db_session, CLOCK, **{**ARGS, "name": "Second Cabs Test"})


async def test_the_same_name_with_another_timezone_is_refused(db_session: AsyncSession) -> None:
    await create_operator(db_session, CLOCK, **ARGS)
    with pytest.raises(CreateOperatorError, match="already exists with timezone"):
        await create_operator(db_session, CLOCK, **ARGS, timezone="Asia/Dubai")
