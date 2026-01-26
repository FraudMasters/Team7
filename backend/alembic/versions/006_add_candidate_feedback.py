"""
Add candidate feedback tables

Creates tables for:
- candidate_feedback: Store constructive feedback for candidates with grammar, skills, and experience analysis
- feedback_templates: Store customizable feedback templates for recruiters
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "006_add_candidate_feedback"
down_revision: Union[str, None] = "005_add_batch_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create feedback_templates table
    op.create_table(
        "feedback_templates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("organization_id", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("language", sa.String(10), nullable=False, server_default="en"),
        sa.Column("tone", sa.String(50), nullable=False, server_default="constructive"),
        sa.Column("sections", postgresql.JSON(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_by", sa.String(255), nullable=True),
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
        comment="Store customizable feedback templates for recruiters",
    )
    op.create_index(
        op.f("ix_feedback_templates_organization_id"), "feedback_templates", ["organization_id"]
    )

    # Create candidate_feedback table
    op.create_table(
        "candidate_feedback",
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
            "match_result_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("match_results.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("feedback_templates.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("language", sa.String(10), nullable=False, server_default="en"),
        sa.Column("grammar_feedback", postgresql.JSON(), nullable=True),
        sa.Column("skills_feedback", postgresql.JSON(), nullable=True),
        sa.Column("experience_feedback", postgresql.JSON(), nullable=True),
        sa.Column("recommendations", postgresql.JSON(), nullable=True),
        sa.Column("match_score", sa.Integer(), nullable=True),
        sa.Column("tone", sa.String(50), nullable=False, server_default="constructive"),
        sa.Column("feedback_source", sa.String(50), nullable=False, server_default="automated"),
        sa.Column("viewed_by_candidate", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("downloaded", sa.Boolean(), nullable=False, server_default="false"),
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
        comment="Store constructive feedback for candidates with grammar, skills, and experience analysis",
    )
    op.create_index(op.f("ix_candidate_feedback_resume_id"), "candidate_feedback", ["resume_id"])
    op.create_index(op.f("ix_candidate_feedback_vacancy_id"), "candidate_feedback", ["vacancy_id"])


def downgrade() -> None:
    # Drop candidate_feedback table
    op.drop_index(op.f("ix_candidate_feedback_vacancy_id"), table_name="candidate_feedback")
    op.drop_index(op.f("ix_candidate_feedback_resume_id"), table_name="candidate_feedback")
    op.drop_table("candidate_feedback")

    # Drop feedback_templates table
    op.drop_index(
        op.f("ix_feedback_templates_organization_id"), table_name="feedback_templates"
    )
    op.drop_table("feedback_templates")
