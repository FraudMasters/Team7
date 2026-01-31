"""
Load fresh test data for AI Candidate Ranking system.

This script clears existing test data and loads fresh resumes and vacancies
to ensure accurate metrics when testing the ranking functionality.
"""
import asyncio
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "data_extractor"))

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from config import get_settings
from models import Resume, JobVacancy, ResumeAnalysis, CandidateRank, RankingFeedback, MatchResult
from database import get_db


# Sample resumes for testing
SAMPLE_RESUMES = [
    {
        "filename": "ivanov_developer.pdf",
        "email": "ivanov@example.com",
        "phone": "+7-999-123-4567",
        "raw_text": """
ИВАНОВ ИВАН ИВАНОВИЧ
Senior Python Developer

КОНТАКТЫ
Email: ivanov@example.com
Телефон: +7-999-123-4567
Город: Москва

ОБРАБОТКА
Опыт работы: 6 лет
Python Developer (2021-настоящее время)
- Разработка бэкенда на FastAPI, Django
- Работа с PostgreSQL, Redis
- Оптимизация SQL-запросов
- Docker, Kubernetes

Middle Python Developer (2019-2021)
- Поддержка legacy кода на Python
- Разработка REST API

ОБРАЗОВАНИЕ
МГТУ им. Баумана, Инженер, 2018

НАВЫКИ
Python, Django, FastAPI, PostgreSQL, Redis, Docker, Kubernetes,
Git, Celery, RabbitMQ, Linux, Nginx
        """,
        "extracted_skills": ["python", "django", "fastapi", "postgresql", "redis", "docker", "kubernetes", "git", "celery", "rabbitmq", "linux", "nginx"],
    },
    {
        "filename": "petrova_frontend.pdf",
        "email": "petrova@example.com",
        "phone": "+7-999-234-5678",
        "raw_text": """
ПЕТРОВА МАРИЯ СЕРГЕЕВНА
Middle Frontend Developer

КОНТАКТЫ
Email: petrova@example.com
Телефон: +7-999-234-5678
Город: Санкт-Петербург

ОПЫТ РАБОТЫ
Frontend Developer (2022-настоящее время)
- Разработка на React, TypeScript
- Redux Toolkit, React Router
- Вёрстка по Figma

Junior Frontend Developer (2020-2022)
- HTML/CSS/JavaScript
- Vue.js

ОБРАЗОВАНИЕ
СПбГУ, Бакалавр информатики, 2020

НАВЫКИ
React, TypeScript, JavaScript, Redux, HTML, CSS, Figma,
Vue.js, Git, Webpack, Vite
        """,
        "extracted_skills": ["react", "typescript", "javascript", "redux", "html", "css", "figma", "vue.js", "git", "webpack", "vite"],
    },
    {
        "filename": "sidorov_fullstack.pdf",
        "email": "sidorov@example.com",
        "phone": "+7-999-345-6789",
        "raw_text": """
СИДОРОВ АЛЕКСЕЙ ПЕТРОВИЧ
Fullstack Developer

КОНТАКТЫ
Email: sidorov@example.com
Телефон: +7-999-345-6789
Город: Казань

ОПЫТ РАБОТЫ
Fullstack Developer (2020-настоящее время)
- Backend: Node.js, Express, MongoDB
- Frontend: React, Next.js
- DevOps: AWS, Docker

Backend Developer (2018-2020)
- Python, Django REST Framework
- PostgreSQL, Redis

ОБРАЗОВАНИЕ
КФУ, Магистр компьютерных наук, 2018

НАВЫКИ
JavaScript, Node.js, Express, MongoDB, React, Next.js,
Python, Django, PostgreSQL, Redis, AWS, Docker, Git
        """,
        "extracted_skills": ["javascript", "node.js", "express", "mongodb", "react", "next.js", "python", "django", "postgresql", "redis", "aws", "docker", "git"],
    },
    {
        "filename": "kozlova_data.pdf",
        "email": "kozlova@example.com",
        "phone": "+7-999-456-7890",
        "raw_text": """
КОЗЛОВА ЕЛЕНА ВЛАДИМИРОВНА
Data Analyst

КОНТАКТЫ
Email: kozlova@example.com
Телефон: +7-999-456-7890
Город: Екатеринбург

ОПЫТ РАБОТЫ
Data Analyst (2021-настоящее время)
- Анализ данных в Python (pandas, numpy)
- Визуализация (matplotlib, seaborn)
- SQL-запросы к базе данных
- Отчёты для бизнеса

Junior Analyst (2020-2021)
- Excel, Google Sheets
- Базовая статистика

ОБРАЗОВАНИЕ
УрФУ, Магистр по анализу данных, 2020

НАВЫКИ
Python, pandas, numpy, matplotlib, seaborn, SQL, Excel,
Tableau, машинное обучение (scikit-learn), Jupyter
        """,
        "extracted_skills": ["python", "pandas", "numpy", "matplotlib", "seaborn", "sql", "excel", "tableau", "scikit-learn", "jupyter"],
    },
    {
        "filename": "smirnov_java.pdf",
        "email": "smirnov@example.com",
        "phone": "+7-999-567-8901",
        "raw_text": """
СМИРНОВ ДМИТРИЙ АЛЕКСАНДРОВИЧ
Java Developer

КОНТАКТЫ
Email: smirnov@example.com
Телефон: +7-999-567-8901
Город: Новосибирск

ОПЫТ РАБОТЫ
Senior Java Developer (2019-настоящее время)
- Java 11-17, Spring Boot
- Microservices architecture
- PostgreSQL, MongoDB
- Apache Kafka

Middle Java Developer (2016-2019)
- Java EE, Spring MVC
- Oracle DB

ОБРАЗОВАНИЕ
НГУ, Бакалавр/Магистр CS, 2016

НАВЫКИ
Java, Spring Boot, Spring Security, Hibernate, PostgreSQL,
MongoDB, Kafka, Docker, Kubernetes, Maven, Gradle
        """,
        "extracted_skills": ["java", "spring boot", "spring security", "hibernate", "postgresql", "mongodb", "kafka", "docker", "kubernetes", "maven", "gradle"],
    },
]


# Sample vacancies for testing
SAMPLE_VACANCIES = [
    {
        "title": "Senior Python Developer",
        "description": "Ищем опытного Python разработчика для работы над высоконагруженным проектом.",
        "required_skills": ["python", "fastapi", "postgresql"],
        "min_experience_months": 48,
        "location": "Москва",
        "salary_min": 250000,
        "salary_max": 400000,
    },
    {
        "title": "React Frontend Developer",
        "description": "Разработка современных SPA на React и TypeScript.",
        "required_skills": ["react", "typescript", "javascript"],
        "min_experience_months": 24,
        "location": "Санкт-Петербург",
        "salary_min": 180000,
        "salary_max": 280000,
    },
    {
        "title": "Fullstack Developer",
        "description": "Универсальный разработчик для fullstack проектов.",
        "required_skills": ["python", "javascript", "react"],
        "min_experience_months": 36,
        "location": "Удалённо",
        "salary_min": 200000,
        "salary_max": 350000,
    },
    {
        "title": "Data Analyst",
        "description": "Аналитик данных для работы с бизнес-метриками.",
        "required_skills": ["python", "sql", "pandas"],
        "min_experience_months": 12,
        "location": "Москва",
        "salary_min": 150000,
        "salary_max": 220000,
    },
    {
        "title": "Java Middle Developer",
        "description": "Java разработчик для enterprise проекта.",
        "required_skills": ["java", "spring boot", "postgresql"],
        "min_experience_months": 36,
        "location": "Новосибирск",
        "salary_min": 200000,
        "salary_max": 300000,
    },
]


async def clear_test_data(db: AsyncSession):
    """Clear existing test data related to ranking."""
    print("Clearing existing test data...")

    # Clear ranking tables first (due to foreign keys)
    await db.execute(delete(RankingFeedback))
    await db.execute(delete(CandidateRank))
    await db.execute(delete(MatchResult))

    # Clear resumes and analyses
    await db.execute(delete(ResumeAnalysis))
    await db.execute(delete(Resume))

    # Clear vacancies
    await db.execute(delete(JobVacancy))

    await db.commit()
    print("Test data cleared.")


async def load_resumes(db: AsyncSession) -> list:
    """Load sample resumes."""
    print("Loading sample resumes...")

    resume_ids = []

    for resume_data in SAMPLE_RESUMES:
        resume = Resume(
            filename=resume_data["filename"],
            file_path=f"/data/uploads/{resume_data['filename']}",
            content_type="application/pdf",
            status="COMPLETED",
            raw_text=resume_data["raw_text"],
        )
        db.add(resume)
        await db.flush()

        # Create resume analysis
        now = datetime.utcnow()
        analysis = ResumeAnalysis(
            resume_id=resume.id,
            skills=resume_data["extracted_skills"],
            raw_text=resume_data["raw_text"],
            quality_score=75,
            created_at=now,
            updated_at=now,
        )
        db.add(analysis)

        resume_ids.append(resume.id)
        print(f"  - Created resume: {resume_data['filename']} ({resume.id})")

    await db.commit()
    print(f"Loaded {len(resume_ids)} resumes.")
    return resume_ids


async def load_vacancies(db: AsyncSession) -> list:
    """Load sample vacancies."""
    print("Loading sample vacancies...")

    vacancy_ids = []

    for vacancy_data in SAMPLE_VACANCIES:
        vacancy = JobVacancy(**vacancy_data)
        db.add(vacancy)
        await db.flush()
        vacancy_ids.append(vacancy.id)
        print(f"  - Created vacancy: {vacancy_data['title']} ({vacancy.id})")

    await db.commit()
    print(f"Loaded {len(vacancy_ids)} vacancies.")
    return vacancy_ids


async def main():
    """Main function to load test data."""
    settings = get_settings()

    # Create async engine
    engine = create_async_engine(
        settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False,
    )

    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as db:
        # Clear existing data
        await clear_test_data(db)

        # Load fresh data
        resume_ids = await load_resumes(db)
        vacancy_ids = await load_vacancies(db)

        print("\n" + "="*50)
        print("Test data loaded successfully!")
        print("="*50)
        print(f"\nResumes created: {len(resume_ids)}")
        print(f"Vacancies created: {len(vacancy_ids)}")

        print("\nResume IDs:")
        for rid in resume_ids:
            print(f"  - {rid}")

        print("\nVacancy IDs:")
        for vid in vacancy_ids:
            print(f"  - {vid}")

        print("\nYou can now test the ranking API with these IDs.")


if __name__ == "__main__":
    asyncio.run(main())
