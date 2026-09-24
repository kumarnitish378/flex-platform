"""Routing for the simulator.

**The simulator must never call the public OSM servers** (ADR-0010 rule 6): a single run
issues thousands of route requests, which is exactly the bulk use those donated servers
forbid. So the default is `approx`, which needs no network at all, and the OSRM client
refuses point-blank to talk to a public host.

`simulator-spec.md` §4: absolute times under `approx` are optimistic because there is no
road network. Runs compare policies against each other with the same seed and the same
provider; they do not predict wall-clock minutes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, timezone
from typing import Protocol, runtime_checkable
from urllib.parse import urlsplit

import httpx

from sim.geo import LatLng, haversine_km, interpolate

IST = timezone(timedelta(hours=5, minutes=30))

# Donated infrastructure. The simulator is barred from all of it.
PUBLIC_OSM_HOSTS = frozenset(
    {
        "router.project-osrm.org",
        "tile.openstreetmap.org",
        "nominatim.openstreetmap.org",
        "nominatim.osm.org",
    }
)


@dataclass(frozen=True, slots=True)
class Route:
    duration_seconds: float
    distance_meters: float
    geometry: tuple[LatLng, ...]
    approximate: bool

    def position_at(self, elapsed_seconds: float) -> LatLng:
        """Where a vehicle following this route is after `elapsed_seconds`."""
        if self.duration_seconds <= 0 or len(self.geometry) < 2:
            return self.geometry[-1] if self.geometry else LatLng(0.0, 0.0)
        fraction = min(1.0, max(0.0, elapsed_seconds / self.duration_seconds))
        return _point_along(self.geometry, fraction)


@runtime_checkable
class RoutingClient(Protocol):
    name: str

    def route(self, origin: LatLng, destination: LatLng, at: datetime) -> Route: ...


@dataclass(frozen=True, slots=True)
class SpeedWindow:
    start: time
    end: time
    factor: float

    def contains(self, moment: time) -> bool:
        if self.start <= self.end:
            return self.start <= moment < self.end
        return moment >= self.start or moment < self.end


@dataclass(frozen=True, slots=True)
class ApproxConfig:
    """Same shape and defaults as the backend's approx provider (see OQ-22)."""

    base_speed_kmh: float = 24.0
    road_factor: float = 1.4
    windows: tuple[SpeedWindow, ...] = field(
        default_factory=lambda: (
            SpeedWindow(time(8, 0), time(10, 30), 0.6),
            SpeedWindow(time(17, 30), time(20, 30), 0.6),
            SpeedWindow(time(23, 0), time(6, 0), 1.3),
        )
    )

    def speed_kmh_at(self, local: time) -> float:
        for window in self.windows:
            if window.contains(local):
                return self.base_speed_kmh * window.factor
        return self.base_speed_kmh


class ApproxRouting:
    """Straight line x road factor at a time-of-day speed. No network, ever."""

    name = "approx"

    def __init__(self, config: ApproxConfig | None = None, traffic_factor: float = 1.0) -> None:
        self._config = config or ApproxConfig()
        # Event injector (rain, closures) scales this during a run.
        self.traffic_factor = traffic_factor

    def route(self, origin: LatLng, destination: LatLng, at: datetime) -> Route:
        road_km = haversine_km(origin, destination) * self._config.road_factor
        speed = self._config.speed_kmh_at(at.astimezone(IST).time()) * self.traffic_factor
        seconds = (road_km / speed) * 3600.0 if speed > 0 else 0.0
        return Route(
            duration_seconds=seconds,
            distance_meters=road_km * 1000.0,
            geometry=(origin, destination),
            approximate=True,
        )


class PublicServerRefusedError(RuntimeError):
    """Raised when a scenario points the simulator at donated OSM infrastructure."""


class OsrmRouting:
    """Self-hosted OSRM only (task I02b). Refuses public hosts by construction."""

    name = "osrm"

    def __init__(self, base_url: str, timeout_seconds: float = 5.0) -> None:
        host = (urlsplit(base_url).hostname or "").lower()
        if host in PUBLIC_OSM_HOSTS:
            raise PublicServerRefusedError(
                f"The simulator must not call the public OSM server at {host}: a run makes "
                "thousands of requests (ADR-0010 rule 6). Use routing: approx, or point "
                "OSRM_URL at a self-hosted instance."
            )
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(timeout=timeout_seconds)
        self._fallback = ApproxRouting()

    def route(self, origin: LatLng, destination: LatLng, at: datetime) -> Route:
        coords = f"{origin.lng:.6f},{origin.lat:.6f};{destination.lng:.6f},{destination.lat:.6f}"
        try:
            response = self._client.get(
                f"{self._base_url}/route/v1/driving/{coords}",
                params={"overview": "full", "geometries": "geojson"},
            )
            response.raise_for_status()
            payload = response.json()
            leg = payload["routes"][0]
            geometry = tuple(
                LatLng(lat=point[1], lng=point[0]) for point in leg["geometry"]["coordinates"]
            )
            return Route(
                duration_seconds=float(leg["duration"]),
                distance_meters=float(leg["distance"]),
                geometry=geometry or (origin, destination),
                approximate=False,
            )
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
            # A simulation must not stop because a route lookup failed.
            return self._fallback.route(origin, destination, at)

    def close(self) -> None:
        self._client.close()


def build_routing(mode: str, osrm_url: str | None = None) -> RoutingClient:
    """Build the routing client a scenario asks for."""
    if mode == "osrm":
        if not osrm_url:
            raise PublicServerRefusedError(
                "routing: osrm needs OSRM_URL pointing at a self-hosted instance"
            )
        return OsrmRouting(osrm_url)
    return ApproxRouting()


def _point_along(geometry: tuple[LatLng, ...], fraction: float) -> LatLng:
    """Interpolate along a polyline by cumulative distance."""
    legs = list(zip(geometry, geometry[1:], strict=False))
    lengths = [haversine_km(a, b) for a, b in legs]
    total = sum(lengths)
    if total <= 0:
        return geometry[-1]

    target = total * fraction
    travelled = 0.0
    for (start, end), length in zip(legs, lengths, strict=True):
        if travelled + length >= target:
            within = (target - travelled) / length if length > 0 else 0.0
            return interpolate(start, end, within)
        travelled += length
    return geometry[-1]
