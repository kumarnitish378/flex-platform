"""Async SQLAlchemy engine, session factory and the FastAPI session dependency.

Repositories receive an `AsyncSession`; they never create engines themselves
(`coding-standards.md` §2 rule 8: API and repositories are async).
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.settings import Settings


class Base(DeclarativeBase):
    """Declarative base for every SQLAlchemy model in the project."""


def create_engine(settings: Settings) -> AsyncEngine:
    return create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,  # survives Postgres restarts and idle-connection drops
        future=True,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        expire_on_commit=False,  # objects stay usable after commit, inside the request
        autoflush=False,
    )


async def session_dependency(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Yield a session and always close it.

    Commit is the service's decision, so a request that raises leaves nothing
    half-written: the context manager rolls back on the way out.
    """
    async with session_factory() as session:
        yield session
