"""DocPack model — rendered export documents attached to an Order."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, utcnow

if TYPE_CHECKING:
    from app.models.order import Order


class DocPack(Base):
    __tablename__ = "doc_packs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    ci_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Commercial Invoice document data",
    )
    pl_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Packing List document data",
    )
    cn_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="CN22/CN23 customs declaration data",
    )
    pbe_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="PBE-III/IV postal export data",
    )
    rendered_pdf_path: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    qr_image_path: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
    )

    # relationships
    order: Mapped[Order] = relationship(
        "Order",
        foreign_keys=[order_id],
    )

    def __repr__(self) -> str:
        return (
            f"<DocPack(id={self.id!r}, order_id={self.order_id!r}, "
            f"generated_at={self.generated_at!r})>"
        )
