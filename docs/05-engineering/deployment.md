# Staging and production deployment (task R01)

One Linux VM, Docker Compose, Caddy for TLS. `non-functional.md` (Portability): 4 vCPU and
8 GB RAM while the public OSM servers are used; 8 vCPU and 16 GB once the NCR extract is
self-hosted (task I02b).

Everything below runs from the repository root on the VM.

## 1. What runs

| Container | Image | What it is | Reachable from |
|---|---|---|---|
| `caddy` | `caddy:2-alpine` | TLS, the only thing on ports 80/443 | the internet |
| `api` | built from `backend/` | FastAPI, one uvicorn process | Caddy, Prometheus |
| `ingestor` | same image | MQTT GPS consumer (B12) | nothing; it dials out |
| `worker` | same image | Celery, the three sweeps (B20) | nothing |
| `beat` | same image | Celery scheduler, exactly one | nothing |
| `broker-seed` | same image | writes Mosquitto's credential files once, before it starts | — |
| `broker-sync` | same image | rewrites them on duty changes and SIGHUPs the broker | nothing |
| `migrate` | same image | `alembic upgrade head`, runs once and exits | — |
| `postgres` | `postgis/postgis:16-3.4` | the database | the compose network only |
| `redis` | `redis:7-alpine` | cache, pub/sub, Celery broker | the compose network only |
| `mosquitto` | `eclipse-mosquitto:2` | MQTT broker, **TLS on 8883** | driver phones |
| `prometheus` | `prom/prometheus` | metrics, 30-day retention | Grafana only |
| `grafana` | `grafana/grafana` | dashboards | the internet, on its own hostname |
| `loki` + `promtail` | `grafana/*` | log shipping and search | Grafana only |
| `backup` | `postgis/postgis` | `pg_dump` daily, 14-day retention | — |

Four processes share one image on purpose: the API, the ingestor, the worker and the beat
are the same code with different entrypoints, and building them separately would let them
drift. A worker running yesterday's domain logic against today's database is a bug nobody
finds until a sweep does the wrong thing.

**Only Caddy and Mosquitto publish ports.** Postgres, Redis, Prometheus and the metrics
endpoints are on the private compose network and cannot be reached from outside the box.
The development compose publishes them so a developer can connect; that is why
`docker-compose.staging.yml` is standalone rather than an override of it.

## 2. Before the first deploy

1. **A VM** with Docker Engine and the Compose plugin. Ports 80, 443 and 8883 open
   inbound; nothing else.
2. **Two DNS A records** pointing at it, *resolving before you start anything*:
   - `SITE_ADDRESS` — the API and the WebSocket, e.g. `staging.example.com`
   - `MONITORING_ADDRESS` — Grafana, e.g. `grafana.staging.example.com`

   Caddy proves control of these over HTTP; if they do not resolve yet, the ACME
   challenge fails and you get no certificate and no MQTTS.
3. **Secrets**, generated on the VM:
   ```bash
   cp infra/.env.staging.example infra/.env.staging
   python3 -c "import secrets; print(secrets.token_urlsafe(48))"   # JWT_SECRET
   python3 -c "import secrets; print(secrets.token_urlsafe(24))"   # POSTGRES_PASSWORD
   python3 -c "import secrets; print(secrets.token_urlsafe(24))"   # MQTT_INGESTOR_PASSWORD
   python3 -c "import secrets; print(secrets.token_urlsafe(24))"   # GRAFANA_ADMIN_PASSWORD
   ```
   `infra/.env.staging` is git-ignored and must stay that way. The API refuses to start
   with the default `JWT_SECRET`, or with one shorter than 32 bytes (RFC 7518 §3.2), or
   with `SIMCTL_ENABLED=true` outside `APP_ENV=sim` (ADR-0008).
4. **`OSM_CONTACT_EMAIL`** must be a real, monitored address. While the public OSM
   servers are in use the application refuses to start without it, because the OSM usage
   policy requires an identifying contact and anonymous traffic gets blocked
   (ADR-0010 rule 4).

## 3. First boot

```bash
make staging-up        # builds the image and starts everything
make staging-ps        # watch until api is (healthy)
```

`migrate` runs to completion before `api` starts. Migrations are deliberately **not** in
the API's own entrypoint: the moment there are two API containers, that races itself.

`broker-seed` then writes Mosquitto's `passwd` and `acl` from the vehicle registry, and
`mqtt-certs` waits for Caddy to finish its ACME challenge and publishes the certificate
to the broker. Both happen inside `make staging-up`; there is no manual first step.

Three details worth knowing, because each one was a failure before it was a feature:

- **`mqtt-certs` waits rather than racing.** On a clean box there is no certificate when
  the stack first comes up, and a one-shot copy exits 1 — which, because Mosquitto waits
  on it, took the whole first `make staging-up` down.
- **Mosquitto cannot read Caddy's volume directly.** Caddy writes the key `0600` as root
  and Mosquitto runs as uid 1883, so a read-only mount fails at startup with a bare
  "Unable to load server key file" and no hint why. `mqtt-certs` copies the pair into a
  volume of its own with the right ownership.
- **The credential directory is setgid.** The files are written by the backend (uid
  10001, never root) and read by the broker (uid 1883), so `broker-files-init` sets the
  directory to `10001:1883` mode `2770`; everything created inside inherits group 1883
  and `0640` is readable by the broker without anything being world-readable.

**Re-run the certificate step after each renewal** (Caddy renews about 30 days out); a
monthly cron is enough:

```cron
0 4 1 * * cd /srv/flex-platform && make staging-mqtt-cert >> /var/log/smartcab-cert.log 2>&1
```

### Check it

```bash
curl -fsS https://$SITE_ADDRESS/health/ready | jq
```

Expect `database`, `redis`, `mqtt` and `routing`. `routing` reports **ok, not probed**
while `OSRM_URL` is public — see §6. Only `database` is required; the other three degrade
the service without taking it out of rotation.

```bash
curl -s https://$SITE_ADDRESS/metrics      # must 404: it is not served at the edge
```

**The broker's certificate SAN is `SITE_ADDRESS`.** Driver phones must therefore connect
to the broker at that same hostname — a separate `mqtt.` name would fail certificate
validation on every device. `/driver/duty` hands the app the right values from
`MQTT_PUBLIC_HOST` / `MQTT_PUBLIC_PORT` / `MQTT_PUBLIC_TLS`, which the compose derives
from `SITE_ADDRESS`; they are deliberately **not** the `MQTT_HOST` the API itself uses,
which is a private service name no phone can resolve.

## 4. Backups

The `backup` container takes a `pg_dump` every 24 hours into the `backups` volume and
prunes anything older than 14 days (`non-functional.md`, Availability). Each dump is
written to a `.part` file and renamed only when complete, and is verified with
`pg_restore --list` immediately — a dump interrupted halfway is a file that looks like a
backup and is not, and the day you find out is the day you need it.

```bash
make backup           # take one now
make backup-list      # what exists
make backup-verify    # dump, restore into a scratch database, compare row counts
```

`make backup-verify` is the **monthly restore test** the requirements ask for. It never
touches the live database: `backup.sh restore` defaults to a scratch database and refuses
the live one without `CONFIRM_LIVE_RESTORE=yes`.

Verified on the development stack while R01 was built: 35 tables, 76,473 location pings
and the PostGIS extension all came back identical, including the partitioned
`location_ping`.

### Restoring for real

```bash
docker compose -f infra/docker-compose.staging.yml stop api ingestor worker beat
docker compose -f infra/docker-compose.staging.yml exec postgres \
  env CONFIRM_LIVE_RESTORE=yes bash /opt/backup/backup.sh restore /backups/<file>.dump smartcab
docker compose -f infra/docker-compose.staging.yml start api ingestor worker beat
```

Stop the four application containers first. They will happily write into a half-restored
schema otherwise.

**Copy the dumps off the box.** A backup on the same disk as the database survives a bad
migration and nothing else.

## 5. Monitoring

Grafana at `https://$MONITORING_ADDRESS`, user `admin`, password from
`GRAFANA_ADMIN_PASSWORD`. The Prometheus and Loki data sources and the
**Smart Cab — operations** dashboard are provisioned from the repository, so a rebuilt box
has them without anyone clicking through the UI. The dashboards are read-only in Grafana
for the same reason: one that exists only in Grafana's database is lost with the box.

Prometheus scrapes **three** targets, not one — the API, the ingestor and the worker are
separate processes with separate counters, so scraping only the API would report zero GPS
pings on a platform ingesting forty a second.

Alert rules are in `infra/prometheus/alerts.yml` and fire into Prometheus's own alert
list, which Grafana shows. There is no Alertmanager until somebody is actually on call.
The rules are deliberately few; each is something a human must act on tonight.

Logs: `{service="api"}` in Grafana's Explore. The backend logs structured JSON with
`request_id`, `operator_id` and `user_id`, and the Loki data source turns `request_id`
into a link, so a slow request on a latency panel leads to the line that caused it.

## 6. When something breaks

| Symptom | What it means | What to do |
|---|---|---|
| `/health/ready` 503, `database` unavailable | Postgres is down or unreachable | `make staging-ps`; check disk. Nothing works without it. |
| `ready` 200 but `status: degraded`, `redis` down | Live map positions, the WebSocket fan-out and Celery are affected | Requests and trips still work. Restart `redis`; data loss is the cache only. |
| `degraded`, `mqtt` down | GPS over MQTT has stopped | Driver apps fall back to `POST /driver/location` over HTTPS (B12). Check the broker and, after a renewal, that `make staging-mqtt-cert` was run. |
| Mosquitto restarting, "Unable to open pwfile" | `broker-seed` has not run, or failed | It needs the database. `docker compose ... logs broker-seed`; it refuses outright if `MQTT_INGESTOR_USER`/`_PASSWORD` are unset, because a broker the ingestor cannot authenticate to records no GPS at all. |
| A driver's app cannot connect to the broker | Wrong address, or a credential the broker has not reloaded | Check `broker-sync` logs for `broker_reloaded`; a credential is issued at duty start and reaches the broker within 15 s. Check too that the app was given `MQTT_PUBLIC_HOST`, not the private one. |
| `routing` says "not probed" | Normal while `OSRM_URL` is public | Not a fault. A public OSRM is never probed: the shared 1 req/s budget (ADR-0010 rule 3) must not be spent on health checks. Watch `smartcab_routing_requests_total{source="approx"}` instead. |
| Most ETAs approximate | OSRM is down, slow, or the budget is exhausted | The product still works — that is the ladder. A sustained share over half is the trigger for **I02b** (OQ-21). |
| GPS pings being dropped | Read the `outcome` label; it names the drop rule | This is the shape of OQ-33, where half of every run's GPS was discarded as `too_far_future` and nothing said so. |
| A sweep failing | Nothing expires, nobody is warned, no stale cab is flagged | A failing sweep is silent by design (B20) — the task logs and returns so one bad pass cannot stop the beat. `smartcab_sweep_runs_total{outcome="failed"}` is where it shows. |
| Certificate expired | The ACME renewal or the broker copy failed | `docker compose ... logs caddy`; then `make staging-mqtt-cert`. |

## 7. Deploying a change

```bash
git pull
make staging-up        # rebuilds, reruns migrations, restarts what changed
make staging-ps
```

There is no blue/green and no zero-downtime story in the pilot: a restart is a few
seconds, the app reconnects its WebSocket on its own (A07), and drivers queue their
actions offline and replay them in order (B15 idempotency by `client_event_id`). Buy
zero-downtime when the pilot says it is worth the complexity, not before.

## 8. Verified end to end

The whole stack was brought up and exercised on 2026-10-15 using Caddy's **internal CA**
with `SITE_ADDRESS=localhost`, which runs the entire TLS path without a public DNS name:

- HTTPS served by Caddy, HTTP redirecting to it with a 308, `/health/ready` reporting all
  four dependencies green through the proxy.
- The allow-list holding: `/metrics`, `/docs`, `/openapi.json`, `/redoc` and `/` all 404
  at the edge while `/api/v1/*` reached the application.
- Prometheus scraping **all three** processes (`api`, `ingestor`, `worker`), with the
  API's request counter and the worker's sweep counter both flowing.
- Grafana with both data sources and the operations dashboard provisioned at the exact
  uids its panels reference, and a panel query returning through its Prometheus proxy.
- Loki holding logs from every container with `service`, `level` and `event` lifted out
  of the structured JSON, and `request_id` present in the line for the derived-field link.
- The backup container taking and verifying a dump on startup.
- MQTTS on the published port serving Caddy's certificate, chain validating against its
  root, and an authenticated subscribe as the ingestor succeeding.
- `broker-sync` detecting a removed credential file, rewriting it and reloading the
  broker — `Reloading config` in Mosquitto's log, broker still healthy.

The only thing that cannot be proved without a public DNS name is the ACME challenge
itself; everything it feeds was exercised with the internal CA standing in.

## 9. What this deployment does not yet do

Stated plainly rather than discovered later:

- **No Alertmanager.** Rules evaluate and show in Grafana; nothing pages anyone.
- **No off-site backup copy.** The dumps are on the VM's disk. Copying them off is a
  decision about where, which needs an owner.
- **No horizontal scale.** One API container, one beat. More API containers work (each is
  scraped separately), but `beat` must stay at exactly one or every sweep runs twice — and
  for the expiry sweep that means two "your cab is nearly due" pushes to the same rider.
- **`OTP_PROVIDER=console`** prints OTPs to the log. Fine for an internal box with known
  testers; it must become a real SMS provider before anyone outside the team logs in
  (OQ-16).
- **`PUSH_PROVIDER=log`.** `ntfy` is implemented and works; `fcm` raises rather than
  dropping pushes silently (OQ-20).
- **Public OSM servers**, with no SLA and no permission for commercial use. **I02b must
  land before the paid pilot** (ADR-0010 §A3, OQ-21).
