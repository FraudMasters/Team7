"""
Add batch_jobs table

Creates table for:
- batch_jobs: Store batch resume processing operations with progress tracking
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "005_add_batch_jobs"
down_revision: Union[str, None] = "004_add_analytics_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create batch_jobs table
    op.create_table(
        "batch_jobs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("total_files", sa.Integer(), nullable=False),
        sa.Column("processed_files", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed_files", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "processing", "completed", "failed", name="batchjobstatus"),
            nullable=False,
            default="pending",
        ),
        sa.Column("notification_email", sa.String(255), nullable=True),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        comment="Store batch resume processing operations with progress tracking",
    )
    op.create_index(op.f("ix_batch_jobs_status"), "batch_jobs", ["status"])


def downgrade() -> None:
    # Drop batch_jobs table
    op.drop_index(op.f("ix_batch_jobs_status"), table_name="batch_jobs")
    op.drop_table("batch_jobs")

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS batchjobstatus")
