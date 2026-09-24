"""Scenario file loading and validation (`simulator-spec.md` §8).

A scenario is data, not code: the same YAML plus the same seed must reproduce a run.
Validation is strict — an unknown key is an error, not a silently ignored typo, because a
misspelled `seed` would quietly destroy reproducibility.
"""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

IST = timezone(timedelta(hours=5, minutes=30))


class RoutingMode(StrEnum):
    """ADR-0010 rule 6: bulk callers use `approx`, or a self-hosted OSRM."""

    approx = "approx"
    osrm = "osrm"


class SupervisorPolicy(StrEnum):
    manual_nearest = "manual_nearest"
    approve_all = "approve_all"
    mixed = "mixed"
    absent = "absent"


class OperatorMode(StrEnum):
    manual = "manual"
    semi_auto = "semi_auto"
    full_auto = "full_auto"


class Strict(BaseModel):
    """Reject unknown keys everywhere: a typo must fail loudly."""

    model_config = ConfigDict(extra="forbid")


class LatLngModel(Strict):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)

    @classmethod
    def from_pair(cls, pair: list[float]) -> LatLngModel:
        return cls(lat=pair[0], lng=pair[1])


class FleetGroup(Strict):
    type: str
    count: int = Field(ge=1)
    depot: list[float] = Field(min_length=2, max_length=2)

    @field_validator("depot")
    @classmethod
    def _valid_point(cls, value: list[float]) -> list[float]:
        LatLngModel.from_pair(value)
        return value


class Drivers(Strict):
    shift_start_ist: time
    shift_end_ist: time
    late_start_p: float = Field(default=0.0, ge=0, le=1)


class Shift(Strict):
    start_ist: time
    end_ist: time
    share: float = Field(gt=0, le=1)


class Office(Strict):
    name: str
    location: list[float] = Field(min_length=2, max_length=2)


class Employees(Strict):
    count: int = Field(ge=1)
    home_zones: list[str] = Field(default_factory=list)
    vip_share: float = Field(default=0.0, ge=0, le=1)
    priority_dist: dict[int, float] = Field(default_factory=dict)
    shifts: list[Shift] = Field(min_length=1)

    @field_validator("priority_dist")
    @classmethod
    def _priorities_in_range(cls, value: dict[int, float]) -> dict[int, float]:
        # glossary.md: priority 1 (highest) to 10.
        for priority in value:
            if not 1 <= priority <= 10:
                raise ValueError(f"priority {priority} is outside 1-10")
        total = sum(value.values())
        if value and abs(total - 1.0) > 0.01:
            raise ValueError(f"priority_dist must sum to 1.0, got {total:.3f}")
        return value

    @model_validator(mode="after")
    def _shares_sum_to_one(self) -> Employees:
        total = sum(shift.share for shift in self.shifts)
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"shift shares must sum to 1.0, got {total:.3f}")
        return self


class Client(Strict):
    name: str
    office: Office
    employees: Employees


class Supervisor(Strict):
    policy: SupervisorPolicy = SupervisorPolicy.manual_nearest
    reaction_delay_s: list[int] = Field(default=[20, 120], min_length=2, max_length=2)

    @field_validator("reaction_delay_s")
    @classmethod
    def _ordered(cls, value: list[int]) -> list[int]:
        if value[0] < 0 or value[1] < value[0]:
            raise ValueError("reaction_delay_s must be [min, max] with 0 <= min <= max")
        return value


class Operator(Strict):
    config_overrides: dict[str, Any] = Field(default_factory=dict)


class ModeEntry(Strict):
    mode: OperatorMode


class Traffic(Strict):
    profile: str = "ncr_default"


class Event(Strict):
    at_ist: time
    type: str
    duration_min: int | None = None
    vehicle: str | None = None


class Assertions(Strict):
    """What must hold for the run to pass (`scenarios.md`)."""

    p90_wait_minutes_max: float | None = None
    gave_up_max: int | None = None
    invalid_transitions: int | None = None
    api_5xx_max: int | None = None
    all_requests_terminal: bool | None = None


class Scenario(Strict):
    name: str
    version: int = 1
    seed: int
    start: datetime
    duration_hours: float = Field(gt=0, le=24 * 14)
    speed_factor: float = Field(default=60.0, gt=0)
    routing: RoutingMode = RoutingMode.approx
    operator: Operator = Field(default_factory=Operator)
    modes: list[ModeEntry] = Field(default_factory=lambda: [ModeEntry(mode=OperatorMode.manual)])
    fleet: list[FleetGroup] = Field(min_length=1)
    drivers: Drivers
    clients: list[Client] = Field(min_length=1)
    supervisor: Supervisor = Field(default_factory=Supervisor)
    traffic: Traffic = Field(default_factory=Traffic)
    events: list[Event] = Field(default_factory=list)
    assertions: Assertions = Field(default_factory=Assertions)

    @field_validator("start")
    @classmethod
    def _start_is_utc(cls, value: datetime) -> datetime:
        # A naive start time would silently mean "local", and runs would not reproduce
        # across machines.
        if value.tzinfo is None:
            raise ValueError("start must include a timezone offset (use ...Z for UTC)")
        return value.astimezone(UTC)

    @property
    def end(self) -> datetime:
        return self.start + timedelta(hours=self.duration_hours)

    @property
    def vehicle_count(self) -> int:
        return sum(group.count for group in self.fleet)

    @property
    def employee_count(self) -> int:
        return sum(client.employees.count for client in self.clients)


class ScenarioError(Exception):
    """A scenario file that cannot be loaded or does not validate."""


def load_scenario(path: str | Path) -> Scenario:
    """Read and validate a scenario file, or raise `ScenarioError` with the reason."""
    file_path = Path(path)
    if not file_path.exists():
        raise ScenarioError(f"scenario file not found: {file_path}")

    try:
        raw = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ScenarioError(f"{file_path}: invalid YAML: {exc}") from exc

    if raw is None:
        raise ScenarioError(f"{file_path}: file is empty")
    if not isinstance(raw, dict):
        raise ScenarioError(f"{file_path}: top level must be a mapping")

    try:
        return Scenario.model_validate(raw)
    except Exception as exc:
        raise ScenarioError(f"{file_path}: {exc}") from exc
