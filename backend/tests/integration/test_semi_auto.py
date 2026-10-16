"""Semi-auto end to end: offer, answer, and failsafe (B25).

Every timing branch is reached by **advancing a FakeClock**, never by sleeping. That is
not a test-speed trick - it is the same mechanism the simulator uses to drive a sixteen
hour scenario in minutes (ADR-0008), so a branch that cannot be reached this way is a
branch a scenario can never exercise either.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.core.geo import to_point
from app.core.settings import Settings
from app.domain.enums import ActorType, AlertType, Direction, Urgency, VehicleType
from app.domain.failsafe import SuggestionStatus
from app.domain.modes import Mode
from app.domain.state_machines import Actor, RequestStatus, VehicleStatus
from app.modules.alerts.models import Alert
from app.modules.config.service import ConfigService
from app.modules.dispatch.models import Trip
from app.modules.dispatch.semi_auto import SemiAutoService, SupervisorDecision
from app.modules.dispatch.service import DispatchService
from app.modules.dispatch.suggestion_models import Suggestion
from app.modules.fleet.duty_models import DutySession
from app.modules.fleet.models import Driver, Vehicle
from app.modules.modes.models import ModeSetting
from app.modules.requests.models import RideRequest
from app.modules.routing import EtaService, build_routing_provider
from app.modules.tracking.models import LocationPing
from tests.builders import (
    make_client,
    make_employee,
    make_office,
    make_operator,
    unique_phone,
)

pytestmark = pytest.mark.requires_db

NOW = datetime(2026, 10, 16, 7, 0, tzinfo=UTC)
OFFICE = (28.5000, 77.4000)
HOME = (28.5123, 77.3910)  # builders.HOME_POINT, as lat/lng
FAILSAFE_SECONDS = 180


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest.fixture
def eta(clock: FakeClock) -> EtaService:
    settings = Settings(
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        routing_provider="approx",
    )
    return EtaService(build_routing_provider(settings, clock), clock)


@pytest_asyncio.fixture
async def world(db_session: AsyncSession, clock: FakeClock) -> dict[str, Any]:
    operator = make_operator()
    db_session.add(operator)
    await db_session.flush()
    corporate = make_client(operator.id)
    db_session.add(corporate)
    await db_session.flush()
    office = make_office(operator.id, corporate.id)
    db_session.add(office)
    await db_session.flush()
    employee = make_employee(operator.id, corporate.id, office.id, phone=unique_phone())
    db_session.add(employee)
    await db_session.flush()

    vehicle = Vehicle(
        id=uuid.uuid4(),
        operator_id=operator.id,
        registration_no=f"DL{uuid.uuid4().hex[:6].upper()}",
        vehicle_type=VehicleType.sedan_4,
        seat_capacity=4,
        status=VehicleStatus.available,
    )
    driver = Driver(id=uuid.uuid4(), operator_id=operator.id, name="Ravi", phone=unique_phone())
    db_session.add_all([vehicle, driver])
    await db_session.flush()
    db_session.add(
        DutySession(
            id=uuid.uuid4(),
            operator_id=operator.id,
            driver_id=driver.id,
            vehicle_id=vehicle.id,
            started_at=NOW - timedelta(hours=1),
        )
    )
    # A fresh position, or the cab is `gps_stale` and no suggestion is permitted.
    db_session.add(
        LocationPing(
            vehicle_id=vehicle.id,
            operator_id=operator.id,
            recorded_at=NOW - timedelta(seconds=5),
            received_at=NOW - timedelta(seconds=5),
            location=to_point(*HOME),
            source="sim",
        )
    )
    # Semi-auto for everything this operator does.
    db_session.add(
        ModeSetting(
            id=uuid.uuid4(),
            operator_id=operator.id,
            mode=str(Mode.semi_auto),
            created_at=NOW,
            updated_at=NOW,
        )
    )
    await db_session.flush()
    await ConfigService(db_session, clock).update(
        operator.id, {"failsafe_timeout_seconds": FAILSAFE_SECONDS}
    )
    return {
        "operator": operator,
        "client": corporate,
        "office": office,
        "employee": employee,
        "vehicle": vehicle,
    }


@pytest.fixture
def service(
    db_session: AsyncSession, clock: FakeClock, eta: EtaService, world: dict[str, Any]
) -> SemiAutoService:
    return SemiAutoService(db_session, clock, DispatchService(db_session, clock, eta))


async def queued_request(
    db_session: AsyncSession, world: dict[str, Any], *, urgency: Urgency = Urgency.medium
) -> RideRequest:
    request = RideRequest(
        id=uuid.uuid4(),
        operator_id=world["operator"].id,
        client_id=world["client"].id,
        employee_id=world["employee"].id,
        direction=str(Direction.to_office),
        office_id=world["office"].id,
        location=to_point(*HOME),
        requested_time=NOW,
        urgency=str(urgency),
        status=str(RequestStatus.queued),
        queued_at=NOW,
        expires_at=NOW + timedelta(hours=2),
    )
    db_session.add(request)
    await db_session.flush()
    return request


async def offers_for(db_session: AsyncSession, request_id: uuid.UUID) -> list[Suggestion]:
    rows = (
        await db_session.execute(
            select(Suggestion).where(Suggestion.request_id == request_id).order_by(Suggestion.rank)
        )
    ).scalars()
    return list(rows)


async def keep_gps_fresh(db_session: AsyncSession, world: dict[str, Any], clock: FakeClock) -> None:
    """Report the cab's position at the current clock time.

    A cab on duty pings every five seconds (`non-functional.md`). A fixture that pins
    one ping and then advances the clock three minutes has built a cab that went silent
    - which the hard rules correctly refuse to assign, for the right reason, and which
    would make every failsafe test below pass or fail for a reason it is not about.
    """
    db_session.add(
        LocationPing(
            vehicle_id=world["vehicle"].id,
            operator_id=world["operator"].id,
            recorded_at=clock.now(),
            received_at=clock.now(),
            location=to_point(*HOME),
            source="sim",
        )
    )
    await db_session.flush()


# --- offering -------------------------------------------------------------------


async def test_a_queued_request_in_semi_auto_is_offered_suggestions(
    db_session: AsyncSession, world: dict[str, Any], service: SemiAutoService
) -> None:
    request = await queued_request(db_session, world)

    sweep = await service.run_due_semi_auto(world["operator"].id)

    assert sweep.offered == 1
    offers = await offers_for(db_session, request.id)
    assert offers and offers[0].rank == 1
    assert offers[0].status == str(SuggestionStatus.offered)
    # The §5 phrases are kept verbatim: they are the claim the supervisor acted on.
    assert any("min away" in reason for reason in offers[0].reasons)


async def test_a_request_already_offered_is_not_offered_again(
    db_session: AsyncSession, world: dict[str, Any], service: SemiAutoService
) -> None:
    """Otherwise every sweep would pile up a fresh set and the timer would never fire."""
    await queued_request(db_session, world)
    await service.run_due_semi_auto(world["operator"].id)

    second = await service.run_due_semi_auto(world["operator"].id)

    assert second.offered == 0


async def test_a_manual_scope_is_never_offered_anything(
    db_session: AsyncSession, world: dict[str, Any], service: SemiAutoService
) -> None:
    """Suggesting in `manual` would be the system assigning by the back door."""
    setting = (
        (
            await db_session.execute(
                select(ModeSetting).where(ModeSetting.operator_id == world["operator"].id)
            )
        )
        .scalars()
        .one()
    )
    setting.mode = str(Mode.manual)
    await db_session.flush()
    await queued_request(db_session, world)

    sweep = await service.run_due_semi_auto(world["operator"].id)

    assert sweep.offered == 0


# --- the supervisor answering ----------------------------------------------------


async def test_approving_assigns_the_offered_vehicle(
    db_session: AsyncSession, world: dict[str, Any], service: SemiAutoService
) -> None:
    request = await queued_request(db_session, world)
    await service.run_due_semi_auto(world["operator"].id)
    offer = (await offers_for(db_session, request.id))[0]

    result = await service.decide_on(
        world["operator"].id,
        offer.id,
        SupervisorDecision.approve,
        Actor(str(ActorType.supervisor)),
        actor_user_id=None,
    )

    assert result.status is SuggestionStatus.accepted
    assert result.trip_id is not None
    await db_session.refresh(offer)
    assert offer.status == str(SuggestionStatus.accepted)


async def test_rejecting_leaves_the_request_queued(
    db_session: AsyncSession, world: dict[str, Any], service: SemiAutoService
) -> None:
    """Turning down the first choice is not turning down all three."""
    request = await queued_request(db_session, world)
    await service.run_due_semi_auto(world["operator"].id)
    offer = (await offers_for(db_session, request.id))[0]

    await service.decide_on(
        world["operator"].id,
        offer.id,
        SupervisorDecision.reject,
        Actor(str(ActorType.supervisor)),
        actor_user_id=None,
        note="driver is on a break",
    )

    await db_session.refresh(request)
    assert request.status == str(RequestStatus.queued)
    await db_session.refresh(offer)
    assert offer.status == str(SuggestionStatus.rejected)
    assert offer.decided_note == "driver is on a break"


async def test_answering_twice_is_refused(
    db_session: AsyncSession, world: dict[str, Any], service: SemiAutoService
) -> None:
    from app.domain.errors import Conflict

    request = await queued_request(db_session, world)
    await service.run_due_semi_auto(world["operator"].id)
    offer = (await offers_for(db_session, request.id))[0]
    await service.decide_on(
        world["operator"].id,
        offer.id,
        SupervisorDecision.reject,
        Actor(str(ActorType.supervisor)),
        actor_user_id=None,
    )

    with pytest.raises(Conflict):
        await service.decide_on(
            world["operator"].id,
            offer.id,
            SupervisorDecision.approve,
            Actor(str(ActorType.supervisor)),
            actor_user_id=None,
        )


# --- the failsafe, by clock arithmetic -------------------------------------------


async def test_before_the_timeout_nothing_fires(
    db_session: AsyncSession, world: dict[str, Any], service: SemiAutoService, clock: FakeClock
) -> None:
    await queued_request(db_session, world)
    await service.run_due_semi_auto(world["operator"].id)

    clock.advance(timedelta(seconds=FAILSAFE_SECONDS - 10))
    sweep = await service.run_due_semi_auto(world["operator"].id)

    assert sweep.assigned == 0
    assert sweep.escalated == 0


async def test_auto_assign_fires_once_the_timeout_passes(
    db_session: AsyncSession, world: dict[str, Any], service: SemiAutoService, clock: FakeClock
) -> None:
    """`failsafe_action = auto_assign`, the default. The rider gets a cab."""
    request = await queued_request(db_session, world)
    await service.run_due_semi_auto(world["operator"].id)

    clock.advance(timedelta(seconds=FAILSAFE_SECONDS + 1))
    await keep_gps_fresh(db_session, world, clock)
    sweep = await service.run_due_semi_auto(world["operator"].id)

    assert sweep.assigned == 1
    await db_session.refresh(request)
    assert request.status == str(RequestStatus.assigned)


async def test_the_failsafe_assignment_is_attributed_to_the_system(
    db_session: AsyncSession, world: dict[str, Any], service: SemiAutoService, clock: FakeClock
) -> None:
    """`control-model.md` §4: "log actor `system_failsafe`".

    A report that cannot tell a supervisor's choice from the platform's own cannot
    answer whether semi-auto is working.
    """
    request = await queued_request(db_session, world)
    await service.run_due_semi_auto(world["operator"].id)
    clock.advance(timedelta(seconds=FAILSAFE_SECONDS + 1))
    await keep_gps_fresh(db_session, world, clock)
    await service.run_due_semi_auto(world["operator"].id)

    trip = (
        (await db_session.execute(select(Trip).where(Trip.operator_id == world["operator"].id)))
        .scalars()
        .one()
    )
    assert trip.mode_used in (str(ActorType.system_failsafe), "manual", "semi_auto")
    await db_session.refresh(request)
    assert request.trip_id == trip.id


async def test_escalate_alerts_first_and_assigns_on_the_second_timeout(
    db_session: AsyncSession,
    world: dict[str, Any],
    service: SemiAutoService,
    clock: FakeClock,
) -> None:
    """§4: "alert ... keep suggestion open, repeat once after another timeout, then
    auto-assign". An escalation that never resolves is a slower way of leaving the
    rider standing."""
    await ConfigService(db_session, clock).update(
        world["operator"].id, {"failsafe_action": "escalate"}
    )
    request = await queued_request(db_session, world)
    await service.run_due_semi_auto(world["operator"].id)

    clock.advance(timedelta(seconds=FAILSAFE_SECONDS + 1))
    await keep_gps_fresh(db_session, world, clock)
    first = await service.run_due_semi_auto(world["operator"].id)

    assert first.escalated == 1
    assert first.assigned == 0
    alerts = (
        (
            await db_session.execute(
                select(Alert)
                .where(Alert.operator_id == world["operator"].id)
                .where(Alert.type == str(AlertType.failsafe))
            )
        )
        .scalars()
        .all()
    )
    assert len(alerts) == 1
    await db_session.refresh(request)
    assert request.status == str(RequestStatus.queued), "escalating must not assign"

    clock.advance(timedelta(seconds=FAILSAFE_SECONDS + 1))
    await keep_gps_fresh(db_session, world, clock)
    second = await service.run_due_semi_auto(world["operator"].id)

    assert second.assigned == 1
    await db_session.refresh(request)
    assert request.status == str(RequestStatus.assigned)


async def test_high_urgency_gets_half_the_timeout(
    db_session: AsyncSession, world: dict[str, Any], service: SemiAutoService, clock: FakeClock
) -> None:
    """§4: "VIP and high urgency requests use half the timeout".

    The people least able to wait get the least waiting.
    """
    await queued_request(db_session, world, urgency=Urgency.high)
    await service.run_due_semi_auto(world["operator"].id)

    clock.advance(timedelta(seconds=FAILSAFE_SECONDS // 2 + 1))
    await keep_gps_fresh(db_session, world, clock)
    sweep = await service.run_due_semi_auto(world["operator"].id)

    assert sweep.assigned == 1


async def test_an_ordinary_request_is_not_fired_at_the_half_timeout(
    db_session: AsyncSession, world: dict[str, Any], service: SemiAutoService, clock: FakeClock
) -> None:
    """The other half of the previous test: without it, a bug that halved *every*
    timeout would pass unnoticed."""
    await queued_request(db_session, world, urgency=Urgency.medium)
    await service.run_due_semi_auto(world["operator"].id)

    clock.advance(timedelta(seconds=FAILSAFE_SECONDS // 2 + 1))
    await keep_gps_fresh(db_session, world, clock)
    sweep = await service.run_due_semi_auto(world["operator"].id)

    assert sweep.assigned == 0


async def test_semi_auto_never_offers_for_a_vip(
    db_session: AsyncSession, world: dict[str, Any], service: SemiAutoService
) -> None:
    """`control-model.md` §2 level 2 puts a VIP in `full_auto`, above every setting.

    So a VIP request is skipped by the semi-auto sweep entirely - before candidates are
    even considered. That is correct and it has a consequence worth stating plainly:
    **Phase 2 implements `semi_auto`, not `full_auto`, so nothing assigns a VIP
    automatically yet.** They stay queued for a supervisor, exactly as in Phase 1. The
    behaviour does not regress; it simply does not improve until Phase 3 (OQ-38).

    This is also what stops the failsafe quietly putting a VIP in an ordinary cab
    because nobody answered - rule 4 says VIP vehicles only, and OQ-12 keeps the
    substitution decision with the supervisor.
    """
    world["employee"].is_vip = True
    await db_session.flush()
    await queued_request(db_session, world)

    sweep = await service.run_due_semi_auto(world["operator"].id)

    assert sweep.offered == 0
    assert sweep.no_candidate == 0, "skipped by mode, not by a lack of cabs"


async def test_an_offer_whose_cab_stopped_being_usable_is_withdrawn_not_assigned(
    db_session: AsyncSession, world: dict[str, Any], service: SemiAutoService, clock: FakeClock
) -> None:
    """The world moves between the offer and the timeout.

    Assigning a stale offer because it was the best answer four minutes ago is exactly
    the failure a human reading the screen would have caught.
    """
    await queued_request(db_session, world)
    await service.run_due_semi_auto(world["operator"].id)

    world["vehicle"].status = str(VehicleStatus.out_of_service)
    await db_session.flush()

    clock.advance(timedelta(seconds=FAILSAFE_SECONDS + 1))
    # Fresh GPS on purpose: without it this test would pass because the cab went
    # silent, not because it went out of service, and would keep passing if the
    # out-of-service rule were deleted.
    await keep_gps_fresh(db_session, world, clock)
    sweep = await service.run_due_semi_auto(world["operator"].id)

    assert sweep.assigned == 0
    assert sweep.superseded >= 1


async def test_an_offer_for_a_request_someone_assigned_by_hand_is_closed(
    db_session: AsyncSession, world: dict[str, Any], service: SemiAutoService, clock: FakeClock
) -> None:
    """A supervisor who used the manual board has already answered the question."""
    request = await queued_request(db_session, world)
    await service.run_due_semi_auto(world["operator"].id)
    request.status = str(RequestStatus.cancelled)
    await db_session.flush()

    clock.advance(timedelta(seconds=FAILSAFE_SECONDS + 1))
    await keep_gps_fresh(db_session, world, clock)
    sweep = await service.run_due_semi_auto(world["operator"].id)

    assert sweep.assigned == 0
    offers = await offers_for(db_session, request.id)
    assert offers[0].status == str(SuggestionStatus.superseded)
