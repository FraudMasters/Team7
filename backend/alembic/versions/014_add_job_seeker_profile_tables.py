"""
Add job seeker profile tables

Creates tables for job seeker profile management:
- job_seeker_profiles: Central profile linking users to their professional information
- work_history: Store job seeker work experience entries
- education: Store job seeker education history
- skills: Store job seeker skills and competencies
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "014_add_job_seeker_profile_tables"
down_revision: Union[str, None] = "013_add_job_seeker_role"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create job seeker profile tables with all necessary columns and indexes.
    """

    # Create employmenttype enum for work_history table
    op.execute(
        "CREATE TYPE employmenttype AS ENUM "
        "('FULL_TIME', 'PART_TIME', 'CONTRACT', 'INTERNSHIP', 'FREELANCE', 'TEMPORARY', 'OTHER')"
    )

    # Create degreetype enum for education table
    op.execute(
        "CREATE TYPE degreetype AS ENUM "
        "('HIGH_SCHOOL', 'CERTIFICATE', 'ASSOCIATE', 'BACHELOR', 'MASTER', 'DOCTORATE', 'POST_DOCTORAL', 'OTHER')"
    )

    # Create proficiencylevel enum for skills table
    op.execute(
        "CREATE TYPE proficiencylevel AS ENUM "
        "('BEGINNER', 'INTERMEDIATE', 'ADVANCED', 'EXPERT')"
    )

    # Create job_seeker_profiles table
    op.create_table(
        "job_seeker_profiles",
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
            unique=True,
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("linkedin_url", sa.String(512), nullable=True),
        sa.Column("portfolio_url", sa.String(512), nullable=True),
        sa.Column("years_of_experience", sa.Numeric(5, 2), nullable=True),
        sa.Column("current_title", sa.String(255), nullable=True),
        sa.Column("current_company", sa.String(255), nullable=True),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("job_seeker_status", sa.String(50), nullable=True),
        sa.Column("preferred_locations", sa.Text(), nullable=True),
        sa.Column("preferred_job_types", sa.String(255), nullable=True),
        sa.Column("expected_salary", sa.String(100), nullable=True),
        sa.Column(
            "resume_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resumes.id", ondelete="SET NULL"),
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
        comment="Central profile for job seekers linking users to their professional information",
    )
    op.create_index(op.f("ix_job_seeker_profiles_user_id"), "job_seeker_profiles", ["user_id"])
    op.create_index(op.f("ix_job_seeker_profiles_organization_id"), "job_seeker_profiles", ["organization_id"])
    op.create_index(op.f("ix_job_seeker_profiles_resume_id"), "job_seeker_profiles", ["resume_id"])

    # Create work_history table
    op.create_table(
        "work_history",
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
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("position_title", sa.String(255), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column(
            "employment_type",
            sa.Enum("FULL_TIME", "PART_TIME", "CONTRACT", "INTERNSHIP", "FREELANCE", "TEMPORARY", "OTHER", name="employmenttype"),
            nullable=False,
            server_default="FULL_TIME",
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
        comment="Store job seeker work experience entries",
    )
    op.create_index(op.f("ix_work_history_resume_id"), "work_history", ["resume_id"])

    # Create education table
    op.create_table(
        "education",
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
        sa.Column("institution_name", sa.String(255), nullable=False),
        sa.Column("degree", sa.String(255), nullable=False),
        sa.Column("field_of_study", sa.String(255), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column(
            "degree_type",
            sa.Enum("HIGH_SCHOOL", "CERTIFICATE", "ASSOCIATE", "BACHELOR", "MASTER", "DOCTORATE", "POST_DOCTORAL", "OTHER", name="degreetype"),
            nullable=False,
            server_default="BACHELOR",
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
        comment="Store job seeker education history",
    )
    op.create_index(op.f("ix_education_resume_id"), "education", ["resume_id"])

    # Create skills table
    op.create_table(
        "skills",
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
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column(
            "proficiency_level",
            sa.Enum("BEGINNER", "INTERMEDIATE", "ADVANCED", "EXPERT", name="proficiencylevel"),
            nullable=False,
            server_default="INTERMEDIATE",
        ),
        sa.Column("years_of_experience", sa.Numeric(5, 2), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
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
        comment="Store job seeker skills and competencies",
    )
    op.create_index(op.f("ix_skills_resume_id"), "skills", ["resume_id"])


def downgrade() -> None:
    """
    Drop job seeker profile tables and related enum types.
    """

    # Drop skills table
    op.drop_index(op.f("ix_skills_resume_id"), table_name="skills")
    op.drop_table("skills")

    # Drop education table
    op.drop_index(op.f("ix_education_resume_id"), table_name="education")
    op.drop_table("education")

    # Drop work_history table
    op.drop_index(op.f("ix_work_history_resume_id"), table_name="work_history")
    op.drop_table("work_history")

    # Drop job_seeker_profiles table
    op.drop_index(op.f("ix_job_seeker_profiles_resume_id"), table_name="job_seeker_profiles")
    op.drop_index(op.f("ix_job_seeker_profiles_organization_id"), table_name="job_seeker_profiles")
    op.drop_index(op.f("ix_job_seeker_profiles_user_id"), table_name="job_seeker_profiles")
    op.drop_table("job_seeker_profiles")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS proficiencylevel")
    op.execute("DROP TYPE IF EXISTS degreetype")
    op.execute("DROP TYPE IF EXISTS employmenttype")
