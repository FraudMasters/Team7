"""
Add SMS templates table

Creates tables for:
- sms_templates: Store customizable SMS templates with character count and segment tracking
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260322_add_sms_templates"
down_revision: Union[str, None] = "20260322_enhance_email_templates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create sms_templates table
    op.create_table(
        "sms_templates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("variables", postgresql.JSON(), nullable=True),
        sa.Column("template_blocks", postgresql.JSON(), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("pipeline_stage", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("language", sa.String(10), nullable=False, server_default="'en'"),
        sa.Column("description", sa.Text(), nullable=True),
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
        comment="Store customizable SMS templates with character count and segment tracking",
    )
    op.create_index(
        op.f("ix_sms_templates_name"), "sms_templates", ["name"]
    )
    op.create_index(
        op.f("ix_sms_templates_category"), "sms_templates", ["category"]
    )
    op.create_index(
        op.f("ix_sms_templates_pipeline_stage"), "sms_templates", ["pipeline_stage"]
    )


def downgrade() -> None:
    # Drop sms_templates table
    op.drop_index(
        op.f("ix_sms_templates_pipeline_stage"), table_name="sms_templates"
    )
    op.drop_index(
        op.f("ix_sms_templates_category"), table_name="sms_templates"
    )
    op.drop_index(
        op.f("ix_sms_templates_name"), table_name="sms_templates"
    )
    op.drop_table("sms_templates")
