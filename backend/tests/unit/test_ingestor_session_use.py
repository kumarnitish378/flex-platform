"""The ingestor's two writers - the message handler and the flush timer - never overlap.

Found by the load test (2026-11-03): both tasks used one `AsyncSession`, so a timer flush could
begin while the handler's commit was still in flight and the session raised "in 'prepared' state;
no further SQL can be emitted". The batch was rolled back and its pings were lost (3 in 751 at
five cabs; worse with more).
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest

from app.core.clock import FakeClock
from app.modules.tracking import ingestor as ingestor_module
from app.modules.tracking.service import GpsIngestor

NOW = datetime(2026, 11, 3, 6, 0, tzinfo=UTC)


class OverlapError(AssertionError):
    pass


class ExclusiveSession:
    """Fails the way a real AsyncSession does when two tasks use it at once."""

    def __init__(self) -> None:
        self.busy = False
        self.overlaps = 0
        self.rows = 0
        #: The first INSERT waits here, so the test decides when the timer's write finishes.
        self.gate = asyncio.Event()

    async def _use(self) -> None:
        if self.busy:
            self.overlaps += 1
            raise OverlapError("session used by two tasks at once")
        self.busy = True
        try:
            await asyncio.sleep(0.02)
        finally:
            self.busy = False

    async def execute(self, statement: Any, rows: list[dict[str, Any]]) -> None:
        await self.gate.wait()
        await self._use()
        self.rows += len(rows)

    async def flush(self) -> None:
        await self._use()

    async def commit(self) -> None:
        await self._use()

    async def rollback(self) -> None:
        self.busy = False


class SlowRedis:
    """Redis answers take time, as they do: that is when the timer can run mid-ping."""

    async def set(self, *args: Any, **kwargs: Any) -> None:
        await asyncio.sleep(0.003)

    async def publish(self, *args: Any, **kwargs: Any) -> None:
        await asyncio.sleep(0.003)


def message(operator: uuid.UUID, vehicle: uuid.UUID, second: int) -> Any:
    ping = {
        "v": 1,
        "ts": (NOW + timedelta(seconds=second)).isoformat(),
        "lat": 28.57 + second * 0.00001,
        "lng": 77.32,
        "spd": 5.0,
        "acc": 5.0,
        "src": "app",
    }
    return SimpleNamespace(
        topic=f"sc/v1/op/{operator}/veh/{vehicle}/gps", payload=json.dumps(ping).encode()
    )


async def test_the_timer_flush_and_the_handler_take_turns(monkeypatch: pytest.MonkeyPatch) -> None:
    """The timer's INSERT is in flight when a ping makes the handler's flush due.

    The handler waits for the write lock; the moment the timer's INSERT finishes, the lock is
    free and the timer goes on to commit - while the handler starts its own INSERT.
    """
    monkeypatch.setattr(ingestor_module, "FLUSH_INTERVAL_SECONDS", 0)
    session = ExclusiveSession()
    clock = FakeClock(NOW)
    ingestor = GpsIngestor(session, clock, None)  # type: ignore[arg-type]
    operator, vehicle = uuid.uuid4(), uuid.uuid4()
    stopping = asyncio.Event()

    await ingestor_module._handle(ingestor, message(operator, vehicle, 1))  # buffered, not due
    assert ingestor.pending == 1

    flusher = asyncio.create_task(ingestor_module._flush_loop(ingestor, session, stopping))
    await asyncio.sleep(0.1)  # the timer is now inside its INSERT, holding the write lock

    clock.advance(timedelta(seconds=6))  # the handler's own flush is due
    handler = asyncio.create_task(ingestor_module._handle(ingestor, message(operator, vehicle, 2)))
    await asyncio.sleep(0.1)  # ... and waiting for that lock

    session.gate.set()
    await handler
    stopping.set()
    await asyncio.gather(flusher, return_exceptions=True)
    await ingestor.flush()

    assert session.overlaps == 0, "the handler and the timer used the session at the same time"
    assert session.rows == 2, "a batch was lost to the failed write"
