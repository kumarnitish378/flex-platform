"""The supervisor agent (M06, `simulator-spec.md` section 5.3).

The behaviour that matters here is what makes manual mode *manual*: one person, one
request at a time, after a delay. Tested against a fake platform so the bottleneck can be
observed rather than inferred.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest

from sim.agents.supervisor import (
    SupervisorAgent,
    SupervisorRecord,
    UnsupportedPolicyError,
)
from sim.agents.supervisor import summarise as summarise_dispatch
from sim.engine import Engine
from sim.scenario import SupervisorPolicy, load_scenario

SCENARIOS = Path(__file__).resolve().parent.parent / "scenarios"


class FakeDispatch:
    """A queue and a candidate list, with a record of what was assigned."""

    def __init__(
        self,
        queued: list[dict[str, Any]] | None = None,
        candidates: list[dict[str, Any]] | None = None,
    ) -> None:
        self.queued = queued if queued is not None else []
        self._candidates = candidates if candidates is not None else []
        self.assigned: list[tuple[uuid.UUID, uuid.UUID]] = []
        self.candidate_calls = 0
        self.fail_on: set[str] = set()
        self.refuse_assign = False
        #: Semi-auto (M09). Offers waiting for an answer, and the answers given.
        self.offers: list[dict[str, Any]] = []
        self.decisions: list[tuple[uuid.UUID, str, uuid.UUID | None]] = []
        self.refuse_decision = False

    def pending_requests(self, token: str, status: str = "queued") -> list[dict[str, Any]]:
        if "queue" in self.fail_on:
            raise RuntimeError("backend said no")
        return self.queued

    def candidates(self, token: str, request_id: uuid.UUID) -> list[dict[str, Any]]:
        if "candidates" in self.fail_on:
            raise RuntimeError("backend said no")
        self.candidate_calls += 1
        return self._candidates

    def assign(
        self,
        token: str,
        request_id: uuid.UUID,
        vehicle_id: uuid.UUID,
        trip_id: uuid.UUID | None = None,
        reason_code: str | None = None,
    ) -> dict[str, Any]:
        if self.refuse_assign:
            raise RuntimeError("409: the vehicle does not have a free seat")
        self.assigned.append((request_id, vehicle_id))
        # A served request leaves the queue, exactly as the real board behaves.
        self.queued = [item for item in self.queued if item["id"] != str(request_id)]
        return {}

    # --- semi-auto (M09) ---------------------------------------------------------

    def open_offers(
        self, token: str, request_id: uuid.UUID | None = None
    ) -> list[dict[str, Any]]:
        if "offers" in self.fail_on:
            raise RuntimeError("backend said no")
        return self.offers

    def suggestions(self, token: str, request_id: uuid.UUID) -> list[dict[str, Any]]:
        if "suggestions" in self.fail_on:
            raise RuntimeError("backend said no")
        return self._candidates

    def decide_suggestion(
        self,
        token: str,
        suggestion_id: uuid.UUID,
        decision: str,
        vehicle_id: uuid.UUID | None = None,
        note: str | None = None,
    ) -> dict[str, Any]:
        if self.refuse_decision:
            raise RuntimeError("409: that offer is no longer open")
        self.decisions.append((suggestion_id, decision, vehicle_id))
        # An answered offer leaves the board, as the real one does.
        self.offers = [item for item in self.offers if item["id"] != str(suggestion_id)]
        return {}

    def set_clock(self, now: Any) -> Any:
        return now


@pytest.fixture
def engine() -> Engine:
    return Engine(load_scenario(SCENARIOS / "smoke_tiny.yaml"))


def request_row(index: int = 0) -> dict[str, Any]:
    return {"id": str(uuid.uuid4()), "status": "queued", "waiting_since": index}


def candidate(eta: int, seats_free_after: int = 2, **extra: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "vehicle_id": str(uuid.uuid4()),
        "eta_to_pickup_seconds": eta,
        "seats_free_after": seats_free_after,
        "violations": [],
        "trip_id": None,
    }
    row.update(extra)
    return row


def supervisor_for(
    engine: Engine,
    platform: FakeDispatch,
    policy: SupervisorPolicy = SupervisorPolicy.manual_nearest,
    delay: tuple[int, int] = (20, 120),
    accept_rate: float = 0.7,
) -> SupervisorAgent:
    engine.platform = platform  # type: ignore[assignment]
    agent = SupervisorAgent(
        engine,
        token="supervisor-token",
        policy=policy,
        reaction_delay_seconds=delay,
        accept_rate=accept_rate,
    )
    engine.supervisor = agent
    engine.spawn(agent.watch)
    return agent


# --- picking a cab ------------------------------------------------------------------


def test_the_soonest_cab_wins(engine: Engine) -> None:
    """`manual_nearest`, and "nearest" means ETA, never distance (allocation-rules 3)."""
    far = candidate(eta=900)
    near = candidate(eta=120)
    platform = FakeDispatch([request_row()], [far, near])
    supervisor_for(engine, platform)

    engine.run()

    assert len(platform.assigned) == 1
    assert str(platform.assigned[0][1]) == near["vehicle_id"]


def test_a_full_cab_is_never_chosen(engine: Engine) -> None:
    """Capacity is the one hard rule the backend refuses outright (ADR-0011)."""
    full = candidate(eta=60, seats_free_after=-1)
    roomy = candidate(eta=600, seats_free_after=3)
    platform = FakeDispatch([request_row()], [full, roomy])
    supervisor_for(engine, platform)

    engine.run()

    assert str(platform.assigned[0][1]) == roomy["vehicle_id"]


def test_a_clean_cab_beats_a_closer_one_with_violations(engine: Engine) -> None:
    breaking = candidate(eta=60, violations=["detour_factor_exceeded"])
    clean = candidate(eta=300)
    platform = FakeDispatch([request_row()], [breaking, clean])
    supervisor_for(engine, platform)

    engine.run()
    assert str(platform.assigned[0][1]) == clean["vehicle_id"]


def test_an_imperfect_cab_beats_no_cab(engine: Engine) -> None:
    """A supervisor would rather send a flawed cab than leave someone standing."""
    only = candidate(eta=60, violations=["pickup_window_missed"])
    platform = FakeDispatch([request_row()], [only])
    agent = supervisor_for(engine, platform)

    engine.run()

    assert len(platform.assigned) == 1
    assert agent.record.violations_accepted == 1


def test_the_rules_an_assignment_broke_are_named(engine: Engine) -> None:
    """A bare count cannot tell a fleet problem from a seeding one. `evening_surge`
    reported 46 of 46 assignments breaking *something*, with no way to know what."""
    only = candidate(eta=60, violations=["pickup_window_missed", "eta_over_candidate_limit"])
    platform = FakeDispatch([request_row()], [only])
    agent = supervisor_for(engine, platform)

    engine.run()

    assert agent.record.violations_by_rule == {
        "pickup_window_missed": 1,
        "eta_over_candidate_limit": 1,
    }


def test_the_same_broken_rule_is_counted_each_time(engine: Engine) -> None:
    """ "Every cab is too far away" is the finding; it needs the tally, not a set."""
    rows = [request_row(), request_row()]
    only = candidate(eta=60, violations=["eta_over_candidate_limit"])
    platform = FakeDispatch(rows, [only])
    agent = supervisor_for(engine, platform)

    engine.run()

    assert agent.record.violations_by_rule["eta_over_candidate_limit"] == len(platform.assigned)
    assert len(platform.assigned) >= 2


def test_a_clean_assignment_names_no_rules(engine: Engine) -> None:
    platform = FakeDispatch([request_row()], [candidate(eta=60)])
    agent = supervisor_for(engine, platform)

    engine.run()

    assert agent.record.violations_accepted == 0
    assert agent.record.violations_by_rule == {}


def test_a_vip_waits_rather_than_sharing_a_cab(engine: Engine) -> None:
    """`allocation-rules.md` section 2 rule 4: VIP means no sharing, and S07 asserts it.

    The agent used to take any violating candidate when nothing clean was offered, so a
    VIP burst put VIPs in with other people - the full suite reported five pooled. "An
    imperfect cab beats no cab" is right for a detour limit and wrong here: this is a
    promise already made to that rider, not an average the supervisor can overrule."""
    only = candidate(eta=60, violations=["no_sharing"])
    platform = FakeDispatch([request_row()], [only])
    agent = supervisor_for(engine, platform)

    engine.run()

    assert platform.assigned == [], "the VIP waits for a car of their own"
    assert agent.record.no_candidate >= 1


def test_an_exclusive_trip_is_not_joined_by_someone_else(engine: Engine) -> None:
    """The same promise from the other side (rule 9): a trip already carrying a rider who
    asked not to share stays theirs."""
    only = candidate(eta=60, violations=["pooling_blocked"])
    platform = FakeDispatch([request_row()], [only])
    supervisor_for(engine, platform)

    engine.run()

    assert platform.assigned == []


def test_an_ordinary_rule_is_still_overridable(engine: Engine) -> None:
    """ADR-0011 stands for the rules that encode an average - the supervisor can see the
    road and the rule cannot."""
    only = candidate(eta=60, violations=["detour_minutes_exceeded"])
    platform = FakeDispatch([request_row()], [only])
    agent = supervisor_for(engine, platform)

    engine.run()

    assert len(platform.assigned) == 1
    assert agent.record.violations_accepted == 1


def test_a_clean_cab_is_preferred_over_an_exclusive_breach(engine: Engine) -> None:
    """And when there is a lawful option, nothing changes."""
    breaking = candidate(eta=60, violations=["no_sharing"])
    clean = candidate(eta=600)
    platform = FakeDispatch([request_row()], [breaking, clean])
    supervisor_for(engine, platform)

    engine.run()

    assert str(platform.assigned[0][1]) == clean["vehicle_id"]


def test_no_candidates_leaves_the_request_waiting(engine: Engine) -> None:
    """The rider's patience decides what happens next; that is the real dynamic."""
    platform = FakeDispatch([request_row()], [])
    agent = supervisor_for(engine, platform)

    engine.run()

    assert platform.assigned == []
    assert agent.record.no_candidate > 0


def test_every_cab_being_full_counts_as_no_candidate(engine: Engine) -> None:
    platform = FakeDispatch([request_row()], [candidate(eta=60, seats_free_after=-1)])
    agent = supervisor_for(engine, platform)

    engine.run()

    assert platform.assigned == []
    assert agent.record.no_candidate > 0


# --- the human bottleneck ------------------------------------------------------------------


def test_one_request_is_handled_at_a_time(engine: Engine) -> None:
    """The point of M06: a supervisor with forty pending does not dispatch forty at once.

    With a two-minute reaction delay and a one-hour run, roughly thirty assignments are
    possible - nowhere near the hundred queued. A simulator that assigned instantly would
    make manual mode look like an optimiser and hide the problem automation solves.
    """
    queue = [request_row(index) for index in range(100)]
    platform = FakeDispatch(queue, [candidate(eta=100)])
    supervisor_for(engine, platform, delay=(120, 120))

    engine.run()

    assert 0 < len(platform.assigned) <= 31


def test_a_faster_supervisor_gets_through_more(engine: Engine) -> None:
    """The delay is the model, so changing it must change the throughput."""
    slow_platform = FakeDispatch([request_row(i) for i in range(100)], [candidate(eta=100)])
    supervisor_for(engine, slow_platform, delay=(120, 120))
    engine.run()

    quick_engine = Engine(load_scenario(SCENARIOS / "smoke_tiny.yaml"))
    quick_platform = FakeDispatch([request_row(i) for i in range(100)], [candidate(eta=100)])
    supervisor_for(quick_engine, quick_platform, delay=(20, 20))
    quick_engine.run()

    assert len(quick_platform.assigned) > len(slow_platform.assigned)


def test_the_oldest_request_is_served_first(engine: Engine) -> None:
    """SUP-02 sorts by waiting time; the board hands them back in that order."""
    first, second = request_row(0), request_row(1)
    platform = FakeDispatch([first, second], [candidate(eta=100)])
    supervisor_for(engine, platform, delay=(20, 20))

    engine.run()

    assert str(platform.assigned[0][0]) == first["id"]


def test_an_empty_queue_costs_nothing(engine: Engine) -> None:
    platform = FakeDispatch([], [candidate(eta=100)])
    supervisor_for(engine, platform)

    engine.run()

    assert platform.candidate_calls == 0
    assert platform.assigned == []


# --- policies ---------------------------------------------------------------------------------


def test_an_absent_supervisor_never_assigns(engine: Engine) -> None:
    """S08 and the failsafe depend on this doing nothing at all."""
    platform = FakeDispatch([request_row()], [candidate(eta=60)])
    agent = supervisor_for(engine, platform, policy=SupervisorPolicy.absent)

    engine.run()

    assert platform.assigned == []
    assert agent.record.looks == 0


def test_an_unknown_policy_is_refused_not_silently_downgraded(engine: Engine) -> None:
    """All four documented policies are implemented since M09; anything else must still
    fail loudly rather than quietly becoming `manual_nearest`."""
    with pytest.raises(UnsupportedPolicyError):
        SupervisorAgent(engine, token="t", policy="telepathy")  # type: ignore[arg-type]


# --- semi-auto: answering offers rather than making assignments (M09) ----------------


def offer_row(vehicle_id: str | None = None, rank: int = 1) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "request_id": str(uuid.uuid4()),
        "vehicle_id": vehicle_id or str(uuid.uuid4()),
        "rank": rank,
        "offered_at": "2026-10-05T01:00:00Z",
        "failsafe_due_at": "2026-10-05T01:03:00Z",
    }


def test_approve_all_answers_the_offer_it_was_shown(engine: Engine) -> None:
    """The semi-auto half of the shift: one call, not three."""
    offered = offer_row()
    platform = FakeDispatch([], [candidate(eta=60)])
    platform.offers = [offered]
    agent = supervisor_for(engine, platform, policy=SupervisorPolicy.approve_all)

    engine.run()

    assert [decision for _, decision, _ in platform.decisions] == ["approve"]
    assert platform.decisions[0][0] == uuid.UUID(offered["id"])
    # It answered the offer; it did not go and assign something itself.
    assert platform.assigned == []
    assert agent.record.approvals == 1
    assert agent.record.offers_seen == 1


def test_approve_all_answers_one_offer_at_a_time(engine: Engine) -> None:
    """The human bottleneck does not disappear in semi-auto - it gets cheaper per
    request, which is the Phase 2 claim and a different thing."""
    platform = FakeDispatch([], [candidate(eta=60)])
    platform.offers = [offer_row() for _ in range(3)]
    supervisor_for(engine, platform, policy=SupervisorPolicy.approve_all)

    engine.run()

    assert len(platform.decisions) == 3
    assert platform.offers == []


def test_mixed_overrides_the_share_it_does_not_approve(engine: Engine) -> None:
    """`choose_other`, not `reject`: a rejection on its own leaves the rider where they
    were, and a supervisor who turns an offer down has somewhere else in mind."""
    other = str(uuid.uuid4())
    platform = FakeDispatch([], [candidate(eta=60, vehicle_id=other)])
    platform.offers = [offer_row() for _ in range(20)]
    agent = supervisor_for(
        engine, platform, policy=SupervisorPolicy.mixed, accept_rate=0.0
    )

    engine.run()

    assert {decision for _, decision, _ in platform.decisions} == {"choose_other"}
    assert all(chosen == uuid.UUID(other) for _, _, chosen in platform.decisions)
    assert agent.record.overrides == len(platform.decisions)
    assert agent.record.approvals == 0


def test_mixed_approves_when_there_is_nothing_else_to_choose(engine: Engine) -> None:
    """Counting "the only permitted cab" as a rejection would make the acceptance rate
    a measure of fleet size."""
    only = str(uuid.uuid4())
    offered = offer_row(vehicle_id=only)
    platform = FakeDispatch([], [candidate(eta=60, vehicle_id=only)])
    platform.offers = [offered]
    agent = supervisor_for(
        engine, platform, policy=SupervisorPolicy.mixed, accept_rate=0.0
    )

    engine.run()

    assert [decision for _, decision, _ in platform.decisions] == ["approve"]
    assert agent.record.approvals == 1


def test_the_acceptance_rate_counts_only_answered_offers(engine: Engine) -> None:
    """Phase 2's exit criterion. A manual run answers none and reports `None` rather
    than 0%, which would be a figure for something that never happened."""
    manual = SupervisorRecord(policy="manual_nearest", assignments=4)
    assert summarise_dispatch(manual).acceptance_rate is None

    answered = SupervisorRecord(
        policy="mixed", offers_seen=10, approvals=7, overrides=2, rejections=1
    )
    assert summarise_dispatch(answered).acceptance_rate == pytest.approx(0.7)


def test_a_refused_decision_is_recorded_not_fatal(engine: Engine) -> None:
    platform = FakeDispatch([], [candidate(eta=60)])
    platform.offers = [offer_row()]
    platform.refuse_decision = True
    agent = supervisor_for(engine, platform, policy=SupervisorPolicy.approve_all)

    engine.run()

    assert agent.record.refusals > 0
    assert agent.record.approvals == 0


def test_an_absent_supervisor_answers_no_offers(engine: Engine) -> None:
    """S08 depends on this: the failsafe only matters if nobody answered."""
    platform = FakeDispatch([], [candidate(eta=60)])
    platform.offers = [offer_row()]
    agent = supervisor_for(engine, platform, policy=SupervisorPolicy.absent)

    engine.run()

    assert platform.decisions == []
    assert agent.record.offers_seen == 0


# --- when the backend says no --------------------------------------------------------------------


def test_a_refused_assignment_is_recorded_not_fatal(engine: Engine) -> None:
    platform = FakeDispatch([request_row()], [candidate(eta=60)])
    platform.refuse_assign = True
    agent = supervisor_for(engine, platform)

    engine.run()

    assert agent.record.refusals > 0
    assert agent.record.assignments == 0


def test_a_failed_queue_read_does_not_end_the_shift(engine: Engine) -> None:
    platform = FakeDispatch([request_row()], [candidate(eta=60)])
    platform.fail_on.add("queue")
    agent = supervisor_for(engine, platform)

    engine.run()
    assert agent.record.errors


def test_a_failed_candidate_lookup_is_recorded(engine: Engine) -> None:
    platform = FakeDispatch([request_row()], [candidate(eta=60)])
    platform.fail_on.add("candidates")
    agent = supervisor_for(engine, platform)

    engine.run()

    assert agent.record.assignments == 0
    assert agent.record.errors


def test_a_supervisor_with_no_platform_does_nothing(engine: Engine) -> None:
    agent = SupervisorAgent(engine, token="t")
    engine.supervisor = agent
    engine.spawn(agent.watch)

    engine.run()
    assert agent.record.assignments == 0


# --- summary -------------------------------------------------------------------------------------


def test_the_dispatch_summary_reports_the_policy() -> None:
    record = SupervisorRecord(policy="manual_nearest", assignments=4, refusals=1)

    summary = summarise_dispatch(record)

    assert summary.policy == "manual_nearest"
    assert summary.assignments == 4
    assert summary.refusals == 1


def test_no_supervisor_means_no_policy() -> None:
    """An offline run had nobody watching, which is not the same as a policy of doing nothing."""
    assert summarise_dispatch(None).policy is None
