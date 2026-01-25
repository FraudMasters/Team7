"""
Add advanced skill matching tables

Creates tables for:
- skill_taxonomies: Industry-specific skill taxonomies with variants and context
- custom_synonyms: Organization-specific custom synonym mappings
- skill_feedback: Recruiter feedback on skill matches for ML learning
- ml_model_versions: Model versioning with A/B testing support
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_add_advanced_matching"
down_revision: Union[str, None] = "001_init"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create skill_taxonomies table
    op.create_table(
        "skill_taxonomies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("industry", sa.String(100), nullable=False),
        sa.Column("skill_name", sa.String(255), nullable=False),
        sa.Column("context", sa.String(100), nullable=True),
        sa.Column("variants", postgresql.JSON(), nullable=True),
        sa.Column("metadata", postgresql.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
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
        comment="Industry-specific skill taxonomies with variants and context",
    )
    op.create_index(op.f("ix_skill_taxonomies_industry"), "skill_taxonomies", ["industry"])
    op.create_index(op.f("ix_skill_taxonomies_skill_name"), "skill_taxonomies", ["skill_name"])

    # Create custom_synonyms table
    op.create_table(
        "custom_synonyms",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("organization_id", sa.String(255), nullable=False),
        sa.Column("canonical_skill", sa.String(255), nullable=False),
        sa.Column("custom_synonyms", postgresql.JSON(), nullable=False, server_default="[]"),
        sa.Column("context", sa.String(100), nullable=True),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
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
        comment="Organization-specific custom synonym mappings",
    )
    op.create_index(
        op.f("ix_custom_synonyms_organization_id"), "custom_synonyms", ["organization_id"]
    )

    # Create skill_feedback table
    op.create_table(
        "skill_feedback",
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
        sa.Column(
            "match_result_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("match_results.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("skill", sa.String(255), nullable=False),
        sa.Column("was_correct", sa.Boolean(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("recruiter_correction", sa.Text(), nullable=True),
        sa.Column("actual_skill", sa.String(255), nullable=True),
        sa.Column("feedback_source", sa.String(50), nullable=False, server_default="api"),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default="false"),
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
        comment="Recruiter feedback on skill matches for ML learning",
    )
    op.create_index(op.f("ix_skill_feedback_resume_id"), "skill_feedback", ["resume_id"])
    op.create_index(op.f("ix_skill_feedback_vacancy_id"), "skill_feedback", ["vacancy_id"])

    # Create ml_model_versions table
    op.create_table(
        "ml_model_versions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_experiment", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("experiment_config", postgresql.JSON(), nullable=True),
        sa.Column("model_metadata", postgresql.JSON(), nullable=True),
        sa.Column("accuracy_metrics", postgresql.JSON(), nullable=True),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("performance_score", sa.Numeric(5, 2), nullable=True),
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
        comment="Model versioning with A/B testing support",
    )
    op.create_index(op.f("ix_ml_model_versions_model_name"), "ml_model_versions", ["model_name"])


def downgrade() -> None:
    # Drop ml_model_versions table
    op.drop_index(op.f("ix_ml_model_versions_model_name"), table_name="ml_model_versions")
    op.drop_table("ml_model_versions")

    # Drop skill_feedback table
    op.drop_index(op.f("ix_skill_feedback_vacancy_id"), table_name="skill_feedback")
    op.drop_index(op.f("ix_skill_feedback_resume_id"), table_name="skill_feedback")
    op.drop_table("skill_feedback")

    # Drop custom_synonyms table
    op.drop_index(
        op.f("ix_custom_synonyms_organization_id"), table_name="custom_synonyms"
    )
    op.drop_table("custom_synonyms")

    # Drop skill_taxonomies table
    op.drop_index(op.f("ix_skill_taxonomies_skill_name"), table_name="skill_taxonomies")
    op.drop_index(op.f("ix_skill_taxonomies_industry"), table_name="skill_taxonomies")
    op.drop_table("skill_taxonomies")
