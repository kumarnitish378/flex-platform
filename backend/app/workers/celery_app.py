"""The Celery app, its beat schedule, and the three due-work tasks (B20).

Design notes worth keeping, because each one is a trap avoided:

* **The tasks are thin.** Each one opens a session, calls the same service method
  `/simctl/clock` calls, commits and logs. The logic stays in the service so the
  simulator and production exercise *the same code* - which is the whole point of
  ADR-0008, and the reason a clock jump in a scenario is a faithful test of this.
* **`SystemClock`, deliberately.** Hard rule 2 bans reading the system clock in domain
  code; this is the edge where real time legitimately enters, exactly as the HTTP layer
  is. The sweeps take the clock as an argument and cannot tell the difference.
* **One engine per worker process, created lazily.** Celery forks, and an async engine
  created before the fork hands every child the parent's sockets.
* **A task that raises must not take the beat down.** Each one logs and returns a
  summary; Celery retries on its own schedule, and the next tick is a minute away.
"""

from __future__ import annotations

import asyncio
from typing import Any

from celery import Celery
from celery.schedules import crontab  # noqa: F401 - kept for the schedule's readability
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.clock import SystemClock
from app.core.db import create_engine, create_session_factory
from app.core.logging import configure_logging, get_logger
from app.core.redis import create_redis
from app.core.settings import Settings, get_settings

logger = get_logger(__name__)

#: How often each sweep runs, in seconds.
#:
#: `expiry` every minute: `request_expiry_minutes` is 120 by default and the near-expiry
#: warning fires 15 minutes out, so a minute of granularity is far finer than anything
#: that depends on it. Escalation (ADR-0019) rides the same sweep.
#:
#: `stop_etas` every 30 seconds, because that is what B15 specifies: a rider watching a
#: cab approach is the one screen where a stale number is immediately obvious.
#:
#: `stale_vehicles` every 30 seconds, half of `stale_gps_seconds` (60) - so a cab that
#: goes quiet is noticed within one interval of crossing the line rather than two.
EXPIRY_INTERVAL_SECONDS = 60
STOP_ETA_INTERVAL_SECONDS = 30
STALE_VEHICLE_INTERVAL_SECONDS = 30


def create_celery(settings: Settings | None = None) -> Celery:
    """The Celery app. Broker and result backend are the Redis we already run."""
    resolved = settings or get_settings()
    app = Celery("smart_cab", broker=resolved.redis_url, backend=resolved.redis_url)
    app.conf.update(
        timezone="UTC",
        enable_utc=True,
        # Due work is only worth doing now: a sweep that queued up while the worker was
        # down should not run twenty times when it comes back.
        task_ignore_result=True,
        broker_connection_retry_on_startup=True,
        beat_schedule={
            "expire-and-escalate-requests": {
                "task": "smart_cab.expire_requests",
                "schedule": float(EXPIRY_INTERVAL_SECONDS),
            },
            "refresh-stop-etas": {
                "task": "smart_cab.refresh_stop_etas",
                "schedule": float(STOP_ETA_INTERVAL_SECONDS),
            },
            "sweep-stale-vehicles": {
                "task": "smart_cab.sweep_stale_vehicles",
                "schedule": float(STALE_VEHICLE_INTERVAL_SECONDS),
            },
        },
    )
    return app


celery_app = create_celery()

#: Created on first use inside the worker process, never at import: Celery forks, and an
#: engine built before the fork would share sockets with every child.
_engine: AsyncEngine | None = None
_sessions: async_sessionmaker[AsyncSession] | None = None


def _session_factory(settings: Settings) -> async_sessionmaker[AsyncSession]:
    global _engine, _sessions
    if _sessions is None:
        _engine = create_engine(settings)
        _sessions = create_session_factory(_engine)
    return _sessions


async def _expire_requests() -> dict[str, int]:
    from app.modules.requests.service import RideRequestService

    settings = get_settings()
    async with _session_factory(settings)() as session:
        sweep = await RideRequestService(session, SystemClock()).run_due_expiries()
        await session.commit()
    return {
        "expired": sweep.expired,
        "warned": sweep.warned,
        "escalated": sweep.escalated,
    }


async def _refresh_stop_etas() -> dict[str, int]:
    from app.modules.dispatch.eta_refresh import EtaRefresher
    from app.modules.routing import EtaService, build_routing_provider

    settings = get_settings()
    clock = SystemClock()
    # The routing provider is built here rather than shared with the API: this is a
    # different process, and the shared 1 req/s limiter lives in Redis for exactly that
    # reason (ADR-0010 rule 4).
    redis = create_redis(settings)
    eta = EtaService(build_routing_provider(settings, clock, redis), clock)
    async with _session_factory(settings)() as session:
        result = await EtaRefresher(session, clock, eta).refresh_due()
        await session.commit()
    return {"stops": result.stops}


async def _sweep_stale_vehicles() -> dict[str, int]:
    from app.modules.alerts.service import AlertService

    settings = get_settings()
    async with _session_factory(settings)() as session:
        sweep = await AlertService(session, SystemClock()).sweep_stale_vehicles()
        await session.commit()
    return {"raised": sweep.raised, "cleared": sweep.cleared}


def _run(name: str, coroutine: Any) -> dict[str, int]:
    """Run one sweep, and never let it take the beat down.

    A sweep that raises is logged and skipped. The alternative - letting the exception
    out - marks the task failed and, with a misconfigured broker, can stall the whole
    beat; and the next tick is thirty seconds away, so one bad pass costs nothing.
    """
    try:
        result: dict[str, int] = asyncio.run(coroutine())
    except Exception as exc:  # noqa: BLE001 - one bad sweep must not stop the rest
        logger.exception("due_work_failed", sweep=name, error=type(exc).__name__)
        return {}
    if any(result.values()):
        logger.info("due_work", sweep=name, **result)
    return result


@celery_app.task(name="smart_cab.expire_requests")
def expire_requests() -> dict[str, int]:
    """Expire what is due, warn about what is nearly due, escalate what nobody served."""
    return _run("expiry", _expire_requests)


@celery_app.task(name="smart_cab.refresh_stop_etas")
def refresh_stop_etas() -> dict[str, int]:
    """Keep the ETA a rider is watching honest (B15)."""
    return _run("stop_etas", _refresh_stop_etas)


@celery_app.task(name="smart_cab.sweep_stale_vehicles")
def sweep_stale_vehicles() -> dict[str, int]:
    """Alert on a cab that has gone quiet, and clear the alert when it comes back."""
    return _run("stale_vehicles", _sweep_stale_vehicles)


configure_logging()
