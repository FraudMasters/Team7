"""
Migrate test CVs and vacancies to database.
"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, delete
from database import async_session_maker
from models.job_vacancy import JobVacancy
from models.resume import Resume, ResumeStatus


VACANCIES_DATA = [
    {
        "external_id": "e3f78c8c36195e4438286bb9395085a0",
        "source": "test_dataset",
        "title": "Software Developer - .Net",
        "description": "Microsoft stack developer with C#, JavaScript, Angular, ASP.NET skills.",
        "required_skills": ["C#", "JavaScript", "SQL", "MVC", "Angular", "ASP.NET", "jQuery"],
        "additional_requirements": ["Visual Studio", "TFS", "SOLID", "OOP", "WCF", "Agile", "Scrum"],
        "industry": "Insurance",
        "work_format": "office",
        "location": "New York City",
        "min_experience_months": 60,
    },
    {
        "external_id": "708584f2d49cb195c9fc9d7bee36e699",
        "source": "test_dataset",
        "title": "Remote Software Developer",
        "description": "Cyber-security software developer with Python, Linux skills.",
        "required_skills": ["Python", "Linux", "Unix", "SQL"],
        "additional_requirements": ["Perl", "PHP", "JavaScript", "Java", "C++", "Ruby", "Security"],
        "industry": "Defense",
        "work_format": "remote",
        "location": "Remote",
        "min_experience_months": 36,
    },
    {
        "external_id": "72fafc405b891220ce78df7fd4e72a80",
        "source": "test_dataset",
        "title": "Junior Level Software Developer (1-4 years experience)",
        "description": "Financial tech developer with Python, Java, C++ skills.",
        "required_skills": ["Python", "Java", "C++", "SQL", "UNIX"],
        "additional_requirements": ["Database programming", "Memory management"],
        "industry": "Finance",
        "work_format": "office",
        "location": "Wall Street",
        "min_experience_months": 12,
    },
    {
        "external_id": "5eb96f825590e690d76930c52b9100de",
        "source": "test_dataset",
        "title": "Backend Software Developer",
        "description": "Backend developer with PHP, Python, Go, AWS skills.",
        "required_skills": ["PHP", "Python", "Go", "SQL", "REST", "APIs", "AWS"],
        "additional_requirements": ["LAMP", "Drupal", "ElasticSearch", "JavaScript", "OOP", "Docker"],
        "industry": "B2B Services",
        "work_format": "office",
        "location": "Washington D.C.",
        "min_experience_months": 36,
    },
    {
        "external_id": "296f9b55a3a3eed93ad08924274f2eba",
        "source": "test_dataset",
        "title": "Software Developer",
        "description": "Java/C# developer for Aberdeen facility.",
        "required_skills": ["Java", "C#", "SQL", "Apache", "Eclipse"],
        "additional_requirements": ["HTTPS", "Web services", "Microservices", "Oracle"],
        "industry": "Defense",
        "work_format": "office",
        "location": "Aberdeen Proving Ground",
        "min_experience_months": 24,
    },
]


async def clear_test_data():
    async with async_session_maker() as session:
        await session.execute(delete(Resume).where(Resume.filename.like("CV_%")))
        await session.execute(delete(JobVacancy).where(JobVacancy.source == "test_dataset"))
        await session.commit()
        print("Cleared existing test data")


async def migrate_vacancies():
    async with async_session_maker() as session:
        for v_data in VACANCIES_DATA:
            vacancy = JobVacancy(**v_data)
            session.add(vacancy)
        
        await session.commit()
        
        result = await session.execute(select(JobVacancy).where(JobVacancy.source == "test_dataset"))
        vacancies = result.scalars().all()
        
        print(f"\nLoaded {len(vacancies)} test vacancies:")
        for v in vacancies:
            print(f"  [{v.external_id}] {v.title}")
        
        return {v.external_id: str(v.id) for v in vacancies}


async def migrate_resumes():
    UPLOAD_DIR = Path("/app/data/uploads")
    
    async with async_session_maker() as session:
        cv_files = []
        for i in range(1, 100):
            cv_file = UPLOAD_DIR / f"{i}.docx"
            if cv_file.exists():
                cv_files.append((i, cv_file))
        
        print(f"\nFound {len(cv_files)} CV files")
        print("Migrating resumes...")
        
        resumes_created = []
        for cv_num, cv_file in cv_files:
            resume = Resume(
                id=uuid4(),
                filename=f"CV_{cv_num}.docx",
                file_path=str(cv_file),
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                status=ResumeStatus.COMPLETED,
                raw_text=None,
                language="en",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(resume)
            resumes_created.append((cv_num, str(resume.id)))
        
        await session.commit()
        
        print(f"Created {len(resumes_created)} resume records")
        
        return {cv_num: resume_id for cv_num, resume_id in resumes_created}


async def main():
    print("="*80)
    print("MIGRATING TEST DATA TO DATABASE")
    print("="*80)
    
    await clear_test_data()
    vacancy_map = await migrate_vacancies()
    resume_map = await migrate_resumes()
    
    print("\n" + "="*80)
    print("MIGRATION COMPLETE!")
    print("="*80)
    print(f"\nSummary:")
    print(f"  - Test vacancies: {len(vacancy_map)}")
    print(f"  - Test resumes: {len(resume_map)}")
    
    print(f"\nSample resume IDs (first 10):")
    for cv_num in range(1, 11):
        if cv_num in resume_map:
            print(f"  CV {cv_num}: {resume_map[cv_num]}")


if __name__ == "__main__":
    asyncio.run(main())
