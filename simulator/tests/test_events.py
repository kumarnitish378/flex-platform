"""The event injector and traffic model (M07, `simulator-spec.md` sections 6 and 7)."""

from __future__ import annotations

from datetime import time
from pathlib import Path
from typing import Any

import pytest

from sim.engine import Engine, inject_events
from sim.events import (
    DEFAULT_DURATION_MINUTES,
    NOT_YET,
    SUPPORTED,
    EventInjector,
    UnsupportedEventError,
)
from sim.events import summarise as summarise_events
from sim.routing import ApproxRouting
from sim.scenario import Event, load_scenario
from sim.traffic import CLOSURE_FACTOR, RAIN_FACTOR, TrafficModel

SCENARIOS = Path(__file__).resolve().parent.parent / "scenarios"


@pytest.fixture
def engine() -> Engine:
    return Engine(load_scenario(SCENARIOS / "smoke_tiny.yaml"))


def event(type_: str, at: str = "06:10", **extra: Any) -> Event:
    hour, minute = (int(part) for part in at.split(":"))
    return Event(at_ist=time(hour, minute), type=type_, **extra)


# --- the traffic model ------------------------------------------------------------------


def test_an_ordinary_day_changes_nothing() -> None:
    assert TrafficModel().factor == 1.0


def test_rain_slows_the_roads() -> None:
    traffic = TrafficModel()

    traffic.begin("rain", RAIN_FACTOR)

    assert traffic.factor == pytest.approx(RAIN_FACTOR)
    assert traffic.is_active("rain")


def test_conditions_multiply() -> None:
    """Rain during a closure is slower than either alone - it is an ordinary Tuesday."""
    traffic = TrafficModel()

    traffic.begin("rain", RAIN_FACTOR)
    traffic.begin("road_closure", CLOSURE_FACTOR)

    assert traffic.factor == pytest.approx(RAIN_FACTOR * CLOSURE_FACTOR)


def test_one_condition_ending_leaves_the_others() -> None:
    """Resetting to 1.0 would silently cancel whatever else was still running."""
    traffic = TrafficModel()
    traffic.begin("rain", RAIN_FACTOR)
    traffic.begin("road_closure", CLOSURE_FACTOR)

    traffic.end("road_closure")

    assert traffic.factor == pytest.approx(RAIN_FACTOR)
    assert traffic.active == ("rain",)


def test_the_same_condition_twice_does_not_stack() -> None:
    traffic = TrafficModel()

    traffic.begin("rain", RAIN_FACTOR)
    traffic.begin("rain", RAIN_FACTOR)

    assert traffic.factor == pytest.approx(RAIN_FACTOR)


def test_ending_something_that_never_started_is_harmless() -> None:
    traffic = TrafficModel()
    traffic.end("rain")
    assert traffic.factor == 1.0


def test_a_zero_factor_is_refused() -> None:
    """Zero would divide by zero in the router and stop the fleet dead."""
    with pytest.raises(ValueError, match="positive"):
        TrafficModel().begin("rain", 0.0)


def test_it_drives_the_router() -> None:
    routing = ApproxRouting()
    traffic = TrafficModel(routing)

    traffic.begin("rain", RAIN_FACTOR)

    assert routing.traffic_factor == pytest.approx(RAIN_FACTOR)


def test_a_router_with_no_speed_knob_is_left_alone() -> None:
    """A real router returns real durations; there is nothing to scale (I02b)."""

    class Bare:
        pass

    bare = Bare()
    TrafficModel(bare).begin("rain", RAIN_FACTOR)

    assert not hasattr(bare, "traffic_factor")


# --- scheduling ---------------------------------------------------------------------------


def test_a_phase_two_event_is_refused_with_the_reason(engine: Engine) -> None:
    """Approximating it would make S07 report a VIP result it never tested."""
    injector = EventInjector(engine)

    with pytest.raises(UnsupportedEventError, match="which employees are VIP"):
        injector.schedule([event("vip_burst")])


def test_every_unimplementable_event_explains_itself() -> None:
    assert set(NOT_YET) == {"vip_burst", "optimizer_down"}
    for reason in NOT_YET.values():
        assert len(reason) > 20


def test_an_unknown_event_type_is_refused(engine: Engine) -> None:
    with pytest.raises(UnsupportedEventError, match="Unknown event type"):
        EventInjector(engine).schedule([event("earthquake")])


def test_validation_happens_before_anything_fires(engine: Engine) -> None:
    """A bad scenario should fail at the start, not ninety simulated minutes in."""
    injector = EventInjector(engine)

    with pytest.raises(UnsupportedEventError):
        injector.schedule([event("rain"), event("optimizer_down")])

    engine.run()
    assert injector.record.fired == []


def test_every_supported_type_has_a_handler(engine: Engine) -> None:
    injector = EventInjector(engine)
    for name in SUPPORTED:
        assert hasattr(injector, f"_on_{name}"), name


def test_an_event_outside_the_run_is_skipped_not_fired(engine: Engine) -> None:
    """smoke_tiny is one hour from 06:00; 23:00 never arrives."""
    injector = EventInjector(engine)
    injector.schedule([event("rain", at="23:00")])

    engine.run()

    assert injector.record.fired == []
    assert injector.record.skipped == ["rain"]


# --- firing -----------------------------------------------------------------------------


def test_rain_starts_and_stops(engine: Engine) -> None:
    injector = EventInjector(engine)
    injector.schedule([event("rain", at="06:10", duration_min=10)])

    engine.run()

    assert injector.record.fired == ["rain"]
    # Ended inside the run, so the roads are back to normal by the end of it.
    assert engine.traffic.factor == pytest.approx(1.0)


def test_rain_is_in_force_while_it_lasts(engine: Engine) -> None:
    engine.spawn(lambda: _watch_for_rain(engine))
    EventInjector(engine).schedule([event("rain", at="06:10", duration_min=20)])

    engine.run()

    assert engine.observed_rain  # type: ignore[attr-defined]


def _watch_for_rain(engine: Engine) -> Any:
    engine.observed_rain = False  # type: ignore[attr-defined]
    while True:
        if engine.traffic.is_active("rain"):
            engine.observed_rain = True  # type: ignore[attr-defined]
        yield engine.env.timeout(60)


def test_rain_with_no_duration_still_ends(engine: Engine) -> None:
    injector = EventInjector(engine)
    injector.schedule([event("rain", at="06:05")])

    engine.run()

    assert DEFAULT_DURATION_MINUTES > 0
    assert injector.record.fired == ["rain"]


def test_a_road_closure_is_a_separate_condition(engine: Engine) -> None:
    injector = EventInjector(engine)
    injector.schedule(
        [event("rain", at="06:05", duration_min=40), event("road_closure", at="06:10")]
    )

    engine.run()
    assert sorted(injector.record.fired) == ["rain", "road_closure"]


def test_an_event_with_nothing_to_act_on_is_recorded_not_fatal(engine: Engine) -> None:
    """A bare engine has no supervisor. The run must still finish and say why."""
    injector = EventInjector(engine)
    injector.schedule([event("supervisor_absent", at="06:05")])

    engine.run()

    assert injector.record.fired == ["supervisor_absent"]
    assert any("no supervisor" in message for message in injector.record.errors)


def test_a_breakdown_with_no_drivers_is_recorded(engine: Engine) -> None:
    injector = EventInjector(engine)
    injector.schedule([event("vehicle_breakdown", at="06:05")])

    engine.run()

    assert any("no drivers" in message for message in injector.record.errors)


# --- surge sizing --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("kwargs", "population", "expected"),
    [
        ({"count": 7}, 300, 7),
        ({"multiplier": 1.15}, 300, 45),
        ({"multiplier": 2.0}, 10, 10),
        ({}, 100, 10),
        ({"multiplier": 1.001}, 10, 1),
    ],
)
def test_surge_size(engine: Engine, kwargs: dict[str, Any], population: int, expected: int) -> None:
    """`multiplier: 1.15` means 15% *more* than the day already has, not 115% of it."""
    injector = EventInjector(engine)
    assert injector._surge_size(event("demand_surge", **kwargs), population) == expected


def test_a_surge_with_nobody_spare_is_recorded(engine: Engine) -> None:
    injector = EventInjector(engine)
    injector.schedule([event("demand_surge", at="06:05")])

    engine.run()

    assert any("already travelling" in message for message in injector.record.errors)


# --- wiring and summary ----------------------------------------------------------------------


def test_the_scenario_arms_its_own_events() -> None:
    engine = Engine(load_scenario(SCENARIOS / "gps_loss.yaml"))

    inject_events(engine)

    assert engine.events is not None
    assert engine._events_scheduled == 2


def test_the_summary_counts_what_happened(engine: Engine) -> None:
    injector = EventInjector(engine)
    injector.schedule([event("rain", at="06:05", duration_min=5)])
    engine.run()

    summary = summarise_events(injector, scheduled=1)

    assert summary.scheduled == 1
    assert summary.fired == 1
    assert summary.types == ("rain",)


def test_no_injector_means_an_empty_summary() -> None:
    assert summarise_events(None).fired == 0


# --- `at_ist` -------------------------------------------------------------------------------


def test_a_time_inside_the_run_resolves(engine: Engine) -> None:
    moment = engine.at_ist(time(6, 30))

    assert moment is not None
    assert engine.now() <= moment <= engine.scenario.end


def test_a_time_outside_the_run_does_not(engine: Engine) -> None:
    assert engine.at_ist(time(23, 0)) is None


def test_an_early_morning_time_rolls_to_the_next_day() -> None:
    """A 16-hour run starting at 06:00 IST covers 02:00 only on the following morning."""
    engine = Engine(load_scenario(SCENARIOS / "rain_day.yaml"))

    assert engine.at_ist(time(22, 0)) is not None
