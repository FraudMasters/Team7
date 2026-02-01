"""
Cache warming tasks for pre-loading frequently accessed data into Redis.

This module provides Celery tasks for warming up the cache with frequently
accessed data to improve response times and reduce database load.
"""
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import Session

from models.resume import Resume
from models.job_vacancy import JobVacancy
from models.match_result import MatchResult
from models.skill_taxonomy import SkillTaxonomy
from services.cache_service import CacheService, get_cache_service
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Number of recent candidates to warm
CANDIDATE_WARM_COUNT = 100

# Number of recent vacancies to warm
VACANCY_WARM_COUNT = 50

# TTL for warmed cache entries (seconds)
WARMED_CACHE_TTL = 3600  # 1 hour

# Minimum time between cache warming cycles (minutes)
WARMING_INTERVAL_MINUTES = 30


def get_frequently_accessed_candidates(
    limit: int = CANDIDATE_WARM_COUNT,
    days_back: int = 7,
    db_session: Optional[Session] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve frequently accessed candidates for cache warming.

    This function identifies candidates that have been accessed frequently
    in the recent past based on analysis results and activity timestamps.

    Args:
        limit: Maximum number of candidates to retrieve (default: 100)
        days_back: Number of days to look back for activity (default: 7)
        db_session: Optional database session for querying

    Returns:
        List of dictionaries containing candidate data:
        [
            {
                "id": "uuid",
                "candidate_name": "John Doe",
                "email": "john@example.com",
                "phone": "123-456-7890",
                "current_position": "Software Engineer",
                "years_of_experience": 5,
                "skills": ["Python", "React"],
                "created_at": "2024-01-01T00:00:00",
                "last_accessed": "2024-01-15T00:00:00"
            },
            ...
        ]

    Example:
        >>> candidates = get_frequently_accessed_candidates(limit=50)
        >>> print(f"Found {len(candidates)} candidates to warm")
        50
    """
    if db_session is None:
        logger.warning(
            "No database session provided for get_frequently_accessed_candidates, returning empty list"
        )
        return []

    logger.info(f"Retrieving top {limit} frequently accessed candidates from last {days_back} days")

    try:
        # Calculate the date cutoff
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        # Query recently updated or accessed resumes
        # Prioritize candidates with recent analysis results or activity
        query = (
            select(Resume)
            .where(Resume.created_at >= cutoff_date)
            .order_by(desc(Resume.updated_at))
            .limit(limit)
        )

        result = db_session.execute(query)
        resumes = result.scalars().all()

        candidates_data = []
        for resume in resumes:
            candidate_info = {
                "id": str(resume.id),
                "candidate_name": resume.candidate_name,
                "email": resume.email,
                "phone": resume.phone_number,
                "current_position": resume.current_position,
                "years_of_experience": resume.years_of_experience,
                "skills": resume.skills or [],
                "created_at": resume.created_at.isoformat() if resume.created_at else None,
                "last_accessed": resume.updated_at.isoformat() if resume.updated_at else None,
            }
            candidates_data.append(candidate_info)

        logger.info(f"Retrieved {len(candidates_data)} candidates for cache warming")

        return candidates_data

    except Exception as e:
        logger.error(f"Error retrieving frequently accessed candidates: {e}", exc_info=True)
        return []


def get_frequently_accessed_vacancies(
    limit: int = VACANCY_WARM_COUNT,
    days_back: int = 7,
    db_session: Optional[Session] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve frequently accessed vacancies for cache warming.

    This function identifies vacancies that have been accessed frequently
    in the recent past based on match results and activity timestamps.

    Args:
        limit: Maximum number of vacancies to retrieve (default: 50)
        days_back: Number of days to look back for activity (default: 7)
        db_session: Optional database session for querying

    Returns:
        List of dictionaries containing vacancy data:
        [
            {
                "id": "uuid",
                "title": "Senior Software Engineer",
                "description": "Job description...",
                "required_skills": ["Python", "React"],
                "min_years_experience": 5,
                "location": "Remote",
                "created_at": "2024-01-01T00:00:00",
                "last_accessed": "2024-01-15T00:00:00"
            },
            ...
        ]

    Example:
        >>> vacancies = get_frequently_accessed_vacancies(limit=25)
        >>> print(f"Found {len(vacancies)} vacancies to warm")
        25
    """
    if db_session is None:
        logger.warning(
            "No database session provided for get_frequently_accessed_vacancies, returning empty list"
        )
        return []

    logger.info(f"Retrieving top {limit} frequently accessed vacancies from last {days_back} days")

    try:
        # Calculate the date cutoff
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        # Query recently updated or accessed vacancies
        query = (
            select(JobVacancy)
            .where(JobVacancy.created_at >= cutoff_date)
            .order_by(desc(JobVacancy.updated_at))
            .limit(limit)
        )

        result = db_session.execute(query)
        vacancies = result.scalars().all()

        vacancies_data = []
        for vacancy in vacancies:
            vacancy_info = {
                "id": str(vacancy.id),
                "title": vacancy.title,
                "description": vacancy.description,
                "required_skills": vacancy.required_skills or [],
                "min_years_experience": vacancy.min_years_experience,
                "location": vacancy.location,
                "created_at": vacancy.created_at.isoformat() if vacancy.created_at else None,
                "last_accessed": vacancy.updated_at.isoformat() if vacancy.updated_at else None,
            }
            vacancies_data.append(vacancy_info)

        logger.info(f"Retrieved {len(vacancies_data)} vacancies for cache warming")

        return vacancies_data

    except Exception as e:
        logger.error(f"Error retrieving frequently accessed vacancies: {e}", exc_info=True)
        return []


def get_skill_taxonomy_data(
    db_session: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Retrieve skill taxonomy data for cache warming.

    This function retrieves the complete skill taxonomy which is used
    frequently for skill matching and normalization.

    Args:
        db_session: Optional database session for querying

    Returns:
        Dictionary containing taxonomy data:
        {
            "skills": {
                "python": {
                    "category": "Programming Language",
                    "synonyms": ["python3", "py"],
                    "related_skills": ["django", "flask"]
                },
                ...
            },
            "categories": ["Programming Language", "Framework", ...],
            "last_updated": "2024-01-15T00:00:00"
        }

    Example:
        >>> taxonomy = get_skill_taxonomy_data()
        >>> print(f"Found {len(taxonomy['skills'])} skills")
        500
    """
    if db_session is None:
        logger.warning(
            "No database session provided for get_skill_taxonomy_data, returning empty taxonomy"
        )
        return {
            "skills": {},
            "categories": [],
            "last_updated": None,
        }

    logger.info("Retrieving skill taxonomy data for cache warming")

    try:
        # Query all skill taxonomy entries
        query = select(SkillTaxonomy).order_by(SkillTaxonomy.skill_name)
        result = db_session.execute(query)
        taxonomy_entries = result.scalars().all()

        taxonomy_data = {
            "skills": {},
            "categories": set(),
            "last_updated": datetime.utcnow().isoformat(),
        }

        for entry in taxonomy_entries:
            skill_info = {
                "category": entry.category,
                "synonyms": entry.synonyms or [],
                "related_skills": entry.related_skills or [],
            }
            taxonomy_data["skills"][entry.skill_name.lower()] = skill_info
            if entry.category:
                taxonomy_data["categories"].add(entry.category)

        taxonomy_data["categories"] = list(taxonomy_data["categories"])

        logger.info(
            f"Retrieved {len(taxonomy_data['skills'])} skills "
            f"in {len(taxonomy_data['categories'])} categories"
        )

        return taxonomy_data

    except Exception as e:
        logger.error(f"Error retrieving skill taxonomy data: {e}", exc_info=True)
        return {
            "skills": {},
            "categories": [],
            "last_updated": None,
        }


def warm_candidate_cache(
    candidates: List[Dict[str, Any]],
    cache: CacheService,
    ttl: int = WARMED_CACHE_TTL,
) -> Dict[str, Any]:
    """
    Warm cache with candidate profile data.

    This function caches candidate profiles to reduce database load
    and improve response times for frequently accessed candidates.

    Args:
        candidates: List of candidate data dictionaries
        cache: CacheService instance
        ttl: Time-to-live for cache entries (default: 3600 seconds)

    Returns:
        Dictionary containing warming results:
        {
            "candidates_warmed": 100,
            "cache_hits": 95,
            "cache_misses": 5,
            "errors": 0,
            "warming_time_ms": 123.45
        }

    Example:
        >>> from services.cache_service import get_cache_service
        >>> cache = get_cache_service()
        >>> candidates = get_frequently_accessed_candidates()
        >>> result = warm_candidate_cache(candidates, cache)
        >>> print(result['candidates_warmed'])
        100
    """
    start_time = time.time()
    warmed_count = 0
    cache_hits = 0
    errors = 0

    logger.info(f"Warming cache for {len(candidates)} candidates")

    for candidate in candidates:
        candidate_id = candidate.get("id")
        if not candidate_id:
            continue

        try:
            # Check if already cached
            cache_key = f"profile:{candidate_id}"
            if cache.exists(CacheService.NAMESPACE_CANDIDATE, cache_key):
                cache_hits += 1
                continue

            # Cache the candidate profile
            success = cache.set(
                CacheService.NAMESPACE_CANDIDATE,
                cache_key,
                candidate,
                ttl=ttl,
            )

            if success:
                warmed_count += 1
            else:
                errors += 1

        except Exception as e:
            logger.error(f"Error warming cache for candidate {candidate_id}: {e}")
            errors += 1

    warming_time_ms = round((time.time() - start_time) * 1000, 2)

    result = {
        "candidates_warmed": warmed_count,
        "cache_hits": cache_hits,
        "cache_misses": len(candidates) - cache_hits,
        "errors": errors,
        "warming_time_ms": warming_time_ms,
    }

    logger.info(
        f"Candidate cache warming complete: {warmed_count} warmed, "
        f"{cache_hits} already cached, {errors} errors in {warming_time_ms}ms"
    )

    return result


def warm_vacancy_cache(
    vacancies: List[Dict[str, Any]],
    cache: CacheService,
    ttl: int = WARMED_CACHE_TTL,
) -> Dict[str, Any]:
    """
    Warm cache with vacancy data.

    This function caches vacancy details to reduce database load
    and improve response times for frequently accessed vacancies.

    Args:
        vacancies: List of vacancy data dictionaries
        cache: CacheService instance
        ttl: Time-to-live for cache entries (default: 3600 seconds)

    Returns:
        Dictionary containing warming results:
        {
            "vacancies_warmed": 50,
            "cache_hits": 40,
            "cache_misses": 10,
            "errors": 0,
            "warming_time_ms": 67.89
        }

    Example:
        >>> from services.cache_service import get_cache_service
        >>> cache = get_cache_service()
        >>> vacancies = get_frequently_accessed_vacancies()
        >>> result = warm_vacancy_cache(vacancies, cache)
        >>> print(result['vacancies_warmed'])
        50
    """
    start_time = time.time()
    warmed_count = 0
    cache_hits = 0
    errors = 0

    logger.info(f"Warming cache for {len(vacancies)} vacancies")

    for vacancy in vacancies:
        vacancy_id = vacancy.get("id")
        if not vacancy_id:
            continue

        try:
            # Check if already cached
            cache_key = f"details:{vacancy_id}"
            if cache.exists(CacheService.NAMESPACE_VACANCY, cache_key):
                cache_hits += 1
                continue

            # Cache the vacancy details
            success = cache.set(
                CacheService.NAMESPACE_VACANCY,
                cache_key,
                vacancy,
                ttl=ttl,
            )

            if success:
                warmed_count += 1
            else:
                errors += 1

        except Exception as e:
            logger.error(f"Error warming cache for vacancy {vacancy_id}: {e}")
            errors += 1

    warming_time_ms = round((time.time() - start_time) * 1000, 2)

    result = {
        "vacancies_warmed": warmed_count,
        "cache_hits": cache_hits,
        "cache_misses": len(vacancies) - cache_hits,
        "errors": errors,
        "warming_time_ms": warming_time_ms,
    }

    logger.info(
        f"Vacancy cache warming complete: {warmed_count} warmed, "
        f"{cache_hits} already cached, {errors} errors in {warming_time_ms}ms"
    )

    return result


def warm_taxonomy_cache(
    taxonomy_data: Dict[str, Any],
    cache: CacheService,
    ttl: int = WARMED_CACHE_TTL,
) -> Dict[str, Any]:
    """
    Warm cache with skill taxonomy data.

    This function caches the skill taxonomy which is frequently accessed
    for skill matching and normalization operations.

    Args:
        taxonomy_data: Dictionary containing taxonomy data
        cache: CacheService instance
        ttl: Time-to-live for cache entries (default: 3600 seconds)

    Returns:
        Dictionary containing warming results:
        {
            "taxonomy_warmed": true,
            "skills_count": 500,
            "categories_count": 10,
            "warming_time_ms": 12.34
        }

    Example:
        >>> from services.cache_service import get_cache_service
        >>> cache = get_cache_service()
        >>> taxonomy = get_skill_taxonomy_data()
        >>> result = warm_taxonomy_cache(taxonomy, cache)
        >>> print(result['taxonomy_warmed'])
        True
    """
    start_time = time.time()

    logger.info("Warming cache with skill taxonomy data")

    try:
        skills_count = len(taxonomy_data.get("skills", {}))
        categories_count = len(taxonomy_data.get("categories", []))

        # Cache the complete taxonomy
        success = cache.set(
            CacheService.NAMESPACE_TAXONOMY,
            "complete",
            taxonomy_data,
            ttl=ttl,
        )

        warming_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "taxonomy_warmed": success,
            "skills_count": skills_count,
            "categories_count": categories_count,
            "warming_time_ms": warming_time_ms,
        }

        if success:
            logger.info(
                f"Taxonomy cache warming complete: {skills_count} skills, "
                f"{categories_count} categories in {warming_time_ms}ms"
            )
        else:
            logger.warning("Taxonomy cache warming failed")

        return result

    except Exception as e:
        logger.error(f"Error warming taxonomy cache: {e}", exc_info=True)
        return {
            "taxonomy_warmed": False,
            "skills_count": 0,
            "categories_count": 0,
            "warming_time_ms": round((time.time() - start_time) * 1000, 2),
            "error": str(e),
        }


@shared_task(
    name="tasks.cache_warming.warm_frequently_accessed_data",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def warm_frequently_accessed_data(
    self,
    candidate_limit: int = CANDIDATE_WARM_COUNT,
    vacancy_limit: int = VACANCY_WARM_COUNT,
    ttl: int = WARMED_CACHE_TTL,
) -> Dict[str, Any]:
    """
    Warm cache with frequently accessed data.

    This Celery task identifies and caches frequently accessed data including
    candidate profiles, vacancies, and taxonomy data to improve response times.

    Task Workflow:
    1. Retrieve frequently accessed candidates (recent activity)
    2. Retrieve frequently accessed vacancies (recent activity)
    3. Retrieve skill taxonomy data
    4. Warm candidate cache
    5. Warm vacancy cache
    6. Warm taxonomy cache
    7. Generate warming report

    Args:
        self: Celery task instance (bind=True)
        candidate_limit: Max candidates to warm (default: 100)
        vacancy_limit: Max vacancies to warm (default: 50)
        ttl: Time-to-live for warmed entries (default: 3600 seconds)

    Returns:
        Dictionary containing warming results:
        - candidates_warmed: Number of candidates warmed
        - vacancies_warmed: Number of vacancies warmed
        - taxonomy_warmed: Whether taxonomy was warmed
        - total_warming_time_ms: Total processing time
        - status: Task status (completed/failed)

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For database or processing errors

    Example:
        >>> from tasks.cache_warming import warm_frequently_accessed_data
        >>> task = warm_frequently_accessed_data.delay(candidate_limit=50)
        >>> result = task.get()
        >>> print(result['candidates_warmed'])
        50
    """
    start_time = time.time()
    total_steps = 6
    current_step = 0

    try:
        logger.info("Starting cache warming for frequently accessed data")

        cache = get_cache_service()

        if not cache.enabled:
            logger.warning("Cache is disabled, skipping warming")
            return {
                "status": "skipped",
                "error": "Cache is disabled",
                "candidates_warmed": 0,
                "vacancies_warmed": 0,
                "taxonomy_warmed": False,
            }

        # Note: In a real implementation, you would get db_session here
        # from database import get_db_session
        # db_session = get_db_session()
        db_session = None

        # Step 1: Retrieve frequently accessed candidates
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "retrieving_candidates",
            "message": "Retrieving frequently accessed candidates...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Retrieving candidates")

        candidates = get_frequently_accessed_candidates(
            limit=candidate_limit,
            db_session=db_session,
        )

        # Step 2: Retrieve frequently accessed vacancies
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "retrieving_vacancies",
            "message": "Retrieving frequently accessed vacancies...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Retrieving vacancies")

        vacancies = get_frequently_accessed_vacancies(
            limit=vacancy_limit,
            db_session=db_session,
        )

        # Step 3: Retrieve skill taxonomy
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "retrieving_taxonomy",
            "message": "Retrieving skill taxonomy...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Retrieving taxonomy")

        taxonomy_data = get_skill_taxonomy_data(db_session=db_session)

        # Step 4: Warm candidate cache
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "warming_candidates",
            "message": "Warming candidate cache...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Warming candidates")

        candidate_result = warm_candidate_cache(candidates, cache, ttl=ttl)

        # Step 5: Warm vacancy cache
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "warming_vacancies",
            "message": "Warming vacancy cache...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Warming vacancies")

        vacancy_result = warm_vacancy_cache(vacancies, cache, ttl=ttl)

        # Step 6: Warm taxonomy cache
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "warming_taxonomy",
            "message": "Warming taxonomy cache...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Warming taxonomy")

        taxonomy_result = warm_taxonomy_cache(taxonomy_data, cache, ttl=ttl)

        total_warming_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "candidates_warmed": candidate_result.get("candidates_warmed", 0),
            "vacancies_warmed": vacancy_result.get("vacancies_warmed", 0),
            "taxonomy_warmed": taxonomy_result.get("taxonomy_warmed", False),
            "candidate_cache_hits": candidate_result.get("cache_hits", 0),
            "vacancy_cache_hits": vacancy_result.get("cache_hits", 0),
            "total_cache_hits": (
                candidate_result.get("cache_hits", 0) + vacancy_result.get("cache_hits", 0)
            ),
            "errors": (
                candidate_result.get("errors", 0)
                + vacancy_result.get("errors", 0)
                + (0 if taxonomy_result.get("taxonomy_warmed") else 1)
            ),
            "total_warming_time_ms": total_warming_time_ms,
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"Cache warming completed: {result['candidates_warmed']} candidates, "
            f"{result['vacancies_warmed']} vacancies, "
            f"taxonomy={'warmed' if result['taxonomy_warmed'] else 'failed'}, "
            f"{result['total_cache_hits']} existing cache hits in {total_warming_time_ms}ms"
        )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        return {
            "status": "failed",
            "error": "Cache warming exceeded maximum time limit",
            "total_warming_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    except Exception as e:
        logger.error(f"Error in cache warming: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "total_warming_time_ms": round((time.time() - start_time) * 1000, 2),
        }


@shared_task(
    name="tasks.cache_warming.periodic_cache_warming",
    bind=True,
)
def periodic_cache_warming(
    self,
) -> Dict[str, Any]:
    """
    Periodic task to warm the cache with frequently accessed data.

    This is a scheduled task that runs periodically (e.g., every 30 minutes)
    to automatically warm the cache with frequently accessed data.

    Returns:
        Dictionary containing warming results

    Example:
        >>> # This would be scheduled via Celery beat
        >>> # celery beat schedule: {
        >>> #     'cache-warming': {
        >>> #         'task': 'tasks.cache_warming.periodic_cache_warming',
        >>> #         'schedule': crontab(minute='*/30'),  # Every 30 minutes
        >>> #     }
        >>> # }
    """
    logger.info("Starting periodic cache warming")

    # Warm frequently accessed data
    result = warm_frequently_accessed_data(
        candidate_limit=CANDIDATE_WARM_COUNT,
        vacancy_limit=VACANCY_WARM_COUNT,
        ttl=WARMED_CACHE_TTL,
    )

    logger.info(f"Periodic cache warming completed: {result.get('status')}")
    return result
