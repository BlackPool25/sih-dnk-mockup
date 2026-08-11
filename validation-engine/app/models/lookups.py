"""Lookup results per transcript (business table — NO config FKs).

Stores the KEYS emitted by extraction (category_key, hs_code) plus the
resolved duty/lane payloads as plain JSONB — deliberately no FK into config
tables, so TRUNCATE-without-CASCADE of config never cascades here.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utcnow


class Lookup(Base):
    __tablename__ = "lookups"

    id: Mapped[int] = mapped_column(primary_key=True)
    # FK business -> business only.
    transcript_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("transcripts.id"), nullable=False
    )
    category_key: Mapped[str] = mapped_column(String(100), nullable=False)
    hs_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    duty: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    lane: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
    )
