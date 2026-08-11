"""Async database engine + session factory for the DNK mockup.

DATABASE_URL is read from the environment (postgresql+psycopg://...),
loaded from the project `.env` via python-dotenv when not already set.
"""

import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

load_dotenv()


def get_engine() -> AsyncEngine:
    """Create an async SQLAlchemy engine from the DATABASE_URL env var.

    Raises:
        ValueError: if DATABASE_URL is not set in the environment.
    """
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL not set")
    return create_async_engine(url, pool_pre_ping=True)


def get_session() -> async_sessionmaker[AsyncSession]:
    """Return an async session factory that yields AsyncSession instances.

    Usage::

        async with get_session() as session:
            result = await session.execute(select(...))
    """
    engine = get_engine()
    return async_sessionmaker(engine, expire_on_commit=False)
