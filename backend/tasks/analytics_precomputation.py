"""
Analytics precomputation tasks for background aggregation.

This module provides Celery tasks for pre-computing analytics aggregations
that would otherwise be expensive to calculate on-demand. Pre-computed metrics
are stored in Redis for fast retrieval via the analytics API.
"""
import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def broadcast_analytics_update(
    aggregation_type: str,
    data: Dict[str, Any],
) -> bool:
    """
    Broadcast analytics update via WebSocket to connected clients.

    This function sends WebSocket notifications to all connected clients
    when analytics aggregations are updated, enabling real-time dashboard
    refreshes without requiring polling.

    Args:
        aggregation_type: Type of aggregation (key_metrics, quality_metrics, etc.)
        data: Aggregation data to broadcast

    Returns:
        True if broadcast was successful, False otherwise

    Example:
        >>> data = {"time_to_hire": {...}, "computed_at": "..."}
        >>> success = broadcast_analytics_update("key_metrics", data)
        >>> success
        True
    """
    try:
        from api.websocket import broadcast_metrics_update, broadcast_predictive_update

        logger.info(f"Broadcasting {aggregation_type} update via WebSocket")

        # Determine which broadcast function to use based on aggregation type
        if aggregation_type == "key_metrics":
            broadcast_func = broadcast_metrics_update
        elif aggregation_type == "quality_metrics":
            broadcast_func = broadcast_metrics_update
        elif aggregation_type == "stage_duration":
            broadcast_func = broadcast_metrics_update
        elif aggregation_type == "predictive":
            broadcast_func = broadcast_predictive_update
        else:
            broadcast_func = broadcast_metrics_update

        # Run async broadcast function in new event loop
        asyncio.run(broadcast_func(data))

        logger.info(f"Successfully broadcast {aggregation_type} update to WebSocket clients")
        return True

    except Exception as e:
        logger.error(f"Failed to broadcast {aggregation_type} update: {e}", exc_info=True)
        return False


def compute_key_metrics_aggregations(
    date_range: Dict[str, datetime],
) -> Dict[str, Any]:
    """
    Compute key metrics aggregations from analytics events.

    This function queries analytics events and calculates aggregations for:
    - Time-to-hire metrics (average, median, min, max, percentiles)
    - Resume processing metrics (total, this month, this week, rate)
    - Match rate metrics (overall, high/low confidence counts, average)

    Args:
        date_range: Date range for the aggregation:
            - start: Start date
            - end: End date

    Returns:
        Dictionary containing aggregated metrics:
        {
            "time_to_hire": {
                "average_days": float,
                "median_days": float,
                "min_days": int,
                "max_days": int,
                "percentile_25": float,
                "percentile_75": float
            },
            "resumes": {
                "total_processed": int,
                "processed_this_month": int,
                "processed_this_week": int,
                "processing_rate_avg": float
            },
            "match_rates": {
                "overall_match_rate": float,
                "high_confidence_matches": int,
                "low_confidence_matches": int,
                "average_confidence": float
            },
            "computed_at": "2024-01-15T10:30:00Z"
        }

    Example:
        >>> from datetime import datetime, timedelta
        >>> date_rng = {
        ...     "start": datetime.utcnow() - timedelta(days=30),
        ...     "end": datetime.utcnow()
        ... }
        >>> metrics = compute_key_metrics_aggregations(date_rng)
        >>> print(metrics['time_to_hire']['average_days'])
        32.5
    """
    # Note: This is a placeholder for metrics aggregation
    # In a real implementation, you would:
    # 1. Query AnalyticsEvent table for events in date range
    # 2. Calculate time-to-hire from resume_uploaded to vacancy_filled events
    # 3. Count resume_processed events for processing metrics
    # 4. Calculate match rates from match_created events
    # 5. Use statistical functions for percentiles

    logger.info(
        f"Computing key metrics aggregations for range: "
        f"{date_range['start'].date()} to {date_range['end'].date()}"
    )

    # Placeholder data - replace with actual database queries
    # Using similar values to analytics.py for consistency
    aggregations = {
        "time_to_hire": {
            "average_days": 32.5,
            "median_days": 28.0,
            "min_days": 7,
            "max_days": 90,
            "percentile_25": 21.0,
            "percentile_75": 45.0,
        },
        "resumes": {
            "total_processed": 1250,
            "processed_this_month": 180,
            "processed_this_week": 42,
            "processing_rate_avg": 8.5,
        },
        "match_rates": {
            "overall_match_rate": 0.78,
            "high_confidence_matches": 890,
            "low_confidence_matches": 156,
            "average_confidence": 0.72,
        },
        "computed_at": datetime.utcnow().isoformat(),
    }

    logger.info("Key metrics aggregations computed successfully")
    return aggregations


def compute_quality_metrics_aggregations(
    date_range: Dict[str, datetime],
) -> Dict[str, Any]:
    """
    Compute ML/NLP model quality metrics aggregations.

    This function queries resume analysis results and calculates quality metrics:
    - Text extraction success rate and timing
    - NER accuracy and entity counts
    - Keyword extraction metrics
    - Grammar error rates
    - Matching confidence, precision, recall
    - Performance metrics and error rates

    Args:
        date_range: Date range for the aggregation:
            - start: Start date
            - end: End date

    Returns:
        Dictionary containing quality metrics aggregations:
        {
            "text_extraction_success_rate": float,
            "avg_extraction_time_seconds": float,
            "ner_accuracy": float,
            "entities_per_resume_avg": float,
            "avg_keywords_per_resume": float,
            "keyword_relevance_avg": float,
            "grammar_error_rate": float,
            "matching_confidence_avg": float,
            "matching_precision": float,
            "matching_recall": float,
            "avg_analysis_time_seconds": float,
            "error_rate": float,
            "total_analyzed": int,
            "computed_at": "2024-01-15T10:30:00Z"
        }

    Example:
        >>> from datetime import datetime, timedelta
        >>> date_rng = {
        ...     "start": datetime.utcnow() - timedelta(days=30),
        ...     "end": datetime.utcnow()
        ... }
        >>> metrics = compute_quality_metrics_aggregations(date_rng)
        >>> print(metrics['ner_accuracy'])
        0.92
    """
    logger.info(
        f"Computing quality metrics aggregations for range: "
        f"{date_range['start'].date()} to {date_range['end'].date()}"
    )

    # Placeholder data - replace with actual database queries
    # Query ResumeAnalysis table and calculate aggregations
    aggregations = {
        "text_extraction_success_rate": 0.98,
        "avg_extraction_time_seconds": 1.2,
        "ner_accuracy": 0.92,
        "entities_per_resume_avg": 15.3,
        "avg_keywords_per_resume": 8.5,
        "keyword_relevance_avg": 0.78,
        "grammar_error_rate": 0.35,
        "matching_confidence_avg": 0.75,
        "matching_precision": 0.87,
        "matching_recall": 0.82,
        "avg_analysis_time_seconds": 12.5,
        "error_rate": 0.02,
        "total_analyzed": 1250,
        "computed_at": datetime.utcnow().isoformat(),
    }

    logger.info("Quality metrics aggregations computed successfully")
    return aggregations


def compute_stage_duration_aggregations(
    date_range: Dict[str, datetime],
) -> Dict[str, Any]:
    """
    Compute stage duration metrics aggregations.

    This function queries hiring stage transitions and calculates duration metrics
    for each stage, including average, median, min, and max time spent in each stage.

    Args:
        date_range: Date range for the aggregation:
            - start: Start date
            - end: End date

    Returns:
        Dictionary containing stage duration aggregations:
        {
            "stages": [
                {
                    "stage_name": "applied",
                    "average_days": float,
                    "median_days": float,
                    "min_days": float,
                    "max_days": float,
                    "candidate_count": int
                },
                ...
            ],
            "computed_at": "2024-01-15T10:30:00Z"
        }

    Example:
        >>> from datetime import datetime, timedelta
        >>> date_rng = {
        ...     "start": datetime.utcnow() - timedelta(days=30),
        ...     "end": datetime.utcnow()
        ... }
        >>> metrics = compute_stage_duration_aggregations(date_rng)
        >>> print(len(metrics['stages']))
        8
    """
    logger.info(
        f"Computing stage duration aggregations for range: "
        f"{date_range['start'].date()} to {date_range['end'].date()}"
    )

    # Placeholder data - replace with actual database queries
    # Query HiringStage table and calculate duration metrics
    aggregations = {
        "stages": [
            {
                "stage_name": "applied",
                "average_days": 2.5,
                "median_days": 2.0,
                "min_days": 0.5,
                "max_days": 7.0,
                "candidate_count": 150,
            },
            {
                "stage_name": "screening",
                "average_days": 5.2,
                "median_days": 4.0,
                "min_days": 1.0,
                "max_days": 14.0,
                "candidate_count": 120,
            },
            {
                "stage_name": "interview",
                "average_days": 7.8,
                "median_days": 6.0,
                "min_days": 2.0,
                "max_days": 21.0,
                "candidate_count": 85,
            },
        ],
        "computed_at": datetime.utcnow().isoformat(),
    }

    logger.info("Stage duration aggregations computed successfully")
    return aggregations


def compute_predictive_analytics(
    date_range: Dict[str, datetime],
) -> Dict[str, Any]:
    """
    Compute predictive analytics for pipeline forecasting.

    This function analyzes historical hiring data to generate predictive insights:
    - Pipeline health forecasts (expected candidates by stage over time)
    - Hiring needs forecasts (expected hires, time to fill open positions)
    - Trend indicators (increasing/decreasing/stable patterns)
    - Confidence intervals for predictions
    - Model accuracy metrics

    Args:
        date_range: Date range for historical data analysis:
            - start: Start date
            - end: End date

    Returns:
        Dictionary containing predictive analytics:
        {
            "pipeline_forecast": {
                "next_30_days": {
                    "expected_candidates": int,
                    "by_stage": {
                        "applied": int,
                        "screening": int,
                        "interview": int,
                        "offer": int
                    },
                    "confidence_interval": {
                        "lower": int,
                        "upper": int
                    }
                },
                "next_90_days": {
                    "expected_candidates": int,
                    "by_stage": {...},
                    "confidence_interval": {...}
                }
            },
            "hiring_needs": {
                "open_positions": int,
                "expected_hires_next_30_days": int,
                "expected_hires_next_90_days": int,
                "avg_time_to_fill_days": float,
                "fill_probability": float
            },
            "trends": {
                "pipeline_health": "increasing" | "decreasing" | "stable",
                "time_to_hire": "improving" | "worsening" | "stable",
                "offer_acceptance_rate": "increasing" | "decreasing" | "stable"
            },
            "model_accuracy": {
                "mape": float,  # Mean Absolute Percentage Error
                "rmse": float,  # Root Mean Square Error
                "sample_size": int
            },
            "computed_at": "2024-01-15T10:30:00Z"
        }

    Example:
        >>> from datetime import datetime, timedelta
        >>> date_rng = {
        ...     "start": datetime.utcnow() - timedelta(days=90),
        ...     "end": datetime.utcnow()
        ... }
        >>> metrics = compute_predictive_analytics(date_rng)
        >>> print(metrics['pipeline_forecast']['next_30_days']['expected_candidates'])
        45
    """
    logger.info(
        f"Computing predictive analytics for range: "
        f"{date_range['start'].date()} to {date_range['end'].date()}"
    )

    # Placeholder data - replace with actual ML models
    # In a real implementation, you would:
    # 1. Query historical hiring data from AnalyticsEvent and Candidate tables
    # 2. Train time series forecasting models (ARIMA, Prophet, or ML-based)
    # 3. Generate predictions for next 30 and 90 days
    # 4. Calculate confidence intervals using statistical methods
    # 5. Detect trends using regression analysis
    # 6. Calculate model accuracy metrics (MAPE, RMSE) using test data

    predictions = {
        "pipeline_forecast": {
            "next_30_days": {
                "expected_candidates": 45,
                "by_stage": {
                    "applied": 120,
                    "screening": 85,
                    "interview": 45,
                    "offer": 15,
                },
                "confidence_interval": {
                    "lower": 38,
                    "upper": 52,
                },
            },
            "next_90_days": {
                "expected_candidates": 135,
                "by_stage": {
                    "applied": 360,
                    "screening": 255,
                    "interview": 135,
                    "offer": 45,
                },
                "confidence_interval": {
                    "lower": 115,
                    "upper": 155,
                },
            },
        },
        "hiring_needs": {
            "open_positions": 25,
            "expected_hires_next_30_days": 12,
            "expected_hires_next_90_days": 35,
            "avg_time_to_fill_days": 32.5,
            "fill_probability": 0.78,
        },
        "trends": {
            "pipeline_health": "increasing",
            "time_to_hire": "improving",
            "offer_acceptance_rate": "stable",
        },
        "model_accuracy": {
            "mape": 0.12,  # 12% Mean Absolute Percentage Error
            "rmse": 5.8,  # Root Mean Square Error
            "sample_size": 1250,
        },
        "computed_at": datetime.utcnow().isoformat(),
    }

    logger.info("Predictive analytics computed successfully")
    return predictions


def store_aggregation_in_cache(
    aggregation_type: str,
    data: Dict[str, Any],
    ttl: Optional[int] = None,
) -> bool:
    """
    Store computed aggregation in Redis cache.

    This function stores the pre-computed aggregation data in Redis
    with appropriate TTL for fast retrieval by the analytics API.

    Args:
        aggregation_type: Type of aggregation (key_metrics, quality_metrics, etc.)
        data: Aggregation data to store
        ttl: Optional TTL in seconds (defaults to settings.cache_ttl_analytics)

    Returns:
        True if stored successfully, False otherwise

    Example:
        >>> data = {"time_to_hire": {...}, "computed_at": "..."}
        >>> success = store_aggregation_in_cache("key_metrics", data)
        >>> success
        True
    """
    try:
        import redis

        logger.info(f"Storing {aggregation_type} aggregation in cache")

        # Connect to Redis
        redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=settings.redis_cache_max_connections,
        )

        # Generate cache key
        cache_key = f"{settings.redis_cache_key_prefix}:analytics:{aggregation_type}"

        # Store data with TTL
        if ttl is None:
            ttl = settings.cache_ttl_analytics

        # Serialize data as JSON for storage
        import json
        serialized_data = json.dumps(data)

        redis_client.setex(cache_key, ttl, serialized_data)

        logger.info(
            f"Successfully stored {aggregation_type} aggregation in cache "
            f"(key: {cache_key}, TTL: {ttl}s)"
        )

        return True

    except Exception as e:
        logger.error(f"Failed to store aggregation in cache: {e}", exc_info=True)
        return False


def retrieve_aggregation_from_cache(
    aggregation_type: str,
) -> Optional[Dict[str, Any]]:
    """
    Retrieve computed aggregation from Redis cache.

    This function retrieves pre-computed aggregation data from Redis,
    returning None if the data is not found or expired.

    Args:
        aggregation_type: Type of aggregation (key_metrics, quality_metrics, etc.)

    Returns:
        Cached aggregation data, or None if not found

    Example:
        >>> data = retrieve_aggregation_from_cache("key_metrics")
        >>> data is not None
        True
    """
    try:
        import redis

        # Connect to Redis
        redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=settings.redis_cache_max_connections,
        )

        # Generate cache key
        cache_key = f"{settings.redis_cache_key_prefix}:analytics:{aggregation_type}"

        # Retrieve data
        cached_data = redis_client.get(cache_key)

        if cached_data:
            import json
            data = json.loads(cached_data)
            logger.info(f"Retrieved {aggregation_type} aggregation from cache")
            return data
        else:
            logger.info(f"No cached data found for {aggregation_type}")
            return None

    except Exception as e:
        logger.error(f"Failed to retrieve aggregation from cache: {e}", exc_info=True)
        return None


@shared_task(
    name="tasks.analytics_precomputation.precompute_analytics_aggregations",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def precompute_analytics_aggregations(
    self,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """
    Pre-compute and cache analytics aggregations.

    This Celery task handles the complete workflow of pre-computing analytics
    aggregations for fast API retrieval:
    1. Check if recent aggregation exists in cache (skip if found and not force_refresh)
    2. Compute key metrics aggregations
    3. Compute quality metrics aggregations
    4. Compute stage duration aggregations
    5. Store all aggregations in Redis cache

    Task Workflow:
    1. Check cache for existing aggregations
    2. Calculate date ranges (last 30 days for key metrics, etc.)
    3. Query database and compute aggregations
    4. Store results in Redis with appropriate TTL
    5. Return summary of computed aggregations

    Args:
        self: Celery task instance (bind=True)
        force_refresh: Force re-computation even if cache exists (default: False)

    Returns:
        Dictionary containing precomputation results:
        - key_metrics: Whether key metrics were computed
        - quality_metrics: Whether quality metrics were computed
        - stage_duration: Whether stage duration was computed
        - cache_hits: Number of aggregations retrieved from cache
        - cache_stores: Number of aggregations stored in cache
        - processing_time_ms: Total processing time
        - status: Task status (completed/failed/cached)
        - error: Error message (if failed)

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For database or cache errors

    Example:
        >>> from tasks.analytics_precomputation import precompute_analytics_aggregations
        >>> task = precompute_analytics_aggregations.delay()
        >>> result = task.get()
        >>> print(result['status'])
        'completed'
    """
    start_time = time.time()
    total_steps = 5
    current_step = 0

    try:
        logger.info("Starting analytics aggregations precomputation")

        # Calculate date ranges
        now = datetime.utcnow()
        last_30_days = now - timedelta(days=30)
        last_7_days = now - timedelta(days=7)

        date_ranges = {
            "key_metrics": {
                "start": last_30_days,
                "end": now,
            },
            "quality_metrics": {
                "start": last_30_days,
                "end": now,
            },
            "stage_duration": {
                "start": last_30_days,
                "end": now,
            },
        }

        result = {
            "key_metrics": False,
            "quality_metrics": False,
            "stage_duration": False,
            "cache_hits": 0,
            "cache_stores": 0,
            "processing_time_ms": 0,
            "status": "completed",
        }

        # Step 1: Check cache for existing aggregations
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "checking_cache",
            "message": "Checking cache for existing aggregations...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Checking cache")

        if not force_refresh:
            cached_key_metrics = retrieve_aggregation_from_cache("key_metrics")
            if cached_key_metrics:
                result["cache_hits"] += 1
                logger.info("Found cached key metrics aggregations")

        # Step 2: Compute key metrics aggregations
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "computing_key_metrics",
            "message": "Computing key metrics aggregations...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Computing key metrics")

        if force_refresh or result["cache_hits"] == 0:
            key_metrics = compute_key_metrics_aggregations(date_ranges["key_metrics"])
            if store_aggregation_in_cache("key_metrics", key_metrics):
                result["cache_stores"] += 1
                result["key_metrics"] = True
                logger.info("Key metrics aggregations computed and cached")

                # Broadcast WebSocket notification
                broadcast_analytics_update("key_metrics", key_metrics)
        else:
            logger.info("Skipping key metrics computation (using cached data)")

        # Step 3: Compute quality metrics aggregations
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "computing_quality_metrics",
            "message": "Computing quality metrics aggregations...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Computing quality metrics")

        quality_metrics = compute_quality_metrics_aggregations(date_ranges["quality_metrics"])
        if store_aggregation_in_cache("quality_metrics", quality_metrics):
            result["cache_stores"] += 1
            result["quality_metrics"] = True
            logger.info("Quality metrics aggregations computed and cached")

            # Broadcast WebSocket notification
            broadcast_analytics_update("quality_metrics", quality_metrics)

        # Step 4: Compute stage duration aggregations
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "computing_stage_duration",
            "message": "Computing stage duration aggregations...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Computing stage duration")

        stage_metrics = compute_stage_duration_aggregations(date_ranges["stage_duration"])
        if store_aggregation_in_cache("stage_duration", stage_metrics):
            result["cache_stores"] += 1
            result["stage_duration"] = True
            logger.info("Stage duration aggregations computed and cached")

            # Broadcast WebSocket notification
            broadcast_analytics_update("stage_duration", stage_metrics)

        # Step 5: Finalize
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "finalizing",
            "message": "Finalizing precomputation...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Finalizing")

        processing_time_ms = round((time.time() - start_time) * 1000, 2)
        result["processing_time_ms"] = processing_time_ms

        # Update status based on what was done
        if result["cache_hits"] > 0 and result["cache_stores"] == 0:
            result["status"] = "cached"
        elif result["cache_stores"] > 0:
            result["status"] = "completed"

        logger.info(
            f"Analytics precomputation completed: "
            f"cache_hits={result['cache_hits']}, "
            f"cache_stores={result['cache_stores']}, "
            f"time={processing_time_ms}ms"
        )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        return {
            "key_metrics": False,
            "quality_metrics": False,
            "stage_duration": False,
            "cache_hits": 0,
            "cache_stores": 0,
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            "status": "failed",
            "error": "Analytics precomputation exceeded maximum time limit",
        }

    except Exception as e:
        logger.error(f"Error in analytics precomputation: {e}", exc_info=True)
        return {
            "key_metrics": False,
            "quality_metrics": False,
            "stage_duration": False,
            "cache_hits": 0,
            "cache_stores": 0,
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            "status": "failed",
            "error": str(e),
        }


@shared_task(
    name="tasks.analytics_precomputation.schedule_periodic_precomputation",
    bind=True,
)
def schedule_periodic_precomputation(
    self,
) -> Dict[str, Any]:
    """
    Schedule periodic analytics precomputation.

    This is a scheduled task (typically run every 5-10 minutes by Celery Beat)
    that triggers analytics precomputation to keep cache warm and ensure
    fast API response times.

    Task Workflow:
    1. Check if precomputation is needed (based on cache age)
    2. Trigger precompute_analytics_aggregations task if needed
    3. Return summary of scheduling results

    Returns:
        Dictionary containing scheduling results:
        - triggered: Whether precomputation was triggered
        - reason: Reason for triggering or skipping
        - processing_time_ms: Total processing time
        - status: Task status

    Example:
        >>> from tasks.analytics_precomputation import schedule_periodic_precomputation
        >>> task = schedule_periodic_precomputation.delay()
        >>> result = task.get()
        >>> print(result['triggered'])
        True
    """
    start_time = time.time()

    try:
        logger.info("Checking if periodic analytics precomputation is needed")

        # Check if cached data exists and is recent
        cached_data = retrieve_aggregation_from_cache("key_metrics")

        triggered = False
        reason = ""

        if cached_data is None:
            # No cached data, trigger precomputation
            triggered = True
            reason = "No cached data found"
        else:
            # Check if data is stale (older than cache_ttl_analytics / 2)
            computed_at_str = cached_data.get("computed_at")
            if computed_at_str:
                try:
                    computed_at = datetime.fromisoformat(computed_at_str)
                    age_seconds = (datetime.utcnow() - computed_at).total_seconds()
                    stale_threshold = settings.cache_ttl_analytics / 2

                    if age_seconds > stale_threshold:
                        triggered = True
                        reason = f"Cached data is stale (age: {age_seconds}s, threshold: {stale_threshold}s)"
                    else:
                        reason = f"Cached data is fresh (age: {age_seconds}s)"
                except ValueError:
                    triggered = True
                    reason = "Invalid computed_at timestamp in cache"
            else:
                triggered = True
                reason = "No computed_at timestamp in cache"

        if triggered:
            logger.info(f"Triggering analytics precomputation: {reason}")
            precompute_analytics_aggregations.delay()
        else:
            logger.info(f"Skipping analytics precomputation: {reason}")

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "triggered": triggered,
            "reason": reason,
            "processing_time_ms": processing_time_ms,
            "status": "completed",
        }

        logger.info(f"Periodic precomputation check completed: triggered={triggered}")

        return result

    except Exception as e:
        logger.error(f"Error in periodic precomputation scheduling: {e}", exc_info=True)
        return {
            "triggered": False,
            "reason": f"Error: {str(e)}",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            "status": "failed",
            "error": str(e),
        }


@shared_task(
    name="tasks.analytics_precomputation.schedule_periodic_predictive_refresh",
    bind=True,
)
def schedule_periodic_predictive_refresh(
    self,
) -> Dict[str, Any]:
    """
    Schedule periodic predictive analytics refresh.

    This is a scheduled task (typically run every 30-60 minutes by Celery Beat)
    that triggers predictive analytics computation to keep forecasting models
    up-to-date and ensure accurate predictions for hiring pipeline insights.

    Predictive analytics are more computationally expensive than regular aggregations,
    so they are refreshed less frequently and use longer historical time windows
    (90+ days) for training forecasting models.

    Task Workflow:
    1. Check if predictive analytics refresh is needed (based on cache age)
    2. Compute predictive analytics using historical data (last 90 days)
    3. Store results in Redis cache with appropriate TTL
    4. Broadcast WebSocket notification to connected clients
    5. Return summary of computation results

    Returns:
        Dictionary containing refresh results:
        - computed: Whether predictive analytics were computed
        - reason: Reason for computing or skipping
        - cached: Whether data was successfully cached
        - broadcast: Whether WebSocket notification was sent
        - processing_time_ms: Total processing time
        - status: Task status

    Example:
        >>> from tasks.analytics_precomputation import schedule_periodic_predictive_refresh
        >>> task = schedule_periodic_predictive_refresh.delay()
        >>> result = task.get()
        >>> print(result['computed'])
        True
    """
    start_time = time.time()

    try:
        logger.info("Checking if periodic predictive analytics refresh is needed")

        # Check if cached predictive data exists and is recent
        cached_data = retrieve_aggregation_from_cache("predictive")

        computed = False
        cached = False
        broadcast = False
        reason = ""

        if cached_data is None:
            # No cached data, compute predictive analytics
            computed = True
            reason = "No cached predictive data found"
        else:
            # Check if data is stale (older than cache_ttl_analytics)
            # Predictive analytics can be cached longer since they're more expensive
            computed_at_str = cached_data.get("computed_at")
            if computed_at_str:
                try:
                    computed_at = datetime.fromisoformat(computed_at_str)
                    age_seconds = (datetime.utcnow() - computed_at).total_seconds()
                    # Use full TTL as threshold for predictive analytics (refresh less frequently)
                    stale_threshold = settings.cache_ttl_analytics

                    if age_seconds > stale_threshold:
                        computed = True
                        reason = f"Cached predictive data is stale (age: {age_seconds}s, threshold: {stale_threshold}s)"
                    else:
                        reason = f"Cached predictive data is fresh (age: {age_seconds}s)"
                except ValueError:
                    computed = True
                    reason = "Invalid computed_at timestamp in predictive cache"
            else:
                computed = True
                reason = "No computed_at timestamp in predictive cache"

        if computed:
            logger.info(f"Computing predictive analytics: {reason}")

            # Calculate date range for predictive analytics (last 90 days for model training)
            now = datetime.utcnow()
            last_90_days = now - timedelta(days=90)

            date_range = {
                "start": last_90_days,
                "end": now,
            }

            # Compute predictive analytics
            predictive_analytics = compute_predictive_analytics(date_range)

            # Store in cache
            if store_aggregation_in_cache("predictive", predictive_analytics):
                cached = True
                logger.info("Predictive analytics cached successfully")

                # Broadcast WebSocket notification
                if broadcast_analytics_update("predictive", predictive_analytics):
                    broadcast = True
                    logger.info("Predictive analytics WebSocket notification sent")
            else:
                logger.warning("Failed to cache predictive analytics")
        else:
            logger.info(f"Skipping predictive analytics computation: {reason}")

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "computed": computed,
            "reason": reason,
            "cached": cached,
            "broadcast": broadcast,
            "processing_time_ms": processing_time_ms,
            "status": "completed",
        }

        logger.info(
            f"Periodic predictive refresh check completed: "
            f"computed={computed}, cached={cached}, broadcast={broadcast}"
        )

        return result

    except Exception as e:
        logger.error(f"Error in periodic predictive refresh scheduling: {e}", exc_info=True)
        return {
            "computed": False,
            "reason": f"Error: {str(e)}",
            "cached": False,
            "broadcast": False,
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            "status": "failed",
            "error": str(e),
        }
