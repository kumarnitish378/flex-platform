"""Regression: an unanswered optimizer offer must reach its failsafe (S10, approve_all).

Rank 1 of an optimizer offer is the **planned** placement. It can be a cab that, for this rider
alone, is not among the three best candidates. The failsafe used to ask "is this cab still in the
single-rider top three?", answered no, withdrew the offer as superseded, and the next batch offered
the same cab again - so in `semi_auto` a rider nobody answered in time was never assigned, and a
supervisor who answered late was told 409 "already superseded" on most offers.
"""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.modes import Mode
from app.domain.optimizer import Placement
from app.domain.state_machines import RequestStatus
from app.modules.dispatch.models import Trip
from app.modules.dispatch.semi_auto import SemiAutoService
from app.modules.dispatch.service import DispatchService
from app.modules.dispatch.suggestion_models import Suggestion
from tests.integration.test_optimizer_down import HOME
from tests.integration.worlds import (
    add_cab,
    add_employee,
    add_request,
    build_world,
    eta_service,
    near,
    ping,
)


async def test_a_planned_offer_outside_the_top_three_is_still_assigned_at_its_timer(
    db_session: AsyncSession,
) -> None:
    from app.core.clock import FakeClock
    from tests.integration.worlds import NOW

    clock = FakeClock(NOW)
    world = await build_world(db_session, clock, Mode.semi_auto)
    cabs = [
        await add_cab(db_session, world, near(*HOME, north_km=km)) for km in (0.2, 0.4, 0.6, 1.5)
    ]
    planned = cabs[3]  # the farthest: fourth best for this rider on their own
    request = await add_request(db_session, world, await add_employee(db_session, world, HOME))
    dispatch = DispatchService(db_session, clock, eta_service(clock))
    top_three = await dispatch.suggestions(world.operator_id, request.id, limit=3)
    assert planned.id not in {c.vehicle.id for c in top_three}, "fixture must put the cab 4th"

    semi = SemiAutoService(db_session, clock, dispatch)
    placement = Placement(
        vehicle_id=planned.id,
        trip_id=None,
        order=(request.id,),
        new_request_ids=(request.id,),
        pickup_eta_seconds={request.id: 300.0},
        added_minutes={request.id: 0.0},
        cost=1.0,
    )
    offers = await semi.offer_planned(request, placement, [])
    assert offers[0].plan is not None and offers[1].plan is None, "only rank 1 carries the plan"
    clock.advance(timedelta(seconds=200))  # past the 180 s failsafe
    for cab, km in zip(cabs, (0.2, 0.4, 0.6, 1.5), strict=True):
        await ping(db_session, world, cab, near(*HOME, north_km=km))  # fresh, same places

    sweep = await semi.run_due_semi_auto(world.operator_id)

    assert (sweep.assigned, sweep.superseded) == (1, 0)
    await db_session.refresh(request)
    assert request.status == str(RequestStatus.assigned)
    trip = await db_session.get(Trip, request.trip_id)
    assert trip is not None and trip.vehicle_id == planned.id
    assert trip.mode_used == "semi_auto", "the plan was applied as a plan, by the failsafe"
    offer = await db_session.get(Suggestion, (await _rank_one(db_session, request.id)))
    assert offer is not None and offer.status == "failsafe_assigned"


async def _rank_one(session: AsyncSession, request_id: object) -> object:
    from sqlalchemy import select

    return await session.scalar(
        select(Suggestion.id).where(Suggestion.request_id == request_id).where(Suggestion.rank == 1)
    )
