"""
Эндпоинты аналитики и отчетности.

# Русский комментарий:
Этот модуль предоставляет эндпоинты для получения метрик аналитики найма,
включая статистику времени найма, метрики обработки резюме, показатели совпадения
и другие ключевые индикаторы эффективности процесса рекрутинга.
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class TimeToHireMetrics(BaseModel):
    """Метрики производительности времени найма."""

    average_days: float = Field(..., description="Среднее время найма в днях")
    median_days: float = Field(..., description="Медианное время найма в днях")
    min_days: int = Field(..., description="Минимальное время найма в днях")
    max_days: int = Field(..., description="Максимальное время найма в днях")
    percentile_25: float = Field(..., description="25-й перцентиль времени найма в днях")
    percentile_75: float = Field(..., description="75-й перцентиль времени найма в днях")


class ResumeMetrics(BaseModel):
    """Метрики обработки резюме."""

    total_processed: int = Field(..., description="Общее количество обработанных резюме")
    processed_this_month: int = Field(..., description="Резюме, обработанные за этот месяц")
    processed_this_week: int = Field(..., description="Резюме, обработанные за эту неделю")
    processing_rate_avg: float = Field(..., description="Средняя скорость обработки (резюме в день)")


class MatchRateMetrics(BaseModel):
    """Метрики производительности сопоставления навыков."""

    overall_match_rate: float = Field(..., description="Общий показатель совпадения навыков (0-1)")
    high_confidence_matches: int = Field(..., description="Количество совпадений с высокой уверенностью (>0.8)")
    low_confidence_matches: int = Field(..., description="Количество совпадений с низкой уверенностью (<0.5)")
    average_confidence: float = Field(..., description="Средний показатель уверенности по всем совпадениям (0-1)")


class KeyMetricsResponse(BaseModel):
    """Модель ответа для ключевых метрик аналитики."""

    time_to_hire: TimeToHireMetrics = Field(..., description="Метрики производительности времени найма")
    resumes: ResumeMetrics = Field(..., description="Метрики обработки резюме")
    match_rates: MatchRateMetrics = Field(..., description="Метрики сопоставления навыков")


@router.get(
    "/key-metrics",
    response_model=KeyMetricsResponse,
    tags=["Analytics"],
)
async def get_key_metrics(
    start_date: Optional[str] = Query(None, description="Фильтр начальной даты (формат ISO 8601)"),
    end_date: Optional[str] = Query(None, description="Фильтр конечной даты (формат ISO 8601)"),
) -> JSONResponse:
    """
    Получить ключевые метрики аналитики рекрутинга.

    Этот эндпоинт предоставляет основные метрики для мониторинга производительности рекрутинга,
    включая статистику времени найма, метрики обработки резюме и показатели совпадения навыков.
    Эти метрики помогают рекрутерам оптимизировать процесс найма и выявлять области для улучшения.

    Args:
        start_date: Опциональная начальная дата для фильтрации метрик (формат ISO 8601)
        end_date: Опциональная конечная дата для фильтрации метрик (формат ISO 8601)

    Returns:
        JSON ответ с ключевыми метриками, включая время найма, обработанные резюме и показатели совпадения

    Raises:
        HTTPException(500): Если не удалось получить данные

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8006/api/analytics/key-metrics")
        >>> response.json()
        {
            "time_to_hire": {
                "average_days": 32.5,
                "median_days": 28.0,
                "min_days": 7,
                "max_days": 90,
                "percentile_25": 21.0,
                "percentile_75": 45.0
            },
            "resumes": {
                "total_processed": 1250,
                "processed_this_month": 180,
                "processed_this_week": 42,
                "processing_rate_avg": 8.5
            },
            "match_rates": {
                "overall_match_rate": 0.78,
                "high_confidence_matches": 890,
                "low_confidence_matches": 156,
                "average_confidence": 0.72
            }
        }
    """
    try:
        logger.info(
            f"Получение ключевых метрик - start_date: {start_date}, end_date: {end_date}"
        )

        # Возвращаем placeholder ответ
        # Интеграция с базой данных будет добавлена в последующем подзадаче
        response_data = {
            "time_to_hire": {
                "average_days": 32.5,
                "median_days": 28.0,
                "min_days": 7,
                "max_days": 90,
                "percentile_25": 21.0,
                "percentile_75": 45.0,
            },
            "resumes": {
                "total_processed": 1250,
                "processed_this_month": 180,
                "processed_this_week": 42,
                "processing_rate_avg": 8.5,
            },
            "match_rates": {
                "overall_match_rate": 0.78,
                "high_confidence_matches": 890,
                "low_confidence_matches": 156,
                "average_confidence": 0.72,
            },
        }

        logger.info("Ключевые метрики успешно получены")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Ошибка получения ключевых метрик: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить ключевые метрики: {str(e)}",
        ) from e


class QualityMetricsResponse(BaseModel):
    """Метрики качества ML/NLP моделей."""

    # Метрики извлечения текста
    text_extraction_success_rate: float = Field(..., description="Успешность извлечения текста (0-1)")
    avg_extraction_time_seconds: float = Field(..., description="Среднее время извлечения текста")

    # Метрики NER
    ner_accuracy: float = Field(..., description="Точность NER (F1-мера определения сущностей)")
    entities_per_resume_avg: float = Field(..., description="Среднее количество определенных сущностей в резюме")

    # Метрики извлечения ключевых слов
    avg_keywords_per_resume: float = Field(..., description="Среднее количество извлеченных ключевых слов в резюме")
    keyword_relevance_avg: float = Field(..., description="Средняя оценка релевантности ключевых слов (0-1)")

    # Метрики грамматики
    grammar_error_rate: float = Field(..., description="Резюме с грамматическими ошибками (0-1)")

    # Метрики сопоставления
    matching_confidence_avg: float = Field(..., description="Средняя оценка уверенности сопоставления (0-1)")
    matching_precision: float = Field(..., description="Точность сопоставления (проверенные совпадения)")
    matching_recall: float = Field(..., description="Полнота сопоставления (найденные релевантные кандидаты)")

    # Метрики производительности
    avg_analysis_time_seconds: float = Field(..., description="Среднее время анализа резюме")
    error_rate: float = Field(..., description="Уровень ошибок анализа (0-1)")

    # Сводка
    total_analyzed: int = Field(..., description="Общее количество проанализированных резюме")


@router.get(
    "/quality-metrics",
    response_model=QualityMetricsResponse,
    tags=["Analytics"],
)
async def get_quality_metrics(
    start_date: Optional[str] = Query(None, description="Фильтр начальной даты (формат ISO 8601)"),
    end_date: Optional[str] = Query(None, description="Фильтр конечной даты (формат ISO 8601)"),
) -> JSONResponse:
    """
    Получить метрики качества ML/NLP моделей.

    Этот эндпоинт предоставляет метрики о качестве и производительности ML/NLP моделей,
    используемых для анализа резюме, включая извлечение текста, NER, извлечение ключевых слов и сопоставление.

    Returns:
        JSON ответ с метриками качества для всех компонентов ML/NLP

    Raises:
        HTTPException(500): Если не удалось получить метрики

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8006/api/analytics/quality-metrics")
        >>> response.json()
        {
            "text_extraction_success_rate": 0.98,
            "avg_extraction_time_seconds": 1.2,
            "ner_accuracy": 0.92,
            "entities_per_resume_avg": 15.3,
            "avg_keywords_per_resume": 8.5,
            "keyword_relevance_avg": 0.78,
            "grammar_error_rate": 0.35,
            "matching_confidence_avg": 0.75,
            "matching_precision": 0.87,
            "matching_recall": 0.82,
            "avg_analysis_time_seconds": 12.5,
            "error_rate": 0.02
        }
    """
    try:
        logger.info(
            f"Получение метрик качества - start_date: {start_date}, end_date: {end_date}"
        )

        # Возвращаем placeholder ответ
        # Интеграция с базой данных будет добавлена в последующем подзадаче
        response_data = {
            "text_extraction_success_rate": 0.98,
            "avg_extraction_time_seconds": 1.2,
            "ner_accuracy": 0.92,
            "entities_per_resume_avg": 15.3,
            "avg_keywords_per_resume": 8.5,
            "keyword_relevance_avg": 0.78,
            "grammar_error_rate": 0.35,
            "matching_confidence_avg": 0.75,
            "matching_precision": 0.87,
            "matching_recall": 0.82,
            "avg_analysis_time_seconds": 12.5,
            "error_rate": 0.02,
            "total_analyzed": 1250,
        }

        logger.info("Метрики качества успешно получены")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Ошибка получения метрик качества: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить метрики качества: {str(e)}",
        ) from e


class DashboardMetrics(BaseModel):
    """Сводные метрики для дашборда."""

    total_resumes: int = Field(..., description="Общее количество резюме в системе")
    active_candidates: int = Field(..., description="Количество активных кандидатов")
    open_vacancies: int = Field(..., description="Количество открытых вакансий")
    interviews_scheduled: int = Field(..., description="Количество запланированных собеседований")
    offers_extended: int = Field(..., description="Количество отправленных предложений")
    hires_this_month: int = Field(..., description="Количество наймов в этом месяце")
    avg_time_to_hire: float = Field(..., description="Среднее время найма в днях")


@router.get(
    "/dashboard",
    response_model=DashboardMetrics,
    tags=["Analytics"],
)
async def get_dashboard_metrics() -> JSONResponse:
    """
    Получить сводные метрики для дашборда.

    Этот эндпоинт предоставляет агрегированные метрики для отображения
    на главном дашборде системы, включая общую статистику по резюме,
    кандидатам, вакансиям и наймам.

    Returns:
        JSON ответ со сводными метриками дашборда

    Raises:
        HTTPException(500): Если не удалось получить метрики

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8006/api/analytics/dashboard")
        >>> response.json()
        {
            "total_resumes": 1250,
            "active_candidates": 450,
            "open_vacancies": 25,
            "interviews_scheduled": 42,
            "offers_extended": 12,
            "hires_this_month": 8,
            "avg_time_to_hire": 28.5
        }
    """
    try:
        logger.info("Получение метрик дашборда")

        # Возвращаем placeholder ответ
        # Интеграция с базой данных и gRPC клиентами будет добавлена в последующем подзадаче
        response_data = {
            "total_resumes": 1250,
            "active_candidates": 450,
            "open_vacancies": 25,
            "interviews_scheduled": 42,
            "offers_extended": 12,
            "hires_this_month": 8,
            "avg_time_to_hire": 28.5,
        }

        logger.info("Метрики дашборда успешно получены")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Ошибка получения метрик дашборда: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить метрики дашборда: {str(e)}",
        ) from e


class TaxonomyUsageStats(BaseModel):
    """Статистика использования таксономии."""

    taxonomy_id: str = Field(..., description="ID таксономии")
    taxonomy_name: str = Field(..., description="Название таксономии")
    usage_count: int = Field(..., description="Количество использований")
    avg_match_score: float = Field(..., description="Средний показатель совпадения")
    success_rate: float = Field(..., description="Уровень успеха (0-1)")
    total_candidates_matched: int = Field(..., description="Общее количество подобранных кандидатов")
    industry: Optional[str] = Field(None, description="Индустрия")


class TaxonomyUsageResponse(BaseModel):
    """Модель ответа для аналитики использования таксономии."""

    most_used_taxonomies: list[TaxonomyUsageStats] = Field(..., description="Наиболее используемые таксономии")
    most_effective_taxonomies: list[TaxonomyUsageStats] = Field(..., description="Наиболее эффективные таксономии")
    industry_filter: Optional[str] = Field(None, description="Примененный фильтр индустрии")
    total_taxonomies_analyzed: int = Field(..., description="Общее количество проанализированных таксономий")


@router.get(
    "/taxonomy-usage",
    response_model=TaxonomyUsageResponse,
    tags=["Analytics"],
)
async def get_taxonomy_usage(
    industry: Optional[str] = Query(None, description="Фильтр по индустрии"),
    limit: int = Query(10, ge=1, le=100, description="Максимальное количество результатов"),
) -> JSONResponse:
    """
    Получить аналитику использования таксономии.

    Этот эндпоинт предоставляет аналитику об использовании таксономии индустрии,
    включая то, какие таксономии наиболее используются и наиболее эффективны
    для подбора кандидатов.

    Args:
        industry: Опциональный фильтр по индустрии
        limit: Максимальное количество таксономий для возврата

    Returns:
        JSON ответ со статистикой использования таксономии

    Raises:
        HTTPException(500): Если не удалось получить данные

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8006/api/analytics/taxonomy-usage?limit=10")
        >>> response.json()
        {
            "most_used_taxonomies": [...],
            "most_effective_taxonomies": [...],
            "industry_filter": null,
            "total_taxonomies_analyzed": 25
        }
    """
    try:
        logger.info(f"Получение статистики использования таксономии - industry: {industry}, limit: {limit}")

        response_data = {
            "most_used_taxonomies": [
                {
                    "taxonomy_id": "tax-001",
                    "taxonomy_name": "Technology",
                    "usage_count": 125,
                    "avg_match_score": 72.5,
                    "success_rate": 0.78,
                    "total_candidates_matched": 625,
                    "industry": "technology",
                }
            ],
            "most_effective_taxonomies": [
                {
                    "taxonomy_id": "tax-001",
                    "taxonomy_name": "Technology",
                    "usage_count": 125,
                    "avg_match_score": 78.5,
                    "success_rate": 0.85,
                    "total_candidates_matched": 625,
                    "industry": "technology",
                }
            ],
            "industry_filter": industry,
            "total_taxonomies_analyzed": 25,
        }

        logger.info("Статистика использования таксономии успешно получена")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Ошибка получения статистики использования таксономии: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить статистику использования таксономии: {str(e)}",
        ) from e


class StageDurationMetrics(BaseModel):
    """Метрики длительности этапов."""

    stage_name: str = Field(..., description="Название этапа найма")
    average_days: float = Field(..., description="Среднее время нахождения кандидатов на этом этапе (дни)")
    median_days: float = Field(..., description="Медианное время нахождения кандидатов на этом этапе (дни)")
    min_days: float = Field(..., description="Минимальное время на этом этапе (дни)")
    max_days: float = Field(..., description="Максимальное время на этом этапе (дни)")
    candidate_count: int = Field(..., description="Количество кандидатов, прошедших этот этап")


class StageDurationResponse(BaseModel):
    """Модель ответа для аналитики длительности этапов."""

    stages: list[StageDurationMetrics] = Field(..., description="Метрики длительности для каждого этапа найма")


@router.get(
    "/stage-duration",
    response_model=StageDurationResponse,
    tags=["Analytics"],
)
async def get_stage_duration_metrics(
    start_date: Optional[str] = Query(None, description="Фильтр начальной даты (формат ISO 8601)"),
    end_date: Optional[str] = Query(None, description="Фильтр конечной даты (формат ISO 8601)"),
) -> JSONResponse:
    """
    Получить метрики длительности этапов.

    Этот эндпоинт предоставляет метрики о том, сколько времени кандидаты
    проводят на каждом этапе найма, помогая организациям выявлять узкие места
    и оптимизировать процесс рекрутинга. Метрики включают среднее, медианное,
    минимальное и максимальное время для каждого этапа.

    Args:
        start_date: Опциональная начальная дата для фильтрации метрик (формат ISO 8601)
        end_date: Опциональная конечная дата для фильтрации метрик (формат ISO 8601)

    Returns:
        JSON ответ с метриками длительности для каждого этапа найма

    Raises:
        HTTPException(500): Если не удалось получить метрики

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8006/api/analytics/stage-duration")
        >>> response.json()
        {
            "stages": [
                {
                    "stage_name": "applied",
                    "average_days": 2.5,
                    "median_days": 2.0,
                    "min_days": 0.5,
                    "max_days": 7.0,
                    "candidate_count": 150
                },
                {
                    "stage_name": "screening",
                    "average_days": 5.2,
                    "median_days": 4.0,
                    "min_days": 1.0,
                    "max_days": 14.0,
                    "candidate_count": 120
                }
            ]
        }
    """
    try:
        logger.info(
            f"Получение метрик длительности этапов - start_date: {start_date}, end_date: {end_date}"
        )

        # Возвращаем placeholder ответ
        response_data = {
            "stages": [
                {
                    "stage_name": "applied",
                    "average_days": 2.5,
                    "median_days": 2.0,
                    "min_days": 0.5,
                    "max_days": 7.0,
                    "candidate_count": 150,
                },
                {
                    "stage_name": "screening",
                    "average_days": 5.2,
                    "median_days": 4.0,
                    "min_days": 1.0,
                    "max_days": 14.0,
                    "candidate_count": 120,
                },
            ]
        }

        logger.info("Метрики длительности этапов успешно получены")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Ошибка получения метрик длительности этапов: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить метрики длительности этапов: {str(e)}",
        ) from e


class FunnelStageMetrics(BaseModel):
    """Метрики этапов воронки найма."""

    stage_name: str = Field(..., description="Название этапа найма")
    count: int = Field(..., description="Количество кандидатов на этом этапе")
    conversion_rate_from_previous: Optional[float] = Field(
        None, description="Коэффициент конверсии с предыдущего этапа (0-1)"
    )
    conversion_rate_from_start: float = Field(
        ..., description="Коэффициент конверсии с начального этапа (0-1)"
    )


class FunnelMetricsResponse(BaseModel):
    """Модель ответа для метрик воронки найма."""

    stages: list[FunnelStageMetrics] = Field(..., description="Метрики воронки для каждого этапа")
    total_candidates: int = Field(..., description="Общее количество кандидатов в воронке")


@router.get(
    "/funnel",
    response_model=FunnelMetricsResponse,
    tags=["Analytics"],
)
async def get_funnel_metrics(
    start_date: Optional[str] = Query(None, description="Фильтр начальной даты (формат ISO 8601)"),
    end_date: Optional[str] = Query(None, description="Фильтр конечной даты (формат ISO 8601)"),
) -> JSONResponse:
    """
    Получить метрики визуализации воронки найма.

    Этот эндпоинт предоставляет визуальное представление воронки найма,
    показывая количество кандидатов на каждом этапе и коэффициенты конверсии
    между этапами. Это помогает выявить узкие места в процессе рекрутинга
    и оптимизировать стратегии конверсии.

    Этапы воронки включают:
    - uploaded: Загруженные резюме в систему
    - analyzed: Резюме, обработанные через анализ NLP
    - screening: Кандидаты на первичном отсмотре
    - interview: Кандидаты на собеседовании
    - technical: Кандидаты на технической оценке
    - offer: Кандидаты, получившие предложение
    - hired: Успешно нанятые кандидаты

    Args:
        start_date: Опциональная начальная дата для фильтрации метрик (формат ISO 8601)
        end_date: Опциональная конечная дата для фильтрации метрик (формат ISO 8601)

    Returns:
        JSON ответ с метриками воронки, включая количество этапов и коэффициенты конверсии

    Raises:
        HTTPException(500): Если не удалось получить данные

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8006/api/analytics/funnel")
        >>> response.json()
        {
            "stages": [
                {
                    "stage_name": "uploaded",
                    "count": 500,
                    "conversion_rate_from_previous": null,
                    "conversion_rate_from_start": 1.0
                },
                {
                    "stage_name": "analyzed",
                    "count": 450,
                    "conversion_rate_from_previous": 0.9,
                    "conversion_rate_from_start": 0.9
                },
                {
                    "stage_name": "hired",
                    "count": 50,
                    "conversion_rate_from_previous": 0.33,
                    "conversion_rate_from_start": 0.1
                }
            ],
            "total_candidates": 500
        }
    """
    try:
        logger.info(
            f"Получение метрик воронки - start_date: {start_date}, end_date: {end_date}"
        )

        # Возвращаем placeholder ответ
        response_data = {
            "stages": [
                {
                    "stage_name": "uploaded",
                    "count": 500,
                    "conversion_rate_from_previous": None,
                    "conversion_rate_from_start": 1.0,
                },
                {
                    "stage_name": "analyzed",
                    "count": 450,
                    "conversion_rate_from_previous": 0.9,
                    "conversion_rate_from_start": 0.9,
                },
                {
                    "stage_name": "screening",
                    "count": 300,
                    "conversion_rate_from_previous": 0.67,
                    "conversion_rate_from_start": 0.6,
                },
                {
                    "stage_name": "interview",
                    "count": 150,
                    "conversion_rate_from_previous": 0.5,
                    "conversion_rate_from_start": 0.3,
                },
                {
                    "stage_name": "hired",
                    "count": 50,
                    "conversion_rate_from_previous": 0.33,
                    "conversion_rate_from_start": 0.1,
                },
            ],
            "total_candidates": 500,
        }

        logger.info("Метрики воронки успешно получены")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Ошибка получения метрик воронки: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить метрики воронки: {str(e)}",
        ) from e


class SourceMetrics(BaseModel):
    """Метрики эффективности источника."""

    source_name: str = Field(..., description="Название источника кандидатов")
    total_applications: int = Field(..., description="Общее количество заявок из этого источника")
    total_hires: int = Field(..., description="Общее количество наймов из этого источника")
    conversion_rate: float = Field(..., description="Коэффициент конверсии заявок в наймы (0-1)")
    average_quality_score: float = Field(..., description="Средний показатель качества кандидатов (0-100)")
    average_time_to_hire_days: float = Field(..., description="Среднее время найма из этого источника (дни)")
    cost_per_hire: Optional[float] = Field(None, description="Стоимость найма одного кандидата")


class SourceEffectivenessResponse(BaseModel):
    """Модель ответа для аналитики эффективности источников."""

    sources: list[SourceMetrics] = Field(..., description="Метрики эффективности для каждого источника")
    total_sources: int = Field(..., description="Общее количество источников")
    best_conversion_source: Optional[str] = Field(None, description="Источник с лучшей конверсией")
    best_quality_source: Optional[str] = Field(None, description="Источник с лучшим качеством кандидатов")


@router.get(
    "/source-effectiveness",
    response_model=SourceEffectivenessResponse,
    tags=["Analytics"],
)
async def get_source_effectiveness(
    start_date: Optional[str] = Query(None, description="Фильтр начальной даты (формат ISO 8601)"),
    end_date: Optional[str] = Query(None, description="Фильтр конечной даты (формат ISO 8601)"),
) -> JSONResponse:
    """
    Получить метрики эффективности источников кандидатов.

    Этот эндпоинт предоставляет аналитику об эффективности различных источников
    кандидатов (LinkedIn, Indeed, рефералы и т.д.), включая коэффициенты конверсии,
    показатели качества и стоимость найма. Эти метрики помогают оптимизировать
    инвестиции в каналы найма и сосредоточиться на наиболее эффективных источниках.

    Args:
        start_date: Опциональная начальная дата для фильтрации метрик (формат ISO 8601)
        end_date: Опциональная конечная дата для фильтрации метрик (формат ISO 8601)

    Returns:
        JSON ответ с метриками эффективности для каждого источника кандидатов

    Raises:
        HTTPException(500): Если не удалось получить данные

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8006/api/analytics/source-effectiveness")
        >>> response.json()
        {
            "sources": [
                {
                    "source_name": "LinkedIn",
                    "total_applications": 250,
                    "total_hires": 35,
                    "conversion_rate": 0.14,
                    "average_quality_score": 78.5,
                    "average_time_to_hire_days": 28.3,
                    "cost_per_hire": 1250.0
                },
                {
                    "source_name": "Referrals",
                    "total_applications": 120,
                    "total_hires": 28,
                    "conversion_rate": 0.23,
                    "average_quality_score": 85.2,
                    "average_time_to_hire_days": 21.5,
                    "cost_per_hire": 500.0
                }
            ],
            "total_sources": 5,
            "best_conversion_source": "Referrals",
            "best_quality_source": "Referrals"
        }
    """
    try:
        logger.info(
            f"Получение метрик эффективности источников - start_date: {start_date}, end_date: {end_date}"
        )

        # Возвращаем placeholder ответ
        # Интеграция с базой данных будет добавлена в последующем подзадаче
        response_data = {
            "sources": [
                {
                    "source_name": "LinkedIn",
                    "total_applications": 250,
                    "total_hires": 35,
                    "conversion_rate": 0.14,
                    "average_quality_score": 78.5,
                    "average_time_to_hire_days": 28.3,
                    "cost_per_hire": 1250.0,
                },
                {
                    "source_name": "Referrals",
                    "total_applications": 120,
                    "total_hires": 28,
                    "conversion_rate": 0.23,
                    "average_quality_score": 85.2,
                    "average_time_to_hire_days": 21.5,
                    "cost_per_hire": 500.0,
                },
                {
                    "source_name": "Indeed",
                    "total_applications": 180,
                    "total_hires": 22,
                    "conversion_rate": 0.12,
                    "average_quality_score": 72.8,
                    "average_time_to_hire_days": 32.1,
                    "cost_per_hire": 980.0,
                },
                {
                    "source_name": "Company Website",
                    "total_applications": 90,
                    "total_hires": 15,
                    "conversion_rate": 0.17,
                    "average_quality_score": 81.3,
                    "average_time_to_hire_days": 25.7,
                    "cost_per_hire": 200.0,
                },
                {
                    "source_name": "Job Boards",
                    "total_applications": 310,
                    "total_hires": 30,
                    "conversion_rate": 0.10,
                    "average_quality_score": 68.9,
                    "average_time_to_hire_days": 35.4,
                    "cost_per_hire": 1100.0,
                },
            ],
            "total_sources": 5,
            "best_conversion_source": "Referrals",
            "best_quality_source": "Referrals",
        }

        logger.info("Метрики эффективности источников успешно получены")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Ошибка получения метрик эффективности источников: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить метрики эффективности источников: {str(e)}",
        ) from e


class FunnelStage(BaseModel):
    """Этап воронки найма с метриками конверсии."""

    stage_name: str = Field(..., description="Название этапа воронки")
    total_candidates: int = Field(..., description="Общее количество кандидатов на этом этапе")
    conversion_rate: float = Field(..., description="Коэффициент конверсии на следующий этап (0-1)")
    dropout_rate: float = Field(..., description="Коэффициент отсева на этом этапе (0-1)")
    average_time_days: float = Field(..., description="Среднее время на этом этапе в днях")


class FunnelConversionResponse(BaseModel):
    """Метрики конверсии воронки найма."""

    stages: list[FunnelStage] = Field(..., description="Список этапов воронки с метриками")
    overall_conversion_rate: float = Field(..., description="Общий коэффициент конверсии от применения до найма (0-1)")
    total_applicants: int = Field(..., description="Общее количество кандидатов, вошедших в воронку")
    total_hires: int = Field(..., description="Общее количество успешных наймов")
    average_funnel_time_days: float = Field(..., description="Среднее время прохождения всей воронки в днях")
    biggest_bottleneck: str = Field(..., description="Этап с наибольшим процентом отсева")


@router.get(
    "/funnel-conversion",
    response_model=FunnelConversionResponse,
    tags=["Analytics"],
)
async def get_funnel_conversion(
    start_date: Optional[str] = Query(None, description="Фильтр начальной даты (формат ISO 8601)"),
    end_date: Optional[str] = Query(None, description="Фильтр конечной даты (формат ISO 8601)"),
) -> JSONResponse:
    """
    Получить метрики конверсии воронки найма.

    Этот эндпоинт предоставляет детальный анализ конверсии кандидатов через различные этапы
    процесса найма, от первоначального применения до окончательного найма. Помогает выявить
    узкие места в процессе рекрутинга и оптимизировать эффективность найма.

    Args:
        start_date: Опциональная начальная дата для фильтрации метрик (формат ISO 8601)
        end_date: Опциональная конечная дата для фильтрации метрик (формат ISO 8601)

    Returns:
        JSON ответ с метриками конверсии по каждому этапу воронки и общей статистикой

    Raises:
        HTTPException(500): Если не удалось получить данные

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8006/api/analytics/funnel-conversion")
        >>> response.json()
        {
            "stages": [
                {
                    "stage_name": "Applied",
                    "total_candidates": 1000,
                    "conversion_rate": 0.60,
                    "dropout_rate": 0.40,
                    "average_time_days": 2.5
                },
                {
                    "stage_name": "Screened",
                    "total_candidates": 600,
                    "conversion_rate": 0.50,
                    "dropout_rate": 0.50,
                    "average_time_days": 5.2
                },
                {
                    "stage_name": "Interviewed",
                    "total_candidates": 300,
                    "conversion_rate": 0.40,
                    "dropout_rate": 0.60,
                    "average_time_days": 8.7
                },
                {
                    "stage_name": "Offered",
                    "total_candidates": 120,
                    "conversion_rate": 0.75,
                    "dropout_rate": 0.25,
                    "average_time_days": 3.1
                },
                {
                    "stage_name": "Hired",
                    "total_candidates": 90,
                    "conversion_rate": 1.0,
                    "dropout_rate": 0.0,
                    "average_time_days": 0.0
                }
            ],
            "overall_conversion_rate": 0.09,
            "total_applicants": 1000,
            "total_hires": 90,
            "average_funnel_time_days": 32.5,
            "biggest_bottleneck": "Interviewed"
        }
    """
    try:
        logger.info(
            f"Получение метрик конверсии воронки - start_date: {start_date}, end_date: {end_date}"
        )

        # Возвращаем placeholder ответ
        # Интеграция с базой данных будет добавлена в последующем подзадаче
        response_data = {
            "stages": [
                {
                    "stage_name": "Applied",
                    "total_candidates": 1000,
                    "conversion_rate": 0.60,
                    "dropout_rate": 0.40,
                    "average_time_days": 2.5,
                },
                {
                    "stage_name": "Screened",
                    "total_candidates": 600,
                    "conversion_rate": 0.50,
                    "dropout_rate": 0.50,
                    "average_time_days": 5.2,
                },
                {
                    "stage_name": "Interviewed",
                    "total_candidates": 300,
                    "conversion_rate": 0.40,
                    "dropout_rate": 0.60,
                    "average_time_days": 8.7,
                },
                {
                    "stage_name": "Offered",
                    "total_candidates": 120,
                    "conversion_rate": 0.75,
                    "dropout_rate": 0.25,
                    "average_time_days": 3.1,
                },
                {
                    "stage_name": "Hired",
                    "total_candidates": 90,
                    "conversion_rate": 1.0,
                    "dropout_rate": 0.0,
                    "average_time_days": 0.0,
                },
            ],
            "overall_conversion_rate": 0.09,
            "total_applicants": 1000,
            "total_hires": 90,
            "average_funnel_time_days": 32.5,
            "biggest_bottleneck": "Interviewed",
        }

        logger.info("Метрики конверсии воронки успешно получены")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Ошибка получения метрик конверсии воронки: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить метрики конверсии воронки: {str(e)}",
        ) from e


class DiversityMetricsResponse(BaseModel):
    """Метрики разнообразия и инклюзивности в процессе найма."""

    # Гендерное разнообразие
    gender_distribution: dict = Field(..., description="Распределение кандидатов по гендеру")
    gender_hire_rate: dict = Field(..., description="Коэффициент найма по гендеру")

    # Возрастное разнообразие
    age_distribution: dict = Field(..., description="Распределение кандидатов по возрастным группам")
    age_hire_rate: dict = Field(..., description="Коэффициент найма по возрастным группам")

    # Этническое разнообразие
    ethnicity_distribution: dict = Field(..., description="Распределение кандидатов по этнической принадлежности")
    ethnicity_hire_rate: dict = Field(..., description="Коэффициент найма по этнической принадлежности")

    # Образовательное разнообразие
    education_distribution: dict = Field(..., description="Распределение кандидатов по уровню образования")
    education_hire_rate: dict = Field(..., description="Коэффициент найма по уровню образования")

    # Метрики инклюзивности
    diversity_index: float = Field(..., description="Индекс разнообразия (0-1, более высокий = более разнообразный)")
    inclusion_score: float = Field(..., description="Оценка инклюзивности (0-1)")
    bias_detection_score: float = Field(..., description="Оценка обнаружения предвзятости (0-1, ниже = меньше предвзятости)")

    # Сводка
    total_candidates: int = Field(..., description="Общее количество кандидатов")
    total_hires: int = Field(..., description="Общее количество нанятых")


@router.get(
    "/diversity-metrics",
    response_model=DiversityMetricsResponse,
    tags=["Analytics"],
)
async def get_diversity_metrics(
    start_date: Optional[str] = Query(None, description="Фильтр начальной даты (формат ISO 8601)"),
    end_date: Optional[str] = Query(None, description="Фильтр конечной даты (формат ISO 8601)"),
) -> JSONResponse:
    """
    Получить метрики разнообразия и инклюзивности в процессе найма.

    Этот эндпоинт предоставляет метрики о разнообразии кандидатов и показатели инклюзивности
    в процессе рекрутинга. Метрики включают гендерное, возрастное и этническое разнообразие,
    а также образовательное разнообразие и оценки предвзятости. Эти данные помогают организациям
    отслеживать и улучшать свои практики DEI (Diversity, Equity, and Inclusion).

    Args:
        start_date: Опциональная начальная дата для фильтрации метрик (формат ISO 8601)
        end_date: Опциональная конечная дата для фильтрации метрик (формат ISO 8601)

    Returns:
        JSON ответ с метриками разнообразия, включая распределение по гендеру, возрасту, этнической принадлежности и образованию

    Raises:
        HTTPException(500): Если не удалось получить данные

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8006/api/analytics/diversity-metrics")
        >>> response.json()
        {
            "gender_distribution": {
                "Male": 450,
                "Female": 420,
                "Non-binary": 80,
                "Prefer not to say": 50
            },
            "gender_hire_rate": {
                "Male": 0.08,
                "Female": 0.09,
                "Non-binary": 0.10,
                "Prefer not to say": 0.06
            },
            "age_distribution": {
                "18-25": 200,
                "26-35": 450,
                "36-45": 250,
                "46-55": 80,
                "56+": 20
            },
            "age_hire_rate": {
                "18-25": 0.07,
                "26-35": 0.10,
                "36-45": 0.08,
                "46-55": 0.06,
                "56+": 0.05
            },
            "ethnicity_distribution": {
                "Asian": 300,
                "Black": 180,
                "Hispanic": 150,
                "White": 320,
                "Other": 50
            },
            "ethnicity_hire_rate": {
                "Asian": 0.09,
                "Black": 0.08,
                "Hispanic": 0.07,
                "White": 0.09,
                "Other": 0.08
            },
            "education_distribution": {
                "High School": 120,
                "Bachelor": 520,
                "Master": 280,
                "PhD": 80
            },
            "education_hire_rate": {
                "High School": 0.05,
                "Bachelor": 0.09,
                "Master": 0.10,
                "PhD": 0.11
            },
            "diversity_index": 0.82,
            "inclusion_score": 0.78,
            "bias_detection_score": 0.15,
            "total_candidates": 1000,
            "total_hires": 90
        }
    """
    try:
        logger.info(
            f"Получение метрик разнообразия - start_date: {start_date}, end_date: {end_date}"
        )

        # Возвращаем placeholder ответ
        # Интеграция с базой данных будет добавлена в последующем подзадаче
        response_data = {
            "gender_distribution": {
                "Male": 450,
                "Female": 420,
                "Non-binary": 80,
                "Prefer not to say": 50,
            },
            "gender_hire_rate": {
                "Male": 0.08,
                "Female": 0.09,
                "Non-binary": 0.10,
                "Prefer not to say": 0.06,
            },
            "age_distribution": {
                "18-25": 200,
                "26-35": 450,
                "36-45": 250,
                "46-55": 80,
                "56+": 20,
            },
            "age_hire_rate": {
                "18-25": 0.07,
                "26-35": 0.10,
                "36-45": 0.08,
                "46-55": 0.06,
                "56+": 0.05,
            },
            "ethnicity_distribution": {
                "Asian": 300,
                "Black": 180,
                "Hispanic": 150,
                "White": 320,
                "Other": 50,
            },
            "ethnicity_hire_rate": {
                "Asian": 0.09,
                "Black": 0.08,
                "Hispanic": 0.07,
                "White": 0.09,
                "Other": 0.08,
            },
            "education_distribution": {
                "High School": 120,
                "Bachelor": 520,
                "Master": 280,
                "PhD": 80,
            },
            "education_hire_rate": {
                "High School": 0.05,
                "Bachelor": 0.09,
                "Master": 0.10,
                "PhD": 0.11,
            },
            "diversity_index": 0.82,
            "inclusion_score": 0.78,
            "bias_detection_score": 0.15,
            "total_candidates": 1000,
            "total_hires": 90,
        }

        logger.info("Метрики разнообразия успешно получены")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Ошибка получения метрик разнообразия: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить метрики разнообразия: {str(e)}",
        ) from e


class BenchmarkComparisonResponse(BaseModel):
    """Метрики сравнения с отраслевыми эталонами."""

    # Время найма
    company_time_to_hire_avg: float = Field(..., description="Среднее время найма компании (дни)")
    industry_time_to_hire_avg: float = Field(..., description="Среднее время найма по отрасли (дни)")
    time_to_hire_percentile: float = Field(..., description="Перцентиль компании по времени найма (0-100)")

    # Скорость обработки резюме
    company_resume_processing_rate: float = Field(..., description="Скорость обработки резюме компании (резюме/день)")
    industry_resume_processing_rate: float = Field(..., description="Скорость обработки резюме по отрасли (резюме/день)")
    processing_rate_percentile: float = Field(..., description="Перцентиль скорости обработки (0-100)")

    # Качество совпадений
    company_match_rate: float = Field(..., description="Показатель совпадений компании (0-1)")
    industry_match_rate: float = Field(..., description="Показатель совпадений по отрасли (0-1)")
    match_rate_percentile: float = Field(..., description="Перцентиль качества совпадений (0-100)")

    # Коэффициенты конверсии
    company_offer_acceptance_rate: float = Field(..., description="Коэффициент принятия предложений компании (0-1)")
    industry_offer_acceptance_rate: float = Field(..., description="Коэффициент принятия предложений по отрасли (0-1)")
    acceptance_rate_percentile: float = Field(..., description="Перцентиль принятия предложений (0-100)")

    # Общая производительность
    overall_performance_score: float = Field(..., description="Общий показатель производительности (0-100)")
    industry_position: str = Field(..., description="Позиция в отрасли (Top 10%, Top 25%, Above Average, Below Average)")
    recommendations: list = Field(..., description="Список рекомендаций по улучшению")


@router.get(
    "/benchmarks",
    response_model=BenchmarkComparisonResponse,
    tags=["Analytics"],
)
async def get_benchmark_comparison(
    industry: Optional[str] = Query(None, description="Фильтр по отрасли"),
    company_size: Optional[str] = Query(None, description="Фильтр по размеру компании (small, medium, large)"),
) -> JSONResponse:
    """
    Получить сравнение метрик с отраслевыми эталонами.

    Этот эндпоинт предоставляет сравнительные метрики производительности рекрутинга компании
    с отраслевыми эталонами. Включает сравнение времени найма, скорости обработки резюме,
    качества совпадений и коэффициентов конверсии. Помогает компаниям понять свою позицию
    на рынке и определить области для улучшения.

    Args:
        industry: Опциональный фильтр по отрасли для более точного сравнения
        company_size: Опциональный фильтр по размеру компании (small, medium, large)

    Returns:
        JSON ответ со сравнительными метриками, перцентилями и рекомендациями

    Raises:
        HTTPException(500): Если не удалось получить данные

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8006/api/analytics/benchmarks")
        >>> response.json()
        {
            "company_time_to_hire_avg": 28.5,
            "industry_time_to_hire_avg": 35.2,
            "time_to_hire_percentile": 72.5,
            "company_resume_processing_rate": 12.5,
            "industry_resume_processing_rate": 8.3,
            "processing_rate_percentile": 68.0,
            "company_match_rate": 0.82,
            "industry_match_rate": 0.75,
            "match_rate_percentile": 65.0,
            "company_offer_acceptance_rate": 0.78,
            "industry_offer_acceptance_rate": 0.72,
            "acceptance_rate_percentile": 62.0,
            "overall_performance_score": 73.5,
            "industry_position": "Top 25%",
            "recommendations": [
                "Продолжайте оптимизировать время найма - вы на 19% быстрее среднего",
                "Рассмотрите улучшение процесса обработки резюме для достижения топ 10%",
                "Качество совпадений выше среднего - поддерживайте текущие стандарты"
            ]
        }
    """
    try:
        logger.info(
            f"Получение сравнения с эталонами - industry: {industry}, company_size: {company_size}"
        )

        # Возвращаем placeholder ответ
        # Интеграция с базой данных будет добавлена в последующем подзадаче
        response_data = {
            "company_time_to_hire_avg": 28.5,
            "industry_time_to_hire_avg": 35.2,
            "time_to_hire_percentile": 72.5,
            "company_resume_processing_rate": 12.5,
            "industry_resume_processing_rate": 8.3,
            "processing_rate_percentile": 68.0,
            "company_match_rate": 0.82,
            "industry_match_rate": 0.75,
            "match_rate_percentile": 65.0,
            "company_offer_acceptance_rate": 0.78,
            "industry_offer_acceptance_rate": 0.72,
            "acceptance_rate_percentile": 62.0,
            "overall_performance_score": 73.5,
            "industry_position": "Top 25%",
            "recommendations": [
                "Продолжайте оптимизировать время найма - вы на 19% быстрее среднего",
                "Рассмотрите улучшение процесса обработки резюме для достижения топ 10%",
                "Качество совпадений выше среднего - поддерживайте текущие стандарты",
            ],
        }

        logger.info("Сравнение с эталонами успешно получено")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Ошибка получения сравнения с эталонами: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить сравнение с эталонами: {str(e)}",
        ) from e
