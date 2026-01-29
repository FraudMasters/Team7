"""
Load test vacancies and run matching evaluation.
"""
import csv
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from sqlalchemy import select
from database import async_session_maker
from models.job_vacancy import JobVacancy

# Vacancies from CSV
VACANCIES_DATA = [
    {
        "external_id": "e3f78c8c36195e4438286bb9395085a0",
        "title": "Software Developer - .Net",
        "description": """Primary Purpose: Development and maintenance of software applications built using Microsoft stack.
        Essential Skills: C#, JavaScript, MSSQL 2012 or above, MVC, Angular, Asp.Net, JQuery, Visual Studio, TFS, SOLID OOP, WCF, Agile/Scrum.
        Desired: Insurance industry experience, Web API, Entity Framework, Crystal Reports, SSRS, SSIS.""",
        "required_skills": ["C#", "JavaScript", "SQL", "MVC", "Angular", "ASP.NET", "jQuery"],
        "additional_requirements": ["Visual Studio", "TFS", "SOLID", "OOP", "WCF", "Agile", "Scrum"],
        "industry": "Insurance",
        "work_format": "office",
        "location": "New York City",
        "min_experience_months": 60,
    },
    {
        "external_id": "708584f2d49cb195c9fc9d7bee36e699",
        "title": "Remote Software Developer",
        "description": """Software Developer (SME Journeyman) for cyber-security and national defense programs.
        Required: Python, Perl, PHP or C/C++, JavaScript, Java, Ruby, Clojure. Strong Linux/Unix, shell scripting.
        Required: DoD 8570 baseline certification (CISSP, Security+). 3+ years experience. Secret clearance.
        Desired: IPv4, IPv6, tcpdump, PKI, SSL, IPSec, MySQL, PostgreSQL.""",
        "required_skills": ["Python", "Linux", "Unix", "SQL"],
        "additional_requirements": ["Perl", "PHP", "JavaScript", "Java", "C++", "Ruby", "Shell scripting", "Security"],
        "industry": "Defense",
        "work_format": "remote",
        "location": "Remote",
        "min_experience_months": 36,
    },
    {
        "external_id": "72fafc405b891220ce78df7fd4e72a80",
        "title": "Junior Level Software Developer (1-4 years experience)",
        "description": """Financial technology company developing software for Bloomberg terminals.
        Required: PYTHON, Java, C++, SQL, UNIX, database programming.
        Must understand Python memory leakage, garbage collection, efficient parser design.
        BS in Computer Science required.""",
        "required_skills": ["Python", "Java", "C++", "SQL", "UNIX"],
        "additional_requirements": ["Database programming", "Memory management", "Parser design"],
        "industry": "Finance",
        "work_format": "office",
        "location": "Wall Street",
        "min_experience_months": 12,
    },
    {
        "external_id": "5eb96f825590e690d76930c52b9100de",
        "title": "Backend Software Developer",
        "description": """Rapidly growing ratings and reviews platform in Washington D.C.
        Required: LAMP, Drupal, ElasticSearch, REST APIs, Python, Go, AWS, View.js, HubSpot, RESTful APIs.
        Required: Strong OOP, 3+ years RESTful APIs, complex SQL queries, AWS (EC2, EB, IAM, S3, Lambda, Cloudfront).
        Desired: Docker, Drupal, Elastic Search, HTML, CSS, JavaScript.""",
        "required_skills": ["PHP", "Python", "Go", "SQL", "REST", "APIs", "AWS"],
        "additional_requirements": ["LAMP", "Drupal", "ElasticSearch", "JavaScript", "OOP", "Docker"],
        "industry": "B2B Services",
        "work_format": "office",
        "location": "Washington D.C.",
        "min_experience_months": 36,
    },
    {
        "external_id": "296f9b55a3a3eed93ad08924274f2eba",
        "title": "Software Developer",
        "description": """Software Developer for Aberdeen Proving Ground facility.
        Required: Java, C#, SQL, HTTPS, Apache, Eclipse.
        Basic: Bachelor's in CS, 2+ years Java.
        Preferred: C#, Elastic Search, Oracle, web services, Micro-Service Architectures, secure web applications.""",
        "required_skills": ["Java", "C#", "SQL", "Apache", "Eclipse"],
        "additional_requirements": ["HTTPS", "Web services", "Microservices", "Oracle", "Elastic Search"],
        "industry": "Defense",
        "work_format": "office",
        "location": "Aberdeen Proving Ground",
        "min_experience_months": 24,
    },
]


async def load_vacancies():
    """Load test vacancies into database."""
    async with async_session_maker() as session:
        # Check if vacancies already exist
        result = await session.execute(select(JobVacancy))
        existing = result.scalars().all()
        
        if existing:
            print(f"Found {len(existing)} existing vacancies. Clearing...")
            for v in existing:
                await session.delete(v)
            await session.commit()
        
        # Load new vacancies
        for v_data in VACANCIES_DATA:
            vacancy = JobVacancy(**v_data)
            session.add(vacancy)
        
        await session.commit()
        
        # Verify
        result = await session.execute(select(JobVacancy))
        vacancies = result.scalars().all()
        print(f"Loaded {len(vacancies)} vacancies:")
        for v in vacancies:
            print(f"  - {v.title} (external_id: {v.external_id})")


if __name__ == "__main__":
    asyncio.run(load_vacancies())
    print("\nVacancies loaded successfully!")
