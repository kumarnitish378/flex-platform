"""A request's writes are committed before the client is told it succeeded.

Found by the end-to-end smoke test: a supervisor confirmed a night escort, got a 200, and the
driver's start - sent immediately - was still refused, because the session was committed in the
dependency's exit code, which FastAPI runs *after* the response has been sent unless the dependency
has `scope="function"`.
"""

from __future__ import annotations

import asyncio
from collections.abc import MutableMapping
from typing import Any

from fastapi import FastAPI

from app.core.dependencies import SessionDep


class _Session:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    async def commit(self) -> None:
        self.events.append("commit")

    async def rollback(self) -> None:
        self.events.append("rollback")


class _Factory:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def __call__(self) -> Any:
        events = self.events

        class _Ctx:
            async def __aenter__(self) -> _Session:
                return _Session(events)

            async def __aexit__(self, *exc_info: object) -> None:
                return None

        return _Ctx()


def _app(events: list[str]) -> FastAPI:
    app = FastAPI()
    app.state.session_factory = _Factory(events)

    @app.post("/write")
    async def write(session: SessionDep) -> dict[str, bool]:
        events.append("handler")
        return {"ok": True}

    return app


async def _call(app: FastAPI, events: list[str]) -> None:
    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: MutableMapping[str, Any]) -> None:
        if message["type"] == "http.response.start":
            events.append("response_start")

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "path": "/write",
        "raw_path": b"/write",
        "query_string": b"",
        "headers": [],
        "server": ("test", 80),
        "client": ("test", 1),
        "scheme": "http",
        "root_path": "",
    }
    await app(scope, receive, send)


def test_the_commit_lands_before_the_response_is_sent() -> None:
    events: list[str] = []

    asyncio.run(_call(_app(events), events))

    assert events == ["handler", "commit", "response_start"]
