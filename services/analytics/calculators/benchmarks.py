"""
Benchmark comparison calculator for analytics.

# Русский комментарий:
Этот модуль предоставляет калькулятор для сравнения метрик найма с отраслевыми эталонами,
включая время найма, эффективность источников, конверсию воронки и стоимость найма.
"""
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class PerformanceStatus(str, Enum):
    """Статус производительности относительно эталона."""

    ABOVE_BENCHMARK = "above_benchmark"
    AT_BENCHMARK = "at_benchmark"
    BELOW_BENCHMARK = "below_benchmark"


class IndustryType(str, Enum):
    """Типы отраслей для сравнения эталонов."""

    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"
    GENERAL = "general"


class MetricBenchmark(BaseModel):
    """Эталон для отдельной метрики."""

    metric_name: str = Field(..., description="Название метрики")
    current_value: float = Field(..., description="Текущее значение метрики")
    benchmark_value: float = Field(..., description="Эталонное значение отрасли")
    variance: float = Field(..., description="Разница от эталона")
    variance_percentage: float = Field(..., description="Разница в процентах")
    performance_status: PerformanceStatus = Field(..., description="Статус производительности")
    lower_is_better: bool = Field(False, description="Меньшее значение означает лучшую производительность")
    unit: Optional[str] = Field(None, description="Единица измерения (дни, доллары, процент)")


class CategoryBenchmarks(BaseModel):
    """Эталоны для категории метрик."""

    category_name: str = Field(..., description="Название категории (Time to Hire, Cost, и т.д.)")
    metrics: List[MetricBenchmark] = Field(default_factory=list, description="Метрики в категории")
    overall_performance: PerformanceStatus = Field(..., description="Общая производительность категории")
    summary: str = Field(..., description="Краткое описание производительности")


class BenchmarkComparison(BaseModel):
    """Полное сравнение с эталонами."""

    industry: IndustryType = Field(..., description="Отрасль для сравнения")
    categories: List[CategoryBenchmarks] = Field(default_factory=list, description="Категории эталонов")
    overall_score: float = Field(..., description="Общий балл производительности (0-100)")
    metrics_above_benchmark: int = Field(0, description="Количество метрик выше эталона")
    metrics_at_benchmark: int = Field(0, description="Количество метрик на уровне эталона")
    metrics_below_benchmark: int = Field(0, description="Количество метрик ниже эталона")
    total_metrics: int = Field(0, description="Общее количество сравниваемых метрик")
    strengths: List[str] = Field(default_factory=list, description="Области превосходства")
    improvement_areas: List[str] = Field(default_factory=list, description="Области для улучшения")


class BenchmarkCalculator:
    """
    Калькулятор сравнения с отраслевыми эталонами.

    Сравнивает метрики найма компании с отраслевыми стандартами для выявления
    областей превосходства и возможностей для улучшения. Поддерживает:
    - Время найма
    - Стоимость найма
    - Эффективность источников
    - Конверсию воронки
    - Качество кандидатов
    """

    # Отраслевые эталоны (средние значения по отраслям)
    INDUSTRY_BENCHMARKS = {
        IndustryType.TECHNOLOGY: {
            "time_to_hire_days": 36.5,
            "cost_per_hire_usd": 4500,
            "overall_conversion_rate": 0.055,
            "source_conversion_rate": 0.085,
            "funnel_first_stage_conversion": 0.70,
            "quality_score": 75.0,
            "offer_acceptance_rate": 0.82,
        },
        IndustryType.HEALTHCARE: {
            "time_to_hire_days": 42.0,
            "cost_per_hire_usd": 3800,
            "overall_conversion_rate": 0.062,
            "source_conversion_rate": 0.078,
            "funnel_first_stage_conversion": 0.68,
            "quality_score": 72.0,
            "offer_acceptance_rate": 0.85,
        },
        IndustryType.FINANCE: {
            "time_to_hire_days": 45.0,
            "cost_per_hire_usd": 5200,
            "overall_conversion_rate": 0.048,
            "source_conversion_rate": 0.072,
            "funnel_first_stage_conversion": 0.65,
            "quality_score": 78.0,
            "offer_acceptance_rate": 0.80,
        },
        IndustryType.RETAIL: {
            "time_to_hire_days": 28.0,
            "cost_per_hire_usd": 2100,
            "overall_conversion_rate": 0.075,
            "source_conversion_rate": 0.095,
            "funnel_first_stage_conversion": 0.75,
            "quality_score": 68.0,
            "offer_acceptance_rate": 0.78,
        },
        IndustryType.MANUFACTURING: {
            "time_to_hire_days": 38.0,
            "cost_per_hire_usd": 3200,
            "overall_conversion_rate": 0.068,
            "source_conversion_rate": 0.088,
            "funnel_first_stage_conversion": 0.72,
            "quality_score": 70.0,
            "offer_acceptance_rate": 0.84,
        },
        IndustryType.GENERAL: {
            "time_to_hire_days": 38.0,
            "cost_per_hire_usd": 3800,
            "overall_conversion_rate": 0.062,
            "source_conversion_rate": 0.082,
            "funnel_first_stage_conversion": 0.70,
            "quality_score": 73.0,
            "offer_acceptance_rate": 0.82,
        },
    }

    def __init__(self, db: AsyncSession):
        """
        Инициализирует калькулятор с сессией базы данных.

        Args:
            db: Асинхронная сессия SQLAlchemy
        """
        self.db = db

    async def compare_to_industry(
        self,
        industry: IndustryType = IndustryType.GENERAL,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> BenchmarkComparison:
        """
        Сравнивает текущие метрики с отраслевыми эталонами.

        Args:
            industry: Отрасль для сравнения
            start_date: Начальная дата для фильтрации (по умолчанию - все время)
            end_date: Конечная дата для фильтрации (по умолчанию - все время)

        Returns:
            BenchmarkComparison: Полное сравнение с эталонами

        Example:
            >>> calculator = BenchmarkCalculator(db)
            >>> comparison = await calculator.compare_to_industry(
            ...     industry=IndustryType.TECHNOLOGY
            ... )
            >>> print(f"Overall score: {comparison.overall_score}")
            >>> print(f"Strengths: {comparison.strengths}")
        """
        logger.info(
            f"Comparing to industry benchmarks - industry: {industry}, "
            f"start_date: {start_date}, end_date: {end_date}"
        )

        try:
            # Получаем эталоны для указанной отрасли
            benchmarks = self.INDUSTRY_BENCHMARKS[industry]

            # Для первой версии используем mock данные для текущих метрик
            # Интеграция с базой данных будет добавлена после завершения других калькуляторов
            current_metrics = {
                "time_to_hire_days": 32.5,
                "cost_per_hire_usd": 4120.50,
                "overall_conversion_rate": 0.054,
                "source_conversion_rate": 0.084,
                "funnel_first_stage_conversion": 0.712,
                "quality_score": 78.0,
                "offer_acceptance_rate": 0.829,
            }

            # Создаем сравнения по категориям
            categories = []

            # Категория: Время найма
            time_to_hire_category = self._create_time_to_hire_benchmarks(
                current_metrics, benchmarks
            )
            categories.append(time_to_hire_category)

            # Категория: Стоимость
            cost_category = self._create_cost_benchmarks(current_metrics, benchmarks)
            categories.append(cost_category)

            # Категория: Конверсия
            conversion_category = self._create_conversion_benchmarks(
                current_metrics, benchmarks
            )
            categories.append(conversion_category)

            # Категория: Качество
            quality_category = self._create_quality_benchmarks(current_metrics, benchmarks)
            categories.append(quality_category)

            # Подсчитываем общие статистики
            all_metrics = []
            for category in categories:
                all_metrics.extend(category.metrics)

            metrics_above = sum(
                1 for m in all_metrics
                if m.performance_status == PerformanceStatus.ABOVE_BENCHMARK
            )
            metrics_at = sum(
                1 for m in all_metrics
                if m.performance_status == PerformanceStatus.AT_BENCHMARK
            )
            metrics_below = sum(
                1 for m in all_metrics
                if m.performance_status == PerformanceStatus.BELOW_BENCHMARK
            )

            # Рассчитываем общий балл (0-100)
            total_metrics = len(all_metrics)
            if total_metrics > 0:
                # Метрики выше эталона дают 100 очков, на уровне - 80, ниже - 0
                score = (
                    (metrics_above * 100 + metrics_at * 80) / total_metrics
                )
            else:
                score = 0.0

            # Определяем сильные стороны и области улучшения
            strengths = [
                m.metric_name
                for m in all_metrics
                if m.performance_status == PerformanceStatus.ABOVE_BENCHMARK
            ]
            improvement_areas = [
                m.metric_name
                for m in all_metrics
                if m.performance_status == PerformanceStatus.BELOW_BENCHMARK
            ]

            comparison = BenchmarkComparison(
                industry=industry,
                categories=categories,
                overall_score=score,
                metrics_above_benchmark=metrics_above,
                metrics_at_benchmark=metrics_at,
                metrics_below_benchmark=metrics_below,
                total_metrics=total_metrics,
                strengths=strengths,
                improvement_areas=improvement_areas,
            )

            logger.info(
                f"Benchmark comparison completed - overall_score: {score:.1f}, "
                f"above: {metrics_above}, at: {metrics_at}, below: {metrics_below}"
            )

            return comparison

        except Exception as e:
            logger.error(f"Error comparing to industry benchmarks: {e}", exc_info=True)
            raise

    def _create_time_to_hire_benchmarks(
        self, current: Dict[str, float], benchmarks: Dict[str, float]
    ) -> CategoryBenchmarks:
        """Создает эталоны для категории времени найма."""
        metric = self._create_metric_benchmark(
            metric_name="Time to Hire",
            current_value=current["time_to_hire_days"],
            benchmark_value=benchmarks["time_to_hire_days"],
            lower_is_better=True,
            unit="days",
        )

        # Определяем общую производительность категории
        overall_performance = metric.performance_status

        if overall_performance == PerformanceStatus.ABOVE_BENCHMARK:
            summary = f"Excellent: {abs(metric.variance_percentage):.1f}% faster than industry average"
        elif overall_performance == PerformanceStatus.AT_BENCHMARK:
            summary = "On par with industry average"
        else:
            summary = f"Needs improvement: {abs(metric.variance_percentage):.1f}% slower than industry average"

        return CategoryBenchmarks(
            category_name="Time to Hire",
            metrics=[metric],
            overall_performance=overall_performance,
            summary=summary,
        )

    def _create_cost_benchmarks(
        self, current: Dict[str, float], benchmarks: Dict[str, float]
    ) -> CategoryBenchmarks:
        """Создает эталоны для категории стоимости."""
        metric = self._create_metric_benchmark(
            metric_name="Cost per Hire",
            current_value=current["cost_per_hire_usd"],
            benchmark_value=benchmarks["cost_per_hire_usd"],
            lower_is_better=True,
            unit="USD",
        )

        overall_performance = metric.performance_status

        if overall_performance == PerformanceStatus.ABOVE_BENCHMARK:
            summary = f"Excellent: {abs(metric.variance_percentage):.1f}% lower cost than industry average"
        elif overall_performance == PerformanceStatus.AT_BENCHMARK:
            summary = "On par with industry average"
        else:
            summary = f"Needs improvement: {abs(metric.variance_percentage):.1f}% higher cost than industry average"

        return CategoryBenchmarks(
            category_name="Cost Efficiency",
            metrics=[metric],
            overall_performance=overall_performance,
            summary=summary,
        )

    def _create_conversion_benchmarks(
        self, current: Dict[str, float], benchmarks: Dict[str, float]
    ) -> CategoryBenchmarks:
        """Создает эталоны для категории конверсии."""
        metrics = []

        # Общая конверсия
        overall_metric = self._create_metric_benchmark(
            metric_name="Overall Conversion Rate",
            current_value=current["overall_conversion_rate"],
            benchmark_value=benchmarks["overall_conversion_rate"],
            lower_is_better=False,
            unit="rate",
        )
        metrics.append(overall_metric)

        # Конверсия источников
        source_metric = self._create_metric_benchmark(
            metric_name="Source Conversion Rate",
            current_value=current["source_conversion_rate"],
            benchmark_value=benchmarks["source_conversion_rate"],
            lower_is_better=False,
            unit="rate",
        )
        metrics.append(source_metric)

        # Конверсия первого этапа воронки
        funnel_metric = self._create_metric_benchmark(
            metric_name="Funnel First Stage Conversion",
            current_value=current["funnel_first_stage_conversion"],
            benchmark_value=benchmarks["funnel_first_stage_conversion"],
            lower_is_better=False,
            unit="rate",
        )
        metrics.append(funnel_metric)

        # Принятие предложения
        offer_metric = self._create_metric_benchmark(
            metric_name="Offer Acceptance Rate",
            current_value=current["offer_acceptance_rate"],
            benchmark_value=benchmarks["offer_acceptance_rate"],
            lower_is_better=False,
            unit="rate",
        )
        metrics.append(offer_metric)

        # Определяем общую производительность (по большинству)
        above_count = sum(
            1 for m in metrics if m.performance_status == PerformanceStatus.ABOVE_BENCHMARK
        )
        below_count = sum(
            1 for m in metrics if m.performance_status == PerformanceStatus.BELOW_BENCHMARK
        )

        if above_count > below_count:
            overall_performance = PerformanceStatus.ABOVE_BENCHMARK
            summary = f"Strong: {above_count} of {len(metrics)} conversion metrics above benchmark"
        elif below_count > above_count:
            overall_performance = PerformanceStatus.BELOW_BENCHMARK
            summary = f"Needs improvement: {below_count} of {len(metrics)} conversion metrics below benchmark"
        else:
            overall_performance = PerformanceStatus.AT_BENCHMARK
            summary = "Mixed performance across conversion metrics"

        return CategoryBenchmarks(
            category_name="Conversion Rates",
            metrics=metrics,
            overall_performance=overall_performance,
            summary=summary,
        )

    def _create_quality_benchmarks(
        self, current: Dict[str, float], benchmarks: Dict[str, float]
    ) -> CategoryBenchmarks:
        """Создает эталоны для категории качества."""
        metric = self._create_metric_benchmark(
            metric_name="Candidate Quality Score",
            current_value=current["quality_score"],
            benchmark_value=benchmarks["quality_score"],
            lower_is_better=False,
            unit="score",
        )

        overall_performance = metric.performance_status

        if overall_performance == PerformanceStatus.ABOVE_BENCHMARK:
            summary = f"Excellent: {abs(metric.variance_percentage):.1f}% higher quality than industry average"
        elif overall_performance == PerformanceStatus.AT_BENCHMARK:
            summary = "On par with industry average"
        else:
            summary = f"Needs improvement: {abs(metric.variance_percentage):.1f}% lower quality than industry average"

        return CategoryBenchmarks(
            category_name="Candidate Quality",
            metrics=[metric],
            overall_performance=overall_performance,
            summary=summary,
        )

    def _create_metric_benchmark(
        self,
        metric_name: str,
        current_value: float,
        benchmark_value: float,
        lower_is_better: bool = False,
        unit: Optional[str] = None,
    ) -> MetricBenchmark:
        """
        Создает сравнение для отдельной метрики.

        Args:
            metric_name: Название метрики
            current_value: Текущее значение
            benchmark_value: Эталонное значение
            lower_is_better: True если меньшее значение лучше (например, для времени/стоимости)
            unit: Единица измерения

        Returns:
            MetricBenchmark: Сравнение метрики с эталоном
        """
        variance = current_value - benchmark_value
        variance_percentage = (
            (variance / benchmark_value * 100) if benchmark_value > 0 else 0
        )

        # Определяем статус производительности
        # Допуск ±5% считается "на уровне эталона"
        tolerance = 0.05
        abs_variance_pct = abs(variance_percentage) / 100

        if abs_variance_pct <= tolerance:
            status = PerformanceStatus.AT_BENCHMARK
        elif lower_is_better:
            # Для метрик, где меньше = лучше
            if variance < 0:
                status = PerformanceStatus.ABOVE_BENCHMARK
            else:
                status = PerformanceStatus.BELOW_BENCHMARK
        else:
            # Для метрик, где больше = лучше
            if variance > 0:
                status = PerformanceStatus.ABOVE_BENCHMARK
            else:
                status = PerformanceStatus.BELOW_BENCHMARK

        return MetricBenchmark(
            metric_name=metric_name,
            current_value=current_value,
            benchmark_value=benchmark_value,
            variance=variance,
            variance_percentage=variance_percentage,
            performance_status=status,
            lower_is_better=lower_is_better,
            unit=unit,
        )

    async def get_metric_comparison(
        self,
        metric_name: str,
        current_value: float,
        industry: IndustryType = IndustryType.GENERAL,
        lower_is_better: bool = False,
    ) -> MetricBenchmark:
        """
        Получает сравнение для одной метрики.

        Args:
            metric_name: Название метрики из эталонов
            current_value: Текущее значение метрики
            industry: Отрасль для сравнения
            lower_is_better: True если меньшее значение лучше

        Returns:
            MetricBenchmark: Сравнение метрики

        Raises:
            ValueError: Если метрика не найдена в эталонах

        Example:
            >>> comparison = await calculator.get_metric_comparison(
            ...     metric_name="time_to_hire_days",
            ...     current_value=35.0,
            ...     industry=IndustryType.TECHNOLOGY,
            ...     lower_is_better=True
            ... )
            >>> print(f"Status: {comparison.performance_status}")
        """
        logger.info(
            f"Getting metric comparison - metric: {metric_name}, "
            f"current: {current_value}, industry: {industry}"
        )

        try:
            benchmarks = self.INDUSTRY_BENCHMARKS[industry]

            if metric_name not in benchmarks:
                available_metrics = list(benchmarks.keys())
                raise ValueError(
                    f"Metric '{metric_name}' not found in benchmarks. "
                    f"Available metrics: {available_metrics}"
                )

            benchmark_value = benchmarks[metric_name]

            comparison = self._create_metric_benchmark(
                metric_name=metric_name,
                current_value=current_value,
                benchmark_value=benchmark_value,
                lower_is_better=lower_is_better,
            )

            logger.info(
                f"Metric comparison completed - {metric_name}: "
                f"current={current_value}, benchmark={benchmark_value}, "
                f"status={comparison.performance_status}"
            )

            return comparison

        except Exception as e:
            logger.error(f"Error getting metric comparison: {e}", exc_info=True)
            raise

    async def get_all_industries_comparison(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[IndustryType, BenchmarkComparison]:
        """
        Сравнивает метрики со всеми отраслевыми эталонами.

        Полезно для определения наилучшего соответствия отрасли или
        для сравнения производительности с несколькими отраслями.

        Args:
            start_date: Начальная дата для фильтрации
            end_date: Конечная дата для фильтрации

        Returns:
            Dict[IndustryType, BenchmarkComparison]: Сравнения по всем отраслям

        Example:
            >>> comparisons = await calculator.get_all_industries_comparison()
            >>> for industry, comparison in comparisons.items():
            ...     print(f"{industry}: {comparison.overall_score}")
        """
        logger.info("Comparing to all industry benchmarks")

        try:
            comparisons = {}
            for industry in IndustryType:
                comparison = await self.compare_to_industry(
                    industry=industry,
                    start_date=start_date,
                    end_date=end_date,
                )
                comparisons[industry] = comparison

            logger.info(
                f"All industries comparison completed - {len(comparisons)} industries"
            )

            return comparisons

        except Exception as e:
            logger.error(f"Error getting all industries comparison: {e}", exc_info=True)
            raise
