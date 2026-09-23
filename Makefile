# Smart Cab — developer commands.
# Windows note: GnuWin32 make runs recipes through cmd.exe, so every recipe below is a
# single portable command. Equivalent PowerShell entry points live in scripts/dev.ps1
# (see README.md). Targets and descriptions are parsed by scripts/make_help.py, which
# reads the `## <description>` comment on the line above each target.

.PHONY: help venv install up down up-maps migrate seed backend-dev ingestor worker beat \
        test lint format api-client sim-quick sim-full maps

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

## Start the OPTIONAL self-hosted map containers (osrm, tileserver, nominatim) - task I02b/I02c
up-maps:
	docker compose -f infra/docker-compose.yml -f infra/docker-compose.maps.yml up -d

## Apply database migrations (alembic upgrade head)
migrate:
	cd backend && python -m alembic upgrade head

## Load the development fixture data
seed:
	cd backend && python -m app.cli seed

## Run the API with auto-reload
backend-dev:
	cd backend && python -m uvicorn app.main:create_app --factory --reload --port 8000

## Run the MQTT GPS ingestor process
ingestor:
	cd backend && python -m app.ingestor

## Run a Celery worker
worker:
	cd backend && python -m celery -A app.workers.celery_app worker --loglevel=info

## Run the Celery beat scheduler
beat:
	cd backend && python -m celery -A app.workers.celery_app beat --loglevel=info

## Run backend tests (unit + integration + contract)
test:
	cd backend && python -m pytest

## Run ruff check and mypy
lint:
	python scripts/lint.py

## Apply ruff formatting
format:
	cd backend && python -m ruff format .

## Regenerate the Dart API client from docs/03-architecture/api-spec.yaml
api-client:
	python scripts/not_ready.py api-client A02

## Simulator smoke scenarios (CI); always uses the approx routing provider
sim-quick:
	cd simulator && python -m sim suite quick

## Full simulator scenario suite
sim-full:
	cd simulator && python -m sim suite full

## OPTIONAL (self-hosting only): prepare OSM map data - see dev-environment.md section 8
maps:
	python scripts/not_ready.py maps I02b
