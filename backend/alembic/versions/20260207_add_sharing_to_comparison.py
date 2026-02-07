"""
Add sharing fields to resume_comparisons table

Adds:
- share_id: Unique string identifier for public/private link sharing
- share_expires_at: Optional timestamp when the share link expires
- share_permissions: Optional JSON object with permission settings (view_only, can_edit, etc.)
- Index on share_id for efficient lookups
- Unique constraint on share_id to prevent collisions
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260207_add_sharing_to_comparison"
down_revision: Union[str, None] = "20260207_add_recruiter_to_saved_search"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add share_id column to resume_comparisons table
    # Nullable, only set when comparison is shared via link
    op.add_column(
        "resume_comparisons",
        sa.Column(
            "share_id",
            sa.String(100),
            nullable=True,
            comment="Unique string identifier for sharing comparisons via public/private link",
        ),
    )

    # Add share_expires_at column for optional link expiration
    op.add_column(
        "resume_comparisons",
        sa.Column(
            "share_expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Optional timestamp when the share link expires",
        ),
    )

    # Add share_permissions column for permission settings
    op.add_column(
        "resume_comparisons",
        sa.Column(
            "share_permissions",
            sa.JSON(),
            nullable=True,
            comment="Optional JSON object with permission settings (view_only, can_edit, etc.)",
        ),
    )

    # Create unique index on share_id for efficient lookups and uniqueness
    op.create_index(
        op.f("ix_resume_comparisons_share_id"),
        "resume_comparisons",
        ["share_id"],
        unique=True,
    )


def downgrade() -> None:
    # Drop the index
    op.drop_index(op.f("ix_resume_comparisons_share_id"), table_name="resume_comparisons")

    # Drop the columns
    op.drop_column("resume_comparisons", "share_permissions")
    op.drop_column("resume_comparisons", "share_expires_at")
    op.drop_column("resume_comparisons", "share_id")
