"""
API endpoints для управления вакансиями.

# Русский комментарий:
Этот модуль предоставляет endpoints для создания, просмотра, обновления
и удаления вакансий, определяющих профиль искомых кандидатов.
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.vacancy import Vacancy

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models / Модели запроса/ответа
class VacancyCreateRequest(BaseModel):
    """Модель запроса для создания новой вакансии."""

    title: str = Field(..., min_length=3, max_length=255, description="Должность")
    description: str = Field(..., min_length=10, description="Описание вакансии и обязанности")
    required_skills: list[str] = Field(..., min_items=1, description="Обязательные технические навыки")
    min_experience_months: Optional[int] = Field(None, ge=0, description="Минимальный опыт в месяцах")
    additional_requirements: Optional[list[str]] = Field(default_factory=list, description="Желательные навыки")
    industry: Optional[str] = Field(None, max_length=100, description="Отрасль")
    work_format: Optional[str] = Field(None, max_length=50, description="Формат работы: удаленно, офис, гибрид")
    location: Optional[str] = Field(None, max_length=255, description="Местоположение")
    salary_min: Optional[int] = Field(None, ge=0, description="Минимальная зарплата")
    salary_max: Optional[int] = Field(None, ge=0, description="Максимальная зарплата")
    english_level: Optional[str] = Field(None, max_length=50, description="Требуемый уровень английского")
    employment_type: Optional[str] = Field(None, max_length=50, description="Тип занятости: полный день, часть времени, контракт")
    external_id: Optional[str] = Field(None, max_length=255, description="ID внешней системы")
    source: Optional[str] = Field("manual", max_length=50, description="Источник вакансии")


class VacancyUpdateRequest(BaseModel):
    """Модель запроса для обновления вакансии."""

    title: Optional[str] = Field(None, min_length=3, max_length=255, description="Должность")
    description: Optional[str] = Field(None, min_length=10, description="Описание вакансии")
    required_skills: Optional[list[str]] = Field(None, min_items=1, description="Обязательные навыки")
    min_experience_months: Optional[int] = Field(None, ge=0, description="Минимальный опыт")
    additional_requirements: Optional[list[str]] = Field(None, description="Желательные навыки")
    industry: Optional[str] = Field(None, max_length=100, description="Отрасль")
    work_format: Optional[str] = Field(None, max_length=50, description="Формат работы")
    location: Optional[str] = Field(None, max_length=255, description="Местоположение")
    salary_min: Optional[int] = Field(None, ge=0, description="Минимальная зарплата")
    salary_max: Optional[int] = Field(None, ge=0, description="Максимальная зарплата")
    english_level: Optional[str] = Field(None, max_length=50, description="Уровень английского")
    employment_type: Optional[str] = Field(None, max_length=50, description="Тип занятости")


class VacancyResponse(BaseModel):
    """Модель ответа для вакансии."""

    id: str = Field(..., description="ID вакансии")
    title: str = Field(..., description="Должность")
    description: str = Field(..., description="Описание вакансии")
    required_skills: list[str] = Field(..., description="Обязательные навыки")
    min_experience_months: Optional[int] = Field(None, description="Минимальный опыт")
    additional_requirements: list[str] = Field(..., description="Дополнительные навыки")
    industry: Optional[str] = Field(None, description="Отрасль")
    work_format: Optional[str] = Field(None, description="Формат работы")
    location: Optional[str] = Field(None, description="Местоположение")
    salary_min: Optional[int] = Field(None, description="Мин. зарплата")
    salary_max: Optional[int] = Field(None, description="Макс. зарплата")
    english_level: Optional[str] = Field(None, description="Уровень английского")
    employment_type: Optional[str] = Field(None, description="Тип занятости")
    external_id: Optional[str] = Field(None, description="Внешний ID")
    source: Optional[str] = Field(None, description="Источник")
    created_at: str = Field(..., description="Время создания")
    updated_at: str = Field(..., description="Время обновления")


def _vacancy_to_response(vacancy: Vacancy) -> dict:
    """Преобразовать модель Vacancy в словарь ответа."""
    return {
        "id": str(vacancy.id),
        "title": vacancy.title,
        "description": vacancy.description,
        "required_skills": vacancy.required_skills or [],
        "min_experience_months": vacancy.min_experience_months,
        "additional_requirements": vacancy.additional_requirements or [],
        "industry": vacancy.industry,
        "work_format": vacancy.work_format,
        "location": vacancy.location,
        "salary_min": vacancy.salary_min,
        "salary_max": vacancy.salary_max,
        "english_level": vacancy.english_level,
        "employment_type": vacancy.employment_type,
        "external_id": vacancy.external_id,
        "source": vacancy.source,
        "created_at": vacancy.created_at.isoformat() if vacancy.created_at else None,
        "updated_at": vacancy.updated_at.isoformat() if vacancy.updated_at else None,
    }


@router.post(
    "/",
    response_model=VacancyResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Vacancies"],
)
async def create_vacancy(
    request: Request,
    vacancy: VacancyCreateRequest,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Создать новую вакансию.

    Этот endpoint позволяет рекрутерам создать новую вакансию,
    определяющую профиль искомых кандидатов.

    Args:
        request: Объект запроса FastAPI
        vacancy: Данные вакансии из тела запроса
        db: Сессия базы данных

    Returns:
        JSON ответ с деталями созданной вакансии

    Example:
        >>> vacancy_data = {
        ...     "title": "Senior Java Developer",
        ...     "description": "We are looking for...",
        ...     "required_skills": ["Java", "Spring", "PostgreSQL"],
        ...     "min_experience_months": 36
        ... }
        >>> response = requests.post("http://localhost:8004/api/vacancies/", json=vacancy_data)
    """
    try:
        # Create new Vacancy instance / Создаем новый экземпляр Vacancy
        new_vacancy = Vacancy(
            title=vacancy.title,
            description=vacancy.description,
            required_skills=vacancy.required_skills,
            min_experience_months=vacancy.min_experience_months,
            additional_requirements=vacancy.additional_requirements or [],
            industry=vacancy.industry,
            work_format=vacancy.work_format,
            location=vacancy.location,
            salary_min=vacancy.salary_min,
            salary_max=vacancy.salary_max,
            english_level=vacancy.english_level,
            employment_type=vacancy.employment_type,
            external_id=vacancy.external_id,
            source=vacancy.source,
        )

        db.add(new_vacancy)
        await db.commit()
        await db.refresh(new_vacancy)

        logger.info(f"Created vacancy: {new_vacancy.id} - {new_vacancy.title}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=_vacancy_to_response(new_vacancy),
        )

    except Exception as e:
        logger.error(f"Error creating vacancy: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create vacancy: {str(e)}",
        ) from e


@router.get("/", response_model=list[VacancyResponse], tags=["Vacancies"])
async def list_vacancies(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Получить список всех вакансий.

    Возвращает пагинированный список всех вакансий.

    Args:
        request: Объект запроса FastAPI
        skip: Количество записей для пропуска (пагинация)
        limit: Максимальное количество записей для возврата
        db: Сессия базы данных

    Returns:
        JSON ответ со списком вакансий

    Example:
        >>> response = requests.get("http://localhost:8004/api/vacancies/?limit=10")
        >>> vacancies = response.json()
    """
    try:
        # Query vacancies from database / Запрашиваем вакансии из базы данных
        query = select(Vacancy).order_by(Vacancy.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        vacancies = result.scalars().all()

        # Convert to response format / Преобразуем в формат ответа
        vacancies_list = [_vacancy_to_response(v) for v in vacancies]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=vacancies_list,
        )

    except Exception as e:
        logger.error(f"Error listing vacancies: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list vacancies: {str(e)}",
        ) from e


@router.get(
    "/{vacancy_id}",
    response_model=VacancyResponse,
    tags=["Vacancies"],
)
async def get_vacancy(
    vacancy_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Получить вакансию по ID.

    Args:
        vacancy_id: UUID вакансии
        db: Сессия базы данных

    Returns:
        JSON ответ с деталями вакансии

    Raises:
        HTTPException(404): Если вакансия не найдена
    """
    try:
        # Parse UUID / Парсим UUID
        try:
            vacancy_uuid = UUID(vacancy_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid vacancy ID format: {vacancy_id}",
            )

        # Query vacancy / Запрашиваем вакансию
        query = select(Vacancy).where(Vacancy.id == vacancy_uuid)
        result = await db.execute(query)
        vacancy = result.scalar_one_or_none()

        if not vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vacancy with ID '{vacancy_id}' not found",
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=_vacancy_to_response(vacancy),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vacancy: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get vacancy: {str(e)}",
        ) from e


@router.put(
    "/{vacancy_id}",
    response_model=VacancyResponse,
    tags=["Vacancies"],
)
async def update_vacancy(
    vacancy_id: str,
    vacancy_update: VacancyUpdateRequest,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Обновить вакансию.

    Args:
        vacancy_id: UUID вакансии
        vacancy_update: Данные для обновления
        db: Сессия базы данных

    Returns:
        JSON ответ с обновленными деталями вакансии

    Raises:
        HTTPException(404): Если вакансия не найдена
    """
    try:
        # Parse UUID / Парсим UUID
        try:
            vacancy_uuid = UUID(vacancy_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid vacancy ID format: {vacancy_id}",
            )

        # Query vacancy / Запрашиваем вакансию
        query = select(Vacancy).where(Vacancy.id == vacancy_uuid)
        result = await db.execute(query)
        vacancy = result.scalar_one_or_none()

        if not vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vacancy with ID '{vacancy_id}' not found",
            )

        # Update fields / Обновляем поля
        update_data = vacancy_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(vacancy, field, value)

        await db.commit()
        await db.refresh(vacancy)

        logger.info(f"Updated vacancy: {vacancy.id} - {vacancy.title}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=_vacancy_to_response(vacancy),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating vacancy: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update vacancy: {str(e)}",
        ) from e


@router.delete(
    "/{vacancy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Vacancies"],
)
async def delete_vacancy(
    vacancy_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Удалить вакансию.

    Args:
        vacancy_id: UUID вакансии
        db: Сессия базы данных

    Returns:
        Пустой ответ с кодом 204

    Raises:
        HTTPException(404): Если вакансия не найдена
    """
    try:
        # Parse UUID / Парсим UUID
        try:
            vacancy_uuid = UUID(vacancy_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid vacancy ID format: {vacancy_id}",
            )

        # Query vacancy / Запрашиваем вакансию
        query = select(Vacancy).where(Vacancy.id == vacancy_uuid)
        result = await db.execute(query)
        vacancy = result.scalar_one_or_none()

        if not vacancy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vacancy with ID '{vacancy_id}' not found",
            )

        # Delete vacancy / Удаляем вакансию
        await db.delete(vacancy)
        await db.commit()

        logger.info(f"Deleted vacancy: {vacancy_id}")

        return JSONResponse(
            status_code=status.HTTP_204_NO_CONTENT,
            content=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting vacancy: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete vacancy: {str(e)}",
        ) from e
