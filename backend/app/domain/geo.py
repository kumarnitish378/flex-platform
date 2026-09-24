"""Pure geographic helpers. No I/O, no clock, no configuration.

Used by the `approx` routing provider and, later, by the cost function and the
simulator's analysis tools.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_KM = 6371.0088


@dataclass(frozen=True, slots=True)
class LatLng:
    """WGS84 coordinate. Matches the api-spec `LatLng` schema."""

    lat: float
    lng: float

    def __post_init__(self) -> None:
        if not -90.0 <= self.lat <= 90.0:
            raise ValueError(f"lat out of range: {self.lat}")
        if not -180.0 <= self.lng <= 180.0:
            raise ValueError(f"lng out of range: {self.lng}")

    def rounded(self, decimals: int) -> tuple[float, float]:
        """Coordinate rounded for cache keys. 4 decimals is roughly 11 m."""
        return (round(self.lat, decimals), round(self.lng, decimals))


def haversine_km(origin: LatLng, destination: LatLng) -> float:
    """Great-circle distance in kilometres."""
    lat1, lng1 = radians(origin.lat), radians(origin.lng)
    lat2, lng2 = radians(destination.lat), radians(destination.lng)
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    inner = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(inner))
