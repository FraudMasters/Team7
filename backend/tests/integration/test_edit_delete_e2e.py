"""
End-to-End Test for Comment Editing and Deletion with Time Restrictions

This script tests the complete flow of editing and deleting comments with time restrictions:

1. Create a new comment
2. Edit comment within 5 minutes - should succeed
3. Try to edit comment after 5 minutes - should fail
4. Delete comment - should succeed
5. Verify comment marked as deleted (soft delete)

Requirements:
- Backend server running on http://localhost:8000
- Database with test data (resumes and recruiters)
- Alembic migrations applied

Usage:
    cd backend
    python tests/integration/test_edit_delete_e2e.py
"""
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4
from datetime import datetime, timedelta, timezone

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import httpx
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from models.base import Base
from models.team_comment import TeamComment
from models.resume import Resume
from models.recruiter import Recruiter


# Configuration
API_BASE_URL = "http://localhost:8000"
DATABASE_URL = "postgresql+asyncpg://agenthr:agenthr@localhost:agenthr"


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def log(message: str, color: str = Colors.END) -> None:
    """Print a colored message to stdout."""
    print(f"{color}{message}{Colors.END}")


def log_step(step: str) -> None:
    """Print a test step header."""
    log(f"\n{'='*70}", Colors.BOLD)
    log(f"STEP: {step}", Colors.BLUE)
    log(f"{'='*70}\n", Colors.BOLD)


def log_success(message: str) -> None:
    """Print a success message."""
    log(f"✓ {message}", Colors.GREEN)


def log_error(message: str) -> None:
    """Print an error message."""
    log(f"✗ {message}", Colors.RED)


def log_info(message: str) -> None:
    """Print an info message."""
    log(f"  {message}", Colors.YELLOW)


class EditDeleteE2ETest:
    """End-to-end test suite for comment editing and deletion."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.engine = create_async_engine(DATABASE_URL, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.test_resume_id: Optional[str] = None
        self.test_author_id: Optional[str] = None
        self.test_comment_id: Optional[str] = None

    async def setup(self) -> bool:
        """Set up test data before running tests."""
        log_step("Setup - Creating Test Data")

        async with self.async_session() as session:
            try:
                # Check if we have existing test data
                result = await session.execute(
                    select(Resume).limit(1)
                )
                resume = result.scalar_one_or_none()

                if resume:
                    self.test_resume_id = str(resume.id)
                    log_success(f"Using existing resume: {self.test_resume_id}")
                else:
                    log_error("No resumes found in database. Please run database seed script.")
                    return False

                # Check if we have existing recruiters
                result = await session.execute(
                    select(Recruiter).limit(1)
                )
                recruiter = result.scalar_one_or_none()

                if recruiter:
                    self.test_author_id = str(recruiter.id)
                    log_success(f"Using existing recruiter: {self.test_author_id}")
                else:
                    log_error("No recruiters found in database. Please run database seed script.")
                    return False

                # Clean up any existing test comments
                await session.execute(
                    text("DELETE FROM team_comments WHERE content LIKE 'Edit/Delete Test:%'")
                )
                await session.commit()
                log_success("Cleaned up previous test comments")

                return True

            except Exception as e:
                log_error(f"Setup failed: {str(e)}")
                return False

    async def test_1_create_comment(self) -> bool:
        """Test 1: Create a new comment."""
        log_step("Test 1: Create New Comment")

        comment_data = {
            "resume_id": self.test_resume_id,
            "author_id": self.test_author_id,
            "content": "Edit/Delete Test: This is a test comment for edit/delete verification",
            "parent_comment_id": None,
            "is_resolved": False
        }

        log_info(f"Creating comment with data:")
        log_info(json.dumps(comment_data, indent=2))

        try:
            response = await self.client.post(
                f"{API_BASE_URL}/api/team-comments/",
                json=comment_data
            )

            if response.status_code == 201:
                comment = response.json()
                self.test_comment_id = comment.get("id")
                log_success(f"Comment created successfully: {self.test_comment_id}")
                log_info(f"Created at: {comment.get('created_at')}")
                log_info(f"Edits count: {comment.get('edits_count')}")
                return True
            else:
                log_error(f"Failed to create comment: {response.status_code}")
                log_info(f"Response: {response.text}")
                return False

        except Exception as e:
            log_error(f"Error creating comment: {str(e)}")
            return False

    async def test_2_edit_within_window(self) -> bool:
        """Test 2: Edit comment within 5 minutes (should succeed)."""
        log_step("Test 2: Edit Comment Within 5-Minute Window")

        update_data = {
            "content": "Edit/Delete Test: Updated content within time window"
        }

        log_info(f"Updating comment immediately (within 5-minute window)")
        log_info(json.dumps(update_data, indent=2))

        try:
            response = await self.client.put(
                f"{API_BASE_URL}/api/team-comments/{self.test_comment_id}",
                json=update_data
            )

            if response.status_code == 200:
                updated_comment = response.json()
                log_success("Comment updated successfully (within time window)")
                log_info(f"New content: {updated_comment.get('content')}")
                log_info(f"Edits count: {updated_comment.get('edits_count')}")

                # Verify edits_count was incremented
                if updated_comment.get('edits_count') != 1:
                    log_error(f"Expected edits_count=1, got {updated_comment.get('edits_count')}")
                    return False

                log_success("Edits count correctly incremented to 1")
                return True
            else:
                log_error(f"Failed to update comment: {response.status_code}")
                log_info(f"Response: {response.text}")
                return False

        except Exception as e:
            log_error(f"Error updating comment: {str(e)}")
            return False

    async def test_3_edit_after_window(self) -> bool:
        """Test 3: Try to edit comment after 5 minutes (should fail)."""
        log_step("Test 3: Edit Comment After 5-Minute Window (Should Fail)")

        # Manually update the comment's created_at timestamp in database
        async with self.async_session() as session:
            try:
                # Set created_at to 6 minutes ago
                old_timestamp = datetime.now(timezone.utc) - timedelta(minutes=6)
                await session.execute(
                    update(TeamComment)
                    .where(TeamComment.id == uuid4(self.test_comment_id))
                    .values(created_at=old_timestamp, updated_at=old_timestamp)
                )
                await session.commit()
                log_success("Set comment created_at to 6 minutes ago in database")
            except Exception as e:
                log_error(f"Failed to update timestamp: {str(e)}")
                return False

        update_data = {
            "content": "Edit/Delete Test: This edit should fail"
        }

        log_info(f"Attempting to update comment that is 6 minutes old")

        try:
            response = await self.client.put(
                f"{API_BASE_URL}/api/team-comments/{self.test_comment_id}",
                json=update_data
            )

            if response.status_code == 403:
                log_success("Edit correctly rejected (403 Forbidden)")
                error_detail = response.json()
                log_info(f"Error message: {error_detail.get('detail')}")

                # Verify error message mentions time restriction
                if "5 minutes" not in error_detail.get('detail', '').lower():
                    log_error("Error message doesn't mention 5-minute restriction")
                    return False

                log_success("Error message correctly mentions 5-minute restriction")
                return True
            else:
                log_error(f"Expected 403, got {response.status_code}")
                log_info(f"Response: {response.text}")
                return False

        except Exception as e:
            log_error(f"Error testing edit restriction: {str(e)}")
            return False

    async def test_4_resolve_status_no_restriction(self) -> bool:
        """Test 4: Verify resolved status can be changed regardless of time."""
        log_step("Test 4: Change Resolved Status (Should Work Despite Time)")

        resolve_data = {
            "is_resolved": True
        }

        log_info(f"Changing resolved status to True (comment is still 6 minutes old)")

        try:
            response = await self.client.put(
                f"{API_BASE_URL}/api/team-comments/{self.test_comment_id}",
                json=resolve_data
            )

            if response.status_code == 200:
                updated_comment = response.json()
                log_success("Resolved status updated successfully")
                log_info(f"is_resolved: {updated_comment.get('is_resolved')}")

                # Verify edits_count was NOT incremented (only content changes increment it)
                if updated_comment.get('edits_count') != 1:
                    log_error(f"Expected edits_count to remain 1, got {updated_comment.get('edits_count')}")
                    return False

                log_success("Edits count correctly remains at 1 (no content change)")
                return True
            else:
                log_error(f"Failed to update resolved status: {response.status_code}")
                return False

        except Exception as e:
            log_error(f"Error updating resolved status: {str(e)}")
            return False

    async def test_5_delete_comment(self) -> bool:
        """Test 5: Delete comment (soft delete)."""
        log_step("Test 5: Delete Comment (Soft Delete)")

        log_info(f"Deleting comment: {self.test_comment_id}")

        try:
            response = await self.client.delete(
                f"{API_BASE_URL}/api/team-comments/{self.test_comment_id}"
            )

            if response.status_code == 200:
                delete_data = response.json()
                log_success("Comment deleted successfully")
                log_info(f"Message: {delete_data.get('message')}")
                log_info(f"ID: {delete_data.get('id')}")
                return True
            else:
                log_error(f"Failed to delete comment: {response.status_code}")
                return False

        except Exception as e:
            log_error(f"Error deleting comment: {str(e)}")
            return False

    async def test_6_verify_soft_delete(self) -> bool:
        """Test 6: Verify comment is marked as deleted but preserved in database."""
        log_step("Test 6: Verify Soft Delete in Database")

        async with self.async_session() as session:
            try:
                # Get the deleted comment from database
                result = await session.execute(
                    select(TeamComment).where(TeamComment.id == uuid4(self.test_comment_id))
                )
                comment = result.scalar_one_or_none()

                if not comment:
                    log_error("Comment not found in database (should be preserved)")
                    return False

                log_success("Comment found in database (soft delete worked)")

                # Verify is_deleted flag
                if not comment.is_deleted:
                    log_error("is_deleted flag is not set to True")
                    return False

                log_success("is_deleted flag correctly set to True")

                # Verify content is preserved
                if "Updated content within time window" not in comment.content:
                    log_error(f"Content not preserved correctly: {comment.content}")
                    return False

                log_success("Content preserved in database")
                log_info(f"Content: {comment.content}")
                log_info(f"is_deleted: {comment.is_deleted}")
                log_info(f"edits_count: {comment.edits_count}")

                return True

            except Exception as e:
                log_error(f"Error verifying soft delete: {str(e)}")
                return False

    async def test_7_verify_not_in_default_list(self) -> bool:
        """Test 7: Verify deleted comment doesn't appear in default list."""
        log_step("Test 7: Verify Deleted Comment Not in Default List")

        try:
            response = await self.client.get(
                f"{API_BASE_URL}/api/team-comments/",
                params={"resume_id": self.test_resume_id}
            )

            if response.status_code == 200:
                comments_data = response.json()
                comments = comments_data.get("comments", [])

                log_success(f"Retrieved {len(comments)} comments")

                # Check if our deleted comment is in the list
                found_deleted = any(c.get("id") == self.test_comment_id for c in comments)

                if found_deleted:
                    log_error("Deleted comment appears in default list (should be hidden)")
                    return False

                log_success("Deleted comment correctly hidden from default list")
                return True
            else:
                log_error(f"Failed to list comments: {response.status_code}")
                return False

        except Exception as e:
            log_error(f"Error listing comments: {str(e)}")
            return False

    async def test_8_verify_visible_with_flag(self) -> bool:
        """Test 8: Verify deleted comment appears when include_deleted=True."""
        log_step("Test 8: Verify Deleted Comment Visible with Flag")

        try:
            response = await self.client.get(
                f"{API_BASE_URL}/api/team-comments/",
                params={
                    "resume_id": self.test_resume_id,
                    "include_deleted": True
                }
            )

            if response.status_code == 200:
                comments_data = response.json()
                comments = comments_data.get("comments", [])

                log_success(f"Retrieved {len(comments)} comments with include_deleted=True")

                # Check if our deleted comment is in the list
                found_deleted = None
                for c in comments:
                    if c.get("id") == self.test_comment_id:
                        found_deleted = c
                        break

                if not found_deleted:
                    log_error("Deleted comment not found even with include_deleted=True")
                    return False

                log_success("Deleted comment found with include_deleted=True")

                # Verify it's marked as deleted
                if not found_deleted.get("is_deleted"):
                    log_error("Comment is not marked as deleted in response")
                    return False

                log_success("Comment correctly marked as deleted in response")
                return True
            else:
                log_error(f"Failed to list comments: {response.status_code}")
                return False

        except Exception as e:
            log_error(f"Error listing comments: {str(e)}")
            return False

    async def test_9_get_deleted_comment_by_id(self) -> bool:
        """Test 9: Verify deleted comment can still be retrieved by ID."""
        log_step("Test 9: Get Deleted Comment by ID")

        try:
            response = await self.client.get(
                f"{API_BASE_URL}/api/team-comments/{self.test_comment_id}"
            )

            if response.status_code == 200:
                comment = response.json()
                log_success("Deleted comment retrieved by ID")
                log_info(f"Content: {comment.get('content')}")
                log_info(f"is_deleted: {comment.get('is_deleted')}")

                # Verify it's marked as deleted
                if not comment.get("is_deleted"):
                    log_error("Comment not marked as deleted in response")
                    return False

                log_success("Comment correctly marked as deleted")
                return True
            else:
                log_error(f"Failed to get deleted comment: {response.status_code}")
                return False

        except Exception as e:
            log_error(f"Error getting deleted comment: {str(e)}")
            return False

    async def cleanup(self) -> None:
        """Clean up test data after running tests."""
        log_step("Cleanup - Removing Test Data")

        async with self.async_session() as session:
            try:
                # Delete test comments
                await session.execute(
                    text("DELETE FROM team_comments WHERE content LIKE 'Edit/Delete Test:%'")
                )
                await session.commit()
                log_success("Test comments removed from database")
            except Exception as e:
                log_error(f"Cleanup failed: {str(e)}")

    async def run_all_tests(self) -> bool:
        """Run all end-to-end tests."""
        log("\n" + "="*70, Colors.BOLD)
        log("COMMENT EDIT/DELETE RESTRICTIONS - END-TO-END TEST", Colors.BOLD)
        log("="*70 + "\n", Colors.BOLD)

        # Setup
        if not await self.setup():
            log_error("Setup failed. Aborting tests.")
            return False

        # Run tests
        tests = [
            ("Create Comment", self.test_1_create_comment),
            ("Edit Within 5-Minute Window", self.test_2_edit_within_window),
            ("Edit After 5-Minute Window (Should Fail)", self.test_3_edit_after_window),
            ("Change Resolved Status (No Time Restriction)", self.test_4_resolve_status_no_restriction),
            ("Delete Comment (Soft Delete)", self.test_5_delete_comment),
            ("Verify Soft Delete in Database", self.test_6_verify_soft_delete),
            ("Verify Not in Default List", self.test_7_verify_not_in_default_list),
            ("Verify Visible with include_deleted Flag", self.test_8_verify_visible_with_flag),
            ("Get Deleted Comment by ID", self.test_9_get_deleted_comment_by_id),
        ]

        results = []
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results.append((test_name, result))
            except Exception as e:
                log_error(f"Test '{test_name}' crashed: {str(e)}")
                results.append((test_name, False))

        # Cleanup
        await self.cleanup()

        # Print summary
        log_step("Test Summary")

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = "PASSED" if result else "FAILED"
            color = Colors.GREEN if result else Colors.RED
            log(f"{status}: {test_name}", color)

        log(f"\nTotal: {passed}/{total} tests passed", Colors.BOLD)

        if passed == total:
            log("\n✓ All tests passed!", Colors.GREEN)
            return True
        else:
            log(f"\n✗ {total - passed} test(s) failed", Colors.RED)
            return False

    async def close(self) -> None:
        """Close resources."""
        await self.client.aclose()
        await self.engine.dispose()


async def main() -> int:
    """Main entry point for the test runner."""
    test_suite = EditDeleteE2ETest()

    try:
        success = await test_suite.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        log("\n\nTests interrupted by user", Colors.YELLOW)
        return 130
    except Exception as e:
        log(f"\n\nFatal error: {str(e)}", Colors.RED)
        return 1
    finally:
        await test_suite.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
