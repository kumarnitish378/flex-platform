"""En-route reuse on the real candidate path, against a database (B33).

The unit tests in `test_enroute_reuse.py` prove the rule on a flat world. This is the same
claim through `DispatchService.candidates()`: the cab's position is loaded, one matrix
call is made, and the verdict a supervisor would see is checked.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.domain.dispatch import Violation
from app.domain.enums import ActorType
from app.domain.modes import Mode
from app.domain.state_machines import Actor
from app.modules.dispatch.service import Candidate, DispatchService
from app.modules.fleet.models import Vehicle
from tests.integration.worlds import (
    NOW,
    OFFICE,
    World,
    add_cab,
    add_employee,
    add_request,
    build_world,
    eta_service,
    near,
)

pytestmark = pytest.mark.requires_db


async def candidate_for(
    session: AsyncSession,
    world: World,
    cab_at: tuple[float, float],
    waiting_at: tuple[float, float],
    newcomer_at: tuple[float, float],
    requested_in: timedelta,
) -> tuple[Candidate, Vehicle]:
    dispatch = DispatchService(session, world.clock, eta_service(world.clock))
    cab = await add_cab(session, world, cab_at)
    waiting = await add_request(session, world, await add_employee(session, world, waiting_at))
    await dispatch.assign(
        world.operator_id, waiting.id, cab.id, Actor(str(ActorType.supervisor)), None
    )
    newcomer = await add_request(
        session,
        world,
        await add_employee(session, world, newcomer_at),
        requested_in=requested_in,
    )
    candidates = await dispatch.candidates(world.operator_id, newcomer.id)
    return next(c for c in candidates if c.vehicle.id == cab.id), cab


async def test_a_cab_whose_route_passes_the_rider_is_a_candidate_though_it_is_far_off(
    db_session: AsyncSession,
) -> None:
    world = await build_world(db_session, FakeClock(NOW), Mode.manual)

    candidate, _ = await candidate_for(
        db_session,
        world,
        cab_at=near(*OFFICE, north_km=-9.0),
        waiting_at=near(*OFFICE, north_km=-6.0),
        newcomer_at=near(*OFFICE, north_km=-5.0),
        requested_in=timedelta(minutes=14),
    )

    assert candidate.eta_to_pickup_seconds > 5 * 60, "the straight ETA is past the ceiling"
    assert Violation.enroute_reuse_eta_exceeded not in candidate.violations
    assert candidate.violations == []


async def test_a_cab_that_is_merely_near_but_heading_away_is_not(
    db_session: AsyncSession,
) -> None:
    world = await build_world(db_session, FakeClock(NOW), Mode.manual)

    candidate, _ = await candidate_for(
        db_session,
        world,
        cab_at=near(*OFFICE, north_km=-6.2),
        waiting_at=near(*OFFICE, north_km=-1.0),
        newcomer_at=near(*OFFICE, north_km=-7.4),
        requested_in=timedelta(minutes=0),
    )

    assert candidate.eta_to_pickup_seconds < 5 * 60, "near: inside the old ceiling"
    assert candidate.violations, "and still not a candidate"


async def test_an_idle_cab_keeps_its_own_ceiling(db_session: AsyncSession) -> None:
    """The ceiling applies per candidate kind: an idle cab is judged on arrival, not route."""
    world = await build_world(db_session, FakeClock(NOW), Mode.manual)
    await add_cab(db_session, world, near(*OFFICE, north_km=-9.0))
    newcomer = await add_request(
        db_session,
        world,
        await add_employee(db_session, world, near(*OFFICE, north_km=-5.0)),
        requested_in=timedelta(minutes=14),
    )
    dispatch = DispatchService(db_session, world.clock, eta_service(world.clock))

    (candidate,) = await dispatch.candidates(world.operator_id, newcomer.id)

    assert candidate.new_trip
    assert Violation.enroute_reuse_eta_exceeded not in candidate.violations
    assert Violation.eta_over_candidate_limit not in candidate.violations
