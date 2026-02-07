"""Add dashboard configuration table

Revision ID: 20260203_add_dashboard_configuration
Revises: 20260201_add_search_performance_indexes
Create Date: 2026-02-03

This migration creates the dashboard_configurations table for storing
user-customizable dashboard layouts. It enables recruiters to customize
their analytics dashboards by saving preferred widgets, layouts, and filters.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '20260203_add_dashboard_configuration'
down_revision: Union[str, None] = '20260201_add_search_performance_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create dashboard_configurations table."""

    # Create dashboard_configurations table
    op.create_table(
        'dashboard_configurations',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # Foreign key to recruiters (indexed for filtering)
        sa.Column(
            'recruiter_id',
            postgresql.UUID(as_uuid=True),
            postgresql.ForeignKey('recruiters.id', ondelete='CASCADE'),
            nullable=True,
            comment='Recruiter who owns this dashboard configuration',
        ),
        # Dashboard name (indexed for searching)
        sa.Column(
            'name',
            sa.String(255),
            nullable=False,
            comment='Human-readable name for this dashboard',
        ),
        # Dashboard configuration as JSON (widgets, layout, filters)
        sa.Column(
            'config',
            postgresql.JSON(),
            nullable=False,
            comment='Dashboard configuration including widgets, layout, and filters',
        ),
        # Default dashboard flag (indexed for filtering)
        sa.Column(
            'is_default',
            sa.Boolean(),
            nullable=False,
            server_default='false',
            comment='Whether this is the default dashboard for the recruiter',
        ),
        # Timestamps (inherited from TimestampMixin)
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        comment='User-customizable dashboard configurations for analytics',
    )

    # Create indexes for common query patterns
    op.create_index(
        'ix_dashboard_configurations_recruiter_id',
        'dashboard_configurations',
        ['recruiter_id'],
    )
    op.create_index(
        'ix_dashboard_configurations_name',
        'dashboard_configurations',
        ['name'],
    )
    op.create_index(
        'ix_dashboard_configurations_is_default',
        'dashboard_configurations',
        ['is_default'],
    )

    # Create composite index for recruiter + default (finding user's default dashboard)
    op.create_index(
        'ix_dashboard_configurations_recruiter_id_is_default',
        'dashboard_configurations',
        ['recruiter_id', 'is_default'],
    )


def downgrade() -> None:
    """Drop dashboard_configurations table."""

    # Drop composite index
    try:
        op.drop_index(
            'ix_dashboard_configurations_recruiter_id_is_default',
            table_name='dashboard_configurations',
        )
    except Exception:
        pass

    # Drop single-column indexes
    try:
        op.drop_index(
            'ix_dashboard_configurations_is_default',
            table_name='dashboard_configurations',
        )
    except Exception:
        pass

    try:
        op.drop_index(
            'ix_dashboard_configurations_name',
            table_name='dashboard_configurations',
        )
    except Exception:
        pass

    try:
        op.drop_index(
            'ix_dashboard_configurations_recruiter_id',
            table_name='dashboard_configurations',
        )
    except Exception:
        pass

    # Drop table
    try:
        op.drop_table('dashboard_configurations')
    except Exception:
        pass
