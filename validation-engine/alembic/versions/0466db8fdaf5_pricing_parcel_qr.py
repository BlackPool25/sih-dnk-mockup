"""pricing/parcel/qr tokens + parcel_id on documents

Revision ID: 0466db8fdaf5
Revises: 8382b870f54f
Create Date: 2026-08-19 00:00:00.000000

Adds pricing/parcel/QR support to the validation-engine schema without
breaking existing orders:

* orders.pricing_breakdown JSONB nullable — full pricing engine response
* orders.parcels JSONB nullable — split-parcel array (weight/value/dims)
* orders.qr_tokens JSONB nullable — per-parcel QR token JTIs (qr_token_jti kept for compat)
* documents.parcel_id nullable VARCHAR(64) — links a document render to a single parcel

All adds are idempotent (inspect before DDL) and backfill existing rows to
NULL / empty where sensible. Downgrade drops the four columns.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0466db8fdaf5"
down_revision: Union[str, Sequence[str], None] = "8382b870f54f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(conn: sa.Connection, table: str) -> dict[str, dict]:
    return {c["name"]: c for c in sa.inspect(conn).get_columns(table)}


def upgrade() -> None:
    conn = op.get_bind()
    # ── orders: pricing_breakdown / parcels / qr_tokens ──────────────────
    cols = _columns(conn, "orders")
    if "pricing_breakdown" not in cols:
        op.add_column("orders", sa.Column("pricing_breakdown", postgresql.JSONB(), nullable=True))
    if "parcels" not in cols:
        op.add_column("orders", sa.Column("parcels", postgresql.JSONB(), nullable=True))
    if "qr_tokens" not in cols:
        op.add_column("orders", sa.Column("qr_tokens", postgresql.JSONB(), nullable=True))

    # Backfill: existing rows stay NULL (explicitly set to NULL for clarity,
    # no default needed). Keep qr_token_jti untouched for backwards compat.
    # No server_default on JSONB columns to avoid surprising defaults.

    # ── documents: parcel_id ─────────────────────────────────────────────
    cols = _columns(conn, "documents")
    if "parcel_id" not in cols:
        op.add_column("documents", sa.Column("parcel_id", sa.String(length=64), nullable=True))
        # Also add parcel_index as alias for same concept if teams prefer integer index
        # We expose parcel_id (string) as canonical; parcel_index is NOT added to avoid
        # divergence. Teams using integer index can store it as stringified index.
    # Optional index on documents.parcel_id for parcel-scoped lookups
    insp = sa.inspect(conn)
    idx_names = {idx["name"] for idx in insp.get_indexes("documents")}
    if "ix_documents_parcel_id" not in idx_names and "parcel_id" in _columns(conn, "documents"):
        op.create_index("ix_documents_parcel_id", "documents", ["parcel_id"])


def downgrade() -> None:
    conn = op.get_bind()
    # documents.parcel_id
    cols = _columns(conn, "documents")
    if "parcel_id" in cols:
        insp = sa.inspect(conn)
        idx_names = {idx["name"] for idx in insp.get_indexes("documents")}
        if "ix_documents_parcel_id" in idx_names:
            op.drop_index("ix_documents_parcel_id", table_name="documents")
        op.drop_column("documents", "parcel_id")

    # orders columns
    cols = _columns(conn, "orders")
    for name in ("qr_tokens", "parcels", "pricing_breakdown"):
        if name in cols:
            op.drop_column("orders", name)
