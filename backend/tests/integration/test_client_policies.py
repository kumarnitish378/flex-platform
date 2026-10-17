"""Client policies, end to end (`allocation-rules.md` §1 and §2 rules 7 and 11, B28).

`client_policy` has had a table since B06 and two of its nine columns read. These
tests are about the other seven doing something, and about the two that already worked
still working from the one place that now resolves them.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, time, timedelta
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import FakeClock
from app.core.geo import to_point
from app.core.settings import Settings
from app.domain.dispatch import Violation
from app.domain.enums import Direction, Role, Urgency, VehicleType
from app.domain.errors import ValidationFailed
from app.domain.state_machines import Actor, RequestStatus, VehicleStatus
from app.modules.config.service import ConfigService
from app.modules.dispatch.service import DispatchService
from app.modules.fleet.duty_models import DutySession
from app.modules.fleet.models import Driver, Vehicle
from app.modules.requests.models import RideRequest
from app.modules.requests.service import RideRequestService
from app.modules.routing import EtaService, build_routing_provider
from app.modules.tenancy.policy_service import ClientPolicyService
from app.modules.tracking.models import LocationPing
from tests.builders import (
    make_client,
    make_employee,
    make_office,
    make_operator,
    make_user,
    unique_phone,
)

pytestmark = pytest.mark.requires_db

#: 20:30 IST, inside the default 20:00-06:00 night window and nowhere near it in UTC -
#: which is the point: 15:00 UTC would be the middle of the afternoon.
NIGHT = datetime(2026, 10, 17, 15, 0, tzinfo=UTC)
MORNING = datetime(2026, 10, 17, 2, 30, tzinfo=UTC)  # 08:00 IST

OFFICE = (28.5703, 77.3218)
HOME_A = (28.5123, 77.3910)
HOME_B = (28.5200, 77.3800)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(MORNING)


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

    asha = make_employee(operator.id, corporate.id, office.id, name="Asha", phone=unique_phone())
    asha.home_location = to_point(*HOME_A)
    asha.night_escort_required = True
    rahul = make_employee(operator.id, corporate.id, office.id, name="Rahul", phone=unique_phone())
    rahul.home_location = to_point(*HOME_B)
    db_session.add_all([asha, rahul])
    await db_session.flush()

    vehicle = Vehicle(
        id=uuid.uuid4(),
        operator_id=operator.id,
        registration_no=f"DL{uuid.uuid4().hex[:6].upper()}",
        vehicle_type=VehicleType.suv_6,
        seat_capacity=6,
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
            started_at=MORNING - timedelta(hours=2),
        )
    )
    await db_session.flush()
    return {
        "operator": operator,
        "client": corporate,
        "office": office,
        "asha": asha,
        "rahul": rahul,
        "vehicle": vehicle,
    }


@pytest.fixture
def dispatch(db_session: AsyncSession, clock: FakeClock, eta: EtaService) -> DispatchService:
    return DispatchService(db_session, clock, eta)


@pytest.fixture
def policies(db_session: AsyncSession, clock: FakeClock) -> ClientPolicyService:
    return ClientPolicyService(db_session, clock)


async def ping(db_session: AsyncSession, world: dict[str, Any], clock: FakeClock) -> None:
    db_session.add(
        LocationPing(
            vehicle_id=world["vehicle"].id,
            operator_id=world["operator"].id,
            recorded_at=clock.now(),
            received_at=clock.now(),
            location=to_point(*HOME_A),
            source="sim",
        )
    )
    await db_session.flush()


async def request_for(
    db_session: AsyncSession,
    world: dict[str, Any],
    who: str,
    at: datetime,
    *,
    direction: Direction = Direction.to_office,
    no_sharing: bool = False,
) -> RideRequest:
    request = RideRequest(
        id=uuid.uuid4(),
        operator_id=world["operator"].id,
        client_id=world["client"].id,
        employee_id=world[who].id,
        direction=str(direction),
        office_id=world["office"].id,
        location=to_point(*(HOME_A if who == "asha" else HOME_B)),
        requested_time=at,
        urgency=str(Urgency.medium),
        status=str(RequestStatus.queued),
        no_sharing=no_sharing,
        queued_at=at,
        expires_at=at + timedelta(hours=2),
    )
    db_session.add(request)
    await db_session.flush()
    return request


def violations_for(candidates: list[Any], vehicle_id: uuid.UUID) -> list[Violation]:
    return next(c.violations for c in candidates if c.vehicle.id == vehicle_id)


# --- rule 7: the stricter value, through the whole stack -----------------------------


async def test_a_clients_tighter_detour_limit_is_the_one_applied(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    dispatch: DispatchService,
    policies: ClientPolicyService,
) -> None:
    await ping(db_session, world, clock)
    await ConfigService(db_session, clock).update(
        world["operator"].id, {"max_detour_minutes": 60, "max_detour_factor": 3.0}
    )
    aboard = await request_for(db_session, world, "rahul", MORNING)
    await dispatch.assign(
        world["operator"].id, aboard.id, world["vehicle"].id, Actor.supervisor, None
    )
    joining = await request_for(db_session, world, "asha", MORNING)

    # Generous operator limits: the detour is allowed.
    assert Violation.detour_minutes_exceeded not in violations_for(
        await dispatch.candidates(world["operator"].id, joining.id), world["vehicle"].id
    )

    # The client will not have their people detoured at all.
    await policies.put(
        world["operator"].id,
        world["client"].id,
        {"max_detour_minutes": 0, "max_detour_factor": 1.0},
    )
    assert Violation.detour_minutes_exceeded in violations_for(
        await dispatch.candidates(world["operator"].id, joining.id), world["vehicle"].id
    )


async def test_a_clients_looser_detour_limit_is_not_applied(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    dispatch: DispatchService,
    policies: ClientPolicyService,
) -> None:
    """The direction a client would actually try. Their number is stored as written -
    and simply not used, which `GET .../policy` shows them."""
    await ping(db_session, world, clock)
    await ConfigService(db_session, clock).update(
        world["operator"].id, {"max_detour_minutes": 0, "max_detour_factor": 1.0}
    )
    aboard = await request_for(db_session, world, "rahul", MORNING)
    await dispatch.assign(
        world["operator"].id, aboard.id, world["vehicle"].id, Actor.supervisor, None
    )
    joining = await request_for(db_session, world, "asha", MORNING)
    await policies.put(
        world["operator"].id,
        world["client"].id,
        {"max_detour_minutes": 60, "max_detour_factor": 3.0},
    )

    effective = await policies.for_client(world["operator"].id, world["client"].id)
    assert effective.max_detour_minutes == 0
    assert Violation.detour_minutes_exceeded in violations_for(
        await dispatch.candidates(world["operator"].id, joining.id), world["vehicle"].id
    )


# --- the keys a client may set either way ---------------------------------------------


async def test_a_clients_own_pickup_window_is_the_one_checked(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    dispatch: DispatchService,
    policies: ClientPolicyService,
) -> None:
    await ping(db_session, world, clock)
    await ConfigService(db_session, clock).update(
        world["operator"].id, {"pickup_window_minutes": 0}
    )
    # Asked for twenty minutes ago; with a zero-minute window the cab is always late.
    late = await request_for(db_session, world, "asha", MORNING - timedelta(minutes=20))
    assert Violation.pickup_window_missed in violations_for(
        await dispatch.candidates(world["operator"].id, late.id), world["vehicle"].id
    )

    await policies.put(world["operator"].id, world["client"].id, {"pickup_window_minutes": 30})
    assert Violation.pickup_window_missed not in violations_for(
        await dispatch.candidates(world["operator"].id, late.id), world["vehicle"].id
    )


# --- pooling and opt-out --------------------------------------------------------------


async def test_a_client_who_does_not_pool_gets_exclusive_trips(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    dispatch: DispatchService,
    policies: ClientPolicyService,
) -> None:
    """Rule by rule the same thing as every one of their riders asking not to share."""
    await ping(db_session, world, clock)
    aboard = await request_for(db_session, world, "rahul", MORNING)
    await dispatch.assign(
        world["operator"].id, aboard.id, world["vehicle"].id, Actor.supervisor, None
    )
    joining = await request_for(db_session, world, "asha", MORNING)
    assert Violation.no_sharing not in violations_for(
        await dispatch.candidates(world["operator"].id, joining.id), world["vehicle"].id
    )

    await policies.put(world["operator"].id, world["client"].id, {"pooling_allowed": False})
    assert Violation.no_sharing in violations_for(
        await dispatch.candidates(world["operator"].id, joining.id), world["vehicle"].id
    )


async def test_an_employee_cannot_opt_out_of_sharing_unless_their_client_allows_it(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    policies: ClientPolicyService,
) -> None:
    """Refused rather than silently ignored: a rider who ticks the box and is pooled
    anyway has been told something untrue.

    The permission is on by default - Phase 1 shipped opting out with no gate, so B28
    had no business revoking it - which is why this test has to turn it off first.
    """
    user = make_user(name="Asha", phone=world["asha"].phone)
    db_session.add(user)
    await db_session.flush()
    world["asha"].user_id = user.id
    await db_session.flush()

    requests = RideRequestService(db_session, clock)
    await policies.put(
        world["operator"].id, world["client"].id, {"employee_opt_out_allowed": False}
    )

    with pytest.raises(ValidationFailed) as excinfo:
        await requests.create(
            operator_id=world["operator"].id,
            actor_role=Role.employee,
            actor_user_id=user.id,
            direction=Direction.to_office,
            requested_time=MORNING + timedelta(hours=1),
            no_sharing=True,
        )
    assert "opt out" in str(excinfo.value)

    await policies.put(world["operator"].id, world["client"].id, {"employee_opt_out_allowed": True})
    created = await requests.create(
        operator_id=world["operator"].id,
        actor_role=Role.employee,
        actor_user_id=user.id,
        direction=Direction.to_office,
        requested_time=MORNING + timedelta(hours=1),
        no_sharing=True,
    )
    assert created.no_sharing is True


# --- rule 11: night safety --------------------------------------------------------------

# One scenario for all four, with one thing varied each time. Rahul is already aboard
# and Asha is joining; the cab is parked at Asha's door, so the planner collects her
# **first** - which is the arrangement rule 11 is about, and which the assignment order
# does not decide. That is the point worth stating: the rule judges the sequence the
# trip would actually run, not the order a supervisor happened to press the buttons in.


async def _joining_asha_first(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    dispatch: DispatchService,
) -> list[Violation]:
    await ping(db_session, world, clock)
    aboard = await request_for(db_session, world, "rahul", clock.now())
    await dispatch.assign(
        world["operator"].id, aboard.id, world["vehicle"].id, Actor.supervisor, None
    )
    joining = await request_for(db_session, world, "asha", clock.now())
    return violations_for(
        await dispatch.candidates(world["operator"].id, joining.id), world["vehicle"].id
    )


async def test_night_safety_refuses_leaving_a_flagged_rider_alone_at_the_first_pickup(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    dispatch: DispatchService,
    policies: ClientPolicyService,
) -> None:
    """Asha is flagged `night_escort_required` and would ride alone from her door
    until Rahul gets in."""
    clock.set(NIGHT)
    await policies.put(world["operator"].id, world["client"].id, {"night_safety_enabled": True})
    assert Violation.night_safety_breach in await _joining_asha_first(
        db_session, world, clock, dispatch
    )


async def test_the_same_sequence_is_fine_for_a_rider_who_is_not_flagged(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    dispatch: DispatchService,
    policies: ClientPolicyService,
) -> None:
    """Same trip, same order, same hour - the flag is the only difference, which is
    what makes the previous test about the flag and not about the geometry."""
    clock.set(NIGHT)
    await policies.put(world["operator"].id, world["client"].id, {"night_safety_enabled": True})
    world["asha"].night_escort_required = False
    await db_session.flush()
    assert Violation.night_safety_breach not in await _joining_asha_first(
        db_session, world, clock, dispatch
    )


async def test_the_same_trip_in_the_morning_is_not_a_night_trip(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    dispatch: DispatchService,
    policies: ClientPolicyService,
) -> None:
    """The window is local time. 20:30 IST is 15:00 UTC - an afternoon by the stored
    instant and an evening to everybody who actually works there, so a rule compared
    against the UTC time of day would police the wrong half of the day."""
    await policies.put(world["operator"].id, world["client"].id, {"night_safety_enabled": True})
    assert clock.now().hour == 2  # 08:00 IST
    assert Violation.night_safety_breach not in await _joining_asha_first(
        db_session, world, clock, dispatch
    )


async def test_night_safety_is_off_until_somebody_turns_it_on(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    dispatch: DispatchService,
) -> None:
    """Phase 1's behaviour, and every operator who has not opted in."""
    clock.set(NIGHT)
    assert Violation.night_safety_breach not in await _joining_asha_first(
        db_session, world, clock, dispatch
    )


async def test_the_operator_can_turn_night_safety_on_for_every_client(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    dispatch: DispatchService,
) -> None:
    """A floor: a client row that exists and has never been touched must not read as
    "off" and quietly disable an operator-wide safety rule."""
    clock.set(NIGHT)
    await ConfigService(db_session, clock).update(
        world["operator"].id, {"night_safety_enabled": True}
    )
    await ClientPolicyService(db_session, clock).put(
        world["operator"].id, world["client"].id, {"pooling_allowed": True}
    )
    assert Violation.night_safety_breach in await _joining_asha_first(
        db_session, world, clock, dispatch
    )


async def test_an_operator_policing_only_the_last_drop_allows_the_morning_pickup(
    db_session: AsyncSession,
    world: dict[str, Any],
    clock: FakeClock,
    dispatch: DispatchService,
    policies: ClientPolicyService,
) -> None:
    """OQ-10 is open, so which lone positions are policed is a config key. Set to
    `last_drop`, a `to_office` trip has no policed position at all."""
    clock.set(NIGHT)
    await ConfigService(db_session, clock).update(
        world["operator"].id, {"night_safety_positions": "last_drop"}
    )
    await policies.put(world["operator"].id, world["client"].id, {"night_safety_enabled": True})
    assert Violation.night_safety_breach not in await _joining_asha_first(
        db_session, world, clock, dispatch
    )


# --- the policy row itself --------------------------------------------------------------


async def test_a_null_clears_an_override_and_an_omitted_field_leaves_it_alone(
    world: dict[str, Any], policies: ClientPolicyService
) -> None:
    await policies.put(
        world["operator"].id,
        world["client"].id,
        {"max_detour_minutes": 5, "pickup_window_minutes": 20},
    )
    await policies.put(world["operator"].id, world["client"].id, {"max_detour_minutes": None})

    row = await policies.row(world["operator"].id, world["client"].id)
    assert row is not None
    assert row.max_detour_minutes is None
    assert row.pickup_window_minutes == 20


async def test_a_client_night_window_overrides_the_operators(
    db_session: AsyncSession, world: dict[str, Any], clock: FakeClock, policies: ClientPolicyService
) -> None:
    await policies.put(
        world["operator"].id,
        world["client"].id,
        {"night_start": time(21, 0), "night_end": time(4, 0)},
    )
    effective = await policies.for_client(world["operator"].id, world["client"].id)
    assert (effective.night_start, effective.night_end) == (time(21, 0), time(4, 0))
