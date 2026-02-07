#!/usr/bin/env python3
"""
Comprehensive end-to-end verification script for bulk actions on search results.

This script verifies all bulk action functionality:
1. Search returning 20+ candidates
2. Bulk tag action on selected candidates
3. Bulk export action (JSON and CSV formats)
4. Bulk add_to_pipeline action
5. Verification that all actions complete successfully

Usage:
    python3 verify_bulk_actions.py
    python3 verify_bulk_actions.py --verbose  # For detailed output
    python3 verify_bulk_actions.py --cleanup  # Cleanup test data after verification

Exit codes:
    0: All verifications passed
    1: One or more verifications failed
"""

import asyncio
import sys
import argparse
import json
import csv
import io
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent))

from database import get_db, Base
from main import app
from models.resume import Resume, ResumeStatus
from models.resume_analysis import ResumeAnalysis
from models.hiring_stage import HiringStage, HiringStageName
from models.workflow_stage_config import WorkflowStageConfig
from models.candidate_tag import CandidateTag
from models.candidate_activity import CandidateActivity, CandidateActivityType
from httpx import AsyncClient, ASGITransport


# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


# Test configuration
API_BASE_URL = os.getenv("API_BASE_URL", "")
if not API_BASE_URL:
    raise ValueError("API_BASE_URL environment variable must be set")
TEST_ORG_ID = uuid4()


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text:^80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.RESET}\n")


def print_success(text: str):
    """Print success message in green."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text: str):
    """Print error message in red."""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_info(text: str):
    """Print info message in blue."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")


def print_step(text: str):
    """Print step indicator in yellow."""
    print(f"\n{Colors.YELLOW}{Colors.BOLD}▶ {text}{Colors.RESET}")


def print_verbose(text: str):
    """Print verbose output if enabled."""
    if args.verbose:
        print(f"{Colors.WHITE}  {text}{Colors.RESET}")


async def setup_test_data(count: int = 25) -> List[str]:
    """
    Create test candidates with various attributes.

    Args:
        count: Number of test candidates to create

    Returns:
        List of created resume IDs
    """
    print_step(f"Creating {count} test candidates...")

    from database import get_db

    async for db in get_db():
        resume_ids = []

        # Diverse skills distribution
        skill_profiles = [
            ["Python", "Django", "FastAPI", "PostgreSQL", "Redis"],
            ["React", "TypeScript", "Node.js", "MongoDB", "GraphQL"],
            ["Java", "Spring Boot", "Kafka", "PostgreSQL", "Docker"],
            ["Python", "TensorFlow", "PyTorch", "Scikit-learn", "Pandas"],
            ["JavaScript", "Vue.js", "Node.js", "Express", "MongoDB"],
            ["Go", "Kubernetes", "Docker", "gRPC", "PostgreSQL"],
            ["C#", ".NET", "Azure", "SQL Server", "React"],
            ["Python", "AWS", "Terraform", "Docker", "Kubernetes"],
            ["Java", "Kotlin", "Android", "Firebase", "GraphQL"],
            ["React", "Redux", "TypeScript", "Node.js", "PostgreSQL"],
        ]

        locations = ["Remote", "New York", "San Francisco", "London", "Berlin", "Toronto", "Singapore"]

        education_levels = [
            {"degree": "PhD", "field": "Computer Science"},
            {"degree": "M.Sc", "field": "Software Engineering"},
            {"degree": "M.Sc", "field": "Data Science"},
            {"degree": "B.Sc", "field": "Computer Science"},
            {"degree": "B.Sc", "field": "Information Technology"},
        ]

        try:
            for i in range(count):
                # Create diverse candidates
                skill_profile = skill_profiles[i % len(skill_profiles)]
                experience_months = ((i % 10) + 1) * 12  # 1-10 years
                location = locations[i % len(locations)]
                education = education_levels[i % len(education_levels)]

                # Create resume
                resume = Resume(
                    organization_id=TEST_ORG_ID,
                    filename=f"test_candidate_{i+1}.pdf",
                    raw_text=f"Test Candidate {i+1} - {' '.join(skill_profile)}",
                    location=location,
                    total_experience_months=experience_months,
                    status=ResumeStatus.PROCESSED,
                )
                db.add(resume)
                await db.flush()

                resume_ids.append(str(resume.id))

                # Create resume analysis
                analysis = ResumeAnalysis(
                    resume_id=resume.id,
                    skills=skill_profile,
                    keywords=skill_profile[:3],
                    education=[education],
                    total_experience_months=experience_months,
                    match_percentage=75 + (i % 25),  # 75-100%
                )
                db.add(analysis)

            await db.commit()
            print_success(f"Created {len(resume_ids)} test candidates")
            return resume_ids

        except Exception as e:
            await db.rollback()
            print_error(f"Failed to create test data: {e}")
            raise


async def execute_search(query: str = "Python", min_count: int = 20) -> List[str]:
    """
    Execute search and return candidate IDs.

    Args:
        query: Search query string
        min_count: Minimum expected results

    Returns:
        List of resume IDs from search results
    """
    print_step(f"Executing search for '{query}' (expecting {min_count}+ results)...")

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url=API_BASE_URL) as client:
            response = await client.post(
                "/api/search/candidates",
                json={
                    "query": query,
                    "limit": 50,
                }
            )

            if response.status_code != 200:
                print_error(f"Search failed with status {response.status_code}: {response.text}")
                return []

            data = response.json()
            results = data.get("results", [])
            resume_ids = [r["id"] for r in results]

            print_success(f"Search returned {len(resume_ids)} candidates")

            if len(resume_ids) < min_count:
                print_error(f"Expected at least {min_count} results, got {len(resume_ids)}")
                return []

            print_verbose(f"Resume IDs: {resume_ids[:5]}...")

            return resume_ids

    except Exception as e:
        print_error(f"Search request failed: {e}")
        return []


async def verify_bulk_tag(resume_ids: List[str]) -> bool:
    """
    Verify bulk tag action works correctly.

    Args:
        resume_ids: List of resume IDs to tag

    Returns:
        True if verification passed, False otherwise
    """
    print_step("Verifying bulk tag action...")

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url=API_BASE_URL) as client:
            tag_name = "Test Bulk Tag"
            tag_color = "#FF5722"

            # Select first 10 candidates for tagging
            selected_ids = resume_ids[:10]
            print_info(f"Tagging {len(selected_ids)} candidates with '{tag_name}'...")

            response = await client.post(
                "/api/candidates/bulk-action",
                json={
                    "action": "tag",
                    "resume_ids": selected_ids,
                    "tag_name": tag_name,
                    "tag_color": tag_color,
                }
            )

            if response.status_code != 200:
                print_error(f"Bulk tag failed with status {response.status_code}: {response.text}")
                return False

            data = response.json()
            print_verbose(f"Response: {json.dumps(data, indent=2)}")

            # Verify response structure
            if "action" not in data or data["action"] != "tag":
                print_error("Response missing 'action' field or incorrect action type")
                return False

            if "successful" not in data or "failed" not in data:
                print_error("Response missing 'successful' or 'failed' counts")
                return False

            successful = data["successful"]
            failed = data["failed"]
            total_requested = data.get("total_requested", len(selected_ids))

            print_info(f"Results: {successful} successful, {failed} failed (total requested: {total_requested})")

            if successful != len(selected_ids):
                print_error(f"Expected {len(selected_ids)} successful tags, got {successful}")
                return False

            if failed > 0:
                print_error(f"Expected 0 failures, got {failed}")
                return False

            # Verify tags were actually created in database
            from database import get_db
            async for db in get_db():
                try:
                    # Check tag exists
                    tag_query = select(CandidateTag).where(
                        and_(
                            CandidateTag.organization_id == TEST_ORG_ID,
                            CandidateTag.tag_name == tag_name
                        )
                    )
                    tag_result = await db.execute(tag_query)
                    tag = tag_result.scalar_one_or_none()

                    if not tag:
                        print_error("Tag was not created in database")
                        return False

                    print_success(f"Tag '{tag_name}' created in database with ID: {tag.id}")

                    # Check activities were created
                    activity_query = select(CandidateActivity).where(
                        and_(
                            CandidateActivity.tag_id == tag.id,
                            CandidateActivity.activity_type == CandidateActivityType.TAG_ADDED
                        )
                    )
                    activity_result = await db.execute(activity_query)
                    activities = activity_result.scalars().all()

                    if len(activities) != len(selected_ids):
                        print_error(f"Expected {len(selected_ids)} activities, got {len(activities)}")
                        return False

                    print_success(f"All {len(activities)} tag activities recorded in database")

                    # Verify each candidate was tagged
                    for resume_id in selected_ids:
                        resume_uuid = UUID(resume_id)
                        candidate_activity_query = select(CandidateActivity).where(
                            and_(
                                CandidateActivity.candidate_id == resume_uuid,
                                CandidateActivity.tag_id == tag.id
                            )
                        )
                        candidate_activity_result = await db.execute(candidate_activity_query)
                        candidate_activity = candidate_activity_result.scalar_one_or_none()

                        if not candidate_activity:
                            print_error(f"Candidate {resume_id} was not tagged")
                            return False

                    print_success(f"All {len(selected_ids)} candidates verified with tag in database")

                except Exception as e:
                    print_error(f"Database verification failed: {e}")
                    return False

            print_success("Bulk tag action verification PASSED")
            return True

    except Exception as e:
        print_error(f"Bulk tag verification failed: {e}")
        import traceback
        print_verbose(traceback.format_exc())
        return False


async def verify_bulk_export_json(resume_ids: List[str]) -> bool:
    """
    Verify bulk export action with JSON format.

    Args:
        resume_ids: List of resume IDs to export

    Returns:
        True if verification passed, False otherwise
    """
    print_step("Verifying bulk export action (JSON format)...")

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url=API_BASE_URL) as client:
            # Select first 10 candidates for export
            selected_ids = resume_ids[:10]
            print_info(f"Exporting {len(selected_ids)} candidates as JSON...")

            response = await client.post(
                "/api/candidates/bulk-action",
                json={
                    "action": "export",
                    "resume_ids": selected_ids,
                    "export_format": "json",
                }
            )

            if response.status_code != 200:
                print_error(f"Bulk export failed with status {response.status_code}: {response.text}")
                return False

            data = response.json()
            print_verbose(f"Response: {json.dumps(data, indent=2)}")

            # Verify response structure
            if "action" not in data or data["action"] != "export":
                print_error("Response missing 'action' field or incorrect action type")
                return False

            if "export_data" not in data:
                print_error("Response missing 'export_data' field")
                return False

            export_data = data["export_data"]
            if export_data.get("format") != "json":
                print_error(f"Expected JSON format, got {export_data.get('format')}")
                return False

            exported_count = export_data.get("count", 0)
            if exported_count != len(selected_ids):
                print_error(f"Expected {len(selected_ids)} exported candidates, got {exported_count}")
                return False

            exported_candidates = export_data.get("data", [])
            if len(exported_candidates) != len(selected_ids):
                print_error(f"Expected {len(selected_ids)} candidates in data, got {len(exported_candidates)}")
                return False

            # Verify each exported candidate has required fields
            for candidate in exported_candidates:
                if "id" not in candidate or "filename" not in candidate:
                    print_error(f"Exported candidate missing required fields: {candidate}")
                    return False

                # Verify ID is in our selected list
                if candidate["id"] not in selected_ids:
                    print_error(f"Exported candidate ID {candidate['id']} not in selected list")
                    return False

            print_success(f"Exported {len(exported_candidates)} candidates with all required fields")
            print_success("Bulk export (JSON) verification PASSED")
            return True

    except Exception as e:
        print_error(f"Bulk export (JSON) verification failed: {e}")
        import traceback
        print_verbose(traceback.format_exc())
        return False


async def verify_bulk_export_csv(resume_ids: List[str]) -> bool:
    """
    Verify bulk export action with CSV format.

    Args:
        resume_ids: List of resume IDs to export

    Returns:
        True if verification passed, False otherwise
    """
    print_step("Verifying bulk export action (CSV format)...")

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url=API_BASE_URL) as client:
            # Select next 10 candidates for export
            selected_ids = resume_ids[10:20]
            print_info(f"Exporting {len(selected_ids)} candidates as CSV...")

            response = await client.post(
                "/api/candidates/bulk-action",
                json={
                    "action": "export",
                    "resume_ids": selected_ids,
                    "export_format": "csv",
                }
            )

            if response.status_code != 200:
                print_error(f"Bulk export failed with status {response.status_code}: {response.text}")
                return False

            data = response.json()
            print_verbose(f"Response: {json.dumps(data, indent=2)}")

            # Verify response structure
            if "action" not in data or data["action"] != "export":
                print_error("Response missing 'action' field or incorrect action type")
                return False

            if "export_data" not in data:
                print_error("Response missing 'export_data' field")
                return False

            export_data = data["export_data"]
            if export_data.get("format") != "csv":
                print_error(f"Expected CSV format, got {export_data.get('format')}")
                return False

            exported_count = export_data.get("count", 0)
            if exported_count != len(selected_ids):
                print_error(f"Expected {len(selected_ids)} exported candidates, got {exported_count}")
                return False

            csv_data = export_data.get("data", "")
            if not csv_data:
                print_error("CSV data is empty")
                return False

            # Parse CSV to verify structure
            csv_reader = csv.DictReader(io.StringIO(csv_data))
            csv_rows = list(csv_reader)

            if len(csv_rows) != len(selected_ids):
                print_error(f"Expected {len(selected_ids)} CSV rows, got {len(csv_rows)}")
                return False

            # Verify CSV has required columns
            if len(csv_rows) > 0:
                required_fields = ["id", "filename"]
                for field in required_fields:
                    if field not in csv_rows[0]:
                        print_error(f"CSV missing required field: {field}")
                        return False

            # Verify all exported IDs are in our selected list
            exported_ids = [row["id"] for row in csv_rows]
            for exported_id in exported_ids:
                if exported_id not in selected_ids:
                    print_error(f"Exported candidate ID {exported_id} not in selected list")
                    return False

            print_success(f"Exported {len(csv_rows)} candidates as CSV with correct structure")
            print_success("Bulk export (CSV) verification PASSED")
            return True

    except Exception as e:
        print_error(f"Bulk export (CSV) verification failed: {e}")
        import traceback
        print_verbose(traceback.format_exc())
        return False


async def verify_bulk_add_to_pipeline(resume_ids: List[str]) -> bool:
    """
    Verify bulk add_to_pipeline action works correctly.

    Args:
        resume_ids: List of resume IDs to add to pipeline

    Returns:
        True if verification passed, False otherwise
    """
    print_step("Verifying bulk add_to_pipeline action...")

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url=API_BASE_URL) as client:
            # Select first 5 candidates for pipeline addition
            selected_ids = resume_ids[:5]
            target_stage = "interview"
            notes = "Bulk added via verification script"

            print_info(f"Adding {len(selected_ids)} candidates to pipeline stage '{target_stage}'...")

            response = await client.post(
                "/api/candidates/bulk-action",
                json={
                    "action": "add_to_pipeline",
                    "resume_ids": selected_ids,
                    "stage_id": target_stage,
                    "notes": notes,
                }
            )

            if response.status_code != 200:
                print_error(f"Bulk add_to_pipeline failed with status {response.status_code}: {response.text}")
                return False

            data = response.json()
            print_verbose(f"Response: {json.dumps(data, indent=2)}")

            # Verify response structure
            if "action" not in data or data["action"] != "add_to_pipeline":
                print_error("Response missing 'action' field or incorrect action type")
                return False

            if "successful" not in data or "failed" not in data:
                print_error("Response missing 'successful' or 'failed' counts")
                return False

            successful = data["successful"]
            failed = data["failed"]
            total_requested = data.get("total_requested", len(selected_ids))

            print_info(f"Results: {successful} successful, {failed} failed (total requested: {total_requested})")

            if successful != len(selected_ids):
                print_error(f"Expected {len(selected_ids)} successful additions, got {successful}")
                return False

            if failed > 0:
                print_error(f"Expected 0 failures, got {failed}")
                return False

            # Verify candidates were actually moved in database
            from database import get_db
            async for db in get_db():
                try:
                    for resume_id in selected_ids:
                        resume_uuid = UUID(resume_id)

                        # Check hiring stage was created/updated
                        stage_query = select(HiringStage).where(
                            and_(
                                HiringStage.resume_id == resume_uuid,
                                HiringStage.stage_name == target_stage
                            )
                        ).order_by(HiringStage.created_at.desc())

                        stage_result = await db.execute(stage_query)
                        stage = stage_result.scalar_one_or_none()

                        if not stage:
                            print_error(f"Candidate {resume_id} was not added to stage '{target_stage}'")
                            return False

                        # Verify notes were saved
                        if stage.notes != notes:
                            print_error(f"Notes not saved correctly for candidate {resume_id}")
                            return False

                    print_success(f"All {len(selected_ids)} candidates verified in pipeline stage '{target_stage}'")

                except Exception as e:
                    print_error(f"Database verification failed: {e}")
                    return False

            print_success("Bulk add_to_pipeline action verification PASSED")
            return True

    except Exception as e:
        print_error(f"Bulk add_to_pipeline verification failed: {e}")
        import traceback
        print_verbose(traceback.format_exc())
        return False


async def cleanup_test_data():
    """Clean up test data from database."""
    print_step("Cleaning up test data...")

    from database import get_db

    try:
        async for db in get_db():
            # Delete candidate activities
            await db.execute(
                delete(CandidateActivity).where(
                    CandidateActivity.candidate_id.in_(
                        select(Resume.id).where(Resume.organization_id == TEST_ORG_ID)
                    )
                )
            )

            # Delete tags
            await db.execute(
                delete(CandidateTag).where(CandidateTag.organization_id == TEST_ORG_ID)
            )

            # Delete hiring stages
            await db.execute(
                delete(HiringStage).where(
                    HiringStage.resume_id.in_(
                        select(Resume.id).where(Resume.organization_id == TEST_ORG_ID)
                    )
                )
            )

            # Delete resume analyses
            await db.execute(
                delete(ResumeAnalysis).where(
                    ResumeAnalysis.resume_id.in_(
                        select(Resume.id).where(Resume.organization_id == TEST_ORG_ID)
                    )
                )
            )

            # Delete resumes
            await db.execute(
                delete(Resume).where(Resume.organization_id == TEST_ORG_ID)
            )

            await db.commit()
            print_success("Test data cleaned up successfully")

    except Exception as e:
        print_error(f"Cleanup failed: {e}")
        await db.rollback()


async def main():
    """Main verification workflow."""
    print_header("Bulk Actions on Search Results - End-to-End Verification")

    global args
    args = parser.parse_args()

    # Track overall success
    all_passed = True

    try:
        # Step 1: Create test data
        resume_ids = await setup_test_data(count=25)
        if not resume_ids:
            print_error("Failed to create test data")
            return 1

        # Step 2: Execute search
        search_results = await execute_search(query="Python", min_count=20)
        if not search_results:
            print_error("Search did not return enough results")
            all_passed = False
        else:
            print_success(f"Search returned {len(search_results)} candidates (≥ 20 required)")

        # Step 3: Verify bulk tag action
        if not await verify_bulk_tag(search_results):
            all_passed = False

        # Step 4: Verify bulk export (JSON)
        if not await verify_bulk_export_json(search_results):
            all_passed = False

        # Step 5: Verify bulk export (CSV)
        if not await verify_bulk_export_csv(search_results):
            all_passed = False

        # Step 6: Verify bulk add_to_pipeline action
        if not await verify_bulk_add_to_pipeline(search_results):
            all_passed = False

        # Final summary
        print_header("Verification Summary")

        if all_passed:
            print_success("All bulk action verifications PASSED ✓")
            print()
            print_info("Verified functionality:")
            print("  ✓ Search returns 20+ candidates")
            print("  ✓ Bulk tag action works correctly")
            print("  ✓ Bulk export (JSON) works correctly")
            print("  ✓ Bulk export (CSV) works correctly")
            print("  ✓ Bulk add_to_pipeline action works correctly")
            print()
            return 0
        else:
            print_error("Some bulk action verifications FAILED ✗")
            print()
            print_info("Please review the errors above and fix the issues.")
            print()
            return 1

    except Exception as e:
        print_error(f"Verification failed with exception: {e}")
        import traceback
        print_verbose(traceback.format_exc())
        return 1

    finally:
        # Cleanup if requested
        if args.cleanup:
            await cleanup_test_data()


# Argument parser
parser = argparse.ArgumentParser(
    description="Verify bulk actions work correctly on search results"
)
parser.add_argument(
    "--verbose", "-v",
    action="store_true",
    help="Enable verbose output"
)
parser.add_argument(
    "--cleanup", "-c",
    action="store_true",
    help="Clean up test data after verification"
)


if __name__ == "__main__":
    args = parser.parse_args()
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
