# ADR-0012: A breakdown ends the trip, and uncollected riders go back on the queue

- Status: accepted
- Date: 2026-09-27

## Context
DRV-06 says a breakdown "marks the vehicle `out_of_service` pending supervisor
confirmation", and B17 implemented exactly that: `POST /driver/issues` raises an alert and
takes the cab off the road.

`trip-lifecycle.md` §2 also carries the edge `in_progress --> aborted: breakdown /
emergency`, and the state machine has always allowed it. **Nothing ever called it.**

The S05 scenario (`breakdown_with_riders`) showed what that costs. The cab was marked
out of service, the driver agent carried on tapping through the trip, and the ride
*completed* — in a vehicle that had broken down twenty minutes earlier. The riders were
recorded as delivered. Nothing in the run reported a problem.

Two questions had to be answered to fix it:

1. Does a breakdown end the trip, or only park the cab?
2. What happens to the riders on it?

## Decision

**A breakdown or accident ends the trip**, not just the vehicle's availability.

Which terminal state depends on whether the trip had started, following §2's own wording
— `cancelled` is "before start", `aborted` is "stopped mid-way":

| Trip status when the cab breaks down | Ends as |
|---|---|
| `in_progress` | `aborted` |
| `planned`, `dispatched` | `cancelled` |

Every unfinished stop on that trip is `skipped`, so the trip is genuinely closed rather
than left with pending work nobody will ever do.

**Riders who had not yet been collected return to `queued`** with their `trip_id`
cleared, using the `assigned -> queued` edge the state machine already had for
reassignment. The supervisor then sees them on the board and can send another cab — which
is what the S05 run now shows happening.

**A rider already inside the cab is left on the aborted trip**, and this is the part we
are deliberately not deciding here. `picked_up` leads only to `dropped`; marking them
dropped would record a journey that did not happen, and inventing an edge would be
guessing at a product decision. `trip-lifecycle.md` §2 says such riders "get new handling
by supervisor" without saying what that is. Tracked as **OQ-27**.

## Consequences
- A driver cannot complete a ride in a broken-down cab. The next stop action returns 409,
  and the simulator's driver agent now stops working the trip when it reports a
  breakdown, as a real driver app would.
- Uncollected riders are not silently stranded: "0 lost requests", S05's own bar, is met
  by the re-queue rather than by luck.
- The supervisor gets more work during an incident, which is correct for Phase 1 — every
  assignment is a human decision, and a breakdown is exactly when judgement is wanted.
- A rider in the cab still ends up giving up or expiring until OQ-27 is settled. That is
  visible in the S05 metrics rather than hidden, which is the point of leaving it open
  rather than papering over it.

## Alternatives considered
- **Leave the trip open and let the supervisor cancel it.** Rejected: the window between
  the breakdown and the supervisor noticing is exactly when the driver app keeps
  accepting stop actions, and the state machine already says what should happen.
- **Always `aborted`.** Rejected: §2 distinguishes the two states by whether the trip had
  started, and a cab that breaks down in the depot has not stopped anything mid-way.
- **Auto-reassign the uncollected riders to another cab.** Rejected for Phase 1: that is
  an optimizer decision, and mode is manual. Returning them to the queue puts the choice
  where the phase says it belongs.
