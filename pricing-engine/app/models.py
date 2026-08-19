from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

JsonType = JSONB().with_variant(JSON(), "sqlite")


class Base(DeclarativeBase):
    pass


class ProvenanceMixin:
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    source_level: Mapped[str] = mapped_column(String(8), nullable=False)
    confidence: Mapped[str] = mapped_column(String(16), nullable=False)
    is_estimate: Mapped[bool] = mapped_column(Boolean, nullable=False)
    effective_from: Mapped[date | None] = mapped_column(nullable=True)
    effective_to: Mapped[date | None] = mapped_column(nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class ProductCategory(ProvenanceMixin, Base):
    __tablename__ = "product_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    hs6_default: Mapped[str | None] = mapped_column(String(10), nullable=True)
    pbe_desc_template: Mapped[str | None] = mapped_column(nullable=True)
    certifications: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    lane_fit: Mapped[dict | None] = mapped_column(JsonType, nullable=True)


class HsCode(ProvenanceMixin, Base):
    __tablename__ = "hs_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    hs6: Mapped[str] = mapped_column(String(6), nullable=False)
    itc_hs_8: Mapped[str | None] = mapped_column(String(8), nullable=True)
    hts_10: Mapped[str | None] = mapped_column(String(10), nullable=True)
    description: Mapped[str] = mapped_column(nullable=False)
    product_cat: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("product_categories.id"),
        nullable=False,
    )


class CountryRate(ProvenanceMixin, Base):
    __tablename__ = "country_rates"

    id: Mapped[int] = mapped_column(primary_key=True)
    country_iso2: Mapped[str] = mapped_column(String(2), nullable=False)
    hs6: Mapped[str | None] = mapped_column(String(6), nullable=True)
    rate_type: Mapped[str] = mapped_column(String(32), nullable=False)
    rate_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    amount_minor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    threshold_minor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    basis: Mapped[str | None] = mapped_column(String(64), nullable=True)


class Lane(ProvenanceMixin, Base):
    __tablename__ = "lanes"

    id: Mapped[int] = mapped_column(primary_key=True)
    lane: Mapped[str] = mapped_column(String(4), nullable=False)
    country_iso2: Mapped[str] = mapped_column(String(2), nullable=False)
    first_slab_g: Mapped[int] = mapped_column(Integer, nullable=False)
    first_slab_rate_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    addl_slab_g: Mapped[int] = mapped_column(Integer, nullable=False)
    addl_slab_rate_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_cap_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    volume_free: Mapped[bool] = mapped_column(Boolean, nullable=False)
    divisor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    transit_min_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    transit_max_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    conflicts: Mapped[dict | None] = mapped_column(JsonType, nullable=True)