"""
Add duplicate merging tables

Creates tables for:
- merge_history: Track profile merge operations with data lineage and undo capability
- duplicate_reviews: Manual review queue for potential duplicate candidates
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260321_add_duplicate_merging_tables"
down_revision: Union[str, None] = "20260221_add_skill_hierarchy_and_relationships"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create merge_history table
    op.create_table(
        "merge_history",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_resume_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resumes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "target_resume_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resumes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "merged_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "merge_timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("merge_data", postgresql.JSON(), nullable=True),
        sa.Column("undo_data", postgresql.JSON(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("can_undo", sa.Boolean(), nullable=False, server_default="true"),
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
        comment="Track profile merge operations with data lineage and undo capability",
    )
    op.create_index(op.f("ix_merge_history_organization_id"), "merge_history", ["organization_id"])
    op.create_index(op.f("ix_merge_history_source_resume_id"), "merge_history", ["source_resume_id"])
    op.create_index(op.f("ix_merge_history_target_resume_id"), "merge_history", ["target_resume_id"])
    op.create_index(op.f("ix_merge_history_merged_by_user_id"), "merge_history", ["merged_by_user_id"])
    op.create_index(op.f("ix_merge_history_merge_timestamp"), "merge_history", ["merge_timestamp"])

    # Create duplicate_reviews table
    op.create_table(
        "duplicate_reviews",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "original_resume_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resumes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "duplicate_resume_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resumes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column(
            "assigned_reviewer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "queue_entered_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "review_started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "review_completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column(
            "batch_job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("batch_jobs.id", ondelete="SET NULL"),
            nullable=True,
        ),
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
        comment="Manual review queue for potential duplicate candidates",
    )
    op.create_index(op.f("ix_duplicate_reviews_organization_id"), "duplicate_reviews", ["organization_id"])
    op.create_index(op.f("ix_duplicate_reviews_original_resume_id"), "duplicate_reviews", ["original_resume_id"])
    op.create_index(op.f("ix_duplicate_reviews_duplicate_resume_id"), "duplicate_reviews", ["duplicate_resume_id"])
    op.create_index(op.f("ix_duplicate_reviews_confidence_score"), "duplicate_reviews", ["confidence_score"])
    op.create_index(op.f("ix_duplicate_reviews_status"), "duplicate_reviews", ["status"])
    op.create_index(op.f("ix_duplicate_reviews_assigned_reviewer_id"), "duplicate_reviews", ["assigned_reviewer_id"])
    op.create_index(op.f("ix_duplicate_reviews_queue_entered_at"), "duplicate_reviews", ["queue_entered_at"])
    op.create_index(op.f("ix_duplicate_reviews_batch_job_id"), "duplicate_reviews", ["batch_job_id"])


def downgrade() -> None:
    # Drop duplicate_reviews table
    op.drop_index(op.f("ix_duplicate_reviews_batch_job_id"), table_name="duplicate_reviews")
    op.drop_index(op.f("ix_duplicate_reviews_queue_entered_at"), table_name="duplicate_reviews")
    op.drop_index(op.f("ix_duplicate_reviews_assigned_reviewer_id"), table_name="duplicate_reviews")
    op.drop_index(op.f("ix_duplicate_reviews_status"), table_name="duplicate_reviews")
    op.drop_index(op.f("ix_duplicate_reviews_confidence_score"), table_name="duplicate_reviews")
    op.drop_index(op.f("ix_duplicate_reviews_duplicate_resume_id"), table_name="duplicate_reviews")
    op.drop_index(op.f("ix_duplicate_reviews_original_resume_id"), table_name="duplicate_reviews")
    op.drop_index(op.f("ix_duplicate_reviews_organization_id"), table_name="duplicate_reviews")
    op.drop_table("duplicate_reviews")

    # Drop merge_history table
    op.drop_index(op.f("ix_merge_history_merge_timestamp"), table_name="merge_history")
    op.drop_index(op.f("ix_merge_history_merged_by_user_id"), table_name="merge_history")
    op.drop_index(op.f("ix_merge_history_target_resume_id"), table_name="merge_history")
    op.drop_index(op.f("ix_merge_history_source_resume_id"), table_name="merge_history")
    op.drop_index(op.f("ix_merge_history_organization_id"), table_name="merge_history")
    op.drop_table("merge_history")
