"""Messaging DB models — messaging_* namespaced tables."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Messaging service declarative base."""


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MessagingThread(Base):
    """Buyer-seller conversation thread — one per order (conceptual).

    Spec: id UUID PK (=order_id conceptual), order_id UUID indexed unique,
          seller_id UUID indexed, buyer_id UUID indexed,
          created_at timestamptz utcnow, last_message_at nullable,
          last_preview_encrypted text nullable
    """

    __tablename__ = "messaging_threads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True, index=True
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    buyer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    last_preview_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)


class MessagingMessage(Base):
    """Single encrypted message within a thread."""

    __tablename__ = "messaging_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messaging_threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    sender_role: Mapped[str] = mapped_column(String(16), nullable=False)
    body_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    enc_nonce_b64: Mapped[str] = mapped_column(String(64), nullable=False)
    attachments: Mapped[object | None] = mapped_column(JSONB, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )


class QuoteState(Base):
    """Current quote state per order/thread — versioned via quote_versions."""

    __tablename__ = "quote_states"
    __table_args__ = (
        CheckConstraint(
            "state IN ('draft','sent','counter','approved','paid_held')",
            name="ck_quote_states_state_enum",
        ),
    )

    quote_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Conceptual order_id / thread_id — same value, no FK to orders table (conceptual only)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True, index=True
    )
    # Alias column for spec compatibility: thread_id mirrors order_id conceptually
    thread_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, unique=True, index=True
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    buyer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    qty: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    shipping_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )


class QuoteVersion(Base):
    """Immutable snapshot of a quote version — composite PK (quote_id, version)."""

    __tablename__ = "quote_versions"

    quote_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quote_states.quote_id", ondelete="CASCADE"),
        primary_key=True,
    )
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    price_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    qty: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    shipping_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )


class PaymentMock(Base):
    """Internal mock payment — replaces external https://pay.mock.

    Supports both quote-linked (quote_id) and generic (order_id only) flows.
    status: initiated | paid_held
    """

    __tablename__ = "payment_mocks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quote_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quote_states.quote_id", ondelete="SET NULL"), nullable=True, index=True
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    thread_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="initiated")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
