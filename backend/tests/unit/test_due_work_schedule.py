"""Every sweep that must run on its own actually has a schedule (B20).

Until B20 the expiry sweep, the stop-ETA refresher and the stale-vehicle sweep had
exactly one caller between them: `PUT /simctl/clock`, which is mounted only when
`APP_ENV=sim` (ADR-0008). Deployed, the platform did not expire requests, warn about a
request about to expire, escalate a request nobody had served, refresh a stop ETA, or
alert on a cab that had gone quiet.

Nothing failed, which is exactly the problem: all of it is work that is supposed to
happen on its own, so its absence looks like a quiet morning. This test is the guard -
if a new sweep is added to the sim endpoint and not to the beat, it fails here.
"""

from __future__ import annotations

import re
from pathlib import Path

from app.workers.celery_app import (
    EXPIRY_INTERVAL_SECONDS,
    STALE_VEHICLE_INTERVAL_SECONDS,
    STOP_ETA_INTERVAL_SECONDS,
    celery_app,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
SIMCTL_ROUTER = REPO_ROOT / "backend" / "app" / "modules" / "simctl" / "router.py"

#: The service calls that make up "due work", and the task that must run each one.
#:
#: Keyed by the method name as it appears in the sim endpoint, because that endpoint is
#: the other - and previously only - caller. Any sweep reachable from a clock jump has
#: to be reachable from the beat too, or it works in a scenario and not in production.
DUE_WORK: dict[str, str] = {
    "run_due_expiries": "smart_cab.expire_requests",
    "refresh_due": "smart_cab.refresh_stop_etas",
    "sweep_stale_vehicles": "smart_cab.sweep_stale_vehicles",
}


def scheduled_tasks() -> set[str]:
    return {entry["task"] for entry in celery_app.conf.beat_schedule.values()}


def test_every_due_work_sweep_is_scheduled() -> None:
    missing = {task for task in DUE_WORK.values()} - scheduled_tasks()

    assert not missing, (
        f"these tasks exist but nothing schedules them: {sorted(missing)}. "
        "A sweep with no schedule runs only in the simulator."
    )


def test_every_sweep_the_sim_endpoint_runs_has_a_task() -> None:
    """The sim endpoint is the list of what counts as due work.

    If somebody adds a fourth sweep to a clock jump, this fails until it is scheduled -
    which is the whole failure mode B20 existed to fix, caught at the source.
    """
    source = SIMCTL_ROUTER.read_text(encoding="utf-8")
    called = {name for name in re.findall(r"await \w+\([^)]*\)\.(\w+)\(", source)}
    # Only the sweeps, not the seeding and claim helpers the endpoint also uses.
    sweeps = {name for name in called if name in DUE_WORK or name.startswith(("run_due", "sweep_"))}

    assert sweeps, "found no sweeps in the sim endpoint; this guard would pass vacuously"
    unscheduled = {name for name in sweeps if name not in DUE_WORK}
    assert not unscheduled, (
        f"the sim endpoint runs {sorted(unscheduled)} and the beat does not. "
        "Add a task in app/workers/celery_app.py and name it in DUE_WORK."
    )


def test_every_task_is_registered_with_celery() -> None:
    """A beat entry naming a task that does not exist fails silently at runtime."""
    for task in scheduled_tasks():
        assert task in celery_app.tasks, f"{task} is scheduled but not registered"


def test_the_intervals_are_finer_than_what_depends_on_them() -> None:
    # A rider watching a cab approach notices a stale ETA immediately, which is why B15
    # specifies 30 seconds.
    assert STOP_ETA_INTERVAL_SECONDS == 30

    # Half of `stale_gps_seconds` (60), so a cab that goes quiet is noticed within one
    # interval of crossing the line rather than two.
    assert STALE_VEHICLE_INTERVAL_SECONDS * 2 <= 60

    # The near-expiry warning fires 15 minutes before expiry, so a minute of granularity
    # is far finer than anything that depends on it.
    assert EXPIRY_INTERVAL_SECONDS <= 60


def test_utc_everywhere() -> None:
    """`non-functional.md`: timestamps are UTC. A beat on local time would drift twice a
    year in any timezone that observes daylight saving."""
    assert celery_app.conf.timezone == "UTC"
    assert celery_app.conf.enable_utc is True
