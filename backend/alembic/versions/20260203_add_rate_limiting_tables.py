"""
Add rate limiting and IP blocklist tables for DDoS protection

Creates tables for:
- rate_limit_configs: Store organization-specific rate limit policies
- ip_blocklist: Store blocked IP addresses and networks
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260203_add_rate_limiting_tables"
down_revision: Union[str, None] = "20260201_add_search_performance_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create rate_limit_configs table
    op.create_table(
        "rate_limit_configs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("organization_id", sa.String(50), nullable=False),
        sa.Column("endpoint_pattern", sa.String(255), nullable=True),
        sa.Column("requests_per_window", sa.Integer(), nullable=False),
        sa.Column("window_size_seconds", sa.Integer(), nullable=False),
        sa.Column("role_type", sa.String(50), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="true"),
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
        comment="Store organization-specific rate limit policies for API endpoints",
    )
    op.create_index(op.f("ix_rate_limit_configs_organization_id"), "rate_limit_configs", ["organization_id"])
    op.create_index(op.f("ix_rate_limit_configs_role_type"), "rate_limit_configs", ["role_type"])

    # Create ip_blocklist table
    op.create_table(
        "ip_blocklist",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("cidr", sa.String(50), nullable=True),
        sa.Column("block_reason", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(100), nullable=True),
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
        comment="Store blocked IP addresses and networks for DDoS protection",
    )
    op.create_index(op.f("ix_ip_blocklist_ip_address"), "ip_blocklist", ["ip_address"])
    op.create_index(op.f("ix_ip_blocklist_cidr"), "ip_blocklist", ["cidr"])
    op.create_index(op.f("ix_ip_blocklist_is_active"), "ip_blocklist", ["is_active"])


def downgrade() -> None:
    # Drop ip_blocklist table
    op.drop_index(op.f("ix_ip_blocklist_is_active"), table_name="ip_blocklist")
    op.drop_index(op.f("ix_ip_blocklist_cidr"), table_name="ip_blocklist")
    op.drop_index(op.f("ix_ip_blocklist_ip_address"), table_name="ip_blocklist")
    op.drop_table("ip_blocklist")

    # Drop rate_limit_configs table
    op.drop_index(op.f("ix_rate_limit_configs_role_type"), table_name="rate_limit_configs")
    op.drop_index(op.f("ix_rate_limit_configs_organization_id"), table_name="rate_limit_configs")
    op.drop_table("rate_limit_configs")
