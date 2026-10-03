# ADR-0020: The rider is told when their cab stops

- Status: accepted
- Date: 2026-10-03
- Settles: OQ-30. Decided without the product owner present, on their instruction; overrulable.

## Context
`trip-lifecycle.md` §6 lists who is notified for every transition. For an aborted trip it
says "Supervisor, operator admin (high priority)" and names **nobody on the rider's side**.

Two things followed from that gap, and both were invisible until they were looked for:

1. ADR-0016 sends a rider whose cab broke down under them back to `queued`. From the
   rider's phone that is a request they watched reach "on the way", then "picked up", then
   silently reappear as "waiting" — while they stand on a roadside. No message explains it.
2. The `trip_aborted` template has existed since B16 and **nothing ever sent it**.
   ADR-0012 reasoned that a breakdown needed no push because it was "urgent for whoever is
   watching the board", which quietly contradicted §6's own table. So not even the
   supervisor got the notification the spec promises.

The product's stated purpose makes this sharp. `vision-and-scope.md` puts the main pain as
uncertainty and hour-long waits; the roadmap puts visibility before any AI. A rider
stranded with no explanation is the most uncertainty this platform is capable of creating.

## Decision

**The rider is notified, with a new `ride_interrupted` type**, high priority.

A separate type from `trip_aborted` because it is a different message to a different
person: the supervisor is told to re-dispatch, the rider is told what happened to the cab
they were waiting for. The app switches on these keys, and a rider's phone should never
receive a message written for an operations desk.

**Two wordings, chosen by whether the rider was on board**, because the useful instruction
differs and a wrong one is worse than none:

| Situation | Told |
|---|---|
| Was on board (stranded) | "Your cab had a problem and could not finish the trip. Please stay where you are — another cab is being arranged to collect you from there." |
| Never collected | "Your cab had a problem before it reached you. Your request is back in the queue for another cab — you do not need to book again." |

The second half of each matters as much as the first. A stranded rider who wanders off
cannot be found by the cab heading to their `pickup_location`. A rider at home who is not
told "you do not need to book again" books again — which is a second request for the
supervisor to serve and a second cab sent to the same person.

**`trip_aborted` is now actually sent** to supervisor and operator admin, as §6 always
said. ADR-0012's reasoning is overturned: "someone is watching the board" is an assumption,
not a mechanism, and §6 is the contract.

## Consequences
- `trip-lifecycle.md` §6 gains the row it was missing, so the table and the code agree.
- A breakdown now sends up to four notifications (two rider groups, supervisor, operator
  admin) where it previously sent none. All are recorded in `notification`; push depends on
  the configured provider, and `LogPushSender` is the Phase 1 default.
- An employee with no `user_id` has never logged in and cannot be told. That is not an
  error — the supervisor's alert is the safety net — and it is silent by design.
- The wording is in `notifications.py`, pure and table-driven, so it can be reviewed and
  translated without touching dispatch. ARB/i18n is an app task (A01); these strings are
  English-only until then.

## Alternatives considered
- **Reuse `trip_aborted` for the rider.** Rejected: one key cannot carry two audiences
  without the app guessing which it is holding, and "Riders need re-dispatching" is not a
  sentence to send to a rider.
- **Say nothing and let the status change speak.** Rejected: that is the behaviour this
  settles. "Waiting" appearing after "picked up" is not an explanation, it is a mystery.
- **Leave it to the supervisor to phone them.** What WhatsApp dispatch does today, and the
  thing the product is sold to replace. It also fails exactly when it is needed most — a
  supervisor in the middle of an incident is the least likely person to make the call.
