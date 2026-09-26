"""The rider (M05, `simulator-spec.md` section 5.2).

A person who needs to get to work, gets impatient, and sometimes does not turn up. Every
one of those behaviours exists because it produces a *demand shape* the platform has to
cope with: requests bunched before a shift, riders giving up after forty minutes, the
occasional no-show that a driver has to wait out.

The agent drives the real API - `POST /ride-requests`, `POST /ride-requests/{id}/cancel` -
as the employee it represents (`simulator-spec.md` section 2). Nothing here writes to the
database, and nothing here decides a request's status: the backend does, and the agent
reads it back.

Distributions are from section 5.2 and are named constants below rather than magic
numbers, so a scenario tuning them later has one place to look.
"""

from __future__ import annotations

import uuid
from collections.abc import Generator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from typing import TYPE_CHECKING, Any

import numpy as np
import simpy

from sim.geo import LatLng

if TYPE_CHECKING:
    from sim.engine import Engine

Process = Generator[simpy.Event, Any, Any]

# --- section 5.2 distributions ---------------------------------------------------------

#: `to_office`: the request goes in this long before the shift starts.
LEAD_TIME_MEAN_MINUTES = 45.0
LEAD_TIME_SIGMA_MINUTES = 10.0

#: `from_office`: people leave later than the shift ends, by this much.
READY_LATE_MEAN_MINUTES = 10.0
READY_LATE_SIGMA_MINUTES = 15.0

#: How long someone waits before giving up and finding their own way home.
PATIENCE_MEAN_MINUTES = 40.0
PATIENCE_SIGMA_MINUTES = 10.0
#: Nobody gives up in the first few minutes, whatever the sample says.
PATIENCE_FLOOR_MINUTES = 5.0

#: Readiness at the pickup point.
ON_TIME_PROBABILITY = 0.9
LATE_MEAN_MINUTES = 3.0
NO_SHOW_PROBABILITY = 0.02

#: Chance a given employee travels at all on a given day.
PARTICIPATION_PROBABILITY = 0.8

#: How often to re-read a request's status while waiting. Simulated seconds.
POLL_INTERVAL_SECONDS = 60

#: Statuses the backend will not move a request out of (`trip-lifecycle.md` section 1).
TERMINAL_STATUSES = frozenset({"dropped", "cancelled", "expired", "no_show"})


class Direction(StrEnum):
    to_office = "to_office"
    from_office = "from_office"


class Outcome(StrEnum):
    """How a rider's day ended. Recorded for metrics, not decided by the agent."""

    not_travelling = "not_travelling"
    completed = "completed"
    gave_up = "gave_up"
    expired = "expired"
    no_show = "no_show"
    cancelled = "cancelled"
    unresolved = "unresolved"
    failed = "failed"


@dataclass
class RiderRecord:
    """What happened to one rider, for the run's metrics."""

    employee_id: str
    direction: Direction | None = None
    requested_at: datetime | None = None
    request_id: uuid.UUID | None = None
    outcome: Outcome = Outcome.not_travelling
    waited_minutes: float | None = None
    patience_minutes: float | None = None
    detail: str | None = None


@dataclass(frozen=True, slots=True)
class EmployeeProfile:
    """Who this rider is. Taken from the scenario and the seeded world."""

    employee_id: str
    token: str
    #: None means "use the employee's saved home", which is what the app sends when a
    #: rider taps home rather than dropping a pin.
    home: LatLng | None
    shift_start: datetime
    shift_end: datetime
    #: Only `to_office` fits inside a short scenario; both are modelled.
    directions: tuple[Direction, ...] = (Direction.to_office,)
    #: Chance this rider travels at all today. On the profile rather than hidden in a
    #: module constant, so a scenario can dial demand up or down.
    participation: float = PARTICIPATION_PROBABILITY


class EmployeeAgent:
    """One simulated rider.

    Deliberately stateless about the platform: it asks the backend what happened rather
    than assuming, so a bug in expiry or assignment shows up here as a stuck request
    instead of being papered over by the simulator's own bookkeeping.
    """

    def __init__(self, engine: Engine, profile: EmployeeProfile) -> None:
        self.engine = engine
        self.profile = profile
        self.record = RiderRecord(employee_id=profile.employee_id)
        self._rng: np.random.Generator = engine.rng.for_agent(f"employee:{profile.employee_id}")

    # --- the day ----------------------------------------------------------------

    def day(self) -> Process:
        """Decide whether to travel, wait for the right moment, then ask for a cab."""
        if self._rng.random() > self.profile.participation:
            self.engine.record(f"employee {self.profile.employee_id} is not travelling today")
            return

        for direction in self.profile.directions:
            moment = self._request_moment(direction)
            delay = (moment - self.engine.now()).total_seconds()
            if delay < 0:
                # The scenario window opened after this rider would have asked. Skipping
                # is honest; asking late would invent demand the scenario did not describe.
                self.engine.record(
                    f"employee {self.profile.employee_id} missed the {direction} window"
                )
                continue
            if moment > self.engine.scenario.end:
                continue

            yield self.engine.env.timeout(delay)
            yield from self._ask_for_a_cab(direction)

    def travel_now(self, direction: Direction = Direction.to_office) -> Process:
        """Ask for a cab right now, outside the normal day (M07 `demand_surge`).

        Goes through exactly the same path as a planned trip - the rider's own token, the
        real endpoint, the same patience and give-up behaviour - so surge demand is
        indistinguishable to the platform from demand the scenario planned.
        """
        yield from self._ask_for_a_cab(direction)

    @property
    def travelling(self) -> bool:
        """Whether this rider already has a ride in play today."""
        return self.record.request_id is not None

    def _request_moment(self, direction: Direction) -> datetime:
        """When this rider asks (`simulator-spec.md` section 5.2, demand model)."""
        if direction is Direction.to_office:
            lead = self._normal(LEAD_TIME_MEAN_MINUTES, LEAD_TIME_SIGMA_MINUTES, floor=5.0)
            return self.profile.shift_start - timedelta(minutes=lead)

        late = self._normal(READY_LATE_MEAN_MINUTES, READY_LATE_SIGMA_MINUTES, floor=0.0)
        return self.profile.shift_end + timedelta(minutes=late)

    def _ask_for_a_cab(self, direction: Direction) -> Process:
        platform = self.engine.platform
        if platform is None:
            # Offline runs have no API to ask. Movement-only runs are still useful, so
            # this is a skip rather than an error.
            return

        requested_time = (
            self.profile.shift_start
            if direction is Direction.to_office
            else self.engine.now() + timedelta(minutes=5)
        )
        try:
            request = platform.create_request(
                token=self.profile.token,
                direction=str(direction),
                requested_time=requested_time,
                lat=self.profile.home.lat if self.profile.home else None,
                lng=self.profile.home.lng if self.profile.home else None,
            )
        except Exception as exc:  # noqa: BLE001 - one rider's failure is not the run's
            self.record.outcome = Outcome.failed
            self.record.detail = f"{type(exc).__name__}: {exc}"
            self.engine.record(f"employee {self.profile.employee_id} could not request: {exc}")
            return

        self.record.direction = direction
        self.record.request_id = request.id
        self.record.requested_at = self.engine.now()
        self.engine.record(
            f"employee {self.profile.employee_id} requested {direction} ({request.id})"
        )
        yield from self._wait_for_the_cab(request.id)

    # --- waiting ------------------------------------------------------------------

    def _wait_for_the_cab(self, request_id: uuid.UUID) -> Process:
        """Wait until the ride resolves, or until patience runs out.

        Reads the shared status board rather than polling its own request: three hundred
        riders each polling would measure the harness, not the platform (OQ-26). Acting -
        cancelling - still goes through this rider's own token.
        """
        patience = self._normal(
            PATIENCE_MEAN_MINUTES, PATIENCE_SIGMA_MINUTES, floor=PATIENCE_FLOOR_MINUTES
        )
        self.record.patience_minutes = patience
        started = self.engine.now()
        deadline = started + timedelta(minutes=patience)

        while True:
            yield self.engine.env.timeout(POLL_INTERVAL_SECONDS)
            now = self.engine.now()

            status = self._status_of(request_id)
            if status in TERMINAL_STATUSES:
                self.record.waited_minutes = (now - started).total_seconds() / 60.0
                self.record.outcome = _outcome_for(str(status))
                return

            if status == "picked_up":
                # On board: patience no longer applies, the ride is happening.
                yield from self._ride_home(request_id, started)
                return

            if now >= deadline:
                self._give_up(request_id, started, now)
                return

            if now >= self.engine.scenario.end:
                self.record.outcome = Outcome.unresolved
                self.record.detail = f"still {status} when the scenario ended"
                return

    def _ride_home(self, request_id: uuid.UUID, started: datetime) -> Process:
        while True:
            yield self.engine.env.timeout(POLL_INTERVAL_SECONDS)
            status = self._status_of(request_id)
            if status in TERMINAL_STATUSES:
                self.record.waited_minutes = (self.engine.now() - started).total_seconds() / 60.0
                self.record.outcome = _outcome_for(status)
                return
            if self.engine.now() >= self.engine.scenario.end:
                self.record.outcome = Outcome.unresolved
                self.record.detail = f"still {status} when the scenario ended"
                return

    def _status_of(self, request_id: uuid.UUID) -> str | None:
        """What the platform last said. `None` means the board has not seen it yet."""
        board = self.engine.board
        if board is not None:
            return board.status_of(request_id)
        platform = self.engine.platform
        if platform is None:
            return None
        return platform.request_status(self.profile.token, request_id)

    def _give_up(self, request_id: uuid.UUID, started: datetime, now: datetime) -> None:
        """Cancel after waiting past patience. This is the number the pilot is judged on."""
        platform = self.engine.platform
        assert platform is not None

        self.record.waited_minutes = (now - started).total_seconds() / 60.0
        try:
            platform.cancel_request(self.profile.token, request_id, reason="Waited too long")
        except Exception as exc:  # noqa: BLE001
            self.record.outcome = Outcome.failed
            self.record.detail = f"cancel failed: {exc}"
            return

        self.record.outcome = Outcome.gave_up
        if self.engine.board is not None:
            # The board is a minute stale; this rider knows better about their own ride.
            self.engine.board.note(request_id, "cancelled")
        self.engine.record(
            f"employee {self.profile.employee_id} gave up after "
            f"{self.record.waited_minutes:.0f} min"
        )

    # --- readiness at the pickup point -----------------------------------------------

    def readiness(self) -> tuple[bool, float]:
        """Whether this rider turns up, and how late (section 5.2).

        Used by the driver agent to decide between boarding and a no-show, so both sides
        of that interaction come from one sampled truth rather than two guesses.
        """
        draw = self._rng.random()
        if draw < NO_SHOW_PROBABILITY:
            return False, 0.0
        if draw < NO_SHOW_PROBABILITY + (1 - ON_TIME_PROBABILITY - NO_SHOW_PROBABILITY):
            return True, float(self._rng.exponential(LATE_MEAN_MINUTES))
        return True, 0.0

    def _normal(self, mean: float, sigma: float, floor: float) -> float:
        return float(max(floor, self._rng.normal(mean, sigma)))


def _outcome_for(status: str) -> Outcome:
    return {
        "dropped": Outcome.completed,
        "cancelled": Outcome.cancelled,
        "expired": Outcome.expired,
        "no_show": Outcome.no_show,
    }.get(status, Outcome.unresolved)


@dataclass
class DemandSummary:
    """What the riders did, for `metrics.json`."""

    riders: int = 0
    requested: int = 0
    completed: int = 0
    gave_up: int = 0
    expired: int = 0
    no_shows: int = 0
    cancelled: int = 0
    unresolved: int = 0
    failed: int = 0
    not_travelling: int = 0
    waits_minutes: list[float] = field(default_factory=list)

    @property
    def all_terminal(self) -> bool:
        """S01's assertion: nothing left hanging when the scenario ended."""
        return self.unresolved == 0 and self.failed == 0


def summarise(records: list[RiderRecord]) -> DemandSummary:
    summary = DemandSummary(riders=len(records))
    counters = {
        Outcome.completed: "completed",
        Outcome.gave_up: "gave_up",
        Outcome.expired: "expired",
        Outcome.no_show: "no_shows",
        Outcome.cancelled: "cancelled",
        Outcome.unresolved: "unresolved",
        Outcome.failed: "failed",
        Outcome.not_travelling: "not_travelling",
    }
    for record in records:
        if record.request_id is not None:
            summary.requested += 1
        setattr(summary, counters[record.outcome], getattr(summary, counters[record.outcome]) + 1)
        if record.waited_minutes is not None:
            summary.waits_minutes.append(record.waited_minutes)
    return summary
