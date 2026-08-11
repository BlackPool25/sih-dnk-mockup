"""ProfileDocument model — encrypted KYC documents attached to a SellerProfile."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, utcnow

if TYPE_CHECKING:
    from app.models.profile import SellerProfile


class DocumentType(enum.StrEnum):
    """Supported KYC document types for seller verification."""

    pan_card = "pan_card"
    bank_statement = "bank_statement"
    iec_certificate = "iec_certificate"
    gst_certificate = "gst_certificate"
    other = "other"


class ProfileDocument(Base):
    __tablename__ = "profile_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("seller_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    doc_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="document_type"),
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    encrypted_content: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )
    checksum_sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    key_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
    )

    # relationships
    profile: Mapped[SellerProfile] = relationship(
        "SellerProfile",
        back_populates="documents",
    )

    def __repr__(self) -> str:
        return (
            f"<ProfileDocument(id={self.id!r}, doc_type={self.doc_type!r}, "
            f"filename={self.filename!r})>"
        )
