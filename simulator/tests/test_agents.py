"""Rider and driver behaviour (M05, `simulator-spec.md` sections 5.1-5.2).

Driven against a fake platform rather than a live backend, so the *behaviour* - when a
rider asks, when they give up, how a driver works a stop - is checked in milliseconds and
in CI. That the same calls work against the real API is `test_closed_loop_live.py`.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from sim.agents.driver import DriverAgent
from sim.agents.driver import summarise as summarise_fleet
from sim.agents.employee import (
    PATIENCE_FLOOR_MINUTES,
    Direction,
    EmployeeAgent,
    EmployeeProfile,
    Outcome,
)
from sim.agents.employee import summarise as summarise_demand
from sim.agents.vehicle import VehicleAgent, VehicleConfig
from sim.engine import Engine
from sim.geo import LatLng
from sim.platform import CreatedRequest, DutyCredentials
from sim.scenario import load_scenario

SCENARIOS = Path(__file__).resolve().parent.parent / "scenarios"

DEPOT = LatLng(lat=28.5355, lng=77.3910)
HOME = LatLng(lat=28.5600, lng=77.4000)
NO_NOISE = VehicleConfig(speed_noise_sigma=0.0, gps_noise_metres=0.0)


class FakePlatform:
    """Records what the agents asked for, and answers with whatever the test wants."""

    def __init__(self, status_sequence: list[str] | None = None) -> None:
        self.created: list[dict[str, Any]] = []
        self.cancelled: list[uuid.UUID] = []
        self.started: list[uuid.UUID] = []
        self.completed: list[uuid.UUID] = []
        self.stop_actions: list[tuple[uuid.UUID, str]] = []
        self.issues: list[str] = []
        self.trips: list[dict[str, Any]] = []
        self._statuses = list(status_sequence or ["queued"])
        self.fail_on: set[str] = set()
        #: Stops this platform refuses to move, like a no-show it will not accept yet.
        self.refuse_stops: set[uuid.UUID] = set()

    # --- what the rider uses ------------------------------------------------

    def create_request(self, **kwargs: Any) -> CreatedRequest:
        if "create" in self.fail_on:
            raise RuntimeError("backend said no")
        self.created.append(kwargs)
        return CreatedRequest(id=uuid.uuid4(), status="queued")

    def request_status(self, token: str, request_id: uuid.UUID) -> str:
        return self._statuses.pop(0) if len(self._statuses) > 1 else self._statuses[0]

    def cancel_request(self, token: str, request_id: uuid.UUID, reason: str) -> str:
        if "cancel" in self.fail_on:
            raise RuntimeError("backend said no")
        self.cancelled.append(request_id)
        return "cancelled"

    # --- what the driver uses -------------------------------------------------

    def driver_trips(self, token: str, scope: str = "active") -> list[dict[str, Any]]:
        if "poll" in self.fail_on:
            raise RuntimeError("backend said no")
        return self.trips

    def start_trip(self, token: str, trip_id: uuid.UUID, at: datetime) -> dict[str, Any]:
        if "start" in self.fail_on:
            raise RuntimeError("backend said no")
        self.started.append(trip_id)
        return {}

    def complete_trip(self, token: str, trip_id: uuid.UUID, at: datetime) -> dict[str, Any]:
        self.completed.append(trip_id)
        return {}

    def stop_action(
        self,
        token: str,
        stop_id: uuid.UUID,
        action: str,
        at: datetime,
        lat: float | None = None,
        lng: float | None = None,
    ) -> dict[str, Any]:
        if action in self.fail_on:
            raise RuntimeError("backend said no")
        self.stop_actions.append((stop_id, action))
        if stop_id in self.refuse_stops:
            # Arrived is accepted, finishing is not - so the stop stays unfinished.
            if action != "arrived":
                raise RuntimeError("backend said no")
            return {}
        # The real backend moves the stop, and the driver re-reads its stops between
        # them. A double that never moved would hand the driver the same stop forever.
        for trip in self.trips:
            for stop in trip.get("stops", []):
                if str(stop["id"]) == str(stop_id) and action in {"arrived", "done", "no_show"}:
                    stop["status"] = {"arrived": "arrived", "done": "done", "no_show": "skipped"}[
                        action
                    ]
        return {}

    def report_issue(self, token: str, issue_type: str, note: str | None = None, **kw: Any) -> Any:
        self.issues.append(issue_type)
        return {}

    def set_clock(self, now: datetime) -> datetime:
        return now


@pytest.fixture
def engine() -> Engine:
    scenario = load_scenario(SCENARIOS / "smoke_tiny.yaml")
    return Engine(scenario)


def with_platform(engine: Engine, platform: FakePlatform) -> FakePlatform:
    engine.platform = platform  # type: ignore[assignment]
    return platform


def profile(engine: Engine, **overrides: Any) -> EmployeeProfile:
    base: dict[str, Any] = {
        "employee_id": "emp-1",
        "token": "rider-token",
        "home": HOME,
        "shift_start": engine.clock.start + timedelta(minutes=50),
        "shift_end": engine.clock.start + timedelta(hours=9),
        # Tests about what a rider does need the rider to travel; the participation
        # draw has its own test.
        "participation": 1.0,
    }
    base.update(overrides)
    return EmployeeProfile(**base)


# --- the rider (section 5.2) ---------------------------------------------------------


def test_a_rider_asks_before_their_shift(engine: Engine) -> None:
    """Demand bunches before a shift; that shape is the point of the model."""
    platform = with_platform(engine, FakePlatform(["queued", "dropped"]))
    rider = EmployeeAgent(engine, profile(engine))
    engine.spawn(rider.day)

    engine.run()

    assert len(platform.created) == 1
    assert platform.created[0]["direction"] == str(Direction.to_office)


def test_a_rider_who_is_not_travelling_asks_for_nothing(engine: Engine) -> None:
    """Participation probability: not everyone commutes every day."""
    platform = with_platform(engine, FakePlatform())
    rider = EmployeeAgent(engine, profile(engine, participation=0.0))
    engine.spawn(rider.day)

    engine.run()

    assert platform.created == []
    assert rider.record.outcome is Outcome.not_travelling


def test_a_rider_whose_window_already_passed_does_not_ask_late(engine: Engine) -> None:
    """Asking late would invent demand the scenario never described."""
    platform = with_platform(engine, FakePlatform())
    past = engine.clock.start - timedelta(hours=3)
    rider = EmployeeAgent(engine, profile(engine, shift_start=past, shift_end=past))
    engine.spawn(rider.day)

    engine.run()
    assert platform.created == []


def test_a_completed_ride_is_recorded_as_completed(engine: Engine) -> None:
    platform = with_platform(engine, FakePlatform(["queued", "dropped"]))
    rider = EmployeeAgent(engine, profile(engine))
    engine.spawn(rider.day)

    engine.run()

    assert rider.record.outcome is Outcome.completed
    assert platform.cancelled == []


def test_an_expired_request_is_recorded_as_expired(engine: Engine) -> None:
    """With nobody dispatching, this is what a request does - and it is terminal."""
    with_platform(engine, FakePlatform(["queued", "expired"]))
    rider = EmployeeAgent(engine, profile(engine))
    engine.spawn(rider.day)

    engine.run()
    assert rider.record.outcome is Outcome.expired


def test_a_rider_gives_up_after_their_patience_runs_out(engine: Engine) -> None:
    """The number the pilot is judged on: people stop waiting and find another way."""
    platform = with_platform(engine, FakePlatform(["queued"]))
    rider = EmployeeAgent(
        engine, profile(engine, shift_start=engine.clock.start + timedelta(minutes=6))
    )
    rider._rng = _patient_for(minutes=PATIENCE_FLOOR_MINUTES)  # type: ignore[attr-defined]
    engine.spawn(rider.day)

    engine.run()

    assert rider.record.outcome is Outcome.gave_up
    assert len(platform.cancelled) == 1
    assert rider.record.waited_minutes is not None


def test_a_rider_on_board_stops_counting_patience(engine: Engine) -> None:
    """Once you are in the cab, being slow is not a reason to cancel."""
    platform = with_platform(engine, FakePlatform(["queued", "picked_up", "dropped"]))
    rider = EmployeeAgent(engine, profile(engine))
    engine.spawn(rider.day)

    engine.run()

    assert platform.cancelled == []
    assert rider.record.outcome is Outcome.completed


class StillRiding(FakePlatform):
    """A rider who is in a moving cab when the demand window closes."""

    def __init__(self, engine: Engine, drop_after: timedelta | None) -> None:
        super().__init__(["queued", "picked_up"])
        self._engine = engine
        self._drop_at = None if drop_after is None else engine.scenario.end + drop_after

    def request_status(self, token: str, request_id: uuid.UUID) -> str:
        if self._drop_at is not None and self._engine.now() >= self._drop_at:
            return "dropped"
        return super().request_status(token, request_id)


def test_a_ride_still_running_at_the_window_is_allowed_to_finish(engine: Engine) -> None:
    """OQ-28. The run used to stop dead on the hour and record a rider in a moving cab
    as `unresolved`, failing `all_requests_terminal` for no reason but where the clock
    stopped - and only sometimes, which is worse."""
    with_platform(engine, StillRiding(engine, drop_after=timedelta(minutes=10)))
    rider = EmployeeAgent(engine, profile(engine))
    engine.riders.append(rider)
    engine.spawn(rider.day)

    summary = engine.run()

    assert rider.record.outcome is Outcome.completed
    assert 10 <= summary.drain_minutes <= 12
    assert summary.drain_capped is False


def test_a_ride_that_never_ends_still_fails_the_run(engine: Engine) -> None:
    """The cap is what keeps the drain a fix and not a cover-up: a genuinely stuck ride
    must still be reported."""
    with_platform(engine, StillRiding(engine, drop_after=None))
    rider = EmployeeAgent(engine, profile(engine))
    engine.riders.append(rider)
    engine.spawn(rider.day)

    summary = engine.run()

    assert rider.record.outcome is Outcome.unresolved
    assert rider.record.detail == "still riding when the run stopped"
    assert summary.drain_minutes == engine.scenario.drain_minutes_max
    assert summary.drain_capped is True


def test_a_scenario_can_refuse_to_wait(engine: Engine) -> None:
    """`drain_minutes_max: 0` is the old behaviour, kept for a scenario that wants to
    measure exactly its own window."""
    engine.scenario = engine.scenario.model_copy(update={"drain_minutes_max": 0.0})
    with_platform(engine, StillRiding(engine, drop_after=timedelta(minutes=10)))
    rider = EmployeeAgent(engine, profile(engine))
    engine.riders.append(rider)
    engine.spawn(rider.day)

    summary = engine.run()

    assert rider.record.outcome is Outcome.unresolved
    assert summary.drain_minutes == 0.0
    assert summary.drain_capped is True


def test_a_rider_nobody_came_for_is_unresolved(engine: Engine) -> None:
    """OQ-29. They asked for a cab and never got an answer. Counted as `not_travelling`
    this was the platform's worst failure recorded as no demand at all, and
    `all_requests_terminal` passed straight over it."""
    with_platform(engine, FakePlatform(["queued"]))
    rider = EmployeeAgent(engine, profile(engine, participation=1.0))
    engine.riders.append(rider)
    engine.spawn(rider.day)

    summary = engine.run()
    demand = summarise_demand([rider.record])

    assert rider.record.outcome is Outcome.unresolved
    assert rider.record.detail == "still waiting when the demand window closed"
    assert demand.requested == 1
    assert demand.still_waiting == 1
    assert demand.all_terminal is False
    assert summary.abandoned == 1


def test_a_rider_left_waiting_does_not_cancel_after_the_window(engine: Engine) -> None:
    """Their patience runs out during the drain, which is not a moment the day contained.
    Giving up there would report a cancellation that never happened and hide the
    abandonment behind a `gave_up`."""
    platform = with_platform(engine, FakePlatform(["queued"]))
    rider = EmployeeAgent(engine, profile(engine, participation=1.0))
    engine.riders.append(rider)
    engine.spawn(rider.day)

    engine.run()

    assert rider.record.patience_minutes is not None
    assert platform.cancelled == []
    assert rider.record.outcome is Outcome.unresolved


def test_the_two_halves_of_unresolved_are_told_apart(engine: Engine) -> None:
    """Nobody came, and the ride never ended, are different failures - and only the
    first is the platform losing a rider."""
    with_platform(engine, StillRiding(engine, drop_after=None))
    riding = EmployeeAgent(engine, profile(engine))
    engine.riders.append(riding)
    engine.spawn(riding.day)

    engine.run()
    demand = summarise_demand([riding.record])

    assert demand.still_riding == 1
    assert demand.still_waiting == 0
    assert demand.unresolved == 1


def test_a_rider_who_stayed_home_is_not_counted_as_waiting(engine: Engine) -> None:
    rider = EmployeeAgent(engine, profile(engine, participation=0.0))
    engine.riders.append(rider)
    engine.spawn(rider.day)

    engine.run()
    summary = summarise_demand([rider.record])

    assert summary.not_travelling == 1
    assert summary.still_waiting == 0


def test_a_run_nobody_is_riding_through_does_not_wait(engine: Engine) -> None:
    """A healthy run pays nothing for the drain."""
    with_platform(engine, FakePlatform(["queued", "dropped"]))
    rider = EmployeeAgent(engine, profile(engine))
    engine.riders.append(rider)
    engine.spawn(rider.day)

    summary = engine.run()

    assert rider.record.outcome is Outcome.completed
    assert summary.drain_minutes == 0.0
    assert summary.drain_capped is False


class CollectedAtTheLastMoment(FakePlatform):
    """The cab arrives exactly as patience runs out, so the cancellation is refused."""

    def __init__(self) -> None:
        super().__init__(["queued"])
        self.collected = False

    def cancel_request(self, token: str, request_id: uuid.UUID, reason: str) -> str:
        # `trip-lifecycle.md` section 1: an employee may cancel only until `picked_up`.
        self.collected = True
        raise RuntimeError("409: already picked up")

    def request_status(self, token: str, request_id: uuid.UUID) -> str:
        return "dropped" if self.collected else "queued"


def test_a_rider_collected_as_patience_ran_out_is_not_a_failure(
    engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The status board is a minute stale, so this is a real race and the platform is
    right to refuse. Recording it as a failed API call reported three riders who were
    sitting in a moving cab as a platform error - and failed `evening_surge` for it."""
    # Patience short enough to run out inside the scenario's hour.
    monkeypatch.setattr("sim.agents.employee.PATIENCE_MEAN_MINUTES", 10.0)
    monkeypatch.setattr("sim.agents.employee.PATIENCE_SIGMA_MINUTES", 0.0)
    platform = CollectedAtTheLastMoment()
    with_platform(engine, platform)
    rider = EmployeeAgent(engine, profile(engine))
    engine.riders.append(rider)
    engine.spawn(rider.day)

    engine.run()

    assert platform.collected is True, "the rider did try to give up"
    assert rider.record.outcome is Outcome.completed
    assert rider.record.detail is None


def test_the_refusal_is_checked_against_the_platform_not_the_stale_board(
    engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The board is a minute behind, and that staleness is *why* the cancellation was
    refused - so checking it there misses the very case this exists for. It cost a whole
    `evening_surge` run to find that out."""
    monkeypatch.setattr("sim.agents.employee.PATIENCE_MEAN_MINUTES", 10.0)
    monkeypatch.setattr("sim.agents.employee.PATIENCE_SIGMA_MINUTES", 0.0)
    platform = CollectedAtTheLastMoment()
    with_platform(engine, platform)
    rider = EmployeeAgent(engine, profile(engine))
    engine.riders.append(rider)

    class LaggingBoard:
        """A minute behind the platform, like the real one."""

        def __init__(self) -> None:
            self.reads_since_pickup = 0

        def status_of(self, request_id: uuid.UUID) -> str:
            if not platform.collected:
                return "queued"
            self.reads_since_pickup += 1
            return "queued" if self.reads_since_pickup <= 1 else "dropped"

        def note(self, request_id: uuid.UUID, status: str) -> None:
            pass

    engine.board = LaggingBoard()  # type: ignore[assignment]
    engine.spawn(rider.day)

    engine.run()

    assert rider.record.outcome is Outcome.completed


def test_a_refused_request_is_recorded_not_raised(engine: Engine) -> None:
    """One rider's bad day must not end the run."""
    platform = with_platform(engine, FakePlatform())
    platform.fail_on.add("create")
    rider = EmployeeAgent(engine, profile(engine))
    engine.spawn(rider.day)

    engine.run()

    assert rider.record.outcome is Outcome.failed
    assert rider.record.detail is not None


def test_a_rider_with_no_platform_does_nothing(engine: Engine) -> None:
    """Offline runs still move cabs; they just have no API to ask."""
    rider = EmployeeAgent(engine, profile(engine))
    engine.spawn(rider.day)

    engine.run()
    assert rider.record.request_id is None


def test_readiness_is_sampled_once_per_rider(engine: Engine) -> None:
    """The driver asks the rider, so both sides agree on whether they turned up."""
    rider = EmployeeAgent(engine, profile(engine))

    present, late = rider.readiness()
    assert isinstance(present, bool)
    assert late >= 0.0


# --- the driver (section 5.1) ------------------------------------------------------------


def vehicle_for(engine: Engine) -> VehicleAgent:
    return VehicleAgent(engine, "vehicle-1", DEPOT, engine.pings, NO_NOISE)


def credentials() -> DutyCredentials:
    return DutyCredentials(
        vehicle_id=uuid.uuid4(),
        host="localhost",
        port=1883,
        username="veh-1",
        password="secret",
        topic_prefix="sc/v1/op/o/veh/v",
    )


def driver_for(engine: Engine, late_start: float = 0.0) -> DriverAgent:
    return DriverAgent(
        engine,
        driver_id="driver-1",
        token="driver-token",
        vehicle=vehicle_for(engine),
        credentials=credentials(),
        late_start_probability=late_start,
    )


def a_trip(stop_count: int = 2) -> dict[str, Any]:
    trip_id = str(uuid.uuid4())
    request_id = str(uuid.uuid4())
    kinds = ["pickup", "drop"]
    return {
        "id": trip_id,
        "stops": [
            {
                "id": str(uuid.uuid4()),
                "sequence": index + 1,
                "stop_type": kinds[index % 2],
                "request_id": request_id,
                "status": "pending",
                "location": {"lat": 28.55 + index * 0.01, "lng": 77.39},
            }
            for index in range(stop_count)
        ],
    }


def test_a_driver_goes_on_duty(engine: Engine) -> None:
    with_platform(engine, FakePlatform())
    driver = driver_for(engine)
    engine.spawn(driver.shift)

    engine.run()

    assert driver.record.went_on_duty is True
    assert driver.vehicle.on_duty is True


def test_a_parked_driver_still_pings(engine: Engine) -> None:
    """A cab with no work must not vanish from the supervisor's map."""
    with_platform(engine, FakePlatform())
    driver = driver_for(engine)
    engine.spawn(driver.shift)

    engine.run()
    assert engine.pings.pings


def test_a_driver_works_a_trip_end_to_end(engine: Engine) -> None:
    platform = with_platform(engine, FakePlatform())
    platform.trips = [a_trip()]
    driver = driver_for(engine)
    engine.spawn(driver.shift)

    engine.run()

    assert driver.record.trips_started == 1
    assert driver.record.trips_completed == 1
    assert driver.record.stops_done == 2


def test_stops_are_worked_in_order(engine: Engine) -> None:
    """A trip's sequence is the route; doing it out of order strands riders."""
    platform = with_platform(engine, FakePlatform())
    trip = a_trip(stop_count=2)
    platform.trips = [trip]
    engine.spawn(driver_for(engine).shift)

    engine.run()

    arrived = [stop_id for stop_id, action in platform.stop_actions if action == "arrived"]
    assert arrived == [uuid.UUID(stop["id"]) for stop in trip["stops"]]


def test_a_rider_added_after_the_trip_started_is_still_collected(engine: Engine) -> None:
    """Dispatch adds riders to a trip already under way (SUP-03), and a driver app polls,
    so it sees the new stop. Working the list the trip was polled with left the extra
    rider standing on the kerb and the driver completing a trip with unfinished stops -
    which is what `smoke_tiny` had been failing on."""
    platform = with_platform(engine, FakePlatform())
    trip = a_trip(stop_count=2)
    platform.trips = [trip]
    driver = driver_for(engine)
    engine.spawn(driver.shift)

    latecomer = str(uuid.uuid4())

    def add_a_rider() -> Any:
        # Once the first pickup is done, somebody else joins the trip.
        while not any(action == "done" for _, action in platform.stop_actions):
            yield engine.env.timeout(60)
        trip["stops"].extend(
            {
                "id": str(uuid.uuid4()),
                "sequence": 3 + index,
                "stop_type": ["pickup", "drop"][index],
                "request_id": latecomer,
                "status": "pending",
                "location": {"lat": 28.57 + index * 0.01, "lng": 77.39},
            }
            for index in range(2)
        )

    engine.spawn(add_a_rider)
    engine.run()

    assert driver.record.stops_done == 4
    assert driver.record.trips_completed == 1
    assert latecomer in driver.record.riders_per_trip[trip["id"]]


def test_a_stop_that_cannot_be_finished_is_left_behind_not_retried(engine: Engine) -> None:
    """Re-reading the stops must not become a loop: a stop the backend will not move
    would otherwise be worked for the rest of the run."""
    platform = with_platform(engine, FakePlatform())
    platform.trips = [a_trip(stop_count=2)]
    platform.fail_on.add("arrived")
    driver = driver_for(engine)
    engine.spawn(driver.shift)

    engine.run()

    assert driver.record.stops_done == 0
    assert sum("stop stuck" in error for error in driver.record.errors) == 2
    # Each stop was attempted once and given up on once - never a third time.
    assert sum(action == "arrived" for _, action in platform.stop_actions) == 0


def test_a_driver_with_one_stuck_stop_still_drops_everyone_else(engine: Engine) -> None:
    """Abandoning the trip would strand the people already in the cab - which is exactly
    what `evening_surge` showed: five riders still aboard after the drain."""
    platform = with_platform(engine, FakePlatform())
    trip = a_trip(stop_count=2)
    platform.trips = [trip]
    # The first stop will not move: a no-show the backend refuses, or a rider who
    # cancelled while the cab was at the kerb.
    platform.refuse_stops.add(uuid.UUID(trip["stops"][0]["id"]))
    driver = driver_for(engine)
    engine.spawn(driver.shift)

    engine.run()

    assert driver.record.stops_done == 1, "the second rider still got their ride"
    assert any("stop stuck" in error for error in driver.record.errors)


def test_every_stop_is_arrived_before_it_is_done(engine: Engine) -> None:
    platform = with_platform(engine, FakePlatform())
    platform.trips = [a_trip()]
    engine.spawn(driver_for(engine).shift)

    engine.run()

    seen: set[uuid.UUID] = set()
    for stop_id, action in platform.stop_actions:
        if action == "done":
            assert stop_id in seen, "a stop was finished before the cab arrived"
        if action == "arrived":
            seen.add(stop_id)


def test_a_trip_is_driven_only_once(engine: Engine) -> None:
    """The driver polls repeatedly; the same trip must not be started twice."""
    platform = with_platform(engine, FakePlatform())
    platform.trips = [a_trip()]
    engine.spawn(driver_for(engine).shift)

    engine.run()
    assert len(platform.started) == 1


def test_a_missing_rider_becomes_a_no_show(engine: Engine) -> None:
    """DRV-05, and the driver waits the configured time first."""
    platform = with_platform(engine, FakePlatform())
    trip = a_trip()
    platform.trips = [trip]

    rider = EmployeeAgent(engine, profile(engine))
    rider.record.request_id = uuid.UUID(trip["stops"][0]["request_id"])
    rider.readiness = lambda: (False, 0.0)  # type: ignore[method-assign]
    engine.riders.append(rider)

    driver = driver_for(engine)
    engine.spawn(driver.shift)
    engine.run()

    assert ("no_show" in [action for _stop, action in platform.stop_actions]) is True
    assert driver.record.no_shows == 1


def test_a_failed_api_call_is_counted_not_fatal(engine: Engine) -> None:
    """A driver whose phone fails a request keeps driving. So does this one."""
    platform = with_platform(engine, FakePlatform())
    platform.trips = [a_trip()]
    platform.fail_on.add("start")
    driver = driver_for(engine)
    engine.spawn(driver.shift)

    engine.run()

    assert driver.record.trips_started == 0
    assert driver.record.errors


def test_a_poll_failure_does_not_end_the_shift(engine: Engine) -> None:
    platform = with_platform(engine, FakePlatform())
    platform.fail_on.add("poll")
    driver = driver_for(engine)
    engine.spawn(driver.shift)

    engine.run()

    assert driver.record.went_on_duty is True
    assert driver.record.errors


def test_a_breakdown_takes_the_cab_off_duty(engine: Engine) -> None:
    platform = with_platform(engine, FakePlatform())
    driver = driver_for(engine)
    driver.vehicle.go_on_duty()

    driver.break_down()

    assert platform.issues == ["breakdown"]
    assert driver.vehicle.on_duty is False
    assert "breakdown" in driver.record.faults


def test_a_late_driver_is_recorded_as_late(engine: Engine) -> None:
    with_platform(engine, FakePlatform())
    driver = driver_for(engine, late_start=1.0)
    engine.spawn(driver.shift)

    engine.run()

    assert any(fault.startswith("late_start") for fault in driver.record.faults)


# --- summaries ------------------------------------------------------------------------------


def test_the_demand_summary_counts_every_outcome(engine: Engine) -> None:
    rider = EmployeeAgent(engine, profile(engine))
    rider.record.outcome = Outcome.gave_up
    rider.record.request_id = uuid.uuid4()
    rider.record.waited_minutes = 41.0

    summary = summarise_demand([rider.record])

    assert summary.riders == 1
    assert summary.requested == 1
    assert summary.gave_up == 1
    assert summary.waits_minutes == [41.0]
    assert summary.all_terminal is True


def test_an_unresolved_rider_fails_the_terminal_check(engine: Engine) -> None:
    """S01's whole assertion: nothing may be left hanging."""
    rider = EmployeeAgent(engine, profile(engine))
    rider.record.outcome = Outcome.unresolved

    assert summarise_demand([rider.record]).all_terminal is False


def test_the_fleet_summary_adds_up(engine: Engine) -> None:
    driver = driver_for(engine)
    driver.record.went_on_duty = True
    driver.record.trips_started = 2
    driver.record.trips_completed = 1
    driver.record.stops_done = 3

    summary = summarise_fleet([driver.record])

    assert summary.drivers == 1
    assert summary.on_duty == 1
    assert summary.trips_started == 2
    assert summary.trips_completed == 1
    assert summary.stops_done == 3


# --- helpers -----------------------------------------------------------------------------------


class _FixedRng:
    """A generator that always draws the same number, to force a branch."""

    def __init__(self, value: float, normal_value: float = 40.0) -> None:
        self._value = value
        self._normal = normal_value

    def random(self) -> float:
        return self._value

    def normal(self, mean: float, sigma: float) -> float:
        return self._normal

    def uniform(self, low: float, high: float) -> float:
        return low

    def exponential(self, scale: float) -> float:
        return scale


def _always(value: float) -> Any:
    return _FixedRng(value)


def _patient_for(minutes: float) -> Any:
    """Travels, and runs out of patience after `minutes`."""
    return _FixedRng(0.0, normal_value=minutes)


# --- a rider who cancelled en route is not a driver fault (M07) --------------


def test_a_stop_resolved_under_the_driver_is_not_an_error(engine: Engine) -> None:
    """The rider cancelled while this cab was on its way; the backend skipped the stop.

    Counting that as a fault would make every cancellation look like a bug, and S04-S06
    assert on agent errors.
    """
    from sim.agents.driver import _is_a_stop_that_moved_on

    assert _is_a_stop_that_moved_on(RuntimeError("409: stop cannot go from skipped to arrived"))
    assert _is_a_stop_that_moved_on(RuntimeError("404: Stop not found"))
    assert not _is_a_stop_that_moved_on(RuntimeError("500: Internal server error"))


def test_a_real_failure_is_still_an_error() -> None:
    from sim.agents.driver import _is_a_stop_that_moved_on

    assert not _is_a_stop_that_moved_on(RuntimeError("connection refused"))


def test_a_broken_down_driver_stops_working(engine: Engine) -> None:
    """The backend has ended the trip; tapping through it would be a driver app bug.

    Found by S05, where a broken-down cab kept marking stops and the run reported four
    API failures that were really the backend correctly refusing.
    """
    platform = FakePlatform()
    platform.trips = [a_trip()]
    with_platform(engine, platform)
    driver = driver_for(engine)
    driver.broken_down = True

    engine.spawn(driver.shift)
    engine.run()

    assert driver.record.trips_started == 0
    assert driver.record.errors == []
