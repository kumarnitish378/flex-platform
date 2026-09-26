"""The driver (M05, `simulator-spec.md` section 5.1).

Wraps the M02 `VehicleAgent`, which knows how to move and ping, with the part that makes
it a *driver*: going on duty, picking up the trips dispatch gives it, driving the stops in
order, and tapping the buttons a real driver taps.

Two things this agent deliberately does not do:

* **It does not decide anything the backend decides.** Whether a stop may go `done`,
  whether a no-show is allowed yet, whether the trip may complete - all of that is asked
  of the API and the answer is believed. A simulator that reimplemented those rules would
  agree with itself and disagree with production.
* **It does not invent trips.** It polls for what it has been assigned. In Phase 1 that
  assignment comes from a supervisor (M06); until then a driver simply drives an empty
  shift, which is exactly what a real driver would do with no dispatch.
"""

from __future__ import annotations

import uuid
from collections.abc import Generator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np
import simpy

from sim.geo import LatLng

if TYPE_CHECKING:
    from sim.agents.vehicle import VehicleAgent
    from sim.engine import Engine
    from sim.platform import DutyCredentials

Process = Generator[simpy.Event, Any, Any]

# --- section 5.1 distributions -----------------------------------------------------------

#: How long the driver takes to notice and accept a new assignment.
ACCEPT_DELAY_MIN_SECONDS = 5
ACCEPT_DELAY_MAX_SECONDS = 60

#: How long a rider takes to get in once the cab has arrived.
BOARDING_MIN_SECONDS = 30
BOARDING_MAX_SECONDS = 120

#: How often to ask dispatch whether anything has been assigned. Simulated seconds.
#: A minute is already faster than a driver notices their phone, and at fleet scale every
#: poll is a synchronous call that blocks the whole simulation (OQ-26).
POLL_INTERVAL_SECONDS = 60

#: A late driver starts this long after their shift (`late_start_p` in the scenario).
LATE_START_MEAN_MINUTES = 20.0

STOP_PICKUP = "pickup"
FINISHED_STOP_STATUSES = frozenset({"done", "skipped"})


@dataclass
class DriverRecord:
    """What one driver did, for the run's metrics."""

    driver_id: str
    went_on_duty: bool = False
    trips_started: int = 0
    trips_completed: int = 0
    stops_done: int = 0
    no_shows: int = 0
    faults: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class DriverAgent:
    """One simulated driver, bound to one cab."""

    def __init__(
        self,
        engine: Engine,
        driver_id: str,
        token: str,
        vehicle: VehicleAgent,
        credentials: DutyCredentials,
        late_start_probability: float = 0.0,
    ) -> None:
        self.engine = engine
        self.driver_id = driver_id
        self.token = token
        self.vehicle = vehicle
        self.credentials = credentials
        self.record = DriverRecord(driver_id=driver_id)
        self._late_start_p = late_start_probability
        self._rng: np.random.Generator = engine.rng.for_agent(f"driver:{driver_id}")
        self._handled: set[uuid.UUID] = set()

    # --- the shift -----------------------------------------------------------------

    def shift(self) -> Process:
        """Start (possibly late), then work whatever dispatch sends until the run ends."""
        if self._rng.random() < self._late_start_p:
            late = float(self._rng.exponential(LATE_START_MEAN_MINUTES))
            self.record.faults.append(f"late_start_{late:.0f}min")
            self.engine.record(f"driver {self.driver_id} starts {late:.0f} min late")
            yield self.engine.env.timeout(late * 60)

        self.vehicle.go_on_duty()
        self.record.went_on_duty = True
        # A parked cab still reports its position; the map must not lose a driver just
        # because dispatch has nothing for them yet.
        self.engine.spawn(self.vehicle.idle)

        while self.engine.now() < self.engine.scenario.end:
            yield self.engine.env.timeout(POLL_INTERVAL_SECONDS)
            trip = self._next_trip()
            if trip is not None:
                yield from self.drive(trip)

    def _next_trip(self) -> dict[str, Any] | None:
        """Whatever dispatch has given this driver and they have not driven yet."""
        platform = self.engine.platform
        if platform is None:
            return None
        try:
            # "upcoming" is planned + dispatched (B15). A freshly assigned trip is
            # `planned` until the driver starts it, so polling "active" - dispatched and
            # in_progress - would never show the driver the work waiting for them.
            trips = platform.driver_trips(self.token, scope="upcoming")
        except Exception as exc:  # noqa: BLE001 - a poll failure is not a crash
            self.record.errors.append(f"poll: {type(exc).__name__}")
            return None

        for trip in trips:
            if uuid.UUID(trip["id"]) not in self._handled:
                return trip
        return None

    # --- driving one trip ------------------------------------------------------------

    def drive(self, trip: dict[str, Any]) -> Process:
        """Accept, start, work the stops in order, complete."""
        platform = self.engine.platform
        assert platform is not None

        trip_id = uuid.UUID(trip["id"])
        self._handled.add(trip_id)

        # Section 5.1: acceptance delay. A driver is looking at the road, not the screen.
        yield self.engine.env.timeout(self._accept_delay_seconds())

        if not self._call(lambda: platform.start_trip(self.token, trip_id, self.engine.now())):
            return
        self.record.trips_started += 1
        self.engine.record(f"driver {self.driver_id} started trip {trip_id}")

        for stop in sorted(trip.get("stops", []), key=lambda item: item["sequence"]):
            if stop["status"] in FINISHED_STOP_STATUSES:
                continue
            yield from self._work_a_stop(trip_id, stop)

        if self._call(lambda: platform.complete_trip(self.token, trip_id, self.engine.now())):
            self.record.trips_completed += 1
            self.engine.record(f"driver {self.driver_id} completed trip {trip_id}")

    def _work_a_stop(self, trip_id: uuid.UUID, stop: dict[str, Any]) -> Process:
        """Drive there, arrive, wait for the rider, then finish or call a no-show."""
        platform = self.engine.platform
        assert platform is not None

        destination = LatLng(lat=stop["location"]["lat"], lng=stop["location"]["lng"])
        yield from self.vehicle.drive_to(destination)

        stop_id = uuid.UUID(stop["id"])
        here = self.vehicle.position
        if not self._call(
            lambda: platform.stop_action(
                self.token, stop_id, "arrived", self.engine.now(), here.lat, here.lng
            )
        ):
            return

        rider_present, late_minutes = self._rider_readiness(stop)
        if not rider_present:
            yield from self._wait_out_a_no_show(stop_id)
            return

        # Section 5.1: boarding delay, plus however late the rider is.
        yield self.engine.env.timeout(self._boarding_delay_seconds() + late_minutes * 60)

        position = self.vehicle.position
        if self._call(
            lambda: platform.stop_action(
                self.token, stop_id, "done", self.engine.now(), position.lat, position.lng
            )
        ):
            self.record.stops_done += 1

    def _wait_out_a_no_show(self, stop_id: uuid.UUID) -> Process:
        """DRV-05: the driver must wait `no_show_wait_minutes` before giving up.

        The wait is not optional and the backend enforces it, so the agent waits the
        configured time plus a margin rather than guessing - a no-show called too early
        comes back as a 409 and the rider is left standing there.
        """
        platform = self.engine.platform
        assert platform is not None

        wait_minutes = self.engine.no_show_wait_minutes
        yield self.engine.env.timeout((wait_minutes + 1) * 60)

        position = self.vehicle.position
        if self._call(
            lambda: platform.stop_action(
                self.token, stop_id, "no_show", self.engine.now(), position.lat, position.lng
            )
        ):
            self.record.no_shows += 1
            self.engine.record(f"driver {self.driver_id} recorded a no-show at {stop_id}")

    # --- faults (section 5.1) -----------------------------------------------------------

    def break_down(self, note: str = "Simulated breakdown") -> None:
        """Report a breakdown. The backend takes the vehicle off the road (DRV-06)."""
        platform = self.engine.platform
        if platform is None:
            return
        if self._call(lambda: platform.report_issue(self.token, "breakdown", note)):
            self.record.faults.append("breakdown")
            self.vehicle.go_off_duty()
            self.engine.record(f"driver {self.driver_id} broke down")

    def lose_gps(self, minutes: float) -> Process:
        """Stop pinging for a while, without going off duty (S06)."""
        self.record.faults.append(f"gps_loss_{minutes:.0f}min")
        self.vehicle.go_off_duty()
        yield self.engine.env.timeout(minutes * 60)
        self.vehicle.go_on_duty()

    # --- plumbing --------------------------------------------------------------------------

    def _rider_readiness(self, stop: dict[str, Any]) -> tuple[bool, float]:
        """Ask the rider agent, if there is one; otherwise assume a punctual rider.

        Asking rather than sampling here keeps one sampled truth per rider: the driver and
        the rider must not disagree about whether that person turned up.
        """
        if stop.get("stop_type") != STOP_PICKUP:
            return True, 0.0
        rider = self.engine.rider_for_request(uuid.UUID(stop["request_id"]))
        return rider.readiness() if rider is not None else (True, 0.0)

    def _accept_delay_seconds(self) -> float:
        return float(self._rng.uniform(ACCEPT_DELAY_MIN_SECONDS, ACCEPT_DELAY_MAX_SECONDS))

    def _boarding_delay_seconds(self) -> float:
        return float(self._rng.uniform(BOARDING_MIN_SECONDS, BOARDING_MAX_SECONDS))

    def _call(self, action: Any) -> bool:
        """Run one API call, recording a failure rather than ending the run.

        A driver whose phone fails a request keeps driving; so does this one. The failure
        is counted so a scenario can assert on it (S01: zero 5xx).
        """
        try:
            action()
        except Exception as exc:  # noqa: BLE001
            self.record.errors.append(f"{type(exc).__name__}: {exc}")
            self.engine.record(f"driver {self.driver_id} API call failed: {exc}")
            return False
        return True


@dataclass
class FleetSummary:
    """What the drivers did, for `metrics.json`."""

    drivers: int = 0
    on_duty: int = 0
    trips_started: int = 0
    trips_completed: int = 0
    stops_done: int = 0
    no_shows: int = 0
    faults: int = 0
    errors: int = 0


def summarise(records: list[DriverRecord]) -> FleetSummary:
    return FleetSummary(
        drivers=len(records),
        on_duty=sum(1 for record in records if record.went_on_duty),
        trips_started=sum(record.trips_started for record in records),
        trips_completed=sum(record.trips_completed for record in records),
        stops_done=sum(record.stops_done for record in records),
        no_shows=sum(record.no_shows for record in records),
        faults=sum(len(record.faults) for record in records),
        errors=sum(len(record.errors) for record in records),
    )
