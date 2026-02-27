"""add text content for entries

Revision ID: 0006_entry_text_content
Revises: 0005_entry_freeze_flag
Create Date: 2026-02-27
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0006_entry_text_content"
down_revision: Union[str, None] = "0005_entry_freeze_flag"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("entries", sa.Column("text_content", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("entries", "text_content")
