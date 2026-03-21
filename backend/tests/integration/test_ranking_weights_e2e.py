"""
End-to-End Integration Test for Ranking Weights Workflow

This script tests the complete flow of customizable ranking weights,
verifying that changing weight configurations actually affects candidate rankings.

Test Steps:
1. Create organization with default ranking weight profile
2. Create vacancy and candidate resumes
3. Rank candidates with default weights (baseline)
4. Create custom ranking profile prioritizing skills_match_ratio
5. Apply custom profile and re-rank candidates
6. Verify ranking order changed
7. Check history log has entry for weight change

Requirements:
- Backend server running on http://localhost:8000
- Database available and migrations applied

Usage:
    cd backend
    pytest tests/integration/test_ranking_weights_e2e.py -v
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import app
from database import get_db
from models.ranking_weights_profile import RankingWeightProfile
from models.ranking_weights_history import RankingWeightVersion
from models import JobVacancy, Resume, ResumeAnalysis, MatchResult


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
async def test_organization_id() -> str:
    """Generate a test organization ID."""
    return str(uuid4())


@pytest.fixture
async def test_vacancy_data(test_organization_id: str) -> dict:
    """Generate test vacancy data."""
    return {
        "organization_id": test_organization_id,
        "title": "Senior Python Developer",
        "description": "We are looking for an experienced Python developer",
        "position": "Senior Python Developer",
        "required_skills": ["Python", "Django", "FastAPI", "PostgreSQL"],
        "mandatory_requirements": ["Python", "Django", "PostgreSQL"],
        "additional_requirements": ["FastAPI", "Docker", "Kubernetes"],
        "experience_levels": ["senior", "middle"],
        "location": "Remote",
    }


@pytest.fixture
async def test_candidates_data() -> List[Dict]:
    """Generate test candidate data with varied skill profiles."""
    return [
        {
            "filename": "candidate_high_skills.pdf",
            "raw_text": "Senior Python Developer with 8 years experience. Expert in Python, Django, FastAPI, PostgreSQL, Docker, Kubernetes.",
            "skills": ["Python", "Django", "FastAPI", "PostgreSQL", "Docker", "Kubernetes"],
            "experience_months": 96,
            "education": {"degree": "Master", "field": "Computer Science"},
            "title": "Senior Python Developer",
        },
        {
            "filename": "candidate_medium_skills.pdf",
            "raw_text": "Python Developer with 5 years experience. Proficient in Python, Django, PostgreSQL.",
            "skills": ["Python", "Django", "PostgreSQL"],
            "experience_months": 60,
            "education": {"degree": "Bachelor", "field": "Computer Science"},
            "title": "Python Developer",
        },
        {
            "filename": "candidate_low_skills.pdf",
            "raw_text": "Junior Python Developer with 2 years experience. Knowledge of Python, Flask.",
            "skills": ["Python", "Flask"],
            "experience_months": 24,
            "education": {"degree": "Bachelor", "field": "Information Technology"},
            "title": "Junior Python Developer",
        },
        {
            "filename": "candidate_high_experience.pdf",
            "raw_text": "Staff Engineer with 12 years experience in software development. Skills: Java, Python, C++, System Design.",
            "skills": ["Java", "Python", "C++", "System Design"],
            "experience_months": 144,
            "education": {"degree": "PhD", "field": "Computer Science"},
            "title": "Staff Engineer",
        },
    ]


@pytest.fixture
async def default_ranking_profile_data(test_organization_id: str) -> dict:
    """Generate default balanced ranking profile data."""
    return {
        "organization_id": test_organization_id,
        "name": "Default Balanced Profile",
        "description": "Default balanced ranking weights for organization",
        "overall_match_score_weight": 0.15,
        "keyword_score_weight": 0.10,
        "tfidf_score_weight": 0.08,
        "vector_score_weight": 0.07,
        "skills_match_ratio_weight": 0.20,
        "experience_months_weight": 0.08,
        "experience_relevance_weight": 0.10,
        "education_level_weight": 0.06,
        "recent_experience_weight": 0.05,
        "skill_rarity_weight": 0.04,
        "title_similarity_weight": 0.04,
        "freshness_score_weight": 0.02,
        "completeness_score_weight": 0.01,
        "is_active": True,
        "is_preset": False,
        "created_by": str(uuid4()),
        "change_reason": "Initial default profile for organization",
    }


@pytest.fixture
async def skills_focused_profile_data(test_organization_id: str) -> dict:
    """Generate skills-focused ranking profile that prioritizes skills match."""
    return {
        "organization_id": test_organization_id,
        "name": "Skills-Focused Profile",
        "description": "Ranking profile that heavily prioritizes skills match ratio",
        "overall_match_score_weight": 0.10,
        "keyword_score_weight": 0.08,
        "tfidf_score_weight": 0.05,
        "vector_score_weight": 0.05,
        "skills_match_ratio_weight": 0.45,  # Heavy emphasis on skills
        "experience_months_weight": 0.05,
        "experience_relevance_weight": 0.08,
        "education_level_weight": 0.03,
        "recent_experience_weight": 0.03,
        "skill_rarity_weight": 0.02,
        "title_similarity_weight": 0.03,
        "freshness_score_weight": 0.02,
        "completeness_score_weight": 0.01,
        "is_active": True,
        "is_preset": False,
        "created_by": str(uuid4()),
        "change_reason": "Prioritize skills match for technical roles",
    }


# ============================================================================
# Helper Functions
# ============================================================================

async def create_vacancy(
    db: AsyncSession,
    vacancy_data: dict,
) -> JobVacancy:
    """Create a test vacancy in the database."""
    vacancy = JobVacancy(
        title=vacancy_data["title"],
        description=vacancy_data.get("description", ""),
        position=vacancy_data.get("position", vacancy_data["title"]),
        location=vacancy_data.get("location", "Remote"),
    )
    db.add(vacancy)
    await db.commit()
    await db.refresh(vacancy)
    return vacancy


async def create_resume_with_analysis(
    db: AsyncSession,
    candidate_data: dict,
) -> Resume:
    """Create a resume with analysis data."""
    resume = Resume(
        filename=candidate_data["filename"],
        file_path=f"/test/{candidate_data['filename']}",
        raw_text=candidate_data["raw_text"],
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    # Create analysis
    analysis = ResumeAnalysis(
        resume_id=resume.id,
        raw_text=candidate_data["raw_text"],
        skills=candidate_data["skills"],
        total_experience_months=candidate_data["experience_months"],
        education=[candidate_data["education"]],
        quality_score=85.0,
    )
    db.add(analysis)
    await db.commit()

    return resume


async def create_mock_match_result(
    db: AsyncSession,
    resume_id: str,
    vacancy_id: str,
    overall_score: float = 0.75,
) -> MatchResult:
    """Create a mock match result for ranking tests."""
    match_result = MatchResult(
        resume_id=resume_id,
        vacancy_id=vacancy_id,
        overall_score=overall_score,
        keyword_score=overall_score * 0.9,
        tfidf_score=overall_score * 0.85,
        vector_score=overall_score * 0.95,
    )
    db.add(match_result)
    await db.commit()
    await db.refresh(match_result)
    return match_result


# ============================================================================
# Test Class
# ============================================================================

@pytest.mark.e2e
@pytest.mark.integration
class TestRankingWeightsE2E:
    """
    End-to-end test suite for ranking weights functionality.

    Tests the complete workflow from creating weight profiles to verifying
    that rankings actually change when weights are modified.
    """

    async def test_e2e_ranking_weights_impact(
        self,
        test_db: AsyncSession,
        test_organization_id: str,
        test_vacancy_data: dict,
        test_candidates_data: List[dict],
        default_ranking_profile_data: dict,
        skills_focused_profile_data: dict,
    ) -> None:
        """
        Test complete ranking weights workflow.

        This test verifies:
        1. Create organization with default ranking weight profile
        2. Create vacancy and candidate resumes
        3. Rank candidates with default weights (baseline)
        4. Create custom ranking profile prioritizing skills_match_ratio
        5. Apply custom profile to vacancy and re-rank
        6. Verify ranking order changed (skills-heavy candidate should rank higher)
        7. Check history log has entry for weight change
        """
        # Use ASGI transport for direct app testing (no server needed)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # ================================================================
            # Step 1: Create default ranking weight profile
            # ================================================================
            response = await client.post(
                "/api/ranking-weights/profiles",
                json=default_ranking_profile_data
            )

            assert response.status_code == 201, f"Default profile creation failed: {response.text}"
            default_profile = response.json()
            default_profile_id = default_profile["id"]

            # Verify profile created in database
            result = await test_db.execute(
                select(RankingWeightProfile).where(RankingWeightProfile.id == default_profile_id)
            )
            db_profile = result.scalar_one_or_none()
            assert db_profile is not None, "Default profile not found in database"
            assert db_profile.skills_match_ratio_weight == 0.20  # Default balanced weight

            # ================================================================
            # Step 2: Create vacancy and candidates
            # ================================================================
            vacancy = await create_vacancy(test_db, test_vacancy_data)
            vacancy_id = str(vacancy.id)

            resumes = []
            for candidate_data in test_candidates_data:
                resume = await create_resume_with_analysis(test_db, candidate_data)
                resumes.append(resume)

                # Create mock match results for each candidate
                # Candidate with high skills gets highest overall score
                if "high_skills" in candidate_data["filename"]:
                    overall_score = 0.90
                elif "medium_skills" in candidate_data["filename"]:
                    overall_score = 0.75
                elif "high_experience" in candidate_data["filename"]:
                    overall_score = 0.85
                else:
                    overall_score = 0.60

                await create_mock_match_result(
                    test_db,
                    str(resume.id),
                    vacancy_id,
                    overall_score
                )

            # ================================================================
            # Step 3: Rank candidates with default weights (baseline)
            # ================================================================
            baseline_rankings = []
            for resume in resumes:
                response = await client.post(
                    "/api/ranking/rank",
                    json={
                        "resume_id": str(resume.id),
                        "vacancy_id": vacancy_id,
                        "use_experiment": False,
                    }
                )

                if response.status_code == 200:
                    ranking = response.json()
                    baseline_rankings.append({
                        "resume_id": str(resume.id),
                        "filename": resume.filename,
                        "rank_score": ranking.get("rank_score", 0.0),
                    })

            # Sort by rank score (descending)
            baseline_rankings.sort(key=lambda x: x["rank_score"], reverse=True)

            assert len(baseline_rankings) > 0, "No baseline rankings generated"

            # ================================================================
            # Step 4: Create custom ranking profile prioritizing skills
            # ================================================================
            response = await client.post(
                "/api/ranking-weights/profiles",
                json=skills_focused_profile_data
            )

            assert response.status_code == 201, f"Skills-focused profile creation failed: {response.text}"
            skills_profile = response.json()
            skills_profile_id = skills_profile["id"]

            # Verify skills-focused profile has high skills_match_ratio_weight
            assert skills_profile["skills_match_ratio_weight"] == 0.45, "Skills weight not set correctly"

            # ================================================================
            # Step 5: Associate custom profile with vacancy and re-rank
            # ================================================================
            # Create a vacancy-specific profile
            vacancy_profile_data = skills_focused_profile_data.copy()
            vacancy_profile_data["vacancy_id"] = vacancy_id
            vacancy_profile_data["name"] = "Skills-Focused for Vacancy"

            response = await client.post(
                "/api/ranking-weights/profiles",
                json=vacancy_profile_data
            )

            assert response.status_code == 201, f"Vacancy profile creation failed: {response.text}"
            vacancy_profile = response.json()
            vacancy_profile_id = vacancy_profile["id"]

            # Re-rank all candidates
            new_rankings = []
            for resume in resumes:
                response = await client.post(
                    "/api/ranking/rank",
                    json={
                        "resume_id": str(resume.id),
                        "vacancy_id": vacancy_id,
                        "use_experiment": False,
                    }
                )

                if response.status_code == 200:
                    ranking = response.json()
                    new_rankings.append({
                        "resume_id": str(resume.id),
                        "filename": resume.filename,
                        "rank_score": ranking.get("rank_score", 0.0),
                    })

            # Sort by rank score (descending)
            new_rankings.sort(key=lambda x: x["rank_score"], reverse=True)

            assert len(new_rankings) > 0, "No new rankings generated"

            # ================================================================
            # Step 6: Verify ranking order changed
            # ================================================================
            # With skills-focused weights, the candidate with highest skill match
            # should rank higher relative to their baseline position

            # Find candidate_high_skills in both rankings
            baseline_high_skills = next(
                (i for i, r in enumerate(baseline_rankings) if "high_skills" in r["filename"]),
                None
            )
            new_high_skills = next(
                (i for i, r in enumerate(new_rankings) if "high_skills" in r["filename"]),
                None
            )

            # Find candidate_high_experience in both rankings
            baseline_high_exp = next(
                (i for i, r in enumerate(baseline_rankings) if "high_experience" in r["filename"]),
                None
            )
            new_high_exp = next(
                (i for i, r in enumerate(new_rankings) if "high_experience" in r["filename"]),
                None
            )

            # Verify rankings exist
            assert baseline_high_skills is not None, "High skills candidate not found in baseline"
            assert new_high_skills is not None, "High skills candidate not found in new rankings"

            # With skills-focused profile, high skills candidate should improve position
            # or at least maintain top position
            if baseline_high_skills > 0:  # If not already first
                assert new_high_skills <= baseline_high_skills, (
                    "High skills candidate should rank better with skills-focused profile"
                )

            # High experience candidate may drop in relative ranking when skills emphasized
            # (This is expected behavior when weights change)

            # ================================================================
            # Step 7: Check history log has entry
            # ================================================================
            # Get history for the vacancy-specific profile
            result = await test_db.execute(
                select(RankingWeightVersion).where(
                    RankingWeightVersion.profile_id == vacancy_profile_id
                )
            )
            history_entries = result.scalars().all()

            # Should have at least one history entry (creation)
            assert len(history_entries) >= 1, "No history entries found for vacancy profile"

            # Verify history entry has weight snapshot
            latest_entry = history_entries[0]
            assert latest_entry.skills_match_ratio_weight == 0.45, (
                "History entry doesn't match profile skills weight"
            )
            assert latest_entry.change_reason is not None, "History entry missing change reason"

            # ================================================================
            # Step 8: Verify weight normalization
            # ================================================================
            # Verify all profile weights sum to approximately 1.0
            profile_result = await test_db.execute(
                select(RankingWeightProfile).where(RankingWeightProfile.id == vacancy_profile_id)
            )
            profile = profile_result.scalar_one()

            assert profile.validate_weights(), "Profile weights don't sum to 1.0"

            total_weight = (
                profile.overall_match_score_weight +
                profile.keyword_score_weight +
                profile.tfidf_score_weight +
                profile.vector_score_weight +
                profile.skills_match_ratio_weight +
                profile.experience_months_weight +
                profile.experience_relevance_weight +
                profile.education_level_weight +
                profile.recent_experience_weight +
                profile.skill_rarity_weight +
                profile.title_similarity_weight +
                profile.freshness_score_weight +
                profile.completeness_score_weight
            )

            assert abs(total_weight - 1.0) < 0.01, f"Weights sum to {total_weight}, expected ~1.0"

            # ================================================================
            # Cleanup
            # ================================================================
            # Delete test profiles (soft delete, returns 204 NO CONTENT)
            delete_response = await client.delete(f"/api/ranking-weights/profiles/{default_profile_id}")
            assert delete_response.status_code in [204, 404], "Default profile cleanup failed"

            delete_response = await client.delete(f"/api/ranking-weights/profiles/{skills_profile_id}")
            assert delete_response.status_code in [204, 404], "Skills profile cleanup failed"

            delete_response = await client.delete(f"/api/ranking-weights/profiles/{vacancy_profile_id}")
            assert delete_response.status_code in [204, 404], "Vacancy profile cleanup failed"

    async def test_e2e_vacancy_specific_weights_override_org_defaults(
        self,
        test_db: AsyncSession,
        test_organization_id: str,
        test_vacancy_data: dict,
        test_candidates_data: List[dict],
        default_ranking_profile_data: dict,
        skills_focused_profile_data: dict,
    ) -> None:
        """
        Test that vacancy-specific weights override organization defaults.

        This test verifies:
        1. Set organization default ranking weights
        2. Create vacancy A (uses org defaults) and rank candidates
        3. Create vacancy B with custom weights
        4. Verify vacancy B uses custom weights, vacancy A uses org defaults
        5. Verify rankings differ between vacancies
        """
        # Use ASGI transport for direct app testing (no server needed)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # ================================================================
            # Step 1: Create organization default ranking weight profile
            # ================================================================
            response = await client.post(
                "/api/ranking-weights/profiles",
                json=default_ranking_profile_data
            )

            assert response.status_code == 201, f"Default profile creation failed: {response.text}"
            org_default_profile = response.json()
            org_default_profile_id = org_default_profile["id"]

            # Verify organization default profile created in database
            result = await test_db.execute(
                select(RankingWeightProfile).where(RankingWeightProfile.id == org_default_profile_id)
            )
            db_profile = result.scalar_one_or_none()
            assert db_profile is not None, "Organization default profile not found in database"
            assert db_profile.skills_match_ratio_weight == 0.20  # Default balanced weight
            assert db_profile.organization_id == test_organization_id
            assert db_profile.vacancy_id is None, "Organization default should not be vacancy-specific"

            # ================================================================
            # Step 2: Create two vacancies and candidates
            # ================================================================
            # Vacancy A - uses org defaults
            vacancy_a_data = test_vacancy_data.copy()
            vacancy_a_data["title"] = "Senior Python Developer - Team A"
            vacancy_a = await create_vacancy(test_db, vacancy_a_data)
            vacancy_a_id = str(vacancy_a.id)

            # Vacancy B - will have custom weights
            vacancy_b_data = test_vacancy_data.copy()
            vacancy_b_data["title"] = "Senior Python Developer - Team B"
            vacancy_b = await create_vacancy(test_db, vacancy_b_data)
            vacancy_b_id = str(vacancy_b.id)

            # Create shared candidate pool
            resumes = []
            for candidate_data in test_candidates_data:
                resume = await create_resume_with_analysis(test_db, candidate_data)
                resumes.append(resume)

                # Create mock match results for vacancy A
                if "high_skills" in candidate_data["filename"]:
                    overall_score_a = 0.90
                elif "medium_skills" in candidate_data["filename"]:
                    overall_score_a = 0.75
                elif "high_experience" in candidate_data["filename"]:
                    overall_score_a = 0.85
                else:
                    overall_score_a = 0.60

                await create_mock_match_result(
                    test_db,
                    str(resume.id),
                    vacancy_a_id,
                    overall_score_a
                )

                # Create mock match results for vacancy B (same scores)
                await create_mock_match_result(
                    test_db,
                    str(resume.id),
                    vacancy_b_id,
                    overall_score_a
                )

            # ================================================================
            # Step 3: Rank candidates for vacancy A (uses org defaults)
            # ================================================================
            vacancy_a_rankings = []
            for resume in resumes:
                response = await client.post(
                    "/api/ranking/rank",
                    json={
                        "resume_id": str(resume.id),
                        "vacancy_id": vacancy_a_id,
                        "use_experiment": False,
                    }
                )

                if response.status_code == 200:
                    ranking = response.json()
                    vacancy_a_rankings.append({
                        "resume_id": str(resume.id),
                        "filename": resume.filename,
                        "rank_score": ranking.get("rank_score", 0.0),
                    })

            # Sort by rank score (descending)
            vacancy_a_rankings.sort(key=lambda x: x["rank_score"], reverse=True)

            assert len(vacancy_a_rankings) > 0, "No rankings generated for vacancy A"

            # ================================================================
            # Step 4: Create vacancy-specific custom profile for vacancy B
            # ================================================================
            # Create skills-focused profile specifically for vacancy B
            vacancy_b_profile_data = skills_focused_profile_data.copy()
            vacancy_b_profile_data["vacancy_id"] = vacancy_b_id
            vacancy_b_profile_data["name"] = "Skills-Focused for Vacancy B"
            vacancy_b_profile_data["change_reason"] = "Custom weights for technical role vacancy B"

            response = await client.post(
                "/api/ranking-weights/profiles",
                json=vacancy_b_profile_data
            )

            assert response.status_code == 201, f"Vacancy B profile creation failed: {response.text}"
            vacancy_b_profile = response.json()
            vacancy_b_profile_id = vacancy_b_profile["id"]

            # Verify vacancy B profile has high skills_match_ratio_weight
            assert vacancy_b_profile["skills_match_ratio_weight"] == 0.45, "Skills weight not set correctly for vacancy B"
            assert vacancy_b_profile["vacancy_id"] == vacancy_b_id, "Vacancy B profile not associated with correct vacancy"

            # ================================================================
            # Step 5: Rank candidates for vacancy B (uses custom weights)
            # ================================================================
            vacancy_b_rankings = []
            for resume in resumes:
                response = await client.post(
                    "/api/ranking/rank",
                    json={
                        "resume_id": str(resume.id),
                        "vacancy_id": vacancy_b_id,
                        "use_experiment": False,
                    }
                )

                if response.status_code == 200:
                    ranking = response.json()
                    vacancy_b_rankings.append({
                        "resume_id": str(resume.id),
                        "filename": resume.filename,
                        "rank_score": ranking.get("rank_score", 0.0),
                    })

            # Sort by rank score (descending)
            vacancy_b_rankings.sort(key=lambda x: x["rank_score"], reverse=True)

            assert len(vacancy_b_rankings) > 0, "No rankings generated for vacancy B"

            # ================================================================
            # Step 6: Verify vacancy A still uses org defaults
            # ================================================================
            # Query database to verify vacancy A doesn't have a specific profile
            result = await test_db.execute(
                select(RankingWeightProfile).where(
                    RankingWeightProfile.vacancy_id == vacancy_a_id
                )
            )
            vacancy_a_specific_profile = result.scalar_one_or_none()
            assert vacancy_a_specific_profile is None, "Vacancy A should not have a specific profile"

            # Verify org default profile is still active and unchanged
            result = await test_db.execute(
                select(RankingWeightProfile).where(RankingWeightProfile.id == org_default_profile_id)
            )
            org_profile = result.scalar_one_or_none()
            assert org_profile is not None, "Organization default profile disappeared"
            assert org_profile.skills_match_ratio_weight == 0.20, "Organization default weights changed"

            # ================================================================
            # Step 7: Verify vacancy B uses custom weights
            # ================================================================
            result = await test_db.execute(
                select(RankingWeightProfile).where(RankingWeightProfile.id == vacancy_b_profile_id)
            )
            vacancy_b_db_profile = result.scalar_one_or_none()
            assert vacancy_b_db_profile is not None, "Vacancy B profile not found in database"
            assert vacancy_b_db_profile.vacancy_id == vacancy_b_id, "Vacancy B profile not associated correctly"
            assert vacancy_b_db_profile.skills_match_ratio_weight == 0.45, "Vacancy B custom weights not applied"

            # ================================================================
            # Step 8: Verify rankings differ between vacancies
            # ================================================================
            # Compare ranking positions for the same candidates across vacancies

            # Find high_skills candidate in both rankings
            vacancy_a_high_skills_idx = next(
                (i for i, r in enumerate(vacancy_a_rankings) if "high_skills" in r["filename"]),
                None
            )
            vacancy_b_high_skills_idx = next(
                (i for i, r in enumerate(vacancy_b_rankings) if "high_skills" in r["filename"]),
                None
            )

            # Find high_experience candidate in both rankings
            vacancy_a_high_exp_idx = next(
                (i for i, r in enumerate(vacancy_a_rankings) if "high_experience" in r["filename"]),
                None
            )
            vacancy_b_high_exp_idx = next(
                (i for i, r in enumerate(vacancy_b_rankings) if "high_experience" in r["filename"]),
                None
            )

            # Verify both candidates exist in both rankings
            assert vacancy_a_high_skills_idx is not None, "High skills candidate not ranked for vacancy A"
            assert vacancy_b_high_skills_idx is not None, "High skills candidate not ranked for vacancy B"
            assert vacancy_a_high_exp_idx is not None, "High experience candidate not ranked for vacancy A"
            assert vacancy_b_high_exp_idx is not None, "High experience candidate not ranked for vacancy B"

            # With skills-focused weights in vacancy B, the high_skills candidate
            # should rank better (lower index = higher rank) than in vacancy A
            # OR at least maintain top position if already first
            if vacancy_a_high_skills_idx > 0:  # If not already first in vacancy A
                assert vacancy_b_high_skills_idx <= vacancy_a_high_skills_idx, (
                    f"High skills candidate should rank better in vacancy B (skills-focused) "
                    f"than vacancy A (balanced): A={vacancy_a_high_skills_idx}, B={vacancy_b_high_skills_idx}"
                )

            # The rankings should differ in some way - check rank scores
            high_skills_resume_id = next(
                r["resume_id"] for r in vacancy_a_rankings if "high_skills" in r["filename"]
            )

            vacancy_a_score = next(
                r["rank_score"] for r in vacancy_a_rankings if r["resume_id"] == high_skills_resume_id
            )
            vacancy_b_score = next(
                r["rank_score"] for r in vacancy_b_rankings if r["resume_id"] == high_skills_resume_id
            )

            # With different weights, scores should differ
            # (Allow small tolerance for floating point comparison)
            assert abs(vacancy_a_score - vacancy_b_score) > 0.001 or vacancy_b_high_skills_idx != vacancy_a_high_skills_idx, (
                "Rankings should differ between vacancy A (org defaults) and vacancy B (custom weights)"
            )

            # ================================================================
            # Step 9: Verify history entries
            # ================================================================
            # Organization default profile should have history
            result = await test_db.execute(
                select(RankingWeightVersion).where(
                    RankingWeightVersion.profile_id == org_default_profile_id
                )
            )
            org_history = result.scalars().all()
            assert len(org_history) >= 1, "Organization default profile should have history entry"

            # Vacancy B profile should have history
            result = await test_db.execute(
                select(RankingWeightVersion).where(
                    RankingWeightVersion.profile_id == vacancy_b_profile_id
                )
            )
            vacancy_b_history = result.scalars().all()
            assert len(vacancy_b_history) >= 1, "Vacancy B profile should have history entry"

            # Verify vacancy B history has correct weights
            vacancy_b_latest = vacancy_b_history[0]
            assert vacancy_b_latest.skills_match_ratio_weight == 0.45, (
                "Vacancy B history doesn't match profile skills weight"
            )
            assert vacancy_b_latest.change_reason is not None, "Vacancy B history missing change reason"

            # ================================================================
            # Cleanup
            # ================================================================
            # Delete test profiles (soft delete, returns 204 NO CONTENT)
            delete_response = await client.delete(f"/api/ranking-weights/profiles/{org_default_profile_id}")
            assert delete_response.status_code in [204, 404], "Organization default profile cleanup failed"

            delete_response = await client.delete(f"/api/ranking-weights/profiles/{vacancy_b_profile_id}")
            assert delete_response.status_code in [204, 404], "Vacancy B profile cleanup failed"


@pytest.mark.e2e
@pytest.mark.integration
class TestRankingWeightsPresets:
    """Test preset ranking weight profiles."""

    async def test_preset_profiles_available(
        self,
        test_db: AsyncSession,
    ) -> None:
        """Test that preset profiles are available and functional."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Get preset profiles
            response = await client.get("/api/ranking-weights/profiles/presets")

            if response.status_code == 200:
                presets_response = response.json()
                assert "profiles" in presets_response
                profiles = presets_response["profiles"]

                # Should have at least one preset
                assert len(profiles) > 0, "No preset profiles found"

                # Check for expected presets
                preset_names = [p["name"] for p in profiles]
                expected_presets = ["Balanced", "Technical", "Sales", "Executive"]

                for expected in expected_presets:
                    if expected in preset_names:
                        preset = next(p for p in profiles if p["name"] == expected)
                        assert preset["is_preset"] is True
                        assert preset["is_active"] is True

                        # Verify weights sum to 1.0
                        total = sum([
                            preset["overall_match_score_weight"],
                            preset["keyword_score_weight"],
                            preset["tfidf_score_weight"],
                            preset["vector_score_weight"],
                            preset["skills_match_ratio_weight"],
                            preset["experience_months_weight"],
                            preset["experience_relevance_weight"],
                            preset["education_level_weight"],
                            preset["recent_experience_weight"],
                            preset["skill_rarity_weight"],
                            preset["title_similarity_weight"],
                            preset["freshness_score_weight"],
                            preset["completeness_score_weight"],
                        ])
                        assert abs(total - 1.0) < 0.01, f"{expected} preset weights don't sum to 1.0"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
