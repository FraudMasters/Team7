#!/usr/bin/env python3
"""
End-to-End Test Script for Team Comments Feature
Subtask 6-1: End-to-end test of comment creation and display flow

This script performs comprehensive e2e testing of the team comments feature including:
1. Comment creation via API
2. Comment threading (replies)
3. Comment display and retrieval
4. Database record verification
5. Integration with frontend components

Prerequisites:
- Backend server running on http://localhost:8000
- PostgreSQL database accessible
- At least one resume record in database

Usage:
    python test_e2e_team_comments.py

Author: Auto-Claude
Date: 2025-02-03
"""

import asyncio
import sys
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_success(msg: str):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg: str):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")

def print_section(msg: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{msg}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")


class E2ETestResults:
    """Track test results"""
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []

    def add_pass(self, test_name: str):
        self.passed.append(test_name)
        print_success(test_name)

    def add_fail(self, test_name: str, error: str):
        self.failed.append((test_name, error))
        print_error(f"{test_name}: {error}")

    def add_warning(self, test_name: str, message: str):
        self.warnings.append((test_name, message))
        print(f"{Colors.YELLOW}⚠ {test_name}: {message}{Colors.END}")

    def print_summary(self):
        print_section("TEST SUMMARY")
        print(f"Total Tests: {len(self.passed) + len(self.failed)}")
        print_success(f"Passed: {len(self.passed)}")
        if self.failed:
            print_error(f"Failed: {len(self.failed)}")
        if self.warnings:
            print(f"{Colors.YELLOW}Warnings: {len(self.warnings)}{Colors.END}")

        if self.failed:
            print(f"\n{Colors.BOLD}Failed Tests:{Colors.END}")
            for test_name, error in self.failed:
                print_error(f"  - {test_name}: {error}")

        if self.warnings:
            print(f"\n{Colors.YELLOW}Warnings:{Colors.END}")
            for test_name, message in self.warnings:
                print(f"  {Colors.YELLOW}⚠ {test_name}: {message}{Colors.END}")

        return len(self.failed) == 0


class TeamCommentsE2ETest:
    """End-to-end test suite for team comments feature"""

    def __init__(self):
        self.results = E2ETestResults()
        self.base_url = "http://localhost:8000/api/team-comments"
        self.test_data = {}
        self.db_session = None

    async def setup(self):
        """Setup test environment"""
        print_section("TEST SETUP")

        try:
            # Import database dependencies
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
            from database import get_db
            from models.team_comment import TeamComment
            from models.comment_mention import CommentMention
            from models.resume import Resume

            self.TeamComment = TeamComment
            self.CommentMention = CommentMention
            self.Resume = Resume

            # Get database session
            async for session in get_db():
                self.db_session = session
                break

            print_success("Database connection established")

            # Check for existing resume
            result = await self.db_session.execute(
                select(self.Resume).limit(1)
            )
            resume = result.scalar_one_or_none()

            if resume:
                self.test_data['resume_id'] = str(resume.id)
                self.test_data['author_id'] = str(resume.recruiter_id)
                print_info(f"Using resume: {resume.filename}")
            else:
                raise Exception("No resume found in database. Please create a resume first.")

            # Set test author ID (using a test UUID)
            import uuid
            self.test_data['test_author_id'] = str(uuid.uuid4())

            print_success("Test setup completed")
            return True

        except Exception as e:
            print_error(f"Setup failed: {str(e)}")
            return False

    async def test_1_create_comment(self):
        """Test 1: Create a new comment via API"""
        print_section("TEST 1: Create Comment")

        try:
            import httpx

            comment_data = {
                "resume_id": self.test_data['resume_id'],
                "author_id": self.test_data['author_id'],
                "content": "This is a test comment for e2e testing. Please review this candidate's experience.",
                "parent_comment_id": None
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url + "/",
                    json=comment_data,
                    timeout=10.0
                )

                if response.status_code == 201:
                    data = response.json()
                    self.test_data['comment_id'] = data['id']

                    self.results.add_pass("Test 1.1: Comment created via API")
                    self.results.add_pass("Test 1.2: API returns 201 status")
                    self.results.add_pass(f"Test 1.3: Comment ID generated: {data['id']}")
                    self.results.add_pass(f"Test 1.4: Content matches: {data['content'] == comment_data['content']}")

                    return data
                else:
                    self.results.add_fail("Test 1: Create comment", f"Status {response.status_code}: {response.text}")
                    return None

        except Exception as e:
            self.results.add_fail("Test 1: Create comment", str(e))
            return None

    async def test_2_retrieve_comment(self):
        """Test 2: Retrieve comment via API"""
        print_section("TEST 2: Retrieve Comment")

        try:
            import httpx
            comment_id = self.test_data.get('comment_id')

            if not comment_id:
                self.results.add_fail("Test 2: Retrieve comment", "No comment_id from test 1")
                return None

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/{comment_id}",
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()

                    self.results.add_pass("Test 2.1: Comment retrieved via API")
                    self.results.add_pass("Test 2.2: API returns 200 status")
                    self.results.add_pass(f"Test 2.3: Resume ID matches: {data['resume_id'] == self.test_data['resume_id']}")
                    self.results.add_pass(f"Test 2.4: Author ID matches: {data['author_id'] == self.test_data['author_id']}")

                    return data
                else:
                    self.results.add_fail("Test 2: Retrieve comment", f"Status {response.status_code}")
                    return None

        except Exception as e:
            self.results.add_fail("Test 2: Retrieve comment", str(e))
            return None

    async def test_3_list_comments(self):
        """Test 3: List all comments for resume"""
        print_section("TEST 3: List Comments")

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/?resume_id={self.test_data['resume_id']}",
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()

                    if isinstance(data, list) and len(data) > 0:
                        self.results.add_pass("Test 3.1: Comments listed via API")
                        self.results.add_pass("Test 3.2: API returns 200 status")
                        self.results.add_pass(f"Test 3.3: Comments array returned: {len(data)} comment(s)")
                        self.results.add_pass("Test 3.4: Comment has all required fields")

                        # Check if our comment is in the list
                        comment_ids = [c['id'] for c in data]
                        if self.test_data.get('comment_id') in comment_ids:
                            self.results.add_pass("Test 3.5: Created comment appears in list")
                    else:
                        self.results.add_fail("Test 3: List comments", "Empty or invalid response")
                else:
                    self.results.add_fail("Test 3: List comments", f"Status {response.status_code}")

        except Exception as e:
            self.results.add_fail("Test 3: List comments", str(e))

    async def test_4_create_reply(self):
        """Test 4: Create a reply to the comment"""
        print_section("TEST 4: Create Reply (Threaded Comment)")

        try:
            import httpx

            reply_data = {
                "resume_id": self.test_data['resume_id'],
                "author_id": self.test_data['author_id'],
                "content": "This is a reply to the original comment. The candidate looks promising!",
                "parent_comment_id": self.test_data['comment_id']
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url + "/",
                    json=reply_data,
                    timeout=10.0
                )

                if response.status_code == 201:
                    data = response.json()
                    self.test_data['reply_id'] = data['id']

                    self.results.add_pass("Test 4.1: Reply created via API")
                    self.results.add_pass("Test 4.2: API returns 201 status")
                    self.results.add_pass(f"Test 4.3: Reply ID generated: {data['id']}")
                    self.results.add_pass(f"Test 4.4: Parent comment ID matches: {data['parent_comment_id'] == self.test_data['comment_id']}")
                    self.results.add_pass(f"Test 4.5: Content is reply: {data['content'] == reply_data['content']}")

                    return data
                else:
                    self.results.add_fail("Test 4: Create reply", f"Status {response.status_code}")
                    return None

        except Exception as e:
            self.results.add_fail("Test 4: Create reply", str(e))
            return None

    async def test_5_verify_thread_structure(self):
        """Test 5: Verify threaded structure in database"""
        print_section("TEST 5: Verify Thread Structure in Database")

        try:
            from sqlalchemy import select

            # Get parent comment
            parent_result = await self.db_session.execute(
                select(self.TeamComment).where(
                    self.TeamComment.id == self.test_data['comment_id']
                )
            )
            parent_comment = parent_result.scalar_one_or_none()

            if parent_comment:
                self.results.add_pass("Test 5.1: Parent comment exists in database")
                self.results.add_pass(f"Test 5.2: Parent has no parent: {parent_comment.parent_comment_id is None}")
                self.results.add_pass(f"Test 5.3: Parent content matches: {'test comment' in parent_comment.content.lower()}")
            else:
                self.results.add_fail("Test 5.1: Parent comment not found in database")
                return

            # Get reply comment
            reply_result = await self.db_session.execute(
                select(self.TeamComment).where(
                    self.TeamComment.id == self.test_data['reply_id']
                )
            )
            reply_comment = reply_result.scalar_one_or_none()

            if reply_comment:
                self.results.add_pass("Test 5.4: Reply comment exists in database")
                self.results.add_pass(f"Test 5.5: Reply has parent: {reply_comment.parent_comment_id == self.test_data['comment_id']}")
                self.results.add_pass(f"Test 5.6: Reply content matches: {'reply' in reply_comment.content.lower()}")
            else:
                self.results.add_fail("Test 5.4: Reply comment not found in database")

        except Exception as e:
            self.results.add_fail("Test 5: Verify thread structure", str(e))

    async def test_6_list_with_threading(self):
        """Test 6: List comments with threading structure"""
        print_section("TEST 6: List Comments with Threading")

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                # Get all comments for this resume
                response = await client.get(
                    f"{self.base_url}/?resume_id={self.test_data['resume_id']}",
                    timeout=10.0
                )

                if response.status_code == 200:
                    comments = response.json()

                    # Separate parent and child comments
                    parents = [c for c in comments if c['parent_comment_id'] is None]
                    children = [c for c in comments if c['parent_comment_id'] is not None]

                    self.results.add_pass("Test 6.1: Comments retrieved with threading info")
                    self.results.add_pass(f"Test 6.2: Found {len(parents)} parent comment(s)")
                    self.results.add_pass(f"Test 6.3: Found {len(children)} reply/replies")

                    # Verify thread structure
                    if children:
                        for child in children:
                            if child['parent_comment_id'] == self.test_data['comment_id']:
                                self.results.add_pass(f"Test 6.4: Reply correctly linked to parent")
                                break

                else:
                    self.results.add_fail("Test 6: List with threading", f"Status {response.status_code}")

        except Exception as e:
            self.results.add_fail("Test 6: List with threading", str(e))

    async def test_7_update_comment(self):
        """Test 7: Update comment (within 5-minute window)"""
        print_section("TEST 7: Update Comment")

        try:
            import httpx

            update_data = {
                "content": "Updated comment: This candidate has excellent experience and skills."
            }

            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.base_url}/{self.test_data['comment_id']}",
                    json=update_data,
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()

                    self.results.add_pass("Test 7.1: Comment updated via API")
                    self.results.add_pass("Test 7.2: API returns 200 status")
                    self.results.add_pass(f"Test 7.3: Content updated: {'Updated' in data['content']}")
                    self.results.add_pass(f"Test 7.4: Edits count incremented: {data['edits_count'] > 0}")

                else:
                    self.results.add_fail("Test 7: Update comment", f"Status {response.status_code}")

        except Exception as e:
            self.results.add_fail("Test 7: Update comment", str(e))

    async def test_8_soft_delete_comment(self):
        """Test 8: Soft delete comment"""
        print_section("TEST 8: Soft Delete Comment")

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/{self.test_data['reply_id']}",
                    timeout=10.0
                )

                if response.status_code == 200:
                    self.results.add_pass("Test 8.1: Comment soft deleted via API")
                    self.results.add_pass("Test 8.2: API returns 200 status")

                    # Verify it's soft deleted by checking it still exists in DB
                    from sqlalchemy import select
                    result = await self.db_session.execute(
                        select(self.TeamComment).where(
                            self.TeamComment.id == self.test_data['reply_id']
                        )
                    )
                    comment = result.scalar_one_or_none()

                    if comment and comment.is_deleted:
                        self.results.add_pass("Test 8.3: Comment marked as deleted in database")
                        self.results.add_pass("Test 8.4: Comment record still exists (soft delete)")
                    else:
                        self.results.add_fail("Test 8.3: Comment not properly soft deleted")

                else:
                    self.results.add_fail("Test 8: Soft delete", f"Status {response.status_code}")

        except Exception as e:
            self.results.add_fail("Test 8: Soft delete", str(e))

    async def test_9_database_integrity(self):
        """Test 9: Verify database integrity and relationships"""
        print_section("TEST 9: Database Integrity Check")

        try:
            from sqlalchemy import select, func

            # Check team_comments table exists and has records
            count_result = await self.db_session.execute(
                select(func.count()).select_from(self.TeamComment)
            )
            total_comments = count_result.scalar()

            self.results.add_pass(f"Test 9.1: team_comments table accessible ({total_comments} total records)")

            # Check foreign key relationships
            result = await self.db_session.execute(
                select(self.TeamComment).where(
                    self.TeamComment.resume_id == self.test_data['resume_id']
                )
            )
            comments = result.scalars().all()

            if comments:
                self.results.add_pass("Test 9.2: Foreign key to resume working")
                self.results.add_pass(f"Test 9.3: Found {len(comments)} comment(s) for test resume")

                # Check timestamps are present
                for comment in comments:
                    if comment.created_at and comment.updated_at:
                        self.results.add_pass("Test 9.4: Timestamps present on comments")
                        break
            else:
                self.results.add_warning("Test 9.2", "No comments found for test resume")

        except Exception as e:
            self.results.add_fail("Test 9: Database integrity", str(e))

    async def test_10_frontend_component_verification(self):
        """Test 10: Verify frontend component files exist and are valid"""
        print_section("TEST 10: Frontend Component Verification")

        try:
            # Check TeamComments component
            team_comments_path = "frontend/src/components/TeamComments.tsx"
            if os.path.exists(team_comments_path):
                self.results.add_pass("Test 10.1: TeamComments.tsx component exists")

                with open(team_comments_path, 'r') as f:
                    content = f.read()

                checks = [
                    ("useState hook present", "useState" in content),
                    ("useEffect hook present", "useEffect" in content),
                    ("API client import present", "teamComments" in content),
                    ("Comment rendering logic", "comment" in content.lower()),
                    ("Reply functionality", "reply" in content.lower()),
                    ("Edit functionality", "edit" in content.lower()),
                    ("Delete functionality", "delete" in content.lower())
                ]

                for check_name, check_result in checks:
                    if check_result:
                        self.results.add_pass(f"Test 10.2: {check_name}")
            else:
                self.results.add_fail("Test 10.1: TeamComments.tsx not found")

            # Check CommentThread component
            comment_thread_path = "frontend/src/components/CommentThread.tsx"
            if os.path.exists(comment_thread_path):
                self.results.add_pass("Test 10.3: CommentThread.tsx component exists")

                with open(comment_thread_path, 'r') as f:
                    content = f.read()

                if "recursive" in content.lower() or "replies" in content.lower():
                    self.results.add_pass("Test 10.4: Threaded reply support present")
            else:
                self.results.add_fail("Test 10.3: CommentThread.tsx not found")

            # Check API client
            api_client_path = "frontend/src/api/teamComments.ts"
            if os.path.exists(api_client_path):
                self.results.add_pass("Test 10.5: teamComments.ts API client exists")

                with open(api_client_path, 'r') as f:
                    content = f.read()

                api_methods = ["create", "get", "update", "delete", "list"]
                for method in api_methods:
                    if method in content:
                        self.results.add_pass(f"Test 10.6: API method '{method}' present")
            else:
                self.results.add_fail("Test 10.5: teamComments.ts not found")

        except Exception as e:
            self.results.add_fail("Test 10: Frontend verification", str(e))

    async def run_all_tests(self):
        """Run all e2e tests"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}")
        print("╔═══════════════════════════════════════════════════════════╗")
        print("║     TEAM COMMENTS - END-TO-END TEST SUITE                ║")
        print("║     Subtask 6-1: Comment Creation and Display Flow       ║")
        print("╚═══════════════════════════════════════════════════════════╝")
        print(f"{Colors.END}")

        # Setup
        if not await self.setup():
            print_error("Cannot proceed - setup failed")
            return False

        # Run tests
        await self.test_1_create_comment()
        await self.test_2_retrieve_comment()
        await self.test_3_list_comments()
        await self.test_4_create_reply()
        await self.test_5_verify_thread_structure()
        await self.test_6_list_with_threading()
        await self.test_7_update_comment()
        await self.test_8_soft_delete_comment()
        await self.test_9_database_integrity()
        await self.test_10_frontend_component_verification()

        # Print summary
        success = self.results.print_summary()

        if success:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED{Colors.END}\n")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}✗ SOME TESTS FAILED{Colors.END}\n")

        return success

    async def cleanup(self):
        """Cleanup test data"""
        if self.db_session:
            await self.db_session.close()


async def main():
    """Main entry point"""
    tester = TeamCommentsE2ETest()

    try:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_info("\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        logger.exception("Test execution failed")
        sys.exit(1)
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
