"""
Enhance email templates table

Adds support for:
- template_blocks: JSON structure for drag-and-drop template builder
- category: Template categorization (notification, feedback, invitation, etc.)
- pipeline_stage: Association with specific hiring pipeline stages
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260322_enhance_email_templates"
down_revision: Union[str, None] = "20260221_add_skill_hierarchy_and_relationships"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add template_blocks column for drag-and-drop structure
    op.add_column(
        "email_templates",
        sa.Column("template_blocks", postgresql.JSON(), nullable=True, comment="JSON structure for drag-and-drop template builder"),
    )

    # Add category column for template categorization
    op.add_column(
        "email_templates",
        sa.Column("category", sa.String(100), nullable=True, comment="Template category (notification, feedback, invitation, etc.)"),
    )

    # Add pipeline_stage column for hiring pipeline association
    op.add_column(
        "email_templates",
        sa.Column("pipeline_stage", sa.String(100), nullable=True, comment="Associated hiring pipeline stage"),
    )

    # Create index on category for faster filtering
    op.create_index(
        op.f("ix_email_templates_category"), "email_templates", ["category"]
    )

    # Create index on pipeline_stage for faster filtering
    op.create_index(
        op.f("ix_email_templates_pipeline_stage"), "email_templates", ["pipeline_stage"]
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f("ix_email_templates_pipeline_stage"), table_name="email_templates")
    op.drop_index(op.f("ix_email_templates_category"), table_name="email_templates")

    # Drop columns
    op.drop_column("email_templates", "pipeline_stage")
    op.drop_column("email_templates", "category")
    op.drop_column("email_templates", "template_blocks")
