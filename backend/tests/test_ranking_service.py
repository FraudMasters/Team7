"""
Tests for RankingService with custom weights support.

Tests the ranking service's ability to apply custom feature weights
and fall back to ML model when no custom weights exist.
"""
import pytest
import numpy as np
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from analyzers.ranking_service import RankingService, RankingFeatures
from models import CandidateRank, JobVacancy, Resume, ResumeAnalysis
from models.ranking_weights_profile import RankingWeightProfile


@pytest.fixture
def sample_resume_data():
    """Sample resume data for testing."""
    return {
        "id": str(uuid4()),
        "title": "Senior Python Developer",
        "skills": ["Python", "Django", "PostgreSQL"],
        "experience": {"total_months": 60},
        "education": {"degree": "bachelor", "level": "bachelor"},
        "updated_at": datetime.now().isoformat(),
    }


@pytest.fixture
def sample_vacancy_data():
    """Sample vacancy data for testing."""
    return {
        "id": str(uuid4()),
        "title": "Python Developer",
        "required_skills": ["Python", "Django"],
        "description": "Looking for experienced Python developer",
    }


@pytest.fixture
def sample_match_result():
    """Sample match result for testing."""
    return {
        "overall_score": 0.8,
        "keyword_score": 0.75,
        "tfidf_score": 0.7,
        "vector_score": 0.85,
    }


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def ranking_service():
    """Create a RankingService instance."""
    return RankingService()


class TestCustomWeightsApplication:
    """Test custom ranking weights application."""

    @pytest.mark.asyncio
    async def test_custom_weights_application(self, ranking_service, mock_db_session):
        """Test that custom weights are applied correctly to feature vector."""
        # Setup: Create test data
        resume_id = uuid4()
        vacancy_id = uuid4()
        organization_id = uuid4()

        # Create mock resume
        mock_resume = MagicMock(spec=Resume)
        mock_resume.id = resume_id
        mock_resume.raw_text = "Senior Python Developer with 5 years experience"
        mock_resume.status = "COMPLETED"
        mock_resume.updated_at = datetime.now()

        # Create mock vacancy
        mock_vacancy = MagicMock(spec=JobVacancy)
        mock_vacancy.id = vacancy_id
        mock_vacancy.title = "Python Developer"
        mock_vacancy.required_skills = ["Python", "Django"]
        mock_vacancy.description = "Looking for Python developer"
        mock_vacancy.organization_id = str(organization_id)

        # Create mock analysis
        mock_analysis = MagicMock(spec=ResumeAnalysis)
        mock_analysis.resume_id = resume_id
        mock_analysis.skills = ["Python", "Django", "PostgreSQL"]
        mock_analysis.raw_text = "Senior Python Developer"

        # Create custom weight profile with emphasis on skills (50%)
        mock_profile = MagicMock(spec=RankingWeightProfile)
        mock_profile.id = uuid4()
        mock_profile.name = "Technical Profile"
        mock_profile.is_active = True
        mock_profile.vacancy_id = vacancy_id
        # Custom weights emphasizing skills_match_ratio (index 4)
        mock_profile.get_weights_as_list.return_value = [
            0.05,  # overall_match_score
            0.05,  # keyword_score
            0.05,  # tfidf_score
            0.05,  # vector_score
            0.50,  # skills_match_ratio (emphasized)
            0.05,  # experience_months
            0.10,  # experience_relevance
            0.05,  # education_level
            0.02,  # recent_experience
            0.02,  # skill_rarity
            0.02,  # title_similarity
            0.02,  # freshness_score
            0.02,  # completeness_score
        ]

        # Setup mock database queries
        def mock_execute(query):
            result = AsyncMock()
            query_str = str(query)

            if "Resume" in query_str:
                result.scalar_one_or_none.return_value = mock_resume
            elif "JobVacancy" in query_str:
                result.scalar_one_or_none.return_value = mock_vacancy
            elif "ResumeAnalysis" in query_str:
                result.scalar_one_or_none.return_value = mock_analysis
            elif "RankingWeightProfile" in query_str and "vacancy_id" in query_str.lower():
                result.scalar_one_or_none.return_value = mock_profile
            elif "MatchResult" in query_str:
                result.scalar_one_or_none.return_value = None
            elif "CandidateRank" in query_str:
                result.scalar_one_or_none.return_value = None
            else:
                result.scalar_one_or_none.return_value = None

            return result

        mock_db_session.execute = AsyncMock(side_effect=mock_execute)
        mock_db_session.commit = AsyncMock()
        mock_db_session.add = MagicMock()

        # Execute: Rank the candidate
        result = await ranking_service.rank_candidate(
            db=mock_db_session,
            resume_id=resume_id,
            vacancy_id=vacancy_id,
            use_experiment=False,
        )

        # Verify: Check that custom weights were applied
        assert result is not None
        assert "rank_score" in result
        assert 0.0 <= result["rank_score"] <= 1.0

        # The rank_score should be influenced by custom weights
        # Since skills_match_ratio has 50% weight and candidate has good skills match,
        # the score should reflect this
        assert result["rank_score"] > 0.3, "Custom weights should influence score"

        # Verify database operations
        assert mock_db_session.commit.called
        assert mock_db_session.add.called

    @pytest.mark.asyncio
    async def test_fallback_to_ml_model_when_no_custom_weights(
        self, ranking_service, mock_db_session
    ):
        """Test that service falls back to ML model when no custom weights exist."""
        # Setup
        resume_id = uuid4()
        vacancy_id = uuid4()

        mock_resume = MagicMock(spec=Resume)
        mock_resume.id = resume_id
        mock_resume.raw_text = "Python Developer"
        mock_resume.status = "COMPLETED"
        mock_resume.updated_at = datetime.now()

        mock_vacancy = MagicMock(spec=JobVacancy)
        mock_vacancy.id = vacancy_id
        mock_vacancy.title = "Python Developer"
        mock_vacancy.required_skills = ["Python"]
        mock_vacancy.description = "Python role"
        mock_vacancy.organization_id = None

        mock_analysis = MagicMock(spec=ResumeAnalysis)
        mock_analysis.resume_id = resume_id
        mock_analysis.skills = ["Python"]
        mock_analysis.raw_text = "Python Developer"

        def mock_execute(query):
            result = AsyncMock()
            query_str = str(query)

            if "Resume" in query_str:
                result.scalar_one_or_none.return_value = mock_resume
            elif "JobVacancy" in query_str:
                result.scalar_one_or_none.return_value = mock_vacancy
            elif "ResumeAnalysis" in query_str:
                result.scalar_one_or_none.return_value = mock_analysis
            else:
                result.scalar_one_or_none.return_value = None

            return result

        mock_db_session.execute = AsyncMock(side_effect=mock_execute)
        mock_db_session.commit = AsyncMock()
        mock_db_session.add = MagicMock()

        # Execute
        result = await ranking_service.rank_candidate(
            db=mock_db_session,
            resume_id=resume_id,
            vacancy_id=vacancy_id,
            use_experiment=False,
        )

        # Verify: ML model should be used (backward compatibility)
        assert result is not None
        assert "rank_score" in result
        assert 0.0 <= result["rank_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_get_ranking_weights_vacancy_specific(
        self, ranking_service, mock_db_session
    ):
        """Test fetching vacancy-specific ranking weights."""
        vacancy_id = uuid4()

        mock_profile = MagicMock(spec=RankingWeightProfile)
        mock_profile.name = "Vacancy Profile"
        mock_profile.vacancy_id = vacancy_id
        mock_profile.is_active = True
        mock_profile.get_weights_as_list.return_value = [0.1] * 10 + [0.0] * 3

        def mock_execute(query):
            result = AsyncMock()
            result.scalar_one_or_none.return_value = mock_profile
            return result

        mock_db_session.execute = AsyncMock(side_effect=mock_execute)

        # Execute
        weights = await ranking_service.get_ranking_weights(
            db=mock_db_session,
            vacancy_id=vacancy_id,
        )

        # Verify
        assert weights is not None
        assert len(weights) == 13
        assert isinstance(weights, np.ndarray)

    @pytest.mark.asyncio
    async def test_get_ranking_weights_organization_default(
        self, ranking_service, mock_db_session
    ):
        """Test fetching organization default ranking weights."""
        organization_id = uuid4()

        mock_profile = MagicMock(spec=RankingWeightProfile)
        mock_profile.name = "Org Profile"
        mock_profile.organization_id = organization_id
        mock_profile.is_active = True
        mock_profile.get_weights_as_list.return_value = [0.077] * 13

        def mock_execute(query):
            result = AsyncMock()
            result.scalar_one_or_none.return_value = mock_profile
            return result

        mock_db_session.execute = AsyncMock(side_effect=mock_execute)

        # Execute
        weights = await ranking_service.get_ranking_weights(
            db=mock_db_session,
            organization_id=organization_id,
        )

        # Verify
        assert weights is not None
        assert len(weights) == 13
        assert all(abs(w - 0.077) < 0.01 for w in weights)

    @pytest.mark.asyncio
    async def test_get_ranking_weights_none_when_not_found(
        self, ranking_service, mock_db_session
    ):
        """Test that get_ranking_weights returns None when no profile found."""
        def mock_execute(query):
            result = AsyncMock()
            result.scalar_one_or_none.return_value = None
            return result

        mock_db_session.execute = AsyncMock(side_effect=mock_execute)

        # Execute
        weights = await ranking_service.get_ranking_weights(
            db=mock_db_session,
            organization_id=uuid4(),
        )

        # Verify
        assert weights is None

    @pytest.mark.asyncio
    async def test_vacancy_weights_override_organization_weights(
        self, ranking_service, mock_db_session
    ):
        """Test that vacancy-specific weights take priority over organization weights."""
        organization_id = uuid4()
        vacancy_id = uuid4()

        # Vacancy profile should be returned (priority)
        vacancy_profile = MagicMock(spec=RankingWeightProfile)
        vacancy_profile.name = "Vacancy Profile"
        vacancy_profile.vacancy_id = vacancy_id
        vacancy_profile.is_active = True
        vacancy_profile.get_weights_as_list.return_value = [0.5] + [0.05] * 12

        call_count = [0]

        def mock_execute(query):
            result = AsyncMock()
            call_count[0] += 1
            # First call (vacancy query) returns vacancy profile
            if call_count[0] == 1:
                result.scalar_one_or_none.return_value = vacancy_profile
            else:
                result.scalar_one_or_none.return_value = None
            return result

        mock_db_session.execute = AsyncMock(side_effect=mock_execute)

        # Execute
        weights = await ranking_service.get_ranking_weights(
            db=mock_db_session,
            organization_id=organization_id,
            vacancy_id=vacancy_id,
        )

        # Verify: Vacancy weights should be used
        assert weights is not None
        assert weights[0] == 0.5  # First weight from vacancy profile
