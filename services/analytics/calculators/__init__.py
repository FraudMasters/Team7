"""
Calculators for analytics metrics.

# Русский комментарий:
Этот модуль содержит калькуляторы для различных метрик аналитики,
включая эффективность источников, конверсию воронки, метрики разнообразия и бенчмарки.
"""

from .source_effectiveness import (
    SourceEffectivenessCalculator,
    SourceEffectivenessMetrics,
    SourceMetrics,
)
from .funnel_conversion import (
    FunnelConversionCalculator,
    FunnelMetrics,
    StageConversion,
)
from .diversity_metrics import (
    DiversityMetricsCalculator,
    DiversityMetricsResult,
    DemographicGroupMetrics,
    CategorySummary,
)
from .benchmarks import (
    BenchmarkCalculator,
    BenchmarkComparison,
    CategoryBenchmarks,
    MetricBenchmark,
    PerformanceStatus,
    IndustryType,
)

__all__ = [
    "SourceEffectivenessCalculator",
    "SourceEffectivenessMetrics",
    "SourceMetrics",
    "FunnelConversionCalculator",
    "FunnelMetrics",
    "StageConversion",
    "DiversityMetricsCalculator",
    "DiversityMetricsResult",
    "DemographicGroupMetrics",
    "CategorySummary",
    "BenchmarkCalculator",
    "BenchmarkComparison",
    "CategoryBenchmarks",
    "MetricBenchmark",
    "PerformanceStatus",
    "IndustryType",
]
