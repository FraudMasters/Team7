"""
Add LinkedIn outreach tracking table

Creates table for:
- linkedin_outreach: Track individual LinkedIn outreach messages and responses
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260322_create_linkedin_outreach"
down_revision: Union[str, None] = "20260322_create_linkedin_campaign"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create linkedin_outreach table
    op.create_table(
        "linkedin_outreach",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "campaign_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("linkedin_campaigns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "linkedin_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("linkedin_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "recruiter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recruiters.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("message_subject", sa.String(255), nullable=True),
        sa.Column("message_body", sa.Text(), nullable=True),
        sa.Column(
            "message_sent_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "response_received_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "response_status",
            sa.String(50),
            nullable=False,
            server_default="no_response",
        ),
        sa.Column("response_text", sa.Text(), nullable=True),
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
        comment="Track individual LinkedIn outreach messages and responses",
    )
    op.create_index(
        op.f("ix_linkedin_outreach_campaign_id"),
        "linkedin_outreach",
        ["campaign_id"],
    )
    op.create_index(
        op.f("ix_linkedin_outreach_linkedin_profile_id"),
        "linkedin_outreach",
        ["linkedin_profile_id"],
    )
    op.create_index(
        op.f("ix_linkedin_outreach_recruiter_id"),
        "linkedin_outreach",
        ["recruiter_id"],
    )
    op.create_index(
        op.f("ix_linkedin_outreach_message_sent_at"),
        "linkedin_outreach",
        ["message_sent_at"],
    )
    op.create_index(
        op.f("ix_linkedin_outreach_response_status"),
        "linkedin_outreach",
        ["response_status"],
    )


def downgrade() -> None:
    # Drop linkedin_outreach table
    op.drop_index(
        op.f("ix_linkedin_outreach_response_status"),
        table_name="linkedin_outreach",
    )
    op.drop_index(
        op.f("ix_linkedin_outreach_message_sent_at"),
        table_name="linkedin_outreach",
    )
    op.drop_index(
        op.f("ix_linkedin_outreach_recruiter_id"),
        table_name="linkedin_outreach",
    )
    op.drop_index(
        op.f("ix_linkedin_outreach_linkedin_profile_id"),
        table_name="linkedin_outreach",
    )
    op.drop_index(
        op.f("ix_linkedin_outreach_campaign_id"),
        table_name="linkedin_outreach",
    )
    op.drop_table("linkedin_outreach")
