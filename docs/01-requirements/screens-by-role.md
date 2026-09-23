# Screens by role

One Flutter app. After login, `GET /auth/me` returns roles and permissions; the app builds navigation from them. Screen IDs are used in code (`lib/features/<area>/screens/`) and tests.

## Common
| ID | Screen | Content / actions |
|---|---|---|
| C-01 | Splash | Version check; token refresh; route by role. |
| C-02 | Login | Phone input (+91 default) → OTP input (6 digits, resend after 30 s). |
| C-03 | Role switcher | Shown only if user has >1 role. Sets active role. |
| C-04 | Profile | Name, phone, active role, language (English/Hindi — Phase 2), logout. |
| C-05 | Notifications | List of past notifications. |
| C-06 | Map attribution | "© OpenStreetMap contributors" visible bottom-right on every map, never covered by sheets, cards or controls. |

**No address search in Phase 1** (ADR-0010 §A1): no screen has an address search box or autocomplete. Locations are set with a draggable map pin plus free-text landmark, or chosen from saved places. This applies to E-02, S-08, A-04 and L-02.

## Employee
| ID | Screen | Content / actions |
|---|---|---|
| E-01 | Home | Active request/trip card (status, ETA, cab no.) or "Request a cab" button; next scheduled request. |
| E-02 | Request form | Direction toggle; time: Now / pick time; pickup/drop pin on map (drag) — **no address search box**; saved places; landmark text; urgency (default medium); submit. |
| E-03 | Request confirmation | Request ID, summary, status "Finding your cab", cancel button. |
| E-04 | Live tracking | Map with cab marker, own pin, route; bottom sheet: vehicle no., model, driver name, call button, ETA, status; SOS button; cancel (before arrival). |
| E-05 | Trip completed | Duration, wait time, rating 1–5, comment. |
| E-06 | History | List (90 days), each with date, direction, wait, rating. |
| E-07 | Saved places | Home (set by client admin, editable request pending approval — Phase 2), other places. |
| E-08 | Ride offer (Phase 4) | Offer card: time, co-rider count, guarantee; Accept / Reject (+ preferred time). |

## Driver
| ID | Screen | Content / actions |
|---|---|---|
| D-01 | Duty home | Big On/Off duty switch; vehicle linked; today's trips count; GPS status indicator. |
| D-02 | Permission explainer | Why background location is needed; request permission. |
| D-03 | Trip list | Current trip on top, upcoming below. |
| D-04 | Trip detail | Ordered stops (pickup/drop, rider first name, landmark, planned time); status buttons per stop; call rider; navigate. |
| D-05 | Navigation map | In-app route to next stop; "Open external nav". |
| D-06 | Report issue | Type selector + note; sends immediately (queues offline). |
| D-07 | Offline banner | Shown when offline; count of queued events. |

## Supervisor
| ID | Screen | Content / actions |
|---|---|---|
| S-01 | Live dispatch map | All vehicles (colour by state), pending requests as pins; filter by client/zone; tap vehicle → details and current trip. |
| S-02 | Pending queue | Requests sorted by wait; live timers; red when over threshold; tap → assign panel. |
| S-03 | Assign panel | Request details; candidate vehicles with ETA to pickup, seats free, added minutes for existing riders; Manual assign. Phase 2: ranked suggestions with reasons, Approve. |
| S-04 | Trips board | Active trips with stops, progress, delays. |
| S-05 | Override sheet (Phase 2) | Actions: reassign, lock, force priority, block pooling, hold, cancel, vehicle out of service; impact preview; reason picker; expiry (end of shift default). |
| S-06 | Modes (Phase 2) | Table of scopes and modes; add scope; emergency pause switch at top (Phase 1). |
| S-07 | Alerts | SOS, driver issues, stale GPS, failsafe actions, mode-switch prompts. SOS alerts are full-screen with sound. |
| S-08 | Create request on behalf | Pick employee → same form as E-02. |

## Operator admin
| ID | Screen | Content / actions |
|---|---|---|
| A-01 | Dashboard | Today: trips, pending, median wait, vehicles on duty. |
| A-02 | Vehicles | List + add/edit (number, model, type, capacity, status). |
| A-03 | Drivers | List + add/edit (name, phone, licence no. last 4 digits only, linked vehicle). |
| A-04 | Clients & offices | List + add/edit; office pin on map (pin only, no address search). |
| A-05 | Users | Supervisors and client admins; invite by phone. |
| A-06 | Zones (Phase 2) | Draw/edit polygons. |
| A-07 | Reports | Date range; per client/driver; CSV export. |
| A-08 | Settings | Operator config values from `allocation-rules.md` (with allowed ranges). |

## Client admin
| ID | Screen | Content / actions |
|---|---|---|
| L-01 | Employees | List, search, add/edit, deactivate; CSV import with validation report. |
| L-02 | Employee form | Name, phone, office, home pin (map pin + landmark, no address search), priority 1–10, VIP, pooling opt-out allowed. |
| L-03 | Policies (Phase 2) | Pooling, night-safety rule and hours, stricter detour limit. |
| L-04 | Reports | Own employees' trips, waits, no-shows. |

## Layout rules
- Phone-first. Supervisor and admin screens must also work on tablets and Flutter web (Phase 2+): use responsive layouts (list + detail side by side on wide screens).
- All times shown in IST (Asia/Kolkata), 12-hour format with am/pm. Store and transmit UTC.
- Minimum touch target 48 dp; driver screens use large buttons (≥ 64 dp high).
