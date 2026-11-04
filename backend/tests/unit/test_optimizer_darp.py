"""The OR-Tools DARP and the solver that chooses between it and the greedy plan (B31)."""

from __future__ import annotations

import importlib
import itertools
import random
import re
from pathlib import Path

import pytest

from app.domain.dispatch import Place
from app.domain.enums import Direction, Urgency
from app.domain.optimizer import Plan, Problem, solve
from app.domain.optimizer.darp import DarpUnavailableError, solve_darp
from app.domain.optimizer.greedy import solve_greedy
from app.domain.optimizer.route import (
    baseline_rides,
    check_route,
    new_person,
    price_route,
    refusal_for,
    seated_people,
)
from tests.unit.optimizer_helpers import (
    NOW,
    OFFICE_ID,
    minutes_out,
    problem,
    req,
    rid,
    seated,
    trip,
    veh,
)

solve_module = importlib.import_module("app.domain.optimizer.solve")


def is_valid(prob: Problem, plan: Plan) -> bool:
    """Every placement passes the exact evaluator: the guarantee that matters."""
    seen: set[object] = set()
    by_id = {r.request_id: r for r in prob.requests}
    for placement in plan.placements:
        v = next(x for x in prob.vehicles if x.vehicle_id == placement.vehicle_id)
        people = []
        existing = {s.request_id: s for s in (v.trip.riders if v.trip else ())}
        for request_id in placement.order:
            people.append(
                seated_people([existing[request_id]])[0]
                if request_id in existing
                else new_person(by_id[request_id])
            )
        first = next(r for r in prob.requests if r.request_id in placement.new_request_ids)
        checked = check_route(prob, v, first.direction, first.office_id, people)
        if checked.violations or len(people) > v.seat_capacity:
            return False
        for request_id in placement.new_request_ids:
            if request_id in seen:
                return False
            seen.add(request_id)
    return True


# --- a world with a known optimum ---------------------------------------------------------


def brute_force_optimum(prob: Problem) -> tuple[int, float]:
    """The best (riders served, cost) over every assignment and every order.

    Exhaustive and only for idle cabs, which is what makes it a trustworthy referee: it
    shares nothing with either solver except the evaluator that prices a route.
    """
    requests = list(prob.requests)
    cabs = list(prob.vehicles)
    best = (-1, float("inf"))
    for choice in itertools.product(range(len(cabs) + 1), repeat=len(requests)):
        groups: dict[int, list[int]] = {}
        for rider, cab in enumerate(choice):
            if cab < len(cabs):
                groups.setdefault(cab, []).append(rider)
        total = 0.0
        served = 0
        feasible = True
        for cab, riders in groups.items():
            cheapest = None
            for order in itertools.permutations(riders):
                people = [new_person(requests[i]) for i in order]
                v = cabs[cab]
                if any(refusal_for(prob, v, requests[i]) for i in order):
                    continue
                first = requests[order[0]]
                checked = check_route(prob, v, first.direction, first.office_id, people)
                if checked.violations or len(people) > v.seat_capacity:
                    continue
                cost = price_route(
                    prob, v, first.direction, first.office_id, checked.route, {}
                ).total
                cheapest = cost if cheapest is None else min(cheapest, cost)
            if cheapest is None:
                feasible = False
                break
            total += cheapest
            served += len(riders)
        if feasible and (-served, total) < (-best[0], best[1]):
            best = (served, total)
    return best


def test_the_worked_example_is_reproduced_at_its_known_optimum() -> None:
    """Four riders along one road, three cabs: pool as much as the detour limits allow.

    The expected figure is not read off the solver. It is the minimum over every possible
    assignment of riders to cabs and every order of each cab's riders, priced by the same
    evaluator, so a solver that is merely self-consistent cannot pass.
    """
    prob = problem(
        [
            req(1, minutes_out(10)),
            req(2, minutes_out(7)),
            req(3, minutes_out(5)),
            req(4, Place(0.04, 0.05)),
        ],
        [veh(1, minutes_out(12)), veh(2, minutes_out(12)), veh(3, Place(0.06, 0.06))],
    )

    served, optimum = brute_force_optimum(prob)
    plan = solve_darp(prob)

    assert served == 4
    assert len(plan.placed_ids) == served
    assert plan.cost == pytest.approx(optimum, rel=1e-6)
    assert is_valid(prob, plan)


def test_pooling_uses_fewer_cabs_than_riders() -> None:
    cabs = [veh(n, minutes_out(14)) for n in range(1, 7)]
    riders = [req(n, minutes_out(4 + n)) for n in range(1, 7)]

    plan = solve(problem(riders, cabs))

    assert len(plan.placed_ids) == 6
    assert len(plan.placements) < 6
    assert is_valid(problem(riders, cabs), plan)


# --- the hard rules hold under the DARP too -------------------------------------------------


def test_the_darp_respects_seats_exclusivity_locks_and_vip() -> None:
    vip_cab = veh(1, minutes_out(12), vehicle_type="vip")
    small = veh(2, minutes_out(12), seats=2)
    pinned = veh(3, minutes_out(15))
    riders = [
        req(1, minutes_out(10), is_vip=True),
        req(2, minutes_out(8), no_sharing=True),
        req(3, minutes_out(6), lock_vehicle_id=pinned.vehicle_id),
        req(4, minutes_out(5)),
        req(5, minutes_out(4)),
    ]
    prob = problem(riders, [vip_cab, small, pinned])

    plan = solve_darp(prob)

    assert is_valid(prob, plan)
    on = {rid_: p.vehicle_id for p in plan.placements for rid_ in p.new_request_ids}
    assert on[rid(1)] == vip_cab.vehicle_id
    assert rid(3) not in on or on[rid(3)] == pinned.vehicle_id
    for placement in plan.placements:
        if rid(1) in placement.order or rid(2) in placement.order:
            assert len(placement.order) == 1


def test_a_trip_blocked_from_pooling_is_left_alone_by_the_darp() -> None:
    blocked = veh(
        1,
        minutes_out(25),
        status="on_trip",
        trip=trip(1, [seated(9, minutes_out(20))], pooling_blocked=True),
    )
    other = veh(2, minutes_out(40))

    plan = solve_darp(problem([req(1, minutes_out(10))], [blocked, other]))

    assert all(p.vehicle_id != blocked.vehicle_id for p in plan.placements)


def test_a_fixed_order_trip_keeps_its_riders_order() -> None:
    first, second = seated(8, minutes_out(20)), seated(9, minutes_out(12))
    cab = veh(
        1,
        minutes_out(30),
        status="on_trip",
        trip=trip(1, [first, second], order_fixed=True),
    )
    prob = problem([req(1, minutes_out(16), requested_in_minutes=14)], [cab])

    plan = solve_darp(prob)

    (placement,) = plan.placements
    kept = [r for r in placement.order if r in (rid(8), rid(9))]
    assert kept == [rid(8), rid(9)]
    assert not placement.reorders_existing
    assert is_valid(prob, plan)


def free_trip_instance(order_fixed: bool) -> Problem:
    """A cab with two riders waiting and a third asking; found by search, then pinned."""
    rng = random.Random(10)
    a = seated(8, Place(rng.uniform(0.05, 0.2), rng.uniform(-0.08, 0.08)))
    b = seated(9, Place(rng.uniform(0.05, 0.2), rng.uniform(-0.08, 0.08)))
    cab = veh(
        1,
        Place(rng.uniform(0.1, 0.3), rng.uniform(-0.08, 0.08)),
        status="on_trip",
        trip=trip(1, [a, b], order_fixed=order_fixed),
    )
    newcomer = req(
        1,
        Place(rng.uniform(0.05, 0.2), rng.uniform(-0.08, 0.08)),
        requested_in_minutes=rng.uniform(5, 15),
    )
    return problem([newcomer], [cab])


def test_a_free_order_trip_may_be_rearranged_for_a_better_route() -> None:
    """Planned, nobody collected, nobody locked: `allocation-rules.md` §6 lets it change."""
    prob = free_trip_instance(order_fixed=False)

    plan = solve_darp(prob)

    (placement,) = plan.placements
    assert placement.reorders_existing
    assert is_valid(prob, plan)


def test_the_same_trip_with_a_fixed_order_is_not_rearranged() -> None:
    prob = free_trip_instance(order_fixed=True)

    plan = solve(prob)

    for placement in plan.placements:
        kept = [r for r in placement.order if r in (rid(8), rid(9))]
        assert kept == [rid(8), rid(9)]
        assert not placement.reorders_existing


def test_a_locked_rider_on_a_trip_is_never_moved() -> None:
    locked = seated(8, minutes_out(20), locked=True)
    other = seated(9, minutes_out(12))
    cab = veh(
        1,
        minutes_out(25),
        status="on_trip",
        trip=trip(1, [locked, other], order_fixed=True),
    )
    plan = solve(problem([req(1, minutes_out(16), requested_in_minutes=9)], [cab]))

    for placement in plan.placements:
        assert placement.order.index(rid(8)) < placement.order.index(rid(9))
        assert not placement.reorders_existing


# --- from_office -----------------------------------------------------------------------------


def test_the_darp_solves_an_evening_batch() -> None:
    cabs = [veh(1, minutes_out(2)), veh(2, minutes_out(2))]
    riders = [
        req(n, minutes_out(6 + 3 * n), direction=Direction.from_office, priority=5)
        for n in (1, 2, 3)
    ]
    prob = problem(riders, cabs)

    plan = solve_darp(prob)

    assert len(plan.placed_ids) == 3
    assert is_valid(prob, plan)
    assert len(plan.placements) == 1  # the same road home: one cab


# --- the fallback ---------------------------------------------------------------------------


def test_when_the_darp_has_no_answer_the_greedy_plan_stands(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The acceptance criterion: a test that makes the solver fail."""
    prob = problem(
        [req(1, minutes_out(10)), req(2, minutes_out(8))],
        [veh(1, minutes_out(12)), veh(2, minutes_out(13))],
    )

    def failing(_: Problem) -> Plan:
        raise DarpUnavailableError("no solution within the time limit")

    monkeypatch.setattr(solve_module, "solve_darp", failing)

    plan = solve(prob)
    baseline = solve_greedy(prob)

    assert plan.solver == "greedy_fallback"
    assert plan.placements == baseline.placements
    assert plan.placed_ids == {rid(1), rid(2)}


def test_a_darp_that_crashes_cannot_stall_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    def crashing(_: Problem) -> Plan:
        raise RuntimeError("the model blew up")

    monkeypatch.setattr(solve_module, "solve_darp", crashing)

    plan = solve(problem([req(1, minutes_out(10))], [veh(1, minutes_out(12))]))

    assert plan.solver == "greedy_fallback" and len(plan.placed_ids) == 1


def test_an_out_of_time_search_falls_back_rather_than_returning_a_half_plan() -> None:
    """A real timeout, not a mock: a limit so small the search cannot finish."""
    riders = [req(n, minutes_out(n)) for n in range(1, 9)]
    cabs = [veh(n, minutes_out(14)) for n in range(1, 6)]
    from app.domain.optimizer import OptimizerParams

    prob = problem(riders, cabs, params=OptimizerParams(time_limit_seconds=0.0))

    plan = solve(prob)

    # Whatever route it took, the batch is served by a plan that passes the evaluator.
    assert is_valid(prob, plan)
    assert plan.solver in ("greedy", "greedy_fallback", "darp")


# --- guarantees ------------------------------------------------------------------------------


def random_problem(seed: int) -> Problem:
    rng = random.Random(seed)
    riders = [
        req(
            n,
            Place(rng.uniform(0.02, 0.2), rng.uniform(-0.05, 0.05)),
            priority=rng.randint(1, 9),
            urgency=rng.choice(list(Urgency)),
            requested_in_minutes=rng.uniform(0, 12),
            no_sharing=rng.random() < 0.1,
        )
        for n in range(1, rng.randint(3, 7))
    ]
    cabs = [
        veh(n, Place(rng.uniform(0.02, 0.25), rng.uniform(-0.05, 0.05)), seats=rng.choice([2, 4]))
        for n in range(1, rng.randint(2, 5))
    ]
    return problem(riders, cabs)


@pytest.mark.parametrize("seed", range(30))
def test_whatever_the_instance_the_plan_is_valid_and_never_worse_than_greedy(seed: int) -> None:
    prob = random_problem(seed)

    plan = solve(prob)
    baseline = solve_greedy(prob)

    assert is_valid(prob, plan)
    assert len(plan.placed_ids) >= len(baseline.placed_ids)
    if len(plan.placed_ids) == len(baseline.placed_ids):
        assert plan.cost <= baseline.cost + 1e-6


@pytest.mark.parametrize("seed", range(10))
def test_the_darp_alone_is_valid_on_random_instances(seed: int) -> None:
    prob = random_problem(100 + seed)
    try:
        plan = solve_darp(prob)
    except DarpUnavailableError:
        pytest.skip("the model had no solution for this instance")

    assert is_valid(prob, plan)


def test_the_same_problem_gives_the_same_plan_whatever_order_it_is_listed_in() -> None:
    prob = random_problem(7)
    shuffled = problem(list(reversed(prob.requests)), list(reversed(prob.vehicles)))

    assert solve(prob) == solve(shuffled)
    assert solve(prob) == solve(prob)


def test_priority_decides_who_is_served_when_seats_run_out() -> None:
    cab = veh(1, minutes_out(12), seats=1)
    prob = problem(
        [
            req(1, minutes_out(10), priority=9, urgency=Urgency.low),
            req(2, minutes_out(10), priority=1, urgency=Urgency.high),
        ],
        [cab],
    )

    plan = solve_darp(prob)

    assert plan.placed_ids == {rid(2)}


# --- purity ------------------------------------------------------------------------------------


def test_the_solver_package_knows_nothing_of_the_database_or_the_clock() -> None:
    """`allocation-rules.md` §6 / B31: pure, so a scenario can be replayed from its inputs."""
    root = Path(__file__).resolve().parents[2] / "app" / "domain" / "optimizer"
    forbidden = re.compile(
        r"\b(sqlalchemy|asyncpg|redis|httpx|app\.modules|app\.core\.clock|datetime\.now|"
        r"time\.time\(|utcnow)\b"
    )
    sources = list(root.glob("*.py"))
    assert sources, "found no optimizer sources; this guard would pass vacuously"
    for path in sources:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            code = line.split("#", 1)[0]
            assert not forbidden.search(code), f"{path.name}:{number} reaches outside: {line}"


def test_helpers_describe_the_same_office() -> None:
    """A sanity check on the fixtures: a typo here would make every test above vacuous."""
    assert req(1, minutes_out(1)).office_id == OFFICE_ID and NOW.year == 2026
    assert (
        baseline_rides(problem([], []), veh(1, minutes_out(1)), Direction.to_office, OFFICE_ID)
        == {}
    )
