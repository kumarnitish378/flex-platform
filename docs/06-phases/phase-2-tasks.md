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

- [ ] **B23 · Suggestions with reasons** · deps B22
  Docs: allocation-rules.md §5, control-model.md §1, api-spec.yaml
  Do: spec first. `GET /dispatch/requests/{id}/suggestions` returning the top 3 scored candidates, each
  with ETA to pickup, seats free after assignment, added minutes per named existing rider, empty km added,
  whether it opens a new trip, and the cost. A `suggestion` record so acceptance can be measured — the
  Phase 2 exit criterion is "acceptance > 70%", which cannot be evaluated unless the offer is stored.
  Done when: the plain-text reason in §5 is reproduced by a test ("8 min away · 2 seats left · +4 min for
  Rahul · reuses trip T-102"); a suggestion that no longer satisfies the hard rules when accepted is
  refused with the rule that broke; acceptance and rejection are both recorded with the actor.

- [ ] **B24 · Mode settings and precedence** · deps B05, B23
  Docs: control-model.md §1–2
  Do: `mode_setting` table (optional `client_id`, `zone_id`, `direction`, `weekdays`, `start_time`,
  `end_time`, `mode`), admin CRUD, and `resolve_mode(request)` implementing the eight-level precedence
  exactly, including "most recently updated wins" at equal specificity.
  Done when: a table-driven test walks all eight levels and the tie-break; `automation_paused` beats
  everything; a VIP request resolves per level 2 including the "no VIP vehicle → alert, do not substitute"
  branch (OQ-12); overlapping settings are detected and reported so the admin screen can warn.

- [ ] **B25 · Semi-auto assignment and failsafe** · deps B24
  Docs: control-model.md §1 and §4, ADR-0008
  Do: in a `semi_auto` scope, creating a request generates suggestions and starts a
  `failsafe_timeout_seconds` timer **through the Clock**, so the simulator drives it. On timeout:
  `auto_assign` re-checks the hard rules and assigns the top suggestion, logging actor `system_failsafe`;
  `escalate` alerts and repeats once before assigning. Half the timeout for VIP and high urgency. If no
  supervisor is logged into the scope, the failsafe applies immediately.
  Done when: every branch is proved by advancing a FakeClock, never by sleeping; a suggestion that has gone
  stale by timeout is not assigned; the Celery beat runs the same sweep the sim clock does, guarded by the
  B20 test that compares the two.

- [ ] **B26 · Full override set with audit** · deps B21
  Docs: control-model.md §3, data-model.md
  Do: the nine actions, each with a required reason code, an `expires_at` defaulting to end of shift, and
  an `override_log` row recording who, what, before, after, reason and time. Impact preview as a
  **dry-run** response: added minutes per affected rider, ETA changes, and zones left with no available
  vehicle.
  Done when: a hard-rule override is refused without `safety`/`client_request`/`other` plus a note and is
  flagged in the report; an expired override stops applying without anything running; a test asserts no
  automatic path ever modifies a locked request or a `pooling_blocked` trip.

- [ ] **B27 · Zones** · deps B06
  Docs: data-model.md, allocation-rules.md §3
  Do: zone polygons (PostGIS), `employee.zone_id` derivation from home location on create, import and
  update — the stub B07 left null — and a backfill for existing rows.
  Done when: a point-in-polygon test fixture covers a home inside, outside and on a boundary; an employee
  whose home moves between zones is re-derived; zone-scoped mode settings resolve.

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

- [ ] **A13 · Supervisor: suggestions and approve/override** · deps A11, B23, B25
  Screens: S-05, S-06 · Docs: screens-by-role.md
  Done when: the top three suggestions render with their reasons; one-tap approve; override opens the
  reason picker; the failsafe countdown is visible.

- [ ] **A14 · Admin: modes, zones, client policies** · deps A12, B24, B27, B28
  Screens: A-06, A-09, A-10
  Done when: a mode setting can be created per scope and the resolved mode for a sample request is shown;
  overlapping settings warn.

- [ ] **A15 · Flutter web build for supervisor and admin** · deps A13, A14
  Docs: tech-stack.md, ADR-0003
  Done when: the supervisor and admin sections build and run as web; the driver and employee sections are
  not reachable there.

- [ ] **A16 · Hindi strings** · deps A15
  Docs: non-functional.md (Usability)
  Done when: `app_hi.arb` is complete for every key in `app_en.arb`; a test fails if a key exists in one
  and not the other.

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
