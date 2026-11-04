"""Mode-switch prompts against a real database (B35, `control-model.md` §5).

Each of the four conditions is made to hold on its own, because "any is true" means a
test that sets two cannot say which one raised the prompt.
"""

from __future__ import annotations

import uuid
from datetime import timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.domain.enums import ActorType, AlertType
from app.domain.failsafe import SuggestionStatus
from app.domain.modes import Mode
from app.domain.state_machines import Actor, RequestStatus, StopKind, StopStatus, VehicleStatus
from app.modules.alerts.models import Alert
from app.modules.dispatch.models import TripStop
from app.modules.dispatch.service import DispatchService
from app.modules.dispatch.suggestion_models import Suggestion
from app.modules.fleet.models import Vehicle
from app.modules.modes.models import ModeSetting
from app.modules.modes.prompts import ModePromptService
from app.modules.requests.models import RideRequestEvent
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
    ping,
)

pytestmark = pytest.mark.requires_db

HOME = near(*OFFICE, north_km=-6.0)


def prompts(session: AsyncSession, world: World) -> ModePromptService:
    return ModePromptService(session, world.clock)


async def prompt_alerts(
    session: AsyncSession, world: World, *, open_only: bool = True
) -> list[Alert]:
    query = select(Alert).where(
        Alert.operator_id == world.operator_id, Alert.type == str(AlertType.mode_prompt)
    )
    if open_only:
        query = query.where(Alert.status != "resolved")
    return list((await session.execute(query.order_by(Alert.created_at))).scalars())


def conditions_of(alert: Alert) -> set[str]:
    return {item["condition"] for item in (alert.data or {})["conditions"]}


async def decided_suggestions(
    session: AsyncSession, world: World, cab: Vehicle, verdicts: list[SuggestionStatus]
) -> None:
    """One rank-1 suggestion per verdict, each for its own request, decided just now."""
    for verdict in verdicts:
        request = await add_request(session, world, await add_employee(session, world, HOME))
        session.add(
            Suggestion(
                id=uuid.uuid4(),
                operator_id=world.operator_id,
                request_id=request.id,
                vehicle_id=cab.id,
                rank=1,
                cost=1.0,
                reasons=[],
                status=str(verdict),
                offered_at=world.clock.now() - timedelta(minutes=5),
                failsafe_due_at=world.clock.now(),
                decided_at=world.clock.now() - timedelta(minutes=1),
            )
        )
    await session.flush()


async def make_world(session: AsyncSession, mode: Mode = Mode.semi_auto) -> World:
    return await build_world(session, FakeClock(NOW), mode)


# --- condition 1: suggestions rejected -----------------------------------------


async def test_a_third_of_suggestions_rejected_raises_a_prompt(db_session: AsyncSession) -> None:
    world = await make_world(db_session)
    cab = await add_cab(db_session, world, HOME)
    accepted, rejected = SuggestionStatus.accepted, SuggestionStatus.rejected
    await decided_suggestions(db_session, world, cab, [accepted] * 6 + [rejected] * 4)

    sweep = await prompts(db_session, world).run_due_mode_prompts(world.operator_id)

    assert sweep.raised == 1
    (alert,) = await prompt_alerts(db_session, world)
    assert conditions_of(alert) == {"suggestions_rejected"}
    assert alert.data is not None and alert.data["suggest"] == "manual"
    setting = await db_session.scalar(
        select(ModeSetting).where(ModeSetting.operator_id == world.operator_id)
    )
    assert alert.data["setting_id"] == str(setting.id)  # type: ignore[union-attr]


async def test_a_few_rejections_among_many_is_not_a_signal(db_session: AsyncSession) -> None:
    world = await make_world(db_session)
    cab = await add_cab(db_session, world, HOME)
    accepted, rejected = SuggestionStatus.accepted, SuggestionStatus.rejected
    await decided_suggestions(db_session, world, cab, [accepted] * 9 + [rejected] * 1)

    assert (await prompts(db_session, world).run_due_mode_prompts(world.operator_id)).raised == 0


async def test_the_failsafe_taking_over_counts_as_decided_but_not_as_rejected(
    db_session: AsyncSession,
) -> None:
    world = await make_world(db_session)
    cab = await add_cab(db_session, world, HOME)
    await decided_suggestions(
        db_session,
        world,
        cab,
        [SuggestionStatus.failsafe_assigned] * 6 + [SuggestionStatus.rejected],
    )

    assert (await prompts(db_session, world).run_due_mode_prompts(world.operator_id)).raised == 0


async def test_old_decisions_fall_out_of_the_window(db_session: AsyncSession) -> None:
    world = await make_world(db_session)
    cab = await add_cab(db_session, world, HOME)
    await decided_suggestions(db_session, world, cab, [SuggestionStatus.rejected] * 6)
    world.clock.advance(timedelta(minutes=16))
    await ping(db_session, world, cab, HOME)  # the cab is still reporting

    assert (await prompts(db_session, world).run_due_mode_prompts(world.operator_id)).raised == 0


# --- condition 2: ETA error ------------------------------------------------------------------


async def test_a_median_eta_error_over_ten_minutes_raises_a_prompt(
    db_session: AsyncSession,
) -> None:
    world = await make_world(db_session)
    dispatch = DispatchService(db_session, world.clock, eta_service(world.clock))
    supervisor = Actor(str(ActorType.supervisor))
    for _ in range(5):
        cab = await add_cab(db_session, world, HOME)
        request = await add_request(db_session, world, await add_employee(db_session, world, HOME))
        trip = await dispatch.assign(world.operator_id, request.id, cab.id, supervisor, None)
        stop = await db_session.scalar(
            select(TripStop).where(
                TripStop.trip_id == trip.id, TripStop.stop_type == str(StopKind.pickup)
            )
        )
        assert stop is not None and stop.planned_eta is not None
        stop.status = str(StopStatus.done)
        stop.done_at = world.clock.now() + timedelta(minutes=14)  # 14 minutes after planned
    await db_session.flush()
    world.clock.advance(timedelta(minutes=14))
    for vehicle in world.vehicles:
        from tests.integration.worlds import ping

        await ping(db_session, world, vehicle, HOME)

    sweep = await prompts(db_session, world).run_due_mode_prompts(world.operator_id)

    assert sweep.raised == 1
    (alert,) = await prompt_alerts(db_session, world)
    assert conditions_of(alert) == {"eta_error"}


# --- condition 3: a surge ------------------------------------------------------


async def test_pending_requests_over_twice_normal_for_the_slot_raise_a_prompt(
    db_session: AsyncSession,
) -> None:
    world = await make_world(db_session)
    cab = await add_cab(db_session, world, HOME)
    rider = await add_employee(db_session, world, HOME)
    # Three previous days: two requests were waiting at this time of day on each.
    for day in (1, 2, 3):
        moment = NOW - timedelta(days=day)
        for _ in range(2):
            past = await add_request(
                db_session, world, rider, queued_at=moment - timedelta(minutes=10)
            )
            past.status = str(RequestStatus.dropped)
            db_session.add(
                RideRequestEvent(
                    operator_id=world.operator_id,
                    request_id=past.id,
                    from_status="queued",
                    to_status=str(RequestStatus.assigned),
                    actor_type=str(ActorType.supervisor),
                    at=moment + timedelta(minutes=10),
                )
            )
    # Today: nine waiting - well over twice a normal two.
    for _ in range(9):
        await add_request(db_session, world, rider)
    await db_session.flush()
    del cab

    sweep = await prompts(db_session, world).run_due_mode_prompts(world.operator_id)

    assert sweep.raised == 1
    (alert,) = await prompt_alerts(db_session, world)
    assert conditions_of(alert) == {"pending_surge"}


async def test_without_history_a_busy_morning_is_not_a_surge(db_session: AsyncSession) -> None:
    world = await make_world(db_session)
    await add_cab(db_session, world, HOME)
    rider = await add_employee(db_session, world, HOME)
    for _ in range(12):
        await add_request(db_session, world, rider)

    assert (await prompts(db_session, world).run_due_mode_prompts(world.operator_id)).raised == 0


# --- condition 4: the fleet ----------------------------------------------------


async def test_a_fifth_of_the_fleet_out_of_service_raises_a_prompt(
    db_session: AsyncSession,
) -> None:
    world = await make_world(db_session)
    cabs = [await add_cab(db_session, world, HOME) for _ in range(5)]
    assert (await prompts(db_session, world).run_due_mode_prompts(world.operator_id)).raised == 0

    cabs[0].status = str(VehicleStatus.out_of_service)
    await db_session.flush()
    sweep = await prompts(db_session, world).run_due_mode_prompts(world.operator_id)

    assert sweep.raised == 1
    (alert,) = await prompt_alerts(db_session, world)
    assert conditions_of(alert) == {"fleet_degraded"}


async def test_stale_vehicles_count_as_degraded(db_session: AsyncSession) -> None:
    world = await make_world(db_session)
    for _ in range(5):
        await add_cab(db_session, world, HOME)
    world.clock.advance(timedelta(minutes=5))  # nobody has pinged since: all five are stale

    sweep = await prompts(db_session, world).run_due_mode_prompts(world.operator_id)

    assert sweep.raised == 1
    assert conditions_of((await prompt_alerts(db_session, world))[0]) == {"fleet_degraded"}


# --- lifecycle -----------------------------------------------------------------


async def test_the_prompt_resolves_itself_when_the_condition_clears(
    db_session: AsyncSession,
) -> None:
    world = await make_world(db_session)
    cabs = [await add_cab(db_session, world, HOME) for _ in range(5)]
    cabs[0].status = str(VehicleStatus.out_of_service)
    await db_session.flush()
    service = prompts(db_session, world)
    await service.run_due_mode_prompts(world.operator_id)
    assert len(await prompt_alerts(db_session, world)) == 1

    cabs[0].status = str(VehicleStatus.available)
    await db_session.flush()
    sweep = await service.run_due_mode_prompts(world.operator_id)

    assert sweep.resolved == 1
    assert await prompt_alerts(db_session, world) == []
    (resolved,) = await prompt_alerts(db_session, world, open_only=False)
    assert resolved.status == "resolved" and resolved.acknowledged_by is None


async def test_a_standing_condition_is_one_alert_however_often_it_is_checked(
    db_session: AsyncSession,
) -> None:
    world = await make_world(db_session)
    cabs = [await add_cab(db_session, world, HOME) for _ in range(5)]
    cabs[0].status = str(VehicleStatus.out_of_service)
    await db_session.flush()
    service = prompts(db_session, world)

    first = await service.run_due_mode_prompts(world.operator_id)
    second = await service.run_due_mode_prompts(world.operator_id)
    third = await service.run_due_mode_prompts(world.operator_id)

    assert (first.raised, second.raised, third.raised) == (1, 0, 0)
    assert len(await prompt_alerts(db_session, world)) == 1


async def test_nothing_in_the_sweep_changes_a_mode(db_session: AsyncSession) -> None:
    world = await make_world(db_session)
    cabs = [await add_cab(db_session, world, HOME) for _ in range(5)]
    cabs[0].status = str(VehicleStatus.out_of_service)
    await db_session.flush()
    before = {
        s.id: (s.mode, s.updated_at)
        for s in (await db_session.execute(select(ModeSetting))).scalars()
        if s.operator_id == world.operator_id
    }

    await prompts(db_session, world).run_due_mode_prompts(world.operator_id)
    world.clock.advance(timedelta(hours=1))
    await prompts(db_session, world).run_due_mode_prompts(world.operator_id)

    after = {
        s.id: (s.mode, s.updated_at)
        for s in (await db_session.execute(select(ModeSetting))).scalars()
        if s.operator_id == world.operator_id
    }
    assert after == before


async def test_a_scope_already_on_manual_is_never_prompted(db_session: AsyncSession) -> None:
    world = await make_world(db_session, Mode.manual)
    cabs = [await add_cab(db_session, world, HOME) for _ in range(5)]
    cabs[0].status = str(VehicleStatus.out_of_service)
    await db_session.flush()

    assert (await prompts(db_session, world).run_due_mode_prompts(world.operator_id)).raised == 0


async def test_each_scope_is_judged_on_its_own_requests(db_session: AsyncSession) -> None:
    """Rejections in one client's scope must not raise a prompt for another's."""
    world = await build_world(db_session, FakeClock(NOW), mode=None)
    noisy = await add_client(db_session, world, "Noisy", Mode.semi_auto)
    calm = await add_client(db_session, world, "Calm", Mode.semi_auto)
    cab = await add_cab(db_session, world, HOME)
    for verdict in [SuggestionStatus.rejected] * 6:
        rider = await add_employee(db_session, world, HOME, client=noisy[0], office=noisy[1])
        request = await add_request(db_session, world, rider)
        db_session.add(
            Suggestion(
                id=uuid.uuid4(),
                operator_id=world.operator_id,
                request_id=request.id,
                vehicle_id=cab.id,
                rank=1,
                cost=1.0,
                reasons=[],
                status=str(verdict),
                offered_at=NOW - timedelta(minutes=5),
                failsafe_due_at=NOW,
                decided_at=NOW - timedelta(minutes=1),
            )
        )
    calm_rider = await add_employee(db_session, world, HOME, client=calm[0], office=calm[1])
    await add_request(db_session, world, calm_rider)
    await db_session.flush()

    await prompts(db_session, world).run_due_mode_prompts(world.operator_id)

    (alert,) = await prompt_alerts(db_session, world)
    noisy_setting = await db_session.scalar(
        select(ModeSetting).where(ModeSetting.client_id == noisy[0].id)
    )
    assert alert.data is not None and alert.data["setting_id"] == str(noisy_setting.id)  # type: ignore[union-attr]
