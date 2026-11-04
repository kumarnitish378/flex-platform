"""The metrics `non-functional.md` (Operability) requires actually exist and move.

The point of these tests is not that `prometheus_client` works. It is that each metric
the operability section names is **wired to the code path that produces it** - a metric
defined and never incremented is a blank Grafana panel, and a blank panel in an incident
is worse than no panel, because it reads as "zero" rather than "not measured".
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from app.core import metrics
from app.core.clock import FakeClock
from app.core.settings import Settings
from app.domain.geo import LatLng
from app.modules.routing.approx import ApproxConfig, ApproxRoutingProvider
from app.modules.routing.metered import MeteredRoutingProvider
from app.modules.routing.osrm import OsrmRoutingProvider
from app.modules.routing.types import RouteResult, Source, TableResult
from app.modules.tracking.service import GpsIngestor
from tests.fakes import FakeRedis

NOW = datetime(2026, 9, 24, 4, 30, tzinfo=UTC)
DELHI = LatLng(lat=28.5703, lng=77.3218)
NOIDA = LatLng(lat=28.5123, lng=77.3910)


def value(metric: object, **labels: str) -> float:
    """Current value of a labelled counter or gauge, 0.0 if it has never been touched."""
    name = metric._name  # type: ignore[attr-defined]
    suffix = "_total" if type(metric).__name__ == "Counter" else ""
    got = metrics.REGISTRY.get_sample_value(f"{name}{suffix}", labels or None)
    return 0.0 if got is None else got


def histogram_count(name: str, **labels: str) -> float:
    got = metrics.REGISTRY.get_sample_value(f"{name}_count", labels or None)
    return 0.0 if got is None else got


# --- the operability list exists --------------------------------------------


@pytest.mark.parametrize(
    "name",
    [
        "smartcab_http_requests_total",
        "smartcab_http_request_duration_seconds",
        "smartcab_routing_requests_total",
        "smartcab_routing_rate_limited_total",
        "smartcab_gps_pings_total",
        "smartcab_pending_requests",
        "smartcab_stale_vehicles",
        "smartcab_vehicles_on_duty",
        "smartcab_open_alerts",
        "smartcab_trips_in_progress",
    ],
)
def test_every_required_metric_is_registered(name: str) -> None:
    """`non-functional.md` Operability, metric by metric."""
    exported = metrics.render().decode()
    assert f"# HELP {name}" in exported, f"{name} is required by non-functional.md"


# --- routing: cache hit rate, calls per provider, approximate share ----------


class _FixedProvider:
    """Returns one canned answer, so the wrapper's labels are the only variable."""

    name = "fixed"

    def __init__(self, source: Source, approximate: bool) -> None:
        self._source = source
        self._approximate = approximate

    async def route(self, origin: LatLng, destination: LatLng) -> RouteResult:
        return RouteResult(
            duration_seconds=600.0,
            distance_meters=5000.0,
            source=self._source,
            approximate=self._approximate,
        )

    async def table(self, origins: list[LatLng], destinations: list[LatLng]) -> TableResult:
        return TableResult(
            durations=((600.0,),),
            distances=((5000.0,),),
            source=self._source,
            approximate=self._approximate,
        )

    async def close(self) -> None:
        return None


async def test_a_cache_hit_is_counted_as_a_cache_hit() -> None:
    before = value(metrics.routing_requests, operation="route", source="cache", approximate="false")
    provider = MeteredRoutingProvider(_FixedProvider(Source.cache, approximate=False))

    await provider.route(DELHI, NOIDA)

    after = value(metrics.routing_requests, operation="route", source="cache", approximate="false")
    assert after == before + 1


async def test_an_approximate_answer_is_counted_as_approximate() -> None:
    """The share of ETAs served approximate is the number ADR-0010 asks us to watch."""
    before = value(metrics.routing_requests, operation="table", source="approx", approximate="true")
    provider = MeteredRoutingProvider(_FixedProvider(Source.approx, approximate=True))

    await provider.table([DELHI], [NOIDA])

    after = value(metrics.routing_requests, operation="table", source="approx", approximate="true")
    assert after == before + 1


class _NoTokens:
    async def try_acquire(self, service: str) -> bool:
        return False


async def test_a_refused_token_is_counted_as_a_rate_limit() -> None:
    """A call that was never made is the one event the answer itself cannot show."""
    before = value(metrics.routing_rate_limited, service="osrm")
    osrm = OsrmRoutingProvider(
        "https://router.project-osrm.org",
        fallback=ApproxRoutingProvider(FakeClock(NOW), ApproxConfig()),
        limiter=_NoTokens(),
        user_agent="flex-platform/test (contact: test@example.com)",
    )

    result = await osrm.route(DELHI, NOIDA)
    await osrm.close()

    assert result.approximate, "a refused token must degrade, not fail"
    assert value(metrics.routing_rate_limited, service="osrm") == before + 1


# --- GPS ---------------------------------------------------------------------


class _UntouchedSession:
    """Stands in for the database.

    `ingest()` of a single fresh ping buffers the row and returns: `flush_if_due()` is
    not due (the ingestor's last flush is `clock.now()`) and the buffer is one row deep,
    so nothing reaches a session. Any attribute access is therefore a bug in this test,
    not a missing fake - hence the explicit failure rather than a `Mock`.
    """

    def __getattr__(self, name: str) -> object:
        raise AssertionError(f"ingest() must not touch the session; it called {name!r}")


def _ping(ts: datetime, **extra: object) -> dict[str, object]:
    return {"v": 1, "ts": ts.isoformat(), "lat": DELHI.lat, "lng": DELHI.lng, **extra}


async def test_an_accepted_ping_is_counted_and_its_lag_observed() -> None:
    clock = FakeClock(NOW)
    accepted_before = value(metrics.gps_pings, outcome="accepted")
    lag_before = histogram_count("smartcab_gps_ingest_lag_seconds")

    ingestor = GpsIngestor(_UntouchedSession(), clock, FakeRedis(clock))  # type: ignore[arg-type]
    result = await ingestor.ingest(
        uuid.UUID(int=1), uuid.UUID(int=2), _ping(NOW - timedelta(seconds=4))
    )

    assert result.accepted == 1
    assert value(metrics.gps_pings, outcome="accepted") == accepted_before + 1
    assert histogram_count("smartcab_gps_ingest_lag_seconds") == lag_before + 1


async def test_a_dropped_ping_is_counted_under_its_reason() -> None:
    """Not one `dropped` bucket: OQ-33 was diagnosed from *which* reason was firing."""
    clock = FakeClock(NOW)
    before = value(metrics.gps_pings, outcome="too_far_future")

    ingestor = GpsIngestor(_UntouchedSession(), clock, FakeRedis(clock))  # type: ignore[arg-type]
    result = await ingestor.ingest(
        uuid.UUID(int=1), uuid.UUID(int=2), _ping(NOW + timedelta(hours=1))
    )

    assert result.dropped == 1
    assert value(metrics.gps_pings, outcome="too_far_future") == before + 1


# --- the exposition itself ----------------------------------------------------


def test_the_scrape_body_is_prometheus_text() -> None:
    body = metrics.render().decode()
    assert body.startswith("# HELP ")
    assert metrics.CONTENT_TYPE.startswith("text/plain")


def test_metrics_port_is_off_unless_configured() -> None:
    """A port opened by default is a port nobody meant to open."""
    settings = Settings(database_url="postgresql+asyncpg://test:test@localhost:5432/test")
    assert settings.metrics_port == 0


# --- the HTTP endpoint ---------------------------------------------------------


async def test_a_served_request_is_counted_under_its_route_template(
    client: AsyncClient,
) -> None:
    """The template, not the path: a UUID in a label mints a series per ride."""
    before = value(metrics.http_requests, method="GET", route="/health/doesnotexist", status="404")

    await client.get("/health/doesnotexist")

    # An unmatched path must land in one bucket, never in a per-path series.
    assert (
        value(metrics.http_requests, method="GET", route="/health/doesnotexist", status="404")
        == before
    )
    assert value(metrics.http_requests, method="GET", route="unmatched", status="404") >= 1


async def test_the_route_label_is_the_full_path_with_parameters_replaced(
    client: AsyncClient,
) -> None:
    """Two things at once, both of which were wrong at first.

    The prefix: this project includes its routers nested, so `route.path` is
    `/auth/me` with no `/api/v1` - which hides the prefix and lets two routers with the
    same relative path share one label.

    The parameter: a UUID in the label mints a time series per ride.
    """
    request_id = "11111111-1111-1111-1111-111111111111"

    # Unauthenticated, so it is refused - the label is recorded either way, which is
    # the point: an endpoint returning 401 to everybody must still be visible.
    await client.get(f"/api/v1/ride-requests/{request_id}")

    assert (
        value(
            metrics.http_requests,
            method="GET",
            route="/api/v1/ride-requests/{request_id}",
            status="401",
        )
        >= 1
    )
    assert (
        value(metrics.http_requests, method="GET", route=f"/api/v1/ride-requests/{request_id}")
        == 0.0
    )


async def test_scraping_does_not_count_itself(client: AsyncClient) -> None:
    """A scrape every 15 s would otherwise be most of the traffic on an idle box."""
    await client.get("/metrics")
    assert value(metrics.http_requests, method="GET", route="/metrics", status="200") == 0.0


async def test_the_metrics_endpoint_serves_the_registry(client: AsyncClient) -> None:
    response = await client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "smartcab_http_requests_total" in response.text


async def test_a_failing_gauge_query_does_not_break_the_scrape(client: AsyncClient) -> None:
    """The fixture app has no reachable database, so every gauge query raises.

    The scrape must still return the counters this process did accumulate: losing the
    database is precisely when the request-rate and error-rate panels matter most.
    """
    response = await client.get("/metrics")

    assert response.status_code == 200
    assert "smartcab_gps_pings_total" in response.text
