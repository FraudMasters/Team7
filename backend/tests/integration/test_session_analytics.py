"""
Integration tests for Session Analytics.

This test suite validates the end-to-end integration between:
- Frontend (simulated via HTTP requests)
- Backend session analytics endpoints
- SessionAnalyticsService (database-backed analytics)
- Session model (session data persistence)
- Analytics calculations and aggregations

Test Coverage:
- Session analytics endpoint returns correct data
- Session metrics calculation (total, active, revoked)
- Device distribution analytics
- Geographic distribution analytics
- Anomaly detection for suspicious patterns
- Login anomaly detection
- Peak usage time analytics
- Session lifecycle statistics
- Error handling for invalid parameters
- Authentication and authorization
- Service health checks
"""
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Generator, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

# Import the FastAPI application
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import app
from database import get_db
from models.user import User
from models.session import Session as SessionModel
from models.login_attempt import LoginAttempt
from services.session_analytics_service import (
    SessionAnalyticsService,
    get_session_analytics_service,
)
from services.auth_service import AuthService


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """
    Create a FastAPI test client for all tests.

    Yields:
        TestClient instance
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def analytics_service():
    """
    Get the session analytics service instance.

    Returns:
        SessionAnalyticsService instance
    """
    return get_session_analytics_service()


@pytest.fixture
async def test_user(test_db: AsyncSession) -> User:
    """
    Create a test user for authentication tests.

    Args:
        test_db: Database session

    Returns:
        Created user instance
    """
    user = User(
        id=uuid.uuid4(),
        email=f"test-{uuid.uuid4()}@example.com",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzpLaEtIZC",  # "password"
        is_active=True,
        role="user",
        created_at=datetime.utcnow(),
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def authenticated_client(client: TestClient, test_user: User) -> TestClient:
    """
    Create an authenticated test client with access token.

    Args:
        client: Test client
        test_user: Test user

    Returns:
        Test client with authentication headers
    """
    # Login to get access token
    response = client.post(
        "/api/auth/login",
        json={
            "email": test_user.email,
            "password": "password",
        }
    )
    assert response.status_code == 200
    access_token = response.json()["access_token"]

    # Add authorization header
    client.headers["Authorization"] = f"Bearer {access_token}"
    return client


class TestSessionAnalyticsEndpoint:
    """Tests for the /sessions/analytics endpoint."""

    def test_get_analytics_requires_authentication(self, client: TestClient):
        """Test that session analytics endpoint requires authentication."""
        response = client.get("/api/auth/sessions/analytics")

        # Should return 401 Unauthorized
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_analytics_returns_valid_data(
        self,
        authenticated_client: TestClient,
        test_user: User,
        test_db: AsyncSession,
    ):
        """Test that analytics endpoint returns valid data structure."""
        # Create some test sessions
        for i in range(3):
            session = SessionModel(
                id=uuid.uuid4(),
                user_id=test_user.id,
                access_token=f"token-{i}",
                refresh_token=f"refresh-{i}",
                is_active=True,
                device_type="desktop" if i < 2 else "mobile",
                ip_address=f"192.168.1.{i}",
                user_agent=f"TestAgent/{i}",
                created_at=datetime.utcnow() - timedelta(days=i),
            )
            test_db.add(session)
        await test_db.commit()

        # Get analytics
        response = authenticated_client.get("/api/auth/sessions/analytics?days=7")

        # Should return 200 OK
        assert response.status_code == 200

        # Verify response structure
        data = response.json()
        assert "period_days" in data
        assert "total_sessions" in data
        assert "active_sessions" in data
        assert "revoked_sessions" in data
        assert "average_session_duration_minutes" in data
        assert "device_distribution" in data
        assert "revocation_reasons" in data

        # Verify data types
        assert isinstance(data["period_days"], int)
        assert isinstance(data["total_sessions"], int)
        assert isinstance(data["active_sessions"], int)
        assert isinstance(data["revoked_sessions"], int)
        assert isinstance(data["device_distribution"], dict)
        assert isinstance(data["revocation_reasons"], dict)

    @pytest.mark.asyncio
    async def test_get_analytics_counts_sessions_correctly(
        self,
        authenticated_client: TestClient,
        test_user: User,
        test_db: AsyncSession,
    ):
        """Test that analytics endpoint counts sessions correctly."""
        # Create 5 active sessions and 3 revoked sessions
        for i in range(8):
            session = SessionModel(
                id=uuid.uuid4(),
                user_id=test_user.id,
                access_token=f"token-{i}",
                refresh_token=f"refresh-{i}",
                is_active=i < 5,  # First 5 are active
                device_type="desktop",
                created_at=datetime.utcnow() - timedelta(hours=i),
            )
            if i >= 5:
                session.revoked_at = datetime.utcnow()
                session.revoke_reason = "user_logout"
            test_db.add(session)
        await test_db.commit()

        # Get analytics
        response = authenticated_client.get("/api/auth/sessions/analytics?days=1")

        # Verify counts
        assert response.status_code == 200
        data = response.json()
        assert data["total_sessions"] == 8
        assert data["active_sessions"] == 5
        assert data["revoked_sessions"] == 3

    @pytest.mark.asyncio
    async def test_get_analytics_device_distribution(
        self,
        authenticated_client: TestClient,
        test_user: User,
        test_db: AsyncSession,
    ):
        """Test that device distribution is calculated correctly."""
        # Create sessions with different device types
        devices = ["desktop", "desktop", "mobile", "tablet", "desktop"]
        for i, device in enumerate(devices):
            session = SessionModel(
                id=uuid.uuid4(),
                user_id=test_user.id,
                access_token=f"token-{i}",
                refresh_token=f"refresh-{i}",
                is_active=True,
                device_type=device,
                created_at=datetime.utcnow() - timedelta(hours=i),
            )
            test_db.add(session)
        await test_db.commit()

        # Get analytics
        response = authenticated_client.get("/api/auth/sessions/analytics?days=1")

        # Verify device distribution
        assert response.status_code == 200
        data = response.json()
        assert data["device_distribution"]["desktop"] == 3
        assert data["device_distribution"]["mobile"] == 1
        assert data["device_distribution"]["tablet"] == 1

    @pytest.mark.asyncio
    async def test_get_analytics_filters_by_days(
        self,
        authenticated_client: TestClient,
        test_user: User,
        test_db: AsyncSession,
    ):
        """Test that analytics filters by days parameter correctly."""
        # Create sessions at different times
        session_old = SessionModel(
            id=uuid.uuid4(),
            user_id=test_user.id,
            access_token="token-old",
            refresh_token="refresh-old",
            is_active=True,
            device_type="desktop",
            created_at=datetime.utcnow() - timedelta(days=10),
        )
        session_recent = SessionModel(
            id=uuid.uuid4(),
            user_id=test_user.id,
            access_token="token-recent",
            refresh_token="refresh-recent",
            is_active=True,
            device_type="desktop",
            created_at=datetime.utcnow() - timedelta(days=2),
        )
        test_db.add_all([session_old, session_recent])
        await test_db.commit()

        # Get analytics for last 7 days (should only include recent session)
        response = authenticated_client.get("/api/auth/sessions/analytics?days=7")

        assert response.status_code == 200
        data = response.json()
        assert data["total_sessions"] == 1  # Only the recent one

        # Get analytics for last 30 days (should include both)
        response = authenticated_client.get("/api/auth/sessions/analytics?days=30")

        assert response.status_code == 200
        data = response.json()
        assert data["total_sessions"] == 2  # Both sessions

    def test_get_analytics_validates_days_parameter_min(
        self,
        authenticated_client: TestClient,
    ):
        """Test that days parameter is validated (minimum value)."""
        response = authenticated_client.get("/api/auth/sessions/analytics?days=0")

        # Should return 400 Bad Request
        assert response.status_code == 400
        assert "between 1 and 365" in response.json()["detail"]

    def test_get_analytics_validates_days_parameter_max(
        self,
        authenticated_client: TestClient,
    ):
        """Test that days parameter is validated (maximum value)."""
        response = authenticated_client.get("/api/auth/sessions/analytics?days=400")

        # Should return 400 Bad Request
        assert response.status_code == 400
        assert "between 1 and 365" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_analytics_default_days_parameter(
        self,
        authenticated_client: TestClient,
        test_user: User,
        test_db: AsyncSession,
    ):
        """Test that days parameter defaults to 30."""
        # Create a session
        session = SessionModel(
            id=uuid.uuid4(),
            user_id=test_user.id,
            access_token="token",
            refresh_token="refresh",
            is_active=True,
            device_type="desktop",
            created_at=datetime.utcnow(),
        )
        test_db.add(session)
        await test_db.commit()

        # Get analytics without days parameter
        response = authenticated_client.get("/api/auth/sessions/analytics")

        assert response.status_code == 200
        data = response.json()
        assert data["period_days"] == 30  # Default value

    @pytest.mark.asyncio
    async def test_get_analytics_revocation_reasons(
        self,
        authenticated_client: TestClient,
        test_user: User,
        test_db: AsyncSession,
    ):
        """Test that revocation reasons are aggregated correctly."""
        # Create sessions with different revocation reasons
        reasons = ["user_logout", "user_logout", "timeout", "admin_revoke"]
        for i, reason in enumerate(reasons):
            session = SessionModel(
                id=uuid.uuid4(),
                user_id=test_user.id,
                access_token=f"token-{i}",
                refresh_token=f"refresh-{i}",
                is_active=False,
                device_type="desktop",
                revoked_at=datetime.utcnow(),
                revoke_reason=reason,
                created_at=datetime.utcnow() - timedelta(hours=i),
            )
            test_db.add(session)
        await test_db.commit()

        # Get analytics
        response = authenticated_client.get("/api/auth/sessions/analytics?days=1")

        # Verify revocation reasons
        assert response.status_code == 200
        data = response.json()
        assert data["revocation_reasons"]["user_logout"] == 2
        assert data["revocation_reasons"]["timeout"] == 1
        assert data["revocation_reasons"]["admin_revoke"] == 1

    @pytest.mark.asyncio
    async def test_get_analytics_empty_results(
        self,
        authenticated_client: TestClient,
    ):
        """Test that analytics endpoint handles no sessions gracefully."""
        response = authenticated_client.get("/api/auth/sessions/analytics?days=7")

        assert response.status_code == 200
        data = response.json()
        assert data["total_sessions"] == 0
        assert data["active_sessions"] == 0
        assert data["revoked_sessions"] == 0


class TestSessionMetricsService:
    """Tests for SessionAnalyticsService.get_session_metrics()."""

    @pytest.mark.asyncio
    async def test_get_session_metrics_calculates_durations(
        self,
        analytics_service: SessionAnalyticsService,
        test_user: User,
        test_db: AsyncSession,
    ):
        """Test that session duration metrics are calculated correctly."""
        # Create sessions with known durations
        now = datetime.utcnow()
        sessions = [
            SessionModel(
                id=uuid.uuid4(),
                user_id=test_user.id,
                access_token=f"token-{i}",
                refresh_token=f"refresh-{i}",
                is_active=False,
                device_type="desktop",
                created_at=now - timedelta(hours=2),
                revoked_at=now - timedelta(hours=1),  # 60 min duration
            )
            for i in range(3)
        ]
        for session in sessions:
            test_db.add(session)
        await test_db.commit()

        # Get metrics
        metrics = await analytics_service.get_session_metrics(
            user_id=str(test_user.id),
            days=1
        )

        # Verify duration calculations
        assert metrics["average_session_duration_minutes"] == 60.0
        assert metrics["max_session_duration_minutes"] == 60.0
        assert metrics["min_session_duration_minutes"] == 60.0

    @pytest.mark.asyncio
    async def test_get_session_metrics_global_stats(
        self,
        analytics_service: SessionAnalyticsService,
        test_db: AsyncSession,
    ):
        """Test that global metrics work without user_id filter."""
        # Create sessions for multiple users
        for i in range(3):
            user_id = uuid.uuid4()
            session = SessionModel(
                id=uuid.uuid4(),
                user_id=user_id,
                access_token=f"token-{i}",
                refresh_token=f"refresh-{i}",
                is_active=True,
                device_type="desktop",
                created_at=datetime.utcnow(),
            )
            test_db.add(session)
        await test_db.commit()

        # Get global metrics (no user_id)
        metrics = await analytics_service.get_session_metrics(
            user_id=None,
            days=1
        )

        # Should include all sessions
        assert metrics["total_sessions"] == 3

    @pytest.mark.asyncio
    async def test_get_session_metrics_includes_expired(
        self,
        analytics_service: SessionAnalyticsService,
        test_user: User,
        test_db: AsyncSession,
    ):
        """Test that expired sessions are counted correctly."""
        # Create an expired session (created > 24 hours ago, still active)
        old_session = SessionModel(
            id=uuid.uuid4(),
            user_id=test_user.id,
            access_token="token-old",
            refresh_token="refresh-old",
            is_active=True,
            device_type="desktop",
            created_at=datetime.utcnow() - timedelta(hours=25),
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        db.add(old_session)
        await db.commit()

        # Get metrics
        metrics = await analytics_service.get_session_metrics(
            user_id=str(test_user.id),
            days=7
        )

        # Should count expired session
        assert metrics["expired_sessions"] >= 1


class TestDeviceDistribution:
    """Tests for SessionAnalyticsService.get_device_distribution()."""

    @pytest.mark.asyncio
    async def test_get_device_distribution_aggregates_correctly(
        self,
        analytics_service: SessionAnalyticsService,
        test_user: User,
        test_db: AsyncSession,
    ):
        """Test that device distribution is aggregated correctly."""
        # Create sessions with various devices
        devices = ["desktop", "mobile", "tablet", "desktop", "mobile", "desktop"]
        for i, device in enumerate(devices):
            session = SessionModel(
                id=uuid.uuid4(),
                user_id=test_user.id,
                access_token=f"token-{i}",
                refresh_token=f"refresh-{i}",
                is_active=True,
                device_type=device,
                created_at=datetime.utcnow(),
            )
            test_db.add(session)
        await test_db.commit()

        # Get distribution
        distribution = await analytics_service.get_device_distribution(
            user_id=str(test_user.id),
            days=1
        )

        # Verify counts
        assert distribution["desktop"] == 3
        assert distribution["mobile"] == 2
        assert distribution["tablet"] == 1

    @pytest.mark.asyncio
    async def test_get_device_distribution_handles_unknown(
        self,
        analytics_service: SessionAnalyticsService,
        test_user: User,
        test_db: AsyncSession,
    ):
        """Test that null device types are labeled as 'unknown'."""
        # Create session with no device type
        session = SessionModel(
            id=uuid.uuid4(),
            user_id=test_user.id,
            access_token="token",
            refresh_token="refresh",
            is_active=True,
            device_type=None,
            created_at=datetime.utcnow(),
        )
        test_db.add(session)
        await test_db.commit()

        # Get distribution
        distribution = await analytics_service.get_device_distribution(
            user_id=str(test_user.id),
            days=1
        )

        # Should have "unknown" entry
        assert "unknown" in distribution
        assert distribution["unknown"] == 1


class TestGeographicDistribution:
    """Tests for SessionAnalyticsService.get_geographic_distribution()."""

    @pytest.mark.asyncio
    async def test_get_geographic_distribution(
        self,
        analytics_service: SessionAnalyticsService,
        test_user: User,
        test_db: AsyncSession,
    ):
        """Test that geographic distribution is calculated correctly."""
        # Create sessions from different locations
        locations = [
            "San Francisco, CA",
            "New York, NY",
            "San Francisco, CA",
            "London, UK",
        ]
        for i, location in enumerate(locations):
            session = SessionModel(
                id=uuid.uuid4(),
                user_id=test_user.id,
                access_token=f"token-{i}",
                refresh_token=f"refresh-{i}",
                is_active=True,
                device_type="desktop",
                location=location,
                created_at=datetime.utcnow(),
            )
            test_db.add(session)
        await test_db.commit()

        # Get distribution
        distribution = await analytics_service.get_geographic_distribution(
            user_id=str(test_user.id),
            days=1
        )

        # Verify counts
        assert distribution["San Francisco, CA"] == 2
        assert distribution["New York, NY"] == 1
        assert distribution["London, UK"] == 1

    @pytest.mark.asyncio
    async def test_get_geographic_distribution_excludes_null(
        self,
        analytics_service: SessionAnalyticsService,
        test_user: User,
        test_db: AsyncSession,
    ):
        """Test that sessions without location are excluded."""
        # Create sessions with and without location
        session_with = SessionModel(
            id=uuid.uuid4(),
            user_id=test_user.id,
            access_token="token-1",
            refresh_token="refresh-1",
            is_active=True,
            device_type="desktop",
            location="Paris, France",
            created_at=datetime.utcnow(),
        )
        session_without = SessionModel(
            id=uuid.uuid4(),
            user_id=test_user.id,
            access_token="token-2",
            refresh_token="refresh-2",
            is_active=True,
            device_type="desktop",
            location=None,
            created_at=datetime.utcnow(),
        )
        test_db.add_all([session_with, session_without])
        await test_db.commit()

        # Get distribution
        distribution = await analytics_service.get_geographic_distribution(
            user_id=str(test_user.id),
            days=1
        )

        # Should only include session with location
        assert "Paris, France" in distribution
        assert distribution["Paris, France"] == 1
        assert len(distribution) == 1


class TestAnomalyDetection:
    """Tests for SessionAnalyticsService.detect_anomalies()."""

    @pytest.mark.asyncio
    async def test_detect_concurrent_sessions_anomaly(
        self,
        analytics_service: SessionAnalyticsService,
        test_user: User,
        test_db: AsyncSession,
    ):
        """Test detection of excessive concurrent sessions."""
        # Create many active sessions (more than threshold)
        for i in range(10):
            session = SessionModel(
                id=uuid.uuid4(),
                user_id=test_user.id,
                access_token=f"token-{i}",
                refresh_token=f"refresh-{i}",
                is_active=True,
                device_type="desktop",
                created_at=datetime.utcnow(),
            )
            test_db.add(session)
        await test_db.commit()

        # Detect anomalies
        anomalies = await analytics_service.detect_anomalies(
            user_id=str(test_user.id),
            days=1
        )

        # Should detect concurrent sessions anomaly
        concurrent_anomaly = next(
            (a for a in anomalies if a["type"] == "concurrent_sessions"),
            None
        )
        assert concurrent_anomaly is not None
        assert concurrent_anomaly["count"] == 10
        assert concurrent_anomaly["severity"] in ["medium", "high"]

    @pytest.mark.asyncio
    async def test_detect_suspicious_ip_anomaly(
        self,
        analytics_service: SessionAnalyticsService,
        test_user: User,
        test_db: AsyncSession,
    ):
        """Test detection of suspicious IP patterns."""
        # Create many sessions from same IP
        for i in range(15):
            session = SessionModel(
                id=uuid.uuid4(),
                user_id=test_user.id,
                access_token=f"token-{i}",
                refresh_token=f"refresh-{i}",
                is_active=True,
                device_type="desktop",
                ip_address="192.168.1.100",
                created_at=datetime.utcnow() - timedelta(hours=i),
            )
            test_db.add(session)
        await test_db.commit()

        # Detect anomalies
        anomalies = await analytics_service.detect_anomalies(
            user_id=str(test_user.id),
            days=1
        )

        # Should detect suspicious IP
        ip_anomaly = next(
            (a for a in anomalies if a["type"] == "suspicious_ip"),
            None
        )
        assert ip_anomaly is not None
        assert ip_anomaly["ip_address"] == "192.168.1.100"
        assert ip_anomaly["count"] == 15

    @pytest.mark.asyncio
    async def test_detect_rapid_session_creation(
        self,
        analytics_service: SessionAnalyticsService,
        test_user: User,
        test_db: AsyncSession,
    ):
        """Test detection of rapid session creation."""
        # Create many sessions in short time
        now = datetime.utcnow()
        for i in range(7):
            session = SessionModel(
                id=uuid.uuid4(),
                user_id=test_user.id,
                access_token=f"token-{i}",
                refresh_token=f"refresh-{i}",
                is_active=True,
                device_type="desktop",
                created_at=now - timedelta(minutes=i),
            )
            test_db.add(session)
        await test_db.commit()

        # Detect anomalies
        anomalies = await analytics_service.detect_anomalies(
            user_id=str(test_user.id),
            days=1
        )

        # Should detect rapid creation
        rapid_anomaly = next(
            (a for a in anomalies if a["type"] == "rapid_session_creation"),
            None
        )
        assert rapid_anomaly is not None
        assert rapid_anomaly["count"] >= 6

    @pytest.mark.asyncio
    async def test_detect_geographic_anomaly(
        self,
        analytics_service: SessionAnalyticsService,
        test_user: User,
        test_db: AsyncSession,
    ):
        """Test detection of sessions from many locations."""
        # Create sessions from many different locations
        locations = [
            "New York, NY",
            "Los Angeles, CA",
            "Chicago, IL",
            "Houston, TX",
            "Phoenix, AZ",
            "Philadelphia, PA",
        ]
        for i, location in enumerate(locations):
            session = SessionModel(
                id=uuid.uuid4(),
                user_id=test_user.id,
                access_token=f"token-{i}",
                refresh_token=f"refresh-{i}",
                is_active=True,
                device_type="desktop",
                location=location,
                created_at=datetime.utcnow() - timedelta(hours=i),
            )
            test_db.add(session)
        await test_db.commit()

        # Detect anomalies
        anomalies = await analytics_service.detect_anomalies(
            user_id=str(test_user.id),
            days=1
        )

        # Should detect geographic anomaly
        geo_anomaly = next(
            (a for a in anomalies if a["type"] == "geographic_anomaly"),
            None
        )
        assert geo_anomaly is not None
        assert len(geo_anomaly["locations"]) == 6

    @pytest.mark.asyncio
    async def test_no_anomalies_for_normal_usage(
        self,
        analytics_service: SessionAnalyticsService,
        test_user: User,
        test_db: AsyncSession,
    ):
        """Test that normal usage doesn't trigger anomalies."""
        # Create a few normal sessions
        for i in range(2):
            session = SessionModel(
                id=uuid.uuid4(),
                user_id=test_user.id,
                access_token=f"token-{i}",
                refresh_token=f"refresh-{i}",
                is_active=True,
                device_type="desktop",
                ip_address=f"192.168.1.{i}",
                created_at=datetime.utcnow() - timedelta(days=i),
            )
            test_db.add(session)
        await test_db.commit()

        # Detect anomalies
        anomalies = await analytics_service.detect_anomalies(
            user_id=str(test_user.id),
            days=7
        )

        # Should not detect any anomalies
        assert len(anomalies) == 0


class TestLoginAnomalyDetection:
    """Tests for SessionAnalyticsService.detect_anomaly() for login attempts."""

    @pytest.mark.asyncio
    async def test_detect_rapid_failed_attempts(
        self,
        analytics_service: SessionAnalyticsService,
        test_user: User,
        test_db: AsyncSession,
    ):
        """Test detection of rapid failed login attempts."""
        # Create multiple failed login attempts in the last hour
        now = datetime.utcnow()
        for i in range(6):
            attempt = LoginAttempt(
                id=uuid.uuid4(),
                user_id=test_user.id,
                email=test_user.email,
                success=False,
                ip_address="192.168.1.100",
                user_agent="TestAgent",
                created_at=now - timedelta(minutes=i),
            )
            test_db.add(attempt)
        await test_db.commit()

        # Detect anomalies
        result = await analytics_service.detect_anomaly(
            user_id=str(test_user.id),
            days=1
        )

        # Should detect rapid failed attempts
        assert result["has_anomaly"] is True
        assert result["risk_score"] > 0
        rapid_anomaly = next(
            (a for a in result["anomalies"] if a["type"] == "rapid_failed_attempts"),
            None
        )
        assert rapid_anomaly is not None
        assert rapid_anomaly["count"] >= 5

    @pytest.mark.asyncio
    async def test_detect_credential_stuffing(
        self,
        analytics_service: SessionAnalyticsService,
        test_user: User,
        test_db: AsyncSession,
    ):
        """Test detection of credential stuffing pattern."""
        # Create failed attempts followed by success
        now = datetime.utcnow()
        for i in range(5):
            attempt = LoginAttempt(
                id=uuid.uuid4(),
                user_id=test_user.id,
                email=test_user.email,
                success=False,
                ip_address="192.168.1.100",
                user_agent="TestAgent",
                created_at=now - timedelta(minutes=10 - i),
            )
            db.add(attempt)

        # Add successful attempt after failures
        success_attempt = LoginAttempt(
            id=uuid.uuid4(),
            user_id=test_user.id,
            email=test_user.email,
            success=True,
            ip_address="192.168.1.100",
            user_agent="TestAgent",
            created_at=now,
        )
        db.add(success_attempt)
        await db.commit()

        # Detect anomalies
        result = await analytics_service.detect_anomaly(
            user_id=str(test_user.id),
            days=1
        )

        # Should detect credential stuffing
        assert result["has_anomaly"] is True
        stuffing_anomaly = next(
            (a for a in result["anomalies"] if a["type"] == "credential_stuffing"),
            None
        )
        assert stuffing_anomaly is not None

    @pytest.mark.asyncio
    async def test_detect_geographic_impossibility(
        self,
        analytics_service: SessionAnalyticsService,
        test_user: User,
        test_db: AsyncSession,
    ):
        """Test detection of geographically impossible logins."""
        # Create successful logins from different locations within 30 minutes
        now = datetime.utcnow()
        attempt1 = LoginAttempt(
            id=uuid.uuid4(),
            user_id=test_user.id,
            email=test_user.email,
            success=True,
            ip_address="192.168.1.1",
            location="New York, NY",
            user_agent="TestAgent",
            created_at=now - timedelta(minutes=30),
        )
        attempt2 = LoginAttempt(
            id=uuid.uuid4(),
            user_id=test_user.id,
            email=test_user.email,
            success=True,
            ip_address="192.168.2.1",
            location="Los Angeles, CA",
            user_agent="TestAgent",
            created_at=now,
        )
        test_db.add_all([attempt1, attempt2])
        await test_db.commit()

        # Detect anomalies
        result = await analytics_service.detect_anomaly(
            user_id=str(test_user.id),
            days=1
        )

        # Should detect geographic impossibility
        assert result["has_anomaly"] is True
        geo_anomaly = next(
            (a for a in result["anomalies"] if a["type"] == "geographic_impossibility"),
            None
        )
        assert geo_anomaly is not None

    @pytest.mark.asyncio
    async def test_risk_score_calculation(
        self,
        analytics_service: SessionAnalyticsService,
        test_user: User,
        test_db: AsyncSession,
    ):
        """Test that risk score is calculated correctly."""
        # Create high-risk scenario: many failed attempts
        now = datetime.utcnow()
        for i in range(10):
            attempt = LoginAttempt(
                id=uuid.uuid4(),
                user_id=test_user.id,
                email=test_user.email,
                success=False,
                ip_address="192.168.1.100",
                user_agent="TestAgent",
                created_at=now - timedelta(minutes=i),
            )
            test_db.add(attempt)
        await test_db.commit()

        # Detect anomalies
        result = await analytics_service.detect_anomaly(
            user_id=str(test_user.id),
            days=1
        )

        # Risk score should be substantial
        assert result["risk_score"] > 0
        assert result["risk_score"] <= 100
        # High risk should have recommendations
        assert len(result["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_no_anomaly_for_normal_logins(
        self,
        analytics_service: SessionAnalyticsService,
        test_user: User,
        test_db: AsyncSession,
    ):
        """Test that normal login patterns don't trigger anomalies."""
        # Create normal successful login
        attempt = LoginAttempt(
            id=uuid.uuid4(),
            user_id=test_user.id,
            email=test_user.email,
            success=True,
            ip_address="192.168.1.100",
            user_agent="TestAgent",
            created_at=datetime.utcnow(),
        )
        test_db.add(attempt)
        await test_db.commit()

        # Detect anomalies
        result = await analytics_service.detect_anomaly(
            user_id=str(test_user.id),
            days=1
        )

        # Should not detect anomalies
        assert result["has_anomaly"] is False
        assert result["risk_score"] == 0
        assert len(result["anomalies"]) == 0


class TestPeakUsageTimes:
    """Tests for SessionAnalyticsService.get_peak_usage_times()."""

    @pytest.mark.asyncio
    async def test_get_peak_usage_times(
        self,
        analytics_service: SessionAnalyticsService,
        test_user: User,
        test_db: AsyncSession,
    ):
        """Test that peak usage times are calculated correctly."""
        # Create sessions at different hours
        now = datetime.utcnow()
        # 3 sessions at hour 10, 2 at hour 14, 1 at hour 18
        hours = [10, 10, 10, 14, 14, 18]
        for i, hour in enumerate(hours):
            created = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            session = SessionModel(
                id=uuid.uuid4(),
                user_id=test_user.id,
                access_token=f"token-{i}",
                refresh_token=f"refresh-{i}",
                is_active=True,
                device_type="desktop",
                created_at=created,
            )
            test_db.add(session)
        await test_db.commit()

        # Get peak usage times
        usage = await analytics_service.get_peak_usage_times(
            user_id=str(test_user.id),
            days=1
        )

        # Verify counts
        assert usage[10] == 3
        assert usage[14] == 2
        assert usage[18] == 1
        # All other hours should be 0
        for hour in range(24):
            if hour not in [10, 14, 18]:
                assert usage[hour] == 0


class TestSessionLifecycleStats:
    """Tests for SessionAnalyticsService.get_session_lifecycle_stats()."""

    @pytest.mark.asyncio
    async def test_get_session_lifecycle_stats(
        self,
        analytics_service: SessionAnalyticsService,
        test_user: User,
        test_db: AsyncSession,
    ):
        """Test that lifecycle statistics are calculated correctly."""
        # Create sessions over 10 days
        for i in range(10):
            session = SessionModel(
                id=uuid.uuid4(),
                user_id=test_user.id,
                access_token=f"token-{i}",
                refresh_token=f"refresh-{i}",
                is_active=i < 6,  # 6 active, 4 revoked
                device_type="desktop",
                created_at=datetime.utcnow() - timedelta(days=i),
            )
            if i >= 6:
                session.revoked_at = datetime.utcnow()
            test_db.add(session)
        await test_db.commit()

        # Get lifecycle stats
        stats = await analytics_service.get_session_lifecycle_stats(
            user_id=str(test_user.id),
            days=30
        )

        # Verify stats
        assert stats["total_sessions"] == 10
        assert stats["active_sessions"] == 6
        assert stats["revoked_sessions"] == 4
        assert stats["daily_creation_rate"] > 0
        assert stats["active_to_total_ratio"] == 0.6
        assert stats["revocation_rate"] == 0.4


class TestHealthCheck:
    """Tests for SessionAnalyticsService.health_check()."""

    @pytest.mark.asyncio
    async def test_health_check_healthy(
        self,
        analytics_service: SessionAnalyticsService,
    ):
        """Test that health check returns healthy status."""
        result = await analytics_service.health_check()

        assert result["status"] == "healthy"
        assert result["error"] is None

    @pytest.mark.asyncio
    async def test_health_check_with_database_error(
        self,
        analytics_service: SessionAnalyticsService,
    ):
        """Test that health check detects database errors."""
        # Mock the get_session_metrics to raise an error
        with patch.object(
            analytics_service,
            "get_session_metrics",
            side_effect=Exception("Database connection failed")
        ):
            result = await analytics_service.health_check()

            assert result["status"] == "unhealthy"
            assert result["error"] is not None
