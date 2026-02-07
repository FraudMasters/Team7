"""
Prometheus Metrics Utility Module

This module provides a centralized registry for Prometheus metrics across the backend API.
It supports:
- Counter metrics for event counting (requests, errors, tasks)
- Histogram metrics for timing distributions (request duration, query time)
- Gauge metrics for current state (active connections, queue depth)
- Label-based metric segmentation for detailed analysis

Metrics are automatically registered with the default Prometheus registry and
exposed via the /metrics endpoint for scraping by Prometheus server.
"""
import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple

from prometheus_client import Counter, Gauge, Histogram, Summary
from prometheus_client.registry import CollectorRegistry

logger = logging.getLogger(__name__)


class MetricsRegistry:
    """
    Centralized registry for Prometheus metrics.

    This class provides a singleton pattern for managing all Prometheus metrics
    in the application. It initializes counters, histograms, and gauges with
    appropriate labels and buckets for monitoring system performance.

    Attributes:
        http_requests_total: Counter for total HTTP requests
        http_request_duration_seconds: Histogram for request duration
        http_requests_in_progress: Gauge for in-flight requests
        http_errors_total: Counter for HTTP errors
        db_query_duration_seconds: Histogram for database query timing
        db_connections_active: Gauge for active database connections
        celery_tasks_total: Counter for Celery task executions
        celery_task_duration_seconds: Histogram for task execution time
        celery_queue_length: Gauge for task queue depth
        ml_inference_duration_seconds: Histogram for ML model inference timing
        ml_predictions_total: Counter for total ML predictions

    Example:
        >>> registry = MetricsRegistry()
        >>> registry.http_requests_total.labels(
        ...     method="GET", endpoint="/api/resumes", status="200"
        ... ).inc()
        >>> registry.http_request_duration_seconds.observe(0.123)
    """

    def __init__(self, registry: Optional[CollectorRegistry] = None) -> None:
        """
        Initialize the metrics registry.

        Args:
            registry: Optional Prometheus CollectorRegistry. If None, uses default registry.

        Example:
            >>> registry = MetricsRegistry()
            >>> # Use default Prometheus registry
        """
        self._registry = registry

        # HTTP Request Metrics
        self.http_requests_total = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"],
            registry=self._registry,
        )

        self.http_request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "HTTP request latency in seconds",
            ["method", "endpoint"],
            buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
            registry=self._registry,
        )

        self.http_requests_in_progress = Gauge(
            "http_requests_in_progress",
            "Number of HTTP requests in progress",
            ["method", "endpoint"],
            registry=self._registry,
        )

        self.http_errors_total = Counter(
            "http_errors_total",
            "Total HTTP errors",
            ["method", "endpoint", "status", "error_type"],
            registry=self._registry,
        )

        # Database Query Metrics
        self.db_query_duration_seconds = Histogram(
            "db_query_duration_seconds",
            "Database query execution time in seconds",
            ["operation", "table"],
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
            registry=self._registry,
        )

        self.db_connections_active = Gauge(
            "db_connections_active",
            "Number of active database connections",
            ["state"],  # states: active, idle
            registry=self._registry,
        )

        self.db_queries_total = Counter(
            "db_queries_total",
            "Total database queries executed",
            ["operation", "table", "status"],
            registry=self._registry,
        )

        # Database Pool Metrics
        self.db_pool_size = Gauge(
            "db_pool_size",
            "Database connection pool size",
            registry=self._registry,
        )

        self.db_pool_overflow = Gauge(
            "db_pool_overflow",
            "Database connection pool overflow connections",
            registry=self._registry,
        )

        self.db_pool_checked_out = Gauge(
            "db_pool_checked_out",
            "Number of database connections currently checked out",
            registry=self._registry,
        )

        self.db_pool_available = Gauge(
            "db_pool_available",
            "Number of available database connections in pool",
            registry=self._registry,
        )

        self.db_pool_checkout_duration_seconds = Histogram(
            "db_pool_checkout_duration_seconds",
            "Database connection checkout time in seconds",
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
            registry=self._registry,
        )

        self.db_pool_checkouts_total = Counter(
            "db_pool_checkouts_total",
            "Total database connection checkouts",
            ["status"],  # status: success, timeout, error
            registry=self._registry,
        )

        # Celery Task Metrics
        self.celery_tasks_total = Counter(
            "celery_tasks_total",
            "Total Celery tasks executed",
            ["task_name", "status"],
            registry=self._registry,
        )

        self.celery_task_duration_seconds = Histogram(
            "celery_task_duration_seconds",
            "Celery task execution time in seconds",
            ["task_name"],
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0),
            registry=self._registry,
        )

        self.celery_queue_length = Gauge(
            "celery_queue_length",
            "Number of tasks in Celery queue",
            ["queue_name"],
            registry=self._registry,
        )

        self.celery_workers_active = Gauge(
            "celery_workers_active",
            "Number of active Celery workers",
            registry=self._registry,
        )

        # ML Model Inference Metrics
        self.ml_inference_duration_seconds = Histogram(
            "ml_inference_duration_seconds",
            "ML model inference time in seconds",
            ["model_name", "operation"],
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
            registry=self._registry,
        )

        self.ml_predictions_total = Counter(
            "ml_predictions_total",
            "Total ML predictions made",
            ["model_name", "prediction_type"],
            registry=self._registry,
        )

        self.ml_models_loaded = Gauge(
            "ml_models_loaded",
            "Number of ML models currently loaded in memory",
            ["model_type"],
            registry=self._registry,
        )

        # System Resource Metrics
        self.system_memory_usage_bytes = Gauge(
            "system_memory_usage_bytes",
            "System memory usage in bytes",
            ["type"],  # types: used, cached, buffers
            registry=self._registry,
        )

        self.system_cpu_usage_percent = Gauge(
            "system_cpu_usage_percent",
            "System CPU usage percentage",
            registry=self._registry,
        )

        logger.info("MetricsRegistry initialized with Prometheus metrics")

    def record_http_request(
        self,
        method: str,
        endpoint: str,
        status: int,
        duration: float,
        error_type: Optional[str] = None,
    ) -> None:
        """
        Record HTTP request metrics.

        Increments request counters, records request duration, and optionally
        records error metrics if the request failed.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: Request endpoint path
            status: HTTP status code
            duration: Request duration in seconds
            error_type: Optional error type if request failed

        Example:
            >>> registry = MetricsRegistry()
            >>> registry.record_http_request("GET", "/api/resumes", 200, 0.123)
        """
        try:
            # Record request count
            self.http_requests_total.labels(
                method=method, endpoint=endpoint, status=str(status)
            ).inc()

            # Record request duration
            self.http_request_duration_seconds.labels(
                method=method, endpoint=endpoint
            ).observe(duration)

            # Record error if applicable
            if status >= 400 and error_type:
                self.http_errors_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status=str(status),
                    error_type=error_type,
                ).inc()

            logger.debug(
                f"Recorded HTTP metric: {method} {endpoint} -> {status} ({duration:.3f}s)"
            )

        except Exception as e:
            logger.error(f"Error recording HTTP request metric: {e}", exc_info=True)

    def record_db_query(
        self,
        operation: str,
        table: str,
        duration: float,
        status: str = "success",
    ) -> None:
        """
        Record database query metrics.

        Records query timing and execution counts for database operations.

        Args:
            operation: Type of query (SELECT, INSERT, UPDATE, DELETE)
            table: Database table name
            duration: Query execution time in seconds
            status: Query status (success, error)

        Example:
            >>> registry = MetricsRegistry()
            >>> registry.record_db_query("SELECT", "resumes", 0.045)
        """
        try:
            # Record query count
            self.db_queries_total.labels(
                operation=operation, table=table, status=status
            ).inc()

            # Record query duration
            self.db_query_duration_seconds.labels(
                operation=operation, table=table
            ).observe(duration)

            logger.debug(
                f"Recorded DB query metric: {operation} on {table} ({duration:.3f}s)"
            )

        except Exception as e:
            logger.error(f"Error recording DB query metric: {e}", exc_info=True)

    def record_celery_task(
        self,
        task_name: str,
        duration: float,
        status: str = "success",
    ) -> None:
        """
        Record Celery task execution metrics.

        Records task execution timing and completion status.

        Args:
            task_name: Name of the Celery task
            duration: Task execution time in seconds
            status: Task status (success, failure, retry)

        Example:
            >>> registry = MetricsRegistry()
            >>> registry.record_celery_task("process_resume", 2.34, "success")
        """
        try:
            # Record task count
            self.celery_tasks_total.labels(task_name=task_name, status=status).inc()

            # Record task duration
            self.celery_task_duration_seconds.labels(task_name=task_name).observe(
                duration
            )

            logger.debug(
                f"Recorded Celery task metric: {task_name} -> {status} ({duration:.3f}s)"
            )

        except Exception as e:
            logger.error(f"Error recording Celery task metric: {e}", exc_info=True)

    def record_ml_inference(
        self,
        model_name: str,
        operation: str,
        duration: float,
        prediction_type: Optional[str] = None,
    ) -> None:
        """
        Record ML model inference metrics.

        Records model inference timing and prediction counts.

        Args:
            model_name: Name of the ML model
            operation: Type of operation (inference, training, embedding)
            duration: Inference time in seconds
            prediction_type: Optional type of prediction (classification, ranking, etc.)

        Example:
            >>> registry = MetricsRegistry()
            >>> registry.record_ml_inference("skill_extractor", "inference", 0.234)
        """
        try:
            # Record inference duration
            self.ml_inference_duration_seconds.labels(
                model_name=model_name, operation=operation
            ).observe(duration)

            # Record prediction count if type specified
            if prediction_type:
                self.ml_predictions_total.labels(
                    model_name=model_name, prediction_type=prediction_type
                ).inc()

            logger.debug(
                f"Recorded ML inference metric: {model_name} {operation} ({duration:.3f}s)"
            )

        except Exception as e:
            logger.error(f"Error recording ML inference metric: {e}", exc_info=True)

    def update_db_connections(self, active: int, idle: int) -> None:
        """
        Update database connection pool metrics.

        Args:
            active: Number of active connections
            idle: Number of idle connections

        Example:
            >>> registry = MetricsRegistry()
            >>> registry.update_db_connections(10, 5)
        """
        try:
            self.db_connections_active.labels(state="active").set(active)
            self.db_connections_active.labels(state="idle").set(idle)
            logger.debug(f"Updated DB connection metrics: {active} active, {idle} idle")
        except Exception as e:
            logger.error(f"Error updating DB connection metrics: {e}", exc_info=True)

    def update_db_pool_metrics(
        self,
        size: int,
        overflow: int,
        checked_out: int,
        available: int,
    ) -> None:
        """
        Update database connection pool metrics.

        Args:
            size: Total pool size
            overflow: Number of overflow connections
            checked_out: Number of checked out connections
            available: Number of available connections

        Example:
            >>> registry = MetricsRegistry()
            >>> registry.update_db_pool_metrics(10, 2, 8, 2)
        """
        try:
            self.db_pool_size.set(size)
            self.db_pool_overflow.set(overflow)
            self.db_pool_checked_out.set(checked_out)
            self.db_pool_available.set(available)
            logger.debug(
                f"Updated DB pool metrics: size={size}, overflow={overflow}, "
                f"checked_out={checked_out}, available={available}"
            )
        except Exception as e:
            logger.error(f"Error updating DB pool metrics: {e}", exc_info=True)

    def record_db_pool_checkout(self, duration: float, status: str = "success") -> None:
        """
        Record database connection pool checkout metrics.

        Args:
            duration: Checkout time in seconds
            status: Checkout status (success, timeout, error)

        Example:
            >>> registry = MetricsRegistry()
            >>> registry.record_db_pool_checkout(0.023, "success")
        """
        try:
            self.db_pool_checkouts_total.labels(status=status).inc()
            self.db_pool_checkout_duration_seconds.observe(duration)
            logger.debug(f"Recorded DB pool checkout: {duration:.3f}s ({status})")
        except Exception as e:
            logger.error(f"Error recording DB pool checkout metric: {e}", exc_info=True)

    def update_celery_queue_length(self, queue_name: str, length: int) -> None:
        """
        Update Celery queue length metric.

        Args:
            queue_name: Name of the Celery queue
            length: Current queue length

        Example:
            >>> registry = MetricsRegistry()
            >>> registry.update_celery_queue_length("default", 42)
        """
        try:
            self.celery_queue_length.labels(queue_name=queue_name).set(length)
            logger.debug(f"Updated Celery queue length: {queue_name} = {length}")
        except Exception as e:
            logger.error(f"Error updating Celery queue metric: {e}", exc_info=True)

    def update_loaded_models(self, model_type: str, count: int) -> None:
        """
        Update loaded ML models metric.

        Args:
            model_type: Type of model (transformer, spacy, sklearn)
            count: Number of models of this type loaded

        Example:
            >>> registry = MetricsRegistry()
            >>> registry.update_loaded_models("transformer", 3)
        """
        try:
            self.ml_models_loaded.labels(model_type=model_type).set(count)
            logger.debug(f"Updated loaded models: {model_type} = {count}")
        except Exception as e:
            logger.error(f"Error updating loaded models metric: {e}", exc_info=True)


# Singleton instance for global access
_registry_instance: Optional[MetricsRegistry] = None


def get_metrics_registry() -> MetricsRegistry:
    """
    Get the singleton MetricsRegistry instance.

    Creates the instance on first call and returns the same instance
    on subsequent calls.

    Returns:
        MetricsRegistry singleton instance

    Example:
        >>> registry = get_metrics_registry()
        >>> registry.record_http_request("GET", "/api/resumes", 200, 0.123)
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = MetricsRegistry()
        logger.info("Created MetricsRegistry singleton instance")
    return _registry_instance


def track_request_time(
    method: str,
    endpoint: str,
) -> Callable:
    """
    Decorator to track HTTP request duration.

    Automatically records request metrics when the decorated function is called.

    Args:
        method: HTTP method for the request
        endpoint: Endpoint path for the request

    Returns:
        Decorator function

    Example:
        >>> @track_request_time("GET", "/api/resumes")
        ... async def get_resumes():
        ...     return {"resumes": []}
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            registry = get_metrics_registry()
            start_time = time.time()
            status = 200

            try:
                # Increment in-progress gauge
                registry.http_requests_in_progress.labels(
                    method=method, endpoint=endpoint
                ).inc()

                # Execute the function
                result = await func(*args, **kwargs)
                return result

            except Exception as e:
                status = 500
                error_type = type(e).__name__
                logger.error(f"Request error: {e}", exc_info=True)
                raise

            finally:
                # Record metrics
                duration = time.time() - start_time
                registry.record_http_request(
                    method=method, endpoint=endpoint, status=status, duration=duration
                )

                # Decrement in-progress gauge
                registry.http_requests_in_progress.labels(
                    method=method, endpoint=endpoint
                ).dec()

        return async_wrapper

    return decorator


def track_db_query(operation: str, table: str) -> Callable:
    """
    Decorator to track database query duration.

    Args:
        operation: Type of database operation
        table: Database table name

    Returns:
        Decorator function

    Example:
        >>> @track_db_query("SELECT", "resumes")
        ... async def get_resume(db, resume_id):
        ...     return await db.execute(query)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            registry = get_metrics_registry()
            start_time = time.time()
            status = "success"

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                logger.error(f"Database query error: {e}", exc_info=True)
                raise
            finally:
                duration = time.time() - start_time
                registry.record_db_query(
                    operation=operation, table=table, duration=duration, status=status
                )

        return async_wrapper

    return decorator


def track_ml_inference(model_name: str, operation: str = "inference") -> Callable:
    """
    Decorator to track ML model inference duration.

    Args:
        model_name: Name of the ML model
        operation: Type of operation (default: "inference")

    Returns:
        Decorator function

    Example:
        >>> @track_ml_inference("skill_extractor", "inference")
        ... def extract_skills(text: str):
        ...     return model.predict(text)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            registry = get_metrics_registry()
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                registry.record_ml_inference(
                    model_name=model_name, operation=operation, duration=duration
                )

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            registry = get_metrics_registry()
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                registry.record_ml_inference(
                    model_name=model_name, operation=operation, duration=duration
                )

        # Return appropriate wrapper based on whether function is async
        import inspect

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
