"""Declarative base and the shared provenance mixin.

Every imported (config) table carries provenance so no figure is ever
presented as fact unless the research says so.  Business tables
(transcripts, lookups, documents) deliberately do NOT mix this in.
"""

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Root declarative base for all models (SQLAlchemy 2.0 style)."""


def utcnow() -> datetime:
    """Timezone-aware UTC now, for Python-side defaults."""
    return datetime.now(timezone.utc)


class ProvenanceMixin:
    """Provenance columns applied to all imported config tables.

    - source_url:   where the figure came from (NOT NULL)
    - source_level: L1..L5 research-confidence tier
    - confidence:   high | moderate | low | unverified
    - is_estimate:  True when the figure is a working estimate, not fact
    - effective_from / effective_to: freshness window (NULL = open-ended)
    - verified_at:  when the record was verified (NULL = not yet)
    """

    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    source_level: Mapped[str] = mapped_column(String(8), nullable=False)
    confidence: Mapped[str] = mapped_column(String(16), nullable=False)
    is_estimate: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", default=False
    )
    effective_from: Mapped[date | None] = mapped_column(nullable=True)
    effective_to: Mapped[date | None] = mapped_column(nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
