"""One shared read of the request board (OQ-26).

Three hundred rider agents each polling `GET /ride-requests/{id}` is three hundred HTTP
calls per simulated minute, and because the simulator's platform client is synchronous
inside a single-threaded SimPy loop, every one of them blocks the whole simulation. S02
ran at about 6x real time instead of the 60x it asks for, which made a 16-hour scenario
take most of a day.

This replaces that with **one** call per interval: the operator's own board, which lists
every request with its status, refreshed on a timer and read from memory.

What this does and does not change:

* Riders still **act** through their own accounts - creating and cancelling a ride goes
  through the rider's token, exactly as the app does, and those are the calls the product
  is being tested on.
* Only the *observation* of status is shared. A rider polling its own request measures
  the harness, not the platform, and three hundred of them measure it three hundred times.
"""

from __future__ import annotations

import uuid
from collections.abc import Generator
from typing import TYPE_CHECKING, Any

import simpy

if TYPE_CHECKING:
    from sim.engine import Engine

Process = Generator[simpy.Event, Any, Any]

#: How often to re-read the board, in simulated seconds. Patience is measured in tens of
#: minutes, so a minute of staleness changes no decision an agent makes.
REFRESH_INTERVAL_SECONDS = 60

#: Every status a request can hold. Asked for explicitly because the board's default is
#: the *open* ones, and a rider whose ride finished would simply vanish - leaving the
#: simulator unable to tell "dropped" from "expired", which is most of what it measures.
ALL_STATUSES = (
    "requested",
    "queued",
    "suggested",
    "assigned",
    "picked_up",
    "dropped",
    "no_show",
    "cancelled",
    "expired",
)


class StatusBoard:
    """The operator's request board, refreshed on a timer and read by every rider."""

    def __init__(self, engine: Engine, token: str) -> None:
        self.engine = engine
        self.token = token
        self.refreshes = 0
        self.errors = 0
        self._status: dict[uuid.UUID, str] = {}

    def status_of(self, request_id: uuid.UUID) -> str | None:
        """The last status seen for this request, or `None` if it is not on the board yet.

        `None` is not "gone": a request created a moment ago may simply predate the last
        refresh, and treating that as terminal would report rides that never happened.
        """
        return self._status.get(request_id)

    def note(self, request_id: uuid.UUID, status: str) -> None:
        """Record a status the caller already knows, so it need not wait for a refresh."""
        self._status[request_id] = status

    def refresh(self) -> None:
        platform = self.engine.platform
        if platform is None:
            return
        try:
            rows = platform.pending_requests(self.token, statuses=ALL_STATUSES)
        except Exception as exc:  # noqa: BLE001 - a stale board beats a dead run
            self.errors += 1
            self.engine.record(f"status board refresh failed: {type(exc).__name__}: {exc}")
            return

        self.refreshes += 1
        self._status = {uuid.UUID(row["id"]): str(row["status"]) for row in rows}

    def watch(self) -> Process:
        """Keep the board current for the life of the run."""
        while True:
            self.refresh()
            yield self.engine.env.timeout(REFRESH_INTERVAL_SECONDS)
