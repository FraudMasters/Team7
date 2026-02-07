"""
Эндпоинты API для загрузки и управления резюме.

# Русский комментарий:
Этот модуль предоставляет эндпоинты для загрузки файлов резюме (PDF, DOCX),
валидации формата и размера файлов, хранения файлов и создания записей в базе данных.
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_db
from models.resume import Resume, ResumeStatus

# Импорт локальных модулей парсеров / Import local parser modules
from parsers.pdf_parser import extract_text_from_pdf, validate_pdf_file
from parsers.docx_parser import extract_text_from_docx, validate_docx_file

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()

# Директория для хранения загруженных резюме / Directory for storing uploaded resumes
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# Модели Pydantic для запросов и ответов / Pydantic models for requests and responses

class ResumeUploadResponse(BaseModel):
    """Модель ответа для эндпоинта загрузки резюме / Response model for resume upload endpoint."""

    id: str = Field(..., description="Уникальный идентификатор загруженного резюме / Unique identifier for the uploaded resume")
    filename: str = Field(..., description="Исходное имя файла резюме / Original filename of the uploaded resume")
    status: str = Field(..., description="Статус обработки резюме / Processing status of the resume")
    message: str = Field(..., description="Сообщение об успехе / Success message")


class ResumeListItem(BaseModel):
    """Модель ответа для одного резюме в списке / Response model for a single resume in a list."""

    id: str = Field(..., description="Уникальный идентификатор / Unique identifier")
    filename: str = Field(..., description="Имя файла / Filename")
    status: str = Field(..., description="Статус обработки / Processing status")
    created_at: str = Field(..., description="Время создания / Creation timestamp")
    language: Optional[str] = Field(None, description="Обнаруженный язык / Detected language")


class ResumeStatusUpdate(BaseModel):
    """Модель запроса для обновления статуса резюме / Request model for updating resume status."""

    status: str = Field(..., description="Новое значение статуса (new, reviewed, interview, offered, hired) / New status value")


# Вспомогательные функции / Helper functions

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


def validate_file_type(filename: str, content_type: str, locale: str = "en") -> None:
    """
    Валидировать что тип файла разрешен.

    Validate that the file type is allowed.

    Args:
        filename: Имя загруженного файла / Name of the uploaded file
        content_type: MIME тип файла / MIME type of the file
        locale: Код языка для переведенных сообщений об ошибках / Language code for translated error messages

    Raises:
        HTTPException: Если тип файла не разрешен / If file type is not allowed
    """
    # Разрешенные расширения файлов / Allowed file extensions
    allowed_extensions = settings.allowed_file_types.split(",")
    file_ext = Path(filename).suffix.lower()

    if file_ext not in allowed_extensions:
        allowed = ", ".join(allowed_extensions)
        error_msg = f"Unsupported file type '{file_ext}'. Allowed types: {allowed}"
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=error_msg,
        )

    # Проверка content_type для дополнительной валидации / Check content type for additional validation
    allowed_content_types = {
        ".pdf": ["application/pdf"],
        ".docx": [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        ],
    }

    if file_ext in allowed_content_types:
        if content_type not in allowed_content_types[file_ext]:
            logger.warning(
                f"Content type mismatch for {filename}: {content_type} not in {allowed_content_types[file_ext]}"
            )


def validate_file_size(file_size: int, locale: str = "en") -> None:
    """
    Валидировать что размер файла в пределах допустимого.

    Validate that the file size is within allowed limits.

    Args:
        file_size: Размер файла в байтах / Size of the file in bytes
        locale: Код языка для переведенных сообщений об ошибках / Language code for translated error messages

    Raises:
        HTTPException: Если размер файла превышает максимально допустимый / If file size exceeds maximum allowed
    """
    max_size = settings.max_file_size_bytes
    if file_size > max_size:
        max_mb = settings.max_file_size_mb
        size_mb = file_size / 1024 / 1024
        error_msg = f"File size ({size_mb:.2f}MB) exceeds maximum allowed size ({max_mb}MB)"
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=error_msg,
        )


# Эндпоинты API / API endpoints

@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Resumes"],
)
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Загрузить файл резюме для анализа.

    Upload a resume file for analysis.

    Этот эндпоинт принимает файлы резюме в форматах PDF или DOCX, валидирует тип и
    размер файла, сохраняет файл и создает запись в базе данных для отслеживания.

    This endpoint accepts resume files in PDF or DOCX format, validates the file
    type and size, stores the file, and creates a database record for tracking.

    Args:
        request: Объект запроса FastAPI (для заголовка Accept-Language) / FastAPI request object (for Accept-Language header)
        file: Загруженный файл резюме (PDF или DOCX) / Uploaded resume file (PDF or DOCX)
        db: Сессия базы данных / Database session

    Returns:
        JSON ответ с ID резюме, именем файла и статусом / JSON response with resume ID, filename, and status

    Raises:
        HTTPException(415): Если тип файла не поддерживается / If file type is not supported
        HTTPException(413): Если размер файла превышает максимально допустимый / If file size exceeds maximum allowed
        HTTPException(500): Если сохранение файла или операция с БД не удалась / If file storage or database operation fails

    Examples:
        >>> import requests
        >>> with open("resume.pdf", "rb") as f:
        ...     response = requests.post("http://localhost:8001/api/resumes/upload", files={"file": f})
        >>> response.json()
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "filename": "resume.pdf",
            "status": "pending",
            "message": "Resume uploaded successfully"
        }
    """
    # Извлечь locale из заголовка Accept-Language / Extract locale from Accept-Language header
    locale = _extract_locale(request)

    try:
        # Прочитать содержимое файла / Read file content
        file_content = await file.read()
        file_size = len(file_content)

        logger.info(f"Received file upload: {file.filename} ({file_size} bytes)")

        # Валидировать тип файла / Validate file type
        validate_file_type(file.filename or "unknown", file.content_type or "application/octet-stream", locale)

        # Валидировать размер файла / Validate file size
        validate_file_size(file_size, locale)

        # Сгенерировать UUID для резюме / Generate UUID for the resume
        resume_id = uuid4()
        safe_filename = Path(file.filename or "resume").name
        file_extension = Path(safe_filename).suffix
        stored_filename = f"{resume_id}{file_extension}"
        file_path = UPLOAD_DIR / stored_filename

        # Сохранить файл на диск / Save file to disk
        logger.info(f"Saving file to: {file_path}")
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Создать запись в базе данных / Create database record
        new_resume = Resume(
            id=resume_id,
            filename=file.filename or "unknown",
            file_path=str(file_path),
            content_type=file.content_type or "application/octet-stream",
            status=ResumeStatus.PENDING,
        )

        db.add(new_resume)
        await db.commit()
        await db.refresh(new_resume)

        response_data = {
            "id": str(resume_id),
            "filename": file.filename or "unknown",
            "status": ResumeStatus.PENDING.value,
            "message": "Resume uploaded successfully",
        }

        logger.info(f"Resume uploaded successfully: {resume_id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        # Перебросить HTTP исключения (ошибки валидации) / Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        logger.error(f"Error uploading resume: {e}", exc_info=True)
        await db.rollback()
        error_msg = "Failed to upload file. Please try again"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e


@router.get(
    "/",
    response_model=List[ResumeListItem],
    tags=["Resumes"],
)
async def list_resumes(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Получить список всех резюме в базе данных.

    List all resumes in the database.

    Возвращает пагинированный список всех резюме с их базовой информацией.

    Returns a paginated list of all resumes with their basic information.

    Args:
        request: Объект запроса FastAPI / FastAPI request object
        skip: Количество записей для пропуска (пагинация) / Number of records to skip (pagination)
        limit: Максимальное количество записей для возврата / Maximum number of records to return
        db: Сессия базы данных / Database session

    Returns:
        JSON ответ со списком резюме / JSON response with list of resumes

    Example:
        >>> response = requests.get("http://localhost:8001/api/resumes/?limit=10")
        >>> resumes = response.json()
    """
    try:
        # Запрос резюме с сортировкой по времени создания / Query resumes ordered by creation time
        query = select(Resume).order_by(Resume.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        resumes = result.scalars().all()

        # Конвертация в формат ответа / Convert to response format
        resumes_list = []
        for resume in resumes:
            resumes_list.append({
                "id": str(resume.id),
                "filename": resume.filename,
                "status": resume.status.value.lower(),  # Возвращаем в lowercase для фронтенда
                "created_at": resume.created_at.isoformat() if resume.created_at else None,
                "language": resume.language,
            })

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=resumes_list,
        )

    except Exception as e:
        logger.error(f"Error listing resumes: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list resumes: {str(e)}",
        ) from e


@router.get("/{resume_id}", tags=["Resumes"])
async def get_resume(
    request: Request,
    resume_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Получить информацию о резюме по ID с извлеченным текстом.

    Get resume information by ID with extracted text.

    Args:
        request: Объект запроса FastAPI / FastAPI request object
        resume_id: Уникальный идентификатор резюме / Unique identifier of the resume
        db: Сессия базы данных / Database session

    Returns:
        JSON ответ с деталями резюме и извлеченным текстом / JSON response with resume details and extracted text

    Raises:
        HTTPException(404): Если резюме не найдено / If resume is not found
        HTTPException(500): Если запрос к БД не удался / If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8001/api/resumes/123e4567-e89b-12d3-a456-426614174000")
        >>> response.json()
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "filename": "resume.pdf",
            "status": "completed",
            "raw_text": "Resume content here..."
        }
    """
    # Извлечь locale из заголовка Accept-Language / Extract locale from Accept-Language header
    locale = _extract_locale(request)

    try:
        # Найти резюме в базе данных / Find resume in database
        try:
            resume_uuid = UUID(resume_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid resume ID format: {resume_id}"
            )

        query = select(Resume).where(Resume.id == resume_uuid)
        result = await db.execute(query)
        resume = result.scalar_one_or_none()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume not found: {resume_id}"
            )

        # Определить путь к файлу / Determine file path
        file_path = Path(resume.file_path)

        if not file_path.exists():
            logger.warning(f"Resume file not found: {file_path}")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "id": resume_id,
                    "filename": resume.filename,
                    "status": "error",
                    "message": "Resume file not found",
                    "raw_text": "",
                },
            )

        # Извлечь текст из резюме / Extract text from resume
        text = ""
        try:
            if file_path.suffix == ".pdf":
                extract_result = extract_text_from_pdf(str(file_path))
                text = extract_result.get("text") or ""
            elif file_path.suffix == ".docx":
                extract_result = extract_text_from_docx(str(file_path))
                text = extract_result.get("text") or ""
            else:
                text = ""
        except Exception as e:
            logger.error(f"Error extracting text from resume: {e}")
            text = ""

        # Обновить raw_text в базе данных если не установлен / Update raw_text in database if not set
        if not resume.raw_text and text:
            resume.raw_text = text
            await db.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": resume_id,
                "filename": resume.filename,
                "status": resume.status.value.lower(),
                "message": "Resume retrieved successfully",
                "raw_text": text,
                "language": resume.language,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting resume {resume_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get resume: {str(e)}",
        ) from e


@router.patch("/{resume_id}", tags=["Resumes"])
async def update_resume_status(
    request: Request,
    resume_id: str,
    status_update: ResumeStatusUpdate,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Обновить статус резюме (для перетаскивания на канбан-доске).

    Update resume status (for Kanban board drag-and-drop).

    Этот эндпоинт позволяет обновлять статус резюме для поддержки
    рабочего процесса канбан-доски.

    This endpoint allows updating a resume's status to support the Kanban board workflow.

    Валидные статусы: new, reviewed, interview, offered, hired, pending, completed, processing, failed

    Args:
        request: Объект запроса FastAPI / FastAPI request object
        resume_id: UUID резюме для обновления / UUID of the resume to update
        status_update: Тело запроса содержащее новый статус / Request body containing new status
        db: Сессия базы данных / Database session

    Returns:
        JSON ответ с обновленными деталями резюме / JSON response with updated resume details

    Raises:
        HTTPException(404): Если резюме не найдено / If resume not found
        HTTPException(422): Если неверное значение статуса / If invalid status value

    Examples:
        >>> import requests
        >>> response = requests.patch(
        ...     "http://localhost:8001/api/resumes/123e4567-e89b-12d3-a456-426614174000",
        ...     json={"status": "interview"}
        ... )
        >>> response.json()
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "status": "interview"
        }
    """
    locale = _extract_locale(request)

    # Валидировать значение статуса / Validate status value
    valid_statuses = {
        "new", "reviewed", "interview", "offered", "hired",
        "pending", "completed", "processing", "failed"
    }
    status_lower = status_update.status.lower()
    if status_lower not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status '{status_update.status}'. Valid values: {', '.join(sorted(valid_statuses))}"
        )

    # Маппинг lowercase к uppercase для базы данных / Map lowercase to uppercase for database
    status_map = {
        "new": "NEW",
        "reviewed": "REVIEWED",
        "interview": "INTERVIEW",
        "offered": "OFFERED",
        "hired": "HIRED",
        "pending": "PENDING",
        "completed": "COMPLETED",
        "processing": "PROCESSING",
        "failed": "FAILED",
    }
    normalized_status = status_map.get(status_lower, status_update.status.upper())

    try:
        # Найти резюме / Find resume
        try:
            resume_uuid = UUID(resume_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid resume ID format: {resume_id}"
            )

        query = select(Resume).where(Resume.id == resume_uuid)
        result = await db.execute(query)
        resume = result.scalar_one_or_none()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume not found: {resume_id}"
            )

        # Сохранить старый статус для логов / Store old status for logging
        old_status = resume.status.value if resume.status else None

        # Обновить статус / Update status
        new_status = ResumeStatus(normalized_status)
        resume.status = new_status

        await db.commit()
        await db.refresh(resume)

        logger.info(f"Updated resume {resume_id} status from {old_status} to {new_status.value}")

        # Возвращаем lowercase статус для совместимости с фронтендом / Return lowercase status for frontend compatibility
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(resume.id),
                "status": status_lower,
                "filename": resume.filename,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating resume status {resume_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update resume status: {str(e)}",
        ) from e


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Resumes"])
async def delete_resume(
    request: Request,
    resume_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Удалить резюме по ID.

    Delete a resume by ID.

    Args:
        request: Объект запроса FastAPI / FastAPI request object
        resume_id: UUID резюме для удаления / UUID of the resume to delete
        db: Сессия базы данных / Database session

    Returns:
        204 No Content при успехе / 204 No Content on success

    Raises:
        HTTPException(404): Если резюме не найдено / If resume not found

    Example:
        >>> response = requests.delete("http://localhost:8001/api/resumes/123")
        >>> response.status_code
        204
    """
    try:
        # Найти резюме в базе данных / Find resume in database
        try:
            resume_uuid = UUID(resume_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid resume ID format: {resume_id}"
            )

        query = select(Resume).where(Resume.id == resume_uuid)
        result = await db.execute(query)
        resume = result.scalar_one_or_none()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume not found: {resume_id}"
            )

        file_path = Path(resume.file_path) if resume.file_path else None

        # Удалить из базы данных / Delete from database
        await db.delete(resume)
        await db.commit()

        # Удалить файл с диска если существует / Delete file from disk if exists
        if file_path and file_path.exists():
            file_path.unlink()

        logger.info(f"Deleted resume: {resume_id}")

        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting resume {resume_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete resume: {str(e)}",
        ) from e
