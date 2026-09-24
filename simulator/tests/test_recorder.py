"""Run output and the compare command (M03).

The pipeline is exercised end to end with real driving agents, so `metrics.json` and
`pings.csv` are checked against movement that actually happened rather than fixtures.
"""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from sim.agents.vehicle import VehicleAgent, VehicleConfig
from sim.cli import main
from sim.engine import Engine
from sim.geo import LatLng
from sim.metrics import RunMetrics, compute_fleet_metrics, percentile
from sim.pings import Ping
from sim.recorder import (
    Recorder,
    compare_runs,
    flatten,
    load_metrics,
    run_directory,
)
from sim.scenario import load_scenario

SCENARIOS = Path(__file__).resolve().parent.parent / "scenarios"
DEPOT = LatLng(28.5355, 77.3910)
OFFICE = LatLng(28.5703, 77.3218)
NOW = datetime(2026, 10, 5, 6, 30, tzinfo=UTC)
NO_NOISE = VehicleConfig(speed_noise_sigma=0.0, gps_noise_metres=0.0)


def run_with_traffic() -> tuple[Engine, RunMetrics]:
    """A run where two cabs actually drive, so the metrics have something to measure."""
    engine = Engine(load_scenario(SCENARIOS / "smoke_tiny.yaml"))
    for index, destination in enumerate((OFFICE, DEPOT), start=1):
        agent = VehicleAgent(engine, f"vehicle-{index}", DEPOT, engine.pings, NO_NOISE)
        agent.go_on_duty()
        engine.spawn(lambda a=agent, d=destination: a.drive_to(d))  # type: ignore[misc]
    summary = engine.run()
    return engine, engine.metrics(summary)


# --- percentiles -------------------------------------------------------------


def test_percentile_of_empty_sample_is_none() -> None:
    assert percentile([], 0.5) is None


def test_percentile_of_one_value() -> None:
    assert percentile([7.0], 0.9) == 7.0


def test_percentile_interpolates() -> None:
    assert percentile([0.0, 10.0], 0.5) == pytest.approx(5.0)
    assert percentile([1.0, 2.0, 3.0, 4.0], 0.5) == pytest.approx(2.5)


def test_percentile_ignores_input_order() -> None:
    assert percentile([5.0, 1.0, 3.0], 0.5) == percentile([1.0, 3.0, 5.0], 0.5)


# --- fleet metrics -----------------------------------------------------------


def test_no_pings_gives_empty_metrics() -> None:
    metrics = compute_fleet_metrics([])
    assert metrics.pings == 0
    assert metrics.vehicles_seen == 0
    assert metrics.speed_kmh_median is None


def test_distance_is_summed_per_vehicle() -> None:
    pings = [
        Ping("v1", NOW, DEPOT.lat, DEPOT.lng, spd=0.0),
        Ping("v1", NOW + timedelta(seconds=5), OFFICE.lat, OFFICE.lng, spd=10.0),
        Ping("v2", NOW, DEPOT.lat, DEPOT.lng, spd=0.0),
    ]
    metrics = compute_fleet_metrics(pings)

    assert metrics.vehicles_seen == 2
    assert metrics.distance_km_by_vehicle["v1"] > 5
    assert metrics.distance_km_by_vehicle["v2"] == 0.0
    assert metrics.distance_km_total == pytest.approx(metrics.distance_km_by_vehicle["v1"])


def test_gps_gaps_over_a_minute_are_counted() -> None:
    """A gap beyond stale_gps_seconds is what makes a vehicle unassignable."""
    pings = [
        Ping("v1", NOW, 28.5, 77.3, spd=1.0),
        Ping("v1", NOW + timedelta(seconds=90), 28.5, 77.3, spd=1.0),
    ]
    metrics = compute_fleet_metrics(pings)
    assert metrics.vehicles_with_gps_gap_over_60s == 1
    assert metrics.ping_gap_seconds_max == 90


def test_pings_are_ordered_before_measuring() -> None:
    """Out-of-order input must not produce a negative gap or a bogus distance."""
    pings = [
        Ping("v1", NOW + timedelta(seconds=10), 28.51, 77.31, spd=5.0),
        Ping("v1", NOW, 28.50, 77.30, spd=5.0),
    ]
    metrics = compute_fleet_metrics(pings)
    assert metrics.ping_gap_seconds_max == 10


def test_speed_is_reported_in_kmh() -> None:
    pings = [Ping("v1", NOW, 28.5, 77.3, spd=10.0), Ping("v1", NOW, 28.5, 77.3, spd=10.0)]
    assert compute_fleet_metrics(pings).speed_kmh_median == pytest.approx(36.0)


def test_demand_metrics_are_null_not_zero() -> None:
    """A zero would read as "nobody gave up"; the truth is "not measured until M05"."""
    _, metrics = run_with_traffic()
    assert metrics.demand.requests is None
    assert metrics.demand.gave_up is None
    assert metrics.integrity.invalid_transitions == 0


# --- run folder --------------------------------------------------------------


def test_run_directory_name_sorts_chronologically() -> None:
    first = run_directory("smoke_tiny", datetime(2026, 10, 5, 0, 30, tzinfo=UTC))
    second = run_directory("smoke_tiny", datetime(2026, 10, 6, 0, 30, tzinfo=UTC))
    assert first.root.name == "20261005T003000Z_smoke_tiny"
    assert first.root.name < second.root.name


def test_write_all_produces_every_artefact(tmp_path: Path) -> None:
    engine, metrics = run_with_traffic()
    paths = Recorder(run_directory("smoke_tiny", datetime.now(UTC), tmp_path)).write_all(
        metrics, engine.pings.pings, ["something happened"]
    )

    for path in (paths.metrics, paths.pings, paths.requests, paths.trips, paths.summary):
        assert path.exists(), f"{path.name} was not written"
    assert paths.events.read_text(encoding="utf-8").strip() == "something happened"


def test_metrics_json_round_trips(tmp_path: Path) -> None:
    engine, metrics = run_with_traffic()
    paths = Recorder(run_directory("smoke_tiny", datetime.now(UTC), tmp_path)).write_all(
        metrics, engine.pings.pings, []
    )

    loaded = json.loads(paths.metrics.read_text(encoding="utf-8"))
    assert loaded["scenario"] == "smoke_tiny"
    assert loaded["seed"] == 42
    assert loaded["routing"] == "approx"
    assert loaded["fleet"]["pings"] == len(engine.pings.pings)
    assert loaded["fleet"]["vehicles_seen"] == 2


def test_pings_csv_has_a_row_per_ping(tmp_path: Path) -> None:
    engine, metrics = run_with_traffic()
    paths = Recorder(run_directory("smoke_tiny", datetime.now(UTC), tmp_path)).write_all(
        metrics, engine.pings.pings, []
    )

    with paths.pings.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == len(engine.pings.pings)
    assert rows[0]["vehicle_id"] == "vehicle-1"
    assert rows[0]["ts"].endswith("Z")
    assert float(rows[0]["lat"]) == pytest.approx(DEPOT.lat, abs=1e-4)


def test_empty_tables_carry_headers(tmp_path: Path) -> None:
    """A run folder always has the same shape, even before M05 fills these in."""
    engine, metrics = run_with_traffic()
    paths = Recorder(run_directory("smoke_tiny", datetime.now(UTC), tmp_path)).write_all(
        metrics, engine.pings.pings, []
    )
    assert paths.requests.read_text(encoding="utf-8").startswith("request_id,")
    assert paths.trips.read_text(encoding="utf-8").startswith("trip_id,")


def test_summary_is_readable_markdown(tmp_path: Path) -> None:
    engine, metrics = run_with_traffic()
    paths = Recorder(run_directory("smoke_tiny", datetime.now(UTC), tmp_path)).write_all(
        metrics, engine.pings.pings, []
    )
    text = paths.summary.read_text(encoding="utf-8")
    assert text.startswith("# smoke_tiny")
    assert "Invalid transitions" in text
    assert "M05" in text, "the summary must say what is not measured yet"


# --- compare -----------------------------------------------------------------


def test_flatten_nests_with_dots() -> None:
    assert flatten({"fleet": {"pings": 3}, "seed": 1}) == {"fleet.pings": 3, "seed": 1}


def test_load_metrics_accepts_a_directory_or_a_file(tmp_path: Path) -> None:
    engine, metrics = run_with_traffic()
    paths = Recorder(run_directory("smoke_tiny", datetime.now(UTC), tmp_path)).write_all(
        metrics, engine.pings.pings, []
    )
    assert load_metrics(paths.root)["seed"] == 42
    assert load_metrics(paths.metrics)["seed"] == 42


def test_load_metrics_reports_a_missing_run(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="no metrics.json"):
        load_metrics(tmp_path)


def test_compare_prints_a_delta_table(tmp_path: Path) -> None:
    """M03 acceptance: compare prints a delta table."""
    engine_a, metrics_a = run_with_traffic()
    paths_a = Recorder(run_directory("run_a", datetime.now(UTC), tmp_path)).write_all(
        metrics_a, engine_a.pings.pings, []
    )

    # A second run that drives only one cab, so the deltas are real.
    engine_b = Engine(load_scenario(SCENARIOS / "smoke_tiny.yaml"))
    agent = VehicleAgent(engine_b, "vehicle-1", DEPOT, engine_b.pings, NO_NOISE)
    agent.go_on_duty()
    engine_b.spawn(lambda: agent.drive_to(OFFICE))
    metrics_b = engine_b.metrics(engine_b.run())
    paths_b = Recorder(run_directory("run_b", datetime.now(UTC), tmp_path)).write_all(
        metrics_b, engine_b.pings.pings, []
    )

    table = compare_runs(paths_a.root, paths_b.root)

    assert "metric" in table and "delta" in table
    assert "fleet.vehicles_seen" in table
    vehicles_row = next(line for line in table.splitlines() if "fleet.vehicles_seen" in line)
    assert vehicles_row.split()[-1] == "-1.00"


def test_compare_marks_unchanged_values() -> None:
    from sim.recorder import _delta

    assert _delta(5, 5) == "0"
    assert _delta("a", "a") == ""
    assert _delta("a", "b") == "changed"
    assert _delta(None, 3) == "changed"
    assert _delta(True, False) == "changed"


# --- cli ---------------------------------------------------------------------


def test_cli_run_writes_a_folder(tmp_path: Path) -> None:
    assert main(["run", str(SCENARIOS / "smoke_tiny.yaml"), "--runs-dir", str(tmp_path)]) == 0
    folders = list(tmp_path.iterdir())
    assert len(folders) == 1
    assert (folders[0] / "metrics.json").exists()


def test_cli_no_output_writes_nothing(tmp_path: Path) -> None:
    assert (
        main(
            ["run", str(SCENARIOS / "smoke_tiny.yaml"), "--runs-dir", str(tmp_path), "--no-output"]
        )
        == 0
    )
    assert list(tmp_path.iterdir()) == []


def test_cli_compare_two_runs(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    main(["run", str(SCENARIOS / "smoke_tiny.yaml"), "--runs-dir", str(tmp_path / "a")])
    main(["run", str(SCENARIOS / "smoke_tiny.yaml"), "--runs-dir", str(tmp_path / "b")])
    capsys.readouterr()

    first = next((tmp_path / "a").iterdir())
    second = next((tmp_path / "b").iterdir())
    assert main(["compare", str(first), str(second)]) == 0

    output = capsys.readouterr().out
    assert "fleet.pings" in output
    assert "delta" in output


def test_cli_compare_reports_a_missing_run(tmp_path: Path) -> None:
    assert main(["compare", str(tmp_path), str(tmp_path)]) == 1


def test_cli_suite_writes_run_folders(tmp_path: Path) -> None:
    assert main(["suite", "quick", "--runs-dir", str(tmp_path)]) == 0
    assert list(tmp_path.iterdir())
