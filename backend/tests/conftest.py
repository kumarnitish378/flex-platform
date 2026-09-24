"""Shared fixtures.

Tests never touch a real database or the system clock: the app factory takes both as
arguments, which is the point of the injection in `create_app`.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.clock import FakeClock
from app.core.logging import configure_logging
from app.core.settings import Settings
from app.main import create_app

# A fixed, timezone-aware instant so every time-dependent assertion is deterministic.
FIXED_NOW = datetime(2026, 9, 24, 4, 30, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _hermetic_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make `Settings()` read documented defaults, not the machine it runs on.

    Without this a test asserting a default silently asserts whatever the environment
    happens to say. CI sets ROUTING_PROVIDER=approx for safety, which is exactly how
    `test_cached_osrm_is_the_default` came to pass locally and fail in CI.

    Field names are derived from the model, so a new setting is covered automatically.
    """
    for field_name in Settings.model_fields:
        monkeypatch.delenv(field_name.upper(), raising=False)
        monkeypatch.delenv(field_name.lower(), raising=False)
    # A developer's local .env must not reach the tests either.
    monkeypatch.setitem(Settings.model_config, "env_file", None)


@pytest.fixture(autouse=True)
def _fresh_logging() -> None:
    """Rebind logging to the current stdout for every test.

    structlog caches the logger on first use, so without this a test that captures
    stdout leaves every later test writing to a closed stream.
    """
    configure_logging(level="INFO", json_output=True, cache_loggers=False)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(FIXED_NOW)


@pytest.fixture
def settings() -> Settings:
    return Settings(
        app_env="dev",
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        jwt_secret="test-secret",
    )


@pytest.fixture
def app(settings: Settings, clock: FakeClock) -> FastAPI:
    # A real AsyncEngine is created but never connected to: nothing in these tests
    # issues a query except the readiness test, which stubs the check.
    return create_app(settings=settings, clock=clock)


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
