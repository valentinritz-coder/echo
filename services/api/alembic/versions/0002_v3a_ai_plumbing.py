"""v3.a ai db + api plumbing

Revision ID: 0002_v3a_ai_plumbing
Revises: 0001_init
Create Date: 2026-02-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_v3a_ai_plumbing"
down_revision: Union[str, None] = "0001_init"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


AI_STATUS_CHECK = "ai_status IN ('none','pending','running','done','error')"
AI_RUN_STATUS_CHECK = "status IN ('pending','running','done','error')"


def upgrade() -> None:
    op.create_table(
        "ai_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("entry_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tasks_json", sa.Text(), nullable=False),
        sa.Column("pipeline_version", sa.String(), nullable=False),
        sa.Column("audio_sha256", sa.String(length=64), nullable=True),
        sa.Column("stt_model", sa.String(), nullable=True),
        sa.Column("llm_model", sa.String(), nullable=True),
        sa.Column("transcript_text", sa.Text(), nullable=True),
        sa.Column("transcript_json", sa.Text(), nullable=True),
        sa.Column("summary_text", sa.Text(), nullable=True),
        sa.Column("keypoints_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metrics_json", sa.Text(), nullable=True),
        sa.CheckConstraint(AI_RUN_STATUS_CHECK, name="ck_ai_runs_status"),
        sa.ForeignKeyConstraint(["entry_id"], ["entries.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_runs_entry_id", "ai_runs", ["entry_id"], unique=False)
    op.create_index("ix_ai_runs_status_requested_at", "ai_runs", ["status", "requested_at"], unique=False)

    with op.batch_alter_table("entries", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("ai_status", sa.String(), nullable=False, server_default="none"))
        batch_op.add_column(sa.Column("ai_last_run_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("ai_updated_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("audio_sha256", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("audio_duration_sec", sa.Float(), nullable=True))
        batch_op.create_check_constraint("ck_entries_ai_status", AI_STATUS_CHECK)
        batch_op.create_foreign_key("fk_entries_ai_last_run_id", "ai_runs", ["ai_last_run_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    with op.batch_alter_table("entries", recreate="always") as batch_op:
        batch_op.drop_constraint("fk_entries_ai_last_run_id", type_="foreignkey")
        batch_op.drop_constraint("ck_entries_ai_status", type_="check")
        batch_op.drop_column("audio_duration_sec")
        batch_op.drop_column("audio_sha256")
        batch_op.drop_column("ai_updated_at")
        batch_op.drop_column("ai_last_run_id")
        batch_op.drop_column("ai_status")

    op.drop_index("ix_ai_runs_status_requested_at", table_name="ai_runs")
    op.drop_index("ix_ai_runs_entry_id", table_name="ai_runs")
    op.drop_table("ai_runs")
