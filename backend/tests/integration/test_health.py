"""Health endpoints — B01 acceptance: the app serves /health/live and /health/ready.

No database is involved: the readiness registry is swapped for stubs, which is exactly
how later tasks will test Redis, MQTT and routing checks too.
"""

from __future__ import annotations

import asyncio

from fastapi import FastAPI
from httpx import AsyncClient

from app.core.health import (
    CheckFn,
    CheckResult,
    HealthRegistry,
    Status,
    mqtt_check,
    routing_check,
)


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


# --- the four dependencies non-functional.md names (R01) ---------------------


async def test_all_four_dependencies_are_checked(app: FastAPI) -> None:
    """Database, Redis, MQTT, OSRM. A missing one is a dependency nobody is watching."""
    registered = set(app.state.health.required) | set(app.state.health.optional)
    assert {"database", "redis", "mqtt", "routing"} <= registered


async def test_only_the_database_is_required(app: FastAPI) -> None:
    """Losing Redis, the broker or OSRM degrades the product; it is not an outage."""
    assert set(app.state.health.required) == {"database"}


async def test_mqtt_check_reports_an_unreachable_broker() -> None:
    """Port 1 on the loopback: privileged and unbound, so nothing can be listening.

    The *shape* of the failure is platform-dependent and deliberately not asserted:
    Linux refuses the connection immediately (`OSError`), Windows drops the packet and
    the attempt times out. What must hold on both is that the check fails and that the
    detail names the host and port, because "mqtt: unavailable" with no address is a
    line nobody can act on.
    """
    check = mqtt_check("127.0.0.1", 1, timeout_seconds=1.0)

    result = await check()

    assert result.status is Status.unavailable
    assert "127.0.0.1:1" in (result.detail or "")
    # A bare `str(TimeoutError())` is empty, which once produced "unreachable: " and
    # told the reader nothing. Whatever the path, the detail must say something.
    assert len(result.detail or "") > len("127.0.0.1:1 ")


async def test_mqtt_check_reports_a_reachable_broker() -> None:
    server = await asyncio.start_server(lambda r, w: w.close(), "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    try:
        result = await mqtt_check("127.0.0.1", port, timeout_seconds=1.0)()
    finally:
        server.close()
        await server.wait_closed()

    assert result.status is Status.ok
    # The check must not claim more than it did: this is a TCP connect.
    assert "not an MQTT CONNECT" in (result.detail or "")


async def test_a_public_osrm_is_never_probed() -> None:
    """ADR-0010 rule 3: the shared budget is one request a second for the whole platform.

    A readiness probe every ten seconds, from every process, would spend a standing
    share of it on a question nobody acts on. If this test ever fails, a health check
    has started competing with real ETAs for donated capacity.
    """
    check = routing_check(
        "https://router.project-osrm.org",
        is_public=True,
        user_agent="flex-platform/test (contact: test@example.com)",
    )

    result = await check()

    assert result.status is Status.ok
    assert "not probed" in (result.detail or "")


async def test_a_self_hosted_osrm_that_is_down_degrades_readiness(
    app: FastAPI, client: AsyncClient
) -> None:
    """Nothing is listening on this port, so the probe fails - and must only degrade."""
    app.state.health = HealthRegistry()
    app.state.health.register("database", _always(Status.ok), required=True)
    app.state.health.register(
        "routing",
        routing_check(
            "http://127.0.0.1:1",
            is_public=False,
            user_agent="flex-platform/test (contact: test@example.com)",
            timeout_seconds=1.0,
        ),
        required=False,
    )

    response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["checks"]["routing"]["status"] == "unavailable"
