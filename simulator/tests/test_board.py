"""The shared status board (OQ-26).

Exists because three hundred riders each polling their own request measured the harness
rather than the platform, and blocked the simulation while doing it.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest

from sim.board import ALL_STATUSES, REFRESH_INTERVAL_SECONDS, StatusBoard
from sim.engine import Engine
from sim.scenario import load_scenario

SCENARIOS = Path(__file__).resolve().parent.parent / "scenarios"


class FakeBoardSource:
    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self.rows = rows if rows is not None else []
        self.calls = 0
        self.asked_for: list[Any] = []
        self.fail = False

    def pending_requests(
        self, token: str, status: str = "queued", statuses: Any = None
    ) -> list[dict[str, Any]]:
        if self.fail:
            raise RuntimeError("backend said no")
        self.calls += 1
        self.asked_for.append(statuses)
        return self.rows

    def set_clock(self, now: Any) -> Any:
        return now


@pytest.fixture
def engine() -> Engine:
    return Engine(load_scenario(SCENARIOS / "smoke_tiny.yaml"))


def board_for(engine: Engine, source: FakeBoardSource) -> StatusBoard:
    engine.platform = source  # type: ignore[assignment]
    board = StatusBoard(engine, token="supervisor-token")
    engine.board = board
    return board


def row(request_id: uuid.UUID, status: str) -> dict[str, Any]:
    return {"id": str(request_id), "status": status}


def test_one_call_serves_every_rider(engine: Engine) -> None:
    """The whole point: one read, not one per rider."""
    ids = [uuid.uuid4() for _ in range(300)]
    source = FakeBoardSource([row(request_id, "queued") for request_id in ids])
    board = board_for(engine, source)

    board.refresh()

    assert source.calls == 1
    assert all(board.status_of(request_id) == "queued" for request_id in ids)


def test_it_asks_for_every_status(engine: Engine) -> None:
    """The board's default is the open ones, and a finished ride would simply vanish.

    Without this the simulator could not tell "dropped" from "expired", which is most of
    what it measures.
    """
    source = FakeBoardSource()
    board_for(engine, source).refresh()

    assert set(source.asked_for[0]) == set(ALL_STATUSES)
    for terminal in ("dropped", "cancelled", "expired", "no_show"):
        assert terminal in source.asked_for[0]


def test_an_unseen_request_is_unknown_not_finished(engine: Engine) -> None:
    """A request created since the last refresh must not be read as a completed ride."""
    board = board_for(engine, FakeBoardSource())
    board.refresh()

    assert board.status_of(uuid.uuid4()) is None


def test_a_caller_can_record_what_it_already_knows(engine: Engine) -> None:
    """A rider who just cancelled knows better than a board a minute stale."""
    request_id = uuid.uuid4()
    board = board_for(engine, FakeBoardSource([row(request_id, "queued")]))
    board.refresh()

    board.note(request_id, "cancelled")
    assert board.status_of(request_id) == "cancelled"


def test_a_refresh_replaces_the_previous_view(engine: Engine) -> None:
    request_id = uuid.uuid4()
    source = FakeBoardSource([row(request_id, "queued")])
    board = board_for(engine, source)
    board.refresh()

    source.rows = [row(request_id, "assigned")]
    board.refresh()

    assert board.status_of(request_id) == "assigned"


def test_a_failed_read_keeps_the_previous_view(engine: Engine) -> None:
    """A stale board beats a dead run, and beats every rider suddenly seeing nothing."""
    request_id = uuid.uuid4()
    source = FakeBoardSource([row(request_id, "assigned")])
    board = board_for(engine, source)
    board.refresh()

    source.fail = True
    board.refresh()

    assert board.status_of(request_id) == "assigned"
    assert board.errors == 1


def test_it_refreshes_on_a_timer(engine: Engine) -> None:
    source = FakeBoardSource()
    board = board_for(engine, source)
    engine.spawn(board.watch)

    engine.run()

    expected = engine.duration_seconds / REFRESH_INTERVAL_SECONDS
    assert source.calls == pytest.approx(expected, abs=2)


def test_it_does_nothing_without_a_platform(engine: Engine) -> None:
    board = StatusBoard(engine, token="t")

    board.refresh()

    assert board.refreshes == 0
    assert board.errors == 0
