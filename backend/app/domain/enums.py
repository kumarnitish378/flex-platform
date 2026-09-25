"""Enumerations shared by the domain and the database.

Kept in `app/domain` so they stay importable without a database or a web framework.
Values are exactly the strings in `data-model.md` and `roles-and-permissions.md`; they
appear in the API contract, so changing one is a breaking change.
"""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    """`roles-and-permissions.md` §Roles."""

    platform_admin = "platform_admin"
    operator_admin = "operator_admin"
    supervisor = "supervisor"
    driver = "driver"
    client_admin = "client_admin"
    employee = "employee"


#: Roles scoped to one client rather than the whole operator.
CLIENT_SCOPED_ROLES = frozenset({Role.client_admin, Role.employee})

#: The only role that may exist without an operator.
PLATFORM_ROLES = frozenset({Role.platform_admin})


class OperatorStatus(StrEnum):
    active = "active"
    suspended = "suspended"


class UserStatus(StrEnum):
    active = "active"
    suspended = "suspended"


class ClientStatus(StrEnum):
    active = "active"
    suspended = "suspended"


class DevicePlatform(StrEnum):
    android = "android"
    ios = "ios"
    web = "web"


class VehicleType(StrEnum):
    """`data-model.md` Fleet; api-spec `VehicleType`."""

    sedan_4 = "sedan_4"
    suv_6 = "suv_6"
    vip = "vip"


class TrackerType(StrEnum):
    app = "app"
    esp32 = "esp32"


class Direction(StrEnum):
    """`glossary.md`: which way the rider is going."""

    to_office = "to_office"
    from_office = "from_office"


class Urgency(StrEnum):
    high = "high"
    medium = "medium"
    low = "low"


class RequestChannel(StrEnum):
    """How the request reached us (`data-model.md`, ride_request.channel)."""

    app = "app"
    supervisor = "supervisor"
    offer = "offer"
    sim = "sim"


class ActorType(StrEnum):
    """Who caused an event (`data-model.md`, ride_request_event.actor_type)."""

    employee = "employee"
    driver = "driver"
    supervisor = "supervisor"
    system = "system"
    system_failsafe = "system_failsafe"
    optimizer = "optimizer"


class AlertType(StrEnum):
    """`data-model.md`, alert.type. B09 raises `request_near_expiry`; B17 adds the rest."""

    sos = "sos"
    driver_issue = "driver_issue"
    request_near_expiry = "request_near_expiry"
    vip_no_vehicle = "vip_no_vehicle"
    failsafe = "failsafe"
    stale_vehicle = "stale_vehicle"
    mode_prompt = "mode_prompt"
    system = "system"


class AlertSeverity(StrEnum):
    info = "info"
    warning = "warning"
    critical = "critical"


class AlertStatus(StrEnum):
    open = "open"
    acknowledged = "acknowledged"
    resolved = "resolved"


class GpsSource(StrEnum):
    """`mqtt-topics.md`: where a ping came from."""

    app = "app"
    esp32 = "esp32"
    sim = "sim"
