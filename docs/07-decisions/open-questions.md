# Open questions

Agents: if you hit an unresolved question, add it here and ask the owner. Do not assume.

| ID | Question | Needed by | Owner | Status |
|---|---|---|---|---|
| OQ-01 | Who is the pilot operator; how many cabs, clients, employees, trips/day? | Phase 0 | Nitish | open |
| OQ-02 | If the pilot is the own employer's transport vendor, do employment terms allow it? | Phase 0 | Nitish | resolved by owner (2026-09-24); details to be added by owner |
| OQ-03 | Pricing model: per cab/month, per trip, or tiered subscription? | Phase 1 end | Nitish | open |
| OQ-04 | Driver tracking: app only, ESP32 tracker, or both? | Phase 1 | Nitish | open (app first) |
| OQ-05 | Routing engine: OSRM (default) or Valhalla? | Phase 0 (I02) | Tech | open (OSRM default) |
| OQ-06 | Semi-auto failsafe default: auto_assign or escalate? | Phase 2 | Operator | open (auto_assign default) |
| OQ-07 | Pilot client values for max detour and pickup window | Phase 2 | Operator/client | open (defaults in allocation-rules) |
| OQ-08 | Final rider weight values (priority × urgency) | Phase 2 | Tuning via sim + pilot | open |
| OQ-09 | Can employees opt out of pooling — per trip or per profile? | Phase 3 | Client | open |
| OQ-10 | Exact night-safety policy of pilot clients (escort, first pickup/last drop rules, hours) | Phase 2 | Client | open |
| OQ-11 | Team: solo or a part-time developer for app/dashboard? | Phase 0 | Nitish | open |
| OQ-12 | VIP request with no VIP car free: wait, or unshared regular car automatically? | Phase 2 | Operator | open (alert supervisor, no auto-substitution) |
| OQ-13 | When to ship iOS and web builds (iPhone share among employees)? | Phase 1 end | Nitish | open |
| OQ-14 | Simulator fidelity: SimPy only, or add SUMO later? | Phase 3 | Tech | open (SimPy) |
| OQ-15 | Acceptable ETA error for the pilot before learned traffic speeds? | Phase 1 | Operator | open (target p90 ≤ 8 min) |
| OQ-16 | SMS provider for OTP (cost, DLT registration in India) | Phase 1 (B03) | Nitish | open |
| OQ-17 | SMS fallback for critical notifications (assigned, arrived) or push only? | Phase 1 | Nitish | open |
| OQ-18 | Product name and domain | Phase 1 end | Nitish | open ("Smart Cab" is a working name) |
| OQ-19 | Data retention periods agreed with operator/client contracts | Phase 1 | Operator | open (defaults in non-functional.md) |
| OQ-20 | Push: Firebase Cloud Messaging or self-hosted ntfy? | Phase 1 (B16) | Tech | open (FCM default) |
| OQ-21 | Decide self-hosting (OSRM + tiles) before the paid pilot — **when**, not whether: the public OSM services have no SLA and may be withdrawn for commercial use, so task I02b must land before go-live. Trigger earlier if the 1 req/s cap or reliability bites | Before paid pilot | Tech | open (timing only — ADR-0010 §A3) |
| OQ-22 | `approx` provider base speed for NCR: what average km/h should the no-network estimator assume off-peak? Implemented provisionally as 24 km/h with the peak factor 0.6 from `simulator-spec.md` section 6 and road factor 1.4 from `control-model.md`; only the base speed is unsourced. Calibrate from the first real GPS data (`road_speed_profile`) | Phase 1 (B10 tuning) | Tech | open (24 km/h provisional) |
| OQ-24 | Should `/auth/otp/request` reveal that a phone is unknown? Implemented as **no** (always 202), trading a slightly worse error message for not leaking who works where; api-spec.yaml was amended from the original 404. Overrule if the pilot operator's support team needs "this number is not registered" feedback in the app | Phase 1 (B03 review) | Nitish | decided provisionally (202 always) |
| OQ-26 | S02 `normal_weekday` cannot currently run in reasonable wall-clock time. Its `speed_factor: 60` asks for an hour a minute; with 300 riders and 35 drivers it manages roughly 6x, because every agent's API call goes through a **synchronous** client inside a single-threaded SimPy loop, so each one blocks the whole simulation. Smaller scenarios are unaffected. Options: run agent HTTP concurrently (a thread pool behind `PlatformClient`, or an async client driven from the SimPy loop), or cut poll frequency - riders poll every simulated minute and drivers every 30 seconds, which is far more often than either needs. Blocks S02-S07 at full scale and therefore M08's nightly suite | Phase 1 (M08) | Tech | open |
| OQ-25 | Which permission should guard the `operator.{id}.alerts` WebSocket channel? `roles-and-permissions.md` has no alert permission yet (B17 adds the endpoints), so B13 rides on `request_queue_view` plus "not client-scoped", which admits exactly the supervisor / operator_admin / platform_admin set `architecture.md` names. **B17 shipped `GET /alerts` and the acknowledge/resolve endpoints on the same permission**, so the question now covers both the channel and the endpoints. Give alerts their own permission if the alert feed should ever be narrower than the request board - for example if SOS alerts should reach only a safety lead | Phase 2 | Tech | open (rides on request_queue_view) |
| OQ-23 | Time-of-day factors applied to OSRM durations for ETAs (ADR-0004: "OSM speeds + time-of-day factors"). Implemented provisionally in `EtaConfig` from the `simulator-spec.md` section 6 windows (peak 1/0.6, night 1/1.3); the real values should be fitted from `road_speed_profile` once GPS data exists, and moved into `operator_config` with B05 | Phase 1 end (B05 + B10 tuning) | Tech | open (provisional defaults in code) |

---

## Appendix: Phase 0 interview questions

### Operator owner
1. How many cabs do you run; owned vs attached drivers?
2. How many corporate clients; roughly how many trips per day?
3. Peak hours and requests during them?
4. When an employee waits over an hour, what is usually happening?
5. Complaints or lost clients due to waiting? Has a client left?
6. How do you decide which cab goes to which request?
7. How do you know where your cabs are right now?
8. Do clients give schedules in advance or is it last-minute?
9. How do you bill clients: per trip, per km, monthly?
10. What would halving waiting time be worth? Monthly, per cab or per trip payment?
11. Have you tried any software before? What happened?
12. How many "where is my cab?" calls/messages per day?
13. Any client complaints about phone numbers in groups or safety?

### Dispatcher
1. Walk me through a request from arrival to cab assigned.
2. Requests in the busiest hour?
3. Hardest part of your day?
4. How do you decide whether two employees can share?
5. Which requests get missed or delayed, and why?
6. Would you trust a system that suggests assignments if you can override?
7. Would a tracking link with live ETA reduce your workload?

### Drivers
1. After a drop, how do you learn about the next trip?
2. Time spent driving empty or waiting for assignment?
3. Comfortable with smartphone apps? Phone model?
4. Paid per trip, per km or salary?

### Employees
1. How often do you wait > 30 min? What do you do meanwhile?
2. Is the wait itself the biggest problem, or not knowing how long?
3. Do you leave the office at a predictable time?
4. Would you accept "cab leaving 7:10 with 2 colleagues, join?"; what would make you say no?
5. Would you share a cab for a guaranteed pickup time?
6. Android or iPhone?

### Own trip log (10–15 trips)
Request sent time · reply received time · cab arrival time · pickup time · drop time · notes.
