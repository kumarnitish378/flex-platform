"""The night escort reasons as arithmetic (owner decisions 2026-11-01 and 2026-11-02)."""

from __future__ import annotations

from datetime import time

from app.domain.enums import Direction
from app.domain.night_escort import (
    EscortBasis,
    EscortReason,
    accepted_bases,
    escort_reason,
)


def reason(
    genders: list[str | None],
    direction: Direction = Direction.from_office,
    at: time = time(22, 30),
    enabled: bool = True,
) -> EscortReason | None:
    return escort_reason(
        enabled=enabled,
        local_time=at,
        night_start=time(20, 0),
        night_end=time(6, 0),
        direction=direction,
        genders_in_drop_order=genders,
    )


def test_a_lone_woman_is_flagged_in_either_direction() -> None:
    assert reason(["female"]) is EscortReason.lone_rider
    assert reason(["female"], Direction.to_office) is EscortReason.lone_rider


def test_a_woman_last_out_going_home_is_flagged() -> None:
    assert reason(["male", "female"]) is EscortReason.last_out
    assert reason(["female", "female"]) is EscortReason.last_out
    assert reason(["male", "male", "female"]) is EscortReason.last_out


def test_a_man_last_out_is_not() -> None:
    assert reason(["female", "male"]) is None
    assert reason(["female", "female", "male"]) is None


def test_to_the_office_only_the_lone_rider_case_applies() -> None:
    assert reason(["male", "female"], Direction.to_office) is None


def test_unknown_gender_never_triggers_either_case() -> None:
    assert reason([None]) is None
    assert reason(["male", None]) is None


def test_the_window_and_the_switch_apply_to_both_cases() -> None:
    assert reason(["male", "female"], at=time(14, 0)) is None
    assert reason(["male", "female"], enabled=False) is None
    assert reason(["male", "female"], at=time(2, 0)) is EscortReason.last_out


def test_only_an_arranged_escort_clears_last_out() -> None:
    assert accepted_bases(EscortReason.last_out) == {EscortBasis.escort_arranged}
    assert accepted_bases(EscortReason.lone_rider) == set(EscortBasis)
