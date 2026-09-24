"""SimPy engine: the scaffolding agents plug into (`simulator-spec.md` §2).

M01 builds the environment, clock, RNG and routing, and can run an empty simulation to the
scenario's end. Vehicle, employee and supervisor agents arrive with M02/M05/M06 and
register themselves as SimPy processes here.
"""

from __future__ import annotations

from collections.abc import Callable, Generator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import simpy

from sim.clock import SimClock
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

    def __init__(self, scenario: Scenario, osrm_url: str | None = None) -> None:
        self.scenario = scenario
        self.env = simpy.Environment()
        self.clock = SimClock(scenario.start, scenario.speed_factor)
        self.rng = RngFactory(scenario.seed)
        self.routing: RoutingClient = build_routing(str(scenario.routing), osrm_url)
        self._log: list[str] = []

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
