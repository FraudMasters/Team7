"""
Add search performance indexes for advanced filtering

Optimizes advanced search queries by adding indexes on:
- Location filtering (resumes.location)
- Experience filtering (resumes.total_experience_months)
- Composite indexes for common filter combinations
- Ensures sub-2 second response times for complex searches
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260201_add_search_performance_indexes"
down_revision: Union[str, None] = "016_add_workflow_stage_config"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Indexes for resumes table - advanced search filtering

    # Index for location filtering (geo-based searches)
    op.create_index(
        op.f("ix_resumes_location"),
        "resumes",
        ["location"],
    )

    # Index for experience filtering (years of experience searches)
    op.create_index(
        op.f("ix_resumes_total_experience_months"),
        "resumes",
        ["total_experience_months"],
    )

    # Composite index for location + status (active candidates in specific locations)
    op.create_index(
        op.f("ix_resumes_location_status"),
        "resumes",
        ["location", "status"],
    )

    # Composite index for experience + status (qualified active candidates)
    op.create_index(
        op.f("ix_resumes_total_experience_months_status"),
        "resumes",
        ["total_experience_months", "status"],
    )

    # Composite index for language + status (language-specific active candidates)
    op.create_index(
        op.f("ix_resumes_language_status"),
        "resumes",
        ["language", "status"],
    )

    # Composite index for location + experience (geo-experience combined searches)
    op.create_index(
        op.f("ix_resumes_location_total_experience_months"),
        "resumes",
        ["location", "total_experience_months"],
    )

    # Composite index for location + experience + status (complex filtered searches)
    op.create_index(
        op.f("ix_resumes_location_total_experience_months_status"),
        "resumes",
        ["location", "total_experience_months", "status"],
    )


def downgrade() -> None:
    # Drop composite index
    op.drop_index(
        op.f("ix_resumes_location_total_experience_months_status"),
        table_name="resumes",
    )

    # Drop composite index
    op.drop_index(
        op.f("ix_resumes_location_total_experience_months"),
        table_name="resumes",
    )

    # Drop composite index
    op.drop_index(
        op.f("ix_resumes_language_status"),
        table_name="resumes",
    )

    # Drop composite index
    op.drop_index(
        op.f("ix_resumes_total_experience_months_status"),
        table_name="resumes",
    )

    # Drop composite index
    op.drop_index(
        op.f("ix_resumes_location_status"),
        table_name="resumes",
    )

    # Drop experience index
    op.drop_index(
        op.f("ix_resumes_total_experience_months"),
        table_name="resumes",
    )

    # Drop location index
    op.drop_index(
        op.f("ix_resumes_location"),
        table_name="resumes",
    )
