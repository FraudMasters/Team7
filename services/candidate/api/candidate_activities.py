"""
Эндпоинты API для временной шкалы активности кандидата.

# Русский комментарий:
Этот модуль предоставляет эндпоинты для получения истории активности
кандидата, включая изменения этапов, добавления/изменения заметок,
модификации тегов и другие важные события кандидата на протяжении
процесса найма.
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.candidate import Candidate
from models.candidate_activity import CandidateActivity, CandidateActivityType

logger = logging.getLogger(__name__)

router = APIRouter()


# ============== Pydantic Models for Request/Response ==============
# Модели Pydantic для запросов и ответов


class ActivityItem(BaseModel):
    """Элемент активности в временной шкале / Single activity item in the timeline."""

    id: str = Field(..., description="Activity ID / ID активности")
    activity_type: str = Field(..., description="Activity type / Тип активности")
    candidate_id: str = Field(..., description="Candidate ID / ID кандидата")
    vacancy_id: Optional[str] = Field(None, description="Related vacancy ID / ID связанной вакансии")
    from_stage: Optional[str] = Field(None, description="Previous stage / Предыдущий этап")
    to_stage: Optional[str] = Field(None, description="New stage / Новый этап")
    note_id: Optional[str] = Field(None, description="Related note ID / ID связанной заметки")
    tag_id: Optional[str] = Field(None, description="Related tag ID / ID связанного тега")
    recruiter_id: Optional[str] = Field(None, description="Recruiter who performed the action / Рекрутер, выполнивший действие")
    activity_data: Optional[dict] = Field(None, description="Additional activity data / Дополнительные данные активности")
    reason: Optional[str] = Field(None, description="Reason / Причина")
    created_at: str = Field(..., description="Activity timestamp / Время активности")


class ActivityTimelineResponse(BaseModel):
    """Модель ответа для временной шкалы активности / Response model for candidate activity timeline."""

    candidate_id: str = Field(..., description="Candidate ID / ID кандидата")
    activities: List[ActivityItem] = Field(..., description="List of activities / Список активностей")
    total_count: int = Field(..., description="Total number of activities / Общее количество активностей")


class ActivityTypesResponse(BaseModel):
    """Модель ответа для типов активностей / Response model for available activity types."""

    activity_types: List[str] = Field(..., description="List of available activity types / Список доступных типов активностей")


# ============== API Endpoints ==============
# Эндпоинты API


@router.get(
    "/",
    response_model=ActivityTimelineResponse,
    tags=["Candidate Activities"],
)
async def get_candidate_activities(
    candidate_id: Optional[str] = Query(None, description="Filter by candidate ID / Фильтр по ID кандидата"),
    activity_type: Optional[str] = Query(None, description="Filter by activity type / Фильтр по типу активности"),
    vacancy_id: Optional[str] = Query(None, description="Filter by vacancy ID / Фильтр по ID вакансии"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum activities to return / Максимум активностей для возврата"),
    offset: int = Query(0, ge=0, description="Activities to skip / Активностей для пропуска"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Получить временную шкалу активности кандидата.

    Get candidate activity timeline.

    Этот эндпоинт получает историю активности для кандидата, включая
    изменения этапов, добавления/изменения заметок, модификации тегов
    и другие важные события на протяжении процесса найма.

    This endpoint retrieves the activity history for a candidate, including
    stage changes, notes additions/changes, tag modifications, and other
    significant events throughout the hiring process.

    Активности возвращаются в обратном хронологическом порядке
    (сначала новые).

    Activities are returned in reverse chronological order (newest first).

    Args:
        candidate_id: Опциональный фильтр для получения активностей конкретного кандидата / Optional filter for specific candidate
        activity_type: Опциональный фильтр для конкретного типа активности / Optional filter for specific activity type
        vacancy_id: Опциональный фильтр для конкретной вакансии / Optional filter for specific vacancy
        limit: Максимум активностей для возврата (по умолчанию: 100) / Maximum activities to return (default: 100)
        offset: Количество активностей для пропуска для пагинации (по умолчанию: 0) / Activities to skip for pagination (default: 0)
        db: Сессия базы данных / Database session

    Returns:
        JSON ответ со списком активностей в хронологическом порядке / JSON response with list of activities in chronological order

    Raises:
        HTTPException(404): Если candidate_id указан и кандидат не найден / If candidate_id provided and candidate not found
        HTTPException(400): Если activity_type неверен / If activity_type is invalid
        HTTPException(500): Если получение данных не удалось / If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8003/api/candidate-activities/?candidate_id=abc-123")
        >>> response.json()
        {
            "candidate_id": "abc-123",
            "activities": [
                {
                    "id": "act-1",
                    "activity_type": "stage_changed",
                    "candidate_id": "abc-123",
                    "vacancy_id": "vac-1",
                    "from_stage": "screening",
                    "to_stage": "interview",
                    "note_id": null,
                    "tag_id": null,
                    "recruiter_id": "rec-1",
                    "activity_data": null,
                    "reason": "Candidate passed initial screening",
                    "created_at": "2026-01-31T10:30:00Z"
                }
            ],
            "total_count": 1
        }
    """
    try:
        logger.info(
            f"Fetching candidate activities - candidate_id: {candidate_id}, "
            f"activity_type: {activity_type}, vacancy_id: {vacancy_id}"
        )

        # Build base query / Создаем базовый запрос
        query = select(CandidateActivity)

        # Apply filters / Применяем фильтры
        if candidate_id:
            # Verify candidate exists / Проверяем, существует ли кандидат
            candidate_result = await db.execute(
                select(Candidate).where(Candidate.id == UUID(candidate_id))
            )
            candidate = candidate_result.scalar_one_or_none()

            if not candidate:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Candidate not found: {candidate_id}",
                )

            query = query.where(CandidateActivity.candidate_id == UUID(candidate_id))

        if vacancy_id:
            query = query.where(CandidateActivity.vacancy_id == UUID(vacancy_id))

        if activity_type:
            # Validate activity type / Валидируем тип активности
            valid_types = [t.value for t in CandidateActivityType]
            if activity_type not in valid_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid activity_type: {activity_type}. "
                           f"Valid types are: {', '.join(valid_types)}",
                )
            query = query.where(CandidateActivity.activity_type == activity_type)

        # Order by created_at descending (newest first) and apply pagination
        # Сортировка по created_at по убыванию (сначала новые) и применение пагинации
        query = query.order_by(CandidateActivity.created_at.desc()).limit(limit).offset(offset)

        # Execute query / Выполняем запрос
        result = await db.execute(query)
        activities = result.scalars().all()

        # Build response data / Формируем данные ответа
        activities_data = []
        for activity in activities:
            activities_data.append({
                "id": str(activity.id),
                "activity_type": activity.activity_type.value,
                "candidate_id": str(activity.candidate_id),
                "vacancy_id": str(activity.vacancy_id) if activity.vacancy_id else None,
                "from_stage": activity.from_stage,
                "to_stage": activity.to_stage,
                "note_id": str(activity.note_id) if activity.note_id else None,
                "tag_id": str(activity.tag_id) if activity.tag_id else None,
                "recruiter_id": str(activity.recruiter_id) if activity.recruiter_id else None,
                "activity_data": activity.activity_data,
                "reason": activity.reason,
                "created_at": activity.created_at.isoformat(),
            })

        # Use the candidate_id from filter or first activity if not specified
        # Используем candidate_id из фильтра или первой активности, если не указан
        response_candidate_id = candidate_id if candidate_id else (
            str(activities[0].candidate_id) if activities else "all"
        )

        response_data = {
            "candidate_id": response_candidate_id,
            "activities": activities_data,
            "total_count": len(activities_data),
        }

        logger.info(f"Retrieved {len(activities_data)} candidate activities")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid UUID format provided",
        )
    except Exception as e:
        logger.error(f"Error retrieving candidate activities: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve candidate activities: {str(e)}",
        ) from e


@router.get(
    "/types",
    response_model=ActivityTypesResponse,
    tags=["Candidate Activities"],
)
async def get_activity_types() -> JSONResponse:
    """
    Получить доступные типы активностей кандидата.

    Get available candidate activity types.

    Этот эндпоинт возвращает список всех допустимых типов активностей,
    которые можно использовать для фильтрации активностей кандидата.

    This endpoint returns a list of all valid activity types that can be used
    for filtering candidate activities.

    Returns:
        JSON ответ со списком типов активностей / JSON response with list of activity types

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8003/api/candidate-activities/types")
        >>> response.json()
        {
            "activity_types": [
                "stage_changed",
                "note_added",
                "note_updated",
                "note_deleted",
                "tag_added",
                "tag_removed",
                "ranking_changed",
                "rating_changed",
                "contact_attempt",
                "interview_scheduled",
                "feedback_provided",
                "status_updated"
            ]
        }
    """
    try:
        logger.info("Fetching available activity types")

        activity_types = [t.value for t in CandidateActivityType]

        response_data = {
            "activity_types": activity_types,
        }

        logger.info(f"Retrieved {len(activity_types)} activity types")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error retrieving activity types: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve activity types: {str(e)}",
        ) from e
