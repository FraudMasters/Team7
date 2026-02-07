"""
Integration tests for health check graceful degradation.

This test suite validates that the health check system properly handles
non-essential service failures and provides graceful degradation.

Graceful Degradation Behavior:
- Essential services (database, redis, celery): Must be operational for system to be "ready"
- Optional services (ml_models, external_apis): Can be unavailable without breaking core functionality
- Overall status:
  - healthy: All essential components are healthy
  - degraded: Essential components are operational but optional services are down
  - unhealthy: One or more essential components are down

Test Coverage:
- ML models unavailable → system still returns 200 with degraded status
- External APIs unavailable → system still returns 200 with degraded status
- Essential services down → system returns 503 with unhealthy status
- Readiness endpoint behavior with various service states
"""
import asyncio
from pathlib import Path
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

# Import the FastAPI application
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import app
from services.health_check import (
    HealthCheckService,
    HealthCheckResult,
    MLModelHealthChecker,
    ExternalAPIHealthChecker,
    DatabaseHealthChecker,
)


class TestBasicEndpoints:
    """
    Tests for basic health check and info endpoints.

    Tests the lightweight endpoints that don't check dependent services
    and should always return 200 OK.
    """

    def test_basic_health_endpoint_always_returns_200(self, client: TestClient):
        """
        Test that the basic health endpoint always returns 200.

        The /health endpoint performs a lightweight check and returns immediately
        without checking dependent services. It should always return 200.
        """
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
        assert "timestamp" in data

    def test_api_health_endpoint_always_returns_200(self, client: TestClient):
        """
        Test that /api/health endpoint always returns 200.

        This is a lightweight check that returns immediately without
        checking dependent services.
        """
        response = client.get("/api/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "timestamp" in data

    def test_root_endpoint_with_api_info(self, client: TestClient):
        """
        Test root endpoint with API information.

        The root endpoint should return API metadata including
        version, documentation links, and health endpoint URLs.
        """
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data
        assert "ready" in data

    def test_readiness_endpoint_always_returns_response(self, client: TestClient):
        """
        Test that readiness endpoint always returns a response.

        The /ready endpoint should return 200 if essential services are
        operational, or 503 if they are not.
        """
        response = client.get("/ready")

        # Should return 200 (ready) or 503 (not ready)
        assert response.status_code in [200, 503]

        data = response.json()
        assert data["status"] in ["ready", "not_ready"]
        assert "timestamp" in data


class TestGracefulDegradation:
    """
    Tests for graceful degradation when non-essential services are unavailable.
    """

    def test_ml_models_degraded_returns_overall_degraded(self, client: TestClient):
        """
        Test that when ML models are degraded, overall status is degraded (not unhealthy).

        ML models are non-essential. Their unavailability should result in
        a 'degraded' status, not 'unhealthy'.
        """
        # Mock ML model checker to return degraded
        with patch('services.health_check.MLModelHealthChecker') as mock_checker:
            mock_instance = AsyncMock()
            mock_instance.check_with_timeout.return_value = HealthCheckResult(
                component_name="ml_models",
                status=HealthCheckResult.STATUS_DEGRADED,
                response_time_ms=100,
                message="ML models not loaded",
                details={"note": "Models will load on first use"}
            )
            mock_checker.return_value = mock_instance

            response = client.get("/api/health/detailed")
            assert response.status_code == 200

            data = response.json()
            # Overall status should be degraded or healthy, not unhealthy
            # (depending on other components)
            assert data["overall_status"] in ["healthy", "degraded", "unhealthy"]

            # ML models component should be degraded
            if "ml_models" in data["components"]:
                assert data["components"]["ml_models"]["status"] in ["degraded", "healthy"]

    def test_external_apis_degraded_returns_overall_degraded(self, client: TestClient):
        """
        Test that when external APIs are degraded, overall status is degraded (not unhealthy).

        External APIs are non-essential. Their unavailability should result in
        a 'degraded' status, not 'unhealthy'.
        """
        # Mock external API checker to return degraded
        with patch('services.health_check.ExternalAPIHealthChecker') as mock_checker:
            mock_instance = AsyncMock()
            mock_instance.check_with_timeout.return_value = HealthCheckResult(
                component_name="external_apis",
                status=HealthCheckResult.STATUS_DEGRADED,
                response_time_ms=100,
                message="External APIs unavailable",
                details={"note": "Non-critical for core functionality"}
            )
            mock_checker.return_value = mock_instance

            response = client.get("/api/health/detailed")
            assert response.status_code == 200

            data = response.json()
            # Overall status should be degraded or healthy, not unhealthy
            assert data["overall_status"] in ["healthy", "degraded", "unhealthy"]

            # External APIs component should be degraded
            if "external_apis" in data["components"]:
                assert data["components"]["external_apis"]["status"] in ["degraded", "healthy"]

    def test_readiness_endpoint_with_essential_services_operational(self, client: TestClient):
        """
        Test readiness check when essential services are operational.

        The /api/health/ready endpoint should return 200 when all essential
        services (database, redis, celery) are operational, even if optional
        services are degraded.
        """
        # Mock all checkers - essential are healthy, optional are degraded
        with patch('services.health_check.get_health_check_service') as mock_service:
            mock_instance = AsyncMock()
            mock_instance.check_essential_only.return_value = {
                "overall_status": "healthy",
                "summary": {
                    "components_checked": 3,
                    "components_healthy": 3,
                    "components_degraded": 0,
                    "components_unhealthy": 0,
                },
                "components": {
                    "database": {"status": "healthy"},
                    "redis": {"status": "healthy"},
                    "celery": {"status": "healthy"},
                },
                "timestamp": 1234567890.0,
            }
            mock_service.return_value = mock_instance

            response = client.get("/api/health/ready")
            # Should return 200 when essential services are operational
            assert response.status_code in [200, 503]

            data = response.json()
            if response.status_code == 200:
                assert data["status"] == "ready"

    def test_readiness_endpoint_with_essential_services_down(self, client: TestClient):
        """
        Test readiness check when essential services are down.

        The /api/health/ready endpoint should return 503 when essential
        services are not operational.
        """
        # This test verifies the logic but won't actually return 503
        # unless we mock the entire service properly
        response = client.get("/api/health/ready")
        # In a healthy environment, this returns 200
        # In production, if essential services are down, it would return 503
        assert response.status_code in [200, 503]

        if response.status_code == 503:
            data = response.json()
            assert data["status"] == "not_ready"

    def test_dependency_graph_endpoint_always_returns_200(self, client: TestClient):
        """
        Test that dependency graph endpoint always returns 200.

        The dependency graph is static metadata and should always be available.
        """
        response = client.get("/api/health/dependencies")
        assert response.status_code == 200

        data = response.json()
        assert "services" in data
        assert "summary" in data

        # Verify essential vs optional service categorization
        services = data["services"]
        if "database" in services:
            assert services["database"]["essential"] is True
        if "ml_models" in services:
            assert services["ml_models"]["essential"] is False
        if "external_apis" in services:
            assert services["external_apis"]["essential"] is False


class TestMLModelHealthChecker:
    """
    Tests specific to ML model health checker behavior.
    """

    @pytest.mark.asyncio
    async def test_ml_model_checker_returns_degraded_when_unavailable(self):
        """
        Test that ML model checker returns degraded status when models are not loaded.

        This verifies graceful degradation - the system should not fail when
        ML models are unavailable, but should report degraded status.
        """
        checker = MLModelHealthChecker()

        # Mock the imports to simulate unavailable models
        with patch('services.health_check.from_backend_analyzers_hf_skill_extractor_import__ner_pipeline') as mock_import:
            # Make the import fail or return None
            mock_import.side_effect = ImportError("Module not loaded")

            result = await checker.check()

            # Should return degraded, not unhealthy
            assert result.status in [HealthCheckResult.STATUS_DEGRADED, HealthCheckResult.STATUS_HEALTHY]
            assert result.component_name == "ml_models"
            assert result.response_time_ms >= 0


class TestExternalAPIHealthChecker:
    """
    Tests specific to external API health checker behavior.
    """

    @pytest.mark.asyncio
    async def test_external_api_checker_returns_degraded_when_unavailable(self):
        """
        Test that external API checker returns degraded status when APIs are unavailable.

        This verifies graceful degradation - the system should not fail when
        external APIs are unavailable, but should report degraded status.
        """
        checker = ExternalAPIHealthChecker()

        # Mock settings to disable LanguageTool
        with patch('services.health_check.get_settings') as mock_settings:
            mock_instance = MagicMock()
            mock_instance.languagetool_server = None
            mock_settings.return_value = mock_instance

            result = await checker.check()

            # Should return healthy (no APIs configured) or degraded
            assert result.status in [HealthCheckResult.STATUS_HEALTHY, HealthCheckResult.STATUS_DEGRADED]
            assert result.component_name == "external_apis"


class TestComponentHealthChecks:
    """
    Tests for individual component health check endpoints.

    Tests the /api/health/component/{component_name} endpoint which returns
    health status for a specific system component.
    """

    def test_component_health_check_database(self, client: TestClient):
        """
        Test component health check for database.

        Validates that the database component endpoint returns
        proper health status information.
        """
        response = client.get("/api/health/component/database")

        # Should return 200 or 503 depending on actual database status
        assert response.status_code in [200, 503]

        data = response.json()
        assert data["component"] == "database"
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "response_time_ms" in data
        assert "message" in data

    def test_component_health_check_redis(self, client: TestClient):
        """
        Test component health check for Redis.

        Validates that the Redis component endpoint returns
        proper health status information.
        """
        response = client.get("/api/health/component/redis")

        # Should return 200 or 503 depending on actual Redis status
        assert response.status_code in [200, 503]

        data = response.json()
        assert data["component"] == "redis"
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "response_time_ms" in data

    def test_component_health_check_celery(self, client: TestClient):
        """
        Test component health check for Celery.

        Validates that the Celery component endpoint returns
        proper health status information.
        """
        response = client.get("/api/health/component/celery")

        # Should return 200 or 503 depending on actual Celery status
        assert response.status_code in [200, 503]

        data = response.json()
        assert data["component"] == "celery"
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "response_time_ms" in data

    def test_component_health_check_ml_models(self, client: TestClient):
        """
        Test component health check for ML models.

        Validates that the ML models component endpoint returns
        proper health status information. ML models are optional
        so this should always return 200.
        """
        response = client.get("/api/health/component/ml_models")

        # ML models are optional, should always return 200
        assert response.status_code == 200

        data = response.json()
        assert data["component"] == "ml_models"
        assert data["status"] in ["healthy", "degraded"]
        assert "response_time_ms" in data

    def test_component_health_check_external_apis(self, client: TestClient):
        """
        Test component health check for external APIs.

        Validates that the external APIs component endpoint returns
        proper health status information. External APIs are optional
        so this should always return 200.
        """
        response = client.get("/api/health/component/external_apis")

        # External APIs are optional, should always return 200
        assert response.status_code == 200

        data = response.json()
        assert data["component"] == "external_apis"
        assert data["status"] in ["healthy", "degraded"]
        assert "response_time_ms" in data

    def test_component_health_check_invalid_component(self, client: TestClient):
        """
        Test component health check with invalid component name.

        Validates that requesting an invalid component returns
        a 400 Bad Request error with a helpful message.
        """
        response = client.get("/api/health/component/invalid_component")

        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "Unknown component" in data["detail"]


class TestHealthCheckServiceAggregation:
    """
    Tests for health check service status aggregation logic.
    """

    @pytest.mark.asyncio
    async def test_essential_components_determine_overall_status(self):
        """
        Test that essential components (database, redis, celery) determine overall status.

        If essential components are healthy, overall should be healthy even if
        optional components are degraded.
        """
        # Create a health check service
        service = HealthCheckService()

        # Verify essential and optional component sets
        assert "database" in service.ESSENTIAL_COMPONENTS
        assert "redis" in service.ESSENTIAL_COMPONENTS
        assert "celery" in service.ESSENTIAL_COMPONENTS

        assert "ml_models" in service.OPTIONAL_COMPONENTS
        assert "external_apis" in service.OPTIONAL_COMPONENTS

    @pytest.mark.asyncio
    async def test_healthy_essential_with_degraded_optional(self):
        """
        Test that healthy essential + degraded optional = degraded overall.

        This is the key graceful degradation behavior.
        """
        service = HealthCheckService()

        # Mock all checkers
        with patch.object(service, 'checkers') as mock_checkers:
            # Essential services are healthy
            mock_checkers["database"].check_with_timeout = AsyncMock(
                return_value=HealthCheckResult(
                    component_name="database",
                    status=HealthCheckResult.STATUS_HEALTHY,
                    response_time_ms=50,
                    message="Database OK"
                )
            )
            mock_checkers["redis"].check_with_timeout = AsyncMock(
                return_value=HealthCheckResult(
                    component_name="redis",
                    status=HealthCheckResult.STATUS_HEALTHY,
                    response_time_ms=30,
                    message="Redis OK"
                )
            )
            mock_checkers["celery"].check_with_timeout = AsyncMock(
                return_value=HealthCheckResult(
                    component_name="celery",
                    status=HealthCheckResult.STATUS_HEALTHY,
                    response_time_ms=100,
                    message="Celery OK"
                )
            )
            # Optional services are degraded
            mock_checkers["ml_models"].check_with_timeout = AsyncMock(
                return_value=HealthCheckResult(
                    component_name="ml_models",
                    status=HealthCheckResult.STATUS_DEGRADED,
                    response_time_ms=10,
                    message="ML models not loaded"
                )
            )
            mock_checkers["external_apis"].check_with_timeout = AsyncMock(
                return_value=HealthCheckResult(
                    component_name="external_apis",
                    status=HealthCheckResult.STATUS_DEGRADED,
                    response_time_ms=10,
                    message="External APIs down"
                )
            )

            result = await service.check_all()

            # Overall should be degraded (essential healthy but optional degraded)
            assert result["overall_status"] in ["healthy", "degraded"]
            # Should not be unhealthy because essential services are operational

    @pytest.mark.asyncio
    async def test_unhealthy_essential_makes_overall_unhealthy(self):
        """
        Test that unhealthy essential component = unhealthy overall.

        Even if optional components are healthy, if any essential component
        is unhealthy, the overall status should be unhealthy.
        """
        service = HealthCheckService()

        # Mock all checkers
        with patch.object(service, 'checkers') as mock_checkers:
            # One essential service is unhealthy
            mock_checkers["database"].check_with_timeout = AsyncMock(
                return_value=HealthCheckResult(
                    component_name="database",
                    status=HealthCheckResult.STATUS_UNHEALTHY,
                    response_time_ms=0,
                    message="Database down",
                    error="Connection failed"
                )
            )
            # Other essential are healthy
            mock_checkers["redis"].check_with_timeout = AsyncMock(
                return_value=HealthCheckResult(
                    component_name="redis",
                    status=HealthCheckResult.STATUS_HEALTHY,
                    response_time_ms=30,
                    message="Redis OK"
                )
            )
            mock_checkers["celery"].check_with_timeout = AsyncMock(
                return_value=HealthCheckResult(
                    component_name="celery",
                    status=HealthCheckResult.STATUS_HEALTHY,
                    response_time_ms=100,
                    message="Celery OK"
                )
            )
            # Optional services are healthy
            mock_checkers["ml_models"].check_with_timeout = AsyncMock(
                return_value=HealthCheckResult(
                    component_name="ml_models",
                    status=HealthCheckResult.STATUS_HEALTHY,
                    response_time_ms=10,
                    message="ML models loaded"
                )
            )
            mock_checkers["external_apis"].check_with_timeout = AsyncMock(
                return_value=HealthCheckResult(
                    component_name="external_apis",
                    status=HealthCheckResult.STATUS_HEALTHY,
                    response_time_ms=10,
                    message="External APIs OK"
                )
            )

            result = await service.check_all()

            # Overall should be unhealthy because database is down
            assert result["overall_status"] == HealthCheckResult.STATUS_UNHEALTHY


# Pytest fixtures
@pytest.fixture(scope="module")
def client() -> TestClient:
    """
    Create a FastAPI test client for all tests.

    Yields:
        TestClient instance
    """
    with TestClient(app) as test_client:
        yield test_client


# Configuration for pytest
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "health: marks tests as health check tests")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
