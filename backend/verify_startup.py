#!/usr/bin/env python3
"""
Backend startup verification script.

This script checks if the backend application can start without errors
by verifying all imports and configurations are correct.
"""
import sys
from pathlib import Path

def verify_imports():
    """Verify that all main imports work correctly."""
    print("=" * 60)
    print("Step 1: Verifying main imports...")
    print("=" * 60)

    try:
        # Check main module imports
        print("✓ Importing config module...")
        from config import get_settings
        print("  ✓ Config module imported successfully")

        print("✓ Importing FastAPI...")
        from fastapi import FastAPI
        print("  ✓ FastAPI imported successfully")

        print("✓ Importing main application...")
        from main import app
        print("  ✓ Main application imported successfully")

        return True
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")
        return False


def verify_routers():
    """Verify that all API routers are properly included."""
    print("\n" + "=" * 60)
    print("Step 2: Verifying API routers...")
    print("=" * 60)

    try:
        from main import app

        # Get all routes
        routes = app.routes
        router_prefixes = set()

        for route in routes:
            if hasattr(route, 'path'):
                # Extract prefix from path (e.g., /api/resumes -> /api/resumes)
                path_parts = route.path.split('/')
                if len(path_parts) >= 3:
                    prefix = f"/{path_parts[1]}/{path_parts[2]}"
                    router_prefixes.add(prefix)

        print(f"✓ Found {len(router_prefixes)} router prefixes:")
        for prefix in sorted(router_prefixes):
            print(f"  - {prefix}")

        expected_routers = {
            "/api/resumes",
            "/api/matching",
            "/api/skill-taxonomies",
            "/api/custom-synonyms",
            "/api/feedback",
            "/api/model-versions",
            "/api/comparisons",
            "/api/analytics",
            "/api/reports",
            "/api/preferences",
        }

        missing_routers = expected_routers - router_prefixes
        if missing_routers:
            print(f"\n✗ Missing routers: {missing_routers}")
            return False
        else:
            print(f"\n✓ All {len(expected_routers)} expected routers are registered")
            return True

    except Exception as e:
        print(f"  ✗ Error verifying routers: {e}")
        return False


def verify_endpoints():
    """Verify that key endpoints exist."""
    print("\n" + "=" * 60)
    print("Step 3: Verifying key endpoints...")
    print("=" * 60)

    try:
        from main import app

        # Check for specific endpoints
        expected_endpoints = {
            "/health": "Health check endpoint",
            "/ready": "Readiness check endpoint",
            "/docs": "API documentation",
            "/": "Root endpoint",
        }

        all_paths = {route.path for route in app.routes if hasattr(route, 'path')}

        print("Checking expected endpoints:")
        all_present = True
        for endpoint, description in expected_endpoints.items():
            if endpoint in all_paths:
                print(f"  ✓ {endpoint:15} - {description}")
            else:
                print(f"  ✗ {endpoint:15} - {description} (MISSING)")
                all_present = False

        return all_present

    except Exception as e:
        print(f"  ✗ Error verifying endpoints: {e}")
        return False


def verify_openapi():
    """Verify that OpenAPI schema can be generated."""
    print("\n" + "=" * 60)
    print("Step 4: Verifying OpenAPI schema generation...")
    print("=" * 60)

    try:
        from main import app

        print("✓ Generating OpenAPI schema...")
        schema = app.openapi()

        # Check schema properties
        if 'openapi' in schema:
            print(f"  ✓ OpenAPI version: {schema['openapi']}")

        if 'info' in schema:
            print(f"  ✓ Title: {schema['info'].get('title', 'N/A')}")
            print(f"  ✓ Version: {schema['info'].get('version', 'N/A')}")

        if 'paths' in schema:
            path_count = len(schema['paths'])
            print(f"  ✓ Total API paths: {path_count}")

        return True

    except Exception as e:
        print(f"  ✗ Error generating OpenAPI schema: {e}")
        return False


def main():
    """Run all verification checks."""
    print("\n" + "=" * 60)
    print("Backend Startup Verification")
    print("=" * 60)

    results = {
        "imports": verify_imports(),
        "routers": verify_routers(),
        "endpoints": verify_endpoints(),
        "openapi": verify_openapi(),
    }

    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)

    for check, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} - {check.capitalize()}")

    all_passed = all(results.values())

    print("=" * 60)
    if all_passed:
        print("✓ All checks passed! Backend should start without errors.")
        print("\nTo start the backend, run:")
        print("  cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000")
        return 0
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
