"""
End-to-end verification tests for AI Explainability Dashboard API endpoints.

These tests verify that:
1. GET /api/analytics/ai-explainability/confidence returns confidence distribution
2. GET /api/analytics/ai-explainability/feature-importance returns 13 features
3. GET /api/analytics/ai-explainability/performance-trends returns metrics array
4. All responses match Pydantic schema

This test file verifies subtask-4-2 requirements.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


# =============================================================================
# Test 1: Confidence Endpoint - Returns correct data structure
# =============================================================================


class TestConfidenceEndpoint:
    """Tests for GET /api/analytics/ai-explainability/confidence endpoint."""

    def test_returns_200_status(self, client):
        """Test endpoint returns 200 status code."""
        with patch('api.analytics.get_db') as mock_get_db:
            # Mock async generator
            async def mock_db_gen():
                mock_db = MagicMock()
                mock_result = MagicMock()
                mock_result.scalars.return_value.all.return_value = []
                mock_db.execute = AsyncMock(return_value=mock_result)
                yield mock_db

            mock_get_db.return_value = mock_db_gen()

            response = client.get("/api/analytics/ai-explainability/confidence")
            assert response.status_code == 200

    def test_response_structure_has_required_fields(self, client):
        """Test response has all required fields for confidence metrics."""
        with patch('api.analytics.get_db') as mock_get_db:
            async def mock_db_gen():
                mock_db = MagicMock()
                mock_result = MagicMock()
                mock_result.scalars.return_value.all.return_value = []
                mock_db.execute = AsyncMock(return_value=mock_result)
                yield mock_db

            mock_get_db.return_value = mock_db_gen()

            response = client.get("/api/analytics/ai-explainability/confidence")
            data = response.json()

            # Verify top-level required fields
            assert "average_confidence" in data, "Missing 'average_confidence' field"
            assert "confidence_interval" in data, "Missing 'confidence_interval' field"
            assert "distribution" in data, "Missing 'distribution' field"
            assert "confidence_accuracy_correlation" in data, "Missing 'confidence_accuracy_correlation' field"

    def test_confidence_interval_structure(self, client):
        """Test confidence_interval has required nested fields."""
        with patch('api.analytics.get_db') as mock_get_db:
            async def mock_db_gen():
                mock_db = MagicMock()
                mock_result = MagicMock()
                mock_result.scalars.return_value.all.return_value = []
                mock_db.execute = AsyncMock(return_value=mock_result)
                yield mock_db

            mock_get_db.return_value = mock_db_gen()

            response = client.get("/api/analytics/ai-explainability/confidence")
            data = response.json()
            ci = data["confidence_interval"]

            assert "lower" in ci, "Missing 'lower' in confidence_interval"
            assert "upper" in ci, "Missing 'upper' in confidence_interval"
            assert "confidence_level" in ci, "Missing 'confidence_level' in confidence_interval"

            # Verify types
            assert isinstance(ci["lower"], (int, float)), "lower must be numeric"
            assert isinstance(ci["upper"], (int, float)), "upper must be numeric"
            assert isinstance(ci["confidence_level"], (int, float)), "confidence_level must be numeric"

    def test_distribution_structure(self, client):
        """Test distribution has required nested fields."""
        with patch('api.analytics.get_db') as mock_get_db:
            async def mock_db_gen():
                mock_db = MagicMock()
                mock_result = MagicMock()
                mock_result.scalars.return_value.all.return_value = []
                mock_db.execute = AsyncMock(return_value=mock_result)
                yield mock_db

            mock_get_db.return_value = mock_db_gen()

            response = client.get("/api/analytics/ai-explainability/confidence")
            data = response.json()
            dist = data["distribution"]

            assert "high_confidence_count" in dist, "Missing 'high_confidence_count' in distribution"
            assert "medium_confidence_count" in dist, "Missing 'medium_confidence_count' in distribution"
            assert "low_confidence_count" in dist, "Missing 'low_confidence_count' in distribution"

            # Verify types
            assert isinstance(dist["high_confidence_count"], int), "high_confidence_count must be integer"
            assert isinstance(dist["medium_confidence_count"], int), "medium_confidence_count must be integer"
            assert isinstance(dist["low_confidence_count"], int), "low_confidence_count must be integer"

    def test_average_confidence_is_numeric(self, client):
        """Test average_confidence is a numeric value."""
        with patch('api.analytics.get_db') as mock_get_db:
            async def mock_db_gen():
                mock_db = MagicMock()
                mock_result = MagicMock()
                mock_result.scalars.return_value.all.return_value = []
                mock_db.execute = AsyncMock(return_value=mock_result)
                yield mock_db

            mock_get_db.return_value = mock_db_gen()

            response = client.get("/api/analytics/ai-explainability/confidence")
            data = response.json()

            assert isinstance(data["average_confidence"], (int, float)), "average_confidence must be numeric"
            assert 0 <= data["average_confidence"] <= 1, "average_confidence must be between 0 and 1"


# =============================================================================
# Test 2: Feature Importance Endpoint - Returns 13 features
# =============================================================================


class TestFeatureImportanceEndpoint:
    """Tests for GET /api/analytics/ai-explainability/feature-importance endpoint."""

    def test_returns_200_status(self, client):
        """Test endpoint returns 200 status code."""
        with patch('api.analytics.get_ranking_service') as mock_get_service:
            mock_service = MagicMock()
            mock_model = MagicMock()
            mock_model.get_feature_importance.return_value = {}
            mock_model.version = "1.0.0"
            mock_model.model_type = "random_forest"
            mock_service.model = mock_model
            mock_get_service.return_value = mock_service

            response = client.get("/api/analytics/ai-explainability/feature-importance")
            assert response.status_code == 200

    def test_response_structure_has_required_fields(self, client):
        """Test response has all required fields."""
        with patch('api.analytics.get_ranking_service') as mock_get_service:
            mock_service = MagicMock()
            mock_model = MagicMock()
            mock_model.get_feature_importance.return_value = {}
            mock_model.version = "1.0.0"
            mock_model.model_type = "random_forest"
            mock_service.model = mock_model
            mock_get_service.return_value = mock_service

            response = client.get("/api/analytics/ai-explainability/feature-importance")
            data = response.json()

            assert "features" in data, "Missing 'features' field"
            assert "model_version" in data, "Missing 'model_version' field"
            assert "model_type" in data, "Missing 'model_type' field"
            assert "total_features" in data, "Missing 'total_features' field"
            assert "last_updated" in data, "Missing 'last_updated' field"

    def test_returns_exactly_13_features(self, client):
        """Test endpoint returns exactly 13 features (per spec)."""
        with patch('api.analytics.get_ranking_service') as mock_get_service:
            mock_service = MagicMock()
            mock_model = MagicMock()

            # Create mock importance dict with 13 features
            mock_importance = {
                "overall_match_score": 0.12,
                "keyword_score": 0.08,
                "tfidf_score": 0.07,
                "vector_score": 0.09,
                "skills_match_ratio": 0.15,
                "experience_months": 0.10,
                "experience_relevance": 0.11,
                "education_level": 0.05,
                "recent_experience": 0.06,
                "skill_rarity_score": 0.04,
                "title_similarity": 0.05,
                "freshness_score": 0.03,
                "completeness_score": 0.05,
            }
            mock_model.get_feature_importance.return_value = mock_importance
            mock_model.version = "1.0.0"
            mock_model.model_type = "random_forest"
            mock_service.model = mock_model
            mock_get_service.return_value = mock_service

            response = client.get("/api/analytics/ai-explainability/feature-importance")
            data = response.json()

            assert data["total_features"] == 13, f"Expected 13 features, got {data['total_features']}"
            assert len(data["features"]) == 13, f"Expected 13 features in array, got {len(data['features'])}"

    def test_each_feature_has_required_fields(self, client):
        """Test each feature item has required fields."""
        with patch('api.analytics.get_ranking_service') as mock_get_service:
            mock_service = MagicMock()
            mock_model = MagicMock()
            mock_model.get_feature_importance.return_value = {
                "skills_match_ratio": 0.15,
                "experience_relevance": 0.11,
            }
            mock_model.version = "1.0.0"
            mock_model.model_type = "random_forest"
            mock_service.model = mock_model
            mock_get_service.return_value = mock_service

            response = client.get("/api/analytics/ai-explainability/feature-importance")
            data = response.json()

            for feature in data["features"]:
                # API uses feature_name and importance_score (not name and importance)
                assert "feature_name" in feature, "Missing feature_name in feature item"
                assert "importance_score" in feature, "Missing importance_score in feature item"
                assert "rank" in feature, "Missing rank in feature item"
                assert "description" in feature, "Missing description in feature item"
                assert "category" in feature, "Missing category in feature item"

                # Verify types
                assert isinstance(feature["feature_name"], str), "feature_name must be string"
                assert isinstance(feature["importance_score"], (int, float)), "importance_score must be numeric"
                assert isinstance(feature["rank"], int), "rank must be integer"
                assert isinstance(feature["description"], str), "description must be string"
                assert isinstance(feature["category"], str), "category must be string"

    def test_features_are_sorted_by_importance(self, client):
        """Test features are sorted by importance score descending."""
        with patch('api.analytics.get_ranking_service') as mock_get_service:
            mock_service = MagicMock()
            mock_model = MagicMock()
            mock_model.get_feature_importance.return_value = {
                "skills_match_ratio": 0.15,
                "experience_relevance": 0.25,  # Higher importance
                "education_level": 0.10,
            }
            mock_model.version = "1.0.0"
            mock_model.model_type = "random_forest"
            mock_service.model = mock_model
            mock_get_service.return_value = mock_service

            response = client.get("/api/analytics/ai-explainability/feature-importance")
            data = response.json()

            features = data["features"]
            for i in range(1, len(features)):
                assert features[i - 1]["importance_score"] >= features[i]["importance_score"], \
                    f"Features not sorted: {features[i-1]['importance_score']} < {features[i]['importance_score']}"


# =============================================================================
# Test 3: Performance Trends Endpoint - Returns metrics array
# =============================================================================


class TestPerformanceTrendsEndpoint:
    """Tests for GET /api/analytics/ai-explainability/performance-trends endpoint."""

    def test_returns_200_status(self, client):
        """Test endpoint returns 200 status code."""
        with patch('api.analytics.get_db') as mock_get_db:
            async def mock_db_gen():
                mock_db = MagicMock()
                mock_result = MagicMock()
                mock_result.scalars.return_value.all.return_value = []
                mock_db.execute = AsyncMock(return_value=mock_result)
                yield mock_db

            mock_get_db.return_value = mock_db_gen()

            response = client.get("/api/analytics/ai-explainability/performance-trends")
            assert response.status_code == 200

    def test_response_structure_has_required_fields(self, client):
        """Test response has all required fields."""
        with patch('api.analytics.get_db') as mock_get_db:
            async def mock_db_gen():
                mock_db = MagicMock()
                mock_result = MagicMock()
                mock_result.scalars.return_value.all.return_value = []
                mock_db.execute = AsyncMock(return_value=mock_result)
                yield mock_db

            mock_get_db.return_value = mock_db_gen()

            response = client.get("/api/analytics/ai-explainability/performance-trends")
            data = response.json()

            assert "period" in data, "Missing 'period' field"
            assert "start_date" in data, "Missing 'start_date' field"
            assert "end_date" in data, "Missing 'end_date' field"
            assert "models" in data, "Missing 'models' field"
            assert "overall_trend" in data, "Missing 'overall_trend' field"
            assert "total_evaluations" in data, "Missing 'total_evaluations' field"

    def test_models_array_structure(self, client):
        """Test models array has correct structure."""
        with patch('api.analytics.get_db') as mock_get_db:
            async def mock_db_gen():
                mock_db = MagicMock()
                mock_result = MagicMock()
                mock_result.scalars.return_value.all.return_value = []
                mock_db.execute = AsyncMock(return_value=mock_result)
                yield mock_db

            mock_get_db.return_value = mock_db_gen()

            response = client.get("/api/analytics/ai-explainability/performance-trends")
            data = response.json()

            assert isinstance(data["models"], list), "models must be a list"

            for model in data["models"]:
                assert "model_name" in model, "Missing model_name in model"
                assert "model_version" in model, "Missing model_version in model"
                assert "current_accuracy" in model, "Missing current_accuracy in model"
                assert "current_f1_score" in model, "Missing current_f1_score in model"
                assert "trend_direction" in model, "Missing trend_direction in model"
                assert "data_points" in model, "Missing data_points in model"

    def test_data_points_structure(self, client):
        """Test data_points in models have correct structure."""
        with patch('api.analytics.get_db') as mock_get_db:
            async def mock_db_gen():
                mock_db = MagicMock()
                mock_result = MagicMock()
                mock_result.scalars.return_value.all.return_value = []
                mock_db.execute = AsyncMock(return_value=mock_result)
                yield mock_db

            mock_get_db.return_value = mock_db_gen()

            response = client.get("/api/analytics/ai-explainability/performance-trends")
            data = response.json()

            for model in data["models"]:
                for point in model.get("data_points", []):
                    assert "timestamp" in point, "Missing timestamp in data_point"
                    # Each point should have at least one metric
                    has_metric = any(k in point for k in ["accuracy", "f1_score", "precision", "recall"])
                    assert has_metric, "data_point must have at least one metric"

    def test_period_parameter_support(self, client):
        """Test period query parameter is supported."""
        with patch('api.analytics.get_db') as mock_get_db:
            async def mock_db_gen():
                mock_db = MagicMock()
                mock_result = MagicMock()
                mock_result.scalars.return_value.all.return_value = []
                mock_db.execute = AsyncMock(return_value=mock_result)
                yield mock_db

            mock_get_db.return_value = mock_db_gen()

            # Test 7d period
            response = client.get("/api/analytics/ai-explainability/performance-trends?period=7d")
            assert response.status_code == 200
            assert response.json()["period"] == "7d"

            # Test 30d period
            response = client.get("/api/analytics/ai-explainability/performance-trends?period=30d")
            assert response.status_code == 200
            assert response.json()["period"] == "30d"

            # Test 90d period
            response = client.get("/api/analytics/ai-explainability/performance-trends?period=90d")
            assert response.status_code == 200
            assert response.json()["period"] == "90d"

    def test_overall_trend_valid_value(self, client):
        """Test overall_trend is a valid value."""
        with patch('api.analytics.get_db') as mock_get_db:
            async def mock_db_gen():
                mock_db = MagicMock()
                mock_result = MagicMock()
                mock_result.scalars.return_value.all.return_value = []
                mock_db.execute = AsyncMock(return_value=mock_result)
                yield mock_db

            mock_get_db.return_value = mock_db_gen()

            response = client.get("/api/analytics/ai-explainability/performance-trends")
            data = response.json()

            valid_trends = ["improving", "stable", "declining"]
            assert data["overall_trend"] in valid_trends, \
                f"Invalid overall_trend: {data['overall_trend']}, must be one of {valid_trends}"


# =============================================================================
# Test 4: Ranking Rationale Endpoint - Returns correct structure
# =============================================================================


class TestRankingRationaleEndpoint:
    """Tests for GET /api/analytics/ai-explainability/ranking-rationale/{candidate_id} endpoint."""

    def test_returns_200_for_test_id(self, client):
        """Test endpoint returns 200 for test candidate ID."""
        response = client.get("/api/analytics/ai-explainability/ranking-rationale/test-id")
        assert response.status_code == 200

    def test_response_structure_has_required_fields(self, client):
        """Test response has all required fields."""
        response = client.get("/api/analytics/ai-explainability/ranking-rationale/test-id")
        data = response.json()

        assert "candidate_id" in data, "Missing 'candidate_id' field"
        assert "rank_score" in data, "Missing 'rank_score' field"
        assert "rank_position" in data, "Missing 'rank_position' field"
        assert "narrative" in data, "Missing 'narrative' field"
        assert "factors" in data, "Missing 'factors' field"
        assert "confidence" in data, "Missing 'confidence' field"
        assert "strengths" in data, "Missing 'strengths' field"
        assert "weaknesses" in data, "Missing 'weaknesses' field"
        assert "skills_match" in data, "Missing 'skills_match' field"

    def test_factors_structure(self, client):
        """Test factors array has correct structure."""
        response = client.get("/api/analytics/ai-explainability/ranking-rationale/test-id")
        data = response.json()

        for factor in data["factors"]:
            assert "factor_name" in factor, "Missing factor_name in factor"
            assert "score" in factor, "Missing score in factor"
            assert "weight" in factor, "Missing weight in factor"
            assert "contribution" in factor, "Missing contribution in factor"
            assert "description" in factor, "Missing description in factor"

    def test_skills_match_structure(self, client):
        """Test skills_match has correct structure."""
        response = client.get("/api/analytics/ai-explainability/ranking-rationale/test-id")
        data = response.json()

        skills_match = data["skills_match"]
        assert "matched_skills" in skills_match, "Missing matched_skills in skills_match"
        assert "missing_skills" in skills_match, "Missing missing_skills in skills_match"
        assert "additional_skills" in skills_match, "Missing additional_skills in skills_match"
        assert "match_percentage" in skills_match, "Missing match_percentage in skills_match"

        # Verify types
        assert isinstance(skills_match["matched_skills"], list), "matched_skills must be list"
        assert isinstance(skills_match["missing_skills"], list), "missing_skills must be list"
        assert isinstance(skills_match["additional_skills"], list), "additional_skills must be list"
        assert isinstance(skills_match["match_percentage"], (int, float)), "match_percentage must be numeric"


# =============================================================================
# Test 5: Pydantic Schema Validation
# =============================================================================


class TestPydanticSchemaValidation:
    """Tests to verify responses match Pydantic schema definitions."""

    def test_confidence_response_validates_against_schema(self, client):
        """Test confidence response validates against ConfidenceMetricsResponse."""
        from schemas.explainability import ConfidenceMetricsResponse, ConfidenceInterval, ConfidenceDistribution

        with patch('api.analytics.get_db') as mock_get_db:
            async def mock_db_gen():
                mock_db = MagicMock()
                mock_result = MagicMock()
                mock_result.scalars.return_value.all.return_value = []
                mock_db.execute = AsyncMock(return_value=mock_result)
                yield mock_db

            mock_get_db.return_value = mock_db_gen()

            response = client.get("/api/analytics/ai-explainability/confidence")
            data = response.json()

            # Try to construct the Pydantic model from response data
            # This will raise ValidationError if the schema doesn't match
            try:
                ci = ConfidenceInterval(**data["confidence_interval"])
                dist = ConfidenceDistribution(**data["distribution"])
                validated = ConfidenceMetricsResponse(
                    average_confidence=data["average_confidence"],
                    confidence_interval=ci,
                    distribution=dist,
                    confidence_accuracy_correlation=data.get("confidence_accuracy_correlation"),
                )
                assert validated is not None
            except Exception as e:
                pytest.fail(f"Response does not match Pydantic schema: {e}")

    def test_feature_importance_response_validates_against_schema(self, client):
        """Test feature importance response validates against FeatureImportanceResponse."""
        from schemas.explainability import FeatureImportanceResponse, FeatureImportanceItem

        with patch('api.analytics.get_ranking_service') as mock_get_service:
            mock_service = MagicMock()
            mock_model = MagicMock()
            mock_model.get_feature_importance.return_value = {
                "skills_match_ratio": 0.15,
                "experience_relevance": 0.11,
            }
            mock_model.version = "1.0.0"
            mock_model.model_type = "random_forest"
            mock_service.model = mock_model
            mock_get_service.return_value = mock_service

            response = client.get("/api/analytics/ai-explainability/feature-importance")
            data = response.json()

            try:
                features = [
                    FeatureImportanceItem(
                        feature_name=f["feature_name"],
                        importance_score=f["importance_score"],
                        rank=f["rank"],
                        description=f["description"],
                        category=f["category"],
                    )
                    for f in data["features"]
                ]
                validated = FeatureImportanceResponse(
                    features=features,
                    model_version=data["model_version"],
                    model_type=data["model_type"],
                    total_features=data["total_features"],
                    last_updated=data["last_updated"],
                )
                assert validated is not None
            except Exception as e:
                pytest.fail(f"Response does not match Pydantic schema: {e}")

    def test_performance_trends_response_validates_against_schema(self, client):
        """Test performance trends response validates against PerformanceTrendsResponse."""
        from schemas.explainability import (
            PerformanceTrendsResponse,
            ModelPerformanceTrend,
            PerformanceTrendPoint,
        )

        with patch('api.analytics.get_db') as mock_get_db:
            async def mock_db_gen():
                mock_db = MagicMock()
                mock_result = MagicMock()
                mock_result.scalars.return_value.all.return_value = []
                mock_db.execute = AsyncMock(return_value=mock_result)
                yield mock_db

            mock_get_db.return_value = mock_db_gen()

            response = client.get("/api/analytics/ai-explainability/performance-trends")
            data = response.json()

            try:
                models = []
                for model_data in data.get("models", []):
                    points = [
                        PerformanceTrendPoint(
                            timestamp=point["timestamp"],
                            accuracy=point.get("accuracy"),
                            precision=point.get("precision"),
                            recall=point.get("recall"),
                            f1_score=point.get("f1_score"),
                            sample_count=point.get("sample_count", 0),
                        )
                        for point in model_data.get("data_points", [])
                    ]
                    models.append(ModelPerformanceTrend(
                        model_name=model_data["model_name"],
                        model_version=model_data["model_version"],
                        current_accuracy=model_data["current_accuracy"],
                        current_f1_score=model_data["current_f1_score"],
                        trend_direction=model_data["trend_direction"],
                        trend_change_pct=model_data["trend_change_pct"],
                        data_points=points,
                        alert_status=model_data.get("alert_status"),
                    ))

                validated = PerformanceTrendsResponse(
                    period=data["period"],
                    start_date=data["start_date"],
                    end_date=data["end_date"],
                    models=models,
                    overall_trend=data["overall_trend"],
                    total_evaluations=data["total_evaluations"],
                )
                assert validated is not None
            except Exception as e:
                pytest.fail(f"Response does not match Pydantic schema: {e}")


# =============================================================================
# Integration Test: All Endpoints Working Together
# =============================================================================


class TestAllEndpointsIntegration:
    """Tests to verify all endpoints work together."""

    def test_all_endpoints_return_200(self, client):
        """Test all four AI explainability endpoints return 200."""
        endpoints = [
            "/api/analytics/ai-explainability/confidence",
            "/api/analytics/ai-explainability/feature-importance",
            "/api/analytics/ai-explainability/performance-trends",
            "/api/analytics/ai-explainability/ranking-rationale/test-id",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200, f"Endpoint {endpoint} returned {response.status_code}"

    def test_all_responses_are_json(self, client):
        """Test all endpoints return valid JSON."""
        endpoints = [
            "/api/analytics/ai-explainability/confidence",
            "/api/analytics/ai-explainability/feature-importance",
            "/api/analytics/ai-explainability/performance-trends",
            "/api/analytics/ai-explainability/ranking-rationale/test-id",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.headers["content-type"].startswith("application/json"), \
                f"Endpoint {endpoint} did not return JSON"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
