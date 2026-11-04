# ADR-0025: `/metrics` is unauthenticated and kept off the public edge

- Status: accepted
- Date: 2026-10-15

## Context

`non-functional.md` (Operability) requires Prometheus metrics: request latency, error
rate, GPS ping rate, stale vehicles, pending requests, routing cache hit rate, and the
share of ETAs served approximate. R01 adds them. They are exposed on `GET /metrics` in
the API process and on a small HTTP server in the GPS ingestor and the Celery worker,
which have no HTTP server of their own.

Every other route in this system declares a permission, and a test harness walks all of
them and fails if one does not (B04). `/metrics` cannot: Prometheus has no user, no role
and no token, and nothing in the scrape protocol carries one.

The data is not nothing. It is request rates per route template, operator ids as labels,
fleet size, how many riders are waiting and how long the longest has waited. It is not
personal data — no phone numbers, no names, no positions — but it is a complete picture
of an operator's day, and the route templates are a map of the API.

## Decision

**`/metrics` is unauthenticated, and is unreachable from outside the deployment.**

Three things hold that together, and all three are enforced rather than remembered:

1. `infra/caddy/Caddyfile` is an **allow-list**. The edge proxies `/api/*`, `/ws` and
   `/health/*`; everything else gets a 404 before it reaches the application.
2. Prometheus reaches the three processes over the private compose network
   (`api:8000`, `ingestor:9101`, `worker:9102`). None of those ports is published.
3. `backend/tests/unit/test_edge_exposes_only_the_api.py` parses that Caddyfile on every
   PR and fails if it ever starts serving `/metrics`, `/docs`, `/openapi.json` or
   anything outside the allow-list — and also fails if the Prometheus config stops
   scraping any of the three targets, because a safe-but-blank dashboard is its own
   failure.

`tests/integration/test_permissions.py` exempts `/metrics` from the permission harness,
in the same list as `/health/live` and `/health/ready`, with a comment pointing here.

`/health/live` and `/health/ready` **are** served publicly. They carry a dependency name
and a status and nothing else, and keeping them reachable is what lets an external uptime
monitor tell "the box is gone" from "the box is up and the database is not".

## Alternatives considered

**Bearer token on the scrape.** Prometheus supports it. It means a long-lived credential
written in plaintext in a scrape config, with no rotation story and no audit trail, to
protect an endpoint that is already behind the network boundary. It converts a
deployment property we can test into a secret we must manage.

**mTLS between Prometheus and the API.** Correct, and disproportionate: a certificate
authority to operate, for one pilot VM where both processes are in the same compose
network and neither port leaves the host.

**Put `/metrics` behind the normal permission system with a service role.** Then the
metrics endpoint depends on the database being reachable to authorise a scrape — so the
moment Postgres goes down, monitoring goes blind, which is exactly when the request-rate
and error-rate panels matter most. (The business *gauges* already degrade gracefully for
the same reason: a failing query is logged and the counters are still served.)

**Expose it through Caddy with basic auth.** Still a shared secret, and it would make a
public listener out of something that has no reason to have one.

## Consequences

- Metrics are available to the monitoring stack with no credential to rotate or leak.
- The safety argument is a **deployment** property, not a code property, so it is only as
  good as the thing that checks it — hence the Caddyfile guard test, which is a unit test
  so it runs on every PR rather than only when somebody deploys.
- Anyone who reaches the private network reaches the metrics. That is accepted: anyone on
  that network also reaches Postgres and Redis directly.
- A second deployment topology (Kubernetes, a managed load balancer, a second VM) must
  reproduce the allow-list. The guard test checks *this* Caddyfile, and will not notice a
  different edge. Adding one means adding its guard.
- Running the API with several uvicorn workers behind one port would make scrapes
  inconsistent — each worker has its own counters and a scrape hits one at random. The
  image therefore runs a single process and scale is by container, each scraped
  separately. This is written on `app/core/metrics.py` and in the Dockerfile.
