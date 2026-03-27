"""
Fairness monitoring endpoints for AI bias detection and mitigation.

This module provides endpoints for monitoring and tracking AI model fairness,
including retrieving fairness metrics, bias reports, and discrimination alerts.
"""
import io
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import desc, select

logger = logging.getLogger(__name__)

router = APIRouter()


class FairnessMetric(BaseModel):
    """Individual fairness metric entry."""

    metric_id: str = Field(..., description="ID of the fairness metric")
    model_name: str = Field(..., description="Name of the model")
    model_version: str = Field(..., description="Version of the model")
    protected_attribute: str = Field(..., description="Protected attribute being analyzed (e.g., gender, race)")
    metric_type: str = Field(..., description="Type of fairness metric (disparate_impact, demographic_parity, etc.)")
    metric_value: float = Field(..., description="Calculated metric value")
    threshold: float = Field(..., description="Acceptable threshold for this metric")
    is_acceptable: bool = Field(..., description="Whether metric is within acceptable bounds")
    sample_size: int = Field(..., description="Number of samples evaluated")
    calculated_at: str = Field(..., description="Timestamp when metric was calculated (ISO 8601 format)")


class FairnessMetricsListResponse(BaseModel):
    """Response model for fairness metrics list."""

    metrics: List[FairnessMetric] = Field(..., description="List of fairness metrics")
    total_count: int = Field(..., description="Total number of metric entries")


class BiasReport(BaseModel):
    """Bias analysis report."""

    report_id: str = Field(..., description="ID of the bias report")
    model_name: str = Field(..., description="Name of the model")
    model_version: str = Field(..., description="Version of the model")
    report_type: str = Field(..., description="Type of report (individual, group, system-wide)")
    protected_attributes: List[str] = Field(..., description="Protected attributes analyzed")
    overall_fairness_score: float = Field(..., description="Overall fairness score (0-1)")
    bias_detected: bool = Field(..., description="Whether bias was detected")
    severity_level: str = Field(..., description="Severity level (none, low, medium, high)")
    findings: List[Dict] = Field(..., description="Detailed findings from bias analysis")
    recommendations: List[str] = Field(..., description="Recommendations for mitigation")
    generated_at: str = Field(..., description="Timestamp when report was generated (ISO 8601 format)")


class BiasReportListResponse(BaseModel):
    """Response model for bias reports list."""

    reports: List[BiasReport] = Field(..., description="List of bias reports")
    total_count: int = Field(..., description="Total number of reports")


class FairnessAlert(BaseModel):
    """Fairness alert information."""

    alert_id: str = Field(..., description="ID of the alert")
    model_name: str = Field(..., description="Name of the model")
    model_version: str = Field(..., description="Version of the model")
    alert_type: str = Field(..., description="Type of alert (bias_detected, threshold_exceeded, etc.)")
    severity: str = Field(..., description="Severity level (low, medium, high, critical)")
    protected_attribute: str = Field(..., description="Protected attribute affected")
    metric_name: str = Field(..., description="Metric that triggered the alert")
    current_value: float = Field(..., description="Current metric value")
    threshold_value: float = Field(..., description="Threshold that was exceeded")
    description: str = Field(..., description="Description of the alert")
    recommendation: str = Field(..., description="Recommended action")
    triggered_at: str = Field(..., description="Timestamp when alert was triggered (ISO 8601 format)")
    acknowledged: bool = Field(..., description="Whether alert has been acknowledged")


class FairnessAlertListResponse(BaseModel):
    """Response model for fairness alerts list."""

    alerts: List[FairnessAlert] = Field(..., description="List of fairness alerts")
    total_count: int = Field(..., description="Total number of alerts")
    unacknowledged_count: int = Field(..., description="Number of unacknowledged alerts")


class FairnessSummary(BaseModel):
    """Summary of fairness metrics across all models."""

    total_models: int = Field(..., description="Total number of models monitored")
    models_with_issues: int = Field(..., description="Number of models with fairness issues")
    overall_fairness_score: float = Field(..., description="Overall fairness across all models (0-1)")
    protected_attributes_analyzed: List[str] = Field(..., description="Protected attributes being monitored")
    recent_alerts: int = Field(..., description="Number of alerts in the last 24 hours")
    last_updated: str = Field(..., description="Timestamp of last update (ISO 8601 format)")


class FairnessTrendDataPoint(BaseModel):
    """Single data point in fairness trends time series."""

    timestamp: str = Field(..., description="Timestamp of the data point (ISO 8601 format)")
    disparate_impact_ratio: Optional[float] = Field(None, description="Disparate impact ratio value")
    demographic_parity_diff: Optional[float] = Field(None, description="Demographic parity difference value")
    equal_opportunity_diff: Optional[float] = Field(None, description="Equal opportunity difference value")
    average_odds_diff: Optional[float] = Field(None, description="Average odds difference value")
    theil_index: Optional[float] = Field(None, description="Theil index value")
    sample_size: int = Field(..., description="Number of samples evaluated")


class FairnessTrendsResponse(BaseModel):
    """Response model for fairness trends over time."""

    data_points: List[FairnessTrendDataPoint] = Field(..., description="Time series data points")
    total_count: int = Field(..., description="Total number of data points")
    start_date: str = Field(..., description="Start date of the time series")
    end_date: str = Field(..., description="End date of the time series")


@router.get(
    "/metrics",
    response_model=FairnessMetricsListResponse,
    tags=["Fairness"],
)
async def get_fairness_metrics(
    model_name: Optional[str] = Query(None, description="Filter by model name"),
    model_version: Optional[str] = Query(None, description="Filter by model version"),
    protected_attribute: Optional[str] = Query(None, description="Filter by protected attribute"),
    metric_type: Optional[str] = Query(None, description="Filter by metric type"),
    is_acceptable: Optional[bool] = Query(None, description="Filter by acceptability status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
) -> JSONResponse:
    """
    Get fairness metrics for AI models.

    This endpoint retrieves fairness metrics from the fairness_metrics table,
    supporting filtering by model name, version, protected attribute, and metric type.
    Returns metrics in reverse chronological order (most recent first).

    Fairness metrics include:
    - Disparate Impact Ratio: Measures adverse impact on protected groups
    - Demographic Parity Difference: Difference in selection rates
    - Equal Opportunity Difference: Difference in true positive rates
    - Average Odds Difference: Average of FPR and TPR differences
    - Theil Index: Measure of inequality in outcomes

    Args:
        model_name: Optional filter for specific model name
        model_version: Optional filter for specific model version
        protected_attribute: Optional filter for protected attribute (e.g., gender, race)
        metric_type: Optional filter for metric type
        is_acceptable: Optional filter for acceptability status
        limit: Maximum number of records to return (default: 100, max: 1000)

    Returns:
        JSON response with list of fairness metrics

    Raises:
        HTTPException(422): If validation fails
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/fairness/metrics?model_name=ranking")
        >>> response.json()
        {
            "metrics": [...],
            "total_count": 50
        }
    """
    try:
        logger.info(
            f"Fetching fairness metrics - model_name: {model_name}, "
            f"model_version: {model_version}, protected_attribute: {protected_attribute}, "
            f"metric_type: {metric_type}, is_acceptable: {is_acceptable}"
        )

        from database import get_db
        from models.fairness_metrics import FairnessMetrics as FairnessMetricsModel

        metrics_list = []
        total_count = 0

        async for db in get_db():
            # Build query for fairness metrics
            query = select(FairnessMetricsModel)

            # Apply filters
            if model_version:
                query = query.where(FairnessMetricsModel.model_version_id == model_version)

            if protected_attribute:
                query = query.where(FairnessMetricsModel.demographic_group == protected_attribute)

            # Order by created_at descending (most recent first)
            query = query.order_by(desc(FairnessMetricsModel.created_at))

            # Get total count
            from sqlalchemy import func
            count_query = select(func.count()).select_from(query)
            count_result = await db.execute(count_query)
            total_count = count_result.scalar() or 0

            # Apply limit
            query = query.limit(limit)

            # Execute query
            result = await db.execute(query)
            fairness_records = result.scalars().all()

            # Transform database records to API response format
            for record in fairness_records:
                # Determine model name (default to "ranking" for now)
                actual_model_name = model_name or "ranking"

                # Get calculated_at timestamp
                calculated_at = record.created_at.isoformat() if record.created_at else record.analysis_date

                # Create separate metric entries for each metric type
                metric_entries = []

                # Disparate Impact Ratio metric
                if record.disparate_impact_ratio is not None:
                    if metric_type is None or metric_type == "disparate_impact":
                        metric_is_acceptable = record.disparate_impact_ratio >= (record.alert_threshold or 0.8)
                        metric_entries.append({
                            "metric_id": str(record.id),
                            "model_name": actual_model_name,
                            "model_version": record.model_version_id or "unknown",
                            "protected_attribute": record.demographic_group,
                            "metric_type": "disparate_impact",
                            "metric_value": float(record.disparate_impact_ratio),
                            "threshold": float(record.alert_threshold or 0.8),
                            "is_acceptable": metric_is_acceptable,
                            "sample_size": record.total_sample_size or 0,
                            "calculated_at": calculated_at,
                        })

                # Statistical Parity Difference metric
                if record.statistical_parity_difference is not None:
                    if metric_type is None or metric_type == "statistical_parity":
                        # For statistical parity, lower absolute values are better (closer to 0)
                        metric_is_acceptable = abs(record.statistical_parity_difference) <= (1 - (record.alert_threshold or 0.8))
                        metric_entries.append({
                            "metric_id": str(record.id),
                            "model_name": actual_model_name,
                            "model_version": record.model_version_id or "unknown",
                            "protected_attribute": record.demographic_group,
                            "metric_type": "statistical_parity",
                            "metric_value": float(record.statistical_parity_difference),
                            "threshold": 1 - float(record.alert_threshold or 0.8),
                            "is_acceptable": metric_is_acceptable,
                            "sample_size": record.total_sample_size or 0,
                            "calculated_at": calculated_at,
                        })

                # Group Selection Rate metric
                if record.group_selection_rate is not None:
                    if metric_type is None or metric_type == "group_selection_rate":
                        metric_entries.append({
                            "metric_id": str(record.id),
                            "model_name": actual_model_name,
                            "model_version": record.model_version_id or "unknown",
                            "protected_attribute": record.demographic_group,
                            "metric_type": "group_selection_rate",
                            "metric_value": float(record.group_selection_rate),
                            "threshold": 0.0,  # No threshold for raw selection rate
                            "is_acceptable": True,
                            "sample_size": record.group_sample_size or 0,
                            "calculated_at": calculated_at,
                        })

                # Overall Selection Rate metric
                if record.overall_selection_rate is not None:
                    if metric_type is None or metric_type == "overall_selection_rate":
                        metric_entries.append({
                            "metric_id": str(record.id),
                            "model_name": actual_model_name,
                            "model_version": record.model_version_id or "unknown",
                            "protected_attribute": record.demographic_group,
                            "metric_type": "overall_selection_rate",
                            "metric_value": float(record.overall_selection_rate),
                            "threshold": 0.0,  # No threshold for raw selection rate
                            "is_acceptable": True,
                            "sample_size": record.total_sample_size or 0,
                            "calculated_at": calculated_at,
                        })

                # Filter by is_acceptable if specified
                for entry in metric_entries:
                    if is_acceptable is None or entry["is_acceptable"] == is_acceptable:
                        metrics_list.append(entry)

                # Apply limit to metrics list (since we may have multiple entries per record)
                if len(metrics_list) >= limit:
                    break

            break

        # Final limit application
        metrics_list = metrics_list[:limit]
        total_count = len(metrics_list)

        logger.info(f"Retrieved {total_count} fairness metrics")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "metrics": metrics_list,
                "total_count": total_count,
            },
        )

    except Exception as e:
        logger.error(f"Error fetching fairness metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch fairness metrics: {str(e)}",
        ) from e


@router.get(
    "/reports",
    response_model=BiasReportListResponse,
    tags=["Fairness"],
)
async def get_bias_reports(
    model_name: Optional[str] = Query(None, description="Filter by model name"),
    model_version: Optional[str] = Query(None, description="Filter by model version"),
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    severity_level: Optional[str] = Query(None, description="Filter by severity level"),
    bias_detected: Optional[bool] = Query(None, description="Filter by bias detection status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
) -> JSONResponse:
    """
    Get bias analysis reports.

    This endpoint retrieves bias analysis reports that provide comprehensive
    fairness evaluations of AI models. Reports include detailed findings,
    recommendations for mitigation, and severity assessments.

    Reports are generated from historical fairness metrics, grouped by analysis date.
    Each report aggregates metrics across all demographic groups analyzed on that date.

    Report types:
    - individual: Analysis of individual predictions for bias
    - group: Analysis of group-level disparities
    - system-wide: System-wide fairness analysis across all models

    Severity levels:
    - none: No bias detected
    - low: Minor bias within acceptable thresholds
    - medium: Moderate bias requiring attention
    - high: Severe bias requiring immediate action

    Args:
        model_name: Optional filter for specific model name
        model_version: Optional filter for specific model version
        report_type: Optional filter for report type
        severity_level: Optional filter for severity level
        bias_detected: Optional filter for bias detection status
        limit: Maximum number of records to return (default: 100, max: 1000)

    Returns:
        JSON response with list of bias reports

    Raises:
        HTTPException(422): If validation fails
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/fairness/reports?severity_level=high")
        >>> response.json()
        {
            "reports": [...],
            "total_count": 5
        }
    """
    try:
        logger.info(
            f"Fetching bias reports - model_name: {model_name}, "
            f"model_version: {model_version}, report_type: {report_type}, "
            f"severity_level: {severity_level}, bias_detected: {bias_detected}"
        )

        from database import get_db
        from models.fairness_metrics import FairnessMetrics as FairnessMetricsModel
        from sqlalchemy import func

        reports_list = []
        total_count = 0

        async for db in get_db():
            # Build query to get reports grouped by analysis_date and model_version
            # We'll create one report per unique analysis_date per model_version
            query = select(
                FairnessMetricsModel.analysis_date,
                FairnessMetricsModel.model_version_id,
                func.max(FairnessMetricsModel.created_at).label('created_at')
            ).group_by(
                FairnessMetricsModel.analysis_date,
                FairnessMetricsModel.model_version_id
            )

            # Apply model_version filter
            if model_version:
                query = query.where(FairnessMetricsModel.model_version_id == model_version)

            # Order by created_at descending (most recent first)
            query = query.order_by(desc(func.max(FairnessMetricsModel.created_at)))

            # Get total count before limit
            # Count unique (analysis_date, model_version) combinations
            count_query = select(
                func.count(func.distinct(
                    func.concat(FairnessMetricsModel.analysis_date, '|', FairnessMetricsModel.model_version_id)
                ))
            )

            if model_version:
                count_query = count_query.where(FairnessMetricsModel.model_version_id == model_version)

            count_result = await db.execute(count_query)
            total_count = count_result.scalar() or 0

            # Apply limit
            query = query.limit(limit)

            # Execute query to get report identifiers
            result = await db.execute(query)
            report_dates = result.all()

            # Build each report by aggregating metrics for that date
            for analysis_date, mv_id, created_at in report_dates:
                # Get all metrics for this analysis_date and model_version
                metrics_query = select(FairnessMetricsModel).where(
                    FairnessMetricsModel.analysis_date == analysis_date,
                    FairnessMetricsModel.model_version_id == mv_id
                )

                metrics_result = await db.execute(metrics_query)
                metrics_records = metrics_result.scalars().all()

                if not metrics_records:
                    continue

                # Aggregate metrics to build report
                actual_model_name = model_name or "ranking"
                actual_model_version = mv_id or "unknown"

                # Collect protected attributes analyzed
                protected_attributes = list(set([
                    m.demographic_group for m in metrics_records
                ]))

                # Calculate overall fairness score (average of disparate impact ratios)
                disparate_impact_values = [
                    m.disparate_impact_ratio for m in metrics_records
                    if m.disparate_impact_ratio is not None
                ]
                overall_fairness_score = (
                    sum(disparate_impact_values) / len(disparate_impact_values)
                    if disparate_impact_values
                    else 0.85
                )

                # Determine if bias was detected
                bias_detected_value = any(
                    m.alert_triggered for m in metrics_records
                )

                # Determine max severity level
                severity_ranks = {"low": 1, "medium": 2, "high": 3, "critical": 4, "none": 0}
                max_severity = "none"
                for m in metrics_records:
                    if m.alert_severity and severity_ranks.get(m.alert_severity, 0) > severity_ranks.get(max_severity, 0):
                        max_severity = m.alert_severity

                # Apply filters
                if severity_level and max_severity != severity_level:
                    continue
                if bias_detected is not None and bias_detected_value != bias_detected:
                    continue

                # Build findings list
                findings = []
                for m in metrics_records:
                    if m.alert_triggered:
                        findings.append({
                            "demographic_attribute": m.demographic_group,
                            "disparate_impact_ratio": float(m.disparate_impact_ratio) if m.disparate_impact_ratio else 1.0,
                            "statistical_parity_difference": float(m.statistical_parity_difference) if m.statistical_parity_difference else 0.0,
                            "severity": m.alert_severity or "low",
                            "sample_size": m.total_sample_size or 0,
                            "vacancy_id": str(m.vacancy_id) if m.vacancy_id else None,
                        })

                # Build recommendations list
                recommendations_set = set()
                for m in metrics_records:
                    if m.mitigation_suggested:
                        recommendations_set.add(m.mitigation_suggested)

                recommendations = sorted(list(recommendations_set)) if recommendations_set else ["No issues detected"]

                # Determine report_type
                # Use passed report_type or default to "system-wide"
                actual_report_type = report_type or "system-wide"

                # Generate report_id from analysis_date and model_version
                report_id = f"{analysis_date}_{actual_model_version}"

                # Get generated_at timestamp
                generated_at = created_at.isoformat() if created_at else analysis_date

                reports_list.append({
                    "report_id": report_id,
                    "model_name": actual_model_name,
                    "model_version": actual_model_version,
                    "report_type": actual_report_type,
                    "protected_attributes": protected_attributes,
                    "overall_fairness_score": round(overall_fairness_score, 2),
                    "bias_detected": bias_detected_value,
                    "severity_level": max_severity if max_severity != "none" else "none",
                    "findings": findings,
                    "recommendations": recommendations,
                    "generated_at": generated_at,
                })

                # Apply limit to reports list
                if len(reports_list) >= limit:
                    break

            break

        logger.info(f"Retrieved {len(reports_list)} bias reports")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "reports": reports_list,
                "total_count": total_count,
            },
        )

    except Exception as e:
        logger.error(f"Error fetching bias reports: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch bias reports: {str(e)}",
        ) from e


@router.get(
    "/alerts",
    response_model=FairnessAlertListResponse,
    tags=["Fairness"],
)
async def get_fairness_alerts(
    model_name: Optional[str] = Query(None, description="Filter by model name"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    severity: Optional[str] = Query(None, description="Filter by severity level"),
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledgment status"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back (default: 30, max: 365)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
) -> JSONResponse:
    """
    Get fairness alerts.

    This endpoint retrieves fairness alerts that are triggered when bias is detected
    or fairness thresholds are exceeded. Alerts provide actionable information about
    potential discrimination issues and recommended mitigation actions.

    Alert types:
    - bias_detected: Bias detected in model predictions
    - threshold_exceeded: Fairness metric exceeded acceptable threshold
    - disparate_impact: Disparate impact detected on protected group
    - data_drift: Data drift affecting fairness
    - model_degradation: Model performance degradation affecting fairness

    Severity levels:
    - low: Minor issue, monitor
    - medium: Moderate issue, investigate
    - high: Major issue, action required
    - critical: Severe issue, immediate action required

    Args:
        model_name: Optional filter for specific model name
        alert_type: Optional filter for alert type
        severity: Optional filter for severity level
        acknowledged: Optional filter for acknowledgment status
        days: Number of days to look back (default: 30, max: 365)
        limit: Maximum number of records to return (default: 100, max: 1000)

    Returns:
        JSON response with list of fairness alerts

    Raises:
        HTTPException(422): If validation fails
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/fairness/alerts?severity=high&acknowledged=false")
        >>> response.json()
        {
            "alerts": [...],
            "total_count": 3,
            "unacknowledged_count": 3
        }
    """
    try:
        logger.info(
            f"Fetching fairness alerts - model_name: {model_name}, "
            f"alert_type: {alert_type}, severity: {severity}, "
            f"acknowledged: {acknowledged}, days: {days}"
        )

        from database import get_db
        from models.fairness_metrics import FairnessAlert as FairnessAlertModel, FairnessMetrics as FairnessMetricsModel
        from sqlalchemy import func

        alerts_list = []
        total_count = 0
        unacknowledged_count = 0

        async for db in get_db():
            # Calculate date threshold
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Build query for fairness alerts with join to fairness_metrics
            query = (
                select(FairnessAlertModel, FairnessMetricsModel)
                .join(
                    FairnessMetricsModel,
                    FairnessAlertModel.fairness_metric_id == FairnessMetricsModel.id
                )
            )

            # Apply date filter - alerts created since cutoff date
            query = query.where(FairnessAlertModel.created_at >= cutoff_date)

            # Apply filters
            if alert_type:
                query = query.where(FairnessAlertModel.alert_type == alert_type)

            if severity:
                query = query.where(FairnessAlertModel.severity == severity)

            # Filter by acknowledgment status
            # acknowledged=True means status is 'acknowledged' or 'resolved'
            # acknowledged=False means status is 'active'
            if acknowledged is not None:
                if acknowledged:
                    query = query.where(FairnessAlertModel.status.in_(["acknowledged", "resolved"]))
                else:
                    query = query.where(FairnessAlertModel.status == "active")

            # Order by created_at descending (most recent first)
            query = query.order_by(desc(FairnessAlertModel.created_at))

            # Get total count before limit
            count_query = select(func.count()).select_from(query.subquery())
            count_result = await db.execute(count_query)
            total_count = count_result.scalar() or 0

            # Get unacknowledged count (active alerts)
            unack_query = (
                select(func.count())
                .select_from(FairnessAlertModel)
                .where(FairnessAlertModel.created_at >= cutoff_date)
                .where(FairnessAlertModel.status == "active")
            )
            if alert_type:
                unack_query = unack_query.where(FairnessAlertModel.alert_type == alert_type)
            if severity:
                unack_query = unack_query.where(FairnessAlertModel.severity == severity)

            unack_result = await db.execute(unack_query)
            unacknowledged_count = unack_result.scalar() or 0

            # Apply limit
            query = query.limit(limit)

            # Execute query
            result = await db.execute(query)
            alert_records = result.all()

            # Transform database records to API response format
            for alert_record, metrics_record in alert_records:
                # Determine if acknowledged
                is_acknowledged = alert_record.status in ["acknowledged", "resolved"]

                # Get protected attribute from metrics record
                protected_attribute = metrics_record.demographic_group if metrics_record else "unknown"

                # Determine model name (default to "ranking" for now)
                actual_model_name = model_name or "ranking"

                # Get triggered_at timestamp
                triggered_at = alert_record.created_at.isoformat() if alert_record.created_at else datetime.utcnow().isoformat()

                # Map alert type to metric name
                metric_name_map = {
                    "disparate_impact": "Disparate Impact Ratio",
                    "statistical_parity": "Statistical Parity Difference",
                    "sample_size": "Sample Size",
                    "threshold_exceeded": "Fairness Threshold",
                    "bias_detected": "Bias Detection",
                }
                metric_name = metric_name_map.get(alert_record.alert_type, alert_record.alert_type)

                # Build recommendation based on alert type
                recommendation_map = {
                    "disparate_impact": "Review selection criteria for potential bias. Consider retraining with fairness-aware algorithms.",
                    "statistical_parity": "Investigate group-specific selection rates. Ensure equal opportunity across demographics.",
                    "sample_size": "Increase sample size for more reliable fairness metrics.",
                    "threshold_exceeded": "Review and adjust fairness thresholds or investigate underlying bias in training data.",
                    "bias_detected": "Conduct detailed bias audit. Consider implementing fairness constraints in the model.",
                }
                recommendation = recommendation_map.get(alert_record.alert_type, "Investigate and address potential bias.")

                alerts_list.append({
                    "alert_id": str(alert_record.id),
                    "model_name": actual_model_name,
                    "model_version": metrics_record.model_version_id if metrics_record else "unknown",
                    "alert_type": alert_record.alert_type,
                    "severity": alert_record.severity,
                    "protected_attribute": protected_attribute,
                    "metric_name": metric_name,
                    "current_value": float(alert_record.actual_value) if alert_record.actual_value is not None else 0.0,
                    "threshold_value": float(alert_record.threshold_value) if alert_record.threshold_value is not None else 0.8,
                    "description": alert_record.message,
                    "recommendation": recommendation,
                    "triggered_at": triggered_at,
                    "acknowledged": is_acknowledged,
                })

            break

        logger.info(f"Retrieved {total_count} fairness alerts ({unacknowledged_count} unacknowledged)")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "alerts": alerts_list,
                "total_count": total_count,
                "unacknowledged_count": unacknowledged_count,
            },
        )

    except Exception as e:
        logger.error(f"Error fetching fairness alerts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch fairness alerts: {str(e)}",
        ) from e


@router.get(
    "/summary",
    response_model=FairnessSummary,
    tags=["Fairness"],
)
async def get_fairness_summary() -> JSONResponse:
    """
    Get fairness summary across all models.

    This endpoint provides a high-level summary of fairness metrics across
    all monitored models, including overall fairness scores, models with issues,
    and recent alert counts.

    Returns:
        JSON response with fairness summary

    Raises:
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/fairness/summary")
        >>> response.json()
        {
            "total_models": 5,
            "models_with_issues": 1,
            "overall_fairness_score": 0.87,
            "protected_attributes_analyzed": ["gender", "race", "age"],
            "recent_alerts": 2,
            "last_updated": "2024-01-25T10:30:00Z"
        }
    """
    try:
        logger.info("Fetching fairness summary")

        from database import get_db
        from models.fairness_metrics import FairnessMetrics as FairnessMetricsModel, FairnessAlert as FairnessAlertModel
        from sqlalchemy import func, distinct

        total_models = 0
        models_with_issues = 0
        overall_fairness_score = 0.0
        protected_attributes = set()
        recent_alerts_count = 0

        async for db in get_db():
            # Get unique model versions (total models monitored)
            model_count_result = await db.execute(
                select(func.count(distinct(FairnessMetricsModel.model_version_id)))
            )
            total_models = model_count_result.scalar() or 0

            # Get unique protected attributes analyzed
            attr_result = await db.execute(
                select(distinct(FairnessMetricsModel.demographic_group))
            )
            protected_attributes = {row[0] for row in attr_result if row[0]}

            # Calculate models with issues (where disparate_impact_ratio < threshold)
            # Count unique model versions with at least one metric below threshold
            if total_models > 0:
                # Get all metrics to calculate overall fairness and count issues
                all_metrics_result = await db.execute(
                    select(FairnessMetricsModel)
                )
                all_metrics = all_metrics_result.scalars().all()

                if all_metrics:
                    # Calculate overall fairness score (average of disparate impact ratios)
                    disparate_impact_values = [
                        m.disparate_impact_ratio for m in all_metrics
                        if m.disparate_impact_ratio is not None
                    ]
                    if disparate_impact_values:
                        overall_fairness_score = sum(disparate_impact_values) / len(disparate_impact_values)
                    else:
                        overall_fairness_score = 0.85  # Default if no metrics available

                    # Count models with issues (at least one metric below threshold)
                    models_with_issues_result = await db.execute(
                        select(func.count(distinct(FairnessMetricsModel.model_version_id)))
                        .where(FairnessMetricsModel.disparate_impact_ratio < (FairnessMetricsModel.alert_threshold | 0.8))
                    )
                    models_with_issues = models_with_issues_result.scalar() or 0
                else:
                    overall_fairness_score = 0.85  # Default placeholder

            # Count recent alerts in last 24 hours
            cutoff_date = datetime.utcnow() - timedelta(days=1)
            recent_alerts_result = await db.execute(
                select(func.count(FairnessAlertModel.id))
                .where(FairnessAlertModel.created_at >= cutoff_date)
            )
            recent_alerts_count = recent_alerts_result.scalar() or 0

            break

        # Build response data
        response_data = {
            "total_models": total_models,
            "models_with_issues": models_with_issues,
            "overall_fairness_score": round(overall_fairness_score, 2),
            "protected_attributes_analyzed": sorted(list(protected_attributes)),
            "recent_alerts": recent_alerts_count,
            "last_updated": datetime.utcnow().isoformat() + "Z",
        }

        logger.info(
            f"Retrieved fairness summary - {total_models} models, "
            f"{models_with_issues} with issues, "
            f"fairness score: {response_data['overall_fairness_score']}"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error fetching fairness summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch fairness summary: {str(e)}",
        ) from e


@router.get(
    "/trends",
    response_model=FairnessTrendsResponse,
    tags=["Fairness"],
)
async def get_fairness_trends(
    start_date: str = Query(..., description="Start date for trends (ISO 8601 format, e.g., 2026-01-01)"),
    end_date: str = Query(..., description="End date for trends (ISO 8601 format, e.g., 2026-03-21)"),
    model_name: Optional[str] = Query(None, description="Filter by model name"),
    model_version: Optional[str] = Query(None, description="Filter by model version"),
    protected_attribute: Optional[str] = Query(None, description="Filter by protected attribute"),
) -> JSONResponse:
    """
    Get historical fairness metrics as time series data.

    This endpoint retrieves fairness metrics over time, allowing users to track
    trends and patterns in AI model fairness. The data is aggregated by analysis
    date and includes all key fairness metrics.

    Time series data helps identify:
    - Trends in model fairness over time
    - Impact of model updates on fairness
    - Seasonal or temporal patterns in bias
    - Effectiveness of bias mitigation strategies

    Args:
        start_date: Start date for the time series (ISO 8601 format, required)
        end_date: End date for the time series (ISO 8601 format, required)
        model_name: Optional filter for specific model name
        model_version: Optional filter for specific model version
        protected_attribute: Optional filter for specific protected attribute

    Returns:
        JSON response with time series data points

    Raises:
        HTTPException(422): If date validation fails
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get(
        ...     "/api/fairness/trends?start_date=2026-01-01&end_date=2026-03-21"
        ... )
        >>> response.json()
        {
            "data_points": [
                {
                    "timestamp": "2026-01-15T00:00:00Z",
                    "disparate_impact_ratio": 0.85,
                    "demographic_parity_diff": 0.12,
                    "equal_opportunity_diff": 0.08,
                    "average_odds_diff": 0.10,
                    "theil_index": 0.05,
                    "sample_size": 1500
                },
                ...
            ],
            "total_count": 30,
            "start_date": "2026-01-01",
            "end_date": "2026-03-21"
        }
    """
    try:
        logger.info(
            f"Fetching fairness trends - start_date: {start_date}, end_date: {end_date}, "
            f"model_name: {model_name}, model_version: {model_version}, "
            f"protected_attribute: {protected_attribute}"
        )

        # Validate date parameters
        try:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

            if start_dt > end_dt:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="start_date must be before or equal to end_date",
                )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid date format. Use ISO 8601 format (e.g., 2026-01-01): {str(e)}",
            ) from e

        from database import get_db
        from models.fairness_metrics import FairnessMetrics as FairnessMetricsModel
        from sqlalchemy import func

        data_points = []
        total_count = 0

        async for db in get_db():
            # Build query to get metrics grouped by analysis_date
            query = select(
                FairnessMetricsModel.analysis_date,
                func.avg(FairnessMetricsModel.disparate_impact_ratio).label('avg_disparate_impact'),
                func.avg(FairnessMetricsModel.demographic_parity_diff).label('avg_demographic_parity'),
                func.avg(FairnessMetricsModel.equal_opportunity_diff).label('avg_equal_opportunity'),
                func.avg(FairnessMetricsModel.average_odds_diff).label('avg_average_odds'),
                func.avg(FairnessMetricsModel.theil_index).label('avg_theil_index'),
                func.sum(FairnessMetricsModel.sample_size).label('total_sample_size'),
            ).group_by(
                FairnessMetricsModel.analysis_date
            )

            # Apply date range filter
            query = query.where(FairnessMetricsModel.analysis_date >= start_date)
            query = query.where(FairnessMetricsModel.analysis_date <= end_date)

            # Apply optional filters
            if model_version:
                query = query.where(FairnessMetricsModel.model_version_id == model_version)

            if protected_attribute:
                query = query.where(FairnessMetricsModel.demographic_group == protected_attribute)

            # Order by analysis_date ascending (chronological)
            query = query.order_by(FairnessMetricsModel.analysis_date)

            # Execute query
            result = await db.execute(query)
            trend_records = result.all()

            total_count = len(trend_records)

            # Transform database records to API response format
            for record in trend_records:
                # Convert analysis_date to ISO 8601 timestamp
                timestamp = f"{record.analysis_date}T00:00:00Z"

                data_point = FairnessTrendDataPoint(
                    timestamp=timestamp,
                    disparate_impact_ratio=round(record.avg_disparate_impact, 3) if record.avg_disparate_impact else None,
                    demographic_parity_diff=round(record.avg_demographic_parity, 3) if record.avg_demographic_parity else None,
                    equal_opportunity_diff=round(record.avg_equal_opportunity, 3) if record.avg_equal_opportunity else None,
                    average_odds_diff=round(record.avg_average_odds, 3) if record.avg_average_odds else None,
                    theil_index=round(record.avg_theil_index, 3) if record.avg_theil_index else None,
                    sample_size=int(record.total_sample_size) if record.total_sample_size else 0,
                )
                data_points.append(data_point)

            break

        # Build response
        response_data = FairnessTrendsResponse(
            data_points=data_points,
            total_count=total_count,
            start_date=start_date,
            end_date=end_date,
        )

        logger.info(f"Retrieved {total_count} trend data points from {start_date} to {end_date}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data.model_dump(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching fairness trends: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch fairness trends: {str(e)}",
        ) from e


@router.post(
    "/reports/generate",
    response_model=BiasReport,
    status_code=status.HTTP_201_CREATED,
    tags=["Fairness"],
)
async def generate_bias_report(
    model_name: str = Query(..., description="Model name to generate report for"),
    model_version: Optional[str] = Query(None, description="Optional model version"),
    report_type: str = Query("system-wide", description="Report type to generate"),
) -> JSONResponse:
    """
    Generate a new bias analysis report.

    This endpoint triggers a new bias analysis for the specified model.
    The analysis evaluates fairness across protected attributes and generates
    a comprehensive report with findings and recommendations.

    For "system-wide" reports, analyzes all active job vacancies and aggregates
    fairness metrics. For individual vacancy reports, use the vacancy_id parameter.

    Args:
        model_name: Name of the model to analyze (e.g., "ranking")
        model_version: Optional model version (defaults to latest)
        report_type: Type of report to generate (individual, group, system-wide)

    Returns:
        Generated bias report with metrics, findings, and recommendations

    Raises:
        HTTPException(404): If model not found or no vacancies available
        HTTPException(422): If validation fails
        HTTPException(500): If report generation fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "/api/fairness/reports/generate?model_name=ranking&report_type=system-wide"
        ... )
        >>> response.json()
        {
            "report_id": "abc-123",
            "model_name": "ranking",
            "overall_fairness_score": 0.85,
            ...
        }
    """
    try:
        logger.info(
            f"Generating bias report - model_name: {model_name}, "
            f"model_version: {model_version}, report_type: {report_type}"
        )

        # Validate model name
        if not model_name or len(model_name.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Model name cannot be empty",
            )

        # Validate report type
        valid_report_types = ["individual", "group", "system-wide"]
        if report_type not in valid_report_types:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid report_type. Must be one of: {', '.join(valid_report_types)}",
            )

        from database import get_db
        from models.job_vacancy import JobVacancy
        from analyzers.fairness_calculator import get_fairness_calculator

        async for db in get_db():
            calculator = get_fairness_calculator()
            analysis_date = datetime.now().strftime("%Y-%m-%d")

            if report_type == "system-wide":
                # Generate system-wide report across all active vacancies
                response_data = await _generate_system_wide_report(
                    db, calculator, model_name, model_version, analysis_date
                )
            else:
                # For individual/group reports, analyze a sample vacancy
                # In a full implementation, this would accept a vacancy_id parameter
                response_data = await _generate_sample_report(
                    db, calculator, model_name, model_version, report_type, analysis_date
                )

        logger.info(f"Generated bias report {response_data['report_id']} for model {model_name}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating bias report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate bias report: {str(e)}",
        ) from e


async def _generate_system_wide_report(
    db,
    calculator,
    model_name: str,
    model_version: Optional[str],
    analysis_date: str,
) -> Dict:
    """
    Generate a system-wide fairness report across all active vacancies.

    Args:
        db: Database session
        calculator: FairnessCalculator instance
        model_name: Name of the model
        model_version: Optional model version
        analysis_date: Analysis date string

    Returns:
        System-wide report dictionary
    """
    from uuid import uuid4

    report_id = str(uuid4())

    # Get all active job vacancies
    vacancies_query = select(JobVacancy).where(JobVacancy.is_active == True)
    vacancies_result = await db.execute(vacancies_query)
    vacancies = vacancies_result.scalars().all()

    if not vacancies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active job vacancies found for analysis",
        )

    logger.info(f"Analyzing {len(vacancies)} active vacancies for system-wide report")

    # Collect metrics across all vacancies
    all_findings = []
    all_recommendations = set()
    protected_attributes_found = set()
    disparate_impact_scores = []
    bias_detected = False
    max_severity = "none"

    for vacancy in vacancies:
        try:
            # Get fairness report for this vacancy
            report = await calculator.get_fairness_report(db, vacancy.id, analysis_date)

            if report.get("status") == "no_data":
                continue

            # Extract findings
            for demographic, metrics in report.get("metrics_by_demographic", {}).items():
                protected_attributes_found.add(demographic)

                disparate_impact = metrics.get("disparate_impact_ratio", 1.0)
                disparate_impact_scores.append(disparate_impact)

                if disparate_impact < 0.8:
                    bias_detected = True
                    severity = metrics.get("alert_severity", "low")
                    if _severity_rank(severity) > _severity_rank(max_severity):
                        max_severity = severity

                    all_findings.append({
                        "vacancy_id": str(vacancy.id),
                        "vacancy_title": vacancy.title,
                        "demographic_attribute": demographic,
                        "disparate_impact_ratio": disparate_impact,
                        "statistical_parity_difference": metrics.get("statistical_parity_difference", 0.0),
                        "severity": severity,
                        "sample_size": metrics.get("sample_size", 0),
                    })

            # Collect recommendations
            for rec in report.get("recommendations", []):
                all_recommendations.add(rec.get("suggestion", ""))

        except Exception as e:
            logger.warning(f"Error analyzing vacancy {vacancy.id}: {e}")
            continue

    # Calculate overall fairness score (average of disparate impact ratios)
    overall_fairness_score = (
        sum(disparate_impact_scores) / len(disparate_impact_scores)
        if disparate_impact_scores
        else 0.85
    )

    # Build response
    response_data = {
        "report_id": report_id,
        "model_name": model_name,
        "model_version": model_version or "latest",
        "report_type": "system-wide",
        "protected_attributes": sorted(list(protected_attributes_found)) or ["gender", "age_group", "ethnicity"],
        "overall_fairness_score": round(overall_fairness_score, 2),
        "bias_detected": bias_detected,
        "severity_level": max_severity if max_severity != "none" else "none",
        "findings": all_findings,
        "recommendations": sorted(list(all_recommendations)) or ["No issues detected"],
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }

    return response_data


async def _generate_sample_report(
    db,
    calculator,
    model_name: str,
    model_version: Optional[str],
    report_type: str,
    analysis_date: str,
) -> Dict:
    """
    Generate a sample individual/group report.

    For demonstration, analyzes the first active vacancy.

    Args:
        db: Database session
        calculator: FairnessCalculator instance
        model_name: Name of the model
        model_version: Optional model version
        report_type: Report type (individual or group)
        analysis_date: Analysis date string

    Returns:
        Sample report dictionary
    """
    from uuid import uuid4

    report_id = str(uuid4())

    # Get a sample active vacancy
    vacancies_query = select(JobVacancy).where(JobVacancy.is_active == True).limit(1)
    vacancies_result = await db.execute(vacancies_query)
    vacancy = vacancies_result.scalar_one_or_none()

    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active job vacancies found for analysis",
        )

    logger.info(f"Generating {report_type} report for vacancy {vacancy.id}")

    # Get fairness report for this vacancy
    report = await calculator.get_fairness_report(db, vacancy.id, analysis_date)

    if report.get("status") == "no_data":
        # Return placeholder if no data available
        return {
            "report_id": report_id,
            "model_name": model_name,
            "model_version": model_version or "latest",
            "report_type": report_type,
            "protected_attributes": ["gender", "age_group", "ethnicity"],
            "overall_fairness_score": 0.85,
            "bias_detected": False,
            "severity_level": "none",
            "findings": [],
            "recommendations": ["Insufficient data for comprehensive analysis"],
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }

    # Extract metrics from the report
    all_findings = []
    all_recommendations = []
    protected_attributes = []
    disparate_impact_scores = []
    bias_detected = False
    max_severity = "none"

    for demographic, metrics in report.get("metrics_by_demographic", {}).items():
        protected_attributes.append(demographic)

        disparate_impact = metrics.get("disparate_impact_ratio", 1.0)
        disparate_impact_scores.append(disparate_impact)

        if disparate_impact < 0.8:
            bias_detected = True
            severity = metrics.get("alert_severity", "low")
            if _severity_rank(severity) > _severity_rank(max_severity):
                max_severity = severity

            all_findings.append({
                "vacancy_id": str(vacancy.id),
                "vacancy_title": vacancy.title,
                "demographic_attribute": demographic,
                "disparate_impact_ratio": disparate_impact,
                "statistical_parity_difference": metrics.get("statistical_parity_difference", 0.0),
                "severity": severity,
                "sample_size": metrics.get("sample_size", 0),
            })

    # Collect recommendations
    for rec in report.get("recommendations", []):
        all_recommendations.append(rec.get("suggestion", ""))

    # Calculate overall fairness score
    overall_fairness_score = (
        sum(disparate_impact_scores) / len(disparate_impact_scores)
        if disparate_impact_scores
        else 0.85
    )

    return {
        "report_id": report_id,
        "model_name": model_name,
        "model_version": model_version or "latest",
        "report_type": report_type,
        "protected_attributes": protected_attributes or ["gender", "age_group", "ethnicity"],
        "overall_fairness_score": round(overall_fairness_score, 2),
        "bias_detected": bias_detected,
        "severity_level": max_severity if max_severity != "none" else "none",
        "findings": all_findings,
        "recommendations": all_recommendations or ["No issues detected"],
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }


def _severity_rank(severity: Optional[str]) -> int:
    """Get numeric rank for severity comparison."""
    if not severity:
        return 0
    ranks = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    return ranks.get(severity, 0)


@router.post(
    "/alerts/{alert_id}/acknowledge",
    status_code=status.HTTP_200_OK,
    tags=["Fairness"],
)
async def acknowledge_alert(
    alert_id: str,
) -> JSONResponse:
    """
    Acknowledge a fairness alert.

    This endpoint marks a fairness alert as acknowledged, indicating that
    the alert has been reviewed and appropriate action is being taken.

    Args:
        alert_id: ID of the alert to acknowledge

    Returns:
        Acknowledged alert details

    Raises:
        HTTPException(404): If alert not found
        HTTPException(500): If acknowledgment fails

    Examples:
        >>> import requests
        >>> response = requests.post("/api/fairness/alerts/abc-123/acknowledge")
        >>> response.json()
        {
            "alert_id": "abc-123",
            "acknowledged": true,
            "acknowledged_at": "2024-01-25T10:30:00Z"
        }
    """
    try:
        logger.info(f"Acknowledging alert {alert_id}")

        from database import get_db
        from models.fairness_metrics import FairnessAlert as FairnessAlertModel

        async for db in get_db():
            # Query for the alert
            query = select(FairnessAlertModel).where(FairnessAlertModel.id == alert_id)
            result = await db.execute(query)
            alert = result.scalar_one_or_none()

            if not alert:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Alert with ID {alert_id} not found",
                )

            # Update alert status to acknowledged
            alert.status = "acknowledged"
            alert.acknowledged_at = datetime.utcnow().isoformat() + "Z"

            # Commit the changes
            await db.commit()
            await db.refresh(alert)

            logger.info(f"Acknowledged alert {alert_id}")

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "alert_id": str(alert.id),
                    "acknowledged": True,
                    "acknowledged_at": alert.acknowledged_at,
                },
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to acknowledge alert: {str(e)}",
        ) from e


@router.post(
    "/scorecard",
    status_code=status.HTTP_200_OK,
    tags=["Fairness"],
)
async def get_fairness_scorecard(
    vacancy_id: Optional[str] = Query(None, description="Optional vacancy ID for specific vacancy scorecard"),
    model_version: Optional[str] = Query(None, description="Optional model version filter"),
) -> JSONResponse:
    """
    Get fairness scorecard with feature importance bias source identification.

    This endpoint generates a comprehensive fairness scorecard that aggregates
    fairness metrics into an overall score (0-100) and identifies feature-level
    bias sources using model feature importance analysis.

    The scorecard includes:
    - Overall fairness score (0-100)
    - Feature bias sources with severity levels
    - Metrics breakdown by demographic
    - Actionable recommendations

    Args:
        vacancy_id: Optional JobVacancy UUID for specific vacancy analysis
        model_version: Optional model version filter

    Returns:
        JSON response with fairness scorecard data

    Raises:
        HTTPException(500): If scorecard generation fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "/api/fairness/scorecard?vacancy_id=abc-123"
        ... )
        >>> response.json()
        {
            "vacancy_id": "abc-123",
            "fairness_score": 82.5,
            "bias_sources": [...],
            "recommendations": [...]
        }
    """
    try:
        logger.info(
            f"Generating fairness scorecard - vacancy_id: {vacancy_id}, "
            f"model_version: {model_version}"
        )

        from database import get_db
        from services.fairness_scorecard import get_fairness_scorecard

        async for db in get_db():
            scorecard_service = get_fairness_scorecard()

            # Convert vacancy_id string to UUID if provided
            vacancy_uuid = None
            if vacancy_id:
                from uuid import UUID
                try:
                    vacancy_uuid = UUID(vacancy_id)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Invalid vacancy_id format: {vacancy_id}",
                    )

            # Generate scorecard
            scorecard = await scorecard_service.generate_scorecard(
                db=db,
                vacancy_id=vacancy_uuid,
                model_version=model_version,
            )

            # Build response - map feature_bias_sources to bias_sources
            response_data = {
                "vacancy_id": scorecard.vacancy_id,
                "vacancy_title": scorecard.vacancy_title,
                "fairness_score": scorecard.fairness_score,
                "bias_sources": scorecard.feature_bias_sources,
                "score_breakdown": scorecard.score_breakdown,
                "metrics_by_demographic": scorecard.metrics_by_demographic,
                "alerts_summary": scorecard.alerts_summary,
                "recommendations": scorecard.recommendations,
                "analyzed_at": scorecard.analyzed_at,
                "total_sample_size": scorecard.total_sample_size,
                "demographics_analyzed": scorecard.demographics_analyzed,
                "model_version": scorecard.model_version,
            }

            logger.info(
                f"Generated fairness scorecard - fairness_score: {scorecard.fairness_score}, "
                f"bias_sources: {len(scorecard.feature_bias_sources)}, "
                f"recommendations: {len(scorecard.recommendations)}"
            )

            break

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating fairness scorecard: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate fairness scorecard: {str(e)}",
        ) from e


@router.get(
    "/reports/{report_id}",
    response_model=BiasReport,
    tags=["Fairness"],
)
async def get_bias_report(
    report_id: str,
) -> JSONResponse:
    """
    Get a specific bias analysis report by ID.

    This endpoint retrieves detailed information about a specific bias analysis
    report including all findings, metrics, and recommendations.

    The report_id format is typically "{analysis_date}_{model_version}".

    Args:
        report_id: Unique identifier for the report

    Returns:
        JSON response with detailed bias report information

    Raises:
        HTTPException(404): If report not found
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("/api/fairness/reports/2024-01-25_v1.0")
        >>> response.json()
        {
            "report_id": "2024-01-25_v1.0",
            "model_name": "ranking",
            "findings": [...],
            ...
        }
    """
    try:
        logger.info(f"Fetching bias report {report_id}")

        from database import get_db
        from models.fairness_metrics import FairnessMetrics as FairnessMetricsModel

        async for db in get_db():
            # Parse report_id to extract analysis_date and model_version
            # Format: "{analysis_date}_{model_version}"
            parts = report_id.rsplit("_", 1)
            if len(parts) != 2:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Invalid report_id format: {report_id}. Expected format: YYYY-MM-DD_version",
                )

            analysis_date, model_version = parts

            # Get all metrics for this analysis_date and model_version
            metrics_query = select(FairnessMetricsModel).where(
                FairnessMetricsModel.analysis_date == analysis_date,
                FairnessMetricsModel.model_version_id == model_version
            )

            metrics_result = await db.execute(metrics_query)
            metrics_records = metrics_result.scalars().all()

            if not metrics_records:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Report not found: {report_id}",
                )

            # Build the report (similar to get_bias_reports logic but for single report)
            actual_model_name = "ranking"

            protected_attributes = list(set([
                m.demographic_group for m in metrics_records
            ]))

            disparate_impact_values = [
                m.disparate_impact_ratio for m in metrics_records
                if m.disparate_impact_ratio is not None
            ]
            overall_fairness_score = (
                sum(disparate_impact_values) / len(disparate_impact_values)
                if disparate_impact_values
                else 0.85
            )

            bias_detected_value = any(
                m.alert_triggered for m in metrics_records
            )

            severity_ranks = {"low": 1, "medium": 2, "high": 3, "critical": 4, "none": 0}
            max_severity = "none"
            for m in metrics_records:
                if m.alert_severity and severity_ranks.get(m.alert_severity, 0) > severity_ranks.get(max_severity, 0):
                    max_severity = m.alert_severity

            findings = []
            for m in metrics_records:
                if m.alert_triggered:
                    findings.append({
                        "demographic_attribute": m.demographic_group,
                        "disparate_impact_ratio": float(m.disparate_impact_ratio) if m.disparate_impact_ratio else 1.0,
                        "statistical_parity_difference": float(m.statistical_parity_difference) if m.statistical_parity_difference else 0.0,
                        "severity": m.alert_severity or "low",
                        "sample_size": m.total_sample_size or 0,
                        "vacancy_id": str(m.vacancy_id) if m.vacancy_id else None,
                    })

            recommendations_set = set()
            for m in metrics_records:
                if m.mitigation_suggested:
                    recommendations_set.add(m.mitigation_suggested)

            recommendations = sorted(list(recommendations_set)) if recommendations_set else ["No issues detected"]

            # Get generated_at timestamp
            created_at = max((m.created_at for m in metrics_records if m.created_at), default=None)
            generated_at = created_at.isoformat() if created_at else analysis_date

            report_data = {
                "report_id": report_id,
                "model_name": actual_model_name,
                "model_version": model_version,
                "report_type": "system-wide",
                "protected_attributes": protected_attributes,
                "overall_fairness_score": round(overall_fairness_score, 2),
                "bias_detected": bias_detected_value,
                "severity_level": max_severity if max_severity != "none" else "none",
                "findings": findings,
                "recommendations": recommendations,
                "generated_at": generated_at,
            }

            logger.info(f"Retrieved bias report {report_id}")
            break

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=report_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching bias report {report_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch bias report: {str(e)}",
        ) from e


@router.post(
    "/reports/{report_id}/export",
    tags=["Fairness"],
)
async def export_bias_report(
    report_id: str,
    format: str = Query("pdf", description="Export format: pdf or csv"),
) -> StreamingResponse:
    """
    Export a bias analysis report in PDF or CSV format.

    This endpoint generates a downloadable file containing the bias analysis
    report in the specified format. PDF reports include visualizations and
    professional formatting, while CSV exports provide raw metrics data.

    The report_id format is "{analysis_date}_{model_version}".

    Args:
        report_id: Unique identifier for the report
        format: Export format - "pdf" for formatted report, "csv" for raw metrics data

    Returns:
        StreamingResponse with file download

    Raises:
        HTTPException(404): If report not found
        HTTPException(422): If format is invalid
        HTTPException(500): If export generation fails

    Examples:
        >>> import requests
        >>> response = requests.post("/api/fairness/reports/2024-01-25_v1.0/export?format=pdf")
        >>> # Returns PDF file for download
    """
    try:
        logger.info(f"Exporting bias report {report_id} as {format}")

        # Validate format
        valid_formats = ["pdf", "csv"]
        if format not in valid_formats:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid format '{format}'. Must be one of: {', '.join(valid_formats)}",
            )

        from database import get_db
        from services.bias_report_generator import get_bias_report_generator

        # Get report generator service
        report_generator = get_bias_report_generator()
        if not report_generator:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="PDF report generation service is not available. Please install reportlab.",
            )

        # Parse report_id to extract analysis_date and model_version
        parts = report_id.rsplit("_", 1)
        if len(parts) != 2:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invalid report_id format: {report_id}. Expected format: YYYY-MM-DD_version",
            )

        analysis_date, model_version = parts

        async for db in get_db():
            if format == "pdf":
                # Generate PDF report
                result = await report_generator.generate_bias_report(
                    db=db,
                    vacancy_id=None,  # System-wide report
                    model_version=model_version,
                    analysis_date=analysis_date,
                    report_type="detailed_analysis",
                )

                if not result.success:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=result.error_message or "Failed to generate PDF report",
                    )

                # Return PDF as streaming response
                logger.info(f"Generated PDF export for report {report_id} ({result.file_size} bytes)")

                return StreamingResponse(
                    io.BytesIO(result.report_bytes),
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": f"attachment; filename={result.filename}",
                        "Content-Length": str(result.file_size),
                    },
                )

            else:  # format == "csv"
                # Generate CSV export
                result = await report_generator.generate_csv_export(
                    db=db,
                    vacancy_id=None,
                    model_version=model_version,
                    analysis_date=analysis_date,
                )

                if not result.success:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=result.error_message or "Failed to generate CSV export",
                    )

                # Return CSV as streaming response
                logger.info(f"Generated CSV export for report {report_id} ({result.file_size} bytes)")

                return StreamingResponse(
                    io.BytesIO(result.report_bytes),
                    media_type="text/csv",
                    headers={
                        "Content-Disposition": f"attachment; filename={result.filename}",
                        "Content-Length": str(result.file_size),
                    },
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting bias report {report_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export bias report: {str(e)}",
        ) from e
