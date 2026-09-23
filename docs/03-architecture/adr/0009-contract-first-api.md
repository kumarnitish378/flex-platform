# ADR-0009: Contract-first API with generated Dart client

- Status: accepted
- Date: 2026-09-24

## Decision
`docs/03-architecture/api-spec.yaml` is the source of truth. The Dart client is generated from it. Backend tests verify responses conform to the spec.

## Consequences
- Every API change starts with a spec change in the same pull request.
- CI fails if the backend's generated OpenAPI diverges from the spec (schema comparison test).
