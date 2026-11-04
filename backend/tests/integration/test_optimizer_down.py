"""The optimizer is allowed to be down (B36, `control-model.md` §6).

> Optimizer/worker down -> scopes in `full_auto`/`semi_auto` behave as `manual`; alert shown.

A scope on automation that goes quiet is the failure this prevents: if the optimizer
stops, nobody should be left with a queue that no longer moves and no explanation.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.core.security import create_access_token
from app.core.settings import Settings
from app.domain.enums import ActorType, AlertType, Role
from app.domain.modes import Mode
from app.domain.optimizer import Plan, Problem, solve
from app.domain.state_machines import Actor, RequestStatus
from app.main import create_app
from app.modules.alerts.models import Alert
from app.modules.dispatch.optimizer_models import OptimizerHint, OptimizerRun
from app.modules.dispatch.optimizer_service import OPTIMIZER_DOWN, OptimizerService
from app.modules.dispatch.semi_auto import SemiAutoService
from app.modules.dispatch.service import DispatchService
from app.modules.dispatch.suggestion_models import Suggestion
from app.modules.modes.prompts import ModePromptService
from tests.builders import make_user, make_user_role, unique_phone
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
    set_config,
)

pytestmark = pytest.mark.requires_db

HOME = near(*OFFICE, north_km=-6.0)
WINDOW = 45
JWT_SECRET = "optimizer-down-tests-secret-0123456789"


class Flaky:
    """A solver that raises for the first `failures` calls and then works."""

    def __init__(self, failures: int) -> None:
        self.failures = failures
        self.calls = 0

    def __call__(self, problem: Problem) -> Plan:
        self.calls += 1
        if self.calls <= self.failures:
            raise RuntimeError("the solver fell over")
        return solve(problem)


def service(session: AsyncSession, world: World, solver: Flaky | None = None) -> OptimizerService:
    dispatch = DispatchService(session, world.clock, eta_service(world.clock))
    return OptimizerService(session, world.clock, dispatch, solver=solver)


async def make_world(session: AsyncSession, mode: Mode) -> World:
    world = await build_world(session, FakeClock(NOW), mode)
    await set_config(session, world, batch_window_seconds=WINDOW)
    return world


async def tick(session: AsyncSession, world: World, optimizer: OptimizerService, cab: Any) -> Any:
    """One window on: the cab pings, the clock moves, the sweep runs."""
    world.clock.advance(timedelta(seconds=WINDOW))
    await ping(session, world, cab, HOME)
    return await optimizer.run_due_batches(world.operator_id)


async def down_alerts(
    session: AsyncSession, world: World, *, open_only: bool = True
) -> list[Alert]:
    query = select(Alert).where(
        Alert.operator_id == world.operator_id, Alert.type == str(AlertType.system)
    )
    if open_only:
        query = query.where(Alert.status != "resolved")
    return [
        a
        for a in (await session.scalars(query)).all()
        if (a.data or {}).get("kind") == OPTIMIZER_DOWN
    ]


async def test_a_failing_optimizer_degrades_the_scope_to_manual_with_an_alert_and_then_recovers(
    db_session: AsyncSession,
) -> None:
    world = await make_world(db_session, Mode.full_auto)
    cab = await add_cab(db_session, world, HOME)
    request = await add_request(db_session, world, await add_employee(db_session, world, HOME))
    solver = Flaky(failures=3)
    optimizer = service(db_session, world, solver)

    # Three failed batches: the optimizer is down.
    for _ in range(3):
        await tick(db_session, world, optimizer, cab)
    await db_session.refresh(request)
    assert request.status == str(RequestStatus.queued)
    (alert,) = await down_alerts(db_session, world)
    assert alert.data is not None and alert.data["reason"] == "solver_failing"
    assert alert.data["behaves_as"] == "manual"
    assert (await optimizer.health(world.operator_id)).available is False

    # Down, the scope is manual: the next run (the probe) may only hint, never assign.
    await tick(db_session, world, optimizer, cab)
    await db_session.refresh(request)
    assert request.status == str(RequestStatus.queued), "behaving as manual, not assigning"
    hint = await db_session.scalar(
        select(OptimizerHint).where(OptimizerHint.request_id == request.id)
    )
    assert hint is not None, "the supervisor still gets the optimizer's view"
    probe = await db_session.scalar(
        select(OptimizerRun)
        .where(OptimizerRun.operator_id == world.operator_id)
        .order_by(OptimizerRun.started_at.desc())
        .limit(1)
    )
    assert probe is not None and probe.mode == "manual" and probe.status == "solved"

    # The probe worked, so nobody has to touch anything: the alert clears, the scope returns.
    assert await down_alerts(db_session, world) == []
    await tick(db_session, world, optimizer, cab)
    await db_session.refresh(request)
    assert request.status == str(RequestStatus.assigned), "recovered without an operator"


async def test_a_supervisor_can_always_assign_by_hand_while_it_is_down(
    db_session: AsyncSession,
) -> None:
    """No request is stuck: the manual path never depended on the optimizer."""
    world = await make_world(db_session, Mode.full_auto)
    cab = await add_cab(db_session, world, HOME)
    request = await add_request(db_session, world, await add_employee(db_session, world, HOME))
    optimizer = service(db_session, world, Flaky(failures=99))
    for _ in range(3):
        await tick(db_session, world, optimizer, cab)

    trip = await optimizer.dispatch.assign(
        world.operator_id, request.id, cab.id, Actor(str(ActorType.supervisor)), None
    )

    await db_session.refresh(request)
    assert request.status == str(RequestStatus.assigned) and request.trip_id == trip.id


async def test_a_worker_that_is_not_running_at_all_is_noticed_by_another_sweep(
    db_session: AsyncSession,
) -> None:
    """No failed runs to count when nothing runs. The mode-prompt task is a second pair of eyes."""
    world = await make_world(db_session, Mode.full_auto)
    cab = await add_cab(db_session, world, HOME)
    await add_request(db_session, world, await add_employee(db_session, world, HOME))
    prompts = ModePromptService(db_session, world.clock)

    world.clock.advance(timedelta(seconds=60))
    await prompts.run_due_mode_prompts(world.operator_id)
    assert await down_alerts(db_session, world) == [], "one minute is not an outage"

    world.clock.advance(timedelta(minutes=5))
    await ping(db_session, world, cab, HOME)
    await prompts.run_due_mode_prompts(world.operator_id)

    (alert,) = await down_alerts(db_session, world)
    assert alert.data is not None and alert.data["reason"] == "not_running"

    # The worker comes back: its first run clears the alert, with nobody touching anything.
    optimizer = service(db_session, world)
    await ping(db_session, world, cab, HOME)
    await optimizer.run_due_batches(world.operator_id)
    assert await down_alerts(db_session, world) == []


async def test_a_paused_operator_is_not_reported_as_having_a_dead_optimizer(
    db_session: AsyncSession,
) -> None:
    world = await make_world(db_session, Mode.full_auto)
    cab = await add_cab(db_session, world, HOME)
    await add_request(db_session, world, await add_employee(db_session, world, HOME))
    dispatch = DispatchService(db_session, world.clock, eta_service(world.clock))
    await dispatch.set_automation_paused(world.operator_id, True, "safety")
    world.clock.advance(timedelta(minutes=10))
    await ping(db_session, world, cab, HOME)

    await ModePromptService(db_session, world.clock).run_due_mode_prompts(world.operator_id)

    assert await down_alerts(db_session, world) == []


async def test_one_bad_batch_is_a_blip_not_an_outage(db_session: AsyncSession) -> None:
    world = await make_world(db_session, Mode.full_auto)
    cab = await add_cab(db_session, world, HOME)
    request = await add_request(db_session, world, await add_employee(db_session, world, HOME))
    optimizer = service(db_session, world, Flaky(failures=1))

    await tick(db_session, world, optimizer, cab)
    assert await down_alerts(db_session, world) == []
    await tick(db_session, world, optimizer, cab)

    await db_session.refresh(request)
    assert request.status == str(RequestStatus.assigned)


async def test_open_offers_still_reach_their_failsafe_while_the_optimizer_is_down(
    db_session: AsyncSession,
) -> None:
    """An offer made before the outage was a human-reviewable decision with a timer; the
    failsafe does not depend on the optimizer, and a rider must not be stranded by one."""
    world = await make_world(db_session, Mode.semi_auto)
    cab = await add_cab(db_session, world, HOME)
    request = await add_request(db_session, world, await add_employee(db_session, world, HOME))
    optimizer = service(db_session, world)
    world.clock.advance(timedelta(seconds=WINDOW))
    await ping(db_session, world, cab, HOME)
    await optimizer.run_due_batches(world.operator_id)
    offer = await db_session.scalar(select(Suggestion).where(Suggestion.request_id == request.id))
    assert offer is not None

    world.clock.advance(timedelta(seconds=200))  # past the 180 s failsafe, inside the window
    await ping(db_session, world, cab, HOME)
    sweep = await SemiAutoService(db_session, world.clock, optimizer.dispatch).run_due_semi_auto(
        world.operator_id
    )

    assert sweep.assigned == 1
    await db_session.refresh(request)
    assert request.status == str(RequestStatus.assigned)


# --- what a supervisor is told ------------------------------------------------------------------


@pytest_asyncio.fixture
async def api(db_session: AsyncSession) -> Any:
    clock = FakeClock(NOW)
    world = await make_world(db_session, Mode.full_auto)
    world.clock = clock
    supervisor = make_user(name="Sunil", phone=unique_phone())
    db_session.add(supervisor)
    await db_session.flush()
    db_session.add(make_user_role(supervisor.id, Role.supervisor, operator_id=world.operator_id))
    await db_session.flush()
    settings = Settings(
        app_env="dev",
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        jwt_secret=JWT_SECRET,
        routing_provider="approx",
    )
    application = create_app(settings=settings, clock=clock)

    class _Factory:
        def __call__(self) -> object:
            return _NoClose(db_session)

    application.state.session_factory = _Factory()
    token, _ = create_access_token(
        user_id=supervisor.id,
        role=str(Role.supervisor),
        secret=JWT_SECRET,
        clock=clock,
        ttl_seconds=900,
        operator_id=world.operator_id,
    )
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as client:
        yield client, world, {"Authorization": f"Bearer {token}"}


class _NoClose:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def __aenter__(self) -> AsyncSession:
        return self._session

    async def __aexit__(self, *exc_info: object) -> None:
        return None


async def test_the_mode_endpoint_says_manual_because_the_optimizer_is_down(
    db_session: AsyncSession, api: Any
) -> None:
    client, world, headers = api
    cab = await add_cab(db_session, world, HOME)
    request = await add_request(db_session, world, await add_employee(db_session, world, HOME))

    before = (await client.get(f"/dispatch/requests/{request.id}/mode", headers=headers)).json()
    assert before["mode"] == "full_auto"

    optimizer = service(db_session, world, Flaky(failures=99))
    for _ in range(3):
        await tick(db_session, world, optimizer, cab)
    after = (await client.get(f"/dispatch/requests/{request.id}/mode", headers=headers)).json()

    assert after["mode"] == "manual" and after["reason"] == "optimizer_down"
