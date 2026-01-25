"""
Add resume_comparisons table

Creates table for:
- resume_comparisons: Store saved multi-resume comparison views with filters and sharing settings
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003_add_resume_comparisons"
down_revision: Union[str, None] = "002_add_advanced_matching"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create resume_comparisons table
    op.create_table(
        "resume_comparisons",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "vacancy_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_vacancies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("resume_ids", postgresql.JSON(), nullable=False, server_default="[]"),
        sa.Column("filters", postgresql.JSON(), nullable=True),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("shared_with", postgresql.JSON(), nullable=True, server_default="[]"),
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
        comment="Store saved multi-resume comparison views with filters and sharing settings",
    )
    op.create_index(op.f("ix_resume_comparisons_vacancy_id"), "resume_comparisons", ["vacancy_id"])


def downgrade() -> None:
    # Drop resume_comparisons table
    op.drop_index(op.f("ix_resume_comparisons_vacancy_id"), table_name="resume_comparisons")
    op.drop_table("resume_comparisons")
