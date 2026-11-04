"""`control-model.md` §5: when to suggest taking a scope off automation (B35)."""

from __future__ import annotations

from app.domain.mode_prompts import (
    PromptCondition,
    PromptThresholds,
    ScopeWindow,
    evaluate,
)

T = PromptThresholds()


def conditions(window: ScopeWindow, thresholds: PromptThresholds = T) -> set[PromptCondition]:
    return {found.condition for found in evaluate(window, thresholds)}


def test_a_quiet_scope_raises_nothing() -> None:
    assert evaluate(ScopeWindow(), T) == []
    healthy = ScopeWindow(
        decided_suggestions=10,
        rejected_suggestions=1,
        eta_errors_minutes=(1.0, 2.0, 3.0, 2.0, 1.0),
        pending_now=4,
        pending_normal=4.0,
        fleet_size=10,
        fleet_degraded=1,
    )
    assert evaluate(healthy, T) == []


def test_rejected_suggestions_raise_it_at_thirty_percent_and_not_below() -> None:
    at = ScopeWindow(decided_suggestions=10, rejected_suggestions=3)
    below = ScopeWindow(decided_suggestions=10, rejected_suggestions=2)

    assert conditions(at) == {PromptCondition.suggestions_rejected}
    assert conditions(below) == set()


def test_eta_error_is_a_median_so_one_terrible_trip_does_not_raise_it() -> None:
    steady = ScopeWindow(eta_errors_minutes=(2.0, 3.0, 2.0, 90.0, 3.0))
    drifting = ScopeWindow(eta_errors_minutes=(11.0, 12.0, 14.0, 3.0, 20.0))

    assert conditions(steady) == set()
    assert conditions(drifting) == {PromptCondition.eta_error}


def test_eta_error_must_exceed_ten_minutes_not_merely_reach_it() -> None:
    assert conditions(ScopeWindow(eta_errors_minutes=(10.0,) * 5)) == set()


def test_a_surge_is_more_than_twice_normal_for_the_slot() -> None:
    surging = ScopeWindow(pending_now=21, pending_normal=10.0)
    exactly_double = ScopeWindow(pending_now=20, pending_normal=10.0)

    assert conditions(surging) == {PromptCondition.pending_surge}
    assert conditions(exactly_double) == set()


def test_no_history_means_no_surge_rather_than_a_surge_from_the_first_request() -> None:
    assert conditions(ScopeWindow(pending_now=30, pending_normal=None)) == set()
    assert conditions(ScopeWindow(pending_now=30, pending_normal=0.0)) == set()


def test_a_fifth_of_the_fleet_stale_or_out_of_service_raises_it() -> None:
    assert conditions(ScopeWindow(fleet_size=10, fleet_degraded=2)) == {
        PromptCondition.fleet_degraded
    }
    assert conditions(ScopeWindow(fleet_size=10, fleet_degraded=1)) == set()


def test_a_tiny_fleet_is_judged_on_its_size_not_on_a_sample_count() -> None:
    assert conditions(ScopeWindow(fleet_size=2, fleet_degraded=1)) == {
        PromptCondition.fleet_degraded
    }


def test_a_percentage_of_too_few_decisions_is_not_a_signal() -> None:
    assert conditions(ScopeWindow(decided_suggestions=1, rejected_suggestions=1)) == set()
    assert conditions(ScopeWindow(eta_errors_minutes=(30.0, 30.0))) == set()
    assert conditions(ScopeWindow(pending_now=3, pending_normal=0.5)) == set()


def test_each_condition_raises_on_its_own_and_reports_the_number() -> None:
    every = ScopeWindow(
        decided_suggestions=10,
        rejected_suggestions=5,
        eta_errors_minutes=(15.0,) * 5,
        pending_now=30,
        pending_normal=10.0,
        fleet_size=10,
        fleet_degraded=4,
    )

    found = {item.condition: item for item in evaluate(every, T)}

    assert set(found) == set(PromptCondition)
    assert found[PromptCondition.suggestions_rejected].observed == 0.5
    assert found[PromptCondition.pending_surge].observed == 3.0
    assert found[PromptCondition.fleet_degraded].as_dict()["threshold"] == 0.2


def test_the_thresholds_are_the_operators_not_constants() -> None:
    strict = PromptThresholds(rejected_share=0.10, min_samples=2)

    assert conditions(ScopeWindow(decided_suggestions=10, rejected_suggestions=1), strict) == {
        PromptCondition.suggestions_rejected
    }
