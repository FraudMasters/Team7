"""
Unit tests for Candidate Recommendation Service

Tests the orchestration of all recommendation types including
similar candidates, best fit for vacancy, and at-risk candidates.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4, UUID
from datetime import datetime

from analyzers.candidate_recommendation_service import (
    CandidateRecommendationService,
    RecommendationSummary,
    VacancyRecommendations,
    get_candidate_recommendation_service,
)
from analyzers.similar_candidates_finder import SimilarCandidateResult
from analyzers.risk_predictor import RiskPredictionResult


class TestCandidateRecommendationServiceInitialization:
    """Test service initialization."""

    def test_initialization_with_defaults(self):
        """Test initialization with default parameters."""
        service = CandidateRecommendationService()
        assert service.enable_ab_testing is True
        assert service.experiment_ratio == 0.2
        assert service.ranking_service is not None
        assert service.similar_finder is not None
        assert service.risk_predictor is not None

    def test_initialization_with_custom_settings(self):
        """Test initialization with custom A/B testing settings."""
        service = CandidateRecommendationService(
            enable_ab_testing=False,
            experiment_ratio=0.5
        )
        assert service.enable_ab_testing is False
        assert service.experiment_ratio == 0.5

    def test_initialization_with_custom_services(self):
        """Test initialization with custom service instances."""
        mock_ranking = Mock()
        mock_finder = Mock()
        mock_predictor = Mock()

        service = CandidateRecommendationService(
            ranking_service=mock_ranking,
            similar_finder=mock_finder,
            risk_predictor=mock_predictor,
        )

        assert service.ranking_service is mock_ranking
        assert service.similar_finder is mock_finder
        assert service.risk_predictor is mock_predictor


class TestGetSimilarCandidates:
    """Test get_similar_candidates method."""

    @pytest.fixture
    def service(self):
        """Create a service instance for testing."""
        return CandidateRecommendationService()

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_get_similar_candidates_returns_results(self, service, mock_db):
        """Test that get_similar_candidates returns results."""
        resume_id = uuid4()

        # Mock similar finder
        similar_results = [
            SimilarCandidateResult(
                resume_id=uuid4(),
                similarity_score=0.8,
                skills_overlap_score=0.7,
                experience_similarity=0.9,
                overall_score=0.8,
                shared_skills=["Python"],
                reason="skills_match",
                explanation="Shared skills: Python",
            )
        ]

        with patch.object(service.similar_finder, 'find_similar', return_value=similar_results):
            with patch.object(service, '_store_similar_candidate_recommendations'):
                results = await service.get_similar_candidates(
                    mock_db, resume_id, limit=10, store_recommendations=False
                )

        assert len(results) == len(similar_results)
        assert isinstance(results[0], SimilarCandidateResult)

    @pytest.mark.asyncio
    async def test_get_similar_candidates_stores_recommendations(self, service, mock_db):
        """Test that get_similar_candidates stores recommendations when requested."""
        resume_id = uuid4()

        similar_results = [
            SimilarCandidateResult(
                resume_id=uuid4(),
                similarity_score=0.8,
                skills_overlap_score=0.7,
                experience_similarity=0.9,
                overall_score=0.8,
                shared_skills=["Python"],
                reason="skills_match",
                explanation="Shared skills: Python",
            )
        ]

        with patch.object(service.similar_finder, 'find_similar', return_value=similar_results):
            with patch.object(service, '_store_similar_candidate_recommendations') as mock_store:
                await service.get_similar_candidates(
                    mock_db, resume_id, limit=10, store_recommendations=True
                )

                mock_store.assert_called_once()


class TestGetBestFitForVacancy:
    """Test get_best_fit_for_vacancy method."""

    @pytest.fixture
    def service(self):
        """Create a service instance for testing."""
        return CandidateRecommendationService()

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_get_best_fit_for_vacancy_returns_results(self, service, mock_db):
        """Test that get_best_fit_for_vacancy returns results."""
        vacancy_id = uuid4()

        # Mock ranking service
        rankings = [
            {
                "resume_id": str(uuid4()),
                "rank_score": 0.85,
                "recommendation": "excellent",
                "confidence": 0.9,
                "ranking_factors": {},
            }
        ]

        with patch.object(service.ranking_service, 'rank_candidates_for_vacancy', return_value=rankings):
            with patch.object(service, '_analyze_vacancy_skill_gaps', return_value={}):
                with patch.object(service, '_store_best_fit_recommendations'):
                    result = await service.get_best_fit_for_vacancy(
                        mock_db, vacancy_id, limit=20, store_recommendations=False
                    )

        assert isinstance(result, VacancyRecommendations)
        assert result.vacancy_id == str(vacancy_id)
        assert len(result.top_candidates) == len(rankings)

    @pytest.mark.asyncio
    async def test_get_best_fit_for_vacancy_includes_skill_gaps(self, service, mock_db):
        """Test that get_best_fit_for_vacancy includes skill gaps when requested."""
        vacancy_id = uuid4()

        rankings = [
            {
                "resume_id": str(uuid4()),
                "rank_score": 0.85,
                "recommendation": "excellent",
                "confidence": 0.9,
                "ranking_factors": {},
            }
        ]

        skill_gaps = {
            "required_skills": ["Python", "Django"],
            "common_gaps": ["Django"],
        }

        with patch.object(service.ranking_service, 'rank_candidates_for_vacancy', return_value=rankings):
            with patch.object(service, '_analyze_vacancy_skill_gaps', return_value=skill_gaps):
                with patch.object(service, '_store_best_fit_recommendations'):
                    result = await service.get_best_fit_for_vacancy(
                        mock_db, vacancy_id, limit=20, include_skill_gaps=True, store_recommendations=False
                    )

        assert result.skill_gaps_summary == skill_gaps


class TestGetBestFitCandidates:
    """Test get_best_fit_candidates API-compatible method."""

    @pytest.fixture
    def service(self):
        """Create a service instance for testing."""
        return CandidateRecommendationService()

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_get_best_fit_candidates_returns_dict(self, service, mock_db):
        """Test that get_best_fit_candidates returns a dictionary."""
        vacancy_id = uuid4()

        rankings = [
            {
                "resume_id": str(uuid4()),
                "rank_score": 0.85,
                "recommendation": "excellent",
                "confidence": 0.9,
                "ranking_factors": {},
                "feature_contributions": {},
            }
        ]

        with patch.object(service.ranking_service, 'rank_candidates_for_vacancy', return_value=rankings):
            with patch('analyzers.candidate_recommendation_service.select') as mock_select:
                mock_query = MagicMock()
                mock_select.return_value = mock_query
                mock_query.where.return_value = mock_query

                # Mock vacancy query
                vacancy_result = MagicMock()
                vacancy = MagicMock()
                vacancy.required_skills = ["Python", "Django"]
                vacancy_result.scalar_one_or_none.return_value = vacancy

                # Mock resume queries
                resume_result = MagicMock()
                resume = MagicMock()
                resume.candidate_name = "John Doe"
                resume.title = "Senior Developer"
                resume.work_experience = []
                resume_result.scalar_one_or_none.return_value = resume

                # Mock analysis queries
                analysis_result = MagicMock()
                analysis = MagicMock()
                analysis.skills = ["Python"]
                analysis_result.scalar_one_or_none.return_value = analysis

                execute_results = [vacancy_result, resume_result, analysis_result]
                mock_db.execute.side_effect = execute_results

                result = await service.get_best_fit_candidates(
                    mock_db, vacancy_id, limit=20, use_experiment=False
                )

        assert isinstance(result, dict)
        assert "vacancy_id" in result
        assert "candidates" in result
        assert "total_candidates" in result

    @pytest.mark.asyncio
    async def test_get_best_fit_candidates_filters_by_score(self, service, mock_db):
        """Test that get_best_fit_candidates filters by minimum score."""
        vacancy_id = uuid4()

        rankings = [
            {
                "resume_id": str(uuid4()),
                "rank_score": 0.85,
                "recommendation": "excellent",
                "confidence": 0.9,
                "ranking_factors": {},
                "feature_contributions": {},
            },
            {
                "resume_id": str(uuid4()),
                "rank_score": 0.3,  # Below threshold
                "recommendation": "maybe",
                "confidence": 0.5,
                "ranking_factors": {},
                "feature_contributions": {},
            }
        ]

        with patch.object(service.ranking_service, 'rank_candidates_for_vacancy', return_value=rankings):
            with patch('analyzers.candidate_recommendation_service.select') as mock_select:
                mock_query = MagicMock()
                mock_select.return_value = mock_query
                mock_query.where.return_value = mock_query

                vacancy_result = MagicMock()
                vacancy = MagicMock()
                vacancy.required_skills = []
                vacancy_result.scalar_one_or_none.return_value = vacancy

                resume_result = MagicMock()
                resume = MagicMock()
                resume.candidate_name = "Test"
                resume.title = "Developer"
                resume.work_experience = []
                resume_result.scalar_one_or_none.return_value = resume

                analysis_result = MagicMock()
                analysis = MagicMock()
                analysis.skills = []
                analysis_result.scalar_one_or_none.return_value = analysis

                execute_results = [vacancy_result, resume_result, analysis_result, resume_result, analysis_result]
                mock_db.execute.side_effect = execute_results

                result = await service.get_best_fit_candidates(
                    mock_db, vacancy_id, limit=20, min_score=0.5, use_experiment=False
                )

        assert result["total_candidates"] == 1


class TestGetCandidatesAtRisk:
    """Test get_candidates_at_risk method."""

    @pytest.fixture
    def service(self):
        """Create a service instance for testing."""
        return CandidateRecommendationService()

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_get_candidates_at_risk_returns_results(self, service, mock_db):
        """Test that get_candidates_at_risk returns results."""
        risk_results = [
            RiskPredictionResult(
                resume_id=str(uuid4()),
                risk_score=0.7,
                risk_level="high",
                primary_risk_factors=["High-demand skills"],
                explanation="Test",
                recommended_actions=["Contact"],
                confidence=0.8,
                model_version="v1.0",
                predicted_at=datetime.now().isoformat(),
            )
        ]

        with patch.object(service.risk_predictor, 'predict_at_risk_candidates', return_value=risk_results):
            # Fix: Use the correct method name
            with patch.object(service, '_store_at_risk_recommendations'):
                results = await service.get_candidates_at_risk(
                    mock_db, limit=15, store_recommendations=False
                )

        assert len(results) == len(risk_results)
        assert isinstance(results[0], RiskPredictionResult)

    @pytest.mark.asyncio
    async def test_get_candidates_at_risk_filters_by_score(self, service, mock_db):
        """Test that get_candidates_at_risk filters by minimum score."""
        risk_results = [
            RiskPredictionResult(
                resume_id=str(uuid4()),
                risk_score=0.8,
                risk_level="high",
                primary_risk_factors=[],
                explanation="Test",
                recommended_actions=[],
                confidence=0.8,
                model_version="v1.0",
                predicted_at=datetime.now().isoformat(),
            ),
            RiskPredictionResult(
                resume_id=str(uuid4()),
                risk_score=0.3,  # Below threshold
                risk_level="low",
                primary_risk_factors=[],
                explanation="Test",
                recommended_actions=[],
                confidence=0.5,
                model_version="v1.0",
                predicted_at=datetime.now().isoformat(),
            )
        ]

        with patch.object(service.risk_predictor, 'predict_candidates_at_risk', return_value=risk_results):
            with patch.object(service, '_store_at_risk_recommendations'):
                results = await service.get_candidates_at_risk(
                    mock_db, limit=15, min_risk_score=0.5, store_recommendations=False
                )

        # Should only return the high-risk candidate
        assert len(results) == 1
        assert results[0].risk_score >= 0.5


class TestGetAtRiskCandidates:
    """Test get_at_risk_candidates API-compatible method."""

    @pytest.fixture
    def service(self):
        """Create a service instance for testing."""
        return CandidateRecommendationService()

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_get_at_risk_candidates_returns_dict(self, service, mock_db):
        """Test that get_at_risk_candidates returns a dictionary."""
        risk_results = [
            RiskPredictionResult(
                resume_id=str(uuid4()),
                risk_score=0.7,
                risk_level="high",
                primary_risk_factors=["High-demand skills"],
                explanation="Test",
                recommended_actions=["Contact"],
                confidence=0.8,
                model_version="v1.0",
                predicted_at=datetime.now().isoformat(),
            )
        ]

        # Add required attributes for API compatibility
        for result in risk_results:
            result.risk_factors = ["High-demand skills"]
            result.days_since_contact = 5
            result.recommended_action = "Contact candidate"
            result.feature_contributions = {}

        with patch.object(service, 'get_candidates_at_risk', return_value=risk_results):
            with patch('analyzers.candidate_recommendation_service.select') as mock_select:
                mock_query = MagicMock()
                mock_select.return_value = mock_query
                mock_query.where.return_value = mock_query

                resume_result = MagicMock()
                resume = MagicMock()
                resume.candidate_name = "Jane Doe"
                resume.title = "Developer"
                resume_result.scalar_one_or_none.return_value = resume

                mock_db.execute.return_value = resume_result

                result = await service.get_at_risk_candidates(
                    mock_db, limit=20, use_experiment=False
                )

        assert isinstance(result, dict)
        assert "total_candidates" in result
        assert "candidates" in result
        assert result["total_candidates"] == len(risk_results)


class TestGetComprehensiveRecommendations:
    """Test get_comprehensive_recommendations method."""

    @pytest.fixture
    def service(self):
        """Create a service instance for testing."""
        return CandidateRecommendationService()

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_get_comprehensive_recommendations_with_all_types(self, service, mock_db):
        """Test comprehensive recommendations with all types."""
        resume_id = uuid4()
        vacancy_id = uuid4()

        similar_results = [
            SimilarCandidateResult(
                resume_id=uuid4(),
                similarity_score=0.8,
                skills_overlap_score=0.7,
                experience_similarity=0.9,
                overall_score=0.8,
                shared_skills=["Python"],
                reason="skills_match",
                explanation="Test",
            )
        ]

        risk_results = [
            RiskPredictionResult(
                resume_id=str(uuid4()),
                risk_score=0.7,
                risk_level="high",
                primary_risk_factors=[],
                explanation="Test",
                recommended_actions=[],
                confidence=0.8,
                model_version="v1.0",
                predicted_at=datetime.now().isoformat(),
            )
        ]

        with patch.object(service, 'get_similar_candidates', return_value=similar_results):
            with patch.object(service, 'get_best_fit_for_vacancy') as mock_best_fit:
                mock_best_fit.return_value = MagicMock(top_candidates=[])
            with patch.object(service, 'get_candidates_at_risk', return_value=risk_results):
                result = await service.get_comprehensive_recommendations(
                    mock_db,
                    resume_id=resume_id,
                    vacancy_id=vacancy_id,
                    include_at_risk=True
                )

        assert isinstance(result, RecommendationSummary)
        assert len(result.similar_candidates) == len(similar_results)
        assert len(result.at_risk_candidates) == len(risk_results)

    @pytest.mark.asyncio
    async def test_get_comprehensive_recommendations_custom_limits(self, service, mock_db):
        """Test comprehensive recommendations with custom limits."""
        resume_id = uuid4()

        with patch.object(service, 'get_similar_candidates') as mock_similar:
            with patch.object(service, 'get_best_fit_for_vacancy') as mock_best_fit:
                with patch.object(service, 'get_candidates_at_risk') as mock_risk:
                    await service.get_comprehensive_recommendations(
                        mock_db,
                        resume_id=resume_id,
                        limits={"similar": 5, "best_fit": 10, "at_risk": 8}
                    )

                    mock_similar.assert_called_with(mock_db, resume_id, limit=5, store_recommendations=True)


class TestSubmitFeedback:
    """Test submit_feedback method."""

    @pytest.fixture
    def service(self):
        """Create a service instance for testing."""
        return CandidateRecommendationService()

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_submit_feedback_success(self, service, mock_db):
        """Test successful feedback submission."""
        recommendation_id = uuid4()

        with patch('analyzers.candidate_recommendation_service.select') as mock_select:
            mock_query = MagicMock()
            mock_select.return_value = mock_query
            mock_query.where.return_value = mock_query

            mock_result = MagicMock()
            recommendation = MagicMock()
            mock_result.scalar_one_or_none.return_value = recommendation
            mock_db.execute.return_value = mock_result

            result = await service.submit_feedback(
                mock_db,
                recommendation_id,
                was_helpful=True,
                was_contacted=True,
                outcome="hired",
            )

        assert isinstance(result, dict)
        assert "id" in result
        assert result["was_helpful"] is True

    @pytest.mark.asyncio
    async def test_submit_feedback_invalid_recommendation(self, service, mock_db):
        """Test feedback submission with invalid recommendation ID."""
        recommendation_id = uuid4()

        with patch('analyzers.candidate_recommendation_service.select') as mock_select:
            mock_query = MagicMock()
            mock_select.return_value = mock_query
            mock_query.where.return_value = mock_query

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            with pytest.raises(ValueError, match="not found"):
                await service.submit_feedback(
                    mock_db,
                    recommendation_id,
                    was_helpful=True,
                )


class TestExperimentGroupAssignment:
    """Test A/B test experiment group assignment."""

    @pytest.fixture
    def service(self):
        """Create a service instance for testing."""
        return CandidateRecommendationService(enable_ab_testing=True, experiment_ratio=1.0)

    def test_assign_experiment_group_enabled(self, service):
        """Test experiment group assignment when enabled."""
        is_experiment, group = service._assign_experiment_group(use_experiment=True)

        # With experiment_ratio=1.0, should always be in experiment
        assert is_experiment is True
        assert group in ["control", "treatment"]

    def test_assign_experiment_group_disabled(self, service):
        """Test experiment group assignment when disabled."""
        service.enable_ab_testing = False

        is_experiment, group = service._assign_experiment_group(use_experiment=True)

        assert is_experiment is False
        assert group is None

    def test_assign_experiment_group_not_requested(self, service):
        """Test experiment group assignment when not requested."""
        is_experiment, group = service._assign_experiment_group(use_experiment=False)

        assert is_experiment is False
        assert group is None


class TestRecommendationSummary:
    """Test RecommendationSummary dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        summary = RecommendationSummary(
            generated_at=datetime.now().isoformat()
        )

        result_dict = summary.to_dict()

        assert isinstance(result_dict, dict)
        assert "similar_candidates" in result_dict
        assert "best_fit_for_vacancy" in result_dict
        assert "at_risk_candidates" in result_dict
        assert "total_recommendations" in result_dict


class TestVacancyRecommendations:
    """Test VacancyRecommendations dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        recommendations = VacancyRecommendations(
            vacancy_id=str(uuid4()),
            generated_at=datetime.now().isoformat()
        )

        result_dict = recommendations.to_dict()

        assert isinstance(result_dict, dict)
        assert "vacancy_id" in result_dict
        assert "top_candidates" in result_dict
        assert "skill_gaps_summary" in result_dict


class TestSingleton:
    """Test singleton getter function."""

    def test_get_candidate_recommendation_service(self):
        """Test that get_candidate_recommendation_service returns instance."""
        service = get_candidate_recommendation_service()
        assert isinstance(service, CandidateRecommendationService)

    def test_get_candidate_recommendation_service_cached(self):
        """Test that get_candidate_recommendation_service caches instance."""
        service1 = get_candidate_recommendation_service()
        service2 = get_candidate_recommendation_service()
        assert service1 is service2
