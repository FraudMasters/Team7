"""
Add communication tracking tables

Creates tables for:
- communications: Main table for tracking all candidate interactions (email, SMS, phone calls, in-system)
- email_messages: Email-specific communication data with threading and sync info
- sms_messages: SMS-specific communication data with delivery tracking
- phone_calls: Phone call-specific communication data with duration and recording
- communication_templates: Customizable templates for common communications
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "064_add_communication_tables"
down_revision: Union[str, None] = "20260131_add_comparison_name"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create communications table
    op.create_table(
        "communications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resumes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "vacancy_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_vacancies.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "recruiter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recruiters.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("direction", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("subject", sa.String(500), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("metadata", postgresql.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        comment="Track all candidate interactions including emails, SMS, phone calls, and in-system messages",
    )
    op.create_index(
        op.f("ix_communications_candidate_id"), "communications", ["candidate_id"]
    )
    op.create_index(
        op.f("ix_communications_vacancy_id"), "communications", ["vacancy_id"]
    )
    op.create_index(
        op.f("ix_communications_recruiter_id"), "communications", ["recruiter_id"]
    )
    op.create_index(
        op.f("ix_communications_type"), "communications", ["type"]
    )
    op.create_index(
        op.f("ix_communications_direction"), "communications", ["direction"]
    )
    op.create_index(
        op.f("ix_communications_status"), "communications", ["status"]
    )
    op.create_index(
        op.f("ix_communications_sent_at"), "communications", ["sent_at"]
    )
    op.create_index(
        op.f("ix_communications_received_at"), "communications", ["received_at"]
    )

    # Create email_messages table
    op.create_table(
        "email_messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "communication_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("communications.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("from_address", sa.String(255), nullable=True),
        sa.Column("to_address", sa.String(1000), nullable=True),
        sa.Column("cc_address", sa.String(1000), nullable=True),
        sa.Column("bcc_address", sa.String(1000), nullable=True),
        sa.Column("message_id", sa.String(500), nullable=True),
        sa.Column("thread_id", sa.String(500), nullable=True),
        sa.Column("in_reply_to", sa.String(500), nullable=True),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        comment="Email-specific communication data with threading and sync information",
    )
    op.create_index(
        op.f("ix_email_messages_communication_id"), "email_messages", ["communication_id"]
    )
    op.create_index(
        op.f("ix_email_messages_message_id"), "email_messages", ["message_id"]
    )
    op.create_index(
        op.f("ix_email_messages_thread_id"), "email_messages", ["thread_id"]
    )
    op.create_index(
        op.f("ix_email_messages_synced_at"), "email_messages", ["synced_at"]
    )

    # Create sms_messages table
    op.create_table(
        "sms_messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "communication_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("communications.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("from_number", sa.String(50), nullable=True),
        sa.Column("to_number", sa.String(50), nullable=True),
        sa.Column("provider", sa.String(100), nullable=True),
        sa.Column("delivery_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("delivery_error", sa.String(500), nullable=True),
        sa.Column("provider_message_id", sa.String(255), nullable=True),
        sa.Column("segment_count", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        comment="SMS-specific communication data with delivery tracking",
    )
    op.create_index(
        op.f("ix_sms_messages_communication_id"), "sms_messages", ["communication_id"]
    )
    op.create_index(
        op.f("ix_sms_messages_to_number"), "sms_messages", ["to_number"]
    )
    op.create_index(
        op.f("ix_sms_messages_provider"), "sms_messages", ["provider"]
    )
    op.create_index(
        op.f("ix_sms_messages_delivery_status"), "sms_messages", ["delivery_status"]
    )
    op.create_index(
        op.f("ix_sms_messages_provider_message_id"), "sms_messages", ["provider_message_id"]
    )

    # Create phone_calls table
    op.create_table(
        "phone_calls",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "communication_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("communications.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("from_number", sa.String(50), nullable=True),
        sa.Column("to_number", sa.String(50), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.Column("call_type", sa.String(50), nullable=False),
        sa.Column("recording_url", sa.String(1000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        comment="Phone call-specific communication data with duration and recording",
    )
    op.create_index(
        op.f("ix_phone_calls_communication_id"), "phone_calls", ["communication_id"]
    )
    op.create_index(
        op.f("ix_phone_calls_to_number"), "phone_calls", ["to_number"]
    )
    op.create_index(
        op.f("ix_phone_calls_call_type"), "phone_calls", ["call_type"]
    )

    # Create communication_templates table
    op.create_table(
        "communication_templates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("organization_id", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("subject", sa.String(500), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("variables", postgresql.JSON(), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("language", sa.String(10), nullable=False, server_default="en"),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        comment="Customizable templates for common communications",
    )
    op.create_index(
        op.f("ix_communication_templates_organization_id"), "communication_templates", ["organization_id"]
    )


def downgrade() -> None:
    # Drop communication_templates table
    op.drop_index(
        op.f("ix_communication_templates_organization_id"), table_name="communication_templates"
    )
    op.drop_table("communication_templates")

    # Drop phone_calls table
    op.drop_index(
        op.f("ix_phone_calls_call_type"), table_name="phone_calls"
    )
    op.drop_index(
        op.f("ix_phone_calls_to_number"), table_name="phone_calls"
    )
    op.drop_index(
        op.f("ix_phone_calls_communication_id"), table_name="phone_calls"
    )
    op.drop_table("phone_calls")

    # Drop sms_messages table
    op.drop_index(
        op.f("ix_sms_messages_provider_message_id"), table_name="sms_messages"
    )
    op.drop_index(
        op.f("ix_sms_messages_delivery_status"), table_name="sms_messages"
    )
    op.drop_index(
        op.f("ix_sms_messages_provider"), table_name="sms_messages"
    )
    op.drop_index(
        op.f("ix_sms_messages_to_number"), table_name="sms_messages"
    )
    op.drop_index(
        op.f("ix_sms_messages_communication_id"), table_name="sms_messages"
    )
    op.drop_table("sms_messages")

    # Drop email_messages table
    op.drop_index(
        op.f("ix_email_messages_synced_at"), table_name="email_messages"
    )
    op.drop_index(
        op.f("ix_email_messages_thread_id"), table_name="email_messages"
    )
    op.drop_index(
        op.f("ix_email_messages_message_id"), table_name="email_messages"
    )
    op.drop_index(
        op.f("ix_email_messages_communication_id"), table_name="email_messages"
    )
    op.drop_table("email_messages")

    # Drop communications table
    op.drop_index(
        op.f("ix_communications_received_at"), table_name="communications"
    )
    op.drop_index(
        op.f("ix_communications_sent_at"), table_name="communications"
    )
    op.drop_index(
        op.f("ix_communications_status"), table_name="communications"
    )
    op.drop_index(
        op.f("ix_communications_direction"), table_name="communications"
    )
    op.drop_index(
        op.f("ix_communications_type"), table_name="communications"
    )
    op.drop_index(
        op.f("ix_communications_recruiter_id"), table_name="communications"
    )
    op.drop_index(
        op.f("ix_communications_vacancy_id"), table_name="communications"
    )
    op.drop_index(
        op.f("ix_communications_candidate_id"), table_name="communications"
    )
    op.drop_table("communications")
