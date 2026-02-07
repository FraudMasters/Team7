"""
Эндпоинты API для управления заметками о кандидатах.

# Русский комментарий:
Этот модуль предоставляет эндпоинты для управления совместными заметками
и комментариями на кандидатов, включая CRUD операции для создания,
чтения, обновления и удаления заметок с поддержкой приватных
и видимых команде заметок.
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.candidate import Candidate
from models.candidate_note import CandidateNote
from models.candidate_activity import CandidateActivity, CandidateActivityType

logger = logging.getLogger(__name__)

router = APIRouter()


# ============== Pydantic Models for Request/Response ==============
# Модели Pydantic для запросов и ответов


class CandidateNoteCreate(BaseModel):
    """Модель запроса для создания заметки о кандидате / Request model for creating a candidate note."""

    candidate_id: str = Field(..., description="Candidate ID / ID кандидата")
    recruiter_id: Optional[str] = Field(None, description="Recruiter ID (author) / ID рекрутера (автор)")
    content: str = Field(..., min_length=1, max_length=10000, description="Note content / Содержимое заметки")
    is_private: bool = Field(False, description="Whether the note is private / Является ли заметка приватной")
    is_pinned: bool = Field(False, description="Whether the note is pinned / Закреплена ли заметка")


class CandidateNoteUpdate(BaseModel):
    """Модель запроса для обновления заметки / Request model for updating a candidate note."""

    content: Optional[str] = Field(None, min_length=1, max_length=10000, description="Note content / Содержимое заметки")
    is_private: Optional[bool] = Field(None, description="Whether the note is private / Является ли заметка приватной")
    is_pinned: Optional[bool] = Field(None, description="Whether the note is pinned / Закреплена ли заметка")


class CandidateNoteResponse(BaseModel):
    """Модель ответа для заметки о кандидате / Response model for a single candidate note."""

    id: str = Field(..., description="Unique identifier / Уникальный идентификатор")
    candidate_id: str = Field(..., description="Candidate ID / ID кандидата")
    recruiter_id: Optional[str] = Field(None, description="Recruiter ID (author) / ID рекрутера (автор)")
    content: str = Field(..., description="Note content / Содержимое заметки")
    is_private: bool = Field(..., description="Whether the note is private / Является ли заметка приватной")
    is_pinned: bool = Field(..., description="Whether the note is pinned / Закреплена ли заметка")
    created_at: str = Field(..., description="Creation timestamp / Время создания")
    updated_at: str = Field(..., description="Last update timestamp / Время последнего обновления")


class CandidateNoteListResponse(BaseModel):
    """Модель ответа для списка заметок / Response model for listing candidate notes."""

    candidate_id: str = Field(..., description="Candidate ID / ID кандидата")
    notes: List[CandidateNoteResponse] = Field(..., description="List of notes / Список заметок")
    total_count: int = Field(..., description="Total number of notes / Общее количество заметок")


# ============== Helper Functions ==============
# Вспомогательные функции


async def _create_note_activity(
    db: AsyncSession,
    candidate_id: UUID,
    note_id: UUID,
    activity_type: CandidateActivityType,
    recruiter_id: Optional[UUID] = None,
) -> None:
    """
    Создать запись активности о заметке.

    Create note activity record.

    Args:
        db: Сессия базы данных / Database session
        candidate_id: ID кандидата / Candidate ID
        note_id: ID заметки / Note ID
        activity_type: Тип активности / Activity type
        recruiter_id: ID рекрутера (опционально) / Recruiter ID (optional)
    """
    activity = CandidateActivity(
        activity_type=activity_type,
        candidate_id=candidate_id,
        note_id=note_id,
        recruiter_id=recruiter_id,
    )
    db.add(activity)


# ============== API Endpoints ==============
# Эндпоинты API


@router.post(
    "/",
    response_model=CandidateNoteResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Candidate Notes"],
)
async def create_candidate_note(
    request: CandidateNoteCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Создать заметку о кандидате.

    Create a candidate note.

    Этот эндпоинт создает новую заметку для кандидата, позволяя рекрутерам
    и наймерам сотрудничать путем добавления комментариев и отзывов.

    This endpoint creates a new note for a candidate, allowing recruiters
    and hiring managers to collaborate by adding comments and feedback.

    Args:
        request: Тело запроса с деталями заметки / Request body containing note details
        db: Сессия базы данных / Database session

    Returns:
        JSON ответ с созданной заметкой / JSON response with created note details

    Raises:
        HTTPException(404): Если кандидат не найден / If candidate is not found
        HTTPException(422): Если валидация не прошла / If validation fails
        HTTPException(500): Если произошла внутренняя ошибка / If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8003/api/candidate-notes/",
        ...     json={
        ...         "candidate_id": "candidate-uuid",
        ...         "content": "Great candidate, strong technical skills",
        ...         "recruiter_id": "recruiter-uuid",
        ...         "is_private": False
        ...     }
        ... )
        >>> response.status_code
        201
    """
    try:
        logger.info(f"Creating candidate note for candidate: {request.candidate_id}")

        # Verify candidate exists / Проверяем, существует ли кандидат
        candidate_result = await db.execute(
            select(Candidate).where(Candidate.id == UUID(request.candidate_id))
        )
        candidate = candidate_result.scalar_one_or_none()

        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate not found: {request.candidate_id}",
            )

        # Create new note / Создаем новую заметку
        new_note = CandidateNote(
            candidate_id=UUID(request.candidate_id),
            recruiter_id=UUID(request.recruiter_id) if request.recruiter_id else None,
            content=request.content,
            is_private=request.is_private,
            is_pinned=request.is_pinned,
        )
        db.add(new_note)
        await db.flush()

        response_data = {
            "id": str(new_note.id),
            "candidate_id": str(new_note.candidate_id),
            "recruiter_id": str(new_note.recruiter_id) if new_note.recruiter_id else None,
            "content": new_note.content,
            "is_private": new_note.is_private,
            "is_pinned": new_note.is_pinned,
            "created_at": new_note.created_at.isoformat(),
            "updated_at": new_note.updated_at.isoformat(),
        }

        # Create activity record / Создаем запись активности
        await _create_note_activity(
            db,
            UUID(request.candidate_id),
            new_note.id,
            CandidateActivityType.NOTE_ADDED,
            UUID(request.recruiter_id) if request.recruiter_id else None,
        )
        await db.commit()

        logger.info(f"Created candidate note with ID: {new_note.id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid UUID format",
        )
    except Exception as e:
        logger.error(f"Error creating candidate note: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create candidate note: {str(e)}",
        ) from e


@router.get("/", tags=["Candidate Notes"])
async def list_candidate_notes(
    candidate_id: Optional[str] = Query(None, description="Filter by candidate ID / Фильтр по ID кандидата"),
    is_private: Optional[bool] = Query(None, description="Filter by private status / Фильтр по приватности"),
    is_pinned: Optional[bool] = Query(None, description="Filter by pinned status / Фильтр по закреплению"),
    recruiter_id: Optional[str] = Query(None, description="Filter by recruiter (author) ID / Фильтр по ID рекрутера"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Получить список заметок о кандидатах с опциональной фильтрацией.

    List candidate notes with optional filters.

    Этот эндпоинт получает заметки о кандидатах с поддержкой фильтрации
    по кандидату, статусу приватности и автору.

    This endpoint retrieves candidate notes with support for filtering
    by candidate, private status, and author.

    Args:
        candidate_id: Опциональный фильтр по ID кандидата / Optional candidate ID filter
        is_private: Опциональный фильтр по приватности / Optional private status filter
        is_pinned: Опциональный фильтр по закреплению / Optional pinned status filter
        recruiter_id: Опциональный фильтр по ID рекрутера / Optional recruiter ID filter
        db: Сессия базы данных / Database session

    Returns:
        JSON ответ со списком заметок / JSON response with list of notes

    Raises:
        HTTPException(500): Если произошла внутренняя ошибка / If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8003/api/candidate-notes/?candidate_id=candidate-uuid")
        >>> response.json()
        {
            "candidate_id": "candidate-uuid",
            "notes": [...],
            "total_count": 3
        }
    """
    try:
        logger.info(
            f"Listing candidate notes - candidate_id: {candidate_id}, "
            f"is_private: {is_private}, is_pinned: {is_pinned}"
        )

        # Build query / Создаем запрос
        query = select(CandidateNote)

        if candidate_id:
            query = query.where(CandidateNote.candidate_id == UUID(candidate_id))
        if is_private is not None:
            query = query.where(CandidateNote.is_private == is_private)
        if is_pinned is not None:
            query = query.where(CandidateNote.is_pinned == is_pinned)
        if recruiter_id:
            query = query.where(CandidateNote.recruiter_id == UUID(recruiter_id))

        # Order pinned notes first, then by created_at descending
        # Сначала закрепленные заметки, потом по дате создания
        query = query.order_by(CandidateNote.is_pinned.desc(), CandidateNote.created_at.desc())

        result = await db.execute(query)
        notes = result.scalars().all()

        # If candidate_id filter was provided, use it in response
        # Если указан фильтр candidate_id, используем его в ответе
        response_candidate_id = candidate_id if candidate_id and len(notes) > 0 else "all"

        # Build response / Формируем ответ
        notes_data = []
        for note in notes:
            notes_data.append({
                "id": str(note.id),
                "candidate_id": str(note.candidate_id),
                "recruiter_id": str(note.recruiter_id) if note.recruiter_id else None,
                "content": note.content,
                "is_private": note.is_private,
                "is_pinned": note.is_pinned,
                "created_at": note.created_at.isoformat(),
                "updated_at": note.updated_at.isoformat(),
            })

        response_data = {
            "candidate_id": response_candidate_id,
            "notes": notes_data,
            "total_count": len(notes_data),
        }

        logger.info(f"Retrieved {len(notes_data)} candidate notes")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid UUID format",
        )
    except Exception as e:
        logger.error(f"Error listing candidate notes: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list candidate notes: {str(e)}",
        ) from e


@router.get("/{note_id}", tags=["Candidate Notes"])
async def get_candidate_note(
    note_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Получить конкретную заметку о кандидате по ID.

    Get a specific candidate note by ID.

    Args:
        note_id: UUID заметки / UUID of the note
        db: Сессия базы данных / Database session

    Returns:
        JSON ответ с деталями заметки / JSON response with note details

    Raises:
        HTTPException(404): Если заметка не найдена / If note is not found
        HTTPException(500): Если произошла внутренняя ошибка / If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8003/api/candidate-notes/note-uuid")
        >>> response.json()
        {
            "id": "note-uuid",
            "candidate_id": "candidate-uuid",
            "content": "Great candidate",
            ...
        }
    """
    try:
        logger.info(f"Retrieving candidate note: {note_id}")

        result = await db.execute(
            select(CandidateNote).where(CandidateNote.id == UUID(note_id))
        )
        note = result.scalar_one_or_none()

        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate note not found: {note_id}",
            )

        response_data = {
            "id": str(note.id),
            "candidate_id": str(note.candidate_id),
            "recruiter_id": str(note.recruiter_id) if note.recruiter_id else None,
            "content": note.content,
            "is_private": note.is_private,
            "is_pinned": note.is_pinned,
            "created_at": note.created_at.isoformat(),
            "updated_at": note.updated_at.isoformat(),
        }

        logger.info(f"Retrieved candidate note: {note_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {note_id}",
        )
    except Exception as e:
        logger.error(f"Error retrieving candidate note: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve candidate note: {str(e)}",
        ) from e


@router.put("/{note_id}", tags=["Candidate Notes"])
async def update_candidate_note(
    note_id: str,
    request: CandidateNoteUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Обновить заметку о кандидате.

    Update a candidate note.

    Этот эндпоинт обновляет существующую заметку о кандидате.
    Обновляются только поля, указанные в теле запроса.

    This endpoint updates an existing candidate note.
    Only the fields specified in the request body will be updated.

    Args:
        note_id: UUID заметки / UUID of the note
        request: Тело запроса с полями для обновления / Request body containing fields to update
        db: Сессия базы данных / Database session

    Returns:
        JSON ответ с обновленными деталями заметки / JSON response with updated note details

    Raises:
        HTTPException(404): Если заметка не найдена / If note is not found
        HTTPException(422): Если валидация не прошла / If validation fails
        HTTPException(500): Если произошла внутренняя ошибка / If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.put(
        ...     "http://localhost:8003/api/candidate-notes/note-uuid",
        ...     json={
        ...         "content": "Updated note content",
        ...         "is_private": True
        ...     }
        ... )
        >>> response.json()
        {
            "id": "note-uuid",
            "content": "Updated note content",
            "is_private": true,
            ...
        }
    """
    try:
        logger.info(f"Updating candidate note: {note_id}")

        # Get existing note / Получаем существующую заметку
        result = await db.execute(
            select(CandidateNote).where(CandidateNote.id == UUID(note_id))
        )
        note = result.scalar_one_or_none()

        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate note not found: {note_id}",
            )

        # Update fields if provided / Обновляем поля, если они предоставлены
        if request.content is not None:
            note.content = request.content
        if request.is_private is not None:
            note.is_private = request.is_private
        if request.is_pinned is not None:
            note.is_pinned = request.is_pinned

        await db.commit()
        await db.refresh(note)

        # Create activity record / Создаем запись активности
        await _create_note_activity(
            db,
            note.candidate_id,
            note.id,
            CandidateActivityType.NOTE_UPDATED,
        )
        await db.commit()

        response_data = {
            "id": str(note.id),
            "candidate_id": str(note.candidate_id),
            "recruiter_id": str(note.recruiter_id) if note.recruiter_id else None,
            "content": note.content,
            "is_private": note.is_private,
            "is_pinned": note.is_pinned,
            "created_at": note.created_at.isoformat(),
            "updated_at": note.updated_at.isoformat(),
        }

        logger.info(f"Updated candidate note: {note_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {note_id}",
        )
    except Exception as e:
        logger.error(f"Error updating candidate note: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update candidate note: {str(e)}",
        ) from e


@router.delete("/{note_id}", tags=["Candidate Notes"])
async def delete_candidate_note(
    note_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Удалить заметку о кандидате.

    Delete a candidate note.

    Этот эндпоинт окончательно удаляет заметку о кандидате.
    Это действие нельзя отменить.

    This endpoint permanently deletes a candidate note.
    This action cannot be undone.

    Args:
        note_id: UUID заметки / UUID of the note
        db: Сессия базы данных / Database session

    Returns:
        JSON ответ с подтверждением удаления / JSON response confirming deletion

    Raises:
        HTTPException(404): Если заметка не найдена / If note is not found
        HTTPException(500): Если произошла внутренняя ошибка / If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8003/api/candidate-notes/note-uuid")
        >>> response.json()
        {
            "message": "Candidate note deleted successfully",
            "id": "note-uuid"
        }
    """
    try:
        logger.info(f"Deleting candidate note: {note_id}")

        # Check if note exists / Проверяем, существует ли заметка
        result = await db.execute(
            select(CandidateNote).where(CandidateNote.id == UUID(note_id))
        )
        note = result.scalar_one_or_none()

        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate note not found: {note_id}",
            )

        # Store candidate_id for activity before deleting
        # Сохраняем candidate_id для активности перед удалением
        candidate_id = note.candidate_id

        # Delete the note / Удаляем заметку
        await db.execute(
            delete(CandidateNote).where(CandidateNote.id == UUID(note_id))
        )
        await db.commit()

        # Create activity record / Создаем запись активности
        await _create_note_activity(
            db,
            candidate_id,
            UUID(note_id),
            CandidateActivityType.NOTE_DELETED,
        )
        await db.commit()

        logger.info(f"Deleted candidate note: {note_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Candidate note deleted successfully",
                "id": note_id,
            },
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {note_id}",
        )
    except Exception as e:
        logger.error(f"Error deleting candidate note: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete candidate note: {str(e)}",
        ) from e
