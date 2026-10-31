"""When is the optimizer "unavailable"? (`control-model.md` §6, B36)

> Optimizer/worker down -> scopes in `full_auto`/`semi_auto` behave as `manual`; alert shown.

§6 says what to do and not how anyone knows. Two things count, because there are two ways an
optimizer is down:

* **It runs and fails.** The solver raises, or the matrix cannot be built. Each attempt is
  recorded (`optimizer_run.status = failed`), so "down" is the last few attempts all failing,
  recently enough that the cause has plausibly not gone away.
* **It does not run at all.** The worker is dead or wedged, so there are no failed runs to
  count - there are no runs. What gives it away is a request that has been ready for far
  longer than the batch window while the newest run is just as old (or there is none).

Pure: the caller reads the runs and the queue, and this decides. A deployment cannot tell
"the optimizer is down" from "nobody has asked it anything", so an empty queue is always
healthy.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum


class Unavailable(StrEnum):
    solver_failing = "solver_failing"
    not_running = "not_running"


@dataclass(frozen=True, slots=True)
class HealthThresholds:
    #: This many most-recent runs all failing means the solver is down.
    failure_threshold: int = 3
    #: A failure older than this no longer says anything about now.
    failure_memory: timedelta = timedelta(minutes=15)
    #: A request ready for this long with no run since is waiting on a worker that is not there.
    stall: timedelta = timedelta(seconds=180)


@dataclass(frozen=True, slots=True)
class RunFact:
    started_at: datetime
    failed: bool


@dataclass(frozen=True, slots=True)
class Health:
    available: bool
    reason: Unavailable | None = None
    #: When the evidence began: the first of the failing runs, or when the oldest stalled
    #: request became ready. What the alert tells a supervisor.
    since: datetime | None = None


def assess(
    runs: list[RunFact],
    oldest_ready_at: datetime | None,
    now: datetime,
    thresholds: HealthThresholds,
    *,
    paused: bool = False,
) -> Health:
    """Is the optimizer usable right now?

    `runs` are the operator's recent runs, newest first. `oldest_ready_at` is when the
    longest-waiting ready request became ready, or `None` when nothing is waiting.

    An operator who has paused automation is **healthy by definition**: the optimizer is not
    supposed to be running, and reporting it down would raise an alert about the very switch
    the operator just pressed.
    """
    if paused:
        return Health(True)

    recent = runs[: thresholds.failure_threshold]
    if (
        len(recent) == thresholds.failure_threshold
        and all(run.failed for run in recent)
        and now - recent[0].started_at <= thresholds.failure_memory
    ):
        return Health(False, Unavailable.solver_failing, recent[-1].started_at)

    # A request ready for a long time while the optimizer has not been seen for a long time:
    # judged on the **newest run, not on whether one happened since the request became
    # ready**. The second form would call a healthy optimizer dead the moment an operator
    # resumed automation after a long pause (the queue is old; nothing has "run since"), and
    # would never notice a worker that died after a good run.
    if oldest_ready_at is not None and now - oldest_ready_at >= thresholds.stall:
        newest = runs[0].started_at if runs else None
        if newest is None or now - newest >= thresholds.stall:
            return Health(False, Unavailable.not_running, oldest_ready_at)

    return Health(True)
