"""
Initial database schema for Resume Analysis System

Creates tables for:
- resumes: Store uploaded resume files and metadata
- analysis_results: Store NLP/ML analysis results
- job_vacancies: Store job descriptions for matching
- match_results: Store resume-to-vacancy match results
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create resumes table
    op.create_table(
        "resumes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "processing", "completed", "failed", name="resumestatus"),
            nullable=False,
            default="pending",
        ),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("language", sa.String(10), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
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
        comment="Store uploaded resume files and processing metadata",
    )
    op.create_index(op.f("ix_resumes_status"), "resumes", ["status"])

    # Create analysis_results table
    op.create_table(
        "analysis_results",
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
            unique=True,
        ),
        sa.Column("errors", postgresql.JSON(), nullable=True),
        sa.Column("skills", postgresql.JSON(), nullable=True),
        sa.Column("experience_summary", postgresql.JSON(), nullable=True),
        sa.Column("recommendations", postgresql.JSON(), nullable=True),
        sa.Column("keywords", postgresql.JSON(), nullable=True),
        sa.Column("entities", postgresql.JSON(), nullable=True),
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
        comment="Store NLP/ML analysis results for resumes",
    )

    # Create job_vacancies table
    op.create_table(
        "job_vacancies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "required_skills", postgresql.JSON(), nullable=False, server_default="[]"
        ),
        sa.Column("min_experience_months", sa.Integer(), nullable=True),
        sa.Column(
            "additional_requirements", postgresql.JSON(), nullable=True, server_default="[]"
        ),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("work_format", sa.String(50), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("source", sa.String(50), nullable=True),
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
        comment="Store job vacancy descriptions for matching",
    )
    op.create_index(op.f("ix_job_vacancies_external_id"), "job_vacancies", ["external_id"])

    # Create match_results table
    op.create_table(
        "match_results",
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
            sa.ForeignKey("job_vacancies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("match_percentage", sa.Numeric(5, 2), nullable=False, server_default="0.0"),
        sa.Column("matched_skills", postgresql.JSON(), nullable=True),
        sa.Column("missing_skills", postgresql.JSON(), nullable=True),
        sa.Column("additional_skills_matched", postgresql.JSON(), nullable=True),
        sa.Column("experience_verified", sa.Boolean(), nullable=True),
        sa.Column("experience_details", postgresql.JSON(), nullable=True),
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
        comment="Store resume-to-vacancy matching results",
    )
    op.create_index(op.f("ix_match_results_resume_id"), "match_results", ["resume_id"])
    op.create_index(op.f("ix_match_results_vacancy_id"), "match_results", ["vacancy_id"])


def downgrade() -> None:
    # Drop match_results table
    op.drop_index(op.f("ix_match_results_vacancy_id"), table_name="match_results")
    op.drop_index(op.f("ix_match_results_resume_id"), table_name="match_results")
    op.drop_table("match_results")

    # Drop job_vacancies table
    op.drop_index(op.f("ix_job_vacancies_external_id"), table_name="job_vacancies")
    op.drop_table("job_vacancies")

    # Drop analysis_results table
    op.drop_table("analysis_results")

    # Drop resumes table
    op.drop_index(op.f("ix_resumes_status"), table_name="resumes")
    op.drop_table("resumes")

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS resumestatus")
