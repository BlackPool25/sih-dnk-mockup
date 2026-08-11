"""Filling rules (config table, carries provenance).

One row per validation rule the booking pipeline enforces (later waves read
these from validate.py).  ``applies_to`` scopes a rule to a subset of
form/item types (NULL = applies everywhere); ``params`` carries the rule's
operator configuration (field names, ratios, thresholds).
"""

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, ProvenanceMixin


class FillingRule(ProvenanceMixin, Base):
    __tablename__ = "filling_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true", default=True
    )
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    applies_to: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
