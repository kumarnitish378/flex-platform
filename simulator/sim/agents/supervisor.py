"""The supervisor (M06, `simulator-spec.md` section 5.3).

The human bottleneck, modelled deliberately. In Phase 1 every assignment is one person
looking at a queue, picking a cab and pressing a button, and that person can only do one
at a time. A simulator that assigned instantly would make the manual mode look like an
optimiser and hide the exact problem automation is meant to solve - so the reaction delay
and the one-at-a-time rule are the *point* of this agent, not incidental detail.

Policies (section 5.3):

* `manual_nearest` - take the candidate with the lowest ETA after a reaction delay.
* `absent` - never respond. Tests what happens when nobody is watching: in Phase 1 the
  requests simply expire, and in Phase 2 the failsafe should fire.

`approve_all` and `mixed` are Phase 2 and are refused rather than quietly treated as
`manual_nearest`, which would make a Phase 2 scenario silently measure the wrong thing.
"""

from __future__ import annotations

import uuid
from collections.abc import Generator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np
import simpy

from sim.scenario import SupervisorPolicy

if TYPE_CHECKING:
    from sim.engine import Engine

Process = Generator[simpy.Event, Any, Any]

#: How often to glance at the queue when it is empty. Simulated seconds.
IDLE_POLL_SECONDS = 30

#: Policies this task implements. The rest are Phase 2.
SUPPORTED = (SupervisorPolicy.manual_nearest, SupervisorPolicy.absent)


class UnsupportedPolicyError(RuntimeError):
    """A scenario asked for a policy this phase does not implement."""


@dataclass
class SupervisorRecord:
    """What the supervisor did, for the run's metrics."""

    policy: str
    looks: int = 0
    assignments: int = 0
    refusals: int = 0
    no_candidate: int = 0
    violations_accepted: int = 0
    minutes_away: float = 0.0
    errors: list[str] = field(default_factory=list)


class SupervisorAgent:
    """One person, one queue, one request at a time."""

    def __init__(
        self,
        engine: Engine,
        token: str,
        policy: SupervisorPolicy = SupervisorPolicy.manual_nearest,
        reaction_delay_seconds: tuple[int, int] = (20, 120),
    ) -> None:
        if policy not in SUPPORTED:
            raise UnsupportedPolicyError(
                f"The {policy} policy arrives with Phase 2; this run supports "
                f"{', '.join(str(item) for item in SUPPORTED)}"
            )
        self.engine = engine
        self.token = token
        self.policy = policy
        self.record = SupervisorRecord(policy=str(policy))
        self._delay = reaction_delay_seconds
        #: True while the supervisor has stepped away (M07 `supervisor_absent`). Distinct
        #: from the `absent` policy, which means nobody was ever watching.
        self.away = False
        self._rng: np.random.Generator = engine.rng.for_agent(f"supervisor:{policy}")

    # --- the shift ------------------------------------------------------------------

    def watch(self) -> Process:
        """Work the queue until the run ends.

        One request per pass, deliberately: a supervisor with forty pending requests does
        not dispatch forty cabs at once, and a scenario that let them would report wait
        times no real operator could achieve.
        """
        if self.policy is SupervisorPolicy.absent:
            self.engine.record("supervisor is absent for this run")
            return

        while self.engine.now() < self.engine.scenario.end:
            if self.away:
                yield self.engine.env.timeout(IDLE_POLL_SECONDS)
                continue

            request = self._oldest_waiting()
            if request is None:
                yield self.engine.env.timeout(IDLE_POLL_SECONDS)
                continue

            # Section 5.3: the reaction delay is the human in the loop.
            yield self.engine.env.timeout(self._reaction_seconds())
            self._assign(request)

    def _oldest_waiting(self) -> dict[str, Any] | None:
        """The request that has been waiting longest (SUP-02 sorts by waiting time)."""
        platform = self.engine.platform
        if platform is None:
            return None
        try:
            queued = platform.pending_requests(self.token, status="queued")
        except Exception as exc:  # noqa: BLE001 - a failed glance is not a crash
            self.record.errors.append(f"queue: {type(exc).__name__}")
            return None

        self.record.looks += 1
        return queued[0] if queued else None

    # --- picking a cab -----------------------------------------------------------------

    def _assign(self, request: dict[str, Any]) -> None:
        platform = self.engine.platform
        assert platform is not None

        request_id = uuid.UUID(request["id"])
        try:
            candidates = platform.candidates(self.token, request_id)
        except Exception as exc:  # noqa: BLE001
            self.record.errors.append(f"candidates: {type(exc).__name__}")
            return

        choice = self._choose(candidates)
        if choice is None:
            # Nothing available. The request waits; the rider's patience decides what
            # happens next, which is exactly the real dynamic.
            self.record.no_candidate += 1
            return

        try:
            platform.assign(
                self.token,
                request_id=request_id,
                vehicle_id=uuid.UUID(choice["vehicle_id"]),
                trip_id=uuid.UUID(choice["trip_id"]) if choice.get("trip_id") else None,
            )
        except Exception as exc:  # noqa: BLE001 - a refused assignment is data, not a crash
            self.record.refusals += 1
            self.record.errors.append(f"assign: {exc}")
            self.engine.record(f"supervisor could not assign {request_id}: {exc}")
            return

        self.record.assignments += 1
        if choice.get("violations"):
            # ADR-0011: manual assignment reports hard-rule violations and applies anyway.
            # Counted so a scenario can tell "dispatched well" from "dispatched at all".
            self.record.violations_accepted += 1
        self.engine.record(
            f"supervisor assigned {request_id} to {choice['vehicle_id']} "
            f"(eta {choice.get('eta_to_pickup_seconds')}s)"
        )

    def _choose(self, candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
        """`manual_nearest`: soonest cab wins.

        Candidates with violations are taken only when nothing clean is offered - which
        mirrors a supervisor who would rather send an imperfect cab than none at all, and
        keeps the accepted-violation count meaningful.
        """
        # A full cab is not a candidate whatever its ETA: capacity is the one hard rule
        # the backend refuses outright (ADR-0011), so offering one wastes the assignment
        # and, in a scenario, looks like a dispatch failure that is really a bad choice.
        seated = [item for item in candidates if item.get("seats_free_after", 0) >= 0]
        if not seated:
            return None

        clean = [item for item in seated if not item.get("violations")]
        pool = clean or seated
        return min(pool, key=lambda item: item.get("eta_to_pickup_seconds", float("inf")))

    def _reaction_seconds(self) -> float:
        low, high = self._delay
        return float(self._rng.uniform(low, high))


@dataclass
class DispatchSummary:
    """What dispatch did, for `metrics.json`."""

    policy: str | None = None
    assignments: int = 0
    refusals: int = 0
    no_candidate: int = 0
    violations_accepted: int = 0
    errors: int = 0


def summarise(record: SupervisorRecord | None) -> DispatchSummary:
    if record is None:
        return DispatchSummary()
    return DispatchSummary(
        policy=record.policy,
        assignments=record.assignments,
        refusals=record.refusals,
        no_candidate=record.no_candidate,
        violations_accepted=record.violations_accepted,
        errors=len(record.errors),
    )
