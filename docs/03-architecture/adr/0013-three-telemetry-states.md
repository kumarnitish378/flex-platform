# ADR-0013: Off duty, no fix and no network are three different things

- Status: accepted
- Date: 2026-09-27

## Context
S06 (`gps_loss`) asks for two faults in one run: "one cab loses GPS 10 min, one cab
offline 15 min", and expects the backend to show the vehicle stale within 60 s, to stop
offering it as a candidate while it is dark, and to **accept a batch upload in order
after reconnection**.

The simulator modelled both faults with the same call — `go_off_duty()` — which made all
three states one state. That is wrong in two separate ways:

- Off duty is not a fault. `non-functional.md` treats it as a **privacy rule**: a driver's
  GPS is collected only while they are on duty. A cab parked off duty is a driver's own
  time, not a problem to alert on.
- Losing a satellite fix and losing the network are not the same event. One destroys the
  data; the other delays it. `mqtt-topics.md` allows a batch upload on reconnection
  precisely because the second case still has the positions.

With all three collapsed together, S06 could not distinguish them, and the batch-upload
path had never been exercised at all.

## Decision
The simulated vehicle carries three independent states:

| State | On duty? | Position recorded? | Sent? | Meaning |
|---|---|---|---|---|
| Off duty | no | **no** | — | Privacy rule: no GPS is collected at all |
| No fix (`has_fix = False`) | yes | **no** | — | The receiver cannot resolve a position; those moments are gone for good |
| No network (`connected = False`) | yes | yes | **later** | The app keeps recording and uploads the backlog, oldest first, on reconnection |

`lose_fix()` / `regain_fix()` and `disconnect()` / `reconnect()` are separate operations,
and neither touches duty status. `reconnect()` returns how many held positions it
uploaded, so a scenario can assert the backlog actually arrived.

## Consequences
- S06 tests what it claims to. The two faults produce different observable behaviour, and
  the reconnect path — which the backend is required to accept in order — is exercised
  for the first time.
- A cab that has gone dark is still on duty, so the backend's stale-vehicle sweep treats
  it as a working cab that stopped reporting, which is what a supervisor needs to see.
  Marking it off duty would have made a fault look like a driver's lunch break.
- The distinction is the simulator's, but it mirrors what the real driver app must do:
  buffer on network loss, discard on fix loss, send nothing off duty.

## Alternatives considered
- **Keep one "dark" state.** Rejected: it cannot express the batch upload, which is an
  explicit acceptance criterion of S06 and a real requirement on the backend.
- **Model network loss by dropping pings.** Rejected: that is the `ping_loss_rate` knob
  and means something else — occasional loss on a working connection, with nothing
  retained to send later.
