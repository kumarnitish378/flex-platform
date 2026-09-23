# Roles and permissions

The universal app renders screens from the roles returned by `GET /auth/me`. **The backend checks permissions on every request.** Hiding a screen is not a security control.

## Roles
| Role | Code | Belongs to | Description |
|---|---|---|---|
| Platform admin | `platform_admin` | Platform | Us. Creates operators, support access. |
| Operator admin | `operator_admin` | Operator | Owner/manager of a cab company. |
| Supervisor | `supervisor` | Operator | Dispatcher. |
| Driver | `driver` | Operator | Drives assigned trips. |
| Client admin | `client_admin` | Client (of an operator) | Manages a company's employees and policies. |
| Employee | `employee` | Client | Rider. |

A user can hold several roles (e.g. supervisor + employee). The app shows a role switcher when a user has more than one role. Every API call acts under the **active role** sent in header `X-Active-Role`; the server verifies the user holds it.

## Data scoping (tenancy)
- Every query is scoped by `operator_id` from the token. No cross-operator access except `platform_admin`.
- `client_admin` and `employee` are further scoped to their `client_id`.
- `driver` sees only trips assigned to them, and only rider details for active/upcoming trips.
- `employee` sees only their own requests and the vehicle/driver of their current trip.

## Permission matrix
Legend: ✅ allowed · 🔸 own/scoped only · ❌ denied

| Action | platform_admin | operator_admin | supervisor | driver | client_admin | employee |
|---|---|---|---|---|---|---|
| Create operator | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Manage operator users (supervisors, drivers) | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Manage vehicles | ✅ | ✅ | 🔸 status only | ❌ | ❌ | ❌ |
| Manage clients, offices | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Manage client policies (safety, pooling, VIP rules) | ✅ | ✅ | ❌ | ❌ | 🔸 own client | ❌ |
| Manage employees (roster, priority, VIP) | ✅ | ✅ | ❌ | ❌ | 🔸 own client | ❌ |
| Manage zones | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Set dispatch modes | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Emergency pause automation | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| View live map (all vehicles) | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| View pending requests | ✅ | ✅ | ✅ | ❌ | 🔸 own client | ❌ |
| Assign / approve suggestion | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Override (reassign, lock, block pooling, hold, cancel, force priority) | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Take vehicle out of service | ✅ | ✅ | ✅ | 🔸 report issue | ❌ | ❌ |
| Go on/off duty, share GPS | ❌ | ❌ | ❌ | 🔸 self | ❌ | ❌ |
| View assigned trips | ✅ | ✅ | ✅ | 🔸 own | ❌ | ❌ |
| Mark arrived / picked up / dropped / no-show | ✅ | ✅ | ✅ | 🔸 own trips | ❌ | ❌ |
| Create ride request | ❌ | ✅ (on behalf) | ✅ (on behalf) | ❌ | 🔸 on behalf, own client | 🔸 self |
| Cancel ride request | ✅ | ✅ | ✅ | ❌ | 🔸 own client | 🔸 self, before pickup |
| Track own ride | ❌ | ❌ | ❌ | ❌ | ❌ | 🔸 self |
| Trigger SOS | ❌ | ❌ | ❌ | 🔸 | ❌ | 🔸 |
| Respond to ride offer (Phase 4) | ❌ | ❌ | ❌ | ❌ | ❌ | 🔸 self |
| View reports | ✅ | ✅ | 🔸 operational | ❌ | 🔸 own client | ❌ |
| View billing | ✅ | ✅ | ❌ | ❌ | 🔸 own client | ❌ |
| Run simulator / time control | 🔸 sim env only | ❌ | ❌ | ❌ | ❌ | ❌ |

## Personal data exposure rules
| Data | Who can see it |
|---|---|
| Employee home location | Operator admin, supervisor, assigned driver (active trip only), the employee |
| Employee phone | Operator admin, supervisor, assigned driver only from assignment until trip end |
| Driver phone | Assigned employees only from assignment until trip end; operator admin; supervisor |
| Live vehicle location | Supervisor/admin always; employee only for their active trip, from assignment until pickup/drop |
| Trip history | Employee (own), driver (own, 30 days in app), client admin (own client), operator |

## Implementation notes
- Permissions are defined in one module (`backend/app/auth/permissions.py`) as a table, not scattered `if` statements.
- Each endpoint declares its required permission via a FastAPI dependency.
- Tests: every endpoint has at least one "denied" test for a role that must not access it.
