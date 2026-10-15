# Smart Cab — developer commands.
# Windows note: GnuWin32 make runs recipes through cmd.exe, so every recipe below is a
# single portable command. Equivalent PowerShell entry points live in scripts/dev.ps1
# (see README.md). Targets and descriptions are parsed by scripts/make_help.py, which
# reads the `## <description>` comment on the line above each target.

.PHONY: help venv install up down check-infra up-maps migrate seed backend-dev ingestor worker beat \
        test test-domain-coverage lint format api-client sim-quick sim-full         sim-offline stack-up stack-down maps

## List available targets and whether their prerequisites exist
help:
	python scripts/make_help.py

## Create the backend virtual environment (.venv) if missing
venv:
	python scripts/venv_setup.py --create

## Install backend + simulator dependencies into .venv
install:
	python scripts/venv_setup.py --install

## Start core infra containers (postgres, redis, mosquitto)
up:
	docker compose -f infra/docker-compose.yml up -d

## Stop core infra containers
down:
	docker compose -f infra/docker-compose.yml down

## Verify the core infra containers are up and usable (I01 acceptance checks)
check-infra:
	python scripts/check_infra.py

## Start the self-hosted map containers (osrm + tileserver) - needs `make maps` first
up-maps:
	docker compose -f infra/docker-compose.yml -f infra/docker-compose.maps.yml up -d

## Apply database migrations (alembic upgrade head)
migrate:
	python scripts/venv_exec.py --cwd backend -m alembic upgrade head

## Load the development fixture data
seed:
	python scripts/venv_exec.py --cwd backend -m app.cli seed

## Run the API with auto-reload
backend-dev:
	python scripts/venv_exec.py --cwd backend -m uvicorn app.main:create_app --factory --reload --port 8000

## Run the MQTT GPS ingestor process
ingestor:
	python scripts/venv_exec.py --cwd backend -m app.ingestor

## Run a Celery worker
worker:
	python scripts/venv_exec.py --cwd backend -m celery -A app.workers.celery_app worker --loglevel=info

## Run the Celery beat scheduler
beat:
	python scripts/venv_exec.py --cwd backend -m celery -A app.workers.celery_app beat --loglevel=info

## Run backend tests (unit + integration + contract)
test:
	python scripts/venv_exec.py --cwd backend -m pytest

## Enforce 100% branch coverage of the state machines (B08 acceptance)
test-domain-coverage:
	python scripts/venv_exec.py --cwd backend -m pytest tests/unit/test_state_machines.py --cov=app.domain.state_machines --cov-branch --cov-report=term-missing --cov-fail-under=100

## Run ruff check and mypy
lint:
	python scripts/lint.py

## Apply ruff formatting
format:
	python scripts/venv_exec.py --cwd backend -m ruff format .

## Regenerate the Dart API client from docs/03-architecture/api-spec.yaml
api-client:
	python scripts/api_client.py

# SIM_PLATFORM points the suites at a live backend so their assertions are actually
# evaluated. Without it a run finishes and reports "assertions not checked" - useful for
# checking the agents move, worthless as a pass. `make stack-up` starts one.
SIM_PLATFORM ?= http://localhost:8000/api/v1

## Start the stack a scenario needs (broker, migrations, API, GPS ingestor)
stack-up:
	bash scripts/live_stack.sh up

## Stop it again
stack-down:
	bash scripts/live_stack.sh down

## Simulator smoke scenarios (PR CI); always uses the approx routing provider
sim-quick:
	python scripts/venv_exec.py --cwd simulator -m sim suite quick --platform $(SIM_PLATFORM)

## Full simulator scenario suite (nightly)
sim-full:
	python scripts/venv_exec.py --cwd simulator -m sim suite full --platform $(SIM_PLATFORM)

## Both suites without a backend: proves the agents run, does NOT check assertions
sim-offline:
	python scripts/venv_exec.py --cwd simulator -m sim suite quick

## OPTIONAL (self-hosting only): prepare OSM map data - see dev-environment.md section 8
maps:
	bash infra/scripts/prepare_maps.sh

# --- staging / production (task R01) -----------------------------------------
# Runbook: docs/05-engineering/deployment.md. These run on the VM, from the repo root,
# and read infra/.env.staging (copy infra/.env.staging.example).
STAGING := docker compose -f infra/docker-compose.staging.yml --env-file infra/.env.staging

## Build and start the staging stack (api, ingestor, worker, beat, caddy, monitoring)
staging-up:
	$(STAGING) up -d --build

## Stop the staging stack, keeping its volumes
staging-down:
	$(STAGING) down

## What is running, and is it healthy
staging-ps:
	$(STAGING) ps

## Follow the application logs
staging-logs:
	$(STAGING) logs -f api ingestor worker beat

## Re-publish Caddy's certificate to the broker after a renewal, and restart it
staging-mqtt-cert:
	$(STAGING) up mqtt-certs
	$(STAGING) restart mosquitto

## Take a database backup now (the staging stack also takes one daily)
backup:
	docker compose -f infra/docker-compose.yml exec -T -e PGUSER=smartcab -e PGPASSWORD=smartcab postgres bash /opt/backup/backup.sh once

## List the backups taken so far
backup-list:
	docker compose -f infra/docker-compose.yml exec -T -e PGUSER=smartcab -e PGPASSWORD=smartcab postgres bash /opt/backup/backup.sh list

## Prove a backup restores and matches the live database (non-functional.md: monthly)
backup-verify:
	bash infra/scripts/verify_restore.sh
