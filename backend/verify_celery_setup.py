"""
Verification script for Celery configuration.

This script verifies that the Celery application is properly configured
and can be imported without errors.
"""
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def verify_celery_import():
    """Verify that Celery app can be imported."""
    try:
        from tasks import celery_app, health_check_task, add_numbers_task, long_running_task
        logger.info("✅ Celery app imported successfully")
        logger.info(f"   App name: {celery_app.main}")
        logger.info(f"   Broker: {celery_app.conf.broker_url}")
        logger.info(f"   Backend: {celery_app.conf.result_backend}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to import Celery app: {e}")
        return False


def verify_celery_config():
    """Verify Celery configuration is valid."""
    try:
        from celery_config import get_celery_config
        config = get_celery_config()

        required_keys = [
            "broker_url",
            "result_backend",
            "task_serializer",
            "result_serializer",
            "accept_content",
            "timezone",
            "task_time_limit",
        ]

        missing_keys = [key for key in required_keys if key not in config]

        if missing_keys:
            logger.error(f"❌ Missing required config keys: {missing_keys}")
            return False

        logger.info("✅ Celery configuration is valid")
        logger.info(f"   Broker URL: {config['broker_url']}")
        logger.info(f"   Result backend: {config['result_backend']}")
        logger.info(f"   Task time limit: {config['task_time_limit']}s")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to verify Celery config: {e}")
        return False


def verify_task_definitions():
    """Verify that task definitions are correct."""
    try:
        from tasks import celery_app

        # Check that tasks are registered
        registered_tasks = list(celery_app.tasks.keys())

        expected_tasks = [
            "tasks.health_check",
            "tasks.add_numbers",
            "tasks.long_running_task",
        ]

        missing_tasks = [task for task in expected_tasks if task not in registered_tasks]

        if missing_tasks:
            logger.warning(f"⚠️  Expected tasks not registered: {missing_tasks}")
        else:
            logger.info("✅ All expected tasks are registered")
            for task in expected_tasks:
                logger.info(f"   - {task}")

        return len(missing_tasks) == 0
    except Exception as e:
        logger.error(f"❌ Failed to verify task definitions: {e}")
        return False


def verify_config_integration():
    """Verify integration with application config."""
    try:
        from config import get_settings
        from celery_config import get_celery_config

        settings = get_settings()
        celery_config = get_celery_config()

        # Check that broker URLs match
        if celery_config["broker_url"] != settings.celery_broker_url:
            logger.error("❌ Celery broker URL doesn't match settings")
            return False

        # Check that result backend matches
        if celery_config["result_backend"] != settings.celery_result_backend:
            logger.error("❌ Celery result backend doesn't match settings")
            return False

        logger.info("✅ Celery config properly integrated with application settings")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to verify config integration: {e}")
        return False


def main():
    """Run all verification checks."""
    logger.info("=" * 60)
    logger.info("Celery Setup Verification")
    logger.info("=" * 60)
    logger.info("")

    checks = [
        ("Celery Import", verify_celery_import),
        ("Celery Configuration", verify_celery_config),
        ("Task Definitions", verify_task_definitions),
        ("Config Integration", verify_config_integration),
    ]

    results = []
    for check_name, check_func in checks:
        logger.info(f"\n🔍 Checking: {check_name}")
        result = check_func()
        results.append((check_name, result))
        logger.info("")

    logger.info("=" * 60)
    logger.info("Verification Summary")
    logger.info("=" * 60)

    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {check_name}")

    all_passed = all(result for _, result in results)

    logger.info("")
    if all_passed:
        logger.info("🎉 All verification checks passed!")
        logger.info("")
        logger.info("To start a Celery worker, run:")
        logger.info("  celery -A tasks worker --loglevel=info")
        logger.info("")
        logger.info("To verify worker connectivity, run:")
        logger.info("  celery -A tasks inspect ping")
        return 0
    else:
        logger.error("❌ Some verification checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
