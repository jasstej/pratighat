"""
Pratighat.ai — Database layer
Async SQLAlchemy configured for PostgreSQL (primary) with SQLite fallback.

In production: uses PostgreSQL + Alembic migrations.
In development/test without PostgreSQL: auto-switches to SQLite.
"""

from __future__ import annotations

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

logger = logging.getLogger("pratighat.db")


# ------------------------------------------------------------------
# Determine which database to use
# ------------------------------------------------------------------

def _resolve_database_url() -> str:
    """Resolve the database URL: PostgreSQL if available, SQLite fallback."""
    if settings.use_sqlite():
        logger.info("Using SQLite database (development mode — no PostgreSQL)")
        return settings.database_sqlite_url

    # Try to connect to PostgreSQL; fall back to SQLite if it fails
    import asyncpg

    try:
        asyncio_import = __import__("asyncio")
        loop = asyncio_import.get_event_loop()
        conn = loop.run_until_complete(
            asyncpg.connect(
                host="localhost",
                port=5432,
                user="pratighat",
                password="pratighat",
                database="pratighat",
                timeout=3,
            )
        )
        conn.close()
        logger.info("PostgreSQL is available — using PostgreSQL database")
        return settings.database_url
    except Exception as e:
        logger.warning("PostgreSQL not available (%s) — falling back to SQLite", e)
        return settings.database_sqlite_url


DATABASE_URL = _resolve_database_url()


# ------------------------------------------------------------------
# Engine & session factory
# ------------------------------------------------------------------

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.database_echo,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,
    pool_recycle=3600,
    future=True,
)

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: provide an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ------------------------------------------------------------------
# Base class for all models
# ------------------------------------------------------------------

class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


# ------------------------------------------------------------------
# Create tables (for initial setup — use Alembic in production)
# ------------------------------------------------------------------


async def init_db() -> None:
    """Create all tables defined in models.

    WARNING: In production, use Alembic migrations instead of this.
    This is only for initial bootstrap / development without migrations.
    """
    from app.models import __all_models  # noqa: F401 — triggers model imports

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables created successfully")


async def dispose_db() -> None:
    """Dispose the engine and close all connections."""
    await engine.dispose()
    logger.info("Database engine disposed")
