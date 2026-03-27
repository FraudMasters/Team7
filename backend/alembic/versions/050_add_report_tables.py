"""
Add report generation and scheduling tables

Creates tables for:
- reports: Store custom report configurations for various report types
- scheduled_reports: Schedule automated report generation and delivery
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "050_add_report_tables"
down_revision: Union[str, None] = "021_add_candidate_review_queue"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create reports table
    op.create_table(
        "reports",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("organization_id", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("report_type", sa.String(100), nullable=False),
        sa.Column("configuration", postgresql.JSON(), nullable=False),
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
        comment="Store custom report configurations for various report types",
    )
    op.create_index(op.f("ix_reports_organization_id"), "reports", ["organization_id"])
    op.create_index(op.f("ix_reports_report_type"), "reports", ["report_type"])

    # Create scheduled_reports table
    op.create_table(
        "scheduled_reports",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("organization_id", sa.String(255), nullable=False),
        sa.Column(
            "report_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("reports.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("schedule_config", postgresql.JSON(), nullable=False),
        sa.Column("delivery_config", postgresql.JSON(), nullable=False),
        sa.Column("recipients", postgresql.JSON(), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
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
        comment="Schedule automated report generation and delivery",
    )
    op.create_index(
        op.f("ix_scheduled_reports_organization_id"),
        "scheduled_reports",
        ["organization_id"],
    )
    op.create_index(
        op.f("ix_scheduled_reports_report_id"),
        "scheduled_reports",
        ["report_id"],
    )
    op.create_index(
        op.f("ix_scheduled_reports_next_run_at"),
        "scheduled_reports",
        ["next_run_at"],
    )
    op.create_index(
        op.f("ix_scheduled_reports_is_active"),
        "scheduled_reports",
        ["is_active"],
    )


def downgrade() -> None:
    # Drop scheduled_reports table first (has foreign key to reports)
    op.drop_index(
        op.f("ix_scheduled_reports_is_active"),
        table_name="scheduled_reports",
    )
    op.drop_index(
        op.f("ix_scheduled_reports_next_run_at"),
        table_name="scheduled_reports",
    )
    op.drop_index(
        op.f("ix_scheduled_reports_report_id"),
        table_name="scheduled_reports",
    )
    op.drop_index(
        op.f("ix_scheduled_reports_organization_id"),
        table_name="scheduled_reports",
    )
    op.drop_table("scheduled_reports")

    # Drop reports table
    op.drop_index(op.f("ix_reports_report_type"), table_name="reports")
    op.drop_index(op.f("ix_reports_organization_id"), table_name="reports")
    op.drop_table("reports")
