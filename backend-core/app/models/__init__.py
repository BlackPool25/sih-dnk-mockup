"""Backend-core SQLAlchemy models.

DeclarativeBase for all backend-core table definitions.
Tables will be added in Wave 4-6 (profiles, orders, doc packs, QR codes).
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for backend-core models."""
