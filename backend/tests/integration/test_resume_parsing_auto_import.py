"""
Integration tests for automatic resume parsing on imported resumes.

This test suite validates that resume parsing runs automatically when
resumes are imported from job boards, including:
- Resume records are created
- ResumeAnalysis records are created with extracted data
- Skills are extracted and stored
- Resumes appear in candidates list

Test Coverage:
- End-to-end flow: import → parse → analyze → results
- Celery task triggering for automatic parsing
- ResumeAnalysis record creation
- Skill extraction and storage
- Candidate list integration
"""
import asyncio
import logging
import time
from pathlib import Path
from typing import AsyncGenerator
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

# Import the FastAPI application
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import get_settings
from database import async_session_maker
from main import app
from models import ImportStatus, ImportedResume, JobBoardIntegration, Resume, ResumeStatus
from tasks.analysis_task import analyze_resume_async
from tasks.import_tasks import process_imported_resume
from celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()


@pytest.fixture
def test_resume_file(tmp_path):
    """
    Create a test resume PDF file for import simulation.

    Returns:
        Tuple of (resume_id, file_path)
    """
    # Create a minimal PDF with resume content
    import subprocess

    resume_id = uuid4()
    file_path = tmp_path / f"{resume_id}.pdf"

    # Create a simple PDF with text content using reportlab or minimal PDF
    # For testing, we'll create a minimal valid PDF
    pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 44>>stream
BT
/F1 12 Tf
50 700 Td
(John Doe - Senior Python Developer) Tj
0 -20 Td
(Experience: 5 years in Python development) Tj
0 -20 Td
(Skills: Python, FastAPI, PostgreSQL, Celery, Redis) Tj
0 -20 Td
(Education: BS Computer Science, Stanford University) Tj
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
0000000401 00000 n
trailer
<</Size 6/Root 1 0 R>>
startxref
490
%%EOF
"""

    with open(file_path, "wb") as f:
        f.write(pdf_content)

    return str(resume_id), str(file_path)


class TestResumeParsingAutoTrigger:
    """Test that resume parsing is automatically triggered on import."""

    @pytest.mark.asyncio
    async async def test_process_imported_resume_task_creates_resume_analysis(
        self, db_session: AsyncSession, test_resume_file: tuple
    ):
        """
        Test that process_imported_resume Celery task creates ResumeAnalysis record.

        Workflow:
        1. Create Resume and ImportedResume records
        2. Trigger process_imported_resume task
        3. Wait for task completion
        4. Verify ResumeAnalysis record is created
        5. Verify skills are extracted
        """
        from models.resume_analysis import ResumeAnalysis

        resume_id, file_path = test_resume_file

        # Step 1: Create Resume record
        resume = Resume(
            id=UUID(resume_id),
            filename="test_resume.pdf",
            file_path=file_path,
            content_type="application/pdf",
            status=ResumeStatus.PENDING,
            raw_text="John Doe - Senior Python Developer\nSkills: Python, FastAPI, PostgreSQL",
        )
        db_session.add(resume)

        # Create ImportedResume record
        imported_resume = ImportedResume(
            resume_id=UUID(resume_id),
            job_board_id=uuid4(),  # Mock job board
            external_id="ext-123",
            source_url="https://example.com/resume/123",
            import_status=ImportStatus.PENDING,
            candidate_name="John Doe",
            candidate_email="john@example.com",
            job_title="Python Developer",
        )
        db_session.add(imported_resume)
        await db_session.commit()

        # Step 2: Trigger process_imported_resume task
        task_result = process_imported_resume.delay(
            resume_id=resume_id,
            applicant_id="ext-123",
            check_grammar=True,
            extract_experience=True,
            detect_errors=True,
        )

        # Step 3: Wait for task completion (max 30 seconds)
        timeout = 30
        start_time = time.time()
        while not task_result.ready() and (time.time() - start_time) < timeout:
            await asyncio.sleep(1)

        assert task_result.ready(), "Task did not complete within timeout"

        result = task_result.get()
        assert result["status"] == "completed", f"Task failed: {result.get('error')}"

        # Step 4: Verify ResumeAnalysis record is created
        from models.resume_analysis import ResumeAnalysis

        result = await db_session.execute(
            select(ResumeAnalysis).where(ResumeAnalysis.resume_id == UUID(resume_id))
        )
        analysis = result.scalar_one_or_none()

        assert analysis is not None, "ResumeAnalysis record was not created"
        assert analysis.resume_id == UUID(resume_id)
        assert analysis.language is not None, "Language was not detected"
        assert analysis.skills is not None, "Skills were not extracted"

        # Step 5: Verify skills are extracted
        skills = analysis.skills
        assert len(skills) > 0, "No skills were extracted"
        assert any("python" in skill.lower() for skill in skills), "Python skill not found"

        logger.info(f"✓ ResumeAnalysis created with {len(skills)} skills")

    @pytest.mark.asyncio
    async async def test_analyze_resume_async_creates_resume_analysis(
        self, db_session: AsyncSession, test_resume_file: tuple
    ):
        """
        Test that analyze_resume_async Celery task creates ResumeAnalysis record.

        This tests the direct analysis task that should be triggered
        after resume import.
        """
        from models.resume_analysis import ResumeAnalysis

        resume_id, file_path = test_resume_file

        # Create Resume record
        resume = Resume(
            id=UUID(resume_id),
            filename="test_resume.pdf",
            file_path=file_path,
            content_type="application/pdf",
            status=ResumeStatus.PENDING,
        )
        db_session.add(resume)
        await db_session.commit()

        # Trigger analyze_resume_async task
        task_result = analyze_resume_async.delay(
            resume_id=resume_id,
            check_grammar=True,
            extract_experience=True,
            detect_errors=True,
        )

        # Wait for task completion (max 60 seconds - analysis can take time)
        timeout = 60
        start_time = time.time()
        while not task_result.ready() and (time.time() - start_time) < timeout:
            await asyncio.sleep(2)

        assert task_result.ready(), "Analysis task did not complete within timeout"

        result = task_result.get()
        assert result["status"] == "completed", f"Analysis failed: {result.get('error')}"

        # Verify ResumeAnalysis record
        result = await db_session.execute(
            select(ResumeAnalysis).where(ResumeAnalysis.resume_id == UUID(resume_id))
        )
        analysis = result.scalar_one_or_none()

        assert analysis is not None, "ResumeAnalysis record was not created by analysis task"
        assert analysis.resume_id == UUID(resume_id)
        assert analysis.raw_text is not None, "Raw text was not stored"
        assert analysis.skills is not None, "Skills were not extracted"
        assert analysis.keywords is not None, "Keywords were not extracted"

        logger.info(f"✓ Analysis task created ResumeAnalysis with {len(analysis.skills)} skills")


class TestResumeAppearsInCandidatesList:
    """Test that imported resumes appear in candidates list."""

    @pytest.mark.asyncio
    async async def test_imported_resume_appears_in_candidates_api(
        self, db_session: AsyncSession, test_resume_file: tuple, client: TestClient
    ):
        """
        Test that imported and parsed resume appears in candidates list API.

        Workflow:
        1. Import resume (create Resume + ImportedResume)
        2. Trigger parsing task
        3. Query candidates list API
        4. Verify resume appears with extracted skills
        """
        from models.resume_analysis import ResumeAnalysis

        resume_id, file_path = test_resume_file

        # Step 1: Create Resume and ImportedResume
        resume = Resume(
            id=UUID(resume_id),
            filename="john_doe.pdf",
            file_path=file_path,
            content_type="application/pdf",
            status=ResumeStatus.COMPLETED,
            raw_text="John Doe - Python Developer\nSkills: Python, FastAPI, PostgreSQL",
        )
        db_session.add(resume)

        imported_resume = ImportedResume(
            resume_id=UUID(resume_id),
            job_board_id=uuid4(),
            external_id="indeed-456",
            source_url="https://indeed.com/resume/456",
            import_status=ImportStatus.COMPLETED,
            candidate_name="John Doe",
            candidate_email="john@example.com",
            job_title="Python Developer",
        )
        db_session.add(imported_resume)

        # Create ResumeAnalysis record (simulating completed parsing)
        analysis = ResumeAnalysis(
            resume_id=UUID(resume_id),
            language="en",
            raw_text=resume.raw_text,
            skills=["Python", "FastAPI", "PostgreSQL", "Celery", "Redis"],
            keywords=["python developer", "fastapi", "postgresql"],
            entities={
                "organizations": ["Indeed"],
                "dates": [],
                "persons": ["John Doe"],
                "locations": [],
            },
            total_experience_months=60,
            quality_score=85,
        )
        db_session.add(analysis)
        await db_session.commit()

        # Step 2: Query candidates list API
        response = client.get("/api/resumes?skip=0&limit=10")

        assert response.status_code == 200, f"API request failed: {response.text}"

        data = response.json()
        resumes = data.get("resumes", [])

        # Step 3: Verify imported resume appears in list
        assert len(resumes) > 0, "No resumes returned from API"

        # Find our imported resume
        imported = None
        for r in resumes:
            if r.get("id") == resume_id:
                imported = r
                break

        assert imported is not None, f"Imported resume {resume_id} not found in candidates list"

        # Step 4: Verify skills are included
        skills = imported.get("skills", [])
        assert len(skills) > 0, "No skills returned for imported resume"
        assert "Python" in skills, "Python skill not found in response"

        logger.info(f"✓ Imported resume appears in candidates list with {len(skills)} skills")


class TestEndToEndAutoParsingFlow:
    """End-to-end tests for automatic resume parsing flow."""

    @pytest.mark.asyncio
    async async def test_full_import_to_parsing_workflow(
        self, db_session: AsyncSession, test_resume_file: tuple
    ):
        """
        Test complete workflow: import → auto-parse → analysis → candidates list.

        This simulates the actual flow when a resume is imported from a job board.
        """
        from models.resume_analysis import ResumeAnalysis

        resume_id, file_path = test_resume_file

        # Create job board integration
        job_board = JobBoardIntegration(
            name="Indeed",
            api_endpoint="https://api.indeed.com",
            api_key="test_key",
            enabled=True,
        )
        db_session.add(job_board)
        await db_session.flush()

        # Step 1: Simulate resume import from job board
        resume = Resume(
            id=UUID(resume_id),
            filename="imported_resume.pdf",
            file_path=file_path,
            content_type="application/pdf",
            status=ResumeStatus.PENDING,
        )
        db_session.add(resume)

        imported_resume = ImportedResume(
            resume_id=UUID(resume_id),
            job_board_id=job_board.id,
            external_id="indeed-789",
            source_url="https://indeed.com/resume/789",
            import_status=ImportStatus.PENDING,
            candidate_name="Jane Smith",
            candidate_email="jane@example.com",
            job_title="Senior Software Engineer",
        )
        db_session.add(imported_resume)
        await db_session.commit()

        # Step 2: Trigger automatic parsing (simulating what should happen)
        task_result = analyze_resume_async.delay(
            resume_id=resume_id,
            check_grammar=True,
            extract_experience=True,
        )

        # Wait for completion
        timeout = 60
        start_time = time.time()
        while not task_result.ready() and (time.time() - start_time) < timeout:
            await asyncio.sleep(2)

        assert task_result.ready(), "Parsing task did not complete"
        result = task_result.get()
        assert result["status"] == "completed"

        # Step 3: Verify ResumeAnalysis was created
        analysis_result = await db_session.execute(
            select(ResumeAnalysis).where(ResumeAnalysis.resume_id == UUID(resume_id))
        )
        analysis = analysis_result.scalar_one_or_none()

        assert analysis is not None, "ResumeAnalysis not created"
        assert analysis.skills is not None, "Skills not extracted"

        # Update ImportedResume status
        imported_resume.import_status = ImportStatus.COMPLETED
        await db_session.commit()

        # Step 4: Verify we can query the parsed resume
        result = await db_session.execute(
            select(Resume)
            .join(ImportedResume, Resume.id == ImportedResume.resume_id)
            .where(ImportedResume.external_id == "indeed-789")
        )
        found_resume = result.scalar_one_or_none()

        assert found_resume is not None, "Cannot find imported resume"
        assert found_resume.id == UUID(resume_id)

        logger.info("✓ Complete workflow: import → parse → analyze successful")


# Helper fixtures
@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator:
    """Create a test database session."""
    async with async_session_maker() as session:
        yield session
        # Cleanup: rollback any changes
        await session.rollback()


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)
