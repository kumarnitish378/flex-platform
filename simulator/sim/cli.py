"""Simulator command line.

python -m sim validate scenarios/smoke_tiny.yaml
python -m sim run      scenarios/smoke_tiny.yaml
python -m sim suite    quick
python -m sim compare  runs/<run-a> runs/<run-b>
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from sim.engine import Engine, connect_fleet, spawn_fleet
from sim.mqtt import MqttUnavailableError
from sim.platform import PlatformClient, PlatformError
from sim.recorder import Recorder, compare_runs, run_directory
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
    run.add_argument("--runs-dir", default="runs", help="where to write the run folder")
    run.add_argument("--no-output", action="store_true", help="run without writing files")
    run.add_argument(
        "--platform",
        default=None,
        metavar="URL",
        help="drive a real backend (M04): seed it, share its clock, publish GPS to MQTT",
    )

    suite = subparsers.add_parser("suite", help="run a named suite")
    suite.add_argument("name", choices=["quick", "full"])
    suite.add_argument("--runs-dir", default="runs")

    compare = subparsers.add_parser("compare", help="delta table between two runs")
    compare.add_argument("run_a")
    compare.add_argument("run_b")

    args = parser.parse_args(argv)

    if args.command == "validate":
        return _validate(args.scenario)
    if args.command == "run":
        return _run(args.scenario, args.runs_dir, args.no_output, args.platform)
    if args.command == "compare":
        return _compare(args.run_a, args.run_b)
    return _suite(args.name, args.runs_dir)


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


def _run(
    path: str,
    runs_dir: str = "runs",
    no_output: bool = False,
    platform_url: str | None = None,
) -> int:
    try:
        scenario = load_scenario(path)
    except ScenarioError as exc:
        print(f"INVALID  {exc}", file=sys.stderr)
        return 1
    return _run_scenario(scenario, runs_dir, no_output, platform_url)


def _run_scenario(
    scenario: Scenario,
    runs_dir: str = "runs",
    no_output: bool = False,
    platform_url: str | None = None,
) -> int:
    platform = None
    if platform_url:
        platform = PlatformClient(platform_url)
        if not platform.health():
            print(f"OFFLINE  no backend at {platform_url}", file=sys.stderr)
            return 3

    try:
        engine = Engine(scenario, osrm_url=os.environ.get("OSRM_URL"), platform=platform)
    except PublicServerRefusedError as exc:
        print(f"REFUSED  {exc}", file=sys.stderr)
        return 2

    if platform is not None:
        try:
            world = connect_fleet(engine, platform)
        except (PlatformError, MqttUnavailableError) as exc:
            print(f"PLATFORM {exc}", file=sys.stderr)
            platform.close()
            return 3
        print(
            f"platform seeded operator={world.operator_id} "
            f"vehicles={len(world.vehicle_ids)} clock={scenario.start.isoformat()}"
        )
        spawn_fleet(engine, [str(value) for value in world.vehicle_ids])
    else:
        spawn_fleet(engine)

    summary = engine.run()
    metrics = engine.metrics(summary)
    print(
        f"ran      {summary.scenario} seed={summary.seed} routing={summary.routing} "
        f"{summary.simulated_seconds / 3600:.1f}h "
        f"vehicles={summary.vehicles} employees={summary.employees} "
        f"pings={metrics.fleet.pings}"
    )

    if engine.mqtt is not None:
        # Anything the last sync did not cover still belongs on the broker.
        engine.mqtt.release_all()
        engine.mqtt.flush()
        print(f"mqtt     published={len(engine.mqtt.published)} unpublished={engine.mqtt.failed}")
        engine.mqtt.close()
    if platform is not None:
        platform.close()

    if not no_output:
        paths = run_directory(scenario.name, summary.started_at, runs_dir)
        Recorder(paths).write_all(metrics, engine.pings.pings, summary.events)
        print(f"output   {paths.root}")

    # Assertions are evaluated once agents produce requests and trips (M05/M07).
    return 0


def _compare(left: str, right: str) -> int:
    try:
        print(compare_runs(left, right))
    except FileNotFoundError as exc:
        print(f"MISSING  {exc}", file=sys.stderr)
        return 1
    return 0


def _suite(name: str, runs_dir: str = "runs") -> int:
    names = QUICK_SUITE if name == "quick" else FULL_SUITE
    failures = 0
    for scenario_name in names:
        path = SCENARIO_DIR / f"{scenario_name}.yaml"
        print(f"--- {scenario_name} ---")
        failures += 1 if _run(str(path), runs_dir) != 0 else 0
    if failures:
        print(f"{failures} scenario(s) failed", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
