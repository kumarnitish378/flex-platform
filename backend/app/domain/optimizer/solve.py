"""The solver entry point: pick the best valid plan for a batch (`allocation-rules.md` §6).

Two solvers, one rule for choosing between them. The greedy plan is always computed - it
is cheap, it is the Phase 2 behaviour, and it is the baseline. The DARP plan is computed
next. Whatever the DARP leaves unplaced or places illegally is **repaired by the greedy
search on the cabs the DARP did not touch**, so a partial DARP answer is still a good one.
Then the better of the two complete plans is returned: more riders served first, then
lower exact §4 cost. A solver that returns nothing, raises, or runs out of time costs the
batch nothing - the greedy plan stands, and says so (`greedy_fallback`).
"""

from __future__ import annotations

from dataclasses import replace

from app.core.logging import get_logger
from app.domain.optimizer.darp import DarpUnavailableError, solve_darp
from app.domain.optimizer.greedy import solve_greedy
from app.domain.optimizer.model import Plan, Problem, Unplaced

logger = get_logger(__name__)


def solve(problem: Problem) -> Plan:
    """Solve one batch. Pure: the same problem always returns the same plan."""
    if not problem.requests:
        return Plan()

    greedy = solve_greedy(problem)
    try:
        darp = _complete(problem, solve_darp(problem))
    except DarpUnavailableError as exc:
        logger.warning("darp_unavailable", reason=str(exc))
        return replace(greedy, solver="greedy_fallback")
    except Exception:  # noqa: BLE001 - the model must never be able to stall dispatch
        logger.exception("darp_failed")
        return replace(greedy, solver="greedy_fallback")

    return darp if _better(darp, greedy) else greedy


def _better(candidate: Plan, baseline: Plan) -> bool:
    """More riders served wins; at equal service, strictly lower cost wins."""
    if len(candidate.placed_ids) != len(baseline.placed_ids):
        return len(candidate.placed_ids) > len(baseline.placed_ids)
    return candidate.cost < baseline.cost - 1e-9


def _complete(problem: Problem, darp: Plan) -> Plan:
    """Give whatever the DARP did not place a chance on the cabs it left alone."""
    leftover = frozenset(item.request_id for item in darp.unplaced)
    if not leftover:
        return darp
    touched = {placement.vehicle_id for placement in darp.placements}
    spare = replace(
        problem, vehicles=tuple(v for v in problem.vehicles if v.vehicle_id not in touched)
    )
    repair = solve_greedy(spare, only=leftover)
    unplaced: list[Unplaced] = list(repair.unplaced)
    return Plan(
        placements=tuple(
            sorted((*darp.placements, *repair.placements), key=lambda p: str(p.vehicle_id))
        ),
        unplaced=tuple(unplaced),
        solver="darp",
        cost=darp.cost + repair.cost,
    )
