"""Traffic conditions (M07, `simulator-spec.md` section 6).

The routing provider already varies speed by time of day — 08:00–10:30 and 17:30–20:30
are slow, the small hours are fast. That is the *baseline*, and it is the same table the
backend's `approx` provider uses, so the simulator and the platform agree about how long
a journey takes when nothing unusual is happening.

This module is the layer on top: the conditions an event injector turns on and off during
a run. Rain slows everything by a factor; a road closure adds a detour penalty. Several
can overlap — rain during the evening peak with a closure on the route is a perfectly
ordinary Tuesday — so conditions **multiply**, and each is removed independently when it
ends rather than by resetting the factor to 1.0 (which would silently cancel whatever
else was still running).

Phase 1 models a closure as a blanket slowdown rather than excluding specific edges: the
`approx` provider draws straight lines and has no edge list to exclude. Section 6 allows
exactly this ("detour penalty in sim movement only"); real edge exclusion arrives with
self-hosted OSRM (I02b).
"""

from __future__ import annotations

from dataclasses import dataclass

#: `simulator-spec.md` section 6: "rain (all x 0.7)".
RAIN_FACTOR = 0.7

#: A closure does not stop the fleet, it sends it the long way round. Applied as a
#: slowdown because the `approx` provider has no network to route around.
CLOSURE_FACTOR = 0.75


@dataclass(frozen=True, slots=True)
class Condition:
    """One thing making the roads slower (or faster) than the baseline."""

    name: str
    factor: float


class TrafficModel:
    """The conditions currently in force, and their combined effect on speed."""

    def __init__(self, routing: object | None = None) -> None:
        # Typed loosely on purpose: only the `approx` provider has a speed knob to turn.
        # A real router returns real durations, and a scenario that needs slower roads
        # there needs a self-hosted profile (I02b) rather than a multiplier.
        self._routing = routing
        self._conditions: dict[str, Condition] = {}
        self._apply()

    # --- reading ----------------------------------------------------------------------

    @property
    def factor(self) -> float:
        """Everything in force, multiplied together. 1.0 when the day is ordinary."""
        combined = 1.0
        for condition in self._conditions.values():
            combined *= condition.factor
        return combined

    @property
    def active(self) -> tuple[str, ...]:
        return tuple(sorted(self._conditions))

    def is_active(self, name: str) -> bool:
        return name in self._conditions

    # --- writing ----------------------------------------------------------------------

    def begin(self, name: str, factor: float) -> None:
        """Turn a condition on. Applying the same name twice replaces it, never stacks."""
        if factor <= 0:
            raise ValueError("a traffic factor must be positive; 0 would stop the fleet dead")
        self._conditions[name] = Condition(name=name, factor=factor)
        self._apply()

    def end(self, name: str) -> None:
        """Turn one condition off, leaving any others in force."""
        self._conditions.pop(name, None)
        self._apply()

    def _apply(self) -> None:
        if self._routing is not None and hasattr(self._routing, "traffic_factor"):
            self._routing.traffic_factor = self.factor
