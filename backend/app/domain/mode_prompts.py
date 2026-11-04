"""When to suggest taking a scope off automation (`control-model.md` §5, B35).

> The system suggests switching a scope to `manual` (**never switches by itself**) when any
> is true in the last 15 minutes: >= 30% of suggestions rejected in that scope, median ETA
> error > 10 minutes, pending requests > 2x normal for that time slot, >= 20% of vehicles in
> the scope stale or out of service.

§5 says "never switches by itself" and the section above it says the same of the whole
design, so this module cannot switch anything: it takes numbers and returns the conditions
that hold. What a person does about them is a different endpoint behind a different
permission.

**Pure.** The caller measures the last window and supplies the figures; this decides.

**A minimum sample, because a percentage of one is not a signal.** One rejected suggestion
out of one is "100% rejected". §5 gives no minimum, so `min_samples` is a provisional
default (5) recorded in the decision log and held in config, and it applies to the three
conditions that are ratios or medians. The fleet condition is judged on the fleet's size
instead: a two-cab operator losing one cab really is 50% of their fleet.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.stats import median


class PromptCondition(StrEnum):
    suggestions_rejected = "suggestions_rejected"
    eta_error = "eta_error"
    pending_surge = "pending_surge"
    fleet_degraded = "fleet_degraded"


@dataclass(frozen=True, slots=True)
class PromptThresholds:
    """`control-model.md` §5's four numbers, as the operator has them configured."""

    window_minutes: int = 15
    rejected_share: float = 0.30
    eta_error_minutes: float = 10.0
    pending_multiple: float = 2.0
    fleet_share: float = 0.20
    min_samples: int = 5


@dataclass(frozen=True, slots=True)
class ScopeWindow:
    """What one scope looked like over the last window."""

    #: Suggestions a person (or the failsafe) settled in the window.
    decided_suggestions: int = 0
    rejected_suggestions: int = 0
    #: |actual pickup - planned pickup|, in minutes, for pickups completed in the window.
    eta_errors_minutes: tuple[float, ...] = ()
    pending_now: int = 0
    #: What "normal" is for this time slot, or `None` when there is no history to say.
    pending_normal: float | None = None
    fleet_size: int = 0
    fleet_degraded: int = 0


@dataclass(frozen=True, slots=True)
class Observation:
    """One condition that holds, with the number behind it."""

    condition: PromptCondition
    observed: float
    threshold: float
    samples: int

    def as_dict(self) -> dict[str, float | int | str]:
        return {
            "condition": str(self.condition),
            "observed": round(self.observed, 3),
            "threshold": self.threshold,
            "samples": self.samples,
        }


def evaluate(window: ScopeWindow, thresholds: PromptThresholds) -> list[Observation]:
    """Every §5 condition that holds. An empty list means: leave the scope alone."""
    found: list[Observation] = []

    if window.decided_suggestions >= thresholds.min_samples:
        share = window.rejected_suggestions / window.decided_suggestions
        if share >= thresholds.rejected_share:
            found.append(
                Observation(
                    PromptCondition.suggestions_rejected,
                    share,
                    thresholds.rejected_share,
                    window.decided_suggestions,
                )
            )

    if len(window.eta_errors_minutes) >= thresholds.min_samples:
        typical = median(list(window.eta_errors_minutes))
        if typical is not None and typical > thresholds.eta_error_minutes:
            found.append(
                Observation(
                    PromptCondition.eta_error,
                    typical,
                    thresholds.eta_error_minutes,
                    len(window.eta_errors_minutes),
                )
            )

    # No history is not "normal is zero": with nothing to compare against, the condition
    # cannot be judged and does not fire (a new deployment would otherwise be in surge
    # from its first request).
    if (
        window.pending_normal is not None
        and window.pending_normal > 0
        and window.pending_now >= thresholds.min_samples
        and window.pending_now > thresholds.pending_multiple * window.pending_normal
    ):
        found.append(
            Observation(
                PromptCondition.pending_surge,
                window.pending_now / window.pending_normal,
                thresholds.pending_multiple,
                window.pending_now,
            )
        )

    if window.fleet_size > 0:
        share = window.fleet_degraded / window.fleet_size
        if share >= thresholds.fleet_share:
            found.append(
                Observation(
                    PromptCondition.fleet_degraded,
                    share,
                    thresholds.fleet_share,
                    window.fleet_size,
                )
            )

    return found
