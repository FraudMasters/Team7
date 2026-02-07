"""
Add LinkedIn tokens table for encrypted OAuth token storage.

Creates table for:
- linkedin_tokens: Store encrypted LinkedIn OAuth access tokens
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260203_add_linkedin_tokens"
down_revision: Union[str, None] = "20260203_add_linkedin_integration"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create linkedin_tokens table
    op.create_table(
        "linkedin_tokens",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "recruiter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recruiters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "access_token_encrypted",
            sa.Text(),
            nullable=False,
            comment="Encrypted LinkedIn OAuth access token (Fernet-encrypted)",
        ),
        sa.Column(
            "refresh_token_encrypted",
            sa.Text(),
            nullable=True,
            comment="Encrypted LinkedIn OAuth refresh token (Fernet-encrypted)",
        ),
        sa.Column(
            "token_expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Token expiration timestamp",
        ),
        sa.Column(
            "linkedin_member_id",
            sa.String(100),
            nullable=True,
            comment="LinkedIn member ID for profile linking",
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
        comment="Store encrypted LinkedIn OAuth access tokens",
    )

    # Create indexes
    op.create_index(
        op.f("ix_linkedin_tokens_recruiter_id"),
        "linkedin_tokens",
        ["recruiter_id"],
        unique=True,  # One active token per recruiter
    )
    op.create_index(
        op.f("ix_linkedin_tokens_linkedin_member_id"),
        "linkedin_tokens",
        ["linkedin_member_id"],
    )
    op.create_index(
        op.f("ix_linkedin_tokens_token_expires_at"),
        "linkedin_tokens",
        ["token_expires_at"],
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(
        op.f("ix_linkedin_tokens_token_expires_at"),
        table_name="linkedin_tokens",
    )
    op.drop_index(
        op.f("ix_linkedin_tokens_linkedin_member_id"),
        table_name="linkedin_tokens",
    )
    op.drop_index(
        op.f("ix_linkedin_tokens_recruiter_id"),
        table_name="linkedin_tokens",
    )

    # Drop table
    op.drop_table("linkedin_tokens")
