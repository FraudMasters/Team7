"""
Unit tests for side-by-side candidate comparison explanations.

Tests cover:
- Differential score breakdown (why A > B or B > A)
- Factor-by-factor comparison
- Natural language summary of key differences
- Strengths/weaknesses comparison table
- Multiple LLM provider support for comparisons
"""
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

import pytest

from analyzers.explanation_generator import (
    ExplanationGenerator,
    OrganizationExplanationPreferences,
    ComparisonExplanation,
    LLMProvider,
)


@pytest.fixture
def default_generator():
    """Create an explanation generator with default settings."""
    with patch('analyzers.explanation_generator.get_settings') as mock_settings:
        mock_settings.return_value = Mock(
            llm_provider="zai",
            llm_model="gpt-4",
            llm_temperature=0.7,
            llm_max_tokens=1000,
            zai_api_key="test-key",
            zai_base_url="http://test.com",
            openai_api_key=None,
            anthropic_api_key=None,
            google_api_key=None,
        )
        return ExplanationGenerator()


@pytest.fixture
def candidate_a_factors():
    """Sample ranking factors for candidate A (higher score)."""
    return {
        "skills_match": {
            "score": 0.95,
            "matched_skills": ["Python", "Django", "FastAPI", "PostgreSQL", "Redis"],
            "missing_skills": ["Kubernetes"],
        },
        "experience_analysis": {
            "score": 0.90,
            "total_months": 120,
            "relevant_months": 108,
        },
        "education_analysis": {
            "score": 0.85,
            "degree": "M.Sc Computer Science",
            "field_of_study": "Computer Science",
            "institution": "Top University",
        },
        "keyword_score": 0.88,
        "tfidf_score": 0.90,
        "vector_score": 0.92,
    }


@pytest.fixture
def candidate_b_factors():
    """Sample ranking factors for candidate B (lower score)."""
    return {
        "skills_match": {
            "score": 0.75,
            "matched_skills": ["Python", "Flask", "MySQL"],
            "missing_skills": ["Django", "PostgreSQL", "Redis"],
        },
        "experience_analysis": {
            "score": 0.70,
            "total_months": 60,
            "relevant_months": 48,
        },
        "education_analysis": {
            "score": 0.75,
            "degree": "B.Sc Computer Science",
            "field_of_study": "Computer Science",
            "institution": "State University",
        },
        "keyword_score": 0.72,
        "tfidf_score": 0.70,
        "vector_score": 0.73,
    }


def test_comparison_explanation_dataclass():
    """Test ComparisonExplanation dataclass structure."""
    comparison = ComparisonExplanation(
        candidate_a_name="John Smith",
        candidate_b_name="Jane Doe",
        candidate_a_score=8.5,
        candidate_b_score=7.2,
        narrative="John Smith ranks higher due to better skills alignment.",
        key_differences=["5 years more experience", "More relevant skills"],
        winning_factors=["Python expertise", "Django experience"],
        losing_factors=["Missing PostgreSQL", "Less experience"],
        recommendation="John Smith",
        provider="zai",
        model="gpt-4",
        generated_at="2024-01-01T00:00:00",
    )

    assert comparison.candidate_a_name == "John Smith"
    assert comparison.candidate_b_name == "Jane Doe"
    assert comparison.candidate_a_score == 8.5
    assert comparison.candidate_b_score == 7.2
    assert len(comparison.key_differences) == 2
    assert len(comparison.winning_factors) == 2
    assert len(comparison.losing_factors) == 2

    # Test to_dict method
    comparison_dict = comparison.to_dict()
    assert comparison_dict["candidate_a_name"] == "John Smith"
    assert comparison_dict["narrative"] == "John Smith ranks higher due to better skills alignment."


def test_create_comparison_prompt(default_generator, candidate_a_factors, candidate_b_factors):
    """Test comparison prompt generation includes all necessary context."""
    prompt = default_generator._create_comparison_prompt(
        candidate_a_name="Alice Johnson",
        candidate_b_name="Bob Williams",
        candidate_a_score=8.8,
        candidate_b_score=7.5,
        candidate_a_factors=candidate_a_factors,
        candidate_b_factors=candidate_b_factors,
        job_title="Senior Backend Engineer",
    )

    # Verify prompt structure
    assert "Senior Backend Engineer" in prompt
    assert "Alice Johnson" in prompt
    assert "Bob Williams" in prompt
    assert "8.8" in prompt or "8.80" in prompt
    assert "7.5" in prompt or "7.50" in prompt

    # Verify candidate A (higher score) context
    assert "CANDIDATE A (Higher Score)" in prompt or "Higher Score" in prompt
    assert "Python" in prompt
    assert "Django" in prompt
    assert "M.Sc Computer Science" in prompt

    # Verify candidate B (lower score) context
    assert "CANDIDATE B (Lower Score)" in prompt or "Lower Score" in prompt
    assert "Flask" in prompt
    assert "B.Sc Computer Science" in prompt

    # Verify expected output format is specified
    assert "narrative" in prompt.lower()
    assert "key_differences" in prompt.lower()
    assert "winning_factors" in prompt.lower()


@pytest.mark.asyncio
async def test_generate_comparison_explanation_with_llm(
    default_generator, candidate_a_factors, candidate_b_factors
):
    """Test comparison explanation generation with LLM call."""
    # Mock LLM response
    mock_llm_response = {
        "narrative": (
            "Alice Johnson ranks 1.3 points higher than Bob Williams primarily due to "
            "superior skills alignment (95% vs 75%) and significantly more relevant experience "
            "(10 years vs 5 years). Alice demonstrates mastery of core technologies including "
            "Django and PostgreSQL, which are critical for this Senior Backend Engineer role."
        ),
        "key_differences": [
            "Alice has 5 years more total experience (10 years vs 5 years)",
            "Alice matches 5 required skills vs Bob's 3",
            "Alice has PostgreSQL and Redis experience, which Bob lacks",
            "Alice holds an M.Sc while Bob has a B.Sc degree",
        ],
        "winning_factors": [
            "Strong Django and FastAPI expertise",
            "Database skills (PostgreSQL, Redis)",
            "Higher education (M.Sc Computer Science)",
            "9 years of relevant backend experience",
        ],
        "losing_factors": [
            "Missing Django framework experience",
            "No PostgreSQL database experience",
            "Only 4 years of relevant experience",
            "Flask instead of Django (different ecosystem)",
        ],
        "recommendation": "Alice Johnson",
    }

    with patch.object(default_generator, '_call_llm', new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_llm_response

        result = await default_generator.generate_comparison_explanation(
            candidate_a_name="Alice Johnson",
            candidate_b_name="Bob Williams",
            candidate_a_score=8.8,
            candidate_b_score=7.5,
            candidate_a_factors=candidate_a_factors,
            candidate_b_factors=candidate_b_factors,
            job_title="Senior Backend Engineer",
            use_llm=True,
        )

    # Verify result structure
    assert isinstance(result, ComparisonExplanation)
    assert result.candidate_a_name == "Alice Johnson"
    assert result.candidate_b_name == "Bob Williams"
    assert result.candidate_a_score == 8.8
    assert result.candidate_b_score == 7.5

    # Verify narrative quality
    assert len(result.narrative) > 50
    assert "Alice Johnson" in result.narrative
    assert "Bob Williams" in result.narrative

    # Verify key differences
    assert len(result.key_differences) >= 3
    assert any("experience" in diff.lower() for diff in result.key_differences)
    assert any("skills" in diff.lower() or "skill" in diff.lower() for diff in result.key_differences)

    # Verify winning/losing factors
    assert len(result.winning_factors) >= 3
    assert len(result.losing_factors) >= 3
    assert any("Django" in factor for factor in result.winning_factors)

    # Verify recommendation
    assert result.recommendation == "Alice Johnson"

    # Verify metadata
    assert result.provider == "zai"
    assert result.model == "gpt-4"
    assert result.generated_at


@pytest.mark.asyncio
async def test_generate_comparison_explanation_without_llm(
    default_generator, candidate_a_factors, candidate_b_factors
):
    """Test comparison explanation generation with fallback (no LLM)."""
    result = await default_generator.generate_comparison_explanation(
        candidate_a_name="Alice Johnson",
        candidate_b_name="Bob Williams",
        candidate_a_score=8.8,
        candidate_b_score=7.5,
        candidate_a_factors=candidate_a_factors,
        candidate_b_factors=candidate_b_factors,
        job_title="Senior Backend Engineer",
        use_llm=False,
    )

    # Verify basic structure
    assert isinstance(result, ComparisonExplanation)
    assert result.candidate_a_name == "Alice Johnson"
    assert result.candidate_b_name == "Bob Williams"

    # Verify fallback narrative exists
    assert len(result.narrative) > 0
    assert "Alice Johnson" in result.narrative
    assert "Bob Williams" in result.narrative

    # Verify score differential is mentioned
    score_diff = 8.8 - 7.5
    assert str(round(score_diff, 1)) in result.narrative or str(round(score_diff, 2)) in result.narrative


@pytest.mark.asyncio
async def test_generate_comparison_explanation_llm_failure_fallback(
    default_generator, candidate_a_factors, candidate_b_factors
):
    """Test comparison explanation falls back gracefully when LLM fails."""
    with patch.object(default_generator, '_call_llm', new_callable=AsyncMock) as mock_call:
        mock_call.side_effect = Exception("LLM API error")

        result = await default_generator.generate_comparison_explanation(
            candidate_a_name="Alice Johnson",
            candidate_b_name="Bob Williams",
            candidate_a_score=8.8,
            candidate_b_score=7.5,
            candidate_a_factors=candidate_a_factors,
            candidate_b_factors=candidate_b_factors,
            job_title="Senior Backend Engineer",
            use_llm=True,
        )

    # Should still return a valid explanation with fallback
    assert isinstance(result, ComparisonExplanation)
    assert len(result.narrative) > 0
    assert "Alice Johnson" in result.narrative


@pytest.mark.asyncio
async def test_comparison_with_reversed_scores(
    default_generator, candidate_a_factors, candidate_b_factors
):
    """Test comparison when B scores higher than A."""
    # Swap the factors so B is better
    result = await default_generator.generate_comparison_explanation(
        candidate_a_name="Bob Williams",  # Now higher score
        candidate_b_name="Alice Johnson",  # Now lower score
        candidate_a_score=8.8,
        candidate_b_score=7.5,
        candidate_a_factors=candidate_b_factors,  # Swapped
        candidate_b_factors=candidate_a_factors,  # Swapped
        job_title="Senior Backend Engineer",
        use_llm=False,
    )

    # Should still produce valid comparison
    assert isinstance(result, ComparisonExplanation)
    assert result.candidate_a_score > result.candidate_b_score
    assert "Bob Williams" in result.narrative


def test_comparison_explanation_to_dict_serialization():
    """Test comparison explanation can be serialized to dict."""
    comparison = ComparisonExplanation(
        candidate_a_name="Test A",
        candidate_b_name="Test B",
        candidate_a_score=9.0,
        candidate_b_score=8.0,
        narrative="Test narrative",
        key_differences=["Diff 1", "Diff 2"],
        winning_factors=["Win 1", "Win 2"],
        losing_factors=["Loss 1", "Loss 2"],
        recommendation="Test A",
        provider="zai",
        model="gpt-4",
        generated_at="2024-01-01T00:00:00",
    )

    result = comparison.to_dict()

    # Verify all fields are present
    assert result["candidate_a_name"] == "Test A"
    assert result["candidate_b_name"] == "Test B"
    assert result["candidate_a_score"] == 9.0
    assert result["candidate_b_score"] == 8.0
    assert result["narrative"] == "Test narrative"
    assert result["key_differences"] == ["Diff 1", "Diff 2"]
    assert result["winning_factors"] == ["Win 1", "Win 2"]
    assert result["losing_factors"] == ["Loss 1", "Loss 2"]
    assert result["recommendation"] == "Test A"
    assert result["provider"] == "zai"
    assert result["model"] == "gpt-4"
    assert result["generated_at"] == "2024-01-01T00:00:00"


@pytest.mark.asyncio
async def test_comparison_with_organization_preferences(candidate_a_factors, candidate_b_factors):
    """Test comparison respects organization preferences."""
    with patch('analyzers.explanation_generator.get_settings') as mock_settings:
        mock_settings.return_value = Mock(
            llm_provider="zai",
            llm_model="gpt-4",
            llm_temperature=0.7,
            llm_max_tokens=1000,
            zai_api_key="test-key",
            zai_base_url="http://test.com",
            openai_api_key=None,
            anthropic_api_key=None,
            google_api_key=None,
        )

        prefs = OrganizationExplanationPreferences(
            tone="professional",
            style="detailed",
            detail_level="high",
            include_skill_names=True,
            include_experience_details=True,
        )

        generator = ExplanationGenerator(org_preferences=prefs)

        prompt = generator._create_comparison_prompt(
            candidate_a_name="Alice Johnson",
            candidate_b_name="Bob Williams",
            candidate_a_score=8.8,
            candidate_b_score=7.5,
            candidate_a_factors=candidate_a_factors,
            candidate_b_factors=candidate_b_factors,
            job_title="Senior Backend Engineer",
        )

        # Verify detailed information is included when preferences demand it
        assert "Python" in prompt  # Skill names
        assert "Django" in prompt  # Skill names
        assert "120" in prompt or "108" in prompt  # Experience months


@pytest.mark.asyncio
async def test_comparison_format_candidate_context(default_generator, candidate_a_factors):
    """Test _format_candidate_context includes all relevant information."""
    context = default_generator._format_candidate_context(
        "Alice Johnson",
        8.8,
        candidate_a_factors
    )

    # Verify name and score
    assert "Alice Johnson" in context
    assert "8.8" in context or "8.80" in context

    # Verify skills information
    assert "Python" in context
    assert "Django" in context

    # Verify experience information
    assert "120" in context or "10" in context  # Months or years

    # Verify education information
    assert "M.Sc Computer Science" in context or "Computer Science" in context


@pytest.mark.asyncio
async def test_comparison_explanation_with_equal_scores(
    default_generator, candidate_a_factors, candidate_b_factors
):
    """Test comparison when candidates have equal scores."""
    result = await default_generator.generate_comparison_explanation(
        candidate_a_name="Alice Johnson",
        candidate_b_name="Bob Williams",
        candidate_a_score=8.0,
        candidate_b_score=8.0,
        candidate_a_factors=candidate_a_factors,
        candidate_b_factors=candidate_b_factors,
        job_title="Senior Backend Engineer",
        use_llm=False,
    )

    # Should still produce valid comparison
    assert isinstance(result, ComparisonExplanation)
    assert result.candidate_a_score == result.candidate_b_score
    assert len(result.narrative) > 0
