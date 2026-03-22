"""
Add agency multi-tenant support

Revision ID: 20260322_add_agency_multi_tenant
Revises: 20260221_add_skill_hierarchy_and_relationships
Create Date: 2026-03-22

Adds tables for multi-tenant agency support:
- agencies: Recruitment agencies managing multiple client organizations
- client_tenants: Many-to-many relationship between agencies and client organizations
- agency_users: Many-to-many relationship between agencies and users with roles
- client_usage: Per-client resource usage tracking for unified billing
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260322_add_agency_multi_tenant"
down_revision: Union[str, None] = "20260221_add_skill_hierarchy_and_relationships"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add agency multi-tenant tables."""
    # Create agencies table
    op.create_table(
        "agencies",
        sa.Column(
            "id",
            sa.String(100),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("domain", sa.String(255), nullable=True, unique=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("contact_phone", sa.String(50), nullable=True),
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
        comment="Store recruitment agencies managing multiple client organizations",
    )
    op.create_index(op.f("ix_agencies_name"), "agencies", ["name"])
    op.create_index(op.f("ix_agencies_slug"), "agencies", ["slug"])
    op.create_index(op.f("ix_agencies_is_active"), "agencies", ["is_active"])

    # Create client_tenants table
    op.create_table(
        "client_tenants",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "agency_id",
            sa.String(100),
            sa.ForeignKey("agencies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            sa.String(100),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="true"),
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
        comment="Many-to-many relationship between agencies and client organizations",
    )
    op.create_index(op.f("ix_client_tenants_agency_id"), "client_tenants", ["agency_id"])
    op.create_index(op.f("ix_client_tenants_organization_id"), "client_tenants", ["organization_id"])

    # Create agency_users table
    op.create_table(
        "agency_users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "agency_id",
            sa.String(100),
            sa.ForeignKey("agencies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(50), nullable=False, server_default="member"),
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
        comment="Many-to-many relationship between agencies and users with roles",
    )
    op.create_index(op.f("ix_agency_users_agency_id"), "agency_users", ["agency_id"])
    op.create_index(op.f("ix_agency_users_user_id"), "agency_users", ["user_id"])

    # Create client_usage table
    op.create_table(
        "client_usage",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "client_tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("client_tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "period_start",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "period_end",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("metadata", postgresql.JSON(), nullable=True),
        sa.Column("cost_cents", sa.Integer(), nullable=True),
        sa.Column("notes", sa.String(1000), nullable=True),
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
        comment="Per-client resource usage tracking for unified billing",
    )
    op.create_index(op.f("ix_client_usage_client_tenant_id"), "client_usage", ["client_tenant_id"])
    op.create_index(op.f("ix_client_usage_resource_type"), "client_usage", ["resource_type"])
    op.create_index(op.f("ix_client_usage_period_start"), "client_usage", ["period_start"])
    op.create_index(op.f("ix_client_usage_period_end"), "client_usage", ["period_end"])


def downgrade() -> None:
    """Remove agency multi-tenant tables."""
    # Drop client_usage table
    op.drop_index(op.f("ix_client_usage_period_end"), table_name="client_usage")
    op.drop_index(op.f("ix_client_usage_period_start"), table_name="client_usage")
    op.drop_index(op.f("ix_client_usage_resource_type"), table_name="client_usage")
    op.drop_index(op.f("ix_client_usage_client_tenant_id"), table_name="client_usage")
    op.drop_table("client_usage")

    # Drop agency_users table
    op.drop_index(op.f("ix_agency_users_user_id"), table_name="agency_users")
    op.drop_index(op.f("ix_agency_users_agency_id"), table_name="agency_users")
    op.drop_table("agency_users")

    # Drop client_tenants table
    op.drop_index(op.f("ix_client_tenants_organization_id"), table_name="client_tenants")
    op.drop_index(op.f("ix_client_tenants_agency_id"), table_name="client_tenants")
    op.drop_table("client_tenants")

    # Drop agencies table
    op.drop_index(op.f("ix_agencies_is_active"), table_name="agencies")
    op.drop_index(op.f("ix_agencies_slug"), table_name="agencies")
    op.drop_index(op.f("ix_agencies_name"), table_name="agencies")
    op.drop_table("agencies")
