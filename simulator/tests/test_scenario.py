"""Scenario loading and validation.

A scenario is the experiment's definition. Validation is strict on purpose: a misspelled
key must fail loudly, because silently ignoring it destroys reproducibility.
"""

from __future__ import annotations

from datetime import UTC
from pathlib import Path

import pytest

from sim.scenario import RoutingMode, ScenarioError, load_scenario

SCENARIOS = Path(__file__).resolve().parent.parent / "scenarios"

MINIMAL = """
name: t
seed: 1
start: "2026-10-05T00:30:00Z"
duration_hours: 1
fleet:
  - {type: sedan_4, count: 1, depot: [28.5, 77.3]}
drivers:
  shift_start_ist: "06:00"
  shift_end_ist: "22:00"
clients:
  - name: C
    office: {name: O, location: [28.57, 77.32]}
    employees:
      count: 1
      shifts:
        - {start_ist: "09:30", end_ist: "18:30", share: 1.0}
"""


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "scenario.yaml"
    path.write_text(text, encoding="utf-8")
    return path


# --- the shipped scenario ----------------------------------------------------


def test_smoke_tiny_is_valid() -> None:
    """M01 acceptance: `python -m sim validate scenarios/smoke_tiny.yaml` passes."""
    scenario = load_scenario(SCENARIOS / "smoke_tiny.yaml")
    assert scenario.name == "smoke_tiny"
    assert scenario.seed == 42
    assert scenario.vehicle_count == 3
    assert scenario.employee_count == 10
    assert scenario.duration_hours == 1


def test_smoke_tiny_uses_approx_routing() -> None:
    """ADR-0010 rule 6: a simulator run must never call the public OSM servers."""
    assert load_scenario(SCENARIOS / "smoke_tiny.yaml").routing is RoutingMode.approx


def test_every_shipped_scenario_loads() -> None:
    files = sorted(SCENARIOS.glob("*.yaml"))
    assert files, "no scenarios found"
    for path in files:
        load_scenario(path)


# --- derived values ----------------------------------------------------------


def test_start_is_normalised_to_utc(tmp_path: Path) -> None:
    text = MINIMAL.replace('"2026-10-05T00:30:00Z"', '"2026-10-05T06:00:00+05:30"')
    scenario = load_scenario(write(tmp_path, text))
    assert scenario.start.tzinfo == UTC
    assert scenario.start.hour == 0
    assert scenario.start.minute == 30


def test_end_is_start_plus_duration(tmp_path: Path) -> None:
    scenario = load_scenario(write(tmp_path, MINIMAL))
    assert (scenario.end - scenario.start).total_seconds() == 3600


def test_counts_are_summed_across_groups(tmp_path: Path) -> None:
    scenario = load_scenario(SCENARIOS / "smoke_tiny.yaml")
    assert scenario.vehicle_count == sum(group.count for group in scenario.fleet)


def test_defaults_are_applied(tmp_path: Path) -> None:
    scenario = load_scenario(write(tmp_path, MINIMAL))
    assert scenario.routing is RoutingMode.approx
    assert scenario.speed_factor == 60.0
    assert scenario.version == 1
    assert [entry.mode for entry in scenario.modes] == ["manual"]


# --- rejections --------------------------------------------------------------


def test_missing_file() -> None:
    with pytest.raises(ScenarioError, match="not found"):
        load_scenario("does/not/exist.yaml")


def test_empty_file(tmp_path: Path) -> None:
    with pytest.raises(ScenarioError, match="empty"):
        load_scenario(write(tmp_path, ""))


def test_not_a_mapping(tmp_path: Path) -> None:
    with pytest.raises(ScenarioError, match="mapping"):
        load_scenario(write(tmp_path, "- just\n- a list\n"))


def test_invalid_yaml(tmp_path: Path) -> None:
    with pytest.raises(ScenarioError, match="invalid YAML"):
        load_scenario(write(tmp_path, "name: [unclosed\n"))


def test_unknown_key_is_rejected(tmp_path: Path) -> None:
    """A typo must fail, not be ignored - `sped_factor` would silently change nothing."""
    with pytest.raises(ScenarioError, match="sped_factor"):
        load_scenario(write(tmp_path, MINIMAL + "sped_factor: 10\n"))


def test_missing_seed_is_rejected(tmp_path: Path) -> None:
    text = MINIMAL.replace("seed: 1\n", "")
    with pytest.raises(ScenarioError, match="seed"):
        load_scenario(write(tmp_path, text))


def test_naive_start_is_rejected(tmp_path: Path) -> None:
    text = MINIMAL.replace('"2026-10-05T00:30:00Z"', '"2026-10-05T00:30:00"')
    with pytest.raises(ScenarioError, match="timezone"):
        load_scenario(write(tmp_path, text))


def test_empty_fleet_is_rejected(tmp_path: Path) -> None:
    text = MINIMAL.replace(
        "fleet:\n  - {type: sedan_4, count: 1, depot: [28.5, 77.3]}\n", "fleet: []\n"
    )
    with pytest.raises(ScenarioError):
        load_scenario(write(tmp_path, text))


def test_out_of_range_coordinates_are_rejected(tmp_path: Path) -> None:
    text = MINIMAL.replace("[28.5, 77.3]", "[128.5, 77.3]")
    with pytest.raises(ScenarioError):
        load_scenario(write(tmp_path, text))


def test_shift_shares_must_sum_to_one(tmp_path: Path) -> None:
    text = MINIMAL.replace("share: 1.0", "share: 0.5")
    with pytest.raises(ScenarioError, match="sum to 1.0"):
        load_scenario(write(tmp_path, text))


def test_priority_distribution_must_sum_to_one(tmp_path: Path) -> None:
    text = MINIMAL.replace("      count: 1\n", "      count: 1\n      priority_dist: {5: 0.5}\n")
    with pytest.raises(ScenarioError, match="sum to 1.0"):
        load_scenario(write(tmp_path, text))


def test_priority_out_of_range_is_rejected(tmp_path: Path) -> None:
    text = MINIMAL.replace("      count: 1\n", "      count: 1\n      priority_dist: {11: 1.0}\n")
    with pytest.raises(ScenarioError, match="outside 1-10"):
        load_scenario(write(tmp_path, text))


def test_zero_duration_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ScenarioError):
        load_scenario(write(tmp_path, MINIMAL.replace("duration_hours: 1", "duration_hours: 0")))


def test_unknown_routing_mode_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ScenarioError):
        load_scenario(write(tmp_path, MINIMAL + "routing: google\n"))


def test_unknown_supervisor_policy_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ScenarioError):
        load_scenario(write(tmp_path, MINIMAL + "supervisor:\n  policy: psychic\n"))


def test_reaction_delay_must_be_ordered(tmp_path: Path) -> None:
    with pytest.raises(ScenarioError, match="min, max"):
        load_scenario(write(tmp_path, MINIMAL + "supervisor:\n  reaction_delay_s: [120, 20]\n"))
