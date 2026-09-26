"""SimPy engine: the scaffolding agents plug into (`simulator-spec.md` §2).

M01 builds the environment, clock, RNG and routing, and can run an empty simulation to the
scenario's end. Vehicle, employee and supervisor agents arrive with M02/M05/M06 and
register themselves as SimPy processes here.
"""

from __future__ import annotations

from collections.abc import Callable, Generator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import simpy

from sim.clock import SimClock
from sim.geo import LatLng
from sim.metrics import RunMetrics, compute_fleet_metrics
from sim.mqtt import MqttPingSink, TeeingPingSink
from sim.pings import MemoryPingSink
from sim.platform import PlatformClient, PlatformError, SeededWorld
from sim.rng import RngFactory
from sim.routing import RoutingClient, build_routing
from sim.scenario import Scenario

# A SimPy process is a generator yielding events.
Process = Generator[simpy.Event, Any, Any]


@dataclass
class RunSummary:
    """What a run produced. Metrics proper arrive with M03."""

    scenario: str
    seed: int
    routing: str
    started_at: datetime
    ended_at: datetime
    simulated_seconds: float
    vehicles: int
    employees: int
    events: list[str] = field(default_factory=list)


class Engine:
    """Owns the SimPy environment and everything shared between agents."""

    def __init__(
        self,
        scenario: Scenario,
        osrm_url: str | None = None,
        platform: PlatformClient | None = None,
    ) -> None:
        self.scenario = scenario
        self.env = simpy.Environment()
        self.clock = SimClock(scenario.start, scenario.speed_factor)
        self.rng = RngFactory(scenario.seed)
        self.routing: RoutingClient = build_routing(str(scenario.routing), osrm_url)
        # Every agent publishes here; the recorder turns it into pings.csv and metrics.
        self.pings = MemoryPingSink()
        #: Where agents actually emit. In a platform run this tees to MQTT as well, so
        #: the run still produces its own metrics and is comparable with an offline one.
        self.sink: Any = self.pings
        #: The real backend, when this is a closed-loop run (M04). None means offline.
        self.platform = platform
        self.mqtt: MqttPingSink | None = None
        self._log: list[str] = []

    # --- closed loop (M04) ----------------------------------------------------

    def connect_to_platform(self, mqtt: MqttPingSink) -> None:
        """Send pings to the broker as well as to the recorder."""
        self.mqtt = mqtt
        self.sink = TeeingPingSink(self.pings, mqtt)

    def sync_clock(self) -> None:
        """Put the backend on simulated time (`architecture.md` section 3.3).

        Called at each step a scenario cares about rather than continuously: the backend
        does due work on every jump, so syncing per simulated second would run the expiry
        and ETA sweeps thousands of times for nothing.
        """
        if self.platform is not None:
            self.platform.set_clock(self.now())

    # --- time ---------------------------------------------------------------

    def now(self) -> datetime:
        """Simulated wall time, derived from SimPy's clock so the two cannot drift."""
        self.clock.advance_to(self.env.now)
        return self.clock.now()

    @property
    def duration_seconds(self) -> float:
        return self.scenario.duration_hours * 3600.0

    # --- processes ----------------------------------------------------------

    def spawn(self, process: Callable[[], Process]) -> simpy.Process:
        """Register an agent process with the environment."""
        return self.env.process(process())

    def record(self, message: str) -> None:
        """Append to the run log, stamped with simulated time."""
        self._log.append(f"{self.now().isoformat()} {message}")

    # --- running ------------------------------------------------------------

    def run(self) -> RunSummary:
        """Run to the scenario's end and summarise."""
        started = self.clock.start
        self.env.run(until=self.duration_seconds)
        ended = self.clock.advance_to(self.duration_seconds)

        return RunSummary(
            scenario=self.scenario.name,
            seed=self.scenario.seed,
            routing=self.routing.name,
            started_at=started,
            ended_at=ended,
            simulated_seconds=self.duration_seconds,
            vehicles=self.scenario.vehicle_count,
            employees=self.scenario.employee_count,
            events=list(self._log),
        )

    def metrics(self, summary: RunSummary) -> RunMetrics:
        """Metrics for a finished run (`simulator-spec.md` §9)."""
        return RunMetrics(
            scenario=summary.scenario,
            seed=summary.seed,
            routing=summary.routing,
            started_at=summary.started_at.isoformat(),
            ended_at=summary.ended_at.isoformat(),
            simulated_hours=summary.simulated_seconds / 3600.0,
            fleet=compute_fleet_metrics(self.pings.pings),
        )


def spawn_fleet(engine: Engine, vehicle_ids: list[str] | None = None) -> list[Any]:
    """Put the scenario's cabs on the road (M02's agent, wired to M04's run).

    Every cab starts at its group's depot, goes on duty and idles, pinging at the
    stationary cadence. **M05 replaces the idling with real trips**; until the demand
    model exists there is nowhere to drive, and a fleet that pings from its depot is the
    honest version of that rather than cabs wandering to invent movement.

    `vehicle_ids` lets a platform run use the backend's real ids, so a ping lands on the
    vehicle the supervisor is looking at rather than on a name the simulator made up.
    """
    from sim.agents.vehicle import VehicleAgent

    agents: list[Any] = []
    index = 0
    for group in engine.scenario.fleet:
        depot = LatLng(lat=group.depot[1], lng=group.depot[0])
        for _ in range(group.count):
            identifier = (
                str(vehicle_ids[index])
                if vehicle_ids is not None and index < len(vehicle_ids)
                else f"vehicle-{index + 1}"
            )
            agent = VehicleAgent(engine, identifier, depot, engine.sink)
            agent.go_on_duty()
            engine.spawn(agent.idle)
            agents.append(agent)
            index += 1
    return agents


def connect_fleet(engine: Engine, platform: PlatformClient) -> SeededWorld:
    """Seed the backend, put its clock on simulated time, and sign every cab in (M04).

    The order matters: **clock first, then seed**. `/simctl/reset` mints an access token
    per role stamped with whatever time the backend thinks it is, so seeding before the
    jump hands out tokens that are already expired the moment the scenario's clock moves
    to its start. Duty sessions and first pings then carry simulated time too, rather
    than whenever the operator happened to run the scenario.
    """
    platform.set_clock(engine.clock.start + _LEAD)
    world = platform.reset()

    tokens = world.tokens_for("driver")
    if not tokens:
        raise PlatformError("The reset fixture seeded no driver logins")

    wanted = min(engine.scenario.vehicle_count, len(world.vehicle_ids), len(tokens))
    if wanted < engine.scenario.vehicle_count:
        # Said out loud rather than silently running a smaller fleet, which would make
        # the run's metrics quietly wrong.
        engine.record(
            f"fleet limited to {wanted}: the seeded world has "
            f"{len(world.vehicle_ids)} vehicles and {len(tokens)} driver logins"
        )

    # Paced: pings wait for the backend clock to reach them (see MqttPingSink).
    mqtt = MqttPingSink(paced=True)
    for vehicle_id, driver_token in zip(world.vehicle_ids[:wanted], tokens[:wanted], strict=True):
        credentials = platform.go_on_duty(driver_token, vehicle_id)
        mqtt.register(vehicle_id, credentials)
        engine.record(f"vehicle {vehicle_id} on duty, publishing to {credentials.gps_topic}")

    engine.connect_to_platform(mqtt)
    engine.spawn(lambda: _keep_clocks_together(engine))
    return world


#: How often, in simulated seconds, to push the clock to the backend during a run.
#: One minute keeps a ping at most a minute ahead of the backend's "now" - well inside
#: the two-minute future tolerance in `mqtt-topics.md` - without making an HTTP call per
#: simulated second.
CLOCK_SYNC_INTERVAL_SECONDS = 60

#: How far ahead of the simulation to hold the backend's clock.
_LEAD = timedelta(seconds=CLOCK_SYNC_INTERVAL_SECONDS)


def _keep_clocks_together(engine: Engine) -> Process:
    """Walk the backend's clock forward with the simulation.

    Setting it once at the start is not enough, and the failure is quietly total: a run
    compresses an hour into milliseconds, so within a moment the simulator is publishing
    pings stamped an hour ahead of the backend's "now" and the ingestor correctly drops
    every one of them as `too_far_future`. Nothing errors; the map simply stays empty.
    """
    while True:
        yield engine.env.timeout(CLOCK_SYNC_INTERVAL_SECONDS)
        if engine.platform is not None:
            # One interval *ahead*, deliberately. Pings are published as the simulation
            # reaches them, but a clock jump is an HTTP call that runs the backend's due
            # work, so syncing to exactly "now" leaves the backend trailing its own
            # incoming pings and the ingestor rejects them as `too_far_future`. A clock
            # slightly ahead costs nothing: a ping in the past is accepted for 24 hours.
            engine.platform.set_clock(engine.now() + _LEAD)
            if engine.mqtt is not None:
                engine.mqtt.release_up_to(engine.now())
