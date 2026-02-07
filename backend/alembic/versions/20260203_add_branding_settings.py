"""Add branding settings table

Creates tables for:
- branding_settings: Store organization customization and branding preferences
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260203_add_branding_settings"
down_revision: Union[str, None] = "20260203_add_email_templates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create branding_settings table."""
    # Create branding_settings table
    op.create_table(
        "branding_settings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("organization_id", sa.String(255), nullable=False),
        sa.Column("primary_color", sa.String(7), nullable=False, server_default="#3B82F6"),
        sa.Column("secondary_color", sa.String(7), nullable=False, server_default="#10B981"),
        sa.Column("accent_color", sa.String(7), nullable=False, server_default="#F59E0B"),
        sa.Column("background_color", sa.String(7), nullable=True),
        sa.Column("text_color", sa.String(7), nullable=True),
        sa.Column("font_family", sa.String(100), nullable=True),
        sa.Column("custom_css", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("favicon_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_by", sa.String(255), nullable=True),
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
        comment="Store organization customization and branding preferences",
    )

    # Create indexes for branding_settings
    op.create_index(
        op.f("ix_branding_settings_organization_id"),
        "branding_settings",
        ["organization_id"],
        unique=False
    )
    op.create_index(
        op.f("ix_branding_settings_is_active"),
        "branding_settings",
        ["is_active"],
        unique=False
    )


def downgrade() -> None:
    """Remove branding_settings table."""
    # Drop indexes
    op.drop_index(
        op.f("ix_branding_settings_is_active"), table_name="branding_settings"
    )
    op.drop_index(
        op.f("ix_branding_settings_organization_id"), table_name="branding_settings"
    )
    # Drop table
    op.drop_table("branding_settings")
