"""FastAPI application factory.

Everything the app needs is built here and stored on `app.state`, so tests can build an
app with a `FakeClock` and a stub engine without touching global state.

Run: `make backend-dev` (uvicorn app.main:create_app --factory).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.clock import Clock, FakeClock, SystemClock
from app.core.db import create_engine, create_session_factory
from app.core.errors import register_error_handlers
from app.core.health import HealthRegistry, Status, database_check
from app.core.logging import (
    configure_logging,
    get_logger,
    operator_id_var,
    request_id_var,
    user_id_var,
)
from app.core.redis import create_redis, redis_check
from app.core.settings import Settings, get_settings
from app.modules.auth.otp import build_otp_sender
from app.modules.auth.router import router as auth_router
from app.modules.config.router import router as config_router
from app.modules.fleet.duty_router import router as duty_router
from app.modules.fleet.router import router as fleet_router
from app.modules.people.router import router as people_router
from app.modules.requests.router import router as requests_router
from app.modules.routing import EtaService, build_geocoding_provider, build_routing_provider
from app.modules.simctl.router import router as simctl_router

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

    health = HealthRegistry()
    health.register("database", database_check(engine), required=True)
    health.register("redis", redis_check(redis), required=False)

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
    app.state.geocoding = geocoding
    app.state.otp_sender = otp_sender
    app.state.health = health

    _register_middleware(app)
    register_error_handlers(app)
    app.include_router(_health_router())

    api = APIRouter(prefix=API_PREFIX)
    api.include_router(auth_router)
    api.include_router(config_router)
    api.include_router(fleet_router)
    api.include_router(duty_router)
    api.include_router(people_router)
    api.include_router(requests_router)

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
        try:
            response: Response = await call_next(request)
        finally:
            request_id_var.reset(request_token)
            operator_id_var.reset(operator_token)
            user_id_var.reset(user_token)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


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
