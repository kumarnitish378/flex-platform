"""Run metrics (`simulator-spec.md` §9).

v0 computes what M02 can produce: fleet activity and GPS behaviour. The request, trip,
wait and ETA-error metrics in §9 need employee and driver agents, so they arrive with M05;
they are declared here as `None` rather than as zeros, because a zero would read as "no
riders gave up" when the truth is "nothing measured that yet".
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from sim.geo import LatLng, haversine_km
from sim.pings import Ping


def percentile(values: list[float], fraction: float) -> float | None:
    """Linear-interpolated percentile. `None` for an empty sample."""
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = fraction * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


@dataclass
class FleetMetrics:
    vehicles_seen: int = 0
    pings: int = 0
    distance_km_total: float = 0.0
    distance_km_by_vehicle: dict[str, float] = field(default_factory=dict)
    speed_kmh_median: float | None = None
    speed_kmh_p90: float | None = None
    ping_gap_seconds_max: float | None = None
    vehicles_with_gps_gap_over_60s: int = 0


@dataclass
class DemandMetrics:
    """Placeholders until M05 adds employee and driver agents."""

    requests: int | None = None
    assigned: int | None = None
    cancelled: int | None = None
    gave_up: int | None = None
    no_shows: int | None = None
    expired: int | None = None
    wait_minutes_median: float | None = None
    wait_minutes_p90: float | None = None
    eta_error_minutes_p90: float | None = None


@dataclass
class IntegrityMetrics:
    """Must stay at zero. Any non-zero value fails a scenario (`scenarios.md`)."""

    invalid_transitions: int = 0
    hard_rule_violations: int = 0
    api_5xx: int = 0


@dataclass
class RunMetrics:
    scenario: str
    seed: int
    routing: str
    started_at: str
    ended_at: str
    simulated_hours: float
    fleet: FleetMetrics = field(default_factory=FleetMetrics)
    demand: DemandMetrics = field(default_factory=DemandMetrics)
    integrity: IntegrityMetrics = field(default_factory=IntegrityMetrics)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute_fleet_metrics(pings: list[Ping]) -> FleetMetrics:
    """Derive fleet metrics from the emitted pings."""
    metrics = FleetMetrics(pings=len(pings))
    if not pings:
        return metrics

    by_vehicle: dict[str, list[Ping]] = {}
    for ping in pings:
        by_vehicle.setdefault(ping.vehicle_id, []).append(ping)

    metrics.vehicles_seen = len(by_vehicle)
    speeds: list[float] = []
    gaps: list[float] = []

    for vehicle_id, vehicle_pings in by_vehicle.items():
        ordered = sorted(vehicle_pings, key=lambda p: p.ts)
        distance_km = 0.0
        for first, second in zip(ordered, ordered[1:], strict=False):
            distance_km += haversine_km(
                LatLng(first.lat, first.lng), LatLng(second.lat, second.lng)
            )
            gap = (second.ts - first.ts).total_seconds()
            gaps.append(gap)
            if gap > 60:
                # A gap over stale_gps_seconds is what makes a vehicle "stale" and
                # unassignable (trip-lifecycle.md §4), so it is worth counting.
                metrics.vehicles_with_gps_gap_over_60s += 1
        metrics.distance_km_by_vehicle[vehicle_id] = round(distance_km, 3)
        distance_km_total = metrics.distance_km_total + distance_km
        metrics.distance_km_total = distance_km_total
        speeds.extend((ping.spd or 0.0) * 3.6 for ping in ordered)

    metrics.distance_km_total = round(metrics.distance_km_total, 3)
    metrics.speed_kmh_median = _rounded(percentile(speeds, 0.5))
    metrics.speed_kmh_p90 = _rounded(percentile(speeds, 0.9))
    metrics.ping_gap_seconds_max = max(gaps) if gaps else None
    return metrics


def _rounded(value: float | None, digits: int = 2) -> float | None:
    return None if value is None else round(value, digits)
