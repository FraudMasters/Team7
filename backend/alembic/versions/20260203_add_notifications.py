"""
Add notification system tables

Creates tables for:
- notifications: Store in-app notifications with delivery tracking
- notification_preferences: Store user notification preferences per type and channel
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260203_add_notifications"
down_revision: Union[str, None] = "20260201_add_search_performance_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create notifications table
    op.create_table(
        "notifications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "recipient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recruiters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("notification_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("data", postgresql.JSON(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivery_failed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("delivery_error", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resumes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "vacancy_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_vacancies.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action_url", sa.String(500), nullable=True),
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
        comment="Store in-app notifications with delivery tracking and links to related entities",
    )
    op.create_index(op.f("ix_notifications_recipient_id"), "notifications", ["recipient_id"])
    op.create_index(op.f("ix_notifications_notification_type"), "notifications", ["notification_type"])
    op.create_index(op.f("ix_notifications_is_read"), "notifications", ["is_read"])
    op.create_index(op.f("ix_notifications_candidate_id"), "notifications", ["candidate_id"])
    op.create_index(op.f("ix_notifications_vacancy_id"), "notifications", ["vacancy_id"])

    # Create notification_preferences table
    op.create_table(
        "notification_preferences",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recruiters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("notification_type", sa.String(50), nullable=False),
        sa.Column("email_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("in_app_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("push_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sms_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("digest_frequency", sa.String(20), nullable=True),
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
        comment="Store user notification preferences per event type and delivery channel",
    )
    op.create_index(op.f("ix_notification_preferences_user_id"), "notification_preferences", ["user_id"])
    op.create_index(op.f("ix_notification_preferences_notification_type"), "notification_preferences", ["notification_type"])


def downgrade() -> None:
    # Drop notification_preferences table
    op.drop_index(op.f("ix_notification_preferences_notification_type"), table_name="notification_preferences")
    op.drop_index(op.f("ix_notification_preferences_user_id"), table_name="notification_preferences")
    op.drop_table("notification_preferences")

    # Drop notifications table
    op.drop_index(op.f("ix_notifications_vacancy_id"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_candidate_id"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_is_read"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_notification_type"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_recipient_id"), table_name="notifications")
    op.drop_table("notifications")
