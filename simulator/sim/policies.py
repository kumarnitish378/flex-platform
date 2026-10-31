"""Policy comparison: the same scenario and seed under each control mode (M13).

Phase 3's exit criterion is a comparison - cab-km per trip and vehicles used *reduced
against a baseline*, median wait reduced - so the comparison has to be a first-class
thing, not three runs a person remembers to line up.

**The runs differ only in the mode.** `policy_variants` derives them from one scenario by
changing exactly three fields: the operator's `modes`, the supervisor `policy` that mode
is staffed by (a manual scope needs someone assigning; a semi-auto one needs someone
answering offers; a full-auto one needs only a monitor), and the `name`. Everything else -
seed, fleet, demand, events, config - is untouched, and `test_policies.py` asserts that by
diffing the whole scenario rather than assuming it.

Assertions are carried over unchanged but **not evaluated** in a comparison: they describe
what one mode must achieve, and a manual run is not supposed to meet `optimizer_assignments_min`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sim.metrics import RunMetrics
from sim.scenario import ModeEntry, OperatorMode, Scenario, SupervisorPolicy

#: The supervisor each mode needs. This is part of what "the mode" means to a person:
#: `manual` is the Phase 1 baseline (one supervisor assigning), `semi_auto` is Phase 2's
#: (the same supervisor answering the system's offers), `full_auto` is Phase 3's (a
#: supervisor who only picks up what the platform hands back).
STAFFING: dict[OperatorMode, SupervisorPolicy] = {
    OperatorMode.manual: SupervisorPolicy.manual_nearest,
    OperatorMode.semi_auto: SupervisorPolicy.approve_all,
    OperatorMode.full_auto: SupervisorPolicy.monitor,
}

#: Fields a variant is allowed to change. The test diffs everything else.
VARIED = frozenset({"name", "modes", "supervisor"})


def policy_variants(
    scenario: Scenario, modes: tuple[OperatorMode, ...] = tuple(STAFFING)
) -> dict[OperatorMode, Scenario]:
    """One scenario per mode, identical in everything but the mode and who staffs it."""
    variants: dict[OperatorMode, Scenario] = {}
    for mode in modes:
        variants[mode] = scenario.model_copy(
            update={
                "name": f"{scenario.name}__{mode}",
                "modes": [ModeEntry(mode=mode)],
                "supervisor": scenario.supervisor.model_copy(update={"policy": STAFFING[mode]}),
            },
            deep=True,
        )
    return variants


def differences(first: Scenario, second: Scenario) -> set[str]:
    """Which top-level fields differ between two scenarios (used to prove the claim above)."""
    left, right = first.model_dump(), second.model_dump()
    return {key for key in left if left[key] != right[key]}


# --- the table ----------------------------------------------------------------------------


@dataclass(frozen=True)
class Row:
    label: str
    path: str
    #: Lower is better for these (cab-km, vehicles, waits); it decides the arrow.
    lower_is_better: bool = True
    digits: int = 2


ROWS = (
    Row("Requests", "demand.requests", lower_is_better=False, digits=0),
    Row("Completed", "demand.completed", lower_is_better=False, digits=0),
    Row("Gave up", "demand.gave_up", digits=0),
    Row("Median wait (min)", "demand.wait_minutes_median"),
    Row("p90 wait (min)", "demand.wait_minutes_p90"),
    Row("Trips driven", "pooling.trips_driven", lower_is_better=False, digits=0),
    Row("Vehicles used", "pooling.vehicles_used", digits=0),
    Row("Riders per trip", "pooling.riders_per_trip", lower_is_better=False),
    Row("Pooling rate", "pooling.pooling_rate", lower_is_better=False, digits=3),
    Row("Cab-km per trip", "pooling.cab_km_per_trip"),
    Row("Cab-km per rider", "pooling.cab_km_per_rider"),
    Row("Cab-km total", "pooling.cab_km_total", digits=1),
    Row("Detour median (min)", "pooling.detour_minutes_median"),
    Row("Rides over detour limit", "pooling.detour_over_limit", digits=0),
    Row("Assigned by the optimizer", "optimizer.applied", lower_is_better=False, digits=0),
)


def _lookup(payload: dict[str, Any], path: str) -> Any:
    value: Any = payload
    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def comparison_table(results: dict[OperatorMode, RunMetrics], baseline: OperatorMode) -> str:
    """A markdown table, one column per mode, with the change against `baseline`.

    A number that was not measured prints as `-`, never as 0: "no cab carried anyone" and
    "the cabs drove zero kilometres" are different claims.
    """
    payloads = {mode: metrics.to_dict() for mode, metrics in results.items()}
    modes = list(results)
    header = ["Metric", *[str(mode) for mode in modes]]
    lines = [
        "| " + " | ".join(header) + " |",
        "|" + "|".join("---" for _ in header) + "|",
    ]
    for row in ROWS:
        cells = [row.label]
        base = _lookup(payloads[baseline], row.path) if baseline in payloads else None
        for mode in modes:
            value = _lookup(payloads[mode], row.path)
            cells.append(_cell(value, base, row, is_baseline=mode == baseline))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _cell(value: Any, base: Any, row: Row, *, is_baseline: bool) -> str:
    if value is None:
        return "-"
    text = f"{value:.{row.digits}f}" if isinstance(value, float) else str(value)
    if is_baseline or not isinstance(base, int | float) or not isinstance(value, int | float):
        return text
    if base == 0:
        return text
    change = (value - base) / abs(base) * 100.0
    if abs(change) < 0.5:
        return f"{text} (=)"
    better = (change < 0) == row.lower_is_better
    return f"{text} ({change:+.0f}% {'better' if better else 'worse'})"
