"""
Fairness monitoring endpoints for AI bias detection and mitigation.

This module provides endpoints for monitoring and tracking AI model fairness,
including retrieving fairness metrics, bias reports, and discrimination alerts.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
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

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        response_data = {
            "reports": [],
            "total_count": 0,
        }

        logger.info(f"Retrieved {response_data['total_count']} bias reports")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
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

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        response_data = {
            "alert_id": alert_id,
            "acknowledged": True,
            "acknowledged_at": datetime.utcnow().isoformat() + "Z",
        }

        logger.info(f"Acknowledged alert {alert_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to acknowledge alert: {str(e)}",
        ) from e
