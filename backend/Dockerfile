# The backend image. One image, four processes (R01).
#
# The API, the GPS ingestor, the Celery worker and the Celery beat are the same code with
# different entrypoints, so they are the same image with different commands - see
# `infra/docker-compose.staging.yml`. Building four images from one source tree would let
# them drift, and a worker running yesterday's domain logic against today's database is a
# bug nobody finds until a sweep does the wrong thing.

FROM python:3.12-slim-bookworm AS base

# No .pyc files to invalidate, unbuffered logs so `docker logs` is live, and no pip
# version chatter in build output.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv

# --- dependencies -----------------------------------------------------------
# Copied before the source so a code change does not reinstall the world. Only the
# project metadata is needed to resolve dependencies.
FROM base AS deps
COPY pyproject.toml ./
# A placeholder package so `pip install .` can resolve the project itself; the real
# source arrives in the next stage.
RUN mkdir -p app && touch app/__init__.py && pip install --no-cache-dir .

# --- runtime ----------------------------------------------------------------
FROM base AS runtime

# curl for the container healthcheck. Nothing else: every dependency this service has is
# a Python package or another container.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

# Never root. A GPS ingestor parsing payloads from the public internet is exactly the
# process that should not be able to write to its own code.
RUN useradd --system --uid 10001 --no-create-home smartcab \
    && chown -R smartcab:smartcab /srv
USER smartcab

EXPOSE 8000

# One uvicorn process, deliberately: `/metrics` reports the process it is scraped from,
# so several workers behind one port would each answer with a fraction of the truth
# (see `app/core/metrics.py`). Scale by running more containers, which Prometheus
# scrapes individually.
CMD ["python", "-m", "uvicorn", "app.main:create_app", "--factory", \
     "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log"]
