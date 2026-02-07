"""
Unit tests for AI-powered Risk Predictor

Tests feature extraction, risk model prediction, and candidate risk assessment.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4, UUID
import numpy as np

from analyzers.risk_predictor import (
    RiskFeatures,
    RiskModel,
    RiskPredictor,
    RiskPredictionResult,
    get_risk_predictor,
)


class TestRiskFeaturesExtraction:
    """Test risk feature extraction."""

    def test_extract_features_returns_array(self):
        """Test that extract_features returns numpy array."""
        resume_data = {
            "skills": ["Python", "Django"],
            "experience": {"total_months": 60},
            "education": {"level": "bachelor"},
        }
        pipeline_data = {
            "stage": "screening",
            "applied_at": (datetime.now() - timedelta(days=10)).isoformat(),
        }

        features = RiskFeatures.extract_features(resume_data, pipeline_data)

        assert isinstance(features, np.ndarray)
        assert len(features) == len(RiskFeatures.FEATURE_NAMES)

    def test_extract_features_all_features_present(self):
        """Test that all expected features are present."""
        resume_data = {
            "skills": ["Python", "Django"],
            "experience": {"total_months": 60},
            "education": {"level": "bachelor"},
            "location": "New York",
        }
        pipeline_data = {
            "stage": "screening",
            "applied_at": (datetime.now() - timedelta(days=10)).isoformat(),
            "last_contact_at": (datetime.now() - timedelta(days=2)).isoformat(),
        }
        vacancy_data = {"location": "New York"}

        features = RiskFeatures.extract_features(resume_data, pipeline_data, vacancy_data)

        assert len(features) == len(RiskFeatures.FEATURE_NAMES)

    def test_compute_days_in_pipeline(self):
        """Test days in pipeline computation."""
        pipeline = {
            "applied_at": (datetime.now() - timedelta(days=30)).isoformat()
        }
        days = RiskFeatures._compute_days_in_pipeline(pipeline)
        assert days == pytest.approx(30 / 90, rel=1e-5)

    def test_compute_days_in_pipeline_no_date(self):
        """Test days in pipeline with no date."""
        pipeline = {}
        days = RiskFeatures._compute_days_in_pipeline(pipeline)
        assert days == 0.0

    def test_compute_days_since_last_contact(self):
        """Test days since last contact computation."""
        pipeline = {
            "last_contact_at": (datetime.now() - timedelta(days=10)).isoformat()
        }
        days = RiskFeatures._compute_days_since_last_contact(pipeline)
        assert days == pytest.approx(10 / 30, rel=1e-5)

    def test_compute_resume_freshness(self):
        """Test resume freshness computation."""
        resume = {
            "updated_at": (datetime.now() - timedelta(days=30)).isoformat()
        }
        freshness = RiskFeatures._compute_resume_freshness(resume)
        assert freshness == pytest.approx(30 / 60, rel=1e-5)

    def test_compute_skills_rarity(self):
        """Test skills rarity computation."""
        resume = {"skills": ["Machine Learning", "Deep Learning", "TensorFlow"]}
        rarity = RiskFeatures._compute_skills_rarity(resume)
        assert 0 <= rarity <= 1

    def test_compute_skills_demand(self):
        """Test skills demand computation."""
        resume = {"skills": ["Python", "AWS", "Kubernetes"]}
        demand = RiskFeatures._compute_skills_demand(resume)
        assert 0 <= demand <= 1

    def test_compute_engagement_score(self):
        """Test engagement score computation."""
        pipeline = {
            "email_open_rate": 0.8,
            "response_rate": 0.7,
            "profile_views": 5,
            "login_frequency_days": 3,
        }
        engagement = RiskFeatures._compute_engagement_score(pipeline)
        # Returns risk score (1 - engagement)
        assert 0 <= engagement <= 1

    def test_compute_response_time(self):
        """Test response time computation."""
        pipeline = {"avg_response_hours": 48}
        response_time = RiskFeatures._compute_response_time(pipeline)
        assert 0 <= response_time <= 1

    def test_compute_missed_communications(self):
        """Test missed communications computation."""
        pipeline = {"missed_communications": 2, "total_communications": 10}
        missed = RiskFeatures._compute_missed_communications(pipeline)
        assert 0 <= missed <= 1

    def test_normalize_interview_stage(self):
        """Test interview stage normalization."""
        stages = ["applied", "screening", "initial_interview", "technical_interview"]
        for stage in stages:
            pipeline = {"stage": stage}
            normalized = RiskFeatures._normalize_interview_stage(pipeline)
            assert 0 <= normalized <= 1

    def test_compute_stage_duration(self):
        """Test stage duration computation."""
        pipeline = {
            "stage": "screening",
            "stage_entered_at": (datetime.now() - timedelta(days=7)).isoformat()
        }
        duration = RiskFeatures._compute_stage_duration(pipeline)
        assert 0 <= duration <= 1

    def test_estimate_competing_applications(self):
        """Test competing applications estimation."""
        resume = {
            "skills": ["Python", "Java", "JavaScript", "React", "Node.js", "AWS", "Docker"],
            "experience": {"total_months": 72},
            "education": {"level": "master"},
        }
        competing = RiskFeatures._estimate_competing_applications(resume)
        assert 0 <= competing <= 1

    def test_compute_salary_gap(self):
        """Test salary gap computation."""
        resume = {"salary_expectation": 120000}
        vacancy = {"salary_max": 100000}
        gap = RiskFeatures._compute_salary_gap(resume, vacancy)
        assert 0 <= gap <= 1

    def test_compute_location_match_perfect(self):
        """Test location match - perfect match."""
        resume = {"location": "San Francisco"}
        vacancy = {"location": "San Francisco"}
        match = RiskFeatures._compute_location_match(resume, vacancy)
        assert match == 0.0

    def test_compute_location_match_no_match(self):
        """Test location match - no match."""
        resume = {"location": "New York"}
        vacancy = {"location": "San Francisco"}
        match = RiskFeatures._compute_location_match(resume, vacancy)
        assert match > 0.5

    def test_compute_experience_level(self):
        """Test experience level computation."""
        resume = {"experience": {"total_months": 120}}
        level = RiskFeatures._compute_experience_level(resume)
        assert level == 1.0

    def test_compute_education_level(self):
        """Test education level computation."""
        resume = {"education": {"degree": "PhD in Computer Science"}}
        level = RiskFeatures._compute_education_level(resume)
        assert level == 1.0


class TestRiskModel:
    """Test risk model prediction and training."""

    @pytest.fixture
    def risk_model(self):
        """Create a RiskModel instance for testing."""
        return RiskModel(model_type="random_forest")

    def test_model_initialization(self, risk_model):
        """Test that the model initializes correctly."""
        assert risk_model is not None
        assert risk_model.model_type == "random_forest"
        assert hasattr(risk_model, 'model')
        assert hasattr(risk_model, 'scaler')
        assert hasattr(risk_model, 'is_trained')

    def test_train_with_sample_data(self, risk_model):
        """Test model training with sample data."""
        X = np.random.rand(100, len(RiskFeatures.FEATURE_NAMES))
        y = np.random.randint(0, 2, 100)

        with patch.object(risk_model, '_save_model'):
            metrics = risk_model.train(X, y)

        assert 'accuracy' in metrics
        assert 'n_samples' in metrics
        assert risk_model.is_trained

    def test_predict_proba_returns_score(self, risk_model):
        """Test that predict_proba returns a risk score."""
        features = np.random.rand(len(RiskFeatures.FEATURE_NAMES))

        with patch.object(risk_model, 'is_trained', True):
            with patch.object(risk_model.model, 'predict_proba') as mock_predict:
                mock_predict.return_value = np.array([[0.3, 0.7]])
                score = risk_model.predict_proba(features)

        assert isinstance(score, float)
        assert 0 <= score <= 1

    def test_predict_proba_untrained_model(self, risk_model):
        """Test predict_proba with untrained model."""
        features = np.random.rand(len(RiskFeatures.FEATURE_NAMES))

        risk_model.is_trained = False
        score = risk_model.predict_proba(features)

        assert isinstance(score, float)
        assert 0 <= score <= 1

    def test_get_feature_importance(self, risk_model):
        """Test getting feature importance."""
        with patch.object(risk_model, 'is_trained', True):
            with patch.object(risk_model.model, 'feature_importances_',
                            return_value=np.array([0.1, 0.2, 0.3] + [0.0] * 12)):
                importance = risk_model.get_feature_importance()

        assert isinstance(importance, dict)
        assert len(importance) > 0


class TestRiskPredictor:
    """Test the risk predictor service."""

    @pytest.fixture
    def predictor(self):
        """Create a RiskPredictor instance for testing."""
        return RiskPredictor()

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.fixture
    def sample_resume(self):
        """Create a sample resume."""
        from models import Resume
        return Resume(
            id=uuid4(),
            filename="test.pdf",
            raw_text="Senior Python Developer",
            status="COMPLETED",
        )

    @pytest.fixture
    def sample_analysis(self):
        """Create a sample resume analysis."""
        from models import ResumeAnalysis
        return ResumeAnalysis(
            id=uuid4(),
            resume_id=uuid4(),
            skills=["Python", "Django"],
            raw_data={
                "experience": {"total_months": 60},
                "education": {"level": "bachelor"},
            },
        )

    def test_predictor_initialization(self, predictor):
        """Test that the predictor initializes correctly."""
        assert predictor is not None
        assert hasattr(predictor, 'model')
        assert hasattr(predictor, 'ab_test_ratio')

    @pytest.mark.asyncio
    async def test_predict_risk_returns_result(
        self, predictor, mock_db, sample_resume, sample_analysis
    ):
        """Test that predict_risk returns a result."""
        with patch('analyzers.risk_predictor.select') as mock_select:
            # Setup mocks for database queries
            mock_query = MagicMock()
            mock_select.return_value = mock_query
            mock_query.where.return_value = mock_query

            # Mock resume query result
            resume_result = MagicMock()
            resume_result.scalar_one_or_none.return_value = sample_resume

            # Mock analysis query result
            analysis_result = MagicMock()
            analysis_result.scalar_one_or_none.return_value = sample_analysis

            # Setup execute to return different results
            execute_results = [resume_result, analysis_result]
            mock_db.execute.side_effect = execute_results

            # Mock commit
            mock_db.commit = MagicMock()

            with patch.object(predictor.model, 'predict_proba', return_value=0.6):
                with patch.object(predictor.model, 'get_feature_importance', return_value={}):
                    result = await predictor.predict_risk(
                        mock_db, sample_resume.id, use_experiment=False
                    )

        assert isinstance(result, RiskPredictionResult)
        assert result.risk_score == 0.6

    @pytest.mark.asyncio
    async def test_predict_risk_with_invalid_resume(self, predictor, mock_db):
        """Test predict_risk with invalid resume ID."""
        with patch('analyzers.risk_predictor.select') as mock_select:
            mock_query = MagicMock()
            mock_select.return_value = mock_query
            mock_query.where.return_value = mock_query

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            with pytest.raises(ValueError, match="Resume not found"):
                await predictor.predict_risk(mock_db, uuid4())

    def test_score_to_risk_level(self, predictor):
        """Test conversion of score to risk level."""
        assert predictor._score_to_risk_level(0.2) == "low"
        assert predictor._score_to_risk_level(0.4) == "medium"
        assert predictor._score_to_risk_level(0.6) == "high"
        assert predictor._score_to_risk_level(0.9) == "critical"

    def test_get_primary_risk_factors(self, predictor):
        """Test getting primary risk factors."""
        feature_contributions = {
            "days_in_pipeline": 0.8,
            "skills_demand_score": 0.6,
            "engagement_score": 0.4,
        }

        factors = predictor._get_primary_risk_factors(feature_contributions, top_n=2)

        assert len(factors) == 2
        assert isinstance(factors, list)

    def test_generate_explanation(self, predictor):
        """Test explanation generation."""
        explanation = predictor._generate_explanation(
            risk_score=0.7,
            risk_level="high",
            primary_factors=["High-demand skills", "Low engagement"],
            pipeline_data={}
        )

        assert "high risk" in explanation.lower()
        assert isinstance(explanation, str)

    def test_generate_recommendations(self, predictor):
        """Test recommendation generation."""
        actions = predictor._generate_recommendations(
            risk_level="high",
            primary_factors=["Low engagement", "Time since last contact"],
            pipeline_data={}
        )

        assert isinstance(actions, list)
        assert len(actions) > 0


class TestRiskPredictionResult:
    """Test RiskPredictionResult dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = RiskPredictionResult(
            resume_id=str(uuid4()),
            risk_score=0.7,
            risk_level="high",
            primary_risk_factors=["High-demand skills"],
            explanation="Test explanation",
            recommended_actions=["Contact candidate"],
            confidence=0.8,
            model_version="v1.0",
            predicted_at=datetime.now().isoformat(),
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert "resume_id" in result_dict
        assert "risk_score" in result_dict
        assert "risk_level" in result_dict
        assert result_dict["risk_score"] == 0.7


class TestSingleton:
    """Test singleton getter function."""

    def test_get_risk_predictor(self):
        """Test that get_risk_predictor returns instance."""
        predictor = get_risk_predictor()
        assert isinstance(predictor, RiskPredictor)

    def test_get_risk_predictor_cached(self):
        """Test that get_risk_predictor caches instance."""
        predictor1 = get_risk_predictor()
        predictor2 = get_risk_predictor()
        assert predictor1 is predictor2


@pytest.mark.parametrize("score,expected_level", [
    (0.1, "low"),
    (0.35, "medium"),
    (0.6, "high"),
    (0.9, "critical"),
])
def test_risk_level_classification(score, expected_level):
    """Test risk level classification for various scores."""
    predictor = RiskPredictor()
    level = predictor._score_to_risk_level(score)
    assert level == expected_level
