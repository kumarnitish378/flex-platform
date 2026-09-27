"""`/simctl/*` — simulator control (B19, ADR-0008).

**Mounted only when `APP_ENV=sim`.** Not guarded by a feature flag inside the handler:
the router is never added to the app at all, so in dev, staging and prod these paths 404
because they genuinely do not exist. A flag could be flipped by a stray environment
variable; a route that was never registered cannot be.

The endpoints are `public_route()` for the same reason, and one more: `/simctl/reset`
creates the users, so there is nobody to authenticate as before it runs. That is only
acceptable because the whole environment is a sandbox that cannot exist in production —
`Settings` refuses `SIMCTL_ENABLED` outside `APP_ENV=sim`.
"""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Request

from app.core.clock import SIM_CLOCK_KEY, FakeClock
from app.core.dependencies import ClockDep, SessionDep
from app.core.logging import get_logger
from app.domain.errors import Conflict, ValidationFailed
from app.modules.alerts.service import AlertService
from app.modules.auth.dependencies import public_route
from app.modules.dispatch.eta_refresh import EtaRefresher
from app.modules.requests.service import RideRequestService
from app.modules.simctl.schemas import (
    ReleaseRequest,
    ResetRequest,
    ResetResult,
    SimClockState,
    SimClockUpdate,
)
from app.modules.simctl.service import SimControlService

logger = get_logger(__name__)

router = APIRouter(tags=["simctl"])


def _fake_clock(clock: ClockDep) -> FakeClock:
    if not isinstance(clock, FakeClock):
        raise ValidationFailed(
            "Sim control needs a controllable clock; this process has a real one"
        )
    return clock


@router.get(
    "/simctl/clock",
    summary="Current sim time",
    dependencies=[Depends(public_route())],
)
async def get_clock(clock: ClockDep) -> SimClockState:
    return SimClockState(now=clock.now())


@router.put(
    "/simctl/clock",
    summary="Set or advance sim time (APP_ENV=sim only; 404 otherwise)",
    dependencies=[Depends(public_route())],
)
async def set_clock(
    body: SimClockUpdate, request: Request, session: SessionDep, clock: ClockDep
) -> SimClockState:
    """Move the clock, then run everything that just became due.

    Running due work *synchronously* before returning is what makes the simulator
    deterministic: when the PUT comes back, every expiry the jump should have triggered
    has already happened, so the next assertion cannot race a background worker
    (`simulator-spec.md` §3).
    """
    fake = _fake_clock(clock)

    if body.now is not None and body.advance_seconds is not None:
        raise ValidationFailed("Send either now or advance_seconds, not both")
    if body.now is None and body.advance_seconds is None:
        raise ValidationFailed("Send now or advance_seconds")

    if body.now is not None:
        if body.now.tzinfo is None:
            raise ValidationFailed("now must include a timezone")
        fake.set(body.now)
    else:
        seconds = body.advance_seconds or 0
        if seconds < 0:
            raise ValidationFailed("advance_seconds cannot be negative")
        fake.advance(timedelta(seconds=seconds))

    # Publish the new time so processes outside the API - the ingestor - validate against
    # simulated time rather than wall time (`app/core/clock.py`, SharedSimClock).
    await _publish_sim_clock(request, fake.now())

    sweep = await RideRequestService(session, fake).run_due_expiries()
    # The ETA worker is due work too, not a background timer, so a clock jump refreshes
    # stop ETAs before returning (`architecture.md` section 3.2 step 4).
    refreshed = await EtaRefresher(session, fake, request.app.state.eta).refresh_due()
    stale = await AlertService(session, fake).sweep_stale_vehicles()
    return SimClockState(
        now=fake.now(),
        expired=sweep.expired,
        near_expiry_alerts=sweep.warned,
        stop_etas_refreshed=refreshed.stops,
        stale_vehicle_alerts=stale.raised,
    )


@router.post(
    "/simctl/reset",
    summary="Truncate operator data and load the seed fixture",
    dependencies=[Depends(public_route())],
)
async def reset(
    body: ResetRequest, request: Request, session: SessionDep, clock: ClockDep
) -> ResetResult:
    fake = _fake_clock(clock)
    if body.scenario_yaml:
        # Seeding from an arbitrary scenario means reimplementing the simulator's
        # loader inside the backend. Failing loudly beats half-honouring the field.
        raise ValidationFailed(
            "scenario_yaml is not supported yet; reset loads the fixed NCR fixture "
            "from testing-strategy.md section 4. Shape the run from the scenario file "
            "on the simulator side."
        )

    await _claim_the_backend(request, body.run_id, force=body.force)

    settings = request.app.state.settings
    service = SimControlService(session, fake, settings)
    if body.start_time is not None:
        fake.set(body.start_time if body.start_time.tzinfo else body.start_time.replace(tzinfo=UTC))

    return await service.reset(
        employees=body.employees,
        vehicles=body.vehicles,
        vip_employees=body.vip_employees,
        fleet=[(group.type, group.count) for group in body.fleet] if body.fleet else None,
    )


#: Who is currently driving this backend, and for how long the claim stands without
#: being renewed. Two hours covers the longest scenario the suite runs; a crashed run
#: releases the backend on its own rather than needing a human to clear a stale lock.
SIM_RUN_KEY = "sim:run"
SIM_RUN_TTL_SECONDS = 2 * 3600


async def _claim_the_backend(request: Request, run_id: str | None, *, force: bool) -> None:
    """Refuse to reset a backend another run is in the middle of using.

    A `reset` truncates every table, so a second run starting against the same backend
    silently destroys the first one's world - the first run then fails somewhere much
    later with an error that says nothing about the real cause. This turns hours of
    confusing wreckage into one clear 409.
    """
    redis = getattr(request.app.state, "redis", None)
    if redis is None or run_id is None:
        return

    # SET NX, not GET-then-SET. Two suites started in the same instant both read "no
    # owner" and both claimed, which is exactly the collision the claim exists to stop -
    # and it happened, racing two full suites against one backend.
    try:
        if force:
            await redis.set(SIM_RUN_KEY, run_id, ex=SIM_RUN_TTL_SECONDS)
            return
        claimed = await redis.set(SIM_RUN_KEY, run_id, nx=True, ex=SIM_RUN_TTL_SECONDS)
    except Exception:  # noqa: BLE001 - a missing Redis must not block a reset
        return

    if claimed:
        return

    owner = None
    with contextlib.suppress(Exception):
        owner = await redis.get(SIM_RUN_KEY)
    current = owner.decode() if isinstance(owner, bytes) else owner

    if current == run_id:
        # Already ours: a suite resets once per scenario under one claim.
        with contextlib.suppress(Exception):
            await redis.expire(SIM_RUN_KEY, SIM_RUN_TTL_SECONDS)
        return

    raise Conflict(
        f"run {current} is using this backend; resetting would destroy its world. "
        f"Wait for it, or pass force=true to take over.",
        {"owner": current, "requested_by": run_id},
    )


async def _renew_the_claim(request: Request) -> None:
    """Keep the claim alive while a run is still pushing its clock forward."""
    redis = getattr(request.app.state, "redis", None)
    if redis is None:
        return
    with contextlib.suppress(Exception):
        await redis.expire(SIM_RUN_KEY, SIM_RUN_TTL_SECONDS)


@router.post(
    "/simctl/release",
    summary="Give up this run's claim on the backend so another can start",
    dependencies=[Depends(public_route())],
)
async def release(body: ReleaseRequest, request: Request) -> dict[str, bool]:
    """Free the backend as soon as a run finishes.

    Without this the claim sits until its TTL expires, and the next run - often the same
    developer, seconds later - is refused by a run that is no longer there. The TTL is
    the fallback for a crash, not the normal way a claim ends.
    """
    redis = getattr(request.app.state, "redis", None)
    if redis is None:
        return {"released": False}

    try:
        owner = await redis.get(SIM_RUN_KEY)
    except Exception:  # noqa: BLE001
        return {"released": False}

    current = owner.decode() if isinstance(owner, bytes) else owner
    # Only the holder may release, or a crashed run's successor could free a claim that
    # a live run is still relying on.
    if current and current != body.run_id:
        return {"released": False}

    with contextlib.suppress(Exception):
        await redis.delete(SIM_RUN_KEY)
    return {"released": True}


def sim_epoch() -> datetime:
    return datetime(2026, 1, 1, tzinfo=UTC)


async def _publish_sim_clock(request: Request, now: datetime) -> None:
    """Best-effort: a clock nobody can read is better than a 500 on a clock jump."""
    await _renew_the_claim(request)
    redis = getattr(request.app.state, "redis", None)
    if redis is None:
        return
    try:
        await redis.set(SIM_CLOCK_KEY, now.isoformat())
    except Exception:  # noqa: BLE001
        logger.warning("sim_clock_publish_failed")
