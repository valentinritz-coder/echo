"""add users and link entries to users

Revision ID: 0002_users_and_auth
Revises: 0001_init
Create Date: 2026-02-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_users_and_auth"
down_revision: Union[str, None] = "0001_init"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.execute(
        sa.text(
            """
            INSERT INTO users (id, email, password_hash, is_active)
            SELECT :id, :email, :password_hash, :is_active
            WHERE EXISTS (SELECT 1 FROM entries)
            """
        ).bindparams(
            id="legacy",
            email="legacy@local",
            password_hash="!",
            is_active=False,
        )
    )

    op.execute(
        sa.text(
            """
            UPDATE entries
            SET user_id = :legacy_id
            WHERE user_id IS NOT NULL
              AND user_id != ''
              AND user_id NOT IN (SELECT id FROM users)
            """
        ).bindparams(legacy_id="legacy")
    )

    with op.batch_alter_table("entries", schema=None) as batch_op:
        batch_op.create_foreign_key(
            "fk_entries_user_id_users", "users", ["user_id"], ["id"]
        )


def downgrade() -> None:
    with op.batch_alter_table("entries", schema=None) as batch_op:
        batch_op.drop_constraint("fk_entries_user_id_users", type_="foreignkey")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
