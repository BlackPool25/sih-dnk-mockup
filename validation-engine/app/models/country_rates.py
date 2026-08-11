"""Country duty / VAT / de-minimis rates (config table, carries provenance)."""

from sqlalchemy import Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, ProvenanceMixin


class CountryRate(ProvenanceMixin, Base):
    __tablename__ = "country_rates"

    id: Mapped[int] = mapped_column(primary_key=True)
    country_iso2: Mapped[str] = mapped_column(String(2), nullable=False)
    hs6: Mapped[str | None] = mapped_column(String(6), nullable=True)
    rate_type: Mapped[str] = mapped_column(String(32), nullable=False)
    rate_pct: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    # Money as integer minor units (paise).
    amount_minor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    threshold_minor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    basis: Mapped[str | None] = mapped_column(String(64), nullable=True)
