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

    if assertions.vip_never_pooled:
        pooled = metrics.demand.vip_pooled
        if pooled is None:
            failures.append(Failure("vip_never_pooled", "no VIP travel was measured in this run"))
        elif pooled > 0:
            failures.append(
                Failure(
                    "vip_never_pooled",
                    f"{pooled} VIP rider(s) shared a cab with someone else",
                )
            )

    if assertions.failsafe_assignments_min is not None:
        fired = metrics.dispatch.failsafe_assignments
        if fired < assertions.failsafe_assignments_min:
            failures.append(
                Failure(
                    "failsafe_assignments_min",
                    f"the failsafe assigned {fired} time(s), expected at least "
                    f"{assertions.failsafe_assignments_min} - a semi-auto run that never "
                    "engaged passes everything else by doing nothing",
                )
            )

    if assertions.locks_respected:
        placed = metrics.dispatch.locks_placed
        broken = metrics.dispatch.locks_broken
        if placed == 0:
            failures.append(
                Failure("locks_respected", "no request was locked, so nothing was checked")
            )
        elif broken > 0:
            failures.append(
                Failure(
                    "locks_respected",
                    f"{broken} of {placed} locked request(s) rode in a different cab",
                )
            )

    if assertions.acceptance_rate_min is not None:
        rate = metrics.dispatch.acceptance_rate
        if rate is None:
            failures.append(Failure("acceptance_rate_min", "no offer was answered by a supervisor"))
        elif rate < assertions.acceptance_rate_min:
            failures.append(
                Failure(
                    "acceptance_rate_min",
                    f"acceptance was {rate:.0%}, floor {assertions.acceptance_rate_min:.0%}",
                )
            )

    if assertions.riders_per_trip_min is not None:
        value = metrics.pooling.riders_per_trip
        if value is None:
            failures.append(Failure("riders_per_trip_min", "no trip carried anyone"))
        elif value < assertions.riders_per_trip_min:
            failures.append(
                Failure(
                    "riders_per_trip_min",
                    f"{value:.2f} riders per trip, floor {assertions.riders_per_trip_min}",
                )
            )

    if assertions.vehicles_used_max is not None:
        used = metrics.pooling.vehicles_used
        if used is None:
            failures.append(Failure("vehicles_used_max", "no cab carried anyone"))
        elif used > assertions.vehicles_used_max:
            failures.append(
                Failure(
                    "vehicles_used_max", f"{used} cabs used, limit {assertions.vehicles_used_max}"
                )
            )

    if assertions.detour_over_limit_max is not None:
        over = metrics.pooling.detour_over_limit
        if over is None:
            failures.append(Failure("detour_over_limit_max", "no ride was measured"))
        elif over > assertions.detour_over_limit_max:
            failures.append(
                Failure(
                    "detour_over_limit_max",
                    f"{over} ride(s) exceeded rule 7's detour limit (worst by "
                    f"{metrics.pooling.detour_worst_excess_minutes} min), allowed "
                    f"{assertions.detour_over_limit_max}",
                )
            )

    if assertions.night_safety_violations_max is not None:
        carried = metrics.pooling.night_flagged_carried
        violations = metrics.pooling.night_safety_violations
        if not carried:
            failures.append(
                Failure(
                    "night_safety_violations_max",
                    "no flagged rider was carried, so rule 11 was never exercised",
                )
            )
        elif (violations or 0) > assertions.night_safety_violations_max:
            failures.append(
                Failure(
                    "night_safety_violations_max",
                    f"{violations} pooled trip(s) left a flagged rider alone in the lone "
                    f"position, allowed {assertions.night_safety_violations_max}",
                )
            )

    if assertions.optimizer_assignments_min is not None:
        applied = metrics.optimizer.applied
        if not applied or applied < assertions.optimizer_assignments_min:
            failures.append(
                Failure(
                    "optimizer_assignments_min",
                    f"the optimizer assigned {applied or 0} request(s), expected at least "
                    f"{assertions.optimizer_assignments_min}",
                )
            )

    if assertions.optimizer_outage_handled:
        optimizer = metrics.optimizer
        if optimizer.outage_minutes is None:
            failures.append(Failure("optimizer_outage_handled", "no outage was injected"))
        else:
            if not optimizer.alert_raised:
                failures.append(
                    Failure(
                        "optimizer_outage_handled", "the platform raised no optimizer_down alert"
                    )
                )
            elif not optimizer.alert_resolved:
                failures.append(
                    Failure(
                        "optimizer_outage_handled",
                        "the optimizer_down alert never cleared after the optimizer came back",
                    )
                )
            if (optimizer.applied_while_down or 0) > 0 or (optimizer.suggested_while_down or 0) > 0:
                failures.append(
                    Failure(
                        "optimizer_outage_handled",
                        f"the platform assigned {optimizer.applied_while_down} and offered "
                        f"{optimizer.suggested_while_down} request(s) while the optimizer was down"
                        " - a scope in manual must do neither",
                    )
                )

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
