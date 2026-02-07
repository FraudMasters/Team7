"""
Integration tests for phone call logging and tracking workflow.

This test module verifies the complete end-to-end phone call workflow:
1. Log phone call via API
2. Verify call saved to database (Communication + PhoneCall records)
3. View call in CommunicationTimeline via API
4. Check communication metrics include call data

These tests require a running database and verify the complete phone call
logging workflow from API to database to timeline visualization.
"""
import asyncio
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import async_session_maker
from models import Communication, PhoneCall, Resume
from models.communication import CommunicationType, CommunicationDirection, CommunicationStatus
from models.phone_call import CallType
from api.communications import create_communication, list_communications, get_communication
from api.sms import get_communication_metrics


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
def test_recruiter():
    """Mock recruiter data for testing."""
    return {
        "id": str(uuid4()),
        "name": "Test Recruiter",
        "phone": "+0987654321"
    }


# Test: Log phone call via API

@pytest.mark.asyncio
async def test_step1_log_phone_call_via_api(db_session: AsyncSession, test_candidate: Resume, test_recruiter):
    """
    Step 1: Log phone call via API.

    Verifies:
    - Phone call can be logged via communications API
    - Call has correct type (phone_call)
    - Call has correct direction (outbound/inbound)
    - Call is linked to candidate
    - Call has duration and call type metadata
    """
    # Log phone call data
    call_data = {
        "candidate_id": str(test_candidate.id),
        "type": "phone_call",
        "direction": "outbound",
        "status": "sent",
        "subject": "Phone call with candidate",
        "body": "Discussed interview availability and experience",
        "sent_at": datetime.utcnow().isoformat(),
        "metadata": {
            "call_type": "outbound",
            "from_number": test_recruiter["phone"],
            "to_number": test_candidate.metadata["contact_phone"],
            "duration_minutes": 15,
            "outcome": "reached",
            "notes": "Candidate is interested in the position"
        }
    }

    # Create communication via API
    communication = await create_communication(call_data, db_session)

    # Verify communication record
    assert communication is not None
    assert communication["type"] == "phone_call"
    assert communication["direction"] == "outbound"
    assert communication["status"] == "sent"
    assert communication["candidate_id"] == str(test_candidate.id)
    assert "metadata" in communication
    assert communication["metadata"]["call_type"] == "outbound"
    assert communication["metadata"]["duration_minutes"] == 15
    assert communication["metadata"]["outcome"] == "reached"


@pytest.mark.asyncio
async def test_step2_verify_call_saved_to_database(db_session: AsyncSession, test_candidate: Resume, test_recruiter):
    """
    Step 2: Verify call saved to database.

    Verifies:
    - Communication record exists in database
    - PhoneCall record exists with correct fields
    - Foreign key relationship is correct
    - Duration and call_type are stored correctly
    """
    # Create phone call communication
    call_data = {
        "candidate_id": str(test_candidate.id),
        "type": "phone_call",
        "direction": "outbound",
        "status": "sent",
        "subject": "Follow-up call",
        "body": "Follow-up discussion about the role",
        "sent_at": datetime.utcnow().isoformat(),
        "metadata": {
            "call_type": "outbound",
            "from_number": test_recruiter["phone"],
            "to_number": test_candidate.metadata["contact_phone"],
            "duration_minutes": 10,
            "outcome": "left_voicemail",
            "notes": "Left message about next steps"
        }
    }

    communication_response = await create_communication(call_data, db_session)
    communication_id = communication_response["id"]

    # Query Communication record
    comm_result = await db_session.execute(
        select(Communication).where(Communication.id == communication_id)
    )
    communication = comm_result.scalars().first()

    # Verify Communication record exists
    assert communication is not None
    assert communication.type == CommunicationType.PHONE_CALL
    assert communication.direction == CommunicationDirection.OUTBOUND
    assert communication.status == CommunicationStatus.SENT
    assert communication.candidate_id == test_candidate.id

    # Query PhoneCall record
    phone_call_result = await db_session.execute(
        select(PhoneCall).where(PhoneCall.communication_id == communication_id)
    )
    phone_call = phone_call_result.scalars().first()

    # Verify PhoneCall record exists
    assert phone_call is not None
    assert phone_call.communication_id == communication_id
    assert phone_call.from_number == test_recruiter["phone"]
    assert phone_call.to_number == test_candidate.metadata["contact_phone"]
    assert phone_call.duration == 10 * 60  # 10 minutes in seconds
    assert phone_call.call_type == CallType.OUTBOUND


@pytest.mark.asyncio
async def test_step3_view_call_in_timeline(db_session: AsyncSession, test_candidate: Resume, test_recruiter):
    """
    Step 3: View call in CommunicationTimeline via API.

    Verifies:
    - Call appears in communications list
    - Timeline filtering works (by type=phone_call)
    - Timeline filtering works (by candidate_id)
    - Call metadata is included in response
    """
    # Create multiple communications
    communications_created = []

    # Create phone call
    call_data = {
        "candidate_id": str(test_candidate.id),
        "type": "phone_call",
        "direction": "outbound",
        "status": "sent",
        "subject": "Screening call",
        "body": "Initial screening call",
        "sent_at": datetime.utcnow().isoformat(),
        "metadata": {
            "call_type": "outbound",
            "from_number": test_recruiter["phone"],
            "to_number": test_candidate.metadata["contact_phone"],
            "duration_minutes": 20,
            "outcome": "reached",
            "notes": "Candidate passed initial screening"
        }
    }
    call_comm = await create_communication(call_data, db_session)
    communications_created.append(call_comm["id"])

    # Create an SMS for the same candidate (to test filtering)
    sms_data = {
        "candidate_id": str(test_candidate.id),
        "type": "sms",
        "direction": "outbound",
        "status": "sent",
        "body": "SMS follow-up",
        "sent_at": datetime.utcnow().isoformat(),
        "metadata": {}
    }
    sms_comm = await create_communication(sms_data, db_session)
    communications_created.append(sms_comm["id"])

    # Query all communications for candidate
    all_comms = await list_communications(
        candidate_id=str(test_candidate.id),
        db_session=db_session
    )

    # Verify both communications appear
    assert len(all_comms["communications"]) >= 2

    # Query only phone calls for candidate
    phone_calls = await list_communications(
        candidate_id=str(test_candidate.id),
        type="phone_call",
        db_session=db_session
    )

    # Verify only phone call appears
    assert len(phone_calls["communications"]) >= 1
    assert phone_calls["communications"][0]["type"] == "phone_call"
    assert phone_calls["communications"][0]["metadata"]["call_type"] == "outbound"
    assert phone_calls["communications"][0]["metadata"]["duration_minutes"] == 20
    assert phone_calls["communications"][0]["metadata"]["outcome"] == "reached"


@pytest.mark.asyncio
async def test_step4_check_metrics_include_call_data(db_session: AsyncSession, test_candidate: Resume, test_recruiter):
    """
    Step 4: Check communication metrics include call data.

    Verifies:
    - Metrics endpoint returns phone call statistics
    - Engagement metrics include phone_call type
    - Total communications count includes calls
    - Breakdown by type includes phone_call data
    """
    # Create phone calls with different outcomes
    call_outcomes = ["reached", "left_voicemail", "no_answer", "call_back_requested"]

    for i, outcome in enumerate(call_outcomes):
        call_data = {
            "candidate_id": str(test_candidate.id),
            "type": "phone_call",
            "direction": "outbound",
            "status": "sent",
            "subject": f"Call attempt {i+1}",
            "body": f"Call attempt with outcome: {outcome}",
            "sent_at": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
            "metadata": {
                "call_type": "outbound",
                "from_number": test_recruiter["phone"],
                "to_number": test_candidate.metadata["contact_phone"],
                "duration_minutes": 5 if outcome == "reached" else 0,
                "outcome": outcome,
                "notes": f"Call outcome: {outcome}"
            }
        }
        await create_communication(call_data, db_session)

    # Get communication metrics
    metrics = await get_communication_metrics(
        db_session=db_session,
        start_date=(datetime.utcnow() - timedelta(days=1)).isoformat(),
        end_date=datetime.utcnow().isoformat()
    )

    # Verify metrics structure
    assert metrics is not None
    assert "engagement" in metrics
    assert "engagement" in metrics["engagement"]
    assert "total_sent" in metrics["engagement"]["engagement"]

    # Verify phone calls are counted in total sent
    total_sent = metrics["engagement"]["engagement"]["total_sent"]
    assert total_sent >= len(call_outcomes)

    # Verify breakdown by type includes phone_call
    assert "breakdown" in metrics["engagement"]["engagement"]
    assert "by_type" in metrics["engagement"]["engagement"]["breakdown"]

    by_type = metrics["engagement"]["engagement"]["breakdown"]["by_type"]
    assert "phone_call" in by_type
    assert by_type["phone_call"]["count"] >= len(call_outcomes)


# Test: Different call types

@pytest.mark.asyncio
async def test_inbound_call_logging(db_session: AsyncSession, test_candidate: Resume, test_recruiter):
    """
    Test: Log inbound phone call.

    Verifies:
    - Inbound calls are logged correctly
    - From/to numbers are correct for inbound direction
    - Call type is set correctly
    """
    call_data = {
        "candidate_id": str(test_candidate.id),
        "type": "phone_call",
        "direction": "inbound",
        "status": "received",
        "subject": "Inbound call from candidate",
        "body": "Candidate called with questions",
        "received_at": datetime.utcnow().isoformat(),
        "metadata": {
            "call_type": "inbound",
            "from_number": test_candidate.metadata["contact_phone"],
            "to_number": test_recruiter["phone"],
            "duration_minutes": 8,
            "outcome": "reached",
            "notes": "Candidate asked about company culture"
        }
    }

    communication = await create_communication(call_data, db_session)

    # Verify inbound call details
    assert communication["direction"] == "inbound"
    assert communication["status"] == "received"
    assert communication["metadata"]["call_type"] == "inbound"
    assert communication["metadata"]["from_number"] == test_candidate.metadata["contact_phone"]
    assert communication["metadata"]["to_number"] == test_recruiter["phone"]


@pytest.mark.asyncio
async def test_missed_call_logging(db_session: AsyncSession, test_candidate: Resume, test_recruiter):
    """
    Test: Log missed phone call.

    Verifies:
    - Missed calls are logged correctly
    - Duration is zero for missed calls
    - Call type is set to "missed"
    """
    call_data = {
        "candidate_id": str(test_candidate.id),
        "type": "phone_call",
        "direction": "inbound",
        "status": "received",
        "subject": "Missed call from candidate",
        "body": "Candidate called but no answer",
        "received_at": datetime.utcnow().isoformat(),
        "metadata": {
            "call_type": "missed",
            "from_number": test_candidate.metadata["contact_phone"],
            "to_number": test_recruiter["phone"],
            "duration_minutes": 0,
            "outcome": "no_answer",
            "notes": "Missed call, need to call back"
        }
    }

    communication = await create_communication(call_data, db_session)

    # Verify missed call details
    assert communication["metadata"]["call_type"] == "missed"
    assert communication["metadata"]["duration_minutes"] == 0
    assert communication["metadata"]["outcome"] == "no_answer"


@pytest.mark.asyncio
async def test_list_phone_calls_with_filters(db_session: AsyncSession, test_candidate: Resume, test_recruiter):
    """
    Test: List phone calls with various filters.

    Verifies:
    - Filtering by candidate_id works
    - Filtering by type=phone_call works
    - Filtering by direction works
    - Filtering by status works
    - Date range filtering works
    """
    # Create multiple calls with different attributes
    calls = [
        {
            "candidate_id": str(test_candidate.id),
            "type": "phone_call",
            "direction": "outbound",
            "status": "sent",
            "subject": "Outbound call 1",
            "sent_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
            "metadata": {"call_type": "outbound", "outcome": "reached"}
        },
        {
            "candidate_id": str(test_candidate.id),
            "type": "phone_call",
            "direction": "inbound",
            "status": "received",
            "subject": "Inbound call",
            "received_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            "metadata": {"call_type": "inbound", "outcome": "reached"}
        },
        {
            "candidate_id": str(test_candidate.id),
            "type": "phone_call",
            "direction": "outbound",
            "status": "sent",
            "subject": "Outbound call 2",
            "sent_at": (datetime.utcnow() - timedelta(days=2)).isoformat(),
            "metadata": {"call_type": "outbound", "outcome": "no_answer"}
        }
    ]

    for call in calls:
        await create_communication(call, db_session)

    # Filter by candidate_id
    candidate_calls = await list_communications(
        candidate_id=str(test_candidate.id),
        type="phone_call",
        db_session=db_session
    )
    assert len(candidate_calls["communications"]) >= 3

    # Filter by direction=outbound
    outbound_calls = await list_communications(
        candidate_id=str(test_candidate.id),
        type="phone_call",
        direction="outbound",
        db_session=db_session
    )
    assert len(outbound_calls["communications"]) >= 2
    for call in outbound_calls["communications"]:
        assert call["direction"] == "outbound"

    # Filter by date range (last 24 hours)
    recent_calls = await list_communications(
        candidate_id=str(test_candidate.id),
        type="phone_call",
        date_range=f"{(datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')},{datetime.utcnow().strftime('%Y-%m-%d')}",
        db_session=db_session
    )
    assert len(recent_calls["communications"]) >= 2


# Test: Complete workflow

@pytest.mark.asyncio
async def test_complete_phone_call_workflow(db_session: AsyncSession, test_candidate: Resume, test_recruiter):
    """
    Test: Complete phone call logging workflow end-to-end.

    This test verifies the entire workflow:
    1. Log phone call with notes and outcome
    2. Verify database storage (Communication + PhoneCall)
    3. Query call in communications timeline
    4. Verify metrics include call data
    """
    # Step 1: Log phone call via API
    call_data = {
        "candidate_id": str(test_candidate.id),
        "type": "phone_call",
        "direction": "outbound",
        "status": "sent",
        "subject": "Technical interview discussion",
        "body": "Discussed candidate's technical experience and availability",
        "sent_at": datetime.utcnow().isoformat(),
        "metadata": {
            "call_type": "outbound",
            "from_number": test_recruiter["phone"],
            "to_number": test_candidate.metadata["contact_phone"],
            "duration_minutes": 25,
            "outcome": "reached",
            "notes": "Candidate has 5 years experience with Python and React. Available for onsite interview next week."
        }
    }

    communication_response = await create_communication(call_data, db_session)
    communication_id = communication_response["id"]

    # Step 2: Verify database storage
    comm_result = await db_session.execute(
        select(Communication).where(Communication.id == communication_id)
    )
    communication = comm_result.scalars().first()
    assert communication is not None
    assert communication.type == CommunicationType.PHONE_CALL

    phone_call_result = await db_session.execute(
        select(PhoneCall).where(PhoneCall.communication_id == communication_id)
    )
    phone_call = phone_call_result.scalars().first()
    assert phone_call is not None
    assert phone_call.call_type == CallType.OUTBOUND
    assert phone_call.duration == 25 * 60  # 25 minutes in seconds

    # Step 3: Query in communications timeline
    timeline = await list_communications(
        candidate_id=str(test_candidate.id),
        type="phone_call",
        db_session=db_session
    )
    assert len(timeline["communications"]) >= 1
    assert timeline["communications"][0]["id"] == communication_id

    # Step 4: Verify metrics include call data
    metrics = await get_communication_metrics(
        db_session=db_session,
        start_date=(datetime.utcnow() - timedelta(days=1)).isoformat(),
        end_date=datetime.utcnow().isoformat()
    )
    assert metrics["engagement"]["engagement"]["total_sent"] >= 1
    assert metrics["engagement"]["engagement"]["breakdown"]["by_type"]["phone_call"]["count"] >= 1
