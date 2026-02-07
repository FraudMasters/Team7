"""
Health Check Utilities Module

This module provides health check functions for monitoring the status of
various system components including database connectivity, Redis availability,
ML model loading, and external service dependencies.

Health checks return structured status information that can be consumed by
API endpoints, monitoring systems, and alerting services.

Functions:
    check_database: Verify database connectivity and query execution
    check_redis: Verify Redis availability (added in subtask-1-2)
    check_celery_workers: Verify Celery worker status (added in phase-2)
    check_ml_models: Verify ML model availability (added in phase-2)
    check_languagetool: Verify LanguageTool service (added in phase-3)
    check_s3: Verify S3 backup service (added in phase-3)

Example:
    >>> from utils.health_checks import check_database
    >>> result = await check_database()
    >>> print(result['status'])
    'healthy'
"""
import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

import redis.asyncio as redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from celery import Celery
from celery.exceptions import TimeoutError as CeleryTimeoutError
from botocore.exceptions import ClientError, BotoCoreError
from config import get_settings
from database import engine
from utils.metrics import get_metrics_registry

logger = logging.getLogger(__name__)


async def check_database() -> Dict[str, Any]:
    """
    Check database connectivity and query execution.

    Verifies that the database is accessible and can execute queries.
    Measures connection latency and reports connection pool status.

    Returns:
        Dictionary containing:
        - status (str): 'healthy', 'degraded', or 'unhealthy'
        - latency_seconds (float): Query execution time
        - pool_size (int): Total connection pool size
        - pool_checked_out (int): Number of checked out connections
        - pool_overflow (int): Number of overflow connections
        - error (Optional[str]): Error message if check failed

    Example:
        >>> result = await check_database()
        >>> if result['status'] == 'healthy':
        ...     print(f"Database latency: {result['latency_seconds']:.3f}s")
    """
    result = {
        'status': 'unhealthy',
        'latency_seconds': 0.0,
        'pool_size': 0,
        'pool_checked_out': 0,
        'pool_overflow': 0,
        'error': None,
    }

    start_time = time.time()

    try:
        # Test database connection with a simple query
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

        # Calculate latency
        latency = time.time() - start_time
        result['latency_seconds'] = round(latency, 3)

        # Get connection pool status
        pool = engine.pool
        result['pool_size'] = pool.size()
        result['pool_checked_out'] = pool.checkedout()
        result['pool_overflow'] = pool.max_overflow - pool.overflow() if pool.max_overflow else 0

        # Determine health status based on latency
        if latency < 1.0:
            result['status'] = 'healthy'
        elif latency < 3.0:
            result['status'] = 'degraded'
        else:
            result['status'] = 'unhealthy'

        logger.info(
            f"Database health check: {result['status']} "
            f"(latency: {latency:.3f}s, pool: {result['pool_size']})"
        )

        # Record health check metric
        try:
            metrics_registry = get_metrics_registry()
            # Health check status: 1=healthy, 0=unhealthy
            health_status = 1 if result['status'] == 'healthy' else 0
            # Note: This metric will be added in subtask-1-5
            # For now, we log it
            logger.debug(f"Database health status for metrics: {health_status}")
        except Exception as e:
            logger.warning(f"Failed to record health check metric: {e}")

    except Exception as e:
        result['status'] = 'unhealthy'
        result['error'] = str(e)
        result['latency_seconds'] = round(time.time() - start_time, 3)

        logger.error(
            f"Database health check failed: {e}",
            exc_info=True
        )

    return result


async def check_redis() -> Dict[str, Any]:
    """
    Check Redis availability and connection performance.

    Verifies that Redis is accessible and responsive.
    Measures connection latency and reports connection status.

    Returns:
        Dictionary containing:
        - status (str): 'healthy', 'degraded', or 'unhealthy'
        - latency_seconds (float): Connection and ping time
        - connected (bool): Whether Redis connection succeeded
        - memory_used (int): Redis memory usage in bytes
        - key_count (int): Number of keys in database
        - error (Optional[str]): Error message if check failed

    Example:
        >>> result = await check_redis()
        >>> if result['status'] == 'healthy':
        ...     print(f"Redis latency: {result['latency_seconds']:.3f}s")
    """
    result = {
        'status': 'unhealthy',
        'latency_seconds': 0.0,
        'connected': False,
        'memory_used': 0,
        'key_count': 0,
        'error': None,
    }

    start_time = time.time()

    try:
        # Get Redis configuration
        settings = get_settings()
        redis_url = settings.redis_url

        # Create Redis connection
        redis_client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

        # Test connection with PING
        await redis_client.ping()
        result['connected'] = True

        # Calculate latency
        latency = time.time() - start_time
        result['latency_seconds'] = round(latency, 3)

        # Get Redis info
        info = await redis_client.info("memory")
        result['memory_used'] = info.get('used_memory', 0)

        # Get database size (key count)
        db_size = await redis_client.dbsize()
        result['key_count'] = db_size

        # Determine health status based on latency
        if latency < 0.1:
            result['status'] = 'healthy'
        elif latency < 0.5:
            result['status'] = 'degraded'
        else:
            result['status'] = 'unhealthy'

        logger.info(
            f"Redis health check: {result['status']} "
            f"(latency: {latency:.3f}s, keys: {db_size})"
        )

        # Close connection
        await redis_client.close()

        # Record health check metric
        try:
            metrics_registry = get_metrics_registry()
            # Health check status: 1=healthy, 0=unhealthy
            health_status = 1 if result['status'] == 'healthy' else 0
            # Note: This metric will be added in subtask-1-5
            # For now, we log it
            logger.debug(f"Redis health status for metrics: {health_status}")
        except Exception as e:
            logger.warning(f"Failed to record health check metric: {e}")

    except RedisError as e:
        result['status'] = 'unhealthy'
        result['error'] = str(e)
        result['latency_seconds'] = round(time.time() - start_time, 3)

        logger.error(
            f"Redis health check failed: {e}",
            exc_info=True
        )
    except Exception as e:
        result['status'] = 'unhealthy'
        result['error'] = str(e)
        result['latency_seconds'] = round(time.time() - start_time, 3)

        logger.error(
            f"Redis health check failed: {e}",
            exc_info=True
        )

    return result


async def check_celery_workers() -> Dict[str, Any]:
    """
    Check Celery worker status and availability.

    Verifies that Celery workers are online and capable of processing tasks.
    Reports worker statistics, queue lengths, and task execution metrics.

    This check uses Celery's inspect API to query worker status in real-time.
    It can detect workers that are offline, busy, or have long queues.

    Returns:
        Dictionary containing:
        - status (str): 'healthy', 'degraded', or 'unhealthy'
        - latency_seconds (float): Time to query workers
        - workers_online (int): Number of active workers
        - total_workers (int): Expected number of workers
        - worker_details (List[Dict]): Details for each worker
        - queue_length (int): Total length of all monitored queues
        - error (Optional[str]): Error message if check failed

    Example:
        >>> result = await check_celery_workers()
        >>> if result['status'] == 'healthy':
        ...     print(f"Workers online: {result['workers_online']}")
    """
    result = {
        'status': 'unhealthy',
        'latency_seconds': 0.0,
        'workers_online': 0,
        'total_workers': 0,
        'worker_details': [],
        'queue_length': 0,
        'error': None,
    }

    start_time = time.time()

    try:
        # Import Celery app - must be done here to avoid import errors
        # when Celery dependencies are not available
        from celery_app import celery_app

        # Create inspector for querying workers
        inspect = celery_app.control.inspect(timeout=5.0)

        # Query active workers
        active_workers = inspect.active()
        stats = inspect.stats()
        registered_tasks = inspect.registered()

        # Calculate latency
        latency = time.time() - start_time
        result['latency_seconds'] = round(latency, 3)

        # Process worker information
        if active_workers is not None:
            workers = list(active_workers.keys())
            result['workers_online'] = len(workers)
            result['total_workers'] = len(workers)

            # Build worker details
            worker_details = []
            total_queue_length = 0

            for worker_name in workers:
                worker_info = {
                    'name': worker_name,
                    'active_tasks': len(active_workers.get(worker_name, [])),
                    'status': 'online'
                }

                # Add stats if available
                if stats and worker_name in stats:
                    worker_stats = stats[worker_name]
                    worker_info['pool'] = worker_stats.get('pool', {})
                    worker_info['broker'] = worker_stats.get('broker', {})

                    # Calculate queue length from worker stats
                    # This is an approximation based on pending tasks
                    if 'rusage' in worker_stats:
                        worker_info['total_tasks'] = worker_stats.get('total', {})

                # Add registered tasks count
                if registered_tasks and worker_name in registered_tasks:
                    worker_info['registered_tasks'] = len(registered_tasks[worker_name])

                worker_details.append(worker_info)

            # Estimate queue length from active tasks
            # Note: This is a simplified check. For production, you'd want
            # to query Redis directly for accurate queue lengths
            for worker_tasks in active_workers.values():
                total_queue_length += len(worker_tasks)

            result['queue_length'] = total_queue_length
            result['worker_details'] = worker_details

            # Determine health status
            # Healthy: At least 1 worker online and low queue
            # Degraded: Workers online but high queue or only 1 worker
            # Unhealthy: No workers online
            if result['workers_online'] == 0:
                result['status'] = 'unhealthy'
                result['error'] = 'No Celery workers are online'
            elif result['queue_length'] > 100:
                result['status'] = 'degraded'
                result['error'] = f'High queue length: {result["queue_length"]} tasks'
            elif result['workers_online'] < 2:
                result['status'] = 'degraded'
                result['error'] = f'Low worker count: {result["workers_online"]} (recommended: 2+)'
            else:
                result['status'] = 'healthy'

            logger.info(
                f"Celery health check: {result['status']} "
                f"(workers: {result['workers_online']}, "
                f"queue: {result['queue_length']}, "
                f"latency: {latency:.3f}s)"
            )

        else:
            # No workers found
            result['workers_online'] = 0
            result['total_workers'] = 0
            result['status'] = 'unhealthy'
            result['error'] = 'No Celery workers are responding'
            result['latency_seconds'] = round(time.time() - start_time, 3)

            logger.warning("Celery health check: No workers responding")

        # Record health check metric
        try:
            metrics_registry = get_metrics_registry()
            # Health check status: 1=healthy, 0=unhealthy
            health_status = 1 if result['status'] == 'healthy' else 0
            logger.debug(f"Celery workers health status for metrics: {health_status}")
        except Exception as e:
            logger.warning(f"Failed to record health check metric: {e}")

    except CeleryTimeoutError as e:
        result['status'] = 'unhealthy'
        result['error'] = f'Celery inspect timeout: {str(e)}'
        result['latency_seconds'] = round(time.time() - start_time, 3)

        logger.error(
            f"Celery health check timed out: {e}",
            exc_info=True
        )
    except ImportError as e:
        result['status'] = 'unhealthy'
        result['error'] = f'Celery not available: {str(e)}'
        result['latency_seconds'] = round(time.time() - start_time, 3)

        logger.error(
            f"Celery health check failed (import error): {e}",
            exc_info=True
        )
    except Exception as e:
        result['status'] = 'unhealthy'
        result['error'] = str(e)
        result['latency_seconds'] = round(time.time() - start_time, 3)

        logger.error(
            f"Celery health check failed: {e}",
            exc_info=True
        )

    return result


async def check_ml_models() -> Dict[str, Any]:
    """
    Check ML model availability and loading status.

    Verifies that critical ML models are loaded and ready for use.
    Checks NER models, zero-shot classification, and LanguageTool instances.

    Returns:
        Dictionary containing:
        - status (str): 'healthy', 'degraded', or 'unhealthy'
        - models_loaded (List[str]): List of successfully loaded model names
        - models_failed (List[str]): List of model names that failed to load
        - total_models (int): Total number of models checked
        - successful_count (int): Number of successfully loaded models
        - failed_count (int): Number of failed models
        - details (Dict[str, bool]): Detailed status of each model type
        - error (Optional[str]): Error message if check failed

    Example:
        >>> result = await check_ml_models()
        >>> if result['status'] == 'healthy':
        ...     print(f"Models loaded: {result['successful_count']}/{result['total_models']}")
    """
    result = {
        'status': 'unhealthy',
        'models_loaded': [],
        'models_failed': [],
        'total_models': 0,
        'successful_count': 0,
        'failed_count': 0,
        'details': {
            'ner_loaded': False,
            'zero_shot_loaded': False,
            'language_tools_loaded': False,
        },
        'error': None,
    }

    start_time = time.time()

    try:
        # Import model modules
        from backend.analyzers.hf_skill_extractor import (
            _ner_pipeline,
            _zero_shot_pipeline,
        )
        from backend.analyzers.grammar_checker import _language_tools

        # Check NER models
        if _ner_pipeline is not None:
            result['details']['ner_loaded'] = True
            result['models_loaded'].append('NER models')
        else:
            result['models_failed'].append('NER models')

        # Check zero-shot classification model
        if _zero_shot_pipeline is not None:
            result['details']['zero_shot_loaded'] = True
            result['models_loaded'].append('Zero-shot classification')
        else:
            result['models_failed'].append('Zero-shot classification')

        # Check LanguageTool instances
        # At least one LanguageTool instance should be loaded
        has_language_tools = any(
            tool is not None for tool in _language_tools.values()
        )
        if has_language_tools:
            result['details']['language_tools_loaded'] = True
            result['models_loaded'].append('LanguageTool')
        else:
            result['models_failed'].append('LanguageTool')

        # Calculate totals
        result['total_models'] = 3  # NER, zero-shot, LanguageTool
        result['successful_count'] = len(result['models_loaded'])
        result['failed_count'] = len(result['models_failed'])

        # Determine health status
        # Healthy: All models loaded
        # Degraded: At least NER and zero-shot loaded (core functionality)
        # Unhealthy: Critical models missing
        if result['successful_count'] == result['total_models']:
            result['status'] = 'healthy'
        elif result['details']['ner_loaded'] and result['details']['zero_shot_loaded']:
            result['status'] = 'degraded'
            result['error'] = (
                f'Some models not loaded: {result["models_failed"]}. '
                'Core functionality available.'
            )
        else:
            result['status'] = 'unhealthy'
            result['error'] = (
                f'Critical models not loaded: {result["models_failed"]}. '
                'ML functionality unavailable.'
            )

        latency = time.time() - start_time
        logger.info(
            f"ML models health check: {result['status']} "
            f"(loaded: {result['successful_count']}/{result['total_models']}, "
            f"latency: {latency:.3f}s)"
        )

        # Record health check metric
        try:
            metrics_registry = get_metrics_registry()
            # Health check status: 1=healthy, 0=unhealthy
            health_status = 1 if result['status'] == 'healthy' else 0
            logger.debug(f"ML models health status for metrics: {health_status}")
        except Exception as e:
            logger.warning(f"Failed to record health check metric: {e}")

    except ImportError as e:
        result['status'] = 'unhealthy'
        result['error'] = f'ML model modules not available: {str(e)}'

        logger.error(
            f"ML models health check failed (import error): {e}",
            exc_info=True
        )
    except Exception as e:
        result['status'] = 'unhealthy'
        result['error'] = str(e)

        logger.error(
            f"ML models health check failed: {e}",
            exc_info=True
        )

    return result


async def check_languagetool() -> Dict[str, Any]:
    """
    Check LanguageTool service availability and functionality.

    Verifies that LanguageTool is accessible and can perform grammar checks.
    Supports both local and remote LanguageTool server configurations.

    This check validates:
    - LanguageTool Python package availability
    - Tool initialization (local or remote server)
    - Basic grammar checking functionality

    Returns:
        Dictionary containing:
        - status (str): 'healthy', 'degraded', or 'unhealthy'
        - latency_seconds (float): Time to initialize and test
        - server_type (str): 'local' or 'remote' based on configuration
        - server_url (Optional[str]): Remote server URL if configured
        - test_passed (bool): Whether test grammar check succeeded
        - error (Optional[str]): Error message if check failed

    Example:
        >>> result = await check_languagetool()
        >>> if result['status'] == 'healthy':
        ...     print(f"LanguageTool {result['server_type']} operational")
    """
    result = {
        'status': 'unhealthy',
        'latency_seconds': 0.0,
        'server_type': 'local',
        'server_url': None,
        'test_passed': False,
        'error': None,
    }

    start_time = time.time()

    try:
        # Get configuration
        settings = get_settings()
        server_url = settings.languagetool_server

        if server_url:
            result['server_type'] = 'remote'
            result['server_url'] = server_url

        # Try to import and initialize LanguageTool
        try:
            from language_tool_python import LanguageTool

            logger.info(
                f"Initializing LanguageTool health check "
                f"(type: {result['server_type']})"
            )

            # Initialize LanguageTool with appropriate configuration
            # For remote servers, LanguageTool will use the remote URL
            if server_url:
                tool = LanguageTool(language='en-US', remoteServer=server_url)
            else:
                tool = LanguageTool(language='en-US')

            # Test with a simple grammar check
            test_text = "This are a test."
            matches = tool.check(test_text)

            # Verify the check found the expected error
            # "This are" should trigger a grammar error
            result['test_passed'] = len(matches) > 0

            if result['test_passed']:
                result['status'] = 'healthy'
                logger.info(
                    f"LanguageTool health check passed: "
                    f"found {len(matches)} error(s) in test text"
                )
            else:
                result['status'] = 'degraded'
                result['error'] = (
                    'LanguageTool initialized but did not detect expected '
                    'grammar errors in test'
                )
                logger.warning("LanguageTool health check: test did not detect errors")

            # Clean up
            del tool

        except ImportError as e:
            result['status'] = 'unhealthy'
            result['error'] = (
                'language-tool-python package not installed. '
                f'Install with: pip install language-tool-python. Details: {str(e)}'
            )
            logger.error(f"LanguageTool health check failed (import error): {e}")

        except Exception as e:
            result['status'] = 'unhealthy'
            result['error'] = f'LanguageTool initialization failed: {str(e)}'
            logger.error(
                f"LanguageTool health check failed (initialization): {e}",
                exc_info=True
            )

        # Calculate latency
        latency = time.time() - start_time
        result['latency_seconds'] = round(latency, 3)

        # Log final status
        logger.info(
            f"LanguageTool health check: {result['status']} "
            f"(type: {result['server_type']}, latency: {latency:.3f}s)"
        )

        # Record health check metric
        try:
            metrics_registry = get_metrics_registry()
            # Health check status: 1=healthy, 0=unhealthy
            health_status = 1 if result['status'] == 'healthy' else 0
            logger.debug(f"LanguageTool health status for metrics: {health_status}")
        except Exception as e:
            logger.warning(f"Failed to record health check metric: {e}")

    except Exception as e:
        result['status'] = 'unhealthy'
        result['error'] = f'Health check failed: {str(e)}'
        result['latency_seconds'] = round(time.time() - start_time, 3)

        logger.error(
            f"LanguageTool health check failed: {e}",
            exc_info=True
        )

    return result


async def check_s3() -> Dict[str, Any]:
    """
    Check S3 backup service availability and connectivity.

    Verifies that S3-compatible storage is accessible and properly configured
    for backup operations. Tests bucket access, permissions, and connectivity.

    This check validates:
    - S3 configuration (credentials, endpoint, bucket)
    - Network connectivity to S3 endpoint
    - Bucket existence and access permissions
    - Basic S3 operations (list/HeadBucket)

    Returns:
        Dictionary containing:
        - status (str): 'healthy', 'degraded', or 'unhealthy'
        - latency_seconds (float): Time to connect and verify
        - enabled (bool): Whether S3 backup is enabled in configuration
        - bucket_exists (bool): Whether the configured bucket exists
        - bucket_accessible (bool): Whether the bucket is accessible
        - bucket_name (Optional[str]): Name of the S3 bucket
        - endpoint (Optional[str]): S3 endpoint URL
        - error (Optional[str]): Error message if check failed

    Example:
        >>> result = await check_s3()
        >>> if result['status'] == 'healthy':
        ...     print(f"S3 bucket {result['bucket_name']} accessible")
    """
    result = {
        'status': 'unhealthy',
        'latency_seconds': 0.0,
        'enabled': False,
        'bucket_exists': False,
        'bucket_accessible': False,
        'bucket_name': None,
        'endpoint': None,
        'error': None,
    }

    start_time = time.time()

    try:
        # Get S3 configuration
        settings = get_settings()

        # Check if S3 backup is enabled
        result['enabled'] = settings.backup_s3_enabled
        result['bucket_name'] = settings.backup_s3_bucket
        result['endpoint'] = settings.backup_s3_endpoint

        if not settings.backup_s3_enabled:
            result['status'] = 'healthy'
            result['error'] = 'S3 backup is disabled in configuration'
            result['latency_seconds'] = round(time.time() - start_time, 3)

            logger.info("S3 health check: S3 backup disabled (skipped)")
            return result

        # Validate required S3 configuration
        if not all([
            settings.backup_s3_bucket,
            settings.backup_s3_endpoint,
            settings.backup_s3_access_key,
            settings.backup_s3_secret_key,
        ]):
            result['status'] = 'unhealthy'
            result['error'] = (
                'S3 backup enabled but configuration incomplete. '
                'Required: bucket, endpoint, access_key, secret_key'
            )
            result['latency_seconds'] = round(time.time() - start_time, 3)

            logger.warning(
                f"S3 health check failed: {result['error']}"
            )
            return result

        # Import boto3 here to avoid import errors when not needed
        import boto3

        # Create S3 client
        s3_client = boto3.client(
            's3',
            endpoint_url=settings.backup_s3_endpoint,
            aws_access_key_id=settings.backup_s3_access_key,
            aws_secret_access_key=settings.backup_s3_secret_key,
            region_name=settings.backup_s3_region,
        )

        # Test S3 connectivity with HeadBucket operation
        # This verifies both network connectivity and permissions
        try:
            s3_client.head_bucket(Bucket=settings.backup_s3_bucket)
            result['bucket_exists'] = True
            result['bucket_accessible'] = True

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')

            if error_code == '404':
                result['bucket_exists'] = False
                result['bucket_accessible'] = False
                result['error'] = (
                    f'S3 bucket "{settings.backup_s3_bucket}" does not exist'
                )
            elif error_code == '403':
                result['bucket_exists'] = True
                result['bucket_accessible'] = False
                result['error'] = (
                    f'Access denied to S3 bucket "{settings.backup_s3_bucket}". '
                    'Check credentials and permissions.'
                )
            else:
                result['bucket_exists'] = False
                result['bucket_accessible'] = False
                result['error'] = (
                    f'S3 access error: {error_code} - {str(e)}'
                )

            result['status'] = 'unhealthy'
            result['latency_seconds'] = round(time.time() - start_time, 3)

            logger.error(
                f"S3 health check failed: {result['error']}",
                exc_info=True
            )
            return result

        # Calculate latency
        latency = time.time() - start_time
        result['latency_seconds'] = round(latency, 3)

        # Determine health status based on latency
        # S3 operations can be slower than local services
        if latency < 2.0:
            result['status'] = 'healthy'
        elif latency < 5.0:
            result['status'] = 'degraded'
            result['error'] = f'S3 connectivity slow: {latency:.3f}s'
        else:
            result['status'] = 'unhealthy'
            result['error'] = f'S3 connectivity very slow: {latency:.3f}s'

        logger.info(
            f"S3 health check: {result['status']} "
            f"(bucket: {settings.backup_s3_bucket}, "
            f"latency: {latency:.3f}s)"
        )

        # Record health check metric
        try:
            metrics_registry = get_metrics_registry()
            # Health check status: 1=healthy, 0=unhealthy
            health_status = 1 if result['status'] == 'healthy' else 0
            logger.debug(f"S3 health status for metrics: {health_status}")
        except Exception as e:
            logger.warning(f"Failed to record health check metric: {e}")

    except ImportError as e:
        result['status'] = 'unhealthy'
        result['error'] = f'boto3 package not installed: {str(e)}'
        result['latency_seconds'] = round(time.time() - start_time, 3)

        logger.error(
            f"S3 health check failed (import error): {e}",
            exc_info=True
        )
    except BotoCoreError as e:
        result['status'] = 'unhealthy'
        result['error'] = f'S3 connection error: {str(e)}'
        result['latency_seconds'] = round(time.time() - start_time, 3)

        logger.error(
            f"S3 health check failed (connection error): {e}",
            exc_info=True
        )
    except Exception as e:
        result['status'] = 'unhealthy'
        result['error'] = str(e)
        result['latency_seconds'] = round(time.time() - start_time, 3)

        logger.error(
            f"S3 health check failed: {e}",
            exc_info=True
        )

    return result
