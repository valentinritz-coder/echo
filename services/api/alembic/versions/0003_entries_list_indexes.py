"""add entries list pagination indexes

Revision ID: 0003_entries_list_indexes
Revises: 0002_users_and_auth
Create Date: 2026-02-24
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_entries_list_indexes"
down_revision: Union[str, None] = "0002_users_and_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_entries_user_id_created_at_id",
        "entries",
        ["user_id", "created_at", "id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_entries_user_id_created_at_id", table_name="entries")
