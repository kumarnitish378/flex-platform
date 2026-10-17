# Phase 3 tasks — Pooling + Full auto

How to use: same as `phase-1-tasks.md` and `phase-2-tasks.md`. One task at a time, read the listed docs,
implement, test, tick the box. IDs: B = backend, A = app, M = simulator, R = release.

Status legend: `[ ]` todo · `[~]` in progress · `[x]` done

**Scope** (roadmap.md, Phase 3): OR-Tools batch optimizer (DARP), micro-batching, evening hold window,
en-route reuse, `full_auto` per scope, mode-switch prompts, degradation fallbacks, learned speed profiles
into OSRM, billing export, full reports, policy comparison runs.

**Exit:** cab-km per trip and vehicles used reduced vs baseline; median wait reduced; full auto running on
at least one scope; S10–S12 pass.

---

## What Phases 1 and 2 already built, and what changes

Phase 2 left four things deliberately unfinished, and they are the spine of Phase 3:

| Phase 2 | Phase 3 |
|---|---|
| Assignment is **one request to one cab**, chosen by cost (`domain/cost.py`) | A **batch** of requests and modifiable trips, solved together (`allocation-rules.md` §6) |
| `semi_auto` offers the top suggestion; a human answers | `full_auto` applies the solution without one, per scope |
| `hold_window_min_minutes` / `hold_window_max_minutes` / `batch_window_seconds` are config keys nothing reads | All three are read. They are the last entries in `PHASE_2_KEYS` |
| `mode_setting.mode` accepts `full_auto` and `resolve_mode` returns it; nothing acts on it | A `full_auto` resolution assigns |
| `road_speed_profile` is a table nothing writes | Written from real trips, read by the `approx` provider and OSRM |

**Two invariants Phase 3 may not weaken**, both already enforced and both easy to lose in an optimizer:

1. **Overridden and locked items are never touched by an automatic path** (`control-model.md` §3 rule 1,
   CLAUDE.md hard rule 6). The optimizer is the most automatic path there has ever been here, and S09 is
   the scenario that proves it. §6 says it plainly: never modifies locked requests, `pooling_blocked`
   trips, or `in_progress` trips except by inserting riders who satisfy every rule.
2. **Every state change goes through the state machine.** A solver returns a plan; applying it is still a
   sequence of transitions, not a bulk write.

---

## Backend

- [ ] **B29 · Evening hold window** · deps B22
  Docs: allocation-rules.md §6 "Evening hold window", §2 rule 10
  Do: `from_office` requests that are not VIP, not priority ≤ 2, not `urgency = high` and not `no_sharing`
  wait `hold_window_min_minutes` before becoming assignable. Phase 3 is the **fixed minimum**; Phase 4
  makes it dynamic. The clock is the injected one, so a scenario can watch the window pass.
  Done when: a held request is not offered or assigned before its window elapses and is immediately after;
  each of the four exemptions is tested separately; `forced_priority` short-circuits the window, which is
  what §3.1 already promised and Phase 1 could not deliver.

- [ ] **B30 · Micro-batching** · deps B29
  Docs: allocation-rules.md §6 first bullet
  Do: collect assignable requests for `batch_window_seconds` and hand them to the optimizer together,
  rather than one at a time. Driven by the Clock, so the simulator's jump produces the same batches.
  Done when: two requests arriving inside one window are solved in one call; the sweep that runs it is the
  same one `/simctl/clock` drives (the B20 guard); a batch that finds no solution leaves every request
  exactly as it was.

- [ ] **B31 · OR-Tools DARP optimizer** · deps B30
  Docs: allocation-rules.md §4 and §6, ADR to be written
  Do: pickup-and-delivery with time windows and capacities, over OSRM time matrices, objective = §4's cost,
  hard rules as **constraints** rather than filters. `optimizer_time_limit_seconds` (default 10) caps a
  run; no solution within it falls back to the single-insertion greedy Phase 2 already has.
  Done when: a worked example with a known optimum is reproduced; the greedy fallback is proved by a test
  that makes the solver fail; the solver is **pure** of the database — it takes a problem and returns a
  plan, so the same inputs always give the same plan and a scenario can be replayed.

- [ ] **B32 · Applying a solution, per mode** · deps B31, B24
  Docs: allocation-rules.md §6 "Output", control-model.md §1
  Do: proposed trips are **applied** in a `full_auto` scope, become **suggestions** in `semi_auto`, and are
  **hints only** in `manual`. One solver, three destinations, decided by `resolve_mode` per request.
  Done when: the same batch in three scopes produces an assignment, an offer and a hint respectively; a
  locked request and a `pooling_blocked` trip come out of all three untouched; applying is a sequence of
  state-machine transitions and every one is logged with actor `optimizer`.

- [ ] **B33 · En-route reuse as a real candidate** · deps B31
  Docs: allocation-rules.md §3
  Do: §3's second bullet — a cab already on a trip of the same direction whose route passes within
  `enroute_reuse_max_eta_minutes` of the pickup. Phase 1 computes the ETA and the ceiling; what is missing
  is route-aware proximity rather than point-to-point ETA from the cab's current position.
  Done when: a cab whose *route* passes a rider is a candidate while one that is merely near but heading
  away is not; the existing ceiling still applies per candidate kind.

- [ ] **B34 · `full_auto`** · deps B32
  Docs: control-model.md §1 and §2, ADR-0008
  Do: the mode the mode table has accepted since B24 and nothing has acted on. A `full_auto` scope assigns
  without a human; VIP handling stays §2 level 2, which is why Phase 2 assigned no VIP automatically
  (OQ-38) — that stops being true here and needs the "no VIP vehicle → alert, do not substitute" branch to
  be live rather than theoretical.
  Done when: a scope in `full_auto` serves a request end to end with no supervisor action; `automation_paused`
  still beats it; every automatic assignment is attributable in `trip_event` and the report.

- [ ] **B35 · Mode-switch prompts** · deps B34
  Docs: control-model.md §5
  Do: the four conditions of §5, evaluated per scope over the last 15 minutes, raising a `mode_prompt`
  alert — the alert type `AlertType` has carried since Phase 1 and nothing raises. **The system suggests;
  it never switches by itself**, which §5 states twice and is the whole point.
  Done when: each of the four conditions raises on its own; the prompt resolves when the condition clears;
  no code path anywhere changes a mode without a human.

- [ ] **B36 · Degradation: the optimizer is allowed to be down** · deps B34
  Docs: control-model.md §6
  Do: a scope in `full_auto` or `semi_auto` behaves as `manual` when the optimizer or worker is
  unavailable, with an alert. The routing ladder (Redis → `osrm` → `approx`) already exists and is not
  this; this is the *control* ladder.
  Done when: killing the optimizer leaves every scope working manually with an alert raised and no request
  stuck; recovery restores the scope without an operator touching anything; S12 passes.

- [ ] **B37 · Learned speed profiles** · deps B15
  Docs: data-model.md (`road_speed_profile`), ADR-0010, OQ-22
  Do: write `road_speed_profile` from completed trips (168 hour-of-week slots) and read it in the `approx`
  provider in place of the constant. **This is OQ-22**, which has been the dominant term in every scenario
  number since Phase 1 and is still unsourced.
  Done when: a profile built from real pings changes an `approx` ETA measurably; the suite is re-run and
  the headline numbers are restated against measured speeds; OQ-22 can be closed or re-stated with data.

- [ ] **B38 · Billing export** · deps B19
  Docs: reports.md if it exists, otherwise add the shape to this task before coding
  Do: per-client monthly export of trips, riders, distance and whatever the pilot operator actually bills
  on — which is **OQ-03 and OQ-01**, so the shape comes from them, not from here.
  Done when: the export reconciles with `trip` and `ride_request` rows for a month of simulated data; a
  cancelled or no-show ride appears exactly as the operator's own invoice would treat it.

- [ ] **B39 · Full reports** · deps B19, B38
  Docs: screens-by-role.md (admin reports)
  Do: the reports Phase 1 stubbed — wait distribution, pooling rate, cab-km per trip, vehicles used,
  override frequency by reason, suggestion acceptance (Phase 2's exit criterion, now computable from the
  `suggestion` table).
  Done when: each number is reproduced by a test against a known fixture; the acceptance figure counts
  `accepted` and excludes `failsafe_assigned`, per OQ-39.

## App

- [ ] **A17 · Supervisor: pooled trips and optimizer hints** · deps B32
  Screens: S-05, S-07 · Docs: screens-by-role.md
  Done when: a multi-rider trip renders with its stop order and each rider's added minutes; a `manual`
  scope shows the optimizer's hint without applying it.

- [ ] **A18 · Admin: full auto and the mode prompt** · deps B34, B35
  Screens: A-06 · Docs: control-model.md §2 and §5
  Done when: `full_auto` can be set on a scope; a `mode_prompt` alert appears as a banner that offers the
  switch and never performs it automatically.

- [ ] **A19 · Reports and billing export** · deps B38, B39
  Screens: A-07 · Done when: the admin can read each Phase 3 report and download the billing export.

## Simulator

- [ ] **M11 · Pooling metrics** · deps B32
  Docs: simulator-spec.md, scenarios.md
  Do: cab-km per trip, vehicles used, riders per trip, detour minutes per rider — the numbers Phase 3's
  exit criterion is stated in and which the current `RunMetrics` does not carry.
  Done when: each is computed from the trips the drivers actually drove, not from what dispatch intended;
  a manual run and a pooled run over the same seed are directly comparable.

- [ ] **M12 · Scenarios S10–S12** · deps M11, B34, B36
  Docs: scenarios.md
  Done when: S10 (`pooling_efficiency`), S11 (`night_safety`) and S12 (`optimizer_down`) run in
  `make sim-full` with their assertions evaluated against a live backend. S11 is the scenario B28's rule 11
  was built for and has never been exercised end to end.

- [ ] **M13 · Policy comparison runs** · deps M12
  Docs: simulator-spec.md
  Do: the same scenario and seed under `manual`, `semi_auto` and `full_auto`, reported side by side.
  Done when: one command produces the comparison; the numbers are the ones the exit criterion names; the
  runs differ only in the mode, which a test asserts rather than assumes.

## Release

- [ ] **R04 · Phase 3 on the pilot** · deps B34, B39, R03
  Do: turn `full_auto` on for one scope with the operator watching, with the mode prompt and the emergency
  pause in front of them.
  Done when: one scope runs a week in `full_auto`; cab-km per trip and vehicles used are measured against
  the Phase 1 baseline; the operator can state what they would need before widening it.

---

## Open questions this phase has to resolve

- **OQ-22** — the `approx` speed constants. B37 is the task that closes it, and until then every scenario
  number in this phase is a property of a constant rather than of the dispatch.
- **OQ-39** — what "suggestion acceptance > 70%" is measured over. Phase 2's exit criterion; B39 computes
  it, and the definition has to be agreed before the figure is quoted.
- **OQ-10** — the escort half of night safety. B28 shipped the sequencing half; S11 cannot be honest about
  a flagged rider travelling alone until the policy is known.
- **OQ-03, OQ-01** — what the operator bills on, which B38 cannot be designed without.
