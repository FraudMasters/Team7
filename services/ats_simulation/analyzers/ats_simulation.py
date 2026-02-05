"""
ATS (Applicant Tracking System) Simulation Module

# Русский комментарий:
Этот модуль предоставляет LLM-симуляцию ATS, которая оценивает, насколько хорошо
резюме соответствует вакансии с точки зрения системы ATS.

Основные функции:
- Оценка сопоставления ключевых слов на основе LLM
- Оценка релевантности опыта
- Сопоставление уровня образования
- Общая оценка соответствия
- Проверка визуального формата
- Обнаружение дисквалифицирующих факторов (красные флаги)

Модуль использует API OpenAI, Anthropic или Google для выполнения комплексного
ATS-анализа, аналогичного тому, как коммерческие ATS-системы оценивают резюме.
"""
import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from config import get_settings

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Поддерживаемые провайдеры LLM."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    ZAI = "zai"


@dataclass
class ATSScoreResult:
    """
    Результат оценки ATS.

    Attributes:
        passed: Прошло ли резюме пороговое значение ATS
        overall_score: Комплексная оценка ATS (0-1)
        keyword_score: Оценка сопоставления ключевых слов (0-1)
        experience_score: Оценка релевантности опыта (0-1)
        education_score: Оценка соответствия образования (0-1)
        fit_score: Общая оценка соответствия (0-1)
        looks_professional: Выглядит ли резюме профессионально оформленным
        disqualified: Есть ли в резюме дисквалифицирующие проблемы
        visual_issues: Список визуальных/проблем с оформлением
        ats_issues: Список специфичных проблем ATS
        missing_keywords: Список важных отсутствующих ключевых слов
        suggestions: Список предложений по улучшению
        feedback: Подробная обратная связь от анализа LLM
        provider: Используемый провайдер LLM
        model: Название использованной модели
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
        """Преобразовать результат в словарь для JSON-сериализации."""
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
    Симуляция ATS с использованием LLM для комплексной оценки резюме.

    Этот симулятор оценивает резюме относительно вакансий с использованием
    LLM-анализа для имитации коммерческих ATS-систем. Предоставляет детальную
    оценку по нескольким измерениям.

    Example:
        >>> simulator = ATSSimulator()
        >>> result = await simulator.evaluate_ats(
        ...     resume_text="Опытный разработчик Python...",
        ...     job_title="Senior Python Developer",
        ...     job_description="Ищем опытного разработчика Python...",
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
        Инициализация симулятора ATS.

        Args:
            provider: Провайдер LLM (по умолчанию из конфигурации)
            model: Название модели (по умолчанию из конфигурации)
            threshold: Порог проходного балла ATS (по умолчанию из конфигурации)
        """
        settings = get_settings()

        self.provider = provider or LLMProvider(settings.llm_provider)
        self.model = model or settings.llm_model
        self.threshold = threshold if threshold is not None else settings.ats_threshold

        # Веса для расчета оценки
        self.keyword_weight = settings.ats_keyword_weight
        self.experience_weight = settings.ats_experience_weight
        self.education_weight = settings.ats_education_weight
        self.fit_weight = settings.ats_fit_weight

        # Параметры LLM
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens

        # API ключи
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
        """Получить системный промпт для оценки ATS."""
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
        """Создать промпт оценки для LLM."""
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
        """Вызвать API OpenAI для оценки ATS."""
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
        """Вызвать API Anthropic для оценки ATS."""
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
        """Вызвать API Google Gemini для оценки ATS."""
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
        """Вызвать API Z.ai для оценки ATS (OpenAI-совместимый)."""
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
        """Вызвать соответствующий провайдер LLM."""
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
        """Вычислить взвешенную общую оценку ATS."""
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
        Оценить резюме относительно вакансии с использованием симуляции ATS.

        Args:
            resume_text: Полный текст резюме
            job_title: Название вакансии
            job_description: Описание вакансии
            required_skills: Список требуемых навыков из вакансии
            min_experience_months: Минимальный требуемый опыт в месяцах
            education_level: Требуемый уровень образования
            candidate_skills: Предварительно извлеченные навыки из резюме
            candidate_experience: Предварительно извлеченные данные об опыте
            candidate_education: Предварительно извлеченные данные об образовании

        Returns:
            ATSScoreResult с комплексной оценкой ATS
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


class SimpleATSChecker:
    """
    Упрощенный проверщик ATS, не требующий API LLM.

    Этот проверщик использует сопоставление на основе правил как запасной вариант,
    когда API LLM недоступны или не настроены.

    Example:
        >>> checker = SimpleATSChecker()
        >>> result = checker.check_ats(
        ...     resume_text="Python разработчик с опытом Django...",
        ...     job_title="Python Developer",
        ...     required_skills=["Python", "Django"]
        ... )
        >>> print(result.passed)
        True
    """

    def __init__(self, threshold: float = 0.5):
        """
        Инициализация упрощенного проверщика ATS.

        Args:
            threshold: Минимальное отношение совпадения для прохода (0-1)
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
        Выполнить проверку ATS на основе правил.

        Args:
            resume_text: Полный текст резюме
            job_title: Название вакансии
            job_description: Описание вакансии
            required_skills: Список требуемых навыков
            candidate_skills: Предварительно извлеченные навыки (если None, будут извлечены)

        Returns:
            ATSScoreResult с оценкой на основе правил
        """
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


# Singleton instance / Одиночный экземпляр
_default_simulator: Optional[ATSSimulator] = None
_default_checker: Optional[SimpleATSChecker] = None


def get_ats_simulator() -> Optional[ATSSimulator]:
    """
    Получить или создать экземпляр симулятора ATS по умолчанию.

    Возвращает None, если API LLM не настроен.
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
    """Получить или создать экземпляр упрощенного проверщика ATS по умолчанию."""
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
    Функция удобства для оценки резюме относительно вакансии.

    Автоматически переходит на проверку на основе правил, если LLM не настроен.

    Args:
        resume_text: Полный текст резюме
        job_title: Название вакансии
        job_description: Описание вакансии
        required_skills: Список требуемых навыков
        use_llm: Предпочитать оценку на основе LLM, если доступно

    Returns:
        ATSScoreResult с результатами оценки
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
