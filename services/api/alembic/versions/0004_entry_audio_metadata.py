"""add entry audio hash and duration columns

Revision ID: 0004_entry_audio_metadata
Revises: 0003_entries_list_indexes
Create Date: 2026-02-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0004_entry_audio_metadata"
down_revision: Union[str, None] = "0003_entries_list_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "entries",
        sa.Column("audio_sha256", sa.String(length=64), nullable=False, server_default="0" * 64),
    )
    op.add_column("entries", sa.Column("audio_duration_ms", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("entries", "audio_duration_ms")
    op.drop_column("entries", "audio_sha256")
