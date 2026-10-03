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
    #: Stops the backend had already resolved before this driver got to them - a rider
    #: who cancelled en route, not a fault.
    stale_stops: int = 0
    no_shows: int = 0
    #: Who shared each trip, keyed by trip id. The driver is the only agent that sees a
    #: whole trip's stop list, so this is where "was this rider pooled?" can be answered
    #: without inventing an endpoint (S07).
    riders_per_trip: dict[str, set[str]] = field(default_factory=dict)
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
        platform_driver_id: uuid.UUID | None = None,
    ) -> None:
        self.engine = engine
        self.driver_id = driver_id
        #: The platform's own id for this driver, which is how the shared trip board
        #: groups work. `driver_id` above is a label for the run log ("driver-7"), so it
        #: cannot be used for this - and `None` simply means "poll for yourself".
        self.platform_driver_id = platform_driver_id
        self.token = token
        self.vehicle = vehicle
        self.credentials = credentials
        self.record = DriverRecord(driver_id=driver_id)
        self._late_start_p = late_start_probability
        self._rng: np.random.Generator = engine.rng.for_agent(f"driver:{driver_id}")
        self._handled: set[uuid.UUID] = set()
        #: What the backend last refused, per stop. A stuck stop is only diagnosable if
        #: the reason survives: "could not finish stop <uuid>" on its own sent me reading
        #: a six-hour run's log for an hour.
        self._last_refusal: dict[uuid.UUID, str] = {}
        #: Set by `_call` when the backend refuses, so the caller can attribute it.
        self._refused: str | None = None
        #: Set once this driver has reported a breakdown. The cab is off the road and the
        #: backend has ended its trip, so there is nothing left to tap through.
        self.broken_down = False

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
            if self.broken_down:
                # The cab is off the road. A broken-down driver does not keep asking
                # dispatch for work, and the backend would not send them any.
                continue
            trip = self._next_trip()
            if trip is not None:
                yield from self.drive(trip)

    def _next_trip(self) -> dict[str, Any] | None:
        """Whatever dispatch has given this driver and they have not driven yet.

        Read from the shared trip board when there is one (OQ-26): thirty-five drivers
        each polling for themselves is thirty-five blocking calls a simulated minute.
        Every *action* still goes through this driver's own token.
        """
        board = self.engine.trip_board
        if board is not None and self.platform_driver_id is not None:
            for trip in board.trips_of(self.platform_driver_id):
                if uuid.UUID(str(trip["id"])) not in self._handled:
                    return trip
            return None

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
        self._note_riders(trip_id, trip)
        self.engine.record(f"driver {self.driver_id} started trip {trip_id}")

        attempted: set[uuid.UUID] = set()
        stuck: set[uuid.UUID] = set()
        while True:
            if self.broken_down:
                # The cab stopped working. The backend has already ended this trip
                # (`trip-lifecycle.md`: breakdown -> aborted), so carrying on would be a
                # driver tapping through a trip that no longer exists.
                self.engine.record(f"driver {self.driver_id} abandoned trip {trip_id}")
                return
            stop = self._next_stop(trip_id, stuck)
            if stop is None:
                break
            stop_id = uuid.UUID(stop["id"])
            if stop_id in attempted:
                # Worked once and still not finished - a no-show the backend refused to
                # accept yet, or a rider who cancelled at the kerb. Retrying would spin
                # for the rest of the run, and *abandoning the trip* would strand the
                # people already in the cab, so the driver leaves this one behind and
                # drives the rest. The trip will fail to complete, which is the truth.
                stuck.add(stop_id)
                why = self._last_refusal.get(stop_id, "no refusal recorded")
                kind = stop.get("stop_type", "stop")
                self.record.errors.append(f"stop stuck ({kind}): {why}")
                self.engine.record(
                    f"driver {self.driver_id} could not finish {kind} stop {stop_id}: {why}"
                )
                if kind == "drop":
                    # The rider is in the cab and will now never be dropped, so they stay
                    # `picked_up` for the rest of the run. Worth saying out loud: it is
                    # the one way a stuck stop strands somebody rather than just skipping
                    # them, and it reads as `still_riding` in the metrics.
                    self.engine.record(
                        f"driver {self.driver_id} is carrying a rider it cannot drop off"
                    )
                continue
            attempted.add(stop_id)
            yield from self._work_a_stop(trip_id, stop)

        if self.broken_down:
            return
        if self._call(lambda: platform.complete_trip(self.token, trip_id, self.engine.now())):
            self.record.trips_completed += 1
            self.engine.record(f"driver {self.driver_id} completed trip {trip_id}")

    def _next_stop(
        self, trip_id: uuid.UUID, skip: set[uuid.UUID] | None = None
    ) -> dict[str, Any] | None:
        """The first stop of this trip still to do, re-read from the platform.

        Re-read rather than taken from the list the trip was polled with: dispatch adds
        riders to a trip already under way (SUP-03), and a driver app polls, so it sees
        the new stop. Working a snapshot meant the extra rider was never collected and
        the driver then tried to complete a trip with unfinished stops - a 409, a rider
        left standing, and a `smoke_tiny` failure that looked like a measurement
        artefact.
        """
        # Deliberately the driver's **own** read, not the shared board: this runs between
        # every stop, and a minute-stale view would hand the driver a stop they have just
        # finished. The same staleness trap the refused-cancellation chase fell into.
        platform = self.engine.platform
        assert platform is not None
        try:
            trips = platform.driver_trips(self.token, scope="active")
        except Exception as exc:  # noqa: BLE001 - a poll failure is not a crash
            self.record.errors.append(f"poll: {type(exc).__name__}")
            return None

        for trip in trips:
            if uuid.UUID(trip["id"]) != trip_id:
                continue
            self._note_riders(trip_id, trip)
            pending = [
                stop
                for stop in trip.get("stops", [])
                if stop["status"] not in FINISHED_STOP_STATUSES
                and uuid.UUID(stop["id"]) not in (skip or set())
            ]
            if not pending:
                return None
            return min(pending, key=lambda item: item["sequence"])
        # The trip is no longer active - cancelled or aborted under the driver.
        return None

    def _note_riders(self, trip_id: uuid.UUID, trip: dict[str, Any]) -> None:
        """Who this driver is actually carrying, including riders added mid-trip.

        S07 reads this to check a VIP was never pooled, and a trip that gained a second
        rider after the VIP boarded breaks that rule just as surely as one planned that
        way.
        """
        riders = self.record.riders_per_trip.setdefault(str(trip_id), set())
        riders.update(
            str(stop["request_id"])
            for stop in trip.get("stops", [])
            if stop.get("request_id") is not None
        )

    def _work_a_stop(self, trip_id: uuid.UUID, stop: dict[str, Any]) -> Process:
        """Drive there, arrive, wait for the rider, then finish or call a no-show."""
        platform = self.engine.platform
        assert platform is not None

        destination = LatLng(lat=stop["location"]["lat"], lng=stop["location"]["lng"])
        yield from self.vehicle.drive_to(destination)

        stop_id = uuid.UUID(stop["id"])
        here = self.vehicle.position
        self._refused = None
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
        self._refused = None
        if self._call(
            lambda: platform.stop_action(
                self.token, stop_id, "done", self.engine.now(), position.lat, position.lng
            )
        ):
            self.record.stops_done += 1
        elif self._refused is not None:
            self._last_refusal[stop_id] = self._refused

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
            self.broken_down = True
            self.record.faults.append("breakdown")
            self.vehicle.go_off_duty()
            self.engine.record(f"driver {self.driver_id} broke down")

    def lose_gps(self, minutes: float) -> Process:
        """The receiver loses its fix. Still on duty; those positions never existed.

        Deliberately not `go_off_duty()`: off duty means no GPS is collected at all, a
        privacy rule rather than a fault, and a cab parked off duty is a different thing
        to the supervisor than a working cab that has gone dark.
        """
        self.record.faults.append(f"gps_loss_{minutes:.0f}min")
        self.vehicle.lose_fix()
        yield self.engine.env.timeout(minutes * 60)
        self.vehicle.regain_fix()

    def go_offline(self, minutes: float) -> Process:
        """The phone loses network. Positions are recorded and uploaded on reconnect (S06)."""
        self.record.faults.append(f"offline_{minutes:.0f}min")
        self.vehicle.disconnect()
        yield self.engine.env.timeout(minutes * 60)
        uploaded = self.vehicle.reconnect()
        self.record.faults.append(f"uploaded_{uploaded}")

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
            if _is_a_stop_that_moved_on(exc):
                # The rider cancelled while this driver was en route, so the backend
                # skipped their stop - correctly - and the driver is holding a snapshot
                # from before that. A real driver app refreshes and drives on; counting
                # it as an error would make every cancellation look like a fault.
                self.record.stale_stops += 1
                self.engine.record(f"driver {self.driver_id} found a stop already resolved")
                return False
            self.record.errors.append(f"{type(exc).__name__}: {exc}")
            self.engine.record(f"driver {self.driver_id} API call failed: {exc}")
            self._refused = str(exc)
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
    #: Stops the backend had already resolved before this driver got to them - a rider
    #: who cancelled en route, not a fault.
    stale_stops: int = 0
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
        stale_stops=sum(record.stale_stops for record in records),
        no_shows=sum(record.no_shows for record in records),
        faults=sum(len(record.faults) for record in records),
        errors=sum(len(record.errors) for record in records),
    )


#: The backend's wording when a stop has already been skipped or finished under a driver
#: who is still acting on an older view of the trip.
_RESOLVED_STOP_MESSAGES = ("from skipped to", "from done to", "Stop not found")


def _is_a_stop_that_moved_on(exc: Exception) -> bool:
    text = str(exc)
    return any(message in text for message in _RESOLVED_STOP_MESSAGES)
