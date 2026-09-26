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
) -> SupervisorAgent:
    engine.platform = platform  # type: ignore[assignment]
    agent = SupervisorAgent(
        engine, token="supervisor-token", policy=policy, reaction_delay_seconds=delay
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


@pytest.mark.parametrize("policy", [SupervisorPolicy.approve_all, SupervisorPolicy.mixed])
def test_a_phase_two_policy_is_refused_not_silently_downgraded(
    engine: Engine, policy: SupervisorPolicy
) -> None:
    """Treating it as `manual_nearest` would make a Phase 2 scenario measure the wrong thing."""
    with pytest.raises(UnsupportedPolicyError, match="Phase 2"):
        SupervisorAgent(engine, token="t", policy=policy)


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
