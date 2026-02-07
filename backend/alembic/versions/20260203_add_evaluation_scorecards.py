"""
Add evaluation scorecards tables for standardized candidate evaluation

Creates tables for:
- evaluation_templates: Store reusable evaluation template definitions
- evaluation_criteria: Store individual criteria within templates with weights and rating scales
- evaluation_scorecards: Store individual evaluator assessments for candidates
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260203_add_evaluation_scorecards"
down_revision: Union[str, None] = "20260201_add_search_performance_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create evaluation_templates table
    op.create_table(
        "evaluation_templates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("organization_id", sa.String(255), nullable=False),
        sa.Column(
            "vacancy_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_vacancies.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
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
        comment="Store reusable evaluation template definitions with version tracking",
    )
    op.create_index(op.f("ix_evaluation_templates_organization_id"), "evaluation_templates", ["organization_id"])
    op.create_index(op.f("ix_evaluation_templates_vacancy_id"), "evaluation_templates", ["vacancy_id"])
    op.create_index(op.f("ix_evaluation_templates_is_active"), "evaluation_templates", ["is_active"])

    # Create evaluation_criteria table
    op.create_table(
        "evaluation_criteria",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("evaluation_templates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("criteria_type", sa.String(50), nullable=False, server_default="custom"),
        sa.Column("weight", sa.Numeric(5, 4), nullable=False, server_default="1.0"),
        sa.Column("min_score", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("max_score", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("rating_scale_description", sa.String(255), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("extra_metadata", postgresql.JSON(), nullable=True),
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
        comment="Store individual criteria within templates with weights and rating scales",
    )
    op.create_index(op.f("ix_evaluation_criteria_template_id"), "evaluation_criteria", ["template_id"])

    # Create evaluation_scorecards table
    op.create_table(
        "evaluation_scorecards",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("evaluation_templates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "resume_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resumes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "evaluator_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recruiters.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("criteria_responses", postgresql.JSON(), nullable=False, server_default="{}"),
        sa.Column("overall_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("evaluator_comments", sa.Text(), nullable=True),
        sa.Column("extra_metadata", postgresql.JSON(), nullable=True),
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
        comment="Store individual evaluator assessments for candidates based on templates",
    )
    op.create_index(op.f("ix_evaluation_scorecards_template_id"), "evaluation_scorecards", ["template_id"])
    op.create_index(op.f("ix_evaluation_scorecards_resume_id"), "evaluation_scorecards", ["resume_id"])
    op.create_index(op.f("ix_evaluation_scorecards_evaluator_id"), "evaluation_scorecards", ["evaluator_id"])
    op.create_index(op.f("ix_evaluation_scorecards_status"), "evaluation_scorecards", ["status"])


def downgrade() -> None:
    # Drop evaluation_scorecards table
    op.drop_index(op.f("ix_evaluation_scorecards_status"), table_name="evaluation_scorecards")
    op.drop_index(op.f("ix_evaluation_scorecards_evaluator_id"), table_name="evaluation_scorecards")
    op.drop_index(op.f("ix_evaluation_scorecards_resume_id"), table_name="evaluation_scorecards")
    op.drop_index(op.f("ix_evaluation_scorecards_template_id"), table_name="evaluation_scorecards")
    op.drop_table("evaluation_scorecards")

    # Drop evaluation_criteria table
    op.drop_index(op.f("ix_evaluation_criteria_template_id"), table_name="evaluation_criteria")
    op.drop_table("evaluation_criteria")

    # Drop evaluation_templates table
    op.drop_index(op.f("ix_evaluation_templates_is_active"), table_name="evaluation_templates")
    op.drop_index(op.f("ix_evaluation_templates_vacancy_id"), table_name="evaluation_templates")
    op.drop_index(op.f("ix_evaluation_templates_organization_id"), table_name="evaluation_templates")
    op.drop_table("evaluation_templates")
