# ADR-0005: MQTT for GPS ingestion

- Status: accepted
- Date: 2026-09-24

## Context
Frequent small location messages from phones on unstable mobile networks, and possibly ESP32 hardware trackers.

## Decision
Mosquitto broker; vehicles publish to per-vehicle topics; a dedicated ingestor process consumes, validates, stores. HTTPS batch endpoint as fallback.

## Alternatives considered
- HTTPS POST per ping: higher overhead, worse on flaky networks.
- WebSocket upstream from the app: couples GPS to API processes; not usable by simple hardware.

## Consequences
- Per-vehicle credentials and ACLs are required.
- The ingestor is a separate process and must be monitored.
