"""The permission table.

`roles-and-permissions.md` (Implementation notes): permissions live in **one module as a
table, not scattered `if` statements**. This file is that table; B04 adds the FastAPI
dependency that enforces it per route.

Two things the matrix expresses that a flat allow-list cannot, and which are therefore
*not* decided here:

* **Scope** (the 🔸 rows) — "own client", "own trips", "self". Holding
  `request.cancel` does not say *which* requests; the service layer narrows by
  `client_id` / `employee_id` / `driver_id` from the active role. A permission check
  alone is never sufficient authorisation for a scoped row.
* **Personal-data exposure** — who may see a phone number or a home location, and for
  how long. Those rules are time-bounded (assignment until trip end) and belong to the
  serialisers, not to a static table.
"""

from __future__ import annotations

from enum import StrEnum

from app.domain.enums import Role


class Permission(StrEnum):
    """One value per row of the permission matrix."""

    # Platform and operator administration
    operator_create = "operator.create"
    operator_user_manage = "operator.user.manage"
    vehicle_manage = "vehicle.manage"
    vehicle_status_manage = "vehicle.status.manage"
    client_manage = "client.manage"
    client_policy_manage = "client.policy.manage"
    employee_manage = "employee.manage"
    zone_manage = "zone.manage"
    config_manage = "config.manage"

    # Dispatch
    mode_set = "dispatch.mode.set"
    automation_pause = "dispatch.automation.pause"
    live_map_view = "dispatch.map.view"
    request_queue_view = "dispatch.requests.view"
    assign = "dispatch.assign"
    override = "dispatch.override"

    # Driver
    duty_manage = "driver.duty.manage"
    trip_view = "trip.view"
    trip_action = "trip.action"
    driver_issue_report = "driver.issue.report"

    # Rider
    request_create = "request.create"
    request_cancel = "request.cancel"
    ride_track = "ride.track"
    sos_trigger = "sos.trigger"
    offer_respond = "offer.respond"

    # Reporting
    report_view = "report.view"
    report_operational_view = "report.operational.view"
    billing_view = "billing.view"

    # Simulator
    sim_control = "sim.control"


P = Permission

#: Role -> permissions, transcribed row by row from the matrix in
#: `roles-and-permissions.md`. A 🔸 cell grants the permission; the scope limit is
#: applied by the service, as explained in the module docstring.
ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.platform_admin: frozenset(
        {
            P.operator_create,
            P.operator_user_manage,
            P.vehicle_manage,
            P.vehicle_status_manage,
            P.client_manage,
            P.client_policy_manage,
            P.employee_manage,
            P.zone_manage,
            P.config_manage,
            P.mode_set,
            P.automation_pause,
            P.live_map_view,
            P.request_queue_view,
            P.assign,
            P.override,
            P.trip_view,
            P.trip_action,
            P.request_cancel,
            P.report_view,
            P.report_operational_view,
            P.billing_view,
            # "Run simulator / time control: 🔸 sim env only" - the environment guard is
            # in settings (SIMCTL_ENABLED requires APP_ENV=sim), not in this table.
            P.sim_control,
        }
    ),
    Role.operator_admin: frozenset(
        {
            P.operator_user_manage,
            P.vehicle_manage,
            P.vehicle_status_manage,
            P.client_manage,
            P.client_policy_manage,
            P.employee_manage,
            P.zone_manage,
            P.config_manage,
            P.mode_set,
            P.automation_pause,
            P.live_map_view,
            P.request_queue_view,
            P.assign,
            P.override,
            P.trip_view,
            P.trip_action,
            P.request_create,
            P.request_cancel,
            P.report_view,
            P.report_operational_view,
            P.billing_view,
        }
    ),
    Role.supervisor: frozenset(
        {
            # "Manage vehicles: 🔸 status only" - status, not the vehicle record.
            P.vehicle_status_manage,
            P.mode_set,
            P.automation_pause,
            P.live_map_view,
            P.request_queue_view,
            P.assign,
            P.override,
            P.trip_view,
            P.trip_action,
            P.request_create,
            P.request_cancel,
            P.report_operational_view,
        }
    ),
    Role.driver: frozenset(
        {
            P.duty_manage,
            P.trip_view,
            P.trip_action,
            P.driver_issue_report,
            P.sos_trigger,
        }
    ),
    Role.client_admin: frozenset(
        {
            P.client_policy_manage,
            P.employee_manage,
            P.request_queue_view,
            P.request_create,
            P.request_cancel,
            P.report_view,
            P.billing_view,
        }
    ),
    Role.employee: frozenset(
        {
            P.request_create,
            P.request_cancel,
            P.ride_track,
            P.sos_trigger,
            P.offer_respond,
        }
    ),
}


def permissions_for(role: Role) -> frozenset[Permission]:
    return ROLE_PERMISSIONS.get(role, frozenset())


def has_permission(role: Role, permission: Permission) -> bool:
    return permission in permissions_for(role)
