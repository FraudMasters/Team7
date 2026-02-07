"""
Add plugin marketplace and installation tracking tables

Creates tables for:
- plugins: Store plugin metadata for the marketplace
- plugin_installations: Track plugin installations by recruiters
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260207_add_plugins"
down_revision: Union[str, None] = "20260207_add_webhooks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create plugins table
    op.create_table(
        "plugins",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("author", sa.String(255), nullable=False),
        sa.Column("author_email", sa.String(255), nullable=True),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("long_description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("tags", postgresql.JSON(), nullable=False, default=[]),
        sa.Column("logo_url", sa.String(2048), nullable=True),
        sa.Column("manifest_url", sa.String(2048), nullable=False),
        sa.Column("download_url", sa.String(2048), nullable=False),
        sa.Column("homepage_url", sa.String(2048), nullable=True),
        sa.Column("repository_url", sa.String(2048), nullable=True),
        sa.Column("documentation_url", sa.String(2048), nullable=True),
        sa.Column("is_official", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending_review"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("install_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rating_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("average_rating", sa.Float(), nullable=True),
        sa.Column("latest_version", sa.String(50), nullable=True),
        sa.Column("min_agenthr_version", sa.String(50), nullable=True),
        sa.Column("max_agenthr_version", sa.String(50), nullable=True),
        sa.Column("permissions", postgresql.JSON(), nullable=False, default=[]),
        sa.Column("dependencies", postgresql.JSON(), nullable=True),
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
        comment="Store plugin metadata for the marketplace",
    )
    op.create_index(
        op.f("ix_plugins_name"),
        "plugins",
        ["name"],
        unique=True,
    )
    op.create_index(
        op.f("ix_plugins_slug"),
        "plugins",
        ["slug"],
        unique=True,
    )
    op.create_index(
        op.f("ix_plugins_author"),
        "plugins",
        ["author"],
    )
    op.create_index(
        op.f("ix_plugins_category"),
        "plugins",
        ["category"],
    )
    op.create_index(
        op.f("ix_plugins_is_official"),
        "plugins",
        ["is_official"],
    )
    op.create_index(
        op.f("ix_plugins_status"),
        "plugins",
        ["status"],
    )
    op.create_index(
        op.f("ix_plugins_is_active"),
        "plugins",
        ["is_active"],
    )

    # Create plugin_installations table
    op.create_table(
        "plugin_installations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "plugin_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plugins.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "recruiter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recruiters.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("config", postgresql.JSON(), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("install_notes", sa.Text(), nullable=True),
        sa.Column("installed_at", sa.String(50), nullable=False, server_default="now()"),
        sa.Column("last_used_at", sa.String(50), nullable=True),
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
        comment="Track plugin installations by recruiters",
    )
    op.create_index(
        op.f("ix_plugin_installations_plugin_id"),
        "plugin_installations",
        ["plugin_id"],
    )
    op.create_index(
        op.f("ix_plugin_installations_recruiter_id"),
        "plugin_installations",
        ["recruiter_id"],
    )
    op.create_index(
        op.f("ix_plugin_installations_is_enabled"),
        "plugin_installations",
        ["is_enabled"],
    )


def downgrade() -> None:
    # Drop plugin_installations table
    op.drop_index(
        op.f("ix_plugin_installations_is_enabled"),
        table_name="plugin_installations",
    )
    op.drop_index(
        op.f("ix_plugin_installations_recruiter_id"),
        table_name="plugin_installations",
    )
    op.drop_index(
        op.f("ix_plugin_installations_plugin_id"),
        table_name="plugin_installations",
    )
    op.drop_table("plugin_installations")

    # Drop plugins table
    op.drop_index(
        op.f("ix_plugins_is_active"),
        table_name="plugins",
    )
    op.drop_index(
        op.f("ix_plugins_status"),
        table_name="plugins",
    )
    op.drop_index(
        op.f("ix_plugins_is_official"),
        table_name="plugins",
    )
    op.drop_index(
        op.f("ix_plugins_category"),
        table_name="plugins",
    )
    op.drop_index(
        op.f("ix_plugins_author"),
        table_name="plugins",
    )
    op.drop_index(
        op.f("ix_plugins_slug"),
        table_name="plugins",
    )
    op.drop_index(
        op.f("ix_plugins_name"),
        table_name="plugins",
    )
    op.drop_table("plugins")
