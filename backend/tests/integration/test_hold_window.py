"""The evening hold window against a real database (B29).

Time passes by advancing a `FakeClock`, never by sleeping: the same mechanism the
simulator uses, so a scenario can watch a window elapse.
"""

from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.domain.enums import ActorType, Direction, Urgency
from app.domain.errors import Conflict
from app.domain.modes import Mode
from app.domain.state_machines import Actor
from app.modules.dispatch.semi_auto import SemiAutoService
from app.modules.dispatch.service import DispatchService
from app.modules.dispatch.suggestion_models import Suggestion
from app.modules.fleet.models import Vehicle
from app.modules.people.models import Employee
from app.modules.requests.models import RideRequest
from app.modules.tenancy.models import ClientPolicy
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
    ping,
)

pytestmark = pytest.mark.requires_db

HOME = near(*OFFICE, north_km=-6.0)


@pytest_asyncio.fixture
async def world(db_session: AsyncSession) -> World:
    return await build_world(db_session, FakeClock(NOW), Mode.semi_auto)


@pytest_asyncio.fixture
async def cab(db_session: AsyncSession, world: World) -> Vehicle:
    """The cab waits at the office: a `from_office` pickup *is* the office."""
    return await add_cab(db_session, world, OFFICE)


@pytest_asyncio.fixture
async def rider(db_session: AsyncSession, world: World) -> Employee:
    return await add_employee(db_session, world, HOME)


@pytest.fixture
def dispatch(db_session: AsyncSession, world: World) -> DispatchService:
    return DispatchService(db_session, world.clock, eta_service(world.clock))


@pytest.fixture
def semi_auto(db_session: AsyncSession, world: World, dispatch: DispatchService) -> SemiAutoService:
    return SemiAutoService(db_session, world.clock, dispatch)


async def evening(
    db_session: AsyncSession, world: World, rider: Employee, **fields: Any
) -> RideRequest:
    return await add_request(db_session, world, rider, direction=Direction.from_office, **fields)


async def offers_for(db_session: AsyncSession, request_id: uuid.UUID) -> list[Suggestion]:
    rows = await db_session.execute(select(Suggestion).where(Suggestion.request_id == request_id))
    return list(rows.scalars())


async def test_a_held_request_is_not_offered_before_its_window_and_is_straight_after(
    db_session: AsyncSession,
    world: World,
    cab: Vehicle,
    rider: Employee,
    semi_auto: SemiAutoService,
) -> None:
    request = await evening(db_session, world, rider)

    assert (await semi_auto.run_due_semi_auto(world.operator_id)).offered == 0
    assert await offers_for(db_session, request.id) == []

    world.clock.advance(timedelta(minutes=9, seconds=59))
    await ping(db_session, world, cab, OFFICE)
    assert (await semi_auto.run_due_semi_auto(world.operator_id)).offered == 0

    world.clock.advance(timedelta(seconds=1))
    await ping(db_session, world, cab, OFFICE)
    after = await semi_auto.run_due_semi_auto(world.operator_id)

    assert after.offered == 1
    assert await offers_for(db_session, request.id)


async def test_suggestions_are_empty_while_held_but_candidates_still_list(
    db_session: AsyncSession,
    world: World,
    cab: Vehicle,
    rider: Employee,
    dispatch: DispatchService,
) -> None:
    request = await evening(db_session, world, rider)

    assert await dispatch.suggestions(world.operator_id, request.id) == []
    assert await dispatch.candidates(world.operator_id, request.id)


async def test_an_automatic_assignment_is_refused_inside_the_window_but_a_supervisor_may(
    db_session: AsyncSession,
    world: World,
    cab: Vehicle,
    rider: Employee,
    dispatch: DispatchService,
) -> None:
    request = await evening(db_session, world, rider)

    for actor in (Actor.system_failsafe, Actor.optimizer):
        with pytest.raises(Conflict) as refused:
            await dispatch.assign(world.operator_id, request.id, cab.id, actor, None)
        assert "held_until" in (refused.value.details or {})

    trip = await dispatch.assign(
        world.operator_id, request.id, cab.id, Actor(str(ActorType.supervisor)), None
    )
    assert trip.id is not None


async def test_forced_priority_short_circuits_the_window(
    db_session: AsyncSession,
    world: World,
    cab: Vehicle,
    rider: Employee,
    dispatch: DispatchService,
    semi_auto: SemiAutoService,
) -> None:
    """`allocation-rules.md` §3.1 promised this in Phase 1 and could not deliver it."""
    request = await evening(db_session, world, rider)
    assert await dispatch.is_held(request)

    request.forced_priority = True
    await db_session.flush()

    assert not await dispatch.is_held(request)
    assert (await semi_auto.run_due_semi_auto(world.operator_id)).offered == 1


async def test_an_expired_force_priority_no_longer_short_circuits(
    db_session: AsyncSession, world: World, rider: Employee, dispatch: DispatchService
) -> None:
    request = await evening(
        db_session,
        world,
        rider,
        forced_priority=True,
        override_until=NOW + timedelta(minutes=2),
        requested_in=timedelta(minutes=5),
    )
    assert not await dispatch.is_held(request)

    world.clock.advance(timedelta(minutes=3))

    assert await dispatch.is_held(request)


@pytest.mark.parametrize(
    "exempt", ["vip", "priority", "urgency", "no_sharing", "client_forbids_pooling"]
)
async def test_each_exemption_means_no_hold(
    db_session: AsyncSession,
    world: World,
    rider: Employee,
    dispatch: DispatchService,
    exempt: str,
) -> None:
    request = await evening(db_session, world, rider)
    assert await dispatch.is_held(request)

    if exempt == "vip":
        rider.is_vip = True
    elif exempt == "priority":
        rider.priority = 2
    elif exempt == "urgency":
        request.urgency = str(Urgency.high)
    elif exempt == "no_sharing":
        request.no_sharing = True
    else:
        db_session.add(
            ClientPolicy(
                id=uuid.uuid4(),
                operator_id=world.operator_id,
                client_id=world.client.id,
                pooling_allowed=False,
            )
        )
    await db_session.flush()

    assert not await dispatch.is_held(request)


async def test_a_to_office_request_is_never_held(
    db_session: AsyncSession, world: World, rider: Employee, dispatch: DispatchService
) -> None:
    request = await add_request(db_session, world, rider, direction=Direction.to_office)

    assert not await dispatch.is_held(request)
