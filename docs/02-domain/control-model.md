# Control model: modes, overrides, failsafe

Principle: **modes decide who normally assigns; overrides let a human step in on one trip at any time; failsafes act when nobody responds.** (Analogy: ArduPilot flight modes + RC override + failsafe.)

## 1. Modes
| Mode | Code | Assignment | System role | Supervisor role |
|---|---|---|---|---|
| Manual | `manual` | Supervisor picks the vehicle | Map, ETAs, candidates, timers | Everything |
| Semi-auto | `semi_auto` | System suggests top 3 with reasons; supervisor approves/changes | Suggestions, failsafe | One-tap approve or override |
| Full auto | `full_auto` | System assigns and notifies | Assign, re-optimize | Monitor, exceptions, overrides |

- Modes control **assignment only**. Tracking, ETA and notifications work in every mode.
- Phase 1 supports `manual` only. Phase 2 adds `semi_auto`. Phase 3 adds `full_auto`.

## 2. Mode scopes and precedence
A `mode_setting` row has optional `client_id`, `zone_id`, `direction`, `weekdays`, `start_time`, `end_time` and a `mode`. For a request, the **most specific matching** setting wins:

1. Global emergency pause (`automation_paused = true`) → effectively `manual` for everything.
2. VIP request → always assigned immediately in `full_auto` behaviour **if** a VIP vehicle is available and scope is not paused; otherwise alert supervisor.
3. Setting matching client + zone + time window
4. client + time window
5. zone + time window
6. client
7. zone
8. operator default (required; initial value `manual`)

Ties at the same specificity: the most recently updated setting wins, and the admin UI warns about overlaps.

## 3. Override actions (available in every mode)
| Action | Code | Effect | Notifies |
|---|---|---|---|
| Reassign | `reassign` | Move request to another vehicle/trip | Employee, both drivers |
| Lock | `lock` | Pin request to vehicle; optimizer never changes it | — |
| Unlock | `unlock` | Remove lock | — |
| Force priority | `force_priority` | Treat request as priority 1 / high urgency / VIP handling | — |
| Block pooling | `block_pooling` | Trip accepts no new riders | — |
| Hold | `hold` | Keep request queued until time T or manual release | Employee (delayed notice) |
| Cancel | `cancel` | Cancel request or trip | Employee, driver |
| Vehicle out of service | `vehicle_out_of_service` | Vehicle unassignable; its planned trips return to queue for re-assignment | Driver, affected employees |
| Emergency pause | `pause_automation` / `resume_automation` | Stop / resume all auto assignment | All supervisors |

### Override rules
1. **Overridden and locked items stay fixed.** The optimizer and failsafe must never revert them. Implementation: `lock_vehicle_id`, `pooling_blocked`, `override_until` fields checked by every automatic path; covered by tests.
2. **Impact preview** before confirm: added minutes for affected riders, ETA changes, zones left with no available vehicle.
3. **Reason required** (one tap): `driver_issue`, `local_knowledge`, `client_request`, `traffic`, `vehicle_issue`, `safety`, `other` (+ note).
4. **Hard-rule overrides** (capacity, night safety, VIP vehicle substitution) require reason `safety`/`client_request`/`other` with a note and are flagged in reports.
5. **Expiry:** each override has `expires_at` (default end of current shift / 23:59 IST; null = until trip ends).
6. **Audit:** every override written to `override_log` (who, what, before, after, reason, time).
7. Override logs are training data for Phase 3–4 tuning.

## 4. Failsafe (semi_auto)
- When a suggestion is created, a timer starts (`failsafe_timeout_seconds`).
- On timeout: if `failsafe_action = auto_assign` → assign top suggestion (if still valid; re-check hard rules), log actor `system_failsafe`. If `escalate` → alert operator admin / backup supervisor, keep suggestion open, repeat once after another timeout, then auto-assign.
- If no supervisor is logged in for a `semi_auto` scope, failsafe applies immediately.
- VIP and high urgency requests use half the timeout.

## 5. Mode-switch prompts (Phase 3)
The system suggests switching a scope to `manual` (never switches by itself) when any is true in the last 15 minutes:
- ≥ 30% of suggestions rejected in that scope,
- median ETA error > 10 minutes,
- pending requests > 2× normal for that time slot,
- ≥ 20% of vehicles in the scope stale or out of service.

## 6. Degradation
- Optimizer/worker down → scopes in `full_auto`/`semi_auto` behave as `manual`; alert shown.
- **Routing degradation ladder** (ADR-0010 §3.4 of `architecture.md`): Redis cache hit → `osrm` provider →
  `approx`. The `approx` step is used whenever OSRM is down, slow, erroring **or the shared 1 request/second
  limit on the public server is exhausted**; it estimates from straight-line distance × 1.4 and the
  time-of-day speed table (last known speed profile once available). Those ETAs carry `approximate: true` in
  the API and are shown as approximate in the app. Degrading to `approx` never changes the control mode and
  never blocks assignment — supervisors keep working with coarser ETAs.
- Sustained `approx` operation (e.g. public server unreachable for a whole peak) is an operational signal to
  move to self-hosted OSRM (task I02b), not a reason to raise the rate limit.
- **No geocoding to degrade**: Phase 1 has none (map pins + landmark text), so address lookup can never be a
  failure mode.
- Tile server unreachable → the map renders from the ≥ 7-day local tile cache; markers, routes and ETAs keep
  working on whatever tiles are cached. No prefetching is used to paper over this.
- MQTT down → driver app falls back to HTTPS location upload every 15 s.
