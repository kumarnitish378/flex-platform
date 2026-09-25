"""What each transition tells whom (B16, `trip-lifecycle.md` section 6, EMP-05).

Pure: a table from "what happened" to "who hears what". No database, no push client, no
clock, so the wording and the targeting can be checked exhaustively in microseconds - and
the wording matters, because this text arrives on a phone at 7am and is the entire product
for the person reading it.

`state_machines.py` already returns *who* to notify with every transition. This decides
what they are told.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from app.domain.state_machines import Recipient


class NotificationType(StrEnum):
    """Stable keys. The app switches on these; the wording may change, these may not."""

    request_assigned = "request_assigned"
    cab_nearby = "cab_nearby"
    cab_arrived = "cab_arrived"
    trip_completed = "trip_completed"
    request_reassigned = "request_reassigned"
    request_cancelled = "request_cancelled"
    request_near_expiry = "request_near_expiry"
    trip_aborted = "trip_aborted"
    sos = "sos"
    driver_new_trip = "driver_new_trip"
    driver_trip_changed = "driver_trip_changed"


#: Notifications a supervisor must not be able to sleep through.
HIGH_PRIORITY = frozenset({NotificationType.sos, NotificationType.trip_aborted})


@dataclass(frozen=True, slots=True)
class Notification:
    """One message for one recipient role, ready to be addressed to actual users."""

    type: NotificationType
    recipient: Recipient
    title: str
    body: str
    data: dict[str, Any] = field(default_factory=dict)

    @property
    def high_priority(self) -> bool:
        return self.type in HIGH_PRIORITY


def _cab(context: dict[str, Any]) -> str:
    """How to name the vehicle in a message. Registration if known, else a plain word."""
    registration = context.get("registration_no")
    return f"Cab {registration}" if registration else "Your cab"


def request_assigned(context: dict[str, Any]) -> list[Notification]:
    """`request -> assigned | Employee (push), driver (push)`."""
    eta = context.get("pickup_eta_minutes")
    when = f" and is about {int(eta)} min away" if eta is not None else ""
    return [
        Notification(
            NotificationType.request_assigned,
            Recipient.employee,
            "Cab assigned",
            f"{_cab(context)} is on the way{when}.",
            context,
        ),
        Notification(
            NotificationType.driver_new_trip,
            Recipient.driver,
            "New trip",
            _pickup_line(context),
            context,
        ),
    ]


def cab_nearby(context: dict[str, Any]) -> list[Notification]:
    """`stop ETA <= 5 min | Employee` (EMP-05)."""
    minutes = int(context.get("minutes_away", 5))
    return [
        Notification(
            NotificationType.cab_nearby,
            Recipient.employee,
            "Cab nearby",
            f"{_cab(context)} is about {minutes} min away.",
            context,
        )
    ]


def cab_arrived(context: dict[str, Any]) -> list[Notification]:
    """`stop -> arrived | Employee`."""
    return [
        Notification(
            NotificationType.cab_arrived,
            Recipient.employee,
            "Cab arrived",
            f"{_cab(context)} is waiting at your pickup point.",
            context,
        )
    ]


def trip_completed(context: dict[str, Any]) -> list[Notification]:
    """EMP-05 lists trip completed among the statuses a rider is told about."""
    return [
        Notification(
            NotificationType.trip_completed,
            Recipient.employee,
            "Trip complete",
            "You have been dropped off. Thanks for riding.",
            context,
        )
    ]


def request_reassigned(context: dict[str, Any]) -> list[Notification]:
    """`request reassigned | Employee (new cab), old driver, new driver`."""
    return [
        Notification(
            NotificationType.request_reassigned,
            Recipient.employee,
            "Cab changed",
            f"Your ride has moved to {_cab(context).lower()}.",
            context,
        ),
        Notification(
            NotificationType.driver_trip_changed,
            Recipient.previous_driver,
            "Trip removed",
            "A rider has been moved off your trip.",
            context,
        ),
        Notification(
            NotificationType.driver_new_trip,
            Recipient.driver,
            "New trip",
            _pickup_line(context),
            context,
        ),
    ]


def request_cancelled(context: dict[str, Any]) -> list[Notification]:
    """Two rows of section 6 at once, told apart by who cancelled.

    Cancelled by the employee: the driver and supervisor hear. Cancelled by the operator:
    the employee hears, **with the reason** - being stood up without one is the worst
    version of this message.
    """
    reason = context.get("reason")
    if context.get("cancelled_by_employee"):
        return [
            Notification(
                NotificationType.request_cancelled,
                Recipient.driver,
                "Ride cancelled",
                "A rider has cancelled. Check your updated trip.",
                context,
            ),
            Notification(
                NotificationType.request_cancelled,
                Recipient.supervisor,
                "Ride cancelled",
                "An employee cancelled their request.",
                context,
            ),
        ]

    because = f" Reason: {reason}." if reason else ""
    return [
        Notification(
            NotificationType.request_cancelled,
            Recipient.employee,
            "Ride cancelled",
            f"Your ride has been cancelled.{because}",
            context,
        )
    ]


def request_near_expiry(context: dict[str, Any]) -> list[Notification]:
    """`request near expiry (15 min before) | Supervisor`."""
    return [
        Notification(
            NotificationType.request_near_expiry,
            Recipient.supervisor,
            "Request about to expire",
            "An unassigned request expires in 15 minutes.",
            context,
        )
    ]


def trip_aborted(context: dict[str, Any]) -> list[Notification]:
    """`trip aborted, SOS | Supervisor, operator admin (high priority)`."""
    return [
        Notification(
            NotificationType.trip_aborted,
            Recipient.supervisor,
            "Trip aborted",
            "A trip was stopped mid-way. Riders need re-dispatching.",
            context,
        ),
        Notification(
            NotificationType.trip_aborted,
            Recipient.operator_admin,
            "Trip aborted",
            "A trip was stopped mid-way.",
            context,
        ),
    ]


def sos(context: dict[str, Any]) -> list[Notification]:
    """`trip aborted, SOS | Supervisor, operator admin (high priority)`."""
    return [
        Notification(
            NotificationType.sos,
            Recipient.supervisor,
            "SOS",
            "Someone has triggered an emergency alert.",
            context,
        ),
        Notification(
            NotificationType.sos,
            Recipient.operator_admin,
            "SOS",
            "Someone has triggered an emergency alert.",
            context,
        ),
    ]


def _pickup_line(context: dict[str, Any]) -> str:
    landmark = context.get("landmark")
    where = f" near {landmark}" if landmark else ""
    return f"A rider has been added to your trip{where}."


#: Every row of `trip-lifecycle.md` section 6, by name. A caller names the event; it does
#: not build messages itself, so the wording lives in exactly one place.
TEMPLATES = {
    NotificationType.request_assigned: request_assigned,
    NotificationType.cab_nearby: cab_nearby,
    NotificationType.cab_arrived: cab_arrived,
    NotificationType.trip_completed: trip_completed,
    NotificationType.request_reassigned: request_reassigned,
    NotificationType.request_cancelled: request_cancelled,
    NotificationType.request_near_expiry: request_near_expiry,
    NotificationType.trip_aborted: trip_aborted,
    NotificationType.sos: sos,
}


def build(event: NotificationType, context: dict[str, Any] | None = None) -> list[Notification]:
    """The notifications one event produces, or an empty list if it produces none."""
    template = TEMPLATES.get(event)
    return template(context or {}) if template is not None else []
