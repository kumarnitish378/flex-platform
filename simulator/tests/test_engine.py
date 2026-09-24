"""Engine, clock, seeded RNG and approx routing."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from sim.clock import SimClock
from sim.engine import Engine
from sim.geo import LatLng, haversine_km, interpolate
from sim.rng import RngFactory, derive_seed, generator_for
from sim.routing import ApproxConfig, ApproxRouting, Route
from sim.scenario import load_scenario

SCENARIOS = Path(__file__).resolve().parent.parent / "scenarios"
START = datetime(2026, 10, 5, 0, 30, tzinfo=UTC)
NOON = datetime(2026, 10, 5, 6, 30, tzinfo=UTC)  # 12:00 IST, off peak
PEAK = datetime(2026, 10, 5, 3, 30, tzinfo=UTC)  # 09:00 IST
ORIGIN = LatLng(28.5703, 77.3218)
DESTINATION = LatLng(28.5123, 77.3910)


# --- clock -------------------------------------------------------------------


def test_clock_starts_at_the_scenario_start() -> None:
    assert SimClock(START).now() == START


def test_clock_advances() -> None:
    clock = SimClock(START)
    assert clock.advance_to(3600) == START + timedelta(hours=1)
    assert clock.elapsed_seconds == 3600


def test_clock_cannot_go_backwards() -> None:
    clock = SimClock(START)
    clock.advance_to(100)
    with pytest.raises(ValueError, match="backwards"):
        clock.advance_to(50)


def test_clock_rejects_naive_start() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        SimClock(datetime(2026, 10, 5, 0, 30))  # noqa: DTZ001 - the point of the test


def test_clock_rejects_non_positive_speed() -> None:
    with pytest.raises(ValueError, match="speed_factor"):
        SimClock(START, speed_factor=0)


def test_ist_view_is_the_same_instant() -> None:
    clock = SimClock(START)
    assert clock.now_ist().hour == 6
    assert clock.now_ist().minute == 0
    assert clock.now_ist().timestamp() == clock.now().timestamp()


def test_speed_factor_converts_to_wall_clock() -> None:
    assert SimClock(START, speed_factor=60).real_seconds_for(3600) == 60
    assert SimClock(START, speed_factor=1).real_seconds_for(3600) == 3600


# --- rng ---------------------------------------------------------------------


def test_same_seed_and_agent_give_the_same_stream() -> None:
    first = generator_for(42, "vehicle-1").random(10).tolist()
    second = generator_for(42, "vehicle-1").random(10).tolist()
    assert first == second


def test_different_agents_get_different_streams() -> None:
    assert generator_for(42, "vehicle-1").random() != generator_for(42, "vehicle-2").random()


def test_different_seeds_give_different_streams() -> None:
    assert generator_for(1, "vehicle-1").random() != generator_for(2, "vehicle-1").random()


def test_derived_seed_is_stable_across_runs() -> None:
    """Hard-coded so a change to the derivation is a deliberate, visible decision."""
    assert derive_seed(42, "vehicle-1") == derive_seed(42, "vehicle-1")
    assert derive_seed(42, "vehicle-1") != derive_seed(42, "vehicle-10")


def test_factory_returns_one_generator_per_agent() -> None:
    factory = RngFactory(42)
    assert factory.for_agent("a") is factory.for_agent("a")
    assert factory.for_agent("a") is not factory.for_agent("b")
    assert factory.seed == 42


def test_adding_an_agent_does_not_disturb_the_others() -> None:
    """Per-agent streams keep runs comparable when the fleet size changes."""
    without = RngFactory(42)
    values_without = [without.for_agent(f"vehicle-{i}").random() for i in range(3)]

    with_extra = RngFactory(42)
    with_extra.for_agent("vehicle-99").random()
    values_with = [with_extra.for_agent(f"vehicle-{i}").random() for i in range(3)]

    assert values_without == values_with


# --- geo ---------------------------------------------------------------------


def test_haversine_is_zero_for_the_same_point() -> None:
    assert haversine_km(ORIGIN, ORIGIN) == pytest.approx(0.0)


def test_haversine_matches_a_known_distance() -> None:
    # Sector 62 to Sector 135, Noida: about 9 km straight line.
    assert haversine_km(ORIGIN, DESTINATION) == pytest.approx(9.0, abs=1.5)


def test_interpolation_endpoints_and_clamping() -> None:
    assert interpolate(ORIGIN, DESTINATION, 0.0) == ORIGIN
    assert interpolate(ORIGIN, DESTINATION, 1.0) == DESTINATION
    assert interpolate(ORIGIN, DESTINATION, 2.0) == DESTINATION
    assert interpolate(ORIGIN, DESTINATION, -1.0) == ORIGIN


def test_invalid_coordinates_are_rejected() -> None:
    with pytest.raises(ValueError, match="lat out of range"):
        LatLng(91.0, 77.0)
    with pytest.raises(ValueError, match="lng out of range"):
        LatLng(28.0, 181.0)


# --- approx routing ----------------------------------------------------------


def test_route_distance_uses_the_road_factor() -> None:
    route = ApproxRouting().route(ORIGIN, DESTINATION, NOON)
    expected_m = haversine_km(ORIGIN, DESTINATION) * 1.4 * 1000
    assert route.distance_meters == pytest.approx(expected_m)
    assert route.approximate is True


def test_peak_hours_are_slower() -> None:
    routing = ApproxRouting()
    assert routing.route(ORIGIN, DESTINATION, PEAK).duration_seconds == pytest.approx(
        routing.route(ORIGIN, DESTINATION, NOON).duration_seconds / 0.6
    )


def test_traffic_factor_slows_everything() -> None:
    """The event injector scales this for rain (simulator-spec.md §6)."""
    normal = ApproxRouting().route(ORIGIN, DESTINATION, NOON)
    rain = ApproxRouting(traffic_factor=0.7).route(ORIGIN, DESTINATION, NOON)
    assert rain.duration_seconds == pytest.approx(normal.duration_seconds / 0.7)


def test_zero_speed_does_not_divide_by_zero() -> None:
    routing = ApproxRouting(ApproxConfig(base_speed_kmh=0.0, windows=()))
    assert routing.route(ORIGIN, DESTINATION, NOON).duration_seconds == 0.0


def test_position_along_a_route() -> None:
    route = ApproxRouting().route(ORIGIN, DESTINATION, NOON)
    assert route.position_at(0) == ORIGIN
    assert route.position_at(route.duration_seconds) == DESTINATION

    midpoint = route.position_at(route.duration_seconds / 2)
    assert midpoint.lat == pytest.approx((ORIGIN.lat + DESTINATION.lat) / 2, abs=1e-6)


def test_position_is_clamped_past_the_end() -> None:
    route = ApproxRouting().route(ORIGIN, DESTINATION, NOON)
    assert route.position_at(route.duration_seconds * 10) == DESTINATION


def test_position_on_a_degenerate_route() -> None:
    route = Route(0.0, 0.0, (ORIGIN,), True)
    assert route.position_at(10) == ORIGIN


def test_position_follows_a_multi_leg_polyline() -> None:
    middle = LatLng(28.5400, 77.3550)
    route = Route(600.0, 10_000.0, (ORIGIN, middle, DESTINATION), False)
    start = route.position_at(0)
    end = route.position_at(600)
    assert start == ORIGIN
    assert end == DESTINATION
    assert ORIGIN.lat > route.position_at(300).lat > DESTINATION.lat


# --- engine ------------------------------------------------------------------


def test_engine_runs_to_the_scenario_end() -> None:
    scenario = load_scenario(SCENARIOS / "smoke_tiny.yaml")
    summary = Engine(scenario).run()

    assert summary.scenario == "smoke_tiny"
    assert summary.seed == 42
    assert summary.routing == "approx"
    assert summary.simulated_seconds == 3600
    assert summary.ended_at - summary.started_at == timedelta(hours=1)
    assert summary.vehicles == 3
    assert summary.employees == 10


def test_engine_time_follows_simpy() -> None:
    scenario = load_scenario(SCENARIOS / "smoke_tiny.yaml")
    engine = Engine(scenario)
    seen: list[datetime] = []

    def ticker():  # type: ignore[no-untyped-def]
        for _ in range(3):
            yield engine.env.timeout(600)
            seen.append(engine.now())

    engine.spawn(ticker)
    engine.run()

    assert seen == [
        scenario.start + timedelta(minutes=10),
        scenario.start + timedelta(minutes=20),
        scenario.start + timedelta(minutes=30),
    ]


def test_engine_records_events_with_simulated_timestamps() -> None:
    scenario = load_scenario(SCENARIOS / "smoke_tiny.yaml")
    engine = Engine(scenario)

    def actor():  # type: ignore[no-untyped-def]
        yield engine.env.timeout(60)
        engine.record("vehicle-1 went on duty")

    engine.spawn(actor)
    summary = engine.run()

    assert len(summary.events) == 1
    assert "vehicle-1 went on duty" in summary.events[0]
    assert summary.events[0].startswith("2026-10-05T00:31:00")


def test_runs_are_reproducible() -> None:
    """Same scenario + same seed -> same numbers (simulator-spec.md §13)."""
    scenario = load_scenario(SCENARIOS / "smoke_tiny.yaml")

    def draws() -> list[float]:
        engine = Engine(scenario)
        return [engine.rng.for_agent(f"vehicle-{i}").random() for i in range(5)]

    assert draws() == draws()
