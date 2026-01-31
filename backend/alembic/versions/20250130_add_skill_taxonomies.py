"""Add skill taxonomies table

Revision ID: 012_add_skill_taxonomies
Revises: 011_add_candidate_ranking
Create Date: 2025-01-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '012_add_skill_taxonomies'
down_revision = '011_add_candidate_ranking'
branch_labels = None
depends_on = None


def upgrade():
    """Create skill_taxonomies table or add missing columns."""

    # Check if table exists - if not, create it
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'skill_taxonomies' not in tables:
        op.create_table(
            'skill_taxonomies',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('industry', sa.String(100), nullable=False),
            sa.Column('skill_name', sa.String(255), nullable=False),
            sa.Column('context', sa.String(100), nullable=True),
            sa.Column('variants', sa.JSON(), nullable=True),
            sa.Column('extra_metadata', sa.JSON(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
            sa.Column('version', sa.Integer(), nullable=False, default=1),
            sa.Column('previous_version_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('is_latest', sa.Boolean(), nullable=False, default=True),
            sa.Column('is_public', sa.Boolean(), nullable=False, default=False),
            sa.Column('organization_id', sa.String(), nullable=True),
            sa.Column('source_organization', sa.String(), nullable=True),
            sa.Column('view_count', sa.Integer(), nullable=False, default=0),
            sa.Column('use_count', sa.Integer(), nullable=False, default=0),
            sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(['previous_version_id'], ['skill_taxonomies.id']),
        )
        op.create_index('ix_skill_taxonomies_industry', 'skill_taxonomies', ['industry'])
        op.create_index('ix_skill_taxonomies_skill_name', 'skill_taxonomies', ['skill_name'])
    else:
        # Table exists - add missing columns
        columns = [col['name'] for col in inspector.get_columns('skill_taxonomies')]

        # Rename metadata to extra_metadata if needed
        if 'extra_metadata' not in columns and 'metadata' in columns:
            op.execute('ALTER TABLE skill_taxonomies RENAME COLUMN metadata TO extra_metadata')
        elif 'extra_metadata' not in columns:
            op.add_column('skill_taxonomies', sa.Column('extra_metadata', sa.JSON(), nullable=True))

        # Add versioning columns
        if 'version' not in columns:
            op.add_column('skill_taxonomies', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
        if 'previous_version_id' not in columns:
            op.add_column('skill_taxonomies', sa.Column('previous_version_id', postgresql.UUID(as_uuid=True), nullable=True))
            op.create_foreign_key('fk_skill_taxonomies_previous_version', 'skill_taxonomies', 'skill_taxonomies', ['previous_version_id'], ['id'])
        if 'is_latest' not in columns:
            op.add_column('skill_taxonomies', sa.Column('is_latest', sa.Boolean(), nullable=False, server_default='true'))

        # Add sharing columns
        if 'is_public' not in columns:
            op.add_column('skill_taxonomies', sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'))
        if 'organization_id' not in columns:
            op.add_column('skill_taxonomies', sa.Column('organization_id', sa.String(), nullable=True))
        if 'source_organization' not in columns:
            op.add_column('skill_taxonomies', sa.Column('source_organization', sa.String(), nullable=True))

        # Add analytics columns
        if 'view_count' not in columns:
            op.add_column('skill_taxonomies', sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'))
        if 'use_count' not in columns:
            op.add_column('skill_taxonomies', sa.Column('use_count', sa.Integer(), nullable=False, server_default='0'))
        if 'last_used_at' not in columns:
            op.add_column('skill_taxonomies', sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    """Drop skill_taxonomies table."""

    op.drop_constraint('fk_skill_taxonomies_previous_version', 'skill_taxonomies', type_='foreignkey')
    op.drop_index('ix_skill_taxonomies_skill_name', table_name='skill_taxonomies')
    op.drop_index('ix_skill_taxonomies_industry', table_name='skill_taxonomies')
    op.drop_table('skill_taxonomies')
