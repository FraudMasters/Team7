"""
Add API usage tracking table for analytics

Creates table for:
- api_usage: Track API usage for analytics and monitoring
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260207_add_api_usage"
down_revision: Union[str, None] = "20260207_add_api_keys"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create api_usage table
    op.create_table(
        "api_usage",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "api_key_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("api_keys.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("endpoint", sa.String(500), nullable=False),
        sa.Column("method", sa.String(10), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("rate_limit_remaining", sa.Integer(), nullable=True),
        sa.Column("request_data", postgresql.JSON(), nullable=True),
        sa.Column("response_data", postgresql.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
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
        comment="Track API usage for analytics and monitoring",
    )
    op.create_index(op.f("ix_api_usage_api_key_id"), "api_usage", ["api_key_id"])
    op.create_index(op.f("ix_api_usage_endpoint"), "api_usage", ["endpoint"])
    op.create_index(op.f("ix_api_usage_method"), "api_usage", ["method"])
    op.create_index(op.f("ix_api_usage_status"), "api_usage", ["status"])
    op.create_index(op.f("ix_api_usage_status_code"), "api_usage", ["status_code"])


def downgrade() -> None:
    # Drop api_usage table
    op.drop_index(op.f("ix_api_usage_status_code"), table_name="api_usage")
    op.drop_index(op.f("ix_api_usage_status"), table_name="api_usage")
    op.drop_index(op.f("ix_api_usage_method"), table_name="api_usage")
    op.drop_index(op.f("ix_api_usage_endpoint"), table_name="api_usage")
    op.drop_index(op.f("ix_api_usage_api_key_id"), table_name="api_usage")
    op.drop_table("api_usage")
