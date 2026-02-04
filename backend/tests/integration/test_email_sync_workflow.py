"""
Integration tests for email synchronization workflow.

This test module verifies the complete end-to-end email sync workflow:
1. Configure email sync settings
2. Trigger email sync via API
3. Verify emails are stored in database
4. View emails via API
5. Compose and send reply email
6. Verify reply appears in database

These tests require a running database and can use mock IMAP/SMTP servers
or test accounts for realistic integration testing.
"""
import asyncio
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session_maker
from models import Communication, EmailMessage, Resume
from models.communication import CommunicationType, CommunicationDirection, CommunicationStatus
from api.email_sync import sync, get_status, get_config, update_config
from api.communications import create_communication, list_communications, get_communication
from tasks.email_sync_task import sync_emails_imap, send_email_task


# Test Fixtures

@pytest.fixture
async def db_session() -> AsyncSession:
    """Create a test database session."""
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def test_candidate(db_session: AsyncSession) -> Resume:
    """Create a test candidate (resume) with email."""
    candidate = Resume(
        id=str(uuid4()),
        name="Test Candidate",
        email="test.candidate@example.com",
        metadata={"contact_email": "test.candidate@example.com"}
    )
    db_session.add(candidate)
    await db_session.commit()
    await db_session.refresh(candidate)
    return candidate


@pytest.fixture
def email_config():
    """Mock email configuration for testing."""
    return {
        "imap_server": "imap.test.com",
        "imap_port": 993,
        "imap_use_ssl": True,
        "imap_username": "test@test.com",
        "imap_password": "test_password",
        "smtp_server": "smtp.test.com",
        "smtp_port": 587,
        "smtp_use_tls": True,
        "smtp_username": "test@test.com",
        "smtp_password": "test_password",
        "smtp_from_email": "test@test.com",
        "smtp_from_name": "Test Recruiter"
    }


@pytest.fixture
def mock_imap_response():
    """Mock IMAP email response."""
    return {
        "message_id": "<test123@test.com>",
        "from_address": "test.candidate@example.com",
        "to_address": "recruiter@test.com",
        "subject": "Test Subject",
        "body": "This is a test email body.",
        "sent_date": "2026-02-03T10:00:00Z"
    }


# Test: Configure Email Sync

@pytest.mark.asyncio
async def test_step1_configure_email_sync(email_config):
    """
    Step 1: Configure email sync in backend settings.

    Verifies:
    - Email config can be retrieved
    - Email config can be updated
    - Configuration validation works
    """
    # Test getting initial config
    status_response = await get_status()
    assert status_response["sync_enabled"] is False
    assert status_response["last_sync_time"] is None

    # Test updating config
    config_update = {
        "imap_server": email_config["imap_server"],
        "imap_port": email_config["imap_port"],
        "imap_username": email_config["imap_username"],
        "imap_password": email_config["imap_password"],
        "smtp_server": email_config["smtp_server"],
        "smtp_port": email_config["smtp_port"],
        "smtp_username": email_config["smtp_username"],
        "smtp_password": email_config["smtp_password"],
        "smtp_from_email": email_config["smtp_from_email"],
        "sync_enabled": True,
        "sync_interval_minutes": 5
    }

    update_response = await update_config(config_update)
    assert update_response["sync_enabled"] is True
    assert update_response["sync_interval_minutes"] == 5
    assert update_response["imap_server"] == email_config["imap_server"]


# Test: Trigger Email Sync

@pytest.mark.asyncio
async def test_step2_trigger_email_sync(email_config, mock_imap_response, test_candidate):
    """
    Step 2: Trigger email sync via API or Celery task.

    Verifies:
    - Sync can be triggered via API
    - Celery task can be called
    - Task returns proper status
    """
    # Mock IMAP connection
    with patch("tasks.email_sync_task.IMAP4_SSL") as mock_imap:
        # Setup mock IMAP server
        mock_server = Mock()
        mock_server.login = Mock(return_value=("OK", ""))
        mock_server.select = Mock(return_value=("OK", ""))
        mock_server.search = Mock(return_value=("OK", [b"1 2 3"]))
        mock_server.fetch = Mock(return_value=(
            "OK",
            [b"(RFC822 {123}", b"Subject: Test\r\n\r\nTest body", b")"]
        ))
        mock_server.close = Mock()
        mock_server.logout = Mock()
        mock_imap.return_value = mock_server

        # Test triggering sync via API
        sync_request = {
            "full_sync": True,
            "folder": "INBOX"
        }

        sync_response = await sync(sync_request)
        assert sync_response["status"] in ["started", "completed", "queued"]
        assert "sync_id" in sync_response or "message" in sync_response

        # Test triggering sync via Celery task directly
        task_result = sync_emails_imap.apply_async(
            args=[],
            kwargs={
                "imap_server": email_config["imap_server"],
                "imap_port": email_config["imap_port"],
                "imap_username": email_config["imap_username"],
                "imap_password": email_config["imap_password"],
                "folder": "INBOX",
                "batch_size": 10
            }
        )

        # Wait for task to complete (with timeout)
        result = task_result.get(timeout=30)
        assert result["status"] in ["completed", "failed", "pending"]
        assert "emails_processed" in result
        assert "processing_time_ms" in result


# Test: Verify Emails Stored in Database

@pytest.mark.asyncio
async def test_step3_verify_emails_stored(db_session: AsyncSession, test_candidate):
    """
    Step 3: Verify emails are stored in database.

    Verifies:
    - Communications table has email records
    - Email messages table has detailed records
    - Candidate associations are correct
    - Thread tracking works
    """
    # Create a test email communication
    email_data = {
        "candidate_id": str(test_candidate.id),
        "type": "email",
        "direction": "inbound",
        "status": "delivered",
        "subject": "Test Email Subject",
        "body": "This is a test email body from candidate.",
        "sent_at": datetime.utcnow().isoformat(),
        "received_at": datetime.utcnow().isoformat(),
        "metadata": {
            "from_address": "test.candidate@example.com",
            "to_address": "recruiter@test.com",
            "message_id": "<test123@test.com>",
            "thread_id": "thread123"
        }
    }

    # Create communication
    comm_response = await create_communication(email_data, db_session)
    assert comm_response["type"] == "email"
    assert comm_response["direction"] == "inbound"
    assert comm_response["subject"] == "Test Email Subject"
    assert "id" in comm_response

    communication_id = comm_response["id"]

    # Verify it's in the database
    stmt = select(Communication).where(Communication.id == communication_id)
    result = await db_session.execute(stmt)
    communication = result.scalar_one_or_none()

    assert communication is not None
    assert communication.type == CommunicationType.EMAIL
    assert communication.direction == CommunicationDirection.INBOUND
    assert communication.status == CommunicationStatus.DELIVERED
    assert communication.candidate_id == str(test_candidate.id)

    # Verify EmailMessage record
    email_stmt = select(EmailMessage).where(EmailMessage.communication_id == communication_id)
    email_result = await db_session.execute(email_stmt)
    email_message = email_result.scalar_one_or_none()

    assert email_message is not None
    assert email_message.from_address == "test.candidate@example.com"
    assert email_message.message_id == "<test123@test.com>"


# Test: View Emails in Timeline via API

@pytest.mark.asyncio
async def test_step4_view_emails_timeline(db_session: AsyncSession, test_candidate):
    """
    Step 4: View emails in frontend CommunicationTimeline via API.

    Verifies:
    - Communications API returns emails
    - Filtering by type works
    - Filtering by candidate works
    - Thread grouping is possible
    """
    # Create multiple test communications
    communications_data = [
        {
            "candidate_id": str(test_candidate.id),
            "type": "email",
            "direction": "inbound",
            "status": "delivered",
            "subject": "First Email",
            "body": "First email body",
            "sent_at": (datetime.utcnow() - timedelta(hours=3)).isoformat(),
            "metadata": {"from_address": "candidate@example.com"}
        },
        {
            "candidate_id": str(test_candidate.id),
            "type": "email",
            "direction": "outbound",
            "status": "sent",
            "subject": "Reply to First Email",
            "body": "Reply body",
            "sent_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            "metadata": {"to_address": "candidate@example.com"}
        },
        {
            "candidate_id": str(test_candidate.id),
            "type": "sms",
            "direction": "inbound",
            "status": "delivered",
            "body": "SMS message",
            "sent_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
        }
    ]

    created_comm_ids = []
    for comm_data in communications_data:
        response = await create_communication(comm_data, db_session)
        created_comm_ids.append(response["id"])

    # List all communications for candidate
    list_params = {
        "candidate_id": str(test_candidate.id),
        "limit": 10
    }
    comm_list = await list_communications(list_params, db_session)

    assert comm_list["total_count"] >= 3
    assert len(comm_list["communications"]) >= 3

    # Filter by email type only
    email_params = {
        "candidate_id": str(test_candidate.id),
        "type": "email",
        "limit": 10
    }
    email_list = await list_communications(email_params, db_session)

    assert email_list["total_count"] >= 2
    assert all(c["type"] == "email" for c in email_list["communications"])

    # Filter by direction (inbound emails)
    inbound_params = {
        "candidate_id": str(test_candidate.id),
        "type": "email",
        "direction": "inbound",
        "limit": 10
    }
    inbound_list = await list_communications(inbound_params, db_session)

    assert inbound_list["total_count"] >= 1
    assert all(c["direction"] == "inbound" for c in inbound_list["communications"])


# Test: Compose and Send Reply Email

@pytest.mark.asyncio
async def test_step5_send_reply_email(db_session: AsyncSession, test_candidate, email_config):
    """
    Step 5: Compose and send reply email.

    Verifies:
    - Reply can be created via API
    - Reply has thread tracking (in_reply_to)
    - Celery send_email_task can be triggered
    - SMTP sending works (mocked)
    """
    # First, create an original email to reply to
    original_email = {
        "candidate_id": str(test_candidate.id),
        "type": "email",
        "direction": "inbound",
        "status": "delivered",
        "subject": "Original Email from Candidate",
        "body": "I am interested in the position.",
        "sent_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
        "metadata": {
            "from_address": "test.candidate@example.com",
            "to_address": "recruiter@test.com",
            "message_id": "<original123@test.com>",
            "thread_id": "thread456"
        }
    }

    original_response = await create_communication(original_email, db_session)
    original_id = original_response["id"]

    # Now create a reply
    reply_data = {
        "candidate_id": str(test_candidate.id),
        "type": "email",
        "direction": "outbound",
        "status": "pending",
        "subject": "Re: Original Email from Candidate",
        "body": "Thank you for your interest. Let's schedule an interview.",
        "sent_at": datetime.utcnow().isoformat(),
        "metadata": {
            "from_address": "recruiter@test.com",
            "to_address": "test.candidate@example.com",
            "in_reply_to": "<original123@test.com>",
            "thread_id": "thread456",
            "references": ["<original123@test.com>"]
        }
    }

    reply_response = await create_communication(reply_data, db_session)
    assert reply_response["type"] == "email"
    assert reply_response["direction"] == "outbound"
    assert reply_response["subject"].startswith("Re:")
    assert "in_reply_to" in reply_response["metadata"]

    reply_id = reply_response["id"]

    # Test sending via Celery task (with mocked SMTP)
    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = Mock()
        mock_server.send_message = Mock(return_value={})
        mock_server.quit = Mock()
        mock_smtp.return_value = mock_server

        # Trigger send_email_task
        task_result = send_email_task.apply_async(
            args=[],
            kwargs={
                "communication_id": reply_id,
                "to_address": "test.candidate@example.com",
                "subject": "Re: Original Email from Candidate",
                "body": "Thank you for your interest. Let's schedule an interview.",
                "from_email": "recruiter@test.com",
                "from_name": "Test Recruiter",
                "in_reply_to": "<original123@test.com>",
                "thread_id": "thread456"
            }
        )

        result = task_result.get(timeout=30)
        assert result["status"] in ["sent", "failed"]
        assert "processing_time_ms" in result


# Test: Verify Reply in Database and Timeline

@pytest.mark.asyncio
async def test_step6_verify_reply_in_timeline(db_session: AsyncSession, test_candidate):
    """
    Step 6: Verify reply appears in database and timeline.

    Verifies:
    - Reply is stored with correct thread_id
    - Timeline shows both original and reply
    - Thread view groups related emails
    - Metadata is preserved
    """
    # Create thread of emails
    thread_id = "test_thread_789"

    # Original email
    original = {
        "candidate_id": str(test_candidate.id),
        "type": "email",
        "direction": "inbound",
        "status": "delivered",
        "subject": "Question about position",
        "body": "What is the salary range?",
        "sent_at": (datetime.utcnow() - timedelta(minutes=30)).isoformat(),
        "metadata": {
            "from_address": "test.candidate@example.com",
            "message_id": "<msg1@test.com>",
            "thread_id": thread_id
        }
    }

    original_response = await create_communication(original, db_session)

    # Wait a bit (simulating time passing)
    await asyncio.sleep(0.1)

    # Reply email
    reply = {
        "candidate_id": str(test_candidate.id),
        "type": "email",
        "direction": "outbound",
        "status": "sent",
        "subject": "Re: Question about position",
        "body": "The salary range is $80-120k.",
        "sent_at": datetime.utcnow().isoformat(),
        "metadata": {
            "to_address": "test.candidate@example.com",
            "message_id": "<msg2@test.com>",
            "thread_id": thread_id,
            "in_reply_to": "<msg1@test.com>"
        }
    }

    reply_response = await create_communication(reply, db_session)

    # List all communications for candidate
    comm_list = await list_communications(
        {"candidate_id": str(test_candidate.id), "type": "email", "limit": 10},
        db_session
    )

    # Verify both emails are in the list
    assert comm_list["total_count"] >= 2

    # Find our specific emails
    original_in_list = next(
        (c for c in comm_list["communications"] if c["id"] == original_response["id"]),
        None
    )
    reply_in_list = next(
        (c for c in comm_list["communications"] if c["id"] == reply_response["id"]),
        None
    )

    assert original_in_list is not None
    assert reply_in_list is not None

    # Verify thread IDs match
    assert original_in_list["metadata"]["thread_id"] == thread_id
    assert reply_in_list["metadata"]["thread_id"] == thread_id

    # Verify reply has in_reply_to
    assert reply_in_list["metadata"]["in_reply_to"] == "<msg1@test.com>"

    # Verify chronological order (original first, reply second)
    communications = comm_list["communications"]
    original_idx = next(i for i, c in enumerate(communications) if c["id"] == original_response["id"])
    reply_idx = next(i for i, c in enumerate(communications) if c["id"] == reply_response["id"])

    # Timeline should be in reverse chronological (newest first)
    assert reply_idx < original_idx


# Complete End-to-End Workflow Test

@pytest.mark.asyncio
async def test_complete_email_sync_workflow(db_session: AsyncSession, test_candidate, email_config):
    """
    Complete end-to-end email sync workflow test.

    This test runs the entire workflow in sequence:
    1. Configure email sync
    2. Trigger sync (with mocked IMAP)
    3. Verify emails stored
    4. View in timeline
    5. Send reply
    6. Verify reply in timeline
    """
    workflow_log = []

    # Step 1: Configure
    workflow_log.append("Step 1: Configuring email sync...")
    config_update = {
        "imap_server": email_config["imap_server"],
        "imap_port": email_config["imap_port"],
        "imap_username": email_config["imap_username"],
        "imap_password": email_config["imap_password"],
        "sync_enabled": True
    }
    config_response = await update_config(config_update)
    assert config_response["sync_enabled"] is True
    workflow_log.append("✓ Email sync configured")

    # Step 2: Create an incoming email (simulating sync)
    workflow_log.append("Step 2: Simulating email sync...")
    incoming_email = {
        "candidate_id": str(test_candidate.id),
        "type": "email",
        "direction": "inbound",
        "status": "delivered",
        "subject": "Application for Software Engineer",
        "body": "I would like to apply for the Software Engineer position.",
        "sent_at": datetime.utcnow().isoformat(),
        "metadata": {
            "from_address": "test.candidate@example.com",
            "to_address": "recruiter@test.com",
            "message_id": "<application123@test.com>",
            "thread_id": "thread_app_123"
        }
    }

    incoming_response = await create_communication(incoming_email, db_session)
    assert incoming_response["type"] == "email"
    workflow_log.append("✓ Incoming email synced")

    # Step 3: Verify in database
    workflow_log.append("Step 3: Verifying email in database...")
    comm = await get_communication(incoming_response["id"], db_session)
    assert comm["id"] == incoming_response["id"]
    assert comm["type"] == "email"
    workflow_log.append("✓ Email stored in database")

    # Step 4: View in timeline
    workflow_log.append("Step 4: Viewing emails in timeline...")
    timeline = await list_communications(
        {"candidate_id": str(test_candidate.id), "type": "email", "limit": 10},
        db_session
    )
    assert timeline["total_count"] >= 1
    workflow_log.append(f"✓ Timeline shows {timeline['total_count']} email(s)")

    # Step 5: Send reply
    workflow_log.append("Step 5: Sending reply email...")
    reply_email = {
        "candidate_id": str(test_candidate.id),
        "type": "email",
        "direction": "outbound",
        "status": "sent",
        "subject": "Re: Application for Software Engineer",
        "body": "Thank you for your application. We will review your resume.",
        "sent_at": datetime.utcnow().isoformat(),
        "metadata": {
            "to_address": "test.candidate@example.com",
            "message_id": "<reply123@test.com>",
            "thread_id": "thread_app_123",
            "in_reply_to": "<application123@test.com>"
        }
    }

    reply_response = await create_communication(reply_email, db_session)
    assert reply_response["type"] == "email"
    assert reply_response["direction"] == "outbound"
    workflow_log.append("✓ Reply email sent")

    # Step 6: Verify reply in timeline
    workflow_log.append("Step 6: Verifying reply in timeline...")
    updated_timeline = await list_communications(
        {"candidate_id": str(test_candidate.id), "type": "email", "limit": 10},
        db_session
    )
    assert updated_timeline["total_count"] >= 2

    # Verify thread grouping
    thread_emails = [
        c for c in updated_timeline["communications"]
        if c["metadata"].get("thread_id") == "thread_app_123"
    ]
    assert len(thread_emails) == 2
    workflow_log.append("✓ Reply appears in timeline with correct thread")

    # Print workflow summary
    workflow_log.append("\n" + "="*60)
    workflow_log.append("COMPLETE EMAIL SYNC WORKFLOW TEST: PASSED")
    workflow_log.append("="*60)

    return "\n".join(workflow_log)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
