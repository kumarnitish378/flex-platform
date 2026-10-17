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

import uuid
from collections.abc import Generator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import simpy

from sim.scenario import Direction, Event
from sim.traffic import CLOSURE_FACTOR, RAIN_FACTOR

if TYPE_CHECKING:
    from sim.agents.driver import DriverAgent
    from sim.engine import Engine

Process = Generator[simpy.Event, Any, Any]

#: Default length for an event whose scenario entry gives no `duration_min`.
DEFAULT_DURATION_MINUTES = 60

#: How long `lock_requests` keeps watching for riders to lock, and how often it looks.
#: An hour is long enough to catch a morning peak arriving and short enough that the
#: locks are all placed before the run is half over.
LOCK_WINDOW_SECONDS = 60 * 60
LOCK_POLL_SECONDS = 20

#: What each type does, for validation and error messages.
SUPPORTED = (
    "rain",
    "road_closure",
    "demand_surge",
    "vehicle_breakdown",
    "gps_loss",
    "offline",
    "supervisor_absent",
    "vip_burst",
    "lock_requests",
)

#: Listed in section 7 but not implementable yet, with the reason. Refused loudly so a
#: scenario cannot quietly measure something other than what it claims to.
NOT_YET = {
    "optimizer_down": (
        "the optimizer that Phase 3 runs does not exist yet; Phase 2's automatic path is"
        " the semi-auto sweep, and taking it down is not the same experiment"
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

        direction = event.direction or Direction.to_office
        chosen = idle[: min(wanted, len(idle))]
        for rider in chosen:
            self.engine.spawn(lambda rider=rider: rider.travel_now(direction))  # type: ignore[misc]
        self.engine.record(
            f"demand surge: {len(chosen)} extra riders {direction} (wanted {wanted})"
        )
        yield self.engine.env.timeout(0)

    def _surge_size(self, event: Event, population: int) -> int:
        if event.count is not None:
            return event.count
        if event.multiplier is not None:
            # `multiplier: 1.15` means "15% more demand than the day already has".
            return max(1, round(population * (event.multiplier - 1.0)))
        return max(1, round(population * 0.1))

    def _on_vip_burst(self, event: Event) -> Process:
        """Several VIPs ask at once (S07).

        Only riders the backend actually seeded as VIP are used. Bursting ordinary riders
        would produce a run that looks like S07 and tests none of it - the whole scenario
        is about VIPs never being pooled and never getting an ordinary cab.
        """
        idle = [
            rider for rider in self.engine.riders if rider.profile.is_vip and not rider.travelling
        ]
        wanted = event.count or 5
        if not idle:
            self.record.errors.append("vip_burst: the seeded world has no VIP rider free to travel")
            return

        if len(idle) < wanted:
            # Worth saying: a burst of three when the scenario asked for five is a
            # weaker test, and silently shrinking it would hide that.
            self.record.errors.append(
                f"vip_burst: wanted {wanted} VIPs, only {len(idle)} were free"
            )

        direction = event.direction or Direction.to_office
        for rider in idle[:wanted]:
            self.engine.spawn(lambda rider=rider: rider.travel_now(direction))  # type: ignore[misc]
        self.engine.record(f"vip burst: {min(wanted, len(idle))} VIP riders {direction}")
        yield self.engine.env.timeout(0)

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

    def _on_lock_requests(self, event: Event) -> Process:
        """A supervisor pins waiting requests to a cab (`control-model.md` §3, S09).

        Locked to a cab **they choose**, not the one the system would have picked -
        otherwise "the optimizer never moved it" would be indistinguishable from "the
        optimizer agreed", which is the thing S09 exists to tell apart.
        """
        platform = self.engine.platform
        supervisor = self.engine.supervisor
        if platform is None or supervisor is None:
            self.record.errors.append("lock_requests: this run has no supervisor")
            return

        wanted = event.count or 10
        # Polled rather than done in one glance. The queue at any given instant is
        # nearly empty - in `semi_auto` the sweep offers a cab within seconds and the
        # supervisor answers - so a single look lands either before the demand or
        # between two riders, and locks nothing. The first live run did exactly that,
        # and `locks_respected` failed rather than passing, which is the point of
        # failing a check that measured nothing.
        deadline = self.engine.env.now + LOCK_WINDOW_SECONDS
        locked = 0
        while locked < wanted and self.engine.env.now < deadline:
            try:
                queued = platform.pending_requests(supervisor.token, status="queued")
            except Exception as exc:  # noqa: BLE001
                self.record.errors.append(f"lock_requests: {type(exc).__name__}")
                return

            for request in queued:
                if locked >= wanted:
                    break
                request_id = uuid.UUID(request["id"])
                if request_id in self.engine.locks:
                    continue
                vehicle_id = self._second_choice(request_id)
                if vehicle_id is None:
                    continue
                try:
                    platform.apply_override(
                        supervisor.token,
                        action="lock",
                        reason_code="local_knowledge",
                        note="scenario lock",
                        request_id=request_id,
                        vehicle_id=vehicle_id,
                    )
                except Exception as exc:  # noqa: BLE001 - a refused lock is data
                    self.record.errors.append(f"lock: {exc}")
                    continue
                self.engine.locks[request_id] = vehicle_id
                locked += 1

            yield self.engine.env.timeout(LOCK_POLL_SECONDS)

        self.engine.record(f"supervisor locked {locked} request(s)")

    def _second_choice(self, request_id: uuid.UUID) -> uuid.UUID | None:
        """A cab that is permitted but is **not** the system's first pick."""
        platform = self.engine.platform
        supervisor = self.engine.supervisor
        assert platform is not None and supervisor is not None
        try:
            options = platform.suggestions(supervisor.token, request_id)
        except Exception as exc:  # noqa: BLE001
            self.record.errors.append(f"lock candidates: {type(exc).__name__}")
            return None
        if not options:
            return None
        chosen = options[1] if len(options) > 1 else options[0]
        return uuid.UUID(str(chosen["vehicle_id"]))

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
