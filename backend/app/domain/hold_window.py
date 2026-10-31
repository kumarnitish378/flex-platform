"""The evening hold window (`allocation-rules.md` §6 "Evening hold window", §2 rule 10; B29).

A `from_office` rider who is ready to go is worth making wait a few minutes, because the
person leaving the same office a few minutes later is the one they can share a cab with.
That is the whole of pooling's saving at the end of the day, and it is paid for in the
rider's wait. So the window is short, it has four exemptions, and nothing about it is
decided here by the system clock.

**Phase 3 is the fixed minimum** (`hold_window_min_minutes`). Phase 4 makes it dynamic and
will start reading `hold_window_max_minutes`; until then that key is declared and unread,
which is why it is the one entry left in `PHASE_2_KEYS`.

**The four exemptions** (§2 rule 10 and rule 4), each tested on its own:

1. VIP - assigned immediately, never pooled, so there is nobody to wait for;
2. `priority <= 2`;
3. `urgency = high`;
4. `no_sharing` - an exclusive trip also has nobody to wait for. A client whose policy
   forbids pooling outright is the same thing, rider by rider (B28), so it counts.

And one more that is not an exemption but a **short-circuit**: `forced_priority`. §3.1 has
said since Phase 1 that escalation "sets `forced_priority`, which short-circuits the hold
window", and Phase 1 could not deliver it because there was no window. A supervisor's
`force_priority` override and a request that has waited past `alert_wait_minutes` both end
a hold, and the second is what stops a hold from being a way to wait indefinitely.

Pure: the caller supplies the facts and the numbers, so a scenario can watch a window pass
by advancing the injected Clock.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from app.domain.enums import Direction, Urgency

#: `priority <= 2` is "high priority" (§2 rule 10).
HIGH_PRIORITY_AT_OR_BELOW = 2


class HoldExemption(StrEnum):
    """Why a request is not held. Reported so a supervisor can see why it was not."""

    not_from_office = "not_from_office"
    vip = "vip"
    high_priority = "high_priority"
    high_urgency = "high_urgency"
    no_sharing = "no_sharing"
    forced_priority = "forced_priority"
    no_window = "no_window"


@dataclass(frozen=True, slots=True)
class HoldFacts:
    direction: Direction
    queued_at: datetime
    requested_time: datetime
    is_vip: bool
    priority: int
    urgency: Urgency
    #: The request's own `no_sharing`, **or** a client policy that forbids pooling.
    no_sharing: bool
    #: True only while a `force_priority` override (or escalation) still applies.
    forced_priority: bool


def exemption(facts: HoldFacts, hold_min_minutes: int) -> HoldExemption | None:
    """The reason this request is not held, or `None` when it is.

    Ordered from the structural to the situational so the reported reason is the most
    fundamental one: a VIP going to the office is "not from office" before it is "VIP".
    """
    if facts.direction is not Direction.from_office:
        return HoldExemption.not_from_office
    if hold_min_minutes <= 0:
        return HoldExemption.no_window
    if facts.is_vip:
        return HoldExemption.vip
    if facts.forced_priority:
        return HoldExemption.forced_priority
    if facts.priority <= HIGH_PRIORITY_AT_OR_BELOW:
        return HoldExemption.high_priority
    if facts.urgency is Urgency.high:
        return HoldExemption.high_urgency
    if facts.no_sharing:
        return HoldExemption.no_sharing
    return None


def release_at(facts: HoldFacts, hold_min_minutes: int) -> datetime | None:
    """When the request becomes assignable, or `None` when it was never held.

    The window runs from the later of when the rider asked and when they said they would
    be ready: a request made at nine for six o'clock is not ready to be pooled at nine, and
    holding it from the moment it was typed would make the window end hours before the
    rider does.
    """
    if exemption(facts, hold_min_minutes) is not None:
        return None
    return max(facts.queued_at, facts.requested_time) + timedelta(minutes=hold_min_minutes)


def is_held(facts: HoldFacts, hold_min_minutes: int, now: datetime) -> bool:
    """True while the window is still open. At the instant it ends, it is over."""
    released = release_at(facts, hold_min_minutes)
    return released is not None and now < released
