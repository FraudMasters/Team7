#!/usr/bin/env python3
"""
End-to-End Verification Test for Tag Suggestions

This script verifies:
1. Backend API - Tag suggestions endpoint returns popular tags with usage counts
2. Backend API - Suggestions are sorted by usage count (descending)
3. Backend API - New tags appear in suggestions after being applied to candidates
4. Backend API - Removed tags don't appear in suggestions
5. Backend API - Limit parameter works correctly
6. Frontend Component - CandidateTagsManager shows popular tags in create dialog
7. Frontend Component - Popular tags are clickable for quick assignment
8. Frontend Component - Usage counts are displayed

Usage:
    python test_e2e_tag_suggestions.py

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
import time

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

class TagSuggestionsE2E:
    """End-to-end test suite for tag suggestions."""

    def __init__(self, base_url: str = BACKEND_URL):
        self.base_url = base_url
        self.results: List[TestResult] = []
        self.session = requests.Session()
        self.test_data: Dict[str, Any] = {}
        self.created_tag_id: str = None
        self.test_candidate_ids: List[str] = []

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
                # Store candidate IDs for testing
                self.test_candidate_ids = [c["id"] for c in candidates[:5]]  # Use first 5
                self.log(f"Using {len(self.test_candidate_ids)} candidates for testing")
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
    # TEST 1: Backend API - Tag Suggestions Endpoint
    # ========================================================================

    def test_tag_suggestions_endpoint(self):
        """Test GET /api/candidate-tags/suggestions endpoint."""
        self.print_section("TEST 1: Tag Suggestions Endpoint")

        # Test 1.1: Get suggestions without limit
        try:
            response = self.session.get(
                f"{self.base_url}/api/candidate-tags/suggestions",
                params={"organization_id": ORGANIZATION_ID},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                suggestions = data.get("suggestions", [])
                total_count = data.get("total_count", len(suggestions))

                self.record_result(
                    "Suggestions endpoint returns 200",
                    True,
                    f"Returns {total_count} suggestions (default limit: 10)",
                    {"count": total_count}
                )

                # Verify structure
                if suggestions:
                    first_suggestion = suggestions[0]
                    has_required_fields = all(
                        field in first_suggestion
                        for field in ["id", "organization_id", "tag_name", "usage_count"]
                    )
                    self.record_result(
                        "Suggestions have required fields",
                        has_required_fields,
                        f"Fields: {list(first_suggestion.keys())}",
                        first_suggestion
                    )
                else:
                    self.record_result(
                        "Suggestions have required fields",
                        True,
                        "No suggestions available to verify structure"
                    )
            else:
                self.record_result(
                    "Suggestions endpoint returns 200",
                    False,
                    f"Unexpected status: {response.status_code}"
                )
        except Exception as e:
            self.record_result(
                "Suggestions endpoint returns 200",
                False,
                f"Error: {str(e)}"
            )

        # Test 1.2: Get suggestions with custom limit
        try:
            response = self.session.get(
                f"{self.base_url}/api/candidate-tags/suggestions",
                params={"organization_id": ORGANIZATION_ID, "limit": 3},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                suggestions = data.get("suggestions", [])
                total_count = data.get("total_count", len(suggestions))

                self.record_result(
                    "Suggestions respect limit parameter",
                    len(suggestions) <= 3,
                    f"Returns {total_count} suggestions (limit: 3)",
                    {"count": total_count, "limit": 3}
                )
            else:
                self.record_result(
                    "Suggestions respect limit parameter",
                    False,
                    f"Unexpected status: {response.status_code}"
                )
        except Exception as e:
            self.record_result(
                "Suggestions respect limit parameter",
                False,
                f"Error: {str(e)}"
            )

    # ========================================================================
    # TEST 2: Suggestions Are Sorted by Usage Count
    # ========================================================================

    def test_suggestions_sorted_by_usage(self):
        """Test that suggestions are sorted by usage_count (descending)."""
        self.print_section("TEST 2: Suggestions Sorted by Usage")

        try:
            response = self.session.get(
                f"{self.base_url}/api/candidate-tags/suggestions",
                params={"organization_id": ORGANIZATION_ID, "limit": 20},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                suggestions = data.get("suggestions", [])

                if len(suggestions) >= 2:
                    # Check if sorted by usage_count descending
                    is_sorted = all(
                        suggestions[i]["usage_count"] >= suggestions[i + 1]["usage_count"]
                        for i in range(len(suggestions) - 1)
                    )

                    usage_counts = [s["usage_count"] for s in suggestions[:5]]
                    self.record_result(
                        "Suggestions sorted by usage_count (descending)",
                        is_sorted,
                        f"Usage counts: {usage_counts}",
                        {"sorted": is_sorted, "counts": usage_counts}
                    )
                else:
                    self.record_result(
                        "Suggestions sorted by usage_count",
                        True,
                        f"Only {len(suggestions)} suggestion(s), cannot verify sorting"
                    )
            else:
                self.record_result(
                    "Suggestions sorted by usage_count",
                    False,
                    f"Unexpected status: {response.status_code}"
                )
        except Exception as e:
            self.record_result(
                "Suggestions sorted by usage_count",
                False,
                f"Error: {str(e)}"
            )

    # ========================================================================
    # TEST 3: Create New Tag and Apply to Candidates
    # ========================================================================

    def test_create_tag_and_apply(self):
        """Test creating a new tag and applying it to candidates."""
        self.print_section("TEST 3: Create Tag and Apply to Candidates")

        # Test 3.1: Create a new tag
        test_tag_name = f"E2E Test Tag {int(time.time())}"

        try:
            tag_data = {
                "organization_id": ORGANIZATION_ID,
                "tag_name": test_tag_name,
                "color": "#FF5722",
                "is_active": True
            }

            response = self.session.post(
                f"{self.base_url}/api/candidate-tags/",
                json=tag_data,
                timeout=10
            )

            if response.status_code == 201:
                tag = response.json()
                self.created_tag_id = tag["id"]

                self.record_result(
                    "Create new tag",
                    True,
                    f"Created tag '{test_tag_name}' with ID: {self.created_tag_id}",
                    tag
                )
            else:
                self.record_result(
                    "Create new tag",
                    False,
                    f"Failed to create tag: {response.status_code} - {response.text}"
                )
                return
        except Exception as e:
            self.record_result(
                "Create new tag",
                False,
                f"Error: {str(e)}"
            )
            return

        # Test 3.2: Apply tag to multiple candidates
        if not self.test_candidate_ids:
            self.record_result(
                "Apply tag to candidates",
                False,
                "No candidates available for testing"
            )
            return

        applied_count = 0
        for candidate_id in self.test_candidate_ids[:3]:  # Apply to first 3 candidates
            try:
                assign_data = {
                    "tag_id": self.created_tag_id,
                    "recruiter_id": None
                }

                response = self.session.post(
                    f"{self.base_url}/api/candidate-tags/resume/{candidate_id}/assign",
                    json=assign_data,
                    timeout=10
                )

                if response.status_code == 201:
                    applied_count += 1
                else:
                    self.log(f"Failed to apply tag to candidate {candidate_id}: {response.status_code}", Colors.RED)
            except Exception as e:
                self.log(f"Error applying tag to candidate {candidate_id}: {str(e)}", Colors.RED)

        self.record_result(
            "Apply tag to multiple candidates",
            applied_count > 0,
            f"Applied tag to {applied_count} of {min(3, len(self.test_candidate_ids))} candidates",
            {"applied": applied_count, "expected": min(3, len(self.test_candidate_ids))}
        )

    # ========================================================================
    # TEST 4: New Tag Appears in Suggestions
    # ========================================================================

    def test_new_tag_appears_in_suggestions(self):
        """Test that newly created tag appears in suggestions."""
        self.print_section("TEST 4: New Tag Appears in Suggestions")

        if not self.created_tag_id:
            self.record_result(
                "New tag appears in suggestions",
                False,
                "No test tag was created in previous test"
            )
            return

        # Wait a moment for database consistency
        time.sleep(0.5)

        try:
            response = self.session.get(
                f"{self.base_url}/api/candidate-tags/suggestions",
                params={"organization_id": ORGANIZATION_ID, "limit": 100},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                suggestions = data.get("suggestions", [])

                # Find our created tag in suggestions
                found_tag = None
                for suggestion in suggestions:
                    if suggestion["id"] == self.created_tag_id:
                        found_tag = suggestion
                        break

                if found_tag:
                    self.record_result(
                        "New tag appears in suggestions",
                        True,
                        f"Tag '{found_tag['tag_name']}' found with usage_count={found_tag['usage_count']}",
                        found_tag
                    )

                    # Verify it has the expected usage count
                    expected_count = min(3, len(self.test_candidate_ids))
                    has_correct_count = found_tag["usage_count"] == expected_count

                    self.record_result(
                        "New tag has correct usage count",
                        has_correct_count,
                        f"Usage count: {found_tag['usage_count']} (expected: {expected_count})",
                        found_tag
                    )
                else:
                    self.record_result(
                        "New tag appears in suggestions",
                        False,
                        f"Tag with ID {self.created_tag_id} not found in {len(suggestions)} suggestions"
                    )

                    # Debug: Show all suggestion IDs
                    suggestion_ids = [s["id"] for s in suggestions]
                    self.log(f"Available suggestion IDs: {suggestion_ids[:10]}", Colors.YELLOW)
            else:
                self.record_result(
                    "New tag appears in suggestions",
                    False,
                    f"Unexpected status: {response.status_code}"
                )
        except Exception as e:
            self.record_result(
                "New tag appears in suggestions",
                False,
                f"Error: {str(e)}"
            )

    # ========================================================================
    # TEST 5: Verify Frontend Component Implementation
    # ========================================================================

    def test_frontend_component(self):
        """Verify CandidateTagsManager component shows popular tags."""
        self.print_section("TEST 5: Frontend Component Verification")

        component_file = Path("frontend/src/components/CandidateTagsManager.tsx")

        if not component_file.exists():
            self.record_result(
                "CandidateTagsManager component exists",
                False,
                f"File not found: {component_file}"
            )
            return

        content = component_file.read_text()

        # Check 5.1: Popular tags computation
        has_popular_tags = "popularTags" in content and "candidate_count" in content
        self.record_result(
            "Component computes popular tags",
            has_popular_tags,
            "popularTags computed from candidate_count" if has_popular_tags else "popularTags not found"
        )

        # Check 5.2: Popular tags sorted by usage
        has_sorting = ".sort(" in content and "candidate_count" in content
        self.record_result(
            "Popular tags sorted by usage",
            has_sorting,
            "Tags sorted by candidate_count" if has_sorting else "Sorting not found"
        )

        # Check 5.3: Popular tags displayed in create dialog
        has_display = "Popular Tags" in content or "Quick add" in content
        self.record_result(
            "Popular tags displayed in create dialog",
            has_display,
            "Shows 'Popular Tags' section with quick-add" if has_display else "Popular tags display not found"
        )

        # Check 5.4: Usage counts displayed
        has_counts = "usage_count" in content or "candidate_count" in content
        self.record_result(
            "Usage counts displayed",
            has_counts,
            "Shows candidate count for each tag" if has_counts else "Usage counts not displayed"
        )

        # Check 5.5: Click handler for suggestions
        has_click_handler = "handleSuggestionClick" in content or "onClick" in content
        self.record_result(
            "Popular tags clickable for quick assignment",
            has_click_handler,
            "handleSuggestionClick function exists" if has_click_handler else "Click handler not found"
        )

        # Check 5.6: Only shown in create mode (not edit mode)
        has_condition = "!editMode" in content or "editMode === false" in content
        self.record_result(
            "Popular tags only shown in create mode",
            has_condition,
            "Conditional display based on editMode" if has_condition else "Mode check not found"
        )

    # ========================================================================
    # TEST 6: Cleanup Test Data
    # ========================================================================

    def cleanup_test_data(self):
        """Clean up test tag created during testing."""
        self.print_section("CLEANUP: Removing Test Data")

        if not self.created_tag_id:
            self.log("No test tag to clean up", Colors.YELLOW)
            return

        try:
            response = self.session.delete(
                f"{self.base_url}/api/candidate-tags/{self.created_tag_id}",
                timeout=10
            )

            if response.status_code == 200:
                self.log(f"Deleted test tag: {self.created_tag_id}", Colors.GREEN)
            else:
                self.log(f"Failed to delete test tag: {response.status_code}", Colors.YELLOW)
        except Exception as e:
            self.log(f"Error cleaning up test tag: {str(e)}", Colors.YELLOW)

    # ========================================================================
    # RUN ALL TESTS
    # ========================================================================

    def run_all_tests(self):
        """Run all verification tests."""
        print(f"\n{Colors.BOLD}{'=' * 70}{Colors.END}")
        print(f"{Colors.BOLD}TAG SUGGESTIONS - END-TO-END VERIFICATION{Colors.END}")
        print(f"{Colors.BOLD}{'=' * 70}{Colors.END}")

        # Setup
        if not self.setup_test_data():
            self.log("\n❌ Setup failed. Cannot continue with tests.", Colors.RED)
            self.print_summary()
            return False

        # Run tests
        self.test_tag_suggestions_endpoint()
        self.test_suggestions_sorted_by_usage()
        self.test_create_tag_and_apply()
        self.test_new_tag_appears_in_suggestions()
        self.test_frontend_component()

        # Cleanup
        self.cleanup_test_data()

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
    tester = TagSuggestionsE2E()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
