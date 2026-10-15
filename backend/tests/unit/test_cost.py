"""The cost function, against the worked example the spec ships (B22).

`allocation-rules.md` §8 states two costs to one decimal place. Those two numbers are
the specification; if this file and that section ever disagree, one of them is wrong and
it matters which, so the example is reproduced here exactly rather than paraphrased.
"""

from __future__ import annotations

import uuid

import pytest

from app.domain.cost import (
    CostInput,
    CostWeights,
    ExistingRider,
    assignment_cost,
    ranking_key,
    rider_weight,
)
from app.domain.enums import Urgency

WEIGHTS = CostWeights()

VEHICLE_A = uuid.UUID(int=1)
VEHICLE_B = uuid.UUID(int=2)
RIDER_X = uuid.UUID(int=10)


# --- rider weight ------------------------------------------------------------


@pytest.mark.parametrize(
    ("priority", "urgency", "expected"),
    [
        # The three examples in `allocation-rules.md` §4, Rider weight.
        (1, Urgency.high, 3.0),
        (5, Urgency.medium, 0.9),
        (10, Urgency.low, 0.1),
    ],
)
def test_rider_weight_matches_the_documented_examples(
    priority: int, urgency: Urgency, expected: float
) -> None:
    assert rider_weight(priority, urgency, WEIGHTS) == pytest.approx(expected)


def test_priority_one_is_the_highest() -> None:
    """Inverted by `(11 - priority)`, and getting it backwards is silently plausible.

    A platform that served priority 10 before priority 1 would produce numbers that all
    look reasonable and an operator who cannot understand why their VIPs wait.
    """
    top = rider_weight(1, Urgency.medium, WEIGHTS)
    bottom = rider_weight(10, Urgency.medium, WEIGHTS)
    assert top > bottom


@pytest.mark.parametrize("priority", [0, 11, -1, 100])
def test_priority_outside_the_scale_is_refused(priority: int) -> None:
    """Rather than returning a weight that is merely odd."""
    with pytest.raises(ValueError, match="priority"):
        rider_weight(priority, Urgency.medium, WEIGHTS)


# --- the worked example (`allocation-rules.md` §8) ---------------------------


def test_worked_example_vehicle_a_costs_33_8() -> None:
    """Idle vehicle, ETA 12 min, 4 empty km.

    1.0 x 0.9 x 12 + 0 + 2.0 x 4 + 15 = 10.8 + 8 + 15 = 33.8
    """
    cost = assignment_cost(
        CostInput(
            priority=5,
            urgency=Urgency.medium,
            wait_minutes=12,
            empty_km_added=4,
            new_trip=True,
            vehicle_id=VEHICLE_A,
        ),
        WEIGHTS,
    )

    assert cost.total == pytest.approx(33.8)
    assert cost.wait == pytest.approx(10.8)
    assert cost.empty_km == pytest.approx(8.0)
    assert cost.new_vehicle == pytest.approx(15.0)
    assert cost.detour == pytest.approx(0.0)


def test_worked_example_vehicle_b_costs_13_8() -> None:
    """On a trip with rider X (w = 1.5), ETA 7 min, adds 5 min to X, no empty km.

    0.9 x 7 + 1.5 x 5 + 0 + 0 = 6.3 + 7.5 = 13.8
    """
    cost = assignment_cost(
        CostInput(
            priority=5,
            urgency=Urgency.medium,
            wait_minutes=7,
            empty_km_added=0,
            new_trip=False,
            riders_on_board=(
                # §8 gives X's weight as 1.5 but not their priority or urgency. Only
                # one combination produces it: priority 1 + medium, ((11-1)/10) x 1.5.
                # Priority 5 + high looks plausible and is 1.8, which makes the total
                # 15.3 - close enough to pass an eyeball and fail the spec.
                ExistingRider(
                    request_id=RIDER_X, priority=1, urgency=Urgency.medium, added_minutes=5
                ),
            ),
            vehicle_id=VEHICLE_B,
        ),
        WEIGHTS,
    )

    assert cost.total == pytest.approx(13.8)
    assert cost.wait == pytest.approx(6.3)
    assert cost.detour == pytest.approx(7.5)
    assert cost.detour_by_rider[RIDER_X] == pytest.approx(7.5)
    assert cost.new_vehicle == pytest.approx(0.0)


def test_the_example_chooses_vehicle_b() -> None:
    """The point of §8: reusing a moving cab beats deploying an idle one here."""
    a = assignment_cost(CostInput(5, Urgency.medium, 12, 4, True, vehicle_id=VEHICLE_A), WEIGHTS)
    b = assignment_cost(
        CostInput(
            5,
            Urgency.medium,
            7,
            0,
            False,
            riders_on_board=(ExistingRider(RIDER_X, 1, Urgency.medium, 5),),
            vehicle_id=VEHICLE_B,
        ),
        WEIGHTS,
    )

    assert b.total < a.total


# --- the rules the function must not break -----------------------------------


def test_an_early_pickup_is_not_a_negative_wait() -> None:
    """Otherwise an early cab buys its way past a rider who has actually waited."""
    early = assignment_cost(
        CostInput(5, Urgency.medium, -30, 0, False, vehicle_id=VEHICLE_A), WEIGHTS
    )
    on_time = assignment_cost(
        CostInput(5, Urgency.medium, 0, 0, False, vehicle_id=VEHICLE_A), WEIGHTS
    )

    assert early.total == on_time.total == pytest.approx(0.0)


def test_there_is_no_separate_traffic_term() -> None:
    """`allocation-rules.md` §4: traffic is already inside the ETAs.

    Stated as a test because the mistake is tempting and invisible: adding a traffic
    weight would double-count it and the totals would still look sensible. The check is
    that the four documented terms are the whole of the total.
    """
    cost = assignment_cost(
        CostInput(
            3,
            Urgency.high,
            9,
            2.5,
            True,
            riders_on_board=(ExistingRider(RIDER_X, 2, Urgency.medium, 4),),
            vehicle_id=VEHICLE_A,
        ),
        WEIGHTS,
    )

    assert cost.total == pytest.approx(cost.wait + cost.detour + cost.empty_km + cost.new_vehicle)


def test_deploying_an_idle_vehicle_carries_its_documented_cost() -> None:
    """`cost_new_vehicle` is what stops the platform sending a fresh cab for everyone."""
    idle = assignment_cost(CostInput(5, Urgency.medium, 5, 0, True), WEIGHTS)
    reuse = assignment_cost(CostInput(5, Urgency.medium, 5, 0, False), WEIGHTS)

    assert idle.total - reuse.total == pytest.approx(WEIGHTS.cost_new_vehicle)


def test_every_rider_aboard_is_charged_for_their_own_detour() -> None:
    """Summed over riders, each at their own weight - not an average."""
    quiet = ExistingRider(uuid.UUID(int=20), priority=10, urgency=Urgency.low, added_minutes=6)
    important = ExistingRider(uuid.UUID(int=21), priority=1, urgency=Urgency.high, added_minutes=6)

    cost = assignment_cost(
        CostInput(5, Urgency.medium, 0, 0, False, riders_on_board=(quiet, important)),
        WEIGHTS,
    )

    assert cost.detour_by_rider[quiet.request_id] == pytest.approx(0.1 * 6)
    assert cost.detour_by_rider[important.request_id] == pytest.approx(3.0 * 6)
    assert cost.detour == pytest.approx(0.6 + 18.0)


# --- determinism -------------------------------------------------------------


def test_ties_break_on_eta_then_vehicle_id() -> None:
    """`allocation-rules.md` §4. The simulator replays a seed and expects the same choice.

    A supervisor refreshing the dispatch screen must not see a different top suggestion
    either, which is the version of this that an operator would actually notice.
    """
    same_cost = CostWeights(weight_wait=0.0, weight_empty_km=0.0, cost_new_vehicle=0.0)

    slow = CostInput(
        5, Urgency.medium, 10, 0, True, eta_to_pickup_seconds=600, vehicle_id=VEHICLE_B
    )
    fast = CostInput(
        5, Urgency.medium, 10, 0, True, eta_to_pickup_seconds=120, vehicle_id=VEHICLE_A
    )

    ordered = sorted(
        (slow, fast), key=lambda facts: ranking_key(facts, assignment_cost(facts, same_cost))
    )

    assert ordered[0] is fast


def test_identical_candidates_order_by_vehicle_id() -> None:
    weights = CostWeights(weight_wait=0.0, weight_empty_km=0.0, cost_new_vehicle=0.0)
    second = CostInput(
        5, Urgency.medium, 1, 0, True, eta_to_pickup_seconds=60, vehicle_id=VEHICLE_B
    )
    first = CostInput(5, Urgency.medium, 1, 0, True, eta_to_pickup_seconds=60, vehicle_id=VEHICLE_A)

    ordered = sorted(
        (second, first), key=lambda facts: ranking_key(facts, assignment_cost(facts, weights))
    )

    assert [facts.vehicle_id for facts in ordered] == [VEHICLE_A, VEHICLE_B]
