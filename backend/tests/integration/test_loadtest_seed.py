"""`make loadtest-seed` builds the pilot-sized world and a second run adds nothing."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import loadtest_seed as world
from app.modules.fleet.models import Driver, Vehicle
from app.modules.people.models import Employee

pytestmark = pytest.mark.requires_db


async def _counts(session: AsyncSession, operator_id: uuid.UUID) -> tuple[int, int, int]:
    found: list[int] = []
    for model in (Vehicle, Driver, Employee):
        total = await session.scalar(
            select(func.count()).select_from(model).where(model.operator_id == operator_id)
        )
        found.append(int(total or 0))
    return found[0], found[1], found[2]


async def test_the_world_has_the_pilot_sized_fleet_and_a_second_run_adds_nothing(
    db_session: AsyncSession,
) -> None:
    first = await world.seed(db_session)
    assert await _counts(db_session, first.operator_id) == (world.CABS, world.CABS, world.RIDERS)

    again = await world.seed(db_session)
    assert again.operator_id == first.operator_id
    assert await _counts(db_session, first.operator_id) == (world.CABS, world.CABS, world.RIDERS)
