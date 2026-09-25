"""Connection registry and Redis fan-out (B13, `architecture.md` section 4).

An API worker that assigns a trip is almost never the process holding the supervisor's
socket, so events travel worker -> Redis -> every hub -> the sockets that asked for that
channel. The hub keeps **one** Redis subscription per channel no matter how many local
sockets want it, and drops it when the last one leaves; a busy operator with forty
supervisors watching the map is still one subscription per feed.

Nothing here decides authorisation. `channels.py` does that before a connection is ever
added, and the socket re-checks on each event through the callback it registered.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
from collections.abc import Awaitable, Callable
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

#: How long to wait for a listener to accept a message before giving up on it. A client
#: on a bad connection must not hold up everyone else's updates.
SEND_TIMEOUT_SECONDS = 5.0

Listener = Callable[[dict[str, Any]], Awaitable[None]]


class Connection:
    """One WebSocket's view of the hub: the channels it holds and how to reach it."""

    def __init__(self, send: Listener) -> None:
        self.send = send
        self.channels: set[str] = set()


class Hub:
    """Local sockets plus the Redis subscription that feeds them."""

    def __init__(self, redis: Any | None = None) -> None:
        self._redis = redis
        self._by_channel: dict[str, set[Connection]] = {}
        self._pubsub: Any | None = None
        self._task: asyncio.Task[None] | None = None

    # --- membership -------------------------------------------------------------

    async def subscribe(self, connection: Connection, channel: str) -> None:
        listeners = self._by_channel.setdefault(channel, set())
        first = not listeners
        listeners.add(connection)
        connection.channels.add(channel)
        if first:
            await self._listen_to(channel)

    async def unsubscribe(self, connection: Connection, channel: str) -> None:
        listeners = self._by_channel.get(channel)
        if listeners is None:
            return
        listeners.discard(connection)
        connection.channels.discard(channel)
        if not listeners:
            del self._by_channel[channel]
            await self._stop_listening_to(channel)

    async def disconnect(self, connection: Connection) -> None:
        for channel in list(connection.channels):
            await self.unsubscribe(connection, channel)

    def listeners(self, channel: str) -> int:
        return len(self._by_channel.get(channel, ()))

    @property
    def channels(self) -> set[str]:
        return set(self._by_channel)

    # --- delivery ----------------------------------------------------------------

    async def deliver(self, channel: str, message: dict[str, Any]) -> int:
        """Send to every local socket on `channel`. Returns how many got it.

        One slow or dead socket must not stall the rest, so sends run concurrently and a
        failure only drops that connection.
        """
        listeners = list(self._by_channel.get(channel, ()))
        if not listeners:
            return 0

        results = await asyncio.gather(
            *(self._send_one(listener, message) for listener in listeners),
            return_exceptions=True,
        )
        return sum(1 for result in results if result is True)

    async def _send_one(self, connection: Connection, message: dict[str, Any]) -> bool:
        try:
            async with asyncio.timeout(SEND_TIMEOUT_SECONDS):
                await connection.send(message)
        except (TimeoutError, asyncio.CancelledError):
            logger.info("ws_send_timeout")
            return False
        except Exception as exc:  # noqa: BLE001 - one bad socket, not everyone's problem
            logger.info("ws_send_failed", error=type(exc).__name__)
            return False
        return True

    # --- Redis ------------------------------------------------------------------

    async def _listen_to(self, channel: str) -> None:
        if self._redis is None:
            return
        if self._pubsub is None:
            self._pubsub = self._redis.pubsub()
        await self._pubsub.subscribe(channel)
        if self._task is None:
            self._task = asyncio.create_task(self._pump())

    async def _stop_listening_to(self, channel: str) -> None:
        if self._pubsub is None:
            return
        with contextlib.suppress(Exception):
            await self._pubsub.unsubscribe(channel)

    async def _pump(self) -> None:
        """Read Redis forever and fan out. Survives a broker hiccup."""
        assert self._pubsub is not None
        while True:
            try:
                raw = await self._pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 - reconnecting beats dying
                logger.warning("ws_pubsub_read_failed", error=type(exc).__name__)
                await asyncio.sleep(1.0)
                continue

            if raw is None:
                continue
            channel = _as_text(raw.get("channel"))
            payload = _decode(raw.get("data"))
            if channel is not None and payload is not None:
                await self.deliver(channel, payload)

    async def close(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await self._task
            self._task = None
        if self._pubsub is not None:
            with contextlib.suppress(Exception):
                await self._pubsub.close()
            self._pubsub = None
        self._by_channel.clear()


def _as_text(value: object) -> str | None:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value if isinstance(value, str) else None


def _decode(value: object) -> dict[str, Any] | None:
    text = _as_text(value)
    if text is None:
        return None
    try:
        loaded = json.loads(text)
    except ValueError:
        logger.info("ws_bad_payload")
        return None
    return loaded if isinstance(loaded, dict) else None
