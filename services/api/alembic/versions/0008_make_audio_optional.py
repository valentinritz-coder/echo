"""make entry audio metadata optional

Revision ID: 0008_make_audio_optional
Revises: 0007_entry_assets
Create Date: 2026-02-28
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0008_make_audio_optional"
down_revision: Union[str, None] = "0007_entry_assets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("entries") as batch_op:
        batch_op.alter_column("audio_path", existing_type=sa.String(), nullable=True)
        batch_op.alter_column("audio_mime", existing_type=sa.String(), nullable=True)
        batch_op.alter_column("audio_size", existing_type=sa.Integer(), nullable=True)
        batch_op.alter_column(
            "audio_sha256", existing_type=sa.String(length=64), nullable=True
        )


def downgrade() -> None:
    bind = op.get_bind()
    null_count = bind.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM entries
            WHERE audio_path IS NULL
               OR audio_mime IS NULL
               OR audio_size IS NULL
               OR audio_sha256 IS NULL
            """
        )
    ).scalar_one()
    if null_count:
        raise RuntimeError(
            "Cannot downgrade 0008_make_audio_optional: entries contain rows without audio metadata."
        )

    with op.batch_alter_table("entries") as batch_op:
        batch_op.alter_column(
            "audio_sha256", existing_type=sa.String(length=64), nullable=False
        )
        batch_op.alter_column("audio_size", existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column("audio_mime", existing_type=sa.String(), nullable=False)
        batch_op.alter_column("audio_path", existing_type=sa.String(), nullable=False)
