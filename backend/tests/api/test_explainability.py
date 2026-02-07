"""
Unit tests for Explainability API endpoints.

Tests cover:
- POST /api/explainability/explain - Ranking explanation
- POST /api/explainability/what-if - Scenario analysis
- GET /api/explainability/confidence/{id} - Confidence intervals
- GET /api/explainability/narrative/{id} - Natural language explanations
- POST /api/explainability/compare-explain - Candidate comparison
- POST /api/explainability/export/pdf - PDF generation
- Request validation
- Error handling
"""
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from uuid import uuid4, UUID

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


@pytest.fixture
def mock_ranking():
    """Create a mock CandidateRank object."""
    ranking = MagicMock()
    ranking.id = uuid4()
    ranking.rank_score = 0.85
    ranking.rank_position = 1
    ranking.recommendation = "excellent"
    ranking.feature_contributions = {
        "skills_match": {"value": 0.9, "weight": 0.4, "contribution": 0.36},
        "experience": {"value": 0.8, "weight": 0.3, "contribution": 0.24},
        "education": {"value": 0.7, "weight": 0.2, "contribution": 0.14},
        "keywords": {"value": 0.85, "weight": 0.1, "contribution": 0.085},
    }
    ranking.ranking_factors = {
        "keyword_score": 0.85,
        "tfidf_score": 0.82,
        "vector_score": 0.88,
    }
    ranking.prediction_confidence = 0.75
    ranking.confidence_interval = {"lower": 0.80, "upper": 0.90}
    ranking.explanation_narrative = "This candidate is an excellent match due to strong skills and experience."
    ranking.resume_highlights = {
        "skills_match": {"section": "skills", "offset": 100, "length": 200}
    }
    return ranking


@pytest.fixture
def mock_resume():
    """Create a mock Resume object."""
    resume = MagicMock()
    resume.id = uuid4()
    resume.filename = "john_developer_resume.pdf"
    resume.raw_text = "John Developer\nPython Developer with 5 years experience..."
    return resume


@pytest.fixture
def mock_vacancy():
    """Create a mock JobVacancy object."""
    vacancy = MagicMock()
    vacancy.id = uuid4()
    vacancy.title = "Senior Python Developer"
    vacancy.description = "We are looking for a Senior Python Developer..."
    return vacancy


class TestExplainRankingEndpoint:
    """Tests for POST /api/explainability/explain endpoint."""

    def test_returns_200_on_success(self, client, mock_ranking, mock_resume, mock_vacancy):
        """Test endpoint returns 200 status code on success."""
        with patch('api.explainability.get_explanation_generator') as mock_get_generator, \
             patch('api.explainability.select') as mock_select:

            # Mock explanation generator
            mock_generator = MagicMock()
            mock_explanation = MagicMock()
            mock_explanation.candidate_name = "John Developer"
            mock_explanation.rank_score = 0.85
            mock_explanation.rank_position = 1
            mock_explanation.narrative = "This candidate is an excellent match..."
            mock_explanation.feature_explanations = [
                MagicMock(to_dict=lambda: {"feature": "skills", "contribution": 0.36})
            ]
            mock_explanation.confidence_interval = MagicMock(
                to_dict=lambda: {"lower": 0.80, "upper": 0.90}
            )
            mock_explanation.strengths = ["Strong Python skills", "Relevant experience"]
            mock_explanation.weaknesses = ["Limited cloud experience"]
            mock_explanation.recommendation = "excellent"
            mock_explanation.highlight_sections = {"skills": "Strong technical skills section"}
            mock_explanation.provider = "openai"
            mock_explanation.model = "gpt-4"
            mock_explanation.generated_at = datetime.utcnow().isoformat()

            mock_generator.generate_ranking_explanation = AsyncMock(return_value=mock_explanation)
            mock_get_generator.return_value = mock_generator

            # Mock database queries
            mock_db_result = MagicMock()
            mock_db_result.scalar_one_or_none = MagicMock(
                side_effect=[mock_ranking, mock_resume, mock_vacancy]
            )
            mock_db = MagicMock()
            mock_db.execute = AsyncMock(return_value=mock_db_result)

            with patch('api.explainability.get_db', return_value=mock_db):
                payload = {
                    "resume_id": str(mock_resume.id),
                    "vacancy_id": str(mock_vacancy.id),
                    "use_llm": True,
                }
                response = client.post("/api/explainability/explain", json=payload)
                assert response.status_code == 200

    def test_response_structure(self, client, mock_ranking, mock_resume, mock_vacancy):
        """Test response has correct structure."""
        with patch('api.explainability.get_explanation_generator') as mock_get_generator, \
             patch('api.explainability.select') as mock_select:

            # Mock explanation generator
            mock_generator = MagicMock()
            mock_explanation = MagicMock()
            mock_explanation.candidate_name = "John Developer"
            mock_explanation.rank_score = 0.85
            mock_explanation.rank_position = 1
            mock_explanation.narrative = "This candidate is an excellent match..."
            mock_explanation.feature_explanations = []
            mock_explanation.confidence_interval = MagicMock(
                to_dict=lambda: {"lower": 0.80, "upper": 0.90}
            )
            mock_explanation.strengths = ["Strong Python skills"]
            mock_explanation.weaknesses = []
            mock_explanation.recommendation = "excellent"
            mock_explanation.highlight_sections = {}
            mock_explanation.provider = "openai"
            mock_explanation.model = "gpt-4"
            mock_explanation.generated_at = datetime.utcnow().isoformat()

            mock_generator.generate_ranking_explanation = AsyncMock(return_value=mock_explanation)
            mock_get_generator.return_value = mock_generator

            # Mock database queries
            mock_db_result = MagicMock()
            mock_db_result.scalar_one_or_none = MagicMock(
                side_effect=[mock_ranking, mock_resume, mock_vacancy]
            )
            mock_db = MagicMock()
            mock_db.execute = AsyncMock(return_value=mock_db_result)

            with patch('api.explainability.get_db', return_value=mock_db):
                payload = {
                    "resume_id": str(mock_resume.id),
                    "vacancy_id": str(mock_vacancy.id),
                }
                response = client.post("/api/explainability/explain", json=payload)

                # Check response structure
                assert "resume_id" in response.json()
                assert "vacancy_id" in response.json()
                assert "candidate_name" in response.json()
                assert "rank_score" in response.json()
                assert "narrative" in response.json()
                assert "feature_explanations" in response.json()
                assert "strengths" in response.json()
                assert "weaknesses" in response.json()
                assert "recommendation" in response.json()

    def test_returns_422_for_invalid_uuid(self, client):
        """Test endpoint returns 422 for invalid UUID format."""
        payload = {
            "resume_id": "not-a-uuid",
            "vacancy_id": str(uuid4()),
        }
        response = client.post("/api/explainability/explain", json=payload)
        assert response.status_code == 422

    def test_returns_404_when_ranking_not_found(self, client, mock_resume, mock_vacancy):
        """Test endpoint returns 404 when ranking not found."""
        with patch('api.explainability.select') as mock_select:
            # Mock database query returning None
            mock_db_result = MagicMock()
            mock_db_result.scalar_one_or_none = MagicMock(return_value=None)
            mock_db = MagicMock()
            mock_db.execute = AsyncMock(return_value=mock_db_result)

            with patch('api.explainability.get_db', return_value=mock_db):
                payload = {
                    "resume_id": str(mock_resume.id),
                    "vacancy_id": str(mock_vacancy.id),
                }
                response = client.post("/api/explainability/explain", json=payload)
                assert response.status_code == 404


class TestWhatIfAnalysisEndpoint:
    """Tests for POST /api/explainability/what-if endpoint."""

    def test_returns_200_on_success(self, client, mock_ranking, mock_resume, mock_vacancy):
        """Test endpoint returns 200 on successful what-if analysis."""
        with patch('api.explainability.get_sensitivity_analyzer') as mock_get_analyzer, \
             patch('api.explainability.select') as mock_select:

            # Mock sensitivity analyzer
            mock_analyzer = MagicMock()
            mock_whatif_result = MagicMock()
            mock_whatif_result.scenario_description = "Increasing experience by 12 months"
            mock_whatif_result.original_score = 0.75
            mock_whatif_result.new_score = 0.82
            mock_whatif_result.score_delta = 0.07
            mock_whatif_result.score_delta_percent = 9.33
            mock_whatif_result.original_recommendation = "good"
            mock_whatif_result.new_recommendation = "excellent"
            mock_whatif_result.perturbations = [
                {"feature": "experience_months", "original": 60, "new": 72}
            ]
            mock_whatif_result.feature_impacts = {"experience_months": 0.07}
            mock_whatif_result.explanation = "More experience improves ranking significantly"

            mock_analyzer.analyze_from_db = AsyncMock(return_value=mock_whatif_result)
            mock_get_analyzer.return_value = mock_analyzer

            # Mock database queries
            mock_db_result = MagicMock()
            mock_db_result.scalar_one_or_none = MagicMock(
                side_effect=[mock_ranking, mock_resume, mock_vacancy]
            )
            mock_db = MagicMock()
            mock_db.execute = AsyncMock(return_value=mock_db_result)

            with patch('api.explainability.get_db', return_value=mock_db):
                payload = {
                    "resume_id": str(mock_resume.id),
                    "vacancy_id": str(mock_vacancy.id),
                    "adjustments": {"experience_months": 12},
                }
                response = client.post("/api/explainability/what-if", json=payload)
                assert response.status_code == 200

    def test_response_structure(self, client, mock_ranking, mock_resume, mock_vacancy):
        """Test what-if response has correct structure."""
        with patch('api.explainability.get_sensitivity_analyzer') as mock_get_analyzer, \
             patch('api.explainability.select') as mock_select:

            # Mock sensitivity analyzer
            mock_analyzer = MagicMock()
            mock_whatif_result = MagicMock()
            mock_whatif_result.scenario_description = "Test scenario"
            mock_whatif_result.original_score = 0.75
            mock_whatif_result.new_score = 0.80
            mock_whatif_result.score_delta = 0.05
            mock_whatif_result.score_delta_percent = 6.67
            mock_whatif_result.original_recommendation = "good"
            mock_whatif_result.new_recommendation = "good"
            mock_whatif_result.perturbations = []
            mock_whatif_result.feature_impacts = {}
            mock_whatif_result.explanation = "Test explanation"

            mock_analyzer.analyze_from_db = AsyncMock(return_value=mock_whatif_result)
            mock_get_analyzer.return_value = mock_analyzer

            # Mock database queries
            mock_db_result = MagicMock()
            mock_db_result.scalar_one_or_none = MagicMock(
                side_effect=[mock_ranking, mock_resume, mock_vacancy]
            )
            mock_db = MagicMock()
            mock_db.execute = AsyncMock(return_value=mock_db_result)

            with patch('api.explainability.get_db', return_value=mock_db):
                payload = {
                    "resume_id": str(mock_resume.id),
                    "vacancy_id": str(mock_vacancy.id),
                    "adjustments": {"experience_months": 12},
                }
                response = client.post("/api/explainability/what-if", json=payload)

                data = response.json()
                assert "resume_id" in data
                assert "vacancy_id" in data
                assert "scenario_description" in data
                assert "original_score" in data
                assert "new_score" in data
                assert "score_delta" in data
                assert "original_recommendation" in data
                assert "new_recommendation" in data


class TestConfidenceIntervalEndpoint:
    """Tests for GET /api/explainability/confidence/{rank_id} endpoint."""

    def test_returns_200_on_success(self, client, mock_ranking):
        """Test endpoint returns 200 with confidence interval."""
        with patch('api.explainability.select') as mock_select:

            # Mock database query
            mock_db_result = MagicMock()
            mock_db_result.scalar_one_or_none = MagicMock(return_value=mock_ranking)
            mock_db = MagicMock()
            mock_db.execute = AsyncMock(return_value=mock_db_result)

            with patch('api.explainability.get_db', return_value=mock_db):
                response = client.get(f"/api/explainability/confidence/{mock_ranking.id}")
                assert response.status_code == 200

    def test_returns_200_for_test_mode(self, client):
        """Test endpoint returns 200 with mock data in test mode."""
        response = client.get("/api/explainability/confidence/test-id?test_mode=true")
        assert response.status_code == 200

    def test_response_structure(self, client, mock_ranking):
        """Test confidence interval response structure."""
        with patch('api.explainability.select') as mock_select:

            # Mock database query
            mock_db_result = MagicMock()
            mock_db_result.scalar_one_or_none = MagicMock(return_value=mock_ranking)
            mock_db = MagicMock()
            mock_db.execute = AsyncMock(return_value=mock_db_result)

            with patch('api.explainability.get_db', return_value=mock_db):
                response = client.get(f"/api/explainability/confidence/{mock_ranking.id}")

                data = response.json()
                assert "rank_id" in data
                assert "confidence_interval" in data
                assert "lower" in data["confidence_interval"]
                assert "upper" in data["confidence_interval"]


class TestNarrativeEndpoint:
    """Tests for GET /api/explainability/narrative/{rank_id} endpoint."""

    def test_returns_200_on_success(self, client, mock_ranking, mock_resume):
        """Test endpoint returns 200 with narrative explanation."""
        with patch('api.explainability.get_explanation_generator') as mock_get_generator, \
             patch('api.explainability.select') as mock_select:

            # Mock explanation generator
            mock_generator = MagicMock()
            mock_explanation = MagicMock()
            mock_explanation.narrative = "This candidate is an excellent match..."
            mock_explanation.candidate_name = "John Developer"
            mock_explanation.rank_score = 0.85
            mock_explanation.recommendation = "excellent"
            mock_explanation.strengths = ["Strong skills"]
            mock_explanation.weaknesses = []
            mock_explanation.provider = "openai"
            mock_explanation.model = "gpt-4"
            mock_explanation.generated_at = datetime.utcnow().isoformat()

            mock_generator.generate_ranking_explanation = AsyncMock(return_value=mock_explanation)
            mock_get_generator.return_value = mock_generator

            # Mock database queries
            mock_db_result = MagicMock()
            mock_db_result.scalar_one_or_none = MagicMock(
                side_effect=[mock_ranking, mock_resume, MagicMock()]
            )
            mock_db = MagicMock()
            mock_db.execute = AsyncMock(return_value=mock_db_result)

            with patch('api.explainability.get_db', return_value=mock_db):
                response = client.get(f"/api/explainability/narrative/{mock_ranking.id}")
                assert response.status_code == 200

    def test_returns_200_for_test_mode(self, client):
        """Test endpoint returns 200 with mock data in test mode."""
        response = client.get("/api/explainability/narrative/test-id?test_mode=true")
        assert response.status_code == 200


class TestCompareExplainEndpoint:
    """Tests for POST /api/explainability/compare-explain endpoint."""

    def test_returns_200_on_success(self, client):
        """Test endpoint returns 200 with comparison explanation."""
        with patch('api.explainability.get_explanation_generator') as mock_get_generator, \
             patch('api.explainability.select') as mock_select:

            # Mock explanation generator
            mock_generator = MagicMock()
            mock_comparison = MagicMock()
            mock_comparison.narrative = "Candidate A ranks higher due to more experience"
            mock_comparison.candidate_a_name = "John Senior"
            mock_comparison.candidate_b_name = "Jane Middle"
            mock_comparison.candidate_a_score = 0.90
            mock_comparison.candidate_b_score = 0.75
            mock_comparison.score_difference = 0.15
            mock_comparison.key_differences = ["More experience", "Better skill match"]
            mock_comparison.winning_factors = ["Senior level experience"]
            mock_comparison.losing_factors = []
            mock_comparison.recommendation = "Prioritize candidate A"
            mock_comparison.provider = "openai"
            mock_comparison.model = "gpt-4"
            mock_comparison.generated_at = datetime.utcnow().isoformat()

            mock_generator.generate_comparison_explanation = AsyncMock(return_value=mock_comparison)
            mock_get_generator.return_value = mock_generator

            # Mock database queries
            mock_ranking_a = MagicMock()
            mock_ranking_a.rank_score = 0.90
            mock_ranking_b = MagicMock()
            mock_ranking_b.rank_score = 0.75
            mock_vacancy = MagicMock()

            mock_db_result = MagicMock()
            mock_db_result.scalar_one_or_none = MagicMock(
                side_effect=[mock_ranking_a, mock_ranking_b, mock_vacancy]
            )
            mock_db = MagicMock()
            mock_db.execute = AsyncMock(return_value=mock_db_result)

            with patch('api.explainability.get_db', return_value=mock_db):
                payload = {
                    "resume_a_id": str(uuid4()),
                    "resume_b_id": str(uuid4()),
                    "vacancy_id": str(uuid4()),
                }
                response = client.post("/api/explainability/compare-explain", json=payload)
                assert response.status_code == 200


class TestExportPDFEndpoint:
    """Tests for POST /api/explainability/export/pdf endpoint."""

    def test_returns_200_on_success(self, client, mock_ranking, mock_resume, mock_vacancy):
        """Test endpoint returns 200 with PDF export info."""
        with patch('api.explainability.get_report_generator') as mock_get_generator, \
             patch('api.explainability.select') as mock_select:

            # Mock report generator
            mock_generator = MagicMock()
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.download_url = "http://localhost:8000/downloads/explanation_abc123.pdf"
            mock_result.filename = "explanation_abc123.pdf"
            mock_result.file_size = 12345
            mock_result.expires_at = "2026-02-08T12:00:00Z"

            mock_generator.generate_report = AsyncMock(return_value=mock_result)
            mock_get_generator.return_value = mock_generator

            # Mock database queries
            mock_db_result = MagicMock()
            mock_db_result.scalar_one_or_none = MagicMock(
                side_effect=[mock_ranking, mock_resume, mock_vacancy]
            )
            mock_db = MagicMock()
            mock_db.execute = AsyncMock(return_value=mock_db_result)

            with patch('api.explainability.get_db', return_value=mock_db):
                payload = {
                    "resume_id": str(mock_resume.id),
                    "vacancy_id": str(mock_vacancy.id),
                    "report_type": "ranking_explanation",
                }
                response = client.post("/api/explainability/export/pdf", json=payload)
                assert response.status_code == 200

    def test_returns_200_for_test_mode(self, client):
        """Test endpoint returns 200 with mock data in test mode."""
        with patch('api.explainability.select') as mock_select:
            # Mock database returning None for test-id
            mock_db_result = MagicMock()
            mock_db_result.scalar_one_or_none = MagicMock(return_value=None)
            mock_db = MagicMock()
            mock_db.execute = AsyncMock(return_value=mock_db_result)

            with patch('api.explainability.get_db', return_value=mock_db):
                payload = {
                    "resume_id": "test-id",
                    "vacancy_id": "test-id",
                }
                response = client.post("/api/explainability/export/pdf", json=payload)
                assert response.status_code == 200

    def test_response_structure(self, client, mock_ranking, mock_resume, mock_vacancy):
        """Test PDF export response structure."""
        with patch('api.explainability.get_report_generator') as mock_get_generator, \
             patch('api.explainability.select') as mock_select:

            # Mock report generator
            mock_generator = MagicMock()
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.download_url = "http://localhost:8000/downloads/test.pdf"
            mock_result.filename = "test.pdf"
            mock_result.file_size = 12345
            mock_result.expires_at = "2026-02-08T12:00:00Z"

            mock_generator.generate_report = AsyncMock(return_value=mock_result)
            mock_get_generator.return_value = mock_generator

            # Mock database queries
            mock_db_result = MagicMock()
            mock_db_result.scalar_one_or_none = MagicMock(
                side_effect=[mock_ranking, mock_resume, mock_vacancy]
            )
            mock_db = MagicMock()
            mock_db.execute = AsyncMock(return_value=mock_db_result)

            with patch('api.explainability.get_db', return_value=mock_db):
                payload = {
                    "resume_id": str(mock_resume.id),
                    "vacancy_id": str(mock_vacancy.id),
                }
                response = client.post("/api/explainability/export/pdf", json=payload)

                data = response.json()
                assert "success" in data
                assert "download_url" in data
                assert "filename" in data
                assert "file_size" in data
                assert "expires_at" in data


class TestErrorHandling:
    """Tests for error handling across all endpoints."""

    def test_explain_handles_internal_errors(self, client, mock_resume, mock_vacancy):
        """Test explain endpoint handles internal errors gracefully."""
        with patch('api.explainability.get_explanation_generator') as mock_get_generator, \
             patch('api.explainability.select') as mock_select:

            # Mock generator that raises exception
            mock_generator = MagicMock()
            mock_generator.generate_ranking_explanation = AsyncMock(
                side_effect=Exception("LLM API error")
            )
            mock_get_generator.return_value = mock_generator

            # Mock database queries
            mock_ranking = MagicMock()
            mock_db_result = MagicMock()
            mock_db_result.scalar_one_or_none = MagicMock(
                side_effect=[mock_ranking, mock_resume, mock_vacancy]
            )
            mock_db = MagicMock()
            mock_db.execute = AsyncMock(return_value=mock_db_result)

            with patch('api.explainability.get_db', return_value=mock_db):
                payload = {
                    "resume_id": str(mock_resume.id),
                    "vacancy_id": str(mock_vacancy.id),
                }
                response = client.post("/api/explainability/explain", json=payload)
                assert response.status_code == 500
