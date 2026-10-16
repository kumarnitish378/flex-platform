"""The failsafe decision, branch by branch (`control-model.md` §4, B25).

Every branch is reached by moving a clock value, never by sleeping - which is the point
of keeping the decision pure and is what lets the simulator drive it.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.enums import Urgency
from app.domain.failsafe import (
    FailsafeAction,
    FailsafeOutcome,
    decide,
    timeout_for,
)

OFFERED = datetime(2026, 10, 16, 7, 0, tzinfo=UTC)
TIMEOUT = timedelta(seconds=180)


def at(seconds: float) -> datetime:
    return OFFERED + timedelta(seconds=seconds)


# --- how long a supervisor gets -----------------------------------------------


def test_an_ordinary_request_gets_the_configured_timeout() -> None:
    assert timeout_for(180, urgency=Urgency.medium, is_vip=False) == timedelta(seconds=180)


@pytest.mark.parametrize(
    ("urgency", "vip"),
    [(Urgency.high, False), (Urgency.medium, True), (Urgency.high, True)],
)
def test_vip_and_high_urgency_get_half(urgency: Urgency, vip: bool) -> None:
    """§4. The people least able to wait get the least waiting."""
    assert timeout_for(180, urgency=urgency, is_vip=vip) == timedelta(seconds=90)


def test_low_urgency_is_not_shortened() -> None:
    assert timeout_for(180, urgency=Urgency.low, is_vip=False) == timedelta(seconds=180)


# --- waiting ------------------------------------------------------------------


def test_before_the_deadline_it_waits() -> None:
    decision = decide(
        offered_at=OFFERED,
        now=at(60),
        timeout=TIMEOUT,
        action=FailsafeAction.auto_assign,
        already_escalated=False,
    )

    assert decision.outcome is FailsafeOutcome.wait
    assert decision.next_due_at == at(180)


def test_exactly_on_the_deadline_it_fires() -> None:
    """A timer that needs one more second to mean anything is a timer nobody trusts."""
    decision = decide(
        offered_at=OFFERED,
        now=at(180),
        timeout=TIMEOUT,
        action=FailsafeAction.auto_assign,
        already_escalated=False,
    )

    assert decision.outcome is FailsafeOutcome.assign


# --- auto_assign ---------------------------------------------------------------


def test_auto_assign_assigns_on_the_first_timeout() -> None:
    decision = decide(
        offered_at=OFFERED,
        now=at(200),
        timeout=TIMEOUT,
        action=FailsafeAction.auto_assign,
        already_escalated=False,
    )

    assert decision.outcome is FailsafeOutcome.assign
    assert decision.next_due_at is None


# --- escalate ------------------------------------------------------------------


def test_escalate_alerts_first_and_keeps_the_offer_open() -> None:
    decision = decide(
        offered_at=OFFERED,
        now=at(200),
        timeout=TIMEOUT,
        action=FailsafeAction.escalate,
        already_escalated=False,
    )

    assert decision.outcome is FailsafeOutcome.escalate
    # One more timeout before it assigns.
    assert decision.next_due_at == at(360)


def test_escalate_assigns_on_the_second_timeout() -> None:
    """§4: "repeat once after another timeout, then auto-assign".

    An escalation that never resolves is just a slower way of leaving the rider standing.
    """
    decision = decide(
        offered_at=OFFERED,
        now=at(400),
        timeout=TIMEOUT,
        action=FailsafeAction.escalate,
        already_escalated=True,
    )

    assert decision.outcome is FailsafeOutcome.assign
    assert decision.next_due_at is None


def test_an_escalated_offer_still_waits_until_its_second_deadline() -> None:
    decision = decide(
        offered_at=OFFERED,
        now=at(100),
        timeout=TIMEOUT,
        action=FailsafeAction.escalate,
        already_escalated=True,
    )

    assert decision.outcome is FailsafeOutcome.wait


# --- nobody watching ------------------------------------------------------------


def test_with_no_supervisor_watching_the_failsafe_applies_at_once() -> None:
    """§4. Waiting out a timer for an answer nobody is there to give just delays the rider."""
    decision = decide(
        offered_at=OFFERED,
        now=at(5),
        timeout=TIMEOUT,
        action=FailsafeAction.auto_assign,
        already_escalated=False,
        supervisor_online=False,
    )

    assert decision.outcome is FailsafeOutcome.assign
    assert "no supervisor" in decision.why


def test_with_nobody_watching_escalate_still_escalates_first() -> None:
    """Skipping straight to assigning would lose the alert an absent team needs most."""
    decision = decide(
        offered_at=OFFERED,
        now=at(5),
        timeout=TIMEOUT,
        action=FailsafeAction.escalate,
        already_escalated=False,
        supervisor_online=False,
    )

    assert decision.outcome is FailsafeOutcome.escalate


def test_a_watching_supervisor_gets_their_full_timeout() -> None:
    """The safe default, and why `supervisor_online` defaults to True (OQ-37).

    Assuming nobody is there would auto-assign instantly in every semi-auto scope -
    which is full-auto wearing semi-auto's name.
    """
    decision = decide(
        offered_at=OFFERED,
        now=at(5),
        timeout=TIMEOUT,
        action=FailsafeAction.auto_assign,
        already_escalated=False,
    )

    assert decision.outcome is FailsafeOutcome.wait
