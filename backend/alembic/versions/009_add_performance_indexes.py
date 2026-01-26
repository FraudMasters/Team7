"""
Add performance indexes for frequently queried fields

Optimizes database queries by adding indexes on:
- Time-based queries (created_at, updated_at)
- Composite indexes for common filter patterns
- Status and active flag lookups
- Match percentage ordering for vacancy searches
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "009_add_performance_indexes"
down_revision: Union[str, None] = "008_add_score_appeals"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Indexes for resumes table
    # Time-based queries for filtering recent resumes
    op.create_index(
        op.f("ix_resumes_created_at"),
        "resumes",
        ["created_at"],
    )
    # Composite index for status filtering with time ordering
    op.create_index(
        op.f("ix_resumes_status_created_at"),
        "resumes",
        ["status", "created_at"],
    )
    # Index for language filtering
    op.create_index(
        op.f("ix_resumes_language"),
        "resumes",
        ["language"],
    )

    # Indexes for analysis_results table
    # Time-based queries for recent analysis results
    op.create_index(
        op.f("ix_analysis_results_created_at"),
        "analysis_results",
        ["created_at"],
    )

    # Indexes for job_vacancies table
    # Time-based queries for recent vacancies
    op.create_index(
        op.f("ix_job_vacancies_created_at"),
        "job_vacancies",
        ["created_at"],
    )
    # Index for industry filtering
    op.create_index(
        op.f("ix_job_vacancies_industry"),
        "job_vacancies",
        ["industry"],
    )
    # Composite index for industry + work_format filtering
    op.create_index(
        op.f("ix_job_vacancies_industry_work_format"),
        "job_vacancies",
        ["industry", "work_format"],
    )

    # Indexes for match_results table
    # Index for match_percentage sorting (finding best matches)
    op.create_index(
        op.f("ix_match_results_match_percentage"),
        "match_results",
        ["match_percentage"],
    )
    # Time-based queries for recent matches
    op.create_index(
        op.f("ix_match_results_created_at"),
        "match_results",
        ["created_at"],
    )
    # Composite index for vacancy_id + match_percentage (sorted matches per vacancy)
    op.create_index(
        op.f("ix_match_results_vacancy_id_match_percentage"),
        "match_results",
        ["vacancy_id", "match_percentage"],
    )

    # Indexes for skill_feedback table
    # Index for processed status filtering
    op.create_index(
        op.f("ix_skill_feedback_processed"),
        "skill_feedback",
        ["processed"],
    )
    # Time-based queries for recent feedback
    op.create_index(
        op.f("ix_skill_feedback_created_at"),
        "skill_feedback",
        ["created_at"],
    )
    # Index for skill-specific queries
    op.create_index(
        op.f("ix_skill_feedback_skill"),
        "skill_feedback",
        ["skill"],
    )

    # Indexes for ml_model_versions table
    # Index for active model lookups
    op.create_index(
        op.f("ix_ml_model_versions_is_active"),
        "ml_model_versions",
        ["is_active"],
    )
    # Index for experiment filtering
    op.create_index(
        op.f("ix_ml_model_versions_is_experiment"),
        "ml_model_versions",
        ["is_experiment"],
    )
    # Composite index for model_name + is_active (finding active model by name)
    op.create_index(
        op.f("ix_ml_model_versions_model_name_is_active"),
        "ml_model_versions",
        ["model_name", "is_active"],
    )

    # Indexes for skill_taxonomies table
    # Index for active filtering
    op.create_index(
        op.f("ix_skill_taxonomies_is_active"),
        "skill_taxonomies",
        ["is_active"],
    )

    # Indexes for custom_synonyms table
    # Index for active filtering
    op.create_index(
        op.f("ix_custom_synonyms_is_active"),
        "custom_synonyms",
        ["is_active"],
    )


def downgrade() -> None:
    # Drop custom_synonyms indexes
    op.drop_index(
        op.f("ix_custom_synonyms_is_active"),
        table_name="custom_synonyms",
    )

    # Drop skill_taxonomies indexes
    op.drop_index(
        op.f("ix_skill_taxonomies_is_active"),
        table_name="skill_taxonomies",
    )

    # Drop ml_model_versions indexes
    op.drop_index(
        op.f("ix_ml_model_versions_model_name_is_active"),
        table_name="ml_model_versions",
    )
    op.drop_index(
        op.f("ix_ml_model_versions_is_experiment"),
        table_name="ml_model_versions",
    )
    op.drop_index(
        op.f("ix_ml_model_versions_is_active"),
        table_name="ml_model_versions",
    )

    # Drop skill_feedback indexes
    op.drop_index(
        op.f("ix_skill_feedback_skill"),
        table_name="skill_feedback",
    )
    op.drop_index(
        op.f("ix_skill_feedback_created_at"),
        table_name="skill_feedback",
    )
    op.drop_index(
        op.f("ix_skill_feedback_processed"),
        table_name="skill_feedback",
    )

    # Drop match_results indexes
    op.drop_index(
        op.f("ix_match_results_vacancy_id_match_percentage"),
        table_name="match_results",
    )
    op.drop_index(
        op.f("ix_match_results_created_at"),
        table_name="match_results",
    )
    op.drop_index(
        op.f("ix_match_results_match_percentage"),
        table_name="match_results",
    )

    # Drop job_vacancies indexes
    op.drop_index(
        op.f("ix_job_vacancies_industry_work_format"),
        table_name="job_vacancies",
    )
    op.drop_index(
        op.f("ix_job_vacancies_industry"),
        table_name="job_vacancies",
    )
    op.drop_index(
        op.f("ix_job_vacancies_created_at"),
        table_name="job_vacancies",
    )

    # Drop analysis_results indexes
    op.drop_index(
        op.f("ix_analysis_results_created_at"),
        table_name="analysis_results",
    )

    # Drop resumes indexes
    op.drop_index(
        op.f("ix_resumes_language"),
        table_name="resumes",
    )
    op.drop_index(
        op.f("ix_resumes_status_created_at"),
        table_name="resumes",
    )
    op.drop_index(
        op.f("ix_resumes_created_at"),
        table_name="resumes",
    )
