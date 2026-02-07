"""
Эндпоинты API для управления кандидатами и их статусами.

# Русский комментарий:
Этот модуль предоставляет эндпоинты для:
- Списка кандидатов с фильтрацией и пагинацией
- Получения информации о конкретном кандидате
- Создания, обновления и удаления кандидатов
- Изменения статуса кандидата (для канбан-доски)
- Массовых операций с кандидатами
"""
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.candidate import Candidate, CandidateStatus
from models.candidate_note import CandidateNote
from models.candidate_tag import CandidateTag
from models.candidate_activity import CandidateActivity, CandidateActivityType

logger = logging.getLogger(__name__)

router = APIRouter()


# ============== Pydantic Models for Request/Response ==============
# Модели Pydantic для запросов и ответов


class TagInfo(BaseModel):
    """Информация о теге кандидата / Information about a candidate tag."""

    id: str = Field(..., description="Tag ID / ID тега")
    tag_name: str = Field(..., description="Tag name / Имя тега")
    color: Optional[str] = Field(None, description="Tag color hex code / Hex код цвета тега")


class LatestActivityInfo(BaseModel):
    """Информация о последней активности кандидата / Information about latest candidate activity."""

    activity_type: str = Field(..., description="Activity type / Тип активности")
    created_at: str = Field(..., description="Activity timestamp / Время активности")


class CandidateListItem(BaseModel):
    """Модель ответа для кандидата в списке / Response model for candidate in list view."""

    id: str = Field(..., description="Unique identifier / Уникальный идентификатор")
    full_name: Optional[str] = Field(None, description="Full name / Полное имя")
    email: Optional[str] = Field(None, description="Email address / Email адрес")
    current_position: Optional[str] = Field(None, description="Current job position / Текущая должность")
    current_company: Optional[str] = Field(None, description="Current company / Текущая компания")
    status: str = Field(..., description="Current hiring status / Текущий статус найма")
    rating: Optional[int] = Field(None, description="Candidate rating (1-5) / Рейтинг кандидата (1-5)")
    tags: List[TagInfo] = Field(default_factory=list, description="Assigned tags / Назначенные теги")
    notes_count: int = Field(0, description="Number of notes / Количество заметок")
    latest_activity: Optional[LatestActivityInfo] = Field(None, description="Latest activity / Последняя активность")
    created_at: str = Field(..., description="Creation timestamp / Время создания")
    updated_at: str = Field(..., description="Last update timestamp / Время последнего обновления")


class CandidateDetail(CandidateListItem):
    """Полная информация о кандидате / Complete candidate information."""

    phone: Optional[str] = Field(None, description="Phone number / Номер телефона")
    years_of_experience: Optional[int] = Field(None, description="Years of experience / Стаж работы в годах")
    expected_salary: Optional[str] = Field(None, description="Expected salary / Ожидаемая зарплата")
    location: Optional[str] = Field(None, description="Location / Местоположение")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL / Ссылка на профиль LinkedIn")
    portfolio_url: Optional[str] = Field(None, description="Portfolio URL / Ссылка на портфолио")
    source: Optional[str] = Field(None, description="Candidate source / Источник кандидата")
    is_active: bool = Field(..., description="Whether profile is active / Активен ли профиль")
    resume_id: str = Field(..., description="Associated resume ID / ID связанного резюме")


class CandidateCreate(BaseModel):
    """Модель запроса для создания кандидата / Request model for creating a candidate."""

    resume_id: str = Field(..., description="Resume ID / ID резюме")
    full_name: Optional[str] = Field(None, max_length=255, description="Full name / Полное имя")
    email: Optional[EmailStr] = Field(None, max_length=255, description="Email address / Email адрес")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number / Номер телефона")
    current_position: Optional[str] = Field(None, max_length=255, description="Current position / Текущая должность")
    current_company: Optional[str] = Field(None, max_length=255, description="Current company / Текущая компания")
    years_of_experience: Optional[int] = Field(None, ge=0, le=50, description="Years of experience / Стаж работы")
    expected_salary: Optional[str] = Field(None, max_length=100, description="Expected salary / Ожидаемая зарплата")
    location: Optional[str] = Field(None, max_length=255, description="Location / Местоположение")
    linkedin_url: Optional[str] = Field(None, max_length=512, description="LinkedIn URL / Ссылка на LinkedIn")
    portfolio_url: Optional[str] = Field(None, max_length=512, description="Portfolio URL / Ссылка на портфолио")
    source: Optional[str] = Field(None, max_length=100, description="Source / Источник")
    status: CandidateStatus = Field(CandidateStatus.NEW, description="Initial status / Начальный статус")


class CandidateUpdate(BaseModel):
    """Модель запроса для обновления кандидата / Request model for updating a candidate."""

    full_name: Optional[str] = Field(None, max_length=255, description="Full name / Полное имя")
    email: Optional[EmailStr] = Field(None, max_length=255, description="Email address / Email адрес")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number / Номер телефона")
    current_position: Optional[str] = Field(None, max_length=255, description="Current position / Текущая должность")
    current_company: Optional[str] = Field(None, max_length=255, description="Current company / Текущая компания")
    years_of_experience: Optional[int] = Field(None, ge=0, le=50, description="Years of experience / Стаж работы")
    expected_salary: Optional[str] = Field(None, max_length=100, description="Expected salary / Ожидаемая зарплата")
    location: Optional[str] = Field(None, max_length=255, description="Location / Местоположение")
    linkedin_url: Optional[str] = Field(None, max_length=512, description="LinkedIn URL / Ссылка на LinkedIn")
    portfolio_url: Optional[str] = Field(None, max_length=512, description="Portfolio URL / Ссылка на портфолио")
    source: Optional[str] = Field(None, max_length=100, description="Source / Источник")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating (1-5) / Рейтинг (1-5)")
    is_active: Optional[bool] = Field(None, description="Active status / Статус активности")


class CandidateStatusUpdate(BaseModel):
    """Модель запроса для обновления статуса кандидата / Request model for updating candidate status."""

    status: CandidateStatus = Field(..., description="New status / Новый статус")
    reason: Optional[str] = Field(None, description="Reason for status change / Причина изменения статуса")


class CandidateStatusUpdateResponse(BaseModel):
    """Модель ответа для обновления статуса / Response model for status update."""

    id: str = Field(..., description="Candidate ID / ID кандидата")
    previous_status: str = Field(..., description="Previous status / Предыдущий статус")
    new_status: str = Field(..., description="New status / Новый статус")
    message: str = Field(..., description="Success message / Сообщение об успехе")


class CandidatesListResponse(BaseModel):
    """Модель ответа для списка кандидатов / Response model for candidates list."""

    total: int = Field(..., description="Total number of candidates / Общее количество кандидатов")
    candidates: List[CandidateListItem] = Field(..., description="List of candidates / Список кандидатов")


# ============== Helper Functions ==============
# Вспомогательные функции


def _extract_locale(request: Optional[Request]) -> str:
    """
    Извлечь заголовок Accept-Language из запроса.

    Extract Accept-Language header from request.

    Args:
        request: Входящий запрос FastAPI (опционально) / The incoming FastAPI request (optional)

    Returns:
        Код языка (напр., 'en', 'ru') / Language code (e.g., 'en', 'ru')
    """
    if request is None:
        return "en"
    accept_language = request.headers.get("Accept-Language", "en")
    lang_code = accept_language.split("-")[0].split(",")[0].strip().lower()
    return lang_code


async def _get_candidate_tags(db: AsyncSession, candidate_id: UUID) -> List[Dict[str, Any]]:
    """
    Получить теги кандидата.

    Get candidate tags.

    Args:
        db: Сессия базы данных / Database session
        candidate_id: ID кандидата / Candidate ID

    Returns:
        Список тегов / List of tags
    """
    # Get candidate to fetch tag IDs
    candidate_query = select(Candidate).where(Candidate.id == candidate_id)
    candidate_result = await db.execute(candidate_query)
    candidate = candidate_result.scalar_one_or_none()

    if not candidate or not candidate.tags:
        return []

    tag_ids = candidate.tags  # List of tag IDs

    # Fetch tag details
    tags_query = select(CandidateTag).where(CandidateTag.id.in_(tag_ids))
    tags_result = await db.execute(tags_query)
    tags = tags_result.scalars().all()

    return [
        {
            "id": str(tag.id),
            "tag_name": tag.tag_name,
            "color": tag.color,
        }
        for tag in tags
    ]


async def _get_candidate_notes_count(db: AsyncSession, candidate_id: UUID) -> int:
    """
    Получить количество заметок кандидата.

    Get candidate notes count.

    Args:
        db: Сессия базы данных / Database session
        candidate_id: ID кандидата / Candidate ID

    Returns:
        Количество заметок / Notes count
    """
    count_query = select(func.count(CandidateNote.id)).where(
        CandidateNote.candidate_id == candidate_id
    )
    count_result = await db.execute(count_query)
    return count_result.scalar() or 0


async def _get_latest_activity(db: AsyncSession, candidate_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Получить последнюю активность кандидата.

    Get latest candidate activity.

    Args:
        db: Сессия базы данных / Database session
        candidate_id: ID кандидата / Candidate ID

    Returns:
        Последняя активность или None / Latest activity or None
    """
    activity_query = select(CandidateActivity).where(
        CandidateActivity.candidate_id == candidate_id
    ).order_by(CandidateActivity.created_at.desc()).limit(1)

    activity_result = await db.execute(activity_query)
    activity = activity_result.scalar_one_or_none()

    if activity:
        return {
            "activity_type": activity.activity_type.value,
            "created_at": activity.created_at.isoformat() if activity.created_at else None,
        }
    return None


async def _create_activity(
    db: AsyncSession,
    candidate_id: UUID,
    activity_type: CandidateActivityType,
    recruiter_id: Optional[UUID] = None,
    from_stage: Optional[str] = None,
    to_stage: Optional[str] = None,
    reason: Optional[str] = None,
    activity_data: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Создать запись активности кандидата.

    Create candidate activity record.

    Args:
        db: Сессия базы данных / Database session
        candidate_id: ID кандидата / Candidate ID
        activity_type: Тип активности / Activity type
        recruiter_id: ID рекрутера (опционально) / Recruiter ID (optional)
        from_stage: Предыдущий этап (опционально) / Previous stage (optional)
        to_stage: Новый этап (опционально) / New stage (optional)
        reason: Причина (опционально) / Reason (optional)
        activity_data: Дополнительные данные (опционально) / Additional data (optional)
    """
    activity = CandidateActivity(
        activity_type=activity_type,
        candidate_id=candidate_id,
        recruiter_id=recruiter_id,
        from_stage=from_stage,
        to_stage=to_stage,
        reason=reason,
        activity_data=activity_data or {},
    )
    db.add(activity)


# ============== API Endpoints ==============
# Эндпоинты API


@router.get(
    "/",
    response_model=CandidatesListResponse,
    tags=["Candidates"],
)
async def list_candidates(
    request: Request,
    status_filter: Optional[CandidateStatus] = Query(None, description="Filter by status / Фильтр по статусу"),
    search: Optional[str] = Query(None, description="Search by name or email / Поиск по имени или email"),
    is_active: Optional[bool] = Query(True, description="Filter by active status / Фильтр по активности"),
    skip: int = Query(0, ge=0, description="Records to skip / Записей для пропуска"),
    limit: int = Query(100, ge=1, le=200, description="Max records to return / Максимум записей"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Получить список кандидатов с фильтрацией и пагинацией.

    List candidates with filtering and pagination.

    Возвращает пагинированный список кандидатов с возможностью фильтрации
    по статусу, поиску по имени/email и статусу активности.

    Returns a paginated list of candidates with optional filtering by status,
    search by name/email, and active status.

    Args:
        request: Объект запроса FastAPI / FastAPI request object
        status_filter: Опциональный фильтр по статусу / Optional status filter
        search: Опциональный поиск по имени или email / Optional search by name or email
        is_active: Фильтр по активности (по умолчанию: True) / Active filter (default: True)
        skip: Количество записей для пропуска / Number of records to skip
        limit: Максимальное количество записей / Maximum number of records
        db: Сессия базы данных / Database session

    Returns:
        JSON ответ со списком кандидатов / JSON response with candidates list

    Raises:
        HTTPException(500): Если получение данных не удалось / If data retrieval fails

    Examples:
        >>> import requests
        >>> # Get all active candidates
        >>> response = requests.get("http://localhost:8003/api/candidates/")
        >>> # Filter by status
        >>> response = requests.get("http://localhost:8003/api/candidates/?status_filter=INTERVIEW")
        >>> # Search by name
        >>> response = requests.get("http://localhost:8003/api/candidates/?search=Ivan")
    """
    try:
        logger.info(
            f"Fetching candidates - status: {status_filter}, search: {search}, "
            f"is_active: {is_active}, skip: {skip}, limit: {limit}"
        )

        # Build base query / Создаем базовый запрос
        query = select(Candidate).where(Candidate.is_active == is_active)

        # Apply filters / Применяем фильтры
        if status_filter:
            query = query.where(Candidate.status == status_filter)

        if search:
            # Case-insensitive search on name or email / Поиск без учета регистра по имени или email
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Candidate.full_name.ilike(search_pattern),
                    Candidate.email.ilike(search_pattern),
                )
            )

        # Get total count / Получаем общее количество
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Add pagination and ordering / Добавляем пагинацию и сортировку
        query = query.order_by(Candidate.created_at.desc()).offset(skip).limit(limit)

        # Execute query / Выполняем запрос
        result = await db.execute(query)
        candidates = result.scalars().all()

        # Fetch related data for each candidate / Получаем связанные данные для каждого кандидата
        candidates_list = []
        for candidate in candidates:
            tags = await _get_candidate_tags(db, candidate.id)
            notes_count = await _get_candidate_notes_count(db, candidate.id)
            latest_activity = await _get_latest_activity(db, candidate.id)

            candidates_list.append({
                "id": str(candidate.id),
                "full_name": candidate.full_name,
                "email": candidate.email,
                "current_position": candidate.current_position,
                "current_company": candidate.current_company,
                "status": candidate.status.value,
                "rating": candidate.rating,
                "tags": tags,
                "notes_count": notes_count,
                "latest_activity": latest_activity,
                "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
                "updated_at": candidate.updated_at.isoformat() if candidate.updated_at else None,
            })

        logger.info(f"Retrieved {len(candidates_list)} candidates (total: {total})")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total": total,
                "candidates": candidates_list,
            },
        )

    except Exception as e:
        logger.error(f"Error listing candidates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list candidates: {str(e)}",
        ) from e


# Search endpoints - must come before /{candidate_id} to avoid route conflicts
@router.post("/search", tags=["Search"])
async def search_candidates_post(
    request: Request,
    query: Optional[str] = Body(None, description="Search query string"),
    filters: Optional[Dict[str, Any]] = Body(None, description="Filter criteria"),
    skip: int = Body(0, description="Pagination offset"),
    limit: int = Body(100, description="Max results"),
    sort_by: str = Body("created_at", description="Sort field"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Search candidates with POST method for complex queries."""
    from services.search_service import get_search_service, SearchFilters

    try:
        search_service = get_search_service(db)

        search_filters = None
        if filters:
            search_filters = SearchFilters(
                query=query,
                skills=filters.get("skills"),
                min_experience_years=filters.get("min_experience_years"),
                max_experience_years=filters.get("max_experience_years"),
                location=filters.get("location"),
                status=filters.get("status"),
                source=filters.get("source"),
                min_rating=filters.get("min_rating"),
                date_from=filters.get("date_from"),
                date_to=filters.get("date_to"),
                tag_ids=filters.get("tag_ids"),
            )

        result = await search_service.search_candidates(
            query=query,
            filters=search_filters,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total": result.total,
                "candidates": result.candidates,
                "query": result.query,
                "filters_applied": result.filters_applied,
                "execution_time_seconds": result.execution_time_seconds,
                "skip": skip,
                "limit": limit,
            },
        )
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        ) from e


@router.get("/search", tags=["Search"])
async def search_candidates_get(
    request: Request,
    query: Optional[str] = Query(None, description="Search query"),
    location: Optional[str] = Query(None, description="Location filter"),
    min_experience: Optional[int] = Query(None, description="Min experience years"),
    max_experience: Optional[int] = Query(None, description="Max experience years"),
    candidate_status: Optional[str] = Query(None, description="Candidate status filter"),
    source: Optional[str] = Query(None, description="Source filter"),
    min_rating: Optional[int] = Query(None, description="Min rating"),
    skip: int = Query(0, description="Pagination offset"),
    limit: int = Query(100, description="Max results"),
    sort_by: str = Query("created_at", description="Sort field"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Search candidates with GET method for simple queries."""
    from services.search_service import get_search_service, SearchFilters

    try:
        search_service = get_search_service(db)

        filters_dict = {}
        if location:
            filters_dict["location"] = location
        if min_experience is not None:
            filters_dict["min_experience_years"] = min_experience
        if max_experience is not None:
            filters_dict["max_experience_years"] = max_experience
        if candidate_status:
            filters_dict["status"] = candidate_status
        if source:
            filters_dict["source"] = source
        if min_rating is not None:
            filters_dict["min_rating"] = min_rating

        search_filters = SearchFilters(**filters_dict) if filters_dict else None

        result = await search_service.search_candidates(
            query=query,
            filters=search_filters,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total": result.total,
                "candidates": result.candidates,
                "query": result.query,
                "filters_applied": result.filters_applied,
                "execution_time_seconds": result.execution_time_seconds,
                "skip": skip,
                "limit": limit,
            },
        )
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        ) from e


@router.post("/bulk-action", tags=["Candidates"])
async def bulk_action(
    request: Request,
    action: str = Body(..., description="Action: export, status, tag"),
    resume_ids: List[str] = Body(..., description="List of candidate IDs"),
    new_status: Optional[str] = Body(None, description="New status"),
    tag_name: Optional[str] = Body(None, description="Tag name"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Perform bulk action on candidates."""
    try:
        if action == "export":
            result = await db.execute(
                select(Candidate).where(Candidate.id.in_(resume_ids))
            )
            candidates = result.scalars().all()

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "total": len(candidates),
                    "candidates": [
                        {
                            "id": str(c.id),
                            "full_name": c.full_name,
                            "email": c.email,
                            "current_position": c.current_position,
                            "location": c.location,
                            "status": c.status.value if hasattr(c.status, 'value') else str(c.status),
                        }
                        for c in candidates
                    ],
                },
            )

        elif action == "status":
            if not new_status:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="new_status is required for status action"
                )
            # TODO: Implement status change
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": f"Would update {len(resume_ids)} candidates to status '{new_status}'"}
            )

        elif action == "tag":
            if not tag_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="tag_name is required for tag action"
                )
            # TODO: Implement tagging
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": f"Would tag {len(resume_ids)} candidates with '{tag_name}'"}
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown action: {action}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk action error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk action failed: {str(e)}",
        ) from e


@router.get(
    "/{candidate_id}",
    response_model=CandidateDetail,
    tags=["Candidates"],
)
async def get_candidate(
    request: Request,
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Получить детальную информацию о кандидате.

    Get detailed candidate information.

    Args:
        request: Объект запроса FastAPI / FastAPI request object
        candidate_id: UUID кандидата / Candidate UUID
        db: Сессия базы данных / Database session

    Returns:
        JSON ответ с деталями кандидата / JSON response with candidate details

    Raises:
        HTTPException(404): Если кандидат не найден / If candidate not found
        HTTPException(500): Если получение данных не удалось / If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8003/api/candidates/123e4567-e89b-12d3-a456-426614174000")
        >>> candidate = response.json()
    """
    try:
        logger.info(f"Fetching candidate: {candidate_id}")

        # Parse UUID / Парсим UUID
        try:
            candidate_uuid = UUID(candidate_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid candidate ID format: {candidate_id}",
            )

        # Get candidate / Получаем кандидата
        query = select(Candidate).where(Candidate.id == candidate_uuid)
        result = await db.execute(query)
        candidate = result.scalar_one_or_none()

        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate not found: {candidate_id}",
            )

        # Fetch related data / Получаем связанные данные
        tags = await _get_candidate_tags(db, candidate.id)
        notes_count = await _get_candidate_notes_count(db, candidate.id)
        latest_activity = await _get_latest_activity(db, candidate.id)

        candidate_data = {
            "id": str(candidate.id),
            "full_name": candidate.full_name,
            "email": candidate.email,
            "phone": candidate.phone,
            "current_position": candidate.current_position,
            "current_company": candidate.current_company,
            "status": candidate.status.value,
            "rating": candidate.rating,
            "tags": tags,
            "notes_count": notes_count,
            "latest_activity": latest_activity,
            "years_of_experience": candidate.years_of_experience,
            "expected_salary": candidate.expected_salary,
            "location": candidate.location,
            "linkedin_url": candidate.linkedin_url,
            "portfolio_url": candidate.portfolio_url,
            "source": candidate.source,
            "is_active": candidate.is_active,
            "resume_id": str(candidate.resume_id),
            "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
            "updated_at": candidate.updated_at.isoformat() if candidate.updated_at else None,
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=candidate_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting candidate {candidate_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get candidate: {str(e)}",
        ) from e


@router.post(
    "/",
    response_model=CandidateDetail,
    status_code=status.HTTP_201_CREATED,
    tags=["Candidates"],
)
async def create_candidate(
    request: Request,
    candidate_data: CandidateCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Создать нового кандидата.

    Create a new candidate.

    Args:
        request: Объект запроса FastAPI / FastAPI request object
        candidate_data: Данные для создания кандидата / Data for creating candidate
        db: Сессия базы данных / Database session

    Returns:
        JSON ответ с созданным кандидатом / JSON response with created candidate

    Raises:
        HTTPException(422): Если формат resume_id неверен / If resume_id format is invalid
        HTTPException(500): Если создание не удалось / If creation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "resume_id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "full_name": "Ivan Ivanov",
        ...     "email": "ivan@example.com",
        ...     "status": "NEW"
        ... }
        >>> response = requests.post("http://localhost:8003/api/candidates/", json=data)
    """
    try:
        logger.info(f"Creating candidate with resume_id: {candidate_data.resume_id}")

        # Parse resume_id UUID / Парсим UUID resume_id
        try:
            resume_uuid = UUID(candidate_data.resume_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid resume ID format: {candidate_data.resume_id}",
            )

        # Check if candidate already exists for this resume / Проверяем, существует ли кандидат для этого резюме
        existing_query = select(Candidate).where(Candidate.resume_id == resume_uuid)
        existing_result = await db.execute(existing_query)
        existing_candidate = existing_result.scalar_one_or_none()

        if existing_candidate:
            # Reactivate if exists / Реактивируем, если существует
            existing_candidate.is_active = True
            existing_candidate.status = candidate_data.status
            await db.commit()
            await db.refresh(existing_candidate)
            candidate = existing_candidate
        else:
            # Create new candidate / Создаем нового кандидата
            candidate = Candidate(
                id=uuid4(),
                resume_id=resume_uuid,
                full_name=candidate_data.full_name,
                email=candidate_data.email,
                phone=candidate_data.phone,
                current_position=candidate_data.current_position,
                current_company=candidate_data.current_company,
                years_of_experience=candidate_data.years_of_experience,
                expected_salary=candidate_data.expected_salary,
                location=candidate_data.location,
                linkedin_url=candidate_data.linkedin_url,
                portfolio_url=candidate_data.portfolio_url,
                source=candidate_data.source,
                status=candidate_data.status,
            )
            db.add(candidate)
            await db.commit()
            await db.refresh(candidate)

        # Create activity record / Создаем запись активности
        await _create_activity(
            db,
            candidate.id,
            CandidateActivityType.STATUS_UPDATED,
            to_stage=candidate.status.value,
            reason="Candidate created",
        )
        await db.commit()

        logger.info(f"Created candidate: {candidate.id}")

        # Fetch related data / Получаем связанные данные
        tags = await _get_candidate_tags(db, candidate.id)
        notes_count = await _get_candidate_notes_count(db, candidate.id)
        latest_activity = await _get_latest_activity(db, candidate.id)

        candidate_response = {
            "id": str(candidate.id),
            "full_name": candidate.full_name,
            "email": candidate.email,
            "phone": candidate.phone,
            "current_position": candidate.current_position,
            "current_company": candidate.current_company,
            "status": candidate.status.value,
            "rating": candidate.rating,
            "tags": tags,
            "notes_count": notes_count,
            "latest_activity": latest_activity,
            "years_of_experience": candidate.years_of_experience,
            "expected_salary": candidate.expected_salary,
            "location": candidate.location,
            "linkedin_url": candidate.linkedin_url,
            "portfolio_url": candidate.portfolio_url,
            "source": candidate.source,
            "is_active": candidate.is_active,
            "resume_id": str(candidate.resume_id),
            "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
            "updated_at": candidate.updated_at.isoformat() if candidate.updated_at else None,
        }

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=candidate_response,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating candidate: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create candidate: {str(e)}",
        ) from e


@router.put(
    "/{candidate_id}",
    response_model=CandidateDetail,
    tags=["Candidates"],
)
async def update_candidate(
    request: Request,
    candidate_id: str,
    candidate_data: CandidateUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Обновить информацию о кандидате.

    Update candidate information.

    Args:
        request: Объект запроса FastAPI / FastAPI request object
        candidate_id: UUID кандидата / Candidate UUID
        candidate_data: Данные для обновления / Data for updating
        db: Сессия базы данных / Database session

    Returns:
        JSON ответ с обновленным кандидатом / JSON response with updated candidate

    Raises:
        HTTPException(404): Если кандидат не найден / If candidate not found
        HTTPException(500): Если обновление не удалось / If update fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "full_name": "Ivan Ivanovich",
        ...     "rating": 5
        ... }
        >>> response = requests.put(
        ...     "http://localhost:8003/api/candidates/123e4567-e89b-12d3-a456-426614174000",
        ...     json=data
        ... )
    """
    try:
        logger.info(f"Updating candidate: {candidate_id}")

        # Parse UUID / Парсим UUID
        try:
            candidate_uuid = UUID(candidate_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid candidate ID format: {candidate_id}",
            )

        # Get candidate / Получаем кандидата
        query = select(Candidate).where(Candidate.id == candidate_uuid)
        result = await db.execute(query)
        candidate = result.scalar_one_or_none()

        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate not found: {candidate_id}",
            )

        # Update fields / Обновляем поля
        update_data = candidate_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(candidate, field, value)

        await db.commit()
        await db.refresh(candidate)

        logger.info(f"Updated candidate: {candidate_id}")

        # Fetch related data / Получаем связанные данные
        tags = await _get_candidate_tags(db, candidate.id)
        notes_count = await _get_candidate_notes_count(db, candidate.id)
        latest_activity = await _get_latest_activity(db, candidate.id)

        candidate_response = {
            "id": str(candidate.id),
            "full_name": candidate.full_name,
            "email": candidate.email,
            "phone": candidate.phone,
            "current_position": candidate.current_position,
            "current_company": candidate.current_company,
            "status": candidate.status.value,
            "rating": candidate.rating,
            "tags": tags,
            "notes_count": notes_count,
            "latest_activity": latest_activity,
            "years_of_experience": candidate.years_of_experience,
            "expected_salary": candidate.expected_salary,
            "location": candidate.location,
            "linkedin_url": candidate.linkedin_url,
            "portfolio_url": candidate.portfolio_url,
            "source": candidate.source,
            "is_active": candidate.is_active,
            "resume_id": str(candidate.resume_id),
            "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
            "updated_at": candidate.updated_at.isoformat() if candidate.updated_at else None,
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=candidate_response,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating candidate {candidate_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update candidate: {str(e)}",
        ) from e


@router.delete(
    "/{candidate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Candidates"],
)
async def delete_candidate(
    request: Request,
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Удалить кандидата (мягкое удаление).

    Delete a candidate (soft delete).

    Устанавливает is_active=False вместо физического удаления записи.

    Sets is_active=False instead of physically deleting the record.

    Args:
        request: Объект запроса FastAPI / FastAPI request object
        candidate_id: UUID кандидата / Candidate UUID
        db: Сессия базы данных / Database session

    Returns:
        204 No Content при успехе / 204 No Content on success

    Raises:
        HTTPException(404): Если кандидат не найден / If candidate not found
        HTTPException(500): Если удаление не удалось / If deletion fails

    Examples:
        >>> import requests
        >>> response = requests.delete(
        ...     "http://localhost:8003/api/candidates/123e4567-e89b-12d3-a456-426614174000"
        ... )
        >>> response.status_code
        204
    """
    try:
        logger.info(f"Deleting candidate: {candidate_id}")

        # Parse UUID / Парсим UUID
        try:
            candidate_uuid = UUID(candidate_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid candidate ID format: {candidate_id}",
            )

        # Get candidate / Получаем кандидата
        query = select(Candidate).where(Candidate.id == candidate_uuid)
        result = await db.execute(query)
        candidate = result.scalar_one_or_none()

        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate not found: {candidate_id}",
            )

        # Soft delete / Мягкое удаление
        candidate.is_active = False
        await db.commit()

        # Create activity record / Создаем запись активности
        await _create_activity(
            db,
            candidate.id,
            CandidateActivityType.STATUS_UPDATED,
            reason="Candidate deleted",
        )
        await db.commit()

        logger.info(f"Deleted candidate: {candidate_id}")

        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting candidate {candidate_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete candidate: {str(e)}",
        ) from e


@router.patch(
    "/{candidate_id}/status",
    response_model=CandidateStatusUpdateResponse,
    tags=["Candidates"],
)
async def update_candidate_status(
    request: Request,
    candidate_id: str,
    status_update: CandidateStatusUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Обновить статус кандидата (для канбан-доски).

    Update candidate status (for Kanban board workflow).

    Этот эндпоинт позволяет обновлять статус кандидата для поддержки
    рабочего процесса канбан-доски. Создает запись активности
    для отслеживания изменений.

    This endpoint allows updating a candidate's status to support the
    Kanban board workflow. Creates an activity record for tracking changes.

    Args:
        request: Объект запроса FastAPI / FastAPI request object
        candidate_id: UUID кандидата / Candidate UUID
        status_update: Тело запроса с новым статусом и причиной / Request body with new status and reason
        db: Сессия базы данных / Database session

    Returns:
        JSON ответ с обновленным статусом / JSON response with updated status

    Raises:
        HTTPException(404): Если кандидат не найден / If candidate not found
        HTTPException(500): Если обновление не удалось / If update fails

    Examples:
        >>> import requests
        >>> data = {"status": "INTERVIEW", "reason": "Passed screening"}
        >>> response = requests.patch(
        ...     "http://localhost:8003/api/candidates/123/status",
        ...     json=data
        ... )
        >>> response.json()
        {
            "id": "123",
            "previous_status": "NEW",
            "new_status": "INTERVIEW",
            "message": "Candidate status updated successfully"
        }
    """
    try:
        logger.info(f"Updating status for candidate {candidate_id} to {status_update.status.value}")

        # Parse UUID / Парсим UUID
        try:
            candidate_uuid = UUID(candidate_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid candidate ID format: {candidate_id}",
            )

        # Get candidate / Получаем кандидата
        query = select(Candidate).where(Candidate.id == candidate_uuid)
        result = await db.execute(query)
        candidate = result.scalar_one_or_none()

        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate not found: {candidate_id}",
            )

        # Store previous status / Сохраняем предыдущий статус
        previous_status = candidate.status.value

        # Update status / Обновляем статус
        candidate.status = status_update.status
        await db.commit()
        await db.refresh(candidate)

        # Create activity record / Создаем запись активности
        await _create_activity(
            db,
            candidate.id,
            CandidateActivityType.STAGE_CHANGED,
            from_stage=previous_status,
            to_stage=status_update.status.value,
            reason=status_update.reason,
        )
        await db.commit()

        logger.info(
            f"Candidate {candidate_id} status updated from {previous_status} to {status_update.status.value}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(candidate.id),
                "previous_status": previous_status,
                "new_status": status_update.status.value,
                "message": "Candidate status updated successfully",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating candidate status {candidate_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update candidate status: {str(e)}",
        ) from e
