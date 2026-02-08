"""Add organization explanation preferences table

Creates tables for:
- organization_explanation_preferences: Store organization-level settings for explanation tone, style, and detail level
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260208_add_explanation_preferences"
down_revision: Union[str, None] = "20260207_add_workflows"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create organization_explanation_preferences table."""
    # Create organization_explanation_preferences table
    op.create_table(
        "organization_explanation_preferences",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("organization_id", sa.String(255), nullable=False),
        sa.Column(
            "tone",
            sa.String(50),
            nullable=False,
            server_default="professional",
            comment='Preferred explanation tone: professional, casual, friendly, formal'
        ),
        sa.Column(
            "style",
            sa.String(50),
            nullable=False,
            server_default="balanced",
            comment='Preferred explanation style: detailed, concise, balanced'
        ),
        sa.Column(
            "detail_level",
            sa.String(50),
            nullable=False,
            server_default="medium",
            comment='Level of detail: high, medium, low'
        ),
        sa.Column(
            "include_percentiles",
            sa.Boolean(),
            nullable=False,
            server_default="true",
            comment='Whether to include percentile-based comparisons'
        ),
        sa.Column(
            "include_skill_names",
            sa.Boolean(),
            nullable=False,
            server_default="true",
            comment='Whether to include specific skill names in explanations'
        ),
        sa.Column(
            "include_experience_details",
            sa.Boolean(),
            nullable=False,
            server_default="true",
            comment='Whether to include experience duration details'
        ),
        sa.Column(
            "include_education_details",
            sa.Boolean(),
            nullable=False,
            server_default="true",
            comment='Whether to include education details'
        ),
        sa.Column(
            "language",
            sa.String(10),
            nullable=True,
            comment='Preferred language for explanations (e.g., en, es, fr)'
        ),
        sa.Column(
            "custom_prompt_template",
            sa.Text(),
            nullable=True,
            comment='Optional custom prompt template for LLM explanations'
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
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
        comment="Store organization-level settings for explanation tone and style",
    )

    # Create indexes for organization_explanation_preferences
    op.create_index(
        op.f("ix_organization_explanation_preferences_organization_id"),
        "organization_explanation_preferences",
        ["organization_id"],
        unique=False
    )
    op.create_index(
        op.f("ix_organization_explanation_preferences_is_active"),
        "organization_explanation_preferences",
        ["is_active"],
        unique=False
    )


def downgrade() -> None:
    """Remove organization_explanation_preferences table."""
    # Drop indexes
    op.drop_index(
        op.f("ix_organization_explanation_preferences_is_active"),
        table_name="organization_explanation_preferences"
    )
    op.drop_index(
        op.f("ix_organization_explanation_preferences_organization_id"),
        table_name="organization_explanation_preferences"
    )
    # Drop table
    op.drop_table("organization_explanation_preferences")
