"""Test doubles shared across the suite.

`FakeRedis` models one Redis *server*: hand the same instance to two provider objects and
you have two processes sharing a key space, which is how the cross-process rate limit is
tested without running Redis. Expiry is driven by the injected `Clock`, so the tests are
deterministic rather than sleep-based.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.clock import Clock


@dataclass
class _Entry:
    value: str
    expires_at_ms: float | None


@dataclass
class FakeRedis:
    """Enough of the Redis API for the cache and the rate limiter."""

    clock: Clock
    store: dict[str, _Entry] = field(default_factory=dict)
    fail_on: set[str] = field(default_factory=set)
    get_calls: int = 0
    set_calls: int = 0

    def _now_ms(self) -> float:
        return self.clock.now().timestamp() * 1000.0

    def _live(self, key: str) -> _Entry | None:
        entry = self.store.get(key)
        if entry is None:
            return None
        if entry.expires_at_ms is not None and self._now_ms() >= entry.expires_at_ms:
            del self.store[key]
            return None
        return entry

    async def get(self, name: str) -> Any:
        self.get_calls += 1
        if "get" in self.fail_on:
            raise ConnectionError("fake redis down")
        entry = self._live(name)
        return entry.value if entry else None

    async def set(
        self,
        name: str,
        value: str,
        *,
        nx: bool = False,
        px: int | None = None,
        ex: int | None = None,
    ) -> bool | None:
        self.set_calls += 1
        if "set" in self.fail_on:
            raise ConnectionError("fake redis down")
        if nx and self._live(name) is not None:
            return None  # redis-py returns None when NX finds an existing key

        expires: float | None = None
        if px is not None:
            expires = self._now_ms() + px
        elif ex is not None:
            expires = self._now_ms() + ex * 1000.0
        self.store[name] = _Entry(value=value, expires_at_ms=expires)
        return True
