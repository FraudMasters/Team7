"""
Add LinkedIn integration tables

Creates tables for:
- linkedin_profiles: Store imported LinkedIn profile data and sync status
- linkedin_imports: Track LinkedIn candidate import history and operations
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260203_add_linkedin_integration"
down_revision: Union[str, None] = "20260201_add_search_performance_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create linkedin_profiles table
    op.create_table(
        "linkedin_profiles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("linkedin_id", sa.String(100), nullable=False, unique=True),
        sa.Column("linkedin_url", sa.String(512), nullable=False, unique=True),
        sa.Column("first_name", sa.String(255), nullable=True),
        sa.Column("last_name", sa.String(255), nullable=True),
        sa.Column("headline", sa.Text(), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("profile_picture_url", sa.String(512), nullable=True),
        sa.Column("skills", postgresql.JSONB(), nullable=True),
        sa.Column("experience", postgresql.JSONB(), nullable=True),
        sa.Column("education", postgresql.JSONB(), nullable=True),
        sa.Column("raw_profile_data", postgresql.JSONB(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "PROCESSING",
                "COMPLETED",
                "FAILED",
                "SYNCED",
                "OUTDATED",
                "ARCHIVED",
                name="linkedinprofilestatus",
            ),
            nullable=False,
            default="PENDING",
        ),
        sa.Column("last_synced_at", sa.String(50), nullable=True),
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
        comment="Store imported LinkedIn profile data and synchronization status",
    )
    op.create_index(op.f("ix_linkedin_profiles_linkedin_id"), "linkedin_profiles", ["linkedin_id"])
    op.create_index(op.f("ix_linkedin_profiles_status"), "linkedin_profiles", ["status"])

    # Create linkedin_imports table
    op.create_table(
        "linkedin_imports",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("status", sa.String(50), nullable=False, default="pending"),
        sa.Column(
            "recruiter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recruiters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "vacancy_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_vacancies.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("source_type", sa.String(100), nullable=True),
        sa.Column("search_params", postgresql.JSON(), nullable=True),
        sa.Column("total_candidates", sa.Integer(), nullable=True),
        sa.Column("successful_imports", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("failed_imports", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("linkedin_search_url", sa.Text(), nullable=True),
        sa.Column("import_metadata", postgresql.JSON(), nullable=True),
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
        comment="Track LinkedIn candidate import history and operations",
    )
    op.create_index(op.f("ix_linkedin_imports_recruiter_id"), "linkedin_imports", ["recruiter_id"])
    op.create_index(op.f("ix_linkedin_imports_vacancy_id"), "linkedin_imports", ["vacancy_id"])
    op.create_index(op.f("ix_linkedin_imports_status"), "linkedin_imports", ["status"])


def downgrade() -> None:
    # Drop linkedin_imports table
    op.drop_index(op.f("ix_linkedin_imports_status"), table_name="linkedin_imports")
    op.drop_index(op.f("ix_linkedin_imports_vacancy_id"), table_name="linkedin_imports")
    op.drop_index(op.f("ix_linkedin_imports_recruiter_id"), table_name="linkedin_imports")
    op.drop_table("linkedin_imports")

    # Drop linkedin_profiles table
    op.drop_index(op.f("ix_linkedin_profiles_status"), table_name="linkedin_profiles")
    op.drop_index(op.f("ix_linkedin_profiles_linkedin_id"), table_name="linkedin_profiles")
    op.drop_table("linkedin_profiles")

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS linkedinprofilestatus")
