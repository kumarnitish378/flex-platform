"""Database fixtures for integration tests.

Uses the compose test profile rather than testcontainers (both are sanctioned by
`testing-strategy.md` §1) — the containers are already running for development, so tests
start in milliseconds instead of pulling a PostGIS image per run.

Two properties matter:

* **The schema comes from the Alembic migration**, not `create_all`. That makes
  "the migration creates the tables" (B02's acceptance criterion) something the suite
  actually proves, and stops models and migrations drifting apart.
* **Every test runs in a transaction that is rolled back**, so tests cannot see each
  other's rows and order never matters.

If no database is reachable the whole module skips with an actionable message, so the
unit suite still runs on a machine without Docker.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import pytest
import pytest_asyncio
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from alembic import command

BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _replace_db(url: str, database: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, f"/{database}", parts.query, parts.fragment))


DEV_URL = os.environ.get(
    "DATABASE_URL", "postgresql+asyncpg://smartcab:smartcab@localhost:5432/smartcab"
)
# A separate database, so running the suite can never touch development data.
TEST_URL = os.environ.get("TEST_DATABASE_URL") or _replace_db(DEV_URL, "smartcab_test")

SKIP_REASON = (
    "no PostgreSQL reachable at "
    f"{urlsplit(TEST_URL).netloc} - run `make up` (needs Docker), "
    "or set TEST_DATABASE_URL"
)


async def _create_database_if_missing() -> None:
    """Connect to the maintenance database and create the test database."""
    import asyncpg

    parts = urlsplit(TEST_URL)
    database = parts.path.lstrip("/")
    dsn = urlunsplit(("postgresql", parts.netloc, "/postgres", "", ""))

    connection = await asyncpg.connect(dsn)
    try:
        exists = await connection.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", database)
        if not exists:
            # CREATE DATABASE cannot run inside a transaction block.
            await connection.execute(f'CREATE DATABASE "{database}"')
    finally:
        await connection.close()


async def _postgis_available() -> bool:
    import asyncpg

    parts = urlsplit(TEST_URL)
    dsn = urlunsplit(("postgresql", parts.netloc, parts.path, "", ""))
    connection = await asyncpg.connect(dsn)
    try:
        await connection.execute("CREATE EXTENSION IF NOT EXISTS postgis")
        await connection.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
        return True
    finally:
        await connection.close()


def _migrate() -> None:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", TEST_URL)
    command.upgrade(config, "head")


@pytest.fixture(scope="session")
def database_ready() -> bool:
    """Create the test database and bring it to head. Skips if Postgres is unreachable.

    Synchronous on purpose: Alembic runs its own event loop, and a session-scoped async
    fixture would need a session-scoped loop that fights with the per-test loops.
    """
    try:
        asyncio.run(_create_database_if_missing())
        asyncio.run(_postgis_available())
    except Exception as exc:  # noqa: BLE001 - any connection problem means "skip"
        pytest.skip(f"{SKIP_REASON} ({type(exc).__name__})")
    _migrate()
    return True


@pytest_asyncio.fixture
async def db_session(database_ready: bool) -> AsyncIterator[AsyncSession]:
    """A session inside a transaction that is always rolled back."""
    engine = create_async_engine(TEST_URL, poolclass=NullPool)
    connection = await engine.connect()
    transaction = await connection.begin()
    factory = async_sessionmaker(bind=connection, expire_on_commit=False, autoflush=False)
    session = factory()
    try:
        yield session
    finally:
        await session.close()
        # A test that asserted an IntegrityError has already rolled the transaction
        # back; rolling back again warns about a deassociated transaction.
        if transaction.is_active:
            await transaction.rollback()
        await connection.close()
        await engine.dispose()


@pytest.fixture
def operator_a() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def operator_b() -> uuid.UUID:
    return uuid.uuid4()
