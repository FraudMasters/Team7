"""
Initial database schema for Resume Processing Service

Creates tables for:
- resumes: Store uploaded resume files and metadata
- analysis_results: Store NLP/ML analysis results
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create resumestatus enum type
    op.execute(
        "CREATE TYPE resumestatus AS ENUM "
        "('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', "
        "'NEW', 'REVIEWED', 'INTERVIEW', 'OFFERED', 'HIRED')"
    )

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
            sa.Enum(
                "PENDING",
                "PROCESSING",
                "COMPLETED",
                "FAILED",
                "NEW",
                "REVIEWED",
                "INTERVIEW",
                "OFFERED",
                "HIRED",
                name="resumestatus",
            ),
            nullable=False,
            default="PENDING",
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
    op.create_index("ix_resumes_status", "resumes", ["status"])

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


def downgrade() -> None:
    # Drop analysis_results table
    op.drop_table("analysis_results")

    # Drop resumes table
    op.drop_index("ix_resumes_status", table_name="resumes")
    op.drop_table("resumes")

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS resumestatus")
