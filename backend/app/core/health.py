"""Readiness checks behind `/health/ready`.

A check is a named async callable returning `CheckResult`. Keeping them in a registry
means adding a dependency never means editing the health route.

`non-functional.md` (Operability) names four: database, Redis, MQTT and OSRM. All four
are registered in `create_app`.

Severity follows `non-functional.md` (Operability): a failing **required** check makes the
service unready; a failing **optional** check only degrades it. Routing is the documented
example — OSRM being down must not take the service out of rotation, because the `approx`
provider keeps ETAs available (ADR-0010, `control-model.md` §6).
"""

from __future__ import annotations

import asyncio
import contextlib
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


def mqtt_check(host: str, port: int, *, timeout_seconds: float = 2.0) -> CheckFn:
    """Optional: can this process open a connection to the broker?

    A TCP connect, not an MQTT CONNECT. Two reasons, and the `detail` says so rather
    than letting the check look stronger than it is:

    * the API process holds no broker credentials - they belong to the ingestor and to
      each vehicle (B11) - so an authenticated CONNECT would need a credential invented
      for health checking, which is a credential that can leak;
    * the thing worth catching here is "the broker is gone or unroutable", and that is
      exactly what a refused TCP connect says.

    **Optional, not required.** GPS stops flowing when the broker is down, but every
    HTTP endpoint still works, and the `/driver/location` HTTPS fallback (B12) exists
    for precisely this case. Taking the API out of rotation would turn a degraded
    tracking picture into a total outage.
    """

    async def check() -> CheckResult:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=timeout_seconds
            )
        except TimeoutError:
            # `str(TimeoutError())` is empty, so reporting the exception alone produced
            # "unreachable: " and told the reader nothing. Name the timeout instead -
            # a timeout and a refused connection point at different problems (a
            # firewall or dead host, against a broker that is down on a reachable one).
            return CheckResult(
                Status.unavailable,
                f"{host}:{port} did not answer within {timeout_seconds:g}s",
            )
        except OSError as exc:
            return CheckResult(Status.unavailable, f"{host}:{port} unreachable: {exc}"[:200])
        writer.close()
        with contextlib.suppress(Exception):
            await writer.wait_closed()
        del reader
        return CheckResult(Status.ok, f"{host}:{port} reachable (tcp, not an MQTT CONNECT)")

    return check


def routing_check(
    osrm_url: str,
    *,
    is_public: bool,
    user_agent: str,
    timeout_seconds: float = 2.0,
) -> CheckFn:
    """Optional: is the routing server answering?

    **A public OSRM is never probed.** ADR-0010 rule 3 gives the whole platform one
    request per second, shared across every process; a readiness probe every ten
    seconds from each of them would spend a standing share of that budget on a question
    nobody acts on, and push real ETAs onto the `approx` fallback to pay for it. So when
    the configured URL is donated infrastructure the check reports `ok` and says it did
    not probe - which is honest, and matches the ladder: a public OSRM that stops
    answering degrades ETAs to `approx` by design and is visible on
    `smartcab_routing_requests_total`, not here.

    A self-hosted OSRM (task I02b) is ours to probe, and is probed.
    """

    async def check() -> CheckResult:
        if is_public:
            return CheckResult(
                Status.ok,
                "public OSRM not probed (ADR-0010 rate budget); "
                'watch smartcab_routing_requests_total{source="approx"}',
            )

        import httpx

        # Two points in the NCR box the pilot serves, so a server that came up with no
        # data answers `NoRoute` and is reported unavailable rather than healthy.
        path = "/route/v1/driving/77.3218,28.5703;77.3910,28.5123"
        try:
            async with httpx.AsyncClient(
                timeout=timeout_seconds, headers={"User-Agent": user_agent}
            ) as client:
                response = await client.get(f"{osrm_url}{path}", params={"overview": "false"})
                response.raise_for_status()
                code = response.json().get("code")
        except (httpx.HTTPError, ValueError) as exc:
            return CheckResult(Status.unavailable, f"{type(exc).__name__}: {exc}"[:200])

        if code != "Ok":
            return CheckResult(Status.unavailable, f"OSRM answered code={code!r}")
        return CheckResult(Status.ok)

    return check
