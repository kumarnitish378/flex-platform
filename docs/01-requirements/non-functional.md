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
| Routing throughput on public OSM servers | 1 request/second per service (shared); above that, ETAs degrade to `approx` |

**ETA accuracy depends on the routing provider** (ADR-0010). Accuracy targets (OQ-15: p90 error ≤ 8 min)
apply to the `osrm` provider. In `approx` mode — straight-line distance × 1.4 with a time-of-day speed
table, used offline, by the simulator and whenever OSRM is rate-limited, slow or down — error is materially
larger, especially where the road network detours (river, rail, expressway entry). Such ETAs are flagged
`approximate` in API responses and shown as approximate in the app, and are excluded from ETA-accuracy
reporting.

## Availability and reliability
- Pilot target 99.5% monthly for API and tracking. This target assumes self-hosted OSRM and tiles: the public
  OSM servers are best-effort with **no SLA** and may be withdrawn for commercial use, so the switch (task
  I02b) must happen before the paid pilot (ADR-0010 §A3, OQ-21).
- Public tile or routing outages degrade the product but do not stop it: routing falls back to `approx`, maps
  fall back to cached tiles.
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
- Map screens show "© OpenStreetMap contributors" bottom-right, always visible and never covered by sheets,
  cards or controls (ADR-0010 §A2).
- Maps are **raster** tiles from `TILES_URL`, cached for at least 7 days per HTTP cache headers. **No offline
  map download and no tile prefetching anywhere, including the driver app** — only on-screen tiles are
  fetched. Tile requests carry `flex-platform/<version> (contact: <OSM_CONTACT_EMAIL>)`, never a library
  default.
- **No address search or autocomplete in Phase 1** — locations are set with map pins + landmark text, so
  screens must work without any geocoding service.

## Operability
- Structured JSON logs with request ID and operator ID.
- Metrics (Prometheus): request latency, error rate, GPS ping rate per vehicle, stale vehicles, pending requests, optimizer duration.
- Health endpoints: `/health/live`, `/health/ready` (DB, Redis, MQTT, OSRM). A failing OSRM check degrades
  readiness to a warning, not an outage — the `approx` provider keeps ETAs available.
- Metrics also cover the routing provider: cache hit rate, calls per provider, rate-limiter fallbacks, share
  of ETAs served as approximate.
- Config changes via admin screens are versioned and audited.

## Portability
- All services run with Docker Compose on one Linux VM (4 vCPU, 8 GB RAM while using the public OSM servers; 8 vCPU, 16 GB RAM once the NCR map extract is self-hosted).
- No vendor lock-in beyond optional Firebase Cloud Messaging for push (replaceable by ntfy).
