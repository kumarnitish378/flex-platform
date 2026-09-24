"""OSRM client. Works against any OSRM URL — the public demo server or a self-hosted one.

Guard rails for the public server (ADR-0010):
  - every request carries the identifying `User-Agent` from settings (rule 4);
  - every request must first win a token from the shared rate limiter (rule 3);
  - no request is ever retried in a loop against a public host.

When a token is refused, or OSRM errors or times out, this provider does not raise: it
hands the question to the `approx` fallback and marks the answer approximate.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.logging import get_logger
from app.domain.geo import LatLng
from app.modules.routing.rate_limit import RateLimiter
from app.modules.routing.types import RouteResult, RoutingProvider, Source, TableResult

logger = get_logger(__name__)

SERVICE = "osrm"


class OsrmRoutingProvider:
    """Talks to OSRM; degrades to `fallback` rather than failing."""

    name = "osrm"

    def __init__(
        self,
        base_url: str,
        *,
        fallback: RoutingProvider,
        limiter: RateLimiter,
        user_agent: str,
        timeout_seconds: float = 5.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._fallback = fallback
        self._limiter = limiter
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=timeout_seconds,
            headers={"User-Agent": user_agent},
            follow_redirects=True,
        )

    async def route(self, origin: LatLng, destination: LatLng) -> RouteResult:
        coords = f"{_coord(origin)};{_coord(destination)}"
        payload = await self._get(
            f"/route/v1/driving/{coords}",
            params={"overview": "full", "geometries": "geojson", "alternatives": "false"},
        )
        if payload is None:
            return await self._fallback.route(origin, destination)

        try:
            leg = payload["routes"][0]
            geometry = tuple(
                LatLng(lat=point[1], lng=point[0])
                for point in leg.get("geometry", {}).get("coordinates", [])
            )
            return RouteResult(
                duration_seconds=float(leg["duration"]),
                distance_meters=float(leg["distance"]),
                source=Source.osrm,
                approximate=False,
                geometry=geometry,
            )
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            logger.warning("osrm_bad_route_payload", error=type(exc).__name__)
            return await self._fallback.route(origin, destination)

    async def table(self, origins: list[LatLng], destinations: list[LatLng]) -> TableResult:
        points = [*origins, *destinations]
        coords = ";".join(_coord(point) for point in points)
        sources = ";".join(str(i) for i in range(len(origins)))
        targets = ";".join(str(i) for i in range(len(origins), len(points)))

        payload = await self._get(
            f"/table/v1/driving/{coords}",
            params={
                "sources": sources,
                "destinations": targets,
                "annotations": "duration,distance",
            },
        )
        if payload is None:
            return await self._fallback.table(origins, destinations)

        try:
            durations = tuple(tuple(float(v) for v in row) for row in payload["durations"])
            raw_distances = payload.get("distances")
            distances = (
                tuple(tuple(float(v) for v in row) for row in raw_distances)
                if raw_distances is not None
                else tuple(tuple(0.0 for _ in destinations) for _ in origins)
            )
            return TableResult(
                durations=durations,
                distances=distances,
                source=Source.osrm,
                approximate=False,
            )
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning("osrm_bad_table_payload", error=type(exc).__name__)
            return await self._fallback.table(origins, destinations)

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def _get(self, path: str, params: dict[str, str]) -> dict[str, Any] | None:
        """One request, or None when the answer must come from the fallback."""
        if not await self._limiter.try_acquire(SERVICE):
            logger.info("osrm_rate_limited", path=path)
            return None
        try:
            response = await self._client.get(f"{self._base_url}{path}", params=params)
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("osrm_request_failed", path=path, error=type(exc).__name__)
            return None

        if payload.get("code") != "Ok":
            logger.warning("osrm_error_code", path=path, code=payload.get("code"))
            return None
        return payload


def _coord(point: LatLng) -> str:
    """OSRM takes lng,lat — the opposite order to everything else in this codebase."""
    return f"{point.lng:.6f},{point.lat:.6f}"
