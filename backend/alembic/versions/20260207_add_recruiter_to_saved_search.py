"""
Add recruiter_id to saved_searches table

Adds:
- recruiter_id: Foreign key to recruiters table for tracking which recruiter created each saved search
- Index on recruiter_id for efficient filtering by recruiter
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260207_add_recruiter_to_saved_search"
down_revision: Union[str, None] = "20260201_add_search_performance_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add recruiter_id column to saved_searches table
    # Making it nullable initially to handle existing data
    op.add_column(
        "saved_searches",
        sa.Column(
            "recruiter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recruiters.id", ondelete="CASCADE"),
            nullable=True,
            comment="Foreign key reference to the recruiter who created this saved search",
        ),
    )

    # Create index on recruiter_id for efficient filtering
    op.create_index(
        op.f("ix_saved_searches_recruiter_id"),
        "saved_searches",
        ["recruiter_id"],
    )


def downgrade() -> None:
    # Drop the index
    op.drop_index(op.f("ix_saved_searches_recruiter_id"), table_name="saved_searches")

    # Drop the column
    op.drop_column("saved_searches", "recruiter_id")
