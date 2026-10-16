"""Supervisor override actions, their reasons and their expiry (`control-model.md` §3).

Pure: no database, no clock, no framework. The service layer loads rows and writes them;
everything that decides *whether an override is allowed and how long it lasts* lives
here so the simulator and the tests can ask the same questions without a session.

Three things §3 asks for that are easy to get subtly wrong, and are therefore here
rather than inline in a router:

* **Which fields an action needs.** `reassign` without a target vehicle is not an
  override, it is a typo; `block_pooling` names a trip, never a request. A table beats
  eight `if` statements that drift apart.
* **Which reasons a hard-rule override accepts.** Rule 4 narrows the usual seven to
  three *plus a note*, because those overrides are the ones the report has to flag.
* **When it stops applying.** Rule 5 gives every override an `expires_at` defaulting to
  the end of the current shift, and the expiry has to take effect **without anything
  running** - no sweep, no Celery beat. That makes it a question asked on every read,
  which is `still_applies`.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from zoneinfo import ZoneInfo

from app.domain.errors import ValidationFailed

#: The local clock time an operator's shift is taken to end on (`control-model.md` §3
#: rule 5, "end of current shift / 23:59 IST"). The operator's own timezone comes from
#: `operator.timezone`; the hour does not vary by operator yet, and when it needs to it
#: becomes a config key rather than a second constant here.
SHIFT_END = (23, 59)


class OverrideAction(StrEnum):
    """The override set of `control-model.md` §3.

    The ninth row of that table, `pause_automation` / `resume_automation`, is absent on
    purpose: it has its own endpoint (`PUT /dispatch/automation`, SUP-05) because it is
    operator-wide and names no request, trip or vehicle. It is still written to
    `override_log` - rule 6 says *every* override is - just not through here.
    """

    reassign = "reassign"
    lock = "lock"
    unlock = "unlock"
    force_priority = "force_priority"
    block_pooling = "block_pooling"
    hold = "hold"
    cancel = "cancel"
    vehicle_out_of_service = "vehicle_out_of_service"


class ReasonCode(StrEnum):
    """§3 rule 3: one tap, always required."""

    driver_issue = "driver_issue"
    local_knowledge = "local_knowledge"
    client_request = "client_request"
    traffic = "traffic"
    vehicle_issue = "vehicle_issue"
    safety = "safety"
    other = "other"


#: §3 rule 4. A hard-rule override - putting a rider in a cab the rules excluded -
#: narrows the seven reasons to these three and demands a note with them. "traffic" is
#: not a defence for carrying a VIP in a non-VIP vehicle; saying why is.
HARD_RULE_REASON_CODES: frozenset[ReasonCode] = frozenset(
    {ReasonCode.safety, ReasonCode.client_request, ReasonCode.other}
)

#: Actions that leave a **standing state** behind them, and therefore expire. The rest
#: happen once and are over: a cancelled request does not un-cancel at 23:59.
EXPIRING_ACTIONS: frozenset[OverrideAction] = frozenset(
    {
        OverrideAction.lock,
        OverrideAction.force_priority,
        OverrideAction.block_pooling,
        OverrideAction.hold,
        OverrideAction.vehicle_out_of_service,
    }
)

#: The action that ends each standing one, where a human has a word for it. Applying the
#: inverse closes the open row rather than writing a contradicting one, so "is this
#: request locked?" has one answer and not two.
ENDED_BY: dict[OverrideAction, OverrideAction] = {OverrideAction.lock: OverrideAction.unlock}


class Target(StrEnum):
    """What an action acts on. One each - an action with two subjects is two actions."""

    request = "request"
    trip = "trip"
    vehicle = "vehicle"


TARGET_OF: dict[OverrideAction, Target] = {
    OverrideAction.reassign: Target.request,
    OverrideAction.lock: Target.request,
    OverrideAction.unlock: Target.request,
    OverrideAction.force_priority: Target.request,
    OverrideAction.block_pooling: Target.trip,
    OverrideAction.hold: Target.request,
    # Cancel is the exception the table forced: §3 says "cancel request **or** trip".
    # Resolved in `check_targets` rather than by inventing `cancel_trip`, because the
    # supervisor's screen has one Cancel button and the app would have to choose.
    OverrideAction.cancel: Target.request,
    OverrideAction.vehicle_out_of_service: Target.vehicle,
}


@dataclass(frozen=True, slots=True)
class OverrideCommand:
    """One override as asked for, before anything has been read from the database."""

    action: OverrideAction
    reason_code: ReasonCode
    request_id: uuid.UUID | None = None
    trip_id: uuid.UUID | None = None
    vehicle_id: uuid.UUID | None = None
    target_vehicle_id: uuid.UUID | None = None
    hold_until: datetime | None = None
    expires_at: datetime | None = None
    #: True when the caller said something about expiry at all - including `null`,
    #: which rule 5 defines as "until the trip ends". Without this an omitted field and
    #: a deliberate open-ended override are the same value, and one of them has to win:
    #: defaulting would quietly end an open override at 23:59, and not defaulting would
    #: make every override permanent, which is the failure rule 5 exists to prevent.
    expiry_specified: bool = False
    note: str | None = None

    @property
    def subject(self) -> tuple[Target, uuid.UUID]:
        """What this command acts on, assuming `check_targets` has passed."""
        if self.action is OverrideAction.cancel and self.request_id is None:
            assert self.trip_id is not None
            return Target.trip, self.trip_id
        target = TARGET_OF[self.action]
        identifier = {
            Target.request: self.request_id,
            Target.trip: self.trip_id,
            Target.vehicle: self.vehicle_id,
        }[target]
        assert identifier is not None
        return target, identifier


def check_targets(command: OverrideCommand) -> None:
    """Refuse a command that does not name what it would act on."""
    problems: list[str] = []

    if command.action is OverrideAction.cancel:
        if (command.request_id is None) == (command.trip_id is None):
            problems.append("cancel needs exactly one of request_id or trip_id")
    else:
        target = TARGET_OF[command.action]
        present = {
            Target.request: command.request_id,
            Target.trip: command.trip_id,
            Target.vehicle: command.vehicle_id,
        }[target]
        if present is None:
            problems.append(f"{command.action} needs {target}_id")

    if command.action is OverrideAction.reassign and command.target_vehicle_id is None:
        problems.append("reassign needs target_vehicle_id")
    if command.action is OverrideAction.hold and command.hold_until is None:
        # §3: "keep request queued until time T **or manual release**". A hold with no T
        # is the manual-release kind, and is spelled with `expires_at: null` instead -
        # which is the same field every other standing override uses, rather than a
        # second nullable timestamp meaning nearly the same thing.
        problems.append("hold needs hold_until (use expires_at: null for an open hold)")

    if problems:
        raise ValidationFailed(
            "The override does not name what it would change",
            {"action": str(command.action), "errors": problems},
        )


def check_reason(command: OverrideCommand, *, waives_hard_rule: bool = False) -> None:
    """§3 rules 3 and 4: a reason always, and a narrowed set with a note for hard rules."""
    if command.reason_code is ReasonCode.other and not (command.note or "").strip():
        raise ValidationFailed(
            "reason_code 'other' needs a note saying what it was",
            {"action": str(command.action), "reason_code": str(command.reason_code)},
        )

    if not waives_hard_rule:
        return

    if command.reason_code not in HARD_RULE_REASON_CODES:
        raise ValidationFailed(
            "Overriding a hard rule needs reason_code safety, client_request or other",
            {
                "action": str(command.action),
                "reason_code": str(command.reason_code),
                "allowed": sorted(str(code) for code in HARD_RULE_REASON_CODES),
            },
        )
    if not (command.note or "").strip():
        raise ValidationFailed(
            "Overriding a hard rule needs a note",
            {"action": str(command.action), "reason_code": str(command.reason_code)},
        )


def default_expiry(action: OverrideAction, now: datetime, timezone: str) -> datetime | None:
    """§3 rule 5: end of the current shift, in the operator's own local time.

    Returned in UTC, like every other timestamp the platform stores. `None` for an
    action that does not leave a standing state, and for one the caller explicitly sent
    `expires_at: null` for - "until the trip ends", which rule 5 also allows.
    """
    if action not in EXPIRING_ACTIONS:
        return None

    local = now.astimezone(ZoneInfo(timezone))
    hour, minute = SHIFT_END
    end = local.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if end <= local:
        # Applied at 23:59 or later: the shift that is current is tomorrow's, not one
        # that ended a minute ago. An override expiring in the past is one that never
        # applied, which is not what anybody tapping the button meant.
        end += timedelta(days=1)
    return end.astimezone(UTC)


def still_applies(expires_at: datetime | None, now: datetime) -> bool:
    """Is this override still in force?

    Asked on **every read** of the state an override set, which is what makes rule 5
    work with nothing running. A sweep that flipped the columns back would be a second
    source of truth, would need to be running for the platform to be correct, and would
    leave a window after a restart where an expired lock still pinned a rider.
    """
    return expires_at is None or expires_at > now
