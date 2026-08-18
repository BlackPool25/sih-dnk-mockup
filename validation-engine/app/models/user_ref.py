"""The auth-owned ``users`` table, registered so Order's seller/buyer FKs resolve.

The ``users`` table is created and owned by the auth service (auth/alembic).
validation-engine only needs it in its metadata for the ``ForeignKey("users.id")``
on ``Order.seller_id`` / ``Order.buyer_id`` to resolve at mapper build time —
this module declares the column shape without owning the schema.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utcnow


class User(Base):
    """Auth's user row as seen by validation-engine (read-only FK target)."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=utcnow, nullable=False
    )


__all__ = ["User"]
