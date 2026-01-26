"""
Add full-text search, saved searches, and alerts tables

Adds:
- search_vector, total_experience_months, location columns to resumes table
- saved_searches: Store user search queries and filter configurations
- search_alerts: Store notifications when new resumes match saved searches
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "007_add_resume_search"
down_revision: Union[str, None] = "006_add_candidate_feedback"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add full-text search and filter columns to resumes table
    op.add_column(
        "resumes",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            nullable=True,
            comment="PostgreSQL tsvector for full-text search",
        ),
    )
    op.add_column(
        "resumes",
        sa.Column(
            "total_experience_months",
            sa.Integer(),
            nullable=True,
            comment="Total work experience in months for filtering",
        ),
    )
    op.add_column(
        "resumes",
        sa.Column(
            "location",
            sa.String(255),
            nullable=True,
            comment="Candidate's location for filtering",
        ),
    )
    # Create index for full-text search
    op.create_index(
        op.f("ix_resumes_search_vector"),
        "resumes",
        ["search_vector"],
        postgresql_using="gin",
    )

    # Create saved_searches table
    op.create_table(
        "saved_searches",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False, comment="User-provided name for the saved search"),
        sa.Column("query", sa.Text(), nullable=False, comment="Search query string with boolean operators"),
        sa.Column(
            "filters",
            postgresql.JSON(),
            nullable=True,
            server_default="{}",
            comment="Filter settings (skills, experience_years, location, language, etc.)",
        ),
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
        comment="Store user search queries and filter configurations",
    )
    op.create_index(op.f("ix_saved_searches_name"), "saved_searches", ["name"])

    # Create search_alerts table
    op.create_table(
        "search_alerts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "saved_search_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("saved_searches.id", ondelete="CASCADE"),
            nullable=False,
            comment="Foreign key reference to the saved search that triggered this alert",
        ),
        sa.Column(
            "resume_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resumes.id", ondelete="CASCADE"),
            nullable=False,
            comment="Foreign key reference to the new resume that matched the search criteria",
        ),
        sa.Column(
            "is_sent",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="Boolean flag indicating whether the notification has been sent",
        ),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Timestamp when the notification was successfully sent",
        ),
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
            comment="Error message if notification sending failed",
        ),
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
        comment="Store notifications when new resumes match saved searches",
    )
    op.create_index(op.f("ix_search_alerts_saved_search_id"), "search_alerts", ["saved_search_id"])
    op.create_index(op.f("ix_search_alerts_resume_id"), "search_alerts", ["resume_id"])
    op.create_index(op.f("ix_search_alerts_is_sent"), "search_alerts", ["is_sent"])


def downgrade() -> None:
    # Drop search_alerts table
    op.drop_index(op.f("ix_search_alerts_is_sent"), table_name="search_alerts")
    op.drop_index(op.f("ix_search_alerts_resume_id"), table_name="search_alerts")
    op.drop_index(op.f("ix_search_alerts_saved_search_id"), table_name="search_alerts")
    op.drop_table("search_alerts")

    # Drop saved_searches table
    op.drop_index(op.f("ix_saved_searches_name"), table_name="saved_searches")
    op.drop_table("saved_searches")

    # Drop full-text search and filter columns from resumes table
    op.drop_index(op.f("ix_resumes_search_vector"), table_name="resumes")
    op.drop_column("resumes", "location")
    op.drop_column("resumes", "total_experience_months")
    op.drop_column("resumes", "search_vector")
