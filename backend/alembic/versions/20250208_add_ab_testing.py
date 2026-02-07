"""Add A/B testing tables for matching weight experiments

Revision ID: 012_add_ab_testing
Revises: 011_add_matching_weights_profiles
Create Date: 2025-02-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '012_add_ab_testing'
down_revision = '011_add_matching_weights_profiles'
branch_labels = None
depends_on = None


def upgrade():
    """Create A/B testing tables for experiments, assignments, and metrics."""

    # Create ab_tests table
    op.create_table(
        'ab_tests',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes for ab_tests
    op.create_index(
        'ix_ab_tests_status',
        'ab_tests',
        ['status'],
        unique=False
    )
    op.create_index(
        'ix_ab_tests_organization_id',
        'ab_tests',
        ['organization_id'],
        unique=False
    )

    # Create ab_test_assignments table
    op.create_table(
        'ab_test_assignments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('test_id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('profile_id', UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ['test_id'],
            ['ab_tests.id'],
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['profile_id'],
            ['matching_weights_profiles.id'],
            ondelete='CASCADE'
        ),
    )

    # Create indexes for ab_test_assignments
    op.create_index(
        'ix_ab_test_assignments_test_id',
        'ab_test_assignments',
        ['test_id'],
        unique=False
    )
    op.create_index(
        'ix_ab_test_assignments_user_id',
        'ab_test_assignments',
        ['user_id'],
        unique=False
    )
    op.create_index(
        'ix_ab_test_assignments_profile_id',
        'ab_test_assignments',
        ['profile_id'],
        unique=False
    )

    # Create ab_test_metrics table
    op.create_table(
        'ab_test_metrics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('test_id', UUID(as_uuid=True), nullable=False),
        sa.Column('assignment_id', UUID(as_uuid=True), nullable=False),
        sa.Column('metric_type', sa.String(50), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ['test_id'],
            ['ab_tests.id'],
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['assignment_id'],
            ['ab_test_assignments.id'],
            ondelete='CASCADE'
        ),
    )

    # Create indexes for ab_test_metrics
    op.create_index(
        'ix_ab_test_metrics_test_id',
        'ab_test_metrics',
        ['test_id'],
        unique=False
    )
    op.create_index(
        'ix_ab_test_metrics_assignment_id',
        'ab_test_metrics',
        ['assignment_id'],
        unique=False
    )
    op.create_index(
        'ix_ab_test_metrics_metric_type',
        'ab_test_metrics',
        ['metric_type'],
        unique=False
    )


def downgrade():
    """Remove A/B testing tables."""

    # Drop ab_test_metrics table
    op.drop_index('ix_ab_test_metrics_metric_type', table_name='ab_test_metrics')
    op.drop_index('ix_ab_test_metrics_assignment_id', table_name='ab_test_metrics')
    op.drop_index('ix_ab_test_metrics_test_id', table_name='ab_test_metrics')
    op.drop_table('ab_test_metrics')

    # Drop ab_test_assignments table
    op.drop_index('ix_ab_test_assignments_profile_id', table_name='ab_test_assignments')
    op.drop_index('ix_ab_test_assignments_user_id', table_name='ab_test_assignments')
    op.drop_index('ix_ab_test_assignments_test_id', table_name='ab_test_assignments')
    op.drop_table('ab_test_assignments')

    # Drop ab_tests table
    op.drop_index('ix_ab_tests_organization_id', table_name='ab_tests')
    op.drop_index('ix_ab_tests_status', table_name='ab_tests')
    op.drop_table('ab_tests')
