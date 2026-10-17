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

* `approve_all` - in a `semi_auto` scope, take whatever the system offered, after the
  same reaction delay. The optimistic bound: what the platform achieves when the human
  never disagrees.
* `mixed` - approve a configurable share and override the rest with a cab of their own
  choosing. The realistic one, and the only policy that makes the Phase 2 exit
  criterion mean anything: acceptance is measured against offers that could have been
  rejected.

**`approve_all` and `mixed` answer offers; `manual_nearest` makes assignments.** That
is not a detail of implementation - it is the difference the scenarios exist to
measure. A manual supervisor reads the queue, asks for candidates and presses assign;
a semi-auto one reads what the system has already proposed and answers yes or no. The
second is a smaller amount of work per request, which is the Phase 2 claim ("supervisor
time per request reduced vs Phase 1"), and it is only true if the agent really does the
smaller thing.
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

#: Every policy `simulator-spec.md` section 5.3 names. All four are implemented;
#: `approve_all` and `mixed` arrived with M09.
SUPPORTED = (
    SupervisorPolicy.manual_nearest,
    SupervisorPolicy.absent,
    SupervisorPolicy.approve_all,
    SupervisorPolicy.mixed,
)

#: Policies that answer the system's offers rather than assigning from scratch.
ANSWERING = (SupervisorPolicy.approve_all, SupervisorPolicy.mixed)


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
    #: Semi-auto (M09). Offers answered, and how. `overrides` are `choose_other`: a
    #: rejection of what was offered **followed by a manual choice**, which is what
    #: makes an acceptance rate a measurement rather than an assumption.
    offers_seen: int = 0
    approvals: int = 0
    overrides: int = 0
    rejections: int = 0
    #: Which rules, and how often. A bare count says "every assignment broke something"
    #: without saying what, which is the difference between a finding and a mystery: a
    #: surge where every cab is too far away is a fleet problem, one where every cab is
    #: the wrong type is a seeding problem, and the count alone cannot tell them apart.
    violations_by_rule: dict[str, int] = field(default_factory=dict)
    #: How old each chosen cab's position was. A run where every assignment is flagged
    #: `gps_stale` needs the number, not the flag, to tell a real problem from a
    #: time-compression artefact.
    gps_age_seconds: list[float] = field(default_factory=list)
    minutes_away: float = 0.0
    errors: list[str] = field(default_factory=list)


#: Violations a supervisor will not accept, however long the rider has waited.
#:
#: ADR-0011 makes hard rules advisory in manual mode, and that is right for the ones that
#: encode an average - a detour limit, an ETA ceiling - because the supervisor can see the
#: road and the rule cannot. These two are different in kind: they are promises already
#: made to a particular rider. `allocation-rules.md` section 2 rule 4 is "VIP -> VIP car
#: immediately, no waiting, **no sharing**", and rule 9 is "request marked `no_sharing` ->
#: exclusive trip". Putting that rider in with someone else does not give them a slightly
#: worse ride; it gives them the thing they were promised would not happen.
#:
#: S07 asserts `vip_never_pooled`, and the agent was breaking it by design: five VIPs
#: pooled in the full suite, two of them genuinely sharing. The honest trade is that a VIP
#: waits for a VIP car - and that wait then shows up in the metrics, where it belongs.
EXCLUSIVITY_VIOLATIONS = frozenset({"no_sharing", "pooling_blocked"})


def _breaks_a_promise(candidate: dict[str, Any]) -> bool:
    return bool(EXCLUSIVITY_VIOLATIONS.intersection(candidate.get("violations") or []))


class SupervisorAgent:
    """One person, one queue, one request at a time."""

    def __init__(
        self,
        engine: Engine,
        token: str,
        policy: SupervisorPolicy = SupervisorPolicy.manual_nearest,
        reaction_delay_seconds: tuple[int, int] = (20, 120),
        accept_rate: float = 0.7,
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
        #: `mixed` only. The share of offers this supervisor approves; the rest are
        #: overridden with a cab they pick themselves.
        self._accept_rate = accept_rate
        #: Offers the backend refused. A supervisor does not press the same dead
        #: button forty times; without this, one stale offer starves the queue for the
        #: rest of the run, which is exactly what S08's first live run did (39 of its
        #: 43 refusals were one offer).
        self._unanswerable: set[str] = set()
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

            if self.policy in ANSWERING:
                offer = self._oldest_offer()
                if offer is None:
                    yield self.engine.env.timeout(IDLE_POLL_SECONDS)
                    continue
                # The same reaction delay, deliberately: the Phase 2 claim is that a
                # supervisor spends *less* time per request, and giving the answering
                # policies a shorter delay would assume the conclusion. What changes is
                # how many requests one person can get through, which falls out of
                # doing one call instead of three.
                yield self.engine.env.timeout(self._reaction_seconds())
                self._answer(offer)
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

    def _oldest_offer(self) -> dict[str, Any] | None:
        """The offer that has been waiting longest for an answer (M09).

        One per pass, like the manual queue: a supervisor with forty pending offers
        still answers them one at a time, and the whole point of measuring semi-auto is
        how far that one person gets.
        """
        platform = self.engine.platform
        if platform is None:
            return None
        try:
            offers = platform.open_offers(self.token)
        except Exception as exc:  # noqa: BLE001 - a failed glance is not a crash
            self.record.errors.append(f"offers: {type(exc).__name__}")
            return None

        self.record.looks += 1
        fresh = [item for item in offers if str(item.get("id")) not in self._unanswerable]
        if not fresh:
            return None
        # Rank 1 is the system's first choice; the siblings are closed with it.
        first = [item for item in fresh if item.get("rank") == 1] or fresh
        return min(first, key=lambda item: str(item.get("offered_at")))

    def _answer(self, offer: dict[str, Any]) -> None:
        """Approve the offer, or override it with a cab of our own choosing."""
        platform = self.engine.platform
        assert platform is not None

        self.record.offers_seen += 1
        suggestion_id = uuid.UUID(offer["id"])
        request_id = uuid.UUID(offer["request_id"])

        if self.policy is SupervisorPolicy.approve_all or self._approves():
            self._decide(suggestion_id, "approve")
            return

        # `mixed` rejecting: a rejection on its own leaves the rider exactly where they
        # were, so a supervisor who rejects always has somewhere else in mind. The
        # override is `choose_other`, which the backend records as a rejection of what
        # was offered **and** assigns the cab actually chosen - one call, which is what
        # the supervisor's screen does.
        alternative = self._alternative_to(request_id, offer)
        if alternative is None:
            # Nothing else is permitted, so the offer is the only option there is.
            # Approving it is what a supervisor would do, and counting this as a
            # rejection would make the acceptance rate a measure of fleet size.
            self._decide(suggestion_id, "approve")
            return
        self._decide(suggestion_id, "choose_other", vehicle_id=alternative)

    def _decide(
        self, suggestion_id: uuid.UUID, decision: str, vehicle_id: uuid.UUID | None = None
    ) -> None:
        platform = self.engine.platform
        assert platform is not None
        try:
            platform.decide_suggestion(
                self.token,
                suggestion_id=suggestion_id,
                decision=decision,
                vehicle_id=vehicle_id,
                note="simulated supervisor" if decision != "approve" else None,
            )
        except Exception as exc:  # noqa: BLE001 - a refused decision is data, not a crash
            self.record.refusals += 1
            self.record.errors.append(f"decision: {exc}")
            self.engine.record(f"supervisor could not answer {suggestion_id}: {exc}")
            self._unanswerable.add(str(suggestion_id))
            return

        if decision == "approve":
            self.record.approvals += 1
            self.record.assignments += 1
        elif decision == "choose_other":
            self.record.overrides += 1
            self.record.assignments += 1
        else:
            self.record.rejections += 1
        self.engine.record(f"supervisor {decision} on offer {suggestion_id}")

    def _alternative_to(self, request_id: uuid.UUID, offer: dict[str, Any]) -> uuid.UUID | None:
        """A cab this supervisor would send instead of the one offered."""
        platform = self.engine.platform
        assert platform is not None
        try:
            candidates = platform.suggestions(self.token, request_id)
        except Exception as exc:  # noqa: BLE001
            self.record.errors.append(f"suggestions: {type(exc).__name__}")
            return None

        offered = str(offer.get("vehicle_id"))
        others = [item for item in candidates if str(item.get("vehicle_id")) != offered]
        choice = self._choose(others)
        return uuid.UUID(choice["vehicle_id"]) if choice else None

    def _approves(self) -> bool:
        """`mixed`: approve this share of offers, from the run's seeded generator."""
        return bool(self._rng.random() < self._accept_rate)

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
        age = choice.get("gps_age_seconds")
        if age is not None:
            self.record.gps_age_seconds.append(float(age))
        broken = choice.get("violations") or []
        if broken:
            # ADR-0011: manual assignment reports hard-rule violations and applies anyway.
            # Counted so a scenario can tell "dispatched well" from "dispatched at all".
            self.record.violations_accepted += 1
            for rule in broken:
                self.record.violations_by_rule[str(rule)] = (
                    self.record.violations_by_rule.get(str(rule), 0) + 1
                )
        self.engine.record(
            f"supervisor assigned {request_id} to {choice['vehicle_id']} "
            f"(eta {choice.get('eta_to_pickup_seconds')}s)"
        )

    def _choose(self, candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
        """`manual_nearest`: soonest cab wins.

        Candidates with violations are taken only when nothing clean is offered - which
        mirrors a supervisor who would rather send an imperfect cab than none at all, and
        keeps the accepted-violation count meaningful. Two kinds of violation are never
        taken, because for those "an imperfect cab" is not what the rider gets.
        """
        # A full cab is not a candidate whatever its ETA: capacity is the one hard rule
        # the backend refuses outright (ADR-0011), so offering one wastes the assignment
        # and, in a scenario, looks like a dispatch failure that is really a bad choice.
        seated = [item for item in candidates if item.get("seats_free_after", 0) >= 0]
        usable = [item for item in seated if not _breaks_a_promise(item)]
        if not usable:
            return None

        clean = [item for item in usable if not item.get("violations")]
        pool = clean or usable
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
    violations_by_rule: dict[str, int] = field(default_factory=dict)
    gps_age_seconds_median: float | None = None
    gps_age_seconds_max: float | None = None
    #: Semi-auto (M09). `acceptance_rate` is the Phase 2 exit criterion: approvals over
    #: offers the supervisor actually answered. Overrides and rejections are both
    #: counted against it, and offers the **failsafe** closed are not counted at all -
    #: nobody accepted those, and counting them would score an absent supervisor 100%.
    offers_seen: int = 0
    approvals: int = 0
    overrides: int = 0
    rejections: int = 0
    acceptance_rate: float | None = None
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
        violations_by_rule=dict(record.violations_by_rule),
        gps_age_seconds_median=_median(record.gps_age_seconds),
        gps_age_seconds_max=max(record.gps_age_seconds, default=None),
        offers_seen=record.offers_seen,
        approvals=record.approvals,
        overrides=record.overrides,
        rejections=record.rejections,
        acceptance_rate=_rate(record),
        errors=len(record.errors),
    )


def _rate(record: SupervisorRecord) -> float | None:
    """Approvals over answered offers, or `None` when none were answered.

    `None` rather than 0.0: a manual run answers no offers at all, and reporting it as
    0% acceptance would put a figure on the board for something that did not happen.
    """
    answered = record.approvals + record.overrides + record.rejections
    return record.approvals / answered if answered else None


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0
