"""En-route reuse looks at the cab's route, not just how far away it is (B33).

`allocation-rules.md` §3: an en-route cab is a candidate if its **route** passes within
`enroute_reuse_max_eta_minutes` of the pickup. Phase 1 compared the straight ETA from the
cab's current position, which cannot tell the best candidate there is (a cab about to
drive past the rider's door, twenty minutes away) from a trap (a cab five minutes away
that is pointed the other way).

The world is the flat one in `optimizer_helpers`: latitude is minutes, the office is the
origin, so "on the way" is a number a test can state.
"""

from __future__ import annotations

import uuid
from datetime import timedelta

import pytest

from app.domain.dispatch import (
    AssignmentFacts,
    DetourLimits,
    Place,
    Rider,
    Violation,
    best_insertion,
    check_hard_rules,
    slot_detour_seconds,
)
from app.domain.enums import Direction
from app.domain.optimizer.model import Veh
from app.domain.optimizer.route import (
    Person,
    best_slot_detour_seconds,
    check_route,
    new_person,
    seated_people,
)
from tests.unit.optimizer_helpers import (
    NOW,
    OFFICE,
    OFFICE_ID,
    minutes_out,
    problem,
    req,
    rid,
    seated,
    seconds,
    trip,
    veh,
)

LIMITS = DetourLimits(max_detour_factor=3.0, max_detour_minutes=60)


def judge(
    origin: Place,
    waiting_at: list[Place],
    newcomer_at: Place,
    *,
    requested_in_minutes: float,
    ceiling_minutes: int = 5,
) -> tuple[list[Violation], float, float]:
    """The §2 verdict for an en-route cab, plus the straight ETA and the slot detour."""
    existing = [Rider(rid(100 + i), place) for i, place in enumerate(waiting_at)]
    newcomer = Rider(rid(1), newcomer_at)
    insertion = best_insertion(Direction.to_office, OFFICE, existing, newcomer, seconds, origin)
    assert insertion.pickup_arrival_seconds is not None
    straight = seconds(origin, newcomer_at)
    facts = AssignmentFacts(
        vehicle_id=uuid.uuid4(),
        vehicle_status="on_trip",
        vehicle_type="sedan_4",
        gps_age_seconds=5.0,
        stale_gps_seconds=60,
        eta_to_pickup_seconds=straight,
        candidate_max_eta_minutes=20,
        pickup_window_minutes=10,
        requested_time=NOW + timedelta(minutes=requested_in_minutes),
        pickup_at=NOW + timedelta(seconds=insertion.pickup_arrival_seconds),
        direction=Direction.to_office,
        office_id=OFFICE_ID,
        employee_is_vip=False,
        request_no_sharing=False,
        lock_vehicle_id=None,
        enroute_reuse_max_eta_minutes=ceiling_minutes,
        trip_direction=Direction.to_office,
        trip_office_id=OFFICE_ID,
        trip_has_other_riders=True,
    )
    limits = {r.request_id: LIMITS for r in [*existing, newcomer]}
    direct = {r.request_id: seconds(r.place, OFFICE) for r in [*existing, newcomer]}
    violations = check_hard_rules(facts, insertion, limits, direct)
    assert insertion.slot_detour_seconds is not None
    return violations, straight, insertion.slot_detour_seconds


def test_a_cab_about_to_drive_past_the_rider_is_a_candidate_however_far_off_it_is() -> None:
    """25 minutes out, a rider waiting at 20, the newcomer at 10 - squarely on the way."""
    violations, straight, detour = judge(
        minutes_out(25), [minutes_out(20)], minutes_out(10), requested_in_minutes=15
    )

    assert straight > 5 * 60, "the old rule would have refused this cab"
    assert detour == pytest.approx(0.0)
    assert Violation.enroute_reuse_eta_exceeded not in violations
    assert violations == []


def test_a_cab_near_the_rider_but_pointed_the_other_way_is_not() -> None:
    """The cab is 1.2 minutes' drive from the newcomer, who is behind it; its rider is far ahead.

    The straight ETA is well inside the five-minute ceiling - which is exactly why the old
    rule offered it - but collecting the newcomer means driving back and then forward
    again.
    """
    origin, ahead, behind = minutes_out(11), minutes_out(30), minutes_out(7)

    straight = seconds(origin, behind)
    early_slot = slot_detour_seconds(seconds, origin, behind, ahead)
    violations, _, _ = judge(origin, [ahead], behind, requested_in_minutes=0)

    assert straight <= 5 * 60, "the old rule would have accepted this cab"
    assert early_slot > 2 * straight * 0.99, "doubling back costs about twice the distance"
    # The slot Phase 1's sequencing picks leaves the cab's own rider undisturbed by putting
    # the newcomer last - so it is refused for collecting them forty minutes late. Either
    # way the cab is not a candidate; the ceiling itself is pinned down just below.
    assert violations


def test_the_ceiling_is_the_configured_one() -> None:
    """A detour of a few minutes passes a 5-minute ceiling and fails a 2-minute one."""
    side = Place(0.22, 0.03)  # a little off the road, between the cab and its rider
    kwargs = {"requested_in_minutes": 15.0}
    wide, _, detour = judge(minutes_out(25), [minutes_out(20)], side, ceiling_minutes=5, **kwargs)
    tight, _, _ = judge(minutes_out(25), [minutes_out(20)], side, ceiling_minutes=2, **kwargs)

    assert 2 * 60 < detour < 5 * 60
    assert Violation.enroute_reuse_eta_exceeded not in wide
    assert Violation.enroute_reuse_eta_exceeded in tight


def test_without_an_origin_the_old_behaviour_stands() -> None:
    """A caller that cannot say where the cab is still gets the straight-ETA ceiling."""
    existing = [Rider(rid(100), minutes_out(20))]
    newcomer = Rider(rid(1), minutes_out(10))
    insertion = best_insertion(Direction.to_office, OFFICE, existing, newcomer, seconds)

    assert insertion.slot_detour_seconds is None
    assert insertion.pickup_arrival_seconds is None


def test_a_from_office_pickup_is_never_a_detour() -> None:
    """Every pickup is the office, which the cab is already heading for."""
    existing = [Rider(rid(100), minutes_out(20))]
    newcomer = Rider(rid(1), minutes_out(10))

    insertion = best_insertion(
        Direction.from_office, OFFICE, existing, newcomer, seconds, minutes_out(8)
    )

    assert insertion.slot_detour_seconds == 0.0


# --- the optimizer applies the same rule -------------------------------------------------------


def test_the_optimizer_takes_the_passing_cab_and_refuses_the_one_pointed_away() -> None:
    passing = veh(1, minutes_out(25), status="on_trip", trip=trip(1, [seated(9, minutes_out(20))]))
    away = veh(2, minutes_out(11), status="on_trip", trip=trip(2, [seated(8, minutes_out(30))]))
    newcomer = req(1, minutes_out(10), requested_in_minutes=15)
    behind = req(2, minutes_out(7))

    # Each alone, so the answer is about that cab and not about a competition.
    takes = check_route(
        problem([newcomer], [passing]),
        passing,
        Direction.to_office,
        OFFICE_ID,
        [*[_p for _p in _seated_people(passing)], new_person(newcomer)],
    )
    refuses = check_route(
        problem([behind], [away]),
        away,
        Direction.to_office,
        OFFICE_ID,
        [new_person(behind), *_seated_people(away)],
    )

    assert takes.violations == ()
    assert Violation.enroute_reuse_eta_exceeded in refuses.violations


def _seated_people(vehicle: Veh) -> list[Person]:
    assert vehicle.trip is not None
    return seated_people(vehicle.trip.riders)


def test_the_best_case_bound_never_exceeds_any_slots_exact_detour() -> None:
    """The DARP uses the bound to rule cabs out early, so it must be optimistic."""
    cab = veh(1, minutes_out(25), status="on_trip", trip=trip(1, [seated(9, minutes_out(20))]))
    newcomer = req(1, Place(0.12, 0.04))
    prob = problem([newcomer], [cab])
    bound = best_slot_detour_seconds(
        prob, cab, Direction.to_office, OFFICE, _seated_people(cab), new_person(newcomer)
    )

    for order in (
        [*_seated_people(cab), new_person(newcomer)],
        [new_person(newcomer), *_seated_people(cab)],
    ):
        exact = check_route(prob, cab, Direction.to_office, OFFICE_ID, order)
        assert exact.route is not None
        from app.domain.optimizer.route import slot_detour_for_order

        assert (
            bound
            <= slot_detour_for_order(
                prob, cab, Direction.to_office, OFFICE, order, new_person(newcomer)
            )
            + 1e-9
        )


def rule_verdict(slot_detour: float | None, straight_eta: float) -> list[Violation]:
    """The en-route ceiling alone: a hand-built insertion with a stated detour."""
    from app.domain.dispatch import Insertion, Plan

    facts = AssignmentFacts(
        vehicle_id=uuid.uuid4(),
        vehicle_status="on_trip",
        vehicle_type="sedan_4",
        gps_age_seconds=5.0,
        stale_gps_seconds=60,
        eta_to_pickup_seconds=straight_eta,
        candidate_max_eta_minutes=20,
        pickup_window_minutes=10,
        requested_time=NOW,
        pickup_at=NOW,
        direction=Direction.to_office,
        office_id=OFFICE_ID,
        employee_is_vip=False,
        request_no_sharing=False,
        lock_vehicle_id=None,
        enroute_reuse_max_eta_minutes=5,
        trip_direction=Direction.to_office,
        trip_office_id=OFFICE_ID,
        trip_has_other_riders=True,
    )
    insertion = Insertion(
        plan=Plan(order=(), stops=(), ride_seconds={}, total_seconds=0.0),
        position=0,
        added_minutes={},
        slot_detour_seconds=slot_detour,
    )
    return check_hard_rules(facts, insertion)


def test_the_ceiling_follows_the_detour_not_the_distance() -> None:
    far_but_on_the_way = rule_verdict(slot_detour=0.0, straight_eta=15 * 60)
    near_but_off_route = rule_verdict(slot_detour=8 * 60, straight_eta=60)

    assert Violation.enroute_reuse_eta_exceeded not in far_but_on_the_way
    assert Violation.enroute_reuse_eta_exceeded in near_but_off_route


def test_with_no_detour_figure_the_straight_eta_still_decides() -> None:
    assert Violation.enroute_reuse_eta_exceeded in rule_verdict(None, 12 * 60)
    assert Violation.enroute_reuse_eta_exceeded not in rule_verdict(None, 60)
