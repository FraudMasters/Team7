"""
Diversity metrics calculator for analytics.

# Русский комментарий:
Этот модуль предоставляет калькулятор для анализа метрик разнообразия и инклюзивности,
включая демографическое представительство, конверсию по группам, достижение целей по разнообразию
и сравнение с отраслевыми эталонами.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DemographicGroupMetrics(BaseModel):
    """Метрики для отдельной демографической группы."""

    demographic_category: str = Field(..., description="Категория демографии (gender, age_group, ethnicity, и т.д.)")
    demographic_value: str = Field(..., description="Значение в категории (например, 'female', '25-34')")
    total_applicants: int = Field(0, description="Общее количество заявок")
    candidates_screened: int = Field(0, description="Количество прошедших скрининг")
    candidates_interviewed: int = Field(0, description="Количество прошедших интервью")
    candidates_offered: int = Field(0, description="Количество получивших офферы")
    candidates_hired: int = Field(0, description="Количество нанятых")
    representation_percentage: float = Field(0.0, description="Процент представительства в пуле (0-1)")
    screening_rate: float = Field(0.0, description="Коэффициент прохождения скрининга (0-1)")
    interview_rate: float = Field(0.0, description="Коэффициент прохождения интервью (0-1)")
    offer_rate: float = Field(0.0, description="Коэффициент получения оффера (0-1)")
    hire_rate: float = Field(0.0, description="Коэффициент найма (0-1)")
    conversion_rate: float = Field(0.0, description="Общий коэффициент конверсии (0-1)")
    target_representation: Optional[float] = Field(None, description="Целевой процент представительства")
    goal_met: Optional[bool] = Field(None, description="Достигнута ли цель по разнообразию")
    variance_from_target: Optional[float] = Field(None, description="Отклонение от целевого значения")
    industry_benchmark: Optional[float] = Field(None, description="Отраслевой эталон (0-1)")


class CategorySummary(BaseModel):
    """Сводка по категории демографии."""

    category: str = Field(..., description="Категория демографии")
    total_groups: int = Field(0, description="Общее количество групп в категории")
    most_represented_group: Optional[str] = Field(None, description="Наиболее представленная группа")
    least_represented_group: Optional[str] = Field(None, description="Наименее представленная группа")
    diversity_index: float = Field(0.0, description="Индекс разнообразия (0-1, выше = лучше)")
    goals_on_track: int = Field(0, description="Количество целей, достигаемых согласно плану")
    goals_behind: int = Field(0, description="Количество целей, отстающих от плана")


class DiversityMetricsResult(BaseModel):
    """Сводные метрики разнообразия и инклюзивности."""

    demographics: List[DemographicGroupMetrics] = Field(default_factory=list, description="Метрики по демографическим группам")
    categories: List[CategorySummary] = Field(default_factory=list, description="Сводки по категориям")
    total_applicants: int = Field(0, description="Общее количество заявок")
    total_hired: int = Field(0, description="Общее количество нанятых")
    overall_diversity_score: float = Field(0.0, description="Общий показатель разнообразия (0-1)")
    diversity_goals_met: int = Field(0, description="Количество достигнутых целей по разнообразию")
    diversity_goals_total: int = Field(0, description="Общее количество целей по разнообразию")
    goals_achievement_rate: float = Field(0.0, description="Процент достижения целей (0-1)")
    top_performing_category: Optional[str] = Field(None, description="Категория с лучшими показателями разнообразия")
    needs_improvement_category: Optional[str] = Field(None, description="Категория, требующая улучшения")


class DiversityMetricsCalculator:
    """
    Калькулятор метрик разнообразия и инклюзивности.

    Анализирует демографические данные кандидатов для расчета ключевых метрик:
    - Представительство различных демографических групп
    - Конверсия по этапам для каждой группы
    - Достижение целей по разнообразию
    - Сравнение с отраслевыми эталонами
    - Индексы разнообразия по категориям
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
    ) -> DiversityMetricsResult:
        """
        Рассчитывает метрики разнообразия за указанный период.

        Args:
            start_date: Начальная дата для фильтрации (по умолчанию - все время)
            end_date: Конечная дата для фильтрации (по умолчанию - все время)
            vacancy_id: ID вакансии для фильтрации (по умолчанию - все вакансии)

        Returns:
            DiversityMetricsResult: Сводные метрики разнообразия и инклюзивности

        Example:
            >>> calculator = DiversityMetricsCalculator(db)
            >>> metrics = await calculator.calculate(
            ...     start_date=datetime(2026, 1, 1),
            ...     end_date=datetime(2026, 3, 31)
            ... )
            >>> print(f"Overall diversity score: {metrics.overall_diversity_score:.2f}")
            >>> print(f"Goals met: {metrics.diversity_goals_met}/{metrics.diversity_goals_total}")
        """
        logger.info(
            f"Calculating diversity metrics - start_date: {start_date}, "
            f"end_date: {end_date}, vacancy_id: {vacancy_id}"
        )

        try:
            # Для первой версии возвращаем mock данные
            # Интеграция с базой данных будет добавлена после создания необходимых моделей
            # и завершения миграций

            # Mock data для демонстрации структуры метрик разнообразия
            demographics_data = [
                # Gender metrics
                DemographicGroupMetrics(
                    demographic_category="gender",
                    demographic_value="female",
                    total_applicants=520,
                    candidates_screened=385,
                    candidates_interviewed=198,
                    candidates_offered=42,
                    candidates_hired=38,
                    representation_percentage=0.416,
                    screening_rate=0.740,
                    interview_rate=0.514,
                    offer_rate=0.212,
                    hire_rate=0.905,
                    conversion_rate=0.073,
                    target_representation=0.50,
                    goal_met=False,
                    variance_from_target=-0.084,
                    industry_benchmark=0.48,
                ),
                DemographicGroupMetrics(
                    demographic_category="gender",
                    demographic_value="male",
                    total_applicants=680,
                    candidates_screened=492,
                    candidates_interviewed=268,
                    candidates_offered=58,
                    candidates_hired=52,
                    representation_percentage=0.544,
                    screening_rate=0.724,
                    interview_rate=0.545,
                    offer_rate=0.216,
                    hire_rate=0.897,
                    conversion_rate=0.076,
                    target_representation=0.50,
                    goal_met=True,
                    variance_from_target=0.044,
                    industry_benchmark=0.52,
                ),
                DemographicGroupMetrics(
                    demographic_category="gender",
                    demographic_value="non-binary",
                    total_applicants=50,
                    candidates_screened=35,
                    candidates_interviewed=18,
                    candidates_offered=4,
                    candidates_hired=4,
                    representation_percentage=0.040,
                    screening_rate=0.700,
                    interview_rate=0.514,
                    offer_rate=0.222,
                    hire_rate=1.000,
                    conversion_rate=0.080,
                    target_representation=None,
                    goal_met=None,
                    variance_from_target=None,
                    industry_benchmark=0.02,
                ),
                # Age group metrics
                DemographicGroupMetrics(
                    demographic_category="age_group",
                    demographic_value="18-24",
                    total_applicants=180,
                    candidates_screened=125,
                    candidates_interviewed=58,
                    candidates_offered=10,
                    candidates_hired=9,
                    representation_percentage=0.144,
                    screening_rate=0.694,
                    interview_rate=0.464,
                    offer_rate=0.172,
                    hire_rate=0.900,
                    conversion_rate=0.050,
                    target_representation=0.15,
                    goal_met=True,
                    variance_from_target=-0.006,
                    industry_benchmark=0.12,
                ),
                DemographicGroupMetrics(
                    demographic_category="age_group",
                    demographic_value="25-34",
                    total_applicants=550,
                    candidates_screened=405,
                    candidates_interviewed=225,
                    candidates_offered=52,
                    candidates_hired=48,
                    representation_percentage=0.440,
                    screening_rate=0.736,
                    interview_rate=0.556,
                    offer_rate=0.231,
                    hire_rate=0.923,
                    conversion_rate=0.087,
                    target_representation=0.45,
                    goal_met=True,
                    variance_from_target=-0.010,
                    industry_benchmark=0.42,
                ),
                DemographicGroupMetrics(
                    demographic_category="age_group",
                    demographic_value="35-44",
                    total_applicants=340,
                    candidates_screened=248,
                    candidates_interviewed=132,
                    candidates_offered=28,
                    candidates_hired=25,
                    representation_percentage=0.272,
                    screening_rate=0.729,
                    interview_rate=0.532,
                    offer_rate=0.212,
                    hire_rate=0.893,
                    conversion_rate=0.074,
                    target_representation=0.25,
                    goal_met=True,
                    variance_from_target=0.022,
                    industry_benchmark=0.28,
                ),
                DemographicGroupMetrics(
                    demographic_category="age_group",
                    demographic_value="45-54",
                    total_applicants=140,
                    candidates_screened=98,
                    candidates_interviewed=48,
                    candidates_offered=10,
                    candidates_hired=9,
                    representation_percentage=0.112,
                    screening_rate=0.700,
                    interview_rate=0.490,
                    offer_rate=0.208,
                    hire_rate=0.900,
                    conversion_rate=0.064,
                    target_representation=0.10,
                    goal_met=True,
                    variance_from_target=0.012,
                    industry_benchmark=0.14,
                ),
                DemographicGroupMetrics(
                    demographic_category="age_group",
                    demographic_value="55+",
                    total_applicants=40,
                    candidates_screened=26,
                    candidates_interviewed=11,
                    candidates_offered=4,
                    candidates_hired=3,
                    representation_percentage=0.032,
                    screening_rate=0.650,
                    interview_rate=0.423,
                    offer_rate=0.364,
                    hire_rate=0.750,
                    conversion_rate=0.075,
                    target_representation=0.05,
                    goal_met=False,
                    variance_from_target=-0.018,
                    industry_benchmark=0.04,
                ),
                # Ethnicity metrics
                DemographicGroupMetrics(
                    demographic_category="ethnicity",
                    demographic_value="asian",
                    total_applicants=310,
                    candidates_screened=235,
                    candidates_interviewed=128,
                    candidates_offered=28,
                    candidates_hired=26,
                    representation_percentage=0.248,
                    screening_rate=0.758,
                    interview_rate=0.545,
                    offer_rate=0.219,
                    hire_rate=0.929,
                    conversion_rate=0.084,
                    target_representation=0.20,
                    goal_met=True,
                    variance_from_target=0.048,
                    industry_benchmark=0.18,
                ),
                DemographicGroupMetrics(
                    demographic_category="ethnicity",
                    demographic_value="black",
                    total_applicants=180,
                    candidates_screened=125,
                    candidates_interviewed=62,
                    candidates_offered=12,
                    candidates_hired=11,
                    representation_percentage=0.144,
                    screening_rate=0.694,
                    interview_rate=0.496,
                    offer_rate=0.194,
                    hire_rate=0.917,
                    conversion_rate=0.061,
                    target_representation=0.15,
                    goal_met=True,
                    variance_from_target=-0.006,
                    industry_benchmark=0.13,
                ),
                DemographicGroupMetrics(
                    demographic_category="ethnicity",
                    demographic_value="hispanic",
                    total_applicants=220,
                    candidates_screened=158,
                    candidates_interviewed=78,
                    candidates_offered=16,
                    candidates_hired=15,
                    representation_percentage=0.176,
                    screening_rate=0.718,
                    interview_rate=0.494,
                    offer_rate=0.205,
                    hire_rate=0.938,
                    conversion_rate=0.068,
                    target_representation=0.18,
                    goal_met=True,
                    variance_from_target=-0.004,
                    industry_benchmark=0.16,
                ),
                DemographicGroupMetrics(
                    demographic_category="ethnicity",
                    demographic_value="white",
                    total_applicants=490,
                    candidates_screened=348,
                    candidates_interviewed=196,
                    candidates_offered=44,
                    candidates_hired=40,
                    representation_percentage=0.392,
                    screening_rate=0.710,
                    interview_rate=0.563,
                    offer_rate=0.224,
                    hire_rate=0.909,
                    conversion_rate=0.082,
                    target_representation=0.40,
                    goal_met=True,
                    variance_from_target=-0.008,
                    industry_benchmark=0.45,
                ),
                DemographicGroupMetrics(
                    demographic_category="ethnicity",
                    demographic_value="other",
                    total_applicants=50,
                    candidates_screened=36,
                    candidates_interviewed=20,
                    candidates_offered=4,
                    candidates_hired=2,
                    representation_percentage=0.040,
                    screening_rate=0.720,
                    interview_rate=0.556,
                    offer_rate=0.200,
                    hire_rate=0.500,
                    conversion_rate=0.040,
                    target_representation=0.07,
                    goal_met=False,
                    variance_from_target=-0.030,
                    industry_benchmark=0.08,
                ),
            ]

            total_applicants = 1250
            total_hired = 94

            # Рассчитываем сводки по категориям
            categories_summary = self._calculate_category_summaries(demographics_data)

            # Рассчитываем общие метрики
            diversity_goals_met = sum(
                1 for d in demographics_data
                if d.goal_met is True
            )
            diversity_goals_total = sum(
                1 for d in demographics_data
                if d.target_representation is not None
            )
            goals_achievement_rate = (
                diversity_goals_met / diversity_goals_total
                if diversity_goals_total > 0 else 0.0
            )

            # Рассчитываем общий показатель разнообразия (средний индекс по категориям)
            overall_diversity_score = (
                sum(c.diversity_index for c in categories_summary) / len(categories_summary)
                if categories_summary else 0.0
            )

            # Определяем лучшую и худшую категории
            top_performing_category = (
                max(categories_summary, key=lambda c: c.diversity_index).category
                if categories_summary else None
            )
            needs_improvement_category = (
                min(categories_summary, key=lambda c: c.diversity_index).category
                if categories_summary else None
            )

            metrics = DiversityMetricsResult(
                demographics=demographics_data,
                categories=categories_summary,
                total_applicants=total_applicants,
                total_hired=total_hired,
                overall_diversity_score=overall_diversity_score,
                diversity_goals_met=diversity_goals_met,
                diversity_goals_total=diversity_goals_total,
                goals_achievement_rate=goals_achievement_rate,
                top_performing_category=top_performing_category,
                needs_improvement_category=needs_improvement_category,
            )

            logger.info(
                f"Diversity metrics calculated - "
                f"total_applicants: {total_applicants}, "
                f"total_hired: {total_hired}, "
                f"diversity_score: {overall_diversity_score:.2f}, "
                f"goals_met: {diversity_goals_met}/{diversity_goals_total}"
            )

            return metrics

        except Exception as e:
            logger.error(f"Error calculating diversity metrics: {e}", exc_info=True)
            raise

    def _calculate_category_summaries(
        self,
        demographics: List[DemographicGroupMetrics]
    ) -> List[CategorySummary]:
        """
        Рассчитывает сводки по категориям демографии.

        Args:
            demographics: Список метрик по демографическим группам

        Returns:
            List[CategorySummary]: Сводки по категориям
        """
        # Группируем метрики по категориям
        categories: Dict[str, List[DemographicGroupMetrics]] = {}
        for demo in demographics:
            if demo.demographic_category not in categories:
                categories[demo.demographic_category] = []
            categories[demo.demographic_category].append(demo)

        summaries = []
        for category, groups in categories.items():
            # Находим наиболее и наименее представленные группы
            most_represented = max(groups, key=lambda g: g.representation_percentage)
            least_represented = min(groups, key=lambda g: g.representation_percentage)

            # Рассчитываем индекс разнообразия (Simpson's Diversity Index)
            # Формула: 1 - sum(p_i^2), где p_i - доля каждой группы
            diversity_index = 1 - sum(g.representation_percentage ** 2 for g in groups)

            # Подсчитываем цели
            goals_on_track = sum(1 for g in groups if g.goal_met is True)
            goals_behind = sum(1 for g in groups if g.goal_met is False)

            summary = CategorySummary(
                category=category,
                total_groups=len(groups),
                most_represented_group=most_represented.demographic_value,
                least_represented_group=least_represented.demographic_value,
                diversity_index=diversity_index,
                goals_on_track=goals_on_track,
                goals_behind=goals_behind,
            )
            summaries.append(summary)

        return summaries

    async def calculate_by_category(
        self,
        category: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[DemographicGroupMetrics]:
        """
        Рассчитывает метрики для конкретной категории демографии.

        Args:
            category: Категория для фильтрации (gender, age_group, ethnicity, и т.д.)
            start_date: Начальная дата для фильтрации
            end_date: Конечная дата для фильтрации

        Returns:
            List[DemographicGroupMetrics]: Метрики по группам указанной категории

        Example:
            >>> gender_metrics = await calculator.calculate_by_category("gender")
            >>> for group in gender_metrics:
            ...     print(f"{group.demographic_value}: {group.representation_percentage:.1%}")
        """
        logger.info(
            f"Calculating diversity metrics for category: {category}"
        )

        try:
            # Получаем все метрики и фильтруем по категории
            all_metrics = await self.calculate(start_date, end_date)
            filtered_groups = [
                demo for demo in all_metrics.demographics
                if demo.demographic_category == category
            ]

            logger.info(
                f"Found {len(filtered_groups)} groups in category {category}"
            )

            return filtered_groups

        except Exception as e:
            logger.error(
                f"Error calculating metrics for category {category}: {e}",
                exc_info=True
            )
            raise

    async def calculate_goal_progress(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, any]:
        """
        Рассчитывает прогресс достижения целей по разнообразию.

        Args:
            start_date: Начальная дата для фильтрации
            end_date: Конечная дата для фильтрации

        Returns:
            Dict с прогрессом достижения целей

        Example:
            >>> progress = await calculator.calculate_goal_progress()
            >>> print(f"Goals on track: {progress['goals_on_track']}")
            >>> print(f"Goals behind: {progress['goals_behind']}")
        """
        logger.info("Calculating diversity goal progress")

        try:
            metrics = await self.calculate(start_date, end_date)

            # Фильтруем группы с установленными целями
            groups_with_goals = [
                d for d in metrics.demographics
                if d.target_representation is not None
            ]

            goals_met = sum(1 for g in groups_with_goals if g.goal_met is True)
            goals_behind = sum(1 for g in groups_with_goals if g.goal_met is False)
            goals_on_track = goals_met  # Для простоты считаем "on track" = "met"

            # Находим группы, наиболее отстающие от целей
            groups_behind = [
                g for g in groups_with_goals
                if g.variance_from_target is not None and g.variance_from_target < -0.05
            ]
            groups_behind.sort(key=lambda g: g.variance_from_target)

            result = {
                "total_goals": len(groups_with_goals),
                "goals_met": goals_met,
                "goals_on_track": goals_on_track,
                "goals_behind": goals_behind,
                "achievement_rate": metrics.goals_achievement_rate,
                "groups_needing_attention": [
                    {
                        "category": g.demographic_category,
                        "value": g.demographic_value,
                        "current": g.representation_percentage,
                        "target": g.target_representation,
                        "variance": g.variance_from_target,
                    }
                    for g in groups_behind[:5]  # Top 5 most behind
                ],
            }

            logger.info(
                f"Goal progress calculated - "
                f"total: {len(groups_with_goals)}, "
                f"met: {goals_met}, "
                f"behind: {goals_behind}"
            )

            return result

        except Exception as e:
            logger.error(f"Error calculating goal progress: {e}", exc_info=True)
            raise

    async def compare_to_benchmarks(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, any]]:
        """
        Сравнивает метрики разнообразия с отраслевыми эталонами.

        Args:
            start_date: Начальная дата для фильтрации
            end_date: Конечная дата для фильтрации

        Returns:
            List[Dict]: Сравнение с эталонами по каждой группе

        Example:
            >>> comparisons = await calculator.compare_to_benchmarks()
            >>> for comp in comparisons:
            ...     print(f"{comp['group']}: {comp['vs_benchmark_status']}")
        """
        logger.info("Comparing diversity metrics to industry benchmarks")

        try:
            metrics = await self.calculate(start_date, end_date)

            # Создаем сравнение для групп с эталонными данными
            comparisons = []
            for demo in metrics.demographics:
                if demo.industry_benchmark is not None:
                    variance = demo.representation_percentage - demo.industry_benchmark

                    # Определяем статус
                    if variance > 0.02:
                        status = "above_benchmark"
                    elif variance < -0.02:
                        status = "below_benchmark"
                    else:
                        status = "at_benchmark"

                    comparison = {
                        "category": demo.demographic_category,
                        "group": demo.demographic_value,
                        "current_representation": demo.representation_percentage,
                        "industry_benchmark": demo.industry_benchmark,
                        "variance": variance,
                        "variance_percentage": (variance / demo.industry_benchmark * 100) if demo.industry_benchmark > 0 else 0,
                        "vs_benchmark_status": status,
                    }
                    comparisons.append(comparison)

            # Сортируем по отклонению (наибольшее отставание первым)
            comparisons.sort(key=lambda c: c["variance"])

            logger.info(
                f"Benchmark comparison completed - {len(comparisons)} groups compared"
            )

            return comparisons

        except Exception as e:
            logger.error(f"Error comparing to benchmarks: {e}", exc_info=True)
            raise
