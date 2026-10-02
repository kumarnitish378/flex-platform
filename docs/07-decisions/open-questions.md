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
| OQ-30 | **Nobody tells the rider their cab broke down.** `trip-lifecycle.md` section 6 has a row for "trip aborted, SOS -> supervisor, operator admin (high priority)" and none for the rider, and ADR-0012 deliberately kept the breakdown off push ("urgent for whoever is watching the board"). That reasoning does not reach the person standing at the roadside: since ADR-0016 their request is back on the queue with a new pickup, and the app will simply show them queued again with no explanation. Options: (a) a `trip_aborted` notification to the affected riders, which is the one row section 6 is missing - my recommendation; (b) leave it to the supervisor to phone them, which is what WhatsApp dispatch does today; (c) nothing, and let the app's status change speak for itself. Cheap either way; it is a product call about what the rider is promised | Phase 1 | Product | open |
| OQ-29 | **Decided: a rider nobody came for is a failed run.** They were recorded as `not_travelling` - the value meaning "stayed at home" - because their agent was suspended mid-poll and never wrote an outcome, so `all_requests_terminal` passed on runs that left riders standing at their pickup point. They are `unresolved` now, recorded by the **run** at the moment the demand window closes and before the drain, and they take no further action: letting their patience expire during the drain would report a cancellation the day never contained and launder an abandonment into a `gave_up`. `unresolved` is reported in its two halves - `still_waiting` (nobody came; dispatch failed) and `still_riding` (carried when the clock stopped). No per-scenario tolerance was added; the assertion means zero and scenarios that cannot serve their demand now say so | Phase 1 | Product/Tech | **resolved** - ADR-0018 |
| OQ-28 | **Decided: a run drains rides in progress before it measures anything.** `duration_hours` is the demand window, not the length of the run: after it closes the clock keeps going for up to `drain_minutes_max` (default 60) while anyone is still in a cab, and stops the moment the last one gets out, so a healthy run pays nothing for it. Nothing new happens during the drain - riders ask for nothing and the supervisor has stopped assigning, leaving only drivers finishing trips they had already started. The cap keeps it honest: if it runs out with someone still aboard, that ride is genuinely stuck and the run still fails, with `drain_minutes` and `drain_capped` in `metrics.json` to tell the two apart. The second half of the fix: the **run** now records who was still riding, because leaving it to the rider agent made the outcome depend on whether one of its minute-by-minute polls happened to land past the end | Phase 1 | Product/Tech | **resolved** - ADR-0017 |
| OQ-27 | **Decided: a re-ride from where they are standing.** A rider who was already on board when the cab broke down returns to `queued` through a new `picked_up -> queued` edge that the state machine refuses unless their trip is `aborted`, with `urgency` raised to `high` and a `system` alert telling the supervisor someone is on a kerb. Where the next cab collects them is carried by a new nullable `ride_request.pickup_location` (the driver's reported position, else the cab's last ping within 15 minutes, else none and the supervisor places it): `location` could not hold it, being the *drop* for a `from_office` request, so writing the breakdown point there would have deleted the rider's destination and still sent the cab to the office. The override wins wherever a pickup is computed - candidate ETAs, detour arithmetic, the pickup stop - and is `None` for every ordinary request | Phase 1 (M08) | Product | **resolved** - ADR-0016 |
| OQ-26 | **Mostly fixed.** S02 ran at ~6x real time instead of the 60x it asks for. Two N+1 queries inside `PUT /simctl/clock` were the whole cost - the stale-vehicle sweep queried `location_ping` once per vehicle, and the ETA refresher re-read every vehicle's position once per trip. Both are now one query, taking a clock jump from **10,064 ms to 20 ms**, and riders read one shared status board instead of polling individually. S02 now runs at ~15x, so 16 simulated hours take about an hour - fine for a nightly `sim-full`, not for interactive use. The remaining cost is 35 drivers each polling `/driver/trips`; the next step would be `GET /dispatch/trips` (already in api-spec.yaml, not yet implemented) so drivers can share one read the way riders do | Phase 1 (M08) | Tech | mostly resolved; 15x is enough for nightly |
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
