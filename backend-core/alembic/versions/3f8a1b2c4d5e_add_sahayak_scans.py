"""add sahayak_scans

Revision ID: 3f8a1b2c4d5e
Revises: 2ae521447228
Create Date: 2026-08-20

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "3f8a1b2c4d5e"
down_revision: str | Sequence[str] | None = "2ae521447228"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sahayak_scans",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("sahayak_user_id", sa.UUID(), nullable=False),
        sa.Column("order_id", sa.String(length=64), nullable=False),
        sa.Column(
            "scanned_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("lane_meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["sahayak_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sahayak_scans_sahayak_user_id", "sahayak_scans", ["sahayak_user_id"])
    op.create_index("ix_sahayak_scans_order_id", "sahayak_scans", ["order_id"])
    op.create_index("ix_sahayak_scans_scanned_at", "sahayak_scans", ["scanned_at"])


def downgrade() -> None:
    op.drop_index("ix_sahayak_scans_scanned_at", table_name="sahayak_scans")
    op.drop_index("ix_sahayak_scans_order_id", table_name="sahayak_scans")
    op.drop_index("ix_sahayak_scans_sahayak_user_id", table_name="sahayak_scans")
    op.drop_table("sahayak_scans")
