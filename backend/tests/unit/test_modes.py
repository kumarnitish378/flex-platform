"""Mode precedence, level by level (`control-model.md` §2, B24).

§2 is an eight-level list, and the reason it needs a table-driven test rather than a
few examples is that levels 3–7 are *combinations*, not a count. A plain "most matching
dimensions wins" ranks a client-only rule above a zone+time one; §2 ranks them the other
way round. Every level is asserted here, in order, against a world where several
settings match at once.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, time, timedelta

import pytest

from app.domain.enums import Direction
from app.domain.modes import (
    Mode,
    ModeReason,
    ModeScope,
    RequestScope,
    Resolution,
    in_window,
    matches,
    overlaps,
    resolve_mode,
    specificity,
)

CLIENT = uuid.UUID(int=1)
OTHER_CLIENT = uuid.UUID(int=2)
ZONE = uuid.UUID(int=10)
OTHER_ZONE = uuid.UUID(int=11)

#: Thursday 09:00.
NOW = datetime(2026, 10, 15, 9, 0, tzinfo=UTC)
EARLIER = NOW - timedelta(days=7)

MORNING = (time(6, 0), time(12, 0))


def scope(
    *,
    mode: Mode = Mode.semi_auto,
    client: uuid.UUID | None = None,
    zone: uuid.UUID | None = None,
    direction: Direction | None = None,
    window: tuple[time, time] | None = None,
    weekdays: frozenset[int] | None = None,
    updated_at: datetime = EARLIER,
    id: uuid.UUID | None = None,
) -> ModeScope:
    return ModeScope(
        id=id or uuid.uuid4(),
        mode=mode,
        updated_at=updated_at,
        client_id=client,
        zone_id=zone,
        direction=direction,
        weekdays=weekdays,
        start_time=window[0] if window else None,
        end_time=window[1] if window else None,
    )


def request(*, vip: bool = False) -> RequestScope:
    return RequestScope(client_id=CLIENT, direction=Direction.to_office, zone_id=ZONE, is_vip=vip)


def resolve(settings: list[ModeScope], *, paused: bool = False, vip: bool = False) -> Resolution:
    return resolve_mode(settings, request(vip=vip), NOW, automation_paused=paused)


# --- levels 1 and 2: not settings at all -------------------------------------


def test_emergency_pause_beats_everything() -> None:
    """The one switch an operator reaches for when the system misbehaves.

    Nothing may sit above it - not a client rule, not VIP.
    """
    settings = [scope(mode=Mode.full_auto, client=CLIENT, zone=ZONE, window=MORNING)]

    assert resolve(settings, paused=True).mode is Mode.manual
    assert resolve(settings, paused=True).reason is ModeReason.automation_paused


def test_pause_beats_vip_too() -> None:
    assert resolve([], paused=True, vip=True).mode is Mode.manual


def test_a_vip_is_full_auto_whatever_the_settings_say() -> None:
    """§2 level 2. Whether a VIP *vehicle* is free is a dispatch question, not a mode
    one - the caller owns that branch, because only it can see the fleet."""
    settings = [scope(mode=Mode.manual, client=CLIENT, zone=ZONE, window=MORNING)]

    resolution = resolve(settings, vip=True)

    assert resolution.mode is Mode.full_auto
    assert resolution.reason is ModeReason.vip


# --- levels 3–7, in order ----------------------------------------------------


def test_every_level_wins_in_the_documented_order() -> None:
    """Add settings from least to most specific; each new one must take over.

    §2 levels 3-7: client+zone+time, client+time, zone+time, client, zone.
    """
    zone_only = scope(mode=Mode.manual, zone=ZONE)
    client_only = scope(mode=Mode.manual, client=CLIENT)
    zone_time = scope(mode=Mode.semi_auto, zone=ZONE, window=MORNING)
    client_time = scope(mode=Mode.semi_auto, client=CLIENT, window=MORNING)
    client_zone_time = scope(mode=Mode.full_auto, client=CLIENT, zone=ZONE, window=MORNING)

    steps = [
        ([zone_only], ModeReason.zone),
        ([zone_only, client_only], ModeReason.client),
        ([zone_only, client_only, zone_time], ModeReason.zone_time),
        ([zone_only, client_only, zone_time, client_time], ModeReason.client_time),
        (
            [zone_only, client_only, zone_time, client_time, client_zone_time],
            ModeReason.client_zone_time,
        ),
    ]
    for settings, expected in steps:
        assert resolve(settings).reason is expected, f"after adding {expected}"


def test_a_time_window_outranks_a_broader_rule_without_one() -> None:
    """The trap a naive 'count the dimensions' implementation falls into.

    zone+time is §2 level 5; client alone is level 6. Counting dimensions would give
    client (1) and zone+time (2)... which happens to be right. Counting *fields* gives
    client 1 and zone+time 2 as well. The one that breaks is weighting client highest:
    then client (1 field, high weight) beats zone+time, and §2 says it must not.
    """
    settings = [
        scope(mode=Mode.manual, client=CLIENT),
        scope(mode=Mode.full_auto, zone=ZONE, window=MORNING),
    ]

    assert resolve(settings).mode is Mode.full_auto


def test_no_matching_setting_falls_back_to_the_operator_default() -> None:
    resolution = resolve_mode(
        [scope(client=OTHER_CLIENT)],
        request(),
        NOW,
        automation_paused=False,
        operator_default=Mode.manual,
    )

    assert resolution.mode is Mode.manual
    assert resolution.reason is ModeReason.operator_default
    assert resolution.setting_id is None


def test_a_setting_that_scopes_nothing_reports_as_the_default() -> None:
    """However it was written. Calling it a client rule sends someone hunting for a
    client that is not there."""
    catch_all = scope(mode=Mode.semi_auto)

    resolution = resolve([catch_all])

    assert resolution.mode is Mode.semi_auto
    assert resolution.reason is ModeReason.operator_default
    assert resolution.setting_id == catch_all.id


# --- the tie-break -----------------------------------------------------------


def test_at_equal_specificity_the_most_recently_updated_wins() -> None:
    """§2, and the reason the admin screen warns about overlaps."""
    older = scope(mode=Mode.manual, client=CLIENT, updated_at=EARLIER)
    newer = scope(mode=Mode.full_auto, client=CLIENT, updated_at=NOW)

    assert resolve([older, newer]).mode is Mode.full_auto
    assert resolve([newer, older]).mode is Mode.full_auto, "order of the list must not matter"


def test_a_direction_scoped_rule_breaks_a_tie_but_jumps_no_level() -> None:
    """§2 lists `direction` as a column and never ranks it (OQ-36).

    Treated as a final tie-break: narrower than an otherwise identical rule, but it
    never outranks a documented level.
    """
    general = scope(mode=Mode.manual, client=CLIENT, updated_at=NOW)
    directed = scope(
        mode=Mode.full_auto, client=CLIENT, direction=Direction.to_office, updated_at=EARLIER
    )

    # Beats an identical rule, despite being older.
    assert resolve([general, directed]).mode is Mode.full_auto

    # But does not beat a documented level above it.
    with_window = scope(mode=Mode.semi_auto, client=CLIENT, window=MORNING, updated_at=EARLIER)
    assert resolve([directed, with_window]).mode is Mode.semi_auto


def test_identical_settings_resolve_the_same_way_every_call() -> None:
    """Two rows saved in one transaction share `updated_at`; order must still be fixed."""
    first = scope(mode=Mode.manual, client=CLIENT, updated_at=NOW, id=uuid.UUID(int=100))
    second = scope(mode=Mode.full_auto, client=CLIENT, updated_at=NOW, id=uuid.UUID(int=200))

    assert resolve([first, second]).setting_id == resolve([second, first]).setting_id


# --- matching ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("setting", "should_match"),
    [
        (scope(), True),
        (scope(client=CLIENT), True),
        (scope(client=OTHER_CLIENT), False),
        (scope(zone=ZONE), True),
        (scope(zone=OTHER_ZONE), False),
        (scope(direction=Direction.to_office), True),
        (scope(direction=Direction.from_office), False),
    ],
)
def test_a_setting_matches_only_what_it_names(setting: ModeScope, should_match: bool) -> None:
    assert matches(setting, request(), NOW) is should_match


def test_a_request_with_no_zone_cannot_match_a_zone_rule() -> None:
    """Zones arrive with B27; until then `zone_id` is null on every employee."""
    unzoned = RequestScope(client_id=CLIENT, direction=Direction.to_office, zone_id=None)

    assert matches(scope(zone=ZONE), unzoned, NOW) is False
    assert matches(scope(client=CLIENT), unzoned, NOW) is True


# --- time windows ------------------------------------------------------------


def test_inside_and_outside_an_ordinary_window() -> None:
    setting = scope(window=(time(8, 0), time(10, 0)))

    assert in_window(setting, NOW) is True
    assert in_window(setting, NOW.replace(hour=11)) is False


def test_a_window_crossing_midnight_covers_the_small_hours() -> None:
    """Night-safety and late-shift rules are exactly the ones that do this."""
    night = scope(window=(time(22, 0), time(6, 0)))

    assert in_window(night, NOW.replace(hour=23)) is True
    assert in_window(night, NOW.replace(hour=2)) is True
    assert in_window(night, NOW.replace(hour=12)) is False


def test_a_crossing_window_matches_the_weekday_it_opened_on() -> None:
    """A rule for Friday 22:00-06:00 covers Saturday's small hours.

    That is what anyone writing "Friday night" means, and the alternative - matching
    Saturday - silently moves every night rule forward a day.
    """
    friday_night = scope(window=(time(22, 0), time(6, 0)), weekdays=frozenset({5}))

    friday_2300 = datetime(2026, 10, 16, 23, 0, tzinfo=UTC)
    saturday_0200 = datetime(2026, 10, 17, 2, 0, tzinfo=UTC)
    saturday_2300 = datetime(2026, 10, 17, 23, 0, tzinfo=UTC)

    assert friday_2300.isoweekday() == 5
    assert in_window(friday_night, friday_2300) is True
    assert in_window(friday_night, saturday_0200) is True
    assert in_window(friday_night, saturday_2300) is False


def test_a_half_written_window_is_treated_as_no_window() -> None:
    """Guessing midnight for the missing end would stop a 'from 18:00' rule at
    midnight - exactly when an evening shift is still running."""
    half = ModeScope(id=uuid.uuid4(), mode=Mode.manual, updated_at=NOW, start_time=time(18, 0))

    assert half.has_time_window is False
    assert in_window(half, NOW) is True
    assert specificity(half)[0] == 0


def test_weekdays_without_a_window_still_restrict_the_day() -> None:
    thursday_only = scope(weekdays=frozenset({4}))

    assert NOW.isoweekday() == 4
    assert in_window(thursday_only, NOW) is True
    assert in_window(thursday_only, NOW + timedelta(days=1)) is False


# --- overlap warnings --------------------------------------------------------


def test_two_rules_at_the_same_specificity_are_reported_as_overlapping() -> None:
    first = scope(client=CLIENT, id=uuid.UUID(int=100))
    second = scope(client=CLIENT, id=uuid.UUID(int=200))

    assert overlaps([first, second]) == [(first.id, second.id)]


def test_rules_that_can_never_both_apply_are_not_reported() -> None:
    """A warning on every pair of client rules is a warning nobody reads."""
    acme = scope(client=CLIENT)
    other = scope(client=OTHER_CLIENT)

    assert overlaps([acme, other]) == []


def test_different_specificity_is_not_an_overlap() -> None:
    """§2 resolves those deterministically; there is nothing ambiguous to warn about."""
    broad = scope(client=CLIENT)
    narrow = scope(client=CLIENT, zone=ZONE, window=MORNING)

    assert overlaps([broad, narrow]) == []


def test_disjoint_weekdays_are_not_an_overlap() -> None:
    weekdays = scope(client=CLIENT, weekdays=frozenset({1, 2, 3, 4, 5}))
    weekend = scope(client=CLIENT, weekdays=frozenset({6, 7}))

    assert overlaps([weekdays, weekend]) == []
