"""Add model approval requests table for deployment workflow

Revision ID: 20260221_add_model_approvals
Revises: 20260221_add_skill_hierarchy_and_relationships
Create Date: 2026-02-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '20260221_add_model_approvals'
down_revision = '20260221_add_skill_hierarchy_and_relationships'
branch_labels = None
depends_on = None


def upgrade():
    """Create model_approval_requests table for approval workflow."""

    # Create approval_status enum type
    approval_status_enum = sa.Enum(
        'pending',
        'approved',
        'rejected',
        'deployed',
        'cancelled',
        name='approvalstatus',
    )
    approval_status_enum.create(op.get_bind(), checkfirst=True)

    # Create model_approval_requests table
    op.create_table(
        'model_approval_requests',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('model_version_id', UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', 'deployed', 'cancelled', name='approvalstatus'), nullable=False, server_default='pending'),
        sa.Column('requested_by', sa.String(), nullable=False),
        sa.Column('reviewed_by', sa.String(), nullable=True),
        sa.Column('requested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('justification', sa.Text(), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('target_environment', sa.String(50), nullable=False, server_default='staging'),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ['model_version_id'],
            ['ml_model_versions.id'],
            ondelete='CASCADE'
        ),
    )

    # Create indexes for model_approval_requests
    op.create_index(
        'ix_model_approval_requests_model_version_id',
        'model_approval_requests',
        ['model_version_id'],
        unique=False
    )
    op.create_index(
        'ix_model_approval_requests_status',
        'model_approval_requests',
        ['status'],
        unique=False
    )
    op.create_index(
        'ix_model_approval_requests_requested_by',
        'model_approval_requests',
        ['requested_by'],
        unique=False
    )
    op.create_index(
        'ix_model_approval_requests_organization_id',
        'model_approval_requests',
        ['organization_id'],
        unique=False
    )


def downgrade():
    """Remove model_approval_requests table."""

    # Drop indexes
    op.drop_index('ix_model_approval_requests_organization_id', table_name='model_approval_requests')
    op.drop_index('ix_model_approval_requests_requested_by', table_name='model_approval_requests')
    op.drop_index('ix_model_approval_requests_status', table_name='model_approval_requests')
    op.drop_index('ix_model_approval_requests_model_version_id', table_name='model_approval_requests')

    # Drop table
    op.drop_table('model_approval_requests')

    # Drop approval_status enum type
    approval_status_enum = sa.Enum(
        'pending',
        'approved',
        'rejected',
        'deployed',
        'cancelled',
        name='approvalstatus',
    )
    approval_status_enum.drop(op.get_bind(), checkfirst=True)
