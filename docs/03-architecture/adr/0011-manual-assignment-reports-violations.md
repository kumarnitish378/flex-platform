# ADR-0011: Manual assignment reports hard-rule violations; only capacity blocks

- Status: accepted
- Date: 2026-09-25

## Context
`allocation-rules.md` §2 lists eleven hard rules that a candidate must satisfy. They are
written for the **optimizer**: a rule a candidate fails is removed from the auto-assignment
search. Phase 1 has no optimizer — every assignment is a supervisor pressing a button.

Task B14 says hard-rule checks are "reported as `violations` only in Phase 1", and
separately that "adding to a full vehicle is rejected". That leaves one question the code
has to answer either way: when a supervisor manually assigns against a hard rule, does the
server refuse?

## Decision
`POST /dispatch/assign` **reports** every hard-rule violation and **applies** the
assignment anyway, with one exception: **seat capacity is enforced and returns 409**.

The violations are recorded on the trip event, so an override against the rules is visible
afterwards rather than invisible.

Blocking stays with things that are not judgement calls:

| Refused (409/422) | Reported as a `violation` |
|---|---|
| Riders on board would exceed `seat_capacity` | Detour limits (`max_detour_factor`, `max_detour_minutes`) |
| The state machine has no such edge (e.g. the request is already assigned or cancelled) | Pickup time window (`pickup_window_minutes`) |
| The request, vehicle or trip belongs to another operator (404) | ETA over `candidate_max_eta_minutes` |
| | Vehicle GPS stale, or vehicle not `available`/`on_trip` |
| | Request locked to a different vehicle |
| | Trip has `pooling_blocked`, or the request is `no_sharing` and the trip is shared |
| | VIP employee in a non-VIP vehicle |
| | Direction or office mismatch with the trip |

## Why
A supervisor overriding the rules is the *purpose* of manual mode, not a bug in it. The
rules encode averages: "within 20 minutes", "detour at most 1.5x". The supervisor knows the
road is flooded, the client called, the driver lives on that street. A server that refuses
sends them back to the phone-and-WhatsApp dispatch this product exists to replace.

Capacity is different in kind. It is not an average or a preference — five people do not
fit in a four-seat car, and an assignment that says they do produces a driver stranded at a
pickup with nowhere to put the rider. The same goes for tenancy and the state machine:
those refusals protect correctness, not optimality.

## Consequences
- The supervisor UI must show `violations` prominently before the confirm button (SUP-03).
- Phase 2 automatic assignment uses the **same** checks as a filter, not a report: the
  function returns the violation list, and the auto path treats a non-empty list as
  disqualifying. One implementation, two policies.
- `trip_event` carries the violations accepted at assignment, so "why did a 40-minute
  detour happen on 12 March" is answerable.
- If an operator later wants hard blocking, it becomes a config key rather than a rewrite.
