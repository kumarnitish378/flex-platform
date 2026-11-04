"""Policy comparison (M13): the same scenario under each mode, differing in nothing else."""

from __future__ import annotations

from pathlib import Path

import pytest

from sim.metrics import OptimizerMetrics, RunMetrics
from sim.policies import (
    STAFFING,
    VARIED,
    comparison_table,
    differences,
    policy_variants,
)
from sim.pooling import PoolingMetrics
from sim.scenario import OperatorMode, SupervisorPolicy, load_scenario

SCENARIOS = Path(__file__).resolve().parent.parent / "scenarios"
EVERY_SCENARIO = sorted(SCENARIOS.glob("*.yaml"))


def run(**sections: object) -> RunMetrics:
    result = RunMetrics(
        scenario="s", seed=1, routing="approx", started_at="a", ended_at="b", simulated_hours=1
    )
    for name, value in sections.items():
        setattr(result, name, value)
    return result


@pytest.mark.parametrize("path", EVERY_SCENARIO, ids=lambda p: p.stem)
def test_the_variants_differ_only_in_the_mode_and_who_staffs_it(path: Path) -> None:
    """The acceptance criterion, as a diff of the whole scenario rather than an assumption.

    Run against every scenario in the suite: a field added to `Scenario` tomorrow that a
    variant accidentally changes would fail here, not in a comparison nobody can explain.
    """
    base = load_scenario(path)
    variants = policy_variants(base)

    assert set(variants) == set(STAFFING)
    for mode, variant in variants.items():
        assert differences(base, variant) <= VARIED, (
            f"{mode} changed {differences(base, variant) - VARIED}"
        )
        assert [entry.mode for entry in variant.modes] == [mode]
        assert variant.supervisor.policy is STAFFING[mode]
        # The seed above all: a comparison with different seeds compares two draws.
        assert variant.seed == base.seed


def test_the_variants_do_not_share_state_with_the_original() -> None:
    base = load_scenario(SCENARIOS / "pooling_efficiency.yaml")
    variants = policy_variants(base)

    variants[OperatorMode.manual].fleet[0].count = 999
    variants[OperatorMode.manual].operator.config_overrides["x"] = 1

    assert base.fleet[0].count != 999 and "x" not in base.operator.config_overrides
    assert variants[OperatorMode.full_auto].fleet[0].count != 999


def test_each_mode_is_staffed_the_way_a_real_operator_would_staff_it() -> None:
    assert STAFFING[OperatorMode.manual] is SupervisorPolicy.manual_nearest
    assert STAFFING[OperatorMode.semi_auto] is SupervisorPolicy.approve_all
    assert STAFFING[OperatorMode.full_auto] is SupervisorPolicy.monitor


def test_a_subset_of_modes_can_be_compared() -> None:
    base = load_scenario(SCENARIOS / "pooling_efficiency.yaml")

    variants = policy_variants(base, (OperatorMode.manual, OperatorMode.full_auto))

    assert list(variants) == [OperatorMode.manual, OperatorMode.full_auto]


# --- the table ---------------------------------------------------------------------------------


def manual() -> RunMetrics:
    return run(pooling=PoolingMetrics(trips_driven=20, vehicles_used=14, cab_km_per_trip=20.0))


def full() -> RunMetrics:
    return run(
        pooling=PoolingMetrics(trips_driven=14, vehicles_used=9, cab_km_per_trip=15.0),
        optimizer=OptimizerMetrics(applied=30),
    )


def test_the_table_shows_each_mode_and_the_change_against_the_baseline() -> None:
    table = comparison_table(
        {OperatorMode.manual: manual(), OperatorMode.full_auto: full()}, OperatorMode.manual
    )

    assert "| Metric | manual | full_auto |" in table
    assert "Vehicles used | 14 | 9 (-36% better)" in table
    assert "Cab-km per trip | 20.00 | 15.00 (-25% better)" in table


def test_a_number_that_got_worse_says_so() -> None:
    worse = run(pooling=PoolingMetrics(trips_driven=20, vehicles_used=16, cab_km_per_trip=20.0))

    table = comparison_table(
        {OperatorMode.manual: manual(), OperatorMode.full_auto: worse}, OperatorMode.manual
    )

    assert "16 (+14% worse)" in table


def test_higher_is_better_for_riders_per_trip_and_the_arrow_knows() -> None:
    low = run(pooling=PoolingMetrics(riders_per_trip=1.0))
    high = run(pooling=PoolingMetrics(riders_per_trip=1.8))

    table = comparison_table(
        {OperatorMode.manual: low, OperatorMode.full_auto: high}, OperatorMode.manual
    )

    assert "1.80 (+80% better)" in table


def test_not_measured_is_a_dash_never_a_zero() -> None:
    table = comparison_table(
        {OperatorMode.manual: run(), OperatorMode.full_auto: full()}, OperatorMode.manual
    )

    assert "Cab-km per trip | - | 15.00" in table
    assert "Median wait (min) | - | -" in table


def test_an_unchanged_number_is_marked_equal() -> None:
    table = comparison_table(
        {OperatorMode.manual: manual(), OperatorMode.full_auto: manual()}, OperatorMode.manual
    )

    assert "14 (=)" in table
