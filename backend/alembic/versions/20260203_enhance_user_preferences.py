"""Enhance user_preferences table

Revision ID: 017_enhance_user_preferences
Revises: 016_add_ats_results
Create Date: 2026-02-03

This migration adds profile fields, dashboard configuration, filter preferences,
and API keys management to the user_preferences table.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '017_enhance_user_preferences'
down_revision: Union[str, None] = '016_add_ats_results'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add new columns to user_preferences table."""

    # Add profile fields
    op.add_column(
        'user_preferences',
        sa.Column('name', sa.String(255), nullable=True),
    )
    op.add_column(
        'user_preferences',
        sa.Column('email', sa.String(255), nullable=True),
    )
    op.add_column(
        'user_preferences',
        sa.Column('role', sa.String(100), nullable=True),
    )
    op.add_column(
        'user_preferences',
        sa.Column('avatar_url', sa.String(512), nullable=True),
    )

    # Add dashboard configuration (JSON)
    op.add_column(
        'user_preferences',
        sa.Column('dashboard_config', postgresql.JSON(), nullable=True),
    )

    # Add filter preferences (JSON)
    op.add_column(
        'user_preferences',
        sa.Column('filter_preferences', postgresql.JSON(), nullable=True),
    )

    # Add API keys storage (JSON)
    op.add_column(
        'user_preferences',
        sa.Column('api_keys', postgresql.JSON(), nullable=True),
    )

    # Create indexes for frequently queried fields
    op.create_index(
        'ix_user_preferences_email',
        'user_preferences',
        ['email'],
    )
    op.create_index(
        'ix_user_preferences_role',
        'user_preferences',
        ['role'],
    )


def downgrade() -> None:
    """Remove added columns from user_preferences table."""

    # Drop indexes
    op.drop_index(
        'ix_user_preferences_role',
        table_name='user_preferences',
    )
    op.drop_index(
        'ix_user_preferences_email',
        table_name='user_preferences',
    )

    # Drop columns
    op.drop_column('user_preferences', 'api_keys')
    op.drop_column('user_preferences', 'filter_preferences')
    op.drop_column('user_preferences', 'dashboard_config')
    op.drop_column('user_preferences', 'avatar_url')
    op.drop_column('user_preferences', 'role')
    op.drop_column('user_preferences', 'email')
    op.drop_column('user_preferences', 'name')
