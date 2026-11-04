"""Pooling metrics (M11): computed from what the drivers drove, not from what was planned."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from sim.agents.driver import RideLog, TripLog
from sim.geo import LatLng
from sim.metrics import RunMetrics
from sim.pooling import PoolingMetrics, pooling_metrics
from sim.recorder import Recorder, run_directory

T0 = datetime(2026, 10, 5, 4, 0, tzinfo=UTC)
HOME = LatLng(28.50, 77.30)
OFFICE = LatLng(28.57, 77.32)


def direct(origin: LatLng, destination: LatLng, at: datetime) -> float:
    """A flat 20 minutes for any ride, so every detour is the ride minus 20."""
    del origin, destination, at
    return 20.0


def ride(rid: str, minutes_in: float, minutes_out: float) -> RideLog:
    return RideLog(
        request_id=rid,
        picked_up_at=T0 + timedelta(minutes=minutes_in),
        picked_up_at_place=HOME,
        dropped_at=T0 + timedelta(minutes=minutes_out),
        dropped_at_place=OFFICE,
    )


def trip(n: int, vehicle: str, km: float, rides: list[RideLog], *, ended: bool = True) -> TripLog:
    log = TripLog(
        trip_id=f"trip-{n}",
        vehicle_id=vehicle,
        started_at=T0,
        odometer_start_km=100.0,
        ended_at=T0 + timedelta(hours=1) if ended else None,
        odometer_end_km=100.0 + km if ended else None,
        completed=ended,
    )
    log.rides = {r.request_id: r for r in rides}
    return log


def test_no_trips_is_not_measured_rather_than_zero() -> None:
    assert pooling_metrics([], direct) == PoolingMetrics()
    assert pooling_metrics([], direct).cab_km_per_trip is None


def test_the_headline_numbers() -> None:
    logs = [
        trip(1, "cab-1", 30.0, [ride("a", 5, 30), ride("b", 8, 32)]),
        trip(2, "cab-2", 10.0, [ride("c", 3, 25)]),
        trip(3, "cab-1", 20.0, [ride("d", 4, 24)]),
    ]

    result = pooling_metrics(logs, direct)

    assert result.trips_driven == 3
    assert result.vehicles_used == 2, "cab-1 drove two trips"
    assert result.riders_carried == 4
    assert result.riders_per_trip == pytest.approx(1.33, abs=0.01)
    assert result.pooled_trips == 1 and result.pooling_rate == pytest.approx(0.333, abs=0.001)
    assert result.cab_km_total == 60.0
    assert result.cab_km_per_trip == 20.0
    assert result.cab_km_per_rider == 15.0


def test_a_trip_that_carried_nobody_does_no_pooling_work() -> None:
    """A cab that drove out to a no-show must not drag cab-km per trip up for a policy."""
    logs = [trip(1, "cab-1", 10.0, [ride("a", 5, 25)]), trip(2, "cab-2", 40.0, [])]

    result = pooling_metrics(logs, direct)

    assert result.trips_driven == 1 and result.cab_km_total == 10.0 and result.vehicles_used == 1


def test_a_rider_who_was_listed_but_never_boarded_is_not_carried() -> None:
    never = RideLog(request_id="x")  # a stop that was never completed
    result = pooling_metrics([trip(1, "cab-1", 12.0, [ride("a", 5, 25), never])], direct)

    assert result.riders_carried == 1 and result.pooled_trips == 0


def test_detour_is_the_ride_beyond_a_direct_one() -> None:
    logs = [trip(1, "cab-1", 30.0, [ride("a", 0, 20), ride("b", 0, 30), ride("c", 0, 38)])]

    result = pooling_metrics(logs, direct)

    assert result.rides_measured == 3
    assert result.detour_minutes_median == 10.0
    assert result.detour_minutes_mean == pytest.approx(9.33, abs=0.01)
    assert result.detour_minutes_p90 == pytest.approx(16.4, abs=0.01)


def test_a_ride_shorter_than_direct_is_zero_detour_not_negative() -> None:
    assert pooling_metrics([trip(1, "c", 5.0, [ride("a", 0, 15)])], direct).detour_minutes_mean == 0


def test_rides_over_the_limit_are_counted() -> None:
    """min(20 x 1.5, 20 + 15) = 30 minutes."""
    logs = [trip(1, "cab-1", 30.0, [ride("a", 0, 30), ride("b", 0, 31)])]

    assert pooling_metrics(logs, direct).detour_over_limit == 1


def test_the_limits_are_the_scenarios_not_constants() -> None:
    logs = [trip(1, "cab-1", 30.0, [ride("a", 0, 26)])]

    assert pooling_metrics(logs, direct).detour_over_limit == 0
    assert pooling_metrics(logs, direct, max_detour_factor=1.2).detour_over_limit == 1


def test_a_trip_with_no_end_reading_contributes_no_distance_rather_than_a_guess() -> None:
    result = pooling_metrics([trip(1, "cab-1", 99.0, [ride("a", 0, 20)], ended=False)], direct)

    assert result.trips_driven == 1 and result.cab_km_total == 0.0


# --- comparable runs ---------------------------------------------------------------------------


def test_the_metrics_are_in_metrics_json_so_two_runs_compare_directly(tmp_path: Any) -> None:
    from sim.recorder import compare_runs, load_metrics

    def run(name: str, per_trip: float) -> Any:
        metrics = RunMetrics(
            scenario="s", seed=1, routing="approx", started_at="a", ended_at="b", simulated_hours=1
        )
        metrics.pooling = PoolingMetrics(trips_driven=10, cab_km_per_trip=per_trip)
        return (
            Recorder(run_directory("s", T0, tmp_path, run_id=name)).write_all(metrics, [], []).root
        )

    manual, pooled = run("manual", 18.0), run("pooled", 11.5)

    assert load_metrics(manual)["pooling"]["cab_km_per_trip"] == 18.0
    table = compare_runs(manual, pooled)
    assert "pooling.cab_km_per_trip" in table and "11.5" in table
