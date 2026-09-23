# Non-functional requirements

Numbers are pilot targets; revisit after Phase 1 measurements.

## Performance
| Item | Target |
|---|---|
| API p95 latency (non-optimizer endpoints) | ≤ 300 ms |
| Assignment notification to employee and driver | ≤ 10 s after supervisor confirms |
| Location update visible to employee/supervisor | ≤ 10 s after GPS ping |
| Suggestion generation (Phase 2) | ≤ 5 s per request |
| Optimizer batch run (Phase 3) | ≤ 20 s for 50 requests / 30 vehicles |
| GPS ping interval while on duty | 5 s moving, 30 s stationary (> 2 min below 1 m/s) |
| Pilot scale | 1 operator, ≤ 200 vehicles, ≤ 5,000 employees, ≤ 3,000 trips/day |

## Availability and reliability
- Pilot target 99.5% monthly for API and tracking.
- Driver app works offline: status events queued locally with timestamps and GPS, delivered in order on reconnect; GPS buffered up to 30 minutes.
- If the optimizer or worker fails, the system falls back to Manual mode for affected scopes and alerts supervisors.
- Daily PostgreSQL backups, 14-day retention; restore tested monthly.

## Security
- Phone + OTP login; access token 15 min, refresh token 30 days (rotated on use, revocable).
- Role-based access on every endpoint; tenant scoping by `operator_id` enforced in the data-access layer.
- MQTT: per-device credentials; drivers can publish only to their own vehicle topics.
- HTTPS everywhere (Caddy automatic TLS). No secrets in the repo.
- Rate limits: OTP requests 3/10 min per phone; API 60 req/min per user (configurable).
- Audit log for all overrides, mode changes, emergency pause, user/role changes.

## Privacy (India DPDP Act, 2023 context)
- Collect only what is needed: name, phone, home location, trip data, driver GPS while on duty.
- Driver GPS is collected **only while on duty**.
- Phone numbers and live location shared only per `roles-and-permissions.md` rules and only during the active trip.
- Retention: raw GPS 90 days, then aggregated into speed profiles and deleted; trips 2 years (configurable per operator contract).
- Employees can see their data (history) and request deletion through their client admin.
- Privacy notice shown at first login and accepted.

## Usability
- Driver app usable on Android 8+ phones with 2 GB RAM; large buttons; minimal typing.
- English at launch; Hindi in Phase 2 (all strings externalised from day one).
- Map screens show OSM attribution.

## Operability
- Structured JSON logs with request ID and operator ID.
- Metrics (Prometheus): request latency, error rate, GPS ping rate per vehicle, stale vehicles, pending requests, optimizer duration.
- Health endpoints: `/health/live`, `/health/ready` (DB, Redis, MQTT, OSRM).
- Config changes via admin screens are versioned and audited.

## Portability
- All services run with Docker Compose on one Linux VM (8 vCPU, 16 GB RAM suggested for NCR map extract + services).
- No vendor lock-in beyond optional Firebase Cloud Messaging for push (replaceable by ntfy).
