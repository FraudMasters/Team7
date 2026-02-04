"""Create interview scheduling tables

Revision ID: 019_create_interview_tables
Revises: 018_add_interview_prep
Create Date: 2026-02-03

This migration creates the core tables for interview scheduling with calendar
integration:
- interviews: Main interview scheduling table with time, location, and calendar sync
- interview_participants: Junction table for interview participants and their roles
- calendar_connections: OAuth connection information for Google/Outlook integration

These tables enable:
- Scheduling interviews with multiple participants
- Google Calendar and Outlook integration via OAuth
- Automatic calendar event creation and management
- Availability checking and conflict detection
- Interview status tracking through the scheduling lifecycle

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '019_create_interview_tables'
down_revision: Union[str, None] = '018_add_interview_prep'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create interview scheduling and calendar integration tables."""

    # Create calendar_connections table first (interviews will reference it)
    op.create_table(
        'calendar_connections',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # Foreign key to recruiter who owns this connection
        sa.Column(
            'recruiter_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('recruiters.id', ondelete='CASCADE'),
            nullable=False,
            unique=True,
            index=True,
        ),
        # Calendar provider (google or outlook)
        sa.Column(
            'provider',
            sa.Enum('google', 'outlook', name='calendarprovider'),
            nullable=False,
            index=True,
        ),
        # OAuth tokens
        sa.Column('access_token', sa.String(2048), nullable=False),
        sa.Column('refresh_token', sa.String(2048), nullable=False),
        sa.Column(
            'token_expires_at',
            sa.DateTime(timezone=True),
            nullable=False,
            index=True,
        ),
        # Connected calendar information
        sa.Column('calendar_email', sa.String(255), nullable=False),
        sa.Column('calendar_id', sa.String(255), nullable=True),
        # Connection status
        sa.Column(
            'status',
            sa.Enum('active', 'expired', 'error', 'disconnected', name='connectionstatus'),
            nullable=False,
            index=True,
        ),
        # Optional webhook for real-time sync
        sa.Column('webhook_subscription_id', sa.String(255), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
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
        comment='OAuth connections for Google Calendar and Outlook integration',
    )

    # Create indexes for calendar_connections
    op.create_index(
        'ix_calendar_connections_recruiter_id',
        'calendar_connections',
        ['recruiter_id'],
    )
    op.create_index(
        'ix_calendar_connections_provider',
        'calendar_connections',
        ['provider'],
    )
    op.create_index(
        'ix_calendar_connections_status',
        'calendar_connections',
        ['status'],
    )

    # Create interviews table
    op.create_table(
        'interviews',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # Foreign keys to candidate and job vacancy
        sa.Column(
            'candidate_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('resumes.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),
        sa.Column(
            'vacancy_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('job_vacancies.id', ondelete='SET NULL'),
            nullable=True,
            index=True,
        ),
        # Interview timing
        sa.Column(
            'scheduled_start',
            sa.DateTime(timezone=True),
            nullable=False,
            index=True,
        ),
        sa.Column(
            'scheduled_end',
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        # Interview status and type
        sa.Column(
            'status',
            sa.Enum(
                'scheduled', 'confirmed', 'cancelled', 'completed', 'no_show', 'rescheduled',
                name='interviewstatus'
            ),
            nullable=False,
            index=True,
        ),
        sa.Column(
            'interview_type',
            sa.Enum('phone', 'video', 'onsite', 'technical', 'panel', name='interviewtype'),
            nullable=False,
        ),
        # Interview details
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location', sa.String(500), nullable=True),
        sa.Column('meeting_link', sa.String(500), nullable=True),
        sa.Column('meeting_room', sa.String(255), nullable=True),
        # Recruiter who scheduled the interview
        sa.Column(
            'recruiter_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('recruiters.id', ondelete='SET NULL'),
            nullable=True,
            index=True,
        ),
        # Calendar integration
        sa.Column('calendar_event_id', sa.String(255), nullable=True),
        sa.Column('calendar_provider', sa.String(50), nullable=True),
        sa.Column('is_reminder_sent', sa.Boolean(), nullable=False, server_default='false'),
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
        comment='Scheduled interviews with calendar integration',
    )

    # Create indexes for interviews
    op.create_index(
        'ix_interviews_candidate_id',
        'interviews',
        ['candidate_id'],
    )
    op.create_index(
        'ix_interviews_vacancy_id',
        'interviews',
        ['vacancy_id'],
    )
    op.create_index(
        'ix_interviews_scheduled_start',
        'interviews',
        ['scheduled_start'],
    )
    op.create_index(
        'ix_interviews_status',
        'interviews',
        ['status'],
    )

    # Create interview_participants junction table
    op.create_table(
        'interview_participants',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # Foreign keys to interview and recruiter
        sa.Column(
            'interview_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('interviews.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),
        sa.Column(
            'recruiter_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('recruiters.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),
        # Participant role and status
        sa.Column(
            'role',
            sa.Enum(
                'lead_interviewer', 'interviewer', 'note_taker', 'observer', 'hiring_manager',
                name='participantrole'
            ),
            nullable=False,
        ),
        sa.Column(
            'status',
            sa.Enum('pending', 'accepted', 'declined', 'tentative', name='participantstatus'),
            nullable=False,
            index=True,
        ),
        sa.Column('response_timestamp', sa.DateTime(timezone=True), nullable=True),
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
        comment='Interview participants with roles and response status',
    )

    # Create indexes for interview_participants
    op.create_index(
        'ix_interview_participants_interview_id',
        'interview_participants',
        ['interview_id'],
    )
    op.create_index(
        'ix_interview_participants_recruiter_id',
        'interview_participants',
        ['recruiter_id'],
    )
    op.create_index(
        'ix_interview_participants_status',
        'interview_participants',
        ['status'],
    )

    # Create composite indexes for common query patterns

    # Index for finding interviews by recruiter and date
    op.create_index(
        'ix_interviews_recruiter_id_scheduled_start',
        'interviews',
        ['recruiter_id', 'scheduled_start'],
    )

    # Index for finding interviews by candidate and status
    op.create_index(
        'ix_interviews_candidate_id_status',
        'interviews',
        ['candidate_id', 'status'],
    )

    # Index for availability checking (interviewer + time range queries)
    op.create_index(
        'ix_interview_participants_recruiter_id_interview_id',
        'interview_participants',
        ['recruiter_id', 'interview_id'],
        unique=True,
    )


def downgrade() -> None:
    """Remove interview scheduling and calendar integration tables."""

    # Drop composite indexes
    try:
        op.drop_index(
            'ix_interview_participants_recruiter_id_interview_id',
            table_name='interview_participants',
        )
    except Exception:
        pass

    try:
        op.drop_index(
            'ix_interviews_candidate_id_status',
            table_name='interviews',
        )
    except Exception:
        pass

    try:
        op.drop_index(
            'ix_interviews_recruiter_id_scheduled_start',
            table_name='interviews',
        )
    except Exception:
        pass

    # Drop interview_participants table and indexes
    try:
        op.drop_index(
            'ix_interview_participants_status',
            table_name='interview_participants',
        )
    except Exception:
        pass

    try:
        op.drop_index(
            'ix_interview_participants_recruiter_id',
            table_name='interview_participants',
        )
    except Exception:
        pass

    try:
        op.drop_index(
            'ix_interview_participants_interview_id',
            table_name='interview_participants',
        )
    except Exception:
        pass

    try:
        op.drop_table('interview_participants')
    except Exception:
        pass

    # Drop interviews table and indexes
    try:
        op.drop_index(
            'ix_interviews_status',
            table_name='interviews',
        )
    except Exception:
        pass

    try:
        op.drop_index(
            'ix_interviews_scheduled_start',
            table_name='interviews',
        )
    except Exception:
        pass

    try:
        op.drop_index(
            'ix_interviews_vacancy_id',
            table_name='interviews',
        )
    except Exception:
        pass

    try:
        op.drop_index(
            'ix_interviews_candidate_id',
            table_name='interviews',
        )
    except Exception:
        pass

    try:
        op.drop_table('interviews')
    except Exception:
        pass

    # Drop calendar_connections table and indexes
    try:
        op.drop_index(
            'ix_calendar_connections_status',
            table_name='calendar_connections',
        )
    except Exception:
        pass

    try:
        op.drop_index(
            'ix_calendar_connections_provider',
            table_name='calendar_connections',
        )
    except Exception:
        pass

    try:
        op.drop_index(
            'ix_calendar_connections_recruiter_id',
            table_name='calendar_connections',
        )
    except Exception:
        pass

    try:
        op.drop_table('calendar_connections')
    except Exception:
        pass
