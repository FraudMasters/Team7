"""
Source effectiveness calculator for analytics.

# Русский комментарий:
Этот модуль предоставляет калькулятор для анализа эффективности источников найма,
включая метрики объема заявок, показателей конверсии, качества и стоимости найма.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SourceMetrics(BaseModel):
    """Метрики для отдельного источника заявок."""

    source_type: str = Field(..., description="Тип источника (JOB_BOARD, REFERRAL, и т.д.)")
    source_name: str = Field(..., description="Название источника")
    total_applications: int = Field(..., description="Общее количество заявок")
    hired_count: int = Field(0, description="Количество нанятых кандидатов")
    conversion_rate: float = Field(0.0, description="Коэффициент конверсии (0-1)")
    average_quality_score: Optional[float] = Field(None, description="Средний балл качества")
    average_cost_per_application: Optional[float] = Field(None, description="Средняя стоимость за заявку в долларах")
    total_cost: Optional[float] = Field(None, description="Общая стоимость источника в долларах")
    cost_per_hire: Optional[float] = Field(None, description="Стоимость найма в долларах")
    average_time_to_hire_days: Optional[float] = Field(None, description="Среднее время найма в днях")


class SourceEffectivenessMetrics(BaseModel):
    """Сводные метрики эффективности источников."""

    sources: List[SourceMetrics] = Field(default_factory=list, description="Метрики по каждому источнику")
    total_applications: int = Field(0, description="Общее количество заявок по всем источникам")
    total_hired: int = Field(0, description="Общее количество нанятых по всем источникам")
    overall_conversion_rate: float = Field(0.0, description="Общий коэффициент конверсии")
    best_source_by_conversion: Optional[str] = Field(None, description="Лучший источник по конверсии")
    best_source_by_quality: Optional[str] = Field(None, description="Лучший источник по качеству")
    best_source_by_cost: Optional[str] = Field(None, description="Лучший источник по стоимости найма")
    total_recruiting_cost: Optional[float] = Field(None, description="Общая стоимость рекрутинга в долларах")
    average_cost_per_hire: Optional[float] = Field(None, description="Средняя стоимость найма в долларах")


class SourceEffectivenessCalculator:
    """
    Калькулятор эффективности источников найма.

    Анализирует данные о заявках для расчета ключевых метрик эффективности по источникам:
    - Объем заявок
    - Коэффициент конверсии (нанятые/заявки)
    - Средний балл качества
    - Стоимость найма
    - Время до найма
    """

    def __init__(self, db: AsyncSession):
        """
        Инициализирует калькулятор с сессией базы данных.

        Args:
            db: Асинхронная сессия SQLAlchemy
        """
        self.db = db

    async def calculate(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> SourceEffectivenessMetrics:
        """
        Рассчитывает метрики эффективности источников за указанный период.

        Args:
            start_date: Начальная дата для фильтрации (по умолчанию - все время)
            end_date: Конечная дата для фильтрации (по умолчанию - все время)

        Returns:
            SourceEffectivenessMetrics: Сводные метрики эффективности источников

        Example:
            >>> calculator = SourceEffectivenessCalculator(db)
            >>> metrics = await calculator.calculate(
            ...     start_date=datetime(2026, 1, 1),
            ...     end_date=datetime(2026, 3, 31)
            ... )
            >>> print(f"Total applications: {metrics.total_applications}")
            >>> print(f"Conversion rate: {metrics.overall_conversion_rate:.2%}")
        """
        logger.info(
            f"Calculating source effectiveness - start_date: {start_date}, end_date: {end_date}"
        )

        try:
            # Для первой версии возвращаем mock данные
            # Интеграция с базой данных будет добавлена после создания необходимых моделей
            # и завершения миграций

            # Mock data для демонстрации структуры
            source_metrics_list = [
                SourceMetrics(
                    source_type="JOB_BOARD",
                    source_name="LinkedIn",
                    total_applications=450,
                    hired_count=38,
                    conversion_rate=0.084,
                    average_quality_score=78.5,
                    average_cost_per_application=12.50,
                    total_cost=5625.0,
                    cost_per_hire=148.03,
                    average_time_to_hire_days=28.5,
                ),
                SourceMetrics(
                    source_type="JOB_BOARD",
                    source_name="Indeed",
                    total_applications=380,
                    hired_count=25,
                    conversion_rate=0.066,
                    average_quality_score=72.3,
                    average_cost_per_application=8.75,
                    total_cost=3325.0,
                    cost_per_hire=133.0,
                    average_time_to_hire_days=32.0,
                ),
                SourceMetrics(
                    source_type="REFERRAL",
                    source_name="Employee Referral",
                    total_applications=125,
                    hired_count=28,
                    conversion_rate=0.224,
                    average_quality_score=85.7,
                    average_cost_per_application=5.0,
                    total_cost=625.0,
                    cost_per_hire=22.32,
                    average_time_to_hire_days=21.5,
                ),
                SourceMetrics(
                    source_type="CAREER_PAGE",
                    source_name="Company Website",
                    total_applications=210,
                    hired_count=15,
                    conversion_rate=0.071,
                    average_quality_score=68.9,
                    average_cost_per_application=2.0,
                    total_cost=420.0,
                    cost_per_hire=28.0,
                    average_time_to_hire_days=35.2,
                ),
                SourceMetrics(
                    source_type="AGENCY",
                    source_name="TechRecruiter Pro",
                    total_applications=85,
                    hired_count=12,
                    conversion_rate=0.141,
                    average_quality_score=82.1,
                    average_cost_per_application=45.0,
                    total_cost=3825.0,
                    cost_per_hire=318.75,
                    average_time_to_hire_days=18.7,
                ),
            ]

            total_applications = sum(s.total_applications for s in source_metrics_list)
            total_hired = sum(s.hired_count for s in source_metrics_list)
            overall_conversion_rate = total_hired / total_applications if total_applications > 0 else 0.0

            # Определяем лучшие источники по различным метрикам
            best_by_conversion = max(
                source_metrics_list,
                key=lambda s: s.conversion_rate
            ).source_name if source_metrics_list else None

            sources_with_quality = [s for s in source_metrics_list if s.average_quality_score is not None]
            best_by_quality = max(
                sources_with_quality,
                key=lambda s: s.average_quality_score
            ).source_name if sources_with_quality else None

            sources_with_cost = [s for s in source_metrics_list if s.cost_per_hire is not None]
            best_by_cost = min(
                sources_with_cost,
                key=lambda s: s.cost_per_hire
            ).source_name if sources_with_cost else None

            total_recruiting_cost = sum(
                s.total_cost for s in source_metrics_list if s.total_cost is not None
            )

            average_cost_per_hire = total_recruiting_cost / total_hired if total_hired > 0 else None

            metrics = SourceEffectivenessMetrics(
                sources=source_metrics_list,
                total_applications=total_applications,
                total_hired=total_hired,
                overall_conversion_rate=overall_conversion_rate,
                best_source_by_conversion=best_by_conversion,
                best_source_by_quality=best_by_quality,
                best_source_by_cost=best_by_cost,
                total_recruiting_cost=total_recruiting_cost,
                average_cost_per_hire=average_cost_per_hire,
            )

            logger.info(
                f"Source effectiveness calculated - "
                f"total_applications: {total_applications}, "
                f"total_hired: {total_hired}, "
                f"conversion_rate: {overall_conversion_rate:.2%}"
            )

            return metrics

        except Exception as e:
            logger.error(f"Error calculating source effectiveness: {e}", exc_info=True)
            raise

    async def calculate_by_source_type(
        self,
        source_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[SourceMetrics]:
        """
        Рассчитывает метрики для конкретного типа источника.

        Args:
            source_type: Тип источника для фильтрации
            start_date: Начальная дата для фильтрации
            end_date: Конечная дата для фильтрации

        Returns:
            List[SourceMetrics]: Список метрик для источников указанного типа
        """
        logger.info(
            f"Calculating metrics for source type: {source_type}"
        )

        try:
            # Получаем все метрики и фильтруем по типу источника
            all_metrics = await self.calculate(start_date, end_date)
            filtered_sources = [
                source for source in all_metrics.sources
                if source.source_type == source_type
            ]

            logger.info(
                f"Found {len(filtered_sources)} sources of type {source_type}"
            )

            return filtered_sources

        except Exception as e:
            logger.error(
                f"Error calculating metrics for source type {source_type}: {e}",
                exc_info=True
            )
            raise

    async def get_top_sources(
        self,
        metric: str = "conversion_rate",
        limit: int = 5,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[SourceMetrics]:
        """
        Получает топ источников по заданной метрике.

        Args:
            metric: Метрика для сортировки (conversion_rate, average_quality_score, cost_per_hire)
            limit: Максимальное количество источников для возврата
            start_date: Начальная дата для фильтрации
            end_date: Конечная дата для фильтрации

        Returns:
            List[SourceMetrics]: Топ источников, отсортированные по указанной метрике

        Raises:
            ValueError: Если указана недопустимая метрика
        """
        logger.info(
            f"Getting top {limit} sources by {metric}"
        )

        valid_metrics = ["conversion_rate", "average_quality_score", "cost_per_hire"]
        if metric not in valid_metrics:
            raise ValueError(
                f"Invalid metric: {metric}. Must be one of {valid_metrics}"
            )

        try:
            all_metrics = await self.calculate(start_date, end_date)

            # Фильтруем источники с доступной метрикой
            if metric == "cost_per_hire":
                sources = [s for s in all_metrics.sources if s.cost_per_hire is not None]
                # Для cost_per_hire меньше = лучше
                sources.sort(key=lambda s: s.cost_per_hire)
            elif metric == "average_quality_score":
                sources = [s for s in all_metrics.sources if s.average_quality_score is not None]
                sources.sort(key=lambda s: s.average_quality_score, reverse=True)
            else:  # conversion_rate
                sources = all_metrics.sources
                sources.sort(key=lambda s: s.conversion_rate, reverse=True)

            top_sources = sources[:limit]

            logger.info(
                f"Returning top {len(top_sources)} sources by {metric}"
            )

            return top_sources

        except Exception as e:
            logger.error(
                f"Error getting top sources by {metric}: {e}",
                exc_info=True
            )
            raise
