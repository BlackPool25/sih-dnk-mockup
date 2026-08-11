"""add_orders_and_doc_packs

Revision ID: af1ad70149eb
Revises: 2ae521447228
Create Date: 2026-08-11 18:14:22.890213

Drop legacy orders table (validation-engine era) and recreate with the
backend-core Order/DocPack models.  The old order_status enum values
(quote_accepted / confirmed / paid_held / …) are replaced with the new
workflow states (created → docs_generated → qr_generated → in_review →
approved / rejected / cancelled).
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "af1ad70149eb"
down_revision: Union[str, Sequence[str], None] = "2ae521447228"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ── Old order_status enum values (for downgrade) ─────────────────────────────
_OLD_ORDER_STATUS_VALUES = [
    "quote_accepted",
    "confirmed",
    "paid_held",
    "in_transit",
    "delivered",
    "disputed",
    "settled",
    "refunded",
]

# ── New order_status enum values ─────────────────────────────────────────────
_NEW_ORDER_STATUS_VALUES = [
    "created",
    "docs_generated",
    "qr_generated",
    "in_review",
    "approved",
    "rejected",
    "cancelled",
]


def upgrade() -> None:
    """Replace legacy orders table with backend-core Order/DocPack schema."""

    # 1. Drop foreign key from legacy line_items → orders.
    op.drop_constraint(
        "line_items_order_id_fkey", "line_items", type_="foreignkey"
    )
    op.drop_table("line_items")

    # 2. Drop the legacy orders table (depends on the old order_status enum).
    op.drop_table("orders")

    # 3. Drop the old order_status enum so we can recreate it with new values.
    sa.Enum(name="order_status").drop(op.get_bind(), checkfirst=True)

    # 4. Create the new order_status enum.
    order_status = postgresql.ENUM(
        *_NEW_ORDER_STATUS_VALUES,
        name="order_status",
        create_type=False,
    )
    order_status.create(op.get_bind(), checkfirst=True)

    # 5. Create the new orders table.
    op.create_table(
        "orders",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("seller_id", sa.UUID(), nullable=False),
        sa.Column("buyer_id", sa.UUID(), nullable=False),
        sa.Column(
            "status",
            order_status,
            nullable=False,
            server_default="created",
        ),
        sa.Column("profile_version", sa.Integer(), nullable=False),
        sa.Column(
            "profile_snapshot_encrypted",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "destination_country", sa.String(length=100), nullable=False
        ),
        sa.Column("value_minor", sa.Integer(), nullable=False),
        sa.Column(
            "currency", sa.String(length=3), nullable=False,
            server_default="INR",
        ),
        sa.Column("consignee", sa.String(length=255), nullable=False),
        sa.Column("net_weight_g", sa.Float(), nullable=False),
        sa.Column("gross_weight_g", sa.Float(), nullable=False),
        sa.Column("article_id", sa.String(), nullable=True),
        sa.Column("iec", sa.String(length=10), nullable=False),
        sa.Column(
            "ad_code_encrypted",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "bank_account_encrypted",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("bank_name", sa.String(length=255), nullable=False),
        sa.Column("ifsc", sa.String(length=11), nullable=False),
        sa.Column("exporter_name", sa.String(length=255), nullable=False),
        sa.Column("exporter_address", sa.String(length=500), nullable=False),
        sa.Column("state_code", sa.String(length=10), nullable=False),
        sa.Column(
            "line_items",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("doc_pack_id", sa.UUID(), nullable=True),
        sa.Column("qr_token_jti", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["seller_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["buyer_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 6. Create the doc_packs table.
    op.create_table(
        "doc_packs",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column(
            "ci_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            comment="Commercial Invoice document data",
        ),
        sa.Column(
            "pl_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            comment="Packing List document data",
        ),
        sa.Column(
            "cn_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            comment="CN22/CN23 customs declaration data",
        ),
        sa.Column(
            "pbe_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            comment="PBE-III/IV postal export data",
        ),
        sa.Column("rendered_pdf_path", sa.String(), nullable=True),
        sa.Column("qr_image_path", sa.String(), nullable=True),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["order_id"], ["orders.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id"),
    )

    # 7. Add the deferred FK from orders → doc_packs (use_alter avoids the
    #    circular dependency during CREATE TABLE).
    op.create_foreign_key(
        "fk_orders_doc_pack_id",
        "orders",
        "doc_packs",
        ["doc_pack_id"],
        ["id"],
        use_alter=True,
    )


def downgrade() -> None:
    """Restore legacy orders table and old order_status enum."""

    # 1. Reverse the deferred FK.
    op.drop_constraint(
        "fk_orders_doc_pack_id", "orders", type_="foreignkey"
    )

    # 2. Drop backend-core tables.
    op.drop_table("doc_packs")
    op.drop_table("orders")

    # 3. Drop the new order_status enum.
    sa.Enum(name="order_status").drop(op.get_bind(), checkfirst=True)

    # 4. Recreate the old order_status enum.
    old_order_status = postgresql.ENUM(
        *_OLD_ORDER_STATUS_VALUES,
        name="order_status",
        create_type=False,
    )
    old_order_status.create(op.get_bind(), checkfirst=True)

    # 4b. Reuse the existing validation_state enum (never dropped — legacy type).
    validation_state = postgresql.ENUM(
        "incomplete", "invalid", "ready",
        name="validation_state",
        create_type=False,
    )
    validation_state.create(op.get_bind(), checkfirst=True)

    # 5. Recreate the legacy orders table.
    op.create_table(
        "orders",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("status", old_order_status, nullable=False),
        sa.Column(
            "validation_state",
            validation_state,
            nullable=True,
        ),
        sa.Column("destination_country", sa.VARCHAR(length=64), nullable=True),
        sa.Column("value_minor", sa.INTEGER(), nullable=True),
        sa.Column("currency", sa.VARCHAR(length=3), nullable=False,
                  server_default="INR"),
        sa.Column("consignee", sa.VARCHAR(length=256), nullable=True),
        sa.Column("net_weight_g", sa.INTEGER(), nullable=True),
        sa.Column("gross_weight_g", sa.INTEGER(), nullable=True),
        sa.Column("article_id", sa.VARCHAR(length=128), nullable=True),
        sa.Column("iec", sa.VARCHAR(length=16), nullable=True),
        sa.Column("gstin", sa.VARCHAR(length=16), nullable=True),
        sa.Column("ad_code", sa.VARCHAR(length=16), nullable=True),
        sa.Column("bank_account", sa.VARCHAR(length=32), nullable=True),
        sa.Column("bank_name", sa.VARCHAR(length=128), nullable=True),
        sa.Column("ifsc", sa.VARCHAR(length=16), nullable=True),
        sa.Column("quote_id", sa.VARCHAR(length=64), nullable=True),
        sa.Column(
            "version",
            sa.INTEGER(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.Column(
            "last_report",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("exporter_name", sa.VARCHAR(length=256), nullable=True),
        sa.Column("exporter_address", sa.VARCHAR(length=512), nullable=True),
        sa.Column("state_code", sa.VARCHAR(length=2), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # 6. Recreate the legacy line_items table.
    op.create_table(
        "line_items",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column(
            "commodity_description",
            sa.Text(),
            nullable=False,
        ),
        sa.Column("hsn_code", sa.VARCHAR(length=8), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column(
            "fob_value_minor",
            sa.Integer(),
            nullable=False,
            comment="Per-unit FOB value in minor currency",
        ),
        sa.ForeignKeyConstraint(
            ["order_id"], ["orders.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
