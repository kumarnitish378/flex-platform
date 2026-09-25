"""What each transition tells whom (B16, `trip-lifecycle.md` section 6, EMP-05).

Pure, and worth testing exhaustively: this text is what arrives on a phone at 7am, and a
message sent to the wrong role is a privacy incident rather than a typo.
"""

from __future__ import annotations

import pytest

from app.domain.notifications import (
    TEMPLATES,
    Notification,
    NotificationType,
    build,
)
from app.domain.state_machines import Recipient


def recipients(messages: list[Notification]) -> set[Recipient]:
    return {message.recipient for message in messages}


# --- section 6, row by row ------------------------------------------------------------


def test_assignment_tells_the_employee_and_the_driver() -> None:
    """`request -> assigned | Employee (push), driver (push)`."""
    assert recipients(build(NotificationType.request_assigned)) == {
        Recipient.employee,
        Recipient.driver,
    }


def test_a_nearby_cab_tells_only_the_employee() -> None:
    """`stop ETA <= 5 min | Employee`."""
    assert recipients(build(NotificationType.cab_nearby)) == {Recipient.employee}


def test_an_arrival_tells_only_the_employee() -> None:
    """`stop -> arrived | Employee`."""
    assert recipients(build(NotificationType.cab_arrived)) == {Recipient.employee}


def test_a_reassignment_tells_the_rider_and_both_drivers() -> None:
    """`request reassigned | Employee (new cab), old driver, new driver`."""
    assert recipients(build(NotificationType.request_reassigned)) == {
        Recipient.employee,
        Recipient.previous_driver,
        Recipient.driver,
    }


def test_an_employee_cancelling_tells_the_driver_and_supervisor() -> None:
    """`request cancelled by employee | Driver (if assigned), supervisor`."""
    messages = build(NotificationType.request_cancelled, {"cancelled_by_employee": True})
    assert recipients(messages) == {Recipient.driver, Recipient.supervisor}


def test_an_operator_cancelling_tells_the_employee() -> None:
    """`request cancelled by operator | Employee (with reason)`."""
    messages = build(NotificationType.request_cancelled, {"reason": "Vehicle breakdown"})
    assert recipients(messages) == {Recipient.employee}


def test_an_operator_cancellation_carries_the_reason() -> None:
    """Being stood up without being told why is the worst version of this message."""
    messages = build(NotificationType.request_cancelled, {"reason": "Vehicle breakdown"})
    assert "Vehicle breakdown" in messages[0].body


def test_a_cancellation_with_no_reason_still_reads_properly() -> None:
    messages = build(NotificationType.request_cancelled, {})
    assert messages[0].body.endswith("cancelled.")


def test_near_expiry_tells_the_supervisor() -> None:
    """`request near expiry (15 min before) | Supervisor`."""
    assert recipients(build(NotificationType.request_near_expiry)) == {Recipient.supervisor}


def test_an_abort_tells_the_supervisor_and_operator_admin() -> None:
    """`trip aborted, SOS | Supervisor, operator admin (high priority)`."""
    assert recipients(build(NotificationType.trip_aborted)) == {
        Recipient.supervisor,
        Recipient.operator_admin,
    }


def test_an_sos_tells_the_supervisor_and_operator_admin() -> None:
    assert recipients(build(NotificationType.sos)) == {
        Recipient.supervisor,
        Recipient.operator_admin,
    }


def test_a_completed_trip_tells_the_rider() -> None:
    """EMP-05 lists trip completed among the statuses a rider is told about."""
    assert recipients(build(NotificationType.trip_completed)) == {Recipient.employee}


def test_every_row_of_section_six_has_a_template() -> None:
    """A new notification type must not silently produce nothing."""
    for event in TEMPLATES:
        assert build(event), f"{event} produces no notifications"


# --- priority --------------------------------------------------------------------------


@pytest.mark.parametrize("event", [NotificationType.sos, NotificationType.trip_aborted])
def test_emergencies_are_high_priority(event: NotificationType) -> None:
    """Section 6 marks these "(high priority)"; a phone on silent must still ring."""
    assert all(message.high_priority for message in build(event))


@pytest.mark.parametrize(
    "event",
    [
        NotificationType.request_assigned,
        NotificationType.cab_nearby,
        NotificationType.cab_arrived,
        NotificationType.trip_completed,
    ],
)
def test_ordinary_updates_are_not(event: NotificationType) -> None:
    assert not any(message.high_priority for message in build(event))


# --- wording ----------------------------------------------------------------------------


def test_the_cab_is_named_when_known() -> None:
    messages = build(NotificationType.request_assigned, {"registration_no": "UP16AB1234"})
    employee = next(m for m in messages if m.recipient is Recipient.employee)
    assert "UP16AB1234" in employee.body


def test_an_unknown_cab_still_reads_naturally() -> None:
    """No "Cab None is on the way"."""
    messages = build(NotificationType.request_assigned, {})
    employee = next(m for m in messages if m.recipient is Recipient.employee)
    assert "None" not in employee.body
    assert employee.body.startswith("Your cab")


def test_the_eta_is_included_when_known() -> None:
    messages = build(NotificationType.request_assigned, {"pickup_eta_minutes": 7})
    employee = next(m for m in messages if m.recipient is Recipient.employee)
    assert "7 min" in employee.body


def test_no_message_is_empty() -> None:
    for event in TEMPLATES:
        for message in build(event):
            assert message.title.strip()
            assert message.body.strip()


def test_an_unknown_event_produces_nothing_rather_than_raising() -> None:
    """A caller naming an event with no template must not take down the request."""
    assert build(NotificationType.driver_new_trip) == []


def test_the_context_travels_with_the_message() -> None:
    """The app needs the ids to deep-link into the right trip."""
    context = {"trip_id": "abc", "request_id": "def"}
    messages = build(NotificationType.cab_arrived, context)
    assert messages[0].data["trip_id"] == "abc"
