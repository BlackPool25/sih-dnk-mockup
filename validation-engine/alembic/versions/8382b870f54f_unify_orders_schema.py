"""unify shared orders table with the validation-engine schema

Revision ID: 8382b870f54f
Revises: b02939665e2f
Create Date: 2026-08-16 19:40:00.000000

Unifies the shared ``orders`` table onto the single schema described by
``app.models.order.Order`` (W3-T7). The live database may carry either the
backend-core workflow schema (created/docs_generated/qr_generated/in_review/
approved/rejected/cancelled, encrypted snapshots, JSONB line_items, doc_packs)
or the fresh validation-engine lifecycle schema — so every step below is
guarded by live introspection and no-ops when the target shape is already
present.

Legacy data handling (deliberate and documented):
- ad_code_encrypted / bank_account_encrypted / profile_snapshot_encrypted are
  app-level encrypted blobs the migration cannot decrypt → ad_code, gstin and
  bank_account stay NULL for legacy rows (seed-demo recreates a full row).
- The JSONB ``line_items`` column is unfolded into the normalized
  ``line_items`` table (hs_code ← hsn_code, value_minor ← total_minor,
  category_slug/weight_g/dimensions/prohibited_flags stay NULL) BEFORE the
  column is dropped.
- ``state_code`` is truncated to 2 chars (varchar(10) → varchar(2)).
- ``doc_packs`` is backend-core-only and is dropped; validation-engine keeps
  its own immutable ``documents`` rows. The downgrade is best-effort and
  cannot restore any of the dropped data.

"""

import re
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "8382b870f54f"
down_revision: Union[str, Sequence[str], None] = "b02939665e2f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Target lifecycle statuses (validation-engine app/models/order.py OrderStatus).
_LIFECYCLE_STATUSES = [
    "quote_accepted",
    "confirmed",
    "paid_held",
    "in_transit",
    "delivered",
    "disputed",
    "settled",
    "refunded",
]

# backend-core workflow statuses (backend-core app/models/order.py OrderStatus)
# → unified lifecycle status. Unknown legacy labels defensively fall back to
# quote_accepted (the live enum carries exactly these seven).
_WORKFLOW_TO_LIFECYCLE = {
    "created": "quote_accepted",
    "docs_generated": "confirmed",
    "qr_generated": "confirmed",
    "in_review": "confirmed",
    "approved": "confirmed",
    "rejected": "disputed",
    "cancelled": "refunded",
}

# Best-effort inverse mapping (downgrade only; data is already lossy).
_LIFECYCLE_TO_WORKFLOW = {
    "quote_accepted": "created",
    "confirmed": "docs_generated",
    "paid_held": "in_review",
    "in_transit": "approved",
    "delivered": "approved",
    "disputed": "rejected",
    "settled": "cancelled",
    "refunded": "cancelled",
}

_VALIDATION_STATES = ["incomplete", "invalid", "ready"]

# backend-core-only columns dropped after their data has been migrated/decided.
_BC_ONLY_COLUMNS = [
    "profile_version",
    "profile_snapshot_encrypted",
    "ad_code_encrypted",
    "bank_account_encrypted",
]

_TYPE_RE = re.compile(r"(\w+)(?:\((\d+)\))?")


def _insp(conn: sa.Connection) -> sa.Inspector:
    """Fresh inspector (SQLAlchemy inspectors cache; re-inspect after DDL)."""
    return sa.inspect(conn)


def _columns(conn: sa.Connection, table: str) -> dict[str, dict]:
    return {c["name"]: c for c in _insp(conn).get_columns(table)}


def _enum_values(conn: sa.Connection, name: str) -> list[str] | None:
    """Current labels of a named enum, or None when the enum does not exist."""
    for enum in _insp(conn).get_enums():
        if enum["name"] == name:
            values = enum.get("values")
            if values is None:
                values = enum.get("labels")
            return list(values) if values else None
    return None


def _base_and_length(col: dict | None) -> tuple[str, int | None]:
    """Upper-cased type base + length for a reflected column, e.g. ("VARCHAR", 64)."""
    if col is None:
        return ("", None)
    match = _TYPE_RE.match(str(col["type"]).upper())
    if match is None:
        return ("", None)
    return (match.group(1), int(match.group(2)) if match.group(2) else None)


def _drop_not_null(conn: sa.Connection, table: str, name: str) -> None:
    op.alter_column(table, name, existing_type=_columns(conn, table)[name]["type"], nullable=True)


def _swap_status_enum(
    conn: sa.Connection,
    source_values: list[str],
    target_values: list[str],
    mapping: dict[str, str],
    *,
    default: str,
) -> None:
    """Replace the order_status enum via an intermediate type + column cast."""
    op.execute(sa.text("ALTER TABLE orders ALTER COLUMN status DROP DEFAULT"))
    postgresql.ENUM(*target_values, name="order_status_v2").create(conn, checkfirst=True)
    whens = " ".join(
        f"WHEN '{value}' THEN '{mapping.get(value, default)}'::order_status_v2" for value in source_values
    )
    op.execute(
        sa.text(
            "ALTER TABLE orders ALTER COLUMN status TYPE order_status_v2 "
            f"USING CASE status::text {whens} ELSE status::text::order_status_v2 END"
        )
    )
    sa.Enum(name="order_status").drop(conn, checkfirst=True)
    op.execute(sa.text("ALTER TYPE order_status_v2 RENAME TO order_status"))


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()

    # ── 1. order_status enum: workflow → lifecycle (skip when already lifecycle) ──
    current_status = _enum_values(conn, "order_status")
    if current_status is not None and "created" in current_status:
        _swap_status_enum(
            conn,
            current_status,
            _LIFECYCLE_STATUSES,
            _WORKFLOW_TO_LIFECYCLE,
            default="quote_accepted",
        )

    # ── 2. add unified-only columns ──────────────────────────────────────────
    cols = _columns(conn, "orders")
    if "validation_state" not in cols:
        sa.Enum(*_VALIDATION_STATES, name="validation_state").create(conn, checkfirst=True)
        op.add_column(
            "orders",
            sa.Column(
                "validation_state",
                sa.Enum(*_VALIDATION_STATES, name="validation_state", create_type=False),
                nullable=True,
            ),
        )
    for name, length in (("gstin", 16), ("ad_code", 16), ("bank_account", 32), ("quote_id", 64)):
        if name not in cols:
            op.add_column("orders", sa.Column(name, sa.String(length=length), nullable=True))
    if "version" not in cols:
        op.add_column("orders", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    if "last_report" not in cols:
        op.add_column("orders", sa.Column("last_report", postgresql.JSONB(), nullable=True))

    # ── 3. seller_id / buyer_id (fresh validation-engine orders lack them) ──
    cols = _columns(conn, "orders")
    tables = set(_insp(conn).get_table_names())
    has_users = "users" in tables
    existing_fks = {fk["name"] for fk in _insp(conn).get_foreign_keys("orders")}
    for name in ("seller_id", "buyer_id"):
        if name not in cols:
            op.add_column("orders", sa.Column(name, sa.UUID(), nullable=True))
            fk_name = f"orders_{name}_fkey"
            if has_users and fk_name not in existing_fks:
                op.create_foreign_key(fk_name, "orders", "users", [name], ["id"], ondelete="CASCADE")

    # ── 4. line_items: ensure table, backfill from JSONB BEFORE dropping it ──
    if "line_items" not in set(_insp(conn).get_table_names()):
        op.create_table(
            "line_items",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("order_id", sa.UUID(), nullable=False),
            sa.Column("category_slug", sa.String(), nullable=True),
            sa.Column("quantity", sa.Integer(), nullable=True),
            sa.Column("weight_g", sa.Integer(), nullable=True),
            sa.Column("hs_code", sa.String(), nullable=True),
            sa.Column("value_minor", sa.Integer(), nullable=True),
            sa.Column("dimensions", postgresql.JSONB(), nullable=True),
            sa.Column("prohibited_flags", postgresql.JSONB(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    cols = _columns(conn, "orders")
    if "line_items" in cols:  # backend-core JSONB column still present
        rows = conn.execute(sa.text("SELECT id, line_items FROM orders")).mappings()
        for row in rows:
            for item in row["line_items"] or []:
                conn.execute(
                    sa.text(
                        "INSERT INTO line_items "
                        "(order_id, category_slug, quantity, weight_g, hs_code, value_minor, "
                        "dimensions, prohibited_flags) "
                        "VALUES (:order_id, NULL, :quantity, NULL, :hs_code, :value_minor, NULL, NULL)"
                    ),
                    {
                        "order_id": row["id"],
                        "quantity": item.get("quantity"),
                        "hs_code": item.get("hsn_code"),
                        "value_minor": item.get("total_minor"),
                    },
                )

    # ── 5. drop backend-core-only columns ────────────────────────────────────
    existing_fks = {fk["name"] for fk in _insp(conn).get_foreign_keys("orders")}
    if "fk_orders_doc_pack_id" in existing_fks:
        op.drop_constraint("fk_orders_doc_pack_id", "orders", type_="foreignkey")
    cols = _columns(conn, "orders")
    for name in ("doc_pack_id", *_BC_ONLY_COLUMNS):
        if name in cols:
            op.drop_column("orders", name)
    if "line_items" in cols:  # JSONB column (already unfolded into line_items rows)
        op.drop_column("orders", "line_items")

    # ── 6. type & nullability alignment (no-op when already unified) ─────────
    def _align_int(name: str) -> None:
        col = _columns(conn, "orders").get(name)
        base, _ = _base_and_length(col)
        if base != "INTEGER":
            op.alter_column(
                "orders",
                name,
                existing_type=col["type"],
                type_=sa.Integer(),
                postgresql_using=f"round({name})",
            )
        if col["nullable"] is False:
            _drop_not_null(conn, "orders", name)

    def _align_varchar(name: str, length: int, *, truncate: bool = False) -> None:
        col = _columns(conn, "orders").get(name)
        base, current_len = _base_and_length(col)
        if base != "VARCHAR" or current_len != length:
            op.alter_column(
                "orders",
                name,
                existing_type=col["type"],
                type_=sa.String(length=length),
                postgresql_using=f"left({name}, {length})" if truncate else None,
            )
        if col["nullable"] is False:
            _drop_not_null(conn, "orders", name)

    def _align_nullable(name: str) -> None:
        col = _columns(conn, "orders").get(name)
        if col is not None and col["nullable"] is False:
            _drop_not_null(conn, "orders", name)

    _align_int("net_weight_g")
    _align_int("gross_weight_g")
    _align_varchar("destination_country", 64)
    _align_varchar("consignee", 256)
    _align_varchar("iec", 16)
    _align_varchar("bank_name", 128)
    _align_varchar("ifsc", 16)
    _align_varchar("exporter_name", 256)
    _align_varchar("exporter_address", 512)
    _align_varchar("state_code", 2, truncate=True)
    _align_nullable("value_minor")

    # ── 7. backfill unified defaults ─────────────────────────────────────────
    conn.execute(sa.text("UPDATE orders SET version = 1 WHERE version IS NULL"))
    conn.execute(
        sa.text("UPDATE orders SET validation_state = 'incomplete' WHERE validation_state IS NULL")
    )

    # ── 8. drop backend-core doc_packs (validation-engine owns `documents`) ──
    if "doc_packs" in set(_insp(conn).get_table_names()):
        op.drop_table("doc_packs")

    # ── 9. documents.order_id → orders.id (immutable doc rows) ───────────────
    if "documents" in set(_insp(conn).get_table_names()):
        doc_cols = _columns(conn, "documents")
        if "order_id" not in doc_cols:
            op.add_column("documents", sa.Column("order_id", sa.UUID(), nullable=True))
            op.create_foreign_key(
                "documents_order_id_fkey",
                "documents",
                "orders",
                ["order_id"],
                ["id"],
                ondelete="CASCADE",
            )


def downgrade() -> None:
    """Best-effort reverse. Data lossy by design: the encrypted legacy columns,
    the JSONB line_items blob and the doc_packs rows cannot be reconstructed."""
    conn = op.get_bind()

    # 1. documents.order_id
    if "documents" in set(_insp(conn).get_table_names()):
        doc_cols = _columns(conn, "documents")
        if "order_id" in doc_cols:
            fks = {fk["name"] for fk in _insp(conn).get_foreign_keys("documents")}
            if "documents_order_id_fkey" in fks:
                op.drop_constraint("documents_order_id_fkey", "documents", type_="foreignkey")
            op.drop_column("documents", "order_id")

    # 2. order_status enum: lifecycle → workflow
    current_status = _enum_values(conn, "order_status")
    if current_status is not None and "created" not in current_status:
        _swap_status_enum(
            conn,
            current_status,
            list(_WORKFLOW_TO_LIFECYCLE),
            _LIFECYCLE_TO_WORKFLOW,
            default="created",
        )
        op.execute(sa.text("ALTER TABLE orders ALTER COLUMN status SET DEFAULT 'created'::order_status"))

    # 3. drop the normalized line_items table (data lossy)
    if "line_items" in set(_insp(conn).get_table_names()):
        op.drop_table("line_items")

    # 4. re-add backend-core columns as nullable (data unrecoverable)
    cols = _columns(conn, "orders")
    legacy_columns = [
        ("doc_pack_id", sa.UUID()),
        ("profile_version", sa.Integer()),
        ("profile_snapshot_encrypted", postgresql.JSONB()),
        ("ad_code_encrypted", postgresql.JSONB()),
        ("bank_account_encrypted", postgresql.JSONB()),
        ("line_items", postgresql.JSONB()),
    ]
    for name, col_type in legacy_columns:
        if name not in cols:
            op.add_column("orders", sa.Column(name, col_type, nullable=True))

    # 5. drop unified-only columns
    cols = _columns(conn, "orders")
    for name in ("last_report", "version", "quote_id", "bank_account", "ad_code", "gstin", "validation_state"):
        if name in cols:
            op.drop_column("orders", name)

    # 6. recreate the empty doc_packs table + deferred orders FK (schema shape
    #    restored; row content is not recoverable)
    if "doc_packs" not in set(_insp(conn).get_table_names()):
        op.create_table(
            "doc_packs",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("order_id", sa.UUID(), nullable=False),
            sa.Column("ci_json", postgresql.JSONB(), nullable=False),
            sa.Column("pl_json", postgresql.JSONB(), nullable=False),
            sa.Column("cn_json", postgresql.JSONB(), nullable=False),
            sa.Column("pbe_json", postgresql.JSONB(), nullable=False),
            sa.Column("rendered_pdf_path", sa.String(), nullable=True),
            sa.Column("qr_image_path", sa.String(), nullable=True),
            sa.Column(
                "generated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("order_id"),
        )
    cols = _columns(conn, "orders")
    fks = {fk["name"] for fk in _insp(conn).get_foreign_keys("orders")}
    if "doc_pack_id" in cols and "fk_orders_doc_pack_id" not in fks:
        op.create_foreign_key("fk_orders_doc_pack_id", "orders", "doc_packs", ["doc_pack_id"], ["id"])
