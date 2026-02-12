"""
Integration tests for Hiring Manager API endpoints.

This test module verifies the hiring manager portal functionality including:
- GET /api/hiring-manager/dashboard - Dashboard statistics
- GET /api/hiring-manager/review-queue - Review queue with candidate filtering
- POST /api/hiring-manager/candidates/{id}/approve - One-click approve
- POST /api/hiring-manager/candidates/{id}/reject - One-click reject
- GET /api/hiring-manager/candidates/{id}/evaluation - Evaluation summary
- GET /api/hiring-manager/notifications - List notifications
- POST /api/hiring-manager/notifications/review-required - Create notification

Test Coverage:
- Dashboard stats retrieval with date filters
- Review queue filtering by vacancy, priority, stage, match score
- Candidate approval with optional rationale
- Candidate rejection with optional rationale and reason
- Evaluation summary retrieval
- Notification listing with type and manager filters
- Notification creation for review requests
- Error handling (400, 404, 500)
"""
import pytest
from uuid import uuid4, UUID
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database import get_db, Base
from models.notification import Notification, NotificationType
from models.recruiter import Recruiter
from dependencies.auth import get_current_user_optional


# ============================================================================
# Test Database Setup
# ============================================================================

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncSession:
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session


@pytest.fixture
async def client(test_session: AsyncSession):
    """Create a test HTTP client with database override."""
    from main import app

    async def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def sample_recruiter(test_session: AsyncSession) -> Recruiter:
    """Create a sample recruiter/manager for testing."""
    recruiter = Recruiter(
        name="Test Hiring Manager",
        email="manager@example.com",
        department="Engineering",
        is_active=True,
    )
    test_session.add(recruiter)
    await test_session.commit()
    await test_session.refresh(recruiter)
    return recruiter


@pytest.fixture
async def sample_notification(
    test_session: AsyncSession,
    sample_recruiter: Recruiter
) -> Notification:
    """Create a sample notification for testing."""
    notification = Notification(
        recipient_id=sample_recruiter.id,
        notification_type=NotificationType.CANDIDATE_REVIEW_REQUIRED,
        title="Test Notification",
        message="A candidate requires your review",
        is_read=False,
    )
    test_session.add(notification)
    await test_session.commit()
    await test_session.refresh(notification)
    return notification


# ============================================================================
# Test 1: Dashboard Stats
# ============================================================================

@pytest.mark.asyncio
async def test_get_dashboard_stats_success(client: AsyncClient):
    """Verify dashboard stats endpoint returns expected structure."""
    response = await client.get("/api/hiring-manager/dashboard")
    assert response.status_code == 200
    data = response.json()

    # Verify all top-level keys exist
    assert "pending_review" in data
    assert "my_vacancies" in data
    assert "recent_activity" in data
    assert "quick_stats" in data

    # Verify pending_review structure
    pending = data["pending_review"]
    assert "total_pending" in pending
    assert "urgent_count" in pending
    assert "new_this_week" in pending
    assert "average_wait_days" in pending

    # Verify my_vacancies is a list
    assert isinstance(data["my_vacancies"], list)

    # Verify recent_activity is a list
    assert isinstance(data["recent_activity"], list)

    # Verify quick_stats structure
    quick_stats = data["quick_stats"]
    assert "approved_this_month" in quick_stats
    assert "rejected_this_month" in quick_stats
    assert "interviews_scheduled" in quick_stats
    assert "avg_time_to_decision_days" in quick_stats


@pytest.mark.asyncio
async def test_get_dashboard_stats_with_date_filters(client: AsyncClient):
    """Verify dashboard stats endpoint accepts date filters."""
    response = await client.get(
        "/api/hiring-manager/dashboard",
        params={
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-31T23:59:59Z",
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "pending_review" in data


@pytest.mark.asyncio
async def test_dashboard_stats_vacancy_structure(client: AsyncClient):
    """Verify vacancy items in dashboard have required fields."""
    response = await client.get("/api/hiring-manager/dashboard")
    assert response.status_code == 200
    data = response.json()

    if len(data["my_vacancies"]) > 0:
        vacancy = data["my_vacancies"][0]
        assert "vacancy_id" in vacancy
        assert "vacancy_title" in vacancy
        assert "pending_review" in vacancy
        assert "total_candidates" in vacancy
        assert "stage" in vacancy


@pytest.mark.asyncio
async def test_dashboard_stats_recent_activity_structure(client: AsyncClient):
    """Verify recent activity items have required fields."""
    response = await client.get("/api/hiring-manager/dashboard")
    assert response.status_code == 200
    data = response.json()

    if len(data["recent_activity"]) > 0:
        activity = data["recent_activity"][0]
        assert "activity_type" in activity
        assert "candidate_name" in activity
        assert "vacancy_title" in activity
        assert "timestamp" in activity


# ============================================================================
# Test 2: Review Queue
# ============================================================================

@pytest.mark.asyncio
async def test_get_review_queue_success(client: AsyncClient):
    """Verify review queue endpoint returns expected structure."""
    response = await client.get("/api/hiring-manager/review-queue")
    assert response.status_code == 200
    data = response.json()

    # Verify top-level structure
    assert "total_candidates" in data
    assert "candidates" in data
    assert "filters_applied" in data
    assert "pagination" in data

    # Verify candidates is a list
    assert isinstance(data["candidates"], list)

    # Verify pagination structure
    pagination = data["pagination"]
    assert "skip" in pagination
    assert "limit" in pagination
    assert "total" in pagination


@pytest.mark.asyncio
async def test_review_queue_candidate_structure(client: AsyncClient):
    """Verify candidate items in review queue have required fields."""
    response = await client.get("/api/hiring-manager/review-queue")
    assert response.status_code == 200
    data = response.json()

    if len(data["candidates"]) > 0:
        candidate = data["candidates"][0]
        assert "id" in candidate
        assert "filename" in candidate
        assert "current_stage" in candidate
        assert "stage_name" in candidate
        assert "days_in_stage" in candidate
        assert "recruiter_feedback" in candidate
        assert "tags" in candidate
        assert "created_at" in candidate
        assert "updated_at" in candidate


@pytest.mark.asyncio
async def test_review_queue_filter_by_vacancy(client: AsyncClient):
    """Verify filtering review queue by vacancy ID."""
    vacancy_id = "550e8400-e29b-41d4-a716-446655440001"
    response = await client.get(
        "/api/hiring-manager/review-queue",
        params={"vacancy_id": vacancy_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filters_applied"]["vacancy_id"] == vacancy_id


@pytest.mark.asyncio
async def test_review_queue_filter_by_priority(client: AsyncClient):
    """Verify filtering review queue by priority."""
    response = await client.get(
        "/api/hiring-manager/review-queue",
        params={"priority": "urgent"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filters_applied"]["priority"] == "urgent"


@pytest.mark.asyncio
async def test_review_queue_invalid_priority(client: AsyncClient):
    """Verify invalid priority returns 400 error."""
    response = await client.get(
        "/api/hiring-manager/review-queue",
        params={"priority": "invalid_priority"}
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Invalid priority" in data["detail"]


@pytest.mark.asyncio
async def test_review_queue_filter_by_match_score(client: AsyncClient):
    """Verify filtering review queue by minimum match score."""
    response = await client.get(
        "/api/hiring-manager/review-queue",
        params={"min_match_score": 0.8}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filters_applied"]["min_match_score"] == 0.8

    # Verify all returned candidates meet the threshold
    for candidate in data["candidates"]:
        if candidate.get("match_score") is not None:
            assert candidate["match_score"] >= 0.8


@pytest.mark.asyncio
async def test_review_queue_filter_by_recruiter_feedback(client: AsyncClient):
    """Verify filtering review queue by recruiter feedback presence."""
    # Filter for candidates with recruiter feedback
    response = await client.get(
        "/api/hiring-manager/review-queue",
        params={"has_recruiter_feedback": True}
    )
    assert response.status_code == 200
    data = response.json()

    # Verify all returned candidates have feedback
    for candidate in data["candidates"]:
        assert len(candidate.get("recruiter_feedback", [])) > 0


@pytest.mark.asyncio
async def test_review_queue_search(client: AsyncClient):
    """Verify search filter works on candidate name and filename."""
    response = await client.get(
        "/api/hiring-manager/review-queue",
        params={"search": "john"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filters_applied"]["search"] == "john"


@pytest.mark.asyncio
async def test_review_queue_pagination(client: AsyncClient):
    """Verify pagination parameters work correctly."""
    response = await client.get(
        "/api/hiring-manager/review-queue",
        params={"skip": 2, "limit": 10}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["skip"] == 2
    assert data["pagination"]["limit"] == 10


# ============================================================================
# Test 3: Approve Candidate
# ============================================================================

@pytest.mark.asyncio
async def test_approve_candidate_success(client: AsyncClient):
    """Verify approving a candidate works correctly."""
    candidate_id = uuid4()
    response = await client.post(
        f"/api/hiring-manager/candidates/{candidate_id}/approve",
        json={}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["candidate_id"] == str(candidate_id)
    assert data["decision"] == "approved"
    assert "previous_stage" in data
    assert "new_stage" in data
    assert "decided_at" in data
    assert "message" in data


@pytest.mark.asyncio
async def test_approve_candidate_with_rationale(client: AsyncClient):
    """Verify approving a candidate with rationale."""
    candidate_id = uuid4()
    rationale = "Excellent technical skills and great culture fit"
    response = await client.post(
        f"/api/hiring-manager/candidates/{candidate_id}/approve",
        json={"rationale": rationale}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["rationale"] == rationale


@pytest.mark.asyncio
async def test_approve_candidate_with_custom_next_stage(client: AsyncClient):
    """Verify approving a candidate with custom next stage."""
    candidate_id = uuid4()
    response = await client.post(
        f"/api/hiring-manager/candidates/{candidate_id}/approve",
        json={"next_stage": "final_interview"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["new_stage"] == "final_interview"


@pytest.mark.asyncio
async def test_approve_candidate_invalid_id(client: AsyncClient):
    """Verify invalid candidate ID returns 400 error."""
    response = await client.post(
        "/api/hiring-manager/candidates/not-a-valid-uuid/approve",
        json={}
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Invalid candidate ID" in data["detail"]


# ============================================================================
# Test 4: Reject Candidate
# ============================================================================

@pytest.mark.asyncio
async def test_reject_candidate_success(client: AsyncClient):
    """Verify rejecting a candidate works correctly."""
    candidate_id = uuid4()
    response = await client.post(
        f"/api/hiring-manager/candidates/{candidate_id}/reject",
        json={}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["candidate_id"] == str(candidate_id)
    assert data["decision"] == "rejected"
    assert "previous_stage" in data
    assert data["new_stage"] == "rejected"
    assert "decided_at" in data
    assert "message" in data


@pytest.mark.asyncio
async def test_reject_candidate_with_rationale(client: AsyncClient):
    """Verify rejecting a candidate with rationale."""
    candidate_id = uuid4()
    rationale = "Insufficient experience for the role"
    response = await client.post(
        f"/api/hiring-manager/candidates/{candidate_id}/reject",
        json={"rationale": rationale}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["rationale"] == rationale


@pytest.mark.asyncio
async def test_reject_candidate_with_reason(client: AsyncClient):
    """Verify rejecting a candidate with rejection reason category."""
    candidate_id = uuid4()
    response = await client.post(
        f"/api/hiring-manager/candidates/{candidate_id}/reject",
        json={"rejection_reason": "skills_match"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "rejected"


@pytest.mark.asyncio
async def test_reject_candidate_invalid_id(client: AsyncClient):
    """Verify invalid candidate ID returns 400 error."""
    response = await client.post(
        "/api/hiring-manager/candidates/not-a-valid-uuid/reject",
        json={}
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Invalid candidate ID" in data["detail"]


@pytest.mark.asyncio
async def test_reject_candidate_invalid_reason(client: AsyncClient):
    """Verify invalid rejection reason returns 400 error."""
    candidate_id = uuid4()
    response = await client.post(
        f"/api/hiring-manager/candidates/{candidate_id}/reject",
        json={"rejection_reason": "invalid_reason"}
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Invalid rejection reason" in data["detail"]


@pytest.mark.asyncio
async def test_reject_candidate_valid_reasons(client: AsyncClient):
    """Verify all valid rejection reasons are accepted."""
    candidate_id = uuid4()
    valid_reasons = [
        "skills_match",
        "experience",
        "culture_fit",
        "salary_expectations",
        "location",
        "availability",
        "other",
    ]

    for reason in valid_reasons:
        response = await client.post(
            f"/api/hiring-manager/candidates/{candidate_id}/reject",
            json={"rejection_reason": reason}
        )
        assert response.status_code == 200, f"Failed for reason: {reason}"


# ============================================================================
# Test 5: Evaluation Summary
# ============================================================================

@pytest.mark.asyncio
async def test_get_evaluation_summary_success(client: AsyncClient):
    """Verify evaluation summary endpoint returns expected structure."""
    candidate_id = uuid4()
    response = await client.get(
        f"/api/hiring-manager/candidates/{candidate_id}/evaluation"
    )
    assert response.status_code == 200
    data = response.json()

    # Verify top-level structure
    assert data["candidate_id"] == str(candidate_id)
    assert "current_stage" in data
    assert "feedback_summary" in data
    assert "consensus_details" in data
    assert "tags" in data
    assert "evaluation_date" in data


@pytest.mark.asyncio
async def test_evaluation_summary_feedback_structure(client: AsyncClient):
    """Verify feedback summary structure in evaluation response."""
    candidate_id = uuid4()
    response = await client.get(
        f"/api/hiring-manager/candidates/{candidate_id}/evaluation"
    )
    assert response.status_code == 200
    data = response.json()

    feedback_summary = data["feedback_summary"]
    assert "total_feedback_count" in feedback_summary
    assert "average_rating" in feedback_summary
    assert "recommendations_breakdown" in feedback_summary
    assert "feedback_list" in feedback_summary


@pytest.mark.asyncio
async def test_evaluation_summary_consensus_structure(client: AsyncClient):
    """Verify consensus details structure in evaluation response."""
    candidate_id = uuid4()
    response = await client.get(
        f"/api/hiring-manager/candidates/{candidate_id}/evaluation"
    )
    assert response.status_code == 200
    data = response.json()

    consensus = data["consensus_details"]
    assert "consensus" in consensus
    assert "approval_rate" in consensus
    assert "rejection_rate" in consensus
    assert "total_reviewers" in consensus
    assert "unanimous" in consensus


@pytest.mark.asyncio
async def test_evaluation_summary_invalid_id(client: AsyncClient):
    """Verify invalid candidate ID returns 400 error."""
    response = await client.get(
        "/api/hiring-manager/candidates/not-a-valid-uuid/evaluation"
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Invalid candidate ID" in data["detail"]


@pytest.mark.asyncio
async def test_evaluation_summary_recruiter_feedback_structure(client: AsyncClient):
    """Verify recruiter feedback items have required fields."""
    candidate_id = uuid4()
    response = await client.get(
        f"/api/hiring-manager/candidates/{candidate_id}/evaluation"
    )
    assert response.status_code == 200
    data = response.json()

    feedback_list = data["feedback_summary"]["feedback_list"]
    if len(feedback_list) > 0:
        feedback = feedback_list[0]
        assert "recruiter_name" in feedback
        assert "created_at" in feedback


# ============================================================================
# Test 6: List Notifications
# ============================================================================

@pytest.mark.asyncio
async def test_list_notifications_success(client: AsyncClient):
    """Verify notifications list endpoint returns expected structure."""
    response = await client.get("/api/hiring-manager/notifications")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_notifications_with_type_filter(
    client: AsyncClient,
    test_session: AsyncSession,
    sample_recruiter: Recruiter
):
    """Verify filtering notifications by type."""
    response = await client.get(
        "/api/hiring-manager/notifications",
        params={"type": "candidate_review_required"}
    )
    assert response.status_code == 200
    data = response.json()

    # Verify all returned notifications have the correct type
    for notification in data:
        assert notification["notification_type"] == "candidate_review_required"


@pytest.mark.asyncio
async def test_list_notifications_with_manager_filter(
    client: AsyncClient,
    sample_recruiter: Recruiter
):
    """Verify filtering notifications by manager ID."""
    response = await client.get(
        "/api/hiring-manager/notifications",
        params={"manager_id": str(sample_recruiter.id)}
    )
    assert response.status_code == 200
    data = response.json()

    # Verify all returned notifications belong to the manager
    for notification in data:
        assert notification["recipient_id"] == str(sample_recruiter.id)


@pytest.mark.asyncio
async def test_list_notifications_invalid_manager_id(client: AsyncClient):
    """Verify invalid manager ID returns 400 error."""
    response = await client.get(
        "/api/hiring-manager/notifications",
        params={"manager_id": "not-a-valid-uuid"}
    )
    assert response.status_code == 400
    data = response.json()
    assert "Invalid manager_id" in data["detail"]


@pytest.mark.asyncio
async def test_list_notifications_nonexistent_manager(client: AsyncClient):
    """Verify non-existent manager returns 404 error."""
    fake_manager_id = uuid4()
    response = await client.get(
        "/api/hiring-manager/notifications",
        params={"manager_id": str(fake_manager_id)}
    )
    assert response.status_code == 404
    data = response.json()
    assert "Manager not found" in data["detail"]


@pytest.mark.asyncio
async def test_list_notifications_unread_only(
    client: AsyncClient,
    test_session: AsyncSession,
    sample_recruiter: Recruiter,
    sample_notification: Notification
):
    """Verify filtering for unread notifications only."""
    response = await client.get(
        "/api/hiring-manager/notifications",
        params={
            "manager_id": str(sample_recruiter.id),
            "unreadOnly": True
        }
    )
    assert response.status_code == 200
    data = response.json()

    # Verify all returned notifications are unread
    for notification in data:
        assert notification["is_read"] is False


@pytest.mark.asyncio
async def test_list_notifications_pagination(client: AsyncClient):
    """Verify pagination parameters work correctly."""
    response = await client.get(
        "/api/hiring-manager/notifications",
        params={"skip": 5, "limit": 20}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_notification_response_structure(
    client: AsyncClient,
    sample_recruiter: Recruiter
):
    """Verify notification items have required fields."""
    # First create a notification
    create_response = await client.post(
        "/api/hiring-manager/notifications/review-required",
        json={
            "manager_id": str(sample_recruiter.id),
            "candidate_id": str(uuid4()),
            "priority": "urgent",
        }
    )
    assert create_response.status_code == 201

    # Then list and verify structure
    response = await client.get(
        "/api/hiring-manager/notifications",
        params={"manager_id": str(sample_recruiter.id)}
    )
    assert response.status_code == 200
    data = response.json()

    if len(data) > 0:
        notification = data[0]
        assert "id" in notification
        assert "recipient_id" in notification
        assert "notification_type" in notification
        assert "title" in notification
        assert "message" in notification
        assert "is_read" in notification
        assert "created_at" in notification


# ============================================================================
# Test 7: Create Review Required Notification
# ============================================================================

@pytest.mark.asyncio
async def test_create_review_notification_success(
    client: AsyncClient,
    sample_recruiter: Recruiter
):
    """Verify creating a review required notification works correctly."""
    candidate_id = uuid4()
    response = await client.post(
        "/api/hiring-manager/notifications/review-required",
        json={
            "manager_id": str(sample_recruiter.id),
            "candidate_id": str(candidate_id),
        }
    )
    assert response.status_code == 201
    data = response.json()

    assert "id" in data
    assert data["recipient_id"] == str(sample_recruiter.id)
    assert data["notification_type"] == "candidate_review_required"
    assert data["is_read"] is False
    assert "title" in data
    assert "message" in data
    assert "created_at" in data
    assert data["result"] == "Notification created successfully"


@pytest.mark.asyncio
async def test_create_review_notification_with_vacancy(
    client: AsyncClient,
    sample_recruiter: Recruiter
):
    """Verify creating notification with vacancy ID."""
    candidate_id = uuid4()
    vacancy_id = uuid4()

    response = await client.post(
        "/api/hiring-manager/notifications/review-required",
        json={
            "manager_id": str(sample_recruiter.id),
            "candidate_id": str(candidate_id),
            "vacancy_id": str(vacancy_id),
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["vacancy_id"] == str(vacancy_id)


@pytest.mark.asyncio
async def test_create_review_notification_with_priority(
    client: AsyncClient,
    sample_recruiter: Recruiter
):
    """Verify creating notification with priority level."""
    candidate_id = uuid4()

    response = await client.post(
        "/api/hiring-manager/notifications/review-required",
        json={
            "manager_id": str(sample_recruiter.id),
            "candidate_id": str(candidate_id),
            "priority": "urgent",
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "URGENT" in data["title"]


@pytest.mark.asyncio
async def test_create_review_notification_with_custom_message(
    client: AsyncClient,
    sample_recruiter: Recruiter
):
    """Verify creating notification with custom message."""
    candidate_id = uuid4()
    custom_message = "High-priority candidate awaiting your immediate review"

    response = await client.post(
        "/api/hiring-manager/notifications/review-required",
        json={
            "manager_id": str(sample_recruiter.id),
            "candidate_id": str(candidate_id),
            "message": custom_message,
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == custom_message


@pytest.mark.asyncio
async def test_create_review_notification_invalid_manager_id(client: AsyncClient):
    """Verify invalid manager ID returns 400 error."""
    response = await client.post(
        "/api/hiring-manager/notifications/review-required",
        json={
            "manager_id": "not-a-valid-uuid",
            "candidate_id": str(uuid4()),
        }
    )
    assert response.status_code == 400
    data = response.json()
    assert "Invalid manager_id" in data["detail"]


@pytest.mark.asyncio
async def test_create_review_notification_invalid_candidate_id(
    client: AsyncClient,
    sample_recruiter: Recruiter
):
    """Verify invalid candidate ID returns 400 error."""
    response = await client.post(
        "/api/hiring-manager/notifications/review-required",
        json={
            "manager_id": str(sample_recruiter.id),
            "candidate_id": "not-a-valid-uuid",
        }
    )
    assert response.status_code == 400
    data = response.json()
    assert "Invalid candidate_id" in data["detail"]


@pytest.mark.asyncio
async def test_create_review_notification_nonexistent_manager(client: AsyncClient):
    """Verify non-existent manager returns 404 error."""
    fake_manager_id = uuid4()
    response = await client.post(
        "/api/hiring-manager/notifications/review-required",
        json={
            "manager_id": str(fake_manager_id),
            "candidate_id": str(uuid4()),
        }
    )
    assert response.status_code == 404
    data = response.json()
    assert "Manager not found" in data["detail"]


@pytest.mark.asyncio
async def test_create_review_notification_invalid_priority(
    client: AsyncClient,
    sample_recruiter: Recruiter
):
    """Verify invalid priority returns 400 error."""
    response = await client.post(
        "/api/hiring-manager/notifications/review-required",
        json={
            "manager_id": str(sample_recruiter.id),
            "candidate_id": str(uuid4()),
            "priority": "invalid_priority",
        }
    )
    assert response.status_code == 400
    data = response.json()
    assert "Invalid priority" in data["detail"]


# ============================================================================
# Run Tests Summary
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
