"""
Add candidate review queue tables

Creates tables for:
- candidate_queue_items: Store candidates in review queue with priority, status, and assignment tracking
- Adds queue-related columns to hiring_stages: priority, assigned_recruiter_id, queue_entered_at
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "021_add_candidate_review_queue"
down_revision: Union[str, None] = "20260212_add_parsing_correction_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types for queue priority and status
    queue_priority_enum = postgresql.ENUM(
        "urgent", "high", "medium", "low", name="queuepriority", create_type=False
    )
    queue_priority_enum.create(op.get_bind(), checkfirst=True)

    queue_status_enum = postgresql.ENUM(
        "pending", "in_review", "completed", "skipped", name="queuestatus", create_type=False
    )
    queue_status_enum.create(op.get_bind(), checkfirst=True)

    # Create candidate_queue_items table
    op.create_table(
        "candidate_queue_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "resume_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resumes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "vacancy_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_vacancies.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "priority",
            queue_priority_enum,
            nullable=False,
            server_default="medium",
        ),
        sa.Column(
            "status",
            queue_status_enum,
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "assigned_recruiter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recruiters.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("queue_entered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("review_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
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
        comment="Store candidates in review queue with priority sorting, status tracking, and assignment management",
    )
    op.create_index(op.f("ix_candidate_queue_items_resume_id"), "candidate_queue_items", ["resume_id"])
    op.create_index(op.f("ix_candidate_queue_items_vacancy_id"), "candidate_queue_items", ["vacancy_id"])
    op.create_index(op.f("ix_candidate_queue_items_priority"), "candidate_queue_items", ["priority"])
    op.create_index(op.f("ix_candidate_queue_items_status"), "candidate_queue_items", ["status"])
    op.create_index(
        op.f("ix_candidate_queue_items_assigned_recruiter_id"),
        "candidate_queue_items",
        ["assigned_recruiter_id"],
    )
    op.create_index(
        op.f("ix_candidate_queue_items_queue_entered_at"),
        "candidate_queue_items",
        ["queue_entered_at"],
    )

    # Add queue-related columns to hiring_stages table
    op.add_column(
        "hiring_stages",
        sa.Column("priority", sa.Integer(), nullable=True),
    )
    op.add_column(
        "hiring_stages",
        sa.Column(
            "assigned_recruiter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recruiters.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "hiring_stages",
        sa.Column("queue_entered_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes for new hiring_stages columns
    op.create_index(op.f("ix_hiring_stages_priority"), "hiring_stages", ["priority"])
    op.create_index(
        op.f("ix_hiring_stages_assigned_recruiter_id"), "hiring_stages", ["assigned_recruiter_id"]
    )
    op.create_index(op.f("ix_hiring_stages_queue_entered_at"), "hiring_stages", ["queue_entered_at"])


def downgrade() -> None:
    # Drop indexes from hiring_stages
    op.drop_index(op.f("ix_hiring_stages_queue_entered_at"), table_name="hiring_stages")
    op.drop_index(op.f("ix_hiring_stages_assigned_recruiter_id"), table_name="hiring_stages")
    op.drop_index(op.f("ix_hiring_stages_priority"), table_name="hiring_stages")

    # Drop columns from hiring_stages
    op.drop_column("hiring_stages", "queue_entered_at")
    op.drop_column("hiring_stages", "assigned_recruiter_id")
    op.drop_column("hiring_stages", "priority")

    # Drop candidate_queue_items table indexes
    op.drop_index(
        op.f("ix_candidate_queue_items_queue_entered_at"), table_name="candidate_queue_items"
    )
    op.drop_index(
        op.f("ix_candidate_queue_items_assigned_recruiter_id"),
        table_name="candidate_queue_items",
    )
    op.drop_index(op.f("ix_candidate_queue_items_status"), table_name="candidate_queue_items")
    op.drop_index(op.f("ix_candidate_queue_items_priority"), table_name="candidate_queue_items")
    op.drop_index(op.f("ix_candidate_queue_items_vacancy_id"), table_name="candidate_queue_items")
    op.drop_index(op.f("ix_candidate_queue_items_resume_id"), table_name="candidate_queue_items")
    op.drop_table("candidate_queue_items")

    # Drop enum types
    queue_status_enum = postgresql.ENUM("pending", "in_review", "completed", "skipped", name="queuestatus", create_type=False)
    queue_status_enum.drop(op.get_bind(), checkfirst=True)

    queue_priority_enum = postgresql.ENUM("urgent", "high", "medium", "low", name="queuepriority", create_type=False)
    queue_priority_enum.drop(op.get_bind(), checkfirst=True)
