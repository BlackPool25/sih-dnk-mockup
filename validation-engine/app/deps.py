"""FastAPI dependencies — DB session injection."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Yield a read-only DB session; caller is responsible for lifecycle.

    For write operations, use ``SessionLocal.begin()`` directly in the
    endpoint to manage the transaction boundary.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
