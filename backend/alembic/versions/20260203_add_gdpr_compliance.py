"""Add GDPR compliance tables

Revision ID: 019_add_gdpr_compliance
Revises: 018_add_audit_logs
Create Date: 2026-02-03

This migration creates all tables required for GDPR compliance including:
- consent_records: Tracking user consent and GDPR compliance
- data_retention_policies: Automatic data deletion and GDPR compliance
- data_deletion_requests: GDPR right-to-be-forgotten requests
- cookie_consent: Tracking GDPR cookie preferences
- processing_agreements: Data Processing Agreement (DPA) templates and signatures

These tables enable full GDPR compliance including consent management, right to erasure,
data portability, data retention policies, and processing agreements.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '019_add_gdpr_compliance'
down_revision: Union[str, None] = '018_add_audit_logs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all GDPR compliance tables."""

    # Create consent_records table
    op.create_table(
        'consent_records',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # Consent type and status (indexed for filtering)
        sa.Column('consent_type', sa.String(50), nullable=False, index=True),
        sa.Column('granted', sa.Boolean(), nullable=False, default=True, index=True),
        # Foreign keys (indexed for filtering)
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            index=True,
        ),
        sa.Column(
            'organization_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            index=True,
        ),
        # Consent details
        sa.Column('consent_text', sa.Text(), nullable=True),
        sa.Column('consent_version', sa.String(20), nullable=True),
        # Request metadata for verification
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        # Withdrawal tracking
        sa.Column(
            'withdrawn_at',
            sa.DateTime(timezone=True),
            nullable=True,
            index=True,
        ),
        sa.Column('withdrawal_reason', sa.Text(), nullable=True),
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
        comment='Tracking user consent and GDPR compliance',
    )

    # Create composite indexes for consent_records
    op.create_index(
        'ix_consent_records_user_id_consent_type',
        'consent_records',
        ['user_id', 'consent_type'],
    )
    op.create_index(
        'ix_consent_records_organization_id_consent_type',
        'consent_records',
        ['organization_id', 'consent_type'],
    )

    # Create data_retention_policies table
    op.create_table(
        'data_retention_policies',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # Policy details (indexed for filtering)
        sa.Column('policy_name', sa.String(200), nullable=False, index=True),
        sa.Column('entity_type', sa.String(50), nullable=False, index=True),
        sa.Column('retention_days', sa.Integer(), nullable=False, default=365),
        sa.Column('action_type', sa.String(50), nullable=False, default='delete'),
        # Organization (NULL for global policies)
        sa.Column(
            'organization_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            index=True,
        ),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True, index=True),
        # Policy metadata
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('legal_basis', sa.String(100), nullable=True),
        sa.Column('deletion_reason', sa.String(500), nullable=True),
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
        comment='Automatic data deletion and GDPR compliance policies',
    )

    # Create composite indexes for data_retention_policies
    op.create_index(
        'ix_data_retention_policies_entity_type_is_active',
        'data_retention_policies',
        ['entity_type', 'is_active'],
    )
    op.create_index(
        'ix_data_retention_policies_organization_id_is_active',
        'data_retention_policies',
        ['organization_id', 'is_active'],
    )

    # Create data_deletion_requests table
    op.create_table(
        'data_deletion_requests',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # Requester information (indexed for filtering)
        sa.Column('requester_email', sa.String(255), nullable=False, index=True),
        sa.Column('requester_type', sa.String(50), nullable=False, default='candidate', index=True),
        # Request status and workflow
        sa.Column('status', sa.String(50), nullable=False, default='pending', index=True),
        sa.Column('verification_token', sa.String(255), nullable=True, unique=True, index=True),
        sa.Column(
            'verified_at',
            sa.DateTime(timezone=True),
            nullable=True,
            index=True,
        ),
        sa.Column(
            'processed_at',
            sa.DateTime(timezone=True),
            nullable=True,
            index=True,
        ),
        # Additional information
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
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
        comment='GDPR right-to-be-forgotten deletion requests',
    )

    # Create composite indexes for data_deletion_requests
    op.create_index(
        'ix_data_deletion_requests_status_created_at',
        'data_deletion_requests',
        ['status', 'created_at'],
    )

    # Create cookie_consent table
    op.create_table(
        'cookie_consent',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # User identification (indexed for lookups)
        sa.Column('session_id', sa.String(255), nullable=True, index=True),
        sa.Column('user_id', sa.String(255), nullable=True, index=True),
        # Cookie preferences
        sa.Column('essential_cookies', sa.Boolean(), nullable=False, default=True),
        sa.Column('functional_cookies', sa.Boolean(), nullable=False, default=False),
        sa.Column('analytics_cookies', sa.Boolean(), nullable=False, default=False),
        sa.Column('marketing_cookies', sa.Boolean(), nullable=False, default=False),
        # Consent metadata
        sa.Column('consent_version', sa.String(20), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
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
        comment='User cookie preferences and GDPR compliance',
    )

    # Create processing_agreements table
    op.create_table(
        'processing_agreements',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # Organization and agreement details (indexed for filtering)
        sa.Column('organization_id', sa.String(255), nullable=False, index=True),
        sa.Column('agreement_type', sa.String(50), nullable=False, index=True),
        sa.Column('status', sa.String(50), nullable=False, index=True),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('template_version', sa.String(50), nullable=True),
        # Processor information
        sa.Column('processor_name', sa.String(255), nullable=False),
        sa.Column('processor_contact', postgresql.JSON(), nullable=False),
        sa.Column('controller_representative', sa.String(255), nullable=True),
        # Agreement terms and conditions (JSON fields)
        sa.Column('terms', postgresql.JSON(), nullable=False),
        sa.Column('data_categories', postgresql.JSON(), nullable=False),
        sa.Column('processing_purposes', postgresql.JSON(), nullable=False),
        sa.Column('security_measures', postgresql.JSON(), nullable=False),
        sa.Column('subprocessing', postgresql.JSON(), nullable=False),
        sa.Column('data_subject_rights', postgresql.JSON(), nullable=False),
        sa.Column('breach_notification', postgresql.JSON(), nullable=False),
        sa.Column('transfer_mechanisms', postgresql.JSON(), nullable=False),
        # Dates and renewal
        sa.Column('effective_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expiry_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('termination_notice_days', sa.Integer(), nullable=False, default=30),
        sa.Column('auto_renewal', sa.Boolean(), nullable=False, default=False),
        sa.Column('renewal_terms', postgresql.JSON(), nullable=False),
        # Signature information
        sa.Column('signatures', postgresql.JSON(), nullable=False),
        sa.Column('signed_by', sa.String(255), nullable=True),
        sa.Column('signed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('signature_method', sa.String(50), nullable=True),
        # Additional information
        sa.Column('documents', postgresql.JSON(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
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
        comment='Data Processing Agreement (DPA) templates and signatures',
    )

    # Create composite indexes for processing_agreements
    op.create_index(
        'ix_processing_agreements_organization_id_status',
        'processing_agreements',
        ['organization_id', 'status'],
    )
    op.create_index(
        'ix_processing_agreements_effective_date',
        'processing_agreements',
        ['effective_date'],
    )
    op.create_index(
        'ix_processing_agreements_expiry_date',
        'processing_agreements',
        ['expiry_date'],
    )


def downgrade() -> None:
    """Drop all GDPR compliance tables."""

    # Drop processing_agreements indexes
    try:
        op.drop_index('ix_processing_agreements_expiry_date', table_name='processing_agreements')
    except Exception:
        pass
    try:
        op.drop_index('ix_processing_agreements_effective_date', table_name='processing_agreements')
    except Exception:
        pass
    try:
        op.drop_index('ix_processing_agreements_organization_id_status', table_name='processing_agreements')
    except Exception:
        pass

    # Drop processing_agreements table
    try:
        op.drop_table('processing_agreements')
    except Exception:
        pass

    # Drop cookie_consent table
    try:
        op.drop_table('cookie_consent')
    except Exception:
        pass

    # Drop data_deletion_requests indexes
    try:
        op.drop_index('ix_data_deletion_requests_status_created_at', table_name='data_deletion_requests')
    except Exception:
        pass

    # Drop data_deletion_requests table
    try:
        op.drop_table('data_deletion_requests')
    except Exception:
        pass

    # Drop data_retention_policies indexes
    try:
        op.drop_index('ix_data_retention_policies_organization_id_is_active', table_name='data_retention_policies')
    except Exception:
        pass
    try:
        op.drop_index('ix_data_retention_policies_entity_type_is_active', table_name='data_retention_policies')
    except Exception:
        pass

    # Drop data_retention_policies table
    try:
        op.drop_table('data_retention_policies')
    except Exception:
        pass

    # Drop consent_records indexes
    try:
        op.drop_index('ix_consent_records_organization_id_consent_type', table_name='consent_records')
    except Exception:
        pass
    try:
        op.drop_index('ix_consent_records_user_id_consent_type', table_name='consent_records')
    except Exception:
        pass

    # Drop consent_records table
    try:
        op.drop_table('consent_records')
    except Exception:
        pass
