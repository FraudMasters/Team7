"""
Comprehensive integration tests for candidate filtering and searching by stage.

This test suite verifies:
1. Filtering candidates by stage
2. Searching candidates by name
3. Combining filters and search
4. Clearing filters
5. Stage-specific search
6. Vacancy-specific search with stage filter
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.resume import Resume
from models.hiring_stage import HiringStage, HiringStageName
from models.workflow_stage_config import WorkflowStageConfig
from models.vacancy import Vacancy


@pytest.mark.asyncio
async def test_filter_candidates_by_stage_name(async_client: AsyncClient, db_session: AsyncSession):
    """Test filtering candidates by default stage name (e.g., 'interview')."""
    # Create test candidates in different stages
    resume1 = Resume(filename="candidate1_applied.pdf", file_path="/test1.pdf")
    resume2 = Resume(filename="candidate2_interview.pdf", file_path="/test2.pdf")
    resume3 = Resume(filename="candidate3_interview.pdf", file_path="/test3.pdf")
    db_session.add_all([resume1, resume2, resume3])
    await db_session.commit()
    await db_session.refresh(resume1)
    await db_session.refresh(resume2)
    await db_session.refresh(resume3)

    # Set stages
    stage1 = HiringStage(resume_id=resume1.id, stage_name=HiringStageName.APPLIED.value)
    stage2 = HiringStage(resume_id=resume2.id, stage_name=HiringStageName.INTERVIEW.value)
    stage3 = HiringStage(resume_id=resume3.id, stage_name=HiringStageName.INTERVIEW.value)
    db_session.add_all([stage1, stage2, stage3])
    await db_session.commit()

    # Filter by interview stage
    response = await async_client.get("/api/candidates/?stage_id=interview")
    assert response.status_code == 200

    candidates = response.json()
    assert len(candidates) == 2
    assert all(c["current_stage"] == "interview" for c in candidates)
    filenames = {c["filename"] for c in candidates}
    assert filenames == {"candidate2_interview.pdf", "candidate3_interview.pdf"}


@pytest.mark.asyncio
async def test_filter_candidates_by_custom_stage_id(async_client: AsyncClient, db_session: AsyncSession):
    """Test filtering candidates by custom workflow stage UUID."""
    # Create custom stage
    custom_stage = WorkflowStageConfig(
        organization_id="test-org",
        stage_name="Phone Screen",
        stage_order=1,
        is_default=False,
        is_active=True,
        color="#3B82F6",
    )
    db_session.add(custom_stage)
    await db_session.commit()
    await db_session.refresh(custom_stage)

    # Create candidates
    resume1 = Resume(filename="candidate1_phone.pdf", file_path="/test1.pdf")
    resume2 = Resume(filename="candidate2_other.pdf", file_path="/test2.pdf")
    db_session.add_all([resume1, resume2])
    await db_session.commit()
    await db_session.refresh(resume1)
    await db_session.refresh(resume2)

    # Set stages
    stage1 = HiringStage(
        resume_id=resume1.id,
        stage_name="Phone Screen",
        workflow_stage_config_id=custom_stage.id
    )
    stage2 = HiringStage(
        resume_id=resume2.id,
        stage_name=HiringStageName.APPLIED.value
    )
    db_session.add_all([stage1, stage2])
    await db_session.commit()

    # Filter by custom stage ID
    response = await async_client.get(f"/api/candidates/?stage_id={custom_stage.id}")
    assert response.status_code == 200

    candidates = response.json()
    assert len(candidates) == 1
    assert candidates[0]["filename"] == "candidate1_phone.pdf"
    assert candidates[0]["current_stage"] == "Phone Screen"


@pytest.mark.asyncio
async def test_search_candidates_by_name(async_client: AsyncClient, db_session: AsyncSession):
    """Test searching candidates by filename."""
    # Create candidates with different names
    resume1 = Resume(filename="john_smith.pdf", file_path="/test1.pdf")
    resume2 = Resume(filename="jane_doe.pdf", file_path="/test2.pdf")
    resume3 = Resume(filename="john_doe.pdf", file_path="/test3.pdf")
    db_session.add_all([resume1, resume2, resume3])
    await db_session.commit()

    # Set all to same stage
    for resume in [resume1, resume2, resume3]:
        await db_session.refresh(resume)
        stage = HiringStage(resume_id=resume.id, stage_name=HiringStageName.APPLIED.value)
        db_session.add(stage)
    await db_session.commit()

    # Search for "john"
    response = await async_client.get("/api/candidates/?search=john")
    assert response.status_code == 200

    candidates = response.json()
    assert len(candidates) == 2
    filenames = {c["filename"] for c in candidates}
    assert filenames == {"john_smith.pdf", "john_doe.pdf"}


@pytest.mark.asyncio
async def test_search_case_insensitive(async_client: AsyncClient, db_session: AsyncSession):
    """Test that search is case-insensitive."""
    resume = Resume(filename="John_Smith_Resume.pdf", file_path="/test.pdf")
    db_session.add(resume)
    await db_session.commit()
    await db_session.refresh(resume)

    stage = HiringStage(resume_id=resume.id, stage_name=HiringStageName.APPLIED.value)
    db_session.add(stage)
    await db_session.commit()

    # Search with different cases
    for search_term in ["john", "JOHN", "John", "jOhN"]:
        response = await async_client.get(f"/api/candidates/?search={search_term}")
        assert response.status_code == 200
        candidates = response.json()
        assert len(candidates) == 1
        assert candidates[0]["filename"] == "John_Smith_Resume.pdf"


@pytest.mark.asyncio
async def test_search_within_specific_stage(async_client: AsyncClient, db_session: AsyncSession):
    """Test searching candidates within a specific stage (combined filters)."""
    # Create candidates in different stages
    resume1 = Resume(filename="john_interview.pdf", file_path="/test1.pdf")
    resume2 = Resume(filename="john_applied.pdf", file_path="/test2.pdf")
    resume3 = Resume(filename="jane_interview.pdf", file_path="/test3.pdf")
    db_session.add_all([resume1, resume2, resume3])
    await db_session.commit()
    await db_session.refresh(resume1)
    await db_session.refresh(resume2)
    await db_session.refresh(resume3)

    # Set stages
    stage1 = HiringStage(resume_id=resume1.id, stage_name=HiringStageName.INTERVIEW.value)
    stage2 = HiringStage(resume_id=resume2.id, stage_name=HiringStageName.APPLIED.value)
    stage3 = HiringStage(resume_id=resume3.id, stage_name=HiringStageName.INTERVIEW.value)
    db_session.add_all([stage1, stage2, stage3])
    await db_session.commit()

    # Search for "john" within "interview" stage
    response = await async_client.get("/api/candidates/?stage_id=interview&search=john")
    assert response.status_code == 200

    candidates = response.json()
    assert len(candidates) == 1
    assert candidates[0]["filename"] == "john_interview.pdf"
    assert candidates[0]["current_stage"] == "interview"


@pytest.mark.asyncio
async def test_clear_filters_verify_all_candidates(async_client: AsyncClient, db_session: AsyncSession):
    """Test that clearing filters returns all candidates."""
    # Create multiple candidates
    resumes = [
        Resume(filename=f"candidate{i}.pdf", file_path=f"/test{i}.pdf")
        for i in range(1, 6)
    ]
    db_session.add_all(resumes)
    await db_session.commit()

    for resume in resumes:
        await db_session.refresh(resume)
        stage = HiringStage(resume_id=resume.id, stage_name=HiringStageName.APPLIED.value)
        db_session.add(stage)
    await db_session.commit()

    # Get all candidates (no filters)
    response = await async_client.get("/api/candidates/")
    assert response.status_code == 200

    candidates = response.json()
    assert len(candidates) == 5


@pytest.mark.asyncio
async def test_filter_by_vacancy_and_stage(async_client: AsyncClient, db_session: AsyncSession):
    """Test filtering by both vacancy and stage."""
    # Create vacancy
    vacancy = Vacancy(
        title="Software Engineer",
        description="Test vacancy",
        location="Remote"
    )
    db_session.add(vacancy)
    await db_session.commit()
    await db_session.refresh(vacancy)

    # Create candidates
    resume1 = Resume(filename="candidate1_vacancy.pdf", file_path="/test1.pdf")
    resume2 = Resume(filename="candidate2_vacancy.pdf", file_path="/test2.pdf")
    resume3 = Resume(filename="candidate3_other.pdf", file_path="/test3.pdf")
    db_session.add_all([resume1, resume2, resume3])
    await db_session.commit()
    await db_session.refresh(resume1)
    await db_session.refresh(resume2)
    await db_session.refresh(resume3)

    # Set stages with vacancy linkage
    stage1 = HiringStage(
        resume_id=resume1.id,
        stage_name=HiringStageName.INTERVIEW.value,
        vacancy_id=vacancy.id
    )
    stage2 = HiringStage(
        resume_id=resume2.id,
        stage_name=HiringStageName.APPLIED.value,
        vacancy_id=vacancy.id
    )
    stage3 = HiringStage(
        resume_id=resume3.id,
        stage_name=HiringStageName.INTERVIEW.value,
    )
    db_session.add_all([stage1, stage2, stage3])
    await db_session.commit()

    # Filter by vacancy and stage
    response = await async_client.get(f"/api/candidates/?vacancy_id={vacancy.id}&stage_id=interview")
    assert response.status_code == 200

    candidates = response.json()
    assert len(candidates) == 1
    assert candidates[0]["filename"] == "candidate1_vacancy.pdf"
    assert candidates[0]["vacancy_id"] == str(vacancy.id)


@pytest.mark.asyncio
async def test_search_with_vacancy_filter(async_client: AsyncClient, db_session: AsyncSession):
    """Test searching within vacancy-filtered results."""
    # Create vacancy
    vacancy = Vacancy(
        title="Software Engineer",
        description="Test vacancy",
        location="Remote"
    )
    db_session.add(vacancy)
    await db_session.commit()
    await db_session.refresh(vacancy)

    # Create candidates
    resume1 = Resume(filename="john_engineer.pdf", file_path="/test1.pdf")
    resume2 = Resume(filename="jane_engineer.pdf", file_path="/test2.pdf")
    resume3 = Resume(filename="john_designer.pdf", file_path="/test3.pdf")
    db_session.add_all([resume1, resume2, resume3])
    await db_session.commit()
    await db_session.refresh(resume1)
    await db_session.refresh(resume2)
    await db_session.refresh(resume3)

    # Set stages with vacancy linkage
    stage1 = HiringStage(
        resume_id=resume1.id,
        stage_name=HiringStageName.APPLIED.value,
        vacancy_id=vacancy.id
    )
    stage2 = HiringStage(
        resume_id=resume2.id,
        stage_name=HiringStageName.APPLIED.value,
        vacancy_id=vacancy.id
    )
    stage3 = HiringStage(
        resume_id=resume3.id,
        stage_name=HiringStageName.APPLIED.value,
    )
    db_session.add_all([stage1, stage2, stage3])
    await db_session.commit()

    # Search for "john" within vacancy
    response = await async_client.get(f"/api/candidates/?vacancy_id={vacancy.id}&search=john")
    assert response.status_code == 200

    candidates = response.json()
    assert len(candidates) == 1
    assert candidates[0]["filename"] == "john_engineer.pdf"


@pytest.mark.asyncio
async def test_empty_search_results(async_client: AsyncClient, db_session: AsyncSession):
    """Test that search returns empty list when no matches."""
    resume = Resume(filename="existing_candidate.pdf", file_path="/test.pdf")
    db_session.add(resume)
    await db_session.commit()
    await db_session.refresh(resume)

    stage = HiringStage(resume_id=resume.id, stage_name=HiringStageName.APPLIED.value)
    db_session.add(stage)
    await db_session.commit()

    # Search for non-existent candidate
    response = await async_client.get("/api/candidates/?search=nonexistent")
    assert response.status_code == 200

    candidates = response.json()
    assert len(candidates) == 0


@pytest.mark.asyncio
async def test_partial_match_search(async_client: AsyncClient, db_session: AsyncSession):
    """Test that search performs partial matching."""
    resume = Resume(filename="Senior_Software_Engineer_Resume.pdf", file_path="/test.pdf")
    db_session.add(resume)
    await db_session.commit()
    await db_session.refresh(resume)

    stage = HiringStage(resume_id=resume.id, stage_name=HiringStageName.APPLIED.value)
    db_session.add(stage)
    await db_session.commit()

    # Search for partial matches
    for search_term in ["Software", "Engineer", "Senior", "Resume", "Soft"]:
        response = await async_client.get(f"/api/candidates/?search={search_term}")
        assert response.status_code == 200
        candidates = response.json()
        assert len(candidates) == 1
        assert candidates[0]["filename"] == "Senior_Software_Engineer_Resume.pdf"


@pytest.mark.asyncio
async def test_pagination_with_filters(async_client: AsyncClient, db_session: AsyncSession):
    """Test that pagination works correctly with filters."""
    # Create multiple candidates in interview stage
    resumes = [
        Resume(filename=f"interview_candidate{i}.pdf", file_path=f"/test{i}.pdf")
        for i in range(1, 11)
    ]
    db_session.add_all(resumes)
    await db_session.commit()

    for resume in resumes:
        await db_session.refresh(resume)
        stage = HiringStage(resume_id=resume.id, stage_name=HiringStageName.INTERVIEW.value)
        db_session.add(stage)
    await db_session.commit()

    # Get first page
    response = await async_client.get("/api/candidates/?stage_id=interview&skip=0&limit=5")
    assert response.status_code == 200
    candidates = response.json()
    assert len(candidates) == 5

    # Get second page
    response = await async_client.get("/api/candidates/?stage_id=interview&skip=5&limit=5")
    assert response.status_code == 200
    candidates = response.json()
    assert len(candidates) == 5
