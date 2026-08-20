"""001 create messaging + quote tables — namespaced, no FK to orders.

Revision ID: 001
Revises:
Create Date: 2026-08-20

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "messaging_threads",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", UUID(as_uuid=True), nullable=False),
        sa.Column("seller_id", UUID(as_uuid=True), nullable=False),
        sa.Column("buyer_id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_preview_encrypted", sa.Text, nullable=True),
    )
    op.create_index("ix_messaging_threads_order_id", "messaging_threads", ["order_id"], unique=True)
    op.create_index("ix_messaging_threads_seller_id", "messaging_threads", ["seller_id"])
    op.create_index("ix_messaging_threads_buyer_id", "messaging_threads", ["buyer_id"])

    op.create_table(
        "messaging_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "thread_id",
            UUID(as_uuid=True),
            sa.ForeignKey("messaging_threads.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sender_id", UUID(as_uuid=True), nullable=False),
        sa.Column("sender_role", sa.String(16), nullable=False),
        sa.Column("body_ciphertext", sa.Text, nullable=False),
        sa.Column("enc_nonce_b64", sa.String(64), nullable=False),
        sa.Column("attachments", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_messaging_messages_thread_id", "messaging_messages", ["thread_id"])
    op.create_index("ix_messaging_messages_sender_id", "messaging_messages", ["sender_id"])

    op.create_table(
        "quote_states",
        sa.Column("quote_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", UUID(as_uuid=True), nullable=False),
        sa.Column("thread_id", UUID(as_uuid=True), nullable=True),
        sa.Column("seller_id", UUID(as_uuid=True), nullable=False),
        sa.Column("buyer_id", UUID(as_uuid=True), nullable=False),
        sa.Column("current_version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("state", sa.String(16), nullable=False, server_default="draft"),
        sa.Column("amount_minor", sa.Integer, nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("qty", sa.Integer, nullable=True),
        sa.Column("shipping_minor", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "state IN ('draft','sent','counter','approved','paid_held')",
            name="ck_quote_states_state_enum",
        ),
    )
    op.create_index("ix_quote_states_order_id", "quote_states", ["order_id"], unique=True)
    op.create_index("ix_quote_states_thread_id", "quote_states", ["thread_id"], unique=True)

    op.create_table(
        "quote_versions",
        sa.Column(
            "quote_id",
            UUID(as_uuid=True),
            sa.ForeignKey("quote_states.quote_id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("version", sa.Integer, primary_key=True, nullable=False),
        sa.Column("price_minor", sa.Integer, nullable=False),
        sa.Column("qty", sa.Integer, nullable=True),
        sa.Column("shipping_minor", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("quote_versions")
    op.drop_table("quote_states")
    op.drop_table("messaging_messages")
    op.drop_table("messaging_threads")
