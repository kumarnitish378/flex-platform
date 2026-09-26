"""The loop actually closing (M04 acceptance).

Opt-in, because it needs the whole stack running:

    make up                                    # postgres, redis, mosquitto
    APP_ENV=sim make backend-dev               # the API, with a controllable clock
    python -m app.ingestor                     # the MQTT consumer (from backend/)
    SIM_PLATFORM_URL=http://localhost:8000/api/v1 python -m pytest tests/test_closed_loop_live.py

The acceptance criterion is "sim vehicles appear moving on the supervisor app live map".
The app itself is blocked on the Flutter SDK, so this asserts against
`GET /dispatch/vehicles` - the endpoint that map reads - which is the same fact one layer
down. `simulator-spec.md` section 2: the simulator drives the real API, so if this passes
the only thing left between it and the map is the map.
"""

from __future__ import annotations

import os
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from sim.assertions import evaluate
from sim.engine import Engine, connect_fleet, spawn_fleet, spawn_people
from sim.platform import PlatformClient
from sim.scenario import load_scenario

SCENARIOS = Path(__file__).resolve().parent.parent / "scenarios"
PLATFORM_URL = os.environ.get("SIM_PLATFORM_URL")

enabled = pytest.mark.skipif(
    not PLATFORM_URL,
    reason=(
        "needs the full stack; run with SIM_PLATFORM_URL set after `make up`, "
        "`APP_ENV=sim make backend-dev` and `python -m app.ingestor`"
    ),
)

#: How long to wait for the ingestor to drain. Polled rather than slept: a compressed run
#: hands the broker an hour of pings in about a second, and how long the ingestor then
#: takes is a property of this machine, not of the pipeline.
INGEST_TIMEOUT_SECONDS = 60.0


@pytest.fixture
def platform() -> PlatformClient:
    assert PLATFORM_URL
    client = PlatformClient(PLATFORM_URL)
    if not client.health():
        pytest.skip(f"no backend answering at {PLATFORM_URL}")
    return client


@enabled
def test_the_backend_accepts_a_seeded_world(platform: PlatformClient) -> None:
    world = platform.reset()

    assert world.vehicle_ids, "the reset fixture seeded no vehicles"
    assert world.token_for("supervisor")
    assert world.token_for("driver")


@enabled
def test_the_clocks_agree(platform: PlatformClient) -> None:
    """Without this the backend expires requests on wall-clock time mid-run."""
    platform.reset()
    moment = datetime(2026, 9, 25, 8, 0, tzinfo=UTC)

    platform.set_clock(moment)

    assert platform.clock() == moment


@enabled
def test_a_driver_going_on_duty_is_issued_broker_credentials(
    platform: PlatformClient,
) -> None:
    world = platform.reset()
    credentials = platform.go_on_duty(world.token_for("driver"), world.vehicle_ids[0])

    assert credentials.username
    assert credentials.gps_topic.startswith("sc/v1/op/")


@enabled
def test_simulated_cabs_appear_moving_on_the_live_map(platform: PlatformClient) -> None:
    """M04 acceptance, one layer below the map widget.

    Runs a short scenario, publishes its GPS to the real broker as real vehicles, and
    then reads `/dispatch/vehicles` - what the supervisor map renders - to check the cabs
    are there, positioned, and not stale.
    """
    scenario = load_scenario(str(SCENARIOS / "smoke_tiny.yaml"))
    engine = Engine(scenario, platform=platform)

    world = connect_fleet(engine, platform)
    spawn_fleet(engine, [str(value) for value in world.vehicle_ids])
    # A cab pings because a driver started their shift (M05); without the driver agent
    # the vehicle sits there silently, exactly as a real one would.
    spawn_people(engine, world)
    assert engine.mqtt is not None

    engine.run()
    engine.mqtt.flush()

    assert engine.mqtt.published, "the run published no GPS at all"
    assert engine.mqtt.failed == 0, f"{engine.mqtt.failed} pings could not be published"

    positioned = _wait_for_the_map(platform, world.token_for("supervisor"))

    assert positioned, "no vehicle reached the live map"
    assert len(positioned) >= min(len(world.vehicle_ids), scenario.vehicle_count)

    # Freshness is judged against the newest position the map itself reports, not against
    # the run's end. A compressed run publishes an hour of pings in about a second, so the
    # ingestor is still draining when the run returns; asserting against the end time
    # would be testing how fast this machine is, not whether the pipeline works. What
    # matters is that the map marks a just-received position as live.
    newest = max(item["position_at"] for item in positioned if item.get("position_at"))
    platform.set_clock(_moment(newest))

    refreshed = platform.live_vehicles(world.token_for("supervisor"))
    live = [item for item in refreshed if item.get("position") and not item["stale"]]
    assert live, "the newest position was already marked stale"

    engine.mqtt.close()


@enabled
def test_the_map_goes_stale_when_the_cabs_stop(platform: PlatformClient) -> None:
    """The other half of SUP-01: a supervisor must be able to tell live from frozen."""
    scenario = load_scenario(str(SCENARIOS / "smoke_tiny.yaml"))
    engine = Engine(scenario, platform=platform)
    world = connect_fleet(engine, platform)
    spawn_fleet(engine, [str(value) for value in world.vehicle_ids])
    spawn_people(engine, world)
    engine.run()
    assert engine.mqtt is not None
    engine.mqtt.flush()

    vehicles = _wait_for_the_map(platform, world.token_for("supervisor"))
    stamps = [item["position_at"] for item in vehicles if item.get("position_at")]
    if not stamps:
        pytest.skip("nothing was ingested, so there is no freshness to lose")
    platform.set_clock(_moment(max(stamps)) + timedelta(hours=1))

    vehicles = platform.live_vehicles(world.token_for("supervisor"))
    assert all(item["stale"] for item in vehicles if item.get("position"))

    engine.mqtt.close()


def _moment(stamp: str) -> datetime:
    return datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def _wait_for_the_map(platform: PlatformClient, token: str) -> list[dict[str, Any]]:
    """Poll the live map until vehicles show up, or give up.

    The ingestor batches its writes (B12), so the map is eventually consistent with the
    broker by design. Polling asserts that property; a fixed sleep would assert this
    laptop's speed.
    """
    deadline = time.monotonic() + INGEST_TIMEOUT_SECONDS
    positioned: list[dict[str, Any]] = []
    while time.monotonic() < deadline:
        positioned = [item for item in platform.live_vehicles(token) if item.get("position")]
        if positioned:
            return positioned
        time.sleep(1.0)
    return positioned


@enabled
def test_s01_runs_end_to_end_with_every_request_terminal(platform: PlatformClient) -> None:
    """M05 acceptance, and S01's own assertion (`scenarios.md`).

    Riders ask for cabs, wait, and either ride or stop waiting. Nothing may be left
    hanging when the run ends - a request still `queued` at the end is a request the
    product quietly lost.

    With no supervisor agent yet (M06), the honest outcome is that the requests expire.
    That is still terminal, and when M06 lands the same assertion will hold with rides
    completed instead.
    """
    scenario = load_scenario(str(SCENARIOS / "smoke_tiny.yaml"))
    engine = Engine(scenario, platform=platform)

    world = connect_fleet(engine, platform)
    spawn_fleet(engine, [str(value) for value in world.vehicle_ids])
    spawn_people(engine, world)

    assert engine.riders, "the scenario produced no riders"
    assert engine.drivers, "the scenario produced no drivers"

    summary = engine.run()
    metrics = engine.metrics(summary)

    assert metrics.demand.requests, "no rider ever asked for a cab"
    assert metrics.demand.unresolved == 0, "a request was still open when the run ended"
    assert metrics.integrity.agent_errors == 0, "an agent's API call failed"
    assert evaluate(scenario.assertions, metrics) == []

    if engine.mqtt is not None:
        engine.mqtt.release_all()
        engine.mqtt.flush()
        engine.mqtt.close()
