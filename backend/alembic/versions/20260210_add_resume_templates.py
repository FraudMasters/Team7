"""Add resume templates table

Creates table for:
- resume_templates: Store customizable resume formatting templates for job seekers
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260210_add_resume_templates"
down_revision: Union[str, None] = "20260210_add_job_application_models"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create resume_templates table
    op.create_table(
        "resume_templates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "organization_id",
            sa.String(255),
            nullable=True,
            comment="ID of the organization this template belongs to (None for global templates)",
        ),
        sa.Column(
            "name",
            sa.String(255),
            nullable=False,
            comment="Template name (e.g., 'Modern', 'Classic', 'Creative')",
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="Optional description of the template style",
        ),
        sa.Column(
            "template_type",
            sa.String(100),
            nullable=False,
            comment="Type of resume template (e.g., 'modern', 'classic', 'creative', 'ats_friendly')",
        ),
        sa.Column(
            "layout_config",
            postgresql.JSON(),
            nullable=True,
            comment="JSON configuration for layout (margins, sections, spacing, etc.)",
        ),
        sa.Column(
            "style_config",
            postgresql.JSON(),
            nullable=True,
            comment="JSON configuration for styling (colors, fonts, headings, etc.)",
        ),
        sa.Column(
            "section_config",
            postgresql.JSON(),
            nullable=True,
            comment="JSON configuration for which sections to include and their order",
        ),
        sa.Column(
            "preview_url",
            sa.String(512),
            nullable=True,
            comment="Optional URL to a preview image of the template",
        ),
        sa.Column(
            "is_default",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="Whether this is the default template for the organization/global",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default="true",
            comment="Whether this template is active and available for use",
        ),
        sa.Column(
            "is_ats_compliant",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="Whether this template is ATS-friendly (optimized for applicant tracking systems)",
        ),
        sa.Column(
            "created_by",
            sa.String(255),
            nullable=True,
            comment="ID of the user who created this template",
        ),
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
        comment="Store customizable resume formatting templates for job seekers",
    )
    op.create_index(op.f("ix_resume_templates_organization_id"), "resume_templates", ["organization_id"])
    op.create_index(op.f("ix_resume_templates_template_type"), "resume_templates", ["template_type"])
    op.create_index(op.f("ix_resume_templates_is_active"), "resume_templates", ["is_active"])
    op.create_index(op.f("ix_resume_templates_is_ats_compliant"), "resume_templates", ["is_ats_compliant"])


def downgrade() -> None:
    # Drop resume_templates table
    op.drop_index(op.f("ix_resume_templates_is_ats_compliant"), table_name="resume_templates")
    op.drop_index(op.f("ix_resume_templates_is_active"), table_name="resume_templates")
    op.drop_index(op.f("ix_resume_templates_template_type"), table_name="resume_templates")
    op.drop_index(op.f("ix_resume_templates_organization_id"), table_name="resume_templates")
    op.drop_table("resume_templates")
