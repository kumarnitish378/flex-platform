"""OSRM client: recorded responses only, never a real server (CLAUDE.md, ADR-0010).

Covers the degradation ladder that matters operationally: rate-limited, erroring, slow or
malformed upstream must all produce an answer flagged `approximate`, not an exception.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest

from app.core.clock import FakeClock
from app.domain.geo import LatLng
from app.modules.routing.approx import ApproxRoutingProvider
from app.modules.routing.osrm import OsrmRoutingProvider
from app.modules.routing.rate_limit import UnlimitedRateLimiter
from app.modules.routing.types import Source

NOW = datetime(2026, 9, 24, 6, 30, tzinfo=UTC)
ORIGIN = LatLng(lat=28.5703, lng=77.3218)
DESTINATION = LatLng(lat=28.5123, lng=77.3910)
USER_AGENT = "flex-platform/0.1 (contact: dev@example.com)"

ROUTE_RESPONSE: dict[str, Any] = {
    "code": "Ok",
    "routes": [
        {
            "duration": 1380.4,
            "distance": 9123.7,
            "geometry": {
                "coordinates": [[77.3218, 28.5703], [77.3550, 28.5400], [77.3910, 28.5123]],
                "type": "LineString",
            },
        }
    ],
}

TABLE_RESPONSE: dict[str, Any] = {
    "code": "Ok",
    "durations": [[0.0, 1380.4], [1402.0, 0.0]],
    "distances": [[0.0, 9123.7], [9200.0, 0.0]],
}


Handler = Callable[[httpx.Request], httpx.Response]


def build(
    handler: Handler,
    *,
    limiter: Any = None,
    base_url: str = "https://osrm.internal",
) -> tuple[OsrmRoutingProvider, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def record(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    client = httpx.AsyncClient(
        transport=httpx.MockTransport(record),
        headers={"User-Agent": USER_AGENT},
    )
    provider = OsrmRoutingProvider(
        base_url,
        fallback=ApproxRoutingProvider(FakeClock(NOW)),
        limiter=limiter or UnlimitedRateLimiter(),
        user_agent=USER_AGENT,
        client=client,
    )
    return provider, seen


def ok(payload: dict[str, Any]) -> Handler:
    return lambda request: httpx.Response(200, json=payload)


async def test_route_parses_a_recorded_response() -> None:
    provider, _ = build(ok(ROUTE_RESPONSE))
    result = await provider.route(ORIGIN, DESTINATION)

    assert result.duration_seconds == pytest.approx(1380.4)
    assert result.distance_meters == pytest.approx(9123.7)
    assert result.approximate is False
    assert result.source is Source.osrm
    assert len(result.geometry) == 3
    # GeoJSON is lng,lat; LatLng is lat,lng. Getting this backwards puts cabs in China.
    assert result.geometry[0] == LatLng(lat=28.5703, lng=77.3218)


async def test_request_carries_the_identifying_user_agent() -> None:
    """ADR-0010 rule 4: a generic User-Agent gets blocked by the public server."""
    provider, seen = build(ok(ROUTE_RESPONSE))
    await provider.route(ORIGIN, DESTINATION)
    assert seen[0].headers["User-Agent"] == USER_AGENT


async def test_coordinates_are_sent_as_lng_lat() -> None:
    provider, seen = build(ok(ROUTE_RESPONSE))
    await provider.route(ORIGIN, DESTINATION)
    assert "77.321800,28.570300;77.391000,28.512300" in str(seen[0].url)


async def test_table_parses_a_recorded_response() -> None:
    provider, _ = build(ok(TABLE_RESPONSE))
    result = await provider.table([ORIGIN, DESTINATION], [ORIGIN, DESTINATION])

    assert result.durations[0][1] == pytest.approx(1380.4)
    assert result.distances[1][0] == pytest.approx(9200.0)
    assert result.approximate is False
    assert result.source is Source.osrm


async def test_table_sends_sources_and_destinations() -> None:
    provider, seen = build(ok(TABLE_RESPONSE))
    await provider.table([ORIGIN], [DESTINATION])
    url = str(seen[0].url)
    assert "sources=0" in url
    assert "destinations=1" in url


async def test_rate_limited_request_falls_back_without_calling_osrm() -> None:
    """I02 acceptance: over the limit means approx, not a queue and not an error."""

    class Deny:
        async def try_acquire(self, service: str) -> bool:
            return False

    provider, seen = build(ok(ROUTE_RESPONSE), limiter=Deny())
    result = await provider.route(ORIGIN, DESTINATION)

    assert seen == [], "no HTTP request may be made once the budget is spent"
    assert result.approximate is True
    assert result.source is Source.approx
    assert result.duration_seconds > 0


async def test_server_error_falls_back() -> None:
    provider, _ = build(lambda request: httpx.Response(503, text="unavailable"))
    result = await provider.route(ORIGIN, DESTINATION)
    assert result.approximate is True
    assert result.source is Source.approx


async def test_timeout_falls_back() -> None:
    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("too slow", request=request)

    provider, _ = build(timeout)
    result = await provider.route(ORIGIN, DESTINATION)
    assert result.approximate is True


async def test_connection_error_falls_back() -> None:
    def refused(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no route to host", request=request)

    provider, _ = build(refused)
    result = await provider.table([ORIGIN], [DESTINATION])
    assert result.approximate is True
    assert result.durations[0][0] > 0


async def test_osrm_error_code_falls_back() -> None:
    """OSRM answers 200 with code=NoRoute when it cannot snap a point to a road."""
    provider, _ = build(ok({"code": "NoRoute", "routes": []}))
    result = await provider.route(ORIGIN, DESTINATION)
    assert result.approximate is True


async def test_malformed_payload_falls_back() -> None:
    provider, _ = build(ok({"code": "Ok", "routes": [{"duration": "soon"}]}))
    result = await provider.route(ORIGIN, DESTINATION)
    assert result.approximate is True


async def test_non_json_response_falls_back() -> None:
    provider, _ = build(lambda request: httpx.Response(200, text="<html>proxy error</html>"))
    result = await provider.route(ORIGIN, DESTINATION)
    assert result.approximate is True


async def test_table_without_distances_still_works() -> None:
    provider, _ = build(ok({"code": "Ok", "durations": [[0.0, 90.0]]}))
    result = await provider.table([ORIGIN], [ORIGIN, DESTINATION])
    assert result.durations[0][1] == pytest.approx(90.0)
    assert result.distances[0][1] == 0.0
    assert result.approximate is False
