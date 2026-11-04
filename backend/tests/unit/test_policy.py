"""Operator config combined with one client's policy (`allocation-rules.md` §1, B28)."""

from __future__ import annotations

from datetime import time
from typing import Any

import pytest

from app.domain.config_keys import STRICTER_ONLY_KEYS, defaults
from app.domain.policy import ClientPolicyValues, resolve, stricter_of


def operator(**overrides: Any) -> dict[str, Any]:
    values = defaults()
    values.update(overrides)
    return values


# --- rule 7: the stricter value, proved both ways ----------------------------------


def test_a_client_may_tighten_the_detour_limits() -> None:
    effective = resolve(
        operator(max_detour_factor=1.6, max_detour_minutes=20),
        ClientPolicyValues(max_detour_factor=1.2, max_detour_minutes=10),
    )
    assert effective.max_detour_factor == 1.2
    assert effective.max_detour_minutes == 10


def test_a_client_cannot_loosen_the_detour_limits() -> None:
    """The other direction, which is the one a client would actually try."""
    effective = resolve(
        operator(max_detour_factor=1.4, max_detour_minutes=15),
        ClientPolicyValues(max_detour_factor=2.5, max_detour_minutes=45),
    )
    assert effective.max_detour_factor == 1.4
    assert effective.max_detour_minutes == 15


def test_a_client_with_no_policy_gets_the_operators_numbers() -> None:
    """Every client today, and every client throughout Phase 1."""
    values = operator(max_detour_factor=1.7, pickup_window_minutes=12)
    effective = resolve(values)
    assert effective.max_detour_factor == 1.7
    assert effective.pickup_window_minutes == 12


def test_the_registry_decides_which_keys_are_stricter_only() -> None:
    """Not a list restated in `policy.py`, or the two could drift apart."""
    assert {"max_detour_factor", "max_detour_minutes"} == STRICTER_ONLY_KEYS


def test_a_zero_override_is_kept_not_treated_as_unset() -> None:
    """`client_value or operator_value` reads naturally and loses a legitimate zero."""
    assert stricter_of(10.0, 0.0) == 0.0
    assert stricter_of(10.0, None) == 10.0


# --- the keys a client may set either way --------------------------------------------


def test_a_client_may_widen_their_own_pickup_window() -> None:
    """Not stricter-only in the registry: how long *their* people will wait at the
    kerb is the client's call, not the operator's."""
    effective = resolve(
        operator(pickup_window_minutes=10), ClientPolicyValues(pickup_window_minutes=25)
    )
    assert effective.pickup_window_minutes == 25


def test_a_client_may_ask_the_driver_to_wait_longer_before_a_no_show() -> None:
    effective = resolve(
        operator(no_show_wait_minutes=5), ClientPolicyValues(no_show_wait_minutes=12)
    )
    assert effective.no_show_wait_minutes == 12


def test_opting_out_of_sharing_is_allowed_until_a_client_forbids_it() -> None:
    """The asymmetry with night safety is deliberate. Night safety is a protection, so
    silence must not switch it off; opting out is a permission Phase 1 already granted
    with no gate, so silence must not revoke it. Both default towards the rider."""
    assert resolve(operator()).employee_opt_out_allowed is True
    assert (
        resolve(
            operator(), ClientPolicyValues(employee_opt_out_allowed=False)
        ).employee_opt_out_allowed
        is False
    )


# --- night safety is a floor ----------------------------------------------------------


@pytest.mark.parametrize(
    ("by_operator", "by_client", "expected"),
    [(False, False, False), (True, False, True), (False, True, True), (True, True, True)],
)
def test_either_side_may_turn_night_safety_on_and_neither_may_turn_it_off(
    by_operator: bool, by_client: bool, expected: bool
) -> None:
    """`client_policy.night_safety_enabled` is NOT NULL with a False default, so a row
    that was never touched is indistinguishable from one that deliberately said no.
    Resolving that towards "off" would mean creating a policy row silently disabled an
    operator-wide safety rule."""
    effective = resolve(
        operator(night_safety_enabled=by_operator),
        ClientPolicyValues(night_safety_enabled=by_client),
    )
    assert effective.night_safety_enabled is expected


def test_a_client_night_window_needs_both_ends() -> None:
    """The same refusal B24 made for mode windows: guessing the missing end moves the
    boundary by hours, and for this rule those hours are the whole point."""
    half = resolve(
        operator(night_safety_start="21:00", night_safety_end="05:00"),
        ClientPolicyValues(night_start=time(22, 0)),
    )
    assert (half.night_start, half.night_end) == (time(21, 0), time(5, 0))

    both = resolve(
        operator(night_safety_start="21:00", night_safety_end="05:00"),
        ClientPolicyValues(night_start=time(22, 0), night_end=time(4, 0)),
    )
    assert (both.night_start, both.night_end) == (time(22, 0), time(4, 0))


def test_the_night_safety_shape_is_a_setting_not_a_constant() -> None:
    """OQ-10 is open: the pilot clients' actual policy is unknown, so which lone
    positions are policed has to be configurable rather than decided here."""
    assert resolve(operator()).night_safety_positions == "both"
    assert (
        resolve(operator(night_safety_positions="last_drop")).night_safety_positions == "last_drop"
    )
