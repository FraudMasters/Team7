"""
Эндпоинты уведомлений для Notification Service.

# Русский комментарий:
Этот модуль предоставляет эндпоинты для отправки email, SMS, webhook
и внутриприкладных уведомлений, а также для управления историей уведомлений.
"""
import logging
import time
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from database import get_db
from models.notification import Notification, NotificationStatus, NotificationType, NotificationPriority
from models.email_template import EmailTemplate
from services.template_service import TemplateService

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic Models / Мод Pydantic
class SendNotificationRequest(BaseModel):
    """Запрос на отправку уведомления."""

    type: str = Field(..., description="Тип уведомления (email, sms, webhook)")
    recipient: str = Field(..., description="Получатель уведомления")
    subject: Optional[str] = Field(None, description="Тема уведомления")
    body: Optional[str] = Field(None, description="Тело уведомления")
    priority: str = Field("normal", description="Приоритет (low, normal, high, urgent)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Дополнительные метаданные")
    template_name: Optional[str] = Field(None, description="Имя шаблона email")
    template_vars: Optional[Dict[str, Any]] = Field(None, description="Переменные для шаблона")


class NotificationResponse(BaseModel):
    """Ответ с информацией об уведомлении."""

    id: str = Field(..., description="ID уведомления")
    type: str = Field(..., description="Тип уведомления")
    recipient: str = Field(..., description="Получатель")
    status: str = Field(..., description="Статус доставки")
    priority: str = Field(..., description="Приоритет")
    subject: Optional[str] = Field(None, description="Тема")
    sent_at: Optional[str] = Field(None, description="Время отправки")
    created_at: str = Field(..., description="Время создания")


class NotificationsListResponse(BaseModel):
    """Ответ со списком уведомлений."""

    total: int = Field(..., description="Общее количество")
    skip: int = Field(..., description="Пропущено записей")
    limit: int = Field(..., description="Лимит записей")
    notifications: List[NotificationResponse] = Field(..., description="Список уведомлений")


# Helper Functions / Вспомогательные функции
async def create_notification_record(
    db: AsyncSession,
    notification_type: str,
    recipient: str,
    subject: Optional[str],
    body: Optional[str],
    priority: str,
    metadata: Optional[Dict[str, Any]],
) -> Notification:
    """
    Создать запись уведомления в базе данных.

    Args:
        db: Сессия базы данных
        notification_type: Тип уведомления
        recipient: Получатель
        subject: Тема
        body: Тело
        priority: Приоритет
        metadata: Метаданные

    Returns:
        Созданная запись уведомления
    """
    notification = Notification(
        notification_type=notification_type,
        recipient=recipient,
        subject=subject,
        body=body,
        priority=priority,
        metadata=metadata,
        status=NotificationStatus.PENDING.value,
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification


async def send_email_notification(
    recipient: str,
    subject: Optional[str],
    body: Optional[str],
    metadata: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Отправить email уведомление.

    Примечание: Это placeholder реализация. В реальном приложении
    здесь должна быть интеграция с SMTP сервером или email API.

    Args:
        recipient: Email получателя
        subject: Тема письма
        body: Тело письма
        metadata: Метаданные

    Returns:
        Результат отправки
    """
    # Placeholder: логируем отправку вместо реальной отправки
    logger.info(
        f"Sending email to={recipient}, subject='{subject}', "
        f"body_length={len(body) if body else 0}"
    )
    return {
        "success": True,
        "message": "Email notification logged (placeholder)",
    }


async def send_sms_notification(
    recipient: str,
    body: Optional[str],
    metadata: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Отправить SMS уведомление.

    Примечание: Это placeholder реализация. В реальном приложении
    здесь должна быть интеграция с SMS провайдером (Twilio, SNS).

    Args:
        recipient: Номер телефона получателя
        body: Текст сообщения
        metadata: Метаданные

    Returns:
        Результат отправки
    """
    logger.info(f"Sending SMS to={recipient}, body_length={len(body) if body else 0}")
    return {
        "success": True,
        "message": "SMS notification logged (placeholder)",
    }


async def send_webhook_notification(
    recipient: str,  # URL
    subject: Optional[str],
    body: Optional[str],
    metadata: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Отправить webhook уведомление.

    Примечание: Это placeholder реализация. В реальном приложении
    здесь должен быть HTTP POST запрос на указанный URL.

    Args:
        recipient: URL webhook
        subject: Тема (используется в payload)
        body: Тело уведомления
        metadata: Метаданные

    Returns:
        Результат отправки
    """
    logger.info(
        f"Sending webhook to={recipient}, subject='{subject}', "
        f"body_length={len(body) if body else 0}"
    )
    return {
        "success": True,
        "message": "Webhook notification logged (placeholder)",
    }


def send_notification_background(
    notification_id: str,
    notification_type: str,
    recipient: str,
    subject: Optional[str],
    body: Optional[str],
    metadata: Optional[Dict[str, Any]],
):
    """
    Фоновая отправка уведомления (для BackgroundTasks).

    Args:
        notification_id: ID уведомления
        notification_type: Тип уведомления
        recipient: Получатель
        subject: Тема
        body: Тело
        metadata: Метаданные
    """
    logger.info(f"Background sending notification {notification_id}")
    # В реальном приложении здесь была бы асинхронная отправка


# API Endpoints / API Эндпоинты
@router.post(
    "/send",
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK,
    tags=["Notifications"],
)
async def send_notification(
    request: SendNotificationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Отправить уведомление.

    Этот эндпоинт принимает запрос на отправку уведомления и ставит его в очередь
    на отправку. Поддерживаются email, SMS, webhook и внутриприкладные уведомления.

    Args:
        request: Запрос на отправку уведомления
        background_tasks: FastAPI BackgroundTasks
        db: Сессия базы данных

    Returns:
        JSON ответ с информацией об уведомлении

    Raises:
        HTTPException(422): Если тип уведомления не поддерживается
        HTTPException(500): При ошибке отправки

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8008/api/notifications/send",
        ...     json={
        ...         "type": "email",
        ...         "recipient": "test@example.com",
        ...         "subject": "Test",
        ...         "body": "Test body"
        ...     }
        ... )
        >>> response.json()
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "type": "email",
            "recipient": "test@example.com",
            "status": "pending",
            "priority": "normal",
            ...
        }
    """
    start_time = time.time()
    try:
        logger.info(
            f"Sending notification: type={request.type}, "
            f"recipient={request.recipient}"
        )

        # Валидация типа уведомления
        valid_types = [t.value for t in NotificationType]
        if request.type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid notification type '{request.type}'. "
                f"Valid types: {', '.join(valid_types)}",
            )

        # Определение subject и body из шаблона, если указан
        subject = request.subject
        body = request.body

        if request.template_name:
            logger.info(f"Loading template: {request.template_name}")

            # Определение типа шаблона на основе типа уведомления
            template_type = "email" if request.type == NotificationType.EMAIL.value else "sms"

            # Инициализация сервиса шаблонов
            template_service = TemplateService()

            try:
                # Загрузка шаблона из базы данных
                template = await template_service.get_template_by_name(
                    db=db,
                    name=request.template_name,
                    template_type=template_type,
                    language="en",  # По умолчанию английский, можно добавить в request
                )

                if not template:
                    logger.warning(
                        f"Template not found: name={request.template_name}, "
                        f"type={template_type}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Template '{request.template_name}' not found",
                    )

                # Подстановка переменных в шаблон
                variables = request.template_vars or {}
                body = template_service.substitute_variables(template.body, variables)

                # Для email шаблонов также подставляем переменные в subject
                if template_type == "email" and hasattr(template, "subject"):
                    subject = template_service.substitute_variables(
                        template.subject, variables
                    )

                logger.info(
                    f"Template loaded and rendered: name={request.template_name}, "
                    f"vars_count={len(variables)}"
                )

            except HTTPException:
                raise
            except Exception as e:
                logger.error(
                    f"Error loading/rendering template {request.template_name}: {e}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to load template: {str(e)}",
                ) from e

        # Создание записи в базе данных
        notification = await create_notification_record(
            db=db,
            notification_type=request.type,
            recipient=request.recipient,
            subject=subject,
            body=body,
            priority=request.priority,
            metadata=request.metadata,
        )

        # Отправка уведомления (синхронно для простоты)
        send_result = None
        if request.type == NotificationType.EMAIL.value:
            send_result = await send_email_notification(
                recipient=request.recipient,
                subject=subject,
                body=body,
                metadata=request.metadata,
            )
        elif request.type == NotificationType.SMS.value:
            send_result = await send_sms_notification(
                recipient=request.recipient,
                body=body,
                metadata=request.metadata,
            )
        elif request.type == NotificationType.WEBHOOK.value:
            send_result = await send_webhook_notification(
                recipient=request.recipient,
                subject=subject,
                body=body,
                metadata=request.metadata,
            )
        else:  # IN_APP
            logger.info(f"In-app notification created: {notification.id}")

        # Обновление статуса
        if send_result and send_result.get("success"):
            notification.status = NotificationStatus.SENT.value
            notification.sent_at = datetime.utcnow()
        elif send_result and not send_result.get("success"):
            notification.status = NotificationStatus.FAILED.value
            notification.error_message = send_result.get("message", "Unknown error")

        await db.commit()
        await db.refresh(notification)

        processing_time_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(
            f"Notification sent: id={notification.id}, type={request.type}, "
            f"status={notification.status}, time={processing_time_ms}ms"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": notification.id,
                "type": notification.notification_type,
                "recipient": notification.recipient,
                "status": notification.status,
                "priority": notification.priority,
                "subject": notification.subject,
                "sent_at": notification.sent_at.isoformat() if notification.sent_at else None,
                "created_at": notification.created_at.isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending notification: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}",
        ) from e


@router.get(
    "/",
    response_model=NotificationsListResponse,
    tags=["Notifications"],
)
async def list_notifications(
    skip: int = Query(0, ge=0, description="Пропустить записей"),
    limit: int = Query(50, ge=1, le=200, description="Лимит записей"),
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    type: Optional[str] = Query(None, description="Фильтр по типу"),
    recipient: Optional[str] = Query(None, description="Фильтр по получателю"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Получить список уведомлений.

    Этот эндпоинт возвращает список уведомлений с поддержкой пагинации
    и фильтрации по статусу, типу и получателю.

    Args:
        skip: Количество пропускаемых записей
        limit: Лимит записей (максимум 200)
        status: Опциональный фильтр по статусу
        type: Опциональный фильтр по типу
        recipient: Опциональный фильтр по получателю
        db: Сессия базы данных

    Returns:
        JSON ответ со списком уведомлений

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8008/api/notifications/")
        >>> response.json()
        {
            "total": 150,
            "skip": 0,
            "limit": 50,
            "notifications": [...]
        }
    """
    try:
        logger.info(
            f"Listing notifications: skip={skip}, limit={limit}, "
            f"status={status}, type={type}"
        )

        # Построение запроса
        query = select(Notification)

        # Применение фильтров
        filters = []
        if status:
            filters.append(Notification.status == status)
        if type:
            filters.append(Notification.notification_type == type)
        if recipient:
            filters.append(Notification.recipient.ilike(f"%{recipient}%"))

        if filters:
            query = query.where(and_(*filters))

        # Подсчет общего количества
        from sqlalchemy import func
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Применение пагинации и сортировки
        query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)

        # Выполнение запроса
        result = await db.execute(query)
        notifications = result.scalars().all()

        # Формирование ответа
        notifications_data = [
            {
                "id": n.id,
                "type": n.notification_type,
                "recipient": n.recipient,
                "status": n.status,
                "priority": n.priority,
                "subject": n.subject,
                "sent_at": n.sent_at.isoformat() if n.sent_at else None,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifications
        ]

        logger.info(f"Returning {len(notifications_data)} notifications (total: {total})")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total": total,
                "skip": skip,
                "limit": limit,
                "notifications": notifications_data,
            },
        )

    except Exception as e:
        logger.error(f"Error listing notifications: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list notifications: {str(e)}",
        ) from e


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
    tags=["Notifications"],
)
async def get_notification(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Получить детали уведомления по ID.

    Args:
        notification_id: ID уведомления
        db: Сессия базы данных

    Returns:
        JSON ответ с деталями уведомления

    Raises:
        HTTPException(404): Если уведомление не найдено
        HTTPException(500): При ошибке получения данных

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:8008/api/notifications/123e4567-e89b-12d3-a456-426614174000"
        ... )
        >>> response.json()
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "type": "email",
            "recipient": "test@example.com",
            ...
        }
    """
    try:
        logger.info(f"Getting notification: {notification_id}")

        query = select(Notification).where(Notification.id == notification_id)
        result = await db.execute(query)
        notification = result.scalar_one_or_none()

        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification not found: {notification_id}",
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": notification.id,
                "type": notification.notification_type,
                "recipient": notification.recipient,
                "status": notification.status,
                "priority": notification.priority,
                "subject": notification.subject,
                "sent_at": notification.sent_at.isoformat() if notification.sent_at else None,
                "created_at": notification.created_at.isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notification: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notification: {str(e)}",
        ) from e


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Notifications"],
)
async def delete_notification(
    notification_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Удалить уведомление.

    Args:
        notification_id: ID уведомления
        db: Сессия базы данных

    Raises:
        HTTPException(404): Если уведомление не найдено
        HTTPException(500): При ошибке удаления

    Examples:
        >>> import requests
        >>> response = requests.delete(
        ...     "http://localhost:8008/api/notifications/123e4567-e89b-12d3-a456-426614174000"
        ... )
        >>> response.status_code
        204
    """
    try:
        logger.info(f"Deleting notification: {notification_id}")

        query = select(Notification).where(Notification.id == notification_id)
        result = await db.execute(query)
        notification = result.scalar_one_or_none()

        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification not found: {notification_id}",
            )

        await db.delete(notification)
        await db.commit()

        logger.info(f"Notification deleted: {notification_id}")

        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete notification: {str(e)}",
        ) from e
