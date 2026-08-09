"""Product categories (config table, carries provenance)."""

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, ProvenanceMixin


class ProductCategory(ProvenanceMixin, Base):
    __tablename__ = "product_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    hs6_default: Mapped[str | None] = mapped_column(String(10), nullable=True)
    pbe_desc_template: Mapped[str | None] = mapped_column(nullable=True)
    certifications: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    lane_fit: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
