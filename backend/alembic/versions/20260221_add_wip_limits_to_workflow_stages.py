"""Add wip_limit column to workflow_stage_configs

Revision ID: 20260221_add_wip_limits_to_workflow_stages
Revises: 20260221_add_skill_hierarchy_and_relationships
Create Date: 2026-02-21

This migration adds the wip_limit column to the workflow_stage_configs table
to support work-in-progress limits for Kanban-style candidate pipeline management.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260221_add_wip_limits_to_workflow_stages"
down_revision: Union[str, None] = "20260221_add_skill_hierarchy_and_relationships"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add wip_limit column to workflow_stage_configs table."""

    # Add wip_limit column for Kanban work-in-progress limits
    op.add_column(
        "workflow_stage_configs",
        sa.Column(
            "wip_limit",
            sa.Integer(),
            nullable=True,
            comment="Work-in-progress limit for Kanban (max candidates in this stage)",
        ),
    )


def downgrade() -> None:
    """Remove wip_limit column from workflow_stage_configs table."""

    # Remove wip_limit column
    op.drop_column("workflow_stage_configs", "wip_limit")
