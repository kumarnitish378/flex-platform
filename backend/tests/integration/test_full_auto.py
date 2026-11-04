"""`full_auto`: a scope the platform serves without a human (B34, `control-model.md` §1, §2).

The mode table has accepted `full_auto` since B24. B32 made the optimizer apply a plan in
such a scope; this is the behaviour around it that makes it safe to leave unattended:
the emergency pause beats it, a VIP is never put in an ordinary cab, and every assignment
says who made it.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.domain.enums import ActorType, AlertType, VehicleType
from app.domain.modes import Mode
from app.domain.state_machines import Actor, RequestStatus
from app.modules.alerts.models import Alert
from app.modules.dispatch.models import Trip
from app.modules.dispatch.optimizer_service import OptimizerService
from app.modules.dispatch.service import DispatchService
from app.modules.notifications.models import Notification
from app.modules.reports.service import ReportService
from app.modules.requests.models import RideRequestEvent
from tests.builders import make_user, unique_phone
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


async def make_world(session: AsyncSession) -> World:
    world = await build_world(session, FakeClock(NOW), Mode.full_auto)
    await set_config(session, world, batch_window_seconds=WINDOW)
    return world


def optimizer(session: AsyncSession, world: World) -> OptimizerService:
    return OptimizerService(
        session, world.clock, DispatchService(session, world.clock, eta_service(world.clock))
    )


async def test_a_scope_in_full_auto_serves_a_request_with_no_supervisor_action(
    db_session: AsyncSession,
) -> None:
    world = await make_world(db_session)
    cab = await add_cab(db_session, world, HOME)
    rider = await add_employee(db_session, world, HOME)
    user = make_user(name="Asha", phone=unique_phone())
    db_session.add(user)
    await db_session.flush()
    rider.user_id = user.id
    request = await add_request(db_session, world, rider)
    service = optimizer(db_session, world)

    assert (await service.run_due_batches(world.operator_id)).runs == 0  # window still open
    world.clock.advance(timedelta(seconds=WINDOW))
    await service.run_due_batches(world.operator_id)

    await db_session.refresh(request)
    assert request.status == str(RequestStatus.assigned)
    trip = await db_session.get(Trip, request.trip_id)
    assert trip is not None and trip.vehicle_id == cab.id
    # The rider was told, which is the part of "served" a person would otherwise do.
    told = await db_session.scalar(select(Notification).where(Notification.user_id == user.id))
    assert told is not None


async def test_the_emergency_pause_beats_full_auto_and_resuming_serves_the_queue(
    db_session: AsyncSession,
) -> None:
    world = await make_world(db_session)
    cab = await add_cab(db_session, world, HOME)
    request = await add_request(db_session, world, await add_employee(db_session, world, HOME))
    dispatch = DispatchService(db_session, world.clock, eta_service(world.clock))
    service = optimizer(db_session, world)
    await dispatch.set_automation_paused(world.operator_id, True, "safety")
    world.clock.advance(timedelta(minutes=5))
    await ping(db_session, world, cab, HOME)

    paused = await service.run_due_batches(world.operator_id)

    assert paused.runs == 0
    await db_session.refresh(request)
    assert request.status == str(RequestStatus.queued)

    await dispatch.set_automation_paused(world.operator_id, False, "safety")
    await ping(db_session, world, cab, HOME)
    await service.run_due_batches(world.operator_id)
    await db_session.refresh(request)
    assert request.status == str(RequestStatus.assigned)


# --- VIP (control-model.md section 2 level 2, allocation-rules.md section 2 rule 4) -------


async def test_a_vip_is_assigned_straight_away_without_waiting_for_the_window(
    db_session: AsyncSession,
) -> None:
    world = await make_world(db_session)
    await add_cab(db_session, world, HOME, vehicle_type=VehicleType.vip)
    vip = await add_employee(db_session, world, HOME, "Chairman", is_vip=True)
    request = await add_request(db_session, world, vip)

    sweep = await optimizer(db_session, world).run_due_batches(world.operator_id)

    assert sweep.runs == 1 and sweep.applied == 1, "no waiting for a window nobody can share"
    await db_session.refresh(request)
    assert request.status == str(RequestStatus.assigned)


async def test_a_vip_with_no_vip_vehicle_raises_an_alert_and_is_not_given_an_ordinary_cab(
    db_session: AsyncSession,
) -> None:
    world = await make_world(db_session)
    await add_cab(db_session, world, HOME)  # a sedan, right outside
    request = await add_request(
        db_session, world, await add_employee(db_session, world, HOME, is_vip=True)
    )

    await optimizer(db_session, world).run_due_batches(world.operator_id)

    await db_session.refresh(request)
    assert request.status == str(RequestStatus.queued) and request.trip_id is None
    alert = await db_session.scalar(
        select(Alert).where(
            Alert.request_id == request.id, Alert.type == str(AlertType.vip_no_vehicle)
        )
    )
    assert alert is not None
    assert "vip_needs_vip_vehicle" in alert.data["reasons"]  # type: ignore[index]


async def test_the_vip_alert_is_one_per_request_and_clears_when_a_vip_cab_appears(
    db_session: AsyncSession,
) -> None:
    world = await make_world(db_session)
    await add_cab(db_session, world, HOME)
    request = await add_request(
        db_session, world, await add_employee(db_session, world, HOME, is_vip=True)
    )
    service = optimizer(db_session, world)
    await service.run_due_batches(world.operator_id)
    world.clock.advance(timedelta(seconds=1))
    await service.run_due_batches(world.operator_id)  # a VIP is retried at once, every sweep

    alerts = list(
        (
            await db_session.scalars(
                select(Alert).where(Alert.request_id == request.id).order_by(Alert.created_at)
            )
        ).all()
    )
    assert len(alerts) == 1

    await add_cab(db_session, world, HOME, vehicle_type=VehicleType.vip)
    world.clock.advance(timedelta(seconds=1))
    await service.run_due_batches(world.operator_id)

    await db_session.refresh(request)
    assert request.status == str(RequestStatus.assigned)
    await db_session.refresh(alerts[0])
    assert alerts[0].status == "resolved"


# --- attribution (control-model.md section 3 rule 6; the report) -------------------------


async def test_every_automatic_assignment_is_attributable_in_the_event_log_and_the_report(
    db_session: AsyncSession,
) -> None:
    world = await make_world(db_session)
    await add_cab(db_session, world, HOME)
    cab_b = await add_cab(db_session, world, near(*HOME, north_km=0.5))
    by_machine = await add_request(db_session, world, await add_employee(db_session, world, HOME))
    by_hand = await add_request(
        db_session, world, await add_employee(db_session, world, near(*HOME, north_km=-0.2))
    )
    dispatch = DispatchService(db_session, world.clock, eta_service(world.clock))
    await dispatch.assign(world.operator_id, by_hand.id, cab_b.id, Actor.supervisor, None)
    world.clock.advance(timedelta(seconds=WINDOW))
    await optimizer(db_session, world).run_due_batches(world.operator_id)

    events = {
        event.request_id: event.actor_type
        for event in (
            await db_session.scalars(
                select(RideRequestEvent).where(
                    RideRequestEvent.to_status == str(RequestStatus.assigned)
                )
            )
        ).all()
        if event.request_id in (by_machine.id, by_hand.id)
    }
    assert events[by_machine.id] == str(ActorType.optimizer)
    assert events[by_hand.id] == str(ActorType.supervisor)

    report = await ReportService(db_session, world.clock).trip_report(
        world.operator_id, date(2026, 10, 16), date(2026, 10, 16)
    )
    assert report.assignments_by_actor == {"optimizer": 1, "supervisor": 1}
    by_request = {row.request_id: row.assigned_by for row in report.rows}
    assert by_request[by_machine.id] == "optimizer" and by_request[by_hand.id] == "supervisor"
    assert "assigned_by" in report.as_csv().splitlines()[0]
