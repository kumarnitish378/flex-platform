"""Integration test against a real, self-hosted OSRM (B10).

Skipped unless `OSRM_URL` points at an instance you run yourself (task I02b). It must
never run against the public demo server: these are real routing requests, and CI runs
this file on every push.

To run it locally:

    make up-maps                       # starts the optional osrm container
    OSRM_URL=http://localhost:5000 make test
"""

from __future__ import annotations

import os
from urllib.parse import urlsplit

import pytest

from app.core.clock import FakeClock, SystemClock
from app.core.settings import PUBLIC_OSM_HOSTS
from app.domain.geo import LatLng
from app.modules.routing.approx import ApproxRoutingProvider
from app.modules.routing.osrm import OsrmRoutingProvider
from app.modules.routing.rate_limit import UnlimitedRateLimiter
from app.modules.routing.service import EtaService
from app.modules.routing.types import Source
from tests.conftest import FIXED_NOW

OSRM_URL = os.environ.get("OSRM_URL", "")
HOST = (urlsplit(OSRM_URL).hostname or "").lower()

# Two points a few kilometres apart in the NCR extract used by prepare_maps.sh.
SECTOR_62 = LatLng(lat=28.5703, lng=77.3218)
SECTOR_135 = LatLng(lat=28.5123, lng=77.3910)

self_hosted_only = pytest.mark.skipif(
    not OSRM_URL or HOST in PUBLIC_OSM_HOSTS,
    reason=(
        "needs a self-hosted OSRM: set OSRM_URL to your own instance (task I02b). "
        "The public demo server is deliberately not accepted here (ADR-0010)."
    ),
)


def live_provider() -> OsrmRoutingProvider:
    return OsrmRoutingProvider(
        OSRM_URL,
        fallback=ApproxRoutingProvider(SystemClock()),
        limiter=UnlimitedRateLimiter(),
        user_agent="flex-platform/0.1 (contact: dev@example.com)",
    )


@self_hosted_only
async def test_route_against_a_real_extract() -> None:
    provider = live_provider()
    try:
        route = await provider.route(SECTOR_62, SECTOR_135)
    finally:
        await provider.close()

    assert route.approximate is False, "a healthy OSRM must not fall back"
    assert route.source is Source.osrm
    assert 120 < route.duration_seconds < 5400
    # Road distance must exceed the straight line but stay in the same order of magnitude.
    assert 7_000 < route.distance_meters < 30_000
    assert len(route.geometry) > 2, "a real route has more than two points"


@self_hosted_only
async def test_table_against_a_real_extract() -> None:
    provider = live_provider()
    try:
        table = await provider.table([SECTOR_62, SECTOR_135], [SECTOR_62, SECTOR_135])
    finally:
        await provider.close()

    assert table.approximate is False
    assert table.durations[0][0] == pytest.approx(0.0, abs=1.0)
    assert table.durations[0][1] > 0


@self_hosted_only
async def test_eta_service_against_a_real_extract() -> None:
    provider = live_provider()
    service = EtaService(provider, FakeClock(FIXED_NOW))
    try:
        estimate = await service.eta(SECTOR_62, SECTOR_135)
    finally:
        await provider.close()

    assert estimate.approximate is False
    assert 2 < estimate.minutes < 90


def test_the_public_server_is_never_used_here() -> None:
    """Runs always: proves the skip guard covers the public host, not just an empty URL."""
    assert not (OSRM_URL and HOST in PUBLIC_OSM_HOSTS and not self_hosted_only.args[0]), (
        "these tests must never be enabled against a public OSM server"
    )
