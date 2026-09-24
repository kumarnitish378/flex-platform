"""Health endpoints — B01 acceptance: the app serves /health/live and /health/ready.

No database is involved: the readiness registry is swapped for stubs, which is exactly
how later tasks will test Redis, MQTT and routing checks too.
"""

from __future__ import annotations

from fastapi import FastAPI
from httpx import AsyncClient

from app.core.health import CheckFn, CheckResult, HealthRegistry, Status


async def test_live_is_always_ok(client: AsyncClient) -> None:
    response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_live_carries_a_request_id(client: AsyncClient) -> None:
    response = await client.get("/health/live")
    assert response.headers["X-Request-ID"]


async def test_supplied_request_id_is_echoed(client: AsyncClient) -> None:
    response = await client.get("/health/live", headers={"X-Request-ID": "req-abc"})
    assert response.headers["X-Request-ID"] == "req-abc"


async def test_ready_is_ok_when_every_check_passes(app: FastAPI, client: AsyncClient) -> None:
    registry = HealthRegistry()
    registry.register("database", _always(Status.ok), required=True)
    app.state.health = registry

    response = await client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "checks": {"database": {"status": "ok"}}}


async def test_failing_required_check_makes_the_service_unready(
    app: FastAPI, client: AsyncClient
) -> None:
    registry = HealthRegistry()
    registry.register("database", _always(Status.unavailable, "connection refused"))
    app.state.health = registry

    response = await client.get("/health/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "unavailable"
    assert body["checks"]["database"]["detail"] == "connection refused"


async def test_failing_optional_check_only_degrades(app: FastAPI, client: AsyncClient) -> None:
    """ADR-0010: OSRM being down must not take the service out of rotation."""
    registry = HealthRegistry()
    registry.register("database", _always(Status.ok), required=True)
    registry.register("routing", _always(Status.unavailable, "osrm timeout"), required=False)
    app.state.health = registry

    response = await client.get("/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["routing"]["status"] == "unavailable"


async def test_a_check_that_raises_counts_as_failed(app: FastAPI, client: AsyncClient) -> None:
    async def explodes() -> CheckResult:
        raise ConnectionError("no route to host")

    registry = HealthRegistry()
    registry.register("database", explodes, required=True)
    app.state.health = registry

    response = await client.get("/health/ready")
    assert response.status_code == 503
    assert "ConnectionError" in response.json()["checks"]["database"]["detail"]


async def test_database_check_is_registered_by_default(app: FastAPI) -> None:
    assert "database" in app.state.health.required


def _always(status: Status, detail: str | None = None) -> CheckFn:
    async def check() -> CheckResult:
        return CheckResult(status, detail)

    return check
