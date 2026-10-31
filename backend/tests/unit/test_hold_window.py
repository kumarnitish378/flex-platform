"""The evening hold window, as pure arithmetic (B29, `allocation-rules.md` §6)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.enums import Direction, Urgency
from app.domain.hold_window import HoldExemption, HoldFacts, exemption, is_held, release_at

NOW = datetime(2026, 10, 16, 18, 0, tzinfo=UTC)
HOLD = 10


def facts(**overrides: object) -> HoldFacts:
    base: dict[str, object] = {
        "direction": Direction.from_office,
        "queued_at": NOW,
        "requested_time": NOW,
        "is_vip": False,
        "priority": 5,
        "urgency": Urgency.medium,
        "no_sharing": False,
        "forced_priority": False,
    }
    base.update(overrides)
    return HoldFacts(**base)  # type: ignore[arg-type]


def test_an_ordinary_evening_request_waits_the_minimum() -> None:
    assert release_at(facts(), HOLD) == NOW + timedelta(minutes=10)


def test_it_is_held_until_the_window_ends_and_free_at_the_instant_it_does() -> None:
    assert is_held(facts(), HOLD, NOW)
    assert is_held(facts(), HOLD, NOW + timedelta(minutes=9, seconds=59))
    assert not is_held(facts(), HOLD, NOW + timedelta(minutes=10))


def test_a_to_office_request_is_never_held() -> None:
    assert exemption(facts(direction=Direction.to_office), HOLD) is HoldExemption.not_from_office
    assert release_at(facts(direction=Direction.to_office), HOLD) is None


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"is_vip": True}, HoldExemption.vip),
        ({"priority": 2}, HoldExemption.high_priority),
        ({"priority": 1}, HoldExemption.high_priority),
        ({"urgency": Urgency.high}, HoldExemption.high_urgency),
        ({"no_sharing": True}, HoldExemption.no_sharing),
        ({"forced_priority": True}, HoldExemption.forced_priority),
    ],
)
def test_each_exemption_on_its_own_ends_the_hold(
    overrides: dict[str, object], reason: HoldExemption
) -> None:
    only_this = facts(**overrides)

    assert exemption(only_this, HOLD) is reason
    assert release_at(only_this, HOLD) is None
    assert not is_held(only_this, HOLD, NOW)


def test_priority_three_is_not_exempt() -> None:
    """The boundary: `priority <= 2` is high, 3 is not."""
    assert exemption(facts(priority=3), HOLD) is None


def test_a_zero_minimum_means_no_window_at_all() -> None:
    assert exemption(facts(), 0) is HoldExemption.no_window
    assert not is_held(facts(), 0, NOW)


def test_the_window_runs_from_when_the_rider_will_be_ready() -> None:
    """A request typed at nine for six o'clock is not held from nine."""
    ready = NOW + timedelta(hours=9)
    early = facts(queued_at=NOW, requested_time=ready)

    assert release_at(early, HOLD) == ready + timedelta(minutes=10)
    assert is_held(early, HOLD, ready + timedelta(minutes=5))


def test_a_request_asked_late_is_held_from_when_it_was_asked() -> None:
    late = facts(queued_at=NOW + timedelta(minutes=3), requested_time=NOW)

    assert release_at(late, HOLD) == NOW + timedelta(minutes=13)
