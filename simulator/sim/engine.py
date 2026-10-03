"""SimPy engine: the scaffolding agents plug into (`simulator-spec.md` §2).

M01 builds the environment, clock, RNG and routing, and can run an empty simulation to the
scenario's end. Vehicle, employee and supervisor agents arrive with M02/M05/M06 and
register themselves as SimPy processes here.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable, Generator
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from datetime import time as dt_time
from typing import Any

import simpy

from sim.agents.driver import DriverAgent
from sim.agents.driver import summarise as summarise_fleet
from sim.agents.employee import EmployeeAgent, EmployeeProfile, Outcome
from sim.agents.employee import summarise as summarise_demand
from sim.agents.supervisor import SupervisorAgent
from sim.agents.supervisor import summarise as summarise_dispatch
from sim.board import StatusBoard, TripBoard
from sim.clock import IST, SimClock
from sim.events import EventInjector
from sim.events import summarise as summarise_events
from sim.geo import LatLng
from sim.metrics import (
    DemandMetrics,
    DispatchMetrics,
    DrivingMetrics,
    IntegrityMetrics,
    RunMetrics,
    compute_fleet_metrics,
)
from sim.mqtt import MqttPingSink, TeeingPingSink
from sim.pings import MemoryPingSink
from sim.platform import DutyCredentials, PlatformClient, PlatformError, SeededWorld
from sim.rng import RngFactory
from sim.routing import RoutingClient, build_routing
from sim.scenario import LatLngModel, Scenario
from sim.traffic import TrafficModel

# A SimPy process is a generator yielding events.
Process = Generator[simpy.Event, Any, Any]

#: How far the clock moves per step while draining. The riders' own poll interval, so the
#: drain notices the last cab emptying within one poll rather than overshooting the cap.
DRAIN_STEP_SECONDS = 60.0


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
    #: Overtime spent letting rides already under way finish (OQ-28). Not part of the
    #: measured window: `simulated_seconds` is still the scenario's own duration.
    drain_minutes: float = 0.0
    #: True when the cap ran out with someone still in a cab. The run is then reporting
    #: a genuinely stuck ride, not an artefact of where the clock stopped.
    drain_capped: bool = False
    #: Riders who asked for a cab and were never served (OQ-29).
    abandoned: int = 0


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
        #: The people (M05). Riders are indexed by request so a driver can ask the rider
        #: it is waiting for whether they turned up, rather than sampling that twice.
        self.riders: list[EmployeeAgent] = []
        self.drivers: list[DriverAgent] = []
        #: One person watching the queue (M06). None until a platform run spawns them.
        self.supervisor: SupervisorAgent | None = None
        #: One shared read of the request board, so riders do not each poll (OQ-26).
        self.board: StatusBoard | None = None
        #: The same for the drivers' trips. None means every driver polls for itself,
        #: which is correct and slow - an offline run has no board to share.
        self.trip_board: TripBoard | None = None
        #: Conditions the event injector turns on and off during the run (M07).
        self.traffic = TrafficModel(self.routing)
        self.events: EventInjector | None = None
        self._events_scheduled = 0
        #: `no_show_wait_minutes` as the backend has it; the driver must not guess.
        self.no_show_wait_minutes = DEFAULT_NO_SHOW_WAIT_MINUTES
        #: True once the demand window has closed: nothing new is asked for, nothing new
        #: is assigned, and a rider still waiting has their answer (OQ-29).
        self.window_closed = False
        #: Cabs, by the order the scenario's fleet declares them.
        self.vehicles: list[Any] = []
        #: MQTT credentials per vehicle id, from going on duty.
        self.duty_credentials: dict[str, DutyCredentials] = {}
        self._log: list[str] = []

    def rider_for_request(self, request_id: uuid.UUID) -> EmployeeAgent | None:
        """The rider who made this request, if it was one of ours."""
        for rider in self.riders:
            if rider.record.request_id == request_id:
                return rider
        return None

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
        """The demand window. What the run's metrics are about."""
        return self.scenario.duration_hours * 3600.0

    @property
    def drain_limit_seconds(self) -> float:
        """The latest the clock may reach while a ride finishes (OQ-28)."""
        return self.duration_seconds + self.scenario.drain_minutes_max * 60.0

    @property
    def drain_end(self) -> datetime:
        """The same moment as wall time, for agents that have to compare against it."""
        return self.scenario.drain_end

    def rides_in_progress(self) -> int:
        """Riders sitting in a moving cab right now."""
        return sum(1 for rider in self.riders if rider.on_board)

    # --- processes ----------------------------------------------------------

    def spawn(self, process: Callable[[], Process]) -> simpy.Process:
        """Register an agent process with the environment."""
        return self.env.process(process())

    def at_ist(self, local: dt_time) -> datetime | None:
        """An IST wall-clock time as an absolute moment inside this run.

        Tries the run's first local date and the next one, so an event written as
        "02:00" on a run that starts at 06:00 IST lands on the following morning rather
        than being silently dropped as already past. Returns `None` when neither falls
        inside the run - the caller decides whether that is a skip or an error.
        """
        first = self.clock.start.astimezone(IST).date()
        for offset in (0, 1):
            moment = datetime.combine(first + timedelta(days=offset), local, tzinfo=IST)
            moment = moment.astimezone(UTC)
            if self.now() <= moment <= self.scenario.end:
                return moment
        return None

    def record(self, message: str) -> None:
        """Append to the run log, stamped with simulated time."""
        self._log.append(f"{self.now().isoformat()} {message}")

    # --- running ------------------------------------------------------------

    def run(self) -> RunSummary:
        """Run to the scenario's end, let rides in progress finish, and summarise."""
        started = self.clock.start
        self.env.run(until=self.duration_seconds)
        ended = self.clock.advance_to(self.duration_seconds)
        # The window has closed. Riders still waiting are measured here, before the
        # drain, because the drain is for finishing rides and not for serving anybody.
        self.window_closed = True
        abandoned = self._record_riders_nobody_came_for()
        drained = self._drain()
        stuck = self._record_rides_that_never_ended()

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
            drain_minutes=drained / 60.0,
            drain_capped=stuck > 0,
            abandoned=abandoned,
        )

    def _drain(self) -> float:
        """Keep the clock running while someone is still in a cab (OQ-28).

        A run that stops dead on the hour leaves whoever was mid-journey `picked_up`,
        which is not terminal - so `all_requests_terminal` failed for no reason other
        than where the clock stopped, and failed only *sometimes*, because live timing
        varies. A gate that fails at random gets ignored.

        Nothing new happens in here. Riders ask for nothing after the window and the
        supervisor has stopped assigning, so the only processes still doing work are the
        drivers finishing the trips they were already driving. It ends the moment the
        last cab empties, so a healthy run pays almost nothing for it.
        """
        if self.scenario.drain_minutes_max <= 0 or not self.riders:
            return 0.0

        start = self.env.now
        while self.env.now < self.drain_limit_seconds and self.rides_in_progress():
            step = min(self.env.now + DRAIN_STEP_SECONDS, self.drain_limit_seconds)
            self.env.run(until=step)
            self.clock.advance_to(self.env.now)

        drained = self.env.now - start
        if drained:
            riding = self.rides_in_progress()
            self.record(
                f"drained {drained / 60.0:.0f} min for rides in progress; "
                + (f"{riding} still riding at the cap" if riding else "all cabs empty")
            )
        return float(drained)

    def _record_riders_nobody_came_for(self) -> int:
        """Record every rider who asked for a cab and never got an answer (OQ-29).

        Their process is suspended inside a poll, so until now the default outcome stood
        and a rider the platform abandoned was counted as one who stayed at home - which
        let `all_requests_terminal` pass over exactly the failure it exists to catch.
        They are `unresolved`, which is what the assertion has always meant.
        """
        abandoned = 0
        for rider in self.riders:
            if not rider.waiting:
                continue
            rider.record.outcome = Outcome.unresolved
            rider.record.detail = "still waiting when the demand window closed"
            rider.record.left_waiting = True
            abandoned += 1
        if abandoned:
            self.record(f"{abandoned} rider(s) were still waiting when the window closed")
        return abandoned

    def _record_rides_that_never_ended(self) -> int:
        """Write the outcome of anyone still in a cab when the clock stopped.

        Their process is suspended inside a poll and will never resume, so nobody else
        will record them, and the default outcome reads as "stayed at home" - a stuck
        ride would be reported as no demand. Doing it here rather than in the agent is
        also what makes the result deterministic: it no longer depends on whether one of
        the rider's minute-by-minute polls happened to land past the end (OQ-28).
        """
        stuck = 0
        for rider in self.riders:
            if not rider.on_board:
                continue
            rider.record.outcome = Outcome.unresolved
            rider.record.detail = "still riding when the run stopped"
            rider.record.left_riding = True
            stuck += 1
        if stuck:
            riders = ", ".join(
                rider.profile.employee_id for rider in self.riders if rider.record.left_riding
            )
            self.record(f"{stuck} rider(s) were still in a cab when the run stopped: {riders}")
        return stuck

    def metrics(self, summary: RunSummary) -> RunMetrics:
        """Metrics for a finished run (`simulator-spec.md` §9)."""
        return RunMetrics(
            scenario=summary.scenario,
            seed=summary.seed,
            routing=summary.routing,
            started_at=summary.started_at.isoformat(),
            ended_at=summary.ended_at.isoformat(),
            simulated_hours=summary.simulated_seconds / 3600.0,
            drain_minutes=summary.drain_minutes,
            drain_capped=summary.drain_capped,
            fleet=compute_fleet_metrics(self.pings.pings),
            demand=self._demand_metrics(),
            driving=self._driving_metrics(),
            dispatch=self._dispatch_metrics(),
            events=summarise_events(self.events, self._events_scheduled),
            integrity=IntegrityMetrics(agent_errors=self._agent_errors()),
        )

    def _dispatch_metrics(self) -> DispatchMetrics:
        summary = summarise_dispatch(
            self.supervisor.record if self.supervisor is not None else None
        )
        return DispatchMetrics(
            policy=summary.policy,
            assignments=summary.assignments,
            refusals=summary.refusals,
            no_candidate=summary.no_candidate,
            violations_accepted=summary.violations_accepted,
            violations_by_rule=summary.violations_by_rule,
            gps_age_seconds_median=summary.gps_age_seconds_median,
            gps_age_seconds_max=summary.gps_age_seconds_max,
            errors=summary.errors,
        )

    def _agent_errors(self) -> int:
        """Every API call an agent could not make. Counted, never fatal."""
        errors = sum(len(driver.record.errors) for driver in self.drivers)
        if self.supervisor is not None:
            errors += len(self.supervisor.record.errors)
        return errors

    def _demand_metrics(self) -> DemandMetrics:
        """`None` everywhere for an offline run: nothing was measured, not nothing happened."""
        if not self.riders:
            return DemandMetrics()

        summary = summarise_demand([rider.record for rider in self.riders])
        waits = sorted(summary.waits_minutes)
        return DemandMetrics(
            riders=summary.riders,
            requests=summary.requested,
            completed=summary.completed,
            cancelled=summary.cancelled,
            gave_up=summary.gave_up,
            no_shows=summary.no_shows,
            expired=summary.expired,
            unresolved=summary.unresolved + summary.failed,
            not_travelling=summary.not_travelling,
            still_waiting=summary.still_waiting,
            still_riding=summary.still_riding,
            wait_minutes_median=_percentile(waits, 0.5),
            wait_minutes_p90=_percentile(waits, 0.9),
            vip_requests=self._vip_requests(),
            vip_pooled=self._vip_pooled(),
        )

    def _vip_requests(self) -> int:
        return sum(1 for rider in self.riders if rider.profile.is_vip and rider.travelling)

    def _vip_pooled(self) -> int:
        """VIP riders who ended up sharing a cab (`allocation-rules.md` section 2 rule 4).

        Read from the trips the drivers actually drove rather than from what dispatch
        intended: the rule is about what happened to the rider, and a trip that gained a
        second rider after the VIP boarded breaks it just as surely as one planned that
        way.
        """
        shared: set[str] = set()
        for driver in self.drivers:
            for riders in driver.record.riders_per_trip.values():
                if len(riders) > 1:
                    shared |= riders

        return sum(
            1
            for rider in self.riders
            if rider.profile.is_vip and str(rider.record.request_id) in shared
        )

    def _driving_metrics(self) -> DrivingMetrics:
        if not self.drivers:
            return DrivingMetrics()
        summary = summarise_fleet([driver.record for driver in self.drivers])
        return DrivingMetrics(
            drivers=summary.drivers,
            on_duty=summary.on_duty,
            trips_started=summary.trips_started,
            trips_completed=summary.trips_completed,
            stops_done=summary.stops_done,
            no_shows=summary.no_shows,
            faults=summary.faults,
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
        # `from_pair` is the scenario's own reader: the YAML pairs are [lat, lng], and
        # reading them the other way round put the depot 8,000 km away, which surfaced as
        # a candidate ETA of fourteen days.
        pair = LatLngModel.from_pair(group.depot)
        depot = LatLng(lat=pair.lat, lng=pair.lng)
        for _ in range(group.count):
            identifier = (
                str(vehicle_ids[index])
                if vehicle_ids is not None and index < len(vehicle_ids)
                else f"vehicle-{index + 1}"
            )
            agent = VehicleAgent(engine, identifier, depot, engine.sink)
            if engine.platform is None:
                # Offline: no driver agent will ever start this cab, so it drives itself.
                agent.go_on_duty()
                engine.spawn(agent.idle)
            agents.append(agent)
            engine.vehicles.append(agent)
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
    world = platform.reset(
        employees=engine.scenario.employee_count,
        vehicles=engine.scenario.vehicle_count,
        vip_employees=engine.scenario.vip_employee_count,
        # The exact mix, not just the count: a scenario asking for two VIP cars that
        # silently got one would test nothing it claims to.
        fleet=[(str(group.type), group.count) for group in engine.scenario.fleet],
    )

    overrides = engine.scenario.operator.config_overrides
    if overrides:
        platform.apply_config(world.token_for("operator_admin"), overrides)
        engine.record(f"applied config overrides: {sorted(overrides)}")
        engine.no_show_wait_minutes = int(
            overrides.get("no_show_wait_minutes", DEFAULT_NO_SHOW_WAIT_MINUTES)
        )

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
    credentials_by_vehicle: dict[str, DutyCredentials] = {}
    for vehicle_id, driver_token in zip(world.vehicle_ids[:wanted], tokens[:wanted], strict=True):
        credentials = platform.go_on_duty(driver_token, vehicle_id)
        mqtt.register(vehicle_id, credentials)
        credentials_by_vehicle[str(vehicle_id)] = credentials
        engine.record(f"vehicle {vehicle_id} on duty, publishing to {credentials.gps_topic}")

    engine.connect_to_platform(mqtt)
    engine.spawn(lambda: _keep_clocks_together(engine))
    engine.duty_credentials = credentials_by_vehicle
    return world


def spawn_people(engine: Engine, world: SeededWorld) -> None:
    """Put riders and drivers into the run (M05).

    Riders come first: a driver asks the rider it is waiting for whether they turned up,
    so the rider must exist before any trip can be worked.
    """
    _spawn_status_board(engine, world)
    _spawn_trip_board(engine, world)
    _spawn_riders(engine, world)
    _spawn_drivers(engine, world)
    _spawn_supervisor(engine, world)
    inject_events(engine)


def inject_events(engine: Engine) -> None:
    """Arm the scenario's timed events (M07).

    After the agents, because an event acts on them - a breakdown needs a driver to
    report it, a surge needs riders who are not already travelling.
    """
    injector = EventInjector(engine)
    engine.events = injector
    engine._events_scheduled = injector.schedule(list(engine.scenario.events))


def _spawn_riders(engine: Engine, world: SeededWorld) -> None:
    tokens = world.tokens_for("employee")
    wanted = min(engine.scenario.employee_count, len(world.employee_ids), len(tokens))
    if wanted < engine.scenario.employee_count:
        engine.record(
            f"demand limited to {wanted} riders: the seeded world has "
            f"{len(world.employee_ids)} employees and {len(tokens)} logins"
        )

    shift_start, shift_end = _first_shift(engine)
    vip = set(world.vip_employee_ids)
    for employee_id, token in zip(world.employee_ids[:wanted], tokens[:wanted], strict=True):
        rider = EmployeeAgent(
            engine,
            EmployeeProfile(
                employee_id=str(employee_id),
                token=token,
                home=None,
                shift_start=shift_start,
                shift_end=shift_end,
                is_vip=employee_id in vip,
            ),
        )
        engine.riders.append(rider)
        engine.spawn(rider.day)


def _spawn_drivers(engine: Engine, world: SeededWorld) -> None:
    tokens = world.tokens_for("driver")
    for index, vehicle in enumerate(engine.vehicles):
        if index >= len(tokens):
            break
        credentials = engine.duty_credentials.get(vehicle.vehicle_id)
        if credentials is None:
            continue
        driver = DriverAgent(
            engine,
            driver_id=f"driver-{index + 1}",
            token=tokens[index],
            vehicle=vehicle,
            credentials=credentials,
            late_start_probability=engine.scenario.drivers.late_start_p,
            platform_driver_id=(world.driver_ids[index] if index < len(world.driver_ids) else None),
        )
        engine.drivers.append(driver)
        engine.spawn(driver.shift)


def _spawn_status_board(engine: Engine, world: SeededWorld) -> None:
    """One process reads every request's status for all the riders (OQ-26)."""
    board = StatusBoard(engine, token=world.token_for("supervisor"))
    engine.board = board
    engine.spawn(board.watch)


def _spawn_trip_board(engine: Engine, world: SeededWorld) -> None:
    """And one reads every driver's trips, for all the drivers (OQ-26).

    The last remaining per-agent poll: thirty-five drivers asking `/driver/trips` every
    simulated minute, each call blocking the whole single-threaded loop.
    """
    board = TripBoard(engine, token=world.token_for("supervisor"))
    engine.trip_board = board
    engine.spawn(board.watch)


def _spawn_supervisor(engine: Engine, world: SeededWorld) -> None:
    """The human in the loop (M06). Without one, nothing is ever assigned."""
    settings = engine.scenario.supervisor
    low, high = settings.reaction_delay_s
    supervisor = SupervisorAgent(
        engine,
        token=world.token_for("supervisor"),
        policy=settings.policy,
        reaction_delay_seconds=(low, high),
    )
    engine.supervisor = supervisor
    engine.spawn(supervisor.watch)


def _first_shift(engine: Engine) -> tuple[datetime, datetime]:
    """The scenario's first shift, as absolute times on the run's date.

    Shifts are written in IST because that is how an NCR operator thinks about them; the
    run works in UTC.
    """
    shift = engine.scenario.clients[0].employees.shifts[0]
    local_date = engine.clock.start.astimezone(IST).date()
    start = datetime.combine(local_date, shift.start_ist, tzinfo=IST).astimezone(UTC)
    end = datetime.combine(local_date, shift.end_ist, tzinfo=IST).astimezone(UTC)
    if end <= start:
        end += timedelta(days=1)
    return start, end


#: `allocation-rules.md` section 1 default. Overridden from the scenario's config.
DEFAULT_NO_SHOW_WAIT_MINUTES = 5

#: How often, in simulated seconds, to push the clock to the backend during a run.
#:
#: This was 60 s, and that collided with `stale_gps_seconds`, which is also 60. The
#: backend's clock is held one interval *ahead* (below), while pings are released only up
#: to simulated now - so the freshest position the backend could ever hold was already a
#: full interval old by its own clock, and **every vehicle was permanently stale**. Every
#: candidate came back flagged `gps_stale`, and the sweep raised an open `stale_vehicle`
#: alert for all thirty cabs while they were driving.
#:
#: Nothing failed loudly, which is why it survived: Phase 1 only *reports* hard rules
#: (ADR-0011), so a flag nobody enforces looked like noise. Phase 2's optimizer treats
#: the same list as a filter, where it would have meant no vehicle was ever dispatchable.
#:
#: Twenty seconds keeps the freshest ping a third of the way to the staleness threshold,
#: at three clock calls a simulated minute. A clock jump costs about 20 ms since the
#: OQ-26 query fixes, so this is a few seconds of wall clock per simulated hour.
CLOCK_SYNC_INTERVAL_SECONDS = 20

#: How far ahead of the simulation to hold the backend's clock. One interval, so that a
#: ping published just before the next sync is not stamped in the backend's future and
#: dropped by the ingestor as `too_far_future`. It must stay well under
#: `stale_gps_seconds` (60) - see above.
_LEAD = timedelta(seconds=CLOCK_SYNC_INTERVAL_SECONDS)


def _keep_clocks_together(engine: Engine) -> Process:
    """Walk the backend's clock forward with the simulation.

    Setting it once at the start is not enough, and the failure is quietly total: a run
    compresses an hour into milliseconds, so within a moment the simulator is publishing
    pings stamped an hour ahead of the backend's "now" and the ingestor correctly drops
    every one of them as `too_far_future`. Nothing errors; the map simply stays empty.
    """
    started_wall = time.monotonic()
    while True:
        yield engine.env.timeout(CLOCK_SYNC_INTERVAL_SECONDS)
        _pace(engine, started_wall)
        if engine.platform is not None:
            # One interval *ahead*, deliberately. Pings are published as the simulation
            # reaches them, but a clock jump is an HTTP call that runs the backend's due
            # work, so syncing to exactly "now" leaves the backend trailing its own
            # incoming pings and the ingestor rejects them as `too_far_future`. A clock
            # slightly ahead costs nothing: a ping in the past is accepted for 24 hours.
            engine.platform.set_clock(engine.now() + _LEAD)
            if engine.mqtt is not None:
                engine.mqtt.release_up_to(engine.now())


def _percentile(ordered: list[float], fraction: float) -> float | None:
    """Same definition as the backend's report (`app/domain/stats.py`): R type 7.

    Stated because a simulator whose p90 disagrees with the product's p90 makes every
    comparison between them meaningless.
    """
    if not ordered:
        return None
    if len(ordered) == 1:
        return round(ordered[0], 1)
    position = fraction * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return round(ordered[lower] * (1 - weight) + ordered[upper] * weight, 1)


def _pace(engine: Engine, started_wall: float) -> None:
    """Hold the simulation to the scenario's `speed_factor` in a closed-loop run.

    Offline, running flat out is the whole point. Against a real backend it is a trap:
    the simulator finishes an hour in seconds, while the ingestor is still writing the
    first minute's GPS and the supervisor asks for candidate vehicles that have no known
    position yet. The result looks like a dispatch bug and is not one.

    `speed_factor: 60` means an hour a minute, which is fast enough to be useful and slow
    enough that the system under test keeps up.
    """
    if engine.platform is None:
        return
    target = engine.clock.real_seconds_for(engine.env.now)
    behind = target - (time.monotonic() - started_wall)
    if behind > 0:
        time.sleep(behind)
