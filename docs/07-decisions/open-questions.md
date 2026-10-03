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
| OQ-22 | **Now the dominant term in every headline number, and still unsourced.** The `approx` provider assumes 24 km/h base, times the 0.6 peak factor from `simulator-spec.md` section 6, times the 1.4 road factor from `control-model.md` - an effective ~10 km/h door to door at peak. Measured against S02's own geometry: a cab leaving the single depot reaches a home 3 km away in **17.5 min**, 5 km in **29 min**, 7 km in **41 min**, and the office itself in **45 min**. `candidate_max_eta_minutes` is 20, so every rider beyond ~3.5 km of the depot is a hard-rule violation before anyone does anything wrong - which is exactly what the suite reports (S02: 68 of 68 assignments; S03: 46 of 46). With rider patience averaging 40 min, a 29-41 min approach arrives after the rider has gone, which is why **0 of 240** requests completed a single stop. So S02's "0 carried" is substantially a property of this constant and not of the dispatch logic. Calibrate from the first real GPS data (`road_speed_profile`) before any of these numbers are quoted outside the team | Phase 1 (B10 tuning) | Tech | open - **now blocking interpretation of every scenario result** |
| OQ-24 | Should `/auth/otp/request` reveal that a phone is unknown? Implemented as **no** (always 202), trading a slightly worse error message for not leaking who works where; api-spec.yaml was amended from the original 404. Overrule if the pilot operator's support team needs "this number is not registered" feedback in the app | Phase 1 (B03 review) | Nitish | decided provisionally (202 always) |
| OQ-33 | **Resolved.** Half of every simulated run's GPS was discarded and every candidate was flagged `gps_stale`. **Two causes, both in the ingestor, both invisible because Phase 1 only reports hard rules (ADR-0011) so the flag looked like noise.** (1) It reads simulated time from Redis via `SharedSimClock` and refreshed that value only on its flush loop - every 5 *real* seconds, which at `speed_factor: 60` is five simulated minutes of frozen clock, so pings arriving in the window were dropped as `too_far_future` (tolerance 2 min). The docstring already assumed a per-message refresh; the call did not exist. (2) `flush()` issues its INSERT inside an open transaction and only the 5-real-second timer committed, so written positions stayed invisible to the API's own connection for up to five simulated minutes. Measured on `smoke_tiny` across the three states: drops **2251 -> 0**, stored **1255/2661 -> 1768/1769**, chosen-cab position age median **340 s -> 160 s -> 35 s** (max 480 -> 300 -> 41) against a 60 s threshold - `gps_stale` no longer appears on any candidate. Neither bug could occur in production, where 5 real seconds is 5 real seconds; both would have hit Phase 2 hard, where the optimizer uses the violation list as a filter and would have found no vehicle dispatchable. A handful of `stale_vehicle` alerts still appear at the very end of a run, when pings stop during the drain - minor, and worth a look if it ever matters | Phase 1 | Tech | **resolved** |
| OQ-32 | **Every scenario parks the whole fleet at one depot, 45 minutes from the office at peak.** S02 and S03 both start 35 and 30 cabs at a single point and spread riders around it, so the first assignment of the morning is always a long dead-head and `no_cab` is zero throughout - cabs were always available, just never near anybody. Real operators either park near demand or keep cabs circulating, and the pilot's actual parking is unknown (OQ-01). Until it is known, the suite's service numbers are a worst case being read as a forecast. Options: (a) ask the pilot operator where cabs actually sit overnight and model that - the only answer that makes the numbers mean anything; (b) spread depots across the home zones as an explicitly-labelled optimistic variant, run alongside the pessimistic one, so the spread between them is visible; (c) leave it and caveat every quoted figure. Found by computing the depot-to-pickup ETAs behind S02's 68-of-68 rule violations | Phase 1 | Product/Tech | open |
| OQ-31 | **Decided: one rolling alert per operator.** It carries `riders` and `longest_wait_minutes`, is updated in place as more riders join it, and **resolves itself** once no queued request is still escalated - a condition alert that outlives its condition says riders are stranded when they are not, and teaches a supervisor to ignore the row. Per-request detail stays on the request, where a supervisor who clicks through is already looking. The count accumulates rather than being recounted, deliberately: a live count would fall as riders gave up, so the alert would get quieter as the morning got worse | Phase 1 | Product/Tech | **resolved** - ADR-0022 |
| OQ-30 | **Decided: the rider is told.** A new high-priority `ride_interrupted` notification, with two wordings because the useful instruction differs - a stranded rider is told to stay where they are (the next cab is coming to their `pickup_location`, and a rider who wanders off cannot be found), a rider never collected is told not to book again (otherwise they do, and the supervisor serves the same person twice). Separate from `trip_aborted` because the app switches on these keys and "riders need re-dispatching" is not a sentence to send a rider. Found while implementing: `trip_aborted` itself had a template since B16 that **nothing ever sent** - ADR-0012 decided a breakdown needed no push, quietly contradicting section 6's table. It is sent now | Phase 1 | Product | **resolved** - ADR-0020 |
| OQ-29 | **Decided: a rider nobody came for is a failed run.** They were recorded as `not_travelling` - the value meaning "stayed at home" - because their agent was suspended mid-poll and never wrote an outcome, so `all_requests_terminal` passed on runs that left riders standing at their pickup point. They are `unresolved` now, recorded by the **run** at the moment the demand window closes and before the drain, and they take no further action: letting their patience expire during the drain would report a cancellation the day never contained and launder an abandonment into a `gave_up`. `unresolved` is reported in its two halves - `still_waiting` (nobody came; dispatch failed) and `still_riding` (carried when the clock stopped). No per-scenario tolerance was added; the assertion means zero and scenarios that cannot serve their demand now say so | Phase 1 | Product/Tech | **resolved** - ADR-0018 |
| OQ-28 | **Decided: a run drains rides in progress before it measures anything.** `duration_hours` is the demand window, not the length of the run: after it closes the clock keeps going for up to `drain_minutes_max` (default 60) while anyone is still in a cab, and stops the moment the last one gets out, so a healthy run pays nothing for it. Nothing new happens during the drain - riders ask for nothing and the supervisor has stopped assigning, leaving only drivers finishing trips they had already started. The cap keeps it honest: if it runs out with someone still aboard, that ride is genuinely stuck and the run still fails, with `drain_minutes` and `drain_capped` in `metrics.json` to tell the two apart. The second half of the fix: the **run** now records who was still riding, because leaving it to the rider agent made the outcome depend on whether one of its minute-by-minute polls happened to land past the end | Phase 1 | Product/Tech | **resolved** - ADR-0017 |
| OQ-27 | **Decided: a re-ride from where they are standing.** A rider who was already on board when the cab broke down returns to `queued` through a new `picked_up -> queued` edge that the state machine refuses unless their trip is `aborted`, with `urgency` raised to `high` and a `system` alert telling the supervisor someone is on a kerb. Where the next cab collects them is carried by a new nullable `ride_request.pickup_location` (the driver's reported position, else the cab's last ping within 15 minutes, else none and the supervisor places it): `location` could not hold it, being the *drop* for a `from_office` request, so writing the breakdown point there would have deleted the rider's destination and still sent the cab to the office. The override wins wherever a pickup is computed - candidate ETAs, detour arithmetic, the pickup stop - and is `None` for every ordinary request | Phase 1 (M08) | Product | **resolved** - ADR-0016 |
| OQ-26 | **Resolved.** S02 ran at ~6x real time instead of 60x. Two N+1 queries inside `PUT /simctl/clock` were most of it - the stale-vehicle sweep queried `location_ping` once per vehicle and the ETA refresher re-read every vehicle's position once per trip; both are one query now, taking a clock jump from **10,064 ms to 20 ms**, and riders read one shared status board instead of polling individually (~15x). The last named cost was 35 drivers each polling `/driver/trips`: `GET /dispatch/trips` is **implemented** now (one query for the trips, one for all their stops) and the drivers share a `TripBoard` the way riders share the status board. Observation is shared; every action still goes through the driver's own token, and a driver's mid-trip stop read stays per-driver because the board is a minute stale | Phase 1 (M08) | Tech | **resolved** |
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
