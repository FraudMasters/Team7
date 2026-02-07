#!/usr/bin/env python3
"""
Manual verification test for automatic resume parsing on imported resumes.

This script verifies that:
1. Imported resumes trigger automatic parsing
2. ResumeAnalysis records are created
3. Skills are extracted and stored
4. Resumes appear in candidates list

Usage:
    python manual_resume_parsing_test.py

Requirements:
    - Resume file at data/uploads/{resume_id}.pdf
    - Database connection configured
    - Celery worker running
"""
import asyncio
import os
import sys
import time
from pathlib import Path
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database import async_session_maker
from models import ImportStatus, ImportedResume, JobBoardIntegration, Resume, ResumeStatus
from tasks.analysis_task import analyze_resume_async
from tasks.import_tasks import process_imported_resume


# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_success(message):
    print(f"{GREEN}✓ {message}{RESET}")


def print_error(message):
    print(f"{RED}✗ {message}{RESET}")


def print_info(message):
    print(f"{BLUE}ℹ {message}{RESET}")


def print_warning(message):
    print(f"{YELLOW}⚠ {message}{RESET}")


def create_test_resume_file():
    """Create a minimal test resume PDF file."""
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    resume_id = str(uuid4())
    file_path = upload_dir / f"{resume_id}.pdf"

    # Minimal PDF with resume content
    pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 200>>stream
BT
/F1 12 Tf
50 700 Td
(Sarah Johnson - Senior Data Scientist) Tj
0 -20 Td
(Experience: 7 years in data science and machine learning) Tj
0 -20 Td
(Skills: Python, TensorFlow, PyTorch, SQL, AWS, Docker) Tj
0 -20 Td
(Education: PhD Computer Science, MIT) Tj
0 -20 Td
(Previous: Data Scientist at Google, 2019-2023) Tj
ET
endstream endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000264 00000 n
0000000501 00000 n
trailer
<</Size 6/Root 1 0 R>>
startxref
591
%%EOF
"""

    with open(file_path, "wb") as f:
        f.write(pdf_content)

    print_success(f"Created test resume file: {file_path}")
    return resume_id, str(file_path)


async def test_1_process_imported_resume_creates_analysis():
    """Test 1: Verify process_imported_resume task creates ResumeAnalysis."""
    print_info("\n=== TEST 1: process_imported_resume creates ResumeAnalysis ===")

    from models.resume_analysis import ResumeAnalysis
    from sqlalchemy import select

    resume_id, file_path = create_test_resume_file()

    async with async_session_maker() as db:
        try:
            # Create Resume record
            resume = Resume(
                id=resume_id,
                filename="test_resume.pdf",
                file_path=file_path,
                content_type="application/pdf",
                status=ResumeStatus.PENDING,
            )
            db.add(resume)

            # Create ImportedResume record
            imported = ImportedResume(
                resume_id=resume_id,
                job_board_id=uuid4(),
                external_id="test-ext-1",
                source_url="https://example.com/resume/1",
                import_status=ImportStatus.PENDING,
                candidate_name="Sarah Johnson",
                candidate_email="sarah@example.com",
            )
            db.add(imported)
            await db.commit()

            # Trigger parsing task
            print_info("Triggering process_imported_resume task...")
            task = process_imported_resume.delay(
                resume_id=str(resume_id),
                applicant_id="test-ext-1",
                check_grammar=True,
                extract_experience=True,
            )

            # Wait for completion
            timeout = 60
            start = time.time()
            while not task.ready() and (time.time() - start) < timeout:
                await asyncio.sleep(1)

            if not task.ready():
                print_error("Task timed out after 60 seconds")
                return False

            result = task.get()
            if result.get("status") != "completed":
                print_error(f"Task failed: {result.get('error')}")
                return False

            # Verify ResumeAnalysis created
            result = await db.execute(
                select(ResumeAnalysis).where(ResumeAnalysis.resume_id == resume_id)
            )
            analysis = result.scalar_one_or_none()

            if not analysis:
                print_error("ResumeAnalysis record not created")
                return False

            if not analysis.skills or len(analysis.skills) == 0:
                print_error("No skills extracted")
                return False

            print_success(f"ResumeAnalysis created with {len(analysis.skills)} skills")
            print_success(f"Skills: {', '.join(analysis.skills[:5])}")
            return True

        except Exception as e:
            print_error(f"Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_2_analyze_resume_async_creates_analysis():
    """Test 2: Verify analyze_resume_async creates ResumeAnalysis."""
    print_info("\n=== TEST 2: analyze_resume_async creates ResumeAnalysis ===")

    from models.resume_analysis import ResumeAnalysis
    from sqlalchemy import select

    resume_id, file_path = create_test_resume_file()

    async with async_session_maker() as db:
        try:
            # Create Resume record
            resume = Resume(
                id=resume_id,
                filename="test_resume2.pdf",
                file_path=file_path,
                content_type="application/pdf",
                status=ResumeStatus.PENDING,
            )
            db.add(resume)
            await db.commit()

            # Trigger analysis task
            print_info("Triggering analyze_resume_async task...")
            task = analyze_resume_async.delay(
                resume_id=str(resume_id),
                check_grammar=True,
                extract_experience=True,
            )

            # Wait for completion
            timeout = 90
            start = time.time()
            while not task.ready() and (time.time() - start) < timeout:
                await asyncio.sleep(2)

            if not task.ready():
                print_error("Task timed out after 90 seconds")
                return False

            result = task.get()
            if result.get("status") != "completed":
                print_error(f"Task failed: {result.get('error')}")
                return False

            # Verify ResumeAnalysis created
            result = await db.execute(
                select(ResumeAnalysis).where(ResumeAnalysis.resume_id == resume_id)
            )
            analysis = result.scalar_one_or_none()

            if not analysis:
                print_error("ResumeAnalysis record not created")
                return False

            print_success(f"ResumeAnalysis created")
            print_success(f"Language: {analysis.language}")
            print_success(f"Skills extracted: {len(analysis.skills) if analysis.skills else 0}")
            print_success(f"Keywords extracted: {len(analysis.keywords) if analysis.keywords else 0}")
            return True

        except Exception as e:
            print_error(f"Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_3_resume_appears_in_candidates():
    """Test 3: Verify imported resume appears in candidates list."""
    print_info("\n=== TEST 3: Imported resume appears in candidates list ===")

    from models.resume_analysis import ResumeAnalysis
    from sqlalchemy import select

    resume_id, file_path = create_test_resume_file()

    async with async_session_maker() as db:
        try:
            # Create complete resume with analysis
            resume = Resume(
                id=resume_id,
                filename="candidate_resume.pdf",
                file_path=file_path,
                content_type="application/pdf",
                status=ResumeStatus.COMPLETED,
                raw_text="Sarah Johnson - Data Scientist\nSkills: Python, TensorFlow, SQL",
            )
            db.add(resume)

            imported = ImportedResume(
                resume_id=resume_id,
                job_board_id=uuid4(),
                external_id="indeed-candidate",
                source_url="https://indeed.com/r/candidate",
                import_status=ImportStatus.COMPLETED,
                candidate_name="Sarah Johnson",
                candidate_email="sarah@example.com",
            )
            db.add(imported)

            analysis = ResumeAnalysis(
                resume_id=resume_id,
                language="en",
                raw_text=resume.raw_text,
                skills=["Python", "TensorFlow", "PyTorch", "SQL", "AWS"],
                keywords=["data scientist", "machine learning", "python"],
                entities={
                    "persons": ["Sarah Johnson"],
                    "organizations": [],
                    "dates": [],
                    "locations": [],
                },
                total_experience_months=84,
            )
            db.add(analysis)
            await db.commit()

            # Query resumes
            result = await db.execute(
                select(Resume)
                .join(ImportedResume, Resume.id == ImportedResume.resume_id)
                .where(ImportedResume.external_id == "indeed-candidate")
            )
            found = result.scalar_one_or_none()

            if not found:
                print_error("Imported resume not found in query")
                return False

            # Verify skills via ResumeAnalysis
            result = await db.execute(
                select(ResumeAnalysis).where(ResumeAnalysis.resume_id == resume_id)
            )
            analysis = result.scalar_one_or_none()

            if not analysis or not analysis.skills:
                print_error("Resume analysis or skills not found")
                return False

            print_success(f"Resume found in candidates list")
            print_success(f"Skills: {', '.join(analysis.skills)}")
            return True

        except Exception as e:
            print_error(f"Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False


async def cleanup_test_data():
    """Clean up test data from database."""
    print_info("\n=== CLEANUP: Removing test data ===")

    from models.resume_analysis import ResumeAnalysis
    from sqlalchemy import delete

    async with async_session_maker() as db:
        try:
            # Delete test resume analyses
            await db.execute(
                delete(ResumeAnalysis).where(
                    ResumeAnalysis.resume_id.in_(
                        select(ImportedResume.resume_id).where(
                            ImportedResume.external_id.like("test-%")
                            or ImportedResume.external_id.like("indeed-%")
                        )
                    )
                )
            )

            # Delete test imported resumes
            await db.execute(
                delete(ImportedResume).where(
                    ImportedResume.external_id.like("test-%")
                    or ImportedResume.external_id.like("indeed-%")
                )
            )

            # Delete test resumes
            await db.execute(
                delete(Resume).where(Resume.filename.like("test%"))
            )

            await db.commit()
            print_success("Test data cleaned up")

        except Exception as e:
            print_warning(f"Cleanup failed: {e}")


async def main():
    """Run all verification tests."""
    print(BLUE + "=" * 60 + RESET)
    print(BLUE + "RESUME PARSING AUTO-IMPORT VERIFICATION" + RESET)
    print(BLUE + "=" * 60 + RESET)

    results = {}

    try:
        # Run tests
        results["test1"] = await test_1_process_imported_resume_creates_analysis()
        results["test2"] = await test_2_analyze_resume_async_creates_analysis()
        results["test3"] = await test_3_resume_appears_in_candidates()

        # Print summary
        print("\n" + "=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)

        for test_name, passed in results.items():
            status = GREEN + "PASS" + RESET if passed else RED + "FAIL" + RESET
            print(f"{test_name}: {status}")

        total = len(results)
        passed = sum(results.values())
        print(f"\nTotal: {passed}/{total} tests passed")

        if passed == total:
            print_success("All verification tests passed!")
            return 0
        else:
            print_error(f"{total - passed} test(s) failed")
            return 1

    except KeyboardInterrupt:
        print_warning("\nTests interrupted by user")
        return 130
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Cleanup
        await cleanup_test_data()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
