"""
Interview Question Generator Module

This module provides LLM-based interview question generation that creates
customized interview questions based on a candidate's resume and job requirements.

Key features:
- Technical questions tailored to candidate's skills
- Behavioral questions based on experience
- Situational questions for role-specific scenarios
- Skill verification questions to validate claimed expertise
- Experience claim probing suggestions
- Skill gap-based question recommendations

The module uses OpenAI, Anthropic, or Google APIs to generate comprehensive
interview preparation materials.
"""
import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from config import get_settings

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    ZAI = "zai"


class QuestionCategory(str, Enum):
    """Categories of interview questions."""
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    SITUATIONAL = "situational"
    SKILL_VERIFICATION = "skill_verification"


@dataclass
class Question:
    """
    A single interview question with metadata.

    Attributes:
        id: Unique identifier for the question
        text: The question text
        category: Category of the question
        difficulty: Difficulty level (beginner, intermediate, advanced)
        skills: List of relevant skills this question probes
        rationale: Why this question is being asked
        expected_answers: Key points to look for in the answer
        follow_up_suggestions: Suggested follow-up questions
    """
    id: str
    text: str
    category: QuestionCategory
    difficulty: str = "intermediate"
    skills: List[str] = field(default_factory=list)
    rationale: str = ""
    expected_answers: List[str] = field(default_factory=list)
    follow_up_suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert question to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "text": self.text,
            "category": self.category.value,
            "difficulty": self.difficulty,
            "skills": self.skills,
            "rationale": self.rationale,
            "expected_answers": self.expected_answers,
            "follow_up_suggestions": self.follow_up_suggestions,
        }


@dataclass
class InterviewPrepResult:
    """
    Result of interview question generation.

    Attributes:
        questions: List of generated questions
        technical_questions: Technical questions only
        behavioral_questions: Behavioral questions only
        situational_questions: Situational questions only
        skill_verification_questions: Skill verification questions only
        areas_to_probe: List of experience claims and skills to verify
        skill_gaps_to_address: Skills the candidate should demonstrate
        interview_tips: Tips for the interviewer
        provider: LLM provider used
        model: Model name used
        generated_at: Timestamp of generation
    """
    questions: List[Question]
    technical_questions: List[Question] = field(default_factory=list)
    behavioral_questions: List[Question] = field(default_factory=list)
    situational_questions: List[Question] = field(default_factory=list)
    skill_verification_questions: List[Question] = field(default_factory=list)
    areas_to_probe: List[str] = field(default_factory=list)
    skill_gaps_to_address: List[str] = field(default_factory=list)
    interview_tips: List[str] = field(default_factory=list)
    provider: str = ""
    model: str = ""
    generated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
            "questions": [q.to_dict() for q in self.questions],
            "technical_questions": [q.to_dict() for q in self.technical_questions],
            "behavioral_questions": [q.to_dict() for q in self.behavioral_questions],
            "situational_questions": [q.to_dict() for q in self.situational_questions],
            "skill_verification_questions": [q.to_dict() for q in self.skill_verification_questions],
            "areas_to_probe": self.areas_to_probe,
            "skill_gaps_to_address": self.skill_gaps_to_address,
            "interview_tips": self.interview_tips,
            "provider": self.provider,
            "model": self.model,
            "generated_at": self.generated_at,
        }


class InterviewQuestionGenerator:
    """
    Interview Question Generator using LLM for comprehensive question creation.

    This generator creates tailored interview questions based on a candidate's
    resume and the job requirements. It generates questions across multiple
    categories and highlights areas to probe during the interview.

    Example:
        >>> generator = InterviewQuestionGenerator()
        >>> result = await generator.generate_questions(
        ...     resume_text="Senior Python developer with 5 years experience...",
        ...     job_title="Senior Python Developer",
        ...     job_description="Looking for senior Python developer...",
        ...     required_skills=["Python", "Django", "PostgreSQL"],
        ...     candidate_skills=["Python", "Django", "FastAPI"],
        ...     skill_gaps=["PostgreSQL", "Redis"]
        ... )
        >>> print(len(result.technical_questions))
        5
        >>> print(result.areas_to_probe[0])
        "Verify 5 years of Python experience claims"
    """

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize the Interview Question Generator.

        Args:
            provider: LLM provider to use (default from config)
            model: Model name to use (default from config)
        """
        settings = get_settings()

        self.provider = provider or LLMProvider(settings.llm_provider)
        self.model = model or settings.llm_model

        # LLM parameters
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens

        # API keys
        self.zai_api_key = settings.zai_api_key
        self.zai_base_url = settings.zai_base_url
        self.openai_api_key = settings.openai_api_key
        self.anthropic_api_key = settings.anthropic_api_key
        self.google_api_key = settings.google_api_key

        logger.info(
            f"InterviewQuestionGenerator initialized: provider={self.provider}, "
            f"model={self.model}"
        )

    def _get_system_prompt(self) -> str:
        """Get the system prompt for question generation."""
        return """You are an expert technical interviewer and hiring manager. Your task is to generate comprehensive interview questions based on a candidate's resume and job requirements.

Generate questions in these categories:

1. **Technical Questions**: Test the candidate's technical knowledge and skills relevant to the job.

2. **Behavioral Questions**: Explore past behavior and soft skills (teamwork, leadership, problem-solving).

3. **Situational Questions**: Present hypothetical scenarios relevant to the role.

4. **Skill Verification Questions**: Deep-dive questions to verify claimed experience and skills.

For each question, provide:
- Clear, specific question text
- Difficulty level (beginner/intermediate/advanced)
- Related skills being tested
- Rationale for why this question matters
- Key points to look for in the answer
- Follow-up suggestions

Return your analysis in the following JSON format:
```json
{
    "technical_questions": [
        {
            "id": "unique_id_1",
            "text": "Question text here",
            "difficulty": "intermediate",
            "skills": ["Python", "Django"],
            "rationale": "Why this question is important",
            "expected_answers": ["Key point 1", "Key point 2"],
            "follow_up_suggestions": ["Follow-up 1", "Follow-up 2"]
        }
    ],
    "behavioral_questions": [
        {
            "id": "unique_id_2",
            "text": "Tell me about a time...",
            "difficulty": "intermediate",
            "skills": ["Leadership", "Communication"],
            "rationale": "Assess leadership capabilities",
            "expected_answers": ["Key point 1", "Key point 2"],
            "follow_up_suggestions": ["Follow-up 1"]
        }
    ],
    "situational_questions": [
        {
            "id": "unique_id_3",
            "text": "How would you handle...",
            "difficulty": "advanced",
            "skills": ["Problem Solving"],
            "rationale": "Test problem-solving approach",
            "expected_answers": ["Key point 1"],
            "follow_up_suggestions": []
        }
    ],
    "skill_verification_questions": [
        {
            "id": "unique_id_4",
            "text": "You mentioned X years of experience with...",
            "difficulty": "intermediate",
            "skills": ["Specific Skill"],
            "rationale": "Verify claimed experience",
            "expected_answers": ["Detailed explanation"],
            "follow_up_suggestions": ["Deeper technical question"]
        }
    ],
    "areas_to_probe": [
        "Specific experience claim to verify",
        "Skill that needs deeper investigation"
    ],
    "skill_gaps_to_address": [
        "Skill from requirements that candidate lacks",
        "Area of concern based on resume"
    ],
    "interview_tips": [
        "Tip for interviewer",
        "Another suggestion"
    ]
}
```

Important guidelines:
- Generate 4-6 technical questions based on required skills
- Generate 3-4 behavioral questions for soft skills assessment
- Generate 2-3 situational questions relevant to the role
- Generate 3-5 skill verification questions for claimed experience
- Focus on skills and experience actually mentioned in the resume
- Highlight areas that need verification based on experience claims
- Address skill gaps by asking how the candidate would handle learning required skills
- Questions should be specific and role-relevant
- Include both fundamental and advanced questions
- Consider the candidate's seniority level when determining difficulty
"""

    def _create_question_prompt(
        self,
        resume_text: str,
        job_title: str,
        job_description: str,
        required_skills: List[str],
        candidate_skills: Optional[List[str]] = None,
        skill_gaps: Optional[List[str]] = None,
        min_experience: Optional[int] = None,
        seniority_level: Optional[str] = None,
    ) -> str:
        """Create the question generation prompt for the LLM."""
        prompt_parts = [
            f"Please generate comprehensive interview questions for a candidate with the following profile:\n",
            f"=== JOB POSTING ===\n",
            f"Title: {job_title}\n",
            f"Description: {job_description}\n",
            f"Required Skills: {', '.join(required_skills)}\n",
        ]

        if min_experience:
            prompt_parts.append(f"Minimum Experience Required: {min_experience // 12} years\n")
        if seniority_level:
            prompt_parts.append(f"Seniority Level: {seniority_level}\n")

        prompt_parts.append(f"\n=== CANDIDATE RESUME ===\n")
        prompt_parts.append(f"{resume_text}\n")

        if candidate_skills:
            prompt_parts.append(f"\nExtracted Skills: {', '.join(candidate_skills)}\n")

        if skill_gaps:
            prompt_parts.append(f"\nSkill Gaps to Address: {', '.join(skill_gaps)}\n")

        prompt_parts.extend([
            f"\n=== END ===\n",
            f"Please generate interview questions and return a JSON response with all question categories.",
        ])

        return "".join(prompt_parts)

    async def _call_openai(self, prompt: str) -> Dict[str, Any]:
        """Call OpenAI API for question generation."""
        try:
            from openai import AsyncOpenAI

            if not self.openai_api_key:
                raise ValueError("OpenAI API key not configured")

            client = AsyncOpenAI(api_key=self.openai_api_key)

            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
            )

            result_text = response.choices[0].message.content
            return json.loads(result_text)

        except ImportError:
            logger.error("OpenAI package not installed. Install with: pip install openai")
            raise
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise

    async def _call_anthropic(self, prompt: str) -> Dict[str, Any]:
        """Call Anthropic API for question generation."""
        try:
            from anthropic import AsyncAnthropic

            if not self.anthropic_api_key:
                raise ValueError("Anthropic API key not configured")

            client = AsyncAnthropic(api_key=self.anthropic_api_key)

            response = await client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=self._get_system_prompt(),
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )

            result_text = response.content[0].text
            # Extract JSON from response (Anthropic may wrap it)
            import re
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                result_text = json_match.group(0)

            return json.loads(result_text)

        except ImportError:
            logger.error("Anthropic package not installed. Install with: pip install anthropic")
            raise
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise

    async def _call_google(self, prompt: str) -> Dict[str, Any]:
        """Call Google Gemini API for question generation."""
        try:
            import google.generativeai as genai

            if not self.google_api_key:
                raise ValueError("Google API key not configured")

            genai.configure(api_key=self.google_api_key)
            genai_model = genai.GenerativeModel(
                self.model,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                    response_mime_type="application/json",
                ),
                system_instruction=self._get_system_prompt(),
            )

            response = await genai_model.generate_content_async(prompt)
            result_text = response.text

            return json.loads(result_text)

        except ImportError:
            logger.error("Google Generative AI package not installed. Install with: pip install google-generativeai")
            raise
        except Exception as e:
            logger.error(f"Google API call failed: {e}")
            raise

    async def _call_zai(self, prompt: str) -> Dict[str, Any]:
        """Call Z.ai API for question generation (OpenAI-compatible)."""
        try:
            from openai import AsyncOpenAI

            if not self.zai_api_key:
                raise ValueError("Z.ai API key not configured")

            client = AsyncOpenAI(
                api_key=self.zai_api_key,
                base_url=self.zai_base_url,
            )

            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            content = response.choices[0].message.content
            logger.info(f"Z.ai API call successful, response length: {len(content)}")

            # Try to extract JSON from response
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()

            return json.loads(content)

        except ImportError:
            logger.error("OpenAI package not installed. Install with: pip install openai")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Z.ai JSON response: {e}")
            logger.error(f"Response content: {content[:500]}...")
            raise ValueError(f"Invalid JSON response from Z.ai API: {e}")
        except Exception as e:
            logger.error(f"Z.ai API call failed: {e}")
            raise

    async def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """Call the appropriate LLM provider."""
        if self.provider == LLMProvider.ZAI:
            return await self._call_zai(prompt)
        elif self.provider == LLMProvider.OPENAI:
            return await self._call_openai(prompt)
        elif self.provider == LLMProvider.ANTHROPIC:
            return await self._call_anthropic(prompt)
        elif self.provider == LLMProvider.GOOGLE:
            return await self._call_google(prompt)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _parse_questions(
        self,
        questions_data: List[Dict[str, Any]],
        category: QuestionCategory,
    ) -> List[Question]:
        """Parse question data from LLM response into Question objects."""
        questions = []
        for q_data in questions_data:
            try:
                question = Question(
                    id=q_data.get("id", f"{category.value}_{len(questions)}"),
                    text=q_data.get("text", ""),
                    category=category,
                    difficulty=q_data.get("difficulty", "intermediate"),
                    skills=q_data.get("skills", []),
                    rationale=q_data.get("rationale", ""),
                    expected_answers=q_data.get("expected_answers", []),
                    follow_up_suggestions=q_data.get("follow_up_suggestions", []),
                )
                questions.append(question)
            except Exception as e:
                logger.warning(f"Failed to parse question: {e}")
                continue
        return questions

    async def generate_questions(
        self,
        resume_text: str,
        job_title: str,
        job_description: str,
        required_skills: List[str],
        candidate_skills: Optional[List[str]] = None,
        skill_gaps: Optional[List[str]] = None,
        min_experience_months: Optional[int] = None,
        seniority_level: Optional[str] = None,
        candidate_experience: Optional[Dict[str, Any]] = None,
        candidate_education: Optional[List[Dict[str, Any]]] = None,
    ) -> InterviewPrepResult:
        """
        Generate interview questions based on resume and job requirements.

        Args:
            resume_text: Full resume text
            job_title: Job posting title
            job_description: Job posting description
            required_skills: List of required skills from job posting
            candidate_skills: Pre-extracted skills from resume
            skill_gaps: Skills required but not found in resume
            min_experience_months: Minimum required experience in months
            seniority_level: Expected seniority level (junior, mid, senior, lead)
            candidate_experience: Pre-extracted experience data
            candidate_education: Pre-extracted education data

        Returns:
            InterviewPrepResult with comprehensive interview questions
        """
        # Create question generation prompt
        prompt = self._create_question_prompt(
            resume_text=resume_text,
            job_title=job_title,
            job_description=job_description,
            required_skills=required_skills,
            candidate_skills=candidate_skills,
            skill_gaps=skill_gaps,
            min_experience=min_experience_months,
            seniority_level=seniority_level,
        )

        # Call LLM for question generation
        try:
            llm_result = await self._call_llm(prompt)

            # Parse questions from each category
            technical_data = llm_result.get("technical_questions", [])
            behavioral_data = llm_result.get("behavioral_questions", [])
            situational_data = llm_result.get("situational_questions", [])
            skill_verification_data = llm_result.get("skill_verification_questions", [])

            technical_questions = self._parse_questions(
                technical_data, QuestionCategory.TECHNICAL
            )
            behavioral_questions = self._parse_questions(
                behavioral_data, QuestionCategory.BEHAVIORAL
            )
            situational_questions = self._parse_questions(
                situational_data, QuestionCategory.SITUATIONAL
            )
            skill_verification_questions = self._parse_questions(
                skill_verification_data, QuestionCategory.SKILL_VERIFICATION
            )

            # Combine all questions
            all_questions = (
                technical_questions +
                behavioral_questions +
                situational_questions +
                skill_verification_questions
            )

            # Extract additional information
            areas_to_probe = llm_result.get("areas_to_probe", [])
            skill_gaps_to_address = llm_result.get("skill_gaps_to_address", [])
            interview_tips = llm_result.get("interview_tips", [])

            # Get current timestamp
            from datetime import datetime
            generated_at = datetime.utcnow().isoformat()

            result = InterviewPrepResult(
                questions=all_questions,
                technical_questions=technical_questions,
                behavioral_questions=behavioral_questions,
                situational_questions=situational_questions,
                skill_verification_questions=skill_verification_questions,
                areas_to_probe=areas_to_probe,
                skill_gaps_to_address=skill_gaps_to_address,
                interview_tips=interview_tips,
                provider=self.provider.value,
                model=self.model,
                generated_at=generated_at,
            )

            logger.info(
                f"Interview question generation complete: "
                f"{len(all_questions)} total questions "
                f"({len(technical_questions)} technical, "
                f"{len(behavioral_questions)} behavioral, "
                f"{len(situational_questions)} situational, "
                f"{len(skill_verification_questions)} skill verification)"
            )

            return result

        except Exception as e:
            logger.error(f"Interview question generation failed: {e}")
            # Return a minimal result
            from datetime import datetime
            return InterviewPrepResult(
                questions=[],
                areas_to_probe=[f"Question generation failed: {str(e)}"],
                interview_tips=["Could not generate questions due to an error"],
                provider=self.provider.value,
                model=self.model,
                generated_at=datetime.utcnow().isoformat(),
            )

    def generate_questions_sync(
        self,
        resume_text: str,
        job_title: str,
        job_description: str,
        required_skills: List[str],
        candidate_skills: Optional[List[str]] = None,
        skill_gaps: Optional[List[str]] = None,
    ) -> InterviewPrepResult:
        """
        Synchronous wrapper for question generation.

        Use this when calling from non-async contexts.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            self.generate_questions(
                resume_text=resume_text,
                job_title=job_title,
                job_description=job_description,
                required_skills=required_skills,
                candidate_skills=candidate_skills,
                skill_gaps=skill_gaps,
            )
        )

    async def batch_generate_questions(
        self,
        candidates: List[Dict[str, Any]],
        job_title: str,
        job_description: str,
        required_skills: List[str],
    ) -> List[InterviewPrepResult]:
        """
        Generate interview questions for multiple candidates.

        Args:
            candidates: List of candidates with 'resume_text', 'id', and optional metadata
            job_title: Job posting title
            job_description: Job posting description
            required_skills: List of required skills

        Returns:
            List of InterviewPrepResult in the same order as input candidates
        """
        tasks = []
        for candidate in candidates:
            task = self.generate_questions(
                resume_text=candidate.get("resume_text", ""),
                job_title=job_title,
                job_description=job_description,
                required_skills=required_skills,
                candidate_skills=candidate.get("skills"),
                skill_gaps=candidate.get("skill_gaps"),
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Candidate {candidates[i].get('id', i)} question generation failed: {result}")
                from datetime import datetime
                processed_results.append(
                    InterviewPrepResult(
                        questions=[],
                        areas_to_probe=[f"Question generation failed: {str(result)}"],
                        interview_tips=["Could not generate questions"],
                        generated_at=datetime.utcnow().isoformat(),
                    )
                )
            else:
                processed_results.append(result)

        return processed_results


# Singleton instance
_default_generator: Optional[InterviewQuestionGenerator] = None


def get_interview_question_generator() -> Optional[InterviewQuestionGenerator]:
    """
    Get or create the default interview question generator instance.

    Returns None if LLM API is not configured.
    """
    global _default_generator
    settings = get_settings()

    # Check if any LLM API key is configured
    has_api_key = bool(
        settings.zai_api_key or
        settings.openai_api_key or
        settings.anthropic_api_key or
        settings.google_api_key
    )

    if not has_api_key:
        logger.warning("No LLM API key configured, interview question generator unavailable")
        return None

    if _default_generator is None:
        _default_generator = InterviewQuestionGenerator()

    return _default_generator


async def generate_interview_questions(
    resume_text: str,
    job_title: str,
    job_description: str,
    required_skills: List[str],
    candidate_skills: Optional[List[str]] = None,
    skill_gaps: Optional[List[str]] = None,
) -> Optional[InterviewPrepResult]:
    """
    Convenience function to generate interview questions.

    Returns None if LLM is not configured.

    Args:
        resume_text: Full resume text
        job_title: Job posting title
        job_description: Job posting description
        required_skills: List of required skills
        candidate_skills: Pre-extracted skills from resume
        skill_gaps: Skills required but not found in resume

    Returns:
        InterviewPrepResult with generated questions, or None if unavailable
    """
    generator = get_interview_question_generator()
    if generator:
        return await generator.generate_questions(
            resume_text=resume_text,
            job_title=job_title,
            job_description=job_description,
            required_skills=required_skills,
            candidate_skills=candidate_skills,
            skill_gaps=skill_gaps,
        )

    return None
