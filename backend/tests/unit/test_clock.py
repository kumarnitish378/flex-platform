"""Clock behaviour and — the acceptance criterion for B01 — that it is injectable."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest
from fastapi import FastAPI

from app.core.clock import Clock, FakeClock, SystemClock
from app.core.settings import Settings
from app.main import create_app

NOW = datetime(2026, 9, 24, 4, 30, tzinfo=UTC)


def test_system_clock_returns_timezone_aware_utc() -> None:
    moment = SystemClock().now()
    assert moment.tzinfo is not None
    assert moment.utcoffset() == timedelta(0)


def test_both_clocks_satisfy_the_protocol() -> None:
    assert isinstance(SystemClock(), Clock)
    assert isinstance(FakeClock(NOW), Clock)


def test_fake_clock_does_not_move_on_its_own() -> None:
    clock = FakeClock(NOW)
    assert clock.now() == NOW
    assert clock.now() == NOW


def test_fake_clock_advances() -> None:
    clock = FakeClock(NOW)
    returned = clock.advance(timedelta(minutes=15))
    assert returned == NOW + timedelta(minutes=15)
    assert clock.now() == NOW + timedelta(minutes=15)


def test_fake_clock_set_can_move_backwards_for_scenario_reset() -> None:
    clock = FakeClock(NOW)
    clock.set(NOW - timedelta(days=1))
    assert clock.now() == NOW - timedelta(days=1)


def test_fake_clock_refuses_to_advance_backwards() -> None:
    clock = FakeClock(NOW)
    with pytest.raises(ValueError, match="moves forward"):
        clock.advance(timedelta(seconds=-1))


def test_naive_datetimes_are_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        FakeClock(datetime(2026, 9, 24, 4, 30))  # noqa: DTZ001 - the point of the test


def test_non_utc_input_is_normalised_to_utc() -> None:
    ist = timezone(timedelta(hours=5, minutes=30))
    clock = FakeClock(datetime(2026, 9, 24, 10, 0, tzinfo=ist))
    assert clock.now() == datetime(2026, 9, 24, 4, 30, tzinfo=UTC)
    assert clock.now().utcoffset() == timedelta(0)


def test_fake_clock_is_injectable_into_the_app() -> None:
    """B01 acceptance: the app can be built with a controllable clock.

    This is what lets the simulator drive backend time through /simctl/clock.
    """
    clock = FakeClock(NOW)
    app: FastAPI = create_app(
        settings=Settings(
            app_env="dev",
            database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        ),
        clock=clock,
    )

    injected: Clock = app.state.clock
    assert injected is clock
    assert injected.now() == NOW

    clock.advance(timedelta(hours=2))
    assert app.state.clock.now() == NOW + timedelta(hours=2)


def test_sim_environment_gets_a_fake_clock_by_default() -> None:
    app = create_app(
        settings=Settings(
            app_env="sim",
            simctl_enabled=True,
            database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        )
    )
    assert isinstance(app.state.clock, FakeClock)


def test_dev_environment_gets_the_system_clock_by_default() -> None:
    app = create_app(
        settings=Settings(
            app_env="dev",
            database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        )
    )
    assert isinstance(app.state.clock, SystemClock)


# --- tokens follow the injected clock too -------------------------------------------


def test_a_token_minted_ahead_of_wall_clock_time_is_accepted() -> None:
    """The simulator runs its clock ahead of real time; tokens must still work.

    PyJWT validates `iat` and `nbf` against the real system clock by default, which
    rejects every token an accelerated `SimClock` mints with "not yet valid". All time
    checks belong to the injected clock (CLAUDE.md hard rule 2).
    """
    import uuid
    from datetime import UTC, datetime

    from app.core.security import create_access_token, decode_access_token

    far_future = FakeClock(datetime(2099, 1, 1, tzinfo=UTC))
    secret = "clock-tests-secret-0123456789abcdef"
    token, _ = create_access_token(
        user_id=uuid.uuid4(),
        role="supervisor",
        secret=secret,
        clock=far_future,
        ttl_seconds=900,
    )

    assert decode_access_token(token, secret, far_future).role == "supervisor"


def test_expiry_is_still_judged_by_the_injected_clock() -> None:
    """Turning off PyJWT's checks must not turn off expiry."""
    import uuid
    from datetime import UTC, datetime, timedelta

    from app.core.security import InvalidTokenError, create_access_token, decode_access_token

    clock = FakeClock(datetime(2099, 1, 1, tzinfo=UTC))
    secret = "clock-tests-secret-0123456789abcdef"
    token, _ = create_access_token(
        user_id=uuid.uuid4(), role="supervisor", secret=secret, clock=clock, ttl_seconds=900
    )

    clock.advance(timedelta(minutes=16))
    with pytest.raises(InvalidTokenError):
        decode_access_token(token, secret, clock)
