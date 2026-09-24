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
        ConfigKey("batch_window_seconds", 45, 10, 120, description="Micro-batch window."),
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
        ConfigKey("alert_wait_minutes", 20, 5, 60, description="Pending request turns red."),
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
        ConfigKey("stale_gps_seconds", 60, 20, 300, description="Vehicle considered stale."),
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
    )
}

#: Keys a client may override, and of those, the ones that may only get stricter.
PER_CLIENT_KEYS = frozenset(key.name for key in CONFIG_KEYS.values() if key.per_client)
STRICTER_ONLY_KEYS = frozenset(key.name for key in CONFIG_KEYS.values() if key.stricter_only)


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
