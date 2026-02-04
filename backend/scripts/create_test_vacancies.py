#!/usr/bin/env python3
"""
Create test vacancies for pagination testing.

This script creates 50+ test vacancies to verify pagination works correctly.
Run this before manually testing pagination in the browser or with API calls.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from models.job_vacancy import JobVacancy
from database import get_db


# Sample job titles and descriptions for variety
JOB_TITLES = [
    "Senior Python Developer",
    "Middle Python Developer",
    "Junior Python Developer",
    "Full Stack Developer",
    "Frontend Developer",
    "Backend Developer",
    "DevOps Engineer",
    "Data Analyst",
    "Machine Learning Engineer",
    "QA Engineer",
]

LOCATIONS = [
    "Moscow",
    "Saint Petersburg",
    "Kazan",
    "Ekaterinburg",
    "Novosibirsk",
    "Remote",
]

WORK_FORMATS = ["remote", "office", "hybrid"]

ENGLISH_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]

EMPLOYMENT_TYPES = ["full-time", "part-time", "contract"]


async def create_test_vacancies(count: int = 55):
    """Create test vacancies for pagination testing."""
    print(f"=== Creating {count} test vacancies ===\n")

    async for db in get_db():
        created_count = 0

        for i in range(count):
            # Vary the data for each vacancy
            title = f"{JOB_TITLES[i % len(JOB_TITLES)]} #{i+1}"
            work_format = WORK_FORMATS[i % len(WORK_FORMATS)]
            location = LOCATIONS[i % len(LOCATIONS)]

            vacancy = JobVacancy(
                title=title,
                description=f"This is test vacancy #{i+1} for pagination testing. "
                           f"We need to ensure that pagination works correctly with large datasets. "
                           f"Position requires a motivated developer who can work independently.",
                required_skills=["Python", "SQL", "Git"],
                min_experience_months=12 + (i % 5) * 12,  # 12, 24, 36, 48, 60 months
                additional_requirements=["Docker", "Linux", "Git"],
                industry="Technology",
                work_format=work_format,
                location=location,
                salary_min=80000 + (i % 10) * 10000,
                salary_max=120000 + (i % 10) * 10000,
                english_level=ENGLISH_LEVELS[i % len(ENGLISH_LEVELS)],
                employment_type=EMPLOYMENT_TYPES[i % len(EMPLOYMENT_TYPES)],
                source="test_script",
            )

            db.add(vacancy)
            created_count += 1

            if (i + 1) % 10 == 0:
                print(f"Created {i+1}/{count} vacancies...")

        try:
            await db.commit()
            print(f"\n✓ Successfully created {created_count} test vacancies")
            print(f"\nYou can now test pagination by:")
            print(f"  1. Opening http://localhost:8000/api/vacancies/?skip=0&limit=20")
            print(f"  2. Opening http://localhost:5173/vacancies in the browser")
            print(f"  3. Running: python backend/tests/integration/test_vacancy_pagination.py")
        except Exception as e:
            await db.rollback()
            print(f"\n✗ Error creating vacancies: {e}")
            raise


async def count_existing_vacancies():
    """Count existing vacancies in database."""
    from sqlalchemy import select, func

    async for db in get_db():
        result = await db.execute(select(func.count()).select_from(JobVacancy))
        total = result.scalar() or 0
        return total


async def clear_test_vacancies():
    """Clear all test vacancies created by this script."""
    from sqlalchemy import delete

    async for db in get_db():
        result = await db.execute(
            delete(JobVacancy).where(JobVacancy.source == "test_script")
        )
        await db.commit()
        print(f"✓ Deleted {result.rowcount} test vacancies")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create test vacancies for pagination testing")
    parser.add_argument("--count", type=int, default=55, help="Number of vacancies to create (default: 55)")
    parser.add_argument("--clear", action="store_true", help="Clear existing test vacancies")
    parser.add_argument("--count-existing", action="store_true", help="Count existing vacancies")

    args = parser.parse_args()

    if args.count_existing:
        total = asyncio.run(count_existing_vacancies())
        print(f"Existing vacancies in database: {total}")
    elif args.clear:
        asyncio.run(clear_test_vacancies())
    else:
        asyncio.run(create_test_vacancies(args.count))
