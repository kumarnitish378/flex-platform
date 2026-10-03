"""Run output (`simulator-spec.md` §10).

Every run writes `runs/<timestamp>_<scenario>/` containing `metrics.json`, CSVs and a
`summary.md`. The folder is self-contained so a run can be archived, diffed or attached to
a CI artifact, and `sim compare` reads only `metrics.json`.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from sim.metrics import RunMetrics
from sim.pings import Ping

RUNS_DIR = Path("runs")


@dataclass
class RunPaths:
    root: Path

    @property
    def metrics(self) -> Path:
        return self.root / "metrics.json"

    @property
    def pings(self) -> Path:
        return self.root / "pings.csv"

    @property
    def requests(self) -> Path:
        return self.root / "requests.csv"

    @property
    def trips(self) -> Path:
        return self.root / "trips.csv"

    @property
    def summary(self) -> Path:
        return self.root / "summary.md"

    @property
    def events(self) -> Path:
        return self.root / "events.log"


def run_directory(
    scenario: str,
    started_at: datetime,
    base: Path | str = RUNS_DIR,
    run_id: str | None = None,
) -> RunPaths:
    """`runs/20261005T003000Z_smoke_tiny__sim-1a2b3c/`. Sorts chronologically by name.

    The simulated start time alone is not unique: a scenario always starts at the same
    simulated instant, so every run of it overwrote the same directory. A run that failed
    before writing then left the *previous* run's metrics sitting there looking like a
    result - which is exactly how a stale offline run was mistaken for a live one, and
    what CI would have uploaded as the nightly artifact.
    """
    stamp = started_at.strftime("%Y%m%dT%H%M%SZ")
    suffix = f"__{run_id}" if run_id else ""
    return RunPaths(Path(base) / f"{stamp}_{scenario}{suffix}")


class Recorder:
    """Writes one run's artefacts."""

    def __init__(self, paths: RunPaths) -> None:
        self.paths = paths
        self.paths.root.mkdir(parents=True, exist_ok=True)

    def write_metrics(self, metrics: RunMetrics) -> Path:
        self.paths.metrics.write_text(
            json.dumps(metrics.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return self.paths.metrics

    def write_pings(self, pings: list[Ping]) -> Path:
        with self.paths.pings.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["vehicle_id", "ts", "lat", "lng", "spd", "hdg", "acc", "bat", "src"])
            for ping in pings:
                writer.writerow(
                    [
                        ping.vehicle_id,
                        ping.ts.isoformat().replace("+00:00", "Z"),
                        f"{ping.lat:.6f}",
                        f"{ping.lng:.6f}",
                        "" if ping.spd is None else f"{ping.spd:.2f}",
                        "" if ping.hdg is None else f"{ping.hdg:.1f}",
                        "" if ping.acc is None else f"{ping.acc:.1f}",
                        "" if ping.bat is None else ping.bat,
                        ping.src,
                    ]
                )
        return self.paths.pings

    def write_empty_tables(self) -> None:
        """Headers for the tables M05 will fill.

        Written now so a run folder always has the same shape and downstream tooling does
        not have to special-case an early run.
        """
        for path, header in (
            (
                self.paths.requests,
                ["request_id", "employee_id", "direction", "created_at", "status", "wait_minutes"],
            ),
            (
                self.paths.trips,
                ["trip_id", "vehicle_id", "started_at", "ended_at", "riders", "distance_km"],
            ),
        ):
            if not path.exists():
                with path.open("w", newline="", encoding="utf-8") as handle:
                    csv.writer(handle).writerow(header)

    def write_events(self, events: list[str]) -> Path:
        self.paths.events.write_text("\n".join(events) + ("\n" if events else ""), encoding="utf-8")
        return self.paths.events

    def write_summary(self, metrics: RunMetrics) -> Path:
        fleet = metrics.fleet
        lines = [
            f"# {metrics.scenario}",
            "",
            f"- seed: `{metrics.seed}`",
            f"- routing: `{metrics.routing}`",
            f"- window: {metrics.started_at} .. {metrics.ended_at} "
            f"({metrics.simulated_hours:.1f} simulated hours)",
            "",
            "## Fleet",
            "",
            "| Metric | Value |",
            "|---|---|",
            f"| Vehicles seen | {fleet.vehicles_seen} |",
            f"| GPS pings | {fleet.pings} |",
            f"| Distance (km) | {fleet.distance_km_total:.1f} |",
            f"| Median speed (km/h) | {_show(fleet.speed_kmh_median)} |",
            f"| p90 speed (km/h) | {_show(fleet.speed_kmh_p90)} |",
            f"| Largest ping gap (s) | {_show(fleet.ping_gap_seconds_max)} |",
            "",
            "## Integrity (must be zero)",
            "",
            "| Metric | Value |",
            "|---|---|",
            f"| Invalid transitions | {metrics.integrity.invalid_transitions} |",
            f"| Hard-rule violations | {metrics.integrity.hard_rule_violations} |",
            f"| API 5xx | {metrics.integrity.api_5xx} |",
            "",
            *_demand_lines(metrics),
            *_dispatch_lines(metrics),
        ]
        self.paths.summary.write_text("\n".join(lines), encoding="utf-8")
        return self.paths.summary

    def write_all(self, metrics: RunMetrics, pings: list[Ping], events: list[str]) -> RunPaths:
        self.write_metrics(metrics)
        self.write_pings(pings)
        self.write_empty_tables()
        self.write_events(events)
        self.write_summary(metrics)
        return self.paths


# --- comparison --------------------------------------------------------------


def load_metrics(run: Path | str) -> dict[str, Any]:
    """Read `metrics.json` from a run directory (or the file itself)."""
    path = Path(run)
    if path.is_dir():
        path = path / "metrics.json"
    if not path.exists():
        raise FileNotFoundError(f"no metrics.json in {run}")
    loaded: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return loaded


def flatten(payload: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """`{"fleet": {"pings": 3}}` -> `{"fleet.pings": 3}`, for a flat delta table."""
    flat: dict[str, Any] = {}
    for key, value in payload.items():
        name = f"{prefix}{key}"
        if isinstance(value, dict):
            flat.update(flatten(value, f"{name}."))
        else:
            flat[name] = value
    return flat


def compare_runs(left: Path | str, right: Path | str) -> str:
    """A delta table between two runs (`simulator-spec.md` §10, compare mode)."""
    first = flatten(load_metrics(left))
    second = flatten(load_metrics(right))

    keys = sorted(set(first) | set(second))
    width = max((len(key) for key in keys), default=6)

    rows = [
        f"{'metric'.ljust(width)}  {'A':>14}  {'B':>14}  {'delta':>14}",
        f"{'-' * width}  {'-' * 14}  {'-' * 14}  {'-' * 14}",
    ]
    for key in keys:
        a, b = first.get(key), second.get(key)
        rows.append(f"{key.ljust(width)}  {_cell(a):>14}  {_cell(b):>14}  {_delta(a, b):>14}")
    return "\n".join(rows)


def _cell(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _delta(a: Any, b: Any) -> str:
    if isinstance(a, bool) or isinstance(b, bool):
        return "" if a == b else "changed"
    if isinstance(a, int | float) and isinstance(b, int | float):
        difference = b - a
        return f"{difference:+.2f}" if difference else "0"
    if a == b:
        return ""
    return "changed"


def _show(value: float | None) -> str:
    return "-" if value is None else f"{value:.1f}"


def _count(value: int | None) -> str:
    """A tally, not a measurement. "125 riders gave up" - never "125.0 riders"."""
    return "-" if value is None else f"{int(value)}"


def _demand_lines(metrics: RunMetrics) -> list[str]:
    """What happened to the riders - the half of the summary that matters most.

    This section said "not measured yet: agents arrive with task M05" long after M05
    landed, so every run directory's human-readable artefact understated its own run
    while `metrics.json` beside it held the numbers. `summary.md` is what a person opens.
    """
    demand = metrics.demand
    if demand.requests is None:
        return [
            "## Demand",
            "",
            "Not measured: this run had no platform, so nobody asked for a cab.",
            "",
        ]

    served = demand.completed or 0
    asked = demand.requests or 0
    lines = [
        "## Demand",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Riders who asked | {asked} |",
        f"| Carried | {served}" + (f" ({served / asked:.0%})" if asked else "") + " |",
        f"| Gave up | {_count(demand.gave_up)} |",
        f"| No-shows | {_count(demand.no_shows)} |",
        f"| Expired | {_count(demand.expired)} |",
        f"| Wait median (min) | {_show(demand.wait_minutes_median)} |",
        f"| Wait p90 (min) | {_show(demand.wait_minutes_p90)} |",
        "",
    ]

    unresolved = demand.unresolved or 0
    if unresolved:
        # Both halves, because they are different failures: nobody came, versus the ride
        # never ended (ADR-0018).
        lines += [
            "### Unresolved (fails `all_requests_terminal`)",
            "",
            "| Metric | Value |",
            "|---|---|",
            f"| Nobody came | {_count(demand.still_waiting)} |",
            f"| Still riding at the end | {_count(demand.still_riding)} |",
            "",
        ]
    if metrics.drain_minutes:
        drained = (
            "ran out with someone still aboard" if metrics.drain_capped else "every cab emptied"
        )
        lines += [
            f"Rides in progress were given {metrics.drain_minutes:.0f} more minutes "
            f"after the demand window closed; {drained} (ADR-0017).",
            "",
        ]
    return lines


def _dispatch_lines(metrics: RunMetrics) -> list[str]:
    dispatch = metrics.dispatch
    if dispatch.policy is None:
        return []
    lines = [
        "## Dispatch",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Policy | `{dispatch.policy}` |",
        f"| Assignments | {dispatch.assignments} |",
        f"| Refused by the backend | {dispatch.refusals} |",
        f"| No cab to offer | {dispatch.no_candidate} |",
        f"| Assignments breaking a hard rule | {dispatch.violations_accepted} |",
        "",
    ]
    if dispatch.violations_by_rule:
        # ADR-0011 reports rather than enforces in Phase 1, so these are decisions a
        # supervisor made knowingly - and which rule it was is the whole finding.
        lines += [
            "### Which rules were broken",
            "",
            "| Rule | Times |",
            "|---|---|",
            *(
                f"| `{rule}` | {count} |"
                for rule, count in sorted(
                    dispatch.violations_by_rule.items(), key=lambda item: -item[1]
                )
            ),
            "",
        ]
    return lines
