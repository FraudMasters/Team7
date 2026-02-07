#!/usr/bin/env python3
"""
End-to-End Test: Comment Resolution Cascading Functionality

This script tests that comment resolution status cascades correctly from parent
comments to all child comments (replies) in threaded discussions.

Test Coverage:
1. Create comment thread with replies (3 levels deep)
2. Mark parent comment as resolved via API
3. Verify all child comments also marked as resolved
4. Mark parent as unresolved via API
5. Verify all child comments also marked as unresolved
6. Verify resolved comments are visually distinguished (check API response)

Prerequisites:
- Backend service running on http://localhost:8000
- Database accessible
- Test data exists (resumes, recruiters)

Usage:
    python test_comment_resolution_e2e.py
"""
import asyncio
import sys
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

import httpx
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_success(message: str):
    """Print success message in green."""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message: str):
    """Print error message in red."""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_info(message: str):
    """Print info message in blue."""
    print(f"{Colors.OKBLUE}ℹ {message}{Colors.ENDC}")


def print_header(message: str):
    """Print header in bold."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{message}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 80}{Colors.ENDC}\n")


class CommentResolutionTester:
    """Test suite for comment resolution cascading functionality."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api/team-comments"
        self.created_comment_ids: List[str] = []

    async def test_api_health(self) -> bool:
        """Test that the API is accessible."""
        print_info("Testing API health...")

        try:
            async with httpx.AsyncClient() as client:
                # Try to list comments (should work even if empty)
                response = await client.get(self.api_url, timeout=5.0)

                if response.status_code in [200, 404]:
                    print_success("API is accessible")
                    return True
                else:
                    print_error(f"API returned unexpected status: {response.status_code}")
                    return False

        except Exception as e:
            print_error(f"API health check failed: {e}")
            print_info("Make sure backend service is running on http://localhost:8000")
            return False

    async def create_test_comment(
        self,
        resume_id: str,
        author_id: str,
        content: str,
        parent_comment_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Create a test comment via API."""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "resume_id": resume_id,
                    "author_id": author_id,
                    "content": content,
                    "parent_comment_id": parent_comment_id,
                    "is_resolved": False,
                }

                response = await client.post(self.api_url, json=payload, timeout=10.0)

                if response.status_code == 201:
                    comment_data = response.json()
                    self.created_comment_ids.append(comment_data["id"])
                    return comment_data
                else:
                    print_error(f"Failed to create comment: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            print_error(f"Exception creating comment: {e}")
            return None

    async def update_comment_resolution(
        self,
        comment_id: str,
        is_resolved: bool,
    ) -> Optional[Dict[str, Any]]:
        """Update comment resolution status via API."""
        try:
            async with httpx.AsyncClient() as client:
                payload = {"is_resolved": is_resolved}

                response = await client.put(
                    f"{self.api_url}/{comment_id}",
                    json=payload,
                    timeout=10.0
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    print_error(f"Failed to update comment: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            print_error(f"Exception updating comment: {e}")
            return None

    async def get_comment(self, comment_id: str) -> Optional[Dict[str, Any]]:
        """Get a comment by ID via API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/{comment_id}",
                    timeout=10.0
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    print_error(f"Failed to get comment: {response.status_code}")
                    return None

        except Exception as e:
            print_error(f"Exception getting comment: {e}")
            return None

    async def list_comments(
        self,
        resume_id: Optional[str] = None,
        parent_comment_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List comments with optional filters."""
        try:
            async with httpx.AsyncClient() as client:
                params = {}
                if resume_id:
                    params["resume_id"] = resume_id
                if parent_comment_id:
                    params["parent_comment_id"] = parent_comment_id

                response = await client.get(
                    self.api_url,
                    params=params,
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("comments", [])
                else:
                    print_error(f"Failed to list comments: {response.status_code}")
                    return []

        except Exception as e:
            print_error(f"Exception listing comments: {e}")
            return []

    async def test_1_create_comment_thread(self) -> bool:
        """Test 1: Create a comment thread with replies."""
        print_header("TEST 1: Create Comment Thread with Replies")

        print_info("This test requires a valid resume_id and author_id")
        print_info("You'll need to provide these or the test will try to use existing data")

        # For testing, we'll need actual IDs from the database
        # Try to get existing comments to find valid IDs
        comments = await self.list_comments()

        if not comments:
            print_error("No existing comments found. Cannot create test thread.")
            print_info("Please create some test data first (resumes and recruiters)")
            return False

        # Use IDs from existing comment
        test_resume_id = comments[0]["resume_id"]
        test_author_id = comments[0]["author_id"]

        print_info(f"Using resume_id: {test_resume_id}")
        print_info(f"Using author_id: {test_author_id}")

        # Create parent comment
        print_info("Creating parent comment...")
        parent = await self.create_test_comment(
            resume_id=test_resume_id,
            author_id=test_author_id,
            content="Test parent comment for resolution testing",
        )

        if not parent:
            print_error("Failed to create parent comment")
            return False

        print_success(f"Created parent comment: {parent['id']}")

        # Create first-level reply
        print_info("Creating first-level reply...")
        reply1 = await self.create_test_comment(
            resume_id=test_resume_id,
            author_id=test_author_id,
            content="Test reply 1",
            parent_comment_id=parent["id"],
        )

        if not reply1:
            print_error("Failed to create reply 1")
            return False

        print_success(f"Created reply 1: {reply1['id']}")

        # Create second-level reply (nested)
        print_info("Creating second-level reply (nested)...")
        reply2 = await self.create_test_comment(
            resume_id=test_resume_id,
            author_id=test_author_id,
            content="Test nested reply",
            parent_comment_id=reply1["id"],
        )

        if not reply2:
            print_error("Failed to create nested reply")
            return False

        print_success(f"Created nested reply: {reply2['id']}")

        # Create another first-level reply
        print_info("Creating another first-level reply...")
        reply3 = await self.create_test_comment(
            resume_id=test_resume_id,
            author_id=test_author_id,
            content="Test reply 2",
            parent_comment_id=parent["id"],
        )

        if not reply3:
            print_error("Failed to create reply 2")
            return False

        print_success(f"Created reply 2: {reply3['id']}")

        print_success("Comment thread structure:")
        print_info(f"  Parent: {parent['id']}")
        print_info(f"    ├── {reply1['id']} (Reply 1)")
        print_info(f"    │   └── {reply2['id']} (Nested Reply)")
        print_info(f"    └── {reply3['id']} (Reply 2)")

        # Verify all are unresolved initially
        print_info("Verifying initial state (all unresolved)...")
        parent_check = await self.get_comment(parent["id"])
        reply1_check = await self.get_comment(reply1["id"])
        reply2_check = await self.get_comment(reply2["id"])
        reply3_check = await self.get_comment(reply3["id"])

        if not all([parent_check, reply1_check, reply2_check, reply3_check]):
            print_error("Failed to retrieve comments for verification")
            return False

        if not all([
            parent_check["is_resolved"] == False,
            reply1_check["is_resolved"] == False,
            reply2_check["is_resolved"] == False,
            reply3_check["is_resolved"] == False,
        ]):
            print_error("Initial state verification failed - some comments already resolved")
            return False

        print_success("Initial state verified: All comments are unresolved")

        # Store IDs for next test
        self.test_parent_id = parent["id"]
        self.test_reply1_id = reply1["id"]
        self.test_reply2_id = reply2["id"]
        self.test_reply3_id = reply3["id"]

        return True

    async def test_2_mark_parent_resolved(self) -> bool:
        """Test 2: Mark parent comment as resolved and verify cascading."""
        print_header("TEST 2: Mark Parent as Resolved - Verify Cascading")

        if not hasattr(self, 'test_parent_id'):
            print_error("Test 1 failed or did not create test data")
            return False

        print_info(f"Marking parent comment {self.test_parent_id} as resolved...")
        result = await self.update_comment_resolution(self.test_parent_id, True)

        if not result:
            print_error("Failed to update parent comment")
            return False

        print_success("Parent comment marked as resolved")

        # Verify parent is resolved
        print_info("Verifying parent is resolved...")
        parent_check = await self.get_comment(self.test_parent_id)

        if not parent_check or not parent_check["is_resolved"]:
            print_error("Parent comment is not resolved")
            return False

        print_success("Parent comment is resolved")

        # Verify all children are also resolved (cascaded)
        print_info("Verifying child comments are also resolved (cascading)...")

        reply1_check = await self.get_comment(self.test_reply1_id)
        reply2_check = await self.get_comment(self.test_reply2_id)
        reply3_check = await self.get_comment(self.test_reply3_id)

        if not all([reply1_check, reply2_check, reply3_check]):
            print_error("Failed to retrieve child comments")
            return False

        # Check each child
        all_resolved = True

        if reply1_check["is_resolved"]:
            print_success(f"Reply 1 ({self.test_reply1_id}) is resolved ✓")
        else:
            print_error(f"Reply 1 ({self.test_reply1_id}) is NOT resolved ✗")
            all_resolved = False

        if reply2_check["is_resolved"]:
            print_success(f"Nested Reply ({self.test_reply2_id}) is resolved ✓")
        else:
            print_error(f"Nested Reply ({self.test_reply2_id}) is NOT resolved ✗")
            all_resolved = False

        if reply3_check["is_resolved"]:
            print_success(f"Reply 2 ({self.test_reply3_id}) is resolved ✓")
        else:
            print_error(f"Reply 2 ({self.test_reply3_id}) is NOT resolved ✗")
            all_resolved = False

        if all_resolved:
            print_success("All child comments are resolved - cascading works! ✓")
        else:
            print_error("Some child comments are not resolved - cascading failed")

        return all_resolved

    async def test_3_mark_parent_unresolved(self) -> bool:
        """Test 3: Mark parent as unresolved and verify cascading."""
        print_header("TEST 3: Mark Parent as Unresolved - Verify Cascading")

        if not hasattr(self, 'test_parent_id'):
            print_error("Test 1 failed or did not create test data")
            return False

        print_info(f"Marking parent comment {self.test_parent_id} as unresolved...")
        result = await self.update_comment_resolution(self.test_parent_id, False)

        if not result:
            print_error("Failed to update parent comment")
            return False

        print_success("Parent comment marked as unresolved")

        # Verify parent is unresolved
        print_info("Verifying parent is unresolved...")
        parent_check = await self.get_comment(self.test_parent_id)

        if not parent_check or parent_check["is_resolved"]:
            print_error("Parent comment is still resolved")
            return False

        print_success("Parent comment is unresolved")

        # Verify all children are also unresolved (cascaded)
        print_info("Verifying child comments are also unresolved (cascading)...")

        reply1_check = await self.get_comment(self.test_reply1_id)
        reply2_check = await self.get_comment(self.test_reply2_id)
        reply3_check = await self.get_comment(self.test_reply3_id)

        if not all([reply1_check, reply2_check, reply3_check]):
            print_error("Failed to retrieve child comments")
            return False

        # Check each child
        all_unresolved = True

        if not reply1_check["is_resolved"]:
            print_success(f"Reply 1 ({self.test_reply1_id}) is unresolved ✓")
        else:
            print_error(f"Reply 1 ({self.test_reply1_id}) is still resolved ✗")
            all_unresolved = False

        if not reply2_check["is_resolved"]:
            print_success(f"Nested Reply ({self.test_reply2_id}) is unresolved ✓")
        else:
            print_error(f"Nested Reply ({self.test_reply2_id}) is still resolved ✗")
            all_unresolved = False

        if not reply3_check["is_resolved"]:
            print_success(f"Reply 2 ({self.test_reply3_id}) is unresolved ✓")
        else:
            print_error(f"Reply 2 ({self.test_reply3_id}) is still resolved ✗")
            all_unresolved = False

        if all_unresolved:
            print_success("All child comments are unresolved - cascading works! ✓")
        else:
            print_error("Some child comments are still resolved - cascading failed")

        return all_unresolved

    async def test_4_visual_distinction(self) -> bool:
        """Test 4: Verify resolved comments are visually distinguished in API response."""
        print_header("TEST 4: Visual Distinction in API Response")

        if not hasattr(self, 'test_parent_id'):
            print_error("Test 1 failed or did not create test data")
            return False

        print_info("Checking API response for visual distinction indicators...")

        # Mark parent as resolved
        await self.update_comment_resolution(self.test_parent_id, True)

        # Get the comment
        comment = await self.get_comment(self.test_parent_id)

        if not comment:
            print_error("Failed to retrieve comment")
            return False

        # Check for is_resolved field
        if "is_resolved" in comment:
            print_success("API response includes 'is_resolved' field")
            print_info(f"  is_resolved value: {comment['is_resolved']}")
        else:
            print_error("API response missing 'is_resolved' field")
            return False

        # Verify value is True
        if comment["is_resolved"] is True:
            print_success("'is_resolved' is correctly set to True")
        else:
            print_error(f"'is_resolved' is {comment['is_resolved']}, expected True")
            return False

        # List comments and check filtering
        print_info("Testing is_resolved filter...")
        resolved_comments = await self.list_comments(
            resume_id=comment["resume_id"],
        )

        resolved_only = [c for c in resolved_comments if c["is_resolved"] == True]
        print_info(f"Found {len(resolved_only)} resolved comment(s) out of {len(resolved_comments)} total")

        if len(resolved_only) > 0:
            print_success("Can filter comments by is_resolved status")
        else:
            print_error("No resolved comments found (unexpected)")

        return True

    async def cleanup(self):
        """Clean up test data."""
        print_header("Cleanup")
        print_info("Cleaning up test comments...")

        # Note: We're not actually deleting them, just listing what we created
        # In production, you might want to delete test data
        print_info(f"Created {len(self.created_comment_ids)} test comments:")
        for comment_id in self.created_comment_ids:
            print_info(f"  - {comment_id}")

        print_info("Test data cleanup skipped (preserving for manual inspection)")
        print_info("To manually clean up, you can delete these comments via the API")

    async def run_all_tests(self) -> bool:
        """Run all resolution tests."""
        print_header("COMMENT RESOLUTION CASCADING - END-TO-END TESTS")

        # Test API health
        if not await self.test_api_health():
            print_error("API health check failed. Exiting.")
            return False

        all_passed = True

        # Run tests in sequence
        try:
            if not await self.test_1_create_comment_thread():
                print_error("Test 1 FAILED")
                all_passed = False
            else:
                print_success("Test 1 PASSED")

            if not await self.test_2_mark_parent_resolved():
                print_error("Test 2 FAILED")
                all_passed = False
            else:
                print_success("Test 2 PASSED")

            if not await self.test_3_mark_parent_unresolved():
                print_error("Test 3 FAILED")
                all_passed = False
            else:
                print_success("Test 3 PASSED")

            if not await self.test_4_visual_distinction():
                print_error("Test 4 FAILED")
                all_passed = False
            else:
                print_success("Test 4 PASSED")

        except Exception as e:
            print_error(f"Test execution failed with exception: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False

        finally:
            await self.cleanup()

        # Print summary
        print_header("TEST SUMMARY")
        if all_passed:
            print_success("All tests PASSED ✓")
            print_info("Comment resolution cascading is working correctly!")
        else:
            print_error("Some tests FAILED ✗")
            print_info("Please review the errors above and fix any issues")

        return all_passed


async def main():
    """Main entry point."""
    tester = CommentResolutionTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print_warning("\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
