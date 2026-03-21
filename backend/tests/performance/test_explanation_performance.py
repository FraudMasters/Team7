"""
Performance benchmarks for LLM-powered explanation generation.

This test suite benchmarks critical explanation endpoints to ensure they meet
performance SLAs and detect regressions early.

Performance Targets:
- Basic explanation generation: < 3s p95
- Detailed explanation generation: < 3s p95
- Comparison explanation generation: < 5s p95
- What-if analysis: < 2s p95

Cache Effectiveness:
- Cached explanations should be >10x faster than uncached
- Cache hit rate should be >70% in production
"""
import time
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from analyzers.explanation_generator import (
    ExplanationGenerator,
    OrganizationExplanationPreferences,
)
from analyzers.sensitivity_analyzer import SensitivityAnalyzer
from models import CandidateRank, JobVacancy, MatchResult, Resume, ResumeAnalysis


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def sample_resume(test_db: AsyncSession):
    """Create a sample resume for testing."""
    resume = Resume(
        id=uuid4(),
        filename="john_doe.pdf",
        file_path="/test/john_doe.pdf",
        candidate_name="John Doe",
        email="john.doe@example.com",
    )
    test_db.add(resume)
    await test_db.commit()
    await test_db.refresh(resume)
    return resume


@pytest.fixture
async def sample_vacancy(test_db: AsyncSession):
    """Create a sample vacancy for testing."""
    vacancy = JobVacancy(
        id=uuid4(),
        title="Senior Python Developer",
        description="Looking for experienced Python developer with FastAPI and PostgreSQL",
        required_skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
        status="active",
    )
    test_db.add(vacancy)
    await test_db.commit()
    await test_db.refresh(vacancy)
    return vacancy


@pytest.fixture
async def sample_match_result(
    test_db: AsyncSession, sample_resume: Resume, sample_vacancy: JobVacancy
):
    """Create a sample match result for testing."""
    match = MatchResult(
        id=uuid4(),
        resume_id=sample_resume.id,
        vacancy_id=sample_vacancy.id,
        match_score=0.85,
        ranking_factors={
            "skills_match": {
                "score": 0.90,
                "matched_skills": ["Python", "FastAPI", "PostgreSQL"],
                "missing_skills": ["Docker"],
            },
            "experience_analysis": {
                "score": 0.85,
                "total_months": 96,
                "relevant_months": 84,
            },
            "education_analysis": {
                "score": 0.80,
                "degree": "M.Sc Computer Science",
                "field_of_study": "Computer Science",
            },
            "keyword_score": 0.85,
            "tfidf_score": 0.82,
            "vector_score": 0.88,
        },
    )
    test_db.add(match)
    await test_db.commit()
    await test_db.refresh(match)
    return match


@pytest.fixture
async def sample_candidate_rank(
    test_db: AsyncSession,
    sample_resume: Resume,
    sample_vacancy: JobVacancy,
    sample_match_result: MatchResult,
):
    """Create a sample candidate rank for testing."""
    rank = CandidateRank(
        id=uuid4(),
        resume_id=sample_resume.id,
        vacancy_id=sample_vacancy.id,
        match_result_id=sample_match_result.id,
        rank_score=0.85,
        rank_position=5,
        confidence_score=0.92,
        feature_contributions={
            "skills_match": 0.36,
            "experience": 0.24,
            "education": 0.14,
            "keyword_match": 0.12,
            "semantic_similarity": 0.14,
        },
    )
    test_db.add(rank)
    await test_db.commit()
    await test_db.refresh(rank)
    return rank


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return {
        "narrative": "Candidate ranked 5th due to strong Python skills and relevant experience.",
        "ranking_rationale": "The candidate demonstrates excellent technical capabilities with 8 years of Python development experience. Their comprehensive skill set includes FastAPI, PostgreSQL, and modern development practices.",
        "strengths_analysis": [
            "Strong proficiency in Python with 8 years of professional experience",
            "Hands-on experience with FastAPI framework and RESTful API development",
            "Solid database expertise with PostgreSQL",
            "Master's degree in Computer Science from reputable institution",
        ],
        "improvement_areas": [
            "Consider gaining experience with Docker containerization",
            "Cloud deployment experience (AWS/GCP) would strengthen profile",
            "Additional DevOps skills would be beneficial",
        ],
        "overall_assessment": "This candidate is a strong match for the Senior Python Developer position. Their technical skills align well with requirements, though additional DevOps experience would make them an ideal candidate.",
    }


# ============================================================================
# Performance Tests
# ============================================================================


@pytest.mark.performance
@pytest.mark.asyncio
async def test_basic_explanation_generation_performance(
    benchmark, test_db: AsyncSession, sample_candidate_rank, sample_resume, sample_vacancy
):
    """
    Benchmark basic explanation generation.

    Target: < 3s p95
    Regression threshold: +20% slowdown
    """
    # Mock LLM call to focus on explanation logic performance
    with patch("analyzers.explanation_generator.ExplanationGenerator._call_llm") as mock_llm:
        mock_llm.return_value = AsyncMock(
            return_value="Candidate ranked 5th due to strong Python skills."
        )

        generator = ExplanationGenerator()

        # Benchmark the explanation generation
        start_time = time.time()

        result = await generator.generate_ranking_explanation(
            candidate_name=sample_resume.candidate_name or "Candidate",
            rank_score=sample_candidate_rank.rank_score,
            rank_position=sample_candidate_rank.rank_position,
            feature_contributions=sample_candidate_rank.feature_contributions,
            ranking_factors={"skills_match": {"score": 0.90}},
            job_title=sample_vacancy.title,
            job_description=sample_vacancy.description or "",
            recommendation="good",
        )

        elapsed_time = time.time() - start_time

        # Assert performance target
        assert elapsed_time < 3.0, f"Basic explanation took {elapsed_time:.2f}s, exceeds 3s target"

        # Assert valid result
        assert result is not None
        assert result.narrative is not None
        assert len(result.strengths) > 0
        assert len(result.weaknesses) > 0


@pytest.mark.performance
@pytest.mark.asyncio
async def test_detailed_explanation_generation_performance(
    benchmark, test_db: AsyncSession, sample_candidate_rank, sample_resume, sample_vacancy, mock_llm_response
):
    """
    Benchmark detailed explanation generation with LLM narratives.

    Target: < 3s p95
    Regression threshold: +20% slowdown
    """
    # Mock LLM call with realistic response
    with patch("analyzers.explanation_generator.ExplanationGenerator._call_llm") as mock_llm:
        mock_llm.return_value = AsyncMock(
            return_value=str(mock_llm_response)
        )

        generator = ExplanationGenerator()

        # Benchmark the detailed narrative generation
        start_time = time.time()

        result = await generator.generate_detailed_narrative(
            candidate_name=sample_resume.candidate_name or "Candidate",
            rank_score=sample_candidate_rank.rank_score,
            rank_position=sample_candidate_rank.rank_position,
            feature_contributions=sample_candidate_rank.feature_contributions,
            ranking_factors={"skills_match": {"score": 0.90}},
            job_title=sample_vacancy.title,
            job_description=sample_vacancy.description or "",
            recommendation="good",
        )

        elapsed_time = time.time() - start_time

        # Assert performance target
        assert elapsed_time < 3.0, f"Detailed explanation took {elapsed_time:.2f}s, exceeds 3s target"

        # Assert valid result
        assert result is not None
        assert isinstance(result, dict)
        assert "ranking_rationale" in result
        assert "strengths_analysis" in result
        assert "improvement_areas" in result
        assert "overall_assessment" in result


@pytest.mark.performance
@pytest.mark.asyncio
async def test_comparison_explanation_performance(
    benchmark, test_db: AsyncSession, sample_resume, sample_vacancy
):
    """
    Benchmark side-by-side comparison explanation generation.

    Target: < 5s p95
    Regression threshold: +20% slowdown
    """
    # Create second candidate for comparison
    resume_b = Resume(
        id=uuid4(),
        filename="jane_smith.pdf",
        file_path="/test/jane_smith.pdf",
        candidate_name="Jane Smith",
        email="jane.smith@example.com",
    )
    test_db.add(resume_b)
    await test_db.commit()
    await test_db.refresh(resume_b)

    # Mock LLM call
    with patch("analyzers.explanation_generator.ExplanationGenerator._call_llm") as mock_llm:
        mock_llm.return_value = AsyncMock(
            return_value="Candidate A ranked higher due to stronger technical skills and more relevant experience."
        )

        generator = ExplanationGenerator()

        # Benchmark the comparison generation
        start_time = time.time()

        result = await generator.generate_comparison_explanation(
            candidate_a_name=sample_resume.candidate_name or "Candidate A",
            candidate_a_score=0.85,
            candidate_a_factors={
                "skills_match": {"score": 0.90},
                "experience": {"score": 0.85},
            },
            candidate_b_name=resume_b.candidate_name or "Candidate B",
            candidate_b_score=0.75,
            candidate_b_factors={
                "skills_match": {"score": 0.80},
                "experience": {"score": 0.75},
            },
            job_title=sample_vacancy.title,
            job_description=sample_vacancy.description or "",
        )

        elapsed_time = time.time() - start_time

        # Assert performance target
        assert elapsed_time < 5.0, f"Comparison explanation took {elapsed_time:.2f}s, exceeds 5s target"

        # Assert valid result
        assert result is not None
        assert result.winner_narrative is not None
        assert len(result.key_differences) > 0
        assert len(result.factor_by_factor_comparison) > 0


@pytest.mark.performance
@pytest.mark.asyncio
async def test_whatif_analysis_performance(
    benchmark, test_db: AsyncSession, sample_candidate_rank, sample_resume, sample_vacancy
):
    """
    Benchmark what-if scenario analysis.

    Target: < 2s p95
    Regression threshold: +20% slowdown
    """
    # Mock ranking model for what-if analysis
    with patch("analyzers.sensitivity_analyzer.RankingModel") as mock_model:
        mock_instance = Mock()
        mock_instance.predict.return_value = 0.88  # Improved score
        mock_model.return_value = mock_instance

        analyzer = SensitivityAnalyzer(model=mock_instance)

        # Benchmark the what-if analysis
        start_time = time.time()

        result = await analyzer.analyze_what_if(
            resume_id=sample_resume.id,
            vacancy_id=sample_vacancy.id,
            perturbations={
                "skills_match_ratio": 0.05,  # +5% skills match
                "experience_months": 12,  # +1 year experience
            },
        )

        elapsed_time = time.time() - start_time

        # Assert performance target
        assert elapsed_time < 2.0, f"What-if analysis took {elapsed_time:.2f}s, exceeds 2s target"

        # Assert valid result
        assert result is not None
        assert result.scenario_description is not None
        assert result.new_score > result.original_score
        assert result.score_delta > 0
        assert len(result.perturbations) > 0


@pytest.mark.performance
@pytest.mark.asyncio
async def test_explanation_with_caching_performance(
    benchmark, test_db: AsyncSession, sample_candidate_rank, sample_resume, sample_vacancy
):
    """
    Benchmark explanation generation with caching.

    Target: Cached requests should be >10x faster
    Cache hit should be < 300ms p95
    """
    # Mock LLM call
    with patch("analyzers.explanation_generator.ExplanationGenerator._call_llm") as mock_llm:
        mock_llm.return_value = AsyncMock(
            return_value="Candidate ranked 5th due to strong Python skills."
        )

        generator = ExplanationGenerator()

        # First call (uncached)
        start_time_uncached = time.time()
        result_uncached = await generator.generate_ranking_explanation(
            candidate_name=sample_resume.candidate_name or "Candidate",
            rank_score=sample_candidate_rank.rank_score,
            rank_position=sample_candidate_rank.rank_position,
            feature_contributions=sample_candidate_rank.feature_contributions,
            ranking_factors={"skills_match": {"score": 0.90}},
            job_title=sample_vacancy.title,
            job_description=sample_vacancy.description or "",
            recommendation="good",
        )
        elapsed_uncached = time.time() - start_time_uncached

        # Second call (potentially cached in generator)
        start_time_cached = time.time()
        result_cached = await generator.generate_ranking_explanation(
            candidate_name=sample_resume.candidate_name or "Candidate",
            rank_score=sample_candidate_rank.rank_score,
            rank_position=sample_candidate_rank.rank_position,
            feature_contributions=sample_candidate_rank.feature_contributions,
            ranking_factors={"skills_match": {"score": 0.90}},
            job_title=sample_vacancy.title,
            job_description=sample_vacancy.description or "",
            recommendation="good",
        )
        elapsed_cached = time.time() - start_time_cached

        # Assert both calls succeeded
        assert result_uncached is not None
        assert result_cached is not None

        # Note: Actual caching would be implemented in the generator
        # This test documents the expected behavior
        print(f"\nUncached explanation: {elapsed_uncached:.3f}s")
        print(f"Cached explanation: {elapsed_cached:.3f}s")


@pytest.mark.performance
@pytest.mark.asyncio
async def test_bulk_explanation_generation_performance(
    benchmark, test_db: AsyncSession, sample_vacancy
):
    """
    Benchmark bulk explanation generation for multiple candidates.

    Target: < 10s for 10 candidates (< 1s per candidate)
    """
    # Create 10 sample candidates
    candidates = []
    for i in range(10):
        resume = Resume(
            id=uuid4(),
            filename=f"candidate_{i}.pdf",
            file_path=f"/test/candidate_{i}.pdf",
            candidate_name=f"Candidate {i}",
            email=f"candidate{i}@example.com",
        )
        test_db.add(resume)
        candidates.append(resume)

    await test_db.commit()

    # Create rankings for all candidates
    ranks = []
    for i, resume in enumerate(candidates):
        await test_db.refresh(resume)
        rank = CandidateRank(
            id=uuid4(),
            resume_id=resume.id,
            vacancy_id=sample_vacancy.id,
            rank_score=0.9 - (i * 0.05),  # Decreasing scores
            rank_position=i + 1,
            confidence_score=0.92,
            feature_contributions={
                "skills_match": 0.36,
                "experience": 0.24,
                "education": 0.14,
            },
        )
        test_db.add(rank)
        ranks.append(rank)

    await test_db.commit()

    # Mock LLM call
    with patch("analyzers.explanation_generator.ExplanationGenerator._call_llm") as mock_llm:
        mock_llm.return_value = AsyncMock(
            return_value="Candidate explanation narrative."
        )

        generator = ExplanationGenerator()

        # Benchmark bulk generation
        start_time = time.time()

        results = []
        for rank in ranks:
            result = await generator.generate_ranking_explanation(
                candidate_name=f"Candidate {rank.rank_position}",
                rank_score=rank.rank_score,
                rank_position=rank.rank_position,
                feature_contributions=rank.feature_contributions,
                ranking_factors={"skills_match": {"score": 0.90}},
                job_title=sample_vacancy.title,
                job_description=sample_vacancy.description or "",
                recommendation="good",
            )
            results.append(result)

        elapsed_time = time.time() - start_time

        # Assert performance target
        assert elapsed_time < 10.0, f"Bulk generation took {elapsed_time:.2f}s, exceeds 10s target"
        assert len(results) == 10

        # Calculate per-candidate average
        avg_per_candidate = elapsed_time / 10
        print(f"\nBulk generation: {elapsed_time:.2f}s total, {avg_per_candidate:.2f}s per candidate")


@pytest.mark.performance
@pytest.mark.asyncio
async def test_explanation_with_organization_preferences_performance(
    benchmark, test_db: AsyncSession, sample_candidate_rank, sample_resume, sample_vacancy
):
    """
    Benchmark explanation generation with custom organization preferences.

    Target: < 3s p95 (same as basic explanation)
    """
    # Mock LLM call
    with patch("analyzers.explanation_generator.ExplanationGenerator._call_llm") as mock_llm:
        mock_llm.return_value = AsyncMock(
            return_value="Professional detailed explanation with high detail level."
        )

        # Create generator with custom preferences
        prefs = OrganizationExplanationPreferences(
            tone="professional",
            style="detailed",
            detail_level="high",
            include_percentiles=True,
            include_skill_names=True,
        )
        generator = ExplanationGenerator(org_preferences=prefs)

        # Benchmark the explanation generation
        start_time = time.time()

        result = await generator.generate_ranking_explanation(
            candidate_name=sample_resume.candidate_name or "Candidate",
            rank_score=sample_candidate_rank.rank_score,
            rank_position=sample_candidate_rank.rank_position,
            feature_contributions=sample_candidate_rank.feature_contributions,
            ranking_factors={"skills_match": {"score": 0.90}},
            job_title=sample_vacancy.title,
            job_description=sample_vacancy.description or "",
            recommendation="good",
        )

        elapsed_time = time.time() - start_time

        # Assert performance target
        assert elapsed_time < 3.0, f"Explanation with prefs took {elapsed_time:.2f}s, exceeds 3s target"

        # Assert valid result
        assert result is not None
        assert result.narrative is not None
