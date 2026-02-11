"""
Job Description Generator Module

This module provides LLM-based job description generation that creates
professional, inclusive, and unbiased job descriptions based on role
title and requirements.

Key features:
- Professional job descriptions from role titles
- Inclusive and unbiased language
- Customizable based on skills, experience, and requirements
- Multiple output sections (summary, responsibilities, requirements, benefits)
- Support for different seniority levels and employment types
- Industry-specific terminology when needed

The module uses OpenAI, Anthropic, Google, or Zai APIs to generate
high-quality job descriptions.
"""
import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from config import get_settings

logger = logging.getLogger(__name__)

__all__ = [
    "LLMProvider",
    "EmploymentType",
    "SeniorityLevel",
    "JobDescriptionSection",
    "JobDescriptionResult",
    "JobDescriptionGenerator",
    "get_job_description_generator",
    "generate_job_description",
]


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    ZAI = "zai"


class EmploymentType(str, Enum):
    """Types of employment."""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"


class SeniorityLevel(str, Enum):
    """Seniority levels for positions."""
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"


@dataclass
class JobDescriptionSection:
    """
    A section of the job description.

    Attributes:
        title: Section title (e.g., "About the Role", "Responsibilities")
        content: Section content as markdown or HTML
        order: Display order for the section
    """
    title: str
    content: str
    order: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert section to dictionary for JSON serialization."""
        return {
            "title": self.title,
            "content": self.content,
            "order": self.order,
        }


@dataclass
class JobDescriptionResult:
    """
    Result of job description generation.

    Attributes:
        title: Job title
        summary: Brief overview of the role (2-3 sentences)
        responsibilities: List of key responsibilities
        requirements: List of requirements (skills, experience, education)
        benefits: List of benefits and perks
        sections: Additional custom sections
        full_description: Complete job description as formatted text
        suggested_salary_range: Suggested salary range (if available)
        inclusive_language_score: Score indicating inclusiveness of language
        bias_warnings: Any potential bias warnings detected
        provider: LLM provider used
        model: Model name used
        generated_at: Timestamp of generation
    """
    title: str
    summary: str
    responsibilities: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)
    sections: List[JobDescriptionSection] = field(default_factory=list)
    full_description: str = ""
    suggested_salary_range: Optional[str] = None
    inclusive_language_score: Optional[float] = None
    bias_warnings: List[str] = field(default_factory=list)
    provider: str = ""
    model: str = ""
    generated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
            "title": self.title,
            "summary": self.summary,
            "responsibilities": self.responsibilities,
            "requirements": self.requirements,
            "benefits": self.benefits,
            "sections": [s.to_dict() for s in self.sections],
            "full_description": self.full_description,
            "suggested_salary_range": self.suggested_salary_range,
            "inclusive_language_score": self.inclusive_language_score,
            "bias_warnings": self.bias_warnings,
            "provider": self.provider,
            "model": self.model,
            "generated_at": self.generated_at,
        }


class JobDescriptionGenerator:
    """
    Job Description Generator using LLM for creating inclusive job descriptions.

    This generator creates professional, inclusive, and unbiased job descriptions
    based on a role title and requirements. It emphasizes inclusive language
    and avoids biased or discriminatory content.

    Example:
        >>> generator = JobDescriptionGenerator()
        >>> result = await generator.generate_description(
        ...     title="Senior Python Developer",
        ...     required_skills=["Python", "Django", "PostgreSQL"],
        ...     min_experience_months=60,
        ...     seniority_level="senior"
        ... )
        >>> print(result.summary)
        "We are looking for a skilled Python Developer to join our team..."
        >>> print(result.responsibilities[0])
        "Design and implement scalable web applications..."
    """

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize the Job Description Generator.

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
            f"JobDescriptionGenerator initialized: provider={self.provider}, "
            f"model={self.model}"
        )

    def _get_system_prompt(self) -> str:
        """Get the system prompt for job description generation."""
        return """You are an expert job description writer specializing in creating professional, inclusive, and unbiased job postings. Your task is to generate high-quality job descriptions that attract diverse talent while accurately representing the role requirements.

## Inclusive Language Guidelines

CRITICAL: Follow these inclusive language principles:

1. **Use gender-neutral language**:
   - Use "they/them/their" instead of "he/him" or "she/her"
   - Avoid gendered terms like "salesman" (use "sales representative")
   - Use inclusive terms like "chairperson" instead of "chairman"

2. **Avoid age-discriminatory language**:
   - Avoid terms like "recent graduate", "young", "energetic", "digital native"
   - Focus on skills and experience, not career stage assumptions

3. **Avoid cultural bias**:
   - Remove requirements like "must be a native English speaker" (use "fluent in English")
   - Avoid cultural references that may exclude certain groups
   - Focus on communication skills, not cultural fit

4. **Avoid ability bias**:
   - Only include physical requirements if truly essential for the job
   - Use phrases like "ability to" instead of "must be able to"

5. **Avoid socioeconomic bias**:
   - Avoid requiring specific degrees unless legally required
   - Focus on skills and competencies over prestigious credentials
   - Accept equivalent experience in place of education

6. **Use welcoming language**:
   - "We encourage candidates from diverse backgrounds to apply"
   - "We value different perspectives and experiences"
   - "You don't need to match every requirement - apply if this role excites you"

## Job Description Structure

Generate a job description with these sections:

1. **Job Summary** (2-3 sentences): Engaging overview of the role and its impact

2. **Key Responsibilities** (5-7 bullet points): What the person will do daily
   - Start with action verbs
   - Be specific about outcomes
   - Avoid jargon where possible

3. **Requirements** (5-7 bullet points): Skills, experience, and qualifications
   - Distinguish between "must have" and "nice to have"
   - Focus on skills, not personal traits
   - Accept equivalent experience

4. **Benefits & Perks** (3-5 bullet points): What the company offers
   - Include both tangible and intangible benefits
   - Highlight work-life balance and growth opportunities

5. **About the Company/Team** (2-3 sentences): Brief, welcoming context

## JSON Response Format

Return your response in this exact JSON structure:
```json
{
    "summary": "Engaging 2-3 sentence overview of the role...",
    "responsibilities": [
        "Action-oriented responsibility 1",
        "Action-oriented responsibility 2"
    ],
    "requirements": [
        "Specific skill or qualification 1",
        "Specific skill or qualification 2"
    ],
    "benefits": [
        "Benefit or perk 1",
        "Benefit or perk 2"
    ],
    "about_team": "Brief welcoming description of the team...",
    "inclusive_language_score": 0.95,
    "bias_warnings": []
}
```

## Quality Checklist

Before finalizing, ensure your description:
- [ ] Uses gender-neutral pronouns throughout
- [ ] Avoids age-coded language (young, energetic, recent grad)
- [ ] Focuses on skills and competencies
- [ ] Includes welcoming language for diverse candidates
- [ ] Distinguishes between essential and preferred requirements
- [ ] Uses action verbs for responsibilities
- [ ] Provides realistic preview of the role

Remember: The goal is to attract the best talent while ensuring every qualified candidate feels welcome to apply.
"""

    def _create_description_prompt(
        self,
        title: str,
        required_skills: List[str],
        min_experience_months: Optional[int] = None,
        seniority_level: Optional[str] = None,
        employment_type: Optional[str] = None,
        department: Optional[str] = None,
        industry: Optional[str] = None,
        location: Optional[str] = None,
        remote_policy: Optional[str] = None,
        salary_range: Optional[str] = None,
        additional_requirements: Optional[List[str]] = None,
        responsibilities: Optional[List[str]] = None,
        company_description: Optional[str] = None,
        custom_sections: Optional[Dict[str, str]] = None,
        language: str = "en",
    ) -> str:
        """Create the job description generation prompt for the LLM."""
        prompt_parts = [
            f"Generate a professional, inclusive job description for the following role:\n\n",
            f"=== ROLE DETAILS ===\n",
            f"Title: {title}\n",
        ]

        if department:
            prompt_parts.append(f"Department: {department}\n")
        if seniority_level:
            prompt_parts.append(f"Seniority Level: {seniority_level}\n")
        if employment_type:
            prompt_parts.append(f"Employment Type: {employment_type}\n")

        prompt_parts.append(f"\n=== REQUIREMENTS ===\n")
        prompt_parts.append(f"Required Skills: {', '.join(required_skills)}\n")

        if min_experience_months:
            years = min_experience_months // 12
            if years > 0:
                prompt_parts.append(f"Minimum Experience: {years} years\n")

        if additional_requirements:
            prompt_parts.append(f"Additional Requirements:\n")
            for req in additional_requirements[:5]:
                prompt_parts.append(f"  - {req}\n")

        if responsibilities:
            prompt_parts.append(f"\nKey Responsibilities to Include:\n")
            for resp in responsibilities[:7]:
                prompt_parts.append(f"  - {resp}\n")

        if industry:
            prompt_parts.append(f"\nIndustry: {industry}\n")

        if location:
            prompt_parts.append(f"Location: {location}\n")
        if remote_policy:
            prompt_parts.append(f"Remote Policy: {remote_policy}\n")

        if salary_range:
            prompt_parts.append(f"Salary Range: {salary_range}\n")

        if company_description:
            prompt_parts.append(f"\n=== COMPANY CONTEXT ===\n")
            prompt_parts.append(f"{company_description[:500]}\n")

        if custom_sections:
            prompt_parts.append(f"\n=== CUSTOM SECTIONS ===\n")
            for section_title, section_content in custom_sections.items():
                prompt_parts.append(f"\n{section_title}:\n{section_content[:200]}\n")

        prompt_parts.append(f"\nLanguage: {language}\n")
        prompt_parts.append(f"\nPlease generate an inclusive, professional job description following the JSON format specified in the system prompt.\n")

        return "".join(prompt_parts)

    async def _call_openai(self, prompt: str) -> Dict[str, Any]:
        """Call OpenAI API for description generation."""
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
        """Call Anthropic API for description generation."""
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
            # Extract JSON from response
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
        """Call Google Gemini API for description generation."""
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
        """Call Z.ai API for description generation (OpenAI-compatible)."""
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

    def _format_full_description(
        self,
        summary: str,
        responsibilities: List[str],
        requirements: List[str],
        benefits: List[str],
        about_team: str,
        custom_sections: Optional[Dict[str, str]] = None,
    ) -> str:
        """Format the complete job description as structured text."""
        sections = []

        # Summary
        sections.append(f"## About the Role\n{summary}\n")

        # Responsibilities
        if responsibilities:
            sections.append("## Key Responsibilities\n")
            for resp in responsibilities:
                sections.append(f"- {resp}")
            sections.append("")

        # Requirements
        if requirements:
            sections.append("## Requirements\n")
            for req in requirements:
                sections.append(f"- {req}")
            sections.append("")

        # Custom sections
        if custom_sections:
            for section_title, section_content in custom_sections.items():
                sections.append(f"## {section_title}\n{section_content}\n")

        # Benefits
        if benefits:
            sections.append("## Benefits & Perks\n")
            for benefit in benefits:
                sections.append(f"- {benefit}")
            sections.append("")

        # About team
        if about_team:
            sections.append(f"## About the Team\n{about_team}\n")

        return "\n".join(sections)

    def _check_inclusive_language(self, text: str) -> tuple[float, List[str]]:
        """
        Check the description for inclusive language and potential biases.

        Returns:
            Tuple of (inclusive_language_score, list of warnings)
        """
        warnings = []
        score = 1.0

        # Keywords that may indicate biased language
        biased_terms = {
            "gender": ["he/she", "him/her", "salesman", "chairman", "manpower", "mankind"],
            "age": ["young", "energetic", "recent graduate", "digital native", "fresh"],
            "cultural": ["native speaker", "cultural fit", "same culture"],
            "ability": ["must be able to stand", "must be able to lift", "physically fit"],
        }

        text_lower = text.lower()

        for category, terms in biased_terms.items():
            for term in terms:
                if term in text_lower:
                    warnings.append(f"Potential {category} bias detected: '{term}'")
                    score -= 0.1

        # Check for welcoming language (positive indicators)
        welcoming_terms = [
            "diverse", "inclusive", "equal opportunity", "all backgrounds",
            "encourage", "welcome", "valued", "different perspectives"
        ]
        has_welcoming = any(term in text_lower for term in welcoming_terms)
        if not has_welcoming:
            warnings.append("Consider adding more welcoming language for diverse candidates")
            score -= 0.05

        # Ensure score is in valid range
        score = max(0.0, min(1.0, score))

        return score, warnings

    async def generate_description(
        self,
        title: str,
        required_skills: List[str],
        min_experience_months: Optional[int] = None,
        seniority_level: Optional[str] = None,
        employment_type: Optional[str] = None,
        department: Optional[str] = None,
        industry: Optional[str] = None,
        location: Optional[str] = None,
        remote_policy: Optional[str] = None,
        salary_range: Optional[str] = None,
        additional_requirements: Optional[List[str]] = None,
        responsibilities: Optional[List[str]] = None,
        company_description: Optional[str] = None,
        custom_sections: Optional[Dict[str, str]] = None,
        language: str = "en",
    ) -> JobDescriptionResult:
        """
        Generate a job description based on role details.

        Args:
            title: Job title
            required_skills: List of required skills
            min_experience_months: Minimum required experience in months
            seniority_level: Seniority level (entry, mid, senior, lead, executive)
            employment_type: Type of employment (full_time, part_time, contract, etc.)
            department: Department or team
            industry: Industry sector
            location: Job location
            remote_policy: Remote work policy (remote, hybrid, on-site)
            salary_range: Salary range for the position
            additional_requirements: Additional requirements to include
            responsibilities: Specific responsibilities to highlight
            company_description: Brief company description for context
            custom_sections: Additional custom sections as {title: content}
            language: Output language (default: "en")

        Returns:
            JobDescriptionResult with complete job description
        """
        logger.info(f"Generating job description for: {title}")

        # Validate required parameters
        if not title:
            raise ValueError("Job title is required")
        if not required_skills:
            raise ValueError("At least one required skill must be specified")

        # Create description generation prompt
        prompt = self._create_description_prompt(
            title=title,
            required_skills=required_skills,
            min_experience_months=min_experience_months,
            seniority_level=seniority_level,
            employment_type=employment_type,
            department=department,
            industry=industry,
            location=location,
            remote_policy=remote_policy,
            salary_range=salary_range,
            additional_requirements=additional_requirements,
            responsibilities=responsibilities,
            company_description=company_description,
            custom_sections=custom_sections,
            language=language,
        )

        try:
            # Call LLM for description generation
            llm_result = await self._call_llm(prompt)

            # Extract data from LLM response
            summary = llm_result.get("summary", "")
            responsibilities_list = llm_result.get("responsibilities", [])
            requirements_list = llm_result.get("requirements", [])
            benefits_list = llm_result.get("benefits", [])
            about_team = llm_result.get("about_team", "")

            # Get inclusive language score from LLM or compute it
            inclusive_score = llm_result.get("inclusive_language_score")
            bias_warnings = llm_result.get("bias_warnings", [])

            # If LLM didn't provide score, compute it ourselves
            if inclusive_score is None:
                full_text = " ".join([
                    summary,
                    " ".join(responsibilities_list),
                    " ".join(requirements_list),
                ])
                inclusive_score, bias_warnings = self._check_inclusive_language(full_text)

            # Create sections
            sections = []
            if about_team:
                sections.append(JobDescriptionSection(
                    title="About the Team",
                    content=about_team,
                    order=0
                ))

            # Add custom sections if provided
            if custom_sections:
                for idx, (section_title, section_content) in enumerate(custom_sections.items()):
                    sections.append(JobDescriptionSection(
                        title=section_title,
                        content=section_content,
                        order=idx + 1
                    ))

            # Format full description
            full_description = self._format_full_description(
                summary=summary,
                responsibilities=responsibilities_list,
                requirements=requirements_list,
                benefits=benefits_list,
                about_team=about_team,
                custom_sections=custom_sections,
            )

            # Get current timestamp
            generated_at = datetime.utcnow().isoformat()

            result = JobDescriptionResult(
                title=title,
                summary=summary,
                responsibilities=responsibilities_list,
                requirements=requirements_list,
                benefits=benefits_list,
                sections=sections,
                full_description=full_description,
                suggested_salary_range=salary_range,
                inclusive_language_score=inclusive_score,
                bias_warnings=bias_warnings,
                provider=self.provider.value,
                model=self.model,
                generated_at=generated_at,
            )

            logger.info(
                f"Job description generated successfully for {title} "
                f"(inclusive score: {inclusive_score:.2f}, "
                f"{len(bias_warnings)} bias warnings)"
            )

            return result

        except Exception as e:
            logger.error(f"Job description generation failed: {e}")
            # Return a minimal result
            generated_at = datetime.utcnow().isoformat()
            return JobDescriptionResult(
                title=title,
                summary=f"Job description generation failed: {str(e)}",
                responsibilities=[],
                requirements=[f"Required: {skill}" for skill in required_skills],
                provider=self.provider.value,
                model=self.model,
                generated_at=generated_at,
                bias_warnings=["Description generation encountered an error"],
            )

    def generate_description_sync(
        self,
        title: str,
        required_skills: List[str],
        min_experience_months: Optional[int] = None,
        seniority_level: Optional[str] = None,
        **kwargs,
    ) -> JobDescriptionResult:
        """
        Synchronous wrapper for description generation.

        Use this when calling from non-async contexts.

        Args:
            title: Job title
            required_skills: List of required skills
            min_experience_months: Minimum required experience in months
            seniority_level: Seniority level
            **kwargs: Additional parameters for generate_description

        Returns:
            JobDescriptionResult with complete job description
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            self.generate_description(
                title=title,
                required_skills=required_skills,
                min_experience_months=min_experience_months,
                seniority_level=seniority_level,
                **kwargs,
            )
        )


# Singleton instance
_default_generator: Optional[JobDescriptionGenerator] = None


def get_job_description_generator() -> Optional[JobDescriptionGenerator]:
    """
    Get or create the default job description generator instance.

    Returns None if LLM API is not configured.

    Example:
        >>> generator = get_job_description_generator()
        >>> if generator:
        ...     result = await generator.generate_description(...)
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
        logger.warning("No LLM API key configured, job description generator unavailable")
        return None

    if _default_generator is None:
        _default_generator = JobDescriptionGenerator()

    return _default_generator


async def generate_job_description(
    title: str,
    required_skills: List[str],
    min_experience_months: Optional[int] = None,
    seniority_level: Optional[str] = None,
    **kwargs,
) -> Optional[JobDescriptionResult]:
    """
    Convenience function to generate a job description.

    Returns None if LLM is not configured.

    Args:
        title: Job title
        required_skills: List of required skills
        min_experience_months: Minimum required experience in months
        seniority_level: Seniority level
        **kwargs: Additional parameters for generate_description

    Returns:
        JobDescriptionResult with complete job description, or None if unavailable

    Example:
        >>> description = await generate_job_description(
        ...     title="Senior Python Developer",
        ...     required_skills=["Python", "Django", "PostgreSQL"],
        ...     min_experience_months=60,
        ...     seniority_level="senior"
        ... )
    """
    generator = get_job_description_generator()
    if generator:
        return await generator.generate_description(
            title=title,
            required_skills=required_skills,
            min_experience_months=min_experience_months,
            seniority_level=seniority_level,
            **kwargs,
        )

    return None
