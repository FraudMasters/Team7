"""
Add score_appeals table

Creates table for:
- score_appeals: Candidate appeals against AI scoring decisions with tracking and resolution
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "008_add_score_appeals"
down_revision: Union[str, None] = "007_add_resume_search"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create score_appeals table
    op.create_table(
        "score_appeals",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "match_result_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("match_results.id", ondelete="CASCADE"),
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
            sa.ForeignKey("job_vacancies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("appeal_reason", sa.String(50), nullable=False),
        sa.Column("candidate_explanation", sa.Text(), nullable=False),
        sa.Column("candidate_email", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("original_score", sa.Float(), nullable=False),
        sa.Column("reviewed_by", sa.String(255), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("adjusted_score", sa.Float(), nullable=True),
        sa.Column("metadata", postgresql.JSON(), nullable=True),
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
        comment="Candidate appeals against AI scoring decisions with tracking and resolution",
    )
    op.create_index(op.f("ix_score_appeals_match_result_id"), "score_appeals", ["match_result_id"])
    op.create_index(op.f("ix_score_appeals_resume_id"), "score_appeals", ["resume_id"])
    op.create_index(op.f("ix_score_appeals_vacancy_id"), "score_appeals", ["vacancy_id"])


def downgrade() -> None:
    # Drop score_appeals table
    op.drop_index(op.f("ix_score_appeals_vacancy_id"), table_name="score_appeals")
    op.drop_index(op.f("ix_score_appeals_resume_id"), table_name="score_appeals")
    op.drop_index(op.f("ix_score_appeals_match_result_id"), table_name="score_appeals")
    op.drop_table("score_appeals")
