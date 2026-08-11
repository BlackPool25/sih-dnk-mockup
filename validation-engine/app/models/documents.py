"""Rendered documents with immutable versioning (business table — NO config FKs)."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utcnow


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    doc_type: Mapped[str] = mapped_column(String(32), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    structured_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    file_path: Mapped[str] = mapped_column(nullable=False)
    # Self-FK: the doc this one supersedes (NULL for the first version).
    supersedes_doc_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("documents.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
    )
