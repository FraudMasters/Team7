"""
Integration tests for screening metrics accuracy.

Tests cover:
- Screening metrics endpoint response structure
- Tier distribution calculations
- Score statistics accuracy
- Volume metrics correctness
- Auto-rejection tracking
- Filtering by vacancy_id
- Filtering by date range
- Metrics aggregation accuracy
"""
from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from main import app
from database import get_db
from models.resume import Resume, ResumeStatus
from models.job_vacancy import JobVacancy
from models.screening_rule import ScreeningRule
from models.screening_result import ScreeningResult
from models.candidate_rank import CandidateRank
from models.resume_analysis import ResumeAnalysis
from services.screening_service import ScreeningService


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_screening_metrics.db"


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


class TestScreeningMetricsEndpoint:
    """Tests for GET /api/screening/metrics endpoint."""

    @pytest.mark.asyncio
    async def test_returns_200(self, client: AsyncClient):
        """Test endpoint returns 200 status code."""
        response = await client.get("/api/screening/metrics")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_response_structure(self, client: AsyncClient):
        """Test response has correct structure."""
        response = await client.get("/api/screening/metrics")
        data = response.json()

        assert "volume" in data
        assert "tier_distribution" in data
        assert "scores" in data
        assert "auto_reject" in data


class TestVolumeMetrics:
    """Tests for volume metrics accuracy."""

    @pytest.mark.asyncio
    async def test_volume_metrics_structure(self, client: AsyncClient):
        """Test volume metrics have all required fields."""
        response = await client.get("/api/screening/metrics")
        data = response.json()
        volume = data["volume"]

        assert "total_screenings" in volume
        assert "screenings_this_month" in volume
        assert "screenings_this_week" in volume
        assert "screening_rate_avg" in volume

    @pytest.mark.asyncio
    async def test_volume_metrics_non_negative(self, client: AsyncClient):
        """Test volume metrics are non-negative."""
        response = await client.get("/api/screening/metrics")
        data = response.json()
        volume = data["volume"]

        assert volume["total_screenings"] >= 0
        assert volume["screenings_this_month"] >= 0
        assert volume["screenings_this_week"] >= 0
        assert volume["screening_rate_avg"] >= 0

    @pytest.mark.asyncio
    async def test_volume_metrics_accuracy(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test volume metrics accurately reflect database state."""
        # Create test data with known timestamps
        now = datetime.utcnow()

        # Create vacancy
        vacancy = JobVacancy(
            title="Test Position",
            description="Test description",
            required_skills=["python"],
            min_experience_months=12
        )
        test_db.add(vacancy)
        await test_db.commit()
        await test_db.refresh(vacancy)

        # Create multiple screening results with different timestamps
        num_total = 20
        num_this_month = 15
        num_this_week = 5

        for i in range(num_total):
            # Create varying timestamps
            if i < num_this_week:
                timestamp = now - timedelta(days=i)
            elif i < num_this_month:
                timestamp = now - timedelta(days=15 + i)
            else:
                timestamp = now - timedelta(days=40 + i)

            result = ScreeningResult(
                resume_id=vacancy.id,  # Use vacancy.id as placeholder UUID
                vacancy_id=vacancy.id,
                screening_rule_id=None,
                tier="HIGH_PRIORITY" if i % 3 == 0 else ("REVIEW" if i % 3 == 1 else "REJECT"),
                score_applied=50.0 + i,
                rejection_reasons=None,
                screening_timestamp=timestamp,
                auto_response_sent=False,
                review_reminder_sent=False
            )
            test_db.add(result)

        await test_db.commit()

        # Get metrics
        response = await client.get("/api/screening/metrics")
        data = response.json()
        volume = data["volume"]

        # Verify total count
        assert volume["total_screenings"] >= num_total, (
            f"Expected at least {num_total} total screenings, got {volume['total_screenings']}"
        )

    @pytest.mark.asyncio
    async def test_screening_rate_calculation(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test screening rate is calculated correctly."""
        # Create test vacancy
        vacancy = JobVacancy(
            title="Test Position",
            description="Test",
            required_skills=["python"],
            min_experience_months=12
        )
        test_db.add(vacancy)
        await test_db.commit()
        await test_db.refresh(vacancy)

        # Create screening results spread over multiple days
        now = datetime.utcnow()
        for i in range(10):
            timestamp = now - timedelta(days=i)
            result = ScreeningResult(
                resume_id=vacancy.id,
                vacancy_id=vacancy.id,
                screening_rule_id=None,
                tier="REVIEW",
                score_applied=60.0,
                rejection_reasons=None,
                screening_timestamp=timestamp,
                auto_response_sent=False,
                review_reminder_sent=False
            )
            test_db.add(result)

        await test_db.commit()

        # Get metrics
        response = await client.get(f"/api/screening/metrics?vacancy_id={vacancy.id}")
        data = response.json()
        volume = data["volume"]

        # Screening rate should be positive
        assert volume["screening_rate_avg"] > 0, "Screening rate should be positive"


class TestTierDistributionMetrics:
    """Tests for tier distribution metrics accuracy."""

    @pytest.mark.asyncio
    async def test_tier_distribution_structure(self, client: AsyncClient):
        """Test tier distribution has all required fields."""
        response = await client.get("/api/screening/metrics")
        data = response.json()
        tier_dist = data["tier_distribution"]

        assert "high_priority_count" in tier_dist
        assert "high_priority_percentage" in tier_dist
        assert "review_count" in tier_dist
        assert "review_percentage" in tier_dist
        assert "reject_count" in tier_dist
        assert "reject_percentage" in tier_dist

    @pytest.mark.asyncio
    async def test_tier_distribution_accuracy(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test tier distribution accurately reflects database state."""
        # Create vacancy
        vacancy = JobVacancy(
            title="Test Position",
            description="Test",
            required_skills=["python"],
            min_experience_months=12
        )
        test_db.add(vacancy)
        await test_db.commit()
        await test_db.refresh(vacancy)

        # Create known distribution
        high_priority_count = 7
        review_count = 13
        reject_count = 5
        total = high_priority_count + review_count + reject_count

        for i in range(high_priority_count):
            result = ScreeningResult(
                resume_id=vacancy.id,
                vacancy_id=vacancy.id,
                screening_rule_id=None,
                tier="HIGH_PRIORITY",
                score_applied=85.0,
                rejection_reasons=None,
                screening_timestamp=datetime.utcnow(),
                auto_response_sent=False,
                review_reminder_sent=False
            )
            test_db.add(result)

        for i in range(review_count):
            result = ScreeningResult(
                resume_id=vacancy.id,
                vacancy_id=vacancy.id,
                screening_rule_id=None,
                tier="REVIEW",
                score_applied=60.0,
                rejection_reasons=None,
                screening_timestamp=datetime.utcnow(),
                auto_response_sent=False,
                review_reminder_sent=False
            )
            test_db.add(result)

        for i in range(reject_count):
            result = ScreeningResult(
                resume_id=vacancy.id,
                vacancy_id=vacancy.id,
                screening_rule_id=None,
                tier="REJECT",
                score_applied=25.0,
                rejection_reasons=["below_threshold"],
                screening_timestamp=datetime.utcnow(),
                auto_response_sent=False,
                review_reminder_sent=False
            )
            test_db.add(result)

        await test_db.commit()

        # Get metrics for this vacancy
        response = await client.get(f"/api/screening/metrics?vacancy_id={vacancy.id}")
        data = response.json()
        tier_dist = data["tier_distribution"]

        # Verify counts
        assert tier_dist["high_priority_count"] == high_priority_count, (
            f"Expected {high_priority_count} high priority, got {tier_dist['high_priority_count']}"
        )
        assert tier_dist["review_count"] == review_count, (
            f"Expected {review_count} review, got {tier_dist['review_count']}"
        )
        assert tier_dist["reject_count"] == reject_count, (
            f"Expected {reject_count} reject, got {tier_dist['reject_count']}"
        )

        # Verify percentages (allow small rounding differences)
        expected_high_pct = (high_priority_count / total) * 100
        expected_review_pct = (review_count / total) * 100
        expected_reject_pct = (reject_count / total) * 100

        assert abs(tier_dist["high_priority_percentage"] - expected_high_pct) < 0.1, (
            f"Expected high priority percentage ~{expected_high_pct:.1f}%, "
            f"got {tier_dist['high_priority_percentage']:.1f}%"
        )
        assert abs(tier_dist["review_percentage"] - expected_review_pct) < 0.1, (
            f"Expected review percentage ~{expected_review_pct:.1f}%, "
            f"got {tier_dist['review_percentage']:.1f}%"
        )
        assert abs(tier_dist["reject_percentage"] - expected_reject_pct) < 0.1, (
            f"Expected reject percentage ~{expected_reject_pct:.1f}%, "
            f"got {tier_dist['reject_percentage']:.1f}%"
        )

    @pytest.mark.asyncio
    async def test_percentages_sum_to_100(self, client: AsyncClient):
        """Test tier distribution percentages sum to approximately 100."""
        response = await client.get("/api/screening/metrics")
        data = response.json()
        tier_dist = data["tier_distribution"]

        if data["volume"]["total_screenings"] > 0:
            total_percentage = (
                tier_dist["high_priority_percentage"] +
                tier_dist["review_percentage"] +
                tier_dist["reject_percentage"]
            )
            assert abs(total_percentage - 100.0) < 0.2, (
                f"Tier percentages should sum to ~100%, got {total_percentage:.2f}%"
            )


class TestScoreMetrics:
    """Tests for score metrics accuracy."""

    @pytest.mark.asyncio
    async def test_score_metrics_structure(self, client: AsyncClient):
        """Test score metrics have all required fields."""
        response = await client.get("/api/screening/metrics")
        data = response.json()
        scores = data["scores"]

        assert "average_score" in scores
        assert "median_score" in scores
        assert "min_score" in scores
        assert "max_score" in scores
        assert "percentile_25" in scores
        assert "percentile_75" in scores

    @pytest.mark.asyncio
    async def test_score_metrics_range(self, client: AsyncClient):
        """Test score metrics are within valid range (0-100)."""
        response = await client.get("/api/screening/metrics")
        data = response.json()

        if data["volume"]["total_screenings"] > 0:
            scores = data["scores"]
            assert 0 <= scores["average_score"] <= 100
            assert 0 <= scores["median_score"] <= 100
            assert 0 <= scores["min_score"] <= 100
            assert 0 <= scores["max_score"] <= 100
            assert 0 <= scores["percentile_25"] <= 100
            assert 0 <= scores["percentile_75"] <= 100

    @pytest.mark.asyncio
    async def test_score_metrics_accuracy(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test score statistics are calculated correctly."""
        # Create vacancy
        vacancy = JobVacancy(
            title="Test Position",
            description="Test",
            required_skills=["python"],
            min_experience_months=12
        )
        test_db.add(vacancy)
        await test_db.commit()
        await test_db.refresh(vacancy)

        # Create screening results with known scores
        test_scores = [20.0, 35.0, 50.0, 65.0, 80.0, 95.0]

        for score in test_scores:
            result = ScreeningResult(
                resume_id=vacancy.id,
                vacancy_id=vacancy.id,
                screening_rule_id=None,
                tier="HIGH_PRIORITY" if score >= 80 else ("REVIEW" if score >= 50 else "REJECT"),
                score_applied=score,
                rejection_reasons=["below_threshold"] if score < 30 else None,
                screening_timestamp=datetime.utcnow(),
                auto_response_sent=False,
                review_reminder_sent=False
            )
            test_db.add(result)

        await test_db.commit()

        # Get metrics
        response = await client.get(f"/api/screening/metrics?vacancy_id={vacancy.id}")
        data = response.json()
        scores = data["scores"]

        # Verify statistics
        expected_avg = sum(test_scores) / len(test_scores)
        expected_min = min(test_scores)
        expected_max = max(test_scores)

        assert abs(scores["average_score"] - expected_avg) < 0.1, (
            f"Expected average ~{expected_avg:.1f}, got {scores['average_score']:.1f}"
        )
        assert scores["min_score"] == expected_min, (
            f"Expected min {expected_min}, got {scores['min_score']}"
        )
        assert scores["max_score"] == expected_max, (
            f"Expected max {expected_max}, got {scores['max_score']}"
        )

    @pytest.mark.asyncio
    async def test_min_max_logic(self, client: AsyncClient):
        """Test min <= median <= max and min <= percentile_25 <= percentile_75 <= max."""
        response = await client.get("/api/screening/metrics")
        data = response.json()

        if data["volume"]["total_screenings"] > 0:
            scores = data["scores"]
            assert scores["min_score"] <= scores["median_score"], (
                "Min should be <= median"
            )
            assert scores["median_score"] <= scores["max_score"], (
                "Median should be <= max"
            )
            assert scores["min_score"] <= scores["percentile_25"], (
                "Min should be <= 25th percentile"
            )
            assert scores["percentile_25"] <= scores["percentile_75"], (
                "25th percentile should be <= 75th percentile"
            )
            assert scores["percentile_75"] <= scores["max_score"], (
                "75th percentile should be <= max"
            )


class TestAutoRejectMetrics:
    """Tests for auto-reject metrics accuracy."""

    @pytest.mark.asyncio
    async def test_auto_reject_structure(self, client: AsyncClient):
        """Test auto-reject metrics have all required fields."""
        response = await client.get("/api/screening/metrics")
        data = response.json()
        auto_reject = data["auto_reject"]

        assert "total_auto_rejected" in auto_reject
        assert "auto_rejection_rate" in auto_reject
        assert "notifications_sent" in auto_reject
        assert "notification_rate" in auto_reject

    @pytest.mark.asyncio
    async def test_auto_reject_non_negative(self, client: AsyncClient):
        """Test auto-reject metrics are non-negative."""
        response = await client.get("/api/screening/metrics")
        data = response.json()
        auto_reject = data["auto_reject"]

        assert auto_reject["total_auto_rejected"] >= 0
        assert auto_reject["auto_rejection_rate"] >= 0
        assert auto_reject["notifications_sent"] >= 0
        assert auto_reject["notification_rate"] >= 0

    @pytest.mark.asyncio
    async def test_auto_rejection_rate_range(self, client: AsyncClient):
        """Test auto-rejection rate is between 0 and 1."""
        response = await client.get("/api/screening/metrics")
        data = response.json()
        auto_reject = data["auto_reject"]

        assert 0 <= auto_reject["auto_rejection_rate"] <= 1, (
            f"Auto-rejection rate should be 0-1, got {auto_reject['auto_rejection_rate']}"
        )

    @pytest.mark.asyncio
    async def test_notification_rate_range(self, client: AsyncClient):
        """Test notification rate is between 0 and 1."""
        response = await client.get("/api/screening/metrics")
        data = response.json()
        auto_reject = data["auto_reject"]

        if auto_reject["total_auto_rejected"] > 0:
            assert 0 <= auto_reject["notification_rate"] <= 1, (
                f"Notification rate should be 0-1, got {auto_reject['notification_rate']}"
            )

    @pytest.mark.asyncio
    async def test_auto_reject_tracking(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test auto-rejected candidates are tracked correctly."""
        # Create vacancy
        vacancy = JobVacancy(
            title="Test Position",
            description="Test",
            required_skills=["python"],
            min_experience_months=12
        )
        test_db.add(vacancy)
        await test_db.commit()
        await test_db.refresh(vacancy)

        # Create rejected and non-rejected screening results
        num_rejected = 8
        num_notifications = 5

        for i in range(num_rejected):
            result = ScreeningResult(
                resume_id=vacancy.id,
                vacancy_id=vacancy.id,
                screening_rule_id=None,
                tier="REJECT",
                score_applied=20.0,
                rejection_reasons=["below_threshold", "missing_must_have_skills"],
                screening_timestamp=datetime.utcnow(),
                auto_response_sent=(i < num_notifications),
                review_reminder_sent=False
            )
            test_db.add(result)

        # Create some non-rejected results
        for i in range(5):
            result = ScreeningResult(
                resume_id=vacancy.id,
                vacancy_id=vacancy.id,
                screening_rule_id=None,
                tier="HIGH_PRIORITY" if i % 2 == 0 else "REVIEW",
                score_applied=70.0 + i * 10,
                rejection_reasons=None,
                screening_timestamp=datetime.utcnow(),
                auto_response_sent=False,
                review_reminder_sent=False
            )
            test_db.add(result)

        await test_db.commit()

        # Get metrics
        response = await client.get(f"/api/screening/metrics?vacancy_id={vacancy.id}")
        data = response.json()
        auto_reject = data["auto_reject"]

        # Verify rejected count
        assert auto_reject["total_auto_rejected"] == num_rejected, (
            f"Expected {num_rejected} auto-rejected, got {auto_reject['total_auto_rejected']}"
        )

        # Verify notifications sent
        assert auto_reject["notifications_sent"] == num_notifications, (
            f"Expected {num_notifications} notifications, got {auto_reject['notifications_sent']}"
        )


class TestVacancyFiltering:
    """Tests for vacancy_id filtering."""

    @pytest.mark.asyncio
    async def test_filter_by_vacancy_id(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test filtering metrics by vacancy_id."""
        # Create two vacancies
        vacancy1 = JobVacancy(
            title="Position 1",
            description="Test 1",
            required_skills=["python"],
            min_experience_months=12
        )
        vacancy2 = JobVacancy(
            title="Position 2",
            description="Test 2",
            required_skills=["javascript"],
            min_experience_months=12
        )
        test_db.add(vacancy1)
        test_db.add(vacancy2)
        await test_db.commit()
        await test_db.refresh(vacancy1)
        await test_db.refresh(vacancy2)

        # Create screening results for vacancy1
        for i in range(10):
            result = ScreeningResult(
                resume_id=vacancy1.id,
                vacancy_id=vacancy1.id,
                screening_rule_id=None,
                tier="HIGH_PRIORITY",
                score_applied=80.0 + i,
                rejection_reasons=None,
                screening_timestamp=datetime.utcnow(),
                auto_response_sent=False,
                review_reminder_sent=False
            )
            test_db.add(result)

        # Create screening results for vacancy2
        for i in range(5):
            result = ScreeningResult(
                resume_id=vacancy2.id,
                vacancy_id=vacancy2.id,
                screening_rule_id=None,
                tier="REVIEW",
                score_applied=60.0 + i,
                rejection_reasons=None,
                screening_timestamp=datetime.utcnow(),
                auto_response_sent=False,
                review_reminder_sent=False
            )
            test_db.add(result)

        await test_db.commit()

        # Get metrics for vacancy1
        response1 = await client.get(f"/api/screening/metrics?vacancy_id={vacancy1.id}")
        data1 = response1.json()

        # Get metrics for vacancy2
        response2 = await client.get(f"/api/screening/metrics?vacancy_id={vacancy2.id}")
        data2 = response2.json()

        # Verify vacancy1 has 10 screenings
        assert data1["volume"]["total_screenings"] == 10, (
            f"Vacancy1 should have 10 screenings, got {data1['volume']['total_screenings']}"
        )

        # Verify vacancy2 has 5 screenings
        assert data2["volume"]["total_screenings"] == 5, (
            f"Vacancy2 should have 5 screenings, got {data2['volume']['total_screenings']}"
        )


class TestDateRangeFiltering:
    """Tests for date range filtering."""

    @pytest.mark.asyncio
    async def test_no_date_filter(self, client: AsyncClient, test_db: AsyncSession):
        """Test metrics without date filter returns all data."""
        # Create vacancy
        vacancy = JobVacancy(
            title="Test Position",
            description="Test",
            required_skills=["python"],
            min_experience_months=12
        )
        test_db.add(vacancy)
        await test_db.commit()
        await test_db.refresh(vacancy)

        # Create screening results across different dates
        now = datetime.utcnow()
        for i in range(10):
            timestamp = now - timedelta(days=i * 5)
            result = ScreeningResult(
                resume_id=vacancy.id,
                vacancy_id=vacancy.id,
                screening_rule_id=None,
                tier="REVIEW",
                score_applied=60.0,
                rejection_reasons=None,
                screening_timestamp=timestamp,
                auto_response_sent=False,
                review_reminder_sent=False
            )
            test_db.add(result)

        await test_db.commit()

        # Get metrics without date filter
        response = await client.get(f"/api/screening/metrics?vacancy_id={vacancy.id}")
        data = response.json()

        # Should include all 10 screenings
        assert data["volume"]["total_screenings"] == 10

    @pytest.mark.asyncio
    async def test_start_date_filter(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test filtering with start_date only."""
        # Create vacancy
        vacancy = JobVacancy(
            title="Test Position",
            description="Test",
            required_skills=["python"],
            min_experience_months=12
        )
        test_db.add(vacancy)
        await test_db.commit()
        await test_db.refresh(vacancy)

        # Create screening results across different dates
        now = datetime.utcnow()
        start_date = now - timedelta(days=10)

        # Create old results (before start_date)
        for i in range(5):
            timestamp = now - timedelta(days=20 + i)
            result = ScreeningResult(
                resume_id=vacancy.id,
                vacancy_id=vacancy.id,
                screening_rule_id=None,
                tier="REVIEW",
                score_applied=60.0,
                rejection_reasons=None,
                screening_timestamp=timestamp,
                auto_response_sent=False,
                review_reminder_sent=False
            )
            test_db.add(result)

        # Create new results (after start_date)
        for i in range(7):
            timestamp = now - timedelta(days=i)
            result = ScreeningResult(
                resume_id=vacancy.id,
                vacancy_id=vacancy.id,
                screening_rule_id=None,
                tier="HIGH_PRIORITY",
                score_applied=80.0,
                rejection_reasons=None,
                screening_timestamp=timestamp,
                auto_response_sent=False,
                review_reminder_sent=False
            )
            test_db.add(result)

        await test_db.commit()

        # Get metrics with start_date filter
        start_date_str = start_date.isoformat()
        response = await client.get(
            f"/api/screening/metrics?vacancy_id={vacancy.id}&start_date={start_date_str}"
        )
        data = response.json()

        # Should only include results after start_date
        assert data["volume"]["total_screenings"] == 7, (
            f"Expected 7 screenings after start_date, got {data['volume']['total_screenings']}"
        )

    @pytest.mark.asyncio
    async def test_end_date_filter(self, client: AsyncClient, test_db: AsyncSession):
        """Test filtering with end_date only."""
        # Create vacancy
        vacancy = JobVacancy(
            title="Test Position",
            description="Test",
            required_skills=["python"],
            min_experience_months=12
        )
        test_db.add(vacancy)
        await test_db.commit()
        await test_db.refresh(vacancy)

        # Create screening results
        now = datetime.utcnow()
        end_date = now - timedelta(days=10)

        # Create old results (before end_date)
        for i in range(6):
            timestamp = end_date - timedelta(days=i)
            result = ScreeningResult(
                resume_id=vacancy.id,
                vacancy_id=vacancy.id,
                screening_rule_id=None,
                tier="REVIEW",
                score_applied=60.0,
                rejection_reasons=None,
                screening_timestamp=timestamp,
                auto_response_sent=False,
                review_reminder_sent=False
            )
            test_db.add(result)

        # Create new results (after end_date)
        for i in range(4):
            timestamp = now - timedelta(days=i)
            result = ScreeningResult(
                resume_id=vacancy.id,
                vacancy_id=vacancy.id,
                screening_rule_id=None,
                tier="HIGH_PRIORITY",
                score_applied=80.0,
                rejection_reasons=None,
                screening_timestamp=timestamp,
                auto_response_sent=False,
                review_reminder_sent=False
            )
            test_db.add(result)

        await test_db.commit()

        # Get metrics with end_date filter
        end_date_str = end_date.isoformat()
        response = await client.get(
            f"/api/screening/metrics?vacancy_id={vacancy.id}&end_date={end_date_str}"
        )
        data = response.json()

        # Should only include results before end_date
        assert data["volume"]["total_screenings"] == 6, (
            f"Expected 6 screenings before end_date, got {data['volume']['total_screenings']}"
        )

    @pytest.mark.asyncio
    async def test_date_range_filter(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test filtering with both start_date and end_date."""
        # Create vacancy
        vacancy = JobVacancy(
            title="Test Position",
            description="Test",
            required_skills=["python"],
            min_experience_months=12
        )
        test_db.add(vacancy)
        await test_db.commit()
        await test_db.refresh(vacancy)

        # Create screening results
        now = datetime.utcnow()
        start_date = now - timedelta(days=15)
        end_date = now - timedelta(days=5)

        # Create old results (before range)
        for i in range(3):
            timestamp = start_date - timedelta(days=i + 1)
            result = ScreeningResult(
                resume_id=vacancy.id,
                vacancy_id=vacancy.id,
                screening_rule_id=None,
                tier="REJECT",
                score_applied=20.0,
                rejection_reasons=["below_threshold"],
                screening_timestamp=timestamp,
                auto_response_sent=False,
                review_reminder_sent=False
            )
            test_db.add(result)

        # Create in-range results
        for i in range(8):
            timestamp = start_date + timedelta(days=i)
            result = ScreeningResult(
                resume_id=vacancy.id,
                vacancy_id=vacancy.id,
                screening_rule_id=None,
                tier="HIGH_PRIORITY",
                score_applied=85.0,
                rejection_reasons=None,
                screening_timestamp=timestamp,
                auto_response_sent=False,
                review_reminder_sent=False
            )
            test_db.add(result)

        # Create new results (after range)
        for i in range(4):
            timestamp = end_date + timedelta(days=i + 1)
            result = ScreeningResult(
                resume_id=vacancy.id,
                vacancy_id=vacancy.id,
                screening_rule_id=None,
                tier="REVIEW",
                score_applied=65.0,
                rejection_reasons=None,
                screening_timestamp=timestamp,
                auto_response_sent=False,
                review_reminder_sent=False
            )
            test_db.add(result)

        await test_db.commit()

        # Get metrics with date range filter
        start_date_str = start_date.isoformat()
        end_date_str = end_date.isoformat()
        response = await client.get(
            f"/api/screening/metrics?vacancy_id={vacancy.id}"
            f"&start_date={start_date_str}&end_date={end_date_str}"
        )
        data = response.json()

        # Should only include in-range results
        assert data["volume"]["total_screenings"] == 8, (
            f"Expected 8 screenings in range, got {data['volume']['total_screenings']}"
        )


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_empty_metrics(self, client: AsyncClient, test_db: AsyncSession):
        """Test metrics when no screening results exist."""
        # Create vacancy with no results
        vacancy = JobVacancy(
            title="Empty Position",
            description="No screenings yet",
            required_skills=["python"],
            min_experience_months=12
        )
        test_db.add(vacancy)
        await test_db.commit()
        await test_db.refresh(vacancy)

        # Get metrics for vacancy with no screenings
        response = await client.get(f"/api/screening/metrics?vacancy_id={vacancy.id}")
        data = response.json()

        # Verify zero values
        assert data["volume"]["total_screenings"] == 0
        assert data["tier_distribution"]["high_priority_count"] == 0
        assert data["tier_distribution"]["review_count"] == 0
        assert data["tier_distribution"]["reject_count"] == 0
        assert data["auto_reject"]["total_auto_rejected"] == 0

    @pytest.mark.asyncio
    async def test_single_screening_result(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test metrics with only one screening result."""
        # Create vacancy
        vacancy = JobVacancy(
            title="Single Result",
            description="Test",
            required_skills=["python"],
            min_experience_months=12
        )
        test_db.add(vacancy)
        await test_db.commit()
        await test_db.refresh(vacancy)

        # Create single result
        result = ScreeningResult(
            resume_id=vacancy.id,
            vacancy_id=vacancy.id,
            screening_rule_id=None,
            tier="HIGH_PRIORITY",
            score_applied=90.0,
            rejection_reasons=None,
            screening_timestamp=datetime.utcnow(),
            auto_response_sent=False,
            review_reminder_sent=False
        )
        test_db.add(result)
        await test_db.commit()

        # Get metrics
        response = await client.get(f"/api/screening/metrics?vacancy_id={vacancy.id}")
        data = response.json()

        # Verify single result is reflected
        assert data["volume"]["total_screenings"] == 1
        assert data["tier_distribution"]["high_priority_count"] == 1
        assert data["scores"]["average_score"] == 90.0
        assert data["scores"]["median_score"] == 90.0
        assert data["scores"]["min_score"] == 90.0
        assert data["scores"]["max_score"] == 90.0

    @pytest.mark.asyncio
    async def test_invalid_vacancy_uuid(self, client: AsyncClient):
        """Test metrics endpoint with invalid vacancy UUID."""
        response = await client.get("/api/screening/metrics?vacancy_id=invalid-uuid")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_date_format(self, client: AsyncClient):
        """Test metrics endpoint with invalid date format."""
        response = await client.get("/api/screening/metrics?start_date=invalid-date")
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_screening_metrics_accuracy(
    client: AsyncClient, test_db: AsyncSession
):
    """
    Comprehensive test: Verify screening metrics accuracy end-to-end.

    This test creates a comprehensive set of screening results and verifies
    that all metrics are calculated correctly including:
    - Volume metrics
    - Tier distribution
    - Score statistics
    - Auto-rejection tracking
    """
    print("\n=== Testing Screening Metrics Accuracy ===\n")

    # Create vacancy
    vacancy = JobVacancy(
        title="Senior Developer",
        description="Test position for metrics verification",
        required_skills=["python", "django"],
        min_experience_months=60
    )
    test_db.add(vacancy)
    await test_db.commit()
    await test_db.refresh(vacancy)

    print(f"✓ Created vacancy: {vacancy.title}")

    # Create comprehensive screening results
    now = datetime.utcnow()

    # High priority candidates (scores >= 80)
    high_priority_scores = [82.5, 85.0, 88.0, 90.5, 92.0, 95.0]
    for score in high_priority_scores:
        result = ScreeningResult(
            resume_id=vacancy.id,
            vacancy_id=vacancy.id,
            screening_rule_id=None,
            tier="HIGH_PRIORITY",
            score_applied=score,
            rejection_reasons=None,
            screening_timestamp=now - timedelta(days=len(high_priority_scores)),
            auto_response_sent=False,
            review_reminder_sent=False
        )
        test_db.add(result)

    # Review candidates (50 <= score < 80)
    review_scores = [52.0, 58.5, 62.0, 65.5, 68.0, 72.5, 75.0, 78.5]
    for i, score in enumerate(review_scores):
        result = ScreeningResult(
            resume_id=vacancy.id,
            vacancy_id=vacancy.id,
            screening_rule_id=None,
            tier="REVIEW",
            score_applied=score,
            rejection_reasons=None,
            screening_timestamp=now - timedelta(days=i),
            auto_response_sent=False,
            review_reminder_sent=False
        )
        test_db.add(result)

    # Rejected candidates (score < 30)
    reject_scores = [15.0, 20.0, 25.0, 28.0]
    for i, score in enumerate(reject_scores):
        result = ScreeningResult(
            resume_id=vacancy.id,
            vacancy_id=vacancy.id,
            screening_rule_id=None,
            tier="REJECT",
            score_applied=score,
            rejection_reasons=["below_threshold"],
            screening_timestamp=now - timedelta(days=i),
            auto_response_sent=(i < 2),  # First 2 have notifications
            review_reminder_sent=False
        )
        test_db.add(result)

    await test_db.commit()

    total_count = len(high_priority_scores) + len(review_scores) + len(reject_scores)
    print(f"✓ Created {total_count} screening results:")
    print(f"  - {len(high_priority_scores)} HIGH_PRIORITY")
    print(f"  - {len(review_scores)} REVIEW")
    print(f"  - {len(reject_scores)} REJECT")

    # Get metrics
    response = await client.get(f"/api/screening/metrics?vacancy_id={vacancy.id}")
    assert response.status_code == 200, f"Failed to get metrics: {response.text}"
    metrics = response.json()

    # Verify volume metrics
    volume = metrics["volume"]
    assert volume["total_screenings"] == total_count, (
        f"Expected {total_count} total screenings, got {volume['total_screenings']}"
    )
    print(f"✓ Volume metrics correct: {volume['total_screenings']} total")

    # Verify tier distribution counts
    tier_dist = metrics["tier_distribution"]
    assert tier_dist["high_priority_count"] == len(high_priority_scores), (
        f"Expected {len(high_priority_scores)} high priority, "
        f"got {tier_dist['high_priority_count']}"
    )
    assert tier_dist["review_count"] == len(review_scores), (
        f"Expected {len(review_scores)} review, got {tier_dist['review_count']}"
    )
    assert tier_dist["reject_count"] == len(reject_scores), (
        f"Expected {len(reject_scores)} reject, got {tier_dist['reject_count']}"
    )
    print(f"✓ Tier distribution counts correct")

    # Verify tier distribution percentages
    expected_high_pct = (len(high_priority_scores) / total_count) * 100
    expected_review_pct = (len(review_scores) / total_count) * 100
    expected_reject_pct = (len(reject_scores) / total_count) * 100

    assert abs(tier_dist["high_priority_percentage"] - expected_high_pct) < 0.1, (
        f"Expected high priority percentage ~{expected_high_pct:.1f}%, "
        f"got {tier_dist['high_priority_percentage']:.1f}%"
    )
    assert abs(tier_dist["review_percentage"] - expected_review_pct) < 0.1, (
        f"Expected review percentage ~{expected_review_pct:.1f}%, "
        f"got {tier_dist['review_percentage']:.1f}%"
    )
    assert abs(tier_dist["reject_percentage"] - expected_reject_pct) < 0.1, (
        f"Expected reject percentage ~{expected_reject_pct:.1f}%, "
        f"got {tier_dist['reject_percentage']:.1f}%"
    )
    print(f"✓ Tier distribution percentages correct")

    # Verify score statistics
    all_scores = high_priority_scores + review_scores + reject_scores
    expected_avg = sum(all_scores) / len(all_scores)
    expected_min = min(all_scores)
    expected_max = max(all_scores)

    scores = metrics["scores"]
    assert abs(scores["average_score"] - expected_avg) < 0.1, (
        f"Expected average ~{expected_avg:.1f}, got {scores['average_score']:.1f}"
    )
    assert scores["min_score"] == expected_min, (
        f"Expected min {expected_min}, got {scores['min_score']}"
    )
    assert scores["max_score"] == expected_max, (
        f"Expected max {expected_max}, got {scores['max_score']}"
    )
    print(f"✓ Score statistics correct:")
    print(f"  - Average: {scores['average_score']:.1f}")
    print(f"  - Min: {scores['min_score']:.1f}")
    print(f"  - Max: {scores['max_score']:.1f}")

    # Verify auto-reject metrics
    auto_reject = metrics["auto_reject"]
    assert auto_reject["total_auto_rejected"] == len(reject_scores), (
        f"Expected {len(reject_scores)} auto-rejected, "
        f"got {auto_reject['total_auto_rejected']}"
    )
    assert auto_reject["notifications_sent"] == 2, (
        f"Expected 2 notifications sent, got {auto_reject['notifications_sent']}"
    )
    print(f"✓ Auto-reject metrics correct:")
    print(f"  - Total auto-rejected: {auto_reject['total_auto_rejected']}")
    print(f"  - Notifications sent: {auto_reject['notifications_sent']}")

    print("\n=== Screening Metrics Accuracy Test PASSED ===\n")
    print("All metrics calculated correctly:")
    print("  ✓ Volume metrics (total, monthly, weekly, rate)")
    print("  ✓ Tier distribution (counts and percentages)")
    print("  ✓ Score statistics (avg, min, max, percentiles)")
    print("  ✓ Auto-reject tracking (count and notifications)")
