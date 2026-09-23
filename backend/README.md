# backend

FastAPI modular monolith, Celery workers, MQTT ingestor and Alembic migrations.

Layout and rules: `docs/05-engineering/coding-standards.md` §2.
Architecture and module list: `docs/03-architecture/architecture.md`.

```
backend/
  pyproject.toml
  alembic/          migrations
  app/
    main.py         FastAPI app factory
    core/           settings, db session, clock, logging, errors, security
    domain/         PURE logic, no I/O (state machines, rules, cost, geo)
    modules/<name>/ router.py, schemas.py, service.py, repository.py, models.py
    workers/        Celery tasks (thin)
    ingestor/       MQTT consumer process
    realtime/       WebSocket hub
  tests/unit, tests/integration, tests/contract
```

Run: `make backend-dev` · Test: `make test` · Lint: `make lint`
(or `.\scripts\dev.ps1 backend-dev` on Windows).
