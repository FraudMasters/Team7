"""
Show detailed matching info for a specific CV.
"""
import sys
import asyncio
import httpx
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzers import extract_resume_entities
from services.data_extractor.extract import extract_text_from_docx
from sqlalchemy import select
from database import async_session_maker
from models.job_vacancy import JobVacancy


# Vacancy ID map
VACANCY_NAMES = {
    1: ".Net Developer",
    2: "Remote Developer", 
    3: "Junior Developer",
    4: "Backend Developer",
    5: "Software Developer (Java)",
}


async def detailed_analysis(cv_num: int):
    """Show detailed matching analysis."""
    print(f"\n{'='*80}")
    print(f"DETAILED ANALYSIS FOR CV {cv_num}")
    print(f"{'='*80}\n")
    
    # Extract text and skills
    cv_path = Path(f"data/uploads/{cv_num}.docx")
    result = extract_text_from_docx(str(cv_path))
    text = result.get("text", "")
    entities = extract_resume_entities(text)
    resume_skills = entities.get("skills") or entities.get("technical_skills") or []
    
    print(f"Resume skills ({len(resume_skills)}):")
    print(f"  {', '.join(resume_skills[:15])}")
    print()
    
    # Get vacancies
    async with async_session_maker() as session:
        result = await session.execute(select(JobVacancy))
        vacancies = result.scalars().all()
    
    # Match with each vacancy
    from analyzers import EnhancedSkillMatcher
    matcher = EnhancedSkillMatcher()
    
    print("Matching against vacancies:\n")
    
    matches = []
    for i, vacancy in enumerate(sorted(vacancies, key=lambda v: v.id), 1):
        required = vacancy.required_skills or []
        additional = vacancy.additional_requirements or []
        
        match_results = matcher.match_multiple(
            resume_skills=resume_skills,
            required_skills=required,
        )
        
        matched = [s for s, r in match_results.items() if r.get("matched")]
        missing = [s for s, r in match_results.items() if not r.get("matched")]
        
        match_pct = (len(matched) / len(required) * 100) if required else 0
        
        matches.append({
            'id': i,
            'title': vacancy.title,
            'required': required,
            'matched': matched,
            'missing': missing,
            'match_pct': match_pct,
        })
        
        print(f"{i}. {vacancy.title}")
        print(f"   Required: {', '.join(required)}")
        print(f"   Matched: {', '.join(matched) if matched else '(none)'}")
        print(f"   Missing: {', '.join(missing) if missing else '(none)'}")
        print(f"   Match: {match_pct:.1f}%")
        print()
    
    # Get API result
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://localhost:8000/api/vacancies/match-all?resume_id={cv_num}",
            timeout=60.0
        )
        api_result = response.json()
    
    print("API Ranking:")
    for i, match in enumerate(api_result.get('matches', []), 1):
        print(f"  {i}. {match['vacancy_title']} - {match['match_percentage']}%")


if __name__ == "__main__":
    asyncio.run(detailed_analysis(3))  # CV 3 had good NDCG
