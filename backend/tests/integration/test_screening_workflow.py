"""
End-to-end integration test for automated resume screening workflow.

This test verifies:
1. Resume upload and analysis completion
2. Auto-screening task triggering
3. ScreeningResult creation with correct tier
4. Tier threshold logic verification
5. Metrics tracking updates
"""
import asyncio
import time
from datetime import datetime
from unittest.mock import Mock

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from main import app
from database import get_db
from models.resume import Resume, ResumeStatus
from models.job_vacancy import JobVacancy
from models.screening_rule import ScreeningRule
from models.screening_result import ScreeningResult
from models.candidate_rank import CandidateRank
from models.resume_analysis import ResumeAnalysis
from services.screening_service import ScreeningService


# Test database URL (use same as main database for integration testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_screening.db"


@pytest.fixture
async def test_db():
    """Create test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def client(test_db):
    """Create test client with database override."""
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_screening_workflow_e2e(client: AsyncClient, test_db: AsyncSession):
    """
    End-to-end test: Resume upload → Analysis → Auto-screening → Tier categorization.

    Verification steps:
    1. Create a job vacancy with screening rules
    2. Create a test resume with analysis data
    3. Create candidate rank (simulating completed analysis)
    4. Trigger auto-screening
    5. Verify ScreeningResult is created with correct tier
    6. Verify tier matches expected threshold logic
    7. Check metrics are incremented
    """
    print("\n=== Starting End-to-End Screening Workflow Test ===\n")

    # Step 1: Create a job vacancy
    print("Step 1: Creating test job vacancy...")
    test_vacancy = JobVacancy(
        title="Senior Python Developer",
        description="We are looking for a senior Python developer with experience in Django, FastAPI, and PostgreSQL.",
        required_skills=["python", "django", "postgresql"],
        min_experience_months=60,
        industry="Software Development",
        work_format="remote"
    )
    test_db.add(test_vacancy)
    await test_db.commit()
    await test_db.refresh(test_vacancy)

    vacancy_id = str(test_vacancy.id)
    print(f"✓ Created vacancy with ID: {vacancy_id}")
    print(f"  Title: {test_vacancy.title}")

    # Step 2: Create screening rules for the vacancy
    print("\nStep 2: Creating screening rules...")
    screening_rule = ScreeningRule(
        vacancy_id=test_vacancy.id,
        min_score_threshold=50.0,
        auto_reject_threshold=30.0,
        high_priority_threshold=80.0,
        must_have_skills=["python"],
        auto_reject_with_notification=False,
        rule_priority=100,
        is_active=True
    )
    test_db.add(screening_rule)
    await test_db.commit()
    await test_db.refresh(screening_rule)

    print(f"✓ Created screening rule with ID: {screening_rule.id}")
    print(f"  Thresholds - Auto-reject: {screening_rule.auto_reject_threshold}, "
          f"Min: {screening_rule.min_score_threshold}, "
          f"High-priority: {screening_rule.high_priority_threshold}")
    print(f"  Must-have skills: {screening_rule.must_have_skills}")

    # Step 3: Create a test resume
    print("\nStep 3: Creating test resume...")
    test_resume = Resume(
        filename="john_doe_developer.pdf",
        file_path="/tmp/test_resume.pdf",
        content_type="application/pdf",
        status=ResumeStatus.COMPLETED,
        raw_text="Experienced Python developer with 8 years of experience in Django, FastAPI, and PostgreSQL. "
                 "Skilled in REST API development, database design, and cloud technologies.",
        language="en"
    )
    test_db.add(test_resume)
    await test_db.commit()
    await test_db.refresh(test_resume)

    resume_id = str(test_resume.id)
    print(f"✓ Created resume with ID: {resume_id}")

    # Step 4: Create resume analysis (simulating completed analysis)
    print("\nStep 4: Creating resume analysis...")
    resume_analysis = ResumeAnalysis(
        resume_id=test_resume.id,
        skills=["python", "django", "fastapi", "postgresql", "rest api", "cloud"],
        total_experience_months=96,
        education=[{"degree": "BS Computer Science", "year": 2015}],
        candidate_name="John Doe",
        email="john.doe@example.com",
        phone="+1234567890"
    )
    test_db.add(resume_analysis)
    await test_db.commit()

    print(f"✓ Created resume analysis with skills: {resume_analysis.skills}")

    # Step 5: Create candidate rank (simulating ranking score)
    print("\nStep 5: Creating candidate rank...")
    # Test HIGH_PRIORITY case: score >= 80
    test_score = 0.85  # 85/100
    candidate_rank = CandidateRank(
        resume_id=test_resume.id,
        vacancy_id=test_vacancy.id,
        rank_score=test_score,
        match_details={
            "skills_match": 0.9,
            "experience_match": 0.85,
            "overall_score": test_score
        }
    )
    test_db.add(candidate_rank)
    await test_db.commit()

    print(f"✓ Created candidate rank with score: {test_score * 100:.1f}/100")

    # Step 6: Trigger auto-screening via service
    print("\nStep 6: Triggering auto-screening...")
    screening_service = ScreeningService(test_db)

    start_time = time.time()
    outcome = await screening_service.apply_screening_rules(
        resume_id=test_resume.id,
        vacancy_id=test_vacancy.id
    )
    screening_duration = time.time() - start_time

    print(f"✓ Screening completed in {screening_duration:.3f}s")
    print(f"  Tier: {outcome.tier}")
    print(f"  Score applied: {outcome.score_applied:.2f}")
    print(f"  Passed must-have skills: {outcome.passed_must_have_skills}")

    # Step 7: Verify ScreeningResult is created
    print("\nStep 7: Verifying ScreeningResult created...")
    result_query = select(ScreeningResult).where(
        and_(
            ScreeningResult.resume_id == test_resume.id,
            ScreeningResult.vacancy_id == test_vacancy.id
        )
    )
    result = await test_db.execute(result_query)
    screening_result = result.scalar_one_or_none()

    assert screening_result is not None, "ScreeningResult should be created"
    print(f"✓ ScreeningResult created with ID: {screening_result.id}")
    print(f"  Tier in database: {screening_result.tier}")
    print(f"  Score in database: {screening_result.score_applied}")

    # Step 8: Verify tier matches expected threshold logic
    print("\nStep 8: Verifying tier threshold logic...")
    expected_tier = ScreeningService.TIER_HIGH_PRIORITY
    actual_tier = screening_result.tier

    assert actual_tier == expected_tier, (
        f"Expected tier {expected_tier}, got {actual_tier}. "
        f"Score {outcome.score_applied:.2f} >= high_priority_threshold {screening_rule.high_priority_threshold}"
    )
    print(f"✓ Tier matches expected logic: {actual_tier}")
    print(f"  Score {outcome.score_applied:.2f} >= High-priority threshold {screening_rule.high_priority_threshold}")

    # Step 9: Check metrics are incremented
    print("\nStep 9: Checking metrics are incremented...")
    metrics = screening_service.get_screening_metrics()

    assert metrics["total_screened"] >= 1, "Total screened should be at least 1"
    assert metrics["high_priority_count"] >= 1, "High priority count should be at least 1"
    assert metrics["average_screening_time_seconds"] > 0, "Average screening time should be recorded"

    print(f"✓ Metrics updated successfully:")
    print(f"  Total screened: {metrics['total_screened']}")
    print(f"  High priority count: {metrics['high_priority_count']}")
    print(f"  Review count: {metrics['review_count']}")
    print(f"  Auto-rejected count: {metrics['auto_rejected_count']}")
    print(f"  Average screening time: {metrics['average_screening_time_seconds']:.3f}s")

    # Step 10: Test REJECT tier (below threshold)
    print("\nStep 10: Testing REJECT tier (below threshold)...")

    # Create another resume with low score
    low_score_resume = Resume(
        filename="low_score_candidate.pdf",
        file_path="/tmp/low_score_resume.pdf",
        content_type="application/pdf",
        status=ResumeStatus.COMPLETED,
        raw_text="Junior developer with basic skills",
        language="en"
    )
    test_db.add(low_score_resume)
    await test_db.commit()
    await test_db.refresh(low_score_resume)

    # Create analysis for low score resume
    low_score_analysis = ResumeAnalysis(
        resume_id=low_score_resume.id,
        skills=["basic programming"],
        total_experience_months=12,
        candidate_name="Junior Dev",
        email="junior@example.com"
    )
    test_db.add(low_score_analysis)
    await test_db.commit()

    # Create low candidate rank (below auto-reject threshold)
    low_rank = CandidateRank(
        resume_id=low_score_resume.id,
        vacancy_id=test_vacancy.id,
        rank_score=0.20,  # 20/100 - below auto_reject_threshold of 30
        match_details={"overall_score": 0.20}
    )
    test_db.add(low_rank)
    await test_db.commit()

    # Apply screening
    low_outcome = await screening_service.apply_screening_rules(
        resume_id=low_score_resume.id,
        vacancy_id=test_vacancy.id
    )

    print(f"✓ Low-score screening completed")
    print(f"  Score: {low_outcome.score_applied:.2f}")
    print(f"  Tier: {low_outcome.tier}")
    print(f"  Rejection reasons: {low_outcome.rejection_reasons}")

    assert low_outcome.tier == ScreeningService.TIER_REJECT, (
        f"Expected REJECT tier for low score, got {low_outcome.tier}"
    )
    assert ScreeningService.REASON_BELOW_THRESHOLD in low_outcome.rejection_reasons, (
        "Expected below_threshold rejection reason"
    )

    # Verify metrics updated
    updated_metrics = screening_service.get_screening_metrics()
    assert updated_metrics["total_screened"] >= 2, "Total screened should be at least 2"
    assert updated_metrics["auto_rejected_count"] >= 1, "Auto-rejected count should be at least 1"
    print(f"✓ REJECT tier verified, metrics updated:")
    print(f"  Auto-rejected count: {updated_metrics['auto_rejected_count']}")

    # Step 11: Test REVIEW tier (middle range)
    print("\nStep 11: Testing REVIEW tier (middle range)...")

    # Create resume with middle score
    mid_score_resume = Resume(
        filename="mid_score_candidate.pdf",
        file_path="/tmp/mid_score_resume.pdf",
        content_type="application/pdf",
        status=ResumeStatus.COMPLETED,
        raw_text="Experienced developer with good skills",
        language="en"
    )
    test_db.add(mid_score_resume)
    await test_db.commit()
    await test_db.refresh(mid_score_resume)

    # Create analysis
    mid_score_analysis = ResumeAnalysis(
        resume_id=mid_score_resume.id,
        skills=["python", "postgresql"],
        total_experience_months=48,
        candidate_name="Mid Dev",
        email="mid@example.com"
    )
    test_db.add(mid_score_analysis)
    await test_db.commit()

    # Create middle candidate rank (between min and high priority thresholds)
    mid_rank = CandidateRank(
        resume_id=mid_score_resume.id,
        vacancy_id=test_vacancy.id,
        rank_score=0.65,  # 65/100 - between min (50) and high_priority (80)
        match_details={"overall_score": 0.65}
    )
    test_db.add(mid_rank)
    await test_db.commit()

    # Apply screening
    mid_outcome = await screening_service.apply_screening_rules(
        resume_id=mid_score_resume.id,
        vacancy_id=test_vacancy.id
    )

    print(f"✓ Middle-score screening completed")
    print(f"  Score: {mid_outcome.score_applied:.2f}")
    print(f"  Tier: {mid_outcome.tier}")

    assert mid_outcome.tier == ScreeningService.TIER_REVIEW, (
        f"Expected REVIEW tier for middle score, got {mid_outcome.tier}"
    )

    # Verify metrics updated
    final_metrics = screening_service.get_screening_metrics()
    assert final_metrics["total_screened"] >= 3, "Total screened should be at least 3"
    assert final_metrics["review_count"] >= 1, "Review count should be at least 1"
    print(f"✓ REVIEW tier verified, metrics updated:")
    print(f"  Review count: {final_metrics['review_count']}")

    # Step 12: Verify all screening results in database
    print("\nStep 12: Verifying all screening results in database...")
    all_results_query = select(ScreeningResult).where(
        ScreeningResult.vacancy_id == test_vacancy.id
    )
    all_results = await test_db.execute(all_results_query)
    all_screening_results = all_results.scalars().all()

    print(f"✓ Total screening results in database: {len(all_screening_results)}")
    for result in all_screening_results:
        print(f"  - Resume {str(result.resume_id)[-8:]}: {result.tier} ({result.score_applied:.1f})")

    print("\n=== End-to-End Screening Workflow Test PASSED ===\n")
    print("Summary:")
    print("  ✓ Job vacancy and screening rules created")
    print("  ✓ Resume with analysis and ranking created")
    print("  ✓ Auto-screening triggered and completed")
    print("  ✓ ScreeningResult created for each candidate")
    print("  ✓ Tier logic verified (HIGH_PRIORITY, REVIEW, REJECT)")
    print("  ✓ Metrics incremented correctly")
    print("  ✓ All results persisted in database")


@pytest.mark.asyncio
async def test_screening_must_have_skills_filter(client: AsyncClient, test_db: AsyncSession):
    """
    Test that must-have skills acts as a hard filter.

    This test verifies that candidates missing must-have skills
    are rejected regardless of their score.
    """
    print("\n=== Testing Must-Have Skills Filter ===\n")

    # Create vacancy with must-have skills
    vacancy = JobVacancy(
        title="Full Stack Developer",
        description="Full stack developer position",
        required_skills=["javascript", "react", "node.js"],
        min_experience_months=36
    )
    test_db.add(vacancy)
    await test_db.commit()
    await test_db.refresh(vacancy)

    # Create screening rule with must-have skills
    rule = ScreeningRule(
        vacancy_id=vacancy.id,
        min_score_threshold=40.0,
        auto_reject_threshold=20.0,
        high_priority_threshold=75.0,
        must_have_skills=["react", "node.js"],  # Must have these
        auto_reject_with_notification=False,
        rule_priority=100,
        is_active=True
    )
    test_db.add(rule)
    await test_db.commit()

    print(f"✓ Created vacancy and rule with must-have skills: {rule.must_have_skills}")

    # Create resume WITHOUT must-have skills (but WITH high score)
    resume = Resume(
        filename="missing_skills.pdf",
        file_path="/tmp/missing_skills.pdf",
        content_type="application/pdf",
        status=ResumeStatus.COMPLETED,
        raw_text="Great developer with high score but missing react and node.js",
        language="en"
    )
    test_db.add(resume)
    await test_db.commit()
    await test_db.refresh(resume)

    # Create analysis without must-have skills
    analysis = ResumeAnalysis(
        resume_id=resume.id,
        skills=["python", "django", "postgresql"],  # Missing react and node.js
        total_experience_months=60,
        candidate_name="Expert Python Dev",
        email="expert@example.com"
    )
    test_db.add(analysis)
    await test_db.commit()

    # Create high candidate rank (but missing must-have skills)
    rank = CandidateRank(
        resume_id=resume.id,
        vacancy_id=vacancy.id,
        rank_score=0.90,  # 90/100 - would be HIGH_PRIORITY
        match_details={"overall_score": 0.90}
    )
    test_db.add(rank)
    await test_db.commit()

    # Apply screening
    screening_service = ScreeningService(test_db)
    outcome = await screening_service.apply_screening_rules(
        resume_id=resume.id,
        vacancy_id=vacancy.id
    )

    print(f"✓ Screening completed for candidate missing must-have skills")
    print(f"  Score: {outcome.score_applied:.2f} (would be HIGH_PRIORITY)")
    print(f"  Tier: {outcome.tier}")
    print(f"  Passed must-have skills: {outcome.passed_must_have_skills}")
    print(f"  Rejection reasons: {outcome.rejection_reasons}")

    # Verify rejected due to missing skills despite high score
    assert outcome.tier == ScreeningService.TIER_REJECT, (
        "Should be REJECT due to missing must-have skills"
    )
    assert outcome.passed_must_have_skills == False, (
        "Should fail must-have skills check"
    )
    assert ScreeningService.REASON_MISSING_SKILLS in outcome.rejection_reasons, (
        "Should have missing_must_have_skills rejection reason"
    )

    print("\n✓ Must-have skills filter working correctly")
    print("  Candidate with high score (90) but missing must-have skills was REJECTED")


@pytest.mark.asyncio
async def test_screening_api_endpoints(client: AsyncClient, test_db: AsyncSession):
    """
    Test screening API endpoints for manual screening.
    """
    print("\n=== Testing Screening API Endpoints ===\n")

    # Create vacancy and screening rule
    vacancy = JobVacancy(
        title="Data Scientist",
        description="Data scientist position",
        required_skills=["python", "machine learning"],
        min_experience_months=48
    )
    test_db.add(vacancy)
    await test_db.commit()
    await test_db.refresh(vacancy)

    # Create screening rule via API
    rule_data = {
        "vacancy_id": str(vacancy.id),
        "min_score_threshold": 50.0,
        "auto_reject_threshold": 30.0,
        "high_priority_threshold": 80.0,
        "must_have_skills": ["python"],
        "auto_reject_with_notification": False,
        "rule_priority": 100,
        "is_active": True
    }

    response = await client.post("/api/screening/rules", json=rule_data)
    assert response.status_code == 201, f"Failed to create screening rule: {response.text}"
    created_rule = response.json()

    print(f"✓ Created screening rule via API: {created_rule['id']}")

    # Get screening rules for vacancy
    response = await client.get(f"/api/screening/rules/{str(vacancy.id)}")
    assert response.status_code == 200
    rules = response.json()

    assert len(rules) >= 1, "Should have at least one screening rule"
    print(f"✓ Retrieved {len(rules)} screening rules for vacancy")

    # Create resume with analysis and rank
    resume = Resume(
        filename="data_scientist.pdf",
        file_path="/tmp/data_scientist.pdf",
        content_type="application/pdf",
        status=ResumeStatus.COMPLETED,
        raw_text="Data scientist with python and ML experience",
        language="en"
    )
    test_db.add(resume)
    await test_db.commit()
    await test_db.refresh(resume)

    analysis = ResumeAnalysis(
        resume_id=resume.id,
        skills=["python", "machine learning", "tensorflow"],
        total_experience_months=60,
        candidate_name="Data Scientist",
        email="ds@example.com"
    )
    test_db.add(analysis)
    await test_db.commit()

    rank = CandidateRank(
        resume_id=resume.id,
        vacancy_id=vacancy.id,
        rank_score=0.82,
        match_details={"overall_score": 0.82}
    )
    test_db.add(rank)
    await test_db.commit()

    # Trigger manual screening via API
    response = await client.post(
        f"/api/screening/screen/{str(resume.id)}/{str(vacancy.id)}",
        json={"force_rescreen": False}
    )
    assert response.status_code == 200, f"Failed to screen candidate: {response.text}"
    screening_result = response.json()

    print(f"✓ Manual screening completed via API")
    print(f"  Tier: {screening_result['tier']}")
    print(f"  Score: {screening_result['score_applied']}")

    assert screening_result["tier"] == ScreeningService.TIER_HIGH_PRIORITY
    assert screening_result["resume_id"] == str(resume.id)
    assert screening_result["vacancy_id"] == str(vacancy.id)

    # Get screening results for vacancy
    response = await client.get(f"/api/screening/results/{str(vacancy.id)}")
    assert response.status_code == 200
    results = response.json()

    assert results["total_results"] >= 1, "Should have at least one screening result"
    assert len(results["results"]) >= 1, "Results list should not be empty"
    print(f"✓ Retrieved {results['total_results']} screening results")

    # Get screening metrics
    response = await client.get("/api/screening/metrics")
    assert response.status_code == 200
    metrics = response.json()

    assert metrics["volume"]["total_screenings"] >= 1
    print(f"✓ Retrieved screening metrics: {metrics['volume']['total_screenings']} total screenings")

    print("\n✓ All screening API endpoints working correctly")


if __name__ == "__main__":
    print("This test requires pytest with async support.")
    print("Run with: pytest backend/tests/integration/test_screening_workflow.py -v")
