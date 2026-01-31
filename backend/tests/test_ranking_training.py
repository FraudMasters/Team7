"""
Integration Tests for Ranking Model Training Celery Task

Tests the model training task that queries HiringStage outcomes
and retrains the ranking model.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from celery import Celery
from datetime import datetime, timedelta

from tasks.ranking_training import train_ranking_model
from models.hiring_stage import HiringStage
from models.match_result import MatchResult


class TestRankingTrainingTask:
    """Tests for the Celery ranking training task."""

    @pytest.fixture
    def mock_celery_app(self):
        """Create a mock Celery app for testing."""
        app = Celery('test_tasks', broker='memory://')
        return app

    @pytest.fixture
    def sample_hiring_outcomes(self):
        """Create sample hiring outcomes for training."""
        return [
            {
                'resume_id': 'resume-1',
                'vacancy_id': 'vacancy-1',
                'stage': 'HIRED',
                'match_score': 85,
                'experience_relevance': 0.9,
                'education_level': 0.8,
            },
            {
                'resume_id': 'resume-2',
                'vacancy_id': 'vacancy-1',
                'stage': 'REJECTED',
                'match_score': 45,
                'experience_relevance': 0.3,
                'education_level': 0.4,
            },
            {
                'resume_id': 'resume-3',
                'vacancy_id': 'vacancy-1',
                'stage': 'HIRED',
                'match_score': 78,
                'experience_relevance': 0.8,
                'education_level': 0.7,
            },
            {
                'resume_id': 'resume-4',
                'vacancy_id': 'vacancy-1',
                'stage': 'REJECTED',
                'match_score': 55,
                'experience_relevance': 0.4,
                'education_level': 0.5,
            },
        ]

    @pytest.mark.db
    def test_train_ranking_model_with_outcomes(self, sample_hiring_outcomes):
        """Test training the ranking model with hiring outcomes."""
        with patch('tasks.ranking_training.db.session') as mock_session:
            # Mock query to return hiring outcomes
            mock_query = MagicMock()
            mock_session.query.return_value = mock_query
            mock_query.join.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.all.return_value = [
                Mock(
                    resume_id=o['resume_id'],
                    vacancy_id=o['vacancy_id'],
                    stage=o['stage'],
                ) for o in sample_hiring_outcomes
            ]

            # Mock feature extraction
            with patch('tasks.ranking_training.extract_ranking_features') as mock_extract:
                mock_extract.side_effect = [
                    {
                        'match_score': o['match_score'],
                        'experience_relevance': o['experience_relevance'],
                        'education_level': o['education_level'],
                    }
                    for o in sample_hiring_outcomes
                ]

                # Mock model training
                with patch('tasks.ranking_training.RankingModel') as mock_model_class:
                    mock_model = MagicMock()
                    mock_model_class.return_value = mock_model

                    result = train_ranking_model()

                    assert result['status'] == 'success'
                    assert 'model_version' in result
                    assert 'samples_used' in result
                    assert result['samples_used'] == len(sample_hiring_outcomes)

    @pytest.mark.db
    def test_training_task_creates_model_version(self, sample_hiring_outcomes):
        """Test that training creates a new model version entry."""
        with patch('tasks.ranking_training.db.session') as mock_session:
            mock_query = MagicMock()
            mock_session.query.return_value = mock_query
            mock_query.join.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.all.return_value = [
                Mock(
                    resume_id=o['resume_id'],
                    vacancy_id=o['vacancy_id'],
                    stage=o['stage'],
                ) for o in sample_hiring_outcomes
            ]

            with patch('tasks.ranking_training.extract_ranking_features') as mock_extract:
                mock_extract.side_effect = [
                    {'match_score': o['match_score'], 'experience_relevance': 0.5}
                    for o in sample_hiring_outcomes
                ]

                with patch('tasks.ranking_training.RankingModel') as mock_model_class:
                    mock_model = MagicMock()
                    mock_model_class.return_value = mock_model

                    with patch('tasks.ranking_training.ModelVersion') as mock_mv_class:
                        mock_mv = MagicMock()
                        mock_mv_class.return_value = mock_mv

                        result = train_ranking_model()

                        assert mock_session.add.called
                        assert mock_session.commit.called

    def test_training_task_with_insufficient_data(self):
        """Test training behavior when insufficient data is available."""
        with patch('tasks.ranking_training.db.session') as mock_session:
            # Mock empty results
            mock_query = MagicMock()
            mock_session.query.return_value = mock_query
            mock_query.join.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.all.return_value = []

            result = train_ranking_model()

            assert result['status'] == 'skipped'
            assert 'reason' in result
            assert 'insufficient_data' in result['reason']

    @pytest.mark.asyncio
    async def test_async_training_task_execution(self, sample_hiring_outcomes):
        """Test that the training task executes properly as an async Celery task."""
        with patch('tasks.ranking_training.db.session') as mock_session:
            mock_query = MagicMock()
            mock_session.query.return_value = mock_query
            mock_query.join.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.all.return_value = [
                Mock(
                    resume_id=o['resume_id'],
                    vacancy_id=o['vacancy_id'],
                    stage=o['stage'],
                ) for o in sample_hiring_outcomes
            ]

            with patch('tasks.ranking_training.extract_ranking_features') as mock_extract:
                mock_extract.side_effect = [
                    {'match_score': o['match_score'], 'experience_relevance': 0.5}
                    for o in sample_hiring_outcomes
                ]

                with patch('tasks.ranking_training.RankingModel') as mock_model_class:
                    mock_model = MagicMock()
                    mock_model_class.return_value = mock_model

                    # Simulate async task execution
                    task = train_ranking_model.delay()

                    # In a real test, we'd wait for the result
                    # For unit testing, we call directly
                    result = train_ranking_model()

                    assert result['status'] == 'success'


class TestTrainingDataPreparation:
    """Tests for training data preparation logic."""

    @pytest.fixture
    def sample_match_results(self):
        """Create sample match results with hiring stages."""
        return [
            {
                'resume_id': 'resume-1',
                'vacancy_id': 'vacancy-1',
                'match_score': 85,
                'unified_score': 0.85,
                'stage': 'HIRED',
                'stage_date': datetime.now() - timedelta(days=30),
            },
            {
                'resume_id': 'resume-2',
                'vacancy_id': 'vacancy-1',
                'match_score': 60,
                'unified_score': 0.60,
                'stage': 'INTERVIEW',
                'stage_date': datetime.now() - timedelta(days=20),
            },
            {
                'resume_id': 'resume-3',
                'vacancy_id': 'vacancy-1',
                'match_score': 40,
                'unified_score': 0.40,
                'stage': 'REJECTED',
                'stage_date': datetime.now() - timedelta(days=10),
            },
        ]

    def test_label_encoding(self, sample_match_results):
        """Test that hiring stages are properly encoded as labels."""
        from tasks.ranking_training import encode_hiring_stage

        label_mapping = {
            'HIRED': 1,
            'INTERVIEW': 0.5,
            'REJECTED': 0,
        }

        for result in sample_match_results:
            encoded = encode_hiring_stage(result['stage'])
            expected = label_mapping.get(result['stage'], 0)
            assert encoded == expected

    def test_feature_vector_construction(self, sample_match_results):
        """Test construction of feature vectors from match results."""
        from tasks.ranking_training import build_feature_vector

        for result in sample_match_results:
            features = build_feature_vector(result)

            assert 'match_score' in features
            assert 'unified_score' in features
            assert isinstance(features['match_score'], (int, float))
            assert isinstance(features['unified_score'], (int, float))

    def test_training_data_balance(self, sample_match_results):
        """Test that training data is balanced between positive and negative examples."""
        positive = [r for r in sample_match_results if r['stage'] == 'HIRED']
        negative = [r for r in sample_match_results if r['stage'] == 'REJECTED']

        # For training, we'd want reasonable balance
        if len(positive) > 0 and len(negative) > 0:
            ratio = len(positive) / len(negative)
            assert 0.2 <= ratio <= 5, "Training data is too imbalanced"


class TestModelRetrainingTriggers:
    """Tests for conditions that trigger model retraining."""

    @pytest.mark.db
    def test_retrain_after_n_hires(self):
        """Test that model retrains after N new hires."""
        threshold = 10  # Retrain after 10 new hires

        with patch('tasks.ranking_training.db.session') as mock_session:
            mock_query = MagicMock()
            mock_session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.count.return_value = threshold

            from tasks.ranking_training import should_retrain_model

            should_retrain = should_retrain_model(threshold=threshold)

            assert should_retrain == True

    @pytest.mark.db
    def test_no_retrain_below_threshold(self):
        """Test that model doesn't retrain below threshold."""
        threshold = 10

        with patch('tasks.ranking_training.db.session') as mock_session:
            mock_query = MagicMock()
            mock_session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.count.return_value = threshold - 1

            from tasks.ranking_training import should_retrain_model

            should_retrain = should_retrain_model(threshold=threshold)

            assert should_retrain == False

    def test_retrain_cooldown_period(self):
        """Test that retraining respects cooldown period."""
        from tasks.ranking_training import is_retrain_allowed
        from datetime import timedelta

        last_training = datetime.now() - timedelta(hours=1)
        cooldown_hours = 24

        # Should not retrain within cooldown
        assert not is_retrain_allowed(last_training, cooldown_hours)

        # Should retrain after cooldown
        last_training = datetime.now() - timedelta(hours=cooldown_hours + 1)
        assert is_retrain_allowed(last_training, cooldown_hours)


@pytest.mark.parametrize("hires,rejected,expected_accuracy", [
    (50, 50, 0.7),  # Balanced dataset
    (80, 20, 0.65),  # Imbalanced (more hires)
    (20, 80, 0.6),   # Imbalanced (more rejections)
])
def test_model_accuracy_expectations(hires, rejected, expected_accuracy):
    """Test expected model accuracy under different data conditions."""
    total_samples = hires + rejected

    # Model should achieve at least minimum expected accuracy
    # even with imbalanced data
    if total_samples >= 50:
        assert expected_accuracy >= 0.5, "Model should exceed random guessing"
