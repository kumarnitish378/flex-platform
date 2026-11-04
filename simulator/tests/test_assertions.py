"""Checking a run against what its scenario promised (M05, `scenarios.md`)."""

from __future__ import annotations

from sim.assertions import evaluate
from sim.metrics import DemandMetrics, IntegrityMetrics, RunMetrics
from sim.scenario import Assertions


def metrics(**overrides: object) -> RunMetrics:
    base = RunMetrics(
        scenario="test",
        seed=1,
        routing="approx",
        started_at="2026-10-05T00:30:00+00:00",
        ended_at="2026-10-05T01:30:00+00:00",
        simulated_hours=1.0,
    )
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


def names(failures: list) -> list[str]:  # type: ignore[type-arg]
    return [failure.check for failure in failures]


# --- all requests terminal (S01) ---------------------------------------------------


def test_a_run_with_nothing_left_open_passes() -> None:
    result = evaluate(
        Assertions(all_requests_terminal=True), metrics(demand=DemandMetrics(unresolved=0))
    )
    assert result == []


def test_an_open_request_fails_the_run() -> None:
    result = evaluate(
        Assertions(all_requests_terminal=True), metrics(demand=DemandMetrics(unresolved=2))
    )
    assert names(result) == ["all_requests_terminal"]
    assert "2 request(s)" in result[0].detail


def test_an_unmeasured_run_fails_rather_than_passes() -> None:
    """A green tick for something never measured is worse than a red one."""
    result = evaluate(Assertions(all_requests_terminal=True), metrics())
    assert names(result) == ["all_requests_terminal"]
    assert "no demand" in result[0].detail


# --- waits and give-ups ---------------------------------------------------------------


def test_a_wait_inside_the_limit_passes() -> None:
    result = evaluate(
        Assertions(p90_wait_minutes_max=30),
        metrics(demand=DemandMetrics(wait_minutes_p90=22.5)),
    )
    assert result == []


def test_a_wait_over_the_limit_fails_with_both_numbers() -> None:
    result = evaluate(
        Assertions(p90_wait_minutes_max=30),
        metrics(demand=DemandMetrics(wait_minutes_p90=41.2)),
    )
    assert names(result) == ["p90_wait_minutes_max"]
    assert "41.2" in result[0].detail
    assert "30" in result[0].detail


def test_give_ups_within_the_budget_pass() -> None:
    assert evaluate(Assertions(gave_up_max=5), metrics(demand=DemandMetrics(gave_up=5))) == []


def test_too_many_give_ups_fail() -> None:
    result = evaluate(Assertions(gave_up_max=2), metrics(demand=DemandMetrics(gave_up=3)))
    assert names(result) == ["gave_up_max"]


# --- integrity ---------------------------------------------------------------------------


def test_an_invalid_transition_fails() -> None:
    result = evaluate(
        Assertions(invalid_transitions=0),
        metrics(integrity=IntegrityMetrics(invalid_transitions=1)),
    )
    assert names(result) == ["invalid_transitions"]


def test_a_server_error_fails() -> None:
    result = evaluate(Assertions(api_5xx_max=0), metrics(integrity=IntegrityMetrics(api_5xx=2)))
    assert names(result) == ["api_5xx_max"]


def test_a_clean_run_against_every_assertion_passes() -> None:
    assertions = Assertions(
        all_requests_terminal=True,
        p90_wait_minutes_max=30,
        gave_up_max=1,
        invalid_transitions=0,
        api_5xx_max=0,
    )
    clean = metrics(demand=DemandMetrics(unresolved=0, wait_minutes_p90=12.0, gave_up=0))

    assert evaluate(assertions, clean) == []


def test_every_broken_promise_is_reported_not_just_the_first() -> None:
    """One run, one list: fixing them one at a time wastes a run each."""
    assertions = Assertions(all_requests_terminal=True, gave_up_max=0, api_5xx_max=0)
    bad = metrics(
        demand=DemandMetrics(unresolved=1, gave_up=4),
        integrity=IntegrityMetrics(api_5xx=1),
    )

    assert len(evaluate(assertions, bad)) == 3


def test_a_scenario_that_promises_nothing_cannot_fail() -> None:
    assert evaluate(Assertions(), metrics()) == []


def test_a_failure_reads_as_a_sentence() -> None:
    result = evaluate(Assertions(gave_up_max=0), metrics(demand=DemandMetrics(gave_up=7)))
    assert str(result[0]).startswith("gave_up_max: ")
