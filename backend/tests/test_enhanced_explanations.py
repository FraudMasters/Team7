"""
Unit tests for enhanced explanation generation features.

Tests cover:
- Candidate-specific context formatting (skills, experience duration, education)
- Percentile-based comparison explanation generation
- Organization preferences (tone, style, detail level)
- Enhanced ranking prompts with specific details
- OrganizationExplanationPreferences dataclass methods
"""
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

import pytest

# Import the enhanced explanation generator components
from analyzers.explanation_generator import (
    ExplanationGenerator,
    OrganizationExplanationPreferences,
    ExplanationTone,
    ExplanationStyle,
    DetailLevel,
    RankingExplanation,
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
def professional_generator():
    """Create an explanation generator with professional tone."""
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
            detail_level="high"
        )
        return ExplanationGenerator(org_preferences=prefs)


@pytest.fixture
def sample_ranking_factors():
    """Create sample ranking factors with detailed candidate information."""
    return {
        "skills_match": {
            "score": 0.90,
            "matched_skills": ["Python", "Django", "FastAPI", "PostgreSQL"],
            "missing_skills": ["Redis", "Kubernetes"],
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
            "institution": "Test University",
        },
        "keyword_score": 0.85,
        "tfidf_score": 0.82,
        "vector_score": 0.88,
    }


@pytest.fixture
def sample_feature_contributions():
    """Create sample feature contributions."""
    return {
        "skills_match": 0.36,
        "experience": 0.24,
        "education": 0.14,
        "keywords": 0.085,
    }


class TestOrganizationExplanationPreferences:
    """Tests for OrganizationExplanationPreferences dataclass."""

    def test_default_values(self):
        """Test default preference values."""
        prefs = OrganizationExplanationPreferences()
        assert prefs.tone == "professional"
        assert prefs.style == "balanced"
        assert prefs.detail_level == "medium"
        assert prefs.include_percentiles is True
        assert prefs.include_skill_names is True
        assert prefs.include_experience_details is True
        assert prefs.include_education_details is True
        assert prefs.language is None
        assert prefs.custom_prompt_template is None

    def test_custom_values(self):
        """Test creating preferences with custom values."""
        prefs = OrganizationExplanationPreferences(
            tone="casual",
            style="concise",
            detail_level="low",
            include_percentiles=False,
            include_skill_names=False,
            include_experience_details=False,
            include_education_details=False,
            language="es",
            custom_prompt_template="Custom template",
        )
        assert prefs.tone == "casual"
        assert prefs.style == "concise"
        assert prefs.detail_level == "low"
        assert prefs.include_percentiles is False
        assert prefs.include_skill_names is False
        assert prefs.include_experience_details is False
        assert prefs.include_education_details is False
        assert prefs.language == "es"
        assert prefs.custom_prompt_template == "Custom template"

    def test_from_dict_with_all_fields(self):
        """Test creating preferences from dictionary with all fields."""
        data = {
            "tone": "friendly",
            "style": "detailed",
            "detail_level": "high",
            "include_percentiles": True,
            "include_skill_names": True,
            "include_experience_details": True,
            "include_education_details": True,
            "language": "fr",
            "custom_prompt_template": "Custom",
        }
        prefs = OrganizationExplanationPreferences.from_dict(data)
        assert prefs.tone == "friendly"
        assert prefs.style == "detailed"
        assert prefs.detail_level == "high"
        assert prefs.include_percentiles is True
        assert prefs.include_skill_names is True
        assert prefs.include_experience_details is True
        assert prefs.include_education_details is True
        assert prefs.language == "fr"
        assert prefs.custom_prompt_template == "Custom"

    def test_from_dict_with_partial_fields(self):
        """Test creating preferences from dictionary with partial fields (uses defaults)."""
        data = {
            "tone": "formal",
            "style": "concise",
        }
        prefs = OrganizationExplanationPreferences.from_dict(data)
        assert prefs.tone == "formal"
        assert prefs.style == "concise"
        # Defaults should be used for missing fields
        assert prefs.detail_level == "medium"
        assert prefs.include_percentiles is True
        assert prefs.include_skill_names is True

    def test_from_dict_with_empty_dict(self):
        """Test creating preferences from empty dictionary (all defaults)."""
        prefs = OrganizationExplanationPreferences.from_dict({})
        assert prefs.tone == "professional"
        assert prefs.style == "balanced"
        assert prefs.detail_level == "medium"
        assert prefs.include_percentiles is True


class TestToneInstructions:
    """Tests for _get_tone_instruction method."""

    def test_professional_tone(self, default_generator):
        """Test professional tone instruction."""
        result = default_generator._get_tone_instruction()
        assert "professional" in result.lower()
        assert "business-like" in result.lower()

    def test_casual_tone(self, default_generator):
        """Test casual tone instruction."""
        default_generator.org_preferences.tone = "casual"
        result = default_generator._get_tone_instruction()
        assert "casual" in result.lower()
        assert "relaxed" in result.lower()

    def test_friendly_tone(self, default_generator):
        """Test friendly tone instruction."""
        default_generator.org_preferences.tone = "friendly"
        result = default_generator._get_tone_instruction()
        assert "warm" in result.lower()
        assert "friendly" in result.lower()

    def test_formal_tone(self, default_generator):
        """Test formal tone instruction."""
        default_generator.org_preferences.tone = "formal"
        result = default_generator._get_tone_instruction()
        assert "formal" in result.lower()
        assert "structured" in result.lower()

    def test_invalid_tone_defaults_to_professional(self, default_generator):
        """Test invalid tone defaults to professional."""
        default_generator.org_preferences.tone = "invalid_tone"
        result = default_generator._get_tone_instruction()
        assert "professional" in result.lower()


class TestStyleInstructions:
    """Tests for _get_style_instruction method."""

    def test_detailed_style(self, default_generator):
        """Test detailed style instruction."""
        default_generator.org_preferences.style = "detailed"
        result = default_generator._get_style_instruction()
        assert "comprehensive" in result.lower()
        assert "thorough" in result.lower()

    def test_concise_style(self, default_generator):
        """Test concise style instruction."""
        default_generator.org_preferences.style = "concise"
        result = default_generator._get_style_instruction()
        assert "brief" in result.lower()
        assert "to-the-point" in result.lower()

    def test_balanced_style(self, default_generator):
        """Test balanced style instruction."""
        default_generator.org_preferences.style = "balanced"
        result = default_generator._get_style_instruction()
        assert "well-rounded" in result.lower()
        assert "balance" in result.lower()

    def test_invalid_style_defaults_to_balanced(self, default_generator):
        """Test invalid style defaults to balanced."""
        default_generator.org_preferences.style = "invalid_style"
        result = default_generator._get_style_instruction()
        assert "balanced" in result.lower()


class TestDetailInstructions:
    """Tests for _get_detail_instruction method."""

    def test_high_detail_level(self, default_generator):
        """Test high detail level instruction."""
        default_generator.org_preferences.detail_level = "high"
        result = default_generator._get_detail_instruction()
        assert "comprehensive" in result.lower()
        assert "extensive" in result.lower()

    def test_medium_detail_level(self, default_generator):
        """Test medium detail level instruction."""
        default_generator.org_preferences.detail_level = "medium"
        result = default_generator._get_detail_instruction()
        assert "moderate" in result.lower()

    def test_low_detail_level(self, default_generator):
        """Test low detail level instruction."""
        default_generator.org_preferences.detail_level = "low"
        result = default_generator._get_detail_instruction()
        assert "high-level" in result.lower()
        assert "minimal" in result.lower()

    def test_exclude_skill_names(self, default_generator):
        """Test detail instruction when skill names are excluded."""
        default_generator.org_preferences.include_skill_names = False
        result = default_generator._get_detail_instruction()
        assert "not include specific skill names" in result.lower()

    def test_exclude_experience_details(self, default_generator):
        """Test detail instruction when experience details are excluded."""
        default_generator.org_preferences.include_experience_details = False
        result = default_generator._get_detail_instruction()
        assert "not include specific experience duration" in result.lower()

    def test_exclude_education_details(self, default_generator):
        """Test detail instruction when education details are excluded."""
        default_generator.org_preferences.include_education_details = False
        result = default_generator._get_detail_instruction()
        assert "not include education details" in result.lower()


class TestSetOrganizationPreferences:
    """Tests for set_organization_preferences method."""

    def test_update_tone(self, default_generator):
        """Test updating organization tone."""
        assert default_generator.org_preferences.tone == "professional"
        new_prefs = OrganizationExplanationPreferences(tone="casual")
        default_generator.set_organization_preferences(new_prefs)
        assert default_generator.org_preferences.tone == "casual"

    def test_update_style(self, default_generator):
        """Test updating organization style."""
        assert default_generator.org_preferences.style == "balanced"
        new_prefs = OrganizationExplanationPreferences(style="detailed")
        default_generator.set_organization_preferences(new_prefs)
        assert default_generator.org_preferences.style == "detailed"

    def test_update_detail_level(self, default_generator):
        """Test updating organization detail level."""
        assert default_generator.org_preferences.detail_level == "medium"
        new_prefs = OrganizationExplanationPreferences(detail_level="high")
        default_generator.set_organization_preferences(new_prefs)
        assert default_generator.org_preferences.detail_level == "high"

    def test_update_inclusion_flags(self, default_generator):
        """Test updating inclusion flags."""
        assert default_generator.org_preferences.include_percentiles is True
        new_prefs = OrganizationExplanationPreferences(
            include_percentiles=False,
            include_skill_names=False,
        )
        default_generator.set_organization_preferences(new_prefs)
        assert default_generator.org_preferences.include_percentiles is False
        assert default_generator.org_preferences.include_skill_names is False


class TestFormatCandidateContext:
    """Tests for _format_candidate_context method."""

    def test_format_with_all_details_included(self, default_generator, sample_ranking_factors):
        """Test formatting candidate context with all details included."""
        result = default_generator._format_candidate_context(
            candidate_name="John Doe",
            score=0.85,
            factors=sample_ranking_factors,
        )
        assert "Name: John Doe" in result
        assert "Score: 0.85" in result
        assert "Matched Skills:" in result
        assert "Python" in result
        assert "Django" in result
        assert "Total Experience:" in result
        assert "8 years" in result
        assert "Degree:" in result
        assert "Computer Science" in result

    def test_format_with_skill_names_excluded(self, default_generator, sample_ranking_factors):
        """Test formatting with skill names excluded."""
        default_generator.org_preferences.include_skill_names = False
        result = default_generator._format_candidate_context(
            candidate_name="John Doe",
            score=0.85,
            factors=sample_ranking_factors,
        )
        assert "Name: John Doe" in result
        assert "Score: 0.85" in result
        assert "Matched Skills:" not in result
        assert "Python" not in result

    def test_format_with_experience_excluded(self, default_generator, sample_ranking_factors):
        """Test formatting with experience details excluded."""
        default_generator.org_preferences.include_experience_details = False
        result = default_generator._format_candidate_context(
            candidate_name="John Doe",
            score=0.85,
            factors=sample_ranking_factors,
        )
        assert "Name: John Doe" in result
        assert "Total Experience:" not in result
        assert "8 years" not in result

    def test_format_with_education_excluded(self, default_generator, sample_ranking_factors):
        """Test formatting with education details excluded."""
        default_generator.org_preferences.include_education_details = False
        result = default_generator._format_candidate_context(
            candidate_name="John Doe",
            score=0.85,
            factors=sample_ranking_factors,
        )
        assert "Name: John Doe" in result
        assert "Degree:" not in result
        assert "Computer Science" not in result

    def test_format_with_minimal_factors(self, default_generator):
        """Test formatting with minimal ranking factors."""
        minimal_factors = {
            "skills_match": {"score": 0.75},
        }
        result = default_generator._format_candidate_context(
            candidate_name="Jane Smith",
            score=0.80,
            factors=minimal_factors,
        )
        assert "Name: Jane Smith" in result
        assert "Score: 0.80" in result
        # Should not include detailed sections
        assert "Matched Skills:" not in result

    def test_format_experience_duration_in_years_only(self, default_generator):
        """Test experience duration formatting when only years (no months)."""
        factors = {
            "experience_analysis": {
                "total_months": 72,  # Exactly 6 years
                "score": 0.80,
            },
        }
        result = default_generator._format_candidate_context(
            candidate_name="Test Candidate",
            score=0.75,
            factors=factors,
        )
        assert "6 years" in result
        assert "0 months" not in result

    def test_format_experience_duration_in_months_only(self, default_generator):
        """Test experience duration formatting when only months (< 1 year)."""
        factors = {
            "experience_analysis": {
                "total_months": 9,
                "score": 0.70,
            },
        }
        result = default_generator._format_candidate_context(
            candidate_name="Test Candidate",
            score=0.75,
            factors=factors,
        )
        assert "9 months" in result


class TestCalculatePercentile:
    """Tests for _calculate_percentile method."""

    def test_top_candidate_percentile(self, default_generator):
        """Test percentile for highest scoring candidate."""
        all_scores = [0.65, 0.70, 0.75, 0.80, 0.85]
        result = default_generator._calculate_percentile(0.85, all_scores)
        assert result == 90.0  # (4 + 0.5 * 1) / 5 * 100 = 90

    def test_lowest_candidate_percentile(self, default_generator):
        """Test percentile for lowest scoring candidate."""
        all_scores = [0.65, 0.70, 0.75, 0.80, 0.85]
        result = default_generator._calculate_percentile(0.65, all_scores)
        assert result == 10.0  # (0 + 0.5 * 1) / 5 * 100 = 10

    def test_median_candidate_percentile(self, default_generator):
        """Test percentile for median scoring candidate."""
        all_scores = [0.65, 0.70, 0.75, 0.80, 0.85]
        result = default_generator._calculate_percentile(0.75, all_scores)
        assert result == 50.0  # (2 + 0.5 * 1) / 5 * 100 = 50

    def test_percentile_with_duplicates(self, default_generator):
        """Test percentile calculation with duplicate scores."""
        all_scores = [0.75, 0.75, 0.75, 0.80, 0.85]
        result = default_generator._calculate_percentile(0.75, all_scores)
        # (0 + 0.5 * 3) / 5 * 100 = 30
        assert result == 30.0

    def test_percentile_with_empty_list(self, default_generator):
        """Test percentile returns default when no scores provided."""
        result = default_generator._calculate_percentile(0.75, [])
        assert result == 50.0  # Default to middle

    def test_percentile_with_all_same_scores(self, default_generator):
        """Test percentile when all candidates have the same score."""
        all_scores = [0.80, 0.80, 0.80, 0.80, 0.80]
        result = default_generator._calculate_percentile(0.80, all_scores)
        # (0 + 0.5 * 5) / 5 * 100 = 50
        assert result == 50.0


class TestGeneratePercentileExplanation:
    """Tests for _generate_percentile_explanation method."""

    def test_top_5_percentile_explanation(self, default_generator):
        """Test explanation for top 5% candidate."""
        result = default_generator._generate_percentile_explanation(
            percentile_rank=95.0,
            candidate_name="John Doe",
            total_candidates=100,
        )
        assert "top 5%" in result.lower()
        assert "95%" in result
        assert "100" in result
        assert "John Doe" in result

    def test_top_10_percentile_explanation(self, default_generator):
        """Test explanation for top 10% candidate."""
        result = default_generator._generate_percentile_explanation(
            percentile_rank=90.0,
            candidate_name="Jane Smith",
            total_candidates=50,
        )
        assert "top 10%" in result.lower()
        assert "90%" in result
        assert "50" in result

    def test_top_quartile_explanation(self, default_generator):
        """Test explanation for top quartile candidate (75-89%)."""
        result = default_generator._generate_percentile_explanation(
            percentile_rank=80.0,
            candidate_name="Bob Johnson",
            total_candidates=200,
        )
        assert "top quartile" in result.lower()
        assert "80%" in result

    def test_top_half_explanation(self, default_generator):
        """Test explanation for top half candidate (50-74%)."""
        result = default_generator._generate_percentile_explanation(
            percentile_rank=60.0,
            candidate_name="Alice Brown",
            total_candidates=30,
        )
        assert "top half" in result.lower()

    def test_third_quartile_explanation(self, default_generator):
        """Test explanation for third quartile candidate (25-49%)."""
        result = default_generator._generate_percentile_explanation(
            percentile_rank=35.0,
            candidate_name="Charlie Davis",
            total_candidates=40,
        )
        assert "third quartile" in result.lower()

    def test_bottom_quartile_explanation(self, default_generator):
        """Test explanation for bottom quartile candidate (<25%)."""
        result = default_generator._generate_percentile_explanation(
            percentile_rank=15.0,
            candidate_name="Test Candidate",
            total_candidates=20,
        )
        assert "15%" in result
        assert "20" in result

    def test_explanation_without_candidate_name(self, default_generator):
        """Test explanation when candidate name is not provided."""
        result = default_generator._generate_percentile_explanation(
            percentile_rank=90.0,
            candidate_name=None,
            total_candidates=100,
        )
        assert "This candidate" in result
        assert "90%" in result


class TestCreateRankingPrompt:
    """Tests for _create_ranking_prompt method with enhanced context."""

    def test_prompt_includes_skill_names(self, default_generator, sample_ranking_factors, sample_feature_contributions):
        """Test prompt includes specific skill names when enabled."""
        prompt = default_generator._create_ranking_prompt(
            candidate_name="John Doe",
            rank_score=0.85,
            feature_contributions=sample_feature_contributions,
            ranking_factors=sample_ranking_factors,
            job_title="Senior Python Developer",
            job_description="We are looking for a senior developer...",
            recommendation="excellent",
        )
        assert "Matched Skills:" in prompt
        assert "Python" in prompt
        assert "Django" in prompt
        assert "Missing Skills:" in prompt
        assert "Redis" in prompt

    def test_prompt_excludes_skill_names_when_disabled(self, default_generator, sample_ranking_factors, sample_feature_contributions):
        """Test prompt excludes skill names when disabled."""
        default_generator.org_preferences.include_skill_names = False
        prompt = default_generator._create_ranking_prompt(
            candidate_name="John Doe",
            rank_score=0.85,
            feature_contributions=sample_feature_contributions,
            ranking_factors=sample_ranking_factors,
            job_title="Senior Python Developer",
            job_description="We are looking for a senior developer...",
            recommendation="excellent",
        )
        assert "Matched Skills:" not in prompt
        assert "Python" not in prompt

    def test_prompt_includes_experience_duration(self, default_generator, sample_ranking_factors, sample_feature_contributions):
        """Test prompt includes experience duration details."""
        prompt = default_generator._create_ranking_prompt(
            candidate_name="John Doe",
            rank_score=0.85,
            feature_contributions=sample_feature_contributions,
            ranking_factors=sample_ranking_factors,
            job_title="Senior Python Developer",
            job_description="We are looking for a senior developer...",
            recommendation="excellent",
        )
        assert "Total Experience:" in prompt
        assert "8 years" in prompt
        assert "Relevant Experience:" in prompt
        assert "7 years" in prompt

    def test_prompt_excludes_experience_when_disabled(self, default_generator, sample_ranking_factors, sample_feature_contributions):
        """Test prompt excludes experience details when disabled."""
        default_generator.org_preferences.include_experience_details = False
        prompt = default_generator._create_ranking_prompt(
            candidate_name="John Doe",
            rank_score=0.85,
            feature_contributions=sample_feature_contributions,
            ranking_factors=sample_ranking_factors,
            job_title="Senior Python Developer",
            job_description="We are looking for a senior developer...",
            recommendation="excellent",
        )
        assert "Total Experience:" not in prompt
        assert "8 years" not in prompt

    def test_prompt_includes_education_details(self, default_generator, sample_ranking_factors, sample_feature_contributions):
        """Test prompt includes education details."""
        prompt = default_generator._create_ranking_prompt(
            candidate_name="John Doe",
            rank_score=0.85,
            feature_contributions=sample_feature_contributions,
            ranking_factors=sample_ranking_factors,
            job_title="Senior Python Developer",
            job_description="We are looking for a senior developer...",
            recommendation="excellent",
        )
        assert "Degree:" in prompt
        assert "Computer Science" in prompt
        assert "Field of Study:" in prompt
        assert "Institution:" in prompt

    def test_prompt_excludes_education_when_disabled(self, default_generator, sample_ranking_factors, sample_feature_contributions):
        """Test prompt excludes education details when disabled."""
        default_generator.org_preferences.include_education_details = False
        prompt = default_generator._create_ranking_prompt(
            candidate_name="John Doe",
            rank_score=0.85,
            feature_contributions=sample_feature_contributions,
            ranking_factors=sample_ranking_factors,
            job_title="Senior Python Developer",
            job_description="We are looking for a senior developer...",
            recommendation="excellent",
        )
        assert "Degree:" not in prompt
        assert "Computer Science" not in prompt

    def test_prompt_with_minimal_ranking_factors(self, default_generator, sample_feature_contributions):
        """Test prompt with minimal ranking factors (no detailed sections)."""
        minimal_factors = {
            "keyword_score": 0.75,
            "tfidf_score": 0.70,
        }
        prompt = default_generator._create_ranking_prompt(
            candidate_name="Jane Smith",
            rank_score=0.75,
            feature_contributions=sample_feature_contributions,
            ranking_factors=minimal_factors,
            job_title="Python Developer",
            job_description="Job description",
            recommendation="good",
        )
        # Should still contain basic sections
        assert "CANDIDATE" in prompt
        assert "JOB POSTING" in prompt
        assert "TOP FACTORS" in prompt
        assert "Jane Smith" in prompt
        assert "0.75" in prompt


class TestGenerateRankingExplanationWithPercentiles:
    """Tests for generate_ranking_explanation with percentile calculation."""

    @pytest.mark.asyncio
    async def test_explanation_includes_percentile_when_enabled(self, default_generator, sample_ranking_factors, sample_feature_contributions):
        """Test explanation includes percentile when enabled and scores provided."""
        all_scores = [0.65, 0.70, 0.75, 0.80, 0.85]

        # Mock the LLM call
        default_generator._call_llm = AsyncMock(return_value={
            "narrative": "This candidate is an excellent match.",
            "strengths": ["Strong Python skills"],
            "weaknesses": [],
            "highlight_suggestions": {},
        })

        result = await default_generator.generate_ranking_explanation(
            candidate_name="John Doe",
            rank_score=0.85,
            rank_position=1,
            feature_contributions=sample_feature_contributions,
            ranking_factors=sample_ranking_factors,
            job_title="Senior Python Developer",
            recommendation="excellent",
            all_candidate_scores=all_scores,
            use_llm=True,
        )

        assert result.percentile_rank == 90.0
        assert result.percentile_explanation != ""
        assert "90%" in result.percentile_explanation

    @pytest.mark.asyncio
    async def test_explanation_excludes_percentile_when_disabled(self, default_generator, sample_ranking_factors, sample_feature_contributions):
        """Test explanation excludes percentile when disabled."""
        default_generator.org_preferences.include_percentiles = False
        all_scores = [0.65, 0.70, 0.75, 0.80, 0.85]

        # Mock the LLM call
        default_generator._call_llm = AsyncMock(return_value={
            "narrative": "This candidate is a good match.",
            "strengths": ["Good skills"],
            "weaknesses": [],
            "highlight_suggestions": {},
        })

        result = await default_generator.generate_ranking_explanation(
            candidate_name="Jane Smith",
            rank_score=0.80,
            rank_position=2,
            feature_contributions=sample_feature_contributions,
            ranking_factors=sample_ranking_factors,
            job_title="Senior Python Developer",
            recommendation="good",
            all_candidate_scores=all_scores,
            use_llm=True,
        )

        assert result.percentile_rank is None
        assert result.percentile_explanation == ""

    @pytest.mark.asyncio
    async def test_explanation_without_all_candidate_scores(self, default_generator, sample_ranking_factors, sample_feature_contributions):
        """Test explanation without all_candidate_scores parameter."""
        # Mock the LLM call
        default_generator._call_llm = AsyncMock(return_value={
            "narrative": "This candidate is a good match.",
            "strengths": ["Good experience"],
            "weaknesses": [],
            "highlight_suggestions": {},
        })

        result = await default_generator.generate_ranking_explanation(
            candidate_name="Test Candidate",
            rank_score=0.75,
            rank_position=3,
            feature_contributions=sample_feature_contributions,
            ranking_factors=sample_ranking_factors,
            job_title="Python Developer",
            recommendation="good",
            all_candidate_scores=None,
            use_llm=True,
        )

        assert result.percentile_rank is None
        assert result.percentile_explanation == ""

    @pytest.mark.asyncio
    async def test_explanation_with_empty_all_candidate_scores(self, default_generator, sample_ranking_factors, sample_feature_contributions):
        """Test explanation with empty all_candidate_scores list."""
        # Mock the LLM call
        default_generator._call_llm = AsyncMock(return_value={
            "narrative": "This candidate is a good match.",
            "strengths": ["Good skills"],
            "weaknesses": [],
            "highlight_suggestions": {},
        })

        result = await default_generator.generate_ranking_explanation(
            candidate_name="Test Candidate",
            rank_score=0.75,
            rank_position=1,
            feature_contributions=sample_feature_contributions,
            ranking_factors=sample_ranking_factors,
            job_title="Python Developer",
            recommendation="good",
            all_candidate_scores=[],
            use_llm=True,
        )

        # Should default to 50.0 percentile when empty
        assert result.percentile_rank == 50.0


class TestRankingExplanationDataclass:
    """Tests for RankingExplanation dataclass."""

    def test_to_dict_with_percentile(self):
        """Test to_dict method includes percentile fields."""
        explanation = RankingExplanation(
            candidate_name="John Doe",
            rank_score=0.85,
            rank_position=1,
            narrative="Excellent match",
            feature_explanations=[],
            confidence_interval=None,
            strengths=["Strong skills"],
            weaknesses=[],
            recommendation="excellent",
            highlight_sections={},
            percentile_rank=90.0,
            percentile_explanation="Top 10% candidate",
            provider="zai",
            model="gpt-4",
            generated_at="2026-02-08T12:00:00Z",
        )

        result = explanation.to_dict()
        assert result["percentile_rank"] == 90.0
        assert result["percentile_explanation"] == "Top 10% candidate"

    def test_to_dict_without_percentile(self):
        """Test to_dict method with None percentile values."""
        explanation = RankingExplanation(
            candidate_name="Jane Smith",
            rank_score=0.75,
            rank_position=2,
            narrative="Good match",
            feature_explanations=[],
            confidence_interval=None,
            strengths=["Good experience"],
            weaknesses=[],
            recommendation="good",
            highlight_sections={},
            percentile_rank=None,
            percentile_explanation="",
            provider="zai",
            model="gpt-4",
            generated_at="2026-02-08T12:00:00Z",
        )

        result = explanation.to_dict()
        assert result["percentile_rank"] is None
        assert result["percentile_explanation"] == ""


class TestGenerateExplanationSync:
    """Tests for generate_explanation_sync wrapper method."""

    def test_sync_wrapper_passes_all_candidate_scores(self, default_generator, sample_ranking_factors, sample_feature_contributions):
        """Test sync wrapper properly passes all_candidate_scores parameter."""
        with patch.object(default_generator, 'generate_ranking_explanation', new=AsyncMock()) as mock_generate:
            mock_generate.return_value = Mock(
                percentile_rank=85.0,
                percentile_explanation="Top 15% candidate",
            )

            all_scores = [0.60, 0.65, 0.70, 0.75, 0.80]

            result = default_generator.generate_explanation_sync(
                candidate_name="Test Candidate",
                rank_score=0.80,
                rank_position=1,
                feature_contributions=sample_feature_contributions,
                ranking_factors=sample_ranking_factors,
                job_title="Senior Developer",
                recommendation="good",
                all_candidate_scores=all_scores,
                use_llm=False,
            )

            # Verify the async method was called with all_candidate_scores
            mock_generate.assert_called_once()
            call_kwargs = mock_generate.call_args.kwargs
            assert "all_candidate_scores" in call_kwargs
            assert call_kwargs["all_candidate_scores"] == all_scores

    def test_sync_wrapper_without_all_candidate_scores(self, default_generator, sample_ranking_factors, sample_feature_contributions):
        """Test sync wrapper without all_candidate_scores parameter."""
        with patch.object(default_generator, 'generate_ranking_explanation', new=AsyncMock()) as mock_generate:
            mock_generate.return_value = Mock(
                percentile_rank=None,
                percentile_explanation="",
            )

            result = default_generator.generate_explanation_sync(
                candidate_name="Test Candidate",
                rank_score=0.75,
                rank_position=2,
                feature_contributions=sample_feature_contributions,
                ranking_factors=sample_ranking_factors,
                job_title="Developer",
                recommendation="maybe",
                use_llm=False,
            )

            # Verify the async method was called with None for all_candidate_scores
            mock_generate.assert_called_once()
            call_kwargs = mock_generate.call_args.kwargs
            assert "all_candidate_scores" in call_kwargs
            assert call_kwargs["all_candidate_scores"] is None


class TestGetExplanationGeneratorWithPreferences:
    """Tests for get_explanation_generator module function with preferences."""

    def test_get_generator_with_custom_preferences(self):
        """Test get_explanation_generator with custom organization preferences."""
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

            from analyzers.explanation_generator import get_explanation_generator

            custom_prefs = OrganizationExplanationPreferences(
                tone="casual",
                style="concise",
                detail_level="low",
            )

            generator = get_explanation_generator(org_preferences=custom_prefs)

            assert generator is not None
            assert generator.org_preferences.tone == "casual"
            assert generator.org_preferences.style == "concise"
            assert generator.org_preferences.detail_level == "low"


class TestGenerateRankingExplanationModuleFunction:
    """Tests for module-level generate_ranking_explanation function."""

    @pytest.mark.asyncio
    async def test_module_function_with_org_preferences(self, sample_ranking_factors, sample_feature_contributions):
        """Test module-level function accepts organization preferences."""
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

            from analyzers.explanation_generator import generate_ranking_explanation

            custom_prefs = OrganizationExplanationPreferences(
                tone="formal",
                include_percentiles=False,
            )

            # Mock the generator's generate_ranking_explanation method
            with patch('analyzers.explanation_generator.ExplanationGenerator.generate_ranking_explanation',
                      new=AsyncMock()) as mock_generate:
                mock_generate.return_value = Mock(
                    percentile_rank=None,
                    percentile_explanation="",
                )

                all_scores = [0.70, 0.75, 0.80]

                await generate_ranking_explanation(
                    candidate_name="Test Candidate",
                    rank_score=0.80,
                    rank_position=1,
                    feature_contributions=sample_feature_contributions,
                    ranking_factors=sample_ranking_factors,
                    job_title="Senior Developer",
                    recommendation="excellent",
                    all_candidate_scores=all_scores,
                    use_llm=False,
                    org_preferences=custom_prefs,
                )

                # Verify the generator was called with org_preferences
                mock_generate.assert_called_once()
                call_kwargs = mock_generate.call_args.kwargs
                assert "all_candidate_scores" in call_kwargs
                assert call_kwargs["all_candidate_scores"] == all_scores
