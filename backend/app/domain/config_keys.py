"""Operator configuration keys, defaults and ranges.

Transcribed from `allocation-rules.md` §1. This is the single place those numbers live:
CLAUDE.md hard rule 4 says business numbers come from config, never from code, and this
registry is what makes that enforceable — a key not defined here cannot be set.

Pure data and pure validation: no database, no framework, so the simulator and the
optimizer can read the same defaults.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from typing import Any

from app.domain.errors import ValidationFailed


@dataclass(frozen=True, slots=True)
class ConfigKey:
    """One tunable number, with the range the docs give for it."""

    name: str
    default: Any
    minimum: float | None = None
    maximum: float | None = None
    choices: tuple[str, ...] | None = None
    per_client: bool = False
    #: True when a client may only make the value *stricter* than the operator's.
    stricter_only: bool = False
    description: str = ""

    def validate(self, value: Any) -> Any:
        """Return the coerced value, or raise `ValidationFailed`."""
        expected = type(self.default)

        if expected is bool:
            if not isinstance(value, bool):
                raise ValidationFailed(
                    f"{self.name} must be true or false", {"key": self.name, "value": value}
                )
            return value

        if self.choices is not None:
            if value not in self.choices:
                raise ValidationFailed(
                    f"{self.name} must be one of {', '.join(self.choices)}",
                    {"key": self.name, "value": value, "allowed": list(self.choices)},
                )
            return value

        if expected is time:
            return _parse_time(self.name, value)

        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ValidationFailed(
                f"{self.name} must be a number", {"key": self.name, "value": value}
            )

        number = float(value)
        if self.minimum is not None and number < self.minimum:
            raise ValidationFailed(
                f"{self.name} must be at least {self.minimum}",
                {"key": self.name, "value": value, "min": self.minimum, "max": self.maximum},
            )
        if self.maximum is not None and number > self.maximum:
            raise ValidationFailed(
                f"{self.name} must be at most {self.maximum}",
                {"key": self.name, "value": value, "min": self.minimum, "max": self.maximum},
            )
        return int(number) if expected is int else number


def _parse_time(name: str, value: Any) -> str:
    if not isinstance(value, str):
        raise ValidationFailed(f"{name} must be a HH:MM time", {"key": name, "value": value})
    try:
        time.fromisoformat(value)
    except ValueError as exc:
        raise ValidationFailed(
            f"{name} must be a HH:MM time", {"key": name, "value": value}
        ) from exc
    return value


#: Every key from `allocation-rules.md` §1, in the order the table lists them.
CONFIG_KEYS: dict[str, ConfigKey] = {
    key.name: key
    for key in (
        ConfigKey(
            "candidate_max_eta_minutes",
            20,
            5,
            60,
            description="A vehicle is a candidate if it can reach pickup within this time.",
        ),
        ConfigKey(
            "pickup_window_minutes",
            10,
            0,
            30,
            per_client=True,
            description="Allowed deviation from requested pickup time for to_office.",
        ),
        ConfigKey(
            "hold_window_min_minutes",
            10,
            0,
            30,
            per_client=True,
            description="Minimum pooling hold for from_office (non-high urgency).",
        ),
        ConfigKey(
            "hold_window_max_minutes",
            30,
            0,
            60,
            per_client=True,
            description="Maximum pooling hold for from_office.",
        ),
        ConfigKey(
            "max_detour_factor",
            1.5,
            1.0,
            3.0,
            per_client=True,
            stricter_only=True,
            description="Rider ride time <= factor x direct time.",
        ),
        ConfigKey(
            "max_detour_minutes",
            15,
            0,
            60,
            per_client=True,
            stricter_only=True,
            description="Rider ride time <= direct time + this.",
        ),
        ConfigKey(
            "enroute_reuse_max_eta_minutes",
            5,
            0,
            15,
            description="An en-route vehicle may take a new same-direction rider within this.",
        ),
        ConfigKey(
            "retry_after_minutes",
            10,
            5,
            60,
            description=(
                "How often an already-escalated request widens its search again. The "
                "*first* escalation is at `alert_wait_minutes` (ADR-0023)."
            ),
        ),
        ConfigKey(
            "retry_eta_widen_minutes",
            10,
            0,
            30,
            description="Each escalation widens that request's candidate ETA ceiling by this.",
        ),
        ConfigKey(
            "retry_eta_max_minutes",
            45,
            5,
            120,
            description="The widest the candidate ETA ceiling may ever get.",
        ),
        ConfigKey("batch_window_seconds", 45, 10, 120, description="Micro-batch window."),
        ConfigKey(
            "stop_dwell_seconds",
            60,
            0,
            300,
            description=(
                "Seconds a cab spends at each stop while riders get in or out. The optimizer "
                "plans with it; the real figure is a pilot measurement. Provisional."
            ),
        ),
        ConfigKey(
            "billing_no_show_billable",
            True,
            description=(
                "Whether a rider who was not there when the cab arrived is on the invoice. "
                "Provisional (OQ-01, OQ-03): nothing says how the pilot operator bills."
            ),
        ),
        ConfigKey(
            "billing_late_cancel_billable",
            False,
            description=(
                "Whether a rider who cancelled after a cab was assigned is on the invoice. "
                "A request cancelled while still queued is never billable. Provisional."
            ),
        ),
        ConfigKey(
            "billing_distance_basis",
            "trip_share",
            choices=("trip_share", "direct"),
            description=(
                "Kilometres billed per ride: an equal share of the trip the cab drove "
                "(`trip_share`, adds up to the trip), or the rider's own journey (`direct`). "
                "Provisional."
            ),
        ),
        ConfigKey(
            "optimizer_failure_threshold",
            3,
            1,
            10,
            description="This many most-recent optimizer runs all failing means it is down.",
        ),
        ConfigKey(
            "optimizer_failure_memory_minutes",
            15,
            1,
            120,
            description="A failed optimizer run older than this says nothing about now.",
        ),
        ConfigKey(
            "optimizer_stall_seconds",
            180,
            60,
            3600,
            description=(
                "A request ready this long with no optimizer run since means the worker is "
                "not running. Never less than three batch windows."
            ),
        ),
        ConfigKey(
            "mode_prompt_window_minutes",
            15,
            5,
            60,
            description="How far back a mode-switch prompt looks (control-model.md section 5).",
        ),
        ConfigKey(
            "mode_prompt_rejected_share",
            0.30,
            0.05,
            1.0,
            description="Prompt when at least this share of a scope's suggestions were rejected.",
        ),
        ConfigKey(
            "mode_prompt_eta_error_minutes",
            10.0,
            1,
            60,
            description="Prompt when the median pickup-ETA error in a scope exceeds this.",
        ),
        ConfigKey(
            "mode_prompt_pending_multiple",
            2.0,
            1.0,
            10.0,
            description="Prompt when pending requests exceed this multiple of normal for the slot.",
        ),
        ConfigKey(
            "mode_prompt_fleet_share",
            0.20,
            0.05,
            1.0,
            description="Prompt when this share of the fleet is stale or out of service.",
        ),
        ConfigKey(
            "mode_prompt_min_samples",
            5,
            1,
            50,
            description=(
                "Fewest decisions, pickups or pending requests a ratio is judged on. "
                "Provisional: section 5 names none, and a percentage of one is not a signal."
            ),
        ),
        ConfigKey(
            "mode_prompt_baseline_days",
            14,
            1,
            60,
            description='How many past days define "normal" pending requests for a time slot.',
        ),
        ConfigKey(
            "optimizer_time_limit_seconds",
            10,
            1,
            60,
            description="Hard cap on one DARP run; no solution within it falls back to greedy.",
        ),
        ConfigKey(
            "failsafe_timeout_seconds",
            180,
            30,
            900,
            description="Semi-auto suggestion timeout.",
        ),
        ConfigKey(
            "failsafe_action",
            "auto_assign",
            choices=("auto_assign", "escalate"),
            description="What happens on failsafe timeout.",
        ),
        ConfigKey(
            "alert_wait_minutes",
            20,
            5,
            60,
            description=(
                "A waiting request has waited too long: the board turns it red, and "
                "escalation starts (ADR-0023)."
            ),
        ),
        ConfigKey(
            "request_expiry_minutes", 120, 30, 480, description="Unassigned request expires."
        ),
        ConfigKey(
            "no_show_wait_minutes",
            5,
            1,
            15,
            per_client=True,
            description="Driver wait before no-show allowed.",
        ),
        ConfigKey(
            "stale_gps_seconds",
            150,
            20,
            300,
            description=(
                "Vehicle considered stale. At least 1.5 x gps_heartbeat_seconds, or a parked "
                "cab would be stale between two heartbeats."
            ),
        ),
        ConfigKey(
            "gps_distance_filter_m",
            5,
            1,
            100,
            description="The driver app publishes a position after moving this far.",
        ),
        ConfigKey(
            "gps_heartbeat_seconds",
            60,
            15,
            120,
            description="While stationary the app publishes a heartbeat this often.",
        ),
        ConfigKey("weight_wait", 1.0, 0, 10, description="Weight of the new rider's wait."),
        ConfigKey("weight_empty_km", 2.0, 0, 20, description="Minutes-equivalent per empty km."),
        ConfigKey(
            "cost_new_vehicle",
            15.0,
            0,
            120,
            description="Minutes-equivalent cost of deploying an idle vehicle.",
        ),
        ConfigKey("urgency_factor_high", 3.0, 1, 10),
        ConfigKey("urgency_factor_medium", 1.5, 1, 10),
        ConfigKey("urgency_factor_low", 1.0, 0.1, 10),
        ConfigKey(
            "night_safety_enabled",
            False,
            per_client=True,
            description="Enable the night-safety rules.",
        ),
        ConfigKey("night_safety_start", time(20, 0), per_client=True),
        ConfigKey("night_safety_end", time(6, 0), per_client=True),
        ConfigKey(
            "night_safety_positions",
            "both",
            choices=("both", "first_pickup", "last_drop"),
            description=(
                "Which lone positions rule 11 polices: the first pickup, the last drop,"
                " or both. A setting rather than a constant because OQ-10 - the pilot"
                " clients' actual policy - is still open."
            ),
        ),
    )
}

#: Keys a client may override, and of those, the ones that may only get stricter.
PER_CLIENT_KEYS = frozenset(key.name for key in CONFIG_KEYS.values() if key.per_client)
STRICTER_ONLY_KEYS = frozenset(key.name for key in CONFIG_KEYS.values() if key.stricter_only)


#: Declared ahead of the code that will read them. Phase 1 reads none of these: the
#: Declared, and still read by nothing. **This list shrinks as the phases land**, and a
#: guard fails if a key in it acquires a reader - B22 removed the six cost-function
#: weights and urgency factors the moment `domain/cost.py` began reading them.
#:
#: What is left, and what will claim it: B30 took `batch_window_seconds` and
#: `hold_window_max_minutes` is left, to the dynamic hold window of
#: Phase 4. B29 took `hold_window_min_minutes` - Phase 3's fixed window.
#: B25 took the failsafe pair and B28 took the night-safety trio, which is
#: now read by `domain/policy.py` and rule 11 - OQ-10 remains open about the exact
#: client policy, which is why `night_safety_positions` is a key and not a constant.
#:
#: `night_safety_enabled` is the subtle one: `client_policy` has a
#: column of that name, so a loose search for the string finds a "reader" that is really
#: a different thing - which is why the guard matches quoted lookups only.
#: Keeping the list here means the next audit does not have to work out which
#: absences are deliberate - ADR-0023, which found `alert_wait_minutes` hiding among
#: them and read by nothing while all seven scenarios set it.
PHASE_2_KEYS = frozenset(
    {
        "hold_window_max_minutes",
    }
)


def defaults() -> dict[str, Any]:
    """Every key at its documented default."""
    return {
        name: (
            key.default.isoformat(timespec="minutes")
            if isinstance(key.default, time)
            else key.default
        )
        for name, key in CONFIG_KEYS.items()
    }


def validate(name: str, value: Any) -> Any:
    """Validate one key/value pair, or raise `ValidationFailed`."""
    key = CONFIG_KEYS.get(name)
    if key is None:
        raise ValidationFailed(
            f"Unknown config key: {name}",
            {"key": name, "known_keys": sorted(CONFIG_KEYS)},
        )
    return key.validate(value)


#: A stale threshold must outlast a missed heartbeat: at 1.0 x, a parked cab is "stale" every time
#: its heartbeat is a second late.
STALE_OVER_HEARTBEAT = 1.5


def check_consistency(values: dict[str, Any]) -> None:
    """Rules between keys, judged on the full effective set (stored values plus the patch)."""
    stale = values["stale_gps_seconds"]
    heartbeat = values["gps_heartbeat_seconds"]
    if stale < STALE_OVER_HEARTBEAT * heartbeat:
        raise ValidationFailed(
            "stale_gps_seconds must be at least 1.5 x gps_heartbeat_seconds, or a parked cab "
            "would be marked stale between two heartbeats",
            {
                "stale_gps_seconds": stale,
                "gps_heartbeat_seconds": heartbeat,
                "minimum_stale_gps_seconds": STALE_OVER_HEARTBEAT * heartbeat,
            },
        )


def validate_all(values: dict[str, Any]) -> dict[str, Any]:
    """Validate a whole patch. Reports every problem, not just the first.

    A partial apply would leave an operator half-configured, so the caller gets one
    error listing all of it and nothing is written.
    """
    validated: dict[str, Any] = {}
    problems: list[dict[str, Any]] = []

    for name, value in values.items():
        try:
            validated[name] = validate(name, value)
        except ValidationFailed as exc:
            problems.append({"message": exc.message, **exc.details})

    if problems:
        raise ValidationFailed("One or more config values are invalid", {"errors": problems})
    return validated
