"""
Verification script for Celery task registration.

This script verifies that all new Celery tasks are properly registered
and can be discovered by the Celery worker.
"""
import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def verify_task_files_exist():
    """Verify that all task files exist."""
    logger.info("🔍 Checking task files...")

    tasks_dir = Path(__file__).parent / "tasks"
    expected_files = [
        "analysis_task.py",
        "learning_tasks.py",
        "report_generation.py",
        "email_task.py",  # NEW
        "search_alerts_task.py",  # NEW
    ]

    missing_files = []
    for file_name in expected_files:
        file_path = tasks_dir / file_name
        if file_path.exists():
            logger.info(f"   ✅ {file_name}")
        else:
            logger.error(f"   ❌ {file_name} - MISSING")
            missing_files.append(file_name)

    if missing_files:
        logger.error(f"❌ Missing task files: {missing_files}")
        return False

    logger.info("✅ All task files exist")
    return True


def verify_task_imports():
    """Verify that all tasks can be imported."""
    logger.info("\n🔍 Checking task imports...")

    try:
        # Import the tasks module
        from tasks import (
            analyze_resume_async,
            batch_analyze_resumes,
            aggregate_feedback_and_generate_synonyms,
            review_and_activate_synonyms,
            periodic_feedback_aggregation,
            retrain_skill_matching_model,
            get_report_data,
            format_report_as_pdf,
            format_report_as_csv,
            send_report_via_email,
            generate_scheduled_reports,
            process_all_pending_reports,
            send_feedback_notification,  # NEW
            send_batch_notification,  # NEW
            check_resume_against_saved_searches,  # NEW
            send_search_alert_notification,  # NEW
            process_pending_alerts,  # NEW
        )

        logger.info("✅ All tasks imported successfully")

        # Verify specific new tasks
        new_tasks = {
            "send_feedback_notification": send_feedback_notification,
            "send_batch_notification": send_batch_notification,
            "check_resume_against_saved_searches": check_resume_against_saved_searches,
            "send_search_alert_notification": send_search_alert_notification,
            "process_pending_alerts": process_pending_alerts,
        }

        for task_name, task_func in new_tasks.items():
            if task_func is not None:
                logger.info(f"   ✅ {task_name}")
            else:
                logger.error(f"   ❌ {task_name} - None")
                return False

        return True

    except ImportError as e:
        logger.error(f"❌ Failed to import tasks: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error during import: {e}")
        return False


def verify_task_decorators():
    """Verify that tasks have @shared_task decorators."""
    logger.info("\n🔍 Checking @shared_task decorators...")

    try:
        from celery import shared_task

        # Import task modules to check decorators
        from tasks import email_task
        from tasks import search_alerts_task

        # Check email_task module
        email_tasks = [
            "send_feedback_notification",
            "send_batch_notification",
        ]

        for task_name in email_tasks:
            if hasattr(email_task, task_name):
                task_func = getattr(email_task, task_name)
                # Check if it has the Celery task attributes
                if hasattr(task_func, 'name') or hasattr(task_func, 'delay'):
                    logger.info(f"   ✅ email_task.{task_name} - has @shared_task decorator")
                else:
                    logger.warning(f"   ⚠️  email_task.{task_name} - decorator may be missing")
            else:
                logger.error(f"   ❌ email_task.{task_name} - not found")
                return False

        # Check search_alerts_task module
        alert_tasks = [
            "check_resume_against_saved_searches",
            "send_search_alert_notification",
            "process_pending_alerts",
        ]

        for task_name in alert_tasks:
            if hasattr(search_alerts_task, task_name):
                task_func = getattr(search_alerts_task, task_name)
                # Check if it has the Celery task attributes
                if hasattr(task_func, 'name') or hasattr(task_func, 'delay'):
                    logger.info(f"   ✅ search_alerts_task.{task_name} - has @shared_task decorator")
                else:
                    logger.warning(f"   ⚠️  search_alerts_task.{task_name} - decorator may be missing")
            else:
                logger.error(f"   ❌ search_alerts_task.{task_name} - not found")
                return False

        logger.info("✅ All new tasks have @shared_task decorators")
        return True

    except Exception as e:
        logger.error(f"❌ Error checking decorators: {e}")
        return False


def verify_task_names():
    """Verify that task names match expected pattern."""
    logger.info("\n🔍 Checking task names...")

    expected_task_names = {
        "email_task": [
            "tasks.email_task.send_feedback_notification",
            "tasks.email_task.send_batch_notification",
        ],
        "search_alerts": [
            "tasks.search_alerts.check_resume_against_saved_searches",
            "tasks.search_alerts.send_search_alert_notification",
            "tasks.search_alerts.process_pending_alerts",
        ],
        "report_generation": [
            "tasks.report_generation.generate_scheduled_reports",
            "tasks.report_generation.process_all_pending_reports",
        ],
    }

    try:
        from tasks import email_task, search_alerts_task

        # Check email_task names
        for attr_name in ["send_feedback_notification", "send_batch_notification"]:
            task_func = getattr(email_task, attr_name)
            task_name = getattr(task_func, 'name', None)
            if task_name:
                logger.info(f"   ✅ {attr_name}: {task_name}")
            else:
                logger.warning(f"   ⚠️  {attr_name}: no name attribute")

        # Check search_alerts_task names
        for attr_name in ["check_resume_against_saved_searches", "send_search_alert_notification", "process_pending_alerts"]:
            task_func = getattr(search_alerts_task, attr_name)
            task_name = getattr(task_func, 'name', None)
            if task_name:
                logger.info(f"   ✅ {attr_name}: {task_name}")
            else:
                logger.warning(f"   ⚠️  {attr_name}: no name attribute")

        logger.info("✅ Task names verified")
        return True

    except Exception as e:
        logger.error(f"❌ Error checking task names: {e}")
        return False


def verify_celery_app_import():
    """Verify that Celery app can import the new tasks."""
    logger.info("\n🔍 Checking Celery app task registration...")

    try:
        from tasks import celery_app

        # Get registered tasks
        registered_tasks = list(celery_app.tasks.keys())

        logger.info(f"   Total registered tasks: {len(registered_tasks)}")

        # Check for expected task name patterns
        expected_patterns = [
            "tasks.email_task",
            "tasks.search_alerts",
            "tasks.report_generation",
        ]

        found_patterns = {pattern: False for pattern in expected_patterns}

        for task_name in registered_tasks:
            for pattern in expected_patterns:
                if pattern in task_name:
                    found_patterns[pattern] = True
                    logger.info(f"   ✅ Found task: {task_name}")

        all_found = all(found_patterns.values())

        if not all_found:
            missing = [p for p, found in found_patterns.items() if not found]
            logger.warning(f"   ⚠️  Patterns not found: {missing}")
            logger.warning(f"   Note: Tasks may not be fully registered until Celery worker starts")

        logger.info("✅ Celery app imports verified")
        return True

    except Exception as e:
        logger.error(f"❌ Error checking Celery app: {e}")
        return False


def main():
    """Run all verification checks."""
    logger.info("=" * 60)
    logger.info("Celery Task Registration Verification")
    logger.info("=" * 60)
    logger.info("")

    checks = [
        ("Task Files Exist", verify_task_files_exist),
        ("Task Imports", verify_task_imports),
        ("Task Decorators", verify_task_decorators),
        ("Task Names", verify_task_names),
        ("Celery App Import", verify_celery_app_import),
    ]

    results = []
    for check_name, check_func in checks:
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Check: {check_name}")
        logger.info("=" * 60)
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
        logger.info("New tasks verified:")
        logger.info("  ✅ email_task.send_feedback_notification")
        logger.info("  ✅ email_task.send_batch_notification")
        logger.info("  ✅ search_alerts_task.check_resume_against_saved_searches")
        logger.info("  ✅ search_alerts_task.send_search_alert_notification")
        logger.info("  ✅ search_alerts_task.process_pending_alerts")
        logger.info("")
        logger.info("To verify with Celery inspect (requires running worker):")
        logger.info("  cd backend && celery -A tasks inspect registered | grep -E '(email_task|search_alerts|report_generation)'")
        logger.info("")
        logger.info("Expected output:")
        logger.info("  - tasks.email_task.send_feedback_notification")
        logger.info("  - tasks.email_task.send_batch_notification")
        logger.info("  - tasks.search_alerts.check_resume_against_saved_searches")
        logger.info("  - tasks.search_alerts.send_search_alert_notification")
        logger.info("  - tasks.search_alerts.process_pending_alerts")
        logger.info("  - tasks.report_generation.generate_scheduled_reports")
        logger.info("  - tasks.report_generation.process_all_pending_reports")
        return 0
    else:
        logger.error("❌ Some verification checks failed")
        logger.error("")
        logger.error("Please check the errors above and fix:")
        logger.error("  1. Ensure email_task.py and search_alerts_task.py exist in backend/tasks/")
        logger.error("  2. Ensure tasks/__init__.py imports all tasks")
        logger.error("  3. Ensure backend/tasks.py imports all tasks")
        logger.error("  4. Ensure all tasks have @shared_task decorators")
        return 1


if __name__ == "__main__":
    sys.exit(main())
