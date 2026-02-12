"""
Pydantic schemas for analytics data export.

This module provides schema definitions for exporting recruitment analytics
data in various formats (JSON, CSV), supporting GDPR compliance and reporting
capabilities.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AnalyticsExportFormat(str, Enum):
    """Supported export formats for analytics data."""

    JSON = "json"
    CSV = "csv"


class AnalyticsExportSection(str, Enum):
    """Analytics sections that can be included in exports."""

    KEY_METRICS = "key_metrics"
    FUNNEL = "funnel"
    RECRUITER_PERFORMANCE = "recruiter_performance"
    SOURCE_TRACKING = "source_tracking"
    STAGE_DURATION = "stage_duration"
    QUALITY_METRICS = "quality_metrics"
    SKILL_DEMAND = "skill_demand"
    RANKING_ACCURACY = "ranking_accuracy"
    TAXONOMY_USAGE = "taxonomy_usage"


class AnalyticsExportRequest(BaseModel):
    """Request model for analytics data export."""

    format: AnalyticsExportFormat = Field(
        default=AnalyticsExportFormat.JSON,
        description="Export format (json or csv)",
    )
    start_date: Optional[datetime] = Field(
        None,
        description="Start date for analytics data (ISO 8601 format)",
    )
    end_date: Optional[datetime] = Field(
        None,
        description="End date for analytics data (ISO 8601 format)",
    )
    sections: Optional[List[AnalyticsExportSection]] = Field(
        None,
        description="Specific sections to include. If null, includes all sections.",
    )
    include_metadata: bool = Field(
        default=True,
        description="Whether to include export metadata in the response",
    )
    recruiter_id: Optional[str] = Field(
        None,
        description="Filter by specific recruiter ID",
    )
    vacancy_id: Optional[str] = Field(
        None,
        description="Filter by specific vacancy ID",
    )


class AnalyticsExportMetadata(BaseModel):
    """Metadata about an analytics export."""

    export_timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp when export was generated",
    )
    format: str = Field(
        ...,
        description="Export format used (json or csv)",
    )
    start_date: Optional[str] = Field(
        None,
        description="Start date of included data (ISO 8601)",
    )
    end_date: Optional[str] = Field(
        None,
        description="End date of included data (ISO 8601)",
    )
    sections_included: List[str] = Field(
        ...,
        description="List of analytics sections included in the export",
    )
    total_records: int = Field(
        ...,
        description="Total number of data records in the export",
    )
    filters_applied: Dict[str, Any] = Field(
        default_factory=dict,
        description="Filters that were applied to the export",
    )
    generated_by: Optional[str] = Field(
        None,
        description="User ID or system that generated the export",
    )


class KeyMetricsExport(BaseModel):
    """Exportable key metrics data."""

    time_to_hire: Dict[str, Any] = Field(
        ...,
        description="Time-to-hire performance metrics",
    )
    resumes: Dict[str, Any] = Field(
        ...,
        description="Resume processing metrics",
    )
    match_rates: Dict[str, Any] = Field(
        ...,
        description="Skill matching metrics",
    )


class FunnelStageExport(BaseModel):
    """Exportable funnel stage data."""

    stage_name: str = Field(..., description="Name of the hiring stage")
    count: int = Field(..., description="Number of candidates at this stage")
    conversion_rate_from_previous: Optional[float] = Field(
        None, description="Conversion rate from previous stage (0-1)"
    )
    conversion_rate_from_start: float = Field(
        ..., description="Conversion rate from initial stage (0-1)"
    )


class FunnelExport(BaseModel):
    """Exportable hiring funnel data."""

    stages: List[FunnelStageExport] = Field(
        ...,
        description="Funnel metrics for each stage",
    )
    total_candidates: int = Field(
        ...,
        description="Total candidates in the funnel",
    )


class RecruiterMetricsExport(BaseModel):
    """Exportable recruiter performance data."""

    recruiter_id: str = Field(..., description="Recruiter UUID")
    recruiter_name: str = Field(..., description="Recruiter full name")
    recruiter_email: str = Field(..., description="Recruiter email")
    department: Optional[str] = Field(None, description="Recruiter department")
    hires: int = Field(..., description="Number of candidates hired")
    interviews_conducted: int = Field(..., description="Number of interviews conducted")
    resumes_processed: int = Field(..., description="Number of resumes processed")
    average_time_to_hire_days: float = Field(
        ..., description="Average time-to-hire in days"
    )
    placement_rate: float = Field(..., description="Placement rate (hires/resumes_processed)")


class RecruiterPerformanceExport(BaseModel):
    """Exportable recruiter performance analytics."""

    recruiters: List[RecruiterMetricsExport] = Field(
        ...,
        description="List of recruiter performance metrics",
    )
    total_recruiters: int = Field(
        ...,
        description="Total number of recruiters analyzed",
    )


class SourceMetricsExport(BaseModel):
    """Exportable source tracking data."""

    source: str = Field(..., description="Candidate source")
    candidate_count: int = Field(..., description="Number of candidates from this source")
    conversion_rate: float = Field(..., description="Conversion rate (0-1)")
    hired_count: int = Field(..., description="Number of candidates hired from this source")


class SourceTrackingExport(BaseModel):
    """Exportable source tracking analytics."""

    sources: List[SourceMetricsExport] = Field(
        ...,
        description="List of source metrics",
    )
    total_candidates: int = Field(
        ...,
        description="Total candidates across all sources",
    )


class StageDurationExport(BaseModel):
    """Exportable stage duration data."""

    stage_name: str = Field(..., description="Name of the hiring stage")
    average_days: float = Field(..., description="Average time in stage (days)")
    median_days: float = Field(..., description="Median time in stage (days)")
    min_days: float = Field(..., description="Minimum time in stage (days)")
    max_days: float = Field(..., description="Maximum time in stage (days)")
    candidate_count: int = Field(..., description="Candidates passing through this stage")


class StageDurationAnalyticsExport(BaseModel):
    """Exportable stage duration analytics."""

    stages: List[StageDurationExport] = Field(
        ...,
        description="Duration metrics for each hiring stage",
    )


class QualityMetricsExport(BaseModel):
    """Exportable ML/NLP quality metrics."""

    text_extraction_success_rate: float = Field(
        ..., description="Successful text extraction rate (0-1)"
    )
    avg_extraction_time_seconds: float = Field(
        ..., description="Average text extraction time"
    )
    ner_accuracy: float = Field(
        ..., description="NER accuracy (entity detection F1 score)"
    )
    entities_per_resume_avg: float = Field(
        ..., description="Average entities detected per resume"
    )
    avg_keywords_per_resume: float = Field(
        ..., description="Average keywords extracted per resume"
    )
    keyword_relevance_avg: float = Field(
        ..., description="Average keyword relevance score (0-1)"
    )
    grammar_error_rate: float = Field(
        ..., description="Resumes with grammar errors (0-1)"
    )
    matching_confidence_avg: float = Field(
        ..., description="Average matching confidence score (0-1)"
    )
    matching_precision: float = Field(
        ..., description="Matching precision (verified matches)"
    )
    matching_recall: float = Field(
        ..., description="Matching recall (found relevant candidates)"
    )
    avg_analysis_time_seconds: float = Field(
        ..., description="Average resume analysis time"
    )
    error_rate: float = Field(..., description="Analysis error rate (0-1)")
    total_analyzed: int = Field(..., description="Total number of resumes analyzed")


class SkillDemandExport(BaseModel):
    """Exportable skill demand data."""

    skill_name: str = Field(..., description="Name of the skill")
    demand_count: int = Field(..., description="Number of job postings requiring this skill")
    demand_percentage: float = Field(
        ..., description="Percentage of postings requiring this skill (0-100)"
    )
    trend: Optional[str] = Field(
        None, description="Trend indicator: 'up', 'down', or 'stable'"
    )


class SkillDemandAnalyticsExport(BaseModel):
    """Exportable skill demand analytics."""

    skills: List[SkillDemandExport] = Field(
        ...,
        description="List of skills with demand metrics",
    )
    total_postings_analyzed: int = Field(
        ...,
        description="Total number of job postings analyzed",
    )


class RankingAccuracyExport(BaseModel):
    """Exportable ranking accuracy analytics."""

    feedback_conversion: Dict[str, Any] = Field(
        ...,
        description="Feedback conversion metrics",
    )
    top_n_performance: Dict[str, Any] = Field(
        ...,
        description="Top-N recommendation success rate metrics",
    )
    confidence_distribution: Dict[str, Any] = Field(
        ...,
        description="Ranking confidence distribution metrics",
    )
    total_vacancies_analyzed: int = Field(
        ...,
        description="Total number of vacancies with ranking data",
    )


class TaxonomyUsageExport(BaseModel):
    """Exportable taxonomy usage analytics."""

    most_used_taxonomies: List[Dict[str, Any]] = Field(
        ...,
        description="Most used taxonomies",
    )
    most_effective_taxonomies: List[Dict[str, Any]] = Field(
        ...,
        description="Most effective taxonomies",
    )
    total_taxonomies_analyzed: int = Field(
        ...,
        description="Total number of taxonomies analyzed",
    )


class AnalyticsExportData(BaseModel):
    """Complete analytics export data structure."""

    key_metrics: Optional[KeyMetricsExport] = Field(
        None,
        description="Key metrics data",
    )
    funnel: Optional[FunnelExport] = Field(
        None,
        description="Hiring funnel data",
    )
    recruiter_performance: Optional[RecruiterPerformanceExport] = Field(
        None,
        description="Recruiter performance data",
    )
    source_tracking: Optional[SourceTrackingExport] = Field(
        None,
        description="Source tracking data",
    )
    stage_duration: Optional[StageDurationAnalyticsExport] = Field(
        None,
        description="Stage duration data",
    )
    quality_metrics: Optional[QualityMetricsExport] = Field(
        None,
        description="Quality metrics data",
    )
    skill_demand: Optional[SkillDemandAnalyticsExport] = Field(
        None,
        description="Skill demand data",
    )
    ranking_accuracy: Optional[RankingAccuracyExport] = Field(
        None,
        description="Ranking accuracy data",
    )
    taxonomy_usage: Optional[TaxonomyUsageExport] = Field(
        None,
        description="Taxonomy usage data",
    )


class AnalyticsExportResponse(BaseModel):
    """Response model for analytics data export."""

    format: str = Field(
        ...,
        description="Export format (json or csv)",
    )
    data: Any = Field(
        ...,
        description="Export data (dict for JSON, string for CSV)",
    )
    metadata: AnalyticsExportMetadata = Field(
        ...,
        description="Export metadata including timestamp and record counts",
    )


class ScheduledReportConfig(BaseModel):
    """Configuration for scheduled analytics reports."""

    report_name: str = Field(
        ...,
        description="Name/identifier for the scheduled report",
    )
    enabled: bool = Field(
        default=True,
        description="Whether the scheduled report is enabled",
    )
    schedule_cron: str = Field(
        ...,
        description="Cron expression for report schedule",
    )
    format: AnalyticsExportFormat = Field(
        default=AnalyticsExportFormat.CSV,
        description="Export format for the report",
    )
    sections: List[AnalyticsExportSection] = Field(
        ...,
        description="Analytics sections to include in the report",
    )
    recipients: List[str] = Field(
        ...,
        description="Email addresses to receive the report",
    )
    include_summary: bool = Field(
        default=True,
        description="Whether to include an executive summary in the email",
    )
    date_range_days: int = Field(
        default=7,
        description="Number of days to look back for data (default: 7 days)",
    )


class ScheduledReportStatus(BaseModel):
    """Status of a scheduled analytics report."""

    report_name: str = Field(..., description="Name of the scheduled report")
    last_run: Optional[datetime] = Field(
        None,
        description="Timestamp of last successful run",
    )
    next_run: Optional[datetime] = Field(
        None,
        description="Timestamp of next scheduled run",
    )
    status: str = Field(
        ...,
        description="Current status (active, paused, error)",
    )
    last_error: Optional[str] = Field(
        None,
        description="Error message from last failed run, if any",
    )
    total_runs: int = Field(
        default=0,
        description="Total number of times the report has been run",
    )
