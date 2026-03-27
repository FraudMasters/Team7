"""
Add search relevance config table

Creates search_relevance_configs table for storing and managing
search result relevance boost values for different fields.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = "20260321_add_search_relevance_config"
down_revision: Union[str, None] = "20260321_add_search_analytics_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create search_relevance_configs table
    op.create_table(
        "search_relevance_configs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "name",
            sa.String(255),
            nullable=False,
            comment="Name/description of this configuration (e.g., 'Default', 'Skills-focused')",
        ),
        sa.Column(
            "skills_boost",
            sa.Float(),
            nullable=False,
            server_default="1.0",
            comment="Boost value for skills field in search relevance scoring",
        ),
        sa.Column(
            "experience_boost",
            sa.Float(),
            nullable=False,
            server_default="1.0",
            comment="Boost value for experience field in search relevance scoring",
        ),
        sa.Column(
            "education_boost",
            sa.Float(),
            nullable=False,
            server_default="1.0",
            comment="Boost value for education field in search relevance scoring",
        ),
        sa.Column(
            "location_boost",
            sa.Float(),
            nullable=False,
            server_default="1.0",
            comment="Boost value for location field in search relevance scoring",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default="true",
            comment="Whether this configuration is currently active",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Create indexes for search_relevance_configs table
    op.create_index(
        op.f("ix_search_relevance_configs_name"),
        "search_relevance_configs",
        ["name"],
    )
    op.create_index(
        op.f("ix_search_relevance_configs_is_active"),
        "search_relevance_configs",
        ["is_active"],
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(
        op.f("ix_search_relevance_configs_is_active"),
        table_name="search_relevance_configs",
    )
    op.drop_index(
        op.f("ix_search_relevance_configs_name"),
        table_name="search_relevance_configs",
    )

    # Drop table
    op.drop_table("search_relevance_configs")
