"""One solver, three destinations: applied, offered, hinted (B32).

The two invariants Phase 3 may not weaken are tested here as much as the delivery is:
no automatic path touches a locked or overridden item, and applying a plan is a sequence
of state-machine transitions, never a bulk write.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import timedelta
from typing import Any

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.core.security import create_access_token
from app.core.settings import Settings
from app.domain.enums import ActorType, Role
from app.domain.failsafe import SuggestionStatus
from app.domain.modes import Mode
from app.domain.optimizer import Placement, Plan, Problem
from app.domain.state_machines import Actor, RequestStatus, VehicleStatus
from app.main import create_app
from app.modules.dispatch.models import Trip, TripEvent, TripStop
from app.modules.dispatch.optimizer_models import OptimizerHint, OptimizerRun
from app.modules.dispatch.optimizer_service import OptimizerService
from app.modules.dispatch.semi_auto import SemiAutoService
from app.modules.dispatch.service import DispatchService
from app.modules.dispatch.suggestion_models import Suggestion
from app.modules.fleet.models import Vehicle
from app.modules.requests.models import RideRequest, RideRequestEvent
from tests.builders import make_user, make_user_role, unique_phone
from tests.integration.worlds import (
    NOW,
    OFFICE,
    World,
    add_cab,
    add_client,
    add_employee,
    add_request,
    build_world,
    eta_service,
    near,
)

pytestmark = pytest.mark.requires_db

JWT_SECRET = "optimizer-tests-secret-0123456789abc"
HOME_1 = near(*OFFICE, north_km=-6.0)
HOME_2 = near(*OFFICE, north_km=-4.0)
HOME_3 = near(*OFFICE, north_km=-2.0)
HOME_NEXT = near(*OFFICE, north_km=-5.0)  # a kilometre on from HOME_1, towards the office


def optimizer_for(
    session: AsyncSession, world: World, solver: object | None = None
) -> OptimizerService:
    dispatch = DispatchService(session, world.clock, eta_service(world.clock))
    return OptimizerService(session, world.clock, dispatch, solver=solver)  # type: ignore[arg-type]


async def batch(session: AsyncSession, world: World, requests: list[RideRequest]) -> None:
    await optimizer_for(session, world).run_batch(world.operator_id, requests)


async def count(session: AsyncSession, model: type, *conditions: Any) -> int:
    result = await session.scalar(select(func.count()).select_from(model).where(*conditions))
    return int(result or 0)


# --- one batch, three scopes ------------------------------------------------------------


async def test_the_same_batch_is_applied_offered_and_hinted_by_scope(
    db_session: AsyncSession,
) -> None:
    world = await build_world(db_session, FakeClock(NOW), mode=None)
    auto, semi, manual = [
        await add_client(db_session, world, name, mode)
        for name, mode in (
            ("Auto", Mode.full_auto),
            ("Semi", Mode.semi_auto),
            ("Hand", Mode.manual),
        )
    ]
    requests: dict[str, RideRequest] = {}
    for label, (client, office), home in (
        ("auto", auto, HOME_1),
        ("semi", semi, HOME_2),
        ("manual", manual, HOME_3),
    ):
        rider = await add_employee(db_session, world, home, label, client=client, office=office)
        await add_cab(db_session, world, home)
        requests[label] = await add_request(db_session, world, rider)

    await batch(db_session, world, list(requests.values()))

    for request in requests.values():
        await db_session.refresh(request)

    # full_auto: an assignment, by the optimizer, through the state machine.
    assert requests["auto"].status == str(RequestStatus.assigned)
    trip = await db_session.get(Trip, requests["auto"].trip_id)
    assert trip is not None and trip.mode_used == "full_auto"
    assigned_events = (
        (
            await db_session.execute(
                select(RideRequestEvent).where(
                    RideRequestEvent.request_id == requests["auto"].id,
                    RideRequestEvent.to_status == str(RequestStatus.assigned),
                )
            )
        )
        .scalars()
        .all()
    )
    assert [e.actor_type for e in assigned_events] == [str(ActorType.optimizer)]
    trip_events = (
        (await db_session.execute(select(TripEvent).where(TripEvent.trip_id == trip.id)))
        .scalars()
        .all()
    )
    assert trip_events and {e.actor_type for e in trip_events} == {str(ActorType.optimizer)}

    # semi_auto: an offer, nothing assigned.
    assert requests["semi"].status == str(RequestStatus.queued)
    offers = (
        (
            await db_session.execute(
                select(Suggestion)
                .where(Suggestion.request_id == requests["semi"].id)
                .order_by(Suggestion.rank)
            )
        )
        .scalars()
        .all()
    )
    assert offers and offers[0].rank == 1
    assert offers[0].status == str(SuggestionStatus.offered)
    assert any("min away" in reason for reason in offers[0].reasons)

    # manual: a hint, no offer, nothing assigned.
    assert requests["manual"].status == str(RequestStatus.queued)
    assert await count(db_session, Suggestion, Suggestion.request_id == requests["manual"].id) == 0
    hint = await db_session.scalar(
        select(OptimizerHint).where(OptimizerHint.request_id == requests["manual"].id)
    )
    assert hint is not None and hint.superseded_at is None
    assert (
        await count(db_session, OptimizerHint, OptimizerHint.request_id == requests["semi"].id) == 0
    )

    modes = {
        run.mode
        for run in (await db_session.execute(select(OptimizerRun))).scalars()
        if run.operator_id == world.operator_id
    }
    assert modes == {"full_auto", "semi_auto", "manual"}


# --- locked and blocked items are never touched ----------------------------------------------


@pytest.mark.parametrize("mode", [Mode.full_auto, Mode.semi_auto, Mode.manual])
async def test_a_locked_rider_and_a_blocked_trip_come_out_untouched_in_every_mode(
    db_session: AsyncSession, mode: Mode
) -> None:
    world = await build_world(db_session, FakeClock(NOW), mode)
    dispatch = DispatchService(db_session, world.clock, eta_service(world.clock))
    supervisor = Actor(str(ActorType.supervisor))

    locked_cab = await add_cab(db_session, world, HOME_1)
    blocked_cab = await add_cab(db_session, world, HOME_2)
    await add_cab(db_session, world, HOME_3)

    locked_rider = await add_request(
        db_session, world, await add_employee(db_session, world, HOME_1, "locked")
    )
    trip_a = await dispatch.assign(
        world.operator_id, locked_rider.id, locked_cab.id, supervisor, None
    )
    locked_rider.lock_vehicle_id = locked_cab.id

    blocked_rider = await add_request(
        db_session, world, await add_employee(db_session, world, HOME_2, "blocked")
    )
    trip_b = await dispatch.assign(
        world.operator_id, blocked_rider.id, blocked_cab.id, supervisor, None
    )
    trip_b.pooling_blocked = True
    await db_session.flush()

    async def snapshot(trip: Trip) -> list[tuple[uuid.UUID, str, int]]:
        stops = (
            (
                await db_session.execute(
                    select(TripStop).where(TripStop.trip_id == trip.id).order_by(TripStop.sequence)
                )
            )
            .scalars()
            .all()
        )
        return [(s.request_id, s.stop_type, s.sequence) for s in stops]

    before_a, before_b = await snapshot(trip_a), await snapshot(trip_b)

    newcomers = [
        await add_request(
            db_session, world, await add_employee(db_session, world, near(*HOME_2, north_km=0.4))
        ),
        await add_request(
            db_session, world, await add_employee(db_session, world, near(*HOME_1, north_km=0.4))
        ),
    ]
    await batch(db_session, world, newcomers)

    # Trip B is blocked: nobody joined it, nothing about it moved.
    assert await snapshot(trip_b) == before_b
    # Trip A took no one out of order: the locked rider's own two stops keep their relative
    # position against every stop that was already there.
    after_a = await snapshot(trip_a)
    kept = [entry for entry in after_a if entry[0] == locked_rider.id]
    assert [entry[1] for entry in kept] == [entry[1] for entry in before_a]
    await db_session.refresh(locked_rider)
    assert locked_rider.trip_id == trip_a.id
    assert locked_rider.lock_vehicle_id == locked_cab.id
    assert locked_rider.status == str(RequestStatus.assigned)
    for newcomer in newcomers:
        await db_session.refresh(newcomer)
        assert newcomer.trip_id != trip_b.id


async def test_a_locked_queued_request_is_only_ever_planned_onto_its_own_cab(
    db_session: AsyncSession,
) -> None:
    world = await build_world(db_session, FakeClock(NOW), Mode.full_auto)
    nearer = await add_cab(db_session, world, HOME_1)
    pinned = await add_cab(db_session, world, near(*HOME_1, north_km=-2.0))
    request = await add_request(
        db_session,
        world,
        await add_employee(db_session, world, HOME_1),
        lock_vehicle_id=pinned.id,
    )

    await batch(db_session, world, [request])

    await db_session.refresh(request)
    trip = await db_session.get(Trip, request.trip_id)
    assert trip is not None and trip.vehicle_id == pinned.id != nearer.id


# --- applying is a transition, not a write ---------------------------------------------------


async def test_a_refused_transition_leaves_nothing_behind(db_session: AsyncSession) -> None:
    """A plan that puts a locked request on a different cab is stopped by the state machine.

    The solver would never produce it - this is the second guard, the one that holds when
    the first is wrong. The refusal comes after the trip and its stops were written, so
    the test is also that the savepoint takes them back.
    """
    world = await build_world(db_session, FakeClock(NOW), Mode.full_auto)
    pinned = await add_cab(db_session, world, HOME_1)
    other = await add_cab(db_session, world, HOME_2)
    request = await add_request(
        db_session,
        world,
        await add_employee(db_session, world, HOME_1),
        lock_vehicle_id=pinned.id,
    )
    bad_plan = Plan(
        placements=(
            Placement(
                vehicle_id=other.id,
                trip_id=None,
                order=(request.id,),
                new_request_ids=(request.id,),
                pickup_eta_seconds={request.id: 120.0},
                added_minutes={},
                cost=1.0,
            ),
        ),
        solver="test",
    )

    def solver(_: Problem) -> Plan:
        return bad_plan

    await optimizer_for(db_session, world, solver).run_batch(world.operator_id, [request])

    await db_session.refresh(request)
    await db_session.refresh(other)
    assert request.status == str(RequestStatus.queued) and request.trip_id is None
    assert await count(db_session, Trip, Trip.operator_id == world.operator_id) == 0
    assert await count(db_session, TripStop, TripStop.operator_id == world.operator_id) == 0
    assert other.status == str(VehicleStatus.available)


async def test_a_pooled_plan_is_applied_rider_by_rider_in_the_planned_order(
    db_session: AsyncSession,
) -> None:
    world = await build_world(db_session, FakeClock(NOW), Mode.full_auto)
    cab = await add_cab(db_session, world, near(*OFFICE, north_km=-7.0))
    first = await add_request(
        db_session, world, await add_employee(db_session, world, HOME_1, "Far")
    )
    second = await add_request(
        db_session, world, await add_employee(db_session, world, HOME_NEXT, "Mid")
    )

    await batch(db_session, world, [first, second])

    for request in (first, second):
        await db_session.refresh(request)
        assert request.status == str(RequestStatus.assigned)
    assert first.trip_id == second.trip_id
    stops = (
        (
            await db_session.execute(
                select(TripStop)
                .where(TripStop.trip_id == first.trip_id)
                .order_by(TripStop.sequence)
            )
        )
        .scalars()
        .all()
    )
    pickups = [s.request_id for s in stops if s.stop_type == "pickup"]
    assert pickups == [first.id, second.id]  # the cab comes from the far side: far rider first
    assert all(r.pooling_added_minutes is not None for r in (first, second))
    assert (await db_session.get(Vehicle, cab.id)).status == str(VehicleStatus.on_trip)  # type: ignore[union-attr]
    events = await count(
        db_session,
        RideRequestEvent,
        RideRequestEvent.to_status == str(RequestStatus.assigned),
        RideRequestEvent.actor_type == str(ActorType.optimizer),
    )
    assert events == 2


async def test_a_vehicle_with_no_driver_on_duty_is_refused_not_forced(
    db_session: AsyncSession,
) -> None:
    from app.modules.fleet.duty_models import DutySession

    world = await build_world(db_session, FakeClock(NOW), Mode.full_auto)
    cab = await add_cab(db_session, world, HOME_1)
    request = await add_request(db_session, world, await add_employee(db_session, world, HOME_1))
    plan = Plan(
        placements=(
            Placement(
                vehicle_id=cab.id,
                trip_id=None,
                order=(request.id,),
                new_request_ids=(request.id,),
                pickup_eta_seconds={request.id: 60.0},
                added_minutes={},
                cost=1.0,
            ),
        ),
    )
    session_row = await db_session.scalar(
        select(DutySession).where(DutySession.vehicle_id == cab.id)
    )
    assert session_row is not None
    session_row.ended_at = NOW

    def solver(_: Problem) -> Plan:
        return plan

    await optimizer_for(db_session, world, solver).run_batch(world.operator_id, [request])

    await db_session.refresh(request)
    assert request.status == str(RequestStatus.queued)


# --- semi_auto offers -------------------------------------------------------------------------


async def test_an_offered_request_is_not_replanned_until_the_offer_is_answered(
    db_session: AsyncSession,
) -> None:
    world = await build_world(db_session, FakeClock(NOW), Mode.semi_auto)
    await add_cab(db_session, world, HOME_1)
    request = await add_request(db_session, world, await add_employee(db_session, world, HOME_1))
    optimizer = optimizer_for(db_session, world)
    world.clock.advance(timedelta(seconds=45))

    first = await optimizer.run_due_batches(world.operator_id)
    world.clock.advance(timedelta(seconds=90))
    second = await optimizer.run_due_batches(world.operator_id)

    assert first.suggested == 1 and second.runs == 0
    assert await count(db_session, Suggestion, Suggestion.request_id == request.id) >= 1


async def test_approving_the_optimizers_offer_assigns_its_vehicle(db_session: AsyncSession) -> None:
    world = await build_world(db_session, FakeClock(NOW), Mode.semi_auto)
    cab = await add_cab(db_session, world, HOME_1)
    request = await add_request(db_session, world, await add_employee(db_session, world, HOME_1))
    await batch(db_session, world, [request])
    offer = await db_session.scalar(
        select(Suggestion).where(Suggestion.request_id == request.id, Suggestion.rank == 1)
    )
    assert offer is not None
    semi = SemiAutoService(
        db_session, world.clock, DispatchService(db_session, world.clock, eta_service(world.clock))
    )

    trip_id = await semi.accept(
        world.operator_id, offer.id, Actor(str(ActorType.supervisor)), actor_user_id=None
    )

    await db_session.refresh(request)
    assert request.status == str(RequestStatus.assigned) and request.trip_id == trip_id
    assert (await db_session.get(Trip, trip_id)).vehicle_id == cab.id  # type: ignore[union-attr]


# --- the API ---------------------------------------------------------------------


@pytest_asyncio.fixture
async def api(db_session: AsyncSession) -> AsyncIterator[tuple[AsyncClient, World, dict[str, str]]]:
    clock = FakeClock(NOW)
    world = await build_world(db_session, clock, Mode.manual)
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
    application: FastAPI = create_app(settings=settings, clock=clock)

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


async def test_hints_are_listed_for_manual_scopes_and_die_with_the_queue(
    db_session: AsyncSession, api: tuple[AsyncClient, World, dict[str, str]]
) -> None:
    client, world, headers = api
    cab = await add_cab(db_session, world, HOME_1)
    request = await add_request(db_session, world, await add_employee(db_session, world, HOME_1))
    await batch(db_session, world, [request])

    response = await client.get("/dispatch/hints", headers=headers)

    assert response.status_code == 200
    (hint,) = response.json()["items"]
    assert hint["request_id"] == str(request.id) and hint["vehicle_id"] == str(cab.id)
    assert hint["rider_order"] == [str(request.id)] and hint["reasons"]
    # Nothing was assigned: the supervisor still has the whole decision.
    await db_session.refresh(request)
    assert request.status == str(RequestStatus.queued)

    await DispatchService(db_session, world.clock, eta_service(world.clock)).assign(
        world.operator_id, request.id, cab.id, Actor(str(ActorType.supervisor)), None
    )
    assert (await client.get("/dispatch/hints", headers=headers)).json()["items"] == []


async def test_a_replanned_request_has_one_live_hint_not_two(
    db_session: AsyncSession, api: tuple[AsyncClient, World, dict[str, str]]
) -> None:
    client, world, headers = api
    await add_cab(db_session, world, HOME_1)
    request = await add_request(db_session, world, await add_employee(db_session, world, HOME_1))

    await batch(db_session, world, [request])
    world.clock.advance(timedelta(seconds=60))
    await batch(db_session, world, [request])

    assert len((await client.get("/dispatch/hints", headers=headers)).json()["items"]) == 1
    assert await count(db_session, OptimizerHint, OptimizerHint.request_id == request.id) == 2


async def test_the_trip_board_shows_each_rider_and_what_pooling_cost_them(
    db_session: AsyncSession, api: tuple[AsyncClient, World, dict[str, str]]
) -> None:
    client, world, headers = api
    dispatch = DispatchService(db_session, world.clock, eta_service(world.clock))
    cab = await add_cab(db_session, world, near(*OFFICE, north_km=-7.0))
    far = await add_request(
        db_session, world, await add_employee(db_session, world, HOME_1, "Farida Khan")
    )
    mid = await add_request(
        db_session, world, await add_employee(db_session, world, HOME_NEXT, "Mohan Das")
    )
    supervisor = Actor(str(ActorType.supervisor))
    await dispatch.assign(world.operator_id, far.id, cab.id, supervisor, None)
    await dispatch.assign(world.operator_id, mid.id, cab.id, supervisor, None)

    response = await client.get("/dispatch/trips", headers=headers)

    (trip,) = response.json()["items"]
    riders = trip["riders"]
    assert [r["rider_first_name"] for r in riders] == ["Farida", "Mohan"]
    assert all(r["added_minutes"] is not None and r["added_minutes"] >= 0 for r in riders)
