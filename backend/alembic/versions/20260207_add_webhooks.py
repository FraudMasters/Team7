"""
Add webhook subscription and delivery tracking tables

Creates tables for:
- webhook_subscriptions: Store webhook endpoint subscriptions with event filters
- webhook_delivery_logs: Track webhook delivery attempts with retry logic
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260207_add_webhooks"
down_revision: Union[str, None] = "20260207_add_api_usage"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create webhook_subscriptions table
    op.create_table(
        "webhook_subscriptions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("events", postgresql.JSON(), nullable=False, default=[]),
        sa.Column("secret", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "api_key_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("api_keys.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("last_delivery_at", sa.DateTime(timezone=True), nullable=True),
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
        comment="Store webhook endpoint subscriptions with event filters",
    )
    op.create_index(
        op.f("ix_webhook_subscriptions_is_active"),
        "webhook_subscriptions",
        ["is_active"],
    )
    op.create_index(
        op.f("ix_webhook_subscriptions_api_key_id"),
        "webhook_subscriptions",
        ["api_key_id"],
    )

    # Create webhook_delivery_logs table
    op.create_table(
        "webhook_delivery_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "subscription_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("webhook_subscriptions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("event_data", postgresql.JSON(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("response_body", sa.Text(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
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
        comment="Track webhook delivery attempts with retry logic",
    )
    op.create_index(
        op.f("ix_webhook_delivery_logs_subscription_id"),
        "webhook_delivery_logs",
        ["subscription_id"],
    )
    op.create_index(
        op.f("ix_webhook_delivery_logs_event_type"),
        "webhook_delivery_logs",
        ["event_type"],
    )
    op.create_index(
        op.f("ix_webhook_delivery_logs_status"),
        "webhook_delivery_logs",
        ["status"],
    )
    op.create_index(
        op.f("ix_webhook_delivery_logs_next_retry_at"),
        "webhook_delivery_logs",
        ["next_retry_at"],
    )


def downgrade() -> None:
    # Drop webhook_delivery_logs table
    op.drop_index(
        op.f("ix_webhook_delivery_logs_next_retry_at"),
        table_name="webhook_delivery_logs",
    )
    op.drop_index(
        op.f("ix_webhook_delivery_logs_status"),
        table_name="webhook_delivery_logs",
    )
    op.drop_index(
        op.f("ix_webhook_delivery_logs_event_type"),
        table_name="webhook_delivery_logs",
    )
    op.drop_index(
        op.f("ix_webhook_delivery_logs_subscription_id"),
        table_name="webhook_delivery_logs",
    )
    op.drop_table("webhook_delivery_logs")

    # Drop webhook_subscriptions table
    op.drop_index(
        op.f("ix_webhook_subscriptions_api_key_id"),
        table_name="webhook_subscriptions",
    )
    op.drop_index(
        op.f("ix_webhook_subscriptions_is_active"),
        table_name="webhook_subscriptions",
    )
    op.drop_table("webhook_subscriptions")
