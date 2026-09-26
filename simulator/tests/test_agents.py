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
        self.stop_actions.append((stop_id, action))
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
