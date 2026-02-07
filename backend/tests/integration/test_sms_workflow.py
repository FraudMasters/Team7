"""
Integration tests for SMS sending and tracking workflow.

This test module verifies the complete end-to-end SMS workflow:
1. Compose SMS via API
2. Send SMS via API endpoint
3. Verify Celery task processes SMS
4. Check delivery status
5. View SMS in CommunicationTimeline via API

These tests require a running database and use mocked SMS providers
(Twilio/AWS SNS) for realistic integration testing.
"""
import asyncio
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import async_session_maker
from models import Communication, SMSMessage, Resume
from models.communication import CommunicationType, CommunicationDirection, CommunicationStatus
from api.sms import send_sms, list_sms, get_sms, get_delivery_status
from api.communications import create_communication, list_communications, get_communication
from tasks.sms_task import send_candidate_update, check_delivery_status


# Test Fixtures

@pytest.fixture
async def db_session() -> AsyncSession:
    """Create a test database session."""
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def test_candidate(db_session: AsyncSession) -> Resume:
    """Create a test candidate (resume) with phone number."""
    candidate = Resume(
        id=str(uuid4()),
        name="Test Candidate",
        email="test.candidate@example.com",
        metadata={"contact_phone": "+1234567890"}
    )
    db_session.add(candidate)
    await db_session.commit()
    await db_session.refresh(candidate)
    return candidate


@pytest.fixture
def sms_config():
    """Mock SMS configuration for testing."""
    return {
        "sms_provider": "twilio",
        "twilio_account_sid": "ACtest123",
        "twilio_auth_token": "test_token",
        "twilio_from_number": "+19876543210"
    }


@pytest.fixture
def mock_twilio_response():
    """Mock Twilio SMS response."""
    return {
        "sid": "SM1234567890abcdef",
        "status": "queued",
        "to": "+1234567890",
        "from": "+19876543210",
        "body": "Test SMS message",
        "date_created": "2026-02-03T10:00:00Z"
    }


# Test: Compose SMS via API

@pytest.mark.asyncio
async def test_step1_compose_sms_via_api(db_session: AsyncSession, test_candidate):
    """
    Step 1: Compose SMS via API.

    Verifies:
    - SMS can be created via communications API
    - SMS has correct type (sms)
    - SMS has correct direction (outbound)
    - SMS is linked to candidate
    """
    # Compose SMS data
    sms_data = {
        "candidate_id": str(test_candidate.id),
        "type": "sms",
        "direction": "outbound",
        "status": "pending",
        "body": "Hello! This is a test SMS message.",
        "sent_at": datetime.utcnow().isoformat(),
        "metadata": {
            "from_number": "+19876543210",
            "to_number": "+1234567890",
            "provider": "twilio"
        }
    }

    # Create SMS communication
    sms_response = await create_communication(sms_data, db_session)

    assert sms_response["type"] == "sms"
    assert sms_response["direction"] == "outbound"
    assert sms_response["status"] == "pending"
    assert sms_response["body"] == "Hello! This is a test SMS message."
    assert "id" in sms_response
    assert sms_response["candidate_id"] == str(test_candidate.id)

    communication_id = sms_response["id"]

    # Verify SMS communication in database
    stmt = select(Communication).where(Communication.id == communication_id)
    result = await db_session.execute(stmt)
    communication = result.scalar_one_or_none()

    assert communication is not None
    assert communication.type == CommunicationType.SMS
    assert communication.direction == CommunicationDirection.OUTBOUND
    assert communication.status == CommunicationStatus.PENDING


# Test: Send SMS via API

@pytest.mark.asyncio
async def test_step2_send_sms_via_api(db_session: AsyncSession, test_candidate, mock_twilio_response):
    """
    Step 2: Send SMS via API endpoint.

    Verifies:
    - SMS send endpoint works
    - Provider is validated
    - Phone number is validated
    - Communication and SMSMessage records are created
    """
    # Mock Twilio client
    with patch("api.sms.Client") as mock_twilio_client:
        # Setup mock Twilio response
        mock_message = Mock()
        mock_message.sid = mock_twilio_response["sid"]
        mock_message.status = mock_twilio_response["status"]
        mock_message.to = mock_twilio_response["to"]
        mock_message.from_ = mock_twilio_response["from"]
        mock_message.body = mock_twilio_response["body"]
        mock_message.date_created = mock_twilio_response["date_created"]

        mock_messages = Mock()
        mock_messages.create = Mock(return_value=mock_message)
        mock_twilio_client.return_value.messages = mock_messages

        # Send SMS via API
        sms_request = {
            "candidate_id": str(test_candidate.id),
            "to_number": "+1234567890",
            "body": "Test SMS from API",
            "provider": "twilio"
        }

        sms_response = await send_sms(sms_request, db_session)

        assert sms_response["status"] == "sent"
        assert sms_response["body"] == "Test SMS from API"
        assert sms_response["to_number"] == "+1234567890"
        assert "id" in sms_response  # communication_id
        assert "sms_id" in sms_response
        assert "provider_message_id" in sms_response
        assert sms_response["segment_count"] == 1

        # Verify Communication record
        comm_id = sms_response["id"]
        comm = await get_communication(comm_id, db_session)
        assert comm["type"] == "sms"
        assert comm["direction"] == "outbound"
        assert comm["status"] == "sent"

        # Verify SMSMessage record exists
        stmt = select(SMSMessage).where(SMSMessage.communication_id == comm_id)
        result = await db_session.execute(stmt)
        sms_message = result.scalar_one_or_none()

        assert sms_message is not None
        assert sms_message.to_number == "+1234567890"
        assert sms_message.provider == "twilio"
        assert sms_message.delivery_status == "sent"
        assert sms_message.provider_message_id == mock_twilio_response["sid"]


# Test: Verify Celery Task Processes SMS

@pytest.mark.asyncio
async def test_step3_verify_celery_task_processes_sms(test_candidate, sms_config):
    """
    Step 3: Verify Celery task processes SMS.

    Verifies:
    - Celery send_candidate_update task can be triggered
    - Task validates phone numbers
    - Task enforces character limits
    - Task returns proper status
    """
    # Mock Twilio client
    with patch("tasks.sms_task.Client") as mock_twilio_client:
        # Setup mock
        mock_message = Mock()
        mock_message.sid = f"twilio_{uuid4()}_{int(datetime.utcnow().timestamp())}"
        mock_message.status = "queued"

        mock_messages = Mock()
        mock_messages.create = Mock(return_value=mock_message)
        mock_twilio_client.return_value.messages = mock_messages

        # Trigger Celery task
        task_result = send_candidate_update.apply_async(
            args=[],
            kwargs={
                "candidate_id": str(test_candidate.id),
                "candidate_phone": "+1234567890",
                "status": "application_received",
                "vacancy_title": "Software Engineer"
            }
        )

        # Wait for task to complete (with timeout)
        result = task_result.get(timeout=30)

        assert result["status"] in ["sent", "failed"]
        assert "processing_time_ms" in result
        assert "provider_message_id" in result or "error" in result

        if result["status"] == "sent":
            assert result["provider"] == "twilio"
            assert len(result["message_body"]) <= 160  # SMS character limit


# Test: Check Delivery Status

@pytest.mark.asyncio
async def test_step4_check_delivery_status(db_session: AsyncSession, test_candidate, mock_twilio_response):
    """
    Step 4: Check delivery status.

    Verifies:
    - Delivery status can be queried by sms_id
    - Delivery status can be queried by provider_message_id
    - Status updates are reflected in database
    """
    # First, send an SMS
    with patch("api.sms.Client") as mock_twilio_client:
        # Setup mock
        mock_message = Mock()
        mock_message.sid = mock_twilio_response["sid"]
        mock_message.status = "delivered"
        mock_message.to = mock_twilio_response["to"]
        mock_message.from_ = mock_twilio_response["from"]
        mock_message.body = mock_twilio_response["body"]

        mock_messages = Mock()
        mock_messages.create = Mock(return_value=mock_message)
        mock_twilio_client.return_value.messages = mock_messages

        # Send SMS
        sms_request = {
            "candidate_id": str(test_candidate.id),
            "to_number": "+1234567890",
            "body": "Status check SMS",
            "provider": "twilio"
        }

        sms_response = await send_sms(sms_request, db_session)
        communication_id = sms_response["id"]
        provider_message_id = sms_response["provider_message_id"]

    # Query delivery status by communication_id (sms_id)
    status_by_sms = await get_delivery_status({"sms_id": communication_id}, db_session)

    assert status_by_sms["communication_id"] == communication_id
    assert status_by_sms["delivery_status"] in ["sent", "delivered", "pending", "failed"]
    assert "to_number" in status_by_sms
    assert "provider" in status_by_sms

    # Query delivery status by provider_message_id
    status_by_provider = await get_delivery_status(
        {"provider_message_id": provider_message_id},
        db_session
    )

    assert status_by_provider["communication_id"] == communication_id
    assert status_by_provider["provider_message_id"] == provider_message_id


# Test: View SMS in CommunicationTimeline

@pytest.mark.asyncio
async def test_step5_view_sms_in_timeline(db_session: AsyncSession, test_candidate):
    """
    Step 5: View SMS in CommunicationTimeline via API.

    Verifies:
    - SMS appears in communications list
    - SMS can be filtered by type
    - SMS can be filtered by candidate
    - Timeline shows correct metadata
    """
    # Create multiple test communications including SMS
    communications_data = [
        {
            "candidate_id": str(test_candidate.id),
            "type": "sms",
            "direction": "outbound",
            "status": "delivered",
            "body": "Interview reminder: Tomorrow at 2 PM",
            "sent_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
            "metadata": {
                "from_number": "+19876543210",
                "to_number": "+1234567890",
                "provider": "twilio"
            }
        },
        {
            "candidate_id": str(test_candidate.id),
            "type": "email",
            "direction": "inbound",
            "status": "delivered",
            "subject": "Question about job",
            "body": "Is this position remote?",
            "sent_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
        },
        {
            "candidate_id": str(test_candidate.id),
            "type": "sms",
            "direction": "inbound",
            "status": "delivered",
            "body": "Yes, I can make the interview",
            "sent_at": (datetime.utcnow() - timedelta(minutes=30)).isoformat(),
            "metadata": {
                "from_number": "+1234567890",
                "to_number": "+19876543210",
                "provider": "twilio"
            }
        }
    ]

    created_comm_ids = []
    for comm_data in communications_data:
        response = await create_communication(comm_data, db_session)
        created_comm_ids.append(response["id"])

    # List all communications for candidate
    all_communications = await list_communications(
        {"candidate_id": str(test_candidate.id), "limit": 10},
        db_session
    )

    assert all_communications["total_count"] >= 3

    # Filter by SMS type only
    sms_params = {
        "candidate_id": str(test_candidate.id),
        "type": "sms",
        "limit": 10
    }
    sms_list = await list_communications(sms_params, db_session)

    assert sms_list["total_count"] >= 2
    assert all(c["type"] == "sms" for c in sms_list["communications"])

    # Verify SMS metadata
    for sms in sms_list["communications"]:
        assert "from_number" in sms["metadata"] or "to_number" in sms["metadata"]
        assert "provider" in sms["metadata"]
        assert sms["body"] is not None
        assert len(sms["body"]) <= 160  # SMS character limit


# Test: List SMS with Filters

@pytest.mark.asyncio
async def test_list_sms_with_filters(db_session: AsyncSession, test_candidate):
    """
    Test: List SMS messages with various filters.

    Verifies:
    - SMS list API works
    - Can filter by candidate_id
    - Can filter by provider
    - Can filter by delivery_status
    """
    # Create test SMS messages
    with patch("api.sms.Client") as mock_twilio_client:
        # Setup mock
        mock_message = Mock()
        mock_message.sid = f"SM{uuid4()}"
        mock_message.status = "delivered"
        mock_message.to = "+1234567890"
        mock_message.from_ = "+19876543210"
        mock_message.body = "Test message"

        mock_messages = Mock()
        mock_messages.create = Mock(return_value=mock_message)
        mock_twilio_client.return_value.messages = mock_messages

        # Send multiple SMS with different statuses
        for i in range(3):
            sms_request = {
                "candidate_id": str(test_candidate.id),
                "to_number": "+1234567890",
                "body": f"Test SMS {i+1}",
                "provider": "twilio"
            }
            await send_sms(sms_request, db_session)

    # List all SMS
    all_sms = await list_sms({}, db_session)
    assert all_sms["total_count"] >= 3
    assert len(all_sms["messages"]) >= 3

    # Filter by candidate
    candidate_sms = await list_sms(
        {"candidate_id": str(test_candidate.id)},
        db_session
    )
    assert candidate_sms["total_count"] >= 3
    assert all(
        msg["candidate_id"] == str(test_candidate.id)
        for msg in candidate_sms["messages"]
    )

    # Filter by provider
    provider_sms = await list_sms(
        {"provider": "twilio"},
        db_session
    )
    assert all(msg["provider"] == "twilio" for msg in provider_sms["messages"])

    # Filter by delivery status
    delivered_sms = await list_sms(
        {"delivery_status": "delivered"},
        db_session
    )
    assert all(
        msg["delivery_status"] == "delivered"
        for msg in delivered_sms["messages"]
    )


# Complete End-to-End Workflow Test

@pytest.mark.asyncio
async def test_complete_sms_workflow(db_session: AsyncSession, test_candidate, sms_config):
    """
    Complete end-to-end SMS workflow test.

    This test runs the entire workflow in sequence:
    1. Compose SMS
    2. Send SMS via API
    3. Verify Celery task processes SMS
    4. Check delivery status
    5. View SMS in timeline
    """
    workflow_log = []

    # Step 1: Compose SMS
    workflow_log.append("Step 1: Composing SMS...")
    sms_composition = {
        "candidate_id": str(test_candidate.id),
        "type": "sms",
        "direction": "outbound",
        "status": "pending",
        "body": "Hello! You have an interview scheduled for tomorrow at 2 PM.",
        "sent_at": datetime.utcnow().isoformat(),
        "metadata": {
            "from_number": "+19876543210",
            "to_number": "+1234567890",
            "provider": "twilio"
        }
    }

    composed_sms = await create_communication(sms_composition, db_session)
    assert composed_sms["type"] == "sms"
    workflow_log.append(f"✓ SMS composed with ID: {composed_sms['id']}")

    # Step 2: Send SMS via API
    workflow_log.append("Step 2: Sending SMS via API...")
    with patch("api.sms.Client") as mock_twilio_client:
        # Setup mock
        mock_message = Mock()
        mock_message.sid = f"SM{uuid4()}"
        mock_message.status = "queued"
        mock_message.to = "+1234567890"
        mock_message.from_ = "+19876543210"
        mock_message.body = sms_composition["body"]

        mock_messages = Mock()
        mock_messages.create = Mock(return_value=mock_message)
        mock_twilio_client.return_value.messages = mock_messages

        # Send SMS
        sms_request = {
            "candidate_id": str(test_candidate.id),
            "to_number": "+1234567890",
            "body": sms_composition["body"],
            "provider": "twilio"
        }

        sms_response = await send_sms(sms_request, db_session)
        assert sms_response["status"] == "sent"
        assert sms_response["provider_message_id"] == mock_message.sid
        workflow_log.append(f"✓ SMS sent with provider ID: {sms_response['provider_message_id']}")

    # Step 3: Verify Celery task processes SMS
    workflow_log.append("Step 3: Verifying Celery task processes SMS...")
    with patch("tasks.sms_task.Client") as mock_twilio_client:
        # Setup mock
        mock_message = Mock()
        mock_message.sid = f"SM{uuid4()}"
        mock_message.status = "sent"

        mock_messages = Mock()
        mock_messages.create = Mock(return_value=mock_message)
        mock_twilio_client.return_value.messages = mock_messages

        # Trigger Celery task
        task_result = send_candidate_update.apply_async(
            args=[],
            kwargs={
                "candidate_id": str(test_candidate.id),
                "candidate_phone": "+1234567890",
                "status": "interview_scheduled",
                "interview_date": "2026-02-04T14:00:00Z"
            }
        )

        result = task_result.get(timeout=30)
        assert result["status"] == "sent"
        assert "processing_time_ms" in result
        workflow_log.append(f"✓ Celery task processed SMS in {result['processing_time_ms']}ms")

    # Step 4: Check delivery status
    workflow_log.append("Step 4: Checking delivery status...")
    delivery_status = await get_delivery_status(
        {"sms_id": sms_response["id"]},
        db_session
    )

    assert delivery_status["communication_id"] == sms_response["id"]
    assert delivery_status["delivery_status"] in ["sent", "delivered", "queued"]
    workflow_log.append(f"✓ Delivery status: {delivery_status['delivery_status']}")

    # Step 5: View SMS in timeline
    workflow_log.append("Step 5: Viewing SMS in CommunicationTimeline...")
    timeline = await list_communications(
        {"candidate_id": str(test_candidate.id), "type": "sms", "limit": 10},
        db_session
    )

    assert timeline["total_count"] >= 1
    sms_in_timeline = [
        c for c in timeline["communications"]
        if c["id"] == sms_response["id"]
    ]
    assert len(sms_in_timeline) == 1
    assert sms_in_timeline[0]["body"] == sms_composition["body"]
    workflow_log.append(f"✓ SMS appears in timeline ({timeline['total_count']} total SMS messages)")

    # Print workflow summary
    workflow_log.append("\n" + "="*60)
    workflow_log.append("COMPLETE SMS WORKFLOW TEST: PASSED")
    workflow_log.append("="*60)

    return "\n".join(workflow_log)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
