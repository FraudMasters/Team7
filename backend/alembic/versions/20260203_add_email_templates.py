"""
Add email templates table

Creates tables for:
- email_templates: Store customizable email templates with organization branding support
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260203_add_email_templates"
down_revision: Union[str, None] = "20260203_add_organizations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create email_templates table
    op.create_table(
        "email_templates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("organization_id", sa.String(255), nullable=False),
        sa.Column("template_type", sa.String(100), nullable=False),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("variables", postgresql.JSON(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
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
        comment="Store customizable email templates with organization branding support",
    )
    op.create_index(
        op.f("ix_email_templates_organization_id"), "email_templates", ["organization_id"]
    )
    op.create_index(
        op.f("ix_email_templates_template_type"), "email_templates", ["template_type"]
    )


def downgrade() -> None:
    # Drop email_templates table
    op.drop_index(
        op.f("ix_email_templates_template_type"), table_name="email_templates"
    )
    op.drop_index(
        op.f("ix_email_templates_organization_id"), table_name="email_templates"
    )
    op.drop_table("email_templates")
