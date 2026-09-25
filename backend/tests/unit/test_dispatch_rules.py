"""Stop sequencing and the hard-rule checks (B14, `allocation-rules.md` sections 2-3).

Pure and fast: every case here is arithmetic over a duration table, so the rules that
decide who shares a cab with whom can be stated in four lines and checked in microseconds.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.domain.dispatch import (
    AssignmentFacts,
    DetourLimits,
    Place,
    Rider,
    Violation,
    best_insertion,
    build_plan,
    check_hard_rules,
    pickup_time,
    stricter,
)
from app.domain.enums import Direction
from app.domain.state_machines import StopKind

NOW = datetime(2026, 9, 25, 9, 0, tzinfo=UTC)

OFFICE = Place(28.5000, 77.4000)
NEAR = Place(28.5100, 77.4000)  # about 1.1 km from the office
MID = Place(28.5300, 77.4000)  # about 3.3 km
FAR = Place(28.5600, 77.4000)  # about 6.7 km


def rider(place: Place, request_id: uuid.UUID | None = None) -> Rider:
    return Rider(request_id or uuid.uuid4(), place)


def straight_line(first: Place, second: Place) -> float:
    """A duration table that is proportional to latitude difference. 1 degree = 1 hour."""
    return abs(first.lat - second.lat) * 3600


# --- sequencing ---------------------------------------------------------------------


def test_a_to_office_trip_picks_everyone_up_then_drops_at_the_office() -> None:
    first, second = rider(FAR), rider(MID)
    plan = build_plan(Direction.to_office, OFFICE, [first, second], straight_line)

    assert [stop.kind for stop in plan.stops] == [
        StopKind.pickup,
        StopKind.pickup,
        StopKind.drop,
        StopKind.drop,
    ]
    assert [stop.place for stop in plan.stops] == [FAR, MID, OFFICE, OFFICE]


def test_a_from_office_trip_collects_at_the_office_then_drops_each_rider() -> None:
    first, second = rider(MID), rider(FAR)
    plan = build_plan(Direction.from_office, OFFICE, [first, second], straight_line)

    assert [stop.place for stop in plan.stops] == [OFFICE, OFFICE, MID, FAR]


def test_sequences_are_contiguous_and_start_at_one() -> None:
    """`trip_stop` is unique on (trip_id, sequence); gaps would break re-ordering."""
    riders = [rider(FAR), rider(MID), rider(NEAR)]
    plan = build_plan(Direction.to_office, OFFICE, riders, straight_line)

    assert [stop.sequence for stop in plan.stops] == [1, 2, 3, 4, 5, 6]


def test_every_rider_gets_a_pickup_and_a_drop() -> None:
    """One stop each would make "picked up" and "dropped" the same event."""
    riders = [rider(FAR), rider(MID)]
    plan = build_plan(Direction.to_office, OFFICE, riders, straight_line)

    for person in riders:
        kinds = [stop.kind for stop in plan.stops if stop.request_id == person.request_id]
        assert sorted(kinds) == sorted([StopKind.pickup, StopKind.drop])


def test_an_empty_trip_plans_nothing() -> None:
    plan = build_plan(Direction.to_office, OFFICE, [], straight_line)
    assert plan.stops == ()
    assert plan.total_seconds == 0.0


def test_ride_time_is_measured_from_pickup_to_drop() -> None:
    solo = rider(FAR)
    plan = build_plan(Direction.to_office, OFFICE, [solo], straight_line)

    # 28.56 -> 28.50 is 0.06 degrees, which this table calls 216 seconds.
    assert plan.ride_seconds[solo.request_id] == pytest.approx(216.0)


def test_the_office_block_costs_nothing_between_its_stops() -> None:
    """Three riders dropped at one office is one arrival, not three drives.

    Stated as: adding riders whose drop stops share a place must not add driving time
    beyond the legs between the pickups.
    """
    riders = [rider(FAR), rider(MID), rider(NEAR)]
    plan = build_plan(Direction.to_office, OFFICE, riders, straight_line)

    pickups = straight_line(FAR, MID) + straight_line(MID, NEAR) + straight_line(NEAR, OFFICE)
    assert plan.total_seconds == pytest.approx(pickups, abs=1e-6)


def test_picking_up_people_already_on_the_way_is_free() -> None:
    """The economics of pooling: collinear riders cost the driver nothing extra."""
    detour = build_plan(
        Direction.to_office, OFFICE, [rider(FAR), rider(MID), rider(NEAR)], straight_line
    )
    solo = build_plan(Direction.to_office, OFFICE, [rider(FAR)], straight_line)

    assert detour.total_seconds == pytest.approx(solo.total_seconds, abs=1e-6)


# --- insertion ---------------------------------------------------------------------------


def test_a_newcomer_on_the_way_goes_in_the_middle() -> None:
    """The point of pooling: someone already on the route costs nobody anything much."""
    far, near = rider(FAR), rider(NEAR)
    newcomer = rider(MID)

    insertion = best_insertion(Direction.to_office, OFFICE, [far, near], newcomer, straight_line)

    order = [person.place for person in insertion.plan.order]
    assert order == [FAR, MID, NEAR]
    assert insertion.position == 1


def test_the_insertion_minimises_time_added_for_the_existing_riders() -> None:
    existing = [rider(FAR), rider(NEAR)]
    newcomer = rider(MID)

    chosen = best_insertion(Direction.to_office, OFFICE, existing, newcomer, straight_line)
    alternatives = []
    for position in range(len(existing) + 1):
        order = [*existing[:position], newcomer, *existing[position:]]
        plan = build_plan(Direction.to_office, OFFICE, order, straight_line)
        before = build_plan(Direction.to_office, OFFICE, existing, straight_line)
        alternatives.append(
            sum(
                plan.ride_seconds[person.request_id] - before.ride_seconds[person.request_id]
                for person in existing
            )
        )

    assert sum(chosen.added_minutes.values()) * 60 == pytest.approx(min(alternatives), abs=1e-6)


def test_the_first_rider_on_an_empty_trip_adds_nothing() -> None:
    insertion = best_insertion(Direction.to_office, OFFICE, [], rider(MID), straight_line)

    assert insertion.position == 0
    assert insertion.added_minutes == {}
    assert insertion.worst_added_minutes == 0.0


def test_added_minutes_are_reported_per_existing_rider() -> None:
    """SUP-03: the supervisor sees what this costs each person already in the cab."""
    first, second = rider(NEAR), rider(MID)
    insertion = best_insertion(
        Direction.to_office, OFFICE, [first, second], rider(FAR), straight_line
    )

    assert set(insertion.added_minutes) == {first.request_id, second.request_id}
    assert all(minutes >= 0 for minutes in insertion.added_minutes.values())


def test_a_detour_backwards_costs_the_existing_rider() -> None:
    """A newcomer behind the current rider drags them away from the office."""
    on_board = rider(MID)
    insertion = best_insertion(Direction.to_office, OFFICE, [on_board], rider(FAR), straight_line)

    # Picking FAR up first is the cheaper order, so the rider at MID is untouched;
    # either way nobody's ride time may shrink.
    assert insertion.added_minutes[on_board.request_id] >= 0.0


def test_added_minutes_are_never_negative() -> None:
    """A re-order that happens to help someone is not a credit; it is zero."""
    on_board = [rider(FAR), rider(NEAR)]
    insertion = best_insertion(Direction.to_office, OFFICE, on_board, rider(MID), straight_line)

    assert min(insertion.added_minutes.values()) >= 0.0


def test_from_office_insertion_orders_the_drops() -> None:
    first = rider(FAR)
    insertion = best_insertion(Direction.from_office, OFFICE, [first], rider(NEAR), straight_line)

    drops = [stop.place for stop in insertion.plan.stops if stop.kind is StopKind.drop]
    assert drops == [NEAR, FAR]


# --- hard rules -----------------------------------------------------------------------


def facts(**overrides: object) -> AssignmentFacts:
    base: dict[str, object] = {
        "vehicle_id": uuid.uuid4(),
        "vehicle_status": "available",
        "vehicle_type": "sedan_4",
        "gps_age_seconds": 5.0,
        "stale_gps_seconds": 60,
        "eta_to_pickup_seconds": 300.0,
        "candidate_max_eta_minutes": 20,
        "pickup_window_minutes": 10,
        "requested_time": NOW + timedelta(minutes=5),
        "pickup_at": NOW + timedelta(minutes=5),
        "direction": Direction.to_office,
        "office_id": uuid.uuid4(),
        "employee_is_vip": False,
        "request_no_sharing": False,
        "lock_vehicle_id": None,
    }
    base.update(overrides)
    return AssignmentFacts(**base)  # type: ignore[arg-type]


def test_a_clean_assignment_breaks_no_rules() -> None:
    assert check_hard_rules(facts()) == []


def test_an_out_of_service_vehicle_is_flagged() -> None:
    assert Violation.vehicle_unavailable in check_hard_rules(facts(vehicle_status="out_of_service"))


def test_an_off_duty_vehicle_is_flagged() -> None:
    assert Violation.vehicle_unavailable in check_hard_rules(facts(vehicle_status="off_duty"))


def test_a_vehicle_on_a_trip_is_not_flagged() -> None:
    """En-route reuse is a feature, not a violation (`allocation-rules.md` section 3)."""
    assert Violation.vehicle_unavailable not in check_hard_rules(facts(vehicle_status="on_trip"))


def test_stale_gps_is_flagged() -> None:
    assert Violation.gps_stale in check_hard_rules(facts(gps_age_seconds=61.0))
    assert Violation.gps_stale not in check_hard_rules(facts(gps_age_seconds=60.0))


def test_no_gps_at_all_is_stale() -> None:
    """Never heard from is worse than heard from late, not better."""
    assert Violation.gps_stale in check_hard_rules(facts(gps_age_seconds=None))


def test_a_lock_to_another_vehicle_is_flagged() -> None:
    assert Violation.locked_to_other_vehicle in check_hard_rules(
        facts(lock_vehicle_id=uuid.uuid4())
    )


def test_a_lock_to_this_vehicle_is_fine() -> None:
    vehicle_id = uuid.uuid4()
    assert check_hard_rules(facts(vehicle_id=vehicle_id, lock_vehicle_id=vehicle_id)) == []


def test_pooling_blocked_only_matters_when_someone_is_on_board() -> None:
    assert Violation.pooling_blocked in check_hard_rules(
        facts(trip_pooling_blocked=True, trip_has_other_riders=True)
    )
    assert Violation.pooling_blocked not in check_hard_rules(
        facts(trip_pooling_blocked=True, trip_has_other_riders=False)
    )


def test_a_vip_needs_a_vip_vehicle() -> None:
    found = check_hard_rules(facts(employee_is_vip=True))
    assert Violation.vip_needs_vip_vehicle in found


def test_a_vip_in_a_vip_vehicle_alone_is_clean() -> None:
    assert check_hard_rules(facts(employee_is_vip=True, vehicle_type="vip")) == []


def test_a_vip_may_not_share() -> None:
    found = check_hard_rules(
        facts(employee_is_vip=True, vehicle_type="vip", trip_has_other_riders=True)
    )
    assert Violation.no_sharing in found


def test_no_sharing_is_flagged_only_on_a_shared_trip() -> None:
    assert Violation.no_sharing in check_hard_rules(
        facts(request_no_sharing=True, trip_has_other_riders=True)
    )
    assert Violation.no_sharing not in check_hard_rules(facts(request_no_sharing=True))


def test_no_sharing_is_reported_once() -> None:
    """A VIP who also opted out is one problem, not two."""
    found = check_hard_rules(
        facts(
            employee_is_vip=True,
            vehicle_type="vip",
            request_no_sharing=True,
            trip_has_other_riders=True,
        )
    )
    assert found.count(Violation.no_sharing) == 1


def test_a_direction_mismatch_is_flagged() -> None:
    found = check_hard_rules(
        facts(direction=Direction.to_office, trip_direction=Direction.from_office)
    )
    assert Violation.direction_mismatch in found


def test_an_office_mismatch_is_flagged() -> None:
    found = check_hard_rules(facts(trip_office_id=uuid.uuid4()))
    assert Violation.office_mismatch in found


def test_the_same_office_is_not_a_mismatch() -> None:
    office_id = uuid.uuid4()
    assert check_hard_rules(facts(office_id=office_id, trip_office_id=office_id)) == []


def test_a_pickup_outside_the_window_is_flagged() -> None:
    late = facts(pickup_at=NOW + timedelta(minutes=16), requested_time=NOW + timedelta(minutes=5))
    assert Violation.pickup_window_missed in check_hard_rules(late)


def test_an_early_pickup_outside_the_window_is_also_flagged() -> None:
    """The window is symmetric: a cab 20 minutes early is a rider standing outside."""
    early = facts(pickup_at=NOW, requested_time=NOW + timedelta(minutes=20))
    assert Violation.pickup_window_missed in check_hard_rules(early)


def test_an_eta_over_the_candidate_limit_is_flagged() -> None:
    assert Violation.eta_over_candidate_limit in check_hard_rules(
        facts(eta_to_pickup_seconds=21 * 60)
    )
    assert Violation.eta_over_candidate_limit not in check_hard_rules(
        facts(eta_to_pickup_seconds=20 * 60)
    )


def test_capacity_is_not_a_reportable_violation() -> None:
    """ADR-0011: capacity is refused by the caller, so it must never be a soft report."""
    assert not hasattr(Violation, "capacity_exceeded")


# --- detour limits -------------------------------------------------------------------------


def test_a_long_detour_breaks_the_factor_limit() -> None:
    on_board = rider(FAR)
    insertion = best_insertion(Direction.to_office, OFFICE, [on_board], rider(NEAR), straight_line)
    direct = {on_board.request_id: 216.0, insertion.plan.order[-1].request_id: 36.0}
    limits = {
        person.request_id: DetourLimits(max_detour_factor=1.0, max_detour_minutes=0.0)
        for person in insertion.plan.order
    }

    found = check_hard_rules(facts(), insertion, limits, direct)
    assert Violation.detour_factor_exceeded in found
    assert Violation.detour_minutes_exceeded in found


def test_a_generous_limit_is_not_broken() -> None:
    on_board = rider(FAR)
    insertion = best_insertion(Direction.to_office, OFFICE, [on_board], rider(NEAR), straight_line)
    direct = {person.request_id: 10.0 for person in insertion.plan.order}
    limits = {
        person.request_id: DetourLimits(max_detour_factor=100.0, max_detour_minutes=600.0)
        for person in insertion.plan.order
    }

    found = check_hard_rules(facts(), insertion, limits, direct)
    assert Violation.detour_factor_exceeded not in found
    assert Violation.detour_minutes_exceeded not in found


def test_a_rider_with_no_stated_limit_is_skipped() -> None:
    """Missing data must not invent a violation out of nothing."""
    insertion = best_insertion(
        Direction.to_office, OFFICE, [rider(FAR)], rider(NEAR), straight_line
    )

    assert check_hard_rules(facts(), insertion, {}, {}) == []


def test_the_stricter_of_two_limits_wins() -> None:
    operator_limit = DetourLimits(max_detour_factor=1.6, max_detour_minutes=25.0)
    client_limit = DetourLimits(max_detour_factor=1.3, max_detour_minutes=40.0)

    combined = stricter(operator_limit, client_limit)
    assert combined.max_detour_factor == 1.3
    assert combined.max_detour_minutes == 25.0


def test_pickup_time_is_now_plus_the_eta() -> None:
    assert pickup_time(NOW, 600) == NOW + timedelta(minutes=10)
