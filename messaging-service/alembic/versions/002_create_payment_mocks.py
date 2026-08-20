"""002 create payment_mocks — internal mock payments replacing pay.mock.

Revision ID: 002
Revises: 001
Create Date: 2026-08-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "payment_mocks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("quote_id", UUID(as_uuid=True), sa.ForeignKey("quote_states.quote_id", ondelete="SET NULL"), nullable=True),
        sa.Column("order_id", UUID(as_uuid=True), nullable=True),
        sa.Column("thread_id", UUID(as_uuid=True), nullable=True),
        sa.Column("amount_minor", sa.Integer, nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="initiated"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_payment_mocks_quote_id", "payment_mocks", ["quote_id"])
    op.create_index("ix_payment_mocks_order_id", "payment_mocks", ["order_id"])
    op.create_index("ix_payment_mocks_thread_id", "payment_mocks", ["thread_id"])


def downgrade() -> None:
    op.drop_table("payment_mocks")
