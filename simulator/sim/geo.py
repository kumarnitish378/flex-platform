"""Pure geographic helpers for the simulator.

Deliberately a copy of the backend's `app/domain/geo.py` rather than an import: the
simulator is a black-box client and must not import backend internals
(`coding-standards.md` §4). Keeping the maths identical is what makes simulated and real
ETAs comparable.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_KM = 6371.0088


@dataclass(frozen=True, slots=True)
class LatLng:
    lat: float
    lng: float

    def __post_init__(self) -> None:
        if not -90.0 <= self.lat <= 90.0:
            raise ValueError(f"lat out of range: {self.lat}")
        if not -180.0 <= self.lng <= 180.0:
            raise ValueError(f"lng out of range: {self.lng}")


def haversine_km(origin: LatLng, destination: LatLng) -> float:
    lat1, lng1 = radians(origin.lat), radians(origin.lng)
    lat2, lng2 = radians(destination.lat), radians(destination.lng)
    inner = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lng2 - lng1) / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(inner))


def interpolate(origin: LatLng, destination: LatLng, fraction: float) -> LatLng:
    """Point a given fraction along the straight line. Used for vehicle movement."""
    clamped = min(1.0, max(0.0, fraction))
    return LatLng(
        lat=origin.lat + (destination.lat - origin.lat) * clamped,
        lng=origin.lng + (destination.lng - origin.lng) * clamped,
    )
