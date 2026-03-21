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

__all__ = [
    "SourceEffectivenessCalculator",
    "SourceEffectivenessMetrics",
    "SourceMetrics",
]
