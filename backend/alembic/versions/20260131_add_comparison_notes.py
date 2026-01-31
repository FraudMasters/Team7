"""
Add notes field to resume_comparisons table

Adds optional notes field for storing recruiter notes and observations
about candidate comparisons
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260131_add_comparison_notes"
down_revision: Union[str, None] = "20260131_add_comparison_name"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add notes column to resume_comparisons table
    op.add_column(
        "resume_comparisons",
        sa.Column("notes", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    # Remove notes column from resume_comparisons table
    op.drop_column("resume_comparisons", "notes")
