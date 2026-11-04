# ADR-0016: A rider stranded by a breakdown gets a re-ride from where they are standing

- Status: accepted
- Date: 2026-10-02
- Settles: OQ-27. Completes ADR-0012.

## Context
ADR-0012 made a breakdown end the trip and sent every rider who had **not** been collected
back to `queued`. It deliberately left one case undecided: the rider who was already in the
cab. `picked_up` led only to `dropped`, so there was no honest transition for them —
marking them dropped would record a journey that did not happen — and they sat on an
aborted trip until they gave up or expired. `trip-lifecycle.md` §2 said only that such
riders "get new handling by supervisor".

OQ-27 offered three ways out: a `picked_up -> queued` edge for a re-ride, a distinct
terminal status such as `stranded`, or a supervisor-only manual resolution.

Settling it exposed a second problem that is really a data-model one. A re-ride has to
start **where the rider is**, and the rider is on a kerb somewhere between their origin and
their destination. `ride_request.location` cannot carry that: it is the rider's own end of
the journey, which is the *pickup* for a `to_office` request but the *drop* for a
`from_office` one, where the pickup is implicitly the office. Writing the breakdown point
into `location` fixes the morning commute and corrupts the evening one — it would delete
where the rider was going **and** still send the next cab to the office.

## Decision

**1. `picked_up -> queued` exists, and only for an aborted trip.**
The state machine guards it: the transition is refused unless the rider's trip is
`aborted` (`_guard_restrand`). The guard is the whole point of the edge — without it, any
actor could un-collect a rider after the fact, which nobody should be able to do.

**2. `ride_request.pickup_location` (nullable point) says where to collect them.**
`None` for every ordinary request, in which case collection follows the direction exactly
as before. When set, it wins everywhere a pickup place is computed: the candidate ETAs the
supervisor chooses from, the detour arithmetic, and the pickup stop itself. `Rider.pickup`
carries it into the pooling domain, so one rider collected somewhere unusual costs the
others the detour it actually costs them.

**3. The breakdown point is the driver's reported position, or the cab's last ping.**
`POST /driver/issues` may carry `lat`/`lng`; a driver dealing with a broken cab often will
not. Failing that, the last `location_ping` within 15 minutes is used — read from the
table, not Redis, for the reason dispatch reads pings too: a cold cache is not a position.
With neither, the rider is **still** re-queued, with no pickup override, and the alert says
`pickup_known: false`.

**4. A stranded rider's `urgency` becomes `high`, and the supervisor gets their own alert**
(`system`, `riders_stranded_by_breakdown`, with the count). They have already been let down
once and are now standing outdoors; ahead of someone still at home is the only defensible
order. The breakdown alert alone cannot tell a supervisor that anyone is on a kerb.

## Consequences
- S05 (`breakdown_with_riders`) can assert on rider outcomes, not only on the trip. Riders
  on board are no longer written off to expiry.
- A re-ride is a new assignment, so it goes through the ordinary manual flow: the board,
  the candidate list, a supervisor pressing assign. Mode is manual in Phase 1 and a
  breakdown is exactly when judgement is wanted.
- The pickup override is a general capability now, and that is a loaded gun: anything that
  sets it moves where a cab is sent. Only the breakdown path writes it, and the API exposes
  it read-only.
- `pickup_location` is in the `RideRequest` response, so clients can show the kerb rather
  than the home address. A client that ignores it shows the wrong pin — the Flutter app
  must honour it when the dispatch screens are built.
- The rider's `location` is never rewritten, so reports, pooling zones and their home
  address survive an incident untouched.

## Alternatives considered
- **A terminal `stranded` status.** Honest, and cheaper — no migration, no dispatch change.
  Rejected: it records the problem and solves nothing. The rider is still on the kerb, and
  the platform's answer to "my cab broke down" would be to close the request.
- **Overwrite `location` with the breakdown point.** What the first cut of this change did.
  Rejected: correct only for `to_office`, and silently destroys the destination of every
  `from_office` rider — the evening commute, which is half the product.
- **Requeue only `to_office` riders.** Rejected for the same reason: it leaves exactly the
  riders the platform most often carries without a way home.
- **Fold the pickup into `Rider.place` and let the planner infer it.** Rejected: `place` is
  the rider's own end of the journey and both ends are needed. A second field in the
  planner is the smaller lie than an overloaded first one.
- **Auto-reassign the stranded rider to the nearest cab.** Rejected for Phase 1, as in
  ADR-0012: that is an optimizer decision.
