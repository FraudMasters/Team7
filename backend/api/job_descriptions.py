"""
Job description generation endpoints for creating AI-powered job descriptions.

This module provides endpoints for generating professional job descriptions
based on role title, required skills, and experience requirements using LLMs.
"""
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from config import get_settings
from i18n.backend_translations import get_error_message, get_success_message

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


# ============================================================================
# Enums and Data Classes
# ============================================================================

class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    ZAI = "zai"


class Tone(str, Enum):
    """Tone for job description."""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FORMAL = "formal"
    FRIENDLY = "friendly"


@dataclass
class JobDescriptionResult:
    """
    Result of job description generation.

    Attributes:
        title: Job title
        summary: Brief summary of the role
        responsibilities: List of key responsibilities
        requirements: List of requirements (skills, qualifications)
        benefits: List of benefits/perks
        company_culture: Brief description of company culture
        interview_process: Brief overview of interview process
        provider: LLM provider used
        model: Model name used
        generated_at: Timestamp of generation
    """
    title: str
    summary: str
    responsibilities: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)
    company_culture: str = ""
    interview_process: str = ""
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
            "company_culture": self.company_culture,
            "interview_process": self.interview_process,
            "provider": self.provider,
            "model": self.model,
            "generated_at": self.generated_at,
        }


# ============================================================================
# Pydantic Models
# ============================================================================

class GenerateJobDescriptionRequest(BaseModel):
    """Request model for generating job descriptions."""

    title: str = Field(..., description="Job title (e.g., 'Senior Python Developer')")
    required_skills: List[str] = Field(
        ..., description="List of required technical skills"
    )
    min_experience_months: Optional[int] = Field(
        default=None, description="Minimum experience in months"
    )
    seniority_level: Optional[str] = Field(
        default=None, description="Seniority level (junior, mid, senior, lead)"
    )
    industry: Optional[str] = Field(
        default=None, description="Industry sector (e.g., 'Technology', 'Finance')"
    )
    work_format: Optional[str] = Field(
        default=None, description="Work format (remote, office, hybrid)"
    )
    location: Optional[str] = Field(
        default=None, description="Job location"
    )
    employment_type: Optional[str] = Field(
        default=None, description="Employment type (full-time, part-time, contract)"
    )
    salary_range: Optional[str] = Field(
        default=None, description="Salary range (e.g., '$80,000 - $120,000')"
    )
    additional_requirements: Optional[List[str]] = Field(
        default=None, description="Additional preferred skills/qualifications"
    )
    tone: Optional[str] = Field(
        default="professional", description="Tone for the description (professional, casual, formal, friendly)"
    )
    language: Optional[str] = Field(
        default="en", description="Language for the job description (en, ru)"
    )


class JobDescriptionResponse(BaseModel):
    """Response model for job description data."""

    title: str = Field(..., description="Job title")
    summary: str = Field(..., description="Brief summary of the role")
    responsibilities: List[str] = Field(..., description="Key responsibilities")
    requirements: List[str] = Field(..., description="Requirements and qualifications")
    benefits: List[str] = Field(..., description="Benefits and perks")
    company_culture: str = Field(..., description="Company culture description")
    interview_process: str = Field(..., description="Interview process overview")
    provider: str = Field(..., description="LLM provider used")
    model: str = Field(..., description="Model name used")
    generated_at: str = Field(..., description="Timestamp of generation")


# ============================================================================
# Helper Functions
# ============================================================================

def _extract_locale(request: Optional[Request]) -> str:
    """
    Extract Accept-Language header from request.

    Args:
        request: The incoming FastAPI request (optional)

    Returns:
        Language code (e.g., 'en', 'ru')
    """
    if request is None:
        return "en"
    accept_language = request.headers.get("Accept-Language", "en")
    lang_code = accept_language.split("-")[0].split(",")[0].strip().lower()
    return lang_code


# ============================================================================
# Job Description Generator
# ============================================================================

class JobDescriptionGenerator:
    """
    Job Description Generator using LLM for creating professional job descriptions.

    This generator creates comprehensive, inclusive job descriptions based on
    role requirements using configured LLM providers.

    Example:
        >>> generator = JobDescriptionGenerator()
        >>> result = await generator.generate_description(
        ...     title="Senior Python Developer",
        ...     required_skills=["Python", "Django", "PostgreSQL"],
        ...     min_experience_months=60
        ... )
        >>> print(result.summary)
        "We are looking for a skilled Senior Python Developer..."
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

    def _get_system_prompt(self, language: str = "en") -> str:
        """Get the system prompt for job description generation."""
        if language == "ru":
            return """Вы эксперт по написанию вакансий и HR-специалист. Ваша задача — создать профессиональное, инклюзивное и привлекательное описание вакансии на основе предоставленной информации.

Создайте описание вакансии, включающее следующие разделы:

1. **Краткое описание (Summary)**: Введение в роль и компанию (2-3 предложения)

2. **Обязанности (Responsibilities)**: Список ключевых обязанностей (5-7 пунктов)

3. **Требования (Requirements)**: Список требований к кандидату, включая навыки и квалификацию (5-7 пунктов)

4. **Преимущества (Benefits)**: Список преимуществ и бонусов (4-5 пунктов)

5. **Корпоративная культура (Company Culture)**: Краткое описание корпоративной культуры и ценностей (2-3 предложения)

6. **Процесс собеседования (Interview Process)**: Обзор процесса собеседования (2-3 предложения)

Верните свой анализ в следующем формате JSON:
```json
{
    "summary": "Краткое описание роли",
    "responsibilities": [
        "Обязанность 1",
        "Обязаность 2"
    ],
    "requirements": [
        "Требование 1",
        "Требование 2"
    ],
    "benefits": [
        "Преимущество 1",
        "Преимущество 2"
    ],
    "company_culture": "Описание корпоративной культуры",
    "interview_process": "Описание процесса собеседования"
}
```

Важные рекомендации:
- Используйте инклюзивный язык, который привлекает разнообразных кандидатов
- Избегайте гендерных стереотипов и предвзятого языка
- Четко укажите основные обязанности и требования
- Сделайте описание привлекательным, но честным
- Используйте активные глаголы для обязанностей
- Будьте конкретны в требованиях к навыкам
- Включите популярные преимущества, которые ценят соискатели
"""

        return """You are an expert job description writer and HR specialist. Your task is to create a professional, inclusive, and compelling job description based on the provided information.

Create a job description that includes the following sections:

1. **Summary**: A brief introduction to the role and company (2-3 sentences)

2. **Responsibilities**: A list of key responsibilities (5-7 bullet points)

3. **Requirements**: A list of requirements for the candidate, including skills and qualifications (5-7 bullet points)

4. **Benefits**: A list of benefits and perks (4-5 bullet points)

5. **Company Culture**: A brief description of the company culture and values (2-3 sentences)

6. **Interview Process**: An overview of the interview process (2-3 sentences)

Return your analysis in the following JSON format:
```json
{
    "summary": "Brief overview of the role",
    "responsibilities": [
        "Responsibility 1",
        "Responsibility 2"
    ],
    "requirements": [
        "Requirement 1",
        "Requirement 2"
    ],
    "benefits": [
        "Benefit 1",
        "Benefit 2"
    ],
    "company_culture": "Description of company culture",
    "interview_process": "Description of interview process"
}
```

Important guidelines:
- Use inclusive language that attracts diverse candidates
- Avoid gendered language and bias
- Be clear about the key responsibilities and requirements
- Make the description engaging but realistic
- Use action verbs for responsibilities
- Be specific about skills needed
- Include competitive benefits that candidates value
- Focus on what the candidate will do and learn, not just what they must have
- Avoid jargon unless necessary for the role
"""

    def _create_prompt(
        self,
        title: str,
        required_skills: List[str],
        min_experience_months: Optional[int] = None,
        seniority_level: Optional[str] = None,
        industry: Optional[str] = None,
        work_format: Optional[str] = None,
        location: Optional[str] = None,
        employment_type: Optional[str] = None,
        salary_range: Optional[str] = None,
        additional_requirements: Optional[List[str]] = None,
        tone: str = "professional",
        language: str = "en",
    ) -> str:
        """Create the job description generation prompt for the LLM."""
        if language == "ru":
            prompt_parts = [
                f"Пожалуйста, создайте профессиональное описание вакансии со следующими деталями:\n\n",
                f"=== ВАКАНСИЯ ===\n",
                f"Должность: {title}\n",
                f"Обязательные навыки: {', '.join(required_skills)}\n",
            ]

            if min_experience_months:
                years = min_experience_months // 12
                months = min_experience_months % 12
                if years > 0 and months > 0:
                    prompt_parts.append(f"Минимальный опыт: {years} лет и {months} месяцев\n")
                elif years > 0:
                    prompt_parts.append(f"Минимальный опыт: {years} лет\n")
                elif months > 0:
                    prompt_parts.append(f"Минимальный опыт: {months} месяцев\n")

            if seniority_level:
                prompt_parts.append(f"Уровень должности: {seniority_level}\n")
            if industry:
                prompt_parts.append(f"Отрасль: {industry}\n")
            if work_format:
                prompt_parts.append(f"Формат работы: {work_format}\n")
            if location:
                prompt_parts.append(f"Местоположение: {location}\n")
            if employment_type:
                prompt_parts.append(f"Тип занятости: {employment_type}\n")
            if salary_range:
                prompt_parts.append(f"Зарплата: {salary_range}\n")
            if additional_requirements:
                prompt_parts.append(f"Дополнительные требования: {', '.join(additional_requirements)}\n")

            prompt_parts.extend([
                f"Тон: {tone}\n",
                f"\n=== КОНЕЦ ===\n",
                f"Пожалуйста, создайте описание вакансии и верните JSON-ответ со всеми разделами.",
            ])
        else:
            prompt_parts = [
                f"Please create a professional job description with the following details:\n\n",
                f"=== JOB POSTING ===\n",
                f"Title: {title}\n",
                f"Required Skills: {', '.join(required_skills)}\n",
            ]

            if min_experience_months:
                years = min_experience_months // 12
                months = min_experience_months % 12
                if years > 0 and months > 0:
                    prompt_parts.append(f"Minimum Experience: {years} years and {months} months\n")
                elif years > 0:
                    prompt_parts.append(f"Minimum Experience: {years} years\n")
                elif months > 0:
                    prompt_parts.append(f"Minimum Experience: {months} months\n")

            if seniority_level:
                prompt_parts.append(f"Seniority Level: {seniority_level}\n")
            if industry:
                prompt_parts.append(f"Industry: {industry}\n")
            if work_format:
                prompt_parts.append(f"Work Format: {work_format}\n")
            if location:
                prompt_parts.append(f"Location: {location}\n")
            if employment_type:
                prompt_parts.append(f"Employment Type: {employment_type}\n")
            if salary_range:
                prompt_parts.append(f"Salary Range: {salary_range}\n")
            if additional_requirements:
                prompt_parts.append(f"Additional Requirements: {', '.join(additional_requirements)}\n")

            prompt_parts.extend([
                f"Tone: {tone}\n",
                f"\n=== END ===\n",
                f"Please create a job description and return a JSON response with all sections.",
            ])

        return "".join(prompt_parts)

    async def _call_openai(self, prompt: str, language: str = "en") -> Dict[str, Any]:
        """Call OpenAI API for job description generation."""
        try:
            from openai import AsyncOpenAI

            if not self.openai_api_key:
                raise ValueError("OpenAI API key not configured")

            client = AsyncOpenAI(api_key=self.openai_api_key)

            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt(language)},
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

    async def _call_anthropic(self, prompt: str, language: str = "en") -> Dict[str, Any]:
        """Call Anthropic API for job description generation."""
        try:
            from anthropic import AsyncAnthropic

            if not self.anthropic_api_key:
                raise ValueError("Anthropic API key not configured")

            client = AsyncAnthropic(api_key=self.anthropic_api_key)

            response = await client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=self._get_system_prompt(language),
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

    async def _call_google(self, prompt: str, language: str = "en") -> Dict[str, Any]:
        """Call Google Gemini API for job description generation."""
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
                system_instruction=self._get_system_prompt(language),
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

    async def _call_zai(self, prompt: str, language: str = "en") -> Dict[str, Any]:
        """Call Z.ai API for job description generation (OpenAI-compatible)."""
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
                    {"role": "system", "content": self._get_system_prompt(language)},
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

    async def _call_llm(self, prompt: str, language: str = "en") -> Dict[str, Any]:
        """Call the appropriate LLM provider."""
        if self.provider == LLMProvider.ZAI:
            return await self._call_zai(prompt, language)
        elif self.provider == LLMProvider.OPENAI:
            return await self._call_openai(prompt, language)
        elif self.provider == LLMProvider.ANTHROPIC:
            return await self._call_anthropic(prompt, language)
        elif self.provider == LLMProvider.GOOGLE:
            return await self._call_google(prompt, language)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    async def generate_description(
        self,
        title: str,
        required_skills: List[str],
        min_experience_months: Optional[int] = None,
        seniority_level: Optional[str] = None,
        industry: Optional[str] = None,
        work_format: Optional[str] = None,
        location: Optional[str] = None,
        employment_type: Optional[str] = None,
        salary_range: Optional[str] = None,
        additional_requirements: Optional[List[str]] = None,
        tone: str = "professional",
        language: str = "en",
    ) -> JobDescriptionResult:
        """
        Generate a job description based on role requirements.

        Args:
            title: Job title
            required_skills: List of required skills
            min_experience_months: Minimum experience in months
            seniority_level: Seniority level (junior, mid, senior, lead)
            industry: Industry sector
            work_format: Work format (remote, office, hybrid)
            location: Job location
            employment_type: Employment type (full-time, part-time, contract)
            salary_range: Salary range
            additional_requirements: Additional preferred skills
            tone: Tone for description (professional, casual, formal, friendly)
            language: Language for description (en, ru)

        Returns:
            JobDescriptionResult with comprehensive job description
        """
        # Create prompt
        prompt = self._create_prompt(
            title=title,
            required_skills=required_skills,
            min_experience_months=min_experience_months,
            seniority_level=seniority_level,
            industry=industry,
            work_format=work_format,
            location=location,
            employment_type=employment_type,
            salary_range=salary_range,
            additional_requirements=additional_requirements,
            tone=tone,
        )

        # Call LLM for generation
        try:
            llm_result = await self._call_llm(prompt, language)

            # Extract components from result
            summary = llm_result.get("summary", "")
            responsibilities = llm_result.get("responsibilities", [])
            requirements = llm_result.get("requirements", [])
            benefits = llm_result.get("benefits", [])
            company_culture = llm_result.get("company_culture", "")
            interview_process = llm_result.get("interview_process", "")

            # Get current timestamp
            generated_at = datetime.utcnow().isoformat()

            result = JobDescriptionResult(
                title=title,
                summary=summary,
                responsibilities=responsibilities,
                requirements=requirements,
                benefits=benefits,
                company_culture=company_culture,
                interview_process=interview_process,
                provider=self.provider.value,
                model=self.model,
                generated_at=generated_at,
            )

            logger.info(
                f"Job description generation complete: "
                f"title={title}, "
                f"{len(responsibilities)} responsibilities, "
                f"{len(requirements)} requirements"
            )

            return result

        except Exception as e:
            logger.error(f"Job description generation failed: {e}")
            # Return a minimal result
            from datetime import datetime
            return JobDescriptionResult(
                title=title,
                summary="Job description generation failed. Please try again.",
                responsibilities=[],
                requirements=[],
                benefits=[],
                company_culture="",
                interview_process="",
                provider=self.provider.value,
                model=self.model,
                generated_at=datetime.utcnow().isoformat(),
            )


# ============================================================================
# API Endpoints
# ============================================================================

@router.post(
    "/generate",
    response_model=JobDescriptionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Job Descriptions"],
)
async def generate_job_description(
    http_request: Request, request: GenerateJobDescriptionRequest
) -> JSONResponse:
    """
    Generate a professional job description based on role requirements.

    This endpoint creates comprehensive, inclusive job descriptions using LLMs.
    The description includes a summary, key responsibilities, requirements,
    benefits, company culture overview, and interview process information.

    Args:
        http_request: FastAPI request object (for Accept-Language header)
        request: Generate request with job details

    Returns:
        JSON response with generated job description

    Raises:
        HTTPException(400): If validation fails
        HTTPException(500): If generation fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "/api/job-descriptions/generate",
        ...     json={
        ...         "title": "Senior Python Developer",
        ...         "required_skills": ["Python", "Django", "PostgreSQL"],
        ...         "min_experience_months": 60
        ...     }
        ... )
        >>> response.json()
        {
            "title": "Senior Python Developer",
            "summary": "We are looking for a skilled Senior Python Developer...",
            "responsibilities": [...],
            "requirements": [...],
            ...
        }
    """
    locale = _extract_locale(http_request)
    start_time = time.time()

    try:
        logger.info(f"Generating job description for title: {request.title}")

        # Validate required fields
        if not request.title or not request.title.strip():
            error_msg = get_error_message("missing_required_field", locale, field="title")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

        if not request.required_skills or len(request.required_skills) == 0:
            error_msg = get_error_message("missing_required_field", locale, field="required_skills")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

        # Validate seniority level if provided
        valid_seniority_levels = ["junior", "mid", "middle", "senior", "lead", "principal", "entry"]
        if request.seniority_level:
            if request.seniority_level.lower() not in valid_seniority_levels:
                logger.warning(f"Unusual seniority level: {request.seniority_level}")

        # Validate work format if provided
        valid_work_formats = ["remote", "office", "hybrid", "on-site", "onsite"]
        if request.work_format:
            if request.work_format.lower() not in [w.lower() for w in valid_work_formats]:
                logger.warning(f"Unusual work format: {request.work_format}")

        # Validate tone if provided
        valid_tones = ["professional", "casual", "formal", "friendly"]
        if request.tone and request.tone.lower() not in valid_tones:
            logger.warning(f"Invalid tone, defaulting to professional: {request.tone}")
            request.tone = "professional"

        # Generate job description using LLM
        generator = JobDescriptionGenerator()
        result = await generator.generate_description(
            title=request.title,
            required_skills=request.required_skills,
            min_experience_months=request.min_experience_months,
            seniority_level=request.seniority_level,
            industry=request.industry,
            work_format=request.work_format,
            location=request.location,
            employment_type=request.employment_type,
            salary_range=request.salary_range,
            additional_requirements=request.additional_requirements,
            tone=request.tone or "professional",
            language=request.language or "en",
        )

        # Build response
        response_data = result.to_dict()

        processing_time_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Job description generated for title: {request.title} "
            f"in {processing_time_ms:.2f}ms"
        )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        error_msg = get_error_message("invalid_input", locale)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        ) from e
    except Exception as e:
        logger.error(f"Error generating job description: {e}", exc_info=True)
        error_msg = get_error_message("internal_server_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
