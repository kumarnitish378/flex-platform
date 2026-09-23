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
| `batch_window_seconds` | 45 | 10–120 | no | Micro-batch window for optimizer runs. |
| `failsafe_timeout_seconds` | 180 | 30–900 | no | Semi-auto suggestion timeout. |
| `failsafe_action` | `auto_assign` | `auto_assign` / `escalate` | no | What happens on timeout. |
| `alert_wait_minutes` | 20 | 5–60 | no | Pending request turns red. |
| `request_expiry_minutes` | 120 | 30–480 | no | Unassigned request expires. |
| `no_show_wait_minutes` | 5 | 1–15 | yes | Driver wait before no-show allowed. |
| `stale_gps_seconds` | 60 | 20–300 | no | Vehicle considered stale. |
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
- En-route reuse: vehicles on a trip of the same direction whose route passes within `enroute_reuse_max_eta_minutes` of the pickup and satisfy all hard rules after insertion.
- Return-trip reuse: vehicles that just completed a drop (become `available`) are ordinary idle candidates; no special rule needed.
- "Nearby" is always **time-based (ETA)**, never straight-line distance.

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
- Runs every `batch_window_seconds` for each operator on all `queued` requests whose hold window has elapsed or which are no-hold, plus modifiable (`planned`/`dispatched`, not locked) trips.
- Model: Pickup-and-Delivery Problem with Time Windows and capacities (Dial-a-Ride), solved with **Google OR-Tools routing** using OSRM time matrices.
- Objective matches the cost function; hard rules become constraints (capacity, time windows, max ride time per rider, vehicle types, exclusivity).
- Time limit per run: 10 s (config `optimizer_time_limit_seconds`). If no solution, fall back to single-insertion greedy using §4.
- Output = proposed trips. In `full_auto` scopes they are applied; in `semi_auto` they become suggestions; in `manual` they are shown as hints only.
- Never modifies locked requests, `pooling_blocked` trips, or trips `in_progress` except inserting riders that satisfy all rules.

### Evening hold window
- `from_office` requests (not VIP, not high priority/urgency, not opt-out) wait between `hold_window_min_minutes` and `hold_window_max_minutes`.
- Phase 3: fixed at the min value.
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
