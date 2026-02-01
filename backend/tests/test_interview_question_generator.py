"""
Unit Tests for Interview Question Generator

Tests the LLM-based interview question generation module that creates
customized interview questions based on candidate resumes and job requirements.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime
import json
import asyncio

from analyzers.interview_question_generator import (
    InterviewQuestionGenerator,
    Question,
    InterviewPrepResult,
    QuestionCategory,
    LLMProvider,
    get_interview_question_generator,
    generate_interview_questions,
)


class TestInterviewQuestionGeneratorInit:
    """Tests for InterviewQuestionGenerator initialization."""

    @patch("analyzers.interview_question_generator.get_settings")
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

        generator = InterviewQuestionGenerator()

        assert generator.provider == LLMProvider.ZAI
        assert generator.model == "gpt-4"
        assert generator.temperature == 0.7
        assert generator.max_tokens == 2000
        assert generator.zai_api_key == "test-zai-key"

    @patch("analyzers.interview_question_generator.get_settings")
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

        generator = InterviewQuestionGenerator(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-sonnet"
        )

        assert generator.provider == LLMProvider.ANTHROPIC
        assert generator.model == "claude-3-sonnet"

    @patch("analyzers.interview_question_generator.get_settings")
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

        generator = InterviewQuestionGenerator()

        assert generator.provider == LLMProvider.ANTHROPIC
        assert generator.model == "claude-3-opus"
        assert generator.anthropic_api_key == "test-anthropic-key"

    @patch("analyzers.interview_question_generator.get_settings")
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

        generator = InterviewQuestionGenerator()

        assert generator.provider == LLMProvider.GOOGLE
        assert generator.model == "gemini-pro"
        assert generator.google_api_key == "test-google-key"


class TestQuestionPromptCreation:
    """Tests for question generation prompt creation."""

    @patch("analyzers.interview_question_generator.get_settings")
    def test_create_basic_prompt(self, mock_get_settings):
        """Test creating a basic question generation prompt."""
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

        generator = InterviewQuestionGenerator()

        prompt = generator._create_question_prompt(
            resume_text="Senior Python developer with 5 years experience",
            job_title="Senior Python Developer",
            job_description="Looking for senior Python developer",
            required_skills=["Python", "Django", "PostgreSQL"]
        )

        assert "Senior Python developer with 5 years experience" in prompt
        assert "Senior Python Developer" in prompt
        assert "Looking for senior Python developer" in prompt
        assert "Python, Django, PostgreSQL" in prompt

    @patch("analyzers.interview_question_generator.get_settings")
    def test_create_prompt_with_candidate_skills(self, mock_get_settings):
        """Test creating prompt with extracted candidate skills."""
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

        generator = InterviewQuestionGenerator()

        prompt = generator._create_question_prompt(
            resume_text="Resume text",
            job_title="Developer",
            job_description="Job description",
            required_skills=["Python"],
            candidate_skills=["Python", "Django", "FastAPI"]
        )

        assert "Extracted Skills:" in prompt
        assert "Python, Django, FastAPI" in prompt

    @patch("analyzers.interview_question_generator.get_settings")
    def test_create_prompt_with_skill_gaps(self, mock_get_settings):
        """Test creating prompt with skill gaps."""
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

        generator = InterviewQuestionGenerator()

        prompt = generator._create_question_prompt(
            resume_text="Resume text",
            job_title="Developer",
            job_description="Job description",
            required_skills=["Python", "PostgreSQL"],
            skill_gaps=["PostgreSQL", "Redis"]
        )

        assert "Skill Gaps to Address:" in prompt
        assert "PostgreSQL, Redis" in prompt

    @patch("analyzers.interview_question_generator.get_settings")
    def test_create_prompt_with_experience_and_seniority(self, mock_get_settings):
        """Test creating prompt with experience and seniority level."""
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

        generator = InterviewQuestionGenerator()

        prompt = generator._create_question_prompt(
            resume_text="Resume text",
            job_title="Senior Developer",
            job_description="Job description",
            required_skills=["Python"],
            min_experience=60,  # 5 years in months
            seniority_level="senior"
        )

        assert "Minimum Experience Required: 5 years" in prompt
        assert "Seniority Level: senior" in prompt


class TestQuestionParsing:
    """Tests for question data parsing."""

    def test_parse_technical_questions(self):
        """Test parsing technical questions from LLM response."""
        generator = InterviewQuestionGenerator.__new__(InterviewQuestionGenerator)

        questions_data = [
            {
                "id": "tech_1",
                "text": "Explain how Python's GIL affects multi-threaded applications",
                "difficulty": "advanced",
                "skills": ["Python", "Concurrency"],
                "rationale": "Test understanding of Python internals",
                "expected_answers": ["GIL limits parallelism", "Only one thread executes bytecode"],
                "follow_up_suggestions": ["How do you work around GIL limitations?"]
            },
            {
                "id": "tech_2",
                "text": "Describe Django's MTV architecture",
                "difficulty": "intermediate",
                "skills": ["Django"],
                "rationale": "Assess Django knowledge",
                "expected_answers": ["Model-View-Template", "Separation of concerns"],
                "follow_up_suggestions": []
            }
        ]

        questions = generator._parse_questions(questions_data, QuestionCategory.TECHNICAL)

        assert len(questions) == 2
        assert questions[0].id == "tech_1"
        assert questions[0].category == QuestionCategory.TECHNICAL
        assert questions[0].difficulty == "advanced"
        assert "Python" in questions[0].skills
        assert questions[0].rationale != ""
        assert len(questions[0].expected_answers) == 2

    def test_parse_behavioral_questions(self):
        """Test parsing behavioral questions from LLM response."""
        generator = InterviewQuestionGenerator.__new__(InterviewQuestionGenerator)

        questions_data = [
            {
                "id": "behav_1",
                "text": "Tell me about a time you led a team through a difficult project",
                "difficulty": "intermediate",
                "skills": ["Leadership", "Communication"],
                "rationale": "Assess leadership experience",
                "expected_answers": ["Clear situation description", "Action taken", "Results achieved"],
                "follow_up_suggestions": ["What would you do differently?"]
            }
        ]

        questions = generator._parse_questions(questions_data, QuestionCategory.BEHAVIORAL)

        assert len(questions) == 1
        assert questions[0].category == QuestionCategory.BEHAVIORAL
        assert "Leadership" in questions[0].skills

    def test_parse_question_with_missing_fields(self):
        """Test parsing questions with missing optional fields."""
        generator = InterviewQuestionGenerator.__new__(InterviewQuestionGenerator)

        questions_data = [
            {
                "id": "minimal_1",
                "text": "Basic question",
                "difficulty": "beginner",
                "skills": [],
                "rationale": "",
                "expected_answers": [],
                "follow_up_suggestions": []
            }
        ]

        questions = generator._parse_questions(questions_data, QuestionCategory.TECHNICAL)

        assert len(questions) == 1
        assert questions[0].id == "minimal_1"
        assert questions[0].difficulty == "beginner"
        assert questions[0].skills == []

    def test_parse_question_generates_id_if_missing(self):
        """Test that missing question ID is auto-generated."""
        generator = InterviewQuestionGenerator.__new__(InterviewQuestionGenerator)

        questions_data = [
            {
                "text": "Question without ID",
                "difficulty": "intermediate",
                "skills": ["Python"],
                "rationale": "",
                "expected_answers": [],
                "follow_up_suggestions": []
            }
        ]

        questions = generator._parse_questions(questions_data, QuestionCategory.TECHNICAL)

        assert len(questions) == 1
        assert questions[0].id == "technical_0"

    def test_parse_question_handles_invalid_data(self):
        """Test that invalid question data is skipped with warning."""
        generator = InterviewQuestionGenerator.__new__(InterviewQuestionGenerator)

        questions_data = [
            {
                "id": "valid_1",
                "text": "Valid question",
                "difficulty": "intermediate",
                "skills": [],
                "rationale": "",
                "expected_answers": [],
                "follow_up_suggestions": []
            },
            None,  # Invalid entry
            {
                "id": "valid_2",
                "text": "Another valid question",
                "difficulty": "beginner",
                "skills": [],
                "rationale": "",
                "expected_answers": [],
                "follow_up_suggestions": []
            }
        ]

        questions = generator._parse_questions(questions_data, QuestionCategory.TECHNICAL)

        # Should skip the None entry
        assert len(questions) == 2


class TestLLMProviderCalls:
    """Tests for LLM provider API calls."""

    @pytest.mark.asyncio
    @patch("analyzers.interview_question_generator.get_settings")
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

        generator = InterviewQuestionGenerator()

        mock_response = {
            "technical_questions": [
                {
                    "id": "tech_1",
                    "text": "Test question",
                    "difficulty": "intermediate",
                    "skills": ["Python"],
                    "rationale": "",
                    "expected_answers": [],
                    "follow_up_suggestions": []
                }
            ],
            "behavioral_questions": [],
            "situational_questions": [],
            "skill_verification_questions": [],
            "areas_to_probe": [],
            "skill_gaps_to_address": [],
            "interview_tips": []
        }

        with patch("analyzers.interview_question_generator.AsyncOpenAI") as mock_openai:
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
    @patch("analyzers.interview_question_generator.get_settings")
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

        generator = InterviewQuestionGenerator()

        mock_response_data = {"technical_questions": []}
        wrapped_json = "```json\n" + json.dumps(mock_response_data) + "\n```"

        with patch("analyzers.interview_question_generator.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client

            mock_completion = AsyncMock()
            mock_completion.choices = [MagicMock()]
            mock_completion.choices[0].message.content = wrapped_json
            mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

            result = await generator._call_zai("test prompt")

            assert result == mock_response_data

    @pytest.mark.asyncio
    @patch("analyzers.interview_question_generator.get_settings")
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

        generator = InterviewQuestionGenerator(provider=LLMProvider.OPENAI)

        mock_response = {"technical_questions": []}

        with patch("analyzers.interview_question_generator.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client

            mock_completion = AsyncMock()
            mock_completion.choices = [MagicMock()]
            mock_completion.choices[0].message.content = json.dumps(mock_response)
            mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

            result = await generator._call_openai("test prompt")

            assert result == mock_response

    @pytest.mark.asyncio
    @patch("analyzers.interview_question_generator.get_settings")
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

        generator = InterviewQuestionGenerator(provider=LLMProvider.ANTHROPIC)

        mock_response = {"technical_questions": []}

        with patch("analyzers.interview_question_generator.AsyncAnthropic") as mock_anthropic:
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
    @patch("analyzers.interview_question_generator.get_settings")
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

        generator = InterviewQuestionGenerator(provider=LLMProvider.GOOGLE)

        mock_response = {"technical_questions": []}

        with patch("analyzers.interview_question_generator.genai") as mock_genai:
            mock_model = AsyncMock()
            mock_response_obj = MagicMock()
            mock_response_obj.text = json.dumps(mock_response)
            mock_model.generate_content_async = AsyncMock(return_value=mock_response_obj)
            mock_genai.GenerativeModel.return_value = mock_model

            result = await generator._call_google("test prompt")

            assert result == mock_response

    @pytest.mark.asyncio
    @patch("analyzers.interview_question_generator.get_settings")
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

        generator = InterviewQuestionGenerator()
        # Manually set an invalid provider
        generator.provider = "invalid_provider"

        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            await generator._call_llm("test prompt")


class TestQuestionGeneration:
    """Tests for the main question generation functionality."""

    @pytest.fixture
    def mock_llm_response(self):
        """Create a mock LLM response with all question categories."""
        return {
            "technical_questions": [
                {
                    "id": "tech_1",
                    "text": "Explain Python decorators",
                    "difficulty": "intermediate",
                    "skills": ["Python"],
                    "rationale": "Test Python knowledge",
                    "expected_answers": ["Functions as first-class objects", "Wrapper functions"],
                    "follow_up_suggestions": ["Show me an example"]
                },
                {
                    "id": "tech_2",
                    "text": "How does Django ORM work?",
                    "difficulty": "advanced",
                    "skills": ["Django", "ORM"],
                    "rationale": "Assess framework understanding",
                    "expected_answers": ["Abstracts SQL", "Model mapping"],
                    "follow_up_suggestions": []
                }
            ],
            "behavioral_questions": [
                {
                    "id": "behav_1",
                    "text": "Describe a challenging project",
                    "difficulty": "intermediate",
                    "skills": ["Problem Solving"],
                    "rationale": "Assess problem-solving",
                    "expected_answers": ["Clear challenge", "Action taken", "Outcome"],
                    "follow_up_suggestions": []
                }
            ],
            "situational_questions": [
                {
                    "id": "sit_1",
                    "text": "How would you handle a tight deadline?",
                    "difficulty": "intermediate",
                    "skills": ["Time Management"],
                    "rationale": "Test prioritization",
                    "expected_answers": ["Communication", "Prioritization"],
                    "follow_up_suggestions": []
                }
            ],
            "skill_verification_questions": [
                {
                    "id": "ver_1",
                    "text": "You mentioned 5 years of Django experience",
                    "difficulty": "intermediate",
                    "skills": ["Django"],
                    "rationale": "Verify experience claim",
                    "expected_answers": ["Specific projects", "Depth of knowledge"],
                    "follow_up_suggestions": []
                }
            ],
            "areas_to_probe": [
                "Verify Django project scale and complexity",
                "Confirm PostgreSQL optimization experience"
            ],
            "skill_gaps_to_address": [
                "Candidate lacks Redis experience",
                "Missing Docker containerization skills"
            ],
            "interview_tips": [
                "Focus on practical Python usage",
                "Ask about team collaboration"
            ]
        }

    @pytest.mark.asyncio
    @patch("analyzers.interview_question_generator.get_settings")
    async def test_generate_questions_success(self, mock_get_settings, mock_llm_response):
        """Test successful question generation."""
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

        generator = InterviewQuestionGenerator()

        with patch.object(generator, '_call_llm', new=AsyncMock(return_value=mock_llm_response)):
            result = await generator.generate_questions(
                resume_text="Senior Python developer with 5 years experience",
                job_title="Senior Python Developer",
                job_description="Looking for senior Python developer with Django experience",
                required_skills=["Python", "Django", "PostgreSQL"],
                candidate_skills=["Python", "Django", "FastAPI"],
                skill_gaps=["PostgreSQL", "Redis"]
            )

            assert isinstance(result, InterviewPrepResult)
            assert len(result.technical_questions) == 2
            assert len(result.behavioral_questions) == 1
            assert len(result.situational_questions) == 1
            assert len(result.skill_verification_questions) == 1
            assert len(result.questions) == 5  # Total of all questions
            assert len(result.areas_to_probe) == 2
            assert len(result.skill_gaps_to_address) == 2
            assert len(result.interview_tips) == 2
            assert result.provider == "zai"
            assert result.model == "gpt-4"

    @pytest.mark.asyncio
    @patch("analyzers.interview_question_generator.get_settings")
    async def test_generate_questions_with_empty_response(self, mock_get_settings):
        """Test question generation with minimal LLM response."""
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

        generator = InterviewQuestionGenerator()

        empty_response = {
            "technical_questions": [],
            "behavioral_questions": [],
            "situational_questions": [],
            "skill_verification_questions": [],
            "areas_to_probe": [],
            "skill_gaps_to_address": [],
            "interview_tips": []
        }

        with patch.object(generator, '_call_llm', new=AsyncMock(return_value=empty_response)):
            result = await generator.generate_questions(
                resume_text="Resume text",
                job_title="Developer",
                job_description="Job description",
                required_skills=["Python"]
            )

            assert len(result.questions) == 0
            assert len(result.technical_questions) == 0

    @pytest.mark.asyncio
    @patch("analyzers.interview_question_generator.get_settings")
    async def test_generate_questions_handles_llm_error(self, mock_get_settings):
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

        generator = InterviewQuestionGenerator()

        with patch.object(generator, '_call_llm', new=AsyncMock(side_effect=Exception("API Error"))):
            result = await generator.generate_questions(
                resume_text="Resume text",
                job_title="Developer",
                job_description="Job description",
                required_skills=["Python"]
            )

            # Should return a minimal result instead of crashing
            assert isinstance(result, InterviewPrepResult)
            assert len(result.questions) == 0
            assert len(result.areas_to_probe) > 0
            assert "Question generation failed" in result.areas_to_probe[0]

    @pytest.mark.asyncio
    @patch("analyzers.interview_question_generator.get_settings")
    async def test_generate_questions_with_seniority_level(self, mock_get_settings, mock_llm_response):
        """Test question generation with seniority level specified."""
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

        generator = InterviewQuestionGenerator()

        with patch.object(generator, '_call_llm', new=AsyncMock(return_value=mock_llm_response)):
            result = await generator.generate_questions(
                resume_text="Senior developer resume",
                job_title="Lead Developer",
                job_description="Lead developer position",
                required_skills=["Python"],
                min_experience_months=96,  # 8 years
                seniority_level="lead"
            )

            assert isinstance(result, InterviewPrepResult)
            # Verify the prompt was created with seniority info
            generator._call_llm.assert_called_once()
            call_args = generator._call_llm.call_args[0][0]
            assert "lead" in call_args.lower()


class TestBatchQuestionGeneration:
    """Tests for batch question generation."""

    @pytest.mark.asyncio
    @patch("analyzers.interview_question_generator.get_settings")
    async def test_batch_generate_for_multiple_candidates(self, mock_get_settings):
        """Test generating questions for multiple candidates."""
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

        generator = InterviewQuestionGenerator()

        candidates = [
            {
                "id": "candidate-1",
                "resume_text": "Python developer with 3 years experience",
                "skills": ["Python", "Django"],
                "skill_gaps": ["PostgreSQL"]
            },
            {
                "id": "candidate-2",
                "resume_text": "Full-stack developer with 5 years experience",
                "skills": ["Python", "React", "Node.js"],
                "skill_gaps": ["Django"]
            }
        ]

        mock_response = {
            "technical_questions": [],
            "behavioral_questions": [],
            "situational_questions": [],
            "skill_verification_questions": [],
            "areas_to_probe": [],
            "skill_gaps_to_address": [],
            "interview_tips": []
        }

        with patch.object(generator, 'generate_questions', new=AsyncMock(return_value=InterviewPrepResult(
            questions=[],
            provider="zai",
            model="gpt-4",
            generated_at=datetime.utcnow().isoformat()
        ))):
            results = await generator.batch_generate_questions(
                candidates=candidates,
                job_title="Senior Developer",
                job_description="Job description",
                required_skills=["Python"]
            )

            assert len(results) == 2
            assert all(isinstance(r, InterviewPrepResult) for r in results)
            assert generator.generate_questions.call_count == 2

    @pytest.mark.asyncio
    @patch("analyzers.interview_question_generator.get_settings")
    async def test_batch_generate_handles_partial_failures(self, mock_get_settings):
        """Test that batch generation handles individual failures gracefully."""
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

        generator = InterviewQuestionGenerator()

        candidates = [
            {"id": "candidate-1", "resume_text": "Resume 1"},
            {"id": "candidate-2", "resume_text": "Resume 2"},
            {"id": "candidate-3", "resume_text": "Resume 3"}
        ]

        async def mock_generate_with_failure(*args, **kwargs):
            # Fail for second candidate
            if "Resume 2" in args:
                raise Exception("API Error for candidate 2")
            return InterviewPrepResult(
                questions=[],
                provider="zai",
                model="gpt-4",
                generated_at=datetime.utcnow().isoformat()
            )

        with patch.object(generator, 'generate_questions', new=AsyncMock(side_effect=mock_generate_with_failure)):
            results = await generator.batch_generate_questions(
                candidates=candidates,
                job_title="Developer",
                job_description="Job desc",
                required_skills=["Python"]
            )

            assert len(results) == 3
            # First and third should succeed
            assert isinstance(results[0], InterviewPrepResult)
            # Second should have error result
            assert isinstance(results[1], InterviewPrepResult)
            assert "Question generation failed" in results[1].areas_to_probe[0]
            # Third should succeed
            assert isinstance(results[2], InterviewPrepResult)


class TestSynchronousWrapper:
    """Tests for synchronous wrapper method."""

    @patch("analyzers.interview_question_generator.get_settings")
    def test_generate_questions_sync(self, mock_get_settings):
        """Test synchronous wrapper for question generation."""
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

        generator = InterviewQuestionGenerator()

        mock_result = InterviewPrepResult(
            questions=[],
            provider="zai",
            model="gpt-4",
            generated_at=datetime.utcnow().isoformat()
        )

        with patch.object(generator, 'generate_questions', new=AsyncMock(return_value=mock_result)):
            result = generator.generate_questions_sync(
                resume_text="Resume text",
                job_title="Developer",
                job_description="Job description",
                required_skills=["Python"]
            )

            assert isinstance(result, InterviewPrepResult)
            assert result.provider == "zai"


class TestHelperFunctions:
    """Tests for module-level helper functions."""

    @patch("analyzers.interview_question_generator.get_settings")
    def test_get_interview_question_generator_with_api_key(self, mock_get_settings):
        """Test getting generator when API key is configured."""
        mock_settings = Mock()
        mock_settings.zai_api_key = "test-key"
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        mock_settings.google_api_key = None
        mock_get_settings.return_value = mock_settings

        generator = get_interview_question_generator()

        assert generator is not None
        assert isinstance(generator, InterviewQuestionGenerator)

    @patch("analyzers.interview_question_generator.get_settings")
    def test_get_interview_question_generator_without_api_key(self, mock_get_settings):
        """Test getting generator when no API key is configured."""
        mock_settings = Mock()
        mock_settings.zai_api_key = None
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        mock_settings.google_api_key = None
        mock_get_settings.return_value = mock_settings

        generator = get_interview_question_generator()

        assert generator is None

    @patch("analyzers.interview_question_generator.get_settings")
    def test_get_interview_question_generator_singleton(self, mock_get_settings):
        """Test that generator is cached as singleton."""
        mock_settings = Mock()
        mock_settings.zai_api_key = "test-key"
        mock_settings.openai_api_key = None
        mock_settings.anthropic_api_key = None
        mock_settings.google_api_key = None
        mock_get_settings.return_value = mock_settings

        generator1 = get_interview_question_generator()
        generator2 = get_interview_question_generator()

        assert generator1 is generator2

    @pytest.mark.asyncio
    @patch("analyzers.interview_question_generator.get_settings")
    @patch("analyzers.interview_question_generator.get_interview_question_generator")
    async def test_generate_interview_questions_convenience_function(self, mock_get_generator, mock_get_settings):
        """Test the convenience function for generating questions."""
        mock_settings = Mock()
        mock_get_settings.return_value = mock_settings

        mock_generator = Mock()
        mock_result = InterviewPrepResult(
            questions=[],
            provider="zai",
            model="gpt-4",
            generated_at=datetime.utcnow().isoformat()
        )
        mock_generator.generate_questions = AsyncMock(return_value=mock_result)
        mock_get_generator.return_value = mock_generator

        result = await generate_interview_questions(
            resume_text="Resume text",
            job_title="Developer",
            job_description="Job description",
            required_skills=["Python"]
        )

        assert result is not None
        assert isinstance(result, InterviewPrepResult)
        mock_generator.generate_questions.assert_called_once()

    @pytest.mark.asyncio
    @patch("analyzers.interview_question_generator.get_settings")
    @patch("analyzers.interview_question_generator.get_interview_question_generator")
    async def test_generate_interview_questions_returns_none_when_unavailable(self, mock_get_generator, mock_get_settings):
        """Test convenience function returns None when generator unavailable."""
        mock_settings = Mock()
        mock_get_settings.return_value = mock_settings

        mock_get_generator.return_value = None

        result = await generate_interview_questions(
            resume_text="Resume text",
            job_title="Developer",
            job_description="Job description",
            required_skills=["Python"]
        )

        assert result is None


class TestQuestionAndResultSerialization:
    """Tests for data serialization."""

    def test_question_to_dict(self):
        """Test Question serialization to dictionary."""
        question = Question(
            id="test_1",
            text="Test question",
            category=QuestionCategory.TECHNICAL,
            difficulty="intermediate",
            skills=["Python", "Django"],
            rationale="Test rationale",
            expected_answers=["Answer 1", "Answer 2"],
            follow_up_suggestions=["Follow-up 1"]
        )

        result = question.to_dict()

        assert result["id"] == "test_1"
        assert result["text"] == "Test question"
        assert result["category"] == "technical"
        assert result["difficulty"] == "intermediate"
        assert "Python" in result["skills"]
        assert len(result["expected_answers"]) == 2

    def test_interview_prep_result_to_dict(self):
        """Test InterviewPrepResult serialization to dictionary."""
        question = Question(
            id="q1",
            text="Question 1",
            category=QuestionCategory.TECHNICAL,
            difficulty="beginner"
        )

        result = InterviewPrepResult(
            questions=[question],
            technical_questions=[question],
            behavioral_questions=[],
            situational_questions=[],
            skill_verification_questions=[],
            areas_to_probe=["Area 1"],
            skill_gaps_to_address=["Gap 1"],
            interview_tips=["Tip 1"],
            provider="zai",
            model="gpt-4",
            generated_at="2024-01-01T00:00:00"
        )

        result_dict = result.to_dict()

        assert len(result_dict["questions"]) == 1
        assert len(result_dict["technical_questions"]) == 1
        assert len(result_dict["behavioral_questions"]) == 0
        assert result_dict["provider"] == "zai"
        assert result_dict["model"] == "gpt-4"
        assert "Area 1" in result_dict["areas_to_probe"]


@pytest.mark.parametrize("category,expected_value", [
    (QuestionCategory.TECHNICAL, "technical"),
    (QuestionCategory.BEHAVIORAL, "behavioral"),
    (QuestionCategory.SITUATIONAL, "situational"),
    (QuestionCategory.SKILL_VERIFICATION, "skill_verification"),
])
def test_question_category_enum_values(category, expected_value):
    """Test QuestionCategory enum values."""
    assert category.value == expected_value


@pytest.mark.parametrize("provider,expected_value", [
    (LLMProvider.OPENAI, "openai"),
    (LLMProvider.ANTHROPIC, "anthropic"),
    (LLMProvider.GOOGLE, "google"),
    (LLMProvider.ZAI, "zai"),
])
def test_llm_provider_enum_values(provider, expected_value):
    """Test LLMProvider enum values."""
    assert provider.value == expected_value
