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
from app.core.settings import Settings
from app.main import create_app

# A fixed, timezone-aware instant so every time-dependent assertion is deterministic.
FIXED_NOW = datetime(2026, 9, 24, 4, 30, tzinfo=UTC)


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
