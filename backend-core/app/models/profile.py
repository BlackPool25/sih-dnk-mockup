"""SellerProfile model — verified seller identity, KYC details, and export-compliance data."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, utcnow

if TYPE_CHECKING:
    from app.models.profile_document import ProfileDocument


class SellerProfile(Base):
    __tablename__ = "seller_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    firm_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    owner_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    pan_encrypted: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    bank_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    bank_account_encrypted: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    ifsc: Mapped[str | None] = mapped_column(
        String(11),
        nullable=True,
    )
    bank_branch: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    iec: Mapped[str | None] = mapped_column(
        String(10),
        unique=True,
        nullable=True,
    )
    ad_code_encrypted: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    gstin_encrypted: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    address_line1: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    address_line2: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    state: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    pincode: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )
    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    profile_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
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
    documents: Mapped[list[ProfileDocument]] = relationship(
        "ProfileDocument",
        back_populates="profile",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<SellerProfile(id={self.id!r}, firm_name={self.firm_name!r}, "
            f"iec={self.iec!r})>"
        )
