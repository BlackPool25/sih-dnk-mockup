"""Auth model registry — importing this module registers every table on Base.metadata.

Alembic autogenerate must see ALL models; importing them here (and importing
this package from auth/alembic/env.py) guarantees that.
"""

from datetime import UTC, datetime

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Root declarative base for auth models (SQLAlchemy 2.0 style)."""


def utcnow() -> datetime:
    """Timezone-aware UTC now, for Python-side defaults."""
    return datetime.now(UTC)


# Register models on Base.metadata — must follow Base definition to avoid
# circular imports (models import Base from here, then we re-import them).
from auth.models.refresh_token import RefreshToken
from auth.models.user import User, UserRole

__all__ = [
    "Base",
    "RefreshToken",
    "User",
    "UserRole",
    "utcnow",
]
