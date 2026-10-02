# ADR-0019: A request nobody has served is escalated, not re-created

- Status: accepted
- Date: 2026-10-02

## Context
A rider asks for a cab and ten minutes later nothing has been assigned. Until now the
platform did nothing in particular about it: the request sat on the board, the supervisor
saw it in a list sorted by waiting time, and the next thing that happened to it was either
an assignment, the rider giving up (~40 minutes in the simulator's demand model), or
expiry at 120 minutes. The S02 run is the extreme version — 240 riders asked, 240 gave up —
and nothing in the product tried to intervene between the ask and the giving up.

"The rider should retry" is the obvious response, and it has three incompatible readings:
re-create the request, tell the rider and let them decide, or make the platform try harder.
The first is the trap: cancelling and re-creating resets the waiting clock, so a rider who
waited fifty minutes would be reported as having waited ten — and p90 wait is the number
the pilot is judged on.

## Decision

**A request still `queued` after `retry_after_minutes` (default 10) is escalated**, and
again at every interval after. It stays **one request with one waiting clock**.

Each escalation:
- **widens that request's candidate ETA ceiling** by `retry_eta_widen_minutes` (10) per
  interval, up to `retry_eta_max_minutes` (45). A rider who has waited half an hour is
  better served by a cab twenty-five minutes away than by the rule that says twenty;
- raises `urgency` to `high`, so the request reads on the board as what it has become;
- raises one `request_unassigned` alert, the first time only. The sweep runs every minute;
  a supervisor must not get fifty identical alerts about one rider;
- sets `forced_priority`, which in Phase 1 is **only a flag** — see below.

### What this actually does in Phase 1, and what it does not
Being precise about this, because the obvious description overstates it. `forced_priority`
is a column nothing reads: the pooling hold window it is meant to short-circuit
(`allocation-rules.md` section 2 rule 10) is not implemented in Phase 1, and the cost
function that would weigh it arrives with the Phase 2 optimizer. The board is already
sorted by waiting time, so an escalated request was at the top anyway.

What bites today is therefore: **one alert** telling a human that nobody has sent this
rider a cab, a **wider search** so a cab 30 minutes away stops being flagged as a rule
break, and **`high` urgency** that the supervisor can see. In manual mode the actor is the
supervisor — escalation makes sure they know and widens what they can legitimately choose.
The same numbers become a real filter when the optimizer uses them.

**Escalation waits until the cab is actually due.** The condition is "queued for
`retry_after_minutes`" **and** "within `pickup_window_minutes` of the pickup the rider
asked for". A rider who asks at 06:00 for a 09:30 pickup is not being failed at 06:10, and
escalating them would force priority across the whole morning and so mean nothing at the
moment it mattered.

**The widening is derived, not stored.** It is a function of how long the request has
waited, so there is no escalation state to drift from what the board shows, and re-running
the sweep changes nothing. Only the alert needs a stamp (`escalated_at`), to fire once.

### The clock defect this uncovered
The first implementation compared `ride_request.created_at` against the injected Clock.
`created_at` is a database `now()` default — the **system** clock — which is exactly what
hard rule 2 forbids domain code from reading. Under the simulator it is real wall time
while everything it would be compared against is simulated.

It was already being used that way elsewhere: `waiting_since` on the API and
`wait_minutes` in the operator report (B18) both measured from `created_at`, so **every
wait figure the platform itself reported during a simulated run was meaningless** — hours
out. Nobody noticed because the simulator measures waits independently, from its own
agents, and those are the numbers that have been quoted.

So `ride_request` now carries `queued_at`, set from the Clock at creation beside
`expires_at`, and everything that measures waiting reads it: escalation, `waiting_since`,
and the report. `created_at` goes back to being the row's own bookkeeping.

## Consequences
- In Phase 1 the ETA ceilings are **reported, not enforced** (ADR-0011), so widening
  removes a flag from a cab the supervisor could already have chosen — see the section
  above for what this does and does not change today.
- `forced_priority` and `hold_until` are both columns nothing reads. They were in the data
  model before anything used them, which is how `enroute_reuse_max_eta_minutes` came to sit
  unread for three milestones. Worth a sweep for others like it.
- The operator report's wait figures change for any data recorded under a simulated clock —
  they become true. Production numbers are unaffected: there, the Clock and the database's
  `now()` agree to within milliseconds.
- `retry_after_minutes` interacts with rider patience, which in the simulator averages 40
  minutes. Escalating at 10 leaves three intervals of widening before a rider typically
  gives up. If the pilot shows riders waiting differently, this is the knob.
- The rider is still told nothing — see **OQ-30**. Escalation is what the platform does;
  what the rider is promised is a separate decision.

## Alternatives considered
- **Cancel and re-create the request ("retry" literally).** Rejected: it resets
  `waiting_since`, so the platform's own wait metric would under-report every rescued rider,
  and p90 wait is the headline the pilot is judged on.
- **Notify the rider and let them choose.** Not rejected so much as separate: it does
  nothing to find them a cab. Tracked as OQ-30.
- **Escalate purely on time since the request.** Rejected: with lead times of 45 minutes,
  every advance booking would escalate long before anyone needed a cab, and a priority flag
  everything carries is a priority flag that means nothing.
- **Store the widened ceiling on the request.** Rejected: a stored copy of something
  derivable from the wait is a second source of truth that can disagree with the board.
