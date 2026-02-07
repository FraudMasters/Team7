"""
Add API keys table for developer authentication

Creates table for:
- api_keys: Store API keys for developer authentication with scopes and rate limiting
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260207_add_api_keys"
down_revision: Union[str, None] = "20260201_add_search_performance_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create api_keys table
    op.create_table(
        "api_keys",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("key_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("key_prefix", sa.String(10), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("scopes", postgresql.JSON(), nullable=False, default=[]),
        sa.Column(
            "rate_limit",
            postgresql.JSON(),
            nullable=True,
            default='{"requests_per_minute": 60, "requests_per_hour": 1000, "requests_per_day": 10000}',
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
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
        comment="Store API keys for developer authentication with scopes and rate limiting",
    )
    op.create_index(op.f("ix_api_keys_key_hash"), "api_keys", ["key_hash"], unique=True)
    op.create_index(op.f("ix_api_keys_key_prefix"), "api_keys", ["key_prefix"])
    op.create_index(op.f("ix_api_keys_is_active"), "api_keys", ["is_active"])


def downgrade() -> None:
    # Drop api_keys table
    op.drop_index(op.f("ix_api_keys_is_active"), table_name="api_keys")
    op.drop_index(op.f("ix_api_keys_key_prefix"), table_name="api_keys")
    op.drop_index(op.f("ix_api_keys_key_hash"), table_name="api_keys")
    op.drop_table("api_keys")
