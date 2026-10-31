"""Micro-batching: requests are collected for a window and solved together (B30).

Every timing branch is reached by advancing a `FakeClock`, so a scenario that jumps time
produces the same batches this does.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.domain.enums import ActorType, Direction
from app.domain.modes import Mode
from app.domain.optimizer import Plan, Problem
from app.domain.state_machines import Actor, RequestStatus
from app.modules.dispatch.optimizer_models import OptimizerRun
from app.modules.dispatch.optimizer_service import OptimizerService
from app.modules.dispatch.service import DispatchService
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
    ping,
    set_config,
)

pytestmark = pytest.mark.requires_db

WINDOW = 45
HOME_A = near(*OFFICE, north_km=-6.0)
HOME_B = near(*OFFICE, north_km=-7.0)


class Recorder:
    """A solver that remembers what it was asked, and answers with a fixed plan."""

    def __init__(self, plan: Plan | None = None, raises: bool = False) -> None:
        self.calls: list[Problem] = []
        self.plan = plan or Plan()
        self.raises = raises

    def __call__(self, problem: Problem) -> Plan:
        self.calls.append(problem)
        if self.raises:
            raise RuntimeError("the solver fell over")
        return self.plan


@pytest_asyncio.fixture
async def world(db_session: AsyncSession) -> World:
    world = await build_world(db_session, FakeClock(NOW), Mode.full_auto)
    await set_config(db_session, world, batch_window_seconds=WINDOW)
    return world


def service(
    db_session: AsyncSession, world: World, solver: Recorder | None = None
) -> OptimizerService:
    dispatch = DispatchService(db_session, world.clock, eta_service(world.clock))
    return OptimizerService(db_session, world.clock, dispatch, solver=solver)


async def runs(db_session: AsyncSession, world: World) -> list[OptimizerRun]:
    rows = await db_session.execute(
        select(OptimizerRun)
        .where(OptimizerRun.operator_id == world.operator_id)
        .order_by(OptimizerRun.started_at)
    )
    return list(rows.scalars())


async def test_two_requests_inside_one_window_are_solved_in_one_call(
    db_session: AsyncSession, world: World
) -> None:
    solver = Recorder()
    optimizer = service(db_session, world, solver)
    await add_cab(db_session, world, HOME_A)
    first = await add_employee(db_session, world, HOME_A)
    second = await add_employee(db_session, world, HOME_B)

    await add_request(db_session, world, first)
    world.clock.advance(timedelta(seconds=20))
    await add_request(db_session, world, second)

    world.clock.advance(timedelta(seconds=10))  # 30 s after the first: window still open
    assert (await optimizer.run_due_batches(world.operator_id)).runs == 0
    assert solver.calls == []

    world.clock.advance(timedelta(seconds=15))  # 45 s after the first: window closes
    sweep = await optimizer.run_due_batches(world.operator_id)

    assert sweep.runs == 1 and sweep.requests == 2
    assert len(solver.calls) == 1
    assert len(solver.calls[0].requests) == 2


async def test_one_big_clock_jump_gives_the_same_single_batch(
    db_session: AsyncSession, world: World
) -> None:
    """The simulator jumps time instead of ticking: the batches must come out the same."""
    solver = Recorder()
    optimizer = service(db_session, world, solver)
    await add_cab(db_session, world, HOME_A)
    first = await add_employee(db_session, world, HOME_A)
    second = await add_employee(db_session, world, HOME_B)
    await add_request(db_session, world, first)
    world.clock.advance(timedelta(seconds=20))
    await add_request(db_session, world, second)

    world.clock.advance(timedelta(hours=1))
    await optimizer.run_due_batches(world.operator_id)

    assert len(solver.calls) == 1
    assert len(solver.calls[0].requests) == 2


async def test_nothing_runs_with_nothing_to_solve(db_session: AsyncSession, world: World) -> None:
    solver = Recorder()

    sweep = await service(db_session, world, solver).run_due_batches(world.operator_id)

    assert sweep.runs == 0 and solver.calls == []


async def test_a_batch_that_finds_no_solution_leaves_every_request_as_it_was(
    db_session: AsyncSession, world: World
) -> None:
    solver = Recorder(Plan())
    optimizer = service(db_session, world, solver)
    await add_cab(db_session, world, HOME_A)
    employee = await add_employee(db_session, world, HOME_A)
    request = await add_request(db_session, world, employee)
    before = (request.status, request.trip_id, request.lock_vehicle_id, request.hold_until)
    world.clock.advance(timedelta(seconds=WINDOW))

    sweep = await optimizer.run_due_batches(world.operator_id)

    assert sweep.runs == 1 and sweep.placed == 0
    await db_session.refresh(request)
    assert (request.status, request.trip_id, request.lock_vehicle_id, request.hold_until) == before
    (run,) = await runs(db_session, world)
    assert run.status == "no_solution"
    assert run.request_ids == [str(request.id)]


async def test_a_solver_that_raises_leaves_requests_alone_and_is_recorded_as_failed(
    db_session: AsyncSession, world: World
) -> None:
    solver = Recorder(raises=True)
    optimizer = service(db_session, world, solver)
    await add_cab(db_session, world, HOME_A)
    request = await add_request(db_session, world, await add_employee(db_session, world, HOME_A))
    world.clock.advance(timedelta(seconds=WINDOW))

    sweep = await optimizer.run_due_batches(world.operator_id)

    assert sweep.failed == 1
    await db_session.refresh(request)
    assert request.status == str(RequestStatus.queued)
    (run,) = await runs(db_session, world)
    assert run.status == "failed" and "fell over" in (run.error or "")


async def test_a_request_left_over_is_tried_again_one_window_later_not_every_sweep(
    db_session: AsyncSession, world: World
) -> None:
    solver = Recorder()
    optimizer = service(db_session, world, solver)
    await add_cab(db_session, world, HOME_A)
    await add_request(db_session, world, await add_employee(db_session, world, HOME_A))
    world.clock.advance(timedelta(seconds=WINDOW))
    await optimizer.run_due_batches(world.operator_id)

    world.clock.advance(timedelta(seconds=10))
    assert (await optimizer.run_due_batches(world.operator_id)).runs == 0

    world.clock.advance(timedelta(seconds=WINDOW))
    assert (await optimizer.run_due_batches(world.operator_id)).runs == 1
    assert len(solver.calls) == 2


async def test_running_the_sweep_twice_at_the_same_instant_runs_once(
    db_session: AsyncSession, world: World
) -> None:
    solver = Recorder()
    optimizer = service(db_session, world, solver)
    await add_request(db_session, world, await add_employee(db_session, world, HOME_A))
    world.clock.advance(timedelta(seconds=WINDOW))

    await optimizer.run_due_batches(world.operator_id)
    await optimizer.run_due_batches(world.operator_id)

    assert len(solver.calls) == 1


async def test_a_held_request_joins_the_batch_only_when_its_hold_ends(
    db_session: AsyncSession, world: World
) -> None:
    solver = Recorder()
    optimizer = service(db_session, world, solver)
    await add_cab(db_session, world, OFFICE)
    rider = await add_employee(db_session, world, HOME_A)
    await add_request(db_session, world, rider, direction=Direction.from_office)

    world.clock.advance(timedelta(minutes=9))
    assert (await optimizer.run_due_batches(world.operator_id)).runs == 0

    # The hold ends at +10 minutes, and the batch window opens when it does.
    world.clock.advance(timedelta(minutes=1))
    assert (await optimizer.run_due_batches(world.operator_id)).runs == 0
    world.clock.advance(timedelta(seconds=WINDOW))
    assert (await optimizer.run_due_batches(world.operator_id)).runs == 1
    assert len(solver.calls[0].requests) == 1


async def test_a_supervisors_hold_keeps_a_request_out_of_the_batch(
    db_session: AsyncSession, world: World
) -> None:
    solver = Recorder()
    optimizer = service(db_session, world, solver)
    await add_request(
        db_session,
        world,
        await add_employee(db_session, world, HOME_A),
        hold_until=NOW + timedelta(hours=1),
    )
    world.clock.advance(timedelta(minutes=5))

    assert (await optimizer.run_due_batches(world.operator_id)).runs == 0


async def test_the_emergency_pause_stops_the_optimizer(
    db_session: AsyncSession, world: World
) -> None:
    solver = Recorder()
    dispatch = DispatchService(db_session, world.clock, eta_service(world.clock))
    await dispatch.set_automation_paused(world.operator_id, True, "safety")
    await add_request(db_session, world, await add_employee(db_session, world, HOME_A))
    world.clock.advance(timedelta(minutes=5))

    sweep = await OptimizerService(
        db_session, world.clock, dispatch, solver=solver
    ).run_due_batches(world.operator_id)

    assert sweep.runs == 0 and solver.calls == []


async def test_the_default_solver_places_a_request_and_records_the_plan(
    db_session: AsyncSession, world: World
) -> None:
    optimizer = service(db_session, world)
    cab = await add_cab(db_session, world, HOME_A)
    request = await add_request(db_session, world, await add_employee(db_session, world, HOME_A))
    world.clock.advance(timedelta(seconds=WINDOW))
    await ping(db_session, world, cab, HOME_A)

    sweep = await optimizer.run_due_batches(world.operator_id)

    assert sweep.placed == 1
    (run,) = await runs(db_session, world)
    assert run.status == "solved" and run.solver in ("greedy", "darp")
    assert run.plan is not None
    assert run.plan["placements"][0]["vehicle_id"] == str(cab.id)
    assert run.plan["placements"][0]["new"] == [str(request.id)]


async def test_the_problem_describes_a_cab_already_on_a_trip(
    db_session: AsyncSession, world: World
) -> None:
    dispatch = DispatchService(db_session, world.clock, eta_service(world.clock))
    optimizer = OptimizerService(db_session, world.clock, dispatch)
    cab: Vehicle = await add_cab(db_session, world, HOME_A)
    seated_request = await add_request(
        db_session, world, await add_employee(db_session, world, HOME_A)
    )
    await dispatch.assign(
        world.operator_id,
        seated_request.id,
        cab.id,
        Actor(str(ActorType.supervisor)),
        None,
    )
    waiting = await add_request(db_session, world, await add_employee(db_session, world, HOME_B))
    await ping(db_session, world, cab, HOME_A)

    problem = await optimizer.build_problem(world.operator_id, [waiting])

    (veh,) = problem.vehicles
    assert veh.trip is not None
    assert [seat.request_id for seat in veh.trip.riders] == [seated_request.id]
    assert not veh.trip.pooling_blocked and not veh.trip.pickups_done
    assert not veh.trip.order_fixed  # planned, nobody collected, nobody locked
    assert [req.request_id for req in problem.requests] == [waiting.id]
    # One matrix covers everything the solver can ask about.
    assert problem.duration(veh.position, problem.offices[waiting.office_id]) > 0
