"""Routing and geocoding contracts (ADR-0010 rule 2).

One interface, several implementations, chosen by configuration. Nothing above this
layer knows whether an answer came from OSRM, from cache, or from the network-free
`approx` estimator — it only reads `approximate` and `source`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

from app.domain.geo import LatLng


class Source(StrEnum):
    """Where an answer actually came from. Recorded on every result for metrics."""

    osrm = "osrm"
    approx = "approx"
    cache = "cache"


@dataclass(frozen=True, slots=True)
class RouteResult:
    duration_seconds: float
    distance_meters: float
    source: Source
    approximate: bool
    geometry: tuple[LatLng, ...] = ()

    @property
    def duration_minutes(self) -> float:
        return self.duration_seconds / 60.0


@dataclass(frozen=True, slots=True)
class TableResult:
    """Duration/distance matrix: `durations[i][j]` is origin i -> destination j."""

    durations: tuple[tuple[float, ...], ...]
    distances: tuple[tuple[float, ...], ...]
    source: Source
    approximate: bool


@runtime_checkable
class RoutingProvider(Protocol):
    """Travel time and distance between points.

    Implementations must never raise for an unreachable upstream: the caller always
    gets an answer, degraded to `approx` and flagged `approximate` if necessary
    (`control-model.md` §6).
    """

    name: str

    async def route(self, origin: LatLng, destination: LatLng) -> RouteResult: ...

    async def table(self, origins: list[LatLng], destinations: list[LatLng]) -> TableResult: ...

    async def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class Place:
    """A geocoding result. Phase 1 never produces one."""

    name: str
    location: LatLng


class GeocodingUnavailableError(Exception):
    """Raised by the `none` provider. Phase 1 has no geocoding by design."""


@runtime_checkable
class GeocodingProvider(Protocol):
    """Address lookup.

    Phase 1 uses `NoGeocodingProvider`: employees and admins set locations with map
    pins plus landmark text, and the public Nominatim is never called (ADR-0010 A1).
    """

    name: str

    async def search(self, query: str, *, limit: int = 5) -> list[Place]: ...

    async def reverse(self, location: LatLng) -> Place | None: ...
