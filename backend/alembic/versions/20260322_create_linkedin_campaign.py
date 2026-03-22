"""
Add LinkedIn campaign tracking table

Creates table for:
- linkedin_campaigns: Track LinkedIn outreach campaigns and performance metrics
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260322_create_linkedin_campaign"
down_revision: Union[str, None] = "20260322_add_resume_source"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create linkedin_campaigns table
    op.create_table(
        "linkedin_campaigns",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "recruiter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recruiters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "vacancy_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_vacancies.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("target_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("sent_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("response_count", sa.Integer(), nullable=True, server_default="0"),
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
        comment="Track LinkedIn outreach campaigns and performance metrics",
    )
    op.create_index(op.f("ix_linkedin_campaigns_recruiter_id"), "linkedin_campaigns", ["recruiter_id"])
    op.create_index(op.f("ix_linkedin_campaigns_vacancy_id"), "linkedin_campaigns", ["vacancy_id"])
    op.create_index(op.f("ix_linkedin_campaigns_status"), "linkedin_campaigns", ["status"])


def downgrade() -> None:
    # Drop linkedin_campaigns table
    op.drop_index(op.f("ix_linkedin_campaigns_status"), table_name="linkedin_campaigns")
    op.drop_index(op.f("ix_linkedin_campaigns_vacancy_id"), table_name="linkedin_campaigns")
    op.drop_index(op.f("ix_linkedin_campaigns_recruiter_id"), table_name="linkedin_campaigns")
    op.drop_table("linkedin_campaigns")
