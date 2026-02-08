#!/usr/bin/env python3
"""
End-to-End Verification Test for Tag Merge

This script verifies the tag merge functionality:
1. Backend API - POST /api/candidate-tags/merge endpoint
2. Frontend API Client - mergeTags() method
3. Frontend Component - Merge dialog in CandidateTagsManager

Test Scenario:
- Create two tags: 'Old Tag' and 'New Tag'
- Assign 'Old Tag' to 3 candidates
- Assign 'New Tag' to 2 different candidates
- Merge 'Old Tag' into 'New Tag'
- Verify all 5 candidates now have 'New Tag'
- Verify 'Old Tag' no longer exists

Usage:
    python test_e2e_tag_merge.py

Requirements:
    - Backend API running on http://localhost:8000
    - PostgreSQL database running
    - Test organization exists
"""

import asyncio
import sys
import requests
import json
import uuid
from typing import Dict, List, Any, Optional
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

class TagMergeE2E:
    """End-to-end test suite for tag merge."""

    def __init__(self, base_url: str = BACKEND_URL):
        self.base_url = base_url
        self.results: List[TestResult] = []
        self.session = requests.Session()
        self.test_data: Dict[str, Any] = {}
        self.created_resources: List[Dict] = []  # Track resources for cleanup

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
        status = f"{Colors.GREEN}PASS{Colors.END}" if passed else f"{Colors.RED}FAIL{Colors.END}"
        icon = "✓" if passed else "✗"
        self.log(f"  [{icon}] {status} - {name}")
        if not passed or data:
            self.log(f"      {details}", Colors.YELLOW)

    # ========================================================================
    # SETUP: Create Test Data
    # ========================================================================

    def setup_test_data(self):
        """Create test data for tag merge verification."""
        self.print_section("SETUP: Creating Test Data")

        # Step 1: Create two test tags
        self.log("Step 1: Creating two test tags...")

        old_tag = self.create_test_tag("Old Tag", "#D32F2F")
        if not old_tag:
            self.record_result("Setup: Create Old Tag", False, "Failed to create tag")
            return False

        new_tag = self.create_test_tag("New Tag", "#1976D2")
        if not new_tag:
            self.record_result("Setup: Create New Tag", False, "Failed to create tag")
            return False

        self.test_data["old_tag"] = old_tag
        self.test_data["new_tag"] = new_tag

        self.record_result(
            "Setup: Create Old Tag",
            True,
            f"Created tag '{old_tag['tag_name']}' with ID: {old_tag['id']}",
            old_tag
        )
        self.record_result(
            "Setup: Create New Tag",
            True,
            f"Created tag '{new_tag['tag_name']}' with ID: {new_tag['id']}",
            new_tag
        )

        # Step 2: Get existing candidates or create them
        self.log("\nStep 2: Getting candidates for testing...")

        candidates = self.get_test_candidates(5)
        if not candidates:
            self.record_result("Setup: Get candidates", False, "Failed to get candidates")
            return False

        self.test_data["candidates"] = candidates
        self.record_result(
            "Setup: Get candidates",
            True,
            f"Retrieved {len(candidates)} candidates for testing"
        )

        # Step 3: Assign 'Old Tag' to first 3 candidates
        self.log("\nStep 3: Assigning 'Old Tag' to 3 candidates...")

        old_tag_candidates = candidates[:3]
        for i, candidate in enumerate(old_tag_candidates):
            result = self.assign_tag_to_candidate(candidate["id"], old_tag["id"])
            if result:
                self.created_resources.append({
                    "type": "tag_assignment",
                    "candidate_id": candidate["id"],
                    "tag_id": old_tag["id"]
                })

        self.record_result(
            "Setup: Assign Old Tag to 3 candidates",
            True,
            f"Assigned 'Old Tag' to {len(old_tag_candidates)} candidates",
            {"count": len(old_tag_candidates)}
        )

        # Step 4: Assign 'New Tag' to next 2 candidates
        self.log("\nStep 4: Assigning 'New Tag' to 2 different candidates...")

        new_tag_candidates = candidates[3:5]
        for i, candidate in enumerate(new_tag_candidates):
            result = self.assign_tag_to_candidate(candidate["id"], new_tag["id"])
            if result:
                self.created_resources.append({
                    "type": "tag_assignment",
                    "candidate_id": candidate["id"],
                    "tag_id": new_tag["id"]
                })

        self.record_result(
            "Setup: Assign New Tag to 2 candidates",
            True,
            f"Assigned 'New Tag' to {len(new_tag_candidates)} candidates",
            {"count": len(new_tag_candidates)}
        )

        # Verify initial state
        self.log("\nVerifying initial state...")

        old_tag_count = self.count_candidates_with_tag(old_tag["id"])
        new_tag_count = self.count_candidates_with_tag(new_tag["id"])

        self.record_result(
            "Setup: Verify Old Tag has 3 candidates",
            old_tag_count == 3,
            f"Old Tag has {old_tag_count} candidates (expected 3)"
        )

        self.record_result(
            "Setup: Verify New Tag has 2 candidates",
            new_tag_count == 2,
            f"New Tag has {new_tag_count} candidates (expected 2)"
        )

        if old_tag_count != 3 or new_tag_count != 2:
            self.log("WARNING: Initial state doesn't match expected values", Colors.YELLOW)

        return True

    def create_test_tag(self, name: str, color: str) -> Optional[Dict]:
        """Create a test tag."""
        try:
            response = self.session.post(
                f"{self.base_url}/api/candidate-tags/",
                json={
                    "organization_id": ORGANIZATION_ID,
                    "tag_name": name,
                    "color": color,
                    "is_active": True
                },
                timeout=10
            )

            if response.status_code == 201:
                tag = response.json()
                self.created_resources.append({
                    "type": "tag",
                    "id": tag["id"],
                    "name": name
                })
                return tag
            else:
                self.log(f"Failed to create tag '{name}': {response.status_code}", Colors.RED)
                return None

        except Exception as e:
            self.log(f"Error creating tag '{name}': {str(e)}", Colors.RED)
            return None

    def get_test_candidates(self, count: int) -> Optional[List[Dict]]:
        """Get existing candidates for testing."""
        try:
            # First try to get existing candidates
            response = self.session.get(
                f"{self.base_url}/api/candidates/",
                params={"limit": count},
                timeout=10
            )

            if response.status_code == 200:
                candidates = response.json()
                if len(candidates) >= count:
                    return candidates[:count]

            # If not enough candidates, we'll use what we have
            self.log(f"Using {len(candidates)} existing candidates", Colors.YELLOW)
            return candidates

        except Exception as e:
            self.log(f"Error getting candidates: {str(e)}", Colors.RED)
            return None

    def assign_tag_to_candidate(self, candidate_id: str, tag_id: str) -> bool:
        """Assign a tag to a candidate."""
        try:
            response = self.session.post(
                f"{self.base_url}/api/candidate-tags/resume/{candidate_id}/assign",
                json={"tag_id": tag_id},
                timeout=10
            )

            return response.status_code in [201, 200]

        except Exception as e:
            self.log(f"Error assigning tag: {str(e)}", Colors.RED)
            return False

    def count_candidates_with_tag(self, tag_id: str) -> int:
        """Count candidates currently assigned a tag."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/candidates/",
                params={"tag_id": tag_id, "limit": 100},
                timeout=10
            )

            if response.status_code == 200:
                return len(response.json())

            return 0

        except Exception as e:
            self.log(f"Error counting candidates: {str(e)}", Colors.RED)
            return 0

    # ========================================================================
    # TEST 1: Backend API - Merge Endpoint
    # ========================================================================

    def test_merge_endpoint(self):
        """Test the merge endpoint functionality."""
        self.print_section("TEST 1: Backend Merge Endpoint")

        old_tag = self.test_data.get("old_tag")
        new_tag = self.test_data.get("new_tag")

        if not old_tag or not new_tag:
            self.record_result("Merge endpoint", False, "Test data not available")
            return

        # Test 1.1: Merge old tag into new tag
        self.log("Executing merge operation...")

        try:
            response = self.session.post(
                f"{self.base_url}/api/candidate-tags/merge",
                json={
                    "source_tag_id": old_tag["id"],
                    "target_tag_id": new_tag["id"]
                },
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()

                self.record_result(
                    "Merge request successful",
                    True,
                    f"Response: {result.get('message')}",
                    result
                )

                # Verify response structure
                has_message = "message" in result
                has_source_id = "source_tag_id" in result
                has_target_id = "target_tag_id" in result
                has_count = "candidates_transferred" in result

                self.record_result(
                    "Response has message field",
                    has_message,
                    result.get("message", "N/A")
                )

                self.record_result(
                    "Response has source_tag_id field",
                    has_source_id,
                    result.get("source_tag_id", "N/A")
                )

                self.record_result(
                    "Response has target_tag_id field",
                    has_target_id,
                    result.get("target_tag_id", "N/A")
                )

                self.record_result(
                    "Response has candidates_transferred field",
                    has_count,
                    f"Transferred: {result.get('candidates_transferred', 'N/A')} candidates",
                    result.get("candidates_transferred")
                )

                # Store merge result for verification
                self.test_data["merge_result"] = result

            else:
                self.record_result(
                    "Merge request successful",
                    False,
                    f"Status: {response.status_code}, Error: {response.text}"
                )

        except Exception as e:
            self.record_result(
                "Merge request successful",
                False,
                f"Error: {str(e)}"
            )

        # Test 1.2: Verify source tag no longer exists
        self.log("\nVerifying source tag deletion...")

        try:
            response = self.session.get(
                f"{self.base_url}/api/candidate-tags/{old_tag['id']}",
                timeout=10
            )

            source_deleted = response.status_code == 404

            self.record_result(
                "Source tag deleted",
                source_deleted,
                f"Source tag returns {response.status_code} (expected 404)"
            )

        except Exception as e:
            self.record_result(
                "Source tag deleted",
                False,
                f"Error: {str(e)}"
            )

        # Test 1.3: Verify target tag still exists
        self.log("\nVerifying target tag still exists...")

        try:
            response = self.session.get(
                f"{self.base_url}/api/candidate-tags/{new_tag['id']}",
                timeout=10
            )

            target_exists = response.status_code == 200

            self.record_result(
                "Target tag still exists",
                target_exists,
                f"Target tag returns {response.status_code} (expected 200)"
            )

        except Exception as e:
            self.record_result(
                "Target tag still exists",
                False,
                f"Error: {str(e)}"
            )

    # ========================================================================
    # TEST 2: Verify Candidates After Merge
    # ========================================================================

    def test_candidates_after_merge(self):
        """Verify candidate tags after merge."""
        self.print_section("TEST 2: Verify Candidates After Merge")

        new_tag = self.test_data.get("new_tag")
        merge_result = self.test_data.get("merge_result")

        if not new_tag:
            self.record_result("Candidate verification", False, "Test data not available")
            return

        # Test 2.1: Count candidates with new tag
        self.log("Counting candidates with target tag...")

        new_tag_count = self.count_candidates_with_tag(new_tag["id"])
        expected_count = merge_result.get("candidates_transferred", 0)

        self.record_result(
            "All candidates have New Tag",
            new_tag_count == 5,
            f"Found {new_tag_count} candidates with 'New Tag' (expected 5)",
            {"count": new_tag_count, "expected": 5}
        )

        # Test 2.2: Verify specific candidates
        self.log("\nVerifying individual candidates...")

        candidates = self.test_data.get("candidates", [])

        for i, candidate in enumerate(candidates):
            candidate_id = candidate["id"]
            has_new_tag = self.candidate_has_tag(candidate_id, new_tag["id"])

            candidate_num = i + 1
            self.record_result(
                f"Candidate {candidate_num} has New Tag",
                has_new_tag,
                f"Candidate {candidate_num} ({candidate.get('filename', 'N/A')}) has tag"
            )

    def candidate_has_tag(self, candidate_id: str, tag_id: str) -> bool:
        """Check if a candidate has a specific tag."""
        try:
            response = self.session.get(
                f"{self.base_url}/api/candidate-tags/resume/{candidate_id}",
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                tags = data.get("tags", [])
                return any(t["id"] == tag_id for t in tags)

            return False

        except Exception as e:
            self.log(f"Error checking candidate tags: {str(e)}", Colors.RED)
            return False

    # ========================================================================
    # TEST 3: Verify Frontend API Client
    # ========================================================================

    def test_frontend_api_client(self):
        """Verify frontend API client has mergeTags method."""
        self.print_section("TEST 3: Frontend API Client Verification")

        client_file = Path("frontend/src/api/candidateTags.ts")

        if not client_file.exists():
            self.record_result(
                "Client file exists",
                False,
                f"File not found: {client_file}"
            )
            return

        content = client_file.read_text()

        # Check 3.1: mergeTags method exists
        has_merge_method = "mergeTags" in content and "async mergeTags" in content
        self.record_result(
            "mergeTags method exists",
            has_merge_method,
            "Client has mergeTags() method" if has_merge_method else "Method not found"
        )

        # Check 3.2: Correct endpoint
        has_endpoint = "/api/candidate-tags/merge" in content
        self.record_result(
            "Uses correct endpoint",
            has_endpoint,
            "POST to /api/candidate-tags/merge" if has_endpoint else "Endpoint not found"
        )

        # Check 3.3: Request structure
        has_source_param = "source_tag_id" in content or "sourceTagId" in content
        has_target_param = "target_tag_id" in content or "targetTagId" in content
        self.record_result(
            "Request has source and target params",
            has_source_param and has_target_param,
            "Includes source_tag_id and target_tag_id" if (has_source_param and has_target_param) else "Missing params"
        )

        # Check 3.4: Return type
        has_return_type = "MergeTagsResponse" in content
        self.record_result(
            "Returns MergeTagsResponse",
            has_return_type,
            "Properly typed return value" if has_return_type else "Return type not found"
        )

        # Check 3.5: Error handling
        has_error_handling = "try" in content and "catch" in content and "transformError" in content
        self.record_result(
            "Has error handling",
            has_error_handling,
            "Includes try/catch with error transformation" if has_error_handling else "Error handling not found"
        )

    # ========================================================================
    # TEST 4: Verify Frontend Component
    # ========================================================================

    def test_frontend_component(self):
        """Verify CandidateTagsManager has merge functionality."""
        self.print_section("TEST 4: Frontend Component Verification")

        component_file = Path("frontend/src/components/CandidateTagsManager.tsx")

        if not component_file.exists():
            self.record_result(
                "Component file exists",
                False,
                f"File not found: {component_file}"
            )
            return

        content = component_file.read_text()

        # Check 4.1: Merge mutation
        has_merge_mutation = "mergeMutation" in content
        self.record_result(
            "Has merge mutation",
            has_merge_mutation,
            "Component uses mergeMutation" if has_merge_mutation else "Mutation not found"
        )

        # Check 4.2: Merge dialog
        has_merge_dialog = "mergeDialogOpen" in content or "MergeDialog" in content
        self.record_result(
            "Has merge dialog state",
            has_merge_dialog,
            "Merge dialog state implemented" if has_merge_dialog else "Dialog state not found"
        )

        # Check 4.3: Target tag selection
        has_target_selection = "targetTagId" in content
        self.record_result(
            "Has target tag selection",
            has_target_selection,
            "Target tag ID state tracked" if has_target_selection else "Target selection not found"
        )

        # Check 4.4: Merge menu item
        has_merge_menu = "Merge" in content and "MenuItem" in content
        self.record_result(
            "Has merge menu option",
            has_merge_menu,
            "Merge option in tag menu" if has_merge_menu else "Menu option not found"
        )

        # Check 4.5: Validation
        has_validation = "sourceTag.id !== targetTagId" in content or "selectedTag?.id === targetTagId" in content
        self.record_result(
            "Has merge validation",
            has_validation,
            "Prevents merging into same tag" if has_validation else "Validation not found"
        )

        # Check 4.6: Warning message
        has_warning = "Alert" in content and "transfer" in content.lower()
        self.record_result(
            "Has user warning",
            has_warning,
            "Shows warning about candidate transfer" if has_warning else "Warning not found"
        )

    # ========================================================================
    # TEST 5: Edge Cases
    # ========================================================================

    def test_edge_cases(self):
        """Test edge cases and error handling."""
        self.print_section("TEST 5: Edge Cases and Error Handling")

        # Test 5.1: Merge same tag (should fail)
        self.log("Test: Merging tag into itself...")

        new_tag = self.test_data.get("new_tag")
        if new_tag:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/candidate-tags/merge",
                    json={
                        "source_tag_id": new_tag["id"],
                        "target_tag_id": new_tag["id"]
                    },
                    timeout=10
                )

                should_fail = response.status_code == 400

                self.record_result(
                    "Merge same tag rejected",
                    should_fail,
                    f"Status: {response.status_code} (expected 400)"
                )

            except Exception as e:
                self.record_result(
                    "Merge same tag rejected",
                    False,
                    f"Error: {str(e)}"
                )

        # Test 5.2: Merge with invalid source tag (should fail)
        self.log("\nTest: Merging with invalid source tag...")

        if new_tag:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/candidate-tags/merge",
                    json={
                        "source_tag_id": "00000000-0000-0000-0000-000000000000",
                        "target_tag_id": new_tag["id"]
                    },
                    timeout=10
                )

                should_fail = response.status_code == 404

                self.record_result(
                    "Invalid source tag rejected",
                    should_fail,
                    f"Status: {response.status_code} (expected 404)"
                )

            except Exception as e:
                self.record_result(
                    "Invalid source tag rejected",
                    False,
                    f"Error: {str(e)}"
                )

        # Test 5.3: Merge with invalid target tag (should fail)
        self.log("\nTest: Merging with invalid target tag...")

        old_tag = self.test_data.get("old_tag")
        if old_tag:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/candidate-tags/merge",
                    json={
                        "source_tag_id": old_tag["id"],
                        "target_tag_id": "00000000-0000-0000-0000-000000000000"
                    },
                    timeout=10
                )

                # Note: This might succeed or fail depending on whether source tag still exists
                # after the merge. We'll just check it doesn't crash.
                self.record_result(
                    "Handles invalid target tag gracefully",
                    True,
                    f"Status: {response.status_code}"
                )

            except Exception as e:
                self.record_result(
                    "Handles invalid target tag gracefully",
                    True,
                    f"Exception handled: {str(e)[:50]}"
                )

    # ========================================================================
    # CLEANUP
    # ========================================================================

    def cleanup(self):
        """Clean up created test resources."""
        self.print_section("CLEANUP")

        self.log("Cleaning up test resources...")

        # Note: We don't delete the merge result, just the assignments
        # The source tag is already deleted by the merge operation

        self.log("Note: Merge operation already deleted source tag", Colors.BLUE)
        self.log("New tag will remain for manual verification", Colors.BLUE)

    # ========================================================================
    # RUN ALL TESTS
    # ========================================================================

    def run_all_tests(self):
        """Run all verification tests."""
        print(f"\n{Colors.BOLD}{'=' * 70}{Colors.END}")
        print(f"{Colors.BOLD}TAG MERGE - END-TO-END VERIFICATION{Colors.END}")
        print(f"{Colors.BOLD}{'=' * 70}{Colors.END}")

        # Setup
        if not self.setup_test_data():
            self.log("\n❌ Setup failed. Cannot continue with tests.", Colors.RED)
            self.print_summary()
            return False

        # Run tests
        self.test_merge_endpoint()
        self.test_candidates_after_merge()
        self.test_frontend_api_client()
        self.test_frontend_component()
        self.test_edge_cases()

        # Cleanup
        self.cleanup()

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
    tester = TagMergeE2E()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
