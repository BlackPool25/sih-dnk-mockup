"""Shipping lanes ITPS/EMS (config table, carries provenance)."""

from sqlalchemy import Boolean, CheckConstraint, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, ProvenanceMixin


class Lane(ProvenanceMixin, Base):
    __tablename__ = "lanes"
    __table_args__ = (CheckConstraint("lane IN ('ITPS', 'EMS')", name="ck_lanes_lane"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    lane: Mapped[str] = mapped_column(String(4), nullable=False)
    country_iso2: Mapped[str] = mapped_column(String(2), nullable=False)
    # Slab math: weights in grams, money in integer minor units (paise).
    first_slab_g: Mapped[int] = mapped_column(Integer, nullable=False)
    first_slab_rate_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    addl_slab_g: Mapped[int] = mapped_column(Integer, nullable=False)
    addl_slab_rate_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_cap_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    volume_free: Mapped[bool] = mapped_column(Boolean, nullable=False)
    divisor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    transit_min_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    transit_max_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Contradiction payloads (C-1..C-13) kept verbatim, never averaged.
    conflicts: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
