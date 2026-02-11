"""
Unit Tests for Job Description Generator

Tests the LLM-based job description generation module that creates
professional, inclusive, and unbiased job descriptions based on role
titles and requirements.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime
import json
import asyncio

from analyzers.job_description_generator import (
    JobDescriptionGenerator,
    JobDescriptionSection,
    JobDescriptionResult,
    LLMProvider,
    EmploymentType,
    SeniorityLevel,
    get_job_description_generator,
    generate_job_description,
)


class TestJobDescriptionGeneratorInit:
    """Tests for JobDescriptionGenerator initialization."""

    @patch("analyzers.job_description_generator.get_settings")
    def test_init_with_default_settings(self, mock_get_settings):
        """Test initialization with default settings from config."""
        mock_settings = Mock()
        mock_settings.llm_provider = "zai"
        mock_settings.llm_model = "gpt-4"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 2000
        mock_settings.zai_api_key = "test-zai-key"
        mock_settings.zai_base_url = "https://api.zai.com/v1"
        mock_settings.openai_api_key = "test-openai-key"
        mock_settings.anthropic_api_key = "test-anthropic-key"
        mock_settings.google_api_key = "test-google-key"
        mock_get_settings.return_value = mock_settings

        generator = JobDescriptionGenerator()

        assert generator.provider == LLMProvider.ZAI
        assert generator.model == "gpt-4"
        assert generator.temperature == 0.7
        assert generator.max_tokens == 2000
        assert generator.zai_api_key == "test-zai-key"

    @patch("analyzers.job_description_generator.get_settings")
    def test_init_with_custom_provider(self, mock_get_settings):
        """Test initialization with custom LLM provider."""
        mock_settings = Mock()
        mock_settings.llm_provider = "openai"
        mock_settings.llm_model = "gpt-3.5-turbo"
        mock_settings.llm_temperature = 0.5
        mock_settings.llm_max_tokens = 1500
        mock_settings.zai_api_key = None
        mock_settings.openai_api_key = "test-openai-key"
        mock_settings.anthropic_api_key = None
        mock_settings.google_api_key = None
        mock_get_settings.return_value = mock_settings

        generator = JobDescriptionGenerator(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-sonnet"
        )

        assert generator.provider == LLMProvider.ANTHROPIC
        assert generator.model == "claude-3-sonnet"

    @patch("analyzers.job_description_generator.get_settings")
    def test_init_with_anthropic_provider(self, mock_get_settings):
        """Test initialization with Anthropic provider."""
        mock_settings = Mock()
        mock_settings.llm_provider = "anthropic"
        mock_settings.llm_model = "claude-3-opus"
        mock_settings.llm_temperature = 0.8
        mock_settings.llm_max_tokens = 4000
        mock_settings.zai_api_key = None
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = "test-anthropic-key"
        mock_settings.google_api_key = None
        mock_get_settings.return_value = mock_settings

        generator = JobDescriptionGenerator()

        assert generator.provider == LLMProvider.ANTHROPIC
        assert generator.model == "claude-3-opus"
        assert generator.anthropic_api_key == "test-anthropic-key"

    @patch("analyzers.job_description_generator.get_settings")
    def test_init_with_google_provider(self, mock_get_settings):
        """Test initialization with Google provider."""
        mock_settings = Mock()
        mock_settings.llm_provider = "google"
        mock_settings.llm_model = "gemini-pro"
        mock_settings.llm_temperature = 0.6
        mock_settings.llm_max_tokens = 2500
        mock_settings.zai_api_key = None
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        mock_settings.google_api_key = "test-google-key"
        mock_get_settings.return_value = mock_settings

        generator = JobDescriptionGenerator()

        assert generator.provider == LLMProvider.GOOGLE
        assert generator.model == "gemini-pro"
        assert generator.google_api_key == "test-google-key"


class TestSystemPrompt:
    """Tests for system prompt generation."""

    @patch("analyzers.job_description_generator.get_settings")
    def test_system_prompt_includes_inclusive_language_guidelines(self, mock_get_settings):
        """Test that system prompt includes inclusive language guidelines."""
        mock_settings = Mock()
        mock_settings.llm_provider = "zai"
        mock_settings.llm_model = "gpt-4"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 2000
        mock_settings.zai_api_key = "test-key"
        mock_settings.zai_base_url = "https://api.zai.com/v1"
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        mock_settings.google_api_key = None
        mock_get_settings.return_value = mock_settings

        generator = JobDescriptionGenerator()
        prompt = generator._get_system_prompt()

        # Check for inclusive language guidelines
        assert "inclusive" in prompt.lower()
        assert "gender-neutral" in prompt.lower()
        assert "bias" in prompt.lower()
        assert "welcoming" in prompt.lower()

    @patch("analyzers.job_description_generator.get_settings")
    def test_system_prompt_includes_json_format_spec(self, mock_get_settings):
        """Test that system prompt specifies JSON response format."""
        mock_settings = Mock()
        mock_settings.llm_provider = "zai"
        mock_settings.llm_model = "gpt-4"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 2000
        mock_settings.zai_api_key = "test-key"
        mock_settings.zai_base_url = "https://api.zai.com/v1"
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        mock_settings.google_api_key = None
        mock_get_settings.return_value = mock_settings

        generator = JobDescriptionGenerator()
        prompt = generator._get_system_prompt()

        # Check for JSON format specification
        assert "json" in prompt.lower()
        assert "summary" in prompt.lower()
        assert "responsibilities" in prompt.lower()
        assert "requirements" in prompt.lower()


class TestDescriptionPromptCreation:
    """Tests for description generation prompt creation."""

    @patch("analyzers.job_description_generator.get_settings")
    def test_create_basic_prompt(self, mock_get_settings):
        """Test creating a basic description generation prompt."""
        mock_settings = Mock()
        mock_settings.llm_provider = "zai"
        mock_settings.llm_model = "gpt-4"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 2000
        mock_settings.zai_api_key = "test-key"
        mock_settings.zai_base_url = "https://api.zai.com/v1"
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        mock_settings.google_api_key = None
        mock_get_settings.return_value = mock_settings

        generator = JobDescriptionGenerator()

        prompt = generator._create_description_prompt(
            title="Senior Python Developer",
            required_skills=["Python", "Django", "PostgreSQL"]
        )

        assert "Senior Python Developer" in prompt
        assert "Python, Django, PostgreSQL" in prompt

    @patch("analyzers.job_description_generator.get_settings")
    def test_create_prompt_with_seniority_and_experience(self, mock_get_settings):
        """Test creating prompt with seniority level and experience."""
        mock_settings = Mock()
        mock_settings.llm_provider = "zai"
        mock_settings.llm_model = "gpt-4"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 2000
        mock_settings.zai_api_key = "test-key"
        mock_settings.zai_base_url = "https://api.zai.com/v1"
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        mock_settings.google_api_key = None
        mock_get_settings.return_value = mock_settings

        generator = JobDescriptionGenerator()

        prompt = generator._create_description_prompt(
            title="Developer",
            required_skills=["Python"],
            seniority_level="senior",
            min_experience_months=60
        )

        assert "Seniority Level: senior" in prompt
        assert "5 years" in prompt  # 60 months = 5 years

    @patch("analyzers.job_description_generator.get_settings")
    def test_create_prompt_with_employment_type_and_department(self, mock_get_settings):
        """Test creating prompt with employment type and department."""
        mock_settings = Mock()
        mock_settings.llm_provider = "zai"
        mock_settings.llm_model = "gpt-4"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 2000
        mock_settings.zai_api_key = "test-key"
        mock_settings.zai_base_url = "https://api.zai.com/v1"
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        mock_settings.google_api_key = None
        mock_get_settings.return_value = mock_settings

        generator = JobDescriptionGenerator()

        prompt = generator._create_description_prompt(
            title="Developer",
            required_skills=["Python"],
            department="Engineering",
            employment_type="full_time"
        )

        assert "Department: Engineering" in prompt
        assert "Employment Type: full_time" in prompt

    @patch("analyzers.job_description_generator.get_settings")
    def test_create_prompt_with_location_and_remote_policy(self, mock_get_settings):
        """Test creating prompt with location and remote policy."""
        mock_settings = Mock()
        mock_settings.llm_provider = "zai"
        mock_settings.llm_model = "gpt-4"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 2000
        mock_settings.zai_api_key = "test-key"
        mock_settings.zai_base_url = "https://api.zai.com/v1"
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        mock_settings.google_api_key = None
        mock_get_settings.return_value = mock_settings

        generator = JobDescriptionGenerator()

        prompt = generator._create_description_prompt(
            title="Developer",
            required_skills=["Python"],
            location="San Francisco, CA",
            remote_policy="hybrid"
        )

        assert "Location: San Francisco, CA" in prompt
        assert "Remote Policy: hybrid" in prompt

    @patch("analyzers.job_description_generator.get_settings")
    def test_create_prompt_with_salary_range(self, mock_get_settings):
        """Test creating prompt with salary range."""
        mock_settings = Mock()
        mock_settings.llm_provider = "zai"
        mock_settings.llm_model = "gpt-4"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 2000
        mock_settings.zai_api_key = "test-key"
        mock_settings.zai_base_url = "https://api.zai.com/v1"
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        mock_settings.google_api_key = None
        mock_get_settings.return_value = mock_settings

        generator = JobDescriptionGenerator()

        prompt = generator._create_description_prompt(
            title="Developer",
            required_skills=["Python"],
            salary_range="$100,000 - $150,000"
        )

        assert "Salary Range: $100,000 - $150,000" in prompt

    @patch("analyzers.job_description_generator.get_settings")
    def test_create_prompt_with_custom_sections(self, mock_get_settings):
        """Test creating prompt with custom sections."""
        mock_settings = Mock()
        mock_settings.llm_provider = "zai"
        mock_settings.llm_model = "gpt-4"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 2000
        mock_settings.zai_api_key = "test-key"
        mock_settings.zai_base_url = "https://api.zai.com/v1"
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        mock_settings.google_api_key = None
        mock_get_settings.return_value = mock_settings

        generator = JobDescriptionGenerator()

        custom_sections = {
            "Tech Stack": "Python, Django, PostgreSQL, Redis",
            "Culture": "Collaborative and inclusive team environment"
        }

        prompt = generator._create_description_prompt(
            title="Developer",
            required_skills=["Python"],
            custom_sections=custom_sections
        )

        assert "CUSTOM SECTIONS" in prompt
        assert "Tech Stack" in prompt
        assert "Culture" in prompt

    @patch("analyzers.job_description_generator.get_settings")
    def test_create_prompt_with_company_description(self, mock_get_settings):
        """Test creating prompt with company description."""
        mock_settings = Mock()
        mock_settings.llm_provider = "zai"
        mock_settings.llm_model = "gpt-4"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 2000
        mock_settings.zai_api_key = "test-key"
        mock_settings.zai_base_url = "https://api.zai.com/v1"
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        mock_settings.google_api_key = None
        mock_get_settings.return_value = mock_settings

        generator = JobDescriptionGenerator()

        prompt = generator._create_description_prompt(
            title="Developer",
            required_skills=["Python"],
            company_description="We are a fast-growing startup building AI-powered tools."
        )

        assert "COMPANY CONTEXT" in prompt
        assert "AI-powered tools" in prompt


class TestInclusiveLanguageChecking:
    """Tests for inclusive language checking."""

    def test_check_inclusive_language_with_biased_terms(self):
        """Test that biased terms are detected."""
        generator = JobDescriptionGenerator.__new__(JobDescriptionGenerator)

        text = "We are looking for a young, energetic salesman who is a native English speaker."

        score, warnings = generator._check_inclusive_language(text)

        assert score < 1.0
        assert len(warnings) > 0
        assert any("age" in w.lower() for w in warnings)
        assert any("gender" in w.lower() or "salesman" in w.lower() for w in warnings)

    def test_check_inclusive_language_with_welcoming_terms(self):
        """Test that welcoming language is recognized."""
        generator = JobDescriptionGenerator.__new__(JobDescriptionGenerator)

        text = "We encourage diverse candidates to apply. We value different perspectives."

        score, warnings = generator._check_inclusive_language(text)

        assert score >= 0.95
        # Should have fewer or no warnings compared to biased text

    def test_check_inclusive_language_without_welcoming_terms(self):
        """Test that missing welcoming language generates a warning."""
        generator = JobDescriptionGenerator.__new__(JobDescriptionGenerator)

        text = "We need a Python developer with Django experience."

        score, warnings = generator._check_inclusive_language(text)

        assert score < 1.0
        assert any("welcoming" in w.lower() for w in warnings)

    def test_check_inclusive_language_clips_score_to_valid_range(self):
        """Test that score is clipped to valid range [0.0, 1.0]."""
        generator = JobDescriptionGenerator.__new__(JobDescriptionGenerator)

        # Text with many biased terms
        text = "young energetic salesman chairman manpower mankind fresh digital native native speaker cultural fit"

        score, warnings = generator._check_inclusive_language(text)

        # Score should not go below 0.0
        assert score >= 0.0
        assert score <= 1.0


class TestFullDescriptionFormatting:
    """Tests for full description formatting."""

    def test_format_full_description_basic(self):
        """Test formatting a basic full description."""
        generator = JobDescriptionGenerator.__new__(JobDescriptionGenerator)

        full_desc = generator._format_full_description(
            summary="We are looking for a Python developer to join our team.",
            responsibilities=[
                "Develop backend services",
                "Write clean code"
            ],
            requirements=[
                "3+ years Python experience",
                "Django framework knowledge"
            ],
            benefits=[
                "Competitive salary",
                "Remote work"
            ],
            about_team="Join our collaborative engineering team."
        )

        assert "## About the Role" in full_desc
        assert "We are looking for a Python developer" in full_desc
        assert "## Key Responsibilities" in full_desc
        assert "Develop backend services" in full_desc
        assert "## Requirements" in full_desc
        assert "3+ years Python experience" in full_desc
        assert "## Benefits & Perks" in full_desc
        assert "Competitive salary" in full_desc
        assert "## About the Team" in full_desc
        assert "Join our collaborative engineering team" in full_desc

    def test_format_full_description_with_custom_sections(self):
        """Test formatting description with custom sections."""
        generator = JobDescriptionGenerator.__new__(JobDescriptionGenerator)

        full_desc = generator._format_full_description(
            summary="Summary text",
            responsibilities=["Responsibility 1"],
            requirements=["Requirement 1"],
            benefits=["Benefit 1"],
            about_team="Team info",
            custom_sections={
                "Tech Stack": "Python, Django, PostgreSQL",
                "Our Culture": "Inclusive and collaborative"
            }
        )

        assert "## Tech Stack" in full_desc
        assert "Python, Django, PostgreSQL" in full_desc
        assert "## Our Culture" in full_desc
        assert "Inclusive and collaborative" in full_desc


class TestLLMProviderCalls:
    """Tests for LLM provider API calls."""

    @pytest.mark.asyncio
    @patch("analyzers.job_description_generator.get_settings")
    async def test_call_zai_provider(self, mock_get_settings):
        """Test calling Z.ai API."""
        mock_settings = Mock()
        mock_settings.llm_provider = "zai"
        mock_settings.llm_model = "gpt-4"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 2000
        mock_settings.zai_api_key = "test-zai-key"
        mock_settings.zai_base_url = "https://api.zai.com/v1"
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        mock_settings.google_api_key = None
        mock_get_settings.return_value = mock_settings

        generator = JobDescriptionGenerator()

        mock_response = {
            "summary": "We are seeking a skilled Python developer.",
            "responsibilities": ["Develop Python applications"],
            "requirements": ["Python proficiency"],
            "benefits": ["Competitive salary"],
            "about_team": "Join our team",
            "inclusive_language_score": 0.95,
            "bias_warnings": []
        }

        with patch("analyzers.job_description_generator.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client

            mock_completion = AsyncMock()
            mock_completion.choices = [MagicMock()]
            mock_completion.choices[0].message.content = json.dumps(mock_response)
            mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

            result = await generator._call_zai("test prompt")

            assert result == mock_response
            mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    @patch("analyzers.job_description_generator.get_settings")
    async def test_call_zai_handles_json_wrapping(self, mock_get_settings):
        """Test that Z.ai response handles JSON in markdown code blocks."""
        mock_settings = Mock()
        mock_settings.llm_provider = "zai"
        mock_settings.llm_model = "gpt-4"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 2000
        mock_settings.zai_api_key = "test-zai-key"
        mock_settings.zai_base_url = "https://api.zai.com/v1"
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        mock_settings.google_api_key = None
        mock_get_settings.return_value = mock_settings

        generator = JobDescriptionGenerator()

        mock_response_data = {"summary": "Test summary"}
        wrapped_json = "```json\n" + json.dumps(mock_response_data) + "\n```"

        with patch("analyzers.job_description_generator.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client

            mock_completion = AsyncMock()
            mock_completion.choices = [MagicMock()]
            mock_completion.choices[0].message.content = wrapped_json
            mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

            result = await generator._call_zai("test prompt")

            assert result == mock_response_data

    @pytest.mark.asyncio
    @patch("analyzers.job_description_generator.get_settings")
    async def test_call_openai_provider(self, mock_get_settings):
        """Test calling OpenAI API."""
        mock_settings = Mock()
        mock_settings.llm_provider = "openai"
        mock_settings.llm_model = "gpt-4"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 2000
        mock_settings.zai_api_key = None
        mock_settings.zai_base_url = None
        mock_settings.openai_api_key = "test-openai-key"
        mock_settings.anthropic_api_key = None
        mock_settings.google_api_key = None
        mock_get_settings.return_value = mock_settings

        generator = JobDescriptionGenerator(provider=LLMProvider.OPENAI)

        mock_response = {"summary": "Test summary"}

        with patch("analyzers.job_description_generator.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client

            mock_completion = AsyncMock()
            mock_completion.choices = [MagicMock()]
            mock_completion.choices[0].message.content = json.dumps(mock_response)
            mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

            result = await generator._call_openai("test prompt")

            assert result == mock_response

    @pytest.mark.asyncio
    @patch("analyzers.job_description_generator.get_settings")
    async def test_call_anthropic_provider(self, mock_get_settings):
        """Test calling Anthropic API."""
        mock_settings = Mock()
        mock_settings.llm_provider = "anthropic"
        mock_settings.llm_model = "claude-3-sonnet"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 2000
        mock_settings.zai_api_key = None
        mock_settings.zai_base_url = None
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = "test-anthropic-key"
        mock_settings.google_api_key = None
        mock_get_settings.return_value = mock_settings

        generator = JobDescriptionGenerator(provider=LLMProvider.ANTHROPIC)

        mock_response = {"summary": "Test summary"}

        with patch("analyzers.job_description_generator.AsyncAnthropic") as mock_anthropic:
            mock_client = AsyncMock()
            mock_anthropic.return_value = mock_client

            mock_message = AsyncMock()
            mock_content = MagicMock()
            mock_content.text = json.dumps(mock_response)
            mock_message.content = [mock_content]
            mock_client.messages.create = AsyncMock(return_value=mock_message)

            result = await generator._call_anthropic("test prompt")

            assert result == mock_response

    @pytest.mark.asyncio
    @patch("analyzers.job_description_generator.get_settings")
    async def test_call_google_provider(self, mock_get_settings):
        """Test calling Google Gemini API."""
        mock_settings = Mock()
        mock_settings.llm_provider = "google"
        mock_settings.llm_model = "gemini-pro"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 2000
        mock_settings.zai_api_key = None
        mock_settings.zai_base_url = None
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        mock_settings.google_api_key = "test-google-key"
        mock_get_settings.return_value = mock_settings

        generator = JobDescriptionGenerator(provider=LLMProvider.GOOGLE)

        mock_response = {"summary": "Test summary"}

        with patch("analyzers.job_description_generator.genai") as mock_genai:
            mock_model = AsyncMock()
            mock_response_obj = MagicMock()
            mock_response_obj.text = json.dumps(mock_response)
            mock_model.generate_content_async = AsyncMock(return_value=mock_response_obj)
            mock_genai.GenerativeModel.return_value = mock_model

            result = await generator._call_google("test prompt")

            assert result == mock_response

    @pytest.mark.asyncio
    @patch("analyzers.job_description_generator.get_settings")
    async def test_call_unsupported_provider_raises_error(self, mock_get_settings):
        """Test that unsupported provider raises ValueError."""
        mock_settings = Mock()
        mock_settings.llm_provider = "zai"
        mock_settings.llm_model = "gpt-4"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 2000
        mock_settings.zai_api_key = "test-key"
        mock_settings.zai_base_url = "https://api.zai.com/v1"
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        mock_settings.google_api_key = None
        mock_get_settings.return_value = mock_settings

        generator = JobDescriptionGenerator()
        # Manually set an invalid provider
        generator.provider = "invalid_provider"

        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            await generator._call_llm("test prompt")


class TestDescriptionGeneration:
    """Tests for the main description generation functionality."""

    @pytest.fixture
    def mock_llm_response(self):
        """Create a mock LLM response for job description."""
        return {
            "summary": "We are seeking a skilled Senior Python Developer to join our innovative team.",
            "responsibilities": [
                "Design and implement scalable backend services using Python and Django",
                "Collaborate with cross-functional teams to define requirements",
                "Write clean, maintainable, and well-tested code",
                "Mentor junior developers and conduct code reviews"
            ],
            "requirements": [
                "5+ years of professional Python development experience",
                "Strong proficiency with Django or FastAPI frameworks",
                "Experience with PostgreSQL or similar relational databases",
                "Knowledge of RESTful API design principles",
                "Excellent problem-solving and communication skills"
            ],
            "benefits": [
                "Competitive salary and equity package",
                "Comprehensive health, dental, and vision insurance",
                "Flexible remote work policy",
                "Professional development budget"
            ],
            "about_team": "Join our collaborative engineering team focused on building innovative solutions.",
            "inclusive_language_score": 0.95,
            "bias_warnings": []
        }

    @pytest.mark.asyncio
    @patch("analyzers.job_description_generator.get_settings")
    async def test_generate_description_success(self, mock_get_settings, mock_llm_response):
        """Test successful description generation."""
        mock_settings = Mock()
        mock_settings.llm_provider = "zai"
        mock_settings.llm_model = "gpt-4"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 2000
        mock_settings.zai_api_key = "test-key"
        mock_settings.zai_base_url = "https://api.zai.com/v1"
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        mock_settings.google_api_key = None
        mock_get_settings.return_value = mock_settings

        generator = JobDescriptionGenerator()

        with patch.object(generator, '_call_llm', new=AsyncMock(return_value=mock_llm_response)):
            result = await generator.generate_description(
                title="Senior Python Developer",
                required_skills=["Python", "Django", "PostgreSQL"],
                min_experience_months=60,
                seniority_level="senior"
            )

            assert isinstance(result, JobDescriptionResult)
            assert result.title == "Senior Python Developer"
            assert len(result.responsibilities) == 4
            assert len(result.requirements) == 5
            assert len(result.benefits) == 4
            assert result.inclusive_language_score == 0.95
            assert len(result.bias_warnings) == 0
            assert result.provider == "zai"
            assert result.model == "gpt-4"

    @pytest.mark.asyncio
    @patch("analyzers.job_description_generator.get_settings")
    async def test_generate_description_with_all_parameters(self, mock_get_settings, mock_llm_response):
        """Test description generation with all optional parameters."""
        mock_settings = Mock()
        mock_settings.llm_provider = "zai"
        mock_settings.llm_model = "gpt-4"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 2000
        mock_settings.zai_api_key = "test-key"
        mock_settings.zai_base_url = "https://api.zai.com/v1"
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        mock_settings.google_api_key = None
        mock_get_settings.return_value = mock_settings

        generator = JobDescriptionGenerator()

        with patch.object(generator, '_call_llm', new=AsyncMock(return_value=mock_llm_response)):
            result = await generator.generate_description(
                title="Senior Python Developer",
                required_skills=["Python", "Django"],
                min_experience_months=60,
                seniority_level="senior",
                employment_type="full_time",
                department="Engineering",
                industry="Technology",
                location="San Francisco, CA",
                remote_policy="hybrid",
                salary_range="$120,000 - $160,000",
                additional_requirements=["AWS experience"],
                responsibilities=["Lead development projects"],
                company_description="Fast-growing startup",
                custom_sections={"Tech Stack": "Python, Django, PostgreSQL"},
                language="en"
            )

            assert isinstance(result, JobDescriptionResult)
            assert result.suggested_salary_range == "$120,000 - $160,000"

    @pytest.mark.asyncio
    @patch("analyzers.job_description_generator.get_settings")
    async def test_generate_description_validates_required_fields(self, mock_get_settings):
        """Test that required fields are validated."""
        mock_settings = Mock()
        mock_settings.llm_provider = "zai"
        mock_settings.llm_model = "gpt-4"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 2000
        mock_settings.zai_api_key = "test-key"
        mock_settings.zai_base_url = "https://api.zai.com/v1"
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        mock_settings.google_api_key = None
        mock_get_settings.return_value = mock_settings

        generator = JobDescriptionGenerator()

        # Test empty title
        with pytest.raises(ValueError, match="Job title is required"):
            await generator.generate_description(
                title="",
                required_skills=["Python"]
            )

        # Test empty required skills
        with pytest.raises(ValueError, match="At least one required skill"):
            await generator.generate_description(
                title="Developer",
                required_skills=[]
            )

    @pytest.mark.asyncio
    @patch("analyzers.job_description_generator.get_settings")
    async def test_generate_description_handles_llm_error(self, mock_get_settings):
        """Test that LLM errors are handled gracefully."""
        mock_settings = Mock()
        mock_settings.llm_provider = "zai"
        mock_settings.llm_model = "gpt-4"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 2000
        mock_settings.zai_api_key = "test-key"
        mock_settings.zai_base_url = "https://api.zai.com/v1"
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        mock_settings.google_api_key = None
        mock_get_settings.return_value = mock_settings

        generator = JobDescriptionGenerator()

        with patch.object(generator, '_call_llm', new=AsyncMock(side_effect=Exception("API Error"))):
            result = await generator.generate_description(
                title="Developer",
                required_skills=["Python"]
            )

            # Should return a minimal result instead of crashing
            assert isinstance(result, JobDescriptionResult)
            assert "generation failed" in result.summary.lower()
            assert len(result.bias_warnings) > 0

    @pytest.mark.asyncio
    @patch("analyzers.job_description_generator.get_settings")
    async def test_generate_description_computes_inclusive_score_if_missing(self, mock_get_settings):
        """Test that inclusive language score is computed if LLM doesn't provide it."""
        mock_settings = Mock()
        mock_settings.llm_provider = "zai"
        mock_settings.llm_model = "gpt-4"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 2000
        mock_settings.zai_api_key = "test-key"
        mock_settings.zai_base_url = "https://api.zai.com/v1"
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        mock_settings.google_api_key = None
        mock_get_settings.return_value = mock_settings

        generator = JobDescriptionGenerator()

        # Response without inclusive_language_score
        response_without_score = {
            "summary": "We value diverse candidates and encourage everyone to apply.",
            "responsibilities": ["Develop applications"],
            "requirements": ["Python experience"],
            "benefits": ["Competitive salary"],
            "about_team": "Our team",
            "bias_warnings": []
        }

        with patch.object(generator, '_call_llm', new=AsyncMock(return_value=response_without_score)):
            result = await generator.generate_description(
                title="Developer",
                required_skills=["Python"]
            )

            # Score should be computed
            assert result.inclusive_language_score is not None
            assert isinstance(result.inclusive_language_score, float)


class TestSynchronousWrapper:
    """Tests for synchronous wrapper method."""

    @patch("analyzers.job_description_generator.get_settings")
    def test_generate_description_sync(self, mock_get_settings):
        """Test synchronous wrapper for description generation."""
        mock_settings = Mock()
        mock_settings.llm_provider = "zai"
        mock_settings.llm_model = "gpt-4"
        mock_settings.llm_temperature = 0.7
        mock_settings.llm_max_tokens = 2000
        mock_settings.zai_api_key = "test-key"
        mock_settings.zai_base_url = "https://api.zai.com/v1"
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        mock_settings.google_api_key = None
        mock_get_settings.return_value = mock_settings

        generator = JobDescriptionGenerator()

        mock_result = JobDescriptionResult(
            title="Developer",
            summary="Summary",
            provider="zai",
            model="gpt-4",
            generated_at=datetime.utcnow().isoformat()
        )

        with patch.object(generator, 'generate_description', new=AsyncMock(return_value=mock_result)):
            result = generator.generate_description_sync(
                title="Developer",
                required_skills=["Python"]
            )

            assert isinstance(result, JobDescriptionResult)
            assert result.provider == "zai"


class TestHelperFunctions:
    """Tests for module-level helper functions."""

    @patch("analyzers.job_description_generator.get_settings")
    def test_get_job_description_generator_with_api_key(self, mock_get_settings):
        """Test getting generator when API key is configured."""
        mock_settings = Mock()
        mock_settings.zai_api_key = "test-key"
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        mock_settings.google_api_key = None
        mock_get_settings.return_value = mock_settings

        generator = get_job_description_generator()

        assert generator is not None
        assert isinstance(generator, JobDescriptionGenerator)

    @patch("analyzers.job_description_generator.get_settings")
    def test_get_job_description_generator_without_api_key(self, mock_get_settings):
        """Test getting generator when no API key is configured."""
        mock_settings = Mock()
        mock_settings.zai_api_key = None
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        mock_settings.google_api_key = None
        mock_get_settings.return_value = mock_settings

        generator = get_job_description_generator()

        assert generator is None

    @patch("analyzers.job_description_generator.get_settings")
    def test_get_job_description_generator_singleton(self, mock_get_settings):
        """Test that generator is cached as singleton."""
        mock_settings = Mock()
        mock_settings.zai_api_key = "test-key"
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        mock_settings.google_api_key = None
        mock_get_settings.return_value = mock_settings

        generator1 = get_job_description_generator()
        generator2 = get_job_description_generator()

        assert generator1 is generator2

    @pytest.mark.asyncio
    @patch("analyzers.job_description_generator.get_settings")
    @patch("analyzers.job_description_generator.get_job_description_generator")
    async def test_generate_job_description_convenience_function(self, mock_get_generator, mock_get_settings):
        """Test the convenience function for generating descriptions."""
        mock_settings = Mock()
        mock_get_settings.return_value = mock_settings

        mock_generator = Mock()
        mock_result = JobDescriptionResult(
            title="Developer",
            summary="Summary",
            provider="zai",
            model="gpt-4",
            generated_at=datetime.utcnow().isoformat()
        )
        mock_generator.generate_description = AsyncMock(return_value=mock_result)
        mock_get_generator.return_value = mock_generator

        result = await generate_job_description(
            title="Developer",
            required_skills=["Python"]
        )

        assert result is not None
        assert isinstance(result, JobDescriptionResult)
        mock_generator.generate_description.assert_called_once()

    @pytest.mark.asyncio
    @patch("analyzers.job_description_generator.get_settings")
    @patch("analyzers.job_description_generator.get_job_description_generator")
    async def test_generate_job_description_returns_none_when_unavailable(self, mock_get_generator, mock_get_settings):
        """Test convenience function returns None when generator unavailable."""
        mock_settings = Mock()
        mock_get_settings.return_value = mock_settings

        mock_get_generator.return_value = None

        result = await generate_job_description(
            title="Developer",
            required_skills=["Python"]
        )

        assert result is None


class TestDataClasses:
    """Tests for data classes and serialization."""

    def test_job_description_section_to_dict(self):
        """Test JobDescriptionSection serialization."""
        section = JobDescriptionSection(
            title="About the Role",
            content="We are looking for a developer",
            order=0
        )

        result = section.to_dict()

        assert result["title"] == "About the Role"
        assert result["content"] == "We are looking for a developer"
        assert result["order"] == 0

    def test_job_description_result_to_dict(self):
        """Test JobDescriptionResult serialization."""
        result = JobDescriptionResult(
            title="Senior Python Developer",
            summary="We are seeking a skilled developer",
            responsibilities=["Responsibility 1"],
            requirements=["Requirement 1"],
            benefits=["Benefit 1"],
            sections=[
                JobDescriptionSection(
                    title="About Team",
                    content="Team info",
                    order=0
                )
            ],
            full_description="Full description text",
            suggested_salary_range="$100k - $150k",
            inclusive_language_score=0.95,
            bias_warnings=["Warning 1"],
            provider="zai",
            model="gpt-4",
            generated_at="2024-01-01T00:00:00"
        )

        result_dict = result.to_dict()

        assert result_dict["title"] == "Senior Python Developer"
        assert result_dict["summary"] == "We are seeking a skilled developer"
        assert len(result_dict["responsibilities"]) == 1
        assert len(result_dict["sections"]) == 1
        assert result_dict["inclusive_language_score"] == 0.95
        assert result_dict["provider"] == "zai"


@pytest.mark.parametrize("provider,expected_value", [
    (LLMProvider.OPENAI, "openai"),
    (LLMProvider.ANTHROPIC, "anthropic"),
    (LLMProvider.GOOGLE, "google"),
    (LLMProvider.ZAI, "zai"),
])
def test_llm_provider_enum_values(provider, expected_value):
    """Test LLMProvider enum values."""
    assert provider.value == expected_value


@pytest.mark.parametrize("employment_type,expected_value", [
    (EmploymentType.FULL_TIME, "full_time"),
    (EmploymentType.PART_TIME, "part_time"),
    (EmploymentType.CONTRACT, "contract"),
    (EmploymentType.INTERNSHIP, "internship"),
    (EmploymentType.FREELANCE, "freelance"),
])
def test_employment_type_enum_values(employment_type, expected_value):
    """Test EmploymentType enum values."""
    assert employment_type.value == expected_value


@pytest.mark.parametrize("seniority_level,expected_value", [
    (SeniorityLevel.ENTRY, "entry"),
    (SeniorityLevel.MID, "mid"),
    (SeniorityLevel.SENIOR, "senior"),
    (SeniorityLevel.LEAD, "lead"),
    (SeniorityLevel.EXECUTIVE, "executive"),
])
def test_seniority_level_enum_values(seniority_level, expected_value):
    """Test SeniorityLevel enum values."""
    assert seniority_level.value == expected_value
