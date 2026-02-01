"""
Integration Tests for LLM Provider Integration

These tests verify that the InterviewQuestionGenerator correctly integrates
with all supported LLM providers (OpenAI, Anthropic, Google, Z.ai).

NOTE: These tests require REAL API keys to be configured in the environment.
They make actual API calls and will consume API credits.

To run these tests:
  1. Set up API keys in environment or .env file:
     - OPENAI_API_KEY for OpenAI tests
     - ANTHROPIC_API_KEY for Anthropic tests
     - GOOGLE_API_KEY for Google tests
     - ZAI_API_KEY for Z.ai tests

  2. Run with pytest:
     pytest tests/test_llm_provider_integration.py -v

  3. Run specific provider tests:
     pytest tests/test_llm_provider_integration.py::TestOpenAIIntegration -v
     pytest tests/test_llm_provider_integration.py::TestAnthropicIntegration -v
     pytest tests/test_llm_provider_integration.py::TestGoogleIntegration -v
     pytest tests/test_llm_provider_integration.py::TestZaiIntegration -v

To skip integration tests (when API keys are not available):
  pytest tests/test_llm_provider_integration.py -v -m "not integration"
"""

import pytest
import os
import asyncio
from typing import Dict, Any, List

from analyzers.interview_question_generator import (
    InterviewQuestionGenerator,
    LLMProvider,
    QuestionCategory,
)


# Sample resume and job data for testing
SAMPLE_RESUME = """
John Doe
Senior Python Developer

Experience:
- Senior Python Developer at Tech Corp (2020-Present)
  - Developed RESTful APIs using FastAPI and Django
  - Worked with PostgreSQL and Redis databases
  - Led a team of 3 developers

- Python Developer at Startup Inc (2018-2020)
  - Built web applications using Django and Flask
  - Integrated with third-party APIs
  - Implemented unit tests with pytest

Skills:
- Programming: Python, JavaScript, SQL
- Frameworks: Django, FastAPI, Flask, React
- Databases: PostgreSQL, MongoDB, Redis
- Tools: Docker, Git, AWS

Education:
- BS Computer Science, University of Technology (2018)
"""

SAMPLE_JOB_TITLE = "Senior Python Developer"

SAMPLE_JOB_DESCRIPTION = """
We are looking for a Senior Python Developer to join our team.

Requirements:
- 5+ years of Python development experience
- Strong experience with Django or FastAPI
- Experience with PostgreSQL database
- Knowledge of RESTful API design
- Experience with cloud platforms (AWS/GCP)
- Team leadership experience

Responsibilities:
- Design and implement backend services
- Mentor junior developers
- Collaborate with frontend team
- Write clean, maintainable code
"""

SAMPLE_REQUIRED_SKILLS = ["Python", "Django", "FastAPI", "PostgreSQL", "AWS", "REST APIs"]

SAMPLE_CANDIDATE_SKILLS = ["Python", "Django", "FastAPI", "PostgreSQL", "Redis", "Docker", "Git"]

SAMPLE_SKILL_GAPS = ["AWS", "Team Leadership"]


def has_openai_key() -> bool:
    """Check if OpenAI API key is configured."""
    return bool(os.getenv("OPENAI_API_KEY"))


def has_anthropic_key() -> bool:
    """Check if Anthropic API key is configured."""
    return bool(os.getenv("ANTHROPIC_API_KEY"))


def has_google_key() -> bool:
    """Check if Google API key is configured."""
    return bool(os.getenv("GOOGLE_API_KEY"))


def has_zai_key() -> bool:
    """Check if Z.ai API key is configured."""
    return bool(os.getenv("ZAI_API_KEY"))


def verify_question_structure(questions: List[Dict[str, Any]], category: str) -> None:
    """
    Verify that questions have the correct structure.

    Args:
        questions: List of question dictionaries
        category: Expected category name

    Raises:
        AssertionError: If questions don't have the required structure
    """
    assert isinstance(questions, list), f"{category} questions should be a list"
    assert len(questions) > 0, f"Should have at least one {category} question"

    for i, question in enumerate(questions):
        assert isinstance(question, dict), f"{category} question {i} should be a dict"
        assert "id" in question, f"{category} question {i} should have 'id'"
        assert "text" in question, f"{category} question {i} should have 'text'"
        assert "category" in question, f"{category} question {i} should have 'category'"
        assert "difficulty" in question, f"{category} question {i} should have 'difficulty'"
        assert "skills" in question, f"{category} question {i} should have 'skills'"
        assert "rationale" in question, f"{category} question {i} should have 'rationale'"

        # Verify field types
        assert isinstance(question["id"], str), f"{category} question {i} 'id' should be string"
        assert isinstance(question["text"], str), f"{category} question {i} 'text' should be string"
        assert isinstance(question["skills"], list), f"{category} question {i} 'skills' should be list"
        assert question["difficulty"] in ["beginner", "intermediate", "advanced"], \
            f"{category} question {i} has invalid difficulty: {question['difficulty']}"


def verify_result_structure(result: Any) -> None:
    """
    Verify the InterviewPrepResult has all required fields.

    Args:
        result: InterviewPrepResult object

    Raises:
        AssertionError: If result doesn't have the required structure
    """
    # Verify result object
    assert result is not None, "Result should not be None"
    assert hasattr(result, "questions"), "Result should have 'questions' attribute"
    assert hasattr(result, "technical_questions"), "Result should have 'technical_questions'"
    assert hasattr(result, "behavioral_questions"), "Result should have 'behavioral_questions'"
    assert hasattr(result, "situational_questions"), "Result should have 'situational_questions'"
    assert hasattr(result, "skill_verification_questions"), "Result should have 'skill_verification_questions'"
    assert hasattr(result, "areas_to_probe"), "Result should have 'areas_to_probe'"
    assert hasattr(result, "skill_gaps_to_address"), "Result should have 'skill_gaps_to_address'"
    assert hasattr(result, "interview_tips"), "Result should have 'interview_tips'"
    assert hasattr(result, "provider"), "Result should have 'provider'"
    assert hasattr(result, "model"), "Result should have 'model'"
    assert hasattr(result, "generated_at"), "Result should have 'generated_at'"

    # Verify we have questions
    assert len(result.questions) > 0, "Should have generated some questions"

    # Verify each question category
    if len(result.technical_questions) > 0:
        verify_question_structure(
            [q.to_dict() for q in result.technical_questions],
            "technical"
        )

    if len(result.behavioral_questions) > 0:
        verify_question_structure(
            [q.to_dict() for q in result.behavioral_questions],
            "behavioral"
        )

    if len(result.situational_questions) > 0:
        verify_question_structure(
            [q.to_dict() for q in result.situational_questions],
            "situational"
        )

    if len(result.skill_verification_questions) > 0:
        verify_question_structure(
            [q.to_dict() for q in result.skill_verification_questions],
            "skill_verification"
        )

    # Verify metadata
    assert isinstance(result.areas_to_probe, list), "areas_to_probe should be a list"
    assert isinstance(result.skill_gaps_to_address, list), "skill_gaps_to_address should be a list"
    assert isinstance(result.interview_tips, list), "interview_tips should be a list"
    assert isinstance(result.provider, str), "provider should be a string"
    assert isinstance(result.model, str), "model should be a string"
    assert isinstance(result.generated_at, str), "generated_at should be a string"


@pytest.mark.integration
class TestOpenAIIntegration:
    """Integration tests for OpenAI provider."""

    @pytest.mark.skipif(not has_openai_key(), reason="OpenAI API key not configured")
    @pytest.mark.asyncio
    async def test_openai_generate_questions(self):
        """Test question generation with OpenAI API."""
        generator = InterviewQuestionGenerator(
            provider=LLMProvider.OPENAI,
            model="gpt-4o-mini"  # Using cheaper model for testing
        )

        result = await generator.generate_questions(
            resume_text=SAMPLE_RESUME,
            job_title=SAMPLE_JOB_TITLE,
            job_description=SAMPLE_JOB_DESCRIPTION,
            required_skills=SAMPLE_REQUIRED_SKILLS,
            candidate_skills=SAMPLE_CANDIDATE_SKILLS,
            skill_gaps=SAMPLE_SKILL_GAPS,
            seniority_level="senior"
        )

        # Verify result structure
        verify_result_structure(result)

        # Verify provider metadata
        assert result.provider == "openai", f"Provider should be 'openai', got '{result.provider}'"
        assert "gpt" in result.model.lower(), f"Model should contain 'gpt', got '{result.model}'"

        # Verify we have questions from each category
        assert len(result.technical_questions) >= 3, "Should have at least 3 technical questions"
        assert len(result.behavioral_questions) >= 2, "Should have at least 2 behavioral questions"
        assert len(result.situational_questions) >= 2, "Should have at least 2 situational questions"
        assert len(result.skill_verification_questions) >= 3, "Should have at least 3 skill verification questions"

        # Verify questions are relevant
        for question in result.technical_questions[:3]:
            question_dict = question.to_dict()
            # Questions should mention relevant skills
            question_text = question_dict["text"].lower()
            assert any(
                skill.lower() in question_text or
                any(s.lower() in question_text for s in ["python", "django", "fastapi", "database", "api"])
                for skill in SAMPLE_REQUIRED_SKILLS
            ), f"Technical question should mention relevant skills: {question_dict['text']}"


@pytest.mark.integration
class TestAnthropicIntegration:
    """Integration tests for Anthropic provider."""

    @pytest.mark.skipif(not has_anthropic_key(), reason="Anthropic API key not configured")
    @pytest.mark.asyncio
    async def test_anthropic_generate_questions(self):
        """Test question generation with Anthropic API."""
        generator = InterviewQuestionGenerator(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-5-sonnet-20241022"  # Using Sonnet for testing
        )

        result = await generator.generate_questions(
            resume_text=SAMPLE_RESUME,
            job_title=SAMPLE_JOB_TITLE,
            job_description=SAMPLE_JOB_DESCRIPTION,
            required_skills=SAMPLE_REQUIRED_SKILLS,
            candidate_skills=SAMPLE_CANDIDATE_SKILLS,
            skill_gaps=SAMPLE_SKILL_GAPS,
            seniority_level="senior"
        )

        # Verify result structure
        verify_result_structure(result)

        # Verify provider metadata
        assert result.provider == "anthropic", f"Provider should be 'anthropic', got '{result.provider}'"
        assert "claude" in result.model.lower(), f"Model should contain 'claude', got '{result.model}'"

        # Verify we have questions from each category
        assert len(result.technical_questions) >= 3, "Should have at least 3 technical questions"
        assert len(result.behavioral_questions) >= 2, "Should have at least 2 behavioral questions"
        assert len(result.situational_questions) >= 2, "Should have at least 2 situational questions"
        assert len(result.skill_verification_questions) >= 3, "Should have at least 3 skill verification questions"

        # Verify areas to probe are generated
        assert len(result.areas_to_probe) > 0, "Should have areas to probe"
        assert isinstance(result.areas_to_probe[0], str), "Area to probe should be a string"


@pytest.mark.integration
class TestGoogleIntegration:
    """Integration tests for Google Gemini provider."""

    @pytest.mark.skipif(not has_google_key(), reason="Google API key not configured")
    @pytest.mark.asyncio
    async def test_google_generate_questions(self):
        """Test question generation with Google Gemini API."""
        generator = InterviewQuestionGenerator(
            provider=LLMProvider.GOOGLE,
            model="gemini-1.5-flash"  # Using Flash for faster/cheaper testing
        )

        result = await generator.generate_questions(
            resume_text=SAMPLE_RESUME,
            job_title=SAMPLE_JOB_TITLE,
            job_description=SAMPLE_JOB_DESCRIPTION,
            required_skills=SAMPLE_REQUIRED_SKILLS,
            candidate_skills=SAMPLE_CANDIDATE_SKILLS,
            skill_gaps=SAMPLE_SKILL_GAPS,
            seniority_level="senior"
        )

        # Verify result structure
        verify_result_structure(result)

        # Verify provider metadata
        assert result.provider == "google", f"Provider should be 'google', got '{result.provider}'"
        assert "gemini" in result.model.lower(), f"Model should contain 'gemini', got '{result.model}'"

        # Verify we have questions from each category
        assert len(result.technical_questions) >= 3, "Should have at least 3 technical questions"
        assert len(result.behavioral_questions) >= 2, "Should have at least 2 behavioral questions"
        assert len(result.situational_questions) >= 2, "Should have at least 2 situational questions"
        assert len(result.skill_verification_questions) >= 3, "Should have at least 3 skill verification questions"

        # Verify interview tips are provided
        assert len(result.interview_tips) > 0, "Should have interview tips"
        assert isinstance(result.interview_tips[0], str), "Interview tip should be a string"


@pytest.mark.integration
class TestZaiIntegration:
    """Integration tests for Z.ai provider."""

    @pytest.mark.skipif(not has_zai_key(), reason="Z.ai API key not configured")
    @pytest.mark.asyncio
    async def test_zai_generate_questions(self):
        """Test question generation with Z.ai API."""
        generator = InterviewQuestionGenerator(
            provider=LLMProvider.ZAI,
            model="gpt-4o-mini"  # Standard model
        )

        result = await generator.generate_questions(
            resume_text=SAMPLE_RESUME,
            job_title=SAMPLE_JOB_TITLE,
            job_description=SAMPLE_JOB_DESCRIPTION,
            required_skills=SAMPLE_REQUIRED_SKILLS,
            candidate_skills=SAMPLE_CANDIDATE_SKILLS,
            skill_gaps=SAMPLE_SKILL_GAPS,
            seniority_level="senior"
        )

        # Verify result structure
        verify_result_structure(result)

        # Verify provider metadata
        assert result.provider == "zai", f"Provider should be 'zai', got '{result.provider}'"

        # Verify we have questions from each category
        assert len(result.technical_questions) >= 3, "Should have at least 3 technical questions"
        assert len(result.behavioral_questions) >= 2, "Should have at least 2 behavioral questions"
        assert len(result.situational_questions) >= 2, "Should have at least 2 situational questions"
        assert len(result.skill_verification_questions) >= 3, "Should have at least 3 skill verification questions"

        # Verify skill gaps are addressed
        if len(result.skill_gaps_to_address) > 0:
            assert isinstance(result.skill_gaps_to_address[0], str), "Skill gap to address should be a string"


@pytest.mark.integration
class TestProviderComparison:
    """Compare results across different providers."""

    @pytest.mark.skipif(
        not (has_openai_key() or has_anthropic_key() or has_google_key() or has_zai_key()),
        reason="At least one API key must be configured"
    )
    @pytest.mark.asyncio
    async def test_all_providers_generate_valid_results(self):
        """Test that all configured providers generate valid results."""
        providers_to_test = []

        if has_openai_key():
            providers_to_test.append((LLMProvider.OPENAI, "gpt-4o-mini"))
        if has_anthropic_key():
            providers_to_test.append((LLMProvider.ANTHROPIC, "claude-3-5-sonnet-20241022"))
        if has_google_key():
            providers_to_test.append((LLMProvider.GOOGLE, "gemini-1.5-flash"))
        if has_zai_key():
            providers_to_test.append((LLMProvider.ZAI, "gpt-4o-mini"))

        results = []

        for provider, model in providers_to_test:
            generator = InterviewQuestionGenerator(
                provider=provider,
                model=model
            )

            result = await generator.generate_questions(
                resume_text=SAMPLE_RESUME,
                job_title=SAMPLE_JOB_TITLE,
                job_description=SAMPLE_JOB_DESCRIPTION,
                required_skills=SAMPLE_REQUIRED_SKILLS,
                candidate_skills=SAMPLE_CANDIDATE_SKILLS,
                skill_gaps=SAMPLE_SKILL_GAPS,
                seniority_level="senior"
            )

            # Verify structure
            verify_result_structure(result)

            # Store summary
            results.append({
                "provider": provider.value,
                "model": model,
                "total_questions": len(result.questions),
                "technical": len(result.technical_questions),
                "behavioral": len(result.behavioral_questions),
                "situational": len(result.situational_questions),
                "skill_verification": len(result.skill_verification_questions),
                "areas_to_probe": len(result.areas_to_probe),
                "interview_tips": len(result.interview_tips),
            })

        # All providers should have generated questions
        for summary in results:
            assert summary["total_questions"] > 0, \
                f"{summary['provider']} should generate questions"

        # Print summary for manual review
        print("\n" + "="*80)
        print("PROVIDER COMPARISON SUMMARY")
        print("="*80)
        for summary in results:
            print(f"\n{summary['provider'].upper()} ({summary['model']}):")
            print(f"  Total Questions: {summary['total_questions']}")
            print(f"  Technical: {summary['technical']}")
            print(f"  Behavioral: {summary['behavioral']}")
            print(f"  Situational: {summary['situational']}")
            print(f"  Skill Verification: {summary['skill_verification']}")
            print(f"  Areas to Probe: {summary['areas_to_probe']}")
            print(f"  Interview Tips: {summary['interview_tips']}")
        print("="*80 + "\n")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
