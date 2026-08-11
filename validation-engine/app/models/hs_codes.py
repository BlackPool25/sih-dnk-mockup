"""HS codes (config table, carries provenance)."""

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, ProvenanceMixin


class HsCode(ProvenanceMixin, Base):
    __tablename__ = "hs_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    hs6: Mapped[str] = mapped_column(String(6), nullable=False)
    itc_hs_8: Mapped[str | None] = mapped_column(String(8), nullable=True)
    hts_10: Mapped[str | None] = mapped_column(String(10), nullable=True)
    description: Mapped[str] = mapped_column(nullable=False)
    # FK config -> config only (business tables hold no FKs into config).
    product_cat: Mapped[int] = mapped_column(
        Integer, ForeignKey("product_categories.id"), nullable=False
    )
