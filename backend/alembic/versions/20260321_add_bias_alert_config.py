"""Add bias alert configuration table

Revision ID: 018_add_bias_alert_config
Revises: 017_add_fairness_metrics
Create Date: 2026-03-21

This migration creates the bias_alert_configs table for storing customizable
alert thresholds and notification settings for bias detection.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '018_add_bias_alert_config'
down_revision: Union[str, None] = '017_add_fairness_metrics'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create bias_alert_configs table."""

    # Create bias_alert_configs table
    op.create_table(
        'bias_alert_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
        sa.Column('alert_type', sa.String(50), nullable=False),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('threshold_value', sa.Numeric(5, 4), nullable=False),
        sa.Column('comparison_operator', sa.String(20), nullable=False, server_default='less_than'),
        sa.Column('severity_level', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notification_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notification_recipients', sa.JSON(), nullable=True),
        sa.Column('demographic_groups', sa.JSON(), nullable=True),
        sa.Column('applies_to_vacancies', sa.JSON(), nullable=True),
        sa.Column('alert_frequency', sa.String(20), nullable=False, server_default='immediate'),
        sa.Column('cooldown_period_hours', sa.Integer(), nullable=True, server_default='24'),
        sa.Column('auto_acknowledge', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('mitigation_recommendations', sa.Text(), nullable=True),
        sa.Column('custom_message_template', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create indexes for bias_alert_configs
    op.create_index('ix_bias_alert_configs_organization_id', 'bias_alert_configs', ['organization_id'])
    op.create_index('ix_bias_alert_configs_alert_type', 'bias_alert_configs', ['alert_type'])


def downgrade() -> None:
    """Drop bias_alert_configs table."""

    # Drop indexes
    op.drop_index('ix_bias_alert_configs_alert_type', table_name='bias_alert_configs')
    op.drop_index('ix_bias_alert_configs_organization_id', table_name='bias_alert_configs')

    # Drop table
    op.drop_table('bias_alert_configs')
