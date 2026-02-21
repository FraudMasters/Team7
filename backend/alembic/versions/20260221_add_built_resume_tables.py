"""Add built_resume tables

Creates table for:
- built_resumes: Store resumes created by job seekers using the resume builder
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260221_add_built_resume_tables"
down_revision: Union[str, None] = "20260212_add_parsing_correction_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create built_resumes table
    op.create_table(
        "built_resumes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String(255),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            comment="User that owns this resume",
        ),
        sa.Column(
            "organization_id",
            sa.String(255),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
            comment="Organization that this resume belongs to",
        ),
        sa.Column(
            "template_id",
            sa.String(255),
            sa.ForeignKey("resume_templates.id", ondelete="SET NULL"),
            nullable=True,
            comment="Template to use for rendering this resume",
        ),
        sa.Column(
            "title",
            sa.String(255),
            nullable=False,
            comment="Name/title of this resume",
        ),
        sa.Column(
            "content",
            postgresql.JSON(),
            nullable=False,
            server_default="{}",
            comment="JSON structure containing all resume sections (personal_info, summary, work_experience, education, skills, etc.)",
        ),
        sa.Column(
            "target_job_id",
            sa.String(255),
            sa.ForeignKey("job_vacancies.id", ondelete="SET NULL"),
            nullable=True,
            comment="Optional job vacancy ID for skill gap analysis",
        ),
        sa.Column(
            "ats_score",
            sa.Integer(),
            nullable=True,
            comment="Current ATS optimization score (0-100)",
        ),
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
            server_default="1",
            comment="Version number of this resume",
        ),
        sa.Column(
            "is_draft",
            sa.Boolean(),
            nullable=False,
            server_default="true",
            comment="Whether this is a draft or published resume",
        ),
        sa.Column(
            "last_ai_suggestions",
            postgresql.JSON(),
            nullable=True,
            comment="JSON field storing recent AI improvement suggestions",
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
        comment="Store resumes created by job seekers using the resume builder",
    )
    op.create_index(op.f("ix_built_resumes_user_id"), "built_resumes", ["user_id"])
    op.create_index(op.f("ix_built_resumes_organization_id"), "built_resumes", ["organization_id"])
    op.create_index(op.f("ix_built_resumes_template_id"), "built_resumes", ["template_id"])
    op.create_index(op.f("ix_built_resumes_target_job_id"), "built_resumes", ["target_job_id"])


def downgrade() -> None:
    # Drop built_resumes table
    op.drop_index(op.f("ix_built_resumes_target_job_id"), table_name="built_resumes")
    op.drop_index(op.f("ix_built_resumes_template_id"), table_name="built_resumes")
    op.drop_index(op.f("ix_built_resumes_organization_id"), table_name="built_resumes")
    op.drop_index(op.f("ix_built_resumes_user_id"), table_name="built_resumes")
    op.drop_table("built_resumes")
