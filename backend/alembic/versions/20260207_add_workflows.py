"""
Add workflow automation tables

Creates tables for:
- workflows: Store workflow definitions with triggers and actions
- workflow_executions: Track workflow execution history with results
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260207_add_workflows"
down_revision: Union[str, None] = "20260207_add_plugins"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create workflows table
    op.create_table(
        "workflows",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("trigger_type", sa.String(50), nullable=False),
        sa.Column("trigger_config", postgresql.JSON(), nullable=False, default={}),
        sa.Column("actions", postgresql.JSON(), nullable=False, default=[]),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "api_key_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("api_keys.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("last_executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("execution_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
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
        comment="Store workflow definitions with triggers and actions",
    )
    op.create_index(
        op.f("ix_workflows_trigger_type"), "workflows", ["trigger_type"]
    )
    op.create_index(
        op.f("ix_workflows_status"), "workflows", ["status"]
    )
    op.create_index(
        op.f("ix_workflows_is_active"), "workflows", ["is_active"]
    )
    op.create_index(
        op.f("ix_workflows_api_key_id"), "workflows", ["api_key_id"]
    )

    # Create workflow_executions table
    op.create_table(
        "workflow_executions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "workflow_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workflows.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("trigger_type", sa.String(50), nullable=False),
        sa.Column("trigger_data", postgresql.JSON(), nullable=True),
        sa.Column("input_data", postgresql.JSON(), nullable=True),
        sa.Column("output_data", postgresql.JSON(), nullable=True),
        sa.Column("action_results", postgresql.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
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
        comment="Track workflow execution history with results",
    )
    op.create_index(
        op.f("ix_workflow_executions_workflow_id"),
        "workflow_executions",
        ["workflow_id"],
    )
    op.create_index(
        op.f("ix_workflow_executions_status"), "workflow_executions", ["status"]
    )


def downgrade() -> None:
    # Drop workflow_executions table
    op.drop_index(
        op.f("ix_workflow_executions_status"),
        table_name="workflow_executions",
    )
    op.drop_index(
        op.f("ix_workflow_executions_workflow_id"),
        table_name="workflow_executions",
    )
    op.drop_table("workflow_executions")

    # Drop workflows table
    op.drop_index(
        op.f("ix_workflows_api_key_id"),
        table_name="workflows",
    )
    op.drop_index(
        op.f("ix_workflows_is_active"),
        table_name="workflows",
    )
    op.drop_index(
        op.f("ix_workflows_status"),
        table_name="workflows",
    )
    op.drop_index(
        op.f("ix_workflows_trigger_type"),
        table_name="workflows",
    )
    op.drop_table("workflows")
