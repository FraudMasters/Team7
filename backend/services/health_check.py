"""
Health check service for monitoring system components and dependencies.

This module provides a comprehensive health checking framework for monitoring
the status of all system dependencies including database, Redis, Celery workers,
ML models, and external APIs.

The health check service supports:
- Base checker class with extensible interface
- Individual checkers for each system component
- Configurable timeouts and thresholds
- Detailed status reporting with metrics
- Graceful handling of unavailable services
- Overall system health aggregation

Health status levels:
- healthy: Service is fully operational
- degraded: Service is working but with limitations (e.g., slow response, some features unavailable)
- unhealthy: Service is down or critical functionality is broken
"""
import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from config import get_settings
from database import engine
from services.cache_service import CacheService

logger = logging.getLogger(__name__)

# Global health check service instance
_health_check_service: Optional["HealthCheckService"] = None


class HealthCheckResult:
    """
    Result object for health check operations.

    Attributes:
        component_name: Name of the component being checked
        status: Health status (healthy, degraded, unhealthy)
        response_time_ms: Response time in milliseconds
        message: Human-readable status message
        details: Additional component-specific details
        error: Error message if check failed

    Example:
        >>> result = HealthCheckResult("database", "healthy", 50, "Database OK")
        >>> print(result.to_dict())
        {'component': 'database', 'status': 'healthy', ...}
    """

    STATUS_HEALTHY = "healthy"
    STATUS_DEGRADED = "degraded"
    STATUS_UNHEALTHY = "unhealthy"

    def __init__(
        self,
        component_name: str,
        status: str,
        response_time_ms: float,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Initialize a health check result.

        Args:
            component_name: Name of the component being checked
            status: Health status (healthy, degraded, unhealthy)
            response_time_ms: Response time in milliseconds
            message: Human-readable status message
            details: Additional component-specific details
            error: Error message if check failed
        """
        self.component_name = component_name
        self.status = status
        self.response_time_ms = response_time_ms
        self.message = message
        self.details = details or {}
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert result to dictionary.

        Returns:
            Dictionary representation of the health check result
        """
        return {
            "component": self.component_name,
            "status": self.status,
            "response_time_ms": round(self.response_time_ms, 2),
            "message": self.message,
            "details": self.details,
            "error": self.error,
        }

    def is_healthy(self) -> bool:
        """
        Check if the component is healthy.

        Returns:
            True if status is healthy, False otherwise
        """
        return self.status == self.STATUS_HEALTHY

    def is_operational(self) -> bool:
        """
        Check if the component is operational (healthy or degraded).

        Returns:
            True if status is healthy or degraded, False if unhealthy
        """
        return self.status in (self.STATUS_HEALTHY, self.STATUS_DEGRADED)

    def __getitem__(self, key: str) -> Any:
        """
        Allow dictionary-style access to result attributes.

        This enables accessing result values using notation like result['status']
        for convenience and backwards compatibility.

        Args:
            key: The attribute name to access

        Returns:
            The value of the attribute

        Raises:
            KeyError: If the key is not a valid attribute
        """
        key_map = {
            "component": "component_name",
            "component_name": "component_name",
            "status": "status",
            "response_time_ms": "response_time_ms",
            "message": "message",
            "details": "details",
            "error": "error",
        }

        attr_name = key_map.get(key)
        if attr_name is None:
            raise KeyError(f"Invalid key: {key}")

        return getattr(self, attr_name)


class BaseHealthChecker(ABC):
    """
    Abstract base class for health checkers.

    All health checkers should inherit from this class and implement
    the check() method.

    Attributes:
        timeout_seconds: Maximum time to wait for health check

    Example:
        >>> class CustomChecker(BaseHealthChecker):
        ...     async def check(self) -> HealthCheckResult:
        ...         # Implementation here
        ...         return HealthCheckResult(...)
    """

    def __init__(self, timeout_seconds: Optional[int] = None) -> None:
        """
        Initialize the health checker.

        Args:
            timeout_seconds: Maximum time to wait for health check (defaults to settings)
        """
        settings = get_settings()
        self.timeout_seconds = timeout_seconds or getattr(
            settings, "health_check_timeout_seconds", 5
        )

    @abstractmethod
    async def check(self) -> HealthCheckResult:
        """
        Perform health check for this component.

        This method must be implemented by subclasses.

        Returns:
            HealthCheckResult with component status
        """
        pass

    async def check_with_timeout(self) -> HealthCheckResult:
        """
        Perform health check with timeout enforcement.

        Wraps the check() method with asyncio timeout to ensure
        the health check doesn't hang indefinitely.

        Returns:
            HealthCheckResult with component status
        """
        try:
            return await asyncio.wait_for(
                self.check(),
                timeout=self.timeout_seconds,
            )
        except asyncio.TimeoutError:
            return HealthCheckResult(
                component_name=self.__class__.__name__.replace("Checker", "").lower(),
                status=HealthCheckResult.STATUS_UNHEALTHY,
                response_time_ms=self.timeout_seconds * 1000,
                message=f"Health check timed out after {self.timeout_seconds}s",
                error="timeout",
            )
        except Exception as e:
            logger.error(
                f"Unexpected error in {self.__class__.__name__}: {e}",
                exc_info=True,
            )
            return HealthCheckResult(
                component_name=self.__class__.__name__.replace("Checker", "").lower(),
                status=HealthCheckResult.STATUS_UNHEALTHY,
                response_time_ms=0,
                message=f"Health check failed with unexpected error",
                error=str(e),
            )


class DatabaseHealthChecker(BaseHealthChecker):
    """
    Health checker for PostgreSQL database connectivity.

    Checks database connection by executing a simple query.
    """

    async def check(self) -> HealthCheckResult:
        """
        Check database connectivity and response time.

        Returns:
            HealthCheckResult with database status
        """
        start_time = time.time()
        component_name = "database"

        try:
            # Test connection with simple query
            async with engine.begin() as conn:
                await conn.execute("SELECT 1")

            response_time_ms = (time.time() - start_time) * 1000

            # Check if response time is acceptable
            settings = get_settings()
            slow_threshold_ms = getattr(settings, "health_check_slow_threshold_ms", 500)

            if response_time_ms > slow_threshold_ms:
                logger.warning(
                    f"Database health check slow: {response_time_ms:.2f}ms"
                )
                return HealthCheckResult(
                    component_name=component_name,
                    status=HealthCheckResult.STATUS_DEGRADED,
                    response_time_ms=response_time_ms,
                    message=f"Database response is slow ({response_time_ms:.2f}ms)",
                    details={"response_time_ms": response_time_ms},
                )

            logger.debug(f"Database health check passed: {response_time_ms:.2f}ms")
            return HealthCheckResult(
                component_name=component_name,
                status=HealthCheckResult.STATUS_HEALTHY,
                response_time_ms=response_time_ms,
                message="Database is operational",
                details={"response_time_ms": response_time_ms},
            )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Database health check failed: {e}")
            return HealthCheckResult(
                component_name=component_name,
                status=HealthCheckResult.STATUS_UNHEALTHY,
                response_time_ms=response_time_ms,
                message="Database is unreachable",
                error=str(e),
            )


class RedisHealthChecker(BaseHealthChecker):
    """
    Health checker for Redis connectivity.

    Checks Redis connection using the CacheService health_check method.
    """

    def __init__(self, timeout_seconds: Optional[int] = None) -> None:
        """
        Initialize the Redis health checker.

        Args:
            timeout_seconds: Maximum time to wait for health check
        """
        super().__init__(timeout_seconds)
        self.cache_service = CacheService()

    async def check(self) -> HealthCheckResult:
        """
        Check Redis connectivity and response time.

        Returns:
            HealthCheckResult with Redis status
        """
        start_time = time.time()
        component_name = "redis"

        try:
            # Use cache service health check
            health = self.cache_service.health_check()

            response_time_ms = (time.time() - start_time) * 1000

            if health.get("status") == "healthy":
                logger.debug(f"Redis health check passed: {response_time_ms:.2f}ms")
                return HealthCheckResult(
                    component_name=component_name,
                    status=HealthCheckResult.STATUS_HEALTHY,
                    response_time_ms=response_time_ms,
                    message="Redis is operational",
                    details={
                        "connected": health.get("connected", False),
                        "key_count": health.get("key_count", 0),
                        "memory_used": health.get("memory_used", 0),
                    },
                )
            else:
                error_msg = health.get("error", "Unknown error")
                logger.warning(f"Redis health check failed: {error_msg}")
                return HealthCheckResult(
                    component_name=component_name,
                    status=HealthCheckResult.STATUS_UNHEALTHY,
                    response_time_ms=response_time_ms,
                    message=f"Redis is not operational",
                    error=error_msg,
                    details={"enabled": health.get("enabled", False)},
                )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Redis health check failed: {e}")
            return HealthCheckResult(
                component_name=component_name,
                status=HealthCheckResult.STATUS_UNHEALTHY,
                response_time_ms=response_time_ms,
                message="Redis is unreachable",
                error=str(e),
            )


class CeleryHealthChecker(BaseHealthChecker):
    """
    Health checker for Celery worker availability.

    Uses the existing health_check_task pattern to verify workers can
    receive and process tasks.
    """

    def __init__(self, timeout_seconds: Optional[int] = None) -> None:
        """
        Initialize the Celery health checker.

        Args:
            timeout_seconds: Maximum time to wait for health check
        """
        super().__init__(timeout_seconds)

    async def check(self) -> HealthCheckResult:
        """
        Check Celery worker availability by executing health_check_task.

        This method actually sends a health_check_task to Celery and waits
        for a worker to process it, providing an end-to-end test of worker
        functionality.

        Returns:
            HealthCheckResult with Celery status
        """
        start_time = time.time()
        component_name = "celery"

        try:
            from celery_app import celery_app, health_check_task

            # Import the health_check_task to execute it
            config = celery_app.conf
            broker_url = config.get("broker_url", "")

            if not broker_url:
                return HealthCheckResult(
                    component_name=component_name,
                    status=HealthCheckResult.STATUS_UNHEALTHY,
                    response_time_ms=0,
                    message="Celery broker URL not configured",
                    error="configuration",
                )

            # Execute health_check_task and wait for result
            # Use apply_async with a short timeout to get synchronous result
            try:
                result = health_check_task.apply_async(
                    timeout=self.timeout_seconds,
                    retry=False,
                )

                # Wait for the task to complete with timeout
                # Use get() with timeout to block until result is ready
                task_result = result.get(timeout=self.timeout_seconds)

                response_time_ms = (time.time() - start_time) * 1000

                # Check if the health check task returned successfully
                if task_result and task_result.get("status") == "healthy":
                    worker_name = task_result.get("worker", "unknown")
                    logger.debug(f"Celery health check passed: worker {worker_name}")
                    return HealthCheckResult(
                        component_name=component_name,
                        status=HealthCheckResult.STATUS_HEALTHY,
                        response_time_ms=response_time_ms,
                        message=f"Celery worker is operational ({worker_name})",
                        details={
                            "worker": worker_name,
                            "task_id": task_result.get("task_id"),
                        },
                    )
                else:
                    logger.warning("Celery health check task returned unexpected result")
                    return HealthCheckResult(
                        component_name=component_name,
                        status=HealthCheckResult.STATUS_DEGRADED,
                        response_time_ms=response_time_ms,
                        message="Celery worker responded with unexpected status",
                        details={"task_result": task_result},
                    )

            except Exception as task_error:
                response_time_ms = (time.time() - start_time) * 1000

                # Check if it's a timeout error
                error_str = str(task_error).lower()
                if "timeout" in error_str:
                    logger.warning("Celery health check timed out waiting for worker")
                    return HealthCheckResult(
                        component_name=component_name,
                        status=HealthCheckResult.STATUS_UNHEALTHY,
                        response_time_ms=response_time_ms,
                        message="No Celery workers available (timed out)",
                        error="worker_timeout",
                        details={"timeout_seconds": self.timeout_seconds},
                    )

                # Check if workers are connected but task failed
                logger.error(f"Celery health check task failed: {task_error}")
                return HealthCheckResult(
                    component_name=component_name,
                    status=HealthCheckResult.STATUS_UNHEALTHY,
                    response_time_ms=response_time_ms,
                    message="Celery worker task failed",
                    error=str(task_error),
                )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Celery health check failed: {e}")
            return HealthCheckResult(
                component_name=component_name,
                status=HealthCheckResult.STATUS_UNHEALTHY,
                response_time_ms=response_time_ms,
                message="Celery health check failed",
                error=str(e),
            )


class MLModelHealthChecker(BaseHealthChecker):
    """
    Health checker for ML model availability.

    Checks if critical ML models are loaded and available.
    """

    async def check(self) -> HealthCheckResult:
        """
        Check ML model availability.

        Returns:
            HealthCheckResult with ML model status
        """
        start_time = time.time()
        component_name = "ml_models"

        try:
            # Check if model modules can be imported
            models_status = {}
            models_loaded = []
            models_missing = []

            # Check NER models
            try:
                from backend.analyzers.hf_skill_extractor import _ner_pipeline

                if _ner_pipeline is not None:
                    models_status["ner_pipeline"] = True
                    models_loaded.append("NER pipeline")
                else:
                    models_status["ner_pipeline"] = False
                    models_missing.append("NER pipeline")
            except Exception as e:
                models_status["ner_pipeline"] = False
                models_missing.append(f"NER pipeline: {str(e)}")

            # Check zero-shot model
            try:
                from backend.analyzers.hf_skill_extractor import _zero_shot_pipeline

                if _zero_shot_pipeline is not None:
                    models_status["zero_shot"] = True
                    models_loaded.append("Zero-shot classifier")
                else:
                    models_status["zero_shot"] = False
                    models_missing.append("Zero-shot classifier")
            except Exception as e:
                models_status["zero_shot"] = False
                models_missing.append(f"Zero-shot classifier: {str(e)}")

            # Check LanguageTool
            try:
                from backend.analyzers.grammar_checker import _language_tools

                language_tools_loaded = any(
                    tool is not None for tool in _language_tools.values()
                )
                if language_tools_loaded:
                    models_status["language_tool"] = True
                    models_loaded.append("LanguageTool")
                else:
                    models_status["language_tool"] = False
                    models_missing.append("LanguageTool")
            except Exception as e:
                models_status["language_tool"] = False
                models_missing.append(f"LanguageTool: {str(e)}")

            response_time_ms = (time.time() - start_time) * 1000

            # Determine overall status
            all_loaded = len(models_loaded) == 3
            some_loaded = len(models_loaded) > 0

            if all_loaded:
                logger.debug(f"ML model health check passed: all {len(models_loaded)} models loaded")
                return HealthCheckResult(
                    component_name=component_name,
                    status=HealthCheckResult.STATUS_HEALTHY,
                    response_time_ms=response_time_ms,
                    message=f"All ML models loaded ({len(models_loaded)}/{len(models_status)})",
                    details={
                        "models_loaded": models_loaded,
                        "models_status": models_status,
                        "total_models": len(models_status),
                    },
                )
            elif some_loaded:
                logger.warning(
                    f"ML model health check degraded: {len(models_loaded)}/{len(models_status)} models loaded"
                )
                return HealthCheckResult(
                    component_name=component_name,
                    status=HealthCheckResult.STATUS_DEGRADED,
                    response_time_ms=response_time_ms,
                    message=f"Some ML models not loaded ({len(models_loaded)}/{len(models_status)})",
                    details={
                        "models_loaded": models_loaded,
                        "models_missing": models_missing,
                        "models_status": models_status,
                        "total_models": len(models_status),
                    },
                )
            else:
                logger.error("ML model health check failed: no models loaded")
                return HealthCheckResult(
                    component_name=component_name,
                    status=HealthCheckResult.STATUS_DEGRADED,
                    response_time_ms=response_time_ms,
                    message="ML models not loaded (will load on first use)",
                    details={
                        "models_missing": models_missing,
                        "models_status": models_status,
                        "note": "Models will be loaded lazily on first use",
                    },
                )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"ML model health check failed: {e}")
            return HealthCheckResult(
                component_name=component_name,
                status=HealthCheckResult.STATUS_DEGRADED,
                response_time_ms=response_time_ms,
                message="ML model check failed (models may load on first use)",
                error=str(e),
                details={"note": "Models will be loaded lazily on first use"},
            )


class ExternalAPIHealthChecker(BaseHealthChecker):
    """
    Health checker for external API availability.

    Checks external services like LanguageTool API.
    """

    async def check(self) -> HealthCheckResult:
        """
        Check external API availability.

        Returns:
            HealthCheckResult with external API status
        """
        start_time = time.time()
        component_name = "external_apis"

        try:
            settings = get_settings()
            apis_checked = []
            apis_available = []
            apis_unavailable = []

            # Check LanguageTool server if configured
            languagetool_server = getattr(settings, "languagetool_server", None)
            if languagetool_server:
                apis_checked.append("LanguageTool")
                try:
                    import aiohttp

                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            f"{languagetool_server}/v2/check",
                            params={"text": "test", "language": "en-US"},
                            timeout=aiohttp.ClientTimeout(total=5),
                        ) as response:
                            if response.status == 200:
                                apis_available.append("LanguageTool")
                            else:
                                apis_unavailable.append(
                                    f"LanguageTool (status {response.status})"
                                )
                except Exception as e:
                    apis_unavailable.append(f"LanguageTool: {str(e)}")
            else:
                apis_checked.append("LanguageTool (not configured)")

            response_time_ms = (time.time() - start_time) * 1000

            if not apis_checked:
                return HealthCheckResult(
                    component_name=component_name,
                    status=HealthCheckResult.STATUS_HEALTHY,
                    response_time_ms=response_time_ms,
                    message="No external APIs configured",
                    details={"apis_checked": apis_checked},
                )

            if apis_available and not apis_unavailable:
                logger.debug(f"External API health check passed: {apis_available}")
                return HealthCheckResult(
                    component_name=component_name,
                    status=HealthCheckResult.STATUS_HEALTHY,
                    response_time_ms=response_time_ms,
                    message=f"All external APIs available ({len(apis_available)})",
                    details={
                        "apis_checked": apis_checked,
                        "apis_available": apis_available,
                    },
                )
            elif apis_available:
                logger.warning(
                    f"External API health check degraded: {apis_unavailable}"
                )
                return HealthCheckResult(
                    component_name=component_name,
                    status=HealthCheckResult.STATUS_DEGRADED,
                    response_time_ms=response_time_ms,
                    message=f"Some external APIs unavailable ({len(apis_available)}/{len(apis_checked)})",
                    details={
                        "apis_checked": apis_checked,
                        "apis_available": apis_available,
                        "apis_unavailable": apis_unavailable,
                    },
                )
            else:
                logger.warning("All external APIs unavailable")
                return HealthCheckResult(
                    component_name=component_name,
                    status=HealthCheckResult.STATUS_DEGRADED,
                    response_time_ms=response_time_ms,
                    message="External APIs unavailable (non-critical)",
                    details={
                        "apis_checked": apis_checked,
                        "apis_unavailable": apis_unavailable,
                        "note": "External APIs are non-critical for core functionality",
                    },
                )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"External API health check failed: {e}")
            return HealthCheckResult(
                component_name=component_name,
                status=HealthCheckResult.STATUS_DEGRADED,
                response_time_ms=response_time_ms,
                message="External API check failed (non-critical)",
                error=str(e),
                details={"note": "External APIs are non-critical for core functionality"},
            )


class HealthCheckService:
    """
    Main health check service that aggregates all component health checks.

    This class provides a unified interface for checking the health of all
    system components and generating overall system health status.

    Attributes:
        checkers: Dictionary of registered health checkers

    Example:
        >>> service = HealthCheckService()
        >>> result = await service.check_all()
        >>> print(result['overall_status'])
        'healthy'
    """

    # Essential components that must be healthy for system to be operational
    ESSENTIAL_COMPONENTS = {"database", "redis", "celery"}

    # Optional components that can be unavailable without breaking core functionality
    OPTIONAL_COMPONENTS = {"ml_models", "external_apis"}

    def __init__(self, checkers: Optional[Dict[str, BaseHealthChecker]] = None) -> None:
        """
        Initialize the health check service.

        Args:
            checkers: Custom dictionary of health checkers (defaults to all built-in checkers)
        """
        if checkers is None:
            self.checkers = {
                "database": DatabaseHealthChecker(),
                "redis": RedisHealthChecker(),
                "celery": CeleryHealthChecker(),
                "ml_models": MLModelHealthChecker(),
                "external_apis": ExternalAPIHealthChecker(),
            }
        else:
            self.checkers = checkers

        logger.info(
            f"HealthCheckService initialized with {len(self.checkers)} checkers: "
            f"{list(self.checkers.keys())}"
        )

    async def check_component(self, component_name: str) -> HealthCheckResult:
        """
        Check health of a specific component.

        Args:
            component_name: Name of the component to check

        Returns:
            HealthCheckResult for the component

        Raises:
            ValueError: If component_name is not a registered checker

        Example:
            >>> service = HealthCheckService()
            >>> result = await service.check_component("database")
            >>> print(result.status)
            'healthy'
        """
        if component_name not in self.checkers:
            raise ValueError(
                f"Unknown component: {component_name}. "
                f"Available components: {list(self.checkers.keys())}"
            )

        checker = self.checkers[component_name]
        return await checker.check_with_timeout()

    async def check_all(self) -> Dict[str, Any]:
        """
        Check health of all registered components.

        Returns:
            Dictionary containing overall health status and component results

        Example:
            >>> service = HealthCheckService()
            >>> result = await service.check_all()
            >>> print(result['overall_status'])
            'healthy'
        """
        start_time = time.time()
        logger.info("Starting comprehensive health check...")

        # Run all health checks concurrently
        check_tasks = {
            name: checker.check_with_timeout()
            for name, checker in self.checkers.items()
        }

        # Wait for all checks to complete
        results_dict = await asyncio.gather(
            *check_tasks.values(), return_exceptions=True
        )

        # Map results back to component names
        results = {}
        for name, result in zip(check_tasks.keys(), results_dict):
            if isinstance(result, Exception):
                logger.error(f"Health check for {name} raised exception: {result}")
                results[name] = HealthCheckResult(
                    component_name=name,
                    status=HealthCheckResult.STATUS_UNHEALTHY,
                    response_time_ms=0,
                    message="Health check failed with exception",
                    error=str(result),
                )
            else:
                results[name] = result

        # Calculate overall status
        total_time_ms = (time.time() - start_time) * 1000

        # Check essential components
        essential_results = {
            name: result
            for name, result in results.items()
            if name in self.ESSENTIAL_COMPONENTS
        }
        essential_healthy = all(
            result.is_healthy() for result in essential_results.values()
        )
        essential_operational = all(
            result.is_operational() for result in essential_results.values()
        )

        # Determine overall status
        if essential_healthy:
            overall_status = HealthCheckResult.STATUS_HEALTHY
        elif essential_operational:
            overall_status = HealthCheckResult.STATUS_DEGRADED
        else:
            overall_status = HealthCheckResult.STATUS_UNHEALTHY

        # Build summary
        summary = {
            "overall_status": overall_status,
            "total_time_ms": round(total_time_ms, 2),
            "components_checked": len(results),
            "components_healthy": sum(
                1 for r in results.values() if r.status == HealthCheckResult.STATUS_HEALTHY
            ),
            "components_degraded": sum(
                1 for r in results.values() if r.status == HealthCheckResult.STATUS_DEGRADED
            ),
            "components_unhealthy": sum(
                1 for r in results.values() if r.status == HealthCheckResult.STATUS_UNHEALTHY
            ),
        }

        # Convert results to dictionaries
        components_dict = {
            name: result.to_dict() for name, result in results.items()
        }

        logger.info(
            f"Health check completed: {overall_status} "
            f"({summary['components_healthy']}/{len(results)} healthy, "
            f"{total_time_ms:.2f}ms)"
        )

        return {
            "overall_status": overall_status,
            "summary": summary,
            "components": components_dict,
            "timestamp": time.time(),
        }

    async def check_essential_only(self) -> Dict[str, Any]:
        """
        Check health of essential components only.

        This is useful for readiness probes where we only need to verify
        critical services are available.

        Returns:
            Dictionary containing overall health status and component results

        Example:
            >>> service = HealthCheckService()
            >>> result = await service.check_essential_only()
            >>> print(result['overall_status'])
            'healthy'
        """
        # Filter to essential components
        essential_checkers = {
            name: checker
            for name, checker in self.checkers.items()
            if name in self.ESSENTIAL_COMPONENTS
        }

        # Create a temporary service with only essential checkers
        essential_service = HealthCheckService(checkers=essential_checkers)
        return await essential_service.check_all()

    def register_checker(
        self, name: str, checker: BaseHealthChecker
    ) -> None:
        """
        Register a custom health checker.

        Args:
            name: Name for the health checker
            checker: Health checker instance

        Example:
            >>> service = HealthCheckService()
            >>> service.register_checker("custom", CustomHealthChecker())
        """
        self.checkers[name] = checker
        logger.info(f"Registered custom health checker: {name}")

    def unregister_checker(self, name: str) -> None:
        """
        Unregister a health checker.

        Args:
            name: Name of the checker to unregister

        Example:
            >>> service = HealthCheckService()
            >>> service.unregister_checker("external_apis")
        """
        if name in self.checkers:
            del self.checkers[name]
            logger.info(f"Unregistered health checker: {name}")


def get_health_check_service() -> HealthCheckService:
    """
    Get or create global health check service instance.

    Returns:
        Global HealthCheckService instance

    Example:
        >>> service = get_health_check_service()
        >>> result = await service.check_all()
    """
    global _health_check_service
    if _health_check_service is None:
        _health_check_service = HealthCheckService()
    return _health_check_service


__all__ = [
    "HealthCheckService",
    "HealthCheckResult",
    "BaseHealthChecker",
    "DatabaseHealthChecker",
    "RedisHealthChecker",
    "CeleryHealthChecker",
    "MLModelHealthChecker",
    "ExternalAPIHealthChecker",
    "get_health_check_service",
]
