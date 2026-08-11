"""Order model — trade order with seller/buyer FKs, encrypted profile snapshot, and line items."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, utcnow

if TYPE_CHECKING:
    from app.models.doc_pack import DocPack


class OrderStatus(enum.StrEnum):
    """Workflow statuses for a trade order."""

    created = "created"
    docs_generated = "docs_generated"
    qr_generated = "qr_generated"
    in_review = "in_review"
    approved = "approved"
    rejected = "rejected"
    cancelled = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    buyer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status"),
        nullable=False,
        default=OrderStatus.created,
    )
    profile_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    profile_snapshot_encrypted: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )
    destination_country: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    value_minor: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="INR",
    )
    consignee: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    net_weight_g: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    gross_weight_g: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    article_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    iec: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )
    ad_code_encrypted: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )
    bank_account_encrypted: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )
    bank_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    ifsc: Mapped[str] = mapped_column(
        String(11),
        nullable=False,
    )
    exporter_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    exporter_address: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    state_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )
    line_items: Mapped[list[dict]] = mapped_column(
        JSONB,
        nullable=False,
    )
    doc_pack_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("doc_packs.id", use_alter=True, name="fk_orders_doc_pack_id"),
        nullable=True,
    )
    qr_token_jti: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
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

    # relationships
    doc_pack: Mapped[DocPack | None] = relationship(
        "DocPack",
        back_populates="order",
        foreign_keys=[doc_pack_id],
    )

    def __repr__(self) -> str:
        return (
            f"<Order(id={self.id!r}, status={self.status!r}, "
            f"destination_country={self.destination_country!r})>"
        )
