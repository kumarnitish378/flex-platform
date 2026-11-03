"""The Celery worker runs every sweep in its own event loop (`asyncio.run` per task).

An engine that keeps pooled connections between sweeps hands the second sweep a connection
that belongs to the first sweep's closed loop. Found by the load test (2026-11-03): in the
`make phone-dev` stack every sweep after the first failed with "Event loop is closed" and
leaked a connection each time until Postgres refused new clients - which silently stopped
request expiry, stale-GPS alerts, the escort alert, the semi_auto failsafe and ETA refresh.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import text
from sqlalchemy.pool import NullPool

from app.core.settings import Settings
from app.workers import celery_app
from tests.integration.conftest import TEST_URL

pytestmark = pytest.mark.requires_db


@pytest.fixture
def worker_sessions(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setattr(celery_app, "_engine", None)
    monkeypatch.setattr(celery_app, "_sessions", None)
    yield


def _select_one() -> object:
    async def sweep() -> dict[str, int]:
        async with celery_app._session_factory(Settings(database_url=TEST_URL))() as session:
            value = (await session.execute(text("select 1"))).scalar_one()
        return {"value": int(value)}

    return sweep


def test_consecutive_sweeps_each_get_a_working_connection(worker_sessions: None) -> None:
    results = [celery_app._run("probe", _select_one()) for _ in range(5)]  # noqa: SLF001
    assert results == [{"value": 1}] * 5


def test_the_worker_engine_keeps_no_connections_between_sweeps(worker_sessions: None) -> None:
    celery_app._run("probe", _select_one())  # noqa: SLF001
    engine = celery_app._engine  # noqa: SLF001
    assert engine is not None
    assert isinstance(engine.pool, NullPool), "a pooled connection would be reused in another loop"
