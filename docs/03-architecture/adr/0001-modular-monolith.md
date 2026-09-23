# ADR-0001: Modular monolith backend

- Status: accepted
- Date: 2026-09-24

## Context
Small team, phased delivery, one pilot operator. Microservices add deployment, networking and consistency overhead.

## Decision
One FastAPI application with internal modules (see `architecture.md`), plus separate processes only for the GPS ingestor and Celery workers, which share the same codebase.

## Alternatives considered
- Microservices from day one: too much overhead for the team size.
- Serverless functions: poor fit for WebSockets, MQTT and long optimizer runs.

## Consequences
- Modules must communicate via service interfaces to allow later extraction.
- One database; module-owned tables are not accessed by other modules' repositories.
