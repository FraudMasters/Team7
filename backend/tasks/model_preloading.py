"""
ML Model pre-loading tasks for worker startup optimization.

This module provides tasks for pre-loading ML models into memory when the
Celery worker starts up. This reduces first-request latency by ensuring
models are already loaded before processing actual analysis tasks.
"""
import logging
from typing import Dict, Any, List

from celery import shared_task
from celery.signals import worker_ready

logger = logging.getLogger(__name__)


@shared_task(
    name="tasks.model_preloading.preload_ml_models",
    bind=True,
    max_retries=0,
)
def preload_ml_models(self) -> Dict[str, Any]:
    """
    Preload ML models into memory to reduce first-request latency.

    This task loads all commonly used ML models:
    - Hugging Face NER models for skill extraction (English and Russian)
    - Hugging Face zero-shot classification model
    - LanguageTool instances for grammar checking (English and Russian)

    The task is automatically executed when the Celery worker starts up
    via the worker_ready signal handler.

    Args:
        self: Celery task instance (bind=True)

    Returns:
        Dictionary containing preload status information:
        - status: Overall status of preloading
        - models_loaded: List of successfully loaded models
        - models_failed: List of models that failed to load
        - total_load_time_ms: Total time taken to load all models

    Example:
        >>> from tasks import preload_ml_models
        >>> result = preload_ml_models.delay()
        >>> print(result.get())
        {'status': 'completed', 'models_loaded': [...], 'total_load_time_ms': 1234}
    """
    import time
    from backend.analyzers.hf_skill_extractor import (
        _get_ner_model,
        _get_zero_shot_model,
    )
    from backend.analyzers.grammar_checker import _get_tool

    start_time = time.time()
    models_loaded = []
    models_failed = []

    logger.info("Starting ML model preloading...")

    # Preload NER models for skill extraction
    ner_models = [
        {
            "name": "NER English",
            "language": "en",
            "model": "dbmdz/bert-large-cased-finetuned-conll03-english",
        },
        {
            "name": "NER Russian",
            "language": "ru",
            "model": "distilbert-base-uncased",
        },
    ]

    for model_config in ner_models:
        try:
            logger.info(f"Loading {model_config['name']} model...")
            _get_ner_model(
                model_name=model_config["model"],
                language=model_config["language"],
            )
            models_loaded.append(model_config["name"])
            logger.info(f"{model_config['name']} model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load {model_config['name']}: {e}")
            models_failed.append(f"{model_config['name']}: {str(e)}")

    # Preload zero-shot classification model
    try:
        logger.info("Loading zero-shot classification model...")
        _get_zero_shot_model(model_name="facebook/bart-large-mnli")
        models_loaded.append("Zero-shot classification")
        logger.info("Zero-shot classification model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load zero-shot classification model: {e}")
        models_failed.append(f"Zero-shot classification: {str(e)}")

    # Preload LanguageTool for grammar checking
    language_tool_configs = [
        {"name": "LanguageTool en-US", "language": "en-US"},
        {"name": "LanguageTool en-GB", "language": "en-GB"},
        {"name": "LanguageTool ru-RU", "language": "ru-RU"},
    ]

    for config in language_tool_configs:
        try:
            logger.info(f"Loading {config['name']}...")
            _get_tool(language=config["language"].split("-")[0])
            models_loaded.append(config["name"])
            logger.info(f"{config['name']} loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load {config['name']}: {e}")
            models_failed.append(f"{config['name']}: {str(e)}")

    total_load_time_ms = round((time.time() - start_time) * 1000, 2)

    result = {
        "status": "completed" if not models_failed else "partial",
        "models_loaded": models_loaded,
        "models_failed": models_failed,
        "total_load_time_ms": total_load_time_ms,
        "total_models": len(models_loaded) + len(models_failed),
        "successful": len(models_loaded),
        "failed": len(models_failed),
    }

    if models_failed:
        logger.warning(
            f"Model preloading completed with {len(models_failed)} failures: "
            f"{models_failed}"
        )
    else:
        logger.info(
            f"Model preloading completed successfully. "
            f"Loaded {len(models_loaded)} models in {total_load_time_ms}ms"
        )

    return result


@shared_task(
    name="tasks.model_preloading.health_check_with_models",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def health_check_with_models(self) -> Dict[str, Any]:
    """
    Health check task that verifies ML models are loaded.

    This task checks if the critical ML models are loaded and ready.
    Useful for monitoring and ensuring the worker is fully operational.

    Args:
        self: Celery task instance (bind=True)

    Returns:
        Dictionary containing health status with model information

    Example:
        >>> from tasks import health_check_with_models
        >>> result = health_check_with_models.delay()
        >>> print(result.get())
        {'status': 'healthy', 'models_loaded': true, ...}
    """
    logger.info("Health check with model verification executed")

    # Check if models are loaded by attempting to access them
    models_status = {}
    try:
        from backend.analyzers.hf_skill_extractor import (
            _ner_pipeline,
            _zero_shot_pipeline,
        )
        from backend.analyzers.grammar_checker import _language_tools

        models_status["ner_loaded"] = _ner_pipeline is not None
        models_status["zero_shot_loaded"] = _zero_shot_pipeline is not None
        models_status["language_tools_loaded"] = any(
            tool is not None for tool in _language_tools.values()
        )

        all_models_loaded = all(models_status.values())

        return {
            "status": "healthy" if all_models_loaded else "degraded",
            "worker": self.request.hostname,
            "task_id": self.request.id,
            "models_status": models_status,
            "message": (
                "All models loaded and ready"
                if all_models_loaded
                else "Some models not loaded - may experience higher latency"
            ),
        }
    except Exception as e:
        logger.error(f"Error checking model status: {e}")
        return {
            "status": "unhealthy",
            "worker": self.request.hostname,
            "task_id": self.request.id,
            "error": str(e),
            "message": "Failed to verify model status",
        }


@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    """
    Signal handler for worker_ready event.

    This function is automatically called when the Celery worker is ready
    to start processing tasks. It triggers the model preloading task to
    ensure models are loaded before any actual work is processed.

    Args:
        sender: The sender of the signal (Celery worker instance)
        **kwargs: Additional keyword arguments from the signal
    """
    logger.info("Worker ready - triggering ML model preloading")
    try:
        # Import preload_ml_models to ensure it's available
        from backend.tasks.model_preloading import preload_ml_models

        # Execute the preload task synchronously on worker startup
        result = preload_ml_models()

        logger.info(
            f"ML model preloading completed on worker startup: "
            f"{result['successful']}/{result['total_models']} models loaded"
        )
    except Exception as e:
        logger.error(f"Failed to preload ML models on worker startup: {e}")
        # Don't raise - allow worker to start even if preloading fails
        # The models will be loaded lazily on first use


# Export tasks for use by celery_app.py
__all__ = [
    "preload_ml_models",
    "health_check_with_models",
    "on_worker_ready",
]
