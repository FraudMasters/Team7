"""Add champion/challenger fields to ml_model_versions table

Revision ID: 20260221_add_champion_challenger_fields
Revises: 20260221_add_model_approvals
Create Date: 2026-02-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '20260221_add_champion_challenger_fields'
down_revision = '20260221_add_model_approvals'
branch_labels = None
depends_on = None


def upgrade():
    """Add champion/challenger workflow fields to ml_model_versions table."""

    # Create modelrole enum type
    model_role_enum = sa.Enum(
        'standard',
        'champion',
        'challenger',
        name='modelrole',
    )
    model_role_enum.create(op.get_bind(), checkfirst=True)

    # Add champion/challenger fields to ml_model_versions
    op.add_column(
        'ml_model_versions',
        sa.Column(
            'model_role',
            sa.Enum('standard', 'champion', 'challenger', name='modelrole'),
            nullable=False,
            server_default='standard'
        )
    )

    op.add_column(
        'ml_model_versions',
        sa.Column(
            'challenger_traffic_percent',
            sa.Numeric(5, 2),
            nullable=True
        )
    )

    op.add_column(
        'ml_model_versions',
        sa.Column(
            'promoted_at',
            sa.DateTime(timezone=True),
            nullable=True
        )
    )

    op.add_column(
        'ml_model_versions',
        sa.Column(
            'promoted_from_id',
            UUID(as_uuid=True),
            nullable=True
        )
    )

    op.add_column(
        'ml_model_versions',
        sa.Column(
            'ab_test_id',
            UUID(as_uuid=True),
            nullable=True
        )
    )

    # Create indexes for new columns
    op.create_index(
        'ix_ml_model_versions_model_role',
        'ml_model_versions',
        ['model_role'],
        unique=False
    )

    op.create_index(
        'ix_ml_model_versions_ab_test_id',
        'ml_model_versions',
        ['ab_test_id'],
        unique=False
    )

    # Add foreign key constraints
    op.create_foreign_key(
        'fk_ml_model_versions_promoted_from_id',
        'ml_model_versions',
        'ml_model_versions',
        ['promoted_from_id'],
        ['id'],
        ondelete='SET NULL'
    )

    op.create_foreign_key(
        'fk_ml_model_versions_ab_test_id',
        'ml_model_versions',
        'ab_tests',
        ['ab_test_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    """Remove champion/challenger fields from ml_model_versions table."""

    # Drop foreign key constraints
    op.drop_constraint(
        'fk_ml_model_versions_ab_test_id',
        'ml_model_versions',
        type_='foreignkey'
    )

    op.drop_constraint(
        'fk_ml_model_versions_promoted_from_id',
        'ml_model_versions',
        type_='foreignkey'
    )

    # Drop indexes
    op.drop_index('ix_ml_model_versions_ab_test_id', table_name='ml_model_versions')
    op.drop_index('ix_ml_model_versions_model_role', table_name='ml_model_versions')

    # Drop columns
    op.drop_column('ml_model_versions', 'ab_test_id')
    op.drop_column('ml_model_versions', 'promoted_from_id')
    op.drop_column('ml_model_versions', 'promoted_at')
    op.drop_column('ml_model_versions', 'challenger_traffic_percent')
    op.drop_column('ml_model_versions', 'model_role')

    # Drop modelrole enum type
    model_role_enum = sa.Enum(
        'standard',
        'champion',
        'challenger',
        name='modelrole',
    )
    model_role_enum.drop(op.get_bind(), checkfirst=True)
