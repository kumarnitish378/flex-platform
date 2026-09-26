"""The event injector (M07, `simulator-spec.md` section 7).

A scenario lists things that happen at a given time of day — rain at six, a breakdown at
quarter past ten — and this fires them. Each becomes one SimPy process that waits for its
moment, does the thing, and (where the event has a duration) undoes it afterwards.

Two rules shape the design:

* **Events act through the same surfaces as the agents.** A breakdown is the driver
  reporting a breakdown to `/driver/issues`, not a flag set on a vehicle row. If the
  platform would refuse it, the scenario should find that out.
* **An event the simulator cannot model faithfully is refused, never approximated.** A
  `vip_burst` that bursts ordinary riders would make S07 report a VIP-pooling result it
  never actually tested. Refusing is the honest failure.
"""

from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import simpy

from sim.scenario import Event
from sim.traffic import CLOSURE_FACTOR, RAIN_FACTOR

if TYPE_CHECKING:
    from sim.agents.driver import DriverAgent
    from sim.engine import Engine

Process = Generator[simpy.Event, Any, Any]

#: Default length for an event whose scenario entry gives no `duration_min`.
DEFAULT_DURATION_MINUTES = 60

#: What each type does, for validation and error messages.
SUPPORTED = (
    "rain",
    "road_closure",
    "demand_surge",
    "vehicle_breakdown",
    "gps_loss",
    "offline",
    "supervisor_absent",
)

#: Listed in section 7 but not implementable yet, with the reason. Refused loudly so a
#: scenario cannot quietly measure something other than what it claims to.
NOT_YET = {
    "vip_burst": (
        "the seeded world does not say which employees are VIP, so a burst would use "
        "ordinary riders and S07 would report a VIP result it never tested"
    ),
    "optimizer_down": (
        "there is no optimizer to take down in Phase 1; automatic mode arrives in Phase 2"
    ),
}


class UnsupportedEventError(RuntimeError):
    """A scenario asked for an event this phase cannot model honestly."""


@dataclass
class EventRecord:
    """What the injector did, for the run's metrics."""

    fired: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class EventSummary:
    """Events, for `metrics.json`."""

    scheduled: int = 0
    fired: int = 0
    skipped: int = 0
    errors: int = 0
    types: tuple[str, ...] = ()


class EventInjector:
    """Fires a scenario's timed events and undoes the ones that end."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self.record = EventRecord()
        self._rng = engine.rng.for_agent("events")

    # --- scheduling -------------------------------------------------------------------

    def schedule(self, events: list[Event]) -> int:
        """Spawn one process per event. Returns how many were scheduled.

        Validation happens here rather than at fire time: a scenario naming an event this
        phase cannot model should fail at the start of the run, not ninety simulated
        minutes in when the results are half-collected.
        """
        for event in events:
            if event.type in NOT_YET:
                raise UnsupportedEventError(
                    f"The {event.type} event is not supported yet: {NOT_YET[event.type]}"
                )
            if event.type not in SUPPORTED:
                raise UnsupportedEventError(
                    f"Unknown event type {event.type!r}; this phase supports {', '.join(SUPPORTED)}"
                )

        for event in events:
            self.engine.spawn(lambda event=event: self._fire(event))  # type: ignore[misc]
        return len(events)

    def _fire(self, event: Event) -> Process:
        delay = self._seconds_until(event)
        if delay is None:
            self.record.skipped.append(event.type)
            self.engine.record(f"event {event.type} at {event.at_ist} falls outside the run")
            return

        yield self.engine.env.timeout(delay)

        handler = getattr(self, f"_on_{event.type}")
        self.record.fired.append(event.type)
        self.engine.record(f"event {event.type} fired")
        try:
            yield from handler(event)
        except Exception as exc:  # noqa: BLE001 - a failed event is data, not a crash
            self.record.errors.append(f"{event.type}: {type(exc).__name__}: {exc}")
            self.engine.record(f"event {event.type} failed: {exc}")

    def _seconds_until(self, event: Event) -> float | None:
        """Simulated seconds from now until this event's local time, or None if it has passed."""
        moment = self.engine.at_ist(event.at_ist)
        if moment is None:
            return None
        delay = (moment - self.engine.now()).total_seconds()
        return delay if delay >= 0 else None

    def _minutes(self, event: Event) -> float:
        return float(event.duration_min or DEFAULT_DURATION_MINUTES)

    # --- weather and roads ------------------------------------------------------------

    def _on_rain(self, event: Event) -> Process:
        """Section 6: rain slows everything by a factor."""
        yield from self._hold_condition("rain", RAIN_FACTOR, self._minutes(event))

    def _on_road_closure(self, event: Event) -> Process:
        yield from self._hold_condition("road_closure", CLOSURE_FACTOR, self._minutes(event))

    def _hold_condition(self, name: str, factor: float, minutes: float) -> Process:
        traffic = self.engine.traffic
        traffic.begin(name, factor)
        self.engine.record(f"{name} started (traffic factor now {traffic.factor:.2f})")
        yield self.engine.env.timeout(minutes * 60)
        traffic.end(name)
        self.engine.record(f"{name} ended (traffic factor now {traffic.factor:.2f})")

    # --- demand -----------------------------------------------------------------------

    def _on_demand_surge(self, event: Event) -> Process:
        """Extra riders ask for a cab now.

        Drawn from the people who were not travelling today rather than invented: a surge
        is more of the same population wanting cabs, and reusing a seeded employee means
        the request goes through a real account with a real home address.
        """
        idle = [rider for rider in self.engine.riders if not rider.travelling]
        wanted = self._surge_size(event, len(self.engine.riders))
        if not idle:
            self.record.errors.append("demand_surge: every rider is already travelling")
            return

        chosen = idle[: min(wanted, len(idle))]
        for rider in chosen:
            self.engine.spawn(rider.travel_now)
        self.engine.record(f"demand surge: {len(chosen)} extra riders (wanted {wanted})")
        yield self.engine.env.timeout(0)

    def _surge_size(self, event: Event, population: int) -> int:
        if event.count is not None:
            return event.count
        if event.multiplier is not None:
            # `multiplier: 1.15` means "15% more demand than the day already has".
            return max(1, round(population * (event.multiplier - 1.0)))
        return max(1, round(population * 0.1))

    # --- faults -----------------------------------------------------------------------

    def _on_vehicle_breakdown(self, event: Event) -> Process:
        driver = self._pick_driver(event)
        if driver is None:
            return
        driver.break_down("Simulated breakdown (scenario event)")
        yield self.engine.env.timeout(0)

    def _on_gps_loss(self, event: Event) -> Process:
        driver = self._pick_driver(event)
        if driver is None:
            return
        yield from driver.lose_gps(self._minutes(event))

    def _on_offline(self, event: Event) -> Process:
        driver = self._pick_driver(event)
        if driver is None:
            return
        yield from driver.go_offline(self._minutes(event))

    def _pick_driver(self, event: Event) -> DriverAgent | None:
        """The vehicle this event names, or one chosen at random.

        A breakdown with riders aboard is the interesting case (S05), so a random pick
        prefers a cab that is actually on a trip. Falling back to any on-duty cab keeps
        the event from silently doing nothing on a quiet stretch of the day.
        """
        drivers = self.engine.drivers
        if not drivers:
            self.record.errors.append(f"{event.type}: the run has no drivers")
            return None

        if event.vehicle and event.vehicle != "random":
            for driver in drivers:
                if driver.vehicle.vehicle_id == event.vehicle:
                    return driver
            self.record.errors.append(f"{event.type}: no vehicle {event.vehicle}")
            return None

        carrying = [driver for driver in drivers if driver.vehicle.driving]
        pool = carrying or [driver for driver in drivers if driver.vehicle.on_duty] or drivers
        return pool[int(self._rng.integers(len(pool)))]

    # --- people -----------------------------------------------------------------------

    def _on_supervisor_absent(self, event: Event) -> Process:
        """The supervisor steps away. Requests pile up; S08's failsafe is Phase 2."""
        supervisor = self.engine.supervisor
        if supervisor is None:
            self.record.errors.append("supervisor_absent: this run has no supervisor")
            return

        minutes = self._minutes(event)
        supervisor.away = True
        self.engine.record(f"supervisor stepped away for {minutes:.0f} min")
        yield self.engine.env.timeout(minutes * 60)
        supervisor.away = False
        supervisor.record.minutes_away += minutes
        self.engine.record("supervisor came back")


def summarise(injector: EventInjector | None, scheduled: int = 0) -> EventSummary:
    if injector is None:
        return EventSummary()
    return EventSummary(
        scheduled=scheduled,
        fired=len(injector.record.fired),
        skipped=len(injector.record.skipped),
        errors=len(injector.record.errors),
        types=tuple(sorted(set(injector.record.fired))),
    )
