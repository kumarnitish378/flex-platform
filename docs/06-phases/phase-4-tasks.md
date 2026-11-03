# Phase 4 tasks — Prediction + offers

**Plan only.** Nothing here is implemented. It is written now so the pilot can collect the data these tasks
need from day one, and so the owner can see what Phase 4 asks of the pilot before deciding to start it.

How to use: same as `phase-1-tasks.md`, `phase-2-tasks.md` and `phase-3-tasks.md`. One task at a time, read
the listed docs, implement, test, tick the box. IDs: B = backend, A = app, M = simulator, R = release, P =
pilot data (new in this phase: a task only the pilot can complete).

Status legend: `[ ]` todo · `[~]` in progress · `[x]` done

**Scope** (roadmap.md, Phase 4): ready-time and zone-demand models, dynamic hold window, proactive ride
offers with accept/reject, learning from override logs, simulated offer behaviour.

**Exit:** offer acceptance > 40% in the pilot; prediction error acceptable for dispatch (defined in P02,
because "acceptable" needs a number); S13 passes.

**Not before:** Phase 3 has run on the pilot for long enough to produce labelled pooled trips (R04), and
the pilot has produced at least the data volumes in the table below. Phase 4 models learn from outcomes; with
no outcomes they would learn the simulator's own assumptions back, which is the failure this plan is built
to avoid.

---

## What Phase 3 hands to Phase 4, and what is still missing

| Phase 3 left | Phase 4 uses it for | Where it is missing today |
|---|---|---|
| `ride_request` rows with `requested_time`, `queued_at`, `status` | Ready-time labels: when did this rider actually ask, relative to their shift | The pilot has to run; the demo data is synthetic |
| `trip` / `trip_stop` rows with real arrival times | Whether a promised pickup time was kept (the guarantee in §7) | Same |
| `override_log` rows with reasons | Learning which automatic choices supervisors reverse (B-P4-5) | Phase 2 override logs exist only from simulated supervisors |
| `suggestion` rows with `accepted` / `rejected` / `failsafe_assigned` | Per-rider and per-supervisor behaviour | OQ-39 must define "acceptance" first |
| `hold_window_min_minutes` / `_max_minutes`, fixed at the minimum | The dynamic hold window (B-P4-3) | The upper bound is a config key nothing reads |
| The simulator's logistic accept model (`simulator-spec.md`, "Phase 4") | S13 (M-P4-2) | Parameters are guesses until P03 |
| `road_speed_profile` learned from pings | ETA error inside the prediction error budget | Fills only once the pilot drives (OQ-22, B37) |

## Data the pilot must provide, per task

Models need history. Nothing below can be faked; each row is a hard dependency of the tasks that name it.

| Data | Minimum before the task can start | Collected by | Needed by |
|---|---|---|---|
| Ride requests per rider, with the rider's shift (start/end) | 6 weeks, ≥ 50% of riders with ≥ 15 requests per direction | Phase 1 request flow plus an `employee.shift` field (new, P01) | B-P4-1, B-P4-2, B-P4-4 |
| Zone-level demand by 15-minute slot | 6 weeks of the same | Derived from requests | B-P4-2, B-P4-3 |
| Actual pickup and drop times | Every pilot trip (already recorded) | Driver app | B-P4-1 (label noise), B-P4-4 (was the guarantee kept) |
| Override reasons from real supervisors | 4 weeks, ≥ 200 overrides | Phase 2 override flow | B-P4-5 |
| Offer responses (accept / reject / ignore, with reason) | 2 weeks of shadow offers | Shadow mode (B-P4-6) | M-P4-2, R-P4-1 |
| Whether a rider's late ride was by choice (stayed back) or by delay | A reason on cancellations and no-shows | Request cancel reasons (exists, free text) | B-P4-1 |

---

## Pilot data tasks

- [ ] **P01 · Capture the shift each rider works** · deps R03
  Docs: data-model.md (`employee`), user-stories.md EMP-01
  Do: `employee.shift_start` / `shift_end` (optional, time of day, per weekday set), loadable from the
  onboarding pack's `employees.csv` (new optional columns, validated by `make onboard-dry-run`) and editable
  by the client admin. Ready time is predicted *relative to the shift end*; without the shift the model has
  nothing to be relative to.
  Done when: the import accepts the columns, the dry-run reports a bad time with its row, the field appears
  on the client admin's employee form; no API behaviour changes for riders who have none.

- [ ] **P02 · Agree what "acceptable prediction error" means** · deps R04
  Docs: roadmap.md Phase 4 exit; this file
  Do: with the pilot operator, write down the cost of being wrong in each direction: a held cab that waits
  for a rider who does not come, versus a cab sent with a half-empty trip because the model said nobody
  would arrive. Turn that into numbers: the ready-time error (minutes, p50 / p90) and the zone-demand error
  (requests per slot) that still beat the Phase 3 fixed hold window in the simulator replay of the
  pilot's own data.
  Done when: an entry in `open-questions.md` is closed with the numbers, and B-P4-1 / B-P4-2 have a pass mark
  they can be tested against. **The owner decides; the model does not.**

- [ ] **P03 · Calibrate the simulator's behaviour model from the pilot** · deps P01, 6 weeks of data
  Docs: simulator-spec.md ("Demand model", "Phase 4")
  Do: replace the simulator's assumed ready-time distribution (`Normal(shift_end + 10, 15)`) and the offer
  accept logistic with ones fitted to the pilot's requests and the shadow-offer responses. Keep the
  assumed ones as the named `default` so old runs stay reproducible.
  Done when: a scenario run with the `pilot` profile reproduces the pilot's per-slot demand within the
  tolerance P02 set; the run records which profile it used.

---

## Backend

- [ ] **B-P4-1 · Ready-time model** · deps P01, P02
  Docs: allocation-rules.md §6 (hold window) and §7, data-model.md (`prediction`), tech-stack.md (ML)
  Do: for each rider and direction, predict the distribution of the time they will ask for a ride, from their
  own history, weekday, shift end and the day's context (the client's policy windows, rain flag if the
  simulator or the pilot records one). scikit-learn / LightGBM, trained offline from `ride_request`, stored
  as versioned rows in `prediction` (`kind = ready_time`, `model_version`, `value` = quantiles), with the
  **actual** written back when the request arrives so the error is always measurable.
  A rider with too little history gets **no prediction** (an explicit `insufficient_history` reason), never a
  guess.
  Done when: on a held-out 20% of the pilot's weeks, p50 / p90 error meet P02's pass mark; the model is
  pure of the database (takes arrays, returns quantiles) so a replay gives the same numbers; the nightly
  job that trains it is a Celery task with a failure that is visible, not silent.

- [ ] **B-P4-2 · Zone-demand model** · deps P01, P02
  Docs: data-model.md (`prediction`, `zone`), allocation-rules.md §6
  Do: predicted requests per zone per 15-minute slot for tomorrow, from the same history plus the ready-time
  predictions summed per zone. Stored as `prediction` rows (`kind = zone_demand`).
  Done when: error against actuals is reported per zone in a new report (`reports.md`), meets P02's pass
  mark on held-out weeks, and a zone with too little history reports `insufficient_history` rather than 0.

- [ ] **B-P4-3 · Dynamic hold window** · deps B-P4-2, B29 (done)
  Docs: allocation-rules.md §6 "Evening hold window", control-model.md
  Do: replace the fixed minimum with: hold while `P(a compatible rider arrives within t min) × expected
  saving > the rider's weighted wait cost`, bounded by `hold_window_min_minutes` and `hold_window_max_minutes`
  (the maximum is read for the first time). The four existing exemptions (VIP, priority ≤ 2, high urgency,
  `no_sharing`) and `forced_priority` still win. With no prediction available the window is the Phase 3
  fixed minimum: **the dynamic window may only ever shorten or lengthen within the configured bounds, and
  falling back is always safe.**
  Done when: with a prediction of an imminent compatible rider the request is held longer than the minimum
  and never longer than the maximum; with none it behaves exactly as Phase 3 (a test pins this); the reason
  for every hold is visible to the supervisor ("holding 6 min: 2 riders expected in Sector 62").

- [ ] **B-P4-4 · Ride offers** · deps B-P4-1, B-P4-3, B32, B34
  Docs: allocation-rules.md §7, data-model.md (`ride_offer`), user-stories.md EMP-10, roles-and-permissions.md
  Do: the `ride_offer` table, `POST /ride-offers/{id}/respond` (`accept`, `reject` with optional preferred
  time), expiry after `offer_expiry_minutes` (default 10), and the planner that proposes pooled trips ahead of
  time from predicted ready times. Rules from §7: confidence ≥ `offer_min_confidence` (0.7), **at most one
  offer per rider per direction per day**, and on-demand requests always remain possible. **Accepting
  creates a normal `ride_request`, locked to the planned trip** (hard rule 6: the optimizer never moves
  it), with the pickup guaranteed within ± `pickup_window_minutes`. Every state change goes through the
  state machine (a new offer machine in `trip-lifecycle.md`).
  `api-spec.yaml` first; Dart client regenerated; the app owner is told in `COORDINATION.md`.
  Done when: each rule in §7 has a test of its own; an accepted offer is a locked request on the right trip;
  a rejected one never blocks a later on-demand request; the guarantee is checked after the trip and
  recorded (B-P4-7 reports it); authorization is on the server for every endpoint.

- [ ] **B-P4-5 · Learning from override logs** · deps B-P4-4, 4 weeks of real overrides
  Docs: control-model.md §3, allocation-rules.md §4 (weights)
  Do: **suggest** weight and rule changes from the reasons supervisors give when they override
  (`driver_issue`, `local_knowledge`, `traffic`, ...): for example, a zone where `local_knowledge`
  overrides cluster on the same road suggests a speed or detour adjustment. Output is a report and a
  proposed `config` diff for the operator admin to accept or ignore. **Nothing changes a weight by itself**,
  the same rule as the mode prompts (B35): the system suggests, a human decides.
  Done when: a fixture of overrides produces the expected suggestion; accepting one writes the config
  through the normal config path with the accepting user recorded; ignoring one is remembered.

- [ ] **B-P4-6 · Shadow mode for offers** · deps B-P4-4
  Docs: this file
  Do: run the offer planner and *record* what it would have offered, without sending anything, for a
  configurable period per client. The first two weeks of every client are shadow, so the model's confidence
  can be checked against what riders then actually did.
  Done when: shadow offers are in `ride_offer` with `response = shadow`, never notified, never creating a
  request; a report compares "would have offered" with "rider's own request time".

- [ ] **B-P4-7 · Prediction and offer reports** · deps B-P4-1, B-P4-2, B-P4-4
  Docs: screens-by-role.md (A-07), reports.md
  Do: prediction error by model version and by zone; offer funnel (planned → sent → accepted / rejected /
  expired) and acceptance rate by client; guarantee kept rate; hold-window minutes saved vs the Phase 3
  fixed window. Acceptance counts `accepted` over *sent*, excluding shadow offers (the OQ-39 lesson: the
  definition is written down before the number is quoted).
  Done when: each figure is reproduced by a test against a known fixture.

- [ ] **B-P4-8 · Privacy review of the models** · deps B-P4-1
  Docs: roles-and-permissions.md, CLAUDE.md hard rules 3 and 10
  Do: a rider's ready-time history is behavioural data about a named person. Decide and document who can see
  a per-rider prediction (nobody outside the rider and the platform's own jobs, by default), retention
  (predictions older than N months are deleted), and that no per-rider prediction leaves the operator's
  tenant. Aggregates only in reports.
  Done when: an ADR records the decisions; an endpoint test shows a supervisor cannot read a rider's
  prediction; the retention job exists and is tested.

## App

- [ ] **A-P4-1 · Rider: the offer card** · deps B-P4-4
  Screens: E-08 · Docs: screens-by-role.md, user-stories.md EMP-10
  Done when: a rider sees an offer with the proposed time, how many co-riders, and the pickup guarantee;
  Accept creates the ride and shows it; Reject offers an optional preferred time; an offer that expires
  disappears and says so. Every string in English and Hindi.

- [ ] **A-P4-2 · Supervisor: why we are holding, and what is coming** · deps B-P4-3
  Screens: S-04, S-05
  Done when: a held request shows the reason and the minutes left; the supervisor can release it now
  (the existing "send a cab early" action); planned offered trips appear on the board marked as such.

- [ ] **A-P4-3 · Admin: prediction and offer reports, shadow switch** · deps B-P4-6, B-P4-7
  Screens: A-07, A-08
  Done when: the admin sees the funnel and error reports and can move a client between shadow and live
  offers, with the switch recorded as an audited setting change.

## Simulator

- [ ] **M-P4-1 · Offer behaviour in the simulator** · deps B-P4-4
  Docs: simulator-spec.md ("Phase 4")
  Do: simulated riders accept an offer with probability from a logistic of (proposed time − preferred time)
  and the number of co-riders; parameters in the scenario, with the pilot-fitted profile from P03 selectable.
  Done when: a rider agent answers offers over the real API; an unanswered offer expires on the simulated
  clock; the same seed reproduces the same answers.

- [ ] **M-P4-2 · S13 `offers_week`** · deps M-P4-1, P03
  Docs: scenarios.md S13
  Do: 5 simulated days, offer model on. Assertions: offer acceptance ≥ 40% *with the simulator's behaviour
  model*, no rider double-booked (an accepted offer and an on-demand request for the same direction and
  hour), no offer sent outside §7's rules.
  Done when: S13 runs in `make sim-full` against a live backend, three seeds, all pass.

- [ ] **M-P4-3 · Policy comparison with prediction** · deps B-P4-3, M-P4-2
  Docs: simulator-spec.md (M13)
  Do: the same scenario and seed with the fixed hold window versus the dynamic one, side by side (cab-km per
  trip, median wait, vehicles used). The runs differ only in that setting, which a test asserts.
  Done when: one command prints the table; a prediction that is deliberately made wrong makes the numbers
  worse, which proves the table measures the prediction and not the noise.

## Release

- [ ] **R-P4-1 · Shadow offers on the pilot** · deps B-P4-6, A-P4-1
  Do: switch on shadow mode for every pilot client for two weeks with the operator informed.
  Done when: the "would have offered" report is read with the operator, and they say which clients they
  are willing to turn live.

- [ ] **R-P4-2 · Live offers for one client** · deps R-P4-1, B-P4-7
  Do: turn offers live for one client, one direction (the morning `to_office`), with the emergency pause
  and the per-client switch in front of the operator.
  Done when: four weeks run; acceptance, guarantee-kept rate and rider complaints are read with the
  operator; **offer acceptance > 40%** is measured the way B-P4-7 defines it; the operator states what
  they would need before widening it. This is the Phase 4 exit.

---

## Order and dependencies at a glance

```
R03 ─ P01 ─┬─ B-P4-1 ─┬─ B-P4-3 ─ A-P4-2
           │          │
           └─ B-P4-2 ─┘
R04 ─ P02 ─┘             B-P4-1 ─ B-P4-4 ─ B-P4-6 ─ R-P4-1 ─ R-P4-2
                         B-P4-4 ─ A-P4-1, M-P4-1 ─ M-P4-2 (needs P03)
B-P4-4 ─ B-P4-5 (needs 4 weeks of real overrides)
B-P4-1 ─ B-P4-8
B-P4-1, B-P4-2, B-P4-4 ─ B-P4-7 ─ A-P4-3
```

The first things that can start without waiting for data: **P01** (a column and an import rule), **B-P4-8**
(a decision about privacy), and the **shape** of B-P4-4 (the offer table and state machine, tested with
hand-written predictions). Everything that fits a model waits for the pilot.

## Open questions this phase has to resolve

- **P02 (new)** — what prediction error is acceptable. The owner's call, made with the operator.
- **OQ-39** — what "acceptance" is measured over. B-P4-7 reuses the Phase 3 definition for suggestions and
  writes the offer one down the same way before the 40% is quoted.
- **OQ-22** — real road speeds. Offer pickup guarantees are only as good as the ETAs under them.
- **New: rider consent for behavioural modelling.** Whether the client (the employer) and the rider must
  be told, and in what words, that ride history is used to predict their ready time. Needs a decision
  before B-P4-1 trains on real people; B-P4-8 records it.
- **New: what an offer promises when the cab is late.** §7 says the pickup is guaranteed within ±
  `pickup_window_minutes`; nothing says what happens to the rider, or the operator's bill, when it is not.
