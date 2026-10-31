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
import uuid
from pathlib import Path

from sim.assertions import evaluate
from sim.engine import Engine, connect_fleet, spawn_fleet, spawn_people
from sim.metrics import RunMetrics
from sim.mqtt import MqttUnavailableError
from sim.platform import PlatformClient, PlatformError
from sim.policies import comparison_table, policy_variants
from sim.recorder import Recorder, compare_runs, run_directory
from sim.routing import PublicServerRefusedError
from sim.scenario import OperatorMode, RoutingMode, Scenario, ScenarioError, load_scenario

SCENARIO_DIR = Path(__file__).resolve().parent.parent / "scenarios"

# `make sim-quick` in CI: short scenarios only (simulator-spec.md §12).
#: The PR suite. One hour of simulated time, so it stays cheap enough to run on every
#: push - the S01 comment ("must stay small and fast") is a constraint, not a note.
#: The PR gate. Cheap enough to run on every pull request, and chosen to cover the paths
#: that have actually broken: `smoke_tiny` is the end-to-end loop, and
#: `breakdown_with_riders` is the incident path - an aborted trip, riders re-queued, a
#: stranded rider collected from the roadside - which four separate defects have hidden
#: in (ADR-0012, ADR-0016, ADR-0020, and twice in the driver agent). Two minutes of
#: simulated incident is worth more than any unit test can say about it.
QUICK_SUITE = ("smoke_tiny", "breakdown_with_riders")

#: The nightly suite, cheapest first so a broken build reports in a minute rather than
#: an hour. `normal_weekday` and `rain_day` are 16 simulated hours each and dominate the
#: runtime.
FULL_SUITE = (
    "smoke_tiny",
    "vip_burst",
    "breakdown_with_riders",
    "gps_loss",
    # The two Phase 2 runs (M10). Four simulated hours each, so they sit above the
    # sixteen-hour days and below nothing - a broken failsafe or a broken override
    # reports in a few minutes rather than at the end of the night.
    "supervisor_absent_semi_auto",
    "override_respected",
    # The three Phase 3 runs (M12): the optimizer pooling a morning, the night-safety
    # rule exercised end to end, and the optimizer being killed mid-peak.
    "pooling_efficiency",
    "night_safety",
    "optimizer_down",
    "evening_surge",
    "normal_weekday",
    "rain_day",
)


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
        "--seed",
        type=int,
        default=None,
        help="override the scenario's seed, to check a result is not one lucky draw",
    )
    run.add_argument(
        "--routing",
        choices=[str(mode) for mode in RoutingMode],
        default=None,
        help=(
            "override the scenario's routing provider. Scenarios declare `approx` "
            "because ADR-0010 rule 6 forbids pointing bulk work at a public OSRM; "
            "`osrm` needs OSRM_URL set to a self-hosted instance (task I02b)"
        ),
    )
    run.add_argument(
        "--platform",
        default=None,
        metavar="URL",
        help="drive a real backend (M04): seed it, share its clock, publish GPS to MQTT",
    )

    suite = subparsers.add_parser("suite", help="run a named suite")
    suite.add_argument("name", choices=["quick", "full"])
    suite.add_argument("--runs-dir", default="runs")
    suite.add_argument(
        "--platform",
        dest="platform_url",
        default=None,
        help="run against a live backend so assertions are actually evaluated",
    )
    suite.add_argument(
        "--routing",
        choices=[str(mode) for mode in RoutingMode],
        default=None,
        help="override every scenario's routing provider (see `run --routing`)",
    )

    policies = subparsers.add_parser(
        "policies",
        help="run one scenario under manual, semi_auto and full_auto and compare (M13)",
    )
    policies.add_argument("scenario", help="path to a scenario YAML file")
    policies.add_argument("--runs-dir", default="runs")
    policies.add_argument("--platform", dest="platform_url", required=True, metavar="URL")
    policies.add_argument("--seed", type=int, default=None)
    policies.add_argument(
        "--modes",
        default="manual,semi_auto,full_auto",
        help="comma-separated, in the order to run them; the first is the baseline",
    )

    compare = subparsers.add_parser("compare", help="delta table between two runs")
    compare.add_argument("run_a")
    compare.add_argument("run_b")

    args = parser.parse_args(argv)

    if args.command == "validate":
        return _validate(args.scenario)
    if args.command == "run":
        return _run(
            args.scenario,
            args.runs_dir,
            args.no_output,
            args.platform,
            args.seed,
            args.routing,
        )
    if args.command == "compare":
        return _compare(args.run_a, args.run_b)
    if args.command == "policies":
        return _policies(args.scenario, args.runs_dir, args.platform_url, args.seed, args.modes)
    return _suite(args.name, args.runs_dir, args.platform_url, args.routing)


def _validate(path: str) -> int:
    try:
        scenario = load_scenario(path)
    except ScenarioError as exc:
        print(f"INVALID  {exc}", file=sys.stderr)
        return 1

    print(f"OK       {scenario.name} (version {scenario.version}, seed {scenario.seed})")
    print(f"  window   {scenario.start.isoformat()} .. {scenario.end.isoformat()}")
    print(f"  drain    up to {scenario.drain_minutes_max:.0f} min for rides in progress")
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
    seed: int | None = None,
    routing: str | None = None,
) -> int:
    try:
        scenario = load_scenario(path)
    except ScenarioError as exc:
        print(f"INVALID  {exc}", file=sys.stderr)
        return 1
    if seed is not None:
        # One seed is one draw. A scenario's result is only worth quoting if it holds
        # across a few of them.
        scenario = scenario.model_copy(update={"seed": seed})
    if routing is not None:
        # The provider is a property of the environment a run happens in, not of the
        # scenario: the file says `approx` because that is the only safe default
        # (ADR-0010 rule 6), and a box with a self-hosted OSRM can say otherwise
        # without seven files being edited and later committed by accident.
        scenario = scenario.model_copy(update={"routing": RoutingMode(routing)})
    return _run_scenario(scenario, runs_dir, no_output, platform_url)


def _run_scenario(
    scenario: Scenario,
    runs_dir: str = "runs",
    no_output: bool = False,
    platform_url: str | None = None,
    collect: list[RunMetrics] | None = None,
    check_assertions: bool = True,
) -> int:
    platform = None
    # Identifies this run in the backend's claim and in the output directory's name, so
    # two runs of the same scenario never overwrite one another's artefacts.
    run_id = f"sim-{uuid.uuid4().hex[:8]}"
    if platform_url:
        platform = PlatformClient(platform_url, run_id=run_id)
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
        spawn_people(engine, world)
        print(f"agents   {len(engine.riders)} riders, {len(engine.drivers)} drivers")
    else:
        spawn_fleet(engine)

    summary = engine.run()
    metrics = engine.metrics(summary)
    if collect is not None:
        collect.append(metrics)
    print(
        f"ran      {summary.scenario} seed={summary.seed} routing={summary.routing} "
        f"{summary.simulated_seconds / 3600:.1f}h "
        f"vehicles={summary.vehicles} employees={summary.employees} "
        f"pings={metrics.fleet.pings}"
    )
    if metrics.demand.riders is not None:
        print(
            f"demand   requests={metrics.demand.requests} "
            f"completed={metrics.demand.completed} gave_up={metrics.demand.gave_up} "
            f"expired={metrics.demand.expired} unresolved={metrics.demand.unresolved}"
        )
        print(
            f"dispatch policy={metrics.dispatch.policy} "
            f"assigned={metrics.dispatch.assignments} "
            f"refused={metrics.dispatch.refusals} "
            f"no_cab={metrics.dispatch.no_candidate}"
        )
        print(
            f"driving  trips={metrics.driving.trips_completed}/"
            f"{metrics.driving.trips_started} stops={metrics.driving.stops_done} "
            f"no_shows={metrics.driving.no_shows} errors={metrics.integrity.agent_errors}"
        )

    if engine.mqtt is not None:
        # Anything the last sync did not cover still belongs on the broker.
        engine.mqtt.release_all()
        engine.mqtt.flush()
        if metrics.events.scheduled:
            print(
                f"events   scheduled={metrics.events.scheduled} fired={metrics.events.fired} "
                f"skipped={metrics.events.skipped} errors={metrics.events.errors}"
                + (f" [{', '.join(metrics.events.types)}]" if metrics.events.types else "")
            )
        print(
            f"mqtt     published={len(engine.mqtt.published)} "
            f"unpublished={engine.mqtt.failed} reconnects={engine.mqtt.reconnects}"
        )
        engine.mqtt.close()
    if platform is not None:
        platform.close()

    if not no_output:
        paths = run_directory(scenario.name, summary.started_at, runs_dir, run_id=run_id)
        Recorder(paths).write_all(metrics, engine.pings.pings, summary.events, engine.trip_logs())
        print(f"output   {paths.root}")

    if platform is None:
        # An offline run moves cabs but never creates a request, so a promise about
        # demand cannot be kept *or* broken by it. Saying "not checked" is honest; a
        # green tick would be a lie and a red one would blame the wrong thing.
        # `make sim-quick` runs offline today; M08 gives CI a backend to run against.
        print("assert   not checked (offline run; use --platform to evaluate)")
        return 0

    if not check_assertions:
        # A policy comparison: the assertions describe what *one* mode must achieve,
        # and a manual run is not supposed to meet `optimizer_assignments_min`.
        return 0

    failures = evaluate(scenario.assertions, metrics)
    for failure in failures:
        print(f"ASSERT   {failure}", file=sys.stderr)
    if not failures:
        print("assert   all scenario assertions held")
    if failures:
        # A scenario that broke its own promise is a failed run, and `make sim-quick`
        # must say so rather than exiting 0 with a warning nobody reads.
        return 4
    return 0


def _policies(
    path: str,
    runs_dir: str,
    platform_url: str,
    seed: int | None,
    modes_arg: str,
) -> int:
    """The same scenario and seed under each mode, reported side by side (M13)."""
    try:
        scenario = load_scenario(path)
        modes = tuple(OperatorMode(item.strip()) for item in modes_arg.split(",") if item.strip())
    except (ScenarioError, ValueError) as exc:
        print(f"INVALID  {exc}", file=sys.stderr)
        return 1
    if not modes:
        print("INVALID  no modes to compare", file=sys.stderr)
        return 1
    if seed is not None:
        scenario = scenario.model_copy(update={"seed": seed})

    results: dict[OperatorMode, RunMetrics] = {}
    for mode, variant in policy_variants(scenario, modes).items():
        print(
            f"policies {variant.name}: seed={variant.seed} supervisor={variant.supervisor.policy}"
        )
        collected: list[RunMetrics] = []
        code = _run_scenario(
            variant, runs_dir, False, platform_url, collect=collected, check_assertions=False
        )
        if code != 0 or not collected:
            print(f"FAILED   the {mode} run did not complete (exit {code})", file=sys.stderr)
            return code or 1
        results[mode] = collected[0]

    table = comparison_table(results, baseline=modes[0])
    print()
    print(f"# {scenario.name}: seed {scenario.seed}, baseline {modes[0]}")
    print()
    print(table)
    out = Path(runs_dir)
    out.mkdir(parents=True, exist_ok=True)
    target = out / f"policies_{scenario.name}_seed{scenario.seed}.md"
    target.write_text(
        f"# {scenario.name}: seed {scenario.seed}, baseline {modes[0]}\n\n{table}\n",
        encoding="utf-8",
    )
    print(f"\noutput   {target}")
    return 0


def _compare(left: str, right: str) -> int:
    try:
        print(compare_runs(left, right))
    except FileNotFoundError as exc:
        print(f"MISSING  {exc}", file=sys.stderr)
        return 1
    return 0


def _suite(
    name: str,
    runs_dir: str = "runs",
    platform_url: str | None = None,
    routing: str | None = None,
) -> int:
    """Run a named suite, reporting every scenario before returning a verdict.

    Every scenario runs even after one fails: a nightly suite that stopped at the first
    failure would hide the other six, and the artifacts are the point.
    """
    names = QUICK_SUITE if name == "quick" else FULL_SUITE
    if routing is not None:
        # Printed, because it changes every number the suite reports: `approx` assumes
        # a flat speed and straight lines, `osrm` follows the road network (OQ-22).
        print(f"routing  every scenario overridden to {routing}", flush=True)
    if platform_url is None:
        print(
            "note     no --platform: scenarios run offline and their assertions are NOT checked",
            file=sys.stderr,
        )

    failed: list[str] = []
    for scenario_name in names:
        path = SCENARIO_DIR / f"{scenario_name}.yaml"
        # Flushed, because the full suite runs for hours and Python buffers stdout when
        # it is redirected to a file. A nightly job that printed nothing until it
        # finished would be undiagnosable the moment it timed out.
        print(f"--- {scenario_name} ---", flush=True)
        if _run(str(path), runs_dir, platform_url=platform_url, routing=routing) != 0:
            failed.append(scenario_name)

    print(
        f"suite    {name}: {len(names) - len(failed)}/{len(names)} scenarios passed",
        flush=True,
    )
    if failed:
        print(f"failed   {', '.join(failed)}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
