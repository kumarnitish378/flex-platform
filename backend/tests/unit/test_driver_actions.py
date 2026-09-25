"""When a driver's tap is believable (B15, DRV-05).

Pure, and the reason it exists is `coding-standards.md` section 5: the app queues taps
offline, so `occurred_at` comes from a phone we do not control.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.driver_actions import (
    MAX_AGE,
    MAX_FUTURE,
    StopAction,
    check_occurred_at,
    effective_time,
)

NOW = datetime(2026, 9, 25, 18, 0, tzinfo=UTC)


def test_a_tap_just_now_is_fine() -> None:
    assert check_occurred_at(NOW, NOW) is None


def test_a_tap_from_an_hour_ago_is_fine() -> None:
    """The whole point of the offline queue: late is normal, not suspicious."""
    assert check_occurred_at(NOW - timedelta(hours=1), NOW) is None


def test_a_tap_from_the_far_future_is_refused() -> None:
    bad = check_occurred_at(NOW + MAX_FUTURE + timedelta(seconds=1), NOW)
    assert bad is not None
    assert bad.reason == "future_timestamp"


def test_small_clock_skew_is_tolerated() -> None:
    """A phone three seconds fast is a phone, not a forgery."""
    assert check_occurred_at(NOW + timedelta(seconds=3), NOW) is None


def test_a_tap_older_than_a_day_is_refused() -> None:
    bad = check_occurred_at(NOW - MAX_AGE - timedelta(seconds=1), NOW)
    assert bad is not None
    assert bad.reason == "stale_timestamp"


def test_a_naive_timestamp_is_refused() -> None:
    """Guessing a zone would shift a whole trip's timeline by hours."""
    bad = check_occurred_at(datetime(2026, 9, 25, 18, 0), NOW)
    assert bad is not None
    assert bad.reason == "naive_timestamp"


def test_a_future_tap_is_recorded_as_now() -> None:
    assert effective_time(NOW + timedelta(seconds=3), NOW) == NOW


def test_a_past_tap_keeps_its_own_time() -> None:
    """A trip that finished at 18:04 must not be recorded as finishing at 19:30."""
    tapped = NOW - timedelta(minutes=86)
    assert effective_time(tapped, NOW) == tapped


@pytest.mark.parametrize("action", ["arrived", "done", "no_show"])
def test_every_action_in_the_api_spec_exists(action: str) -> None:
    assert StopAction(action)


def test_no_other_action_exists() -> None:
    with pytest.raises(ValueError, match="cancelled"):
        StopAction("cancelled")
