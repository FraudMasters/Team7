"""
Add integration tables for HRIS/ATS platform connections

Creates tables for:
- integrations: Store HRIS/ATS platform integration configurations and credentials
- sync_logs: Track sync operations, errors, and status for monitoring
- integration_mappings: Configurable field mappings between systems
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260203_add_integrations"
down_revision: Union[str, None] = "20260201_add_search_performance_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    integrationplatform_enum = postgresql.ENUM(
        "WORKDAY",
        "GREENHOUSE",
        "LEVER",
        "BAMBOOHR",
        "ASHBY",
        name="integrationplatform",
    )
    integrationplatform_enum.create(op.get_bind(), checkfirst=True)

    integrationstatus_enum = postgresql.ENUM(
        "ACTIVE",
        "INACTIVE",
        "ERROR",
        "PENDING",
        name="integrationstatus",
    )
    integrationstatus_enum.create(op.get_bind(), checkfirst=True)

    fieldmappingtype_enum = postgresql.ENUM(
        "DIRECT",
        "TRANSFORMED",
        "COMPUTED",
        "LOOKUP",
        name="fieldmappingtype",
    )
    fieldmappingtype_enum.create(op.get_bind(), checkfirst=True)

    # Create integrations table
    op.create_table(
        "integrations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "platform",
            sa.Enum("WORKDAY", "GREENHOUSE", "LEVER", "BAMBOOHR", "ASHBY", name="integrationplatform"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "INACTIVE", "ERROR", "PENDING", name="integrationstatus"),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("credentials", postgresql.JSON(), nullable=False, server_default="{}"),
        sa.Column("organization_config", postgresql.JSON(), nullable=True),
        sa.Column("webhook_url", sa.String(512), nullable=True),
        sa.Column("sync_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sync_interval_minutes", sa.Integer(), nullable=True),
        sa.Column("last_sync_at", sa.String(50), nullable=True),
        sa.Column("last_sync_status", sa.String(50), nullable=True),
        sa.Column("error_message", sa.String(1000), nullable=True),
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
        comment="Store HRIS/ATS platform integration configurations and credentials",
    )
    op.create_index(op.f("ix_integrations_platform"), "integrations", ["platform"])
    op.create_index(op.f("ix_integrations_status"), "integrations", ["status"])

    # Create sync_logs table
    op.create_table(
        "sync_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "integration_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("integrations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sync_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("records_processed", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("records_successful", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("records_failed", sa.Integer(), nullable=True, server_default="0"),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_details", postgresql.JSON(), nullable=True),
        sa.Column("sync_metadata", postgresql.JSON(), nullable=True),
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
        comment="Track sync operations, errors, and status for monitoring",
    )
    op.create_index(op.f("ix_sync_logs_integration_id"), "sync_logs", ["integration_id"])
    op.create_index(op.f("ix_sync_logs_sync_type"), "sync_logs", ["sync_type"])
    op.create_index(op.f("ix_sync_logs_status"), "sync_logs", ["status"])

    # Create integration_mappings table
    op.create_table(
        "integration_mappings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "integration_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("integrations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_field", sa.String(255), nullable=False),
        sa.Column("target_field", sa.String(255), nullable=False),
        sa.Column(
            "mapping_type",
            sa.Enum("DIRECT", "TRANSFORMED", "COMPUTED", "LOOKUP", name="fieldmappingtype"),
            nullable=False,
            server_default="DIRECT",
        ),
        sa.Column("field_type", sa.String(50), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("transform_config", postgresql.JSON(), nullable=True),
        sa.Column("default_value", sa.String(500), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("validation_rule", sa.String(500), nullable=True),
        sa.Column("description", sa.String(500), nullable=True),
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
        comment="Configurable field mappings between internal and external systems",
    )
    op.create_index(op.f("ix_integration_mappings_integration_id"), "integration_mappings", ["integration_id"])
    op.create_index(op.f("ix_integration_mappings_source_field"), "integration_mappings", ["source_field"])
    op.create_index(op.f("ix_integration_mappings_target_field"), "integration_mappings", ["target_field"])
    op.create_index(op.f("ix_integration_mappings_mapping_type"), "integration_mappings", ["mapping_type"])
    op.create_index(op.f("ix_integration_mappings_is_active"), "integration_mappings", ["is_active"])
    op.create_index(op.f("ix_integration_mappings_priority"), "integration_mappings", ["priority"])


def downgrade() -> None:
    # Drop integration_mappings table
    op.drop_index(op.f("ix_integration_mappings_priority"), table_name="integration_mappings")
    op.drop_index(op.f("ix_integration_mappings_is_active"), table_name="integration_mappings")
    op.drop_index(op.f("ix_integration_mappings_mapping_type"), table_name="integration_mappings")
    op.drop_index(op.f("ix_integration_mappings_target_field"), table_name="integration_mappings")
    op.drop_index(op.f("ix_integration_mappings_source_field"), table_name="integration_mappings")
    op.drop_index(op.f("ix_integration_mappings_integration_id"), table_name="integration_mappings")
    op.drop_table("integration_mappings")

    # Drop sync_logs table
    op.drop_index(op.f("ix_sync_logs_status"), table_name="sync_logs")
    op.drop_index(op.f("ix_sync_logs_sync_type"), table_name="sync_logs")
    op.drop_index(op.f("ix_sync_logs_integration_id"), table_name="sync_logs")
    op.drop_table("sync_logs")

    # Drop integrations table
    op.drop_index(op.f("ix_integrations_status"), table_name="integrations")
    op.drop_index(op.f("ix_integrations_platform"), table_name="integrations")
    op.drop_table("integrations")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS fieldmappingtype")
    op.execute("DROP TYPE IF EXISTS integrationstatus")
    op.execute("DROP TYPE IF EXISTS integrationplatform")
