"""
Add candidate_appeals table

Creates table for:
- candidate_appeals: Candidate appeals against ranking decisions with tracking and resolution
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "041_add_enhanced_explainability"
down_revision: Union[str, None] = "070_add_candidate_recommendations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create candidate_appeals table
    op.create_table(
        "candidate_appeals",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "candidate_rank_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidate_ranks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("candidate_email", sa.String(255), nullable=False),
        sa.Column("appeal_type", sa.String(50), nullable=False),
        sa.Column("appeal_text", sa.Text(), nullable=False),
        sa.Column("supporting_documents", postgresql.JSON(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column(
            "reviewer_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("resolution_outcome", sa.String(50), nullable=True),
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
        comment="Candidate appeals against ranking decisions with tracking and resolution",
    )
    op.create_index(op.f("ix_candidate_appeals_candidate_rank_id"), "candidate_appeals", ["candidate_rank_id"])
    op.create_index(op.f("ix_candidate_appeals_status"), "candidate_appeals", ["status"])
    op.create_index(op.f("ix_candidate_appeals_candidate_email"), "candidate_appeals", ["candidate_email"])


def downgrade() -> None:
    # Drop candidate_appeals table
    op.drop_index(op.f("ix_candidate_appeals_candidate_email"), table_name="candidate_appeals")
    op.drop_index(op.f("ix_candidate_appeals_status"), table_name="candidate_appeals")
    op.drop_index(op.f("ix_candidate_appeals_candidate_rank_id"), table_name="candidate_appeals")
    op.drop_table("candidate_appeals")
