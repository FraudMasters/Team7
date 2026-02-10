"""Add job application and saved job models

Creates tables for:
- job_applications: Store job applications submitted by job seekers
- saved_jobs: Store jobs bookmarked/saved by job seekers for later viewing
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260210_add_job_application_models"
down_revision: Union[str, None] = "20260208_add_explanation_preferences"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create applicationstatus enum type
    applicationstatus_enum = sa.Enum(
        "PENDING",
        "SUBMITTED",
        "UNDER_REVIEW",
        "REJECTED",
        "ACCEPTED",
        name="applicationstatus",
    )
    applicationstatus_enum.create(op.get_bind(), checkfirst=True)

    # Create job_applications table
    op.create_table(
        "job_applications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "vacancy_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_vacancies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "resume_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resumes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("cover_letter", sa.Text(), nullable=True),
        sa.Column(
            "status",
            applicationstatus_enum,
            nullable=False,
            server_default="PENDING",
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
        comment="Store job applications submitted by job seekers",
    )
    op.create_index(op.f("ix_job_applications_user_id"), "job_applications", ["user_id"])
    op.create_index(op.f("ix_job_applications_vacancy_id"), "job_applications", ["vacancy_id"])
    op.create_index(op.f("ix_job_applications_resume_id"), "job_applications", ["resume_id"])
    op.create_index(op.f("ix_job_applications_status"), "job_applications", ["status"])

    # Create saved_jobs table
    op.create_table(
        "saved_jobs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "vacancy_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_vacancies.id", ondelete="CASCADE"),
            nullable=False,
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
        comment="Store jobs bookmarked/saved by job seekers for later viewing",
    )
    op.create_index(op.f("ix_saved_jobs_user_id"), "saved_jobs", ["user_id"])
    op.create_index(op.f("ix_saved_jobs_vacancy_id"), "saved_jobs", ["vacancy_id"])

    # Create unique constraint on saved_jobs to prevent duplicate saves
    op.create_unique_constraint(
        op.f("uq_saved_jobs_user_vacancy"),
        "saved_jobs",
        ["user_id", "vacancy_id"]
    )


def downgrade() -> None:
    # Drop unique constraint
    op.drop_constraint(
        op.f("uq_saved_jobs_user_vacancy"),
        "saved_jobs",
        type_="unique"
    )

    # Drop saved_jobs table
    op.drop_index(op.f("ix_saved_jobs_vacancy_id"), table_name="saved_jobs")
    op.drop_index(op.f("ix_saved_jobs_user_id"), table_name="saved_jobs")
    op.drop_table("saved_jobs")

    # Drop job_applications table
    op.drop_index(op.f("ix_job_applications_status"), table_name="job_applications")
    op.drop_index(op.f("ix_job_applications_resume_id"), table_name="job_applications")
    op.drop_index(op.f("ix_job_applications_vacancy_id"), table_name="job_applications")
    op.drop_index(op.f("ix_job_applications_user_id"), table_name="job_applications")
    op.drop_table("job_applications")

    # Drop enum type
    sa.Enum(name="applicationstatus").drop(op.get_bind(), checkfirst=True)
