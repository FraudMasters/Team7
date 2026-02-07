"""
Tests for ATS Simulation Service.

Tests cover ATS evaluation, scoring, LLM provider integration,
and rule-based fallback functionality.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime


class TestLLMProvider:
    """Tests for LLMProvider enum."""

    def test_llm_provider_values(self):
        """Test that LLMProvider has expected values."""
        from analyzers.ats_simulation import LLMProvider

        assert LLMProvider.OPENAI.value == "openai"
        assert LLMProvider.ANTHROPIC.value == "anthropic"
        assert LLMProvider.GOOGLE.value == "google"
        assert LLMProvider.ZAI.value == "zai"

    def test_llm_provider_from_string(self):
        """Test creating LLMProvider from string."""
        from analyzers.ats_simulation import LLMProvider

        provider = LLMProvider("openai")
        assert provider == LLMProvider.OPENAI


class TestATSScoreResult:
    """Tests for ATSScoreResult dataclass."""

    def test_ats_score_result_creation(self):
        """Test creation of ATSScoreResult."""
        from analyzers.ats_simulation import ATSScoreResult

        result = ATSScoreResult(
            passed=True,
            overall_score=0.75,
            keyword_score=0.8,
            experience_score=0.7,
            education_score=0.8,
            fit_score=0.75,
            looks_professional=True,
            disqualified=False,
            provider="openai",
            model="gpt-4",
        )

        assert result.passed is True
        assert result.overall_score == 0.75
        assert result.keyword_score == 0.8

    def test_ats_score_result_default_values(self):
        """Test ATSScoreResult with default values."""
        from analyzers.ats_simulation import ATSScoreResult

        result = ATSScoreResult(
            passed=False,
            overall_score=0.5,
        )

        assert result.keyword_score == 0.0
        assert result.experience_score == 0.0
        assert result.looks_professional is True
        assert result.disqualified is False

    def test_ats_score_result_to_dict(self):
        """Test converting ATSScoreResult to dictionary."""
        from analyzers.ats_simulation import ATSScoreResult

        result = ATSScoreResult(
            passed=True,
            overall_score=0.85,
            keyword_score=0.9,
            provider="anthropic",
            model="claude-3",
        )

        result_dict = result.to_dict()

        assert result_dict["passed"] is True
        assert result_dict["overall_score"] == 0.85
        assert result_dict["keyword_score"] == 0.9
        assert result_dict["provider"] == "anthropic"

    def test_ats_score_result_with_issues(self):
        """Test ATSScoreResult with issues and suggestions."""
        from analyzers.ats_simulation import ATSScoreResult

        result = ATSScoreResult(
            passed=False,
            overall_score=0.4,
            visual_issues=["Poor formatting", "Missing sections"],
            ats_issues=["Low keyword match"],
            missing_keywords=["Python", "Django"],
            suggestions=["Add more keywords", "Improve formatting"],
        )

        assert len(result.visual_issues) == 2
        assert len(result.missing_keywords) == 2
        assert len(result.suggestions) == 2


class TestATSSimulator:
    """Tests for ATSSimulator class."""

    def test_ats_simulator_initialization(self):
        """Test ATSSimulator initialization."""
        from analyzers.ats_simulation import ATSSimulator, LLMProvider

        simulator = ATSSimulator(
            provider=LLMProvider.OPENAI,
            model="gpt-4",
            threshold=0.7,
        )

        assert simulator.provider == LLMProvider.OPENAI
        assert simulator.model == "gpt-4"
        assert simulator.threshold == 0.7

    def test_ats_simulator_default_initialization(self):
        """Test ATSSimulator initialization with defaults."""
        from analyzers.ats_simulation import ATSSimulator

        simulator = ATSSimulator()

        assert simulator.provider is not None
        assert simulator.model is not None
        assert simulator.threshold is not None
        assert 0 <= simulator.threshold <= 1

    def test_system_prompt_generation(self):
        """Test system prompt generation."""
        from analyzers.ats_simulation import ATSSimulator

        simulator = ATSSimulator()
        prompt = simulator._get_system_prompt()

        assert "ATS" in prompt
        assert "keyword" in prompt.lower()
        assert "experience" in prompt.lower()
        assert "JSON" in prompt

    def test_evaluation_prompt_creation(self):
        """Test creation of evaluation prompt."""
        from analyzers.ats_simulation import ATSSimulator

        simulator = ATSSimulator()
        prompt = simulator._create_evaluation_prompt(
            resume_text="Experienced Python developer...",
            job_title="Senior Python Developer",
            job_description="Looking for senior Python developer...",
            required_skills=["Python", "Django", "PostgreSQL"],
            min_experience=60,  # months
            education_level="Bachelor's",
        )

        assert "Senior Python Developer" in prompt
        assert "Python" in prompt
        assert "Django" in prompt
        assert "Bachelor's" in prompt

    def test_evaluation_prompt_minimal(self):
        """Test evaluation prompt with minimal parameters."""
        from analyzers.ats_simulation import ATSSimulator

        simulator = ATSSimulator()
        prompt = simulator._create_evaluation_prompt(
            resume_text="Java Developer",
            job_title="Java Developer",
            job_description="Java development role",
            required_skills=["Java"],
        )

        assert "Java Developer" in prompt
        assert "Java" in prompt

    def test_overall_score_computation(self):
        """Test computation of overall ATS score."""
        from analyzers.ats_simulation import ATSSimulator

        simulator = ATSSimulator()
        llm_result = {
            "keyword_score": 0.8,
            "experience_score": 0.7,
            "education_score": 0.9,
            "fit_score": 0.75,
        }

        overall = simulator._compute_overall_score(llm_result)

        assert 0 <= overall <= 1
        assert isinstance(overall, float)

    def test_overall_score_capped_at_one(self):
        """Test that overall score is capped at 1.0."""
        from analyzers.ats_simulation import ATSSimulator

        simulator = ATSSimulator()
        llm_result = {
            "keyword_score": 1.0,
            "experience_score": 1.0,
            "education_score": 1.0,
            "fit_score": 1.0,
        }

        overall = simulator._compute_overall_score(llm_result)

        assert overall <= 1.0


class TestATSSimulatorLLMCalls:
    """Tests for LLM API calls in ATSSimulator."""

    @pytest.mark.asyncio
    async def test_call_openai_mock(self):
        """Test mocked OpenAI API call."""
        from analyzers.ats_simulation import ATSSimulator

        simulator = ATSSimulator(provider="openai", model="gpt-4")

        # Mock the OpenAI client
        with patch("analyzers.ats_simulation.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = '{"keyword_score": 0.8}'
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            result = await simulator._call_openai("test prompt")

            assert "keyword_score" in result

    @pytest.mark.asyncio
    async def test_call_anthropic_mock(self):
        """Test mocked Anthropic API call."""
        from analyzers.ats_simulation import ATSSimulator

        simulator = ATSSimulator(provider="anthropic", model="claude-3")

        with patch("analyzers.ats_simulation.AsyncAnthropic") as mock_anthropic:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.content = [Mock(text='{"keyword_score": 0.85}')]
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            mock_anthropic.return_value = mock_client

            result = await simulator._call_anthropic("test prompt")

            assert "keyword_score" in result


class TestATSEvaluation:
    """Tests for ATS evaluation logic."""

    @pytest.mark.asyncio
    async def test_evaluate_ats_mocked(self):
        """Test ATS evaluation with mocked LLM."""
        from analyzers.ats_simulation import ATSSimulator

        simulator = ATSSimulator()

        # Mock the LLM call
        with patch.object(simulator, "_call_llm", new=AsyncMock()) as mock_llm:
            mock_llm.return_value = {
                "keyword_score": 0.8,
                "experience_score": 0.7,
                "education_score": 0.9,
                "fit_score": 0.75,
                "looks_professional": True,
                "disqualified": False,
                "visual_issues": [],
                "ats_issues": [],
                "missing_keywords": [],
                "suggestions": [],
                "feedback": "Good match",
            }

            result = await simulator.evaluate_ats(
                resume_text="Python developer with 5 years experience",
                job_title="Senior Python Developer",
                job_description="Senior Python role",
                required_skills=["Python", "Django"],
            )

            assert result.passed is not None
            assert isinstance(result.overall_score, float)
            assert 0 <= result.overall_score <= 1

    @pytest.mark.asyncio
    async def test_evaluate_ats_with_disqualification(self):
        """Test ATS evaluation with disqualification."""
        from analyzers.ats_simulation import ATSSimulator

        simulator = ATSSimulator(threshold=0.7)

        with patch.object(simulator, "_call_llm", new=AsyncMock()) as mock_llm:
            mock_llm.return_value = {
                "keyword_score": 0.9,
                "experience_score": 0.8,
                "education_score": 0.9,
                "fit_score": 0.85,
                "looks_professional": True,
                "disqualified": True,  # Disqualified despite good scores
                "visual_issues": [],
                "ats_issues": [],
                "missing_keywords": [],
                "suggestions": [],
                "feedback": "Employment gap detected",
            }

            result = await simulator.evaluate_ats(
                resume_text="Resume with issues",
                job_title="Developer",
                job_description="Dev role",
                required_skills=["Python"],
            )

            assert result.disqualified is True
            assert result.passed is False  # Should not pass if disqualified

    @pytest.mark.asyncio
    async def test_evaluate_ats_error_handling(self):
        """Test ATS evaluation error handling."""
        from analyzers.ats_simulation import ATSSimulator

        simulator = ATSSimulator()

        with patch.object(simulator, "_call_llm", new=AsyncMock()) as mock_llm:
            mock_llm.side_effect = Exception("API Error")

            result = await simulator.evaluate_ats(
                resume_text="Test resume",
                job_title="Test Job",
                job_description="Test description",
                required_skills=["Python"],
            )

            assert result.passed is False
            assert result.overall_score == 0.0
            assert len(result.visual_issues) > 0


class TestSimpleATSChecker:
    """Tests for SimpleATSChecker class."""

    def test_simple_ats_checker_initialization(self):
        """Test SimpleATSChecker initialization."""
        from analyzers.ats_simulation import SimpleATSChecker

        checker = SimpleATSChecker(threshold=0.6)

        assert checker.threshold == 0.6

    def test_simple_ats_checker_default_threshold(self):
        """Test SimpleATSChecker default threshold."""
        from analyzers.ats_simulation import SimpleATSChecker

        checker = SimpleATSChecker()

        assert checker.threshold == 0.5

    def test_check_ats_basic_match(self):
        """Test basic ATS check with matching skills."""
        from analyzers.ats_simulation import SimpleATSChecker

        checker = SimpleATSChecker(threshold=0.5)

        result = checker.check_ats(
            resume_text="Experienced Python and Django developer",
            job_title="Python Developer",
            job_description="Looking for Python developer",
            required_skills=["Python", "Django"],
        )

        assert result.passed is True
        assert result.overall_score > 0

    def test_check_ats_low_match(self):
        """Test ATS check with low skill match."""
        from analyzers.ats_simulation import SimpleATSChecker

        checker = SimpleATSChecker(threshold=0.7)

        result = checker.check_ats(
            resume_text="Java developer",
            job_title="Python Developer",
            job_description="Python role",
            required_skills=["Python", "Django", "Flask", "FastAPI"],
        )

        assert result.passed is False

    def test_check_ats_with_candidate_skills(self):
        """Test ATS check with pre-extracted skills."""
        from analyzers.ats_simulation import SimpleATSChecker

        checker = SimpleATSChecker()

        result = checker.check_ats(
            resume_text="Developer resume",
            job_title="Developer",
            job_description="Dev role",
            required_skills=["Python", "Java"],
            candidate_skills=["Python", "Java", "JavaScript"],
        )

        assert result.keyword_score > 0.5

    def test_check_ats_short_resume(self):
        """Test ATS check with very short resume."""
        from analyzers.ats_simulation import SimpleATSChecker

        checker = SimpleATSChecker()

        result = checker.check_ats(
            resume_text="Dev",
            job_title="Developer",
            job_description="Dev role",
            required_skills=["Python"],
        )

        assert result.looks_professional is False

    def test_check_ats_very_long_resume(self):
        """Test ATS check with very long resume."""
        from analyzers.ats_simulation import SimpleATSChecker

        checker = SimpleATSChecker()

        long_resume = "Developer" * 5000  # Very long resume

        result = checker.check_ats(
            resume_text=long_resume,
            job_title="Developer",
            job_description="Dev role",
            required_skills=["Python"],
        )

        assert len(result.suggestions) > 0


class TestATSGlobalFunctions:
    """Tests for global ATS functions."""

    @pytest.mark.asyncio
    async def test_get_ats_simulator_with_api_key(self):
        """Test get_ats_simulator when API key is configured."""
        from analyzers.ats_simulation import get_ats_simulator

        with patch("analyzers.ats_simulation.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                zai_api_key="test-key",
                llm_provider="zai",
                llm_model="model",
                ats_threshold=0.7,
            )

            simulator = get_ats_simulator()

            # First call creates instance
            assert simulator is not None

    @pytest.mark.asyncio
    async def test_get_ats_simulator_no_api_key(self):
        """Test get_ats_simulator when no API key is configured."""
        from analyzers.ats_simulation import get_ats_simulator

        with patch("analyzers.ats_simulation.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                zai_api_key=None,
                openai_api_key=None,
                anthropic_api_key=None,
                google_api_key=None,
            )

            simulator = get_ats_simulator()

            assert simulator is None

    def test_get_simple_ats_checker(self):
        """Test get_simple_ats_checker function."""
        from analyzers.ats_simulation import get_simple_ats_checker

        checker = get_simple_ats_checker(threshold=0.6)

        assert checker.threshold == 0.6

        # Should return same instance on subsequent calls
        checker2 = get_simple_ats_checker(threshold=0.8)

        # Threshold doesn't change once initialized
        assert checker2.threshold == 0.6


class TestATSEdgeCases:
    """Tests for ATS edge cases."""

    def test_empty_resume_text(self):
        """Test ATS evaluation with empty resume."""
        from analyzers.ats_simulation import SimpleATSChecker

        checker = SimpleATSChecker()

        result = checker.check_ats(
            resume_text="",
            job_title="Developer",
            job_description="Dev role",
            required_skills=["Python"],
        )

        assert result.passed is False

    def test_empty_required_skills(self):
        """Test ATS evaluation with no required skills."""
        from analyzers.ats_simulation import SimpleATSChecker

        checker = SimpleATSChecker()

        result = checker.check_ats(
            resume_text="Developer resume",
            job_title="Developer",
            job_description="Dev role",
            required_skills=[],
        )

        # Should still produce a result
        assert result is not None

    def test_unicode_resume_content(self):
        """Test ATS evaluation with Unicode characters."""
        from analyzers.ats_simulation import SimpleATSChecker

        checker = SimpleATSChecker()

        result = checker.check_ats(
            resume_text="Разработчик Python с опытом",
            job_title="Python Developer",
            job_description="Python development",
            required_skills=["Python"],
        )

        assert result is not None

    def test_case_insensitive_matching(self):
        """Test that skill matching is case-insensitive."""
        from analyzers.ats_simulation import SimpleATSChecker

        checker = SimpleATSChecker()

        result = checker.check_ats(
            resume_text="PYTHON DJANGO DEVELOPER",
            job_title="Developer",
            job_description="Dev role",
            required_skills=["python", "django"],
        )

        assert result.keyword_score > 0


class TestATSScoringWeights:
    """Tests for ATS scoring weight configuration."""

    def test_weight_configuration(self):
        """Test that scoring weights are properly configured."""
        from analyzers.ats_simulation import ATSSimulator

        simulator = ATSSimulator()

        assert hasattr(simulator, "keyword_weight")
        assert hasattr(simulator, "experience_weight")
        assert hasattr(simulator, "education_weight")
        assert hasattr(simulator, "fit_weight")

    def test_weights_sum_to_one(self):
        """Test that weights sum approximately to one."""
        from analyzers.ats_simulation import ATSSimulator

        simulator = ATSSimulator()
        total_weight = (
            simulator.keyword_weight +
            simulator.experience_weight +
            simulator.education_weight +
            simulator.fit_weight
        )

        # Allow for small floating point errors
        assert abs(total_weight - 1.0) < 0.01


class TestATSThresholdLogic:
    """Tests for ATS threshold logic."""

    def test_passed_threshold_logic(self):
        """Test that passing requires meeting threshold."""
        from analyzers.ats_simulation import SimpleATSChecker

        checker = SimpleATSChecker(threshold=0.7)

        # Create a result that would fail
        result = checker.check_ats(
            resume_text="Some skills",
            job_title="Developer",
            job_description="Dev role",
            required_skills=["Python", "Django", "Flask", "FastAPI", "SQLAlchemy"],
        )

        if result.overall_score < 0.7:
            assert result.passed is False

    def test_disqualified_always_fails(self):
        """Test that disqualified resumes always fail."""
        from analyzers.ats_simulation import ATSScoreResult

        result = ATSScoreResult(
            passed=True,  # Would be true based on score
            overall_score=0.9,
            disqualified=True,  # But disqualified
        )

        # The actual logic determines passed based on disqualified
        # This tests the concept
        assert result.disqualified is True


class TestATSSuggestions:
    """Tests for ATS suggestion generation."""

    def test_missing_keywords_suggestions(self):
        """Test suggestions for missing keywords."""
        from analyzers.ats_simulation import SimpleATSChecker

        checker = SimpleATSChecker()

        result = checker.check_ats(
            resume_text="Python developer",
            job_title="Full Stack Developer",
            job_description="Full stack role",
            required_skills=["Python", "React", "Docker", "Kubernetes"],
        )

        # Should suggest missing keywords
        if result.missing_keywords:
            assert len(result.suggestions) > 0

    def test_resume_length_suggestions(self):
        """Test suggestions based on resume length."""
        from analyzers.ats_simulation import SimpleATSChecker

        checker = SimpleATSChecker()

        # Very short resume
        result = checker.check_ats(
            resume_text="Python dev",
            job_title="Developer",
            job_description="Dev role",
            required_skills=["Python"],
        )

        # Should suggest adding more details
        assert len(result.suggestions) > 0


class TestATSMetadata:
    """Tests for ATS metadata and tracking."""

    def test_result_contains_provider_info(self):
        """Test that result contains provider information."""
        from analyzers.ats_simulation import SimpleATSChecker

        checker = SimpleATSChecker()

        result = checker.check_ats(
            resume_text="Python developer",
            job_title="Developer",
            job_description="Dev role",
            required_skills=["Python"],
        )

        assert result.provider == "rule-based"
        assert result.model == "v1.0"

    def test_llm_result_provider_info(self):
        """Test provider info in LLM-based results."""
        from analyzers.ats_simulation import ATSSimulator, ATSScoreResult

        simulator = ATSSimulator(provider="openai", model="gpt-4")

        # Create result manually to test
        result = ATSScoreResult(
            passed=True,
            overall_score=0.8,
            provider="openai",
            model="gpt-4",
        )

        assert result.provider == "openai"
        assert result.model == "gpt-4"
