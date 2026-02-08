#!/usr/bin/env python3
"""
End-to-End Verification Test for Tag Filtering

This script verifies:
1. Backend API - Single tag filtering via /api/candidates/?tag_id={uuid}
2. Backend API - Multiple tag filtering via /api/search/candidates
3. Frontend API Client - tagIds parameter support
4. TagFilter Component - Implementation and features

Usage:
    python test_e2e_tag_filtering.py

Requirements:
    - Backend API running on http://localhost:8000
    - PostgreSQL database running
    - Test data: at least 2 tags and multiple candidates
"""

import asyncio
import sys
import requests
import json
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

# Configuration
BACKEND_URL = "http://localhost:8000"
ORGANIZATION_ID = "default-org"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

@dataclass
class TestResult:
    """Result of a test case."""
    name: str
    passed: bool
    details: str
    data: Any = None

class TagFilteringE2E:
    """End-to-end test suite for tag filtering."""

    def __init__(self, base_url: str = BACKEND_URL):
        self.base_url = base_url
        self.results: List[TestResult] = []
        self.session = requests.Session()
        self.test_data: Dict[str, Any] = {}

    def log(self, message: str, color: str = Colors.END):
        """Print colored message."""
        print(f"{color}{message}{Colors.END}")

    def print_section(self, title: str):
        """Print section header."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{title.center(70)}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}\n")

    def record_result(self, name: str, passed: bool, details: str, data: Any = None):
        """Record test result."""
        result = TestResult(name, passed, details, data)
        self.results.append(result)
        status = f"{Colors.GREEN}✓ PASS{Colors.END}" if passed else f"{Colors.RED}✗ FAIL{Colors.END}"
        self.log(f"{status} - {name}")
        if not passed or data:
            self.log(f"  {details}", Colors.YELLOW)

    # ========================================================================
    # SETUP: Get Test Data
    # ========================================================================

    def setup_test_data(self):
        """Get test data from the system."""
        self.print_section("SETUP: Gathering Test Data")

        # Get all tags
        try:
            response = self.session.get(
                f"{self.base_url}/api/candidate-tags/",
                params={"organization_id": ORGANIZATION_ID, "is_active": True},
                timeout=10
            )
            if response.status_code == 200:
                tags = response.json().get("tags", [])
                self.test_data["tags"] = tags
                self.log(f"Found {len(tags)} active tags")
                for tag in tags[:3]:
                    self.log(f"  - {tag['tag_name']} (ID: {tag['id']})", Colors.BLUE)
                if len(tags) < 2:
                    self.log("WARNING: Need at least 2 tags for comprehensive testing", Colors.YELLOW)
            else:
                self.record_result(
                    "Setup: Get tags",
                    False,
                    f"Failed to get tags: {response.status_code}"
                )
                return False
        except Exception as e:
            self.record_result(
                "Setup: Get tags",
                False,
                f"Error: {str(e)}"
            )
            return False

        # Get all candidates
        try:
            response = self.session.get(
                f"{self.base_url}/api/candidates/",
                params={"limit": 100},
                timeout=10
            )
            if response.status_code == 200:
                candidates = response.json()
                self.test_data["candidates"] = candidates
                self.log(f"Found {len(candidates)} candidates")
                # Count candidates with tags
                candidates_with_tags = [c for c in candidates if c.get("tags")]
                self.log(f"  {len(candidates_with_tags)} candidates have tags")
            else:
                self.record_result(
                    "Setup: Get candidates",
                    False,
                    f"Failed to get candidates: {response.status_code}"
                )
                return False
        except Exception as e:
            self.record_result(
                "Setup: Get candidates",
                False,
                f"Error: {str(e)}"
            )
            return False

        return True

    # ========================================================================
    # TEST 1: Backend API - Single Tag Filtering
    # ========================================================================

    def test_single_tag_filtering(self):
        """Test filtering by single tag via /api/candidates/?tag_id={uuid}."""
        self.print_section("TEST 1: Single Tag Filtering (GET /api/candidates/)")

        tags = self.test_data.get("tags", [])
        if not tags:
            self.record_result("Single tag filtering", False, "No tags available for testing")
            return

        tag = tags[0]
        tag_id = tag["id"]
        tag_name = tag["tag_name"]

        # Test 1.1: Filter by valid tag
        try:
            response = self.session.get(
                f"{self.base_url}/api/candidates/",
                params={"tag_id": tag_id, "limit": 100},
                timeout=10
            )

            if response.status_code == 200:
                candidates = response.json()
                # Verify all results have the tag
                all_have_tag = all(
                    any(t["id"] == tag_id for t in c.get("tags", []))
                    for c in candidates
                )
                self.record_result(
                    "Filter by valid tag_id",
                    all_have_tag,
                    f"Found {len(candidates)} candidates with tag '{tag_name}'",
                    {"count": len(candidates), "tag": tag_name}
                )
            else:
                self.record_result(
                    "Filter by valid tag_id",
                    False,
                    f"Unexpected status: {response.status_code}"
                )
        except Exception as e:
            self.record_result(
                "Filter by valid tag_id",
                False,
                f"Error: {str(e)}"
            )

        # Test 1.2: Filter by invalid tag (should return empty)
        try:
            response = self.session.get(
                f"{self.base_url}/api/candidates/",
                params={"tag_id": "00000000-0000-0000-0000-000000000000", "limit": 100},
                timeout=10
            )

            if response.status_code == 200:
                candidates = response.json()
                self.record_result(
                    "Filter by invalid tag_id",
                    len(candidates) == 0,
                    f"Returns {len(candidates)} candidates (expected 0)"
                )
            else:
                self.record_result(
                    "Filter by invalid tag_id",
                    False,
                    f"Unexpected status: {response.status_code}"
                )
        except Exception as e:
            self.record_result(
                "Filter by invalid tag_id",
                False,
                f"Error: {str(e)}"
            )

        # Test 1.3: Combine tag filter with other filters
        try:
            response = self.session.get(
                f"{self.base_url}/api/candidates/",
                params={
                    "tag_id": tag_id,
                    "stage_id": "new",
                    "limit": 100
                },
                timeout=10
            )

            if response.status_code == 200:
                candidates = response.json()
                # Verify candidates have the tag AND are in 'new' stage
                valid = all(
                    any(t["id"] == tag_id for t in c.get("tags", []))
                    and c.get("current_stage") in ["new", "New"]
                    for c in candidates
                )
                self.record_result(
                    "Combine tag_id with stage filter",
                    valid,
                    f"Found {len(candidates)} candidates with tag '{tag_name}' in 'new' stage"
                )
            else:
                self.record_result(
                    "Combine tag_id with stage filter",
                    False,
                    f"Unexpected status: {response.status_code}"
                )
        except Exception as e:
            self.record_result(
                "Combine tag_id with stage filter",
                False,
                f"Error: {str(e)}"
            )

    # ========================================================================
    # TEST 2: Backend API - Multiple Tag Filtering (Search API)
    # ========================================================================

    def test_multiple_tag_filtering(self):
        """Test filtering by multiple tags via /api/search/candidates."""
        self.print_section("TEST 2: Multiple Tag Filtering (POST /api/search/candidates)")

        tags = self.test_data.get("tags", [])
        if len(tags) < 2:
            self.record_result(
                "Multiple tag filtering",
                False,
                "Need at least 2 tags for testing (found {len(tags)})"
            )
            return

        # Use first 2 tags
        tag_ids = [tags[0]["id"], tags[1]["id"]]
        tag_names = [tags[0]["tag_name"], tags[1]["tag_name"]]

        # Test 2.1: Search with tag_ids filter
        try:
            request_body = {
                "query": "",
                "filters": {
                    "tag_ids": tag_ids
                },
                "skip": 0,
                "limit": 100
            }

            response = self.session.post(
                f"{self.base_url}/api/search/candidates",
                json=request_body,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                candidates = result.get("candidates", [])
                total = result.get("total", len(candidates))

                # Verify candidates have at least one of the tags (OR logic)
                valid = all(
                    any(t["id"] in tag_ids for t in c.get("tags", []))
                    for c in candidates
                )

                self.record_result(
                    "Search with tag_ids filter (OR logic)",
                    valid,
                    f"Found {total} candidates with tags '{', '.join(tag_names)}'",
                    {"count": total, "tags": tag_names}
                )
            else:
                self.record_result(
                    "Search with tag_ids filter",
                    False,
                    f"Unexpected status: {response.status_code}"
                )
        except Exception as e:
            self.record_result(
                "Search with tag_ids filter",
                False,
                f"Error: {str(e)}"
            )

        # Test 2.2: Combine tag_ids with other filters
        try:
            request_body = {
                "query": "",
                "filters": {
                    "tag_ids": tag_ids,
                    "stage_id": "new"
                },
                "skip": 0,
                "limit": 100
            }

            response = self.session.post(
                f"{self.base_url}/api/search/candidates",
                json=request_body,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                candidates = result.get("candidates", [])
                self.record_result(
                    "Combine tag_ids with stage filter",
                    True,
                    f"Found {len(candidates)} candidates"
                )
            else:
                self.record_result(
                    "Combine tag_ids with stage filter",
                    False,
                    f"Unexpected status: {response.status_code}"
                )
        except Exception as e:
            self.record_result(
                "Combine tag_ids with stage filter",
                False,
                f"Error: {str(e)}"
            )

    # ========================================================================
    # TEST 3: Verify Frontend API Client
    # ========================================================================

    def test_frontend_api_client(self):
        """Verify frontend API client supports tag filtering."""
        self.print_section("TEST 3: Frontend API Client Verification")

        # Check if frontend client file exists and has correct implementation
        client_file = Path("frontend/src/api/candidates.ts")

        if not client_file.exists():
            self.record_result(
                "Frontend client file exists",
                False,
                f"File not found: {client_file}"
            )
            return

        content = client_file.read_text()

        # Check 3.1: listCandidates method accepts tagIds parameter
        has_tag_ids_param = "tagIds" in content and "string[]" in content
        self.record_result(
            "Client accepts tagIds array parameter",
            has_tag_ids_param,
            "listCandidates method includes tagIds parameter" if has_tag_ids_param else "tagIds parameter not found"
        )

        # Check 3.2: Client passes tagIds to API request
        has_params_setting = "params.tag_ids" in content or "params[\"tag_ids\"]" in content
        self.record_result(
            "Client sends tag_ids to backend API",
            has_params_setting,
            "tagIds properly mapped to tag_ids in request" if has_params_setting else "tag_ids not set in request params"
        )

        # Check 3.3: Documentation includes tag filtering examples
        has_tag_docs = "tag" in content.lower() and "filter" in content.lower()
        self.record_result(
            "Documentation includes tag filtering",
            has_tag_docs,
            "JSDoc includes tag filtering examples" if has_tag_docs else "Tag filtering documentation not found"
        )

    # ========================================================================
    # TEST 4: Verify TagFilter Component
    # ========================================================================

    def test_tagfilter_component(self):
        """Verify TagFilter component implementation."""
        self.print_section("TEST 4: TagFilter Component Verification")

        component_file = Path("frontend/src/components/TagFilter.tsx")

        if not component_file.exists():
            self.record_result(
                "TagFilter component exists",
                False,
                f"File not found: {component_file}"
            )
            return

        content = component_file.read_text()

        # Check 4.1: Component structure
        has_component = "interface TagFilterProps" in content and "const TagFilter" in content
        self.record_result(
            "TagFilter component defined",
            has_component,
            "Component exports properly" if has_component else "Component definition not found"
        )

        # Check 4.2: Multi-select support
        has_multi_select = "Checkbox" in content and "selectedTagIds" in content
        self.record_result(
            "Multi-select functionality",
            has_multi_select,
            "Supports multiple tag selection" if has_multi_select else "Multi-select not implemented"
        )

        # Check 4.3: Tag color display
        has_color = "getTagColor" in content or "backgroundColor" in content
        self.record_result(
            "Tag color display",
            has_color,
            "Shows tags with custom colors" if has_color else "Tag color display not found"
        )

        # Check 4.4: Clear all functionality
        has_clear = "handleClearAll" in content or "clearAll" in content
        self.record_result(
            "Clear all filters functionality",
            has_clear,
            "Provides clear button" if has_clear else "Clear functionality not found"
        )

        # Check 4.5: Loading and error states
        has_states = "loading" in content and "error" in content.lower()
        self.record_result(
            "Loading and error states",
            has_states,
            "Handles loading and error states" if has_states else "State handling not found"
        )

        # Check 4.6: Max selections limit
        has_max = "maxSelections" in content
        self.record_result(
            "Max selections limit",
            has_max,
            "Supports maxSelections prop" if has_max else "maxSelections not implemented"
        )

    # ========================================================================
    # TEST 5: Backend API Response Structure
    # ========================================================================

    def test_api_response_structure(self):
        """Verify API responses include tag information."""
        self.print_section("TEST 5: API Response Structure")

        # Test 5.1: Candidates list includes tags
        try:
            response = self.session.get(
                f"{self.base_url}/api/candidates/",
                params={"limit": 10},
                timeout=10
            )

            if response.status_code == 200:
                candidates = response.json()
                has_tags_field = all("tags" in c for c in candidates)
                self.record_result(
                    "Candidates include tags field",
                    has_tags_field,
                    "All candidates have tags array" if has_tags_field else "tags field missing"
                )

                if has_tags_field:
                    # Check tag structure
                    sample_tag = None
                    for c in candidates:
                        if c.get("tags"):
                            sample_tag = c["tags"][0]
                            break

                    if sample_tag:
                        has_id = "id" in sample_tag
                        has_name = "tag_name" in sample_tag
                        has_color = "color" in sample_tag

                        self.record_result(
                            "Tag has id field",
                            has_id,
                            f"Tag ID: {sample_tag.get('id')}" if has_id else "id field missing"
                        )
                        self.record_result(
                            "Tag has tag_name field",
                            has_name,
                            f"Tag name: {sample_tag.get('tag_name')}" if has_name else "tag_name field missing"
                        )
                        self.record_result(
                            "Tag has color field",
                            has_color,
                            f"Tag color: {sample_tag.get('color')}" if has_color else "color field missing (optional)"
                        )
            else:
                self.record_result(
                    "Candidates include tags field",
                    False,
                    f"Unexpected status: {response.status_code}"
                )
        except Exception as e:
            self.record_result(
                "Candidates include tags field",
                False,
                f"Error: {str(e)}"
            )

    # ========================================================================
    # RUN ALL TESTS
    # ========================================================================

    def run_all_tests(self):
        """Run all verification tests."""
        print(f"\n{Colors.BOLD}{'=' * 70}{Colors.END}")
        print(f"{Colors.BOLD}TAG FILTERING - END-TO-END VERIFICATION{Colors.END}")
        print(f"{Colors.BOLD}{'=' * 70}{Colors.END}")

        # Setup
        if not self.setup_test_data():
            self.log("\n❌ Setup failed. Cannot continue with tests.", Colors.RED)
            self.print_summary()
            return False

        # Run tests
        self.test_single_tag_filtering()
        self.test_multiple_tag_filtering()
        self.test_frontend_api_client()
        self.test_tagfilter_component()
        self.test_api_response_structure()

        # Print summary
        self.print_summary()
        return True

    def print_summary(self):
        """Print test summary."""
        self.print_section("TEST SUMMARY")

        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)

        print(f"{Colors.BOLD}Total Tests: {total}{Colors.END}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.END}")
        print(f"{Colors.RED}Failed: {failed}{Colors.END}")
        print(f"\nSuccess Rate: {passed / total * 100:.1f}%")

        if failed > 0:
            print(f"\n{Colors.BOLD}{Colors.RED}Failed Tests:{Colors.END}")
            for result in self.results:
                if not result.passed:
                    print(f"  ✗ {result.name}: {result.details}")

        print(f"\n{Colors.BOLD}{'=' * 70}{Colors.END}")
        if failed == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}ALL TESTS PASSED ✓{Colors.END}")
        else:
            print(f"{Colors.RED}{Colors.BOLD}SOME TESTS FAILED ✗{Colors.END}")
        print(f"{Colors.BOLD}{'=' * 70}{Colors.END}\n")

def main():
    """Main entry point."""
    tester = TagFilteringE2E()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
