"""
Add search analytics tables

Creates three new tables for search analytics:
- search_queries: Tracks all search queries performed in the system
- popular_searches: Aggregated statistics for popular search queries
- recent_searches: Per-user recent search history with unique constraint on recruiter_id and query
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = "20260321_add_search_analytics_tables"
down_revision: Union[str, None] = "20260212_add_alert_settings_to_saved_search"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create search_queries table
    op.create_table(
        "search_queries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "recruiter_id",
            UUID(as_uuid=True),
            sa.ForeignKey("recruiters.id", ondelete="SET NULL"),
            nullable=True,
            comment="Foreign key to Recruiter who performed the search",
        ),
        sa.Column(
            "query",
            sa.Text(),
            nullable=False,
            comment="Search query string with boolean operators",
        ),
        sa.Column(
            "filters",
            sa.JSON(),
            nullable=True,
            server_default="{}",
            comment="Filter settings in JSON format (skills, experience_years, location, language, etc.)",
        ),
        sa.Column(
            "results_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Number of results returned by the search",
        ),
        sa.Column(
            "execution_time_ms",
            sa.Float(),
            nullable=True,
            comment="Time taken to execute the search in milliseconds",
        ),
        sa.Column(
            "search_type",
            sa.String(50),
            nullable=True,
            comment="Type of search performed (e.g., 'full_text', 'faceted', 'boolean')",
        ),
        sa.Column(
            "clicked_result_ids",
            sa.JSON(),
            nullable=True,
            server_default="[]",
            comment="Array of resume IDs that were clicked from results",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Create indexes for search_queries table
    op.create_index(
        op.f("ix_search_queries_recruiter_id"),
        "search_queries",
        ["recruiter_id"],
    )
    op.create_index(
        op.f("ix_search_queries_query"),
        "search_queries",
        ["query"],
    )
    op.create_index(
        op.f("ix_search_queries_results_count"),
        "search_queries",
        ["results_count"],
    )
    op.create_index(
        op.f("ix_search_queries_search_type"),
        "search_queries",
        ["search_type"],
    )

    # Create popular_searches table
    op.create_table(
        "popular_searches",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "query",
            sa.Text(),
            nullable=False,
            unique=True,
            comment="Search query string",
        ),
        sa.Column(
            "filters",
            sa.JSON(),
            nullable=True,
            server_default="{}",
            comment="Common filter settings for this query in JSON format",
        ),
        sa.Column(
            "search_count",
            sa.Integer(),
            nullable=False,
            server_default="1",
            comment="Number of times this query has been searched",
        ),
        sa.Column(
            "avg_results_count",
            sa.Float(),
            nullable=True,
            comment="Average number of results returned",
        ),
        sa.Column(
            "avg_click_through_rate",
            sa.Float(),
            nullable=True,
            comment="Average click-through rate (clicks / results)",
        ),
        sa.Column(
            "last_searched_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Timestamp when this query was last searched",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Create indexes for popular_searches table
    op.create_index(
        op.f("ix_popular_searches_query"),
        "popular_searches",
        ["query"],
    )
    op.create_index(
        op.f("ix_popular_searches_search_count"),
        "popular_searches",
        ["search_count"],
    )
    op.create_index(
        op.f("ix_popular_searches_last_searched_at"),
        "popular_searches",
        ["last_searched_at"],
    )

    # Create recent_searches table
    op.create_table(
        "recent_searches",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "recruiter_id",
            UUID(as_uuid=True),
            sa.ForeignKey("recruiters.id", ondelete="CASCADE"),
            nullable=False,
            comment="Foreign key to Recruiter who performed the search",
        ),
        sa.Column(
            "query",
            sa.Text(),
            nullable=False,
            comment="Search query string with boolean operators",
        ),
        sa.Column(
            "filters",
            sa.JSON(),
            nullable=True,
            server_default="{}",
            comment="Filter settings in JSON format (skills, experience_years, location, language, etc.)",
        ),
        sa.Column(
            "results_count",
            sa.Integer(),
            nullable=True,
            comment="Number of results returned by the search",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Create indexes for recent_searches table
    op.create_index(
        op.f("ix_recent_searches_recruiter_id"),
        "recent_searches",
        ["recruiter_id"],
    )

    # Create unique constraint for recent_searches
    op.create_unique_constraint(
        "uq_recent_search_recruiter_query",
        "recent_searches",
        ["recruiter_id", "query"],
    )


def downgrade() -> None:
    # Drop recent_searches table
    op.drop_constraint("uq_recent_search_recruiter_query", "recent_searches", type_="unique")
    op.drop_index(op.f("ix_recent_searches_recruiter_id"), table_name="recent_searches")
    op.drop_table("recent_searches")

    # Drop popular_searches table
    op.drop_index(op.f("ix_popular_searches_last_searched_at"), table_name="popular_searches")
    op.drop_index(op.f("ix_popular_searches_search_count"), table_name="popular_searches")
    op.drop_index(op.f("ix_popular_searches_query"), table_name="popular_searches")
    op.drop_table("popular_searches")

    # Drop search_queries table
    op.drop_index(op.f("ix_search_queries_search_type"), table_name="search_queries")
    op.drop_index(op.f("ix_search_queries_results_count"), table_name="search_queries")
    op.drop_index(op.f("ix_search_queries_query"), table_name="search_queries")
    op.drop_index(op.f("ix_search_queries_recruiter_id"), table_name="search_queries")
    op.drop_table("search_queries")
