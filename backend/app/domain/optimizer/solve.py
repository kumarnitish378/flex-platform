"""The solver entry point: pick the best valid plan for a batch (`allocation-rules.md` §6)."""

from __future__ import annotations

from app.domain.optimizer.greedy import solve_greedy
from app.domain.optimizer.model import Plan, Problem


def solve(problem: Problem) -> Plan:
    """Solve one batch. Pure: the same problem always returns the same plan."""
    if not problem.requests:
        return Plan()
    return solve_greedy(problem)
