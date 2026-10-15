"""Prometheus metrics (`non-functional.md`, Operability).

Every metric named in that section is defined here, once, so a dashboard panel and the
code that feeds it cannot drift apart. Nothing else in the codebase constructs a metric.

**Why a module-level registry and not a per-app one.** Prometheus client metrics are
process-global by construction: a scrape reads the whole process. Building them inside
`create_app()` would raise `Duplicated timeseries` the second time a test built an app,
so they are defined at import and the API route only renders them.

**Three processes expose metrics, not one.** The API serves `/metrics` itself; the GPS
ingestor and the Celery worker are separate processes with their own counters and run a
tiny HTTP server each (`serve_metrics`). Prometheus scrapes all three - see
`infra/prometheus/prometheus.yml`. Run the API as a **single** uvicorn process per
container: with several workers a scrape would hit one at random and report a fraction
of the truth.

**Business gauges are read at scrape time** (`app/core/business_metrics.py`), because
"how many requests are pending right now" is a question about the database, not a count
this process accumulated.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Final

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest
from prometheus_client.exposition import start_http_server

from app.core.logging import get_logger

logger = get_logger(__name__)

CONTENT_TYPE: Final = "text/plain; version=0.0.4; charset=utf-8"

#: Our own registry rather than the global default: the default also carries the process
#: and GC collectors of whatever imported us, and a test asserting on our output should
#: not have to filter those out.
REGISTRY: Final = CollectorRegistry()

# --- HTTP (API latency and error rate) --------------------------------------

#: Buckets chosen around the p95 <= 300 ms target in `non-functional.md`: several below
#: it, so a drift from 120 ms to 280 ms is visible before it breaches, and a long tail
#: above for the ones that go wrong.
_LATENCY_BUCKETS: Final = (0.025, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0, 2.5, 5.0, 10.0)

http_requests = Counter(
    "smartcab_http_requests_total",
    "HTTP requests served, by route template and status code.",
    ("method", "route", "status"),
    registry=REGISTRY,
)

http_duration = Histogram(
    "smartcab_http_request_duration_seconds",
    "Wall time to serve an HTTP request.",
    ("method", "route"),
    buckets=_LATENCY_BUCKETS,
    registry=REGISTRY,
)

# --- routing (ADR-0010: cache hit rate, calls per provider, approximate share) ---

routing_requests = Counter(
    "smartcab_routing_requests_total",
    "Routing answers served, by where the answer came from.",
    ("operation", "source", "approximate"),
    registry=REGISTRY,
)

routing_rate_limited = Counter(
    "smartcab_routing_rate_limited_total",
    "Upstream routing calls not made because the shared budget was spent, and therefore "
    "answered by the approx provider instead.",
    ("service",),
    registry=REGISTRY,
)

routing_upstream_duration = Histogram(
    "smartcab_routing_upstream_seconds",
    "Wall time of a call that actually reached the routing server.",
    ("operation",),
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=REGISTRY,
)

# --- GPS ingestion (B12) -----------------------------------------------------

#: `outcome` is `accepted` or the drop reason from `app/domain/gps.py`, so the reasons
#: that mattered in OQ-33 (`too_far_future`, `out_of_order`, ...) are each visible
#: rather than summed into one "dropped".
#:
#: Deliberately **not** labelled by vehicle. `non-functional.md` asks for "GPS ping rate
#: per vehicle"; a UUID label churns a new time series every time the fleet changes and
#: costs more than it tells. The per-vehicle rate is
#: `rate(smartcab_gps_pings_total[5m]) / smartcab_vehicles_on_duty`, and one cab going
#: silent is what `smartcab_stale_vehicles` is for.
gps_pings = Counter(
    "smartcab_gps_pings_total",
    "GPS pings received by the ingestor, by outcome.",
    ("outcome",),
    registry=REGISTRY,
)

gps_ingest_lag = Histogram(
    "smartcab_gps_ingest_lag_seconds",
    "Age of a ping when the ingestor accepted it (ping timestamp to ingest time).",
    buckets=(1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
    registry=REGISTRY,
)

gps_rows_written = Counter(
    "smartcab_gps_rows_written_total",
    "Location pings persisted to location_ping.",
    registry=REGISTRY,
)

# --- scheduled sweeps (B20) --------------------------------------------------

sweep_runs = Counter(
    "smartcab_sweep_runs_total",
    "Scheduled sweep executions, by task and outcome.",
    ("task", "outcome"),
    registry=REGISTRY,
)

sweep_duration = Histogram(
    "smartcab_sweep_duration_seconds",
    "Wall time of a scheduled sweep.",
    ("task",),
    buckets=(0.05, 0.1, 0.5, 1.0, 5.0, 15.0, 30.0, 60.0),
    registry=REGISTRY,
)

# --- business state (read at scrape time) ------------------------------------

pending_requests = Gauge(
    "smartcab_pending_requests",
    "Ride requests queued and not yet assigned to a vehicle.",
    ("operator_id",),
    registry=REGISTRY,
)

longest_pending_wait = Gauge(
    "smartcab_longest_pending_wait_seconds",
    "How long the oldest unassigned request has been waiting.",
    ("operator_id",),
    registry=REGISTRY,
)

vehicles_on_duty = Gauge(
    "smartcab_vehicles_on_duty",
    "Vehicles with an open duty session.",
    ("operator_id",),
    registry=REGISTRY,
)

stale_vehicles = Gauge(
    "smartcab_stale_vehicles",
    "On-duty vehicles whose last GPS ping is older than the staleness threshold.",
    ("operator_id",),
    registry=REGISTRY,
)

open_alerts = Gauge(
    "smartcab_open_alerts",
    "Alerts raised and not yet resolved, by severity.",
    ("operator_id", "severity"),
    registry=REGISTRY,
)

trips_in_progress = Gauge(
    "smartcab_trips_in_progress",
    "Trips that have started and not finished.",
    ("operator_id",),
    registry=REGISTRY,
)


# --- helpers -----------------------------------------------------------------


def render() -> bytes:
    """The scrape body."""
    return generate_latest(REGISTRY)


def observe_routing(operation: str, source: str, approximate: bool) -> None:
    """Record one routing answer. Called by the metered provider wrapper."""
    routing_requests.labels(
        operation=operation,
        source=source,
        approximate="true" if approximate else "false",
    ).inc()


@contextmanager
def timed(histogram: Histogram, **labels: str) -> Iterator[None]:
    """Observe the duration of a block, including when it raises."""
    started = time.perf_counter()
    try:
        yield
    finally:
        target = histogram.labels(**labels) if labels else histogram
        target.observe(time.perf_counter() - started)


def serve_metrics(port: int) -> None:
    """Expose this process's metrics on `port` for Prometheus to scrape.

    Used by the ingestor and the Celery worker, which have no HTTP server of their own.
    A failure here is logged and swallowed: losing metrics must never stop GPS ingestion.
    """
    try:
        start_http_server(port, registry=REGISTRY)
    except OSError as exc:
        logger.warning("metrics_server_failed", port=port, error=str(exc))
        return
    logger.info("metrics_server_started", port=port)
