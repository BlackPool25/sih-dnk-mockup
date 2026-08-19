"""add order_id/parcel_id to shipments

Revision ID: 5f6d15dbe3f4
Revises:
Create Date: 2026-08-19 00:00:00.000000

Adds nullable order/parcel linkage to tracking-api shipments. The
tracking-api previously used Base.metadata.create_all — this migration
replaces that anti-pattern with an Alembic-managed additive change.

* shipments.order_id VARCHAR(64) nullable indexed — FK to validation-engine orders.id (logical, not enforced to avoid cross-service FK coupling)
* shipments.parcel_id VARCHAR(64) nullable indexed — identifies parcel within order

Idempotent via inspector check; downgrade drops indexes then columns.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5f6d15dbe3f4"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(conn: sa.Connection, table: str) -> dict[str, dict]:
    return {c["name"]: c for c in sa.inspect(conn).get_columns(table)}


def upgrade() -> None:
    conn = op.get_bind()
    # Ensure shipments exists (legacy create_all path). If not, create minimal table.
    tables = set(sa.inspect(conn).get_table_names())
    if "shipments" not in tables:
        op.create_table(
            "shipments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("tracking_number", sa.String(), unique=True, nullable=False),
            sa.Column("carrier", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False, server_default="Booked"),
            sa.Column("order_id", sa.String(length=64), nullable=True),
            sa.Column("parcel_id", sa.String(length=64), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_shipments_order_id", "shipments", ["order_id"])
        op.create_index("ix_shipments_parcel_id", "shipments", ["parcel_id"])
        return

    cols = _columns(conn, "shipments")
    insp = sa.inspect(conn)
    idx_names = {idx["name"] for idx in insp.get_indexes("shipments")}

    if "order_id" not in cols:
        op.add_column("shipments", sa.Column("order_id", sa.String(length=64), nullable=True))
        cols = _columns(conn, "shipments")  # refresh

    if "parcel_id" not in cols:
        op.add_column("shipments", sa.Column("parcel_id", sa.String(length=64), nullable=True))

    # indexes idempotent
    insp = sa.inspect(conn)
    idx_names = {idx["name"] for idx in insp.get_indexes("shipments")}
    if "ix_shipments_order_id" not in idx_names:
        op.create_index("ix_shipments_order_id", "shipments", ["order_id"])
    if "ix_shipments_parcel_id" not in idx_names:
        op.create_index("ix_shipments_parcel_id", "shipments", ["parcel_id"])


def downgrade() -> None:
    conn = op.get_bind()
    if "shipments" not in set(sa.inspect(conn).get_table_names()):
        return
    cols = _columns(conn, "shipments")
    insp = sa.inspect(conn)
    idx_names = {idx["name"] for idx in insp.get_indexes("shipments")}
    if "ix_shipments_parcel_id" in idx_names:
        op.drop_index("ix_shipments_parcel_id", table_name="shipments")
    if "ix_shipments_order_id" in idx_names:
        op.drop_index("ix_shipments_order_id", table_name="shipments")
    if "parcel_id" in cols:
        op.drop_column("shipments", "parcel_id")
    if "order_id" in cols:
        op.drop_column("shipments", "order_id")
