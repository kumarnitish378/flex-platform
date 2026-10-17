"""The full override set, end to end (`control-model.md` §3, B26).

Two things these tests are really about, beyond "the nine actions work":

* **Expiry happens with nothing running.** Every expiry test advances a FakeClock and
  then *reads*. No sweep is called, no task is run - if an expired lock still pinned a
  rider, the assertion would fail, which is the only honest way to prove rule 5.
* **No automatic path may touch an overridden item** (rule 1, and CLAUDE.md hard rule
  6). That is asserted against the real semi-auto sweep rather than by inspecting the
  columns, because the column being right is not the claim - the optimizer leaving it
  alone is.
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
from app.domain.dispatch import Violation
from app.domain.enums import Direction, Urgency, VehicleType
from app.domain.errors import Conflict, InvalidTransition, ValidationFailed
from app.domain.modes import Mode
from app.domain.overrides import OverrideAction, OverrideCommand, ReasonCode
from app.domain.state_machines import Actor, RequestStatus, TripStatus, VehicleStatus
from app.modules.config.service import ConfigService
from app.modules.dispatch.models import Trip
from app.modules.dispatch.override_models import OverrideLog
from app.modules.dispatch.override_service import OverrideService
from app.modules.dispatch.semi_auto import SemiAutoService
from app.modules.dispatch.service import DispatchService
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
    make_zone,
    unique_phone,
)

pytestmark = pytest.mark.requires_db

NOW = datetime(2026, 10, 16, 7, 0, tzinfo=UTC)
HOME = (28.5123, 77.3910)
#: Inside `make_zone`'s square (lng 77.32-77.33, lat 28.57-28.58).
IN_ZONE = (28.5750, 77.3250)
SUPERVISOR = uuid.uuid4()


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


async def _add_vehicle(
    session: AsyncSession,
    operator_id: uuid.UUID,
    at: tuple[float, float],
    *,
    seats: int = 4,
) -> Vehicle:
    vehicle = Vehicle(
        id=uuid.uuid4(),
        operator_id=operator_id,
        registration_no=f"DL{uuid.uuid4().hex[:6].upper()}",
        vehicle_type=VehicleType.sedan_4,
        seat_capacity=seats,
        status=VehicleStatus.available,
    )
    driver = Driver(id=uuid.uuid4(), operator_id=operator_id, name="Ravi", phone=unique_phone())
    session.add_all([vehicle, driver])
    await session.flush()
    session.add_all(
        [
            DutySession(
                id=uuid.uuid4(),
                operator_id=operator_id,
                driver_id=driver.id,
                vehicle_id=vehicle.id,
                started_at=NOW - timedelta(hours=1),
            ),
            LocationPing(
                vehicle_id=vehicle.id,
                operator_id=operator_id,
                recorded_at=NOW - timedelta(seconds=5),
                received_at=NOW - timedelta(seconds=5),
                location=to_point(*at),
                source="sim",
            ),
        ]
    )
    await session.flush()
    return vehicle


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
    asha = make_employee(operator.id, corporate.id, office.id, name="Asha", phone=unique_phone())
    rahul = make_employee(operator.id, corporate.id, office.id, name="Rahul", phone=unique_phone())
    db_session.add_all([asha, rahul])
    await db_session.flush()

    first = await _add_vehicle(db_session, operator.id, HOME)
    second = await _add_vehicle(db_session, operator.id, HOME)
    await ConfigService(db_session, clock).update(operator.id, {"failsafe_timeout_seconds": 180})
    return {
        "operator": operator,
        "client": corporate,
        "office": office,
        "employee": asha,
        "other_employee": rahul,
        "vehicle": first,
        "other_vehicle": second,
    }


@pytest.fixture
def dispatch(db_session: AsyncSession, clock: FakeClock, eta: EtaService) -> DispatchService:
    return DispatchService(db_session, clock, eta)


@pytest.fixture
def overrides(
    db_session: AsyncSession, clock: FakeClock, dispatch: DispatchService, world: dict[str, Any]
) -> OverrideService:
    return OverrideService(db_session, clock, dispatch)


async def queued_request(
    db_session: AsyncSession,
    world: dict[str, Any],
    *,
    employee_key: str = "employee",
    urgency: Urgency = Urgency.medium,
) -> RideRequest:
    request = RideRequest(
        id=uuid.uuid4(),
        operator_id=world["operator"].id,
        client_id=world["client"].id,
        employee_id=world[employee_key].id,
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


def apply(
    overrides: OverrideService, world: dict[str, Any], action: OverrideAction, **kwargs: object
) -> Any:
    command = OverrideCommand(
        action=action,
        reason_code=kwargs.pop("reason_code", ReasonCode.traffic),  # type: ignore[arg-type]
        **kwargs,  # type: ignore[arg-type]
    )
    return overrides.apply(
        world["operator"].id, command, actor=Actor.supervisor, actor_user_id=None
    )


async def keep_gps_fresh(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    where: tuple[float, float] = HOME,
) -> None:
    """Report both cabs at the current clock time.

    A cab on duty pings every five seconds. A test that advances the clock eleven
    hours and then reads has built two cabs that went silent, and `candidates()`
    correctly returns nothing for them - so an assertion that "the lock no longer
    applies" would pass against an empty list, proving nothing.
    """
    for key in ("vehicle", "other_vehicle"):
        db_session.add(
            LocationPing(
                vehicle_id=world[key].id,
                operator_id=world["operator"].id,
                recorded_at=clock.now(),
                received_at=clock.now(),
                location=to_point(*where),
                source="sim",
            )
        )
    await db_session.flush()


async def log_rows(db_session: AsyncSession) -> list[OverrideLog]:
    rows = (await db_session.execute(select(OverrideLog).order_by(OverrideLog.at))).scalars()
    return list(rows)


# --- reassign ------------------------------------------------------------------------


async def test_reassign_moves_the_rider_and_frees_the_cab_behind_them(
    db_session: AsyncSession,
    world: dict[str, Any],
    dispatch: DispatchService,
    overrides: OverrideService,
) -> None:
    request = await queued_request(db_session, world)
    first = await dispatch.assign(
        world["operator"].id, request.id, world["vehicle"].id, Actor.supervisor, None
    )

    result = await apply(
        overrides,
        world,
        OverrideAction.reassign,
        request_id=request.id,
        target_vehicle_id=world["other_vehicle"].id,
    )

    await db_session.refresh(request)
    moved = await db_session.get(Trip, result.trip_id)
    assert moved is not None and moved.vehicle_id == world["other_vehicle"].id
    assert request.trip_id == moved.id
    assert request.status == str(RequestStatus.assigned)

    # The trip they left has nobody on it, so it is cancelled and its cab is free
    # again. Without this the vehicle stays `on_trip` forever with no stop anybody will
    # ever mark done, and never appears as a candidate again.
    emptied = await db_session.get(Trip, first.id)
    assert emptied is not None and emptied.status == str(TripStatus.cancelled)
    freed = await db_session.get(Vehicle, world["vehicle"].id)
    assert freed is not None and freed.status == str(VehicleStatus.available)


async def test_every_override_writes_who_what_before_and_after(
    db_session: AsyncSession,
    world: dict[str, Any],
    dispatch: DispatchService,
    overrides: OverrideService,
) -> None:
    """§3 rule 6, and rule 7 - this row is Phase 3's training data."""
    request = await queued_request(db_session, world)
    first = await dispatch.assign(
        world["operator"].id, request.id, world["vehicle"].id, Actor.supervisor, None
    )

    await apply(
        overrides,
        world,
        OverrideAction.reassign,
        request_id=request.id,
        target_vehicle_id=world["other_vehicle"].id,
        reason_code=ReasonCode.driver_issue,
        note="driver reported sick",
    )

    (row,) = await log_rows(db_session)
    assert row.action == str(OverrideAction.reassign)
    assert row.reason_code == str(ReasonCode.driver_issue)
    assert row.note == "driver reported sick"
    assert row.before["vehicle_id"] == str(world["vehicle"].id)
    assert row.after["vehicle_id"] == str(world["other_vehicle"].id)
    assert row.before["trip_id"] == str(first.id)
    assert row.at == NOW


async def test_a_locked_request_moves_only_through_the_override(
    db_session: AsyncSession,
    world: dict[str, Any],
    dispatch: DispatchService,
    overrides: OverrideService,
) -> None:
    """The state machine has refused this since Phase 1; B26 is the first caller that
    can say yes, and it can only say yes with a reason attached."""
    request = await queued_request(db_session, world)
    await dispatch.assign(
        world["operator"].id, request.id, world["vehicle"].id, Actor.supervisor, None
    )
    await apply(overrides, world, OverrideAction.lock, request_id=request.id)

    result = await apply(
        overrides,
        world,
        OverrideAction.reassign,
        request_id=request.id,
        target_vehicle_id=world["other_vehicle"].id,
        reason_code=ReasonCode.safety,
        note="the locked cab broke down",
    )
    moved = await db_session.get(Trip, result.trip_id)
    assert moved is not None and moved.vehicle_id == world["other_vehicle"].id


# --- rule 4: hard-rule overrides ------------------------------------------------------


async def test_a_hard_rule_override_is_refused_without_the_narrowed_reason_and_a_note(
    db_session: AsyncSession,
    world: dict[str, Any],
    dispatch: DispatchService,
    overrides: OverrideService,
) -> None:
    """Rule 4. The rule broken here is `direction_mismatch`: a cab already running the
    other way is a real cab a supervisor may still choose, with a reason."""
    outbound = await queued_request(db_session, world)
    await dispatch.assign(
        world["operator"].id, outbound.id, world["other_vehicle"].id, Actor.supervisor, None
    )
    returning = await queued_request(db_session, world, employee_key="other_employee")
    returning.direction = str(Direction.from_office)
    await db_session.flush()

    with pytest.raises(ValidationFailed) as excinfo:
        await apply(
            overrides,
            world,
            OverrideAction.reassign,
            request_id=returning.id,
            target_vehicle_id=world["other_vehicle"].id,
            reason_code=ReasonCode.traffic,
            note="worth a try",
        )
    assert "safety" in str(excinfo.value)

    with pytest.raises(ValidationFailed):
        await apply(
            overrides,
            world,
            OverrideAction.reassign,
            request_id=returning.id,
            target_vehicle_id=world["other_vehicle"].id,
            reason_code=ReasonCode.safety,
        )

    result = await apply(
        overrides,
        world,
        OverrideAction.reassign,
        request_id=returning.id,
        target_vehicle_id=world["other_vehicle"].id,
        reason_code=ReasonCode.safety,
        note="last cab before the storm closes the road",
    )
    # Flagged, so the report can find it (rule 4).
    assert any(
        breach.rule is Violation.direction_mismatch for breach in result.impact.hard_rule_violations
    )
    (row,) = await log_rows(db_session)
    assert any(str(Violation.direction_mismatch) in flag for flag in row.waived_violations)


async def test_no_reason_waives_a_rule_nobody_may_waive(
    db_session: AsyncSession,
    world: dict[str, Any],
    overrides: OverrideService,
) -> None:
    """B21's `NEVER_WAIVABLE`: a cab that is out of service has no driver to send, and
    bravery is not the missing ingredient."""
    request = await queued_request(db_session, world)
    idle = await db_session.get(Vehicle, world["other_vehicle"].id)
    assert idle is not None
    idle.status = str(VehicleStatus.out_of_service)
    await db_session.flush()

    with pytest.raises(Conflict) as excinfo:
        await apply(
            overrides,
            world,
            OverrideAction.reassign,
            request_id=request.id,
            target_vehicle_id=idle.id,
            reason_code=ReasonCode.safety,
            note="I really want this one",
        )
    assert str(Violation.vehicle_unavailable) in str(excinfo.value.details)


# --- rule 5: expiry, with nothing running ------------------------------------------


async def test_a_lock_stops_pinning_the_rider_when_it_expires(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    dispatch: DispatchService,
    overrides: OverrideService,
) -> None:
    request = await queued_request(db_session, world)
    await apply(
        overrides,
        world,
        OverrideAction.lock,
        request_id=request.id,
        vehicle_id=world["vehicle"].id,
    )

    def locked_out(candidates: list[Any]) -> list[Any]:
        return [
            candidate
            for candidate in candidates
            if Violation.locked_to_other_vehicle in candidate.violations
        ]

    assert locked_out(await dispatch.candidates(world["operator"].id, request.id))

    # 23:59 IST is 18:29 UTC; one minute past it the lock is history. Nothing is swept,
    # nothing is run - the next read simply stops honouring it.
    clock.advance(timedelta(hours=11, minutes=30))
    await keep_gps_fresh(db_session, world, clock)
    after = await dispatch.candidates(world["operator"].id, request.id)
    assert after, "both cabs went silent - this would pass against an empty list"
    assert not locked_out(after)
    assert request.lock_vehicle_id is not None  # the column is untouched; the read is gated


async def test_an_expired_force_priority_stops_weighing(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    dispatch: DispatchService,
    overrides: OverrideService,
) -> None:
    """ADR-0021: the rider's own `urgency` is never rewritten, so when the override
    lapses the request goes back to the answer the rider actually gave.

    Measured against a **control** request made at the same moment and never forced,
    not against the same request before and after. Cost also rises with the wait, so
    comparing one request across eleven hours would compare two things at once.
    """
    # Both cabs ten kilometres off, so there is a wait for the rider's weight to
    # multiply. With the cab already standing at the pickup the wait is zero, the
    # weighted term vanishes, and every rider scores the same - which is correct, and
    # would make this test pass whatever `forced_priority` did.
    await keep_gps_fresh(db_session, world, clock, where=IN_ZONE)
    request = await queued_request(db_session, world, urgency=Urgency.low)
    control = await queued_request(
        db_session, world, employee_key="other_employee", urgency=Urgency.low
    )
    await apply(overrides, world, OverrideAction.force_priority, request_id=request.id)

    async def cost_of(subject: RideRequest) -> float:
        best = (await dispatch.candidates(world["operator"].id, subject.id))[0].cost
        assert best is not None
        return best

    # Priority 1 and high urgency weigh the rider heaviest, so every candidate for them
    # scores higher than the same candidate for an identical unforced rider.
    assert await cost_of(request) > await cost_of(control)

    clock.advance(timedelta(hours=11, minutes=30))
    await keep_gps_fresh(db_session, world, clock, where=IN_ZONE)
    assert await cost_of(request) == await cost_of(control)
    assert request.urgency == str(Urgency.low)


async def test_an_expired_pooling_block_lets_the_trip_be_shared_again(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    dispatch: DispatchService,
    overrides: OverrideService,
) -> None:
    first = await queued_request(db_session, world)
    trip = await dispatch.assign(
        world["operator"].id, first.id, world["vehicle"].id, Actor.supervisor, None
    )
    await apply(overrides, world, OverrideAction.block_pooling, trip_id=trip.id)

    second = await queued_request(db_session, world, employee_key="other_employee")

    def blocked(candidates: list[Any]) -> list[Any]:
        return [
            candidate
            for candidate in candidates
            if Violation.pooling_blocked in candidate.violations
        ]

    assert blocked(await dispatch.candidates(world["operator"].id, second.id))
    clock.advance(timedelta(hours=11, minutes=30))
    await keep_gps_fresh(db_session, world, clock)
    after = await dispatch.candidates(world["operator"].id, second.id)
    assert after, "both cabs went silent - this would pass against an empty list"
    assert not blocked(after)


async def test_an_explicit_null_expiry_means_until_the_trip_ends(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    dispatch: DispatchService,
    overrides: OverrideService,
) -> None:
    """Rule 5 allows both, so omitting the field and sending `null` must differ."""
    request = await queued_request(db_session, world)
    result = await overrides.apply(
        world["operator"].id,
        OverrideCommand(
            action=OverrideAction.lock,
            reason_code=ReasonCode.client_request,
            request_id=request.id,
            vehicle_id=world["vehicle"].id,
            expires_at=None,
            expiry_specified=True,
        ),
        actor=Actor.supervisor,
        actor_user_id=None,
    )
    assert result.expires_at is None

    # Well past the 23:59 the default would have chosen, and still pinned.
    clock.advance(timedelta(days=3))
    await keep_gps_fresh(db_session, world, clock)
    still_locked = [
        candidate
        for candidate in await dispatch.candidates(world["operator"].id, request.id)
        if Violation.locked_to_other_vehicle in candidate.violations
    ]
    assert still_locked


async def test_unlock_ends_the_lock_and_closes_its_row(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    overrides: OverrideService,
) -> None:
    request = await queued_request(db_session, world)
    await apply(
        overrides,
        world,
        OverrideAction.lock,
        request_id=request.id,
        vehicle_id=world["vehicle"].id,
    )
    clock.advance(timedelta(minutes=5))
    await apply(overrides, world, OverrideAction.unlock, request_id=request.id)

    assert request.lock_vehicle_id is None
    lock_row, unlock_row = await log_rows(db_session)
    assert lock_row.action == str(OverrideAction.lock)
    # Closed at the moment of release, not left open and contradicted by the next row.
    assert lock_row.expires_at == clock.now()
    assert unlock_row.action == str(OverrideAction.unlock)


# --- hold, cancel, out of service -------------------------------------------------


async def test_a_held_request_is_not_offered_until_the_hold_passes(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    dispatch: DispatchService,
    overrides: OverrideService,
) -> None:
    """The hold exists to stop exactly this automatic path."""
    db_session.add(
        ModeSetting(
            id=uuid.uuid4(),
            operator_id=world["operator"].id,
            mode=str(Mode.semi_auto),
            created_at=NOW,
            updated_at=NOW,
        )
    )
    request = await queued_request(db_session, world)
    # Five minutes, not thirty: `pickup_window_minutes` defaults to 10, so a longer
    # hold would make the request unassignable for a second reason and the test would
    # stop being about the hold.
    await apply(
        overrides,
        world,
        OverrideAction.hold,
        request_id=request.id,
        hold_until=NOW + timedelta(minutes=5),
    )

    semi_auto = SemiAutoService(db_session, clock, dispatch)
    assert (await semi_auto.run_due_semi_auto()).offered == 0

    clock.advance(timedelta(minutes=6))
    await keep_gps_fresh(db_session, world, clock)
    assert (await semi_auto.run_due_semi_auto()).offered == 1


async def test_cancelling_a_trip_requeues_its_riders_rather_than_cancelling_them(
    db_session: AsyncSession,
    world: dict[str, Any],
    dispatch: DispatchService,
    overrides: OverrideService,
) -> None:
    request = await queued_request(db_session, world)
    trip = await dispatch.assign(
        world["operator"].id, request.id, world["vehicle"].id, Actor.supervisor, None
    )

    result = await apply(
        overrides,
        world,
        OverrideAction.cancel,
        trip_id=trip.id,
        reason_code=ReasonCode.vehicle_issue,
    )

    assert [affected.requeued for affected in result.impact.affected_requests] == [True]
    await db_session.refresh(request)
    # They still need a cab. Cancelling their request too would be a second decision.
    assert request.status == str(RequestStatus.queued)
    assert request.trip_id is None
    cancelled = await db_session.get(Trip, trip.id)
    assert cancelled is not None and cancelled.status == str(TripStatus.cancelled)


async def test_taking_a_vehicle_off_the_road_returns_its_riders_to_the_queue(
    db_session: AsyncSession,
    world: dict[str, Any],
    dispatch: DispatchService,
    overrides: OverrideService,
) -> None:
    request = await queued_request(db_session, world)
    trip = await dispatch.assign(
        world["operator"].id, request.id, world["vehicle"].id, Actor.supervisor, None
    )

    await apply(
        overrides,
        world,
        OverrideAction.vehicle_out_of_service,
        vehicle_id=world["vehicle"].id,
        reason_code=ReasonCode.vehicle_issue,
    )

    await db_session.refresh(request)
    assert request.status == str(RequestStatus.queued)
    cancelled = await db_session.get(Trip, trip.id)
    assert cancelled is not None and cancelled.status == str(TripStatus.cancelled)
    parked = await db_session.get(Vehicle, world["vehicle"].id)
    assert parked is not None and parked.status == str(VehicleStatus.out_of_service)


# --- rule 2: the preview ------------------------------------------------------------


async def test_the_preview_changes_nothing(
    db_session: AsyncSession,
    world: dict[str, Any],
    dispatch: DispatchService,
    overrides: OverrideService,
) -> None:
    request = await queued_request(db_session, world)
    trip = await dispatch.assign(
        world["operator"].id, request.id, world["vehicle"].id, Actor.supervisor, None
    )

    impact = await overrides.preview(
        world["operator"].id,
        OverrideCommand(
            action=OverrideAction.reassign,
            reason_code=ReasonCode.traffic,
            request_id=request.id,
            target_vehicle_id=world["other_vehicle"].id,
        ),
    )

    assert [affected.request_id for affected in impact.affected_requests] == [request.id]
    await db_session.refresh(request)
    assert request.trip_id == trip.id
    untouched = await db_session.get(Trip, trip.id)
    assert untouched is not None and untouched.status == str(TripStatus.planned)
    assert await log_rows(db_session) == []


async def test_the_preview_names_the_riders_a_detour_would_cost_minutes(
    db_session: AsyncSession,
    world: dict[str, Any],
    dispatch: DispatchService,
    overrides: OverrideService,
) -> None:
    """§3 rule 2's "added minutes for affected riders", by name - a supervisor
    confirming a detour is confirming it against Rahul, not against a uuid."""
    aboard = await queued_request(db_session, world, employee_key="other_employee")
    await dispatch.assign(
        world["operator"].id, aboard.id, world["other_vehicle"].id, Actor.supervisor, None
    )
    moving = await queued_request(db_session, world)
    await dispatch.assign(
        world["operator"].id, moving.id, world["vehicle"].id, Actor.supervisor, None
    )

    impact = await overrides.preview(
        world["operator"].id,
        OverrideCommand(
            action=OverrideAction.reassign,
            reason_code=ReasonCode.traffic,
            request_id=moving.id,
            target_vehicle_id=world["other_vehicle"].id,
        ),
    )

    detoured = {
        affected.employee_name: affected.added_minutes
        for affected in impact.affected_requests
        if affected.added_minutes is not None
    }
    assert "Rahul" in detoured
    moved = next(
        affected for affected in impact.affected_requests if affected.request_id == moving.id
    )
    assert moved.eta_change_minutes is not None


async def test_the_preview_names_a_zone_left_with_no_available_cab(
    db_session: AsyncSession,
    world: dict[str, Any],
    overrides: OverrideService,
) -> None:
    """§3 rule 2's third number. Only a zone that has cover **now** is reported: one
    that was already empty is not something this override did."""
    zone = make_zone(world["operator"].id, name="sector_62")
    db_session.add(zone)
    await db_session.flush()
    only_cab = await _add_vehicle(db_session, world["operator"].id, IN_ZONE)

    impact = await overrides.preview(
        world["operator"].id,
        OverrideCommand(
            action=OverrideAction.vehicle_out_of_service,
            reason_code=ReasonCode.vehicle_issue,
            vehicle_id=only_cab.id,
        ),
    )
    assert impact.zones_without_available_vehicle == ["sector_62"]

    # A second cab in the same zone, and the same override leaves it covered.
    await _add_vehicle(db_session, world["operator"].id, IN_ZONE)
    impact = await overrides.preview(
        world["operator"].id,
        OverrideCommand(
            action=OverrideAction.vehicle_out_of_service,
            reason_code=ReasonCode.vehicle_issue,
            vehicle_id=only_cab.id,
        ),
    )
    assert impact.zones_without_available_vehicle == []


# --- rule 1: the automatic paths leave overrides alone --------------------------------


async def test_no_automatic_path_moves_a_locked_request_or_pools_a_blocked_trip(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    dispatch: DispatchService,
    overrides: OverrideService,
) -> None:
    """CLAUDE.md hard rule 6, asserted against the real semi-auto sweep.

    The claim is not that the columns are set - it is that the optimizer honours them,
    so the sweep is the thing that has to be run.
    """
    db_session.add(
        ModeSetting(
            id=uuid.uuid4(),
            operator_id=world["operator"].id,
            mode=str(Mode.semi_auto),
            created_at=NOW,
            updated_at=NOW,
        )
    )
    # One rider aboard the first cab, with pooling blocked on their trip.
    aboard = await queued_request(db_session, world, employee_key="other_employee")
    trip = await dispatch.assign(
        world["operator"].id, aboard.id, world["vehicle"].id, Actor.supervisor, None
    )
    await apply(overrides, world, OverrideAction.block_pooling, trip_id=trip.id)

    # ...and a queued rider locked to that same first cab.
    locked = await queued_request(db_session, world)
    await apply(
        overrides,
        world,
        OverrideAction.lock,
        request_id=locked.id,
        vehicle_id=world["vehicle"].id,
    )

    sweep = await SemiAutoService(db_session, clock, dispatch).run_due_semi_auto()

    # Nothing may be offered: the only cab they are allowed on is closed to pooling,
    # and the open cab is the one they are locked away from. Both halves of rule 1 hold
    # at once, and a suggestion here would be the optimizer overruling a supervisor.
    assert sweep.offered == 0
    await db_session.refresh(locked)
    assert locked.status == str(RequestStatus.queued)
    assert locked.trip_id is None


async def test_a_lock_does_not_block_the_cab_it_pins_the_rider_to(
    db_session: AsyncSession,
    world: dict[str, Any],
    dispatch: DispatchService,
    overrides: OverrideService,
) -> None:
    """Found by S09, against a live backend.

    `assign` declared `changes_vehicle=True` unconditionally, so the state machine
    refused "a locked request can only change vehicle through a supervisor override"
    even when the vehicle being assigned **was** the locked one. A locked queued
    request could then never be assigned at all - not by the failsafe, not by a
    supervisor pressing the button, not by anybody - which is the exact opposite of
    what locking it was for.
    """
    request = await queued_request(db_session, world)
    await apply(
        overrides,
        world,
        OverrideAction.lock,
        request_id=request.id,
        vehicle_id=world["vehicle"].id,
    )

    trip = await dispatch.assign(
        world["operator"].id, request.id, world["vehicle"].id, Actor.supervisor, None
    )
    assert trip.vehicle_id == world["vehicle"].id
    assert request.status == str(RequestStatus.assigned)


async def test_a_lock_still_blocks_a_different_cab_without_an_override(
    db_session: AsyncSession,
    world: dict[str, Any],
    dispatch: DispatchService,
    overrides: OverrideService,
) -> None:
    """The other half of the same fix: the guard must still guard."""
    request = await queued_request(db_session, world)
    await apply(
        overrides,
        world,
        OverrideAction.lock,
        request_id=request.id,
        vehicle_id=world["vehicle"].id,
    )

    with pytest.raises(InvalidTransition):
        await dispatch.assign(
            world["operator"].id, request.id, world["other_vehicle"].id, Actor.supervisor, None
        )
