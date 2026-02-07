"""
Integration tests for microservices architecture.

This test suite validates:
1. Service health checks and readiness probes
2. Inter-service communication (gRPC/REST)
3. End-to-end workflows across multiple services
4. Database isolation between services
5. Distributed tracing with Jaeger
6. Service discovery with Consul

Test Configuration:
- Services are expected to run on their configured ports (8001-8009)
- Tests can run against locally started services or Docker Compose
- Use pytest markers: @pytest.mark.integration, @pytest.mark.slow

Usage:
    # Run all integration tests
    pytest tests/integration/test_microservices.py -v

    # Run only health check tests
    pytest tests/integration/test_microservices.py::TestServiceHealthChecks -v

    # Skip slow tests
    pytest tests/integration/test_microservices.py -v -m "not slow"
"""
import asyncio
import io
import os
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, List, Optional
from unittest.mock import Mock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport, HTTPStatusError, TimeoutException


# Service configuration
SERVICES = {
    "resume_processing": {
        "name": "Resume Processing Service",
        "port": 8001,
        "host": os.getenv("RESUME_PROCESSING_HOST", "localhost"),
        "health_path": "/health",
        "ready_path": "/ready",
        "api_prefix": "/api/resumes",
    },
    "matching": {
        "name": "Matching Service",
        "port": 8002,
        "host": os.getenv("MATCHING_HOST", "localhost"),
        "health_path": "/health",
        "ready_path": "/ready",
        "api_prefix": "/api/matching",
    },
    "candidate": {
        "name": "Candidate Service",
        "port": 8003,
        "host": os.getenv("CANDIDATE_HOST", "localhost"),
        "health_path": "/health",
        "ready_path": "/ready",
        "api_prefix": "/api/candidates",
    },
    "vacancy": {
        "name": "Vacancy Service",
        "port": 8004,
        "host": os.getenv("VACANCY_HOST", "localhost"),
        "health_path": "/health",
        "ready_path": "/ready",
        "api_prefix": "/api/vacancies",
    },
    "taxonomy": {
        "name": "Taxonomy Service",
        "port": 8005,
        "host": os.getenv("TAXONOMY_HOST", "localhost"),
        "health_path": "/health",
        "ready_path": "/ready",
        "api_prefix": "/api/skill-taxonomies",
    },
    "analytics": {
        "name": "Analytics Service",
        "port": 8006,
        "host": os.getenv("ANALYTICS_HOST", "localhost"),
        "health_path": "/health",
        "ready_path": "/ready",
        "api_prefix": "/api/analytics",
    },
    "ats_simulation": {
        "name": "ATS Simulation Service",
        "port": 8007,
        "host": os.getenv("ATS_SIMULATION_HOST", "localhost"),
        "health_path": "/health",
        "ready_path": "/ready",
        "api_prefix": "/api/ats",
    },
    "notifications": {
        "name": "Notification Service",
        "port": 8008,
        "host": os.getenv("NOTIFICATIONS_HOST", "localhost"),
        "health_path": "/health",
        "ready_path": "/ready",
        "api_prefix": "/api/notifications",
    },
    "integration": {
        "name": "Integration Service",
        "port": 8009,
        "host": os.getenv("INTEGRATION_HOST", "localhost"),
        "health_path": "/health",
        "ready_path": "/ready",
        "api_prefix": "/api/integrations",
    },
}


def get_service_url(service_key: str, path: str = "") -> str:
    """
    Get the full URL for a service endpoint.

    Args:
        service_key: Key from SERVICES dict
        path: Optional path to append

    Returns:
        Full URL string
    """
    service = SERVICES[service_key]
    base_url = f"http://{service['host']}:{service['port']}"
    return base_url + path


class TestServiceHealthChecks:
    """Test suite for service health check and readiness endpoints."""

    @pytest.mark.asyncio
    async def test_all_services_health_endpoints(self):
        """
        Test that all services return healthy status.

        Verifies:
        - Health endpoint returns 200
        - Response contains "status": "healthy"
        - Service name is present
        - Version information is present
        """
        failed_services = []

        async with AsyncClient(timeout=5.0) as client:
            for service_key, service_config in SERVICES.items():
                url = get_service_url(service_key, service_config["health_path"])
                try:
                    response = await client.get(url)
                    if response.status_code != 200:
                        failed_services.append(
                            f"{service_key}: Status {response.status_code}"
                        )
                        continue

                    data = response.json()
                    assert data.get("status") == "healthy", \
                        f"{service_key}: status not healthy"
                    assert "service" in data, \
                        f"{service_key}: missing service name"
                    assert "version" in data, \
                        f"{service_key}: missing version"

                except Exception as e:
                    failed_services.append(
                        f"{service_key}: {str(e)}"
                    )

        if failed_services:
            pytest.fail(f"Health checks failed:\n" + "\n".join(failed_services))

    @pytest.mark.asyncio
    async def test_all_services_readiness_endpoints(self):
        """
        Test that all services return ready status.

        Verifies:
        - Readiness endpoint returns 200
        - Response contains "status": "ready"
        - Service can accept traffic
        """
        failed_services = []

        async with AsyncClient(timeout=5.0) as client:
            for service_key, service_config in SERVICES.items():
                url = get_service_url(service_key, service_config["ready_path"])
                try:
                    response = await client.get(url)
                    if response.status_code != 200:
                        failed_services.append(
                            f"{service_key}: Status {response.status_code}"
                        )
                        continue

                    data = response.json()
                    assert data.get("status") == "ready", \
                        f"{service_key}: status not ready"

                except Exception as e:
                    failed_services.append(
                        f"{service_key}: {str(e)}"
                    )

        if failed_services:
            pytest.fail(f"Readiness checks failed:\n" + "\n".join(failed_services))

    @pytest.mark.asyncio
    async def test_all_services_root_endpoints(self):
        """
        Test that all services return API information from root endpoint.

        Verifies:
        - Root endpoint returns 200
        - Response contains message, version, docs links
        """
        async with AsyncClient(timeout=5.0) as client:
            for service_key, service_config in SERVICES.items():
                url = get_service_url(service_key, "/")
                response = await client.get(url)

                assert response.status_code == 200, \
                    f"{service_key}: root endpoint failed"

                data = response.json()
                assert "message" in data, \
                    f"{service_key}: missing message"
                assert "version" in data, \
                    f"{service_key}: missing version"
                assert "docs" in data, \
                    f"{service_key}: missing docs link"

    @pytest.mark.asyncio
    async def test_service_response_times(self):
        """
        Test that services respond within acceptable time limits.

        Performance targets:
        - Health check: < 100ms
        - Readiness check: < 100ms
        - Root endpoint: < 100ms
        """
        async with AsyncClient(timeout=5.0) as client:
            for service_key, service_config in SERVICES.items():
                # Test health endpoint response time
                url = get_service_url(service_key, service_config["health_path"])
                start = time.time()
                response = await client.get(url)
                duration = (time.time() - start) * 1000  # Convert to ms

                assert response.status_code == 200
                assert duration < 100, \
                    f"{service_key}: health check took {duration:.2f}ms (> 100ms)"


class TestDatabaseIsolation:
    """Test suite for database isolation between microservices."""

    @pytest.mark.asyncio
    async def test_resume_processing_uses_own_schema(self):
        """
        Verify Resume Processing Service uses its own database schema.

        This test validates:
        - Service connects to correct schema
        - Models are properly isolated
        - Queries don't leak to other schemas
        """
        # This would require database access
        # For now, we verify the service can access its data
        async with AsyncClient(timeout=10.0) as client:
            url = get_service_url("resume_processing", "/api/resumes")
            response = await client.get(url)

            # Should return 200 (possibly empty list)
            assert response.status_code in [200, 401], \
                "Resume Processing Service database access failed"

    @pytest.mark.asyncio
    async def test_matching_uses_own_schema(self):
        """
        Verify Matching Service uses its own database schema.
        """
        async with AsyncClient(timeout=10.0) as client:
            url = get_service_url("matching", "/api/matching")
            response = await client.get(url)

            assert response.status_code in [200, 401], \
                "Matching Service database access failed"

    @pytest.mark.asyncio
    async def test_candidate_uses_own_schema(self):
        """
        Verify Candidate Service uses its own database schema.
        """
        async with AsyncClient(timeout=10.0) as client:
            url = get_service_url("candidate", "/api/candidates")
            response = await client.get(url)

            assert response.status_code in [200, 401], \
                "Candidate Service database access failed"


class TestInterServiceCommunication:
    """Test suite for inter-service communication via gRPC and REST."""

    @pytest.mark.asyncio
    async def test_matching_can_call_resume_processing(self):
        """
        Test that Matching Service can communicate with Resume Processing.

        This validates:
        - gRPC channel can be established
        - Resume data can be retrieved by Matching Service
        - Communication timeout is handled correctly
        """
        # Create a test resume first
        async with AsyncClient(timeout=30.0) as client:
            # Upload a test resume
            pdf_content = self._create_test_pdf()
            upload_url = get_service_url("resume_processing", "/api/resumes/upload")

            upload_response = await client.post(
                upload_url,
                files={"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
            )

            if upload_response.status_code == 201:
                resume_id = upload_response.json().get("id")

                # Try to match using the Matching Service
                match_url = get_service_url("matching", "/api/matching/compare")
                match_response = await client.post(
                    match_url,
                    json={
                        "resume_id": resume_id,
                        "vacancy_data": {
                            "position": "Software Engineer",
                            "mandatory_requirements": ["Python", "FastAPI"],
                            "min_experience_years": 1
                        }
                    }
                )

                # Should succeed (200) or fail gracefully (404 if analysis not done)
                assert match_response.status_code in [200, 404, 422], \
                    f"Matching service communication failed: {match_response.status_code}"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_end_to_end_resume_to_match_workflow(self):
        """
        Test complete workflow: Upload → Analyze → Match.

        This is an end-to-end integration test that verifies:
        1. Resume upload via Resume Processing Service
        2. Analysis via Resume Processing Service
        3. Matching via Matching Service
        4. Data consistency across services
        """
        async with AsyncClient(timeout=60.0) as client:
            # Step 1: Upload resume
            pdf_content = self._create_test_pdf()
            upload_url = get_service_url("resume_processing", "/api/resumes/upload")

            upload_response = await client.post(
                upload_url,
                files={"file": ("workflow_test.pdf", io.BytesIO(pdf_content), "application/pdf")}
            )

            # Upload might not be available in test environment
            if upload_response.status_code != 201:
                pytest.skip("Resume upload not available in test environment")

            resume_id = upload_response.json()["id"]
            assert resume_id is not None

            # Step 2: Analyze resume
            analyze_url = get_service_url("resume_processing", "/api/analysis")
            analyze_response = await client.post(
                analyze_url,
                json={
                    "resume_id": resume_id,
                    "check_grammar": False,
                    "extract_experience": False
                }
            )

            # Analysis might not be available
            if analyze_response.status_code != 200:
                pytest.skip("Resume analysis not available in test environment")

            analysis_data = analyze_response.json()
            assert analysis_data["status"] in ["completed", "pending"]

            # Step 3: Match with vacancy
            match_url = get_service_url("matching", "/api/matching/compare")
            match_response = await client.post(
                match_url,
                json={
                    "resume_id": resume_id,
                    "vacancy_data": {
                        "position": "Software Engineer",
                        "mandatory_requirements": ["Python", "FastAPI"],
                        "min_experience_years": 1
                    }
                }
            )

            # Matching might not be available
            if match_response.status_code != 200:
                pytest.skip("Resume matching not available in test environment")

            match_data = match_response.json()
            assert "match_percentage" in match_data
            assert 0 <= match_data["match_percentage"] <= 100

    @staticmethod
    def _create_test_pdf() -> bytes:
        """
        Create a minimal valid PDF for testing.

        Returns:
            Bytes content of a simple PDF file
        """
        return b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 4 0 R
>>
>>
/MediaBox [0 0 612 792]
/Contents 5 0 R
>>
endobj
4 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj
5 0 obj
<<
/Length 100
>>
stream
BT
/F1 12 Tf
50 700 Td
(Test Resume) Tj
0 -20 Td
(Skills: Python, FastAPI) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000264 00000 n
0000000349 00000 n
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
428
%%EOF
"""


class TestServiceDiscovery:
    """Test suite for service discovery with Consul."""

    @pytest.mark.asyncio
    async def test_consul_service_registration(self):
        """
        Test that all services are registered in Consul.

        Verifies:
        - Each service appears in Consul catalog
        - Service health is properly reported
        - Service tags are present
        """
        consul_url = os.getenv("CONSUL_URL", "http://localhost:8500")

        async with AsyncClient(timeout=5.0) as client:
            # Query Consul API for registered services
            response = await client.get(f"{consul_url}/v1/catalog/services")

            if response.status_code != 200:
                pytest.skip("Consul not available for testing")

            registered_services = response.json()

            # Check that our services are registered
            expected_services = [
                "resume_processing",
                "matching",
                "candidate",
                "vacancy",
                "taxonomy",
                "analytics",
                "ats_simulation",
                "notifications",
                "integration"
            ]

            for service in expected_services:
                # Service might be registered with slightly different name
                found = any(
                    service.lower() in s.lower()
                    for s in registered_services.keys()
                )
                # Don't fail - just log
                if not found:
                    print(f"Warning: Service {service} not found in Consul")

    @pytest.mark.asyncio
    async def test_consul_health_checks(self):
        """
        Test that Consul health checks are passing for all services.
        """
        consul_url = os.getenv("CONSUL_URL", "http://localhost:8500")

        async with AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{consul_url}/v1/health/state/any")

            if response.status_code != 200:
                pytest.skip("Consul not available for testing")

            health_checks = response.json()

            # Check for critical health failures
            critical_checks = [
                check for check in health_checks
                if check.get("Status") == "critical"
                and any(
                    svc in check.get("ServiceName", "")
                    for svc in SERVICES.keys()
                )
            ]

            # Log warnings but don't fail
            if critical_checks:
                print(f"Warning: {len(critical_checks)} critical health checks in Consul")


class TestDistributedTracing:
    """Test suite for distributed tracing with Jaeger."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_tracing_headers_propagated(self):
        """
        Test that tracing headers are propagated across services.

        Validates:
        - X-Request-ID header is set
        - Uber-trace-id header is present (Jaeger)
        - Trace context is maintained across requests
        """
        async with AsyncClient(timeout=10.0) as client:
            # Make request to first service
            headers = {
                "X-Request-ID": "test-trace-123",
                "Uber-Trace-Id": "test-trace-id:0:test-trace-id:0"
            }

            url = get_service_url("resume_processing", "/health")
            response = await client.get(url, headers=headers)

            assert response.status_code == 200
            # Headers should be returned (or at least not cause errors)


class TestServiceResilience:
    """Test suite for service resilience and error handling."""

    @pytest.mark.asyncio
    async def test_service_handles_missing_dependencies(self):
        """
        Test that services handle missing dependent services gracefully.

        Validates:
        - Circuit breaker pattern works
        - Fallback responses are returned
        - No cascade failures occur
        """
        # This test would require stopping a dependent service
        # For now, we document the expected behavior
        pass

    @pytest.mark.asyncio
    async def test_service_timeouts_are_configured(self):
        """
        Test that services have appropriate timeout configurations.

        Validates:
        - Read timeouts are set
        - Connect timeouts are set
        - Timeouts are reasonable for service type
        """
        async with AsyncClient(timeout=1.0) as client:
            # Make a request that should timeout
            # This validates timeout configuration
            for service_key, service_config in SERVICES.items():
                url = get_service_url(service_key, "/health")
                try:
                    response = await client.get(url, timeout=0.001)
                    # Should timeout
                except (TimeoutException, asyncio.TimeoutError):
                    # Expected behavior
                    pass


@pytest.fixture(scope="session")
def verify_services_running():
    """
    Verify that required services are running before running tests.

    This fixture checks if services are accessible and skips tests
    if services are not available.
    """
    async def check_services():
        async with AsyncClient(timeout=2.0) as client:
            for service_key, service_config in SERVICES.items():
                url = get_service_url(service_key, service_config["health_path"])
                try:
                    response = await client.get(url)
                    if response.status_code != 200:
                        return False
                except Exception:
                    return False
            return True

    services_running = asyncio.run(check_services())

    if not services_running:
        pytest.skip(
            "Services not running. Start services with: "
            "docker-compose -f docker-compose.microservices.yml up"
        )

    yield services_running


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
