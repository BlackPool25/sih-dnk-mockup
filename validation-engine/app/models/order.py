"""Orders — business table for export consignment lifecycle (NO provenance, NO config FKs)."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow

if TYPE_CHECKING:
    from app.models.line_item import LineItem


class OrderStatus(enum.StrEnum):
    """Lifecycle states for an export consignment order."""

    quote_accepted = "quote_accepted"
    confirmed = "confirmed"
    paid_held = "paid_held"
    in_transit = "in_transit"
    delivered = "delivered"
    disputed = "disputed"
    settled = "settled"
    refunded = "refunded"


class ValidationState(enum.StrEnum):
    """Validation readiness for order data."""

    incomplete = "incomplete"
    invalid = "invalid"
    ready = "ready"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status"),
        nullable=False,
        default=OrderStatus.quote_accepted,
    )
    validation_state: Mapped[ValidationState | None] = mapped_column(
        Enum(ValidationState, name="validation_state"),
        nullable=True,
        default=None,
    )

    # ── business fields ────────────────────────────────────────────
    destination_country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    value_minor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="INR", server_default="INR"
    )
    consignee: Mapped[str | None] = mapped_column(String(256), nullable=True)
    net_weight_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gross_weight_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    article_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    iec: Mapped[str | None] = mapped_column(String(16), nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(16), nullable=True)
    ad_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    bank_account: Mapped[str | None] = mapped_column(String(32), nullable=True)
    bank_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ifsc: Mapped[str | None] = mapped_column(String(16), nullable=True)
    quote_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    exporter_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    exporter_address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    state_code: Mapped[str | None] = mapped_column(String(2), nullable=True)

    # ── ownership ──────────────────────────────────────────────────
    seller_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    buyer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    qr_token_jti: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # ── versioning & JSONB ─────────────────────────────────────────
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    last_report: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # ── timestamps ─────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
        onupdate=utcnow,
    )

    # ── relationships ──────────────────────────────────────────────
    line_items: Mapped[list[LineItem]] = relationship(
        "LineItem", back_populates="order", cascade="all, delete-orphan"
    )
