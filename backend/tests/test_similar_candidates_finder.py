"""
Unit tests for Similar Candidates Finder

Tests vector-based candidate similarity search, skill overlap computation,
and candidate recommendation generation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4, UUID
import numpy as np

from analyzers.similar_candidates_finder import (
    SimilarCandidatesFinder,
    SimilarCandidateResult,
    get_similar_candidates_finder,
)
from models import Resume, ResumeAnalysis


class TestSimilarCandidatesFinderInitialization:
    """Test SimilarCandidatesFinder initialization."""

    def test_initialization_with_defaults(self):
        """Test initialization with default parameters."""
        finder = SimilarCandidatesFinder()
        assert finder.threshold == 0.4
        assert finder.model_name == "all-MiniLM-L6-v2"
        assert finder.device is None

    def test_initialization_with_custom_threshold(self):
        """Test initialization with custom threshold."""
        finder = SimilarCandidatesFinder(threshold=0.6)
        assert finder.threshold == 0.6

    def test_initialization_with_custom_model(self):
        """Test initialization with custom model name."""
        finder = SimilarCandidatesFinder(model_name="custom-model")
        assert finder.model_name == "custom-model"

    def test_initialization_with_custom_device(self):
        """Test initialization with custom device."""
        finder = SimilarCandidatesFinder(device="cpu")
        assert finder.device == "cpu"


class TestSimilarityComputation:
    """Test similarity computation methods."""

    @pytest.fixture
    def finder(self):
        """Create a SimilarCandidatesFinder instance for testing."""
        return SimilarCandidatesFinder()

    def test_cosine_similarity_identical_vectors(self, finder):
        """Test cosine similarity with identical vectors."""
        vec1 = np.array([1.0, 2.0, 3.0])
        vec2 = np.array([1.0, 2.0, 3.0])
        result = finder._cosine_similarity(vec1, vec2)
        assert result == pytest.approx(1.0, rel=1e-5)

    def test_cosine_similarity_orthogonal_vectors(self, finder):
        """Test cosine similarity with orthogonal vectors."""
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([0.0, 1.0, 0.0])
        result = finder._cosine_similarity(vec1, vec2)
        assert result == pytest.approx(0.0, rel=1e-5)

    def test_cosine_similarity_opposite_vectors(self, finder):
        """Test cosine similarity with opposite vectors."""
        vec1 = np.array([1.0, 2.0, 3.0])
        vec2 = np.array([-1.0, -2.0, -3.0])
        result = finder._cosine_similarity(vec1, vec2)
        assert result == pytest.approx(-1.0, rel=1e-5)

    def test_cosine_similarity_zero_vectors(self, finder):
        """Test cosine similarity with zero vectors."""
        vec1 = np.array([0.0, 0.0, 0.0])
        vec2 = np.array([1.0, 2.0, 3.0])
        result = finder._cosine_similarity(vec1, vec2)
        assert result == 0.0

    def test_normalize_score_positive(self, finder):
        """Test score normalization for positive cosine similarity."""
        result = finder._normalize_score(0.5)
        assert result == pytest.approx(0.75, rel=1e-5)

    def test_normalize_score_negative(self, finder):
        """Test score normalization for negative cosine similarity."""
        result = finder._normalize_score(-0.5)
        assert result == pytest.approx(0.25, rel=1e-5)

    def test_normalize_score_extreme_positive(self, finder):
        """Test score normalization for extreme positive value."""
        result = finder._normalize_score(1.0)
        assert result == pytest.approx(1.0, rel=1e-5)

    def test_normalize_score_extreme_negative(self, finder):
        """Test score normalization for extreme negative value."""
        result = finder._normalize_score(-1.0)
        assert result == pytest.approx(0.0, rel=1e-5)


class TestSkillsOverlap:
    """Test skills overlap computation."""

    @pytest.fixture
    def finder(self):
        """Create a SimilarCandidatesFinder instance for testing."""
        return SimilarCandidatesFinder()

    def test_full_skills_overlap(self, finder):
        """Test full skills overlap."""
        skills1 = ["Python", "Django", "PostgreSQL"]
        skills2 = ["Python", "Django", "PostgreSQL"]
        score, shared = finder._compute_skills_overlap(skills1, skills2)
        assert score == 1.0
        assert set(shared) == set(skills1)

    def test_partial_skills_overlap(self, finder):
        """Test partial skills overlap."""
        skills1 = ["Python", "Django", "PostgreSQL"]
        skills2 = ["Python", "React", "Node.js"]
        score, shared = finder._compute_skills_overlap(skills1, skills2)
        assert score == pytest.approx(1.0 / 5.0, rel=1e-5)
        assert shared == ["Python"]

    def test_no_skills_overlap(self, finder):
        """Test no skills overlap."""
        skills1 = ["Python", "Django"]
        skills2 = ["React", "Node.js"]
        score, shared = finder._compute_skills_overlap(skills1, skills2)
        assert score == 0.0
        assert shared == []

    def test_case_insensitive_overlap(self, finder):
        """Test case-insensitive skills overlap."""
        skills1 = ["Python", "DJANGO"]
        skills2 = ["python", "django"]
        score, shared = finder._compute_skills_overlap(skills1, skills2)
        assert score == 1.0
        assert len(shared) == 2

    def test_empty_skills_lists(self, finder):
        """Test with empty skills lists."""
        score, shared = finder._compute_skills_overlap([], [])
        assert score == 0.0
        assert shared == []

    def test_none_skills_lists(self, finder):
        """Test with None skills lists."""
        score, shared = finder._compute_skills_overlap(None, None)
        assert score == 0.0
        assert shared == []


class TestExperienceSimilarity:
    """Test experience similarity computation."""

    @pytest.fixture
    def finder(self):
        """Create a SimilarCandidatesFinder instance for testing."""
        return SimilarCandidatesFinder()

    def test_identical_experience(self, finder):
        """Test with identical experience levels."""
        result = finder._compute_experience_similarity(60, 60)
        assert result == 1.0

    def test_similar_experience(self, finder):
        """Test with similar experience levels."""
        result = finder._compute_experience_similarity(60, 66)
        assert result == pytest.approx(0.909, rel=1e-3)

    def test_different_experience(self, finder):
        """Test with different experience levels."""
        result = finder._compute_experience_similarity(12, 120)
        assert result == pytest.approx(0.1, rel=1e-3)

    def test_zero_experience(self, finder):
        """Test with zero experience."""
        result = finder._compute_experience_similarity(0, 60)
        assert result == 0.5

    def test_none_experience(self, finder):
        """Test with None experience."""
        result = finder._compute_experience_similarity(None, 60)
        assert result == 0.5


class TestExplanationBuilding:
    """Test explanation building."""

    @pytest.fixture
    def finder(self):
        """Create a SimilarCandidatesFinder instance for testing."""
        return SimilarCandidatesFinder()

    def test_explanation_with_shared_skills(self, finder):
        """Test explanation with shared skills."""
        explanation = finder._build_explanation(
            shared_skills=["Python", "Django"],
            similarity_score=0.8,
            skills_overlap=0.7,
            exp_similarity=0.9,
        )
        assert "Shared skills" in explanation
        assert "Python" in explanation
        assert "Django" in explanation

    def test_explanation_with_many_shared_skills(self, finder):
        """Test explanation with many shared skills (truncation)."""
        shared_skills = ["Python", "Django", "PostgreSQL", "React", "Node.js", "AWS"]
        explanation = finder._build_explanation(
            shared_skills=shared_skills,
            similarity_score=0.8,
            skills_overlap=0.7,
            exp_similarity=0.9,
        )
        assert "Shared skills" in explanation
        assert "more" in explanation

    def test_explanation_high_similarity(self, finder):
        """Test explanation with high similarity."""
        explanation = finder._build_explanation(
            shared_skills=[],
            similarity_score=0.8,
            skills_overlap=0.5,
            exp_similarity=0.5,
        )
        assert "Very similar profile" in explanation

    def test_explanation_comparable_experience(self, finder):
        """Test explanation with comparable experience."""
        explanation = finder._build_explanation(
            shared_skills=[],
            similarity_score=0.5,
            skills_overlap=0.5,
            exp_similarity=0.9,
        )
        assert "Comparable experience" in explanation

    def test_explanation_default(self, finder):
        """Test default explanation."""
        explanation = finder._build_explanation(
            shared_skills=[],
            similarity_score=0.5,
            skills_overlap=0.5,
            exp_similarity=0.5,
        )
        assert "Similar candidate profile" in explanation


class TestReasonComputation:
    """Test reason computation."""

    @pytest.fixture
    def finder(self):
        """Create a SimilarCandidatesFinder instance for testing."""
        return SimilarCandidatesFinder()

    def test_reason_skills_match(self, finder):
        """Test reason for skills match."""
        reason = finder._compute_reason(
            skills_overlap=0.7,
            similarity_score=0.5,
            exp_similarity=0.5,
        )
        assert reason == "skills_match"

    def test_reason_profile_similarity(self, finder):
        """Test reason for profile similarity."""
        reason = finder._compute_reason(
            skills_overlap=0.5,
            similarity_score=0.8,
            exp_similarity=0.5,
        )
        assert reason == "profile_similarity"

    def test_reason_experience(self, finder):
        """Test reason for experience."""
        reason = finder._compute_reason(
            skills_overlap=0.5,
            similarity_score=0.5,
            exp_similarity=0.9,
        )
        assert reason == "experience"

    def test_reason_overall_fit(self, finder):
        """Test reason for overall fit."""
        reason = finder._compute_reason(
            skills_overlap=0.5,
            similarity_score=0.5,
            exp_similarity=0.5,
        )
        assert reason == "overall_fit"


class TestFindSimilar:
    """Test find_similar method."""

    @pytest.fixture
    def finder(self):
        """Create a SimilarCandidatesFinder instance for testing."""
        return SimilarCandidatesFinder()

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.fixture
    def sample_resume(self):
        """Create a sample resume."""
        return Resume(
            id=uuid4(),
            filename="test.pdf",
            raw_text="Senior Python Developer with 5 years experience",
            status="COMPLETED",
        )

    @pytest.fixture
    def sample_analysis(self):
        """Create a sample resume analysis."""
        return ResumeAnalysis(
            id=uuid4(),
            resume_id=uuid4(),
            skills=["Python", "Django", "PostgreSQL"],
            total_experience_months=60,
        )

    @pytest.mark.asyncio
    async def test_find_similar_returns_results(
        self, finder, mock_db, sample_resume, sample_analysis
    ):
        """Test that find_similar returns results."""
        with patch('analyzers.similar_candidates_finder.select') as mock_select:
            # Setup mock queries
            mock_query = MagicMock()
            mock_select.return_value = mock_query
            mock_query.where.return_value = mock_query
            mock_query.limit.return_value = mock_query

            # Mock source resume
            source_result = MagicMock()
            source_result.scalar_one_or_none.return_value = sample_resume
            source_analysis_result = MagicMock()
            source_analysis_result.scalar_one_or_none.return_value = sample_analysis

            # Mock candidate resumes
            candidate_result = MagicMock()
            candidate_result.scalars.return_value.all.return_value = [
                sample_resume,
                Resume(
                    id=uuid4(),
                    filename="test2.pdf",
                    raw_text="Java Developer with 3 years experience",
                    status="COMPLETED",
                ),
            ]

            analyses_result = MagicMock()
            analyses_result.scalars.return_value.all.return_value = [sample_analysis]

            # Setup execute to return different results based on query
            execute_results = [source_result, source_analysis_result, candidate_result, analyses_result]
            mock_db.execute.side_effect = execute_results

            # Mock encoding
            with patch.object(finder, '_encode_text', return_value=np.array([0.1, 0.2, 0.3])):
                results = await finder.find_similar(mock_db, sample_resume.id, limit=10)

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_find_similar_with_invalid_resume_id(self, finder, mock_db):
        """Test find_similar with invalid resume ID."""
        with patch('analyzers.similar_candidates_finder.select') as mock_select:
            mock_query = MagicMock()
            mock_select.return_value = mock_query
            mock_query.where.return_value = mock_query

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_result

            with pytest.raises(ValueError, match="Resume not found"):
                await finder.find_similar(mock_db, uuid4())


class TestCreateRecommendations:
    """Test create_recommendations method."""

    @pytest.fixture
    def finder(self):
        """Create a SimilarCandidatesFinder instance for testing."""
        return SimilarCandidatesFinder()

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_create_recommendations_stores_results(self, finder, mock_db):
        """Test that create_recommendations stores results in database."""
        resume_id = uuid4()

        # Mock find_similar to return results
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

        with patch.object(finder, 'find_similar', return_value=similar_results):
            with patch('analyzers.similar_candidates_finder.select') as mock_select:
                mock_query = MagicMock()
                mock_select.return_value = mock_query
                mock_query.where.return_value = mock_query

                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = None
                mock_db.execute.return_value = mock_result

                recommendations = await finder.create_recommendations(
                    mock_db, resume_id, limit=10
                )

        assert len(recommendations) == len(similar_results)


class TestSingleton:
    """Test singleton getter function."""

    def test_get_similar_candidates_finder(self):
        """Test that get_similar_candidates_finder returns instance."""
        finder = get_similar_candidates_finder()
        if finder is not None:
            assert isinstance(finder, SimilarCandidatesFinder)

    def test_get_similar_candidates_finder_cached(self):
        """Test that get_similar_candidates_finder caches instance."""
        finder1 = get_similar_candidates_finder()
        finder2 = get_similar_candidates_finder()
        if finder1 is not None:
            assert finder1 is finder2
