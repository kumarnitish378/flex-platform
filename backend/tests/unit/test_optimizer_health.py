"""When the optimizer counts as down (B36, `control-model.md` §6)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.domain.optimizer_health import HealthThresholds, RunFact, Unavailable, assess

NOW = datetime(2026, 10, 16, 8, 0, tzinfo=UTC)
T = HealthThresholds()


def run(minutes_ago: float, *, failed: bool) -> RunFact:
    return RunFact(NOW - timedelta(minutes=minutes_ago), failed)


def test_no_runs_and_nothing_waiting_is_healthy() -> None:
    assert assess([], None, NOW, T).available


def test_one_failure_is_a_blip_not_an_outage() -> None:
    assert assess([run(1, failed=True), run(2, failed=False)], None, NOW, T).available


def test_the_last_three_runs_all_failing_is_down() -> None:
    health = assess([run(1, failed=True), run(2, failed=True), run(3, failed=True)], None, NOW, T)

    assert not health.available
    assert health.reason is Unavailable.solver_failing
    assert health.since == NOW - timedelta(minutes=3)


def test_a_success_among_the_last_three_means_it_is_working() -> None:
    runs = [run(1, failed=True), run(2, failed=False), run(3, failed=True)]

    assert assess(runs, None, NOW, T).available


def test_old_failures_say_nothing_about_now() -> None:
    long_ago = [run(60, failed=True), run(61, failed=True), run(62, failed=True)]

    assert assess(long_ago, None, NOW, T).available


def test_a_request_ready_for_ages_with_no_run_since_means_nothing_is_running() -> None:
    health = assess([], NOW - timedelta(minutes=5), NOW, T)

    assert not health.available and health.reason is Unavailable.not_running
    assert health.since == NOW - timedelta(minutes=5)


def test_a_run_since_the_request_became_ready_means_it_is_running() -> None:
    """It ran and placed nothing: that is an answer, not an outage."""
    ready = NOW - timedelta(minutes=5)

    assert assess([run(1, failed=False)], ready, NOW, T).available


def test_a_run_from_before_the_request_became_ready_does_not_count() -> None:
    ready = NOW - timedelta(minutes=5)

    assert not assess([run(10, failed=False)], ready, NOW, T).available


def test_a_request_that_has_only_just_become_ready_is_not_stalled() -> None:
    assert assess([], NOW - timedelta(seconds=179), NOW, T).available
    assert not assess([], NOW - timedelta(seconds=180), NOW, T).available


def test_a_paused_operator_is_healthy_by_definition() -> None:
    down = [run(1, failed=True), run(2, failed=True), run(3, failed=True)]

    assert assess(down, NOW - timedelta(hours=1), NOW, T, paused=True).available


def test_the_thresholds_are_the_operators() -> None:
    strict = HealthThresholds(failure_threshold=1)

    assert not assess([run(1, failed=True)], None, NOW, strict).available


def test_a_worker_that_died_after_a_good_run_is_noticed_once_that_run_is_old() -> None:
    ready = NOW - timedelta(minutes=10)

    assert assess([run(1, failed=False)], ready, NOW, T).available
    gone = assess([run(4, failed=False)], ready, NOW, T)

    assert not gone.available and gone.reason is Unavailable.not_running


def test_resuming_after_a_long_pause_is_not_an_outage() -> None:
    """The queue is old and nothing has run for an hour - because automation was paused and
    the sweep said so with a marker run. The marker is a run."""
    ready = NOW - timedelta(hours=1)

    assert assess([run(0.2, failed=False)], ready, NOW, T).available
