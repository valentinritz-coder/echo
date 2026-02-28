"""add entry assets table

Revision ID: 0007_entry_assets
Revises: 0006_entry_text_content
Create Date: 2026-02-27
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0007_entry_assets"
down_revision: Union[str, None] = "0006_entry_text_content"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "entry_assets",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("entry_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("asset_type", sa.String(), nullable=False),
        sa.Column("path", sa.String(), nullable=False),
        sa.Column("mime", sa.String(), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["entry_id"], ["entries.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_entry_assets_user_id_created_at_id",
        "entry_assets",
        ["user_id", "created_at", "id"],
        unique=False,
    )
    op.create_index(
        "ix_entry_assets_entry_id_created_at_id",
        "entry_assets",
        ["entry_id", "created_at", "id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_entry_assets_entry_id_created_at_id", table_name="entry_assets")
    op.drop_index("ix_entry_assets_user_id_created_at_id", table_name="entry_assets")
    op.drop_table("entry_assets")
