"""Hard rules as a filter, and what each one came from (`allocation-rules.md` §2, B21).

Phase 1 computed the same violations and **reported** them: manual assignment applies
anyway, because overriding is the point of manual mode (ADR-0011). Phase 2 needs the
other half - automatic paths must drop a candidate that breaks a rule, never weigh it
against cost. §2 is explicit: "filters - never traded off in the cost".

So both behaviours exist side by side, and which one a caller gets is a decision it
makes on purpose:

* `evaluate()` - every violation, nothing dropped. What `/dispatch/candidates` uses, and
  what a supervisor sees. Unchanged from Phase 1.
* `assignable()` / `filter_assignable()` - the filter. What suggestions and the
  optimizer use.

The rules themselves stay in `dispatch.py` where Phase 1 put them, already pure and
already ordered as §2 orders them. Moving them here would be churn: this module adds the
two things §2 needs and `dispatch.py` does not have - the filter, and the config key
behind each rule, so a dropped candidate can say *which number* excluded it rather than
just that something did.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass

from app.domain.dispatch import Violation

#: The config key whose value decides each rule, or `None` where the rule is structural
#: and has no number to tune. A supervisor told "no cab available" learns nothing; told
#: "every cab is over candidate_max_eta_minutes (20)" they know what to change.
CONFIG_KEY_FOR: dict[Violation, str | None] = {
    Violation.vehicle_unavailable: None,
    Violation.gps_stale: "stale_gps_seconds",
    Violation.locked_to_other_vehicle: None,
    Violation.pooling_blocked: None,
    Violation.no_sharing: None,
    Violation.vip_needs_vip_vehicle: None,
    Violation.direction_mismatch: None,
    Violation.office_mismatch: None,
    Violation.detour_factor_exceeded: "max_detour_factor",
    Violation.detour_minutes_exceeded: "max_detour_minutes",
    Violation.pickup_window_missed: "pickup_window_minutes",
    Violation.eta_over_candidate_limit: "candidate_max_eta_minutes",
    Violation.enroute_reuse_eta_exceeded: "enroute_reuse_max_eta_minutes",
}

#: Rules a human may waive with a reason, and rules nobody may (control-model.md §3
#: rule 4 calls the first group "hard-rule overrides" and requires a reason plus a note).
#:
#: Seat capacity is absent from `Violation` entirely and deliberately: the dispatch
#: service refuses on capacity rather than reporting it, so it can never be waived by
#: accident (ADR-0011). Putting a cab's fifth passenger in a four-seat car is not a
#: judgement call.
NEVER_WAIVABLE: frozenset[Violation] = frozenset(
    {
        # A cab that is off duty or out of service has no driver to send. There is
        # nothing for a supervisor to be braver about.
        Violation.vehicle_unavailable,
        # The request is pinned to a different vehicle. Waiving this would silently
        # undo somebody's explicit override (control-model.md §3 rule 1).
        Violation.locked_to_other_vehicle,
    }
)


@dataclass(frozen=True, slots=True)
class RuleBreach:
    """One violation, with the number behind it."""

    rule: Violation
    config_key: str | None
    waivable: bool

    @property
    def summary(self) -> str:
        source = f" ({self.config_key})" if self.config_key else ""
        return f"{self.rule}{source}"


def explain(violations: Iterable[Violation]) -> list[RuleBreach]:
    """Attribute each violation to the config key that set the limit."""
    return [
        RuleBreach(
            rule=violation,
            config_key=CONFIG_KEY_FOR.get(violation),
            waivable=violation not in NEVER_WAIVABLE,
        )
        for violation in violations
    ]


def assignable(violations: Sequence[Violation]) -> bool:
    """True when nothing in §2 forbids this assignment."""
    return not violations


def waivable(violations: Sequence[Violation]) -> bool:
    """True when a supervisor may override every violation present, given a reason.

    An empty list is trivially waivable - there is nothing to waive.
    """
    return all(violation not in NEVER_WAIVABLE for violation in violations)


def filter_assignable[T](
    candidates: Iterable[T], violations_of: Callable[[T], Sequence[Violation]]
) -> tuple[list[T], list[tuple[T, list[RuleBreach]]]]:
    """Split candidates into those §2 permits and those it excludes, with reasons.

    Returns both halves rather than only the survivors, because an empty result has to
    be explainable. "No vehicle available" with nothing behind it is the message that
    makes an operator distrust the system; "all four cabs are over
    candidate_max_eta_minutes" is one they can act on.
    """
    kept: list[T] = []
    dropped: list[tuple[T, list[RuleBreach]]] = []
    for candidate in candidates:
        violations = violations_of(candidate)
        if assignable(violations):
            kept.append(candidate)
        else:
            dropped.append((candidate, explain(violations)))
    return kept, dropped
