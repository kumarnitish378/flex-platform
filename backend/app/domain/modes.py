"""Which mode governs a request (`control-model.md` §1–2, task B24).

Pure: a list of settings, the request's facts, and the time. No database, no clock of
its own - the caller supplies "now", because the simulator needs to ask this question at
a simulated moment.

**Modes decide who normally assigns, and nothing else.** Tracking, ETA and notifications
work identically in every mode (§1). A mode is not a feature flag.

The precedence in §2 is a list of eight levels, and the awkward part is that levels 3–7
are *combinations* rather than a simple count: client+zone+time, client+time, zone+time,
client, zone. A plain "count the matching dimensions" gets it wrong - it would rank a
client-only setting above a zone+time one, and §2 ranks them the other way round. The
weights below reproduce the documented order exactly; see `specificity`.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, time
from enum import StrEnum

from app.domain.enums import Direction


class Mode(StrEnum):
    """`control-model.md` §1. Phase 1 supports `manual` only; Phase 2 adds `semi_auto`."""

    manual = "manual"
    semi_auto = "semi_auto"
    full_auto = "full_auto"


class ModeReason(StrEnum):
    """Why this mode won - the level of §2 that decided it.

    Returned with every resolution because a supervisor asking "why is this request on
    manual?" deserves better than the answer "it is". The admin screen shows this.
    """

    automation_paused = "automation_paused"
    vip = "vip"
    client_zone_time = "client_zone_time"
    client_time = "client_time"
    zone_time = "zone_time"
    client_zone = "client_zone"
    client = "client"
    zone = "zone"
    operator_default = "operator_default"


@dataclass(frozen=True, slots=True)
class ModeScope:
    """One `mode_setting` row, as pure data.

    Every scoping field is optional; `None` means "any". A row with all of them `None`
    is the operator default and matches everything.
    """

    id: uuid.UUID
    mode: Mode
    updated_at: datetime
    client_id: uuid.UUID | None = None
    zone_id: uuid.UUID | None = None
    direction: Direction | None = None
    #: ISO weekdays, Monday = 1 ... Sunday = 7, matching `datetime.isoweekday()`.
    #: `None` or empty means every day.
    weekdays: frozenset[int] | None = None
    start_time: time | None = None
    end_time: time | None = None

    @property
    def has_time_window(self) -> bool:
        """A window needs both ends. One end alone is a half-written rule, not a window.

        Treated as no window rather than guessed at: assuming midnight for the missing
        end would silently make a 'from 18:00' rule stop at midnight, which is exactly
        when an evening shift is still running.
        """
        return self.start_time is not None and self.end_time is not None


@dataclass(frozen=True, slots=True)
class RequestScope:
    """What a request is, for the purpose of matching a setting."""

    client_id: uuid.UUID
    direction: Direction
    #: Local time at the operator, already converted. `None` until zones exist (B27),
    #: in which case no zone-scoped setting can match.
    zone_id: uuid.UUID | None = None
    is_vip: bool = False


@dataclass(frozen=True, slots=True)
class Resolution:
    """The answer, and which rule produced it."""

    mode: Mode
    reason: ModeReason
    #: The setting that won, or `None` for the pause, the VIP rule and the default.
    setting_id: uuid.UUID | None = None


#: `control-model.md` §2, levels 3–7, reproduced exactly.
#:
#: A time window dominates: *every* time-scoped combination outranks *every* one without
#: a window. Then client, then zone. The resulting order is
#: 7 client+zone+time, 6 client+time, 5 zone+time, 3 client+zone, 2 client, 1 zone -
#: which is §2's list, with client+zone slotted where it belongs.
#:
#: §2 does not list client+zone without a window, and does not say where `direction`
#: ranks at all even though it is one of the columns (OQ-36). Direction is therefore
#: used for *matching* and as a final tie-break only, never to outrank a documented
#: level.
_TIME_WEIGHT = 4
_CLIENT_WEIGHT = 2
_ZONE_WEIGHT = 1

_REASON_FOR: dict[tuple[bool, bool, bool], ModeReason] = {
    # (client, zone, time)
    (True, True, True): ModeReason.client_zone_time,
    (True, False, True): ModeReason.client_time,
    (False, True, True): ModeReason.zone_time,
    (True, True, False): ModeReason.client_zone,
    (True, False, False): ModeReason.client,
    (False, True, False): ModeReason.zone,
}


def in_window(setting: ModeScope, at: datetime) -> bool:
    """Does `at` fall inside this setting's weekdays and time window?

    Handles a window that crosses midnight (22:00–06:00), because night-safety and
    late-shift rules are exactly the ones that do. For those, the **weekday is matched
    on the day the window opened**: a rule for Friday 22:00–06:00 covers the small
    hours of Saturday morning, which is what anyone writing "Friday night" means.
    """
    if setting.weekdays:
        weekday = at.isoweekday()
        if not setting.has_time_window:
            if weekday not in setting.weekdays:
                return False
        else:
            assert setting.start_time is not None and setting.end_time is not None
            crosses_midnight = setting.start_time > setting.end_time
            # After midnight inside a crossing window belongs to the previous day.
            opened_on = weekday
            if crosses_midnight and at.time() < setting.end_time:
                opened_on = 7 if weekday == 1 else weekday - 1
            if opened_on not in setting.weekdays:
                return False

    if not setting.has_time_window:
        return True

    assert setting.start_time is not None and setting.end_time is not None
    now = at.time()
    if setting.start_time <= setting.end_time:
        return setting.start_time <= now <= setting.end_time
    return now >= setting.start_time or now <= setting.end_time


def matches(setting: ModeScope, request: RequestScope, at: datetime) -> bool:
    """True when every scoping field the setting names agrees with the request."""
    if setting.client_id is not None and setting.client_id != request.client_id:
        return False
    if setting.zone_id is not None and setting.zone_id != request.zone_id:
        return False
    if setting.direction is not None and setting.direction != request.direction:
        return False
    return in_window(setting, at)


def specificity(setting: ModeScope) -> tuple[int, int]:
    """How narrow this setting is. Higher wins.

    The first element is §2's documented ordering. The second is `direction`, which §2
    does not rank (OQ-36): it breaks ties between otherwise equally specific settings
    rather than jumping any documented level, so a direction-scoped rule beats an
    identical one without a direction, and nothing else changes.
    """
    documented = (
        _TIME_WEIGHT * setting.has_time_window
        + _CLIENT_WEIGHT * (setting.client_id is not None)
        + _ZONE_WEIGHT * (setting.zone_id is not None)
    )
    return (documented, int(setting.direction is not None))


def _reason_for(setting: ModeScope) -> ModeReason:
    key = (
        setting.client_id is not None,
        setting.zone_id is not None,
        setting.has_time_window,
    )
    return _REASON_FOR.get(key, ModeReason.operator_default)


def resolve_mode(
    settings: list[ModeScope],
    request: RequestScope,
    at: datetime,
    *,
    automation_paused: bool,
    operator_default: Mode = Mode.manual,
) -> Resolution:
    """The mode governing this request, and why (`control-model.md` §2).

    Levels 1 and 2 are not settings and are checked first:

    * **Emergency pause** makes everything manual. It is the one switch an operator
      reaches for when the system is doing something they do not like, so nothing may
      sit above it - not a client rule, not VIP.
    * **VIP** is assigned immediately, in `full_auto` behaviour. Whether a VIP vehicle
      is actually free is a dispatch question, not a mode one: §2 says "if a VIP vehicle
      is available ... otherwise alert supervisor", and the caller owns that branch
      because only it can see the fleet. This function answers "which mode", and for a
      VIP the answer is always the same.

    Then the most specific matching setting, with the most recently updated winning a
    tie - §2's rule, and the reason the admin screen warns about overlaps.
    """
    if automation_paused:
        return Resolution(Mode.manual, ModeReason.automation_paused)

    if request.is_vip:
        return Resolution(Mode.full_auto, ModeReason.vip)

    applicable = [setting for setting in settings if matches(setting, request, at)]
    if not applicable:
        return Resolution(operator_default, ModeReason.operator_default)

    # Most specific first; then most recently updated (§2); then by id, so two rows
    # saved in the same transaction cannot order differently between two calls.
    best = max(
        applicable,
        key=lambda setting: (specificity(setting), setting.updated_at, str(setting.id)),
    )
    if specificity(best) == (0, 0):
        # A setting that scopes nothing *is* the operator default, however it was
        # written. Reporting it as a client rule would send someone hunting for a client
        # that is not there.
        return Resolution(best.mode, ModeReason.operator_default, best.id)
    return Resolution(best.mode, _reason_for(best), best.id)


def overlaps(settings: list[ModeScope]) -> list[tuple[uuid.UUID, uuid.UUID]]:
    """Pairs of settings at the same specificity that could both match one request.

    §2 resolves these by update time, which is a deterministic answer to a question the
    operator probably did not mean to ask. The admin screen warns about them (B24's
    acceptance criterion), so this reports rather than refuses - an overlap is often
    deliberate while a rule is being migrated.
    """
    found: list[tuple[uuid.UUID, uuid.UUID]] = []
    for index, first in enumerate(settings):
        for second in settings[index + 1 :]:
            if specificity(first) != specificity(second):
                continue
            if _can_collide(first, second):
                found.append((first.id, second.id))
    return found


def _can_collide(first: ModeScope, second: ModeScope) -> bool:
    """True when no scoping field proves the two can never match the same request."""
    for left, right in (
        (first.client_id, second.client_id),
        (first.zone_id, second.zone_id),
        (first.direction, second.direction),
    ):
        if left is not None and right is not None and left != right:
            return False
    # Disjoint weekdays prove it: a weekday rule and a weekend rule never collide.
    return not (first.weekdays and second.weekdays and not (first.weekdays & second.weekdays))
