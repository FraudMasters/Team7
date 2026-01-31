"""
ATS (Applicant Tracking System) Simulation Module

This module provides LLM-based ATS simulation that evaluates how well a resume
matches a job posting from the perspective of an ATS system.

Key features:
- LLM-based keyword matching score
- Experience relevance evaluation
- Education level matching
- Overall fit assessment
- Visual format checking
- Disqualification detection (red flags)

The module uses OpenAI, Anthropic, or Google APIs to perform comprehensive
ATS analysis similar to how commercial ATS systems evaluate resumes.
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


@dataclass
class ATSScoreResult:
    """
    Result of ATS scoring analysis.

    Attributes:
        passed: Whether the resume passes the ATS threshold
        overall_score: Combined ATS score (0-1)
        keyword_score: Keyword matching score (0-1)
        experience_score: Experience relevance score (0-1)
        education_score: Education match score (0-1)
        fit_score: Overall fit assessment (0-1)
        looks_professional: Whether the resume looks professionally formatted
        disqualified: Whether the resume has disqualifying issues
        visual_issues: List of visual/formatting issues found
        ats_issues: List of ATS-specific issues found
        missing_keywords: List of important missing keywords
        suggestions: List of improvement suggestions
        feedback: Detailed feedback from LLM analysis
        provider: LLM provider used
        model: Model name used
    """
    passed: bool
    overall_score: float
    keyword_score: float = 0.0
    experience_score: float = 0.0
    education_score: float = 0.0
    fit_score: float = 0.0
    looks_professional: bool = True
    disqualified: bool = False
    visual_issues: List[str] = field(default_factory=list)
    ats_issues: List[str] = field(default_factory=list)
    missing_keywords: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    feedback: str = ""
    provider: str = ""
    model: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
            "passed": self.passed,
            "overall_score": round(self.overall_score, 4),
            "keyword_score": round(self.keyword_score, 4),
            "experience_score": round(self.experience_score, 4),
            "education_score": round(self.education_score, 4),
            "fit_score": round(self.fit_score, 4),
            "looks_professional": self.looks_professional,
            "disqualified": self.disqualified,
            "visual_issues": self.visual_issues,
            "ats_issues": self.ats_issues,
            "missing_keywords": self.missing_keywords,
            "suggestions": self.suggestions,
            "feedback": self.feedback,
            "provider": self.provider,
            "model": self.model,
        }


class ATSSimulator:
    """
    ATS Simulation using LLM for comprehensive resume evaluation.

    This simulator evaluates resumes against job postings using LLM-based
    analysis to mimic commercial ATS systems. It provides detailed scoring
    across multiple dimensions.

    Example:
        >>> simulator = ATSSimulator()
        >>> result = await simulator.evaluate_ats(
        ...     resume_text="Experienced Python developer...",
        ...     job_title="Senior Python Developer",
        ...     job_description="Looking for senior Python developer...",
        ...     required_skills=["Python", "Django", "PostgreSQL"]
        ... )
        >>> print(result.passed)
        True
        >>> print(result.overall_score)
        0.75
    """

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
        threshold: Optional[float] = None,
    ):
        """
        Initialize the ATS Simulator.

        Args:
            provider: LLM provider to use (default from config)
            model: Model name to use (default from config)
            threshold: ATS pass threshold (default from config)
        """
        settings = get_settings()

        self.provider = provider or LLMProvider(settings.llm_provider)
        self.model = model or settings.llm_model
        self.threshold = threshold if threshold is not None else settings.ats_threshold

        # Weights for score calculation
        self.keyword_weight = settings.ats_keyword_weight
        self.experience_weight = settings.ats_experience_weight
        self.education_weight = settings.ats_education_weight
        self.fit_weight = settings.ats_fit_weight

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
            f"ATSSimulator initialized: provider={self.provider}, "
            f"model={self.model}, threshold={self.threshold}"
        )

    def _get_system_prompt(self) -> str:
        """Get the system prompt for ATS evaluation."""
        return """You are an expert ATS (Applicant Tracking System) evaluator. Your task is to analyze resumes against job postings and provide detailed scoring.

Evaluate the resume on these dimensions:

1. **Keyword Matching (0-1)**: How well the resume contains required skills and keywords from the job posting.

2. **Experience Relevance (0-1)**: How relevant and sufficient the candidate's experience is for the role.

3. **Education Match (0-1)**: How well the education level matches the job requirements.

4. **Overall Fit (0-1)**: Your assessment of how well the candidate fits the role overall.

5. **Visual/Format Check**: Does the resume appear professionally formatted?

6. **Disqualification Flags**: Are there any red flags (gaps in employment, inconsistent info, concerning issues)?

Return your analysis in the following JSON format:
```json
{
    "keyword_score": <float 0-1>,
    "experience_score": <float 0-1>,
    "education_score": <float 0-1>,
    "fit_score": <float 0-1>,
    "looks_professional": <boolean>,
    "disqualified": <boolean>,
    "disqualification_reason": "<string or null>",
    "visual_issues": ["<list of visual/formatting issues>"],
    "ats_issues": ["<list of ATS-specific concerns>"],
    "missing_keywords": ["<list of important missing keywords>"],
    "suggestions": ["<list of actionable improvement suggestions>"],
    "feedback": "<detailed feedback summary>"
}
```

Important scoring guidelines:
- Be fair but realistic - ATS systems are strict about keywords
- Consider related technologies as partial matches
- Experience should be recent and relevant
- Education level should meet or exceed requirements
- Mark as disqualified only for serious issues (employment gaps >2 years, inconsistent dates, false claims)
- Visual issues include: poor formatting, missing sections, unclear structure
"""

    def _create_evaluation_prompt(
        self,
        resume_text: str,
        job_title: str,
        job_description: str,
        required_skills: List[str],
        min_experience: Optional[int] = None,
        education_level: Optional[str] = None,
    ) -> str:
        """Create the evaluation prompt for the LLM."""
        prompt_parts = [
            f"Please evaluate the following resume for this job posting:\n",
            f"=== JOB POSTING ===\n",
            f"Title: {job_title}\n",
            f"Description: {job_description}\n",
            f"Required Skills: {', '.join(required_skills)}\n",
        ]

        if min_experience:
            prompt_parts.append(f"Minimum Experience Required: {min_experience // 12} years\n")
        if education_level:
            prompt_parts.append(f"Required Education: {education_level}\n")

        prompt_parts.extend([
            f"\n=== RESUME ===\n",
            f"{resume_text}\n",
            f"\n=== END ===\n",
            f"Please analyze and return a JSON response with the evaluation scores.",
        ])

        return "".join(prompt_parts)

    async def _call_openai(self, prompt: str) -> Dict[str, Any]:
        """Call OpenAI API for ATS evaluation."""
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
        """Call Anthropic API for ATS evaluation."""
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
        """Call Google Gemini API for ATS evaluation."""
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
        """Call Z.ai API for ATS evaluation (OpenAI-compatible)."""
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

    def _compute_overall_score(self, llm_result: Dict[str, Any]) -> float:
        """Compute weighted overall ATS score."""
        keyword_score = llm_result.get("keyword_score", 0.0)
        experience_score = llm_result.get("experience_score", 0.0)
        education_score = llm_result.get("education_score", 0.0)
        fit_score = llm_result.get("fit_score", 0.0)

        overall = (
            self.keyword_weight * keyword_score +
            self.experience_weight * experience_score +
            self.education_weight * education_score +
            self.fit_weight * fit_score
        )

        return min(overall, 1.0)

    async def evaluate_ats(
        self,
        resume_text: str,
        job_title: str,
        job_description: str,
        required_skills: List[str],
        min_experience_months: Optional[int] = None,
        education_level: Optional[str] = None,
        candidate_skills: Optional[List[str]] = None,
        candidate_experience: Optional[Dict[str, Any]] = None,
        candidate_education: Optional[List[Dict[str, Any]]] = None,
    ) -> ATSScoreResult:
        """
        Evaluate a resume against a job posting using ATS simulation.

        Args:
            resume_text: Full resume text
            job_title: Job posting title
            job_description: Job posting description
            required_skills: List of required skills from job posting
            min_experience_months: Minimum required experience in months
            education_level: Required education level
            candidate_skills: Pre-extracted skills from resume
            candidate_experience: Pre-extracted experience data
            candidate_education: Pre-extracted education data

        Returns:
            ATSScoreResult with comprehensive ATS evaluation
        """
        # Create evaluation prompt
        prompt = self._create_evaluation_prompt(
            resume_text=resume_text,
            job_title=job_title,
            job_description=job_description,
            required_skills=required_skills,
            min_experience=min_experience_months,
            education_level=education_level,
        )

        # Call LLM for evaluation
        try:
            llm_result = await self._call_llm(prompt)

            # Extract scores
            keyword_score = float(llm_result.get("keyword_score", 0.0))
            experience_score = float(llm_result.get("experience_score", 0.0))
            education_score = float(llm_result.get("education_score", 0.0))
            fit_score = float(llm_result.get("fit_score", 0.0))
            looks_professional = bool(llm_result.get("looks_professional", True))
            disqualified = bool(llm_result.get("disqualified", False))

            # Extract issues and feedback
            visual_issues = llm_result.get("visual_issues", [])
            ats_issues = llm_result.get("ats_issues", [])
            missing_keywords = llm_result.get("missing_keywords", [])
            suggestions = llm_result.get("suggestions", [])
            feedback = llm_result.get("feedback", "")

            # Compute overall score
            overall_score = self._compute_overall_score(llm_result)

            # Determine if passed
            passed = (
                not disqualified and
                looks_professional and
                overall_score >= self.threshold
            )

            result = ATSScoreResult(
                passed=passed,
                overall_score=overall_score,
                keyword_score=keyword_score,
                experience_score=experience_score,
                education_score=education_score,
                fit_score=fit_score,
                looks_professional=looks_professional,
                disqualified=disqualified,
                visual_issues=visual_issues,
                ats_issues=ats_issues,
                missing_keywords=missing_keywords,
                suggestions=suggestions,
                feedback=feedback,
                provider=self.provider.value,
                model=self.model,
            )

            logger.info(
                f"ATS evaluation complete: passed={passed}, "
                f"score={overall_score:.3f}, "
                f"keywords={keyword_score:.2f}, "
                f"experience={experience_score:.2f}, "
                f"disqualified={disqualified}"
            )

            return result

        except Exception as e:
            logger.error(f"ATS evaluation failed: {e}")
            # Return a failed result
            return ATSScoreResult(
                passed=False,
                overall_score=0.0,
                looks_professional=True,
                disqualified=False,
                visual_issues=[f"Evaluation failed: {str(e)}"],
                feedback="ATS evaluation could not be completed due to an error.",
                provider=self.provider.value,
                model=self.model,
            )

    def evaluate_ats_sync(
        self,
        resume_text: str,
        job_title: str,
        job_description: str,
        required_skills: List[str],
        min_experience_months: Optional[int] = None,
        education_level: Optional[str] = None,
    ) -> ATSScoreResult:
        """
        Synchronous wrapper for ATS evaluation.

        Use this when calling from non-async contexts.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            self.evaluate_ats(
                resume_text=resume_text,
                job_title=job_title,
                job_description=job_description,
                required_skills=required_skills,
                min_experience_months=min_experience_months,
                education_level=education_level,
            )
        )

    async def batch_evaluate_ats(
        self,
        resumes: List[Dict[str, Any]],
        job_title: str,
        job_description: str,
        required_skills: List[str],
    ) -> List[ATSScoreResult]:
        """
        Evaluate multiple resumes against a single job posting.

        Args:
            resumes: List of resumes with 'text', 'id', and optional metadata
            job_title: Job posting title
            job_description: Job posting description
            required_skills: List of required skills

        Returns:
            List of ATSScoreResult in the same order as input resumes
        """
        tasks = []
        for resume in resumes:
            task = self.evaluate_ats(
                resume_text=resume.get("text", ""),
                job_title=job_title,
                job_description=job_description,
                required_skills=required_skills,
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Resume {resumes[i].get('id', i)} evaluation failed: {result}")
                processed_results.append(
                    ATSScoreResult(
                        passed=False,
                        overall_score=0.0,
                        looks_professional=True,
                        disqualified=False,
                        visual_issues=[f"Evaluation failed: {str(result)}"],
                        feedback="ATS evaluation could not be completed.",
                    )
                )
            else:
                processed_results.append(result)

        return processed_results


class SimpleATSChecker:
    """
    Simplified ATS checker that doesn't require LLM API.

    This checker uses rule-based matching as a fallback when LLM APIs
    are not available or configured.

    Example:
        >>> checker = SimpleATSChecker()
        >>> result = checker.check_ats(
        ...     resume_text="Python developer with Django experience...",
        ...     job_title="Python Developer",
        ...     required_skills=["Python", "Django"]
        ... )
        >>> print(result.passed)
        True
    """

    def __init__(self, threshold: float = 0.5):
        """
        Initialize the simple ATS checker.

        Args:
            threshold: Minimum match ratio to pass (0-1)
        """
        self.threshold = threshold

    def check_ats(
        self,
        resume_text: str,
        job_title: str,
        job_description: str,
        required_skills: List[str],
        candidate_skills: Optional[List[str]] = None,
    ) -> ATSScoreResult:
        """
        Perform rule-based ATS checking.

        Args:
            resume_text: Full resume text
            job_title: Job posting title
            job_description: Job posting description
            required_skills: List of required skills
            candidate_skills: Pre-extracted skills (if None, will extract)

        Returns:
            ATSScoreResult with rule-based evaluation
        """
        import re
        from difflib import SequenceMatcher

        resume_lower = resume_text.lower()

        # Extract skills if not provided
        if candidate_skills is None:
            # Simple skill extraction from required skills
            found_skills = []
            for skill in required_skills:
                skill_lower = skill.lower()
                # Check for exact match
                if skill_lower in resume_lower:
                    found_skills.append(skill)
                else:
                    # Check for fuzzy match
                    words = resume_lower.split()
                    for word in words:
                        if SequenceMatcher(None, skill_lower, word).ratio() > 0.85:
                            found_skills.append(skill)
                            break
            candidate_skills = found_skills

        # Calculate keyword score
        if required_skills:
            matched = sum(1 for s in required_skills if any(
                s.lower() in cs.lower() or cs.lower() in s.lower()
                for cs in candidate_skills
            ))
            keyword_score = matched / len(required_skills)
        else:
            keyword_score = 1.0

        # Simple experience score (based on resume length and keywords)
        experience_score = min(len(resume_text) / 2000, 1.0)
        if keyword_score > 0.5:
            experience_score = min(experience_score + 0.2, 1.0)

        # Simple fit score (keyword-heavy)
        fit_score = keyword_score * 0.7 + experience_score * 0.3

        # Education score (default high - assume meets requirements)
        education_score = 0.8

        # Overall score
        overall_score = (
            0.3 * keyword_score +
            0.3 * experience_score +
            0.2 * education_score +
            0.2 * fit_score
        )

        # Missing keywords
        missing_keywords = [
            s for s in required_skills
            if not any(s.lower() in cs.lower() or cs.lower() in s.lower()
                      for cs in candidate_skills)
        ]

        # Suggestions
        suggestions = []
        if missing_keywords:
            suggestions.append(f"Add missing keywords: {', '.join(missing_keywords[:5])}")
        if len(resume_text) < 500:
            suggestions.append("Resume seems too short - add more details about experience")
        if len(resume_text) > 10000:
            suggestions.append("Resume is very long - consider condensing to key points")

        # Visual check (basic)
        looks_professional = len(resume_text) > 200 and len(resume_text) < 15000

        result = ATSScoreResult(
            passed=overall_score >= self.threshold and looks_professional,
            overall_score=overall_score,
            keyword_score=keyword_score,
            experience_score=experience_score,
            education_score=education_score,
            fit_score=fit_score,
            looks_professional=looks_professional,
            disqualified=False,
            missing_keywords=missing_keywords,
            suggestions=suggestions,
            feedback="Rule-based ATS evaluation (LLM not configured).",
            provider="rule-based",
            model="v1.0",
        )

        return result


# Singleton instance
_default_simulator: Optional[ATSSimulator] = None
_default_checker: Optional[SimpleATSChecker] = None


def get_ats_simulator() -> Optional[ATSSimulator]:
    """
    Get or create the default ATS simulator instance.

    Returns None if LLM API is not configured.
    """
    global _default_simulator
    settings = get_settings()

    # Check if any LLM API key is configured
    has_api_key = bool(
        settings.zai_api_key or
        settings.openai_api_key or
        settings.anthropic_api_key or
        settings.google_api_key
    )

    if not has_api_key:
        logger.warning("No LLM API key configured, ATS simulator unavailable")
        return None

    if _default_simulator is None:
        _default_simulator = ATSSimulator()

    return _default_simulator


def get_simple_ats_checker(threshold: float = 0.5) -> SimpleATSChecker:
    """Get or create the default simple ATS checker instance."""
    global _default_checker
    if _default_checker is None:
        _default_checker = SimpleATSChecker(threshold=threshold)
    return _default_checker


async def evaluate_resume_ats(
    resume_text: str,
    job_title: str,
    job_description: str,
    required_skills: List[str],
    use_llm: bool = True,
) -> ATSScoreResult:
    """
    Convenience function to evaluate a resume against a job posting.

    Automatically falls back to rule-based checking if LLM is not configured.

    Args:
        resume_text: Full resume text
        job_title: Job posting title
        job_description: Job posting description
        required_skills: List of required skills
        use_llm: Prefer LLM-based evaluation if available

    Returns:
        ATSScoreResult with evaluation results
    """
    if use_llm:
        simulator = get_ats_simulator()
        if simulator:
            return await simulator.evaluate_ats(
                resume_text=resume_text,
                job_title=job_title,
                job_description=job_description,
                required_skills=required_skills,
            )

    # Fallback to simple checker
    checker = get_simple_ats_checker()
    return checker.check_ats(
        resume_text=resume_text,
        job_title=job_title,
        job_description=job_description,
        required_skills=required_skills,
    )
