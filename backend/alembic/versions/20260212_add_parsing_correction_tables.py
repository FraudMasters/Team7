"""Add parsing correction and learning feedback tables

Creates tables for:
- parsing_corrections: Track user corrections to AI-parsed resume fields
- learning_feedbacks: Store aggregated correction feedback for parser improvement
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260212_add_parsing_correction_tables"
down_revision: Union[str, None] = "20260210_add_resume_templates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create parsing_corrections table
    op.create_table(
        "parsing_corrections",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resume_id", sa.UUID(), nullable=False),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("original_value", postgresql.JSON(), nullable=True),
        sa.Column("corrected_value", postgresql.JSON(), nullable=True),
        sa.Column("reason", sa.String(100), nullable=True),
        sa.Column("source_text_location", postgresql.JSON(), nullable=True),
        sa.Column("corrected_by", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_parsing_corrections_resume_id"), "parsing_corrections", ["resume_id"], unique=False
    )
    op.create_index(
        op.f("ix_parsing_corrections_field_name"), "parsing_corrections", ["field_name"], unique=False
    )

    # Create learning_feedbacks table
    op.create_table(
        "learning_feedbacks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("correction_id", sa.UUID(), nullable=True),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("error_pattern", sa.Text(), nullable=True),
        sa.Column("suggestion", sa.Text(), nullable=True),
        sa.Column("pattern_type", sa.String(50), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("sample_count", sa.Integer(), nullable=True),
        sa.Column("examples", postgresql.JSON(), nullable=True),
        sa.Column("parser_version", sa.String(50), nullable=True),
        sa.Column("is_applied", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(
            ["correction_id"], ["parsing_corrections.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_learning_feedbacks_correction_id"),
        "learning_feedbacks",
        ["correction_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_learning_feedbacks_field_name"), "learning_feedbacks", ["field_name"], unique=False
    )


def downgrade() -> None:
    # Drop learning_feedbacks table
    op.drop_index(op.f("ix_learning_feedbacks_field_name"), table_name="learning_feedbacks")
    op.drop_index(op.f("ix_learning_feedbacks_correction_id"), table_name="learning_feedbacks")
    op.drop_table("learning_feedbacks")

    # Drop parsing_corrections table
    op.drop_index(op.f("ix_parsing_corrections_field_name"), table_name="parsing_corrections")
    op.drop_index(op.f("ix_parsing_corrections_resume_id"), table_name="parsing_corrections")
    op.drop_table("parsing_corrections")
