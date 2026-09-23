# ADR-0002: Python + FastAPI backend

- Status: accepted
- Date: 2026-09-24

## Context
The optimizer (OR-Tools), ML (scikit-learn/LightGBM) and simulator (SimPy) are Python-native.

## Decision
Backend in Python 3.12 with FastAPI, Pydantic v2, SQLAlchemy 2 async.

## Alternatives considered
- Node.js/NestJS or Go: fine for the API, but would need Python anyway for optimizer/ML/sim → two languages, duplicated domain logic.
- Django: heavier than needed; UI is in Flutter.

## Consequences
- Domain logic (cost function, rules, state machines) is shared between backend and simulator analysis.
- FastAPI's OpenAPI support fits the contract-first workflow.
- If GPS ingestion exceeds ~1,000 msg/s, the ingestor alone may move to Go.
