#!/usr/bin/env python3
"""
API Endpoint Verification Script

This script verifies that all API endpoints are properly configured and accessible.
It tests both new endpoints from the merge and existing endpoints.

Usage:
    python verify_api_endpoints.py              # Static analysis only
    python verify_api_endpoints.py --live       # Test against running backend
    python verify_api_endpoints.py --verbose    # Detailed output

Requirements for live testing:
    - Backend running on http://localhost:8000
    - Database accessible
    - No authentication required for health/metadata endpoints
"""

import sys
import ast
import re
from pathlib import Path
from typing import Dict, List, Tuple, Set
import argparse


class APIEndpoint:
    """Represents a single API endpoint."""

    def __init__(self, path: str, method: str, tags: List[str], file_path: str):
        self.path = path
        self.method = method.upper()
        self.tags = tags
        self.file_path = file_path
        self.full_path = ""  # Will be set after prefix is determined

    def __repr__(self):
        return f"{self.method} {self.full_path or self.path} ({', '.join(self.tags)})"


class APIRouter:
    """Represents an API router with its endpoints."""

    def __init__(self, name: str, file_path: str, prefix: str = "", tags: List[str] = None):
        self.name = name
        self.file_path = file_path
        self.prefix = prefix
        self.tags = tags or []
        self.endpoints: List[APIEndpoint] = []

    def add_endpoint(self, endpoint: APIEndpoint):
        """Add an endpoint to this router."""
        endpoint.full_path = f"{self.prefix}{endpoint.path}" if self.prefix else endpoint.path
        self.endpoints.append(endpoint)

    def __repr__(self):
        return f"Router({self.name}, prefix={self.prefix}, {len(self.endpoints)} endpoints)"


def extract_router_info(file_path: Path) -> Tuple[List[APIEndpoint], str]:
    """
    Extract API endpoints and router configuration from a router file.

    Args:
        file_path: Path to the router Python file

    Returns:
        Tuple of (endpoints list, router_variable_name)
    """
    endpoints = []
    router_var = None

    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Find router variable assignment
        router_match = re.search(r'(\w+)\s*=\s*APIRouter\(', content)
        if router_match:
            router_var = router_match.group(1)

        # Find all @router decorators
        pattern = rf'@{router_var}\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
        for match in re.finditer(pattern, content):
            method = match.group(1)
            path = match.group(2)

            # Extract tags if present
            tags_match = re.search(r'tags=\[([^\]]+)\]', content[match.start():match.start()+200])
            tags = []
            if tags_match:
                tags_str = tags_match.group(1)
                tags = [t.strip().strip('"\'') for t in tags_str.split(',')]

            endpoints.append(APIEndpoint(path, method, tags, str(file_path)))

    except Exception as e:
        print(f"Warning: Could not parse {file_path}: {e}")

    return endpoints, router_var


def analyze_main_py(main_path: Path) -> Dict[str, APIRouter]:
    """
    Analyze main.py to extract router registrations.

    Args:
        main_path: Path to main.py

    Returns:
        Dictionary of router_name -> APIRouter
    """
    routers = {}

    try:
        with open(main_path, 'r') as f:
            content = f.read()

        # Find all router imports
        import_pattern = r'from\s+api\.(\w+)\s+import\s+\w+\s+as\s+(\w+)'
        imports = {}
        for match in re.finditer(import_pattern, content):
            module_name = match.group(1)
            alias = match.group(2)
            imports[alias] = module_name

        # Find all include_router calls
        include_pattern = r'app\.include_router\((\w+)\.router,\s*prefix="([^"]+)",\s*tags=\[([^\]]+)\]'
        for match in re.finditer(include_pattern, content):
            alias = match.group(1)
            prefix = match.group(2)
            tags_str = match.group(3)
            tags = [t.strip().strip('"\'') for t in tags_str.split(',')]

            module_name = imports.get(alias, alias)
            router = APIRouter(module_name, f"api/{module_name}.py", prefix, tags)
            routers[module_name] = router

    except Exception as e:
        print(f"Warning: Could not analyze main.py: {e}")

    return routers


def discover_all_endpoints(backend_dir: Path) -> Dict[str, APIRouter]:
    """
    Discover all API endpoints by analyzing router files and main.py.

    Args:
        backend_dir: Path to backend directory

    Returns:
        Dictionary of router_name -> APIRouter with all endpoints
    """
    main_path = backend_dir / "main.py"
    api_dir = backend_dir / "api"

    # First analyze main.py to get router registrations
    routers = analyze_main_py(main_path)

    # Then parse each router file to extract endpoints
    for router_file in api_dir.glob("*.py"):
        if router_file.name == "__init__.py":
            continue

        router_name = router_file.stem
        if router_name in routers:
            endpoints, _ = extract_router_info(router_file)
            for endpoint in endpoints:
                routers[router_name].add_endpoint(endpoint)
        else:
            # Router exists but not included in main.py
            print(f"Warning: Router {router_name} exists but not included in main.py")

    return routers


def print_endpoint_summary(routers: Dict[str, APIRouter], verbose: bool = False):
    """Print a summary of all discovered endpoints."""
    total_endpoints = sum(len(r.endpoints) for r in routers.values())

    print("\n" + "="*80)
    print("API ENDPOINT VERIFICATION SUMMARY")
    print("="*80)
    print(f"\nTotal Routers: {len(routers)}")
    print(f"Total Endpoints: {total_endpoints}\n")

    # Group by new vs existing
    new_routers = ["analytics", "reports"]
    existing_routers = [k for k in routers.keys() if k not in new_routers]

    print("NEW ROUTERS (from merge):")
    print("-" * 80)
    for router_name in new_routers:
        if router_name in routers:
            router = routers[router_name]
            print(f"\n{router_name.upper()} ({router.prefix})")
            for endpoint in router.endpoints:
                print(f"  {endpoint.method:6} {endpoint.full_path}")
                if verbose:
                    print(f"        Tags: {', '.join(endpoint.tags)}")
                    print(f"        File: {endpoint.file_path}")

    print("\n\nEXISTING ROUTERS:")
    print("-" * 80)
    for router_name in sorted(existing_routers):
        router = routers[router_name]
        print(f"\n{router_name.upper()} ({router.prefix})")
        for endpoint in router.endpoints:
            print(f"  {endpoint.method:6} {endpoint.full_path}")

    print("\n")


def generate_curl_commands(routers: Dict[str, APIRouter]) -> List[str]:
    """Generate curl commands to test endpoints."""
    commands = []

    # Add health check
    commands.append("# Health Check")
    commands.append("curl -s http://localhost:8000/health | jq .")
    commands.append("")

    # Test new analytics endpoints
    commands.append("# Analytics Endpoints (NEW)")
    analytics_router = routers.get("analytics")
    if analytics_router:
        for endpoint in analytics_router.endpoints:
            if endpoint.method == "GET":
                commands.append(f"curl -s http://localhost:8000{endpoint.full_path} | jq .")

    commands.append("")

    # Test new reports endpoints
    commands.append("# Reports Endpoints (NEW)")
    reports_router = routers.get("reports")
    if reports_router:
        for endpoint in reports_router.endpoints:
            if endpoint.method == "GET":
                commands.append(f"curl -s http://localhost:8000{endpoint.full_path} | jq .")

    return commands


def verify_endpoints_with_backend(base_url: str = "http://localhost:8000") -> Dict[str, any]:
    """
    Verify endpoints against a running backend server.

    Args:
        base_url: Base URL of the backend API

    Returns:
        Dictionary with verification results
    """
    import urllib.request
    import json
    from urllib.error import URLError, HTTPError

    results = {
        "endpoints_tested": 0,
        "endpoints_passed": 0,
        "endpoints_failed": 0,
        "errors": []
    }

    backend_dir = Path(__file__).parent
    routers = discover_all_endpoints(backend_dir)

    print(f"\nTesting endpoints against {base_url}...")
    print("="*80)

    # Test health first
    try:
        with urllib.request.urlopen(f"{base_url}/health", timeout=5) as response:
            if response.status == 200:
                print("✓ Backend health check: PASS")
            else:
                print(f"✗ Backend health check: FAIL (status {response.status})")
                results["errors"].append("Health check failed")
                return results
    except Exception as e:
        print(f"✗ Backend health check: FAIL ({e})")
        results["errors"].append(f"Cannot connect to backend: {e}")
        return results

    # Test each endpoint
    for router_name, router in routers.items():
        for endpoint in router.endpoints:
            if endpoint.method != "GET":
                continue  # Only test GET endpoints without data

            url = f"{base_url}{endpoint.full_path}"
            results["endpoints_tested"] += 1

            try:
                with urllib.request.urlopen(url, timeout=5) as response:
                    if response.status == 200:
                        print(f"✓ {endpoint.method:6} {endpoint.full_path}: PASS (200)")
                        results["endpoints_passed"] += 1
                    elif response.status == 404:
                        print(f"✗ {endpoint.method:6} {endpoint.full_path}: FAIL (404 Not Found)")
                        results["endpoints_failed"] += 1
                        results["errors"].append(f"{url} returned 404")
                    else:
                        print(f"⚠ {endpoint.method:6} {endpoint.full_path}: WARN (status {response.status})")
                        results["endpoints_failed"] += 1
            except HTTPError as e:
                if e.code == 404:
                    print(f"✗ {endpoint.method:6} {endpoint.full_path}: FAIL (404 Not Found)")
                    results["endpoints_failed"] += 1
                    results["errors"].append(f"{url} returned 404")
                elif e.code == 422:
                    # Validation error is OK - endpoint exists but needs params
                    print(f"✓ {endpoint.method:6} {endpoint.full_path}: PASS (422 - needs parameters)")
                    results["endpoints_passed"] += 1
                else:
                    print(f"✗ {endpoint.method:6} {endpoint.full_path}: FAIL ({e.code} {e.reason})")
                    results["endpoints_failed"] += 1
                    results["errors"].append(f"{url} returned {e.code}")
            except URLError as e:
                print(f"✗ {endpoint.method:6} {endpoint.full_path}: FAIL (Connection error)")
                results["endpoints_failed"] += 1
                results["errors"].append(f"{url} connection failed")
            except Exception as e:
                print(f"✗ {endpoint.method:6} {endpoint.full_path}: FAIL ({e})")
                results["endpoints_failed"] += 1
                results["errors"].append(f"{url} error: {e}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Verify API endpoints")
    parser.add_argument("--live", action="store_true", help="Test against running backend")
    parser.add_argument("--url", default="http://localhost:8000", help="Backend URL")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--commands", action="store_true", help="Generate curl commands")

    args = parser.parse_args()

    # Get backend directory
    backend_dir = Path(__file__).parent

    # Discover all endpoints
    print("Discovering API endpoints...")
    routers = discover_all_endpoints(backend_dir)

    # Print summary
    print_endpoint_summary(routers, args.verbose)

    # Generate curl commands if requested
    if args.commands:
        print("\nCURL COMMANDS FOR MANUAL TESTING:")
        print("="*80)
        commands = generate_curl_commands(routers)
        for cmd in commands:
            print(cmd)
        print("\n")

    # Live testing
    if args.live:
        print("="*80)
        print("LIVE ENDPOINT TESTING")
        print("="*80)
        results = verify_endpoints_with_backend(args.url)

        print("\n" + "="*80)
        print("TEST RESULTS SUMMARY")
        print("="*80)
        print(f"Endpoints Tested: {results['endpoints_tested']}")
        print(f"Passed: {results['endpoints_passed']}")
        print(f"Failed: {results['endpoints_failed']}")

        if results["errors"]:
            print("\nErrors:")
            for error in results["errors"]:
                print(f"  - {error}")

        # Return exit code
        sys.exit(0 if results["endpoints_failed"] == 0 else 1)

    else:
        print("\nNote: Run with --live to test against a running backend server")
        print("Example: python verify_api_endpoints.py --live")


if __name__ == "__main__":
    main()
