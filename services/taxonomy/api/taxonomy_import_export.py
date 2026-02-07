"""
Эндпоинты импорта/экспорта таксономии.

# Русский комментарий:
Этот модуль предоставляет эндпоинты для экспорта и импорта данных таксономии навыков
в форматах JSON и CSV, позволяя создавать резервные копии, мигрировать и
делиться данными таксономии между системами.
"""
import csv
import io
import json
import logging
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Query, status, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.skill_taxonomy import SkillTaxonomy

logger = logging.getLogger(__name__)

router = APIRouter()


class TaxonomyExportResponse(BaseModel):
    """Response model for taxonomy export. Модель ответа для экспорта таксономии."""

    industry: str = Field(..., description="Industry sector / Отрасль")
    format: str = Field(..., description="Export format (json or csv) / Формат экспорта")
    total_count: int = Field(..., description="Number of entries exported / Количество экспортированных записей")
    data: List[dict] = Field(..., description="Exported taxonomy data / Экспортированные данные таксономии")


class TaxonomyImportResponse(BaseModel):
    """Response model for taxonomy import. Модель ответа для импорта таксономии."""

    industry: str = Field(..., description="Industry sector / Отрасль")
    format: str = Field(..., description="Import format (json or csv) / Формат импорта")
    total_received: int = Field(..., description="Number of entries received / Количество полученных записей")
    imported_count: int = Field(..., description="Number of entries successfully imported / Количество успешно импортированных записей")
    skipped_count: int = Field(..., description="Number of entries skipped (duplicates) / Количество пропущенных записей (дубликаты)")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered during import / Ошибки при импорте")


def model_to_dict(taxonomy: SkillTaxonomy) -> dict:
    """
    Convert SkillTaxonomy model to dictionary.

    Конвертирует модель SkillTaxonomy в словарь.

    Args:
        taxonomy: SkillTaxonomy model instance / Экземпляр модели SkillTaxonomy

    Returns:
        Dictionary representation of the taxonomy / Словарное представление таксономии
    """
    return {
        "id": str(taxonomy.id),
        "industry": taxonomy.industry,
        "skill_name": taxonomy.skill_name,
        "context": taxonomy.context,
        "variants": taxonomy.variants or [],
        "extra_metadata": taxonomy.extra_metadata,
        "is_active": taxonomy.is_active,
        "version": taxonomy.version,
        "is_latest": taxonomy.is_latest,
        "is_public": taxonomy.is_public,
        "organization_id": taxonomy.organization_id,
        "source_organization": taxonomy.source_organization,
        "view_count": taxonomy.view_count,
        "use_count": taxonomy.use_count,
        "last_used_at": taxonomy.last_used_at.isoformat() if taxonomy.last_used_at else None,
        "created_at": taxonomy.created_at.isoformat() if taxonomy.created_at else "",
        "updated_at": taxonomy.updated_at.isoformat() if taxonomy.updated_at else "",
    }


@router.get("/export", tags=["Taxonomy Import/Export"])
async def export_taxonomies(
    industry: str = Query(..., description="Industry sector to export / Отрасль для экспорта"),
    format: str = Query("json", description="Export format: json or csv / Формат экспорта"),
    include_metadata: bool = Query(True, description="Include versioning and sharing metadata / Включить метаданные версионности и шаринга"),
    db: AsyncSession = Depends(get_db)
) -> StreamingResponse:
    """
    Export skill taxonomy data for an industry.

    Экспорт данных таксономии навыков для отрасли.

    This endpoint exports all skill taxonomy entries for a specific industry
    in either JSON or CSV format. The exported data can be used for backup,
    migration, or sharing purposes.

    Этот эндпоинт экспортирует все записи таксономии навыков для указанной отрасли
    в формате JSON или CSV. Экспортированные данные могут быть использованы для
    создания резервных копий, миграции или обмена.

    Args:
        industry: Industry sector to export / Отрасль для экспорта
        format: Export format (json or csv) / Формат экспорта (json или csv)
        include_metadata: Whether to include versioning and sharing metadata / Включать ли метаданные версионности
        db: Database session / Сессия базы данных

    Returns:
        StreamingResponse with file download / StreamingResponse с файлом для загрузки

    Raises:
        HTTPException(422): If format is invalid / Если формат неверный
        HTTPException(404): If no data found for industry / Если данные не найдены
        HTTPException(500): If export fails / Если экспорт не удался

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "http://localhost:8005/api/taxonomy-import-export/export?industry=technology&format=json"
        ... )
        >>> with open("technology_taxonomies.json", "wb") as f:
        ...     f.write(response.content)
    """
    try:
        logger.info(f"Exporting taxonomies for industry: {industry}, format: {format}")
        logger.info(f"Экспорт таксономий для отрасли: {industry}, формат: {format}")

        # Validate format / Валидация формата
        if format not in ["json", "csv"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid format. Must be 'json' or 'csv', got: {format}",
            )

        # Query database / Запрос к базе данных
        query = select(SkillTaxonomy).where(SkillTaxonomy.industry == industry)
        result = await db.execute(query)
        taxonomies = result.scalars().all()

        if not taxonomies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No taxonomy data found for industry: {industry}",
            )

        # Convert to dictionaries / Конвертация в словари
        taxonomy_data = [model_to_dict(t) for t in taxonomies]

        if format == "json":
            # Export as JSON / Экспорт в формате JSON
            json_data = json.dumps(taxonomy_data, indent=2)

            return StreamingResponse(
                io.BytesIO(json_data.encode("utf-8")),
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename={industry}_taxonomies.json"
                },
            )
        else:
            # Export as CSV / Экспорт в формате CSV
            output = io.StringIO()

            # Determine which fields to include / Определение полей для включения
            if include_metadata:
                fieldnames = [
                    "id", "industry", "skill_name", "context", "variants",
                    "extra_metadata", "is_active", "version", "is_latest",
                    "is_public", "organization_id", "source_organization",
                    "view_count", "use_count", "last_used_at",
                    "created_at", "updated_at"
                ]
            else:
                fieldnames = [
                    "skill_name", "context", "variants", "extra_metadata", "is_active"
                ]

            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()

            for taxonomy in taxonomy_data:
                # For CSV, we need to JSON-encode the variants and extra_metadata
                # Для CSV нужно JSON-кодировать variants и extra_metadata
                row = {k: taxonomy[k] for k in fieldnames if k in taxonomy}

                # Convert lists and dicts to JSON strings for CSV
                # Конвертация списков и словарей в JSON строки для CSV
                if "variants" in row and isinstance(row["variants"], list):
                    row["variants"] = json.dumps(row["variants"])
                if "extra_metadata" in row and isinstance(row["extra_metadata"], dict):
                    row["extra_metadata"] = json.dumps(row["extra_metadata"])

                writer.writerow(row)

            csv_data = output.getvalue()

            return StreamingResponse(
                io.BytesIO(csv_data.encode("utf-8")),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={industry}_taxonomies.csv"
                },
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting taxonomies: {e}", exc_info=True)
        logger.error(f"Ошибка при экспорте таксономий: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export taxonomies: {str(e)}",
        ) from e


@router.post("/import", tags=["Taxonomy Import/Export"])
async def import_taxonomies(
    industry: str = Query(..., description="Industry sector for import / Отрасль для импорта"),
    format: str = Query("json", description="Import format: json or csv / Формат импорта"),
    replace: bool = Query(False, description="Replace existing entries instead of merging / Заменить существующие записи"),
    file: UploadFile = File(..., description="File to import / Файл для импорта"),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Import skill taxonomy data from a file.

    Импорт данных таксономии навыков из файла.

    This endpoint imports skill taxonomy entries from a JSON or CSV file,
    allowing for bulk import of taxonomy data. The import can either merge
    with existing data or replace all entries for the industry.

    Этот эндпоинт импортирует записи таксономии навыков из файла JSON или CSV,
    позволяя выполнять массовый импорт данных таксономии. Импорт может быть
    выполнен с слиянием с существующими данными или с заменой всех записей отрасли.

    Args:
        industry: Industry sector for import / Отрасль для импорта
        format: Import format (json or csv) / Формат импорта (json или csv)
        replace: If True, delete existing entries before importing / Если True, удалить существующие записи перед импортом
        file: Uploaded file containing taxonomy data / Загруженный файл с данными таксономии
        db: Database session / Сессия базы данных

    Returns:
        JSON response with import results / JSON ответ с результатами импорта

    Raises:
        HTTPException(422): If format is invalid or data is malformed / Если формат неверный или данные некорректны
        HTTPException(500): If import fails / Если импорт не удался

    Examples:
        >>> import requests
        >>> with open("technology_taxonomies.json", "rb") as f:
        ...     response = requests.post(
        ...         "http://localhost:8005/api/taxonomy-import-export/import?industry=technology&format=json",
        ...         files={"file": f}
        ...     )
        >>> response.json()
    """
    try:
        logger.info(f"Importing taxonomies for industry: {industry}, format: {format}, replace: {replace}")
        logger.info(f"Импорт таксономий для отрасли: {industry}, формат: {format}, замена: {replace}")

        # Validate format / Валидация формата
        if format not in ["json", "csv"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid format. Must be 'json' or 'csv', got: {format}",
            )

        # Read file content / Чтение содержимого файла
        content = await file.read()

        # Delete existing entries if replace is True / Удаление существующих записей при replace=True
        if replace:
            delete_query = delete(SkillTaxonomy).where(SkillTaxonomy.industry == industry)
            await db.execute(delete_query)
            await db.commit()
            logger.info(f"Deleted existing taxonomies for industry: {industry}")
            logger.info(f"Удалены существующие таксономии для отрасли: {industry}")

        # Parse data based on format / Парсинг данных в зависимости от формата
        imported_count = 0
        skipped_count = 0
        errors = []

        if format == "json":
            try:
                taxonomy_data = json.loads(content.decode("utf-8"))

                if not isinstance(taxonomy_data, list):
                    raise ValueError("JSON data must be a list of taxonomy entries / JSON данные должны быть списком записей таксономии")

                for entry in taxonomy_data:
                    try:
                        # Check if skill already exists / Проверка существования навыка
                        existing_query = select(SkillTaxonomy).where(
                            SkillTaxonomy.industry == industry,
                            SkillTaxonomy.skill_name == entry.get("skill_name")
                        )
                        result = await db.execute(existing_query)
                        existing = result.scalar_one_or_none()

                        if existing and not replace:
                            skipped_count += 1
                            continue

                        # Create new taxonomy entry / Создание новой записи таксономии
                        new_taxonomy = SkillTaxonomy(
                            industry=industry,
                            skill_name=entry.get("skill_name"),
                            context=entry.get("context"),
                            variants=entry.get("variants", []),
                            extra_metadata=entry.get("extra_metadata"),
                            is_active=entry.get("is_active", True),
                            version=entry.get("version", 1),
                            is_latest=entry.get("is_latest", True),
                            is_public=entry.get("is_public", False),
                            organization_id=entry.get("organization_id"),
                            source_organization=entry.get("source_organization"),
                        )

                        db.add(new_taxonomy)
                        imported_count += 1

                    except Exception as e:
                        error_msg = f"Error importing entry '{entry.get('skill_name', 'unknown')}': {str(e)}"
                        errors.append(error_msg)
                        logger.warning(error_msg)

                await db.commit()

            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid JSON file: {str(e)}",
                )
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=str(e),
                )

        else:  # CSV format
            try:
                csv_data = content.decode("utf-8")
                reader = csv.DictReader(io.StringIO(csv_data))

                for row in reader:
                    try:
                        # Parse JSON fields / Парсинг JSON полей
                        variants = []
                        if row.get("variants"):
                            try:
                                variants = json.loads(row["variants"])
                            except json.JSONDecodeError:
                                variants = [row["variants"]]

                        extra_metadata = None
                        if row.get("extra_metadata"):
                            try:
                                extra_metadata = json.loads(row["extra_metadata"])
                            except json.JSONDecodeError:
                                pass

                        # Check if skill already exists / Проверка существования навыка
                        skill_name = row.get("skill_name")
                        if not skill_name:
                            errors.append("Row missing skill_name field / Отсутствует поле skill_name")
                            continue

                        existing_query = select(SkillTaxonomy).where(
                            SkillTaxonomy.industry == industry,
                            SkillTaxonomy.skill_name == skill_name
                        )
                        result = await db.execute(existing_query)
                        existing = result.scalar_one_or_none()

                        if existing and not replace:
                            skipped_count += 1
                            continue

                        # Create new taxonomy entry / Создание новой записи таксономии
                        new_taxonomy = SkillTaxonomy(
                            industry=industry,
                            skill_name=skill_name,
                            context=row.get("context"),
                            variants=variants,
                            extra_metadata=extra_metadata,
                            is_active=row.get("is_active", "True").lower() == "true",
                        )

                        db.add(new_taxonomy)
                        imported_count += 1

                    except Exception as e:
                        error_msg = f"Error importing row: {str(e)}"
                        errors.append(error_msg)
                        logger.warning(error_msg)

                await db.commit()

            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid CSV file: {str(e)}",
                )

        logger.info(
            f"Import completed: {imported_count} imported, {skipped_count} skipped, {len(errors)} errors"
        )
        logger.info(
            f"Импорт завершен: {imported_count} импортировано, {skipped_count} пропущено, {len(errors)} ошибок"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "industry": industry,
                "format": format,
                "total_received": imported_count + skipped_count,
                "imported_count": imported_count,
                "skipped_count": skipped_count,
                "errors": errors,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing taxonomies: {e}", exc_info=True)
        logger.error(f"Ошибка при импорте таксономий: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import taxonomies: {str(e)}",
        ) from e
