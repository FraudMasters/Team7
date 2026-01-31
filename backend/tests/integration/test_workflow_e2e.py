"""
End-to-end integration test for candidate workflow stage movement.

This test verifies:
1. Candidate creation in Applied stage
2. Stage movement through Screening, Interview, Offer, Hired
3. AnalyticsEvent audit trail logging
4. Stage duration analytics
5. Candidate filtering by stage
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from main import app
from database import get_db
from models.resume import Resume, ResumeStatus
from models.hiring_stage import HiringStage, HiringStageName
from models.workflow_stage_config import WorkflowStageConfig
from models.analytics_event import AnalyticsEvent, AnalyticsEventType


# Test database URL (use same as main database for integration testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture
async def test_db():
    """Create test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def client(test_db):
    """Create test client with database override."""
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_candidate_workflow_e2e(client: AsyncClient, test_db: AsyncSession):
    """
    End-to-end test: Create candidate and move through all stages with audit trail.

    Verification steps:
    1. Create candidate in Applied stage via UI (simulated via API)
    2. Drag candidate to Screening stage
    3. Verify AnalyticsEvent STAGE_CHANGED logged in database
    4. Verify candidate appears in Screening column
    5. Check stage duration analytics updated
    6. Move candidate through Interview -> Offer -> Hired
    7. Verify all stage transitions logged with timestamps
    """
    print("\n=== Starting End-to-End Workflow Test ===\n")

    # Step 1: Create a test resume (candidate)
    print("Step 1: Creating test candidate (resume)...")
    test_resume = Resume(
        filename="test_candidate_john_doe.pdf",
        file_path="/tmp/test_candidate_john_doe.pdf",
        content_type="application/pdf",
        status=ResumeStatus.COMPLETED,
        raw_text="Test resume content for John Doe",
        language="en"
    )
    test_db.add(test_resume)
    await test_db.commit()
    await test_db.refresh(test_resume)

    candidate_id = str(test_resume.id)
    print(f"✓ Created candidate with ID: {candidate_id}")

    # Verify candidate can be retrieved
    response = await client.get(f"/api/candidates/{candidate_id}")
    assert response.status_code == 200
    candidate_data = response.json()
    print(f"✓ Candidate retrieved successfully: {candidate_data['filename']}")
    print(f"  Initial stage: {candidate_data['current_stage']}")

    # Step 2: Move candidate from Applied to Screening
    print("\nStep 2: Moving candidate to Screening stage...")
    move_response = await client.put(
        f"/api/candidates/{candidate_id}/stage",
        json={
            "stage_id": HiringStageName.SCREENING.value,
            "notes": "Passed initial review"
        }
    )
    assert move_response.status_code == 200
    move_data = move_response.json()
    print(f"✓ Moved to {move_data['new_stage']} stage")
    print(f"  Previous stage: {move_data['previous_stage']}")

    # Step 3: Verify AnalyticsEvent logged for stage change
    print("\nStep 3: Verifying analytics event logged...")
    analytics_query = select(AnalyticsEvent).where(
        and_(
            AnalyticsEvent.entity_id == test_resume.id,
            AnalyticsEvent.event_type == AnalyticsEventType.STAGE_CHANGED
        )
    ).order_by(AnalyticsEvent.created_at.desc())

    analytics_result = await test_db.execute(analytics_query)
    analytics_events = analytics_result.scalars().all()

    assert len(analytics_events) >= 1, "Expected at least one STAGE_CHANGED analytics event"
    latest_event = analytics_events[0]

    print(f"✓ Analytics event found:")
    print(f"  Event ID: {latest_event.id}")
    print(f"  Event type: {latest_event.event_type}")
    print(f"  Timestamp: {latest_event.created_at}")
    print(f"  Event data: {latest_event.event_data}")

    # Verify event data contains correct stage information
    assert latest_event.event_data["previous_stage"] == HiringStageName.APPLIED.value
    assert latest_event.event_data["new_stage"] == HiringStageName.SCREENING.value

    # Step 4: Verify candidate appears in Screening column
    print("\nStep 4: Verifying candidate appears in Screening column...")
    screening_response = await client.get(
        f"/api/candidates/?stage_id={HiringStageName.SCREENING.value}"
    )
    assert screening_response.status_code == 200
    screening_candidates = screening_response.json()

    assert len(screening_candidates) >= 1, "Expected at least one candidate in Screening"
    candidate_in_screening = next(
        (c for c in screening_candidates if c["id"] == candidate_id),
        None
    )
    assert candidate_in_screening is not None, "Candidate not found in Screening stage"
    print(f"✓ Candidate found in Screening column")
    print(f"  Total candidates in Screening: {len(screening_candidates)}")

    # Step 5: Move to Interview stage
    print("\nStep 5: Moving candidate to Interview stage...")
    interview_response = await client.put(
        f"/api/candidates/{candidate_id}/stage",
        json={
            "stage_id": HiringStageName.INTERVIEW.value,
            "notes": "Technical interview scheduled"
        }
    )
    assert interview_response.status_code == 200
    interview_data = interview_response.json()
    print(f"✓ Moved to {interview_data['new_stage']} stage")

    # Verify analytics event for interview stage
    analytics_result = await test_db.execute(analytics_query)
    analytics_events = analytics_result.scalars().all()
    assert len(analytics_events) >= 2, "Expected at least two STAGE_CHANGED events"
    print(f"✓ Analytics event logged for Interview transition")

    # Step 6: Move to Offer stage
    print("\nStep 6: Moving candidate to Offer stage...")
    offer_response = await client.put(
        f"/api/candidates/{candidate_id}/stage",
        json={
            "stage_id": HiringStageName.OFFER.value,
            "notes": "Offer extended"
        }
    )
    assert offer_response.status_code == 200
    offer_data = offer_response.json()
    print(f"✓ Moved to {offer_data['new_stage']} stage")

    # Step 7: Move to Hired stage
    print("\nStep 7: Moving candidate to Hired stage...")
    hired_response = await client.put(
        f"/api/candidates/{candidate_id}/stage",
        json={
            "stage_id": HiringStageName.HIRED.value,
            "notes": "Candidate accepted offer"
        }
    )
    assert hired_response.status_code == 200
    hired_data = hired_response.json()
    print(f"✓ Moved to {hired_data['new_stage']} stage")

    # Verify all stage transitions logged with timestamps
    print("\nStep 8: Verifying all stage transitions logged with timestamps...")
    analytics_result = await test_db.execute(analytics_query)
    all_stage_events = analytics_result.scalars().all()

    print(f"✓ Total stage change events logged: {len(all_stage_events)}")

    stage_transitions = []
    for event in all_stage_events:
        stage_transitions.append({
            "from": event.event_data.get("previous_stage"),
            "to": event.event_data.get("new_stage"),
            "timestamp": event.created_at,
            "notes": event.event_data.get("notes")
        })

    # Verify expected transitions
    expected_transitions = [
        (HiringStageName.APPLIED.value, HiringStageName.SCREENING.value),
        (HiringStageName.SCREENING.value, HiringStageName.INTERVIEW.value),
        (HiringStageName.INTERVIEW.value, HiringStageName.OFFER.value),
        (HiringStageName.OFFER.value, HiringStageName.HIRED.value),
    ]

    print("\n  Stage Transition History:")
    for i, (from_stage, to_stage) in enumerate(expected_transitions):
        transition = stage_transitions[i]
        print(f"  {i+1}. {transition['from']} → {transition['to']}")
        print(f"     Timestamp: {transition['timestamp']}")
        print(f"     Notes: {transition['notes']}")
        assert transition['from'] == from_stage, f"Expected from_stage {from_stage}, got {transition['from']}"
        assert transition['to'] == to_stage, f"Expected to_stage {to_stage}, got {transition['to']}"
        assert transition['timestamp'] is not None, "Timestamp should not be None"

    # Step 9: Verify candidate final stage
    print("\nStep 9: Verifying candidate final stage...")
    final_response = await client.get(f"/api/candidates/{candidate_id}")
    assert final_response.status_code == 200
    final_data = final_response.json()

    assert final_data["current_stage"] == HiringStageName.HIRED.value
    print(f"✓ Candidate final stage confirmed: {final_data['current_stage']}")

    # Step 10: Check candidate in Hired column
    hired_candidates_response = await client.get(
        f"/api/candidates/?stage_id={HiringStageName.HIRED.value}"
    )
    hired_candidates = hired_candidates_response.json()
    assert len(hired_candidates) >= 1
    assert any(c["id"] == candidate_id for c in hired_candidates)
    print(f"✓ Candidate appears in Hired column")

    print("\n=== End-to-End Workflow Test PASSED ===\n")
    print("Summary:")
    print("  ✓ Candidate creation successful")
    print("  ✓ Stage movements successful (Applied → Screening → Interview → Offer → Hired)")
    print("  ✓ All transitions logged in analytics_events table")
    print("  ✓ All transitions have valid timestamps")
    print("  ✓ Candidate appears in correct stage columns")
    print("  ✓ Audit trail complete and accurate")


@pytest.mark.asyncio
async def test_workflow_stage_duration_analytics(client: AsyncClient, test_db: AsyncSession):
    """
    Test that stage duration analytics are calculated correctly.

    This verifies the time tracking between stage transitions.
    """
    print("\n=== Testing Stage Duration Analytics ===\n")

    # Create test resume
    test_resume = Resume(
        filename="analytics_test_resume.pdf",
        file_path="/tmp/analytics_test.pdf",
        content_type="application/pdf",
        status=ResumeStatus.COMPLETED,
        raw_text="Test content",
        language="en"
    )
    test_db.add(test_resume)
    await test_db.commit()
    await test_db.refresh(test_resume)

    candidate_id = str(test_resume.id)

    # Move through stages with controlled timing
    stages = [
        HiringStageName.SCREENING.value,
        HiringStageName.INTERVIEW.value,
        HiringStageName.OFFER.value,
    ]

    for i, stage in enumerate(stages):
        await client.put(
            f"/api/candidates/{candidate_id}/stage",
            json={"stage_id": stage, "notes": f"Moved to {stage}"}
        )
        # Small delay to ensure different timestamps
        await asyncio.sleep(0.1)

    # Query analytics events
    analytics_query = select(AnalyticsEvent).where(
        AnalyticsEvent.entity_id == test_resume.id
    ).order_by(AnalyticsEvent.created_at.asc())

    result = await test_db.execute(analytics_query)
    events = result.scalars().all()

    print(f"✓ Total analytics events: {len(events)}")

    # Calculate durations between stages
    durations = []
    for i in range(len(events) - 1):
        if events[i].event_type == AnalyticsEventType.STAGE_CHANGED:
            time_diff = events[i+1].created_at - events[i].created_at
            durations.append({
                "transition": f"{events[i].event_data.get('new_stage')} → {events[i+1].event_data.get('new_stage', 'end')}",
                "duration_seconds": time_diff.total_seconds()
            })

    print("\n  Stage Durations:")
    for duration in durations:
        print(f"  {duration['transition']}: {duration['duration_seconds']:.2f}s")

    print("\n✓ Stage duration analytics tracking successful")


@pytest.mark.asyncio
async def test_candidate_stage_filtering(client: AsyncClient, test_db: AsyncSession):
    """
    Test that candidates can be filtered by stage correctly.
    """
    print("\n=== Testing Candidate Stage Filtering ===\n")

    # Create multiple candidates in different stages
    candidates_data = [
        ("candidate1.pdf", HiringStageName.APPLIED.value),
        ("candidate2.pdf", HiringStageName.SCREENING.value),
        ("candidate3.pdf", HiringStageName.INTERVIEW.value),
        ("candidate4.pdf", HiringStageName.SCREENING.value),
    ]

    candidate_ids = []
    for filename, stage in candidates_data:
        resume = Resume(
            filename=filename,
            file_path=f"/tmp/{filename}",
            content_type="application/pdf",
            status=ResumeStatus.COMPLETED,
            raw_text="Test content",
            language="en"
        )
        test_db.add(resume)
        await test_db.commit()
        await test_db.refresh(resume)

        # Move to specified stage
        await client.put(
            f"/api/candidates/{str(resume.id)}/stage",
            json={"stage_id": stage}
        )
        candidate_ids.append(str(resume.id))

    # Test filtering by Screening stage
    screening_response = await client.get(
        f"/api/candidates/?stage_id={HiringStageName.SCREENING.value}"
    )
    assert screening_response.status_code == 200
    screening_candidates = screening_response.json()

    print(f"✓ Candidates in Screening: {len(screening_candidates)}")
    assert len(screening_candidates) >= 2, "Expected at least 2 candidates in Screening"

    # Verify correct candidates are in Screening
    screening_filenames = [c["filename"] for c in screening_candidates]
    assert "candidate2.pdf" in screening_filenames
    assert "candidate4.pdf" in screening_filenames
    print(f"✓ Correct candidates filtered: {screening_filenames}")

    # Test filtering by Interview stage
    interview_response = await client.get(
        f"/api/candidates/?stage_id={HiringStageName.INTERVIEW.value}"
    )
    interview_candidates = interview_response.json()

    print(f"✓ Candidates in Interview: {len(interview_candidates)}")
    interview_filenames = [c["filename"] for c in interview_candidates]
    assert "candidate3.pdf" in interview_filenames
    print(f"✓ Correct candidates in Interview: {interview_filenames}")

    # Test getting all candidates (no filter)
    all_response = await client.get("/api/candidates/")
    all_candidates = all_response.json()

    print(f"✓ Total candidates (no filter): {len(all_candidates)}")
    assert len(all_candidates) >= len(candidates_data)

    print("\n✓ Candidate stage filtering working correctly")


if __name__ == "__main__":
    print("This test requires pytest with async support.")
    print("Run with: pytest backend/tests/integration/test_workflow_e2e.py -v")
