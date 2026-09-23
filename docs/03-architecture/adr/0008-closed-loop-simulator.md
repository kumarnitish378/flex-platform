# ADR-0008: Closed-loop simulator (SITL-style) as a release gate

- Status: accepted
- Date: 2026-09-24

## Context
Real-world testing with operators is slow and risky. Dispatch logic must be verified before it affects real employees.

## Decision
A Python/SimPy simulator drives the real backend through the same REST API and MQTT topics, with simulated vehicles, drivers, employees, supervisors, traffic and events. The backend uses an injectable Clock so simulated time can run faster than real time. Every phase must pass the scenario suite before going live.

## Consequences
- Backend code must never read wall-clock time directly.
- A `sim` environment with `/simctl/*` endpoints exists and is disabled elsewhere.
- Simulation proves logic and performance, not human adoption.
