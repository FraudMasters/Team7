"""
Pydantic schemas for request/response validation

This module provides schema definitions for API endpoints.
"""
from .backup import (
    BackupResponse,
    BackupCreate,
    BackupRestoreRequest,
    BackupConfigResponse,
    BackupConfigUpdate,
    BackupStatusResponse,
    S3Config,
)
from .plugin_manifest import (
    PluginManifest,
    PluginManifestResponse,
    PluginManifestCreate,
    PluginManifestValidate,
    PluginManifestValidateResponse,
    PluginPermission,
    PluginPermissionType,
    PluginDependency,
    PluginEntryPoint,
    PluginCategory,
)
from .ranking_metrics import (
    FeedbackConversionMetrics,
    TopNRecommendationMetrics,
    RankingConfidenceMetrics,
    RankingPerformanceTrend,
    RankingMetricsResponse,
    RankingMetricsByVacancy,
    RankingMetricsByRecruiter,
    RankingLeaderboardResponse,
)

__all__ = [
    "BackupResponse",
    "BackupCreate",
    "BackupRestoreRequest",
    "BackupConfigResponse",
    "BackupConfigUpdate",
    "BackupStatusResponse",
    "S3Config",
    "PluginManifest",
    "PluginManifestResponse",
    "PluginManifestCreate",
    "PluginManifestValidate",
    "PluginManifestValidateResponse",
    "PluginPermission",
    "PluginPermissionType",
    "PluginDependency",
    "PluginEntryPoint",
    "PluginCategory",
    "FeedbackConversionMetrics",
    "TopNRecommendationMetrics",
    "RankingConfidenceMetrics",
    "RankingPerformanceTrend",
    "RankingMetricsResponse",
    "RankingMetricsByVacancy",
    "RankingMetricsByRecruiter",
    "RankingLeaderboardResponse",
]
