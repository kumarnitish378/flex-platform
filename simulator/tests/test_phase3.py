"""Phase 3 in the simulator (M12): S10-S12 and the machinery they need."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from sim.agents.driver import RideLog, TripLog
from sim.assertions import evaluate
from sim.engine import Engine
from sim.events import EventInjector
from sim.metrics import OptimizerMetrics, RunMetrics
from sim.platform import OptimizerLedger, PlatformClient
from sim.pooling import PoolingMetrics, pooling_metrics
from sim.scenario import Assertions, Event, SupervisorPolicy, load_scenario

SCENARIOS = Path(__file__).resolve().parent.parent / "scenarios"
T0 = datetime(2026, 10, 5, 16, 0, tzinfo=UTC)
HOME = (28.50, 77.30)
OFFICE = (28.57, 77.32)


def metrics(**sections: Any) -> RunMetrics:
    result = RunMetrics(
        scenario="s", seed=1, routing="approx", started_at="a", ended_at="b", simulated_hours=1
    )
    for name, value in sections.items():
        setattr(result, name, value)
    return result


# --- the scenarios ------------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["pooling_efficiency", "night_safety", "optimizer_down"])
def test_the_phase_three_scenarios_load(name: str) -> None:
    scenario = load_scenario(SCENARIOS / f"{name}.yaml")

    assert scenario.name == name
    assert [entry.mode for entry in scenario.modes] == ["full_auto"]
    assert scenario.supervisor.policy is SupervisorPolicy.monitor


def test_night_safety_flags_a_share_of_riders_rounded_up() -> None:
    scenario = load_scenario(SCENARIOS / "night_safety.yaml")

    assert scenario.night_escort_employee_count == 14  # ceil(40 x 0.35)
    assert scenario.operator.config_overrides["night_safety_enabled"] is True


def test_the_outage_is_in_the_scenario_not_the_code() -> None:
    scenario = load_scenario(SCENARIOS / "optimizer_down.yaml")

    (event,) = scenario.events
    assert event.type == "optimizer_down" and event.duration_min == 20
    assert scenario.assertions.optimizer_outage_handled is True


# --- the assertions -----------------------------------------------------------------------------


def checks(assertions: Assertions, result: RunMetrics) -> set[str]:
    return {failure.check for failure in evaluate(assertions, result)}


def test_pooling_assertions_fail_when_not_measured_and_pass_when_met() -> None:
    asked = Assertions(riders_per_trip_min=1.5, detour_over_limit_max=0, vehicles_used_max=10)
    assert checks(asked, metrics()) == {
        "riders_per_trip_min",
        "detour_over_limit_max",
        "vehicles_used_max",
    }

    good = metrics(
        pooling=PoolingMetrics(
            trips_driven=10, vehicles_used=8, riders_per_trip=1.7, detour_over_limit=0
        )
    )
    assert checks(asked, good) == set()

    bad = metrics(
        pooling=PoolingMetrics(
            trips_driven=10, vehicles_used=12, riders_per_trip=1.1, detour_over_limit=2
        )
    )
    assert checks(asked, bad) == {
        "riders_per_trip_min",
        "detour_over_limit_max",
        "vehicles_used_max",
    }


def test_the_optimizer_must_actually_have_assigned_something() -> None:
    asked = Assertions(optimizer_assignments_min=5)

    assert checks(asked, metrics()) == {"optimizer_assignments_min"}
    assert checks(asked, metrics(optimizer=OptimizerMetrics(applied=4))) == {
        "optimizer_assignments_min"
    }
    assert checks(asked, metrics(optimizer=OptimizerMetrics(applied=5))) == set()


def test_a_night_safety_run_that_carried_no_flagged_rider_has_proved_nothing() -> None:
    asked = Assertions(night_safety_violations_max=0)

    assert checks(asked, metrics()) == {"night_safety_violations_max"}
    nobody = metrics(pooling=PoolingMetrics(night_flagged_carried=0, night_safety_violations=0))
    assert checks(asked, nobody) == {"night_safety_violations_max"}
    held = metrics(pooling=PoolingMetrics(night_flagged_carried=9, night_safety_violations=0))
    assert checks(asked, held) == set()
    broken = metrics(pooling=PoolingMetrics(night_flagged_carried=9, night_safety_violations=1))
    assert checks(asked, broken) == {"night_safety_violations_max"}


def handled(**fields: Any) -> RunMetrics:
    base: dict[str, Any] = {
        "outage_minutes": 20.0,
        "applied_while_down": 0,
        "suggested_while_down": 0,
        "alert_raised": True,
        "alert_resolved": True,
    }
    base.update(fields)
    return metrics(optimizer=OptimizerMetrics(**base))


def test_an_outage_is_handled_only_if_all_three_things_happened() -> None:
    asked = Assertions(optimizer_outage_handled=True)

    assert checks(asked, handled()) == set()
    assert checks(asked, metrics()) == {"optimizer_outage_handled"}  # no outage injected
    assert checks(asked, handled(alert_raised=False, alert_resolved=False)) == {
        "optimizer_outage_handled"
    }
    assert checks(asked, handled(alert_resolved=False)) == {"optimizer_outage_handled"}
    assert checks(asked, handled(applied_while_down=3)) == {"optimizer_outage_handled"}
    assert checks(asked, handled(suggested_while_down=1)) == {"optimizer_outage_handled"}


# --- night safety, judged on what was driven -----------------------------------------------------


def ride(rid: str, minutes_in: float, minutes_out: float) -> RideLog:
    place = (HOME, OFFICE)
    from sim.geo import LatLng

    return RideLog(
        request_id=rid,
        picked_up_at=T0 + timedelta(minutes=minutes_in),
        picked_up_at_place=LatLng(*place[0]),
        dropped_at=T0 + timedelta(minutes=minutes_out),
        dropped_at_place=LatLng(*place[1]),
    )


def trip(direction: str, rides: list[RideLog]) -> TripLog:
    log = TripLog(
        trip_id="t",
        vehicle_id="v",
        started_at=T0,
        odometer_start_km=0.0,
        odometer_end_km=10.0,
        direction=direction,
        completed=True,
    )
    log.rides = {r.request_id: r for r in rides}
    return log


def direct(a: Any, b: Any, at: Any) -> float:
    return 20.0


def night(logs: list[TripLog], flagged: set[str]) -> PoolingMetrics:
    return pooling_metrics(logs, direct, night_escort_riders=frozenset(flagged))


def test_going_to_the_office_the_lone_position_is_the_first_pickup() -> None:
    """Everyone is dropped together at the office, so the first one picked up rides alone."""
    flagged_first = trip("to_office", [ride("a", 0, 30), ride("b", 10, 30)])
    flagged_second = trip("to_office", [ride("a", 0, 30), ride("b", 10, 30)])

    assert night([flagged_first], {"a"}).night_safety_violations == 1
    assert night([flagged_second], {"b"}).night_safety_violations == 0


def test_coming_home_the_lone_position_is_the_last_drop() -> None:
    home = trip("from_office", [ride("a", 0, 20), ride("b", 0, 35)])

    assert night([home], {"b"}).night_safety_violations == 1
    assert night([home], {"a"}).night_safety_violations == 0


def test_a_solo_trip_cannot_breach_the_rule_and_an_unflagged_world_measures_nothing() -> None:
    solo = trip("to_office", [ride("a", 0, 30)])

    assert night([solo], {"a"}).night_safety_violations == 0
    assert night([solo], {"a"}).night_flagged_carried == 1
    assert night([solo], set()).night_safety_violations is None


@pytest.fixture
def engine() -> Engine:
    return Engine(load_scenario(SCENARIOS / "smoke_tiny.yaml"))


# --- the event and the ledger -------------------------------------------------


class SwitchBoard:
    def __init__(self) -> None:
        self.calls: list[bool] = []
        self.optimizer_down = False

    def set_optimizer(self, available: bool) -> None:
        self.calls.append(available)
        self.optimizer_down = not available

    def set_clock(self, now: Any) -> Any:
        return now


def test_the_outage_switches_the_optimizer_off_for_its_duration_then_on(engine: Engine) -> None:
    board = SwitchBoard()
    engine.platform = board  # type: ignore[assignment]
    injector = EventInjector(engine)
    injector.schedule(
        [Event(at_ist="06:10", type="optimizer_down", duration_min=20)]  # type: ignore[arg-type]
    )

    engine.run()

    assert board.calls == [False, True]
    (outage,) = engine.optimizer_outages
    assert outage[1] - outage[0] == timedelta(minutes=20)


def test_the_ledger_counts_what_the_platform_reports_and_separates_the_outage() -> None:
    client = PlatformClient("http://backend/api/v1")
    jump: dict[str, Any] = {"optimizer_runs": 2, "optimizer_applied": 3, "optimizer_failed": 0}

    client._note_optimizer(jump)
    client.optimizer_down = True
    client._note_optimizer({"optimizer_runs": 1, "optimizer_applied": 0, "optimizer_failed": 1})
    client._note_optimizer({"optimizer_applied": 2, "optimizer_suggested": 1})

    ledger: OptimizerLedger = client.optimizer
    assert (ledger.runs, ledger.applied, ledger.failed) == (3, 5, 1)
    assert (ledger.applied_while_down, ledger.suggested_while_down) == (2, 1)
