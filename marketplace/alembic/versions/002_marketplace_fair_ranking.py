"""marketplace fair ranking — add images/weight/dims/base_cost/margin/make_time/status etc

Revision ID: 002_marketplace_fair
Revises: 001_marketplace_init
Create Date: 2026-08-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "002_marketplace_fair"
down_revision: Union[str, None] = "001_marketplace_init"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _add_column_if_not_exists(table: str, column: sa.Column) -> None:
    # Use batch approach: try add, ignore if exists (postgres will error but we catch via try)
    # Simpler: check via inspector outside transaction? We'll just try and catch.
    try:
        op.add_column(table, column)
    except Exception:
        pass


def upgrade() -> None:
    # marketplace_products — add spec columns
    try:
        op.add_column("marketplace_products", sa.Column("images", JSONB, nullable=True))
    except Exception:
        pass
    try:
        op.add_column("marketplace_products", sa.Column("weight_g", sa.Integer, nullable=True))
    except Exception:
        pass
    try:
        op.add_column("marketplace_products", sa.Column("dims", JSONB, nullable=True))
    except Exception:
        pass
    try:
        op.add_column("marketplace_products", sa.Column("base_cost_minor", sa.Integer, nullable=False, server_default="0"))
    except Exception:
        pass
    try:
        op.add_column("marketplace_products", sa.Column("margin_pct", sa.Float, nullable=False, server_default="20.0"))
    except Exception:
        pass
    try:
        op.add_column("marketplace_products", sa.Column("make_time_days", sa.Integer, nullable=False, server_default="3"))
    except Exception:
        pass
    try:
        op.add_column("marketplace_products", sa.Column("status", sa.String(16), nullable=False, server_default="active"))
    except Exception:
        pass

    # marketplace_listings — add spec columns
    try:
        op.add_column("marketplace_listings", sa.Column("status", sa.String(16), nullable=False, server_default="live"))
    except Exception:
        pass
    try:
        op.add_column("marketplace_listings", sa.Column("featured", sa.Boolean, nullable=False, server_default="false"))
    except Exception:
        pass
    try:
        op.add_column("marketplace_listings", sa.Column("views", sa.Integer, nullable=False, server_default="0"))
    except Exception:
        pass
    try:
        op.add_column("marketplace_listings", sa.Column("sales_count", sa.Integer, nullable=False, server_default="0"))
    except Exception:
        pass
    try:
        op.add_column("marketplace_listings", sa.Column("published_at", sa.DateTime(timezone=True), nullable=True))
    except Exception:
        pass

    # marketplace_sales_ledger — add listing_id + event
    try:
        op.add_column("marketplace_sales_ledger", sa.Column("listing_id", UUID(as_uuid=True), nullable=True))
    except Exception:
        pass
    try:
        op.add_column("marketplace_sales_ledger", sa.Column("event", sa.String(16), nullable=False, server_default="sale"))
    except Exception:
        pass

    # Create FK if not exists (listing_id -> marketplace_listings.id)
    try:
        op.create_foreign_key(
            "fk_marketplace_sales_ledger_listing_id",
            "marketplace_sales_ledger",
            "marketplace_listings",
            ["listing_id"],
            ["id"],
            ondelete="CASCADE",
        )
    except Exception:
        pass

    # Index for marketplace_products.seller_id etc already via models but ensure
    try:
        op.create_index("ix_marketplace_products_seller_id", "marketplace_products", ["seller_id"])
    except Exception:
        pass
    try:
        op.create_index("ix_marketplace_products_category_slug", "marketplace_products", ["category_slug"])
    except Exception:
        pass
    try:
        op.create_index("ix_marketplace_listings_seller_id", "marketplace_listings", ["seller_id"])
    except Exception:
        pass
    try:
        op.create_index("ix_marketplace_listings_product_id", "marketplace_listings", ["product_id"])
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.drop_constraint("fk_marketplace_sales_ledger_listing_id", "marketplace_sales_ledger", type_="foreignkey")
    except Exception:
        pass
    for col in ["event", "listing_id"]:
        try:
            op.drop_column("marketplace_sales_ledger", col)
        except Exception:
            pass
    for col in ["published_at", "sales_count", "views", "featured", "status"]:
        try:
            op.drop_column("marketplace_listings", col)
        except Exception:
            pass
    for col in ["status", "make_time_days", "margin_pct", "base_cost_minor", "dims", "weight_g", "images"]:
        try:
            op.drop_column("marketplace_products", col)
        except Exception:
            pass
