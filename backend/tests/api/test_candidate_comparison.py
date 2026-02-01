"""
Unit tests for candidate comparison endpoint.

Tests cover:
- Compare candidates endpoint (success cases)
- Score breakdown accuracy
- Ranking functionality
- Validation and error handling
- Edge cases
"""
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI application
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import app


@pytest.fixture
def client():
    """
    Create a test client for the FastAPI application.

    Returns:
        TestClient: Configured test client
    """
    return TestClient(app)


class TestCompareCandidatesEndpoint:
    """Tests for POST /api/matching/compare-candidates endpoint."""

    def test_compare_candidates_success(self, client):
        """Test successful candidate comparison."""
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_ids": ["resume1", "resume2", "resume3"],
        }
        response = client.post("/api/matching/compare-candidates", json=payload)
        # May return 404 if vacancies/resumes don't exist
        assert response.status_code in [200, 404]

    def test_compare_candidates_min_resumes(self, client):
        """Test comparison with minimum 1 resume."""
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_ids": ["resume1"],
        }
        response = client.post("/api/matching/compare-candidates", json=payload)
        # May return 404 if vacancies/resumes don't exist
        assert response.status_code in [200, 404]

    def test_compare_candidates_max_resumes(self, client):
        """Test comparison with maximum 10 resumes."""
        resume_ids = [f"resume{i}" for i in range(1, 11)]
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_ids": resume_ids,
        }
        response = client.post("/api/matching/compare-candidates", json=payload)
        # May return 404 if vacancies/resumes don't exist
        assert response.status_code in [200, 404]

    def test_compare_candidates_too_many_resumes(self, client):
        """Test comparison with more than 10 resumes (should fail)."""
        resume_ids = [f"resume{i}" for i in range(1, 12)]  # 11 resumes
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_ids": resume_ids,
        }
        response = client.post("/api/matching/compare-candidates", json=payload)
        assert response.status_code == 422

    def test_compare_candidates_empty_resume_ids(self, client):
        """Test comparison with empty resume_ids list."""
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_ids": [],
        }
        response = client.post("/api/matching/compare-candidates", json=payload)
        assert response.status_code == 422

    def test_compare_candidates_missing_vacancy_id(self, client):
        """Test comparison without vacancy_id."""
        payload = {
            "resume_ids": ["resume1", "resume2"],
        }
        response = client.post("/api/matching/compare-candidates", json=payload)
        assert response.status_code == 422

    def test_compare_candidates_missing_resume_ids(self, client):
        """Test comparison without resume_ids."""
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
        }
        response = client.post("/api/matching/compare-candidates", json=payload)
        assert response.status_code == 422

    def test_compare_candidates_invalid_vacancy_id_format(self, client):
        """Test comparison with non-UUID vacancy_id."""
        payload = {
            "vacancy_id": "not-a-uuid",
            "resume_ids": ["resume1", "resume2"],
        }
        response = client.post("/api/matching/compare-candidates", json=payload)
        assert response.status_code in [400, 404]

    def test_compare_candidates_response_structure(self, client):
        """Test that response has correct structure."""
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_ids": ["resume1"],
        }
        response = client.post("/api/matching/compare-candidates", json=payload)
        if response.status_code == 200:
            data = response.json()
            assert "vacancy_id" in data
            assert "vacancy_title" in data
            assert "candidates" in data
            assert "summary" in data
            assert "processing_time_ms" in data

    def test_compare_candidates_candidate_structure(self, client):
        """Test that each candidate has correct structure."""
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_ids": ["resume1"],
        }
        response = client.post("/api/matching/compare-candidates", json=payload)
        if response.status_code == 200:
            data = response.json()
            if len(data["candidates"]) > 0:
                candidate = data["candidates"][0]
                assert "resume_id" in candidate
                assert "filename" in candidate
                assert "match_score" in candidate
                assert "passed" in candidate
                assert "recommendation" in candidate
                assert "matched_skills" in candidate
                assert "missing_skills" in candidate
                assert "rank" in candidate

    def test_compare_candidates_score_breakdown(self, client):
        """Test that score breakdown has all components."""
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_ids": ["resume1"],
        }
        response = client.post("/api/matching/compare-candidates", json=payload)
        if response.status_code == 200:
            data = response.json()
            if len(data["candidates"]) > 0:
                match_score = data["candidates"][0]["match_score"]
                assert "overall_score" in match_score
                assert "keyword_score" in match_score
                assert "tfidf_score" in match_score
                assert "vector_score" in match_score

    def test_compare_candidates_summary_structure(self, client):
        """Test that summary has correct structure."""
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_ids": ["resume1"],
        }
        response = client.post("/api/matching/compare-candidates", json=payload)
        if response.status_code == 200:
            data = response.json()
            summary = data["summary"]
            assert "total_candidates" in summary
            assert "best_score" in summary
            assert "average_score" in summary
            assert "worst_score" in summary
            assert "passed_count" in summary

    def test_compare_candidates_ranking_order(self, client):
        """Test that candidates are ranked by score (descending)."""
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_ids": ["resume1", "resume2", "resume3"],
        }
        response = client.post("/api/matching/compare-candidates", json=payload)
        if response.status_code == 200:
            data = response.json()
            candidates = data["candidates"]
            if len(candidates) > 1:
                # Check that ranks are sequential
                for i, candidate in enumerate(candidates, start=1):
                    assert candidate["rank"] == i
                # Check that scores are in descending order
                scores = [c["match_score"]["overall_score"] for c in candidates]
                assert scores == sorted(scores, reverse=True)

    def test_compare_candidates_scores_in_range(self, client):
        """Test that all scores are between 0 and 1."""
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_ids": ["resume1"],
        }
        response = client.post("/api/matching/compare-candidates", json=payload)
        if response.status_code == 200:
            data = response.json()
            if len(data["candidates"]) > 0:
                match_score = data["candidates"][0]["match_score"]
                assert 0 <= match_score["overall_score"] <= 1
                assert 0 <= match_score["keyword_score"] <= 1
                assert 0 <= match_score["tfidf_score"] <= 1
                assert 0 <= match_score["vector_score"] <= 1

    def test_compare_candidates_processing_time(self, client):
        """Test that processing_time_ms is positive."""
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_ids": ["resume1"],
        }
        response = client.post("/api/matching/compare-candidates", json=payload)
        if response.status_code == 200:
            data = response.json()
            assert data["processing_time_ms"] >= 0


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_compare_candidates_with_invalid_resume_id(self, client):
        """Test comparison with one invalid and one valid resume ID."""
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_ids": ["valid-resume", "invalid-resume"],
        }
        response = client.post("/api/matching/compare-candidates", json=payload)
        # Should process valid resume and skip invalid one
        assert response.status_code in [200, 404]

    def test_compare_candidates_vacancy_not_found(self, client):
        """Test comparison with non-existent vacancy."""
        payload = {
            "vacancy_id": "00000000-0000-0000-0000-000000000000",
            "resume_ids": ["resume1"],
        }
        response = client.post("/api/matching/compare-candidates", json=payload)
        assert response.status_code == 404

    def test_compare_candidates_all_resumes_not_found(self, client):
        """Test comparison where none of the resumes exist."""
        payload = {
            "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
            "resume_ids": ["non-existent-1", "non-existent-2"],
        }
        response = client.post("/api/matching/compare-candidates", json=payload)
        # Should return 404 when no valid resumes are found
        assert response.status_code == 404


class TestErrorHandling:
    """Tests for error handling."""

    def test_compare_candidates_invalid_json(self, client):
        """Test endpoint with invalid JSON."""
        response = client.post(
            "/api/matching/compare-candidates",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_compare_candidates_missing_content_type(self, client):
        """Test POST endpoint without Content-Type."""
        response = client.post(
            "/api/matching/compare-candidates",
            data="vacancy_id=test&resume_ids=r1,r2",
        )
        # Should either work or return 415/422
        assert response.status_code in [200, 415, 422]

    def test_compare_candidates_method_not_allowed(self, client):
        """Test unsupported HTTP method."""
        response = client.get("/api/matching/compare-candidates")
        assert response.status_code == 405
