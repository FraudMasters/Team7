"""Add performance tracking and model training event tables

Revision ID: 015_add_performance_tracking
Revises: 014_add_matching_weights
Create Date: 2026-01-31

This migration creates tables for:
- model_performance_history: Track ML model performance metrics over time
- model_training_events: Track model training runs and their status

These tables enable automated model retraining based on performance degradation
and provide historical tracking for A/B testing and model version comparison.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '015_add_performance_tracking'
down_revision: Union[str, None] = '014_add_matching_weights'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create performance tracking tables."""

    # Create model_performance_history table
    op.create_table(
        'model_performance_history',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            'model_version_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('ml_model_versions.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('dataset_type', sa.String(50), nullable=False),
        sa.Column('accuracy', sa.Numeric(5, 4), nullable=True),
        sa.Column('precision', sa.Numeric(5, 4), nullable=True),
        sa.Column('recall', sa.Numeric(5, 4), nullable=True),
        sa.Column('f1_score', sa.Numeric(5, 4), nullable=True),
        sa.Column('auc_score', sa.Numeric(5, 4), nullable=True),
        sa.Column('sample_size', sa.Integer(), nullable=True),
        sa.Column('confusion_matrix', postgresql.JSON(), nullable=True),
        sa.Column('custom_metrics', postgresql.JSON(), nullable=True),
        sa.Column('performance_delta', sa.Numeric(5, 4), nullable=True),
        sa.Column('evaluation_metadata', postgresql.JSON(), nullable=True),
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
        comment='Track ML model performance metrics over time for monitoring and A/B testing',
    )

    # Create indexes for model_performance_history
    op.create_index(
        'ix_model_performance_history_model_version_id',
        'model_performance_history',
        ['model_version_id'],
    )
    op.create_index(
        'ix_model_performance_history_dataset_type',
        'model_performance_history',
        ['dataset_type'],
    )
    op.create_index(
        'ix_model_performance_history_created_at',
        'model_performance_history',
        ['created_at'],
    )

    # Create model_training_events table
    op.create_table(
        'model_training_events',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('training_status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('training_config', postgresql.JSON(), nullable=True),
        sa.Column('training_metrics', postgresql.JSON(), nullable=True),
        sa.Column('error_message', sa.String(1000), nullable=True),
        sa.Column('started_at', sa.String(50), nullable=True),
        sa.Column('completed_at', sa.String(50), nullable=True),
        sa.Column('training_duration', sa.Numeric(10, 2), nullable=True),
        sa.Column('dataset_info', postgresql.JSON(), nullable=True),
        sa.Column('ml_model_version_id', sa.String(50), nullable=True),
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
        comment='Track model training runs for automated retraining and audit trail',
    )

    # Create indexes for model_training_events
    op.create_index(
        'ix_model_training_events_model_name',
        'model_training_events',
        ['model_name'],
    )
    op.create_index(
        'ix_model_training_events_training_status',
        'model_training_events',
        ['training_status'],
    )
    op.create_index(
        'ix_model_training_events_created_at',
        'model_training_events',
        ['created_at'],
    )
    op.create_index(
        'ix_model_training_events_model_name_status',
        'model_training_events',
        ['model_name', 'training_status'],
    )


def downgrade() -> None:
    """Drop performance tracking tables."""

    # Drop model_training_events table
    op.drop_index(
        'ix_model_training_events_model_name_status',
        table_name='model_training_events',
    )
    op.drop_index(
        'ix_model_training_events_created_at',
        table_name='model_training_events',
    )
    op.drop_index(
        'ix_model_training_events_training_status',
        table_name='model_training_events',
    )
    op.drop_index(
        'ix_model_training_events_model_name',
        table_name='model_training_events',
    )
    op.drop_table('model_training_events')

    # Drop model_performance_history table
    op.drop_index(
        'ix_model_performance_history_created_at',
        table_name='model_performance_history',
    )
    op.drop_index(
        'ix_model_performance_history_dataset_type',
        table_name='model_performance_history',
    )
    op.drop_index(
        'ix_model_performance_history_model_version_id',
        table_name='model_performance_history',
    )
    op.drop_table('model_performance_history')
