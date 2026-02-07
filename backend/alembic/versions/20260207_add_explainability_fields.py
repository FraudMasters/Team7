"""Add explainability fields to candidate_ranks

Revision ID: 20260207_add_explainability_fields
Revises: 018_add_interview_prep
Create Date: 2026-02-07

This migration adds enhanced explainability fields to the candidate_ranks table:
- explanation_narrative: Natural language explanation from LLM (1-3 sentences)
- confidence_interval: JSON object with lower/upper bounds for uncertainty
- resume_highlights: JSON mapping features to resume sections for highlighting

These fields support the Enhanced Explainability Dashboard feature which provides
comprehensive explanations of AI ranking decisions to recruiters and hiring managers.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260207_add_explainability_fields"
down_revision: Union[str, None] = "018_add_interview_prep"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add explainability fields to candidate_ranks table."""

    # Add explanation_narrative column for LLM-generated natural language explanations
    op.add_column(
        'candidate_ranks',
        sa.Column(
            'explanation_narrative',
            sa.Text(),
            nullable=True,
            comment='LLM-generated natural language explanation (1-3 sentences)'
        ),
    )

    # Add confidence_interval column for uncertainty bounds
    op.add_column(
        'candidate_ranks',
        sa.Column(
            'confidence_interval',
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
            comment='JSON object with lower/upper bounds for uncertainty (e.g., {"lower": 0.65, "upper": 0.85})'
        ),
    )

    # Add resume_highlights column for feature-to-section mapping
    op.add_column(
        'candidate_ranks',
        sa.Column(
            'resume_highlights',
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
            comment='JSON mapping features to resume sections for highlighting (e.g., {"skills_match": {"section": "skills", "offset": 100, "length": 50}})'
        ),
    )


def downgrade() -> None:
    """Remove explainability fields from candidate_ranks table."""

    # Drop columns in reverse order
    op.drop_column('candidate_ranks', 'resume_highlights')
    op.drop_column('candidate_ranks', 'confidence_interval')
    op.drop_column('candidate_ranks', 'explanation_narrative')
