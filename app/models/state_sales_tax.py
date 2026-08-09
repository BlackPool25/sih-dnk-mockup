"""US state sales tax (config table, carries provenance)."""

from sqlalchemy import Boolean, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, ProvenanceMixin


class StateSalesTax(ProvenanceMixin, Base):
    __tablename__ = "state_sales_tax"

    id: Mapped[int] = mapped_column(primary_key=True)
    state_iso2: Mapped[str] = mapped_column(String(2), unique=True, nullable=False)
    state_name: Mapped[str] = mapped_column(String(64), nullable=False)
    state_rate_pct: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    combined_min_pct: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    combined_max_pct: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    nexus_threshold_usd: Mapped[int | None] = mapped_column(Integer, nullable=True)
    nexus_tx_test: Mapped[bool] = mapped_column(Boolean, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
