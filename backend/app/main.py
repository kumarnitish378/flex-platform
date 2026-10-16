"""FastAPI application factory.

Everything the app needs is built here and stored on `app.state`, so tests can build an
app with a `FakeClock` and a stub engine without touching global state.

Run: `make backend-dev` (uvicorn app.main:create_app --factory).
"""

from __future__ import annotations

import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core import metrics
from app.core.clock import Clock, FakeClock, SystemClock
from app.core.db import create_engine, create_session_factory
from app.core.errors import register_error_handlers
from app.core.events import RedisEventPublisher
from app.core.health import (
    HealthRegistry,
    Status,
    database_check,
    mqtt_check,
    routing_check,
)
from app.core.logging import (
    configure_logging,
    get_logger,
    operator_id_var,
    request_id_var,
    user_id_var,
)
from app.core.redis import create_redis, redis_check
from app.core.settings import Settings, get_settings
from app.modules.alerts.router import router as alerts_router
from app.modules.auth.otp import build_otp_sender
from app.modules.auth.router import router as auth_router
from app.modules.config.router import router as config_router
from app.modules.dispatch.driver_router import router as driver_trips_router
from app.modules.dispatch.router import router as dispatch_router
from app.modules.fleet.duty_router import router as duty_router
from app.modules.fleet.router import router as fleet_router
from app.modules.modes.router import router as modes_router
from app.modules.notifications.push import build_push_sender
from app.modules.observability import BusinessGaugeCollector
from app.modules.people.router import router as people_router
from app.modules.realtime.hub import Hub
from app.modules.realtime.router import router as realtime_router
from app.modules.realtime.service import MembershipService
from app.modules.reports.router import router as reports_router
from app.modules.requests.router import router as requests_router
from app.modules.routing import EtaService, build_geocoding_provider, build_routing_provider
from app.modules.simctl.router import router as simctl_router
from app.modules.tracking.router import router as tracking_router

logger = get_logger(__name__)

API_PREFIX = "/api/v1"
REQUEST_ID_HEADER = "X-Request-ID"


def create_app(
    settings: Settings | None = None,
    clock: Clock | None = None,
    engine: AsyncEngine | None = None,
) -> FastAPI:
    """Build the application.

    Arguments are injection points for tests; production passes nothing and everything
    is derived from the environment.
    """
    settings = settings or get_settings()
    configure_logging(level=settings.log_level, json_output=settings.log_json)

    # APP_ENV=sim gets a controllable clock so the simulator can accelerate time
    # (architecture.md §3.3). Everything else gets real time.
    if clock is None:
        clock = FakeClock(_sim_epoch()) if settings.is_sim else SystemClock()

    engine = engine if engine is not None else create_engine(settings)
    redis = create_redis(settings)

    # One place decides which map services are used, so switching between the public
    # OSM servers and a self-hosted stack is configuration only (ADR-0010).
    routing = build_routing_provider(settings, clock, redis)
    geocoding = build_geocoding_provider(settings)
    eta = EtaService(routing, clock)
    otp_sender = build_otp_sender(settings)
    push_sender = build_push_sender(settings)

    # The four dependencies `non-functional.md` (Operability) names. Only the database
    # is required: losing Redis, the broker or OSRM degrades the product - a stale map,
    # GPS over the HTTPS fallback, approximate ETAs - but every endpoint still answers,
    # and taking the service out of rotation would turn each of those into an outage.
    health = HealthRegistry()
    health.register("database", database_check(engine), required=True)
    health.register("redis", redis_check(redis), required=False)
    health.register(
        "mqtt",
        mqtt_check(settings.mqtt_host, settings.mqtt_port),
        required=False,
    )
    health.register(
        "routing",
        routing_check(
            settings.osrm_url,
            is_public=settings.uses_public_osrm,
            user_agent=settings.user_agent,
            timeout_seconds=settings.osm_request_timeout_seconds,
        ),
        required=False,
    )

    app = FastAPI(
        title="Smart Cab API",
        version="0.1.0",
        docs_url="/docs" if settings.app_env != "prod" else None,
        lifespan=_lifespan,
    )

    app.state.settings = settings
    app.state.clock = clock
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    app.state.redis = redis
    app.state.routing = routing
    app.state.eta = eta
    app.state.events = RedisEventPublisher(redis)
    # One hub per process; it holds the sockets and the Redis subscription behind them.
    app.state.hub = Hub(redis)
    app.state.membership = MembershipService
    app.state.geocoding = geocoding
    app.state.otp_sender = otp_sender
    app.state.push_sender = push_sender
    app.state.health = health

    _register_middleware(app)
    register_error_handlers(app)
    app.include_router(_health_router())
    app.include_router(_metrics_router())

    api = APIRouter(prefix=API_PREFIX)
    api.include_router(auth_router)
    api.include_router(config_router)
    api.include_router(modes_router)
    api.include_router(fleet_router)
    api.include_router(duty_router)
    api.include_router(tracking_router)
    api.include_router(people_router)
    api.include_router(requests_router)
    api.include_router(dispatch_router)
    api.include_router(driver_trips_router)
    api.include_router(alerts_router)
    api.include_router(reports_router)
    api.include_router(realtime_router)

    # Mounted only in sim, so these paths genuinely do not exist anywhere else
    # (ADR-0008). A runtime flag could be flipped; an unregistered route cannot be.
    if settings.is_sim:
        api.include_router(simctl_router)
    app.include_router(api)

    logger.info(
        "app_created",
        app_env=str(settings.app_env),
        clock=type(clock).__name__,
        routing_provider=routing.name,
        geocoding_provider=geocoding.name,
        public_osm=settings.uses_public_osm,
    )
    return app


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await app.state.hub.close()
    await app.state.routing.close()
    await app.state.redis.aclose()
    engine: AsyncEngine = app.state.engine
    await engine.dispose()


def _register_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_context(request: Request, call_next: Any) -> Response:
        """Give every request an id and put it in the log context and the response."""
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request_token = request_id_var.set(request_id)
        # Populated by the auth dependency once B03/B04 land.
        operator_token = operator_id_var.set(None)
        user_token = user_id_var.set(None)
        started = time.perf_counter()
        status_code = 500
        try:
            response: Response = await call_next(request)
            status_code = response.status_code
        finally:
            _record_http(request, status_code, time.perf_counter() - started)
            request_id_var.reset(request_token)
            operator_id_var.reset(operator_token)
            user_id_var.reset(user_token)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


def _route_template(request: Request) -> str:
    """The full route template for a served request, or `unmatched`.

    `/api/v1/ride-requests/{request_id}`, never the concrete path: a UUID in a label
    mints a new time series per ride and makes the metric cost more than the traffic it
    measures. A request that matched no route is recorded once as `unmatched`, so a
    flood of 404s against random paths cannot do the same thing.

    Built from the request path with the matched path parameters put back as
    placeholders, **not** from `route.path`. This project includes its routers nested
    rather than flattened, so `route.path` is relative to the router it was declared in
    - `/auth/me`, with no `/api/v1` - which both hides the prefix and lets two routers
    with the same relative path share one label. Path parameters are always whole
    segments here, so substituting segment by segment is exact.
    """
    route = request.scope.get("route")
    if route is None or getattr(route, "path", None) is None:
        return "unmatched"

    path = request.url.path
    params = request.scope.get("path_params") or {}
    if not params:
        return path

    placeholder_for = {str(value): name for name, value in params.items()}
    return "/".join(
        "{" + placeholder_for[segment] + "}" if segment in placeholder_for else segment
        for segment in path.split("/")
    )


def _record_http(request: Request, status_code: int, seconds: float) -> None:
    """One observation per request."""
    template = _route_template(request)
    if template in _METRICS_EXCLUDED_ROUTES:
        return
    method = request.method
    metrics.http_requests.labels(method=method, route=template, status=str(status_code)).inc()
    metrics.http_duration.labels(method=method, route=template).observe(seconds)


#: Scraping and liveness are not traffic. Counting them makes the request rate look
#: busy on an idle box and pollutes the latency histogram with sub-millisecond hits.
_METRICS_EXCLUDED_ROUTES = frozenset({"/metrics", "/health/live", "/health/ready"})


def _metrics_router() -> APIRouter:
    """The Prometheus scrape endpoint.

    Outside `/api/v1` and out of the OpenAPI schema for the same reason as the health
    endpoints: this is for the monitoring stack, not for a client.

    It is **not** authenticated, and must not be exposed publicly. In the staging and
    production compose Caddy serves only `/api` and `/ws`; Prometheus reaches this over
    the private compose network (`infra/docker-compose.staging.yml`).
    """
    router = APIRouter(tags=["metrics"])

    @router.get("/metrics", include_in_schema=False)
    async def scrape(request: Request) -> PlainTextResponse:
        session_factory = request.app.state.session_factory
        async with session_factory() as session:
            await BusinessGaugeCollector(session, request.app.state.clock).collect()
        return PlainTextResponse(metrics.render(), media_type=metrics.CONTENT_TYPE)

    return router


def _health_router() -> APIRouter:
    """Operational endpoints.

    Deliberately outside `/api/v1` and outside `api-spec.yaml`: the spec is the client
    contract (its server URL is `/api/v1`), while these are for the process manager and
    monitoring, as specified in `architecture.md` §5 and `non-functional.md`.
    """
    router = APIRouter(tags=["health"])

    @router.get("/health/live", include_in_schema=False)
    async def live() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/health/ready", include_in_schema=False)
    async def ready(request: Request) -> JSONResponse:
        registry: HealthRegistry = request.app.state.health
        overall, checks = await registry.run()
        # Degraded still serves traffic: a failing optional dependency must not take the
        # service out of rotation (non-functional.md, Operability).
        status_code = 503 if overall is Status.unavailable else 200
        return JSONResponse(
            status_code=status_code,
            content={"status": str(overall), "checks": checks},
        )

    return router


def _sim_epoch() -> Any:
    """Starting point for the simulated clock before the first `/simctl/clock` call."""
    from datetime import UTC, datetime

    return datetime(2026, 1, 1, tzinfo=UTC)
