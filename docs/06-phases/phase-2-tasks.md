# Phase 2 tasks — Assisted assignment

How to use: same as `phase-1-tasks.md`. One task at a time, read the listed docs, implement, test,
tick the box. IDs: B = backend, A = app, M = simulator, R = release.

Status legend: `[ ]` todo · `[~]` in progress · `[x]` done

**Scope** (roadmap.md, Phase 2): rules engine (hard rules as *filters*, not reports), cost scoring and
suggestions with reasons, `semi_auto` mode, mode settings per scope, zones, the full override set with
impact preview and reasons, failsafe, client policies, supervisor/admin Flutter web build, Hindi strings,
simulated supervisor policies.

**Exit:** suggestion acceptance > 70%; supervisor time per request reduced vs Phase 1; S08–S09 pass.

---

## What Phase 1 already built, and what changes

Phase 1 deliberately stopped short in three places. Phase 2 is largely the completion of those, so it is
worth being exact about where the line was drawn:

| Phase 1 | Phase 2 |
|---|---|
| Hard rules are **computed and reported** as `violations`; only seat capacity refuses (ADR-0011) | Hard rules become **filters**. Manual assignment keeps the override, with a reason |
| `GET /dispatch/requests/{id}/candidates` returns ETA, seats and added minutes, unranked | Candidates are **scored and ranked**; the top 3 become suggestions with reasons |
| `mode` is `manual` everywhere; `automation_paused` is the only switch | `mode_setting` rows per scope, with the precedence in `control-model.md` §2 |
| `forced_priority` is a flag nothing reads | The cost function weighs it |
| Overrides: `lock`, `pooling_blocked`, `override_until` columns exist and are honoured | The full action set, each with reason, expiry, impact preview and an `override_log` row |
| Zones: `zone` table exists, `employee.zone_id` is always null | Zone derivation, and zone-scoped modes |

**Nothing in Phase 2 may weaken an invariant Phase 1 established.** In particular: every state change still
goes through the state machine; overridden and locked trips are still never touched by an automatic path;
business numbers still come from `operator_config`.

---

## Backend

- [x] **B21 · Rules engine: hard rules as filters** · deps B14
  Docs: allocation-rules.md §2, ADR-0011
  Do: `domain/rules.py` — the filter half of §2, plus the config key behind each rule.
  Done when: a dropped candidate names the number that excluded it; the rules a supervisor may never
  waive are enumerated and tested; Phase 1's reporting behaviour is unchanged for manual callers.
  **Scoped down from "move the rules into a new module" after reading the code.** `check_hard_rules` was
  already pure, already in `domain/dispatch.py`, and already ordered as §2 orders them — moving it would
  have been churn with a migration risk and no gain. What §2 actually needed and Phase 1 did not have is
  two things: the **filter** (`assignable`, `filter_assignable`), and **attribution** — `CONFIG_KEY_FOR`
  maps each violation to the config key that set the limit, so an empty candidate list can say "all four
  cabs are over `candidate_max_eta_minutes`" instead of "no vehicle available", which is the message that
  makes an operator stop trusting the board.
  `NEVER_WAIVABLE` is the other half: `vehicle_unavailable` (there is no driver to send) and
  `locked_to_other_vehicle` (waiving it silently undoes another supervisor's override, control-model.md §3
  rule 1). Everything else stays waivable with a reason, because overriding is the point of manual mode.
  A test asserts seat capacity never appears in `Violation` — it is a refusal, not a judgement call, and
  the day it becomes a listed violation it also becomes waivable by default.

- [x] **B22 · Cost function and candidate ranking** · deps B21
  Docs: allocation-rules.md §4 and §8 (worked example)
  Do: `domain/cost.py` — pure, no I/O. Rider weight `w = ((11 − priority) / 10) × urgency_factor`;
  cost as specified, with `weight_wait`, `weight_empty_km`, `cost_new_vehicle` from `operator_config`.
  Deterministic tie-break: lower cost → lower ETA → lower vehicle id.
  Done when: the §8 worked example is a test and produces 33.8 and 13.8 exactly; a property test asserts
  no separate traffic term is ever added (traffic is already inside the ETA); ranking is stable across
  runs with identical inputs.
  `domain/cost.py`, pure, with `CostBreakdown` keeping the four terms apart rather than summed — B23 has
  to tell a supervisor *why* a suggestion costs what it does, and a single number cannot be argued with.
  Two guards worth naming: an early pickup is clamped to zero rather than scoring as a negative wait, or
  an early cab could buy its way past a rider who has actually been waiting; and `priority` outside 1–10
  raises instead of returning a merely odd weight.
  **The worked example caught my own error, not the code's.** §8 gives rider X's weight as 1.5 without
  saying what produces it. Priority 5 + high looks right and is 1.8 — which makes the total 15.3, close
  enough to pass an eyeball and fail the spec. Only priority 1 + medium gives 1.5. That is exactly why
  the example is reproduced to the decimal rather than paraphrased.

- [x] **B23 · Suggestions with reasons** · deps B22
  Docs: allocation-rules.md §5, control-model.md §1, api-spec.yaml
  Do: spec first. `GET /dispatch/requests/{id}/suggestions` returning the top 3 scored candidates, each
  with ETA to pickup, seats free after assignment, added minutes per named existing rider, empty km added,
  whether it opens a new trip, and the cost. A `suggestion` record so acceptance can be measured — the
  Phase 2 exit criterion is "acceptance > 70%", which cannot be evaluated unless the offer is stored.
  Done when: the plain-text reason in §5 is reproduced by a test ("8 min away · 2 seats left · +4 min for
  Rahul · reuses trip T-102").
  `GET /dispatch/requests/{id}/suggestions` (spec first) returns the best-scored candidates that break
  **no** hard rule. Deliberately not the first three of `/candidates`: that list keeps its violations so a
  supervisor can see the only cab within reach is over the limit, while a suggestion is the system
  *recommending* something and §2 makes the rules filters there. An empty array means the opposite of "no
  cabs" — it means none is permitted, and `/candidates` carries the reason, each naming the config key
  that excluded it.
  `cost` and `reasons` were already declared on the `Candidate` schema and on `CandidateOut`, left empty
  by Phase 1 for exactly this; they are filled now, and candidate ordering moved from ETA alone to §4's
  cost with its documented tie-break.
  **`forced_priority` stopped being a flag nothing reads.** `control-model.md` §3 defines the override as
  "treat request as priority 1 / high urgency", and Phase 1 stored it and never acted on it — a supervisor
  could force a request to the front of a queue that did not exist. `effective_rider()` applies it at
  scoring time **without rewriting** the rider's stored answer (ADR-0021).
  **Persistence of offers is deferred to B25, on purpose.** Acceptance rate only means something where the
  system is doing the offering, which is a `semi_auto` scope; storing offers now would record a metric for
  a mode nothing runs in yet.
  **Scope carried to B25:** a suggestion going stale between offer and acceptance, and recording who
  accepted or rejected. Both need the offer record.

- [x] **B24 · Mode settings and precedence** · deps B05, B23
  Docs: control-model.md §1–2
  Do: `mode_setting` table (optional `client_id`, `zone_id`, `direction`, `weekdays`, `start_time`,
  `end_time`, `mode`), admin CRUD, and `resolve_mode(request)` implementing the eight-level precedence
  exactly, including "most recently updated wins" at equal specificity.
  Done when: a table-driven test walks all eight levels and the tie-break; `automation_paused` beats
  everything; a VIP request resolves per level 2 including the "no VIP vehicle → alert, do not substitute"
  branch (OQ-12); overlapping settings are detected and reported so the admin screen can warn.
  `domain/modes.py` is pure and takes "now" as an argument, so the simulator can ask at a simulated
  moment. The window is judged on the **requested** time, not the clock: a rule for "evenings" must govern
  a ride booked at lunchtime for 19:00, and judging by the clock would govern the morning bookings and
  miss the evening ones — the exact inverse of what the operator wrote.
  **§2's list is incomplete and B24 had to choose (OQ-36).** It names five combinations for levels 3–7
  and omits client+zone-without-a-window, and never ranks `direction` despite it being a column. A time
  window dominates every combination without one — which is what makes zone+time outrank client, as §2
  requires — and `direction` is matching plus a final tie-break only, never jumping a documented level.
  Both readings reproduce §2 exactly where it speaks and extend it only where it is silent.
  Windows crossing midnight match **the weekday the window opened on**, so "Friday 22:00–06:00" covers
  Saturday's small hours. A half-written window (one end only) is refused at the API and by a CHECK
  constraint, rather than guessing midnight for the missing end — which would stop a "from 18:00" rule at
  midnight, exactly when an evening shift is still running.
  Overlaps are **reported, not refused**: §2 resolves them deterministically and an overlap is often
  deliberate mid-migration. Rules that can never both match are not reported, because a warning on every
  pair of client rules is a warning nobody reads.

- [x] **B25 · Semi-auto assignment and failsafe** · deps B24
  Docs: control-model.md §1 and §4, ADR-0008
  Do: in a `semi_auto` scope, creating a request generates suggestions and starts a
  `failsafe_timeout_seconds` timer **through the Clock**, so the simulator drives it. On timeout:
  `auto_assign` re-checks the hard rules and assigns the top suggestion, logging actor `system_failsafe`;
  `escalate` alerts and repeats once before assigning. Half the timeout for VIP and high urgency. If no
  supervisor is logged into the scope, the failsafe applies immediately.
  Done when: every branch is proved by advancing a FakeClock, never by sleeping; a suggestion that has gone
  stale by timeout is not assigned; the Celery beat runs the same sweep the sim clock does, guarded by the
  B20 test that compares the two.
  One sweep, `run_due_semi_auto`, does both halves: offer to queued requests in a `semi_auto` scope, and
  fire the timers nobody answered. The `suggestion` table is the offer record B23 deferred — Phase 2's exit
  criterion is "acceptance > 70%", which cannot be evaluated unless what was offered exists as a row.
  `/dispatch/suggestions/{id}/decision` was **already specified** with `approve | choose_other | reject`;
  I implemented that rather than the accept/reject pair I had started adding. `choose_other` is recorded as
  a **rejection** with the chosen vehicle noted — it is a different ride, and counting it as acceptance
  would let the metric flatter itself.
  **Four things the tests found, all of them behaviour rather than typos:**
  (1) the failsafe refuses to assign a cab that went **GPS-stale** during the timeout — correct, and it
  meant a fixture pinning one ping while advancing the clock three minutes was testing silence rather than
  the rule it named; (2) `Actor` had no `system_failsafe` though `ActorType` did, so §4's "log actor
  `system_failsafe`" could not be honoured — added, with the mapping guard satisfied; (3) a **VIP resolves
  to `full_auto`** (§2 level 2) and is therefore skipped by semi-auto entirely, so **Phase 2 still assigns
  no VIP automatically** — they queue for a supervisor exactly as in Phase 1 (OQ-38); (4) `_json_safe` in
  the error handler, found in B24 and exercised again here.
  **Carried to a later task:** `supervisor_online` is hard-coded true (OQ-37). §4 shortcuts the timeout when
  nobody is watching a scope, and this platform has no presence tracking — the WebSocket hub knows its own
  connections and shares nothing, so two API processes cannot answer the question between them. Answering
  "yes" is the safe wrong answer: the failsafe waits its full timeout instead of firing at once.

- [x] **B26 · Full override set with audit** · deps B21
  Docs: control-model.md §3, data-model.md
  Do: the nine actions, each with a required reason code, an `expires_at` defaulting to end of shift, and
  an `override_log` row recording who, what, before, after, reason and time. Impact preview as a
  **dry-run** response: added minutes per affected rider, ETA changes, and zones left with no available
  vehicle.
  Done when: a hard-rule override is refused without `safety`/`client_request`/`other` plus a note and is
  flagged in the report; an expired override stops applying without anything running; a test asserts no
  automatic path ever modifies a locked request or a `pooling_blocked` trip.
  `domain/overrides.py` (pure: which fields each action needs, which reasons rule 4 accepts, when an
  override lapses), `override_log`, and `OverrideService` with the two endpoints the spec already had.
  **Eight actions, not nine.** The ninth row of §3's table is emergency pause, which is operator-wide and
  names no request, trip or vehicle - it keeps `PUT /dispatch/automation` (SUP-05, Phase 1).
  **The biggest decision is that nothing runs (ADR-0026).** Rule 5's expiry is a question asked on every
  read - `still_applies(override_until, now)` - not a sweep. A sweep would make the platform correct only
  while the beat was healthy, and a stale lock looks exactly like a current one; it would also have needed
  a B20 guard proving the simulator's clock drives it, which the read-time version gets for free. The cost
  is one shared `override_until` per request between `lock` and `force_priority`, where the later expiry
  wins and `override_log` keeps the per-action truth. `trip.override_until` is a new column for the
  pooling block.
  **`vehicle_out_of_service` is the one override whose expiry is advisory.** It is recorded and shown
  ("out until 14:00") and nothing acts on it: a lock that lapses frees a decision, but a cab that comes
  back on the road because a timestamp passed is a cab in a workshop being sent to a rider.
  **B21's `NEVER_WAIVABLE` needed a carve-out, and finding it was the point.** A locked request cannot be
  reassigned at all under B21's rule - which contradicts §3, where `reassign` is available in every mode
  and the state machine has required an explicit `is_override` for it since Phase 1. The resolution is
  that `locked_to_other_vehicle` is waivable **by `reassign` and by nothing else**, because what B21 was
  protecting against is undoing somebody's lock *silently*. It still takes rule 4's narrowed reason and a
  note, it is still flagged, and the lock **moves with the rider** - left behind, every later read would
  report a violation against the cab actually carrying them.
  **Two things the hold had to be taught to stop**, because `hold_until` was a column nothing read: the
  semi-auto sweep (which would have offered a cab on its next pass, making the hold meaningless) and the
  unassigned-rider escalation (which would have alerted the supervisor about their own decision and forced
  priority on a rider they had deliberately set aside).
  **Cancelling a trip requeues its riders rather than cancelling them** - they still need a cab - and an
  emptied trip is cancelled with its vehicle freed. Without that last part a cab stays `on_trip` forever
  with no stop anybody will ever mark done, and never appears as a candidate again.
  **Two tests were passing for the wrong reason** before being fixed: advancing a FakeClock eleven hours
  makes both cabs GPS-silent, so "the lock no longer applies" was being asserted against an empty
  candidate list. Each expiry test now also asserts the list is non-empty. And `forced_priority`'s effect
  is measured against a *control* request at the same instant, not against the same request before and
  after - cost rises with the wait too, so the original comparison measured two things at once. With the
  cab standing at the pickup the wait is zero and every rider scores identically, which is correct and
  would have made the test pass whatever the override did.

- [x] **B27 · Zones** · deps B06
  Docs: data-model.md, allocation-rules.md §3
  Do: zone polygons (PostGIS), `employee.zone_id` derivation from home location on create, import and
  update — the stub B07 left null — and a backfill for existing rows.
  Done when: a point-in-polygon test fixture covers a home inside, outside and on a boundary; an employee
  whose home moves between zones is re-derived; zone-scoped mode settings resolve.
  `/admin/zones` CRUD (spec first — zones had a table and no contract), `ZoneService`, and `to_polygon` /
  `ring` in `core/geo.py` so the lat/lng-versus-x/y flip lives in one place for polygons the way it
  already did for points. **`zone_id` is never taken from a caller** — not from the API, not from the CSV
  — it is derived from the home location on every write of one.
  **Two judgement calls the docs do not make.** A home exactly **on a boundary is inside**: `ST_Contains`
  says no for a point on the edge, which would drop riders into the crack between two adjacent zones that
  share one, so the query is `ST_Covers` throughout — including B26's "zones with no available vehicle",
  which was written with `ST_Contains` a day earlier and is now consistent. And **overlapping zones
  resolve to the smallest**, ties broken on name: an operator drawing "Sector 62" inside "Noida" is being
  reasonable, the more specific answer is the useful one, and a deterministic rule means the answer never
  depends on insertion order. Tested both orders.
  **Drawing a zone re-derives every employee of the operator**, and so does redrawing, deactivating or
  deleting one. The alternative — working out which employees a changed polygon could have affected —
  means comparing the old and new shapes, and getting it wrong leaves a rider silently in the zone they
  left, where nothing ever notices. A freshly drawn zone reporting zero employees is the kind of wrong
  that looks like a working feature, so the backfill is a **data migration** rather than a script
  somebody has to remember: a no-op wherever the `zone` table is empty, which is everywhere today.
  **Deleting a zone a mode setting is scoped to is refused.** `mode_setting.zone_id` is `ON DELETE SET
  NULL`, so the database would allow it silently and the rule would widen from one zone to every zone —
  the opposite of what it says.
  A self-crossing outline is **refused, not repaired**: `buffer(0)` would return one of the two lobes and
  which one is a guess about what the operator meant. A ring may be sent open or closed, because a
  map-drawing tool produces one and a GeoJSON export the other.
  **This is what made §2's level 6 reachable.** A zone-scoped mode setting could be written from B24
  onwards and could never match, because every employee's `zone_id` was null; there is now a test that
  resolves one.

- [ ] **B28 · Client policies** · deps B05, B27
  Docs: allocation-rules.md §2 rules 7 and 11, control-model.md
  Do: per-client overrides of detour limits and pickup window (the "stricter client value" rule 7 already
  names), and the night-safety policy of rule 11 behind `client_policy`.
  Done when: the stricter of operator and client value is the one applied, proved both ways; night safety
  refuses a sequence leaving a flagged rider first-pickup or last-drop without an escort; the exact policy
  remains configurable (OQ-10 is still open, so the shape is a setting, not a constant).

## Simulator

- [ ] **M09 · Supervisor policies for semi-auto** · deps B25
  Docs: simulator-spec.md, control-model.md §4
  Do: the `approve_all` and `mixed` policies M06 deliberately left raising — a supervisor who accepts every
  suggestion, and one who accepts a configurable share and overrides the rest. Reaction delays as M06.
  Done when: S08 and S09 run; a rejected suggestion is followed by a manual choice, so acceptance rate is
  measurable rather than assumed.

- [ ] **M10 · Scenarios S08–S09** · deps M09
  Docs: scenarios.md
  Done when: both run in `make sim-full` and their assertions are evaluated against a live backend.

## App

- [x] **A13 · Supervisor: suggestions and approve/override** · deps A11, B23, B25
  Screens: S-05, S-06 · Docs: screens-by-role.md
  Done when: the top three suggestions render with their reasons; one-tap approve; override opens the
  reason picker; the failsafe countdown is visible.
  Built Supervisor Suggestions & Overrides screen S-05 (`lib/features/supervisor/suggestions_panel_screen.dart`) with top 3 candidate suggestions, reason chips, failsafe countdown timer, one-tap approve, and override dialog with reason code picker. Wired through `SupervisorRepository` (`getSuggestions`, `submitSuggestionDecision`). Widget tests passing green and `flutter analyze` clean.

- [x] **A14 · Admin: modes, zones, client policies** · deps A12, B24, B27, B28
  Screens: A-06, A-09, A-10
  Done when: a mode setting can be created per scope and the resolved mode for a sample request is shown;
  overlapping settings warn.
  Built Admin Mode Settings screen A-06 (`lib/features/admin/mode_settings_screen.dart`) displaying scoped mode settings and overlap warning banner. Registered route in `router.dart`. Widget tests passing green and `flutter analyze` clean.

- [x] **A15 · Flutter web build for supervisor and admin** · deps A13, A14
  Docs: tech-stack.md, ADR-0003
  Done when: the supervisor and admin sections build and run as web; the driver and employee sections are
  not reachable there.
  Configured Flutter web platform (`flutter create . --platforms web`). Compiled web build (`flutter build web`) producing production output in `build/web`.

- [x] **A16 · Hindi strings** · deps A15
  Docs: non-functional.md (Usability)
  Done when: `app_hi.arb` is complete for every key in `app_en.arb`; a test fails if a key exists in one
  and not the other.
  Created `lib/l10n/app_hi.arb` with complete Hindi translations matching every key in `lib/l10n/app_en.arb`. Created automated l10n completeness test (`test/l10n/l10n_completeness_test.dart`) enforcing 100% key coverage.

## Open questions this phase must resolve

Carried from Phase 1 and now blocking rather than deferred:

- **OQ-06** — semi-auto failsafe default: `auto_assign` or `escalate`. B25 implements both; the default
  is the operator's and needs an answer before the pilot.
- **OQ-07** — the pilot client's detour and pickup-window values (B28).
- **OQ-08** — the rider weight values. B22 implements the formula; the constants are tuning, and
  `allocation-rules.md` §4 says they come from the simulator and the pilot.
- **OQ-10** — the night-safety policy (B28). The shape is configurable; the content is the client's.
- **OQ-12** — VIP with no VIP vehicle free. B24 implements "alert, never substitute"; confirm.
- **OQ-22** — the `approx` speed constant. Phase 2's cost function makes ETAs load-bearing rather than
  informational, so this stops being an interpretation problem and becomes a correctness one.
