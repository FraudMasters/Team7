"""
Add analytics and reporting tables

Creates tables for:
- hiring_stages: Track resume progression through hiring pipeline for funnel analytics
- analytics_events: Track time-based analytics events for metrics and trends
- recruiters: Track recruiter attribution and performance metrics
- reports: Store custom report configurations
- scheduled_reports: Schedule automated report generation and delivery
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "004_add_analytics_tables"
down_revision: Union[str, None] = "003_add_resume_comparisons"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create recruiters table first (analytics_events references it)
    op.create_table(
        "recruiters",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("department", sa.String(100), nullable=True),
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
        comment="Track recruiter attribution and performance metrics",
    )
    op.create_index(op.f("ix_recruiters_name"), "recruiters", ["name"])
    op.create_index(op.f("ix_recruiters_email"), "recruiters", ["email"])
    op.create_index(op.f("ix_recruiters_department"), "recruiters", ["department"])
    op.create_index(op.f("ix_recruiters_is_active"), "recruiters", ["is_active"])

    # Create hiring_stages table
    op.create_table(
        "hiring_stages",
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
            sa.ForeignKey("job_vacancies.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("stage_name", sa.String(50), nullable=False),
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
        comment="Track resume progression through hiring pipeline for funnel analytics",
    )
    op.create_index(op.f("ix_hiring_stages_resume_id"), "hiring_stages", ["resume_id"])
    op.create_index(op.f("ix_hiring_stages_vacancy_id"), "hiring_stages", ["vacancy_id"])
    op.create_index(op.f("ix_hiring_stages_stage_name"), "hiring_stages", ["stage_name"])

    # Create analytics_events table
    op.create_table(
        "analytics_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "recruiter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recruiters.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("session_id", sa.String(255), nullable=True),
        sa.Column("event_data", postgresql.JSON(), nullable=True),
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
        comment="Track time-based analytics events for metrics and trends",
    )
    op.create_index(op.f("ix_analytics_events_event_type"), "analytics_events", ["event_type"])
    op.create_index(op.f("ix_analytics_events_entity_type"), "analytics_events", ["entity_type"])
    op.create_index(op.f("ix_analytics_events_entity_id"), "analytics_events", ["entity_id"])
    op.create_index(op.f("ix_analytics_events_user_id"), "analytics_events", ["user_id"])
    op.create_index(op.f("ix_analytics_events_recruiter_id"), "analytics_events", ["recruiter_id"])
    op.create_index(op.f("ix_analytics_events_session_id"), "analytics_events", ["session_id"])

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
        comment="Store custom report configurations",
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
    op.create_index(op.f("ix_scheduled_reports_organization_id"), "scheduled_reports", ["organization_id"])
    op.create_index(op.f("ix_scheduled_reports_report_id"), "scheduled_reports", ["report_id"])


def downgrade() -> None:
    # Drop scheduled_reports table
    op.drop_index(op.f("ix_scheduled_reports_report_id"), table_name="scheduled_reports")
    op.drop_index(op.f("ix_scheduled_reports_organization_id"), table_name="scheduled_reports")
    op.drop_table("scheduled_reports")

    # Drop reports table
    op.drop_index(op.f("ix_reports_report_type"), table_name="reports")
    op.drop_index(op.f("ix_reports_organization_id"), table_name="reports")
    op.drop_table("reports")

    # Drop analytics_events table
    op.drop_index(op.f("ix_analytics_events_session_id"), table_name="analytics_events")
    op.drop_index(op.f("ix_analytics_events_recruiter_id"), table_name="analytics_events")
    op.drop_index(op.f("ix_analytics_events_user_id"), table_name="analytics_events")
    op.drop_index(op.f("ix_analytics_events_entity_id"), table_name="analytics_events")
    op.drop_index(op.f("ix_analytics_events_entity_type"), table_name="analytics_events")
    op.drop_index(op.f("ix_analytics_events_event_type"), table_name="analytics_events")
    op.drop_table("analytics_events")

    # Drop hiring_stages table
    op.drop_index(op.f("ix_hiring_stages_stage_name"), table_name="hiring_stages")
    op.drop_index(op.f("ix_hiring_stages_vacancy_id"), table_name="hiring_stages")
    op.drop_index(op.f("ix_hiring_stages_resume_id"), table_name="hiring_stages")
    op.drop_table("hiring_stages")

    # Drop recruiters table
    op.drop_index(op.f("ix_recruiters_is_active"), table_name="recruiters")
    op.drop_index(op.f("ix_recruiters_department"), table_name="recruiters")
    op.drop_index(op.f("ix_recruiters_email"), table_name="recruiters")
    op.drop_index(op.f("ix_recruiters_name"), table_name="recruiters")
    op.drop_table("recruiters")
