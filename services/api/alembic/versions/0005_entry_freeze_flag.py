"""add freeze flag for entries

Revision ID: 0005_entry_freeze_flag
Revises: 0004_entry_audio_metadata
Create Date: 2026-02-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0005_entry_freeze_flag"
down_revision: Union[str, None] = "0004_entry_audio_metadata"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "entries",
        sa.Column(
            "is_frozen", sa.Boolean(), nullable=False, server_default=sa.text("0")
        ),
    )


def downgrade() -> None:
    op.drop_column("entries", "is_frozen")
