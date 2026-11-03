# Runbook: the load test

Goal: know, with numbers, whether the stack carries a pilot-sized peak before a real operator does:
**35 cabs publishing GPS, 300 riders asking over a 2-hour peak, 2 supervisors working the queue.**

It drives the *running* stack the way the apps do (HTTP, WebSocket, MQTT) and reports API latency,
ingestor lag, WebSocket fan-out delay and every error. Development only: it uses the test login.

## Run it

```text
make phone-dev          # the stack (api, ingestor, worker, beat); local OSRM when the maps are prepared
make loadtest-seed      # once: "Load Test Cabs" - 35 cabs, 300 riders, 2 supervisors (idempotent, dev only)
make loadtest           # the real peak: 120 minutes of arrivals, then up to 30 minutes to finish trips
make loadtest ARGS="--minutes 20 --speed-kph 60"      # the same 300 riders in 20 minutes (denser than real)
make loadtest ARGS="--cabs 5 --riders 12 --minutes 3 --speed-kph 150"        # a 6-minute shake-down
```

Needs the `websockets` package (it comes with `uvicorn[standard]`, so `make install` has it).
Leave the laptop awake: the run is real time, and the full peak takes a little over two hours.
Options: `--supervisors 1|2`, `--grace-minutes N`, `--seed N`, `--json PATH` (default
`.loadtest/last-run.json`).

Before it starts it tidies up after any earlier interrupted run (cancels the load-test riders' open
requests, takes the cabs off duty); none of that is measured.

## What it plays

| Who | What they do |
|---|---|
| 35 drivers | go on duty (spread over about 30 s), publish a ping per 5 m moved (at most one a second) or every 60 s when still, poll `GET /driver/trips?scope=upcoming` every 8 s, start the trip, drive straight to each stop at `--speed-kph`, arrive, wait 5 s, mark done, complete |
| 300 riders | request a ride to the office at a time drawn from a peak-shaped curve (busiest in the middle of the window); hold a WebSocket on their own channel and then on their trip's; poll their request every 15 s until it is dropped |
| 2 supervisors | read the queue and the map every 5 s, hold the live WebSocket, and assign the nearest free cab to each waiting request after a 3-15 s pause; they split the queue by request id |

Pooling is off for this client: the load measured is the API and the GPS pipeline, not the optimizer.

## What it reports, and the targets

Targets are from `docs/01-requirements/non-functional.md`.

| Measure | How | Target |
|---|---|---|
| API latency p50 / p95 / p99 per endpoint | timed at the client; the server's own histogram is read from `/metrics` before and after | **p95 <= 300 ms** |
| Ingestor lag | `received_at - recorded_at` of this run's rows in `location_ping` | **<= 10 s** (p95) |
| Fan-out delay | time the supervisor's (and the rider's) WebSocket receives a `vehicle.location` minus the ping's own timestamp | **<= 10 s** (p95) |
| Assignment notification | the rider's `request.assigned` minus the moment the supervisor sent the assign | **<= 10 s** (p95) |
| GPS pings lost | pings published versus rows persisted | none |
| Events ahead of their data | a rider refetches on `request.assigned` and still reads `queued` | none |
| Errors | any unexpected HTTP status, transport failure, dropped WebSocket, 5xx | none |
| Riders finished | every request ends `dropped` | all |

Exit status 0 only when every target holds. The numbers are also written to `.loadtest/last-run.json`.

## What it found (2026-11-03)

The first runs found and fixed seven defects - see the load-test entries in
`docs/07-decisions/decision-log.md`: the Celery sweeps failing after their first run, a cab left
`on_trip` by a rider's last cancel, events sent before their commit, the ingestor's two writers
overlapping, `vehicle.location` never reaching a rider, and assignment waiting on the public OSRM server.
`PROGRESS.md` has the numbers of the final runs.

## Reading a failure

| Symptom | Likely cause |
|---|---|
| `FAIL login ... run make loadtest-seed first` | the load-test operator is missing (a simulator run, which resets the database, removes it) |
| `driver_no_duty` / 409 "Already on duty" | an earlier run was killed with cabs on trips; start again (the tidy-up handles it) or look at `.phone-dev/api.log` |
| `POST /dispatch/assign` p50 near 1000 ms | routing is going to the public OSRM; `make phone-dev` only uses the local one when `infra/maps/tiles/ncr.mbtiles` exists |
| Pings lost, `ingestor_handler_failed` in `.phone-dev/ingestor.log` | the ingestor's session; the log carries the traceback |
| `too many clients` from Postgres | connections leaked by a process; `.phone-dev/worker.log` and `api.log` name it |
| Fewer WebSocket events than pings | check the harness first: `ws.recv()` under `asyncio.wait_for` discards frames in websockets 17 on Python 3.14, so the script reads with `async for` |
