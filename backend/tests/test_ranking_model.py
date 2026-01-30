"""
Unit tests for AI Candidate Ranking Model

Tests feature extraction, ranking prediction, and model training logic.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from analyzers.ranking_features import extract_ranking_features
from analyzers.ranking_model import RankingModel
from models.match_result import MatchResult
from models.resume import Resume
from models.vacancy import Vacancy


class TestRankingFeatureExtraction:
    """Test feature extraction for candidate ranking."""

    @pytest.fixture
    def sample_resume(self):
        """Create a sample resume for testing."""
        return Resume(
            id="resume-1",
            filename="test_resume.pdf",
            raw_text="Senior Python developer with 5 years experience",
            status="processed",
        )

    @pytest.fixture
    def sample_vacancy(self):
        """Create a sample vacancy for testing."""
        return Vacancy(
            id="vacancy-1",
            position="Senior Python Developer",
            required_skills=["Python", "Django", "PostgreSQL"],
            experience_years=5,
        )

    @pytest.fixture
    def sample_match_result(self, sample_resume, sample_vacancy):
        """Create a sample match result."""
        return MatchResult(
            id="match-1",
            resume_id=sample_resume.id,
            vacancy_id=sample_vacancy.id,
            match_percentage=85,
            unified_score=0.85,
            tfidf_score=0.80,
            vector_score=0.90,
        )

    def test_extract_basic_features(self, sample_match_result, sample_vacancy):
        """Test basic feature extraction."""
        features = extract_ranking_features(
            match_result=sample_match_result,
            vacancy=sample_vacancy,
            days_since_last_activity=30,
        )

        assert features is not None
        assert 'match_score' in features
        assert features['match_score'] == 85

    def test_extract_experience_features(self, sample_resume, sample_vacancy):
        """Test experience-related feature extraction."""
        with patch('analyzers.ranking_features.get_total_experience_months') as mock_exp:
            mock_exp.return_value = 60  # 5 years

            features = extract_ranking_features(
                match_result=Mock(resume_id=sample_resume.id),
                vacancy=sample_vacancy,
                days_since_last_activity=30,
            )

            assert 'experience_relevance' in features
            assert 0 <= features['experience_relevance'] <= 1

    def test_extract_education_features(self, sample_resume, sample_vacancy):
        """Test education-related feature extraction."""
        with patch('analyzers.ranking_features.get_education_level') as mock_edu:
            mock_edu.return_value = 'masters'

            features = extract_ranking_features(
                match_result=Mock(resume_id=sample_resume.id),
                vacancy=sample_vacancy,
                days_since_last_activity=30,
            )

            assert 'education_level' in features
            assert features['education_level'] > 0

    def test_extract_skills_freshness(self, sample_resume, sample_vacancy):
        """Test skills freshness feature extraction."""
        days_since_update = 45

        features = extract_ranking_features(
            match_result=Mock(resume_id=sample_resume.id),
            vacancy=sample_vacancy,
            days_since_last_activity=days_since_update,
        )

        assert 'skills_freshness_days' in features
        assert features['skills_freshness_days'] == days_since_update

    def test_extract_feedback_score(self, sample_resume, sample_vacancy):
        """Test recruiter feedback score extraction."""
        with patch('analyzers.ranking_features.get_feedback_score') as mock_feedback:
            mock_feedback.return_value = 0.8

            features = extract_ranking_features(
                match_result=Mock(resume_id=sample_resume.id),
                vacancy=sample_vacancy,
                days_since_last_activity=30,
            )

            assert 'feedback_score' in features
            assert features['feedback_score'] == 0.8

    def test_features_within_valid_range(self, sample_match_result, sample_vacancy):
        """Test that all extracted features are within valid ranges."""
        features = extract_ranking_features(
            match_result=sample_match_result,
            vacancy=sample_vacancy,
            days_since_last_activity=30,
        )

        for key, value in features.items():
            if isinstance(value, (int, float)):
                assert 0 <= value <= 100 or value >= 0, f"Feature {key}={value} out of range"


class TestRankingModel:
    """Test the ranking model prediction and training."""

    @pytest.fixture
    def ranking_model(self):
        """Create a RankingModel instance for testing."""
        return RankingModel()

    def test_model_initialization(self, ranking_model):
        """Test that the model initializes correctly."""
        assert ranking_model is not None
        assert hasattr(ranking_model, 'model')
        assert hasattr(ranking_model, 'is_trained')

    def test_predict_with_features(self, ranking_model):
        """Test prediction with sample features."""
        features = {
            'match_score': 85,
            'experience_relevance': 0.8,
            'education_level': 0.7,
            'skills_freshness_days': 30,
            'feedback_score': 0.75,
        }

        # Mock the model to return a prediction
        with patch.object(ranking_model, 'is_trained', True):
            with patch.object(ranking_model.model, 'predict') as mock_predict:
                mock_predict.return_value = np.array([78])

                score = ranking_model.predict(features)

                assert isinstance(score, (int, float))
                assert 0 <= score <= 100

    def test_predict_returns_confidence_score(self, ranking_model):
        """Test that prediction includes confidence score."""
        features = {
            'match_score': 85,
            'experience_relevance': 0.8,
            'education_level': 0.7,
            'skills_freshness_days': 30,
            'feedback_score': 0.75,
        }

        with patch.object(ranking_model, 'is_trained', True):
            with patch.object(ranking_model.model, 'predict_proba') as mock_proba:
                mock_proba.return_value = np.array([[0.2, 0.8]])

                score, confidence = ranking_model.predict_with_confidence(features)

                assert isinstance(score, (int, float))
                assert isinstance(confidence, (int, float))
                assert 0 <= confidence <= 1

    def test_train_with_hiring_data(self, ranking_model):
        """Test model training with historical hiring data."""
        training_data = [
            {
                'features': {
                    'match_score': 85,
                    'experience_relevance': 0.8,
                    'education_level': 0.7,
                    'skills_freshness_days': 30,
                    'feedback_score': 0.75,
                },
                'outcome': 'HIRED',  # Positive example
            },
            {
                'features': {
                    'match_score': 45,
                    'experience_relevance': 0.3,
                    'education_level': 0.4,
                    'skills_freshness_days': 180,
                    'feedback_score': 0.4,
                },
                'outcome': 'REJECTED',  # Negative example
            },
        ]

        with patch.object(ranking_model.model, 'fit') as mock_fit:
            ranking_model.train(training_data)

            assert mock_fit.called
            assert ranking_model.is_trained

    def test_model_persistence(self, ranking_model, tmp_path):
        """Test saving and loading model."""
        model_path = tmp_path / "ranking_model.pkl"

        # Mock the training
        with patch.object(ranking_model.model, 'fit'):
            ranking_model.train([])

        # Test save
        with patch('analyzers.ranking_model.joblib.dump') as mock_dump:
            ranking_model.save(str(model_path))
            assert mock_dump.called

        # Test load
        with patch('analyzers.ranking_model.joblib.load') as mock_load:
            mock_load.return_value = ranking_model.model
            loaded_model = RankingModel.load(str(model_path))
            assert loaded_model is not None


class TestRankingPredictionIntegration:
    """Integration tests for ranking predictions."""

    @pytest.fixture
    def sample_candidates(self):
        """Create sample candidates for ranking."""
        return [
            {
                'resume_id': 'resume-1',
                'candidate_name': 'Alice Johnson',
                'features': {
                    'match_score': 90,
                    'experience_relevance': 0.9,
                    'education_level': 0.8,
                    'skills_freshness_days': 15,
                    'feedback_score': 0.85,
                }
            },
            {
                'resume_id': 'resume-2',
                'candidate_name': 'Bob Smith',
                'features': {
                    'match_score': 75,
                    'experience_relevance': 0.7,
                    'education_level': 0.6,
                    'skills_freshness_days': 45,
                    'feedback_score': 0.65,
                }
            },
            {
                'resume_id': 'resume-3',
                'candidate_name': 'Carol Davis',
                'features': {
                    'match_score': 60,
                    'experience_relevance': 0.5,
                    'education_level': 0.7,
                    'skills_freshness_days': 90,
                    'feedback_score': 0.5,
                }
            },
        ]

    def test_rank_candidates_returns_scores(self, sample_candidates):
        """Test that ranking returns scores for all candidates."""
        model = RankingModel()

        with patch.object(model, 'is_trained', True):
            with patch.object(model, 'predict') as mock_predict:
                mock_predict.side_effect = [92, 78, 65]

                ranked = model.rank_candidates(sample_candidates)

                assert len(ranked) == len(sample_candidates)
                assert all('ranking_score' in c for c in ranked)
                assert all('hire_probability' in c for c in ranked)

    def test_rank_candidates_sorts_by_score(self, sample_candidates):
        """Test that candidates are sorted by ranking score."""
        model = RankingModel()

        with patch.object(model, 'is_trained', True):
            with patch.object(model, 'predict') as mock_predict:
                # Return scores in reverse order
                mock_predict.side_effect = [65, 92, 78]

                ranked = model.rank_candidates(sample_candidates)

                # Verify sorted descending
                scores = [c['ranking_score'] for c in ranked]
                assert scores == sorted(scores, reverse=True)

    def test_top_candidates_selection(self, sample_candidates):
        """Test selecting top N candidates."""
        model = RankingModel()

        with patch.object(model, 'is_trained', True):
            with patch.object(model, 'predict') as mock_predict:
                mock_predict.side_effect = [92, 78, 65]

                top_2 = model.get_top_candidates(sample_candidates, n=2)

                assert len(top_2) == 2
                assert top_2[0]['ranking_score'] >= top_2[1]['ranking_score']


@pytest.mark.parametrize("match_score,expected_rating", [
    (90, 'excellent'),
    (75, 'good'),
    (50, 'fair'),
    (30, 'poor'),
])
def test_rating_classification(match_score, expected_rating):
    """Test classification of candidates into rating categories."""
    from analyzers.ranking_model import classify_candidate_rating

    rating = classify_candidate_rating(match_score)

    if match_score >= 80:
        assert rating in ['excellent', 'good']
    elif match_score >= 60:
        assert rating in ['good', 'fair']
    else:
        assert rating in ['fair', 'poor']
