"""Readiness checks behind `/health/ready`.

A check is a named async callable returning `CheckResult`. Later tasks register more
(Redis with B12, MQTT with B12, routing with I02/B10). Keeping them in a registry means
adding a dependency never means editing the health route.

Severity follows `non-functional.md` (Operability): a failing **required** check makes the
service unready; a failing **optional** check only degrades it. Routing is the documented
example — OSRM being down must not take the service out of rotation, because the `approx`
provider keeps ETAs available (ADR-0010, `control-model.md` §6).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.logging import get_logger

logger = get_logger(__name__)


class Status(StrEnum):
    ok = "ok"
    degraded = "degraded"
    unavailable = "unavailable"


@dataclass(frozen=True)
class CheckResult:
    status: Status
    detail: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"status": str(self.status)}
        if self.detail:
            payload["detail"] = self.detail
        return payload


CheckFn = Callable[[], Awaitable[CheckResult]]


@dataclass
class HealthRegistry:
    """Named readiness checks and how much each one matters."""

    required: dict[str, CheckFn] = field(default_factory=dict)
    optional: dict[str, CheckFn] = field(default_factory=dict)

    def register(self, name: str, check: CheckFn, *, required: bool = True) -> None:
        (self.required if required else self.optional)[name] = check

    async def run(self) -> tuple[Status, dict[str, dict[str, Any]]]:
        results: dict[str, dict[str, Any]] = {}
        overall = Status.ok

        for name, check in self.required.items():
            result = await _safe(name, check)
            results[name] = result.as_dict()
            if result.status is not Status.ok:
                overall = Status.unavailable

        for name, check in self.optional.items():
            result = await _safe(name, check)
            results[name] = result.as_dict()
            if result.status is not Status.ok and overall is Status.ok:
                overall = Status.degraded

        return overall, results


async def _safe(name: str, check: CheckFn) -> CheckResult:
    """A check that raises is a failed check, never a 500 on the health endpoint."""
    try:
        return await check()
    except Exception as exc:  # noqa: BLE001 - any failure means "not ready"
        logger.warning("health_check_failed", check=name, error=type(exc).__name__)
        return CheckResult(Status.unavailable, f"{type(exc).__name__}: {exc}"[:200])


def database_check(engine: AsyncEngine) -> CheckFn:
    """Required: the service cannot serve anything useful without Postgres."""

    async def check() -> CheckResult:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return CheckResult(Status.ok)

    return check
