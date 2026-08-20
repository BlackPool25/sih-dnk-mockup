"""Verification DB models — verification_* namespaced tables."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Verification service declarative base."""


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class VerificationAttempt(Base):
    """One verification attempt (L0/L1/L2/liveness)."""

    __tablename__ = "verification_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seller_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    level: Mapped[str] = mapped_column(String(16), nullable=False)  # L0, L1, L2, liveness
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")  # pending|success|failed
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="mock")
    payload: Mapped[object | None] = mapped_column(JSONB, nullable=True)
    result: Mapped[object | None] = mapped_column(JSONB, nullable=True)
    mocked: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


class TrustLevel(Base):
    """Current trust level per seller (derived from attempts)."""

    __tablename__ = "verification_trust_levels"

    seller_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    level: Mapped[str] = mapped_column(String(16), nullable=False, default="L0")
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
