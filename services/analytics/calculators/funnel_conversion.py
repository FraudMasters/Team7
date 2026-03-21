"""
Funnel conversion rate calculator for analytics.

# Русский комментарий:
Этот модуль предоставляет калькулятор для анализа конверсии воронки найма,
включая метрики конверсии между этапами, точки выбытия кандидатов и узкие места в процессе.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class StageConversion(BaseModel):
    """Метрики конверсии для отдельного этапа воронки."""

    stage_name: str = Field(..., description="Название этапа воронки")
    candidates_entered: int = Field(..., description="Количество кандидатов, вошедших в этап")
    candidates_advanced: int = Field(0, description="Количество кандидатов, прошедших на следующий этап")
    candidates_dropped: int = Field(0, description="Количество кандидатов, отсеянных на этапе")
    conversion_rate: float = Field(0.0, description="Коэффициент конверсии (0-1)")
    drop_rate: float = Field(0.0, description="Коэффициент выбытия (0-1)")
    average_time_in_stage_hours: Optional[float] = Field(None, description="Среднее время на этапе в часах")
    average_time_in_stage_days: Optional[float] = Field(None, description="Среднее время на этапе в днях")


class FunnelMetrics(BaseModel):
    """Сводные метрики конверсии воронки найма."""

    stages: List[StageConversion] = Field(default_factory=list, description="Метрики по каждому этапу")
    total_applications: int = Field(0, description="Общее количество заявок в начале воронки")
    total_hired: int = Field(0, description="Общее количество нанятых в конце воронки")
    overall_conversion_rate: float = Field(0.0, description="Общий коэффициент конверсии (нанятые/заявки)")
    average_funnel_time_days: Optional[float] = Field(None, description="Среднее время прохождения всей воронки в днях")
    bottleneck_stage: Optional[str] = Field(None, description="Этап с наименьшей конверсией (узкое место)")
    highest_dropout_stage: Optional[str] = Field(None, description="Этап с наибольшим выбытием")


class FunnelConversionCalculator:
    """
    Калькулятор конверсии воронки найма.

    Анализирует движение кандидатов через этапы найма для расчета ключевых метрик:
    - Конверсия между этапами
    - Точки выбытия кандидатов
    - Время на каждом этапе
    - Узкие места в процессе
    - Общая эффективность воронки
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
        vacancy_id: Optional[str] = None,
    ) -> FunnelMetrics:
        """
        Рассчитывает метрики конверсии воронки за указанный период.

        Args:
            start_date: Начальная дата для фильтрации (по умолчанию - все время)
            end_date: Конечная дата для фильтрации (по умолчанию - все время)
            vacancy_id: ID вакансии для фильтрации (по умолчанию - все вакансии)

        Returns:
            FunnelMetrics: Сводные метрики конверсии воронки

        Example:
            >>> calculator = FunnelConversionCalculator(db)
            >>> metrics = await calculator.calculate(
            ...     start_date=datetime(2026, 1, 1),
            ...     end_date=datetime(2026, 3, 31)
            ... )
            >>> print(f"Overall conversion: {metrics.overall_conversion_rate:.2%}")
            >>> print(f"Bottleneck: {metrics.bottleneck_stage}")
        """
        logger.info(
            f"Calculating funnel conversion - start_date: {start_date}, "
            f"end_date: {end_date}, vacancy_id: {vacancy_id}"
        )

        try:
            # Для первой версии возвращаем mock данные
            # Интеграция с базой данных будет добавлена после создания необходимых моделей
            # и завершения миграций

            # Mock data для демонстрации структуры воронки
            stage_conversions = [
                StageConversion(
                    stage_name="NEW",
                    candidates_entered=1250,
                    candidates_advanced=890,
                    candidates_dropped=360,
                    conversion_rate=0.712,
                    drop_rate=0.288,
                    average_time_in_stage_hours=24.5,
                    average_time_in_stage_days=1.02,
                ),
                StageConversion(
                    stage_name="SCREENING",
                    candidates_entered=890,
                    candidates_advanced=512,
                    candidates_dropped=378,
                    conversion_rate=0.575,
                    drop_rate=0.425,
                    average_time_in_stage_hours=48.2,
                    average_time_in_stage_days=2.01,
                ),
                StageConversion(
                    stage_name="PHONE_SCREEN",
                    candidates_entered=512,
                    candidates_advanced=298,
                    candidates_dropped=214,
                    conversion_rate=0.582,
                    drop_rate=0.418,
                    average_time_in_stage_hours=72.8,
                    average_time_in_stage_days=3.03,
                ),
                StageConversion(
                    stage_name="INTERVIEW",
                    candidates_entered=298,
                    candidates_advanced=156,
                    candidates_dropped=142,
                    conversion_rate=0.523,
                    drop_rate=0.477,
                    average_time_in_stage_hours=120.5,
                    average_time_in_stage_days=5.02,
                ),
                StageConversion(
                    stage_name="TECHNICAL",
                    candidates_entered=156,
                    candidates_advanced=89,
                    candidates_dropped=67,
                    conversion_rate=0.571,
                    drop_rate=0.429,
                    average_time_in_stage_hours=168.3,
                    average_time_in_stage_days=7.01,
                ),
                StageConversion(
                    stage_name="BACKGROUND_CHECK",
                    candidates_entered=89,
                    candidates_advanced=82,
                    candidates_dropped=7,
                    conversion_rate=0.921,
                    drop_rate=0.079,
                    average_time_in_stage_hours=96.7,
                    average_time_in_stage_days=4.03,
                ),
                StageConversion(
                    stage_name="OFFER",
                    candidates_entered=82,
                    candidates_advanced=68,
                    candidates_dropped=14,
                    conversion_rate=0.829,
                    drop_rate=0.171,
                    average_time_in_stage_hours=48.5,
                    average_time_in_stage_days=2.02,
                ),
                StageConversion(
                    stage_name="ACCEPTED",
                    candidates_entered=68,
                    candidates_advanced=68,
                    candidates_dropped=0,
                    conversion_rate=1.0,
                    drop_rate=0.0,
                    average_time_in_stage_hours=120.0,
                    average_time_in_stage_days=5.0,
                ),
            ]

            total_applications = stage_conversions[0].candidates_entered if stage_conversions else 0
            total_hired = stage_conversions[-1].candidates_advanced if stage_conversions else 0
            overall_conversion_rate = total_hired / total_applications if total_applications > 0 else 0.0

            # Рассчитываем среднее время прохождения воронки
            total_avg_time = sum(
                s.average_time_in_stage_days for s in stage_conversions
                if s.average_time_in_stage_days is not None
            )
            average_funnel_time_days = total_avg_time if total_avg_time > 0 else None

            # Находим узкое место (этап с наименьшей конверсией)
            # Исключаем последний этап, так как он всегда имеет конверсию 100%
            stages_for_bottleneck = [s for s in stage_conversions[:-1]]
            bottleneck = min(
                stages_for_bottleneck,
                key=lambda s: s.conversion_rate
            ) if stages_for_bottleneck else None
            bottleneck_stage = bottleneck.stage_name if bottleneck else None

            # Находим этап с наибольшим выбытием
            highest_dropout = max(
                stage_conversions,
                key=lambda s: s.drop_rate
            ) if stage_conversions else None
            highest_dropout_stage = highest_dropout.stage_name if highest_dropout else None

            metrics = FunnelMetrics(
                stages=stage_conversions,
                total_applications=total_applications,
                total_hired=total_hired,
                overall_conversion_rate=overall_conversion_rate,
                average_funnel_time_days=average_funnel_time_days,
                bottleneck_stage=bottleneck_stage,
                highest_dropout_stage=highest_dropout_stage,
            )

            logger.info(
                f"Funnel conversion calculated - "
                f"total_applications: {total_applications}, "
                f"total_hired: {total_hired}, "
                f"conversion_rate: {overall_conversion_rate:.2%}, "
                f"bottleneck: {bottleneck_stage}"
            )

            return metrics

        except Exception as e:
            logger.error(f"Error calculating funnel conversion: {e}", exc_info=True)
            raise

    async def calculate_stage_transition(
        self,
        from_stage: str,
        to_stage: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, float]:
        """
        Рассчитывает конверсию между двумя конкретными этапами.

        Args:
            from_stage: Начальный этап
            to_stage: Конечный этап
            start_date: Начальная дата для фильтрации
            end_date: Конечная дата для фильтрации

        Returns:
            Dict с метриками конверсии между этапами

        Example:
            >>> metrics = await calculator.calculate_stage_transition(
            ...     from_stage="SCREENING",
            ...     to_stage="PHONE_SCREEN"
            ... )
            >>> print(f"Conversion: {metrics['conversion_rate']:.2%}")
        """
        logger.info(
            f"Calculating stage transition - from: {from_stage}, to: {to_stage}"
        )

        try:
            # Получаем полные метрики воронки
            funnel_metrics = await self.calculate(start_date, end_date)

            # Находим этапы в воронке
            from_stage_data = next(
                (s for s in funnel_metrics.stages if s.stage_name == from_stage),
                None
            )
            to_stage_data = next(
                (s for s in funnel_metrics.stages if s.stage_name == to_stage),
                None
            )

            if not from_stage_data:
                raise ValueError(f"Stage not found: {from_stage}")
            if not to_stage_data:
                raise ValueError(f"Stage not found: {to_stage}")

            # Рассчитываем прямую конверсию между этапами
            conversion_rate = (
                to_stage_data.candidates_entered / from_stage_data.candidates_entered
                if from_stage_data.candidates_entered > 0 else 0.0
            )

            result = {
                "from_stage": from_stage,
                "to_stage": to_stage,
                "candidates_from": from_stage_data.candidates_entered,
                "candidates_to": to_stage_data.candidates_entered,
                "conversion_rate": conversion_rate,
            }

            logger.info(
                f"Stage transition calculated - "
                f"{from_stage} -> {to_stage}: {conversion_rate:.2%}"
            )

            return result

        except Exception as e:
            logger.error(
                f"Error calculating stage transition from {from_stage} to {to_stage}: {e}",
                exc_info=True
            )
            raise

    async def get_bottlenecks(
        self,
        threshold: float = 0.5,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[StageConversion]:
        """
        Получает этапы с конверсией ниже порогового значения (узкие места).

        Args:
            threshold: Пороговое значение конверсии (по умолчанию 0.5)
            start_date: Начальная дата для фильтрации
            end_date: Конечная дата для фильтрации

        Returns:
            List[StageConversion]: Этапы с низкой конверсией, отсортированные по возрастанию

        Example:
            >>> bottlenecks = await calculator.get_bottlenecks(threshold=0.6)
            >>> for stage in bottlenecks:
            ...     print(f"{stage.stage_name}: {stage.conversion_rate:.2%}")
        """
        logger.info(
            f"Getting bottlenecks with threshold {threshold}"
        )

        try:
            funnel_metrics = await self.calculate(start_date, end_date)

            # Фильтруем этапы с конверсией ниже порогового значения
            # Исключаем последний этап (ACCEPTED), так как он всегда 100%
            bottlenecks = [
                stage for stage in funnel_metrics.stages[:-1]
                if stage.conversion_rate < threshold
            ]

            # Сортируем по возрастанию конверсии (худшие первыми)
            bottlenecks.sort(key=lambda s: s.conversion_rate)

            logger.info(
                f"Found {len(bottlenecks)} bottleneck stages below {threshold:.0%}"
            )

            return bottlenecks

        except Exception as e:
            logger.error(
                f"Error getting bottlenecks: {e}",
                exc_info=True
            )
            raise

    async def calculate_time_to_hire(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, float]:
        """
        Рассчитывает метрики времени найма на основе воронки.

        Args:
            start_date: Начальная дата для фильтрации
            end_date: Конечная дата для фильтрации

        Returns:
            Dict с метриками времени найма

        Example:
            >>> time_metrics = await calculator.calculate_time_to_hire()
            >>> print(f"Average time to hire: {time_metrics['average_days']:.1f} days")
        """
        logger.info("Calculating time to hire from funnel data")

        try:
            funnel_metrics = await self.calculate(start_date, end_date)

            # Рассчитываем метрики времени
            stages_with_time = [
                s for s in funnel_metrics.stages
                if s.average_time_in_stage_days is not None
            ]

            if not stages_with_time:
                return {
                    "average_days": 0.0,
                    "total_stages": 0,
                }

            total_time = sum(s.average_time_in_stage_days for s in stages_with_time)

            # Находим самый медленный этап
            slowest_stage = max(
                stages_with_time,
                key=lambda s: s.average_time_in_stage_days
            )

            # Находим самый быстрый этап
            fastest_stage = min(
                stages_with_time,
                key=lambda s: s.average_time_in_stage_days
            )

            result = {
                "average_days": total_time,
                "total_stages": len(stages_with_time),
                "slowest_stage": slowest_stage.stage_name,
                "slowest_stage_days": slowest_stage.average_time_in_stage_days,
                "fastest_stage": fastest_stage.stage_name,
                "fastest_stage_days": fastest_stage.average_time_in_stage_days,
            }

            logger.info(
                f"Time to hire calculated - average: {total_time:.1f} days, "
                f"slowest: {slowest_stage.stage_name} ({slowest_stage.average_time_in_stage_days:.1f} days)"
            )

            return result

        except Exception as e:
            logger.error(f"Error calculating time to hire: {e}", exc_info=True)
            raise
