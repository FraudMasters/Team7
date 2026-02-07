"""
ATS (Applicant Tracking System) Simulation endpoints.

# Русский комментарий:
Этот модуль предоставляет эндпоинты для LLM-оценки резюме относительно вакансий,
аналогично тому, как это работают коммерческие ATS-системы.
"""
import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from analyzers.ats_simulation import (
    evaluate_resume_ats,
    get_ats_simulator,
    get_simple_ats_checker,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class ATSEvaluationRequest(BaseModel):
    """Модель запроса для оценки ATS."""
    resume_text: str = Field(..., description="Текст резюме для оценки", min_length=10)
    job_title: str = Field(..., description="Название вакансии", min_length=1)
    job_description: str = Field(
        default="",
        description="Описание вакансии",
    )
    required_skills: List[str] = Field(
        default_factory=list,
        description="Список требуемых навыков",
    )
    use_llm: bool = Field(
        default=True,
        description="Использовать оценку на основе LLM, если доступно (переход к правилам, если нет)",
    )


class ATSEvaluationByIdRequest(BaseModel):
    """Модель запроса для оценки ATS по ID резюме и вакансии."""
    resume_id: str = Field(..., description="ID резюме для оценки")
    vacancy_id: str = Field(..., description="ID вакансии для оценки")
    use_llm: bool = Field(
        default=True,
        description="Использовать оценку на основе LLM, если доступно",
    )


class ATSEvaluationResponse(BaseModel):
    """Модель ответа для оценки ATS."""
    passed: bool = Field(..., description="Прошло ли резюме пороговое значение ATS")
    overall_score: float = Field(..., description="Комплексная оценка ATS (0-1)")
    keyword_score: float = Field(..., description="Оценка сопоставления ключевых слов (0-1)")
    experience_score: float = Field(..., description="Оценка релевантности опыта (0-1)")
    education_score: float = Field(..., description="Оценка соответствия образования (0-1)")
    fit_score: float = Field(..., description="Общая оценка соответствия (0-1)")
    looks_professional: bool = Field(..., description="Проверка профессионального формата")
    disqualified: bool = Field(..., description="Наличие дисквалифицирующих проблем")
    visual_issues: List[str] = Field(default_factory=list, description="Визуальные проблемы")
    ats_issues: List[str] = Field(default_factory=list, description="Проблемы ATS")
    missing_keywords: List[str] = Field(default_factory=list, description="Отсутствующие ключевые слова")
    suggestions: List[str] = Field(default_factory=list, description="Предложения по улучшению")
    feedback: str = Field(..., description="Подробная обратная связь")
    provider: str = Field(..., description="Используемый провайдер LLM")
    model: str = Field(..., description="Использованная модель")
    processing_time_ms: float = Field(..., description="Время обработки")


class BatchATSEvaluationRequest(BaseModel):
    """Модель запроса для пакетной оценки ATS."""
    job_title: str = Field(..., description="Название вакансии", min_length=1)
    job_description: str = Field(default="", description="Описание вакансии")
    required_skills: List[str] = Field(
        default_factory=list,
        description="Список требуемых навыков",
    )
    resume_texts: List[str] = Field(..., description="Список текстов резюме для оценки")
    use_llm: bool = Field(
        default=True,
        description="Использовать оценку на основе LLM, если доступно",
    )


@router.post(
    "/simulate",
    response_model=ATSEvaluationResponse,
    status_code=status.HTTP_200_OK,
    tags=["ATS Simulation"],
)
async def simulate_ats_endpoint(
    request: Request,
    evaluation_request: ATSEvaluationRequest,
) -> JSONResponse:
    """
    Оценить резюме относительно вакансии с использованием симуляции ATS.

    Этот эндпоинт выполняет комплексную оценку ATS с использованием:
    1. Оценки на основе LLM (если настроен API ключ) - более точная
    2. Оценки на основе правил (запасной вариант) - быстрее, но менее сложная

    Оценка ATS включает:
    - **keyword_score**: Насколько хорошо резюме содержит требуемые навыки
    - **experience_score**: Релевантность и достаточность опыта
    - **education_score**: Насколько хорошо образование соответствует требованиям
    - **fit_score**: Общая оценка соответствия кандидата

    Args:
        request: Объект запроса FastAPI
        evaluation_request: Запрос оценки ATS с текстом резюме и данными о вакансии

    Returns:
        JSON ответ с комплексными результатами оценки ATS

    Raises:
        HTTPException(500): Если оценка не удалась

    Examples:
        >>> import requests
        >>> data = {
        ...     "resume_text": "Experienced Python developer with Django knowledge...",
        ...     "job_title": "Senior Python Developer",
        ...     "job_description": "Looking for senior Python developer...",
        ...     "required_skills": ["Python", "Django", "PostgreSQL"],
        ...     "use_llm": True
        ... }
        >>> response = requests.post("/api/ats/simulate", json=data)
        >>> response.json()
        {
            "passed": True,
            "overall_score": 0.75,
            "keyword_score": 0.8,
            "experience_score": 0.7,
            "education_score": 0.8,
            "fit_score": 0.7,
            "looks_professional": True,
            "disqualified": False,
            "visual_issues": [],
            "ats_issues": [],
            "missing_keywords": ["Docker"],
            "suggestions": ["Add Docker experience"],
            "feedback": "Strong candidate with relevant experience...",
            "provider": "zai",
            "model": "glm-4.7",
            "processing_time_ms": 1250.5
        }
    """
    start_time = time.time()

    try:
        logger.info(
            f"Оценка ATS для резюме (длина: {len(evaluation_request.resume_text)}) "
            f"против вакансии '{evaluation_request.job_title}'"
        )

        # Perform ATS evaluation
        ats_result = await evaluate_resume_ats(
            resume_text=evaluation_request.resume_text,
            job_title=evaluation_request.job_title,
            job_description=evaluation_request.job_description,
            required_skills=evaluation_request.required_skills,
            use_llm=evaluation_request.use_llm,
        )

        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000

        # Build response
        response_data = {
            **ats_result.to_dict(),
            "processing_time_ms": round(processing_time_ms, 2),
        }

        logger.info(
            f"ATS evaluation completed: passed={ats_result.passed}, "
            f"score={ats_result.overall_score:.2f}, "
            f"provider={ats_result.provider}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in ATS evaluation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ATS evaluation failed: {str(e)}",
        ) from e


@router.post(
    "/evaluate",
    response_model=ATSEvaluationResponse,
    status_code=status.HTTP_200_OK,
    tags=["ATS Simulation"],
)
async def evaluate_ats_by_id_endpoint(
    request: Request,
    evaluation_request: ATSEvaluationByIdRequest,
) -> JSONResponse:
    """
    Оценить резюме относительно вакансии по ID (заглушка для будущего gRPC вызова).

    Этот эндпоинт предназначен для оценки ATS, когда резюме и вакансия
    получены из других микросервисов через gRPC.

    В настоящее время возвращает заглушку с данными запроса. Полная реализация
    будет добавлена после интеграции с Resume Processing Service и Vacancy Service.

    Args:
        request: Объект запроса FastAPI
        evaluation_request: Запрос с resume_id и vacancy_id

    Returns:
        JSON ответ с результатами оценки ATS

    Note:
        В будущей версии этот эндпоинт будет:
        1. Вызывать Resume Processing Service для получения текста резюме
        2. Вызывать Vacancy Service для получения деталей вакансии
        3. Выполнять оценку ATS
        4. Сохранять результаты в базе данных
    """
    start_time = time.time()

    try:
        logger.info(
            f"ATS evaluation requested for resume_id={evaluation_request.resume_id}, "
            f"vacancy_id={evaluation_request.vacancy_id}"
        )

        # TODO: Implement gRPC calls to fetch resume and vacancy data
        # For now, return a mock response
        processing_time_ms = (time.time() - start_time) * 1000

        response_data = {
            "passed": False,
            "overall_score": 0.0,
            "keyword_score": 0.0,
            "experience_score": 0.0,
            "education_score": 0.0,
            "fit_score": 0.0,
            "looks_professional": True,
            "disqualified": False,
            "visual_issues": ["gRPC integration not yet implemented"],
            "ats_issues": [],
            "missing_keywords": [],
            "suggestions": ["Implement gRPC client to fetch resume and vacancy data"],
            "feedback": "This endpoint is a placeholder. Use /api/ats/simulate with direct resume text.",
            "provider": "mock",
            "model": "v1.0",
            "processing_time_ms": round(processing_time_ms, 2),
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error in ATS evaluation by ID: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ATS evaluation failed: {str(e)}",
        ) from e


@router.post(
    "/batch-simulate",
    status_code=status.HTTP_200_OK,
    tags=["ATS Simulation"],
)
async def batch_simulate_ats(
    request: BatchATSEvaluationRequest,
) -> JSONResponse:
    """
    Оценить несколько резюме относительно одной вакансии.

    Args:
        request: Запрос пакетной оценки с vacancy_id и списком текстов резюме

    Returns:
        JSON ответ со списком результатов оценки ATS

    Raises:
        HTTPException(500): Если оценка не удалась

    Examples:
        >>> import requests
        >>> data = {
        ...     "job_title": "Python Developer",
        ...     "job_description": "Looking for Python developer...",
        ...     "required_skills": ["Python", "Django"],
        ...     "resume_texts": ["Resume 1 text...", "Resume 2 text..."],
        ...     "use_llm": True
        ... }
        >>> response = requests.post("/api/ats/batch-simulate", json=data)
        >>> response.json()
        {
            "job_title": "Python Developer",
            "results": [
                {"passed": True, "overall_score": 0.75, ...},
                {"passed": False, "overall_score": 0.45, ...}
            ],
            "total_count": 2,
            "passed_count": 1,
            "processing_time_ms": 3500.5
        }
    """
    start_time = time.time()

    try:
        logger.info(f"Batch ATS evaluation for {len(request.resume_texts)} resumes against vacancy '{request.job_title}'")

        # Check which LLM method to use
        simulator = get_ats_simulator() if request.use_llm else None
        checker = get_simple_ats_checker() if not simulator else None

        if not simulator and not checker:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LLM API not configured and rule-based checker unavailable",
            )

        results = []
        passed_count = 0

        # Evaluate each resume
        for i, resume_text in enumerate(request.resume_texts):
            try:
                if simulator:
                    ats_result = await simulator.evaluate_ats(
                        resume_text=resume_text,
                        job_title=request.job_title,
                        job_description=request.job_description,
                        required_skills=request.required_skills,
                    )
                else:
                    ats_result = checker.check_ats(
                        resume_text=resume_text,
                        job_title=request.job_title,
                        job_description=request.job_description,
                        required_skills=request.required_skills,
                    )

                if ats_result.passed:
                    passed_count += 1

                results.append({
                    "resume_index": i,
                    **ats_result.to_dict(),
                })

            except Exception as e:
                logger.error(f"Error evaluating resume {i}: {e}")
                results.append({
                    "resume_index": i,
                    "error": str(e),
                    "passed": False,
                    "overall_score": 0.0,
                })

        processing_time_ms = (time.time() - start_time) * 1000

        # Sort by overall score descending
        for r in results:
            if "error" not in r:
                r["overall_score"] = round(r.get("overall_score", 0), 4)
        results.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

        response_data = {
            "job_title": request.job_title,
            "results": results,
            "total_count": len(results),
            "passed_count": passed_count,
            "processing_time_ms": round(processing_time_ms, 2),
        }

        logger.info(
            f"Batch ATS evaluation completed: {passed_count}/{len(results)} passed, "
            f"time={processing_time_ms:.2f}ms"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch ATS evaluation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch ATS evaluation failed: {str(e)}",
        ) from e


@router.get(
    "/config",
    tags=["ATS Simulation"],
)
async def get_ats_config() -> JSONResponse:
    """
    Получить текущую конфигурацию симуляции ATS.

    Возвращает информацию о:
    - Доступных провайдерах LLM
    - Настроенном провайдере
    - Модели по умолчанию
    - Настройках порога ATS

    Examples:
        >>> import requests
        >>> response = requests.get("/api/ats/config")
        >>> response.json()
        {
            "llm_configured": true,
            "provider": "zai",
            "model": "glm-4.7",
            "threshold": 0.6,
            "weights": {
                "keyword": 0.3,
                "experience": 0.3,
                "education": 0.2,
                "fit": 0.2
            }
        }
    """
    from config import get_settings

    settings = get_settings()
    simulator = get_ats_simulator()

    response_data = {
        "llm_configured": simulator is not None,
        "provider": settings.llm_provider,
        "model": settings.llm_model,
        "threshold": settings.ats_threshold,
        "weights": {
            "keyword": settings.ats_keyword_weight,
            "experience": settings.ats_experience_weight,
            "education": settings.ats_education_weight,
            "fit": settings.ats_fit_weight,
        },
        "visual_check_enabled": settings.ats_visual_check_enabled,
    }

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=response_data,
    )
