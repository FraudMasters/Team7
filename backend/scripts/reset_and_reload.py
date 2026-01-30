#!/usr/bin/env python3
"""
Reset database and reload test data.
Clears all resumes, analyses, and match results, then reloads fresh data.
"""
import asyncio
import sys
import os
import glob
import csv
import uuid
import time
import random
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import async_session_maker, engine
from models.resume import Resume, ResumeStatus
from models.resume_analysis import ResumeAnalysis
from models.match_result import MatchResult
from models.job_vacancy import JobVacancy
from sqlalchemy import delete, select, text
from services.data_extractor.extract import extract_text_from_pdf, extract_text_from_docx
from analyzers.hf_skill_extractor import extract_resume_skills, extract_resume_keywords
from analyzers.ner_extractor import extract_resume_entities
from analyzers.analysis_saver import save_resume_analysis
from langdetect import detect

# Configuration
TEST_DATA_DIR = "./testdata/vacancy-resume-matching-dataset"
# Alternative path if running inside container
if not os.path.exists(TEST_DATA_DIR):
    TEST_DATA_DIR = "./testdata"


async def clear_database():
    """Clear all resume-related data."""
    print("Clearing database...")

    async with async_session_maker() as db:
        # Delete match results
        await db.execute(delete(MatchResult))
        # Delete resume analyses
        await db.execute(delete(ResumeAnalysis))
        # Delete resumes
        await db.execute(delete(Resume))
        # Delete vacancies (optional - keep them if needed)
        await db.execute(delete(JobVacancy))

        await db.commit()
        print("  Database cleared")


async def load_resumes(resume_dir: str):
    """Load resumes from directory."""
    print(f"Loading resumes from {resume_dir}...")

    resume_files = []
    for ext in ['*.pdf', '*.PDF', '*.docx', '*.DOCX']:
        resume_files.extend(glob.glob(os.path.join(resume_dir, ext)))

    print(f"  Found {len(resume_files)} resume files")

    loaded = 0
    failed = 0

    async with async_session_maker() as db:
        for resume_path in resume_files:
            filename = os.path.basename(resume_path)

            # Check if already exists
            existing = await db.execute(
                select(Resume).where(Resume.filename == filename)
            )
            if existing.scalar_one_or_none():
                print(f"  Skipping (duplicate): {filename}")
                continue

            # Extract text
            try:
                if filename.lower().endswith('.pdf'):
                    result = extract_text_from_pdf(resume_path)
                else:
                    result = extract_text_from_docx(resume_path)

                text = result.get('text', '')

                if not text or len(text) < 50:
                    print(f"  Skipping (no text): {filename}")
                    failed += 1
                    continue

                # Detect language
                try:
                    lang_code = detect(text[:1000])
                    if lang_code == 'ru':
                        language = 'ru'
                    elif lang_code == 'en':
                        language = 'en'
                    else:
                        language = lang_code
                except:
                    language = 'en'

                # Extract skills with pattern matching (cleaner results)
                skills = extract_resume_skills(
                    text, method='pattern', top_n=30
                )
                skills_list = skills.get('skills', [])

                # Extract entities
                entities = extract_resume_entities(text)

                # Determine content type
                content_type = 'application/pdf' if filename.lower().endswith('.pdf') else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

                # Create resume
                resume = Resume(
                    id=uuid.uuid4(),
                    filename=filename,
                    file_path=resume_path,
                    content_type=content_type,
                    status=ResumeStatus.COMPLETED,
                    language=language,
                    raw_text=text[:10000],  # Store sample
                )
                db.add(resume)
                await db.flush()  # Get the ID

                # Simulate processing time (1-3 seconds)
                processing_time = 1.0 + random.random() * 2.0

                # Save analysis
                await save_resume_analysis(
                    db=db,
                    resume_id=resume.id,
                    raw_text=text[:50000],
                    language=language,
                    skills=skills_list,
                    keywords=[{'keyword': s, 'score': 0.8} for s in skills_list[:20]],
                    entities=entities,
                    quality_score=75,  # Default good score
                    processing_time_seconds=processing_time,
                    analyzer_version="2.0.0"
                )

                loaded += 1
                print(f"  Loaded: {filename} ({len(skills_list)} skills, lang={language})")

            except Exception as e:
                print(f"  ERROR loading {filename}: {str(e)[:100]}")
                await db.rollback()
                failed += 1

        await db.commit()

    print(f"\nResumes loaded: {loaded}, failed: {failed}")
    return loaded


async def load_vacancies(csv_path: str):
    """Load vacancies from CSV file."""
    print(f"\nLoading vacancies from {csv_path}...")

    loaded = 0

    async with async_session_maker() as db:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    # Check if already exists
                    existing = await db.execute(
                        select(JobVacancy).where(
                            JobVacancy.title == row.get('job_title', 'Unknown')
                        )
                    )
                    if existing.scalar_one_or_none():
                        continue

                    # Parse required skills from description
                    description = row.get('job_description', '')
                    title = row.get('job_title', 'Unknown')

                    # Extract skills from description (pattern matching for cleaner results)
                    skills_result = extract_resume_skills(
                        description, method='pattern', top_n=20
                    )
                    required_skills = skills_result.get('skills', [])[:15]

                    vacancy = JobVacancy(
                        title=title,
                        description=description[:5000],
                        location='Remote',
                        work_format='remote',
                        required_skills=required_skills,
                        min_experience_months=36
                    )
                    db.add(vacancy)
                    loaded += 1
                    print(f"  Loaded: {title} ({len(required_skills)} skills)")

                except Exception as e:
                    print(f"  ERROR loading vacancy: {str(e)[:100]}")

        await db.commit()

    print(f"Vacancies loaded: {loaded}")
    return loaded


async def main():
    """Main function."""
    print("=" * 50)
    print("RESET AND RELOAD TEST DATA")
    print("=" * 50)
    print()

    # Check test data directory
    resume_dir = os.path.join(TEST_DATA_DIR, 'CV')
    vacancy_csv = os.path.join(TEST_DATA_DIR, '5_vacancies.csv')

    if not os.path.exists(resume_dir):
        print(f"ERROR: Resume directory not found: {resume_dir}")
        return

    # Step 1: Clear database
    await clear_database()

    # Step 2: Load resumes
    resumes_count = await load_resumes(resume_dir)

    # Step 3: Load vacancies
    vacancies_count = 0
    if os.path.exists(vacancy_csv):
        vacancies_count = await load_vacancies(vacancy_csv)

    print()
    print("=" * 50)
    print(f"COMPLETE: {resumes_count} resumes, {vacancies_count} vacancies")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
