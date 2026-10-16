"""The override rules of `control-model.md` §3, as pure functions (B26).

Everything here is decidable without a database: which fields an action needs, which
reasons rule 4 accepts, when an override lapses, and whether it still applies.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.domain.errors import ValidationFailed
from app.domain.overrides import (
    EXPIRING_ACTIONS,
    HARD_RULE_REASON_CODES,
    TARGET_OF,
    OverrideAction,
    OverrideCommand,
    ReasonCode,
    Target,
    check_reason,
    check_targets,
    default_expiry,
    still_applies,
)

IST = "Asia/Kolkata"
# 07:00 IST on a Friday.
MORNING = datetime(2026, 10, 16, 1, 30, tzinfo=UTC)


def command(action: OverrideAction, **kwargs: object) -> OverrideCommand:
    defaults: dict[str, object] = {"reason_code": ReasonCode.traffic}
    defaults.update(kwargs)
    return OverrideCommand(action=action, **defaults)  # type: ignore[arg-type]


# --- what an action must name ----------------------------------------------------


@pytest.mark.parametrize("action", sorted(OverrideAction, key=str))
def test_every_action_says_what_it_acts_on(action: OverrideAction) -> None:
    """A table, not eight `if` statements: an action added without a subject is a bug."""
    assert action in TARGET_OF


def test_reassign_without_a_target_vehicle_is_refused() -> None:
    with pytest.raises(ValidationFailed) as excinfo:
        check_targets(command(OverrideAction.reassign, request_id=uuid.uuid4()))
    assert "target_vehicle_id" in str(excinfo.value.details)


def test_block_pooling_names_a_trip_not_a_request() -> None:
    with pytest.raises(ValidationFailed):
        check_targets(command(OverrideAction.block_pooling, request_id=uuid.uuid4()))
    check_targets(command(OverrideAction.block_pooling, trip_id=uuid.uuid4()))


def test_cancel_takes_exactly_one_subject() -> None:
    """§3 says "cancel request **or** trip". Both at once is two decisions in one tap."""
    with pytest.raises(ValidationFailed):
        check_targets(command(OverrideAction.cancel))
    with pytest.raises(ValidationFailed):
        check_targets(command(OverrideAction.cancel, request_id=uuid.uuid4(), trip_id=uuid.uuid4()))
    check_targets(command(OverrideAction.cancel, request_id=uuid.uuid4()))
    check_targets(command(OverrideAction.cancel, trip_id=uuid.uuid4()))


def test_a_hold_needs_the_time_it_holds_until() -> None:
    with pytest.raises(ValidationFailed):
        check_targets(command(OverrideAction.hold, request_id=uuid.uuid4()))
    check_targets(command(OverrideAction.hold, request_id=uuid.uuid4(), hold_until=MORNING))


def test_the_subject_of_a_trip_cancel_is_the_trip() -> None:
    trip_id = uuid.uuid4()
    assert command(OverrideAction.cancel, trip_id=trip_id).subject == (Target.trip, trip_id)


# --- rule 3 and rule 4: reasons ----------------------------------------------------


def test_other_always_needs_a_note() -> None:
    """Rule 3 writes it as "`other` (+ note)". A reason of "other" alone says nothing."""
    with pytest.raises(ValidationFailed):
        check_reason(command(OverrideAction.lock, reason_code=ReasonCode.other))
    check_reason(command(OverrideAction.lock, reason_code=ReasonCode.other, note="client director"))


def test_an_ordinary_override_takes_any_of_the_seven_reasons() -> None:
    for code in ReasonCode:
        if code is ReasonCode.other:
            continue
        check_reason(command(OverrideAction.lock, reason_code=code))


@pytest.mark.parametrize("code", sorted(set(ReasonCode) - HARD_RULE_REASON_CODES, key=str))
def test_a_hard_rule_override_refuses_the_everyday_reasons(code: ReasonCode) -> None:
    """Rule 4. "Traffic" is not a defence for putting a VIP in a non-VIP vehicle."""
    with pytest.raises(ValidationFailed) as excinfo:
        check_reason(
            command(OverrideAction.reassign, reason_code=code, note="needed"),
            waives_hard_rule=True,
        )
    assert "safety" in str(excinfo.value)


@pytest.mark.parametrize("code", sorted(HARD_RULE_REASON_CODES, key=str))
def test_a_hard_rule_override_needs_a_note_with_the_narrowed_reason(
    code: ReasonCode,
) -> None:
    with pytest.raises(ValidationFailed):
        check_reason(command(OverrideAction.reassign, reason_code=code), waives_hard_rule=True)
    check_reason(
        command(OverrideAction.reassign, reason_code=code, note="escort arranged"),
        waives_hard_rule=True,
    )


# --- rule 5: expiry -----------------------------------------------------------------


def test_the_default_expiry_is_the_end_of_the_operators_day_not_the_servers() -> None:
    """23:59 **IST**, which is 18:29 UTC. A platform that stored 23:59 UTC would leave
    an override standing five and a half hours into the next morning's peak."""
    end = default_expiry(OverrideAction.lock, MORNING, IST)
    assert end == datetime(2026, 10, 16, 18, 29, tzinfo=UTC)


def test_an_override_applied_after_the_shift_ends_runs_to_tomorrows_end() -> None:
    """At 23:59:30 IST the current shift is tomorrow's. An override expiring a minute
    ago is one that never applied, which is not what anyone tapping the button meant."""
    late = datetime(2026, 10, 16, 18, 29, 30, tzinfo=UTC)  # 23:59:30 IST
    assert default_expiry(OverrideAction.lock, late, IST) == datetime(
        2026, 10, 17, 18, 29, tzinfo=UTC
    )


def test_an_operator_in_another_timezone_gets_their_own_end_of_shift() -> None:
    assert default_expiry(OverrideAction.lock, MORNING, "UTC") == datetime(
        2026, 10, 16, 23, 59, tzinfo=UTC
    )


@pytest.mark.parametrize("action", sorted(set(OverrideAction) - EXPIRING_ACTIONS, key=str))
def test_an_action_that_happens_once_has_no_expiry(action: OverrideAction) -> None:
    """A cancelled request does not un-cancel at 23:59."""
    assert default_expiry(action, MORNING, IST) is None


def test_an_open_ended_override_always_applies() -> None:
    assert still_applies(None, MORNING) is True


def test_an_override_stops_applying_the_moment_it_expires() -> None:
    expiry = MORNING + timedelta(hours=1)
    assert still_applies(expiry, MORNING) is True
    assert still_applies(expiry, expiry - timedelta(seconds=1)) is True
    # At the stroke itself it is over: an expiry inclusive of its own second would
    # leave a lock applying for one more tick of whatever read it next.
    assert still_applies(expiry, expiry) is False
    assert still_applies(expiry, expiry + timedelta(seconds=1)) is False
