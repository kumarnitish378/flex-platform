"""The Phase 3 batch optimizer: pure, deterministic, and free of the database.

`solve()` takes a `Problem` and returns a `Plan`. See `model.py` for why it is pure and
`allocation-rules.md` §6 for what it is for.
"""

from app.domain.optimizer.model import (
    NightPolicy,
    OptimizerParams,
    Placement,
    Plan,
    Problem,
    Req,
    Seated,
    TripState,
    Unplaced,
    Veh,
)
from app.domain.optimizer.solve import solve

__all__ = [
    "NightPolicy",
    "OptimizerParams",
    "Placement",
    "Plan",
    "Problem",
    "Req",
    "Seated",
    "TripState",
    "Unplaced",
    "Veh",
    "solve",
]
