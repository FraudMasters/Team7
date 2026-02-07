"""
Эндпоинты API для управления тегами кандидатов.

# Русский комментарий:
Этот модуль предоставляет эндпоинты для управления тегами кандидатов
организации, включая CRUD операции для создания, чтения, обновления
и удаления конфигураций тегов, а также назначения/удаления тегов
от кандидатов. Теги обеспечивают гибкую категоризацию и приоритизацию
(например, 'Высокий приоритет', 'Удаленно', 'По рекомендации').
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy import select, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.candidate import Candidate
from models.candidate_tag import CandidateTag
from models.candidate_activity import CandidateActivity, CandidateActivityType

logger = logging.getLogger(__name__)

router = APIRouter()


# ============== Pydantic Models for Request/Response ==============
# Модели Pydantic для запросов и ответов


class CandidateTagCreate(BaseModel):
    """Модель запроса для создания тега кандидата / Request model for creating a candidate tag."""

    organization_id: str = Field(..., description="Organization ID / ID организации")
    tag_name: str = Field(..., min_length=1, max_length=100, description="Tag name / Имя тега")
    tag_order: int = Field(0, ge=0, description="Order in UI / Порядок в интерфейсе")
    is_default: bool = Field(False, description="Is default tag / Является ли тег стандартным")
    is_active: bool = Field(True, description="Is tag active / Активен ли тег")
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$', description="Hex color code / Hex код цвета")
    description: Optional[str] = Field(None, max_length=500, description="Description / Описание")


class CandidateTagUpdate(BaseModel):
    """Модель запроса для обновления тега / Request model for updating a candidate tag."""

    tag_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Tag name / Имя тега")
    tag_order: Optional[int] = Field(None, ge=0, description="Order in UI / Порядок в интерфейсе")
    is_default: Optional[bool] = Field(None, description="Is default tag / Является ли тег стандартным")
    is_active: Optional[bool] = Field(None, description="Is tag active / Активен ли тег")
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$', description="Hex color code / Hex код цвета")
    description: Optional[str] = Field(None, max_length=500, description="Description / Описание")


class CandidateTagResponse(BaseModel):
    """Модель ответа для тега кандидата / Response model for a single candidate tag."""

    id: str = Field(..., description="Unique identifier / Уникальный идентификатор")
    organization_id: str = Field(..., description="Organization ID / ID организации")
    tag_name: str = Field(..., description="Tag name / Имя тега")
    tag_order: int = Field(..., description="Order in UI / Порядок в интерфейсе")
    is_default: bool = Field(..., description="Is default tag / Является ли тег стандартным")
    is_active: bool = Field(..., description="Is tag active / Активен ли тег")
    color: Optional[str] = Field(None, description="Hex color code / Hex код цвета")
    description: Optional[str] = Field(None, description="Description / Описание")
    created_at: str = Field(..., description="Creation timestamp / Время создания")
    updated_at: str = Field(..., description="Last update timestamp / Время последнего обновления")


class CandidateTagListResponse(BaseModel):
    """Модель ответа для списка тегов / Response model for listing candidate tags."""

    organization_id: str = Field(..., description="Organization ID / ID организации")
    tags: List[CandidateTagResponse] = Field(..., description="List of tags / Список тегов")
    total_count: int = Field(..., description="Total number of tags / Общее количество тегов")


class AssignTagRequest(BaseModel):
    """Модель запроса для назначения тега / Request model for assigning a tag."""

    tag_id: str = Field(..., description="Tag ID to assign / ID тега для назначения")
    recruiter_id: Optional[str] = Field(None, description="Recruiter ID assigning the tag / ID рекрутера, назначающего тег")


class CandidateTagsResponse(BaseModel):
    """Модель ответа для тегов кандидата / Response model for tags assigned to a candidate."""

    candidate_id: str = Field(..., description="Candidate ID / ID кандидата")
    tags: List[CandidateTagResponse] = Field(..., description="List of tags / Список тегов")
    total_count: int = Field(..., description="Total number of tags / Общее количество тегов")


# ============== API Endpoints ==============
# Эндпоинты API


@router.post(
    "/",
    response_model=CandidateTagResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Candidate Tags"],
)
async def create_candidate_tag(
    request: CandidateTagCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Создать тег кандидата для организации.

    Create a candidate tag for an organization.

    Args:
        request: Тело запроса с деталями тега / Request body containing tag details
        db: Сессия базы данных / Database session

    Returns:
        JSON ответ с созданным тегом / JSON response with created tag details

    Raises:
        HTTPException(409): Если тег с таким именем уже существует / If tag with same name already exists
        HTTPException(500): Если произошла внутренняя ошибка / If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8003/api/candidate-tags/",
        ...     json={
        ...         "organization_id": "org-123",
        ...         "tag_name": "High Priority",
        ...         "tag_order": 1,
        ...         "is_default": False,
        ...         "is_active": True,
        ...         "color": "#EF4444",
        ...         "description": "For urgent candidates"
        ...     }
        ... )
        >>> response.status_code
        201
    """
    try:
        logger.info(f"Creating candidate tag '{request.tag_name}' for organization: {request.organization_id}")

        # Check if tag with same name already exists for this organization
        # Проверяем, существует ли тег с таким же именем для этой организации
        existing = await db.execute(
            select(CandidateTag).where(
                CandidateTag.organization_id == request.organization_id,
                CandidateTag.tag_name == request.tag_name,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tag '{request.tag_name}' already exists for this organization",
            )

        # Create new tag / Создаем новый тег
        new_tag = CandidateTag(
            organization_id=request.organization_id,
            tag_name=request.tag_name,
            tag_order=request.tag_order,
            is_default=request.is_default,
            is_active=request.is_active,
            color=request.color,
            description=request.description,
        )
        db.add(new_tag)
        await db.flush()

        response_data = {
            "id": str(new_tag.id),
            "organization_id": new_tag.organization_id,
            "tag_name": new_tag.tag_name,
            "tag_order": new_tag.tag_order,
            "is_default": new_tag.is_default,
            "is_active": new_tag.is_active,
            "color": new_tag.color,
            "description": new_tag.description,
            "created_at": new_tag.created_at.isoformat(),
            "updated_at": new_tag.updated_at.isoformat(),
        }

        await db.commit()

        logger.info(f"Created candidate tag '{request.tag_name}' with ID: {new_tag.id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating candidate tag: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create candidate tag: {str(e)}",
        ) from e


@router.get("/", tags=["Candidate Tags"])
async def list_candidate_tags(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID / Фильтр по ID организации"),
    is_active: Optional[bool] = Query(None, description="Filter by active status / Фильтр по активности"),
    is_default: Optional[bool] = Query(None, description="Filter by default status / Фильтр по стандартности"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Получить список тегов кандидатов с опциональной фильтрацией.

    List candidate tags with optional filters.

    Args:
        organization_id: Опциональный фильтр по ID организации / Optional organization ID filter
        is_active: Опциональный фильтр по активности / Optional active status filter
        is_default: Опциональный фильтр по стандартности / Optional default status filter
        db: Сессия базы данных / Database session

    Returns:
        JSON ответ со списком тегов / JSON response with list of tags

    Raises:
        HTTPException(500): Если произошла внутренняя ошибка / If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8003/api/candidate-tags/?organization_id=org-123")
        >>> response.json()
        {
            "organization_id": "org-123",
            "tags": [...],
            "total_count": 5
        }
    """
    try:
        logger.info(
            f"Listing candidate tags - organization_id: {organization_id}, "
            f"is_active: {is_active}, is_default: {is_default}"
        )

        # Build query / Создаем запрос
        query = select(CandidateTag)

        if organization_id:
            query = query.where(CandidateTag.organization_id == organization_id)
        if is_active is not None:
            query = query.where(CandidateTag.is_active == is_active)
        if is_default is not None:
            query = query.where(CandidateTag.is_default == is_default)

        query = query.order_by(CandidateTag.tag_order, CandidateTag.tag_name)

        result = await db.execute(query)
        tags = result.scalars().all()

        # If organization_id filter was provided, use it in response
        # Если указан фильтр organization_id, используем его в ответе
        response_org_id = organization_id if organization_id and len(tags) > 0 else "all"

        # Build response / Формируем ответ
        tags_data = []
        for tag in tags:
            tags_data.append({
                "id": str(tag.id),
                "organization_id": tag.organization_id,
                "tag_name": tag.tag_name,
                "tag_order": tag.tag_order,
                "is_default": tag.is_default,
                "is_active": tag.is_active,
                "color": tag.color,
                "description": tag.description,
                "created_at": tag.created_at.isoformat(),
                "updated_at": tag.updated_at.isoformat(),
            })

        response_data = {
            "organization_id": response_org_id,
            "tags": tags_data,
            "total_count": len(tags_data),
        }

        logger.info(f"Retrieved {len(tags_data)} candidate tags")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error listing candidate tags: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list candidate tags: {str(e)}",
        ) from e


@router.get("/{tag_id}", tags=["Candidate Tags"])
async def get_candidate_tag(
    tag_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Получить конкретный тег кандидата по ID.

    Get a specific candidate tag by ID.

    Args:
        tag_id: UUID тега / UUID of the tag
        db: Сессия базы данных / Database session

    Returns:
        JSON ответ с деталями тега / JSON response with tag details

    Raises:
        HTTPException(404): Если тег не найден / If tag is not found
        HTTPException(500): Если произошла внутренняя ошибка / If an internal error occurs
    """
    try:
        logger.info(f"Retrieving candidate tag: {tag_id}")

        result = await db.execute(
            select(CandidateTag).where(CandidateTag.id == UUID(tag_id))
        )
        tag = result.scalar_one_or_none()

        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate tag not found: {tag_id}",
            )

        response_data = {
            "id": str(tag.id),
            "organization_id": tag.organization_id,
            "tag_name": tag.tag_name,
            "tag_order": tag.tag_order,
            "is_default": tag.is_default,
            "is_active": tag.is_active,
            "color": tag.color,
            "description": tag.description,
            "created_at": tag.created_at.isoformat(),
            "updated_at": tag.updated_at.isoformat(),
        }

        logger.info(f"Retrieved candidate tag: {tag_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {tag_id}",
        )
    except Exception as e:
        logger.error(f"Error retrieving candidate tag: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve candidate tag: {str(e)}",
        ) from e


@router.get("/candidate/{candidate_id}", tags=["Candidate Tags"])
async def get_candidate_tags(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Получить все теги, назначенные конкретному кандидату.

    Get all tags assigned to a specific candidate.

    Этот эндпоинт получает все теги, которые сейчас назначены кандидату,
    проверяя активности назначения тегов.

    This endpoint retrieves all tags that are currently assigned to a candidate
    by checking for tag assignment activities.

    Args:
        candidate_id: UUID кандидата / UUID of the candidate
        db: Сессия базы данных / Database session

    Returns:
        JSON ответ со списком тегов / JSON response with list of tags

    Raises:
        HTTPException(404): Если кандидат не найден / If candidate is not found
        HTTPException(500): Если произошла внутренняя ошибка / If an internal error occurs
    """
    try:
        logger.info(f"Retrieving tags for candidate: {candidate_id}")

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

        # Get all tag_added activities for this candidate
        # Получаем все активности tag_added для этого кандидата
        activities_result = await db.execute(
            select(CandidateActivity).where(
                CandidateActivity.candidate_id == UUID(candidate_id),
                CandidateActivity.activity_type == CandidateActivityType.TAG_ADDED,
            ).order_by(CandidateActivity.created_at.desc())
        )
        all_tag_activities = activities_result.scalars().all()

        # Get unique tag IDs that haven't been removed
        # Получаем уникальные ID тегов, которые не были удалены
        assigned_tag_ids = set()
        for activity in all_tag_activities:
            if activity.tag_id:
                # Check if this tag has been removed after this activity
                # Проверяем, был ли этот тег удален после этой активности
                removal_result = await db.execute(
                    select(CandidateActivity).where(
                        CandidateActivity.candidate_id == UUID(candidate_id),
                        CandidateActivity.activity_type == CandidateActivityType.TAG_REMOVED,
                        CandidateActivity.tag_id == activity.tag_id,
                        CandidateActivity.created_at > activity.created_at,
                    ).limit(1)
                )
                removal_activity = removal_result.scalar_one_or_none()

                if not removal_activity:
                    assigned_tag_ids.add(activity.tag_id)

        # Fetch tag details / Получаем детали тегов
        tags_data = []
        if assigned_tag_ids:
            tags_result = await db.execute(
                select(CandidateTag).where(CandidateTag.id.in_(assigned_tag_ids))
            )
            tags = tags_result.scalars().all()

            for tag in tags:
                tags_data.append({
                    "id": str(tag.id),
                    "organization_id": tag.organization_id,
                    "tag_name": tag.tag_name,
                    "tag_order": tag.tag_order,
                    "is_default": tag.is_default,
                    "is_active": tag.is_active,
                    "color": tag.color,
                    "description": tag.description,
                    "created_at": tag.created_at.isoformat(),
                    "updated_at": tag.updated_at.isoformat(),
                })

        response_data = {
            "candidate_id": candidate_id,
            "tags": tags_data,
            "total_count": len(tags_data),
        }

        logger.info(f"Retrieved {len(tags_data)} tags for candidate: {candidate_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {candidate_id}",
        )
    except Exception as e:
        logger.error(f"Error retrieving candidate tags: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve candidate tags: {str(e)}",
        ) from e


@router.put("/{tag_id}", tags=["Candidate Tags"])
async def update_candidate_tag(
    tag_id: str,
    request: CandidateTagUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Обновить тег кандидата.

    Update a candidate tag.

    Args:
        tag_id: UUID тега / UUID of the tag
        request: Тело запроса с полями для обновления / Request body containing fields to update
        db: Сессия базы данных / Database session

    Returns:
        JSON ответ с обновленными деталями тега / JSON response with updated tag details

    Raises:
        HTTPException(404): Если тег не найден / If tag is not found
        HTTPException(409): Если имя тега конфликтует с существующим / If tag name conflicts with existing tag
        HTTPException(500): Если произошла внутренняя ошибка / If an internal error occurs
    """
    try:
        logger.info(f"Updating candidate tag: {tag_id}")

        # Get existing tag / Получаем существующий тег
        result = await db.execute(
            select(CandidateTag).where(CandidateTag.id == UUID(tag_id))
        )
        tag = result.scalar_one_or_none()

        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate tag not found: {tag_id}",
            )

        # Update fields if provided / Обновляем поля, если они предоставлены
        if request.tag_name is not None:
            # Check if new name conflicts with existing tag
            # Проверяем, не конфликтует ли новое имя с существующим тегом
            existing = await db.execute(
                select(CandidateTag).where(
                    CandidateTag.organization_id == tag.organization_id,
                    CandidateTag.tag_name == request.tag_name,
                    CandidateTag.id != UUID(tag_id),
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Tag '{request.tag_name}' already exists for this organization",
                )
            tag.tag_name = request.tag_name

        if request.tag_order is not None:
            tag.tag_order = request.tag_order
        if request.is_default is not None:
            tag.is_default = request.is_default
        if request.is_active is not None:
            tag.is_active = request.is_active
        if request.color is not None:
            tag.color = request.color
        if request.description is not None:
            tag.description = request.description

        await db.commit()
        await db.refresh(tag)

        response_data = {
            "id": str(tag.id),
            "organization_id": tag.organization_id,
            "tag_name": tag.tag_name,
            "tag_order": tag.tag_order,
            "is_default": tag.is_default,
            "is_active": tag.is_active,
            "color": tag.color,
            "description": tag.description,
            "created_at": tag.created_at.isoformat(),
            "updated_at": tag.updated_at.isoformat(),
        }

        logger.info(f"Updated candidate tag: {tag_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {tag_id}",
        )
    except Exception as e:
        logger.error(f"Error updating candidate tag: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update candidate tag: {str(e)}",
        ) from e


@router.delete("/{tag_id}", tags=["Candidate Tags"])
async def delete_candidate_tag(
    tag_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Удалить тег кандидата.

    Delete a candidate tag.

    Args:
        tag_id: UUID тега / UUID of the tag
        db: Сессия базы данных / Database session

    Returns:
        JSON ответ с подтверждением удаления / JSON response confirming deletion

    Raises:
        HTTPException(404): Если тег не найден / If tag is not found
        HTTPException(500): Если произошла внутренняя ошибка / If an internal error occurs
    """
    try:
        logger.info(f"Deleting candidate tag: {tag_id}")

        # Check if tag exists / Проверяем, существует ли тег
        result = await db.execute(
            select(CandidateTag).where(CandidateTag.id == UUID(tag_id))
        )
        tag = result.scalar_one_or_none()

        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate tag not found: {tag_id}",
            )

        # Delete the tag / Удаляем тег
        await db.execute(
            delete(CandidateTag).where(CandidateTag.id == UUID(tag_id))
        )
        await db.commit()

        logger.info(f"Deleted candidate tag: {tag_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Candidate tag deleted successfully",
                "id": tag_id,
            },
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {tag_id}",
        )
    except Exception as e:
        logger.error(f"Error deleting candidate tag: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete candidate tag: {str(e)}",
        ) from e


@router.post("/candidate/{candidate_id}/assign", tags=["Candidate Tags"])
async def assign_tag_to_candidate(
    candidate_id: str,
    request: AssignTagRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Назначить тег кандидату.

    Assign a tag to a candidate.

    Args:
        candidate_id: UUID кандидата / UUID of the candidate
        request: Тело запроса с tag_id и опциональным recruiter_id / Request body with tag_id and optional recruiter_id
        db: Сессия базы данных / Database session

    Returns:
        JSON ответ с подтверждением назначения / JSON response confirming the assignment

    Raises:
        HTTPException(404): Если кандидат или тег не найден / If candidate or tag is not found
        HTTPException(409): Если тег уже назначен этому кандидату / If tag is already assigned to this candidate
        HTTPException(500): Если произошла внутренняя ошибка / If an internal error occurs
    """
    try:
        logger.info(f"Assigning tag {request.tag_id} to candidate: {candidate_id}")

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

        # Verify tag exists / Проверяем, существует ли тег
        tag_result = await db.execute(
            select(CandidateTag).where(CandidateTag.id == UUID(request.tag_id))
        )
        tag = tag_result.scalar_one_or_none()

        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag not found: {request.tag_id}",
            )

        # Check if tag is already assigned (has been added and not removed)
        # Проверяем, назначен ли уже тег (был добавлен и не удален)
        existing_assignment = await db.execute(
            select(CandidateActivity).where(
                CandidateActivity.candidate_id == UUID(candidate_id),
                CandidateActivity.activity_type == CandidateActivityType.TAG_ADDED,
                CandidateActivity.tag_id == UUID(request.tag_id),
            ).order_by(CandidateActivity.created_at.desc()).limit(1)
        )
        last_activity = existing_assignment.scalar_one_or_none()

        if last_activity:
            # Check if there's been a removal after this addition
            # Проверяем, было ли удаление после этого добавления
            removal_result = await db.execute(
                select(CandidateActivity).where(
                    CandidateActivity.candidate_id == UUID(candidate_id),
                    CandidateActivity.activity_type == CandidateActivityType.TAG_REMOVED,
                    CandidateActivity.tag_id == UUID(request.tag_id),
                    CandidateActivity.created_at > last_activity.created_at,
                ).limit(1)
            )
            removal_activity = removal_result.scalar_one_or_none()

            if not removal_activity:
                # Tag is currently assigned / Тег сейчас назначен
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Tag '{tag.tag_name}' is already assigned to this candidate",
                )

        # Create activity record for tag assignment
        # Создаем запись активности для назначения тега
        activity = CandidateActivity(
            activity_type=CandidateActivityType.TAG_ADDED,
            candidate_id=UUID(candidate_id),
            tag_id=UUID(request.tag_id),
            recruiter_id=UUID(request.recruiter_id) if request.recruiter_id else None,
            activity_data={"tag_name": tag.tag_name, "color": tag.color},
        )
        db.add(activity)
        await db.flush()

        # Update candidate's tags list / Обновляем список тегов кандидата
        if not candidate.tags:
            candidate.tags = []
        if str(UUID(request.tag_id)) not in [str(t) for t in candidate.tags]:
            candidate.tags.append(UUID(request.tag_id))

        await db.commit()

        logger.info(f"Assigned tag '{tag.tag_name}' to candidate: {candidate_id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": f"Tag '{tag.tag_name}' assigned successfully",
                "candidate_id": candidate_id,
                "tag_id": request.tag_id,
                "activity_id": str(activity.id),
            },
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid UUID format",
        )
    except Exception as e:
        logger.error(f"Error assigning tag to candidate: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign tag to candidate: {str(e)}",
        ) from e


@router.delete("/candidate/{candidate_id}/tags/{tag_id}", tags=["Candidate Tags"])
async def remove_tag_from_candidate(
    candidate_id: str,
    tag_id: str,
    recruiter_id: Optional[str] = Query(None, description="Recruiter ID removing the tag / ID рекрутера, удаляющего тег"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Удалить тег от кандидата.

    Remove a tag from a candidate.

    Args:
        candidate_id: UUID кандидата / UUID of the candidate
        tag_id: UUID тега для удаления / UUID of the tag to remove
        recruiter_id: Опциональный ID рекрутера, удаляющего тег / Optional recruiter ID who is removing the tag
        db: Сессия базы данных / Database session

    Returns:
        JSON ответ с подтверждением удаления / JSON response confirming the removal

    Raises:
        HTTPException(404): Если кандидат или тег не найден / If candidate or tag is not found
        HTTPException(409): Если тег сейчас не назначен этому кандидату / If tag is not currently assigned to this candidate
        HTTPException(500): Если произошла внутренняя ошибка / If an internal error occurs
    """
    try:
        logger.info(f"Removing tag {tag_id} from candidate: {candidate_id}")

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

        # Verify tag exists / Проверяем, существует ли тег
        tag_result = await db.execute(
            select(CandidateTag).where(CandidateTag.id == UUID(tag_id))
        )
        tag = tag_result.scalar_one_or_none()

        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag not found: {tag_id}",
            )

        # Check if tag is currently assigned
        # Проверяем, назначен ли сейчас тег
        existing_assignment = await db.execute(
            select(CandidateActivity).where(
                CandidateActivity.candidate_id == UUID(candidate_id),
                CandidateActivity.activity_type == CandidateActivityType.TAG_ADDED,
                CandidateActivity.tag_id == UUID(tag_id),
            ).order_by(CandidateActivity.created_at.desc()).limit(1)
        )
        last_activity = existing_assignment.scalar_one_or_none()

        if not last_activity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tag '{tag.tag_name}' is not assigned to this candidate",
            )

        # Check if there's been a removal after this addition
        # Проверяем, было ли удаление после этого добавления
        removal_result = await db.execute(
            select(CandidateActivity).where(
                CandidateActivity.candidate_id == UUID(candidate_id),
                CandidateActivity.activity_type == CandidateActivityType.TAG_REMOVED,
                CandidateActivity.tag_id == UUID(tag_id),
                CandidateActivity.created_at > last_activity.created_at,
            ).limit(1)
        )
        removal_activity = removal_result.scalar_one_or_none()

        if removal_activity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tag '{tag.tag_name}' has already been removed from this candidate",
            )

        # Create activity record for tag removal
        # Создаем запись активности для удаления тега
        activity = CandidateActivity(
            activity_type=CandidateActivityType.TAG_REMOVED,
            candidate_id=UUID(candidate_id),
            tag_id=UUID(tag_id),
            recruiter_id=UUID(recruiter_id) if recruiter_id else None,
            activity_data={"tag_name": tag.tag_name, "color": tag.color},
        )
        db.add(activity)
        await db.flush()

        # Update candidate's tags list / Обновляем список тегов кандидата
        if candidate.tags:
            tag_uuid = UUID(tag_id)
            candidate.tags = [t for t in candidate.tags if str(t) != str(tag_uuid)]

        await db.commit()

        logger.info(f"Removed tag '{tag.tag_name}' from candidate: {candidate_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": f"Tag '{tag.tag_name}' removed successfully",
                "candidate_id": candidate_id,
                "tag_id": tag_id,
                "activity_id": str(activity.id),
            },
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid UUID format",
        )
    except Exception as e:
        logger.error(f"Error removing tag from candidate: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove tag from candidate: {str(e)}",
        ) from e
