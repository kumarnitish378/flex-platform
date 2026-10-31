# ADR-0027 — The optimizer is pure, models the hard rules, and is checked by the evaluator

**Status:** accepted · **Date:** 2026-11-01 · **Task:** B30, B31 · **Supersedes:** nothing

## Context

`allocation-rules.md` §6 asks for a batch optimizer: a pickup-and-delivery problem with
time windows and capacities, solved with OR-Tools routing over OSRM time matrices, with
the hard rules as **constraints**, the cost as the **objective**, a ten-second cap, and a
fall-back to Phase 2's single-insertion greedy when there is no answer. B31 adds that the
solver must be **pure of the database**, so the same inputs always give the same plan and
a scenario can be replayed.

Three things in that list pull against each other: a constraint model is only as correct
as its author, the routing library can only minimise a sum of arc costs, and "the same
inputs give the same plan" is not what a time-limited search does by default.

## Decision

**1. Two layers, and the database is only in the outer one.** `app/domain/optimizer/` takes
a `Problem` (plain frozen dataclasses plus two callables, `duration` and `distance`, backed
by one pre-fetched matrix) and returns a `Plan`. A guard test fails if anything in that
package imports SQLAlchemy, Redis, httpx, `app.modules`, the clock, or reads wall time.
`modules/dispatch/optimizer_service.py` loads the world, makes **one** routing call, runs
the solver, records the run, and (B32) delivers the plan.

**2. The hard rules are enforced twice, on purpose.** Inside the OR-Tools model they are
constraints (seats, exclusivity, rule 8 windows, rule 7 ride limits, locks, VIP vehicles,
the candidate and en-route ceilings, fixed order for under-way trips) so the search stays
in legal space. Then **every vehicle's result is re-judged by `route.check_route`**, which
calls the same `check_hard_rules` manual assignment and semi-auto use. The second pass
carries the guarantee; the first makes it rarely needed. A placement that fails it is
dropped and its riders are repaired by the greedy search on cabs the DARP did not touch.

**3. The objective is §4 as far as arcs can say it, and the answer is chosen by §4.** The
routing library minimises arc costs plus fixed costs. What it can state exactly: the empty
kilometres of an idle cab's approach, and the cost of waking an idle cab. §4's detour term
is a function of a whole path and cannot be an arc cost, so driving time is charged at the
batch's mean rider weight, which is the rider time driving burns. The result is then
**re-priced exactly** (`route.price_route`) and `solve()` returns the better of the DARP
plan and the greedy plan: more riders served first, then lower exact cost. The surrogate
steers the search; it does not get to decide the answer, and the optimizer is therefore
never worse than the Phase 2 baseline under the cost the docs define.

**4. Determinism comes from a solution count, not from the clock.** The search stops on
`solution_limit`; `optimizer_time_limit_seconds` is a failsafe cap. Inputs are sorted
before the model is built, so listing order does not change the answer. A test shuffles
the inputs and compares plans.

**5. A batch cost generalises §4 symmetrically.** Every rider on a touched route is charged
`w x (ride - baseline)`: baseline is the direct time for a new rider and the current ride
for a seated one. For one insertion this equals §4 plus the newcomer's own excess ride,
which a lone insertion has no one else to blame it on; two newcomers who detour each other
are the case it exists for.

**6. The shape of a trip makes this a vehicle-routing problem, not 2N delivery nodes.**
One direction and one office per trip means the delivery half of every request is the same
node. The model chooses *which cab* and *in what order*.

**7. Groups are solved one at a time.** Requests are partitioned by (direction, office);
an idle cab belongs to whichever group takes it first (groups in a fixed order). A cab with
a trip belongs to that trip's group. The approximation matters only to an operator whose
clients have several offices wanting the same idle cab in the same window.

**8. Bulk callers use `approx` on the public OSRM** (CLAUDE.md hard rule 7):
`build_bulk_eta_service`.

## Consequences

- A bug in the OR-Tools model can cost optimality, never legality.
- This build's Python binding cannot take `absl::Span` arguments, so
  `SetAllowedVehiclesForIndex` is replaced by restricting the vehicle variable directly.
- Pooling quality depends on the matrix. Until OQ-22 is closed with measured speeds
  (B37), the `approx` matrix is a property of a constant as much as of the dispatch.
- The model assumes slack-free arrival (a cab does not wait for a window to open), the
  same as the evaluator and the Phase 1/2 rule 8 check.
