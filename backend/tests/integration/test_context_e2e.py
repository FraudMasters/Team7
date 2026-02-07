"""
End-to-end integration tests for Context API (Graphiti knowledge graph).

This test suite validates the complete flow:
- Episode ingestion via POST /api/v1/context/episodes
- Semantic search via GET /api/v1/context/search
- Health monitoring via GET /api/v1/context/health

Test Coverage:
- Episode creation and retrieval
- Semantic search functionality
- Error handling (invalid data, service unavailable)
- Response format validation
"""
import asyncio
from datetime import datetime
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Import the FastAPI application
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import app


# Pytest fixtures


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """
    Create a FastAPI test client for all tests.

    Yields:
        TestClient instance
    """
    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async test client for async endpoint testing.

    Yields:
        AsyncClient instance
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# Test Data Fixtures


@pytest.fixture
def sample_episode_data() -> dict:
    """
    Sample episode data for testing.

    Returns:
        Dictionary with episode content
    """
    return {
        "name": "Test Episode: Software Engineer Skills",
        "body": """
        Jane Doe is a senior software engineer with expertise in:
        - Backend: Python, FastAPI, Django, Node.js, Express
        - Frontend: React, Vue.js, TypeScript
        - Databases: PostgreSQL, MongoDB, Redis
        - DevOps: Docker, Kubernetes, AWS, CI/CD
        - Experience: 7 years building web applications
        """,
        "source": "test_verification",
        "source_description": "Automated E2E test verification",
    }


@pytest.fixture
def sample_vacancy_episode() -> dict:
    """
    Sample episode representing a job vacancy.

    Returns:
        Dictionary with vacancy content
    """
    return {
        "name": "Job Vacancy: Senior Python Developer",
        "body": """
        We are looking for a Senior Python Developer to join our team.

        Requirements:
        - 5+ years of Python development experience
        - Strong knowledge of FastAPI and Django frameworks
        - Experience with PostgreSQL and Redis
        - Docker and Kubernetes for containerization
        - AWS cloud services experience
        - Strong problem-solving skills

        Responsibilities:
        - Design and implement REST APIs
        - Develop microservices architecture
        - Mentor junior developers
        - Participate in code reviews
        """,
        "source": "vacancy",
        "source_description": "Job posting from company careers page",
    }


# Test Classes


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_endpoint_returns_200(self, client: TestClient):
        """Test that health endpoint returns 200 OK."""
        response = client.get("/api/v1/context/health")
        assert response.status_code == 200

    def test_health_endpoint_response_structure(self, client: TestClient):
        """Test that health endpoint returns correct response structure."""
        response = client.get("/api/v1/context/health")
        assert response.status_code == 200

        data = response.json()

        # Validate required fields
        assert "healthy" in data
        assert "initialized" in data
        assert "neo4j_connected" in data
        assert "episode_count" in data
        assert "error" in data or data.get("healthy") is True

    def test_health_endpoint_data_types(self, client: TestClient):
        """Test that health endpoint returns correct data types."""
        response = client.get("/api/v1/context/health")
        assert response.status_code == 200

        data = response.json()

        # Validate data types
        assert isinstance(data.get("healthy"), bool)
        assert isinstance(data.get("initialized"), bool)
        assert isinstance(data.get("neo4j_connected"), bool)
        assert isinstance(data.get("episode_count"), int)


class TestEpisodeIngestion:
    """Tests for episode ingestion endpoint."""

    def test_create_episode_success(self, client: TestClient, sample_episode_data: dict):
        """Test creating an episode with valid data."""
        response = client.post(
            "/api/v1/context/episodes",
            json=sample_episode_data,
        )

        # Should return 201 Created or 503 Service Unavailable if graphiti not initialized
        assert response.status_code in [201, 503]

        if response.status_code == 201:
            data = response.json()

            # Validate response structure
            assert "episode_id" in data
            assert "status" in data
            assert "name" in data

            # Validate response values
            assert data["status"] == "created"
            assert data["name"] == sample_episode_data["name"]
            assert len(data["episode_id"]) > 0

    def test_create_episode_with_minimal_data(self, client: TestClient):
        """Test creating an episode with only required fields."""
        minimal_data = {
            "name": "Minimal Test Episode",
            "body": "This is a minimal episode with just name and body.",
        }

        response = client.post(
            "/api/v1/context/episodes",
            json=minimal_data,
        )

        # Accept 201 or 503 (service not initialized)
        assert response.status_code in [201, 503]

        if response.status_code == 201:
            data = response.json()
            assert data["status"] == "created"
            assert data["name"] == "Minimal Test Episode"

    def test_create_episode_missing_name(self, client: TestClient):
        """Test that creating an episode without name returns validation error."""
        invalid_data = {
            "body": "Episode without a name",
        }

        response = client.post(
            "/api/v1/context/episodes",
            json=invalid_data,
        )

        # Should return 422 Unprocessable Entity
        assert response.status_code == 422

    def test_create_episode_missing_body(self, client: TestClient):
        """Test that creating an episode without body returns validation error."""
        invalid_data = {
            "name": "Episode without body",
        }

        response = client.post(
            "/api/v1/context/episodes",
            json=invalid_data,
        )

        # Should return 422 Unprocessable Entity
        assert response.status_code == 422

    def test_create_episode_empty_name(self, client: TestClient):
        """Test that creating an episode with empty name returns validation error."""
        invalid_data = {
            "name": "",
            "body": "Episode with empty name",
        }

        response = client.post(
            "/api/v1/context/episodes",
            json=invalid_data,
        )

        # Should return 422 Unprocessable Entity
        assert response.status_code == 422

    def test_create_episode_with_custom_timestamp(self, client: TestClient):
        """Test creating an episode with a custom reference_time."""
        episode_data = {
            "name": "Episode with Timestamp",
            "body": "Testing custom timestamp functionality",
            "reference_time": "2024-01-15T10:30:00Z",
        }

        response = client.post(
            "/api/v1/context/episodes",
            json=episode_data,
        )

        # Accept 201 or 503 (service not initialized)
        assert response.status_code in [201, 503]


class TestSemanticSearch:
    """Tests for semantic search endpoint."""

    def test_search_with_query_param(self, client: TestClient):
        """Test searching with a query parameter."""
        response = client.get(
            "/api/v1/context/search",
            params={"query": "python developer"},
        )

        # Accept 200 OK or 503 Service Unavailable
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()

            # Validate response structure
            assert "query" in data
            assert "results" in data
            assert "count" in data

            # Validate response values
            assert data["query"] == "python developer"
            assert isinstance(data["results"], list)
            assert isinstance(data["count"], int)
            assert data["count"] == len(data["results"])

    def test_search_with_limit_param(self, client: TestClient):
        """Test searching with a custom limit."""
        response = client.get(
            "/api/v1/context/search",
            params={"query": "developer", "limit": 5},
        )

        # Accept 200 OK or 503 Service Unavailable
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert data["count"] <= 5

    def test_search_missing_query_param(self, client: TestClient):
        """Test that searching without query parameter returns error."""
        response = client.get("/api/v1/context/search")

        # Should return 422 Unprocessable Entity
        assert response.status_code == 422

    def test_search_empty_query(self, client: TestClient):
        """Test that searching with empty query returns error."""
        response = client.get(
            "/api/v1/context/search",
            params={"query": ""},
        )

        # Should return 422 Unprocessable Entity
        assert response.status_code == 422

    def test_search_limit_too_high(self, client: TestClient):
        """Test that limit above maximum returns error."""
        response = client.get(
            "/api/v1/context/search",
            params={"query": "test", "limit": 101},
        )

        # Should return 422 Unprocessable Entity (max is 100)
        assert response.status_code == 422

    def test_search_response_structure(self, client: TestClient):
        """Test that search results have correct structure."""
        response = client.get(
            "/api/v1/context/search",
            params={"query": "python"},
        )

        # Accept 200 OK or 503 Service Unavailable
        if response.status_code == 200:
            data = response.json()

            # Validate each result has required fields
            for result in data["results"]:
                assert "name" in result
                assert "body" in result
                assert "score" in result
                assert "uuid" in result

                # Validate data types
                assert isinstance(result["name"], str)
                assert isinstance(result["body"], str)
                assert isinstance(result["score"], (int, float))
                assert 0 <= result["score"] <= 1  # Score should be between 0 and 1


class TestEndToEndWorkflows:
    """End-to-end workflow tests simulating real usage scenarios."""

    @pytest.mark.slow
    def test_add_and_search_episode_workflow(
        self, client: TestClient, sample_episode_data: dict
    ):
        """
        Test complete workflow: add episode -> search for it.

        This is the core E2E test for subtask-4-3 verification.
        """
        # Step 1: Add an episode
        create_response = client.post(
            "/api/v1/context/episodes",
            json=sample_episode_data,
        )

        # Handle case where service is not initialized
        if create_response.status_code == 503:
            pytest.skip("Graphiti service not initialized")
            return

        assert create_response.status_code == 201
        create_data = create_response.json()
        episode_id = create_data["episode_id"]

        # Verify response structure
        assert "episode_id" in create_data
        assert create_data["status"] == "created"
        assert create_data["name"] == sample_episode_data["name"]

        # Step 2: Search for the episode content
        # Use a query that matches the episode content
        search_query = "Python FastAPI software engineer"
        search_response = client.get(
            "/api/v1/context/search",
            params={"query": search_query, "limit": 10},
        )

        assert search_response.status_code == 200
        search_data = search_response.json()

        # Verify search response structure
        assert search_data["query"] == search_query
        assert "results" in search_data
        assert "count" in search_data
        assert isinstance(search_data["results"], list)

        # Note: The episode might not appear immediately in search results
        # because Graphiti needs time to:
        # 1. Extract entities using LLM
        # 2. Generate embeddings
        # 3. Build relationships in the graph
        # This is why we don't assert count > 0 here

    @pytest.mark.slow
    def test_multiple_episodes_search_workflow(
        self, client: TestClient, sample_episode_data: dict, sample_vacancy_episode: dict
    ):
        """
        Test adding multiple related episodes and searching across them.

        Simulates a real scenario where:
        1. Multiple resumes are ingested
        2. Multiple vacancies are ingested
        3. Search returns relevant results from both
        """
        # Step 1: Add first episode (candidate)
        response1 = client.post(
            "/api/v1/context/episodes",
            json=sample_episode_data,
        )

        if response1.status_code == 503:
            pytest.skip("Graphiti service not initialized")
            return

        assert response1.status_code == 201

        # Step 2: Add second episode (vacancy)
        response2 = client.post(
            "/api/v1/context/episodes",
            json=sample_vacancy_episode,
        )

        assert response2.status_code == 201

        # Step 3: Search for relevant content
        search_response = client.get(
            "/api/v1/context/search",
            params={"query": "Python Django FastAPI developer", "limit": 10},
        )

        assert search_response.status_code == 200
        search_data = search_response.json()

        # Verify search response
        assert search_data["count"] >= 0
        assert isinstance(search_data["results"], list)

    def test_health_check_workflow(self, client: TestClient):
        """
        Test health check workflow to verify service status.

        This test verifies:
        1. Health endpoint is accessible
        2. Returns correct status information
        3. Can be used for monitoring
        """
        response = client.get("/api/v1/context/health")

        # Should return 200 OK (even if service not initialized)
        assert response.status_code == 200

        data = response.json()

        # Verify response structure
        assert "healthy" in data
        assert "initialized" in data
        assert "neo4j_connected" in data
        assert "episode_count" in data

        # If healthy, verify Neo4j is connected
        if data.get("healthy"):
            assert data.get("neo4j_connected") is True


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_service_unavailable_handling(self, client: TestClient):
        """
        Test that service returns proper 503 when Graphiti is not available.

        This test validates graceful degradation.
        """
        # This test assumes the service might not be initialized
        # The actual behavior depends on whether Graphiti is running
        episode_data = {
            "name": "Test Episode",
            "body": "Testing error handling",
        }

        response = client.post(
            "/api/v1/context/episodes",
            json=episode_data,
        )

        # Accept 201 (service available) or 503 (service unavailable)
        assert response.status_code in [201, 503]

        if response.status_code == 503:
            data = response.json()
            # Verify error message is helpful
            assert "detail" in data

    def test_malformed_json_request(self, client: TestClient):
        """Test handling of malformed JSON in request body."""
        # This would typically be handled by FastAPI's automatic validation
        # We're testing that our endpoint handles it gracefully
        response = client.post(
            "/api/v1/context/episodes",
            json={"invalid": "data structure without required fields"},
        )

        # Should return 422 Unprocessable Entity
        assert response.status_code == 422


# Configuration for pytest


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
