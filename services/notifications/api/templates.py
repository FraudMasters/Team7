"""
Эндпоинты управления шаблонами для Notification Service.

# Русский комментарий:
Этот модуль предоставляет эндпоинты для создания, чтения, обновления
и удаления шаблонов email и SMS уведомлений.
"""
import logging
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services.template_service import get_template_service

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic Models / Модели Pydantic
class CreateTemplateRequest(BaseModel):
    """Запрос на создание шаблона."""

    template_type: str = Field(..., description="Тип шаблона (email, sms)")
    name: str = Field(..., description="Название шаблона (уникальное)")
    subject: Optional[str] = Field(None, description="Тема (только для email)")
    body: str = Field(..., description="Тело шаблона")
    variables: Optional[List[str]] = Field(None, description="Список переменных")
    template_blocks: Optional[Dict[str, Any]] = Field(None, description="JSON-структура блоков")
    category: Optional[str] = Field(None, description="Категория шаблона")
    pipeline_stage: Optional[str] = Field(None, description="Этап pipeline")
    language: str = Field("en", description="Язык шаблона (en, ru)")
    description: Optional[str] = Field(None, description="Описание шаблона")
    is_active: bool = Field(True, description="Флаг активности")


class UpdateTemplateRequest(BaseModel):
    """Запрос на обновление шаблона."""

    subject: Optional[str] = Field(None, description="Тема (только для email)")
    body: Optional[str] = Field(None, description="Тело шаблона")
    variables: Optional[List[str]] = Field(None, description="Список переменных")
    template_blocks: Optional[Dict[str, Any]] = Field(None, description="JSON-структура блоков")
    category: Optional[str] = Field(None, description="Категория шаблона")
    pipeline_stage: Optional[str] = Field(None, description="Этап pipeline")
    language: Optional[str] = Field(None, description="Язык шаблона")
    description: Optional[str] = Field(None, description="Описание шаблона")
    is_active: Optional[bool] = Field(None, description="Флаг активности")


class TemplateResponse(BaseModel):
    """Ответ с информацией о шаблоне."""

    id: str = Field(..., description="ID шаблона")
    template_type: str = Field(..., description="Тип шаблона (email, sms)")
    name: str = Field(..., description="Название шаблона")
    subject: Optional[str] = Field(None, description="Тема (для email)")
    body: str = Field(..., description="Тело шаблона")
    variables: Optional[List[str]] = Field(None, description="Список переменных")
    template_blocks: Optional[Dict[str, Any]] = Field(None, description="JSON-структура блоков")
    category: Optional[str] = Field(None, description="Категория")
    pipeline_stage: Optional[str] = Field(None, description="Этап pipeline")
    language: str = Field(..., description="Язык")
    description: Optional[str] = Field(None, description="Описание")
    is_active: bool = Field(..., description="Активность")
    created_at: str = Field(..., description="Время создания")
    updated_at: str = Field(..., description="Время обновления")


class TemplatesListResponse(BaseModel):
    """Ответ со списком шаблонов."""

    total: int = Field(..., description="Общее количество")
    skip: int = Field(..., description="Пропущено записей")
    limit: int = Field(..., description="Лимит записей")
    templates: List[TemplateResponse] = Field(..., description="Список шаблонов")


class PreviewTemplateRequest(BaseModel):
    """Запрос на предпросмотр шаблона."""

    template_id: str = Field(..., description="ID шаблона для предпросмотра")
    template_type: str = Field("email", description="Тип шаблона (email, sms)")
    variables: Dict[str, Any] = Field(..., description="Переменные для подстановки")


class PreviewTemplateResponse(BaseModel):
    """Ответ с отрендеренным шаблоном."""

    subject: Optional[str] = Field(None, description="Отрендеренная тема (для email)")
    body: str = Field(..., description="Отрендеренное тело")
    active_blocks: List[Dict[str, Any]] = Field(..., description="Вычисленные активные блоки")


# Helper Functions / Вспомогательные функции
def template_to_response(template, template_type: str) -> TemplateResponse:
    """
    Преобразовать модель шаблона в ответ API.

    Args:
        template: Модель EmailTemplate или SMSTemplate
        template_type: Тип шаблона ("email" или "sms")

    Returns:
        TemplateResponse с данными шаблона
    """
    return TemplateResponse(
        id=template.id,
        template_type=template_type,
        name=template.name,
        subject=getattr(template, "subject", None),
        body=template.body,
        variables=template.variables,
        template_blocks=template.template_blocks,
        category=template.category,
        pipeline_stage=template.pipeline_stage,
        language=template.language,
        description=template.description,
        is_active=template.is_active,
        created_at=template.created_at.isoformat(),
        updated_at=template.updated_at.isoformat(),
    )


# API Endpoints / API эндпоинты
@router.get("", response_model=TemplatesListResponse, status_code=status.HTTP_200_OK)
async def list_templates(
    template_type: str = Query("email", description="Тип шаблона (email, sms)"),
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    pipeline_stage: Optional[str] = Query(None, description="Фильтр по этапу pipeline"),
    language: Optional[str] = Query(None, description="Фильтр по языку"),
    is_active: Optional[bool] = Query(None, description="Фильтр по активности"),
    skip: int = Query(0, ge=0, description="Пропустить записей"),
    limit: int = Query(100, ge=1, le=1000, description="Лимит записей"),
    db: AsyncSession = Depends(get_db),
):
    """
    Получить список шаблонов с фильтрацией.

    Args:
        template_type: Тип шаблона (email или sms)
        category: Фильтр по категории
        pipeline_stage: Фильтр по этапу pipeline
        language: Фильтр по языку
        is_active: Фильтр по активности
        skip: Количество пропускаемых записей
        limit: Максимальное количество записей
        db: Сессия базы данных

    Returns:
        TemplatesListResponse со списком шаблонов

    Example:
        >>> curl "http://localhost:8008/api/templates?template_type=email&category=recruitment"
        {"total": 5, "skip": 0, "limit": 100, "templates": [...]}
    """
    try:
        service = get_template_service()

        templates = await service.list_templates(
            db=db,
            template_type=template_type,
            category=category,
            pipeline_stage=pipeline_stage,
            language=language,
            is_active=is_active,
            skip=skip,
            limit=limit,
        )

        response_templates = [
            template_to_response(template, template_type) for template in templates
        ]

        return TemplatesListResponse(
            total=len(response_templates),
            skip=skip,
            limit=limit,
            templates=response_templates,
        )

    except Exception as e:
        logger.error(f"Error listing templates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить список шаблонов: {str(e)}",
        )


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    request: CreateTemplateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Создать новый шаблон.

    Args:
        request: Данные для создания шаблона
        db: Сессия базы данных

    Returns:
        TemplateResponse с созданным шаблоном

    Raises:
        HTTPException: Если шаблон с таким именем уже существует или данные некорректны

    Example:
        >>> curl -X POST "http://localhost:8008/api/templates" \\
        ...   -H "Content-Type: application/json" \\
        ...   -d '{"template_type":"email","name":"welcome","subject":"Welcome!","body":"Hello {name}"}'
        {"id": "...", "name": "welcome", ...}
    """
    try:
        service = get_template_service()

        # Валидация для email шаблонов
        if request.template_type == "email" and not request.subject:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Subject is required for email templates",
            )

        template = await service.create_template(
            db=db,
            template_type=request.template_type,
            name=request.name,
            subject=request.subject,
            body=request.body,
            variables=request.variables,
            template_blocks=request.template_blocks,
            category=request.category,
            pipeline_stage=request.pipeline_stage,
            language=request.language,
            description=request.description,
            is_active=request.is_active,
        )

        logger.info(f"Created template: name={request.name}, type={request.template_type}, id={template.id}")

        return template_to_response(template, request.template_type)

    except ValueError as e:
        logger.warning(f"Validation error creating template: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error creating template: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось создать шаблон: {str(e)}",
        )


@router.get("/{template_id}", response_model=TemplateResponse, status_code=status.HTTP_200_OK)
async def get_template(
    template_id: str,
    template_type: str = Query("email", description="Тип шаблона (email, sms)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Получить шаблон по ID.

    Args:
        template_id: ID шаблона
        template_type: Тип шаблона (email или sms)
        db: Сессия базы данных

    Returns:
        TemplateResponse с данными шаблона

    Raises:
        HTTPException: Если шаблон не найден

    Example:
        >>> curl "http://localhost:8008/api/templates/abc-123?template_type=email"
        {"id": "abc-123", "name": "welcome", ...}
    """
    try:
        service = get_template_service()

        template = await service.get_template(
            db=db,
            template_id=template_id,
            template_type=template_type,
        )

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Шаблон не найден: id={template_id}",
            )

        return template_to_response(template, template_type)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить шаблон: {str(e)}",
        )


@router.put("/{template_id}", response_model=TemplateResponse, status_code=status.HTTP_200_OK)
async def update_template(
    template_id: str,
    request: UpdateTemplateRequest,
    template_type: str = Query("email", description="Тип шаблона (email, sms)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Обновить существующий шаблон.

    Args:
        template_id: ID шаблона
        request: Данные для обновления
        template_type: Тип шаблона (email или sms)
        db: Сессия базы данных

    Returns:
        TemplateResponse с обновленным шаблоном

    Raises:
        HTTPException: Если шаблон не найден

    Example:
        >>> curl -X PUT "http://localhost:8008/api/templates/abc-123" \\
        ...   -H "Content-Type: application/json" \\
        ...   -d '{"body":"Updated body","is_active":false}'
        {"id": "abc-123", "body": "Updated body", ...}
    """
    try:
        service = get_template_service()

        # Подготовка обновлений (только заданные поля)
        updates = {}
        if request.subject is not None:
            updates["subject"] = request.subject
        if request.body is not None:
            updates["body"] = request.body
        if request.variables is not None:
            updates["variables"] = request.variables
        if request.template_blocks is not None:
            updates["template_blocks"] = request.template_blocks
        if request.category is not None:
            updates["category"] = request.category
        if request.pipeline_stage is not None:
            updates["pipeline_stage"] = request.pipeline_stage
        if request.language is not None:
            updates["language"] = request.language
        if request.description is not None:
            updates["description"] = request.description
        if request.is_active is not None:
            updates["is_active"] = request.is_active

        template = await service.update_template(
            db=db,
            template_id=template_id,
            template_type=template_type,
            **updates,
        )

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Шаблон не найден: id={template_id}",
            )

        logger.info(f"Updated template: id={template_id}, type={template_type}")

        return template_to_response(template, template_type)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось обновить шаблон: {str(e)}",
        )


@router.delete("/{template_id}", status_code=status.HTTP_200_OK)
async def delete_template(
    template_id: str,
    template_type: str = Query("email", description="Тип шаблона (email, sms)"),
    hard_delete: bool = Query(False, description="Жесткое удаление (иначе мягкое)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Удалить шаблон.

    По умолчанию выполняется мягкое удаление (is_active=False).
    Используйте hard_delete=true для полного удаления из базы данных.

    Args:
        template_id: ID шаблона
        template_type: Тип шаблона (email или sms)
        hard_delete: Флаг жесткого удаления
        db: Сессия базы данных

    Returns:
        JSONResponse с подтверждением удаления

    Raises:
        HTTPException: Если шаблон не найден

    Example:
        >>> curl -X DELETE "http://localhost:8008/api/templates/abc-123?template_type=email"
        {"message": "Шаблон успешно удален", "deleted": true}
    """
    try:
        service = get_template_service()

        deleted = await service.delete_template(
            db=db,
            template_id=template_id,
            template_type=template_type,
            soft_delete=not hard_delete,
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Шаблон не найден: id={template_id}",
            )

        delete_type = "жестко" if hard_delete else "мягко"
        logger.info(f"Deleted template ({delete_type}): id={template_id}, type={template_type}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Шаблон успешно удален",
                "deleted": True,
                "hard_delete": hard_delete,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось удалить шаблон: {str(e)}",
        )


@router.post("/preview", response_model=PreviewTemplateResponse, status_code=status.HTTP_200_OK)
async def preview_template(
    request: PreviewTemplateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Предпросмотр шаблона с подстановкой переменных.

    Отрендерить шаблон с заданными переменными для предварительного просмотра
    результата без фактической отправки уведомления.

    Args:
        request: Данные для предпросмотра (template_id, template_type, variables)
        db: Сессия базы данных

    Returns:
        PreviewTemplateResponse с отрендеренным контентом

    Raises:
        HTTPException: Если шаблон не найден или произошла ошибка рендеринга

    Example:
        >>> curl -X POST "http://localhost:8008/api/templates/preview" \\
        ...   -H "Content-Type: application/json" \\
        ...   -d '{"template_id":"abc-123","template_type":"email","variables":{"name":"John"}}'
        {"subject": "Welcome John", "body": "Hello John!", "active_blocks": [...]}
    """
    try:
        service = get_template_service()

        rendered = await service.render_template(
            db=db,
            template_id=request.template_id,
            template_type=request.template_type,
            variables=request.variables,
        )

        logger.info(
            f"Previewed template: id={request.template_id}, type={request.template_type}, "
            f"vars={list(request.variables.keys())}"
        )

        return PreviewTemplateResponse(
            subject=rendered.get("subject"),
            body=rendered["body"],
            active_blocks=rendered["active_blocks"],
        )

    except ValueError as e:
        logger.warning(f"Validation error previewing template: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error previewing template: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось выполнить предпросмотр шаблона: {str(e)}",
        )
