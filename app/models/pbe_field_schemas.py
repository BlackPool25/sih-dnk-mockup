"""PBE form field schemas (config table, carries provenance)."""

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, ProvenanceMixin


class PbeFieldSchema(ProvenanceMixin, Base):
    __tablename__ = "pbe_field_schemas"

    id: Mapped[int] = mapped_column(primary_key=True)
    form_type: Mapped[str] = mapped_column(String(16), nullable=False)
    section: Mapped[str | None] = mapped_column(String(64), nullable=True)
    field_key: Mapped[str] = mapped_column(String(128), nullable=False)
    label: Mapped[str] = mapped_column(nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    value_type: Mapped[str] = mapped_column(String(32), nullable=False)
    validation: Mapped[str | None] = mapped_column(nullable=True)
    options: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
