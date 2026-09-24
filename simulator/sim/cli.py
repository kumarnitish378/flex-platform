"""Simulator command line.

python -m sim validate scenarios/smoke_tiny.yaml
python -m sim run      scenarios/smoke_tiny.yaml
python -m sim suite    quick
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from sim.engine import Engine
from sim.routing import PublicServerRefusedError
from sim.scenario import Scenario, ScenarioError, load_scenario

SCENARIO_DIR = Path(__file__).resolve().parent.parent / "scenarios"

# `make sim-quick` in CI: short scenarios only (simulator-spec.md §12).
QUICK_SUITE = ("smoke_tiny",)
FULL_SUITE = ("smoke_tiny",)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sim", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="check a scenario file")
    validate.add_argument("scenario", help="path to a scenario YAML file")

    run = subparsers.add_parser("run", help="run a scenario")
    run.add_argument("scenario", help="path to a scenario YAML file")

    suite = subparsers.add_parser("suite", help="run a named suite")
    suite.add_argument("name", choices=["quick", "full"])

    args = parser.parse_args(argv)

    if args.command == "validate":
        return _validate(args.scenario)
    if args.command == "run":
        return _run(args.scenario)
    return _suite(args.name)


def _validate(path: str) -> int:
    try:
        scenario = load_scenario(path)
    except ScenarioError as exc:
        print(f"INVALID  {exc}", file=sys.stderr)
        return 1

    print(f"OK       {scenario.name} (version {scenario.version}, seed {scenario.seed})")
    print(f"  window   {scenario.start.isoformat()} .. {scenario.end.isoformat()}")
    print(f"  fleet    {scenario.vehicle_count} vehicles in {len(scenario.fleet)} groups")
    print(f"  demand   {scenario.employee_count} employees across {len(scenario.clients)} clients")
    print(f"  routing  {scenario.routing}  (speed factor {scenario.speed_factor})")
    if scenario.events:
        print(f"  events   {len(scenario.events)}")
    return 0


def _run(path: str) -> int:
    try:
        scenario = load_scenario(path)
    except ScenarioError as exc:
        print(f"INVALID  {exc}", file=sys.stderr)
        return 1
    return _run_scenario(scenario)


def _run_scenario(scenario: Scenario) -> int:
    try:
        engine = Engine(scenario, osrm_url=os.environ.get("OSRM_URL"))
    except PublicServerRefusedError as exc:
        print(f"REFUSED  {exc}", file=sys.stderr)
        return 2

    summary = engine.run()
    print(
        f"ran      {summary.scenario} seed={summary.seed} routing={summary.routing} "
        f"{summary.simulated_seconds / 3600:.1f}h "
        f"vehicles={summary.vehicles} employees={summary.employees}"
    )
    # Agents (and therefore real metrics and assertions) arrive with M02/M05.
    return 0


def _suite(name: str) -> int:
    names = QUICK_SUITE if name == "quick" else FULL_SUITE
    failures = 0
    for scenario_name in names:
        path = SCENARIO_DIR / f"{scenario_name}.yaml"
        print(f"--- {scenario_name} ---")
        failures += 1 if _run(str(path)) != 0 else 0
    if failures:
        print(f"{failures} scenario(s) failed", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
