"""
Add name field to resume_comparisons table

Adds optional name field for identifying comparison views
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260131_add_comparison_name"
down_revision: Union[str, None] = "20260131_add_work_experience_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add name column to resume_comparisons table
    op.add_column(
        "resume_comparisons",
        sa.Column("name", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    # Remove name column from resume_comparisons table
    op.drop_column("resume_comparisons", "name")
