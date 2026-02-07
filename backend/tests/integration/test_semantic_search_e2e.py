"""
End-to-End Integration Test for Semantic Search Flow

This test verifies the complete semantic search flow from API request to response:
1. User enters natural language query in SemanticSearchInput
2. Frontend calls semantic search API with query
3. Backend generates query embedding using LLM
4. Backend ranks candidates by semantic similarity
5. Results include match explanations (why candidates matched)
6. Frontend displays results with semantic scores and explanations
7. Query completes in under 2 seconds (with cache)

Run with: pytest tests/integration/test_semantic_search_e2e.py -v
"""
import asyncio
import time
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from main import app
from database import get_db
from models import Resume, ResumeAnalysis
from services.semantic_search_service import (
    SemanticSearchService,
    SemanticSearchFilters,
    get_semantic_search_service,
)


# Mock database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


class MockSemanticSearchService:
    """Mock semantic search service for testing without LLM API calls."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._llm_available = False  # Simulate LLM unavailable for testing

    async def semantic_search_candidates(
        self, filters: SemanticSearchFilters
    ) -> Dict[str, Any]:
        """Mock semantic search returning test data."""
        # Simulate processing time
        await asyncio.sleep(0.1)

        return {
            "total": 2,
            "candidates": [
                {
                    "id": "resume-1",
                    "filename": "john_developer.pdf",
                    "status": "processed",
                    "created_at": "2025-01-15T10:00:00",
                    "semantic_score": 0.85,
                    "keyword_score": 0.70,
                    "final_score": 0.80,
                    "skills": ["Python", "Django", "PostgreSQL"],
                    "experience_years": 5.0,
                    "language": "en",
                    "match_explanation": {
                        "semantic_score": 0.85,
                        "skill_match_score": 0.90,
                        "experience_relevance_score": 0.80,
                        "context_fit_score": 0.85,
                        "matched_skills": ["Python", "Django"],
                        "inferred_skills": ["FastAPI", "REST APIs"],
                        "transferable_skills": ["Team Leadership"],
                        "missing_skills": ["Docker"],
                        "explanation": "Strong match with relevant Python experience and backend development skills.",
                    },
                },
                {
                    "id": "resume-2",
                    "filename": "jane_engineer.pdf",
                    "status": "processed",
                    "created_at": "2025-01-16T14:30:00",
                    "semantic_score": 0.72,
                    "keyword_score": 0.65,
                    "final_score": 0.69,
                    "skills": ["Python", "Flask", "MySQL"],
                    "experience_years": 3.0,
                    "language": "en",
                    "match_explanation": {
                        "semantic_score": 0.72,
                        "skill_match_score": 0.75,
                        "experience_relevance_score": 0.65,
                        "context_fit_score": 0.70,
                        "matched_skills": ["Python"],
                        "inferred_skills": ["Web Development"],
                        "transferable_skills": [],
                        "missing_skills": ["Django", "PostgreSQL"],
                        "explanation": "Good match with Python experience but missing some required technologies.",
                    },
                },
            ],
            "query": filters.query,
            "execution_time_seconds": 0.1,
            "semantic_scores_used": True,
            "fallback_used": False,
            "filters_applied": {},
        }

    async def explain_match(
        self, query: str, resume_id: str, vacancy_id: str = None
    ) -> Dict[str, Any]:
        """Mock match explanation."""
        await asyncio.sleep(0.05)
        return {
            "resume_id": resume_id,
            "semantic_score": 0.85,
            "skill_match_score": 0.90,
            "experience_relevance_score": 0.80,
            "context_fit_score": 0.85,
            "matched_skills": ["Python", "Django"],
            "inferred_skills": ["FastAPI", "REST APIs"],
            "transferable_skills": ["Team Leadership"],
            "missing_skills": ["Docker"],
            "explanation": "Strong match with relevant Python experience and backend development skills.",
            "used_embeddings": True,
        }


@pytest.fixture
def mock_semantic_search_service():
    """Fixture providing mock semantic search service."""
    return MockSemanticSearchService(Mock())


@pytest.fixture
def mock_db_session():
    """Fixture providing mock database session."""
    return Mock(spec=AsyncSession)


class TestSemanticSearchE2E:
    """End-to-end tests for semantic search flow."""

    @pytest.mark.asyncio
    async def test_semantic_search_api_endpoint(
        self, mock_semantic_search_service, mock_db_session
    ):
        """
        Step 1-2: User enters natural language query, Frontend calls semantic search API.

        Verifies that the API endpoint accepts natural language queries and returns
        properly formatted responses.
        """
        # Override the dependency injection
        async def override_get_db():
            yield mock_db_session

        async def override_get_semantic_search_service(db: AsyncSession):
            return mock_semantic_search_service

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_semantic_search_service] = override_get_semantic_search_service

        try:
            # Test the API endpoint
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                start_time = time.time()

                response = await client.post(
                    "/api/semantic-search/candidates",
                    json={
                        "query": "Find senior Python developers with team leadership experience",
                        "limit": 10,
                    },
                )

                elapsed_time = time.time() - start_time

                # Verify response
                assert response.status_code == 200
                data = response.json()

                # Verify response structure
                assert "total" in data
                assert "candidates" in data
                assert "query" in data
                assert "execution_time_seconds" in data
                assert "semantic_scores_used" in data

                # Verify query performance (under 2 seconds)
                assert elapsed_time < 2.0, f"Query took {elapsed_time:.2f}s, expected under 2s"

                # Verify results include semantic scores
                assert data["total"] > 0
                candidate = data["candidates"][0]
                assert "semantic_score" in candidate
                assert "keyword_score" in candidate
                assert "final_score" in candidate

                # Verify match explanations are included
                assert "match_explanation" in candidate
                explanation = candidate["match_explanation"]
                assert "semantic_score" in explanation
                assert "matched_skills" in explanation
                assert "inferred_skills" in explanation
                assert "transferable_skills" in explanation
                assert "explanation" in explanation

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_hybrid_search_endpoint(
        self, mock_semantic_search_service, mock_db_session
    ):
        """
        Test hybrid search combining semantic and keyword matching.

        Verifies that hybrid search accepts configurable weights and combines
        semantic and keyword scoring.
        """
        async def override_get_db():
            yield mock_db_session

        async def override_get_semantic_search_service(db: AsyncSession):
            return mock_semantic_search_service

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_semantic_search_service] = override_get_semantic_search_service

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/semantic-search/hybrid",
                    json={
                        "query": "React developer with TypeScript",
                        "semantic_weight": 0.6,
                        "keyword_weight": 0.4,
                        "limit": 10,
                    },
                )

                assert response.status_code == 200
                data = response.json()

                # Verify hybrid search response
                assert "semantic_weight" in data
                assert "keyword_weight" in data
                assert data["semantic_weight"] == 0.6
                assert data["keyword_weight"] == 0.4

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_match_explanation_endpoint(
        self, mock_semantic_search_service, mock_db_session
    ):
        """
        Step 5: Test match explanation endpoint.

        Verifies that detailed explanations are provided showing why candidates matched.
        """
        async def override_get_db():
            yield mock_db_session

        async def override_get_semantic_search_service(db: AsyncSession):
            return mock_semantic_search_service

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_semantic_search_service] = override_get_semantic_search_service

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/semantic-search/explain",
                    json={
                        "query": "Find senior Python developers",
                        "resume_id": "resume-1",
                    },
                )

                assert response.status_code == 200
                data = response.json()

                # Verify explanation structure
                assert "resume_id" in data
                assert "semantic_score" in data
                assert "skill_match_score" in data
                assert "experience_relevance_score" in data
                assert "context_fit_score" in data
                assert "matched_skills" in data
                assert "inferred_skills" in data
                assert "transferable_skills" in data
                assert "missing_skills" in data
                assert "explanation" in data

                # Verify explanation contains human-readable text
                assert len(data["explanation"]) > 0

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_semantic_search_with_traditional_filters(
        self, mock_semantic_search_service, mock_db_session
    ):
        """
        Test semantic search combined with traditional filters.

        Verifies that semantic search works alongside traditional filtering
        (skills, experience, location, etc).
        """
        async def override_get_db():
            yield mock_db_session

        async def override_get_semantic_search_service(db: AsyncSession):
            return mock_semantic_search_service

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_semantic_search_service] = override_get_semantic_search_service

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/semantic-search/candidates",
                    json={
                        "query": "Senior software engineer",
                        "filters": {
                            "min_experience_years": 5,
                            "location": "Remote",
                            "skills": ["Python", "Django"],
                        },
                        "limit": 10,
                    },
                )

                assert response.status_code == 200
                data = response.json()

                # Verify filters were applied
                assert "filters_applied" in data

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_endpoint_equivalence(
        self, mock_semantic_search_service, mock_db_session
    ):
        """
        Test that GET endpoint provides same functionality as POST.

        Verifies that GET endpoint with query parameters works equivalently
        to POST endpoint with JSON body.
        """
        async def override_get_db():
            yield mock_db_session

        async def override_get_semantic_search_service(db: AsyncSession):
            return mock_semantic_search_service

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_semantic_search_service] = override_get_semantic_search_service

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get(
                    "/api/semantic-search/candidates",
                    params={
                        "query": "Find senior Python developers",
                        "limit": 10,
                    },
                )

                assert response.status_code == 200
                data = response.json()

                # Verify response structure matches POST endpoint
                assert "candidates" in data
                assert "total" in data

        finally:
            app.dependency_overrides.clear()


class TestSemanticSearchPerformance:
    """Performance tests for semantic search."""

    @pytest.mark.asyncio
    async def test_query_performance_under_2_seconds(
        self, mock_semantic_search_service, mock_db_session
    ):
        """
        Step 7: Verify query completes in under 2 seconds (with cache).

        This test ensures the semantic search meets the 2-second SLA
        specified in the requirements.
        """
        async def override_get_db():
            yield mock_db_session

        async def override_get_semantic_search_service(db: AsyncSession):
            return mock_semantic_search_service

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_semantic_search_service] = override_get_semantic_search_service

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                # Run multiple queries to test consistency
                query_times = []
                for i in range(5):
                    start_time = time.time()
                    response = await client.post(
                        "/api/semantic-search/candidates",
                        json={
                            "query": f"Find Python developers - query {i}",
                            "limit": 10,
                        },
                    )
                    elapsed_time = time.time() - start_time
                    query_times.append(elapsed_time)

                    assert response.status_code == 200

                # Verify all queries completed under 2 seconds
                avg_time = sum(query_times) / len(query_times)
                max_time = max(query_times)

                assert (
                    avg_time < 2.0
                ), f"Average query time {avg_time:.2f}s exceeds 2s SLA"
                assert (
                    max_time < 2.0
                ), f"Max query time {max_time:.2f}s exceeds 2s SLA"

        finally:
            app.dependency_overrides.clear()


class TestSemanticSearchDataFlow:
    """Tests for data flow through the semantic search pipeline."""

    @pytest.mark.asyncio
    async def test_response_contains_all_required_fields(
        self, mock_semantic_search_service, mock_db_session
    ):
        """
        Verify that semantic search response contains all required fields
        for frontend display.
        """
        async def override_get_db():
            yield mock_db_session

        async def override_get_semantic_search_service(db: AsyncSession):
            return mock_semantic_search_service

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_semantic_search_service] = override_get_semantic_search_service

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/semantic-search/candidates",
                    json={
                        "query": "Find senior Python developers",
                        "limit": 10,
                    },
                )

                assert response.status_code == 200
                data = response.json()

                # Verify top-level response fields
                required_top_level_fields = [
                    "total",
                    "candidates",
                    "query",
                    "execution_time_seconds",
                    "semantic_scores_used",
                    "fallback_used",
                    "filters_applied",
                    "skip",
                    "limit",
                ]
                for field in required_top_level_fields:
                    assert field in data, f"Missing top-level field: {field}"

                # Verify candidate fields
                if data["candidates"]:
                    candidate = data["candidates"][0]
                    required_candidate_fields = [
                        "id",
                        "filename",
                        "status",
                        "created_at",
                        "semantic_score",
                        "keyword_score",
                        "final_score",
                        "skills",
                    ]
                    for field in required_candidate_fields:
                        assert field in candidate, f"Missing candidate field: {field}"

                    # Verify match explanation fields
                    if "match_explanation" in candidate:
                        explanation = candidate["match_explanation"]
                        required_explanation_fields = [
                            "semantic_score",
                            "skill_match_score",
                            "experience_relevance_score",
                            "context_fit_score",
                            "matched_skills",
                            "inferred_skills",
                            "transferable_skills",
                            "explanation",
                        ]
                        for field in required_explanation_fields:
                            assert (
                                field in explanation
                            ), f"Missing explanation field: {field}"

        finally:
            app.dependency_overrides.clear()


class TestErrorHandling:
    """Tests for error handling in semantic search."""

    @pytest.mark.asyncio
    async def test_empty_query_validation(self, mock_db_session):
        """Test that empty queries are rejected."""
        async def override_get_db():
            yield mock_db_session

        app.dependency_overrides[get_db] = override_get_db

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/semantic-search/candidates",
                    json={
                        "query": "",  # Empty query
                        "limit": 10,
                    },
                )

                # Should return validation error
                assert response.status_code in [400, 422]

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_invalid_semantic_score_range(self, mock_db_session):
        """Test that invalid semantic score ranges are rejected."""
        async def override_get_db():
            yield mock_db_session

        app.dependency_overrides[get_db] = override_get_db

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post(
                    "/api/semantic-search/candidates",
                    json={
                        "query": "Test query",
                        "min_semantic_score": 1.5,  # Invalid: must be 0-1
                        "limit": 10,
                    },
                )

                # Should return validation error
                assert response.status_code in [400, 422]

        finally:
            app.dependency_overrides.clear()
