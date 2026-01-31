#!/usr/bin/env python3
"""
Performance Verification Script for Advanced Search

This script verifies that search performance meets the sub-2 second requirement
with 10,000+ candidates in the database, as specified in the acceptance criteria.

Acceptance Criterion: "Search performance optimization (sub-2 second response for >10k candidates)"
"""
import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from httpx import AsyncClient, ASGITransport

from main import app
from database import get_db
from models.resume import Resume, ResumeStatus
from models.resume_analysis import ResumeAnalysis
from models.hiring_stage import HiringStage, HiringStageName
import random

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_performance_10k.db"


async def create_large_dataset(db: AsyncSession, num_candidates: int = 10000):
    """
    Create a large dataset of candidates for performance testing.
    """
    print(f"\n{'='*60}")
    print(f"Creating {num_candidates} test candidates...")
    print(f"{'='*60}\n")

    # Define skill pools
    skill_pools = {
        "backend": [
            "Python", "Java", "Go", "Node.js", "Django", "FastAPI", "Flask",
            "PostgreSQL", "MongoDB", "Redis", "Kafka", "Docker", "Kubernetes"
        ],
        "frontend": [
            "React", "Vue", "Angular", "TypeScript", "JavaScript", "HTML",
            "CSS", "Next.js", "Redux", "Webpack"
        ],
        "data": [
            "Python", "R", "SQL", "TensorFlow", "PyTorch", "Pandas", "NumPy",
            "Scikit-learn", "Tableau", "Power BI", "Apache Spark"
        ],
        "devops": [
            "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Terraform",
            "Ansible", "Jenkins", "GitLab CI", "CircleCI"
        ],
        "mobile": [
            "Swift", "Kotlin", "React Native", "Flutter", "Objective-C",
            "Android", "iOS", "Xamarin", "Java"
        ]
    }

    locations = [
        "Remote", "New York", "San Francisco", "London", "Berlin",
        "Toronto", "Sydney", "Singapore", "Tokyo", "Amsterdam"
    ]

    education_levels = [
        {"degree": "PhD", "field": "Computer Science"},
        {"degree": "PhD", "field": "Data Science"},
        {"degree": "M.Sc", "field": "Computer Science"},
        {"degree": "M.Sc", "field": "Software Engineering"},
        {"degree": "M.Sc", "field": "Data Science"},
        {"degree": "M.Sc", "field": "Information Technology"},
        {"degree": "B.Sc", "field": "Computer Science"},
        {"degree": "B.Sc", "field": "Software Engineering"},
        {"degree": "B.Sc", "field": "Information Technology"},
        {"degree": "B.Sc", "field": "Computer Engineering"},
        {"degree": "MBA", "field": "Business Administration"},
        {"degree": "Diploma", "field": "Software Development"}
    ]

    batch_size = 500
    for batch_start in range(0, num_candidates, batch_size):
        batch_end = min(batch_start + batch_size, num_candidates)

        for i in range(batch_start, batch_end):
            role_type = random.choice(list(skill_pools.keys()))
            skills = random.sample(skill_pools[role_type], k=random.randint(3, 8))

            # Add cross-role skills
            if random.random() < 0.3:
                extra_role = random.choice(list(skill_pools.keys()))
                if extra_role != role_type:
                    skills.extend(random.sample(skill_pools[extra_role], k=random.randint(1, 2)))
                    skills = list(set(skills))

            experience_months = random.randint(12, 180)
            location = random.choice(locations)
            education = random.choice(education_levels)

            resume = Resume(
                filename=f"candidate_{i}_{role_type}.pdf",
                file_path=f"/test/candidates/candidate_{i}.pdf",
                status=ResumeStatus.COMPLETED,
                raw_text=f"Candidate {i} - {role_type.capitalize()} Developer with "
                        f"{experience_months // 12} years experience in {', '.join(skills)}. "
                        f"Located in {location}. "
                        f"Education: {education['degree']} in {education['field']}.",
                location=location,
            )
            db.add(resume)
            await db.flush()

            analysis = ResumeAnalysis(
                resume_id=resume.id,
                raw_text=resume.raw_text,
                skills=skills,
                total_experience_months=experience_months,
                education=[education],
                language="en",
                quality_score=random.uniform(60.0, 95.0),
            )
            db.add(analysis)

            stage_name = random.choice([
                HiringStageName.APPLIED.value,
                HiringStageName.SCREENING.value,
                HiringStageName.INTERVIEW.value,
                HiringStageName.OFFER.value,
            ])
            stage = HiringStage(
                resume_id=resume.id,
                stage_name=stage_name,
            )
            db.add(stage)

        await db.commit()
        progress = (batch_end / num_candidates) * 100
        print(f"Progress: {batch_end}/{num_candidates} candidates ({progress:.1f}%)")

    print(f"\n✓ Successfully created {num_candidates} test candidates\n")


async def verify_search_performance(client: AsyncClient, db: AsyncSession):
    """
    Verify search performance with complex queries and filters.
    """
    print(f"\n{'='*60}")
    print("PERFORMANCE VERIFICATION TEST")
    print(f"{'='*60}\n")

    test_cases = [
        {
            "name": "Complex Boolean Query with Filters",
            "query": "Python AND (Django OR FastAPI OR Flask)",
            "filters": {
                "min_experience_years": 3,
                "max_experience_years": 10,
                "skills": ["Python"],
                "location": "Remote",
            },
            "sort_by": "relevance",
            "limit": 50,
        },
        {
            "name": "Filters Only (No Text Query)",
            "filters": {
                "min_experience_years": 5,
                "max_experience_years": 15,
                "skills": ["Python", "React"],
            },
            "sort_by": "experience",
            "limit": 100,
        },
        {
            "name": "Simple Full-Text Query",
            "query": "Python Developer",
            "limit": 50,
        },
        {
            "name": "Multi-Skill Filter with Experience Range",
            "filters": {
                "min_experience_years": 2,
                "max_experience_years": 8,
                "skills": ["Docker", "Kubernetes", "AWS"],
            },
            "sort_by": "experience",
            "limit": 50,
        },
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print("-" * 60)

        start_time = time.time()

        response = await client.post(
            "/api/search/candidates",
            json=test_case
        )

        end_time = time.time()
        execution_time = end_time - start_time

        if response.status_code == 200:
            data = response.json()
            passed = execution_time < 2.0

            result = {
                "test": test_case['name'],
                "execution_time": execution_time,
                "results_count": data.get('total', 0),
                "server_time": data.get('execution_time_seconds', 0),
                "passed": passed,
            }

            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status} - Time: {execution_time:.3f}s (requirement: < 2.0s)")
            print(f"  Results: {data.get('total', 0)} candidates")
            print(f"  Server time: {data.get('execution_time_seconds', 0):.3f}s")

            if not passed:
                print(f"  ⚠ PERFORMANCE CRITICAL: Exceeds 2 second requirement!")

            results.append(result)
        else:
            print(f"✗ FAIL - HTTP {response.status_code}")
            results.append({
                "test": test_case['name'],
                "error": f"HTTP {response.status_code}",
                "passed": False,
            })

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}\n")

    passed_count = sum(1 for r in results if r.get('passed', False))
    total_count = len(results)

    for result in results:
        status = "✓" if result.get('passed', False) else "✗"
        time_str = f"{result.get('execution_time', 0):.3f}s" if 'execution_time' in result else "ERROR"
        print(f"{status} {result['test']}: {time_str}")

    print(f"\nTotal: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print(f"\n✓✓✓ ALL PERFORMANCE TESTS PASSED ✓✓✓")
        print(f"Search performance meets sub-2 second requirement!")
        return True
    else:
        print(f"\n✗✗✗ SOME PERFORMANCE TESTS FAILED ✗✗✗")
        print(f"Search performance does NOT meet requirements")
        return False


async def main():
    """Main execution function."""
    print("\n" + "="*60)
    print("ADVANCED SEARCH PERFORMANCE VERIFICATION")
    print("Acceptance Criterion: Sub-2 second response with 10k+ candidates")
    print("="*60)

    # Create test database
    print("\nInitializing test database...")
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Create tables
        from models.base import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Create large dataset
        await create_large_dataset(db, num_candidates=10000)

        # Create test client
        async def override_get_db():
            yield db

        app.dependency_overrides[get_db] = override_get_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Verify performance
            success = await verify_search_performance(client, db)

        app.dependency_overrides.clear()

    await engine.dispose()

    # Cleanup test database
    print("\nCleaning up test database...")
    import os
    try:
        if os.path.exists("./test_performance_10k.db"):
            os.remove("./test_performance_10k.db")
            print("✓ Test database removed")
    except Exception as e:
        print(f"Warning: Could not remove test database: {e}")

    print("\n" + "="*60)
    if success:
        print("VERIFICATION COMPLETE: ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("VERIFICATION FAILED: PERFORMANCE BELOW REQUIREMENTS")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
