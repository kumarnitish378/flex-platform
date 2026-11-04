"""A realtime event goes out only after the data it announces is committed.

Found by the load test (2026-11-03): a rider's phone received `request.assigned`, fetched the
request at once and still saw it `queued`, because the handler published to Redis before the
session was committed. A client reacting to an event must be able to trust a read that follows it.
"""

from __future__ import annotations

import asyncio
from collections.abc import MutableMapping
from typing import Any

from fastapi import FastAPI, HTTPException

from app.core.dependencies import EventsDep, SessionDep
from app.core.events import Event


class _Session:
    def __init__(self, log: list[str]) -> None:
        self.log = log

    async def commit(self) -> None:
        self.log.append("commit")

    async def rollback(self) -> None:
        self.log.append("rollback")


class _Factory:
    def __init__(self, log: list[str]) -> None:
        self.log = log

    def __call__(self) -> Any:
        log = self.log

        class _Ctx:
            async def __aenter__(self) -> _Session:
                return _Session(log)

            async def __aexit__(self, *exc_info: object) -> None:
                return None

        return _Ctx()


class _Publisher:
    def __init__(self, log: list[str]) -> None:
        self.log = log

    async def publish(self, event: Event) -> None:
        self.log.append(f"publish:{event.name}")


def _app(log: list[str]) -> FastAPI:
    app = FastAPI()
    app.state.session_factory = _Factory(log)
    app.state.events = _Publisher(log)

    @app.post("/session-first")
    async def session_first(session: SessionDep, events: EventsDep) -> dict[str, bool]:
        log.append("handler")
        await events.publish(Event("request.assigned", "user.1"))
        return {"ok": True}

    @app.post("/events-first")
    async def events_first(events: EventsDep, session: SessionDep) -> dict[str, bool]:
        log.append("handler")
        await events.publish(Event("request.assigned", "user.1"))
        return {"ok": True}

    @app.post("/no-session")
    async def no_session(events: EventsDep) -> dict[str, bool]:
        log.append("handler")
        await events.publish(Event("alert.raised", "operator.1.alerts"))
        return {"ok": True}

    @app.post("/fails")
    async def fails(session: SessionDep, events: EventsDep) -> None:
        await events.publish(Event("request.assigned", "user.1"))
        raise HTTPException(status_code=409, detail="no")

    @app.post("/two")
    async def two(session: SessionDep, events: EventsDep) -> dict[str, bool]:
        await events.publish(Event("a", "c"))
        await events.publish(Event("b", "c"))
        return {"ok": True}

    return app


async def _call(app: FastAPI, path: str, log: list[str]) -> None:
    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: MutableMapping[str, Any]) -> None:
        if message["type"] == "http.response.start":
            log.append("response_start")

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [],
        "server": ("test", 80),
        "client": ("test", 1),
        "scheme": "http",
        "root_path": "",
    }
    await app(scope, receive, send)


def run(path: str) -> list[str]:
    log: list[str] = []
    asyncio.run(_call(_app(log), path, log))
    return log


def test_the_event_follows_the_commit_whichever_dependency_is_listed_first() -> None:
    expected = ["handler", "commit", "publish:request.assigned", "response_start"]
    assert run("/session-first") == expected
    assert run("/events-first") == expected


def test_a_route_with_no_session_publishes_when_it_finishes() -> None:
    assert run("/no-session") == ["handler", "publish:alert.raised", "response_start"]


def test_a_failed_request_publishes_nothing() -> None:
    log = run("/fails")
    assert "publish:request.assigned" not in log
    assert "rollback" in log
    assert "commit" not in log


def test_events_keep_the_order_they_were_published_in() -> None:
    assert run("/two") == ["commit", "publish:a", "publish:b", "response_start"]
