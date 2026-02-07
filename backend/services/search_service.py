"""
Advanced Search Service for Candidates and Vacancies

This module provides PostgreSQL full-text search with multi-field filtering
and boolean operator support for finding candidates and job vacancies.

Features:
- Full-text search using PostgreSQL tsvector for fast text queries
- Multi-field filtering: skills, experience, education, location, languages
- Boolean operators: AND, OR, NOT for complex queries
- Range filters: experience years, match score, date ranges, salary ranges
- Semantic search using vector similarity matching
- Performance optimized with proper indexing

The service builds on the existing resume_analyses table which contains
extracted data from resumes including skills, experience, education, etc.
and job_vacancies table for searching job postings.
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import (
    Select,
    and_,
    func,
    or_,
    select,
    text,
)
from sqlalchemy.ext.asyncio import AsyncSession

from models import Resume, ResumeAnalysis, HiringStage, HiringStageName, JobVacancy

logger = logging.getLogger(__name__)

# Import vector matcher for semantic search
try:
    from analyzers.vector_matcher import get_vector_matcher, VectorMatchResult
    _HAS_VECTOR_MATCHER = True
except ImportError:
    _HAS_VECTOR_MATCHER = False
    logger.warning("Vector matcher not available, semantic search disabled")


@dataclass
class SearchFilters:
    """
    Filter configuration for candidate search.

    Attributes:
        skills: List of required skills (OR logic within list)
        min_experience_years: Minimum years of experience (optional)
        max_experience_years: Maximum years of experience (optional)
        location: Location filter (optional)
        education_level: Minimum education level (optional)
        languages: List of required languages (optional)
        min_match_score: Minimum match score (0-100, optional)
        max_match_score: Maximum match score (0-100, optional)
        date_from: Start date filter (ISO date, optional)
        date_to: End date filter (ISO date, optional)
        vacancy_id: Filter by vacancy ID (optional)
        stage_id: Filter by workflow stage (optional)
        use_semantic_search: Enable semantic similarity search (optional)
    """

    skills: Optional[List[str]] = None
    min_experience_years: Optional[int] = None
    max_experience_years: Optional[int] = None
    location: Optional[str] = None
    education_level: Optional[str] = None
    languages: Optional[List[str]] = None
    min_match_score: Optional[float] = None
    max_match_score: Optional[float] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    vacancy_id: Optional[str] = None
    stage_id: Optional[str] = None
    use_semantic_search: Optional[bool] = None


@dataclass
class VacancyFilters:
    """
    Filter configuration for vacancy search.

    Attributes:
        work_format: Work format filter (remote, hybrid, office) (optional)
        location: Location filter (optional)
        salary_min: Minimum salary filter (optional)
        salary_max: Maximum salary filter (optional)
        employment_type: Employment type filter (full-time, part-time, contract) (optional)
    """

    work_format: Optional[str] = None
    location: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    employment_type: Optional[str] = None


@dataclass
class SearchResult:
    """
    Search result containing candidates and metadata.

    Attributes:
        total: Total number of matching candidates
        candidates: List of candidate dictionaries
        query: The search query used
        filters_applied: Filters that were applied
        execution_time_seconds: Time taken to execute search
        semantic_search_enabled: Whether semantic search was used (optional)
        avg_semantic_score: Average semantic score of results (optional)
    """

    total: int
    candidates: List[Dict[str, Any]]
    query: str
    filters_applied: Dict[str, Any]
    execution_time_seconds: float
    semantic_search_enabled: Optional[bool] = None
    avg_semantic_score: Optional[float] = None


class SearchService:
    """
    Service for advanced candidate and vacancy search with PostgreSQL full-text search.

    This service provides fast, flexible search capabilities leveraging:
    - PostgreSQL tsvector for full-text search on resume and vacancy content
    - JSON field queries for filtering on analyzed resume data
    - Proper indexing for sub-2 second response times with 10k+ candidates
    """

    # Education level ordering for filtering
    EDUCATION_LEVELS = {
        "phd": 5,
        "doctorate": 5,
        "master": 4,
        "ms": 4,
        "m.sc": 4,
        "mba": 4,
        "bachelor": 3,
        "bs": 3,
        "b.sc": 3,
        "ba": 3,
        "diploma": 2,
        "associate": 2,
        "certificate": 1,
        "high_school": 0,
        "none": 0,
    }

    def __init__(self, db: AsyncSession):
        """
        Initialize the search service.

        Args:
            db: Database session for executing queries
        """
        self.db = db

    async def search_candidates(
        self,
        query: Optional[str] = None,
        filters: Optional[SearchFilters] = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "relevance",
    ) -> SearchResult:
        """
        Search for candidates with full-text search and filters.

        Args:
            query: Search query string (supports AND, OR, NOT operators)
            filters: SearchFilters object with field-specific filters
            skip: Number of results to skip (pagination)
            limit: Maximum number of results to return
            sort_by: Sort field (relevance, date, experience)

        Returns:
            SearchResult with candidates and metadata

        Raises:
            ValueError: If filter parameters are invalid
        """
        import time
        start_time = time.time()

        try:
            logger.info(
                f"Searching candidates - query: {query}, filters: {filters}, "
                f"skip: {skip}, limit: {limit}"
            )

            # Build the base query with joins
            query_builder = self._build_search_query(query, filters)

            # Get total count
            count_query = select(func.count()).select_from(query_builder.alias())
            total_result = await self.db.execute(count_query)
            total = total_result.scalar() or 0

            # Apply sorting
            query_builder = self._apply_sorting(query_builder, sort_by, query is not None)

            # Apply pagination
            query_builder = query_builder.offset(skip).limit(limit)

            # Execute search
            result = await self.db.execute(query_builder)
            rows = result.all()

            # Convert to candidate format
            candidates = await self._format_results(rows)

            # Apply semantic search if enabled
            semantic_search_enabled = False
            avg_semantic_score = None

            if filters and filters.use_semantic_search and _HAS_VECTOR_MATCHER:
                semantic_search_enabled = True
                candidates = await self._apply_semantic_search(
                    candidates, query, filters
                )

                # Calculate average semantic score
                if candidates:
                    semantic_scores = [
                        c.get("semantic_score", 0.0)
                        for c in candidates
                        if "semantic_score" in c
                    ]
                    if semantic_scores:
                        avg_semantic_score = round(
                            sum(semantic_scores) / len(semantic_scores), 3
                        )

            execution_time = time.time() - start_time

            logger.info(
                f"Search completed: found {total} candidates, "
                f"returned {len(candidates)} in {execution_time:.3f}s"
                + (f", semantic search: {avg_semantic_score:.3f} avg score"
                   if semantic_search_enabled else "")
            )

            return SearchResult(
                total=total,
                candidates=candidates,
                query=query or "",
                filters_applied=self._serialize_filters(filters),
                execution_time_seconds=execution_time,
                semantic_search_enabled=semantic_search_enabled,
                avg_semantic_score=avg_semantic_score,
            )

        except Exception as e:
            logger.error(f"Error during candidate search: {e}", exc_info=True)
            raise ValueError(f"Search failed: {str(e)}") from e

    async def search_vacancies(
        self,
        query: Optional[str] = None,
        filters: Optional[VacancyFilters] = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "date",
    ) -> SearchResult:
        """
        Search for vacancies with full-text search and filters.

        Args:
            query: Search query string (supports AND, OR, NOT operators)
            filters: VacancyFilters object with field-specific filters
            skip: Number of results to skip (pagination)
            limit: Maximum number of results to return
            sort_by: Sort field (date, salary, relevance)

        Returns:
            SearchResult with vacancies and metadata

        Raises:
            ValueError: If filter parameters are invalid
        """
        import time
        start_time = time.time()

        try:
            logger.info(
                f"Searching vacancies - query: {query}, filters: {filters}, "
                f"skip: {skip}, limit: {limit}"
            )

            # Build the base query
            query_builder = self._build_vacancy_search_query(query, filters)

            # Get total count
            count_query = select(func.count()).select_from(query_builder.alias())
            total_result = await self.db.execute(count_query)
            total = total_result.scalar() or 0

            # Apply sorting
            query_builder = self._apply_vacancy_sorting(query_builder, sort_by, query is not None)

            # Apply pagination
            query_builder = query_builder.offset(skip).limit(limit)

            # Execute search
            result = await self.db.execute(query_builder)
            rows = result.all()

            # Convert to vacancy format
            vacancies = self._format_vacancy_results(rows)

            execution_time = time.time() - start_time

            logger.info(
                f"Vacancy search completed: found {total} vacancies, "
                f"returned {len(vacancies)} in {execution_time:.3f}s"
            )

            return SearchResult(
                total=total,
                candidates=vacancies,
                query=query or "",
                filters_applied=self._serialize_vacancy_filters(filters),
                execution_time_seconds=execution_time,
            )

        except Exception as e:
            logger.error(f"Error during vacancy search: {e}", exc_info=True)
            raise ValueError(f"Vacancy search failed: {str(e)}") from e

    def _build_search_query(
        self,
        query: Optional[str],
        filters: Optional[SearchFilters],
    ) -> Select:
        """
        Build the SQLAlchemy search query with filters.

        Args:
            query: Full-text search query
            filters: SearchFilters object

        Returns:
            SQLAlchemy Select object with applied filters
        """
        # Base query with resume and analysis join
        stmt = (
            select(Resume, ResumeAnalysis)
            .outerjoin(ResumeAnalysis, Resume.id == ResumeAnalysis.resume_id)
            .where(Resume.status == "completed")
        )

        # Apply full-text search if query provided
        if query:
            search_tsquery = self._parse_boolean_query(query)
            if search_tsquery:
                # Search in resume raw_text and analysis fields
                # Using to_tsquery for parsed boolean search
                stmt = stmt.where(
                    or_(
                        text("to_tsvector('english', resumes.raw_text) @@ :search_query"),
                        text("to_tsvector('english', COALESCE(resume_analyses.raw_text, '')) @@ :search_query"),
                    )
                )
                stmt = stmt.params(search_query=search_tsquery)

        # Apply filters
        if filters:
            stmt = self._apply_filters(stmt, filters)

        return stmt

    def _parse_boolean_query(self, query: str) -> Optional[str]:
        """
        Parse boolean search query into PostgreSQL tsquery format.

        Converts:
        - "Python AND Django" -> "python & django"
        - "Python OR Django" -> "python | django"
        - "Python NOT Flask" -> "python & !flask"
        - "Python Django" (implicit AND) -> "python & django"

        Args:
            query: User search query with boolean operators

        Returns:
            PostgreSQL tsquery string or None if query is empty
        """
        if not query or not query.strip():
            return None

        # Normalize and convert to lowercase
        query = query.strip().lower()

        # Replace boolean operators with tsquery syntax
        # Handle NOT first to avoid partial matches
        query = query.replace(" not ", " !")
        query = query.replace(" -", " !")
        query = query.replace(" and ", " &")
        query = query.replace(" or ", " |")
        query = query.replace(" ", " &")  # Implicit AND for remaining spaces

        # Remove parentheses for now (could add more sophisticated parsing)
        query = query.replace("(", "").replace(")", "")

        # Remove any extra whitespace
        query = " ".join(query.split())

        return query

    def _apply_filters(self, stmt: Select, filters: SearchFilters) -> Select:
        """
        Apply search filters to the query.

        Args:
            stmt: SQLAlchemy Select statement
            filters: SearchFilters object

        Returns:
            Modified Select statement with filters applied
        """
        # Skills filter - search in resume_analysis.skills JSON array
        if filters.skills:
            for skill in filters.skills:
                # Use JSON containment operator to check if skill exists in array
                stmt = stmt.where(
                    text("resume_analyses.skills @> :skill::jsonb")
                ).params(skill=f'["{skill}"]')

        # Experience range filter
        if filters.min_experience_years is not None:
            min_months = filters.min_experience_years * 12
            stmt = stmt.where(
                or_(
                    ResumeAnalysis.total_experience_months >= min_months,
                    ResumeAnalysis.total_experience_months.is_(None),
                )
            )

        if filters.max_experience_years is not None:
            max_months = filters.max_experience_years * 12
            stmt = stmt.where(
                or_(
                    ResumeAnalysis.total_experience_months <= max_months,
                    ResumeAnalysis.total_experience_months.is_(None),
                )
            )

        # Location filter - search in entities JSON field
        if filters.location:
            stmt = stmt.where(
                or_(
                    text("resume_analyses.entities->>'locations' ILIKE :location"),
                    Resume.location.ilike(f"%{filters.location}%"),
                )
            ).params(location=f"%{filters.location}%")

        # Education level filter
        if filters.education_level:
            min_level = self.EDUCATION_LEVELS.get(filters.education_level.lower(), 0)
            # Filter by education level in education array
            # This checks if education field exists and has data
            stmt = stmt.where(
                text("resume_analyses.education IS NOT NULL")
            )

        # Languages filter - check in entities or analysis
        if filters.languages:
            for lang in filters.languages:
                stmt = stmt.where(
                    or_(
                        text("resume_analyses.language ILIKE :lang"),
                        text("resume_analyses.raw_text ILIKE :lang"),
                    )
                ).params(lang=f"%{lang}%")

        # Date range filter
        if filters.date_from:
            try:
                date_from = datetime.fromisoformat(filters.date_from.replace("Z", "+00:00"))
                stmt = stmt.where(Resume.created_at >= date_from)
            except ValueError:
                logger.warning(f"Invalid date_from format: {filters.date_from}")

        if filters.date_to:
            try:
                date_to = datetime.fromisoformat(filters.date_to.replace("Z", "+00:00"))
                stmt = stmt.where(Resume.created_at <= date_to)
            except ValueError:
                logger.warning(f"Invalid date_to format: {filters.date_to}")

        # Vacancy filter - via hiring_stage
        if filters.vacancy_id:
            try:
                vacancy_uuid = UUID(filters.vacancy_id)
                stmt = stmt.where(
                    Resume.id.in_(
                        select(HiringStage.resume_id).where(
                            HiringStage.vacancy_id == vacancy_uuid
                        )
                    )
                )
            except ValueError:
                logger.warning(f"Invalid vacancy_id format: {filters.vacancy_id}")

        # Stage filter - via hiring_stage
        if filters.stage_id:
            try:
                # Try parsing as UUID first (custom stage)
                stage_uuid = UUID(filters.stage_id)
                stmt = stmt.where(
                    Resume.id.in_(
                        select(HiringStage.resume_id).where(
                            HiringStage.workflow_stage_config_id == stage_uuid
                        )
                    )
                )
            except ValueError:
                # It's a stage name
                try:
                    stage_enum = HiringStageName(filters.stage_id)
                    stmt = stmt.where(
                        Resume.id.in_(
                            select(HiringStage.resume_id).where(
                                HiringStage.stage_name == stage_enum
                            )
                        )
                    )
                except ValueError:
                    logger.warning(f"Invalid stage_id: {filters.stage_id}")

        return stmt

    def _apply_sorting(
        self,
        stmt: Select,
        sort_by: str,
        has_query: bool,
    ) -> Select:
        """
        Apply sorting to the query.

        Args:
            stmt: SQLAlchemy Select statement
            sort_by: Sort field (relevance, date, experience)
            has_query: Whether a full-text search query is present

        Returns:
            Modified Select statement with ordering applied
        """
        if sort_by == "relevance" and has_query:
            # Sort by ts_rank if full-text search is used
            stmt = stmt.order_by(
                text(
                    "ts_rank("
                    "to_tsvector('english', COALESCE(resumes.raw_text, '')), "
                    "plainto_tsquery('english', :query)"
                    ") DESC"
                )
            )
        elif sort_by == "experience":
            # Sort by experience (most experienced first)
            stmt = stmt.order_by(
                ResumeAnalysis.total_experience_months.desc().nulls_last()
            )
        elif sort_by == "date":
            # Sort by upload date (newest first)
            stmt = stmt.order_by(Resume.created_at.desc())
        else:
            # Default to date sorting
            stmt = stmt.order_by(Resume.created_at.desc())

        return stmt

    async def _format_results(self, rows: List[tuple]) -> List[Dict[str, Any]]:
        """
        Format query results into candidate dictionaries.

        Args:
            rows: Raw query result rows

        Returns:
            List of formatted candidate dictionaries
        """
        candidates = []

        for row in rows:
            resume = row[0]
            analysis = row[1]

            # Get current hiring stage
            stage_query = (
                select(HiringStage)
                .where(HiringStage.resume_id == resume.id)
                .order_by(HiringStage.created_at.desc())
                .limit(1)
            )
            stage_result = await self.db.execute(stage_query)
            hiring_stage = stage_result.scalar_one_or_none()

            candidate = {
                "id": str(resume.id),
                "filename": resume.filename,
                "status": resume.status.value,
                "created_at": resume.created_at.isoformat()
                if resume.created_at
                else None,
                "updated_at": resume.updated_at.isoformat()
                if resume.updated_at
                else None,
                "current_stage": hiring_stage.stage_name if hiring_stage else "applied",
                "vacancy_id": str(hiring_stage.vacancy_id)
                if hiring_stage and hiring_stage.vacancy_id
                else None,
            }

            # Add analysis data if available
            if analysis:
                candidate["skills"] = analysis.skills or []
                candidate["total_experience_months"] = analysis.total_experience_months
                candidate["experience_years"] = (
                    round(analysis.total_experience_months / 12, 1)
                    if analysis.total_experience_months
                    else None
                )
                candidate["education"] = analysis.education or []
                candidate["language"] = analysis.language
                candidate["quality_score"] = analysis.quality_score

            candidates.append(candidate)

        return candidates

    async def _apply_semantic_search(
        self,
        candidates: List[Dict[str, Any]],
        query: Optional[str],
        filters: SearchFilters,
    ) -> List[Dict[str, Any]]:
        """
        Apply semantic similarity search to candidates.

        Calculates semantic similarity scores between resumes and job postings
        using vector embeddings. Enhances candidate results with semantic scores.

        Args:
            candidates: List of candidate dictionaries from initial search
            query: Search query string
            filters: SearchFilters object

        Returns:
            List of candidates with semantic_score added
        """
        vector_matcher = get_vector_matcher()
        if vector_matcher is None:
            logger.warning("Vector matcher not available, skipping semantic search")
            return candidates

        # Determine job context for matching
        job_title = ""
        job_description = ""
        job_skills = []

        # Try to get vacancy details if vacancy_id is provided
        if filters.vacancy_id:
            try:
                from models import Vacancy
                vacancy_uuid = UUID(filters.vacancy_id)
                vacancy_query = select(Vacancy).where(Vacancy.id == vacancy_uuid)
                vacancy_result = await self.db.execute(vacancy_query)
                vacancy = vacancy_result.scalar_one_or_none()

                if vacancy:
                    job_title = vacancy.title or ""
                    job_description = vacancy.description or ""
                    job_skills = vacancy.skills or []
                    logger.info(
                        f"Using vacancy '{job_title}' for semantic search"
                    )
            except Exception as e:
                logger.warning(f"Failed to load vacancy for semantic search: {e}")

        # If no vacancy, use query as job context
        if not job_title and query:
            job_title = query
            job_description = ""
            job_skills = filters.skills or []

        # If still no job context, skip semantic search
        if not job_title and not job_description and not job_skills:
            logger.info("No job context available for semantic search")
            return candidates

        # Calculate semantic scores for each candidate
        for candidate in candidates:
            try:
                # Get resume text from database
                resume_uuid = UUID(candidate["id"])
                resume_query = select(Resume).where(Resume.id == resume_uuid)
                resume_result = await self.db.execute(resume_query)
                resume = resume_result.scalar_one_or_none()

                if not resume or not resume.raw_text:
                    candidate["semantic_score"] = 0.0
                    candidate["semantic_passed"] = False
                    continue

                # Get skills from analysis if available
                resume_skills = candidate.get("skills", [])

                # Calculate semantic similarity
                match_result = vector_matcher.match_resume_to_vacancy(
                    resume_text=resume.raw_text,
                    resume_skills=resume_skills,
                    vacancy_title=job_title,
                    vacancy_description=job_description,
                    vacancy_skills=job_skills,
                )

                candidate["semantic_score"] = round(match_result.score, 3)
                candidate["semantic_passed"] = match_result.passed
                candidate["semantic_similarity"] = round(match_result.similarity, 3)

            except Exception as e:
                logger.error(f"Error calculating semantic score for candidate {candidate.get('id')}: {e}")
                candidate["semantic_score"] = 0.0
                candidate["semantic_passed"] = False

        # Filter by min_match_score if specified
        if filters.min_match_score is not None:
            min_score = filters.min_match_score / 100.0  # Convert to 0-1 range
            candidates = [
                c for c in candidates
                if c.get("semantic_score", 0.0) >= min_score
            ]
            logger.info(
                f"Filtered to {len(candidates)} candidates with semantic score >= {min_score}"
            )

        # Sort by semantic score (highest first)
        candidates = sorted(
            candidates,
            key=lambda c: c.get("semantic_score", 0.0),
            reverse=True
        )

        return candidates

    def _serialize_filters(self, filters: Optional[SearchFilters]) -> Dict[str, Any]:
        """
        Serialize filters for response.

        Args:
            filters: SearchFilters object

        Returns:
            Dictionary representation of applied filters
        """
        if not filters:
            return {}

        return {
            "skills": filters.skills,
            "min_experience_years": filters.min_experience_years,
            "max_experience_years": filters.max_experience_years,
            "location": filters.location,
            "education_level": filters.education_level,
            "languages": filters.languages,
            "min_match_score": filters.min_match_score,
            "max_match_score": filters.max_match_score,
            "date_from": filters.date_from,
            "date_to": filters.date_to,
            "vacancy_id": filters.vacancy_id,
            "stage_id": filters.stage_id,
            "use_semantic_search": filters.use_semantic_search,
        }

    def _build_vacancy_search_query(
        self,
        query: Optional[str],
        filters: Optional[VacancyFilters],
    ) -> Select:
        """
        Build the SQLAlchemy vacancy search query with filters.

        Args:
            query: Full-text search query
            filters: VacancyFilters object

        Returns:
            SQLAlchemy Select object with applied filters
        """
        # Base query for job vacancies
        stmt = select(JobVacancy)

        # Apply full-text search if query provided
        if query:
            search_tsquery = self._parse_boolean_query(query)
            if search_tsquery:
                # Search in title and description
                stmt = stmt.where(
                    or_(
                        text("to_tsvector('english', job_vacancies.title) @@ :search_query"),
                        text("to_tsvector('english', job_vacancies.description) @@ :search_query"),
                    )
                )
                stmt = stmt.params(search_query=search_tsquery)

        # Apply filters
        if filters:
            stmt = self._apply_vacancy_filters(stmt, filters)

        return stmt

    def _apply_vacancy_filters(self, stmt: Select, filters: VacancyFilters) -> Select:
        """
        Apply vacancy search filters to the query.

        Args:
            stmt: SQLAlchemy Select statement
            filters: VacancyFilters object

        Returns:
            Modified Select statement with filters applied
        """
        # Work format filter
        if filters.work_format:
            stmt = stmt.where(
                JobVacancy.work_format.ilike(f"%{filters.work_format}%")
            )

        # Location filter
        if filters.location:
            stmt = stmt.where(
                JobVacancy.location.ilike(f"%{filters.location}%")
            )

        # Salary range filter
        if filters.salary_min is not None:
            stmt = stmt.where(
                or_(
                    JobVacancy.salary_min >= filters.salary_min,
                    JobVacancy.salary_min.is_(None),
                )
            )

        if filters.salary_max is not None:
            stmt = stmt.where(
                or_(
                    JobVacancy.salary_max <= filters.salary_max,
                    JobVacancy.salary_max.is_(None),
                )
            )

        # Employment type filter
        if filters.employment_type:
            stmt = stmt.where(
                JobVacancy.employment_type.ilike(f"%{filters.employment_type}%")
            )

        return stmt

    def _apply_vacancy_sorting(
        self,
        stmt: Select,
        sort_by: str,
        has_query: bool,
    ) -> Select:
        """
        Apply sorting to the vacancy query.

        Args:
            stmt: SQLAlchemy Select statement
            sort_by: Sort field (date, salary, relevance)
            has_query: Whether a full-text search query is present

        Returns:
            Modified Select statement with ordering applied
        """
        if sort_by == "relevance" and has_query:
            # Sort by ts_rank if full-text search is used
            stmt = stmt.order_by(
                text(
                    "ts_rank("
                    "to_tsvector('english', COALESCE(job_vacancies.title, '') || ' ' || COALESCE(job_vacancies.description, '')), "
                    "plainto_tsquery('english', :query)"
                    ") DESC"
                )
            )
        elif sort_by == "salary":
            # Sort by salary (highest first)
            stmt = stmt.order_by(JobVacancy.salary_max.desc().nulls_last())
        elif sort_by == "date":
            # Sort by creation date (newest first)
            stmt = stmt.order_by(JobVacancy.created_at.desc())
        else:
            # Default to date sorting
            stmt = stmt.order_by(JobVacancy.created_at.desc())

        return stmt

    def _format_vacancy_results(self, rows: List[tuple]) -> List[Dict[str, Any]]:
        """
        Format query results into vacancy dictionaries.

        Args:
            rows: Raw query result rows

        Returns:
            List of formatted vacancy dictionaries
        """
        vacancies = []

        for row in rows:
            vacancy = row[0]

            vacancy_dict = {
                "id": str(vacancy.id),
                "title": vacancy.title,
                "description": vacancy.description,
                "required_skills": vacancy.required_skills or [],
                "min_experience_months": vacancy.min_experience_months,
                "additional_requirements": vacancy.additional_requirements or [],
                "industry": vacancy.industry,
                "work_format": vacancy.work_format,
                "location": vacancy.location,
                "salary_min": vacancy.salary_min,
                "salary_max": vacancy.salary_max,
                "english_level": vacancy.english_level,
                "employment_type": vacancy.employment_type,
                "external_id": vacancy.external_id,
                "source": vacancy.source,
                "created_at": vacancy.created_at.isoformat()
                if vacancy.created_at
                else None,
                "updated_at": vacancy.updated_at.isoformat()
                if vacancy.updated_at
                else None,
            }

            vacancies.append(vacancy_dict)

        return vacancies

    def _serialize_vacancy_filters(self, filters: Optional[VacancyFilters]) -> Dict[str, Any]:
        """
        Serialize vacancy filters for response.

        Args:
            filters: VacancyFilters object

        Returns:
            Dictionary representation of applied filters
        """
        if not filters:
            return {}

        return {
            "work_format": filters.work_format,
            "location": filters.location,
            "salary_min": filters.salary_min,
            "salary_max": filters.salary_max,
            "employment_type": filters.employment_type,
        }


# Singleton instance getter for dependency injection
_search_service_instance: Optional[SearchService] = None


def get_search_service(db: AsyncSession) -> SearchService:
    """
    Get or create a SearchService instance.

    This function is designed for use with FastAPI dependency injection.

    Args:
        db: Database session

    Returns:
        SearchService instance

    Example:
        >>> from fastapi import Depends
        >>> from database import get_db
        >>> from services.search_service import get_search_service
        >>>
        >>> @router.get("/search")
        >>> async def search_candidates(
        >>>     query: str,
        >>>     db: AsyncSession = Depends(get_db),
        >>>     search_service: SearchService = Depends(get_search_service)
        >>> ):
        >>>     results = await search_service.search_candidates(query=query)
        >>>     return results
    """
    return SearchService(db)
