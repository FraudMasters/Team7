"""
Add alert settings fields to saved_searches table

Adds:
- alert_enabled: Boolean flag to enable/disable automatic alerts for saved searches
- alert_frequency: String field for alert frequency (e.g., 'daily', 'weekly', 'realtime')
- last_alert_at: Timestamp tracking when the last alert was sent for this search
- Index on alert_enabled for efficient filtering of active alerts
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260212_add_alert_settings_to_saved_search"
down_revision: Union[str, None] = "20260212_add_parsing_correction_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add alert_enabled column to saved_searches table
    # Using server_default to handle existing rows
    op.add_column(
        "saved_searches",
        sa.Column(
            "alert_enabled",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="Whether automatic alerts are enabled for this saved search",
        ),
    )

    # Create index on alert_enabled for efficient filtering of active alerts
    op.create_index(
        op.f("ix_saved_searches_alert_enabled"),
        "saved_searches",
        ["alert_enabled"],
    )

    # Add alert_frequency column to saved_searches table
    # Nullable since not all saved searches will have alerts enabled
    op.add_column(
        "saved_searches",
        sa.Column(
            "alert_frequency",
            sa.String(20),
            nullable=True,
            comment="Frequency of alerts (e.g., 'daily', 'weekly', 'realtime')",
        ),
    )

    # Add last_alert_at column to saved_searches table
    # Nullable since new saved searches won't have any alerts sent yet
    op.add_column(
        "saved_searches",
        sa.Column(
            "last_alert_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Timestamp when the last alert was sent for this search",
        ),
    )


def downgrade() -> None:
    # Drop the columns in reverse order
    op.drop_column("saved_searches", "last_alert_at")
    op.drop_column("saved_searches", "alert_frequency")

    # Drop the index
    op.drop_index(op.f("ix_saved_searches_alert_enabled"), table_name="saved_searches")

    # Drop the column
    op.drop_column("saved_searches", "alert_enabled")
