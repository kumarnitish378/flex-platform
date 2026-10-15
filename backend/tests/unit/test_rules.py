"""Hard rules as a filter, and the reasons behind a drop (B21).

The behaviour that matters here is the pair: Phase 1's reporting must survive untouched
(ADR-0011 - a supervisor overriding a rule is the point of manual mode), while automatic
paths get a filter that never trades a rule against cost.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.domain.dispatch import Violation
from app.domain.rules import (
    CONFIG_KEY_FOR,
    NEVER_WAIVABLE,
    assignable,
    explain,
    filter_assignable,
    waivable,
)


@dataclass(frozen=True)
class FakeCandidate:
    name: str
    violations: tuple[Violation, ...] = ()


def violations_of(candidate: FakeCandidate) -> tuple[Violation, ...]:
    return candidate.violations


# --- the filter ---------------------------------------------------------------


def test_a_clean_candidate_is_assignable() -> None:
    assert assignable([]) is True


def test_any_violation_makes_a_candidate_unassignable() -> None:
    """§2: filters, never traded off in the cost. One breach is enough."""
    assert assignable([Violation.office_mismatch]) is False


def test_filter_keeps_the_clean_and_explains_the_dropped() -> None:
    clean = FakeCandidate("clean")
    far = FakeCandidate("far", (Violation.eta_over_candidate_limit,))
    wrong_office = FakeCandidate("wrong-office", (Violation.office_mismatch,))

    kept, dropped = filter_assignable([clean, far, wrong_office], violations_of)

    assert kept == [clean]
    assert [candidate.name for candidate, _ in dropped] == ["far", "wrong-office"]


def test_a_dropped_candidate_names_the_config_key_that_excluded_it() -> None:
    """ "No vehicle available" is what makes an operator distrust the system.

    "Every cab is over candidate_max_eta_minutes" is something they can act on - by
    raising the number, or by accepting that the fleet is in the wrong place.
    """
    far = FakeCandidate("far", (Violation.eta_over_candidate_limit,))

    _, dropped = filter_assignable([far], violations_of)
    _, breaches = dropped[0]

    assert breaches[0].config_key == "candidate_max_eta_minutes"
    assert "candidate_max_eta_minutes" in breaches[0].summary


def test_every_violation_has_a_decided_config_key() -> None:
    """Including the structural ones, which are explicitly `None` rather than missing.

    A rule added later without a decision here would silently explain nothing.
    """
    assert set(CONFIG_KEY_FOR) == set(Violation)


# --- what a supervisor may and may not waive ---------------------------------


def test_an_unavailable_vehicle_can_never_be_waived() -> None:
    """There is no driver to send. Nothing for a supervisor to be braver about."""
    assert waivable([Violation.vehicle_unavailable]) is False


def test_a_lock_can_never_be_waived() -> None:
    """control-model.md §3 rule 1: overridden and locked items stay fixed.

    Waiving this would let one supervisor silently undo another's explicit override.
    """
    assert waivable([Violation.locked_to_other_vehicle]) is False


@pytest.mark.parametrize(
    "violation",
    sorted(set(Violation) - NEVER_WAIVABLE, key=str),
)
def test_every_other_rule_is_waivable_with_a_reason(violation: Violation) -> None:
    """ADR-0011: manual assignment reports and applies anyway. That must keep working."""
    assert waivable([violation]) is True


def test_nothing_to_waive_is_waivable() -> None:
    assert waivable([]) is True


def test_a_mix_is_only_waivable_if_every_rule_is() -> None:
    assert waivable([Violation.office_mismatch, Violation.vehicle_unavailable]) is False


# --- Phase 1 behaviour is untouched ------------------------------------------


def test_explain_reports_without_dropping() -> None:
    """The reporting half of ADR-0011: every violation, nothing filtered."""
    breaches = explain([Violation.detour_factor_exceeded, Violation.pickup_window_missed])

    assert [breach.rule for breach in breaches] == [
        Violation.detour_factor_exceeded,
        Violation.pickup_window_missed,
    ]
    assert [breach.config_key for breach in breaches] == [
        "max_detour_factor",
        "pickup_window_minutes",
    ]


def test_capacity_is_absent_from_the_rule_set_on_purpose() -> None:
    """ADR-0011: the dispatch service refuses on capacity rather than reporting it.

    If capacity ever appears in `Violation` it becomes waivable by default, and a fifth
    passenger in a four-seat car stops being a refusal and becomes a judgement call.
    """
    assert not any("capacity" in str(violation) for violation in Violation)


def test_every_named_config_key_actually_exists() -> None:
    """A typo here points a supervisor at a setting that is not there.

    `CONFIG_KEY_FOR` exists so a dropped candidate can say which number excluded it.
    The string is shown to a human and used to deep-link the admin screen, so a key
    that does not exist is worse than no key at all - it reads as a real setting
    nobody can find.
    """
    from app.domain import config_keys

    registry = config_keys.defaults()
    named = {key for key in CONFIG_KEY_FOR.values() if key is not None}

    missing = sorted(key for key in named if key not in registry)
    assert not missing, f"CONFIG_KEY_FOR names config keys that do not exist: {missing}"
