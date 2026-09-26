"""Checking a run against what its scenario promised (M05, `scenarios.md`).

Pure: takes the metrics a run produced and the assertions its scenario declared, and
returns the failures. Separate from the CLI so the same check runs in a test, and separate
from the metrics so "what happened" and "what was supposed to happen" cannot quietly
become the same statement.

An assertion that was **not measured** fails rather than passes. A scenario asking for
"p90 wait under 30 minutes" on a run that never measured waits has not been satisfied; it
has been skipped, and a green tick there is worse than a red one.
"""

from __future__ import annotations

from dataclasses import dataclass

from sim.metrics import RunMetrics
from sim.scenario import Assertions


@dataclass(frozen=True, slots=True)
class Failure:
    """One broken promise, phrased so the run log says what to look at."""

    check: str
    detail: str

    def __str__(self) -> str:
        return f"{self.check}: {self.detail}"


def evaluate(assertions: Assertions, metrics: RunMetrics) -> list[Failure]:
    """Every assertion the run did not satisfy. Empty means the scenario passed."""
    failures: list[Failure] = []

    if assertions.all_requests_terminal:
        unresolved = metrics.demand.unresolved
        if unresolved is None:
            failures.append(Failure("all_requests_terminal", "no demand was measured in this run"))
        elif unresolved > 0:
            failures.append(
                Failure(
                    "all_requests_terminal",
                    f"{unresolved} request(s) were still open when the run ended",
                )
            )

    if assertions.p90_wait_minutes_max is not None:
        p90 = metrics.demand.wait_minutes_p90
        if p90 is None:
            failures.append(Failure("p90_wait_minutes_max", "no waits were measured"))
        elif p90 > assertions.p90_wait_minutes_max:
            failures.append(
                Failure(
                    "p90_wait_minutes_max",
                    f"p90 wait was {p90:.1f} min, limit {assertions.p90_wait_minutes_max}",
                )
            )

    if assertions.gave_up_max is not None:
        gave_up = metrics.demand.gave_up
        if gave_up is None:
            failures.append(Failure("gave_up_max", "give-ups were not measured"))
        elif gave_up > assertions.gave_up_max:
            failures.append(
                Failure("gave_up_max", f"{gave_up} riders gave up, limit {assertions.gave_up_max}")
            )

    if assertions.invalid_transitions is not None and (
        metrics.integrity.invalid_transitions > assertions.invalid_transitions
    ):
        failures.append(
            Failure(
                "invalid_transitions",
                f"{metrics.integrity.invalid_transitions} invalid transitions",
            )
        )

    if assertions.api_5xx_max is not None and metrics.integrity.api_5xx > assertions.api_5xx_max:
        failures.append(Failure("api_5xx_max", f"{metrics.integrity.api_5xx} server errors"))

    return failures
