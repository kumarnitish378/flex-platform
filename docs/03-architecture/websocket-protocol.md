# WebSocket protocol (`/ws`)

The contract for the realtime surface. `api-spec.yaml` is the contract for everything
request/response; OpenAPI cannot describe a WebSocket, so this file is the authority for
`/ws` and is referenced from the spec's `x-websocket` block. **Change this file first**,
then the code, exactly as with `api-spec.yaml` (CLAUDE.md hard rule 1).

Introduced by task B13. Events are produced by API workers and Celery, published on Redis
pub/sub, and fanned out here, so any number of API processes can serve connections
(`architecture.md` section 4).

## 1. Connecting

    wss://<host>/api/v1/ws

Authentication uses the same access token as the REST API, presented **one of two ways**:

1. `Authorization: Bearer <token>` on the upgrade request. Preferred; native clients can
   set it.
2. An `auth` frame as the **first** message, for browsers, which cannot set headers on a
   WebSocket upgrade.

The token is never accepted in the query string. A URL lands in proxy logs, browser
history and `Referer` headers, and an access token there is an access token leaked.

```json
{"type": "auth", "token": "<access token>", "active_role": "supervisor"}
```

A connection that has not authenticated within **10 seconds** is closed with `4401`. The
active role follows the same rule as `X-Active-Role` on REST calls: it must be one of the
roles the token carries.

### Close codes

| Code | Meaning |
|---|---|
| `1000` | Normal close |
| `4401` | Not authenticated, token invalid or expired, or the auth deadline passed |
| `4403` | Subscription refused for a channel the caller may not read |
| `4408` | Client sent an unparseable frame |

An expired token does not silently keep a connection alive: the server closes with `4401`
when the token's expiry passes, and the client reconnects with a refreshed token.

## 2. Frames

Every frame is a JSON object with a `type`. Unknown types are ignored rather than fatal,
so a newer client can talk to an older server.

### Client to server

```json
{"type": "subscribe",   "channels": ["operator.<id>.vehicles", "trip.<id>"]}
{"type": "unsubscribe", "channels": ["trip.<id>"]}
{"type": "ping"}
```

### Server to client

```json
{"type": "subscribed",   "channels": ["operator.<id>.vehicles"], "refused": []}
{"type": "event", "event": "vehicle.location", "channel": "operator.<id>.vehicles", "data": {}}
{"type": "pong"}
{"type": "error", "code": "forbidden_channel", "message": "...", "channel": "trip.<id>"}
```

A `subscribe` naming several channels is answered once, listing which were accepted and
which were refused. One refused channel does not close the connection or lose the others:
a client asking for six channels on login should not lose the five it may read because a
trip ended a second ago.

## 3. Channels

| Channel | Who may subscribe |
|---|---|
| `operator.{id}.vehicles` | Supervisor, operator admin, platform admin of that operator |
| `operator.{id}.requests` | Supervisor, operator admin, platform admin of that operator |
| `operator.{id}.alerts` | Supervisor, operator admin, platform admin of that operator |
| `trip.{id}` | An employee riding on that trip, the assigned driver, and supervisors of the operator |
| `user.{id}` | That user only |

Rules the server enforces, in addition to the table:

- **Operator scope.** `{id}` must equal the caller's `operator_id`. Another operator's
  channel is refused exactly like a non-existent one.
- **Not client-scoped.** A `client_admin` holds `request_queue_view` for their own client,
  which is *not* permission to read an operator-wide feed: the operator channels are
  refused for any caller carrying a `client_id`.
- **Trip membership is time-bounded.** An employee may read `trip.{id}` from assignment
  until their own ride ends (`roles-and-permissions.md`, "Live vehicle location:
  employee only for their active trip, from assignment until pickup/drop"). Once their
  request is `dropped`, `cancelled` or `no_show`, the subscription is refused and any
  existing one is dropped at the next event.
- **Authorization is re-checked, not cached.** Subscribing grants nothing permanent; each
  event checks the subscription still stands.

## 4. Events

| Event | Channel | Emitted when |
|---|---|---|
| `vehicle.location` | `operator.{id}.vehicles`, `trip.{id}` | A GPS ping moves a vehicle's latest position (B12) |
| `request.created` | `operator.{id}.requests` | An employee or supervisor creates a request |
| `request.assigned` | `trip.{id}`, `user.{id}` | A request is put on a trip (B14) |
| `request.cancelled` | `operator.{id}.requests`, `trip.{id}` | A request is cancelled |
| `trip.assigned` | `user.{id}` (driver), `operator.{id}.requests` | A trip is created or gains a rider (B14) |
| `trip.started` / `trip.completed` | `trip.{id}`, `operator.{id}.requests` | The driver starts or finishes (B15) |
| `stop.eta` | `trip.{id}` | The ETA worker recomputes a stop's arrival |
| `stop.arrived` / `stop.done` | `trip.{id}` | The driver marks a stop (B15) |
| `alert.raised` / `alert.resolved` | `operator.{id}.alerts` | An alert changes state (B17) |
| `automation.changed` | `operator.{id}.requests` | A supervisor pauses or resumes automation (SUP-05) |

Event payloads carry ids and the few fields a screen needs to update in place. They are
**not** a substitute for the REST resource: a client that misses events while backgrounded
re-fetches rather than replaying.

## 5. Delivery

- **At most once.** Redis pub/sub does not persist, so an event published while a client
  is disconnected is gone. This is deliberate: the REST endpoints are the source of truth
  and a reconnecting client re-fetches. Nothing that matters may exist *only* as an event.
- **Latency budget.** Assignment and location events must reach the client within 10
  seconds (`non-functional.md`).
- **Ordering** is per channel and best-effort. Clients must tolerate an out-of-order
  `stop.eta` (compare timestamps) rather than assume monotonicity.
