# Allocation rules

Pipeline: **request → hard-rule filter → candidate vehicles → cost scoring → mode (manual / semi-auto / full-auto) → assign**.
Phase 1 uses only candidate listing with ETAs (manual). Phase 2 adds rules + scoring for suggestions. Phase 3 adds pooling optimizer and full auto. Phase 4 adds predictions and offers.

All numbers below are **config keys** (table `operator_config`, overridable per client where marked). Code must read them from config.

## 1. Config keys and defaults
| Key | Default | Range | Per client | Meaning |
|---|---|---|---|---|
| `candidate_max_eta_minutes` | 20 | 5–60 | no | A vehicle is a candidate if it can reach pickup within this time. |
| `pickup_window_minutes` | 10 | 0–30 | yes | Allowed ± deviation from requested pickup time for `to_office`. |
| `hold_window_min_minutes` | 10 | 0–30 | yes | Minimum pooling hold for `from_office` (non-high urgency). |
| `hold_window_max_minutes` | 30 | 0–60 | yes | Maximum pooling hold for `from_office`. |
| `max_detour_factor` | 1.5 | 1.0–3.0 | yes (stricter only) | Rider ride time ≤ factor × direct time. |
| `max_detour_minutes` | 15 | 0–60 | yes (stricter only) | Rider ride time ≤ direct time + this. |
| `enroute_reuse_max_eta_minutes` | 5 | 0–15 | no | An assigned/en-route vehicle may take a new same-direction rider if it reaches them within this. |
| `retry_after_minutes` | 10 | 5–60 | no | How often an already-escalated request widens its search again. The *first* escalation is at `alert_wait_minutes`. |
| `retry_eta_widen_minutes` | 10 | 0–30 | no | Each escalation widens `candidate_max_eta_minutes` for that request by this. |
| `retry_eta_max_minutes` | 45 | 5–120 | no | The widest the candidate ETA ceiling may ever get, however long the wait. |
| `batch_window_seconds` | 45 | 10–120 | no | Micro-batch window for optimizer runs. |
| `optimizer_time_limit_seconds` | 10 | 1–60 | no | Hard cap on one DARP run. No solution within it falls back to single-insertion greedy. |
| `stop_dwell_seconds` | 60 | 0–300 | no | Seconds a cab spends at each stop while riders get in or out; the optimizer plans with it (B31). **Provisional** - the real figure is a pilot measurement. |
| `billing_no_show_billable` | true | bool | no | Whether a no-show is on the invoice (B38). **Provisional** (OQ-01/OQ-03). |
| `billing_late_cancel_billable` | false | bool | no | Whether a cancellation after assignment is on the invoice (B38). **Provisional.** |
| `billing_distance_basis` | `trip_share` | `trip_share` / `direct` | no | Kilometres billed per ride: an equal share of the trip's measured distance, or the rider's own journey (B38). **Provisional.** |
| `optimizer_failure_threshold` | 3 | 1–10 | no | This many most-recent optimizer runs all failing means it is down (`control-model.md` §6). **Provisional.** |
| `optimizer_failure_memory_minutes` | 15 | 1–120 | no | A failed optimizer run older than this says nothing about now. **Provisional.** |
| `optimizer_stall_seconds` | 180 | 60–3600 | no | A request ready this long with no optimizer run since means the worker is not running; never less than three batch windows. **Provisional.** |
| `mode_prompt_window_minutes` | 15 | 5–60 | no | How far back a mode-switch prompt looks (`control-model.md` §5). |
| `mode_prompt_rejected_share` | 0.30 | 0.05–1.0 | no | Prompt when at least this share of a scope's suggestions were rejected. |
| `mode_prompt_eta_error_minutes` | 10 | 1–60 | no | Prompt when the median pickup-ETA error in a scope exceeds this. |
| `mode_prompt_pending_multiple` | 2.0 | 1.0–10.0 | no | Prompt when pending requests exceed this multiple of normal for the time slot. |
| `mode_prompt_fleet_share` | 0.20 | 0.05–1.0 | no | Prompt when this share of the fleet is stale or out of service. |
| `mode_prompt_min_samples` | 5 | 1–50 | no | Fewest decisions / pickups / pending requests a ratio is judged on. **Provisional** (§5 names none). |
| `mode_prompt_baseline_days` | 14 | 1–60 | no | Past days that define "normal" pending requests for a time slot. |
| `failsafe_timeout_seconds` | 180 | 30–900 | no | Semi-auto suggestion timeout. |
| `failsafe_action` | `auto_assign` | `auto_assign` / `escalate` | no | What happens on timeout. |
| `alert_wait_minutes` | 20 | 5–60 | no | A waiting request has waited too long: the board turns it red **and escalation starts** (ADR-0023). |
| `request_expiry_minutes` | 120 | 30–480 | no | Unassigned request expires. |
| `no_show_wait_minutes` | 5 | 1–15 | yes | Driver wait before no-show allowed. |
| `stale_gps_seconds` | 150 | 20–300 | no | Vehicle considered stale. Must be at least 1.5 x `gps_heartbeat_seconds` (the config service refuses less). Was 60 until the phone moved to a distance filter + 60 s heartbeat. |
| `gps_distance_filter_m` | 5 | 1–100 | no | The driver app publishes a position after moving this far. Sent to the app in `/driver/duty`. |
| `gps_heartbeat_seconds` | 60 | 15–120 | no | While stationary the app publishes a heartbeat this often, so a parked cab is not stale. |
| `weight_wait` | 1.0 | 0–10 | no | Weight of new rider's wait minutes. |
| `weight_empty_km` | 2.0 | 0–20 | no | Minutes-equivalent per empty km. |
| `cost_new_vehicle` | 15.0 | 0–120 | no | Minutes-equivalent cost of deploying an idle vehicle. |
| `urgency_factor_high` | 3.0 | 1–10 | no | |
| `urgency_factor_medium` | 1.5 | 1–10 | no | |
| `urgency_factor_low` | 1.0 | 0.1–10 | no | |
| `night_safety_enabled` | false | bool | yes | Enable night rules below. |
| `night_safety_start` / `_end` | 20:00 / 06:00 | time | yes | Night window (IST). |

## 2. Hard rules (filters — never traded off in the cost)
Applied in this order. A candidate that fails any rule is removed. If no candidate remains, the request stays `queued` and the supervisor is alerted.

1. **Vehicle state:** only `available` or `on_trip` (for en-route reuse) vehicles with fresh GPS; never `out_of_service`, `off_duty`, `stale`.
2. **Automation pause:** if `automation_paused`, no automatic assignment at all (manual only).
3. **Locks:** a locked request can only go to its locked vehicle. A trip with `pooling_blocked` accepts no new riders.
4. **VIP:** if `employee.is_vip`: only `vip` vehicles; no pooling (trip exclusive); no hold window; assign immediately. If no VIP vehicle is available: alert supervisor immediately; **do not** auto-assign a non-VIP vehicle (supervisor decides — open question OQ-12).
5. **Capacity:** riders on board at any point ≤ `seat_capacity`.
6. **Direction compatibility:** pooled riders share direction and office.
7. **Detour limits:** for every rider on the resulting trip: ride time ≤ min(direct × `max_detour_factor`, direct + `max_detour_minutes`) using the stricter client value.
8. **Time window:** `to_office` pickup ETA within requested time ± `pickup_window_minutes`; must reach office by requested arrival time if given.
9. **Opt-out:** request marked `no_sharing` → exclusive trip.
10. **High priority / high urgency:** `priority ≤ 2` or `urgency = high` → no hold window.
11. **Night safety (if enabled, client policy):** during night window, a trip's sequence must not leave a rider flagged `night_escort_required` as first pickup or last drop without an escort (exact client policy configurable; see OQ-10). Overrides require explicit reason.

## 3. Candidates
- Idle vehicles: `available`, ETA to pickup ≤ `candidate_max_eta_minutes` (OSRM time, adjusted by speed profile).
- En-route reuse: vehicles on a trip of the same direction whose route passes within `enroute_reuse_max_eta_minutes` of the pickup and satisfy all hard rules after insertion. **"Passes within" is the extra driving** the cab does to collect the rider where the insertion puts them - `dur(a, p) + dur(p, b) - dur(a, b)` for the neighbouring stops `a` and `b` (B33) - not the straight ETA from where the cab is now. A cab about to drive past the rider's door is a candidate however far off it is; one that must double back is not however near. When the cab's position is unknown the straight ETA is the fallback. The rider's pickup time for rule 8 is likewise the time the cab reaches them along that route.
- Return-trip reuse: vehicles that just completed a drop (become `available`) are ordinary idle candidates; no special rule needed.
- "Nearby" is always **time-based (ETA)**, never straight-line distance.
- Each candidate kind is judged against its own ceiling, and only its own: an idle cab on
  `candidate_max_eta_minutes`, an en-route one on `enroute_reuse_max_eta_minutes`. A twenty-minute
  diversion by a cab with riders aboard is a different proposition from a twenty-minute approach by an
  empty one.

### 3.1 When nobody has been served
A request still `queued` once it has waited `alert_wait_minutes` - the operator's own answer to "how long
is too long", and the threshold their board already turns red at - is **escalated**, and again every
`retry_after_minutes` after that (ADR-0019, ADR-0023). It stays one request with one waiting clock — the number the pilot is
judged on must keep counting from the original ask, so nothing here cancels and re-creates it.

Each escalation:
- widens that request's candidate ETA ceiling by `retry_eta_widen_minutes`, up to `retry_eta_max_minutes`.
  A rider who has waited half an hour is better served by a cab twenty-five minutes away than by the
  rule that says twenty;
- stamps `escalated_at`, which is what a board renders as "late". **`urgency` is not touched** - that is
  the rider's own answer and the platform never rewrites it (ADR-0021);
- refreshes **one rolling `request_unassigned` alert per operator**, carrying how many riders are unserved
  and the longest wait, which resolves itself once nobody is (ADR-0022). One alert per request put 142 rows
  on the board in a single surge run;
- sets `forced_priority`, which in Phase 1 is **only a flag**: the hold window it short-circuits
  (section 2 rule 10) is not implemented yet, and the Phase 2 cost function is what will weigh it.

Escalation only ever changes how hard the platform looks and who it tells. It never assigns, and it
never cancels and re-creates the request - that would reset the waiting clock.

The widening is derived from how long the request has waited, so it needs no stored state and cannot
drift from what the board shows. In Phase 1 the ceilings are **reported, not enforced** (ADR-0011), so
widening removes a flag from a cab a supervisor could already have chosen; it becomes a real filter when
the Phase 2 optimizer uses the same numbers.

## 4. Cost function (minutes-equivalent)
For assigning request *r* to vehicle *v* (single insertion, Phase 2):

```
cost(r, v) = weight_wait × w_r × wait_r
           + Σ_i ( w_i × added_minutes_i )        over riders already on v's trip
           + weight_empty_km × empty_km_added
           + cost_new_vehicle × [v is idle, i.e. new trip]
```
- `wait_r` = minutes from requested time (or now if later) to pickup ETA.
- `added_minutes_i` = increase in rider i's ride time (detour).
- Traffic is already inside ETAs — **never add a separate traffic term**.
- Lowest cost wins. Ties → lower ETA → lower vehicle id (deterministic).

### Rider weight
```
w = ((11 − priority) / 10) × urgency_factor
```
Examples: priority 1 + high = 3.0 · priority 5 + medium = 0.9 · priority 10 + low = 0.1.

## 5. Suggestion reasons (Phase 2)
Each suggestion lists: ETA to pickup, seats free after assignment, added minutes per existing rider, empty km added, whether it opens a new trip, and cost. Shown as plain text, e.g. "8 min away · 2 seats left · +4 min for Rahul · reuses trip T-102".

## 6. Pooling optimizer (Phase 3)
- Runs when a batch window closes (B30): the window opens when the oldest ready request became ready and lasts `batch_window_seconds`, with at least one window between runs. Each run covers, for the operator, all `queued` requests whose hold window has elapsed or which are no-hold, plus modifiable (`planned`/`dispatched`, not locked) trips.
- Model: Pickup-and-Delivery Problem with Time Windows and capacities (Dial-a-Ride), solved with **Google OR-Tools routing** using OSRM time matrices.
- Objective matches the cost function; hard rules become constraints (capacity, time windows, max ride time per rider, vehicle types, exclusivity).
- Time limit per run: 10 s (config `optimizer_time_limit_seconds`). If no solution, fall back to single-insertion greedy using §4.
- Output = proposed trips. In `full_auto` scopes they are applied; in `semi_auto` they become suggestions; in `manual` they are shown as hints only.
- Never modifies locked requests, `pooling_blocked` trips, or trips `in_progress` except inserting riders that satisfy all rules.

### Evening hold window
- `from_office` requests (not VIP, not high priority/urgency, not opt-out) wait between `hold_window_min_minutes` and `hold_window_max_minutes`.
- Phase 3: fixed at the min value (B29). The window runs from the later of `queued_at` and the requested time, ends at the instant it elapses, and binds automatic assignment only - a supervisor may still send a cab early. A client policy that forbids pooling is exempt, as is any request under `forced_priority` (§3.1).
- Phase 4: dynamic — hold while predicted probability of a compatible rider arriving in the next *t* minutes × expected savings > rider's weighted wait cost.

## 7. Ride offers (Phase 4)
- Predicted demand per employee (ready time distribution) → candidate pooled trips planned ahead.
- Offer sent only if model confidence ≥ `offer_min_confidence` (default 0.7), max one offer per employee per direction per day.
- Accepted offer → request created, locked to planned trip, pickup time guaranteed within ± `pickup_window_minutes`.
- Rejected → logged with optional preferred time; on-demand requests always remain possible.

## 8. Worked example
Request R (priority 5, medium → w = 0.9), requested now.
- Vehicle A idle, ETA 12 min, empty km 4: cost = 1.0×0.9×12 + 0 + 2.0×4 + 15 = 10.8 + 8 + 15 = **33.8**
- Vehicle B on trip with rider X (w = 1.5), ETA to R 7 min, adds 5 min to X, empty km 0: cost = 0.9×7 + 1.5×5 + 0 + 0 = 6.3 + 7.5 = **13.8** → B chosen (if detour limits hold for X and R).
