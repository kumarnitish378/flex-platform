# Vision and scope

Last updated: 24 Sep 2026

## 1. Problem
Cab operators serving corporate employee transport run dispatch manually:

- Employees request cabs by WhatsApp message (text + location pin + landmark) or phone call.
- A single supervisor assigns cabs by calling or messaging drivers.
- The employee receives a template reply: car number, driver name, driver mobile. **No ETA, no live location, no status updates.**
- Employees call drivers to ask "where are you?". Area-wise WhatsApp groups expose everyone's phone numbers.
- Waits of **more than one hour** are the main complaint. There is no trip record, so waits cannot be measured or proven.
- Example observed: request 10:05, cab details 10:06 — assignment is fast; the delay and uncertainty happen after assignment.

## 2. Business model (Option B)
We sell software **to cab operators**, not to corporate clients directly.

- Operators keep their fleets, drivers and client contracts.
- Our platform makes them competitive with large platforms (MoveInSync, Routematic, Safetrax) that target large enterprises.
- One operator brings many corporate clients and their employees onto the platform.
- Pricing model: open question (per cab per month, per trip, or tiered).

## 3. Product vision
In phases:
1. **Visibility** — tracking, ETA, status alerts, trip log, supervisor live map. Replaces WhatsApp groups.
2. **Assisted assignment** — rules engine + ranked suggestions; supervisor approves (Semi-auto).
3. **Pooling + Full auto** — optimizer pools riders, reuses cabs, runs automatically per scope.
4. **Prediction + offers** — demand/ready-time prediction, proactive ride offers with accept/reject.
5. **Multi-operator SaaS** — self-onboarding, subscriptions, analytics.

Human control is central: Manual / Semi-auto / Full-auto modes per scope, and supervisor override available at all times.

## 4. Goals
- Cut median and worst-case pickup wait versus the Phase 0 baseline.
- Eliminate "where is my cab?" calls through live tracking and ETA.
- Reduce supervisor effort per request.
- Reduce empty kilometres and cabs deployed through pooling and reuse.
- Give operators proof of performance (trip logs, reports) to win and keep corporate clients.

## 5. Non-goals
- We do not own or operate cabs or employ drivers.
- No WhatsApp API integration.
- No paid map, routing or traffic APIs (OpenStreetMap stack only).
- No consumer ride-hailing (public riders) in scope.
- No fare payment by employees inside the app (billing is operator ↔ client).
- No iOS or web build in Phase 1 (Flutter keeps both possible later).

## 6. Users
Operator owner/admin, supervisor/dispatcher, driver, employee (rider), corporate client admin. See `roles-and-permissions.md`.

## 7. Constraints
- Solo or very small team; phased delivery; each phase ships to a live pilot operator.
- Every phase must pass the simulator scenario suite before going live.
- Indian context: Delhi NCR first; Indian data protection law (Digital Personal Data Protection Act, 2023) applies to employee and driver data.
- Low-end Android phones and unreliable mobile data for drivers.

## 8. Success metrics
See `docs/06-phases/roadmap.md` (exit criteria) and `docs/01-requirements/non-functional.md`.
