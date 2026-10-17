"""When nobody answers a suggestion (`control-model.md` §4, task B25).

Semi-auto's bargain is that a human approves each assignment. The failsafe is what
happens when no human does - because a rider standing outside at 7am is not served by a
suggestion sitting unread on a screen nobody is watching.

Pure. The caller supplies "now" and the configuration; this decides what should happen,
and the service does it. That split is what lets every branch be proved by advancing a
`FakeClock` rather than by sleeping.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from app.domain.enums import Urgency


class FailsafeAction(StrEnum):
    """`failsafe_action` in `operator_config`. OQ-06: which should be the default."""

    auto_assign = "auto_assign"
    escalate = "escalate"


class SuggestionStatus(StrEnum):
    """Where an offer got to.

    `superseded` and `expired` are distinct on purpose. Superseded means the platform
    replaced the offer - the cab it named stopped being usable, so a fresh set was
    computed. Expired means the offer simply ran out of road. Collapsing them would
    make the Phase 2 acceptance metric lie: a supervisor who never saw an offer because
    it was withdrawn has not rejected anything.
    """

    offered = "offered"
    accepted = "accepted"
    rejected = "rejected"
    superseded = "superseded"
    expired = "expired"
    #: The failsafe assigned it because nobody answered in time (§4). **Not**
    #: `accepted`: Phase 2's exit criterion is "suggestion acceptance > 70%", and a
    #: scope where no supervisor ever looked would otherwise score 100% - the platform
    #: agreeing with itself, counted as a human agreeing with the platform. Found in
    #: M09, writing the scenario (S08) whose whole subject is an absent supervisor.
    failsafe_assigned = "failsafe_assigned"


class FailsafeOutcome(StrEnum):
    """What the sweep should do with an offer whose timer has run out."""

    wait = "wait"
    assign = "assign"
    escalate = "escalate"


@dataclass(frozen=True, slots=True)
class FailsafeDecision:
    outcome: FailsafeOutcome
    #: When to look again. `None` when nothing further is due.
    next_due_at: datetime | None = None
    why: str = ""


def timeout_for(base_seconds: int, *, urgency: Urgency | str, is_vip: bool) -> timedelta:
    """How long a supervisor gets to answer.

    `control-model.md` §4: "VIP and high urgency requests use half the timeout." The
    people least able to wait get the least waiting.
    """
    seconds = float(base_seconds)
    if is_vip or Urgency(urgency) is Urgency.high:
        seconds /= 2
    return timedelta(seconds=seconds)


def decide(
    *,
    offered_at: datetime,
    now: datetime,
    timeout: timedelta,
    action: FailsafeAction,
    already_escalated: bool,
    supervisor_online: bool = True,
) -> FailsafeDecision:
    """What to do with an offer that is still unanswered.

    `control-model.md` §4, in order:

    * Before the deadline, wait - unless **no supervisor is watching this scope**, in
      which case the timeout is pointless and the failsafe applies at once.
    * On timeout with `auto_assign`: assign the top suggestion, after the caller
      re-checks the hard rules. This function does not know whether they still hold;
      that is a database question and the caller owns it.
    * On timeout with `escalate`: alert, keep the offer open, and **repeat once**. The
      second timeout assigns. An escalation that never resolves is just a slower way of
      leaving the rider standing.
    """
    deadline = offered_at + timeout

    if now < deadline and supervisor_online:
        return FailsafeDecision(FailsafeOutcome.wait, deadline, "within the timeout")

    if not supervisor_online and now < deadline:
        # §4: "If no supervisor is logged in for a semi_auto scope, failsafe applies
        # immediately." Waiting out a timer for an answer nobody is there to give just
        # delays the rider.
        return FailsafeDecision(
            _on_timeout(action, already_escalated), None, "no supervisor watching"
        )

    outcome = _on_timeout(action, already_escalated)
    if outcome is FailsafeOutcome.escalate:
        # One more timeout, then it assigns.
        return FailsafeDecision(outcome, deadline + timeout, "escalating, then assigning")
    return FailsafeDecision(outcome, None, "timed out")


def _on_timeout(action: FailsafeAction, already_escalated: bool) -> FailsafeOutcome:
    if action is FailsafeAction.auto_assign:
        return FailsafeOutcome.assign
    return FailsafeOutcome.assign if already_escalated else FailsafeOutcome.escalate
