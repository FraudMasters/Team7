#!/usr/bin/env python3
"""
Simple validation script for scheduled report delivery implementation.
This script verifies that all required functions and configurations are present.
"""
import sys
import importlib.util

def validate_implementation():
    """Validate the scheduled report delivery implementation."""
    errors = []

    # Load the module
    spec = importlib.util.spec_from_file_location(
        "report_generation",
        "tasks/report_generation.py"
    )
    module = importlib.util.module_from_spec(spec)

    try:
        spec.loader.exec_module(module)
    except Exception as e:
        errors.append(f"Failed to load module: {e}")
        return errors

    # Check for required functions
    required_functions = [
        "get_scheduled_report_config",
        "get_report_data",
        "format_report_as_pdf",
        "format_report_as_csv",
        "send_report_via_email",
        "generate_scheduled_reports",
        "process_all_pending_reports",
    ]

    for func_name in required_functions:
        if not hasattr(module, func_name):
            errors.append(f"Missing required function: {func_name}")
        else:
            print(f"✓ Found function: {func_name}")

    # Check for beat_schedule
    if not hasattr(module, "beat_schedule"):
        errors.append("Missing beat_schedule dictionary")
    else:
        print("✓ Found beat_schedule")
        beat_schedule = getattr(module, "beat_schedule")

        if not isinstance(beat_schedule, dict):
            errors.append("beat_schedule is not a dictionary")
        else:
            print(f"  - Contains {len(beat_schedule)} scheduled task(s)")

            # Check if process-all-pending-reports is in the schedule
            if "process-all-pending-reports" not in beat_schedule:
                errors.append("beat_schedule missing 'process-all-pending-reports' task")
            else:
                print("  ✓ Found 'process-all-pending-reports' task")

    # Test get_scheduled_report_config
    try:
        config = module.get_scheduled_report_config()
        required_keys = [
            "enabled",
            "check_interval_minutes",
            "batch_size",
            "retry_failed_reports",
            "max_retries",
            "retry_delay_minutes",
        ]

        for key in required_keys:
            if key not in config:
                errors.append(f"Config missing key: {key}")
            else:
                print(f"  ✓ Config has {key}: {config[key]}")

    except Exception as e:
        errors.append(f"Failed to get config: {e}")

    return errors

if __name__ == "__main__":
    print("Validating scheduled report delivery implementation...\n")

    errors = validate_implementation()

    print("\n" + "=" * 60)
    if errors:
        print("VALIDATION FAILED")
        print("\nErrors found:")
        for error in errors:
            print(f"  ✗ {error}")
        sys.exit(1)
    else:
        print("✓ VALIDATION PASSED")
        print("\nAll required components are present and correctly configured.")
        sys.exit(0)
