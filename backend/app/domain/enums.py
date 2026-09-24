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
