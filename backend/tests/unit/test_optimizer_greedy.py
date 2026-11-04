"""The greedy batch solver, on a flat world where costs can be worked out by hand (B30/B31)."""

from __future__ import annotations

import pytest

from app.domain.dispatch import Place
from app.domain.enums import Direction, Urgency
from app.domain.optimizer import solve
from app.domain.optimizer.greedy import solve_greedy
from tests.unit.optimizer_helpers import (
    minutes_out,
    problem,
    req,
    rid,
    seated,
    trip,
    veh,
)


def placed_on(plan: object, request_n: int) -> object:
    for placement in plan.placements:  # type: ignore[attr-defined]
        if rid(request_n) in placement.new_request_ids:
            return placement.vehicle_id
    return None


def test_an_empty_batch_is_an_empty_plan() -> None:
    plan = solve(problem([], [veh(1, minutes_out(5))]))

    assert plan.empty and not plan.unplaced


def test_one_request_goes_to_the_cab_that_is_cheapest() -> None:
    near, far = veh(1, minutes_out(11)), veh(2, minutes_out(30))

    plan = solve(problem([req(1, minutes_out(10))], [far, near]))

    assert placed_on(plan, 1) == near.vehicle_id
    only = plan.placements[0]
    assert only.pickup_eta_seconds[rid(1)] == pytest.approx(60.0)


def test_two_riders_on_the_same_road_share_one_cab() -> None:
    """Each cab costs 15 to wake; two riders on one road add no detour to each other."""
    cabs = [veh(1, minutes_out(12)), veh(2, minutes_out(12))]
    riders = [req(1, minutes_out(10)), req(2, minutes_out(6))]

    plan = solve(problem(riders, cabs))

    assert len(plan.placements) == 1
    pooled = plan.placements[0]
    assert set(pooled.new_request_ids) == {rid(1), rid(2)}
    # The nearer-to-the-cab rider is collected first: that is the order with no detour.
    assert pooled.order == (rid(1), rid(2))
    assert all(minutes == pytest.approx(0.0) for minutes in pooled.added_minutes.values())


def test_riders_in_opposite_directions_of_travel_do_not_pool_when_it_breaks_the_detour_limit() -> (
    None
):
    """The riders are on opposite sides of the office: either order sends one the long way round."""
    cabs = [veh(1, minutes_out(10)), veh(2, Place(-0.11, 0.0))]
    riders = [req(1, minutes_out(9)), req(2, Place(-0.10, 0.0))]

    plan = solve(problem(riders, cabs))

    assert len(plan.placements) == 2


def test_an_opt_out_rider_rides_alone() -> None:
    cabs = [veh(1, minutes_out(12)), veh(2, minutes_out(12))]
    riders = [req(1, minutes_out(10), no_sharing=True), req(2, minutes_out(6))]

    plan = solve(problem(riders, cabs))

    assert len(plan.placements) == 2
    assert placed_on(plan, 1) != placed_on(plan, 2)


def test_a_vip_needs_a_vip_vehicle_and_without_one_is_left_unplaced() -> None:
    plan = solve(problem([req(1, minutes_out(10), is_vip=True)], [veh(1, minutes_out(12))]))

    assert plan.empty
    (left,) = plan.unplaced
    assert left.request_id == rid(1)
    assert "vip_needs_vip_vehicle" in left.reasons


def test_a_vip_takes_the_vip_vehicle_alone() -> None:
    vip_cab = veh(1, minutes_out(12), vehicle_type="vip")
    plan = solve(
        problem(
            [req(1, minutes_out(10), is_vip=True), req(2, minutes_out(8))],
            [vip_cab, veh(2, minutes_out(40))],
        )
    )

    assert placed_on(plan, 1) == vip_cab.vehicle_id
    assert placed_on(plan, 2) != vip_cab.vehicle_id


def test_a_lock_pins_the_request_to_its_vehicle() -> None:
    pinned = veh(1, minutes_out(15))
    nearer = veh(2, minutes_out(11))

    plan = solve(
        problem([req(1, minutes_out(10), lock_vehicle_id=pinned.vehicle_id)], [nearer, pinned])
    )

    assert placed_on(plan, 1) == pinned.vehicle_id


def test_a_lock_to_an_unusable_vehicle_leaves_the_request_unplaced_not_reassigned() -> None:
    pinned = veh(1, minutes_out(11), status="out_of_service")
    other = veh(2, minutes_out(11))

    plan = solve(
        problem([req(1, minutes_out(10), lock_vehicle_id=pinned.vehicle_id)], [pinned, other])
    )

    assert plan.empty


def test_a_cab_never_carries_more_than_its_seats() -> None:
    cab = veh(1, minutes_out(12), seats=2)
    riders = [req(n, minutes_out(10 - n)) for n in (1, 2, 3)]

    plan = solve(problem(riders, [cab]))

    assert len(plan.placements[0].order) == 2
    assert len(plan.unplaced) == 1


def test_a_request_outside_its_pickup_window_is_not_placed() -> None:
    """Asked for in 40 minutes, a cab 1 minute away would be 39 minutes early (rule 8)."""
    plan = solve(
        problem([req(1, minutes_out(10), requested_in_minutes=40)], [veh(1, minutes_out(11))])
    )

    assert plan.empty
    assert "pickup_window_missed" in plan.unplaced[0].reasons


def test_a_cab_beyond_the_candidate_ceiling_is_not_used() -> None:
    plan = solve(problem([req(1, minutes_out(10))], [veh(1, minutes_out(60))]))

    assert plan.empty
    assert "eta_over_candidate_limit" in plan.unplaced[0].reasons


def test_a_stale_cab_is_never_used() -> None:
    plan = solve(problem([req(1, minutes_out(10))], [veh(1, minutes_out(11), gps_age_seconds=900)]))

    assert plan.empty
    assert "gps_stale" in plan.unplaced[0].reasons


def test_a_blocked_trip_takes_no_one() -> None:
    riding = seated(9, minutes_out(20))
    blocked = veh(
        1,
        minutes_out(30),
        status="on_trip",
        trip=trip(1, [riding], pooling_blocked=True),
    )

    plan = solve(problem([req(1, minutes_out(10))], [blocked]))

    assert plan.empty
    assert "pooling_blocked" in plan.unplaced[0].reasons


def test_a_trip_passing_the_rider_takes_them_without_moving_the_existing_riders() -> None:
    existing = seated(9, minutes_out(20))
    on_the_way = veh(1, minutes_out(25), status="on_trip", trip=trip(1, [existing]))

    plan = solve(problem([req(1, minutes_out(10), requested_in_minutes=15)], [on_the_way]))

    (placement,) = plan.placements
    assert placement.trip_id == on_the_way.trip.trip_id  # type: ignore[union-attr]
    assert placement.order == (rid(9), rid(1))
    assert not placement.reorders_existing


def test_a_from_office_trip_that_has_left_the_office_takes_no_one() -> None:
    gone = veh(
        1,
        minutes_out(5),
        status="on_trip",
        trip=trip(
            1,
            [seated(9, minutes_out(10), picked_up=True)],
            direction=Direction.from_office,
            pickups_done=True,
        ),
    )

    plan = solve(problem([req(1, minutes_out(8), direction=Direction.from_office)], [gone]))

    assert plan.empty


def test_a_higher_priority_rider_gets_the_only_cab() -> None:
    cab = veh(1, minutes_out(12), seats=1)
    plan = solve(
        problem(
            [
                req(1, minutes_out(10), priority=9, urgency=Urgency.low),
                req(2, minutes_out(10), priority=1, urgency=Urgency.high),
            ],
            [cab],
        )
    )

    assert placed_on(plan, 2) == cab.vehicle_id
    assert plan.unplaced[0].request_id == rid(1)


def test_the_same_problem_always_gives_the_same_plan() -> None:
    cabs = [veh(n, minutes_out(10 + n)) for n in range(1, 5)]
    riders = [req(n, minutes_out(2 * n)) for n in range(1, 7)]

    first = solve(problem(riders, cabs))
    second = solve(problem(list(reversed(riders)), list(reversed(cabs))))

    assert first == second


def test_greedy_can_be_restricted_to_a_subset_of_the_batch() -> None:
    plan = solve_greedy(
        problem([req(1, minutes_out(10)), req(2, minutes_out(20))], [veh(1, minutes_out(11))]),
        only=frozenset({rid(2)}),
    )

    assert plan.placed_ids == {rid(2)}


def test_stop_dwell_is_charged_to_everyone_aboard() -> None:
    """The first rider sits through the second's boarding: that minute is added ride time."""
    from app.domain.cost import CostWeights
    from app.domain.optimizer.model import OptimizerParams

    cabs = [veh(1, minutes_out(12))]
    riders = [req(1, minutes_out(10)), req(2, minutes_out(6))]
    params = OptimizerParams(weights=CostWeights(), dwell_seconds=60)

    plan = solve(problem(riders, cabs, params=params))

    pooled = plan.placements[0]
    assert pooled.order == (rid(1), rid(2))
    assert pooled.added_minutes[rid(1)] == pytest.approx(2.0)
