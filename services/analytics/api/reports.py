"""
Эндпоинты управления пользовательскими отчетами.

# Русский комментарий:
Этот модуль предоставляет эндпоинты для управления пользовательскими отчетами аналитики,
включая операции CRUD для создания, чтения, обновления и удаления
сохраненных отчетов с метриками и фильтрами.
"""
import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class ReportCreate(BaseModel):
    """Модель запроса для создания пользовательского отчета."""

    name: str = Field(..., description="Название отчета")
    description: Optional[str] = Field(None, description="Описание отчета")
    organization_id: Optional[str] = Field(None, description="Идентификатор организации")
    created_by: Optional[str] = Field(None, description="ID пользователя, создающего этот отчет")
    metrics: List[str] = Field(..., description="Список метрик для включения (например, time_to_hire, resumes_processed, match_rates)")
    filters: Dict = Field(default_factory=dict, description="Фильтры отчета (например, диапазон дат, источники)")
    is_public: bool = Field(False, description="Виден ли этот отчет всем членам организации")


class ReportUpdate(BaseModel):
    """Модель запроса для обновления пользовательского отчета."""

    name: Optional[str] = Field(None, description="Название отчета")
    description: Optional[str] = Field(None, description="Описание отчета")
    metrics: Optional[List[str]] = Field(None, description="Список метрик для включения")
    filters: Optional[Dict] = Field(None, description="Фильтры отчета")
    is_public: Optional[bool] = Field(None, description="Виден ли этот отчет всем членам организации")


class ReportResponse(BaseModel):
    """Модель ответа для одной записи отчета."""

    id: str = Field(..., description="Уникальный идентификатор отчета")
    organization_id: str = Field(..., description="Идентификатор организации")
    name: str = Field(..., description="Название отчета")
    description: Optional[str] = Field(None, description="Описание отчета")
    created_by: Optional[str] = Field(None, description="ID пользователя, создавшего отчет")
    metrics: List[str] = Field(..., description="Список метрик, включенных в отчет")
    filters: Dict = Field(..., description="Фильтры отчета")
    is_public: bool = Field(..., description="Виден ли этот отчет всем членам организации")
    created_at: str = Field(..., description="Время создания")
    updated_at: str = Field(..., description="Время последнего обновления")


class ReportListResponse(BaseModel):
    """Модель ответа для списка отчетов."""

    organization_id: Optional[str] = Field(None, description="Идентификатор организации (если отфильтрован)")
    reports: List[ReportResponse] = Field(..., description="Список записей отчетов")
    total_count: int = Field(..., description="Общее количество записей")


class PDFExportRequest(BaseModel):
    """Модель запроса для экспорта отчета в PDF."""

    report_id: str = Field(..., description="ID отчета для экспорта")
    data: Dict = Field(..., description="Данные отчета для включения в PDF")
    format: Optional[str] = Field("A4", description="Формат страницы (например, A4, Letter)")


class PDFExportResponse(BaseModel):
    """Модель ответа для экспорта PDF."""

    report_id: str = Field(..., description="ID отчета")
    download_url: str = Field(..., description="URL для загрузки сгенерированного PDF")
    expires_at: str = Field(..., description="Время истечения срока действия ссылки для загрузки")


class CSVExportRequest(BaseModel):
    """Модель запроса для экспорта данных аналитики в CSV."""

    metrics: List[str] = Field(..., description="Список метрик для экспорта (например, time_to_hire, resumes_processed, match_rates)")
    filters: Dict = Field(default_factory=dict, description="Фильтры для применения к данным (например, диапазон дат, источники)")
    format: Optional[str] = Field("standard", description="Вариант формата CSV (например, standard, detailed)")


class ScheduleReportRequest(BaseModel):
    """Модель запроса для планирования автоматических отчетов."""

    name: str = Field(..., description="Название расписания")
    organization_id: Optional[str] = Field(None, description="Идентификатор организации")
    report_id: Optional[str] = Field(None, description="ID существующего отчета для планирования (опционально)")
    configuration: Dict = Field(..., description="Конфигурация отчета с метриками и фильтрами")
    schedule_config: Dict = Field(..., description="Настройки расписания (frequency, day_of_week, day_of_month, hour, minute)")
    delivery_config: Dict = Field(..., description="Настройки доставки (format, include_charts, include_summary)")
    recipients: List[str] = Field(..., description="Список адресов электронной почты получателей")
    is_active: bool = Field(True, description="Активно ли расписание")


class ScheduleReportResponse(BaseModel):
    """Модель ответа для создания запланированного отчета."""

    id: str = Field(..., description="ID расписания")
    name: str = Field(..., description="Название расписания")
    report_id: Optional[str] = Field(None, description="Связанный ID отчета")
    next_run_at: str = Field(..., description="Время следующего запуска")
    created_at: str = Field(..., description="Время создания")


@router.post(
    "/",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Reports"],
)
async def create_report(request: ReportCreate) -> JSONResponse:
    """
    Создать пользовательский отчет.

    Этот эндпоинт принимает определение пользовательского отчета с метриками и фильтрами,
    проверяет данные и создает запись в базе данных для сохраненного отчета.

    Args:
        request: Запрос на создание с деталями отчета

    Returns:
        JSON ответ с созданной записью отчета

    Raises:
        HTTPException(422): Если проверка не удалась
        HTTPException(500): Если операция с базой данных не удалась

    Examples:
        >>> import requests
        >>> data = {
        ...     "name": "Ежемесячный отчет о найме",
        ...     "description": "Обзор метрик найма за этот месяц",
        ...     "organization_id": "org123",
        ...     "created_by": "user456",
        ...     "metrics": ["time_to_hire", "resumes_processed", "match_rates"],
        ...     "filters": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
        ...     "is_public": True
        ... }
        >>> response = requests.post("http://localhost:8006/api/reports/", json=data)
        >>> response.json()
        {
            "id": "report-123",
            "organization_id": "org123",
            "name": "Ежемесячный отчет о найме",
            ...
        }
    """
    try:
        logger.info(f"Создание отчета '{request.name}'")

        # Проверка названия
        if not request.name or len(request.name.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Название отчета не может быть пустым",
            )

        # Проверка списка метрик
        if not request.metrics or len(request.metrics) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Должна быть предоставлена хотя бы одна метрика",
            )

        # Возвращаем placeholder ответ
        # Интеграция с базой данных будет добавлена в последующей подзадаче
        from datetime import datetime
        now = datetime.utcnow().isoformat() + "Z"

        response_data = {
            "id": "placeholder-report-id",
            "organization_id": request.organization_id or "default",
            "name": request.name,
            "description": request.description,
            "created_by": request.created_by,
            "metrics": request.metrics,
            "filters": request.filters,
            "is_public": request.is_public,
            "created_at": now,
            "updated_at": now,
        }

        logger.info(f"Создан отчет '{request.name}' с ID: {response_data['id']}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка создания отчета: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось создать отчет: {str(e)}",
        ) from e


@router.get("/", tags=["Reports"])
async def list_reports(
    organization_id: Optional[str] = Query(None, description="Фильтр по ID организации"),
    created_by: Optional[str] = Query(None, description="Фильтр по ID пользователя-создателя"),
    is_public: Optional[bool] = Query(None, description="Фильтр по публичному статусу"),
) -> JSONResponse:
    """
    Получить список пользовательских отчетов с опциональными фильтрами.

    Args:
        organization_id: Опциональный фильтр по ID организации
        created_by: Опциональный фильтр по ID пользователя-создателя
        is_public: Опциональный фильтр по публичному статусу

    Returns:
        JSON ответ со списком записей отчетов

    Raises:
        HTTPException(500): Если запрос к базе данных не удался

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8006/api/reports/?organization_id=org123")
        >>> response.json()
    """
    try:
        logger.info(f"Получение списка отчетов с фильтрами - organization_id: {organization_id}, created_by: {created_by}, is_public: {is_public}")

        # Возвращаем placeholder ответ
        response_data = {
            "organization_id": organization_id,
            "reports": [],
            "total_count": 0,
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Ошибка получения списка отчетов: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить список отчетов: {str(e)}",
        ) from e


@router.get("/{report_id}", tags=["Reports"])
async def get_report(report_id: str) -> JSONResponse:
    """
    Получить конкретный отчет по ID.

    Args:
        report_id: Уникальный идентификатор отчета

    Returns:
        JSON ответ с деталями отчета

    Raises:
        HTTPException(404): Если отчет не найден
        HTTPException(500): Если запрос к базе данных не удался

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8006/api/reports/123e4567-e89b-12d3-a456-426614174000")
        >>> response.json()
    """
    try:
        logger.info(f"Получение отчета: {report_id}")

        # Возвращаем placeholder ответ
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": report_id,
                "organization_id": "org123",
                "name": "Пример отчета",
                "description": "Пример отчета",
                "created_by": "user456",
                "metrics": ["time_to_hire", "resumes_processed"],
                "filters": {},
                "is_public": True,
                "created_at": "2024-01-25T00:00:00Z",
                "updated_at": "2024-01-25T00:00:00Z",
            },
        )

    except Exception as e:
        logger.error(f"Ошибка получения отчета: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось получить отчет: {str(e)}",
        ) from e


@router.put("/{report_id}", tags=["Reports"])
async def update_report(
    report_id: str, request: ReportUpdate
) -> JSONResponse:
    """
    Обновить пользовательский отчет.

    Args:
        report_id: Уникальный идентификатор отчета
        request: Запрос на обновление с полями для изменения

    Returns:
        JSON ответ с обновленной записью отчета

    Raises:
        HTTPException(404): Если отчет не найден
        HTTPException(422): Если проверка не удалась
        HTTPException(500): Если операция с базой данных не удалась

    Examples:
        >>> import requests
        >>> data = {"name": "Обновленное название отчета", "metrics": ["time_to_hire", "match_rates"]}
        >>> response = requests.put(
        ...     "http://localhost:8006/api/reports/123",
        ...     json=data
        ... )
        >>> response.json()
    """
    try:
        logger.info(f"Обновление отчета: {report_id}")

        # Возвращаем placeholder ответ
        from datetime import datetime
        now = datetime.utcnow().isoformat() + "Z"

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": report_id,
                "organization_id": "org123",
                "name": request.name or "Пример отчета",
                "description": request.description,
                "created_by": "user456",
                "metrics": request.metrics or ["time_to_hire"],
                "filters": request.filters or {},
                "is_public": request.is_public if request.is_public is not None else True,
                "created_at": "2024-01-25T00:00:00Z",
                "updated_at": now,
            },
        )

    except Exception as e:
        logger.error(f"Ошибка обновления отчета: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось обновить отчет: {str(e)}",
        ) from e


@router.delete("/{report_id}", tags=["Reports"])
async def delete_report(report_id: str) -> JSONResponse:
    """
    Удалить пользовательский отчет.

    Args:
        report_id: Уникальный идентификатор отчета

    Returns:
        JSON ответ, подтверждающий удаление

    Raises:
        HTTPException(404): Если отчет не найден
        HTTPException(500): Если операция с базой данных не удалась

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8006/api/reports/123")
        >>> response.json()
        {"message": "Отчет успешно удален"}
    """
    try:
        logger.info(f"Удаление отчета: {report_id}")

        # Возвращаем placeholder ответ
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": f"Отчет {report_id} успешно удален"},
        )

    except Exception as e:
        logger.error(f"Ошибка удаления отчета: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось удалить отчет: {str(e)}",
        ) from e


@router.delete("/organization/{organization_id}", tags=["Reports"])
async def delete_reports_by_organization(organization_id: str) -> JSONResponse:
    """
    Удалить все пользовательские отчеты для конкретной организации.

    Args:
        organization_id: Идентификатор организации для удаления отчетов

    Returns:
        JSON ответ, подтверждающий удаление с количеством

    Raises:
        HTTPException(500): Если операция с базой данных не удалась

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8006/api/reports/organization/org123")
        >>> response.json()
        {"message": "Удалено 5 отчетов для организации: org123"}
    """
    try:
        logger.info(f"Удаление всех отчетов для организации: {organization_id}")

        # Возвращаем placeholder ответ
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": f"Удалены отчеты для организации: {organization_id}", "deleted_count": 0},
        )

    except Exception as e:
        logger.error(f"Ошибка удаления отчетов для организации {organization_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось удалить отчеты: {str(e)}",
        ) from e


@router.post("/export/pdf", tags=["Reports"])
async def export_report_pdf(request: PDFExportRequest) -> JSONResponse:
    """
    Экспортировать отчет в формат PDF.

    Этот эндпоинт генерирует PDF документ из данных отчета и возвращает
    URL для загрузки сгенерированного файла.

    Args:
        request: Запрос на экспорт PDF с ID отчета и данными

    Returns:
        JSON ответ с URL загрузки и сроком действия

    Raises:
        HTTPException(422): Если проверка не удалась
        HTTPException(500): Если генерация PDF не удалась

    Examples:
        >>> import requests
        >>> data = {
        ...     "report_id": "test-id",
        ...     "data": {
        ...         "title": "Ежемесячный отчет о найме",
        ...         "metrics": {"time_to_hire": "15 дней", "resumes_processed": 150},
        ...         "charts": []
        ...     }
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8006/api/reports/export/pdf",
        ...     json=data
        ... )
        >>> response.json()
        {
            "report_id": "test-id",
            "download_url": "https://example.com/downloads/report-test-id.pdf",
            "expires_at": "2024-01-26T00:00:00Z"
        }
    """
    try:
        logger.info(f"Генерация PDF для отчета: {request.report_id}")

        # Проверка report_id
        if not request.report_id or len(request.report_id.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="ID отчета не может быть пустым",
            )

        # Проверка данных
        if not request.data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Данные отчета не могут быть пустыми",
            )

        # Возвращаем placeholder ответ
        # Фактическая генерация PDF будет добавлена в последующей подзадаче
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        expires_at = (now + timedelta(hours=24)).isoformat() + "Z"

        response_data = {
            "report_id": request.report_id,
            "download_url": f"/api/reports/downloads/{request.report_id}.pdf",
            "expires_at": expires_at,
        }

        logger.info(f"PDF успешно сгенерирован для отчета: {request.report_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка генерации PDF для отчета {request.report_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось сгенерировать PDF: {str(e)}",
        ) from e


@router.post("/export/csv", tags=["Reports"])
async def export_report_csv(request: CSVExportRequest) -> StreamingResponse:
    """
    Экспортировать данные аналитики в формат CSV.

    Этот эндпоинт генерирует CSV файл из метрик аналитики и фильтров,
    возвращая файл напрямую для загрузки.

    Args:
        request: Запрос на экспорт CSV с метриками и фильтрами

    Returns:
        StreamingResponse с содержимым CSV файла

    Raises:
        HTTPException(422): Если проверка не удалась
        HTTPException(500): Если генерация CSV не удалась

    Examples:
        >>> import requests
        >>> data = {
        ...     "metrics": ["time_to_hire", "resumes_processed"],
        ...     "filters": {"start_date": "2024-01-01", "end_date": "2024-01-31"}
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8006/api/reports/export/csv",
        ...     json=data
        ... )
        >>> with open("report.csv", "wb") as f:
        ...     f.write(response.content)
    """
    try:
        logger.info(f"Генерация CSV для метрик: {request.metrics}")

        # Проверка списка метрик
        if not request.metrics or len(request.metrics) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Должна быть предоставлена хотя бы одна метрика",
            )

        # Генерация содержимого CSV
        import io
        csv_buffer = io.StringIO()

        # Запись заголовка CSV
        header = ["metric", "value", "date"]
        csv_buffer.write(",".join(header) + "\n")

        # Запись строк примера данных на основе запрошенных метрик
        from datetime import datetime
        sample_data = {
            "time_to_hire": {"value": "15 days", "unit": "days"},
            "resumes_processed": {"value": "150", "unit": "count"},
            "match_rates": {"value": "85%", "unit": "percentage"},
            "interviews_scheduled": {"value": "25", "unit": "count"},
            "offers_extended": {"value": "10", "unit": "count"},
            "offers_accepted": {"value": "8", "unit": "count"},
        }

        # Генерация строки для каждой метрики с сегодняшней датой
        today = datetime.utcnow().strftime("%Y-%m-%d")
        for metric in request.metrics:
            if metric in sample_data:
                row = [metric, sample_data[metric]["value"], today]
                csv_buffer.write(",".join(row) + "\n")
            else:
                row = [metric, "N/A", today]
                csv_buffer.write(",".join(row) + "\n")

        csv_content = csv_buffer.getvalue()
        csv_buffer.close()

        logger.info(f"CSV успешно сгенерирован для метрик: {request.metrics}")

        # Возврат в виде загружаемого CSV файла
        return StreamingResponse(
            io.BytesIO(csv_content.encode("utf-8")),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=analytics_export.csv",
                "Content-Type": "text/csv; charset=utf-8",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка генерации CSV: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось сгенерировать CSV: {str(e)}",
        ) from e


@router.post("/schedule", tags=["Reports"], response_model=ScheduleReportResponse)
async def schedule_report(request: ScheduleReportRequest) -> JSONResponse:
    """
    Запланировать автоматический отчет с доставкой по электронной почте.

    Этот эндпоинт создает конфигурацию запланированного отчета, которая будет автоматически
    генерировать и отправлять отчеты на основе указанных настроек расписания и доставки.

    Args:
        request: Запрос на планирование с конфигурацией, расписанием и настройками доставки

    Returns:
        JSON ответ с ID расписания и временем следующего запуска

    Raises:
        HTTPException(422): Если проверка не удалась
        HTTPException(500): Если планирование не удалась

    Examples:
        >>> import requests
        >>> data = {
        ...     "name": "Еженедельный отчет аналитики",
        ...     "organization_id": "org123",
        ...     "report_id": None,
        ...     "configuration": {
        ...         "metrics": ["time_to_hire", "resumes_processed"],
        ...         "filters": {}
        ...     },
        ...     "schedule_config": {
        ...         "frequency": "weekly",
        ...         "day_of_week": 1,
        ...         "hour": 9,
        ...         "minute": 0
        ...     },
        ...     "delivery_config": {
        ...         "format": "pdf",
        ...         "include_charts": True,
        ...         "include_summary": True
        ...     },
        ...     "recipients": ["manager@example.com"],
        ...     "is_active": True
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8006/api/reports/schedule",
        ...     json=data
        ... )
        >>> response.json()
    """
    try:
        logger.info(f"Создание запланированного отчета: {request.name}")

        # Проверка названия
        if not request.name or len(request.name.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Название расписания не может быть пустым",
            )

        # Проверка наличия метрик в конфигурации
        if not request.configuration.get("metrics") or len(request.configuration["metrics"]) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Должна быть предоставлена хотя бы одна метрика в конфигурации",
            )

        # Проверка получателей
        if not request.recipients or len(request.recipients) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Должен быть указан хотя бы один получатель электронной почты",
            )

        # Проверка формата email
        import re
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        for email in request.recipients:
            if not re.match(email_pattern, email):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Неверный адрес электронной почты: {email}",
                )

        # Проверка schedule_config
        freq = request.schedule_config.get("frequency")
        if freq not in ["daily", "weekly", "monthly"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Частота должна быть одной из: daily, weekly, monthly",
            )

        hour = request.schedule_config.get("hour", 0)
        if not isinstance(hour, int) or hour < 0 or hour > 23:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Час должен быть целым числом от 0 до 23",
            )

        minute = request.schedule_config.get("minute", 0)
        if not isinstance(minute, int) or minute < 0 or minute > 59:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Минута должна быть целым числом от 0 до 59",
            )

        # Проверка расписания еженедельных отчетов
        if freq == "weekly":
            day_of_week = request.schedule_config.get("day_of_week")
            if day_of_week is None or not isinstance(day_of_week, int) or day_of_week < 0 or day_of_week > 6:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="day_of_week должен быть целым числом от 0 (воскресенье) до 6 (суббота) для еженедельной частоты",
                )

        # Проверка расписания ежемесячных отчетов
        if freq == "monthly":
            day_of_month = request.schedule_config.get("day_of_month")
            if day_of_month is None or not isinstance(day_of_month, int) or day_of_month < 1 or day_of_month > 28:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="day_of_month должен быть целым числом от 1 до 28 для ежемесячной частоты",
                )

        # Проверка формата delivery_config
        format_type = request.delivery_config.get("format")
        if format_type not in ["pdf", "csv", "both"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Формат должен быть одним из: pdf, csv, both",
            )

        # Возвращаем placeholder ответ
        # Интеграция с базой данных и планированием Celery будет добавлена в последующих подзадачах
        from datetime import datetime, timedelta
        import uuid

        schedule_id = str(uuid.uuid4())
        now = datetime.utcnow()
        created_at = now.isoformat() + "Z"

        # Вычисление next_run_at на основе конфигурации расписания
        if freq == "daily":
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        elif freq == "weekly":
            day_of_week = request.schedule_config.get("day_of_week", 0)
            days_ahead = day_of_week - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            next_run += timedelta(days=days_ahead)
        else:  # monthly
            day_of_month = request.schedule_config.get("day_of_month", 1)
            next_run = now.replace(day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                # Переход к следующему месяцу
                if now.month == 12:
                    next_run = next_run.replace(year=now.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=now.month + 1)

        next_run_at = next_run.isoformat() + "Z"

        response_data = {
            "id": schedule_id,
            "name": request.name,
            "report_id": request.report_id,
            "next_run_at": next_run_at,
            "created_at": created_at,
        }

        logger.info(f"Создан запланированный отчет '{request.name}' с ID: {schedule_id}, следующий запуск: {next_run_at}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка создания запланированного отчета: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось создать запланированный отчет: {str(e)}",
        ) from e
