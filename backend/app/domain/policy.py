"""What a client's own rules resolve to (`allocation-rules.md` §1 and §2, B28).

An operator sets numbers for the whole business; a client may override a handful of
them for their own people. Phase 1 implemented exactly one half of one rule of that -
the detour pair in rule 7 - inline in the dispatch service. Everything else in the
`client_policy` table was a column nothing read.

This module is the one place the two sets of numbers are combined, so there is a single
answer to "what applies to this rider" and it can be asked without a database.

**Stricter only, and only where §1 says so.** `max_detour_factor` and
`max_detour_minutes` are marked `stricter_only` in the config registry: a client may
tighten them, never loosen them. `pickup_window_minutes` and `no_show_wait_minutes` are
not - a client may set either way, because how long *their* employees will wait at the
kerb is their call to make. The registry is the authority on which is which, so this
module reads it rather than restating it.

**Night safety is a floor, not a setting a client can lower.** It is on if either the
operator or the client turns it on. `client_policy.night_safety_enabled` is a
`NOT NULL` boolean with a `False` default, so a client row that exists and has never
been touched is indistinguishable from one that deliberately said no - and resolving
that ambiguity in the direction of "off" would mean creating a policy row silently
disabled an operator-wide safety rule.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import time
from typing import Any

from app.domain.config_keys import CONFIG_KEYS


@dataclass(frozen=True, slots=True)
class ClientPolicyValues:
    """One client's overrides, as the `client_policy` row holds them.

    A plain dataclass rather than the ORM model so the resolution stays pure and the
    simulator can ask the same question without a session.
    """

    pooling_allowed: bool = True
    #: True by default; see the note on the column. A client restricts, rather than
    #: having to grant what Phase 1 already allowed.
    employee_opt_out_allowed: bool = True
    night_safety_enabled: bool = False
    night_start: time | None = None
    night_end: time | None = None
    max_detour_factor: float | None = None
    max_detour_minutes: int | None = None
    pickup_window_minutes: int | None = None
    no_show_wait_minutes: int | None = None


@dataclass(frozen=True, slots=True)
class EffectivePolicy:
    """The numbers that actually apply to one client's rides."""

    max_detour_factor: float
    max_detour_minutes: float
    pickup_window_minutes: int
    no_show_wait_minutes: int
    pooling_allowed: bool
    employee_opt_out_allowed: bool
    night_safety_enabled: bool
    night_start: time
    night_end: time
    night_safety_positions: str


def stricter_of(operator_value: float, client_value: float | None) -> float:
    """The tighter of the two limits. Lower is tighter for every §1 number.

    `None` means the client did not override it, which is not the same as zero - a
    distinction worth keeping explicit, because `client_value or operator_value` reads
    naturally and silently discards a legitimate `0`.
    """
    if client_value is None:
        return operator_value
    return min(operator_value, client_value)


def client_value_or(operator_value: float, client_value: float | None) -> float:
    """The client's number when they set one, whichever direction it goes."""
    return operator_value if client_value is None else client_value


def _apply(key: str, operator_value: float, client_value: float | None) -> float:
    """Combine one number the way the config registry says that key combines.

    Reading `stricter_only` from the registry rather than restating the list here means
    a key that becomes stricter-only later cannot be tightened in one place and left
    loose in another.
    """
    config_key = CONFIG_KEYS[key]
    if config_key.stricter_only:
        return stricter_of(operator_value, client_value)
    return client_value_or(operator_value, client_value)


def resolve(
    operator_values: Mapping[str, Any], client: ClientPolicyValues | None = None
) -> EffectivePolicy:
    """Operator config, overridden by one client's policy where §1 allows it."""
    policy = client or ClientPolicyValues()

    operator_night_start = _as_time(operator_values["night_safety_start"])
    operator_night_end = _as_time(operator_values["night_safety_end"])

    return EffectivePolicy(
        max_detour_factor=_apply(
            "max_detour_factor",
            float(operator_values["max_detour_factor"]),
            None if policy.max_detour_factor is None else float(policy.max_detour_factor),
        ),
        max_detour_minutes=_apply(
            "max_detour_minutes",
            float(operator_values["max_detour_minutes"]),
            None if policy.max_detour_minutes is None else float(policy.max_detour_minutes),
        ),
        pickup_window_minutes=int(
            _apply(
                "pickup_window_minutes",
                float(operator_values["pickup_window_minutes"]),
                None
                if policy.pickup_window_minutes is None
                else float(policy.pickup_window_minutes),
            )
        ),
        no_show_wait_minutes=int(
            _apply(
                "no_show_wait_minutes",
                float(operator_values["no_show_wait_minutes"]),
                None if policy.no_show_wait_minutes is None else float(policy.no_show_wait_minutes),
            )
        ),
        pooling_allowed=policy.pooling_allowed,
        employee_opt_out_allowed=policy.employee_opt_out_allowed,
        # A floor: either side may turn it on, neither side's silence turns it off.
        night_safety_enabled=bool(operator_values["night_safety_enabled"])
        or policy.night_safety_enabled,
        # A window needs both ends, so a client supplying one end gets neither - the
        # same refusal B24 made for mode windows, for the same reason: guessing the
        # missing end moves the boundary by hours.
        night_start=(
            policy.night_start
            if policy.night_start is not None and policy.night_end is not None
            else operator_night_start
        ),
        night_end=(
            policy.night_end
            if policy.night_start is not None and policy.night_end is not None
            else operator_night_end
        ),
        night_safety_positions=str(operator_values["night_safety_positions"]),
    )


def _as_time(value: Any) -> time:
    """Config stores a time of day as `HH:MM`; the registry hands back either form."""
    if isinstance(value, time):
        return value
    return time.fromisoformat(str(value))
