"""Rule 11: nobody flagged is left alone at either end of a night trip (B28)."""

from __future__ import annotations

import uuid
from datetime import time

import pytest

from app.domain.enums import Direction
from app.domain.night_safety import (
    NightPosition,
    breaches_night_safety,
    exposed_riders,
    in_night_window,
    lone_positions,
)

ASHA = uuid.UUID(int=1)
RAHUL = uuid.UUID(int=2)
PRIYA = uuid.UUID(int=3)

NIGHT = time(22, 30)
DAY = time(14, 0)


def breach(**overrides: object) -> bool:
    kwargs: dict[str, object] = {
        "direction": Direction.to_office,
        "order": [ASHA, RAHUL],
        "flagged": [ASHA],
        "at": NIGHT,
        "enabled": True,
        "night_start": time(20, 0),
        "night_end": time(6, 0),
    }
    kwargs.update(overrides)
    return breaches_night_safety(**kwargs)  # type: ignore[arg-type]


# --- the window ------------------------------------------------------------------


def test_a_night_window_crosses_midnight() -> None:
    """`start <= at <= end` is empty for every real night window, which is the bug
    this test exists to catch."""
    start, end = time(20, 0), time(6, 0)
    assert in_night_window(time(23, 59), start, end) is True
    assert in_night_window(time(2, 0), start, end) is True
    assert in_night_window(time(20, 0), start, end) is True
    assert in_night_window(time(6, 0), start, end) is True
    assert in_night_window(time(14, 0), start, end) is False


def test_a_window_inside_one_day_still_works() -> None:
    assert in_night_window(time(13, 0), time(12, 0), time(14, 0)) is True
    assert in_night_window(time(15, 0), time(12, 0), time(14, 0)) is False


def test_nothing_is_a_breach_outside_the_window() -> None:
    assert breach(at=DAY) is False


def test_nothing_is_a_breach_when_the_rule_is_off() -> None:
    assert breach(enabled=False) is False


# --- which positions are lone ones ---------------------------------------------------


def test_the_lone_position_depends_on_the_direction() -> None:
    """On a `to_office` trip everyone is dropped at the same office, so the drops
    happen together and the only solitary moment is the first pickup. Going home,
    everyone boards at the office and the lone moment is the last drop."""
    assert lone_positions(Direction.to_office) == frozenset({NightPosition.first_pickup})
    assert lone_positions(Direction.from_office) == frozenset({NightPosition.last_drop})


def test_the_first_rider_picked_up_to_the_office_is_exposed() -> None:
    assert breach(direction=Direction.to_office, order=[ASHA, RAHUL], flagged=[ASHA]) is True
    assert breach(direction=Direction.to_office, order=[RAHUL, ASHA], flagged=[ASHA]) is False


def test_the_last_rider_dropped_from_the_office_is_exposed() -> None:
    assert breach(direction=Direction.from_office, order=[RAHUL, ASHA], flagged=[ASHA]) is True
    assert breach(direction=Direction.from_office, order=[ASHA, RAHUL], flagged=[ASHA]) is False


def test_a_rider_in_the_middle_is_never_alone() -> None:
    assert (
        breach(direction=Direction.to_office, order=[RAHUL, ASHA, PRIYA], flagged=[ASHA]) is False
    )


def test_an_unflagged_rider_in_an_exposed_position_is_fine() -> None:
    assert breach(order=[RAHUL, ASHA], flagged=[ASHA]) is False


# --- what the rule deliberately does not do --------------------------------------------


def test_a_solo_trip_cannot_breach_a_rule_about_order() -> None:
    """With one rider aboard there is no order to get wrong, and refusing the ride
    would leave them with no cab at all, which is not safer. Whether a flagged rider
    may travel alone at night, and what an escort is, is OQ-10."""
    assert breach(order=[ASHA], flagged=[ASHA]) is False


def test_the_policed_positions_are_configurable() -> None:
    """OQ-10 is open, so a pilot client may want only one of the two."""
    going = {"direction": Direction.to_office, "order": [ASHA, RAHUL], "flagged": [ASHA]}
    assert breach(**going, positions="both") is True
    assert breach(**going, positions="first_pickup") is True
    # Policing only the last drop says nothing about a morning pickup.
    assert breach(**going, positions="last_drop") is False


def test_an_unknown_positions_setting_polices_everything() -> None:
    """A typo in config must not quietly switch a safety rule off."""
    assert breach(positions="nonsense") is True


@pytest.mark.parametrize("positions", ["both", "first_pickup", "last_drop"])
def test_exposure_is_empty_for_a_single_rider_whatever_the_setting(positions: str) -> None:
    assert exposed_riders(Direction.to_office, [ASHA], positions) == frozenset()
