# User stories

Format: ID · story · phase · acceptance criteria (Given/When/Then). IDs are referenced from task files and tests.

## Employee (EMP)

**EMP-01 · Log in** · Phase 1
As an employee, I log in with my phone number and OTP so that I don't need a password.
- Given a phone number registered by my client admin, when I request an OTP, then I receive a 6-digit code valid for 5 minutes.
- Given a correct OTP, when I submit it, then I am logged in and see the employee home screen.
- Given an unregistered number, then I see "Number not registered. Contact your company admin." and no OTP is sent.
- After 5 wrong OTP attempts, OTP requests are blocked for 15 minutes.

**EMP-02 · Request a cab** · Phase 1
As an employee, I request a cab to or from the office with a time and location.
- The form pre-fills my saved home location and my office.
- I can choose direction (to office / from office), time ("now" or a time up to 7 days ahead), urgency, and adjust the pickup pin on the map.
- A landmark/notes field (max 200 characters) is optional.
- When I submit, then a request is created with status `requested` and I see a confirmation screen with a request ID.
- I cannot have two active requests with the same direction whose times are within 60 minutes of each other (error shown).

**EMP-03 · See cab details and ETA** · Phase 1
- When my request is assigned, then within 10 s I receive a push notification and the app shows: vehicle number, vehicle model, driver name, driver phone (tap to call), pickup ETA.
- The ETA refreshes at least every 30 s while the cab approaches.

**EMP-04 · Track the cab live** · Phase 1
- From assignment until pickup, I see the cab moving on the map (update latency ≤ 10 s from the driver's GPS ping).
- After pickup, I see the route and ETA to destination.
- If no GPS ping has arrived for 60 s, the map shows "Location updating…" and the last known time.

**EMP-05 · Status alerts** · Phase 1
- I get push notifications for: assigned, cab 5 minutes away, cab arrived, trip completed, cab changed (reassignment), request cancelled by operator.

**EMP-06 · Cancel a request** · Phase 1
- I can cancel any time before the cab arrives. After "arrived", cancel requires a reason.
- The driver and supervisor are notified immediately.

**EMP-07 · Trip history and rating** · Phase 1
- I see my last 90 days of trips with times and wait duration.
- After drop, I can rate the trip 1–5 with an optional comment (once per trip).

**EMP-08 · SOS** · Phase 1
- During an active trip, a visible SOS button sends an alert with live location to the supervisor and operator admin, and offers to call the emergency number 112.

**EMP-09 · Opt out of pooling** · Phase 3
- If the client policy allows, I can mark a request "no sharing". The system treats it as a hard rule.

**EMP-10 · Receive and answer ride offers** · Phase 4
- I receive an offer notification with proposed time, co-riders count, and pickup time guarantee.
- Accept → request created and locked to that trip. Reject → I can optionally give my preferred time.
- An offer expires after a configurable time (default 10 min).

## Driver (DRV)

**DRV-01 · Log in with phone + OTP** · Phase 1 (same as EMP-01).

**DRV-02 · Go on/off duty** · Phase 1
- Going on duty starts GPS sharing (foreground service with a persistent notification) and makes the vehicle assignable.
- Going off duty stops GPS and is blocked while a trip is in progress.
- The app asks for location permissions only when the driver first goes on duty, with an explanation screen.

**DRV-03 · See my trips in order** · Phase 1
- I see current and upcoming trips; for the current trip, stops in order with rider name, landmark, and planned time.
- New or changed assignments trigger a push notification with sound.

**DRV-04 · Navigate** · Phase 1
- Tapping a stop opens the route on the in-app map; an "Open in external navigation" button passes coordinates to any installed navigation app.

**DRV-05 · Update stop status** · Phase 1
- Buttons: Start trip → Arrived → Picked up / No-show → … → Dropped → Complete trip.
- "No-show" is enabled only after waiting at least `no_show_wait_minutes` (default 5) after "Arrived".
- Each tap is timestamped with GPS position; if offline, queued and sent later in order.

**DRV-06 · Report an issue** · Phase 1
- Driver can report: breakdown, accident, traffic block, rider issue. Supervisor is alerted; breakdown marks the vehicle `out_of_service` pending supervisor confirmation.

## Supervisor (SUP)

**SUP-01 · Live map** · Phase 1
- I see all on-duty vehicles on the map, coloured by state (free, on trip, en route to pickup, stale GPS > 60 s, out of service).

**SUP-02 · Pending requests with timers** · Phase 1
- I see all unassigned requests sorted by waiting time, each with a live timer. Requests waiting more than `alert_wait_minutes` (default 20) turn red.

**SUP-03 · Manual assignment** · Phase 1
- I select a request and a vehicle; the system shows ETA to pickup and current load; I confirm.
- The employee and driver are notified within 10 s.
- I can add a request to an existing trip if seats allow; the system shows the added minutes for existing riders.

**SUP-04 · Create request on behalf** · Phase 1
- For phone/WhatsApp requests during transition, I create a request for an employee.

**SUP-05 · Emergency pause** · Phase 1 (meaningful from Phase 2)
- One button pauses all automatic assignment; assigned trips continue. The pause is visible to all supervisors.

**SUP-06 · Suggestions (Semi-auto)** · Phase 2
- For each pending request in a Semi-auto scope, I see up to 3 ranked vehicles, each with reasons (minutes away, seats free, route fit, added minutes to others).
- One tap approves the top suggestion; I can choose another.
- If I do not respond within `failsafe_timeout_seconds` (default 180), the failsafe action runs.

**SUP-07 · Overrides** · Phase 2
- On any request/trip I can: reassign, lock to vehicle, force priority, block pooling, hold, cancel, and take a vehicle out of service.
- Before confirming, I see the impact. I must choose a reason. Affected users are notified.

**SUP-08 · Modes per scope** · Phase 2
- I can set Manual / Semi-auto / Full-auto for: operator default, a client, a zone, a time window, or combinations.

**SUP-09 · Mode-switch prompts** · Phase 3
- When the system detects unusual conditions, it prompts me to switch a scope to Manual; I decide.

## Operator admin (OPA)

**OPA-01 · Manage fleet** · Phase 1 — add/edit vehicles (number, model, type, seat capacity), drivers, link driver to vehicle.
**OPA-02 · Manage clients and offices** · Phase 1 — client name, offices with location pin, contact.
**OPA-03 · Manage supervisors** · Phase 1.
**OPA-04 · Zones** · Phase 2 — draw zone polygons on the map.
**OPA-05 · Reports** · Phase 1 basic, Phase 3 full — trips per day, median/p90 wait, no-shows, per client and per driver; CSV export.
**OPA-06 · Billing export** · Phase 3 — per client, per period: trips, km, invoice-ready CSV.

## Client admin (CLA)

**CLA-01 · Manage employees** · Phase 1 — add/edit/deactivate employees; bulk import via CSV (name, phone, home pin lat/lng, office, priority, VIP).
**CLA-02 · Policies** · Phase 2 — pooling allowed yes/no, employee opt-out allowed, night-safety rule on/off and hours, max detour override (stricter only).
**CLA-03 · Reports** · Phase 1 basic — own employees' trips and waits.
