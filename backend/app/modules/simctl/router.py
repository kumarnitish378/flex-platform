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

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Request

from app.core.clock import FakeClock
from app.core.dependencies import ClockDep, SessionDep
from app.domain.errors import ValidationFailed
from app.modules.auth.dependencies import public_route
from app.modules.dispatch.eta_refresh import EtaRefresher
from app.modules.requests.service import RideRequestService
from app.modules.simctl.schemas import ResetRequest, ResetResult, SimClockState, SimClockUpdate
from app.modules.simctl.service import SimControlService

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

    sweep = await RideRequestService(session, fake).run_due_expiries()
    # The ETA worker is due work too, not a background timer, so a clock jump refreshes
    # stop ETAs before returning (`architecture.md` section 3.2 step 4).
    refreshed = await EtaRefresher(session, fake, request.app.state.eta).refresh_due()
    return SimClockState(
        now=fake.now(),
        expired=sweep.expired,
        near_expiry_alerts=sweep.warned,
        stop_etas_refreshed=refreshed.stops,
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

    settings = request.app.state.settings
    service = SimControlService(session, fake, settings)
    if body.start_time is not None:
        fake.set(body.start_time if body.start_time.tzinfo else body.start_time.replace(tzinfo=UTC))

    return await service.reset()


def sim_epoch() -> datetime:
    return datetime(2026, 1, 1, tzinfo=UTC)
