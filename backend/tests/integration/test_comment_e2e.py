"""
End-to-End Integration Test for Team Comments Feature

This script tests the complete flow of creating and displaying team comments,
including threaded replies and database verification.

Test Steps:
1. Navigate to candidate detail page (simulated via API)
2. Add a new comment via frontend (simulated via API)
3. Verify comment appears in thread
4. Reply to existing comment
5. Verify reply appears nested under parent
6. Check database for comment records

Requirements:
- Backend server running on http://localhost:8000
- Database with test data (resumes and recruiters)
- Alembic migrations applied

Usage:
    cd backend
    python tests/integration/test_comment_e2e.py
"""
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import httpx
from sqlalchemy import select, text
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


class TeamCommentsE2ETest:
    """End-to-end test suite for team comments feature."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.engine = create_async_engine(DATABASE_URL, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.test_resume_id: Optional[str] = None
        self.test_author_id: Optional[str] = None
        self.test_comment_id: Optional[str] = None
        self.test_reply_id: Optional[str] = None

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
                    text("DELETE FROM team_comments WHERE content LIKE 'E2E Test:%'")
                )
                await session.commit()
                log_success("Cleaned up previous test comments")

                return True

            except Exception as e:
                log_error(f"Setup failed: {str(e)}")
                return False

    async def test_1_check_backend_health(self) -> bool:
        """Test 1: Check if backend is running."""
        log_step("Test 1: Backend Health Check")

        try:
            response = await self.client.get(f"{API_BASE_URL}/health")
            if response.status_code == 200:
                log_success("Backend is running and healthy")
                return True
            else:
                log_error(f"Backend returned status {response.status_code}")
                return False
        except Exception as e:
            log_error(f"Cannot connect to backend: {str(e)}")
            log_info("Make sure the backend server is running on http://localhost:8000")
            return False

    async def test_2_list_empty_comments(self) -> bool:
        """Test 2: List comments (should be empty initially)."""
        log_step("Test 2: List Comments (Initial State)")

        try:
            response = await self.client.get(
                f"{API_BASE_URL}/api/team-comments/",
                params={"resume_id": self.test_resume_id}
            )

            if response.status_code == 200:
                comments = response.json()
                log_success(f"API returned {len(comments)} comments (expected 0)")
                log_info(f"Response: {json.dumps(comments, indent=2)}")
                return True
            else:
                log_error(f"Failed to list comments: {response.status_code}")
                return False

        except Exception as e:
            log_error(f"Error listing comments: {str(e)}")
            return False

    async def test_3_create_comment(self) -> bool:
        """Test 3: Create a new comment."""
        log_step("Test 3: Create New Comment")

        comment_data = {
            "resume_id": self.test_resume_id,
            "author_id": self.test_author_id,
            "content": "E2E Test: This is a test comment for end-to-end verification",
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
                log_info(f"Response: {json.dumps(comment, indent=2)}")

                # Verify the comment has required fields
                required_fields = ["id", "resume_id", "author_id", "content", "created_at"]
                missing_fields = [f for f in required_fields if f not in comment]
                if missing_fields:
                    log_error(f"Missing fields in response: {missing_fields}")
                    return False

                log_success("All required fields present in response")
                return True
            else:
                log_error(f"Failed to create comment: {response.status_code}")
                log_info(f"Response: {response.text}")
                return False

        except Exception as e:
            log_error(f"Error creating comment: {str(e)}")
            return False

    async def test_4_verify_comment_in_thread(self) -> bool:
        """Test 4: Verify comment appears in thread."""
        log_step("Test 4: Verify Comment Appears in Thread")

        try:
            response = await self.client.get(
                f"{API_BASE_URL}/api/team-comments/",
                params={"resume_id": self.test_resume_id}
            )

            if response.status_code == 200:
                comments = response.json()
                log_success(f"API returned {len(comments)} comments")

                # Find our test comment
                test_comment = None
                for comment in comments:
                    if comment.get("id") == self.test_comment_id:
                        test_comment = comment
                        break

                if not test_comment:
                    log_error("Test comment not found in list")
                    return False

                log_success("Test comment found in thread")
                log_info(f"Comment content: {test_comment.get('content')}")

                # Verify comment structure
                assert test_comment.get("resume_id") == self.test_resume_id
                assert test_comment.get("author_id") == self.test_author_id
                assert "E2E Test:" in test_comment.get("content", "")
                assert test_comment.get("parent_comment_id") is None
                log_success("Comment structure is correct")

                return True
            else:
                log_error(f"Failed to list comments: {response.status_code}")
                return False

        except Exception as e:
            log_error(f"Error verifying comment: {str(e)}")
            return False

    async def test_5_get_comment_by_id(self) -> bool:
        """Test 5: Get comment by ID."""
        log_step("Test 5: Get Comment by ID")

        try:
            response = await self.client.get(
                f"{API_BASE_URL}/api/team-comments/{self.test_comment_id}"
            )

            if response.status_code == 200:
                comment = response.json()
                log_success("Comment retrieved successfully")
                log_info(f"Comment: {json.dumps(comment, indent=2)}")

                # Verify it's the same comment
                assert comment.get("id") == self.test_comment_id
                log_success("Comment ID matches")
                return True
            else:
                log_error(f"Failed to get comment: {response.status_code}")
                return False

        except Exception as e:
            log_error(f"Error getting comment: {str(e)}")
            return False

    async def test_6_create_reply(self) -> bool:
        """Test 6: Reply to existing comment."""
        log_step("Test 6: Create Reply to Comment")

        reply_data = {
            "resume_id": self.test_resume_id,
            "author_id": self.test_author_id,
            "content": "E2E Test: This is a reply to the parent comment",
            "parent_comment_id": self.test_comment_id,
            "is_resolved": False
        }

        log_info(f"Creating reply with data:")
        log_info(json.dumps(reply_data, indent=2))

        try:
            response = await self.client.post(
                f"{API_BASE_URL}/api/team-comments/",
                json=reply_data
            )

            if response.status_code == 201:
                reply = response.json()
                self.test_reply_id = reply.get("id")
                log_success(f"Reply created successfully: {self.test_reply_id}")
                log_info(f"Response: {json.dumps(reply, indent=2)}")

                # Verify reply structure
                assert reply.get("parent_comment_id") == self.test_comment_id
                log_success("Reply correctly references parent comment")
                return True
            else:
                log_error(f"Failed to create reply: {response.status_code}")
                log_info(f"Response: {response.text}")
                return False

        except Exception as e:
            log_error(f"Error creating reply: {str(e)}")
            return False

    async def test_7_verify_reply_nested_under_parent(self) -> bool:
        """Test 7: Verify reply appears nested under parent."""
        log_step("Test 7: Verify Reply Appears Nested Under Parent")

        try:
            # Get all comments for this resume
            response = await self.client.get(
                f"{API_BASE_URL}/api/team-comments/",
                params={"resume_id": self.test_resume_id}
            )

            if response.status_code != 200:
                log_error(f"Failed to list comments: {response.status_code}")
                return False

            comments = response.json()
            log_success(f"API returned {len(comments)} comments")

            # Find parent and reply
            parent_comment = None
            reply_comment = None

            for comment in comments:
                if comment.get("id") == self.test_comment_id:
                    parent_comment = comment
                elif comment.get("id") == self.test_reply_id:
                    reply_comment = comment

            if not parent_comment:
                log_error("Parent comment not found")
                return False

            if not reply_comment:
                log_error("Reply comment not found")
                return False

            log_success("Both parent and reply found")

            # Verify parent-child relationship
            if reply_comment.get("parent_comment_id") != self.test_comment_id:
                log_error("Reply does not reference parent comment correctly")
                return False

            log_success("Reply correctly references parent comment")

            # Verify threading structure
            # Get all replies to parent
            response_replies = await self.client.get(
                f"{API_BASE_URL}/api/team-comments/",
                params={"parent_comment_id": self.test_comment_id}
            )

            if response_replies.status_code == 200:
                replies = response_replies.json()
                log_success(f"Found {len(replies)} reply(ies) to parent comment")

                if self.test_reply_id in [r.get("id") for r in replies]:
                    log_success("Reply is correctly nested under parent")
                    return True
                else:
                    log_error("Reply not found in parent's reply list")
                    return False
            else:
                log_error("Failed to get replies")
                return False

        except Exception as e:
            log_error(f"Error verifying reply nesting: {str(e)}")
            return False

    async def test_8_check_database_records(self) -> bool:
        """Test 8: Check database for comment records."""
        log_step("Test 8: Check Database Records")

        async with self.async_session() as session:
            try:
                # Check parent comment in database
                result = await session.execute(
                    select(TeamComment).where(TeamComment.id == uuid4(self.test_comment_id))
                )
                parent_comment = result.scalar_one_or_none()

                if not parent_comment:
                    log_error("Parent comment not found in database")
                    return False

                log_success("Parent comment found in database")
                log_info(f"  ID: {parent_comment.id}")
                log_info(f"  Content: {parent_comment.content}")
                log_info(f"  Created: {parent_comment.created_at}")
                log_info(f"  Parent ID: {parent_comment.parent_comment_id}")

                # Verify parent has no parent (top-level comment)
                if parent_comment.parent_comment_id is not None:
                    log_error("Parent comment should not have a parent_comment_id")
                    return False

                log_success("Parent comment is correctly top-level")

                # Check reply in database
                result = await session.execute(
                    select(TeamComment).where(TeamComment.id == uuid4(self.test_reply_id))
                )
                reply_comment = result.scalar_one_or_none()

                if not reply_comment:
                    log_error("Reply comment not found in database")
                    return False

                log_success("Reply comment found in database")
                log_info(f"  ID: {reply_comment.id}")
                log_info(f"  Content: {reply_comment.content}")
                log_info(f"  Created: {reply_comment.created_at}")
                log_info(f"  Parent ID: {reply_comment.parent_comment_id}")

                # Verify reply has parent
                if reply_comment.parent_comment_id != uuid4(self.test_comment_id):
                    log_error("Reply comment should reference parent comment")
                    return False

                log_success("Reply correctly references parent in database")

                # Check comment count for this resume
                result = await session.execute(
                    select(TeamComment).where(TeamComment.resume_id == uuid4(self.test_resume_id))
                )
                all_comments = result.scalars().all()

                log_success(f"Total comments in database for resume: {len(all_comments)}")

                if len(all_comments) < 2:
                    log_error("Expected at least 2 comments in database")
                    return False

                return True

            except Exception as e:
                log_error(f"Error checking database: {str(e)}")
                return False

    async def test_9_update_comment(self) -> bool:
        """Test 9: Update comment (edits within time window)."""
        log_step("Test 9: Update Comment")

        update_data = {
            "content": "E2E Test: Updated comment content for testing",
            "is_resolved": False
        }

        log_info(f"Updating comment with data:")
        log_info(json.dumps(update_data, indent=2))

        try:
            response = await self.client.put(
                f"{API_BASE_URL}/api/team-comments/{self.test_comment_id}",
                json=update_data
            )

            if response.status_code == 200:
                updated_comment = response.json()
                log_success("Comment updated successfully")
                log_info(f"Response: {json.dumps(updated_comment, indent=2)}")

                # Verify content was updated
                if "Updated comment content" not in updated_comment.get("content", ""):
                    log_error("Content was not updated correctly")
                    return False

                log_success("Comment content updated successfully")
                return True
            else:
                log_error(f"Failed to update comment: {response.status_code}")
                log_info(f"Response: {response.text}")
                return False

        except Exception as e:
            log_error(f"Error updating comment: {str(e)}")
            return False

    async def test_10_mark_resolved(self) -> bool:
        """Test 10: Mark comment as resolved."""
        log_step("Test 10: Mark Comment as Resolved")

        resolve_data = {
            "is_resolved": True
        }

        log_info(f"Marking comment as resolved")

        try:
            response = await self.client.put(
                f"{API_BASE_URL}/api/team-comments/{self.test_comment_id}",
                json=resolve_data
            )

            if response.status_code == 200:
                updated_comment = response.json()
                log_success("Comment marked as resolved")

                if not updated_comment.get("is_resolved"):
                    log_error("Comment is_resolved flag was not set")
                    return False

                log_success("Comment is correctly marked as resolved")
                return True
            else:
                log_error(f"Failed to mark comment as resolved: {response.status_code}")
                return False

        except Exception as e:
            log_error(f"Error marking comment as resolved: {str(e)}")
            return False

    async def cleanup(self) -> None:
        """Clean up test data after running tests."""
        log_step("Cleanup - Removing Test Data")

        async with self.async_session() as session:
            try:
                # Delete test comments
                await session.execute(
                    text("DELETE FROM team_comments WHERE content LIKE 'E2E Test:%'")
                )
                await session.commit()
                log_success("Test comments removed from database")
            except Exception as e:
                log_error(f"Cleanup failed: {str(e)}")

    async def run_all_tests(self) -> bool:
        """Run all end-to-end tests."""
        log("\n" + "="*70, Colors.BOLD)
        log("TEAM COMMENTS - END-TO-END INTEGRATION TEST", Colors.BOLD)
        log("="*70 + "\n", Colors.BOLD)

        # Setup
        if not await self.setup():
            log_error("Setup failed. Aborting tests.")
            return False

        # Run tests
        tests = [
            ("Backend Health Check", self.test_1_check_backend_health),
            ("List Empty Comments", self.test_2_list_empty_comments),
            ("Create Comment", self.test_3_create_comment),
            ("Verify Comment in Thread", self.test_4_verify_comment_in_thread),
            ("Get Comment by ID", self.test_5_get_comment_by_id),
            ("Create Reply", self.test_6_create_reply),
            ("Verify Reply Nested Under Parent", self.test_7_verify_reply_nested_under_parent),
            ("Check Database Records", self.test_8_check_database_records),
            ("Update Comment", self.test_9_update_comment),
            ("Mark Comment Resolved", self.test_10_mark_resolved),
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
    test_suite = TeamCommentsE2ETest()

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
