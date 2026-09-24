# simulator

Closed-loop SimPy simulator (SITL-style). It drives the real API, WebSocket and MQTT
interfaces — it never imports backend internals.

Specification: `docs/04-simulation/simulator-spec.md`. Scenarios: `docs/04-simulation/scenarios.md`.

Routing uses the **approx** provider by default and must never bulk-call the public OSM
servers (ADR-0010).

Run: `make sim-quick` / `make sim-full`.
