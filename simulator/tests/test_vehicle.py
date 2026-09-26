"""Vehicle movement and GPS pings (M02).

The acceptance criterion "a plot of the route matches the provider's geometry" is checked
numerically instead of visually: every emitted position must lie on the routed polyline
within GPS noise. That catches the failure a plot would show, and it catches it in CI.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from sim.agents.vehicle import VehicleAgent, VehicleConfig
from sim.engine import Engine
from sim.geo import LatLng, haversine_km
from sim.pings import (
    MOVING_INTERVAL_SECONDS,
    STATIONARY_INTERVAL_SECONDS,
    JsonlPingSink,
    MemoryPingSink,
    Ping,
    ping_interval_seconds,
)
from sim.routing import Route
from sim.scenario import load_scenario

SCENARIOS = Path(__file__).resolve().parent.parent / "scenarios"
DEPOT = LatLng(28.5355, 77.3910)
OFFICE = LatLng(28.5703, 77.3218)
NOW = datetime(2026, 10, 5, 6, 30, tzinfo=UTC)

NO_NOISE = VehicleConfig(speed_noise_sigma=0.0, gps_noise_metres=0.0)


def build_engine() -> Engine:
    return Engine(load_scenario(SCENARIOS / "smoke_tiny.yaml"))


def drive(
    engine: Engine, sink: MemoryPingSink, config: VehicleConfig | None = None
) -> VehicleAgent:
    agent = VehicleAgent(engine, "vehicle-1", DEPOT, sink, config or NO_NOISE)
    agent.go_on_duty()
    engine.spawn(lambda: agent.drive_to(OFFICE))
    engine.run()
    return agent


# --- ping interval rules (mqtt-topics.md) ------------------------------------


def test_moving_interval() -> None:
    assert ping_interval_seconds(speed_ms=8.0, stationary_for_seconds=0) == 5


def test_briefly_stopped_still_pings_every_five_seconds() -> None:
    """A cab at a red light must not look frozen on the supervisor's map."""
    assert ping_interval_seconds(speed_ms=0.0, stationary_for_seconds=30) == 5
    assert ping_interval_seconds(speed_ms=0.0, stationary_for_seconds=119) == 5


def test_stationary_beyond_two_minutes_drops_to_thirty_seconds() -> None:
    assert ping_interval_seconds(speed_ms=0.0, stationary_for_seconds=120) == 30
    assert ping_interval_seconds(speed_ms=0.5, stationary_for_seconds=600) == 30


def test_speed_threshold_is_one_metre_per_second() -> None:
    assert ping_interval_seconds(speed_ms=1.1, stationary_for_seconds=600) == 5
    assert ping_interval_seconds(speed_ms=1.0, stationary_for_seconds=600) == 30


# --- ping payload ------------------------------------------------------------


def test_payload_matches_the_mqtt_spec() -> None:
    ping = Ping("v1", NOW, 28.5, 77.3, spd=8.4, hdg=132.0, acc=6.5, bat=71)
    payload = ping.to_payload()
    assert payload["v"] == 1
    assert payload["ts"] == "2026-10-05T06:30:00Z"
    assert payload["lat"] == 28.5
    assert payload["src"] == "sim"
    assert payload["spd"] == 8.4
    assert payload["bat"] == 71


def test_optional_fields_are_omitted_when_absent() -> None:
    payload = Ping("v1", NOW, 28.5, 77.3).to_payload()
    assert set(payload) == {"v", "ts", "lat", "lng", "src"}


# --- movement ----------------------------------------------------------------


def test_vehicle_reaches_its_destination() -> None:
    engine = build_engine()
    sink = MemoryPingSink()
    agent = drive(engine, sink)
    assert agent.position == OFFICE
    assert agent.speed_ms == 0.0


def test_positions_stay_on_the_routed_geometry() -> None:
    """M02 acceptance, checked numerically rather than by eye."""
    engine = build_engine()
    sink = MemoryPingSink()
    agent = VehicleAgent(engine, "vehicle-1", DEPOT, sink, NO_NOISE)
    route = agent.route_to(OFFICE)
    drive(engine, sink)

    assert len(sink.pings) > 10
    for ping in sink.pings:
        point = LatLng(ping.lat, ping.lng)
        assert _distance_to_polyline_m(point, route.geometry) < 1.0


def test_pings_are_five_seconds_apart_while_moving() -> None:
    engine = build_engine()
    sink = MemoryPingSink()
    drive(engine, sink)

    moving = [ping for ping in sink.pings if (ping.spd or 0) > 1.0]
    gaps = {
        (second.ts - first.ts).total_seconds()
        for first, second in zip(moving, moving[1:], strict=False)
    }
    assert gaps <= {float(MOVING_INTERVAL_SECONDS)}


def test_progress_is_monotonic_towards_the_destination() -> None:
    engine = build_engine()
    sink = MemoryPingSink()
    drive(engine, sink)

    remaining = [haversine_km(LatLng(p.lat, p.lng), OFFICE) for p in sink.pings]
    assert remaining == sorted(remaining, reverse=True)
    assert remaining[-1] == pytest.approx(0.0, abs=0.01)


def test_speed_and_heading_are_reported() -> None:
    engine = build_engine()
    sink = MemoryPingSink()
    drive(engine, sink)

    moving = [ping for ping in sink.pings if (ping.spd or 0) > 1.0]
    assert moving, "the vehicle never reported movement"
    assert all(0 <= (ping.hdg or 0) < 360 for ping in moving)
    # Depot to office is north-west; bearing should be in the third quadrant.
    assert 270 < (moving[1].hdg or 0) < 360


def test_zero_length_trip_is_handled() -> None:
    engine = build_engine()
    sink = MemoryPingSink()
    agent = VehicleAgent(engine, "vehicle-1", DEPOT, sink, NO_NOISE)
    agent.go_on_duty()
    engine.spawn(lambda: agent.drive_to(DEPOT))
    engine.run()
    assert agent.position == DEPOT


# --- duty and privacy --------------------------------------------------------


def test_no_pings_while_off_duty() -> None:
    """non-functional.md: driver GPS is collected only while on duty."""
    engine = build_engine()
    sink = MemoryPingSink()
    agent = VehicleAgent(engine, "vehicle-1", DEPOT, sink, NO_NOISE)
    engine.spawn(lambda: agent.drive_to(OFFICE))
    engine.run()
    assert sink.pings == []


def test_going_off_duty_stops_the_pings() -> None:
    engine = build_engine()
    sink = MemoryPingSink()
    agent = VehicleAgent(engine, "vehicle-1", DEPOT, sink, NO_NOISE)
    agent.go_on_duty()
    agent.go_off_duty()
    engine.spawn(lambda: agent.drive_to(OFFICE))
    engine.run()
    assert sink.pings == []


def test_idle_vehicle_settles_to_the_stationary_cadence() -> None:
    engine = build_engine()
    sink = MemoryPingSink()
    agent = VehicleAgent(engine, "vehicle-1", DEPOT, sink, NO_NOISE)
    agent.go_on_duty()
    engine.spawn(agent.idle)
    engine.run()

    gaps = [
        (second.ts - first.ts).total_seconds()
        for first, second in zip(sink.pings, sink.pings[1:], strict=False)
    ]
    assert gaps[0] == MOVING_INTERVAL_SECONDS
    assert gaps[-1] == STATIONARY_INTERVAL_SECONDS


# --- noise and determinism ---------------------------------------------------


def test_gps_noise_moves_the_reported_position_slightly() -> None:
    engine = build_engine()
    sink = MemoryPingSink()
    config = VehicleConfig(speed_noise_sigma=0.0, gps_noise_metres=5.0)
    agent = VehicleAgent(engine, "vehicle-1", DEPOT, sink, config)
    agent.go_on_duty()
    engine.spawn(lambda: agent.drive_to(OFFICE))
    engine.run()

    route = Route(0, 0, (DEPOT, OFFICE), True)
    offsets = [_distance_to_polyline_m(LatLng(p.lat, p.lng), route.geometry) for p in sink.pings]
    assert max(offsets) > 0.5, "noise was configured but never applied"
    assert max(offsets) < 50.0, "5 m sigma should not throw pings across the road"


def test_speed_noise_changes_the_duration_but_not_the_path() -> None:
    engine = build_engine()
    sink = MemoryPingSink()
    noisy = VehicleAgent(engine, "vehicle-1", DEPOT, sink, VehicleConfig(gps_noise_metres=0.0))
    plain_duration = engine.routing.route(DEPOT, OFFICE, NOW).duration_seconds
    noisy_route = noisy.route_to(OFFICE)

    assert noisy_route.duration_seconds != pytest.approx(plain_duration)
    assert noisy_route.geometry == (DEPOT, OFFICE)


def test_ping_loss_drops_some_pings() -> None:
    engine = build_engine()
    complete = MemoryPingSink()
    drive(engine, complete)

    lossy_engine = build_engine()
    lossy = MemoryPingSink()
    drive(lossy_engine, lossy, VehicleConfig(speed_noise_sigma=0.0, ping_loss_rate=0.5))

    assert 0 < len(lossy.pings) < len(complete.pings)


def test_two_runs_with_the_same_seed_are_identical() -> None:
    def run() -> list[tuple[float, float]]:
        engine = build_engine()
        sink = MemoryPingSink()
        drive(engine, sink, VehicleConfig(gps_noise_metres=5.0))
        return [(ping.lat, ping.lng) for ping in sink.pings]

    assert run() == run()


def test_different_vehicles_get_different_noise() -> None:
    engine = build_engine()
    sink = MemoryPingSink()
    config = VehicleConfig(gps_noise_metres=5.0)
    first = VehicleAgent(engine, "vehicle-1", DEPOT, sink, config)
    second = VehicleAgent(engine, "vehicle-2", DEPOT, sink, config)
    first.go_on_duty()
    second.go_on_duty()
    engine.spawn(lambda: first.drive_to(OFFICE))
    engine.spawn(lambda: second.drive_to(OFFICE))
    engine.run()

    assert [(p.lat, p.lng) for p in sink.for_vehicle("vehicle-1")] != [
        (p.lat, p.lng) for p in sink.for_vehicle("vehicle-2")
    ]


# --- provider independence ---------------------------------------------------


class MultiPointRouting:
    """Stands in for a self-hosted OSRM: a real polyline rather than a straight line."""

    name = "osrm"

    def route(self, origin: LatLng, destination: LatLng, at: datetime) -> Route:
        middle = LatLng(28.5400, 77.3800)
        elbow = LatLng(28.5600, 77.3400)
        return Route(
            duration_seconds=900.0,
            distance_meters=12_000.0,
            geometry=(origin, middle, elbow, destination),
            approximate=False,
        )


def test_the_agent_works_the_same_with_an_osrm_style_provider() -> None:
    """M02 acceptance: identical behaviour under approx and a self-hosted OSRM."""
    engine = build_engine()
    engine.routing = MultiPointRouting()
    sink = MemoryPingSink()
    agent = drive(engine, sink)

    assert agent.position == OFFICE
    route = MultiPointRouting().route(DEPOT, OFFICE, NOW)
    for ping in sink.pings:
        assert _distance_to_polyline_m(LatLng(ping.lat, ping.lng), route.geometry) < 1.0


def test_the_vehicle_follows_the_bends_of_a_polyline() -> None:
    """A straight-line shortcut between waypoints would fail this."""
    engine = build_engine()
    engine.routing = MultiPointRouting()
    sink = MemoryPingSink()
    drive(engine, sink)

    straight = Route(0, 0, (DEPOT, OFFICE), True)
    off_straight_line = [
        _distance_to_polyline_m(LatLng(p.lat, p.lng), straight.geometry) for p in sink.pings
    ]
    assert max(off_straight_line) > 100.0


# --- sinks -------------------------------------------------------------------


def test_jsonl_sink_writes_one_record_per_line(tmp_path: Path) -> None:
    import json

    path = tmp_path / "runs" / "pings.jsonl"
    with JsonlPingSink(path) as sink:
        sink.emit(Ping("vehicle-1", NOW, 28.5, 77.3, spd=8.0))
        sink.emit(Ping("vehicle-2", NOW, 28.6, 77.4))

    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["vehicle_id"] == "vehicle-1"
    assert first["spd"] == 8.0


def test_memory_sink_filters_by_vehicle() -> None:
    sink = MemoryPingSink()
    sink.emit(Ping("a", NOW, 1.0, 1.0))
    sink.emit(Ping("b", NOW, 2.0, 2.0))
    assert len(sink.for_vehicle("a")) == 1


# --- helpers -----------------------------------------------------------------


def _distance_to_polyline_m(point: LatLng, geometry: tuple[LatLng, ...]) -> float:
    """Shortest distance from a point to a polyline, in metres."""
    if len(geometry) == 1:
        return haversine_km(point, geometry[0]) * 1000.0
    return min(
        _distance_to_segment_m(point, start, end)
        for start, end in zip(geometry, geometry[1:], strict=False)
    )


def _distance_to_segment_m(point: LatLng, start: LatLng, end: LatLng) -> float:
    """Planar approximation, fine over the few kilometres a segment spans."""
    scale = 0.878  # cos(28.5 degrees): longitude compression at NCR latitudes
    px, py = point.lng * scale, point.lat
    ax, ay = start.lng * scale, start.lat
    bx, by = end.lng * scale, end.lat

    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return haversine_km(point, start) * 1000.0

    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    closest = LatLng(lat=ay + t * dy, lng=(ax + t * dx) / scale)
    return haversine_km(point, closest) * 1000.0


# --- faults: no fix vs no network (S06, M07) ---------------------------------


def test_a_cab_with_no_fix_sends_nothing() -> None:
    """No satellite fix means no position was ever resolved. Nothing to send."""
    engine, sink = build_engine(), MemoryPingSink()
    agent = VehicleAgent(engine, "vehicle-1", DEPOT, sink, NO_NOISE)
    agent.go_on_duty()
    agent.lose_fix()

    engine.spawn(lambda: agent.drive_to(OFFICE))
    engine.run()

    assert sink.pings == []
    assert agent.held_pings == 0


def test_those_positions_are_gone_for_good() -> None:
    """Regaining a fix does not resurrect what was never recorded."""
    engine, sink = build_engine(), MemoryPingSink()
    agent = VehicleAgent(engine, "vehicle-1", DEPOT, sink, NO_NOISE)
    agent.go_on_duty()
    agent.lose_fix()
    engine.spawn(lambda: agent.drive_to(OFFICE))
    engine.run()

    agent.regain_fix()

    assert sink.pings == []


def test_an_offline_cab_keeps_recording() -> None:
    """No network is not no data: the driver app buffers and uploads later."""
    engine, sink = build_engine(), MemoryPingSink()
    agent = VehicleAgent(engine, "vehicle-1", DEPOT, sink, NO_NOISE)
    agent.go_on_duty()
    agent.disconnect()

    engine.spawn(lambda: agent.drive_to(OFFICE))
    engine.run()

    assert sink.pings == []
    assert agent.held_pings > 0


def test_reconnecting_uploads_the_backlog_in_order() -> None:
    """mqtt-topics.md allows a batch upload after a reconnection, oldest first."""
    engine, sink = build_engine(), MemoryPingSink()
    agent = VehicleAgent(engine, "vehicle-1", DEPOT, sink, NO_NOISE)
    agent.go_on_duty()
    agent.disconnect()
    engine.spawn(lambda: agent.drive_to(OFFICE))
    engine.run()
    held = agent.held_pings

    uploaded = agent.reconnect()

    assert uploaded == held
    assert len(sink.pings) == held
    assert agent.held_pings == 0
    timestamps = [ping.ts for ping in sink.pings]
    assert timestamps == sorted(timestamps)


def test_neither_fault_takes_the_cab_off_duty() -> None:
    """Off duty means no GPS is collected at all - a privacy rule, not a fault."""
    engine = build_engine()
    agent = VehicleAgent(engine, "vehicle-1", DEPOT, MemoryPingSink(), NO_NOISE)
    agent.go_on_duty()

    agent.lose_fix()
    agent.disconnect()

    assert agent.on_duty is True


def test_an_off_duty_cab_buffers_nothing() -> None:
    """The privacy rule wins: no GPS off duty, so there is nothing to upload later."""
    engine, sink = build_engine(), MemoryPingSink()
    agent = VehicleAgent(engine, "vehicle-1", DEPOT, sink, NO_NOISE)
    agent.disconnect()

    engine.spawn(lambda: agent.drive_to(OFFICE))
    engine.run()

    assert agent.held_pings == 0
    assert sink.pings == []
