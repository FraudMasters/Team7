"""
Semantic Search Service using LLM for Natural Language Queries

This module provides advanced semantic search capabilities using large language
models to understand natural language queries beyond keyword matching.

Features:
- Natural language query understanding (e.g., "Find me senior Python developers with fintech experience")
- LLM-powered semantic matching with embeddings
- Hybrid search combining semantic and keyword matching
- Multi-language support for resumes in different languages
- Explainable results showing why candidates matched
- Graceful fallback to UnifiedSkillMatcher when LLM unavailable
- Performance optimized with caching

The service uses:
- LLMSemanticMatcher for deep semantic analysis
- UnifiedSkillMatcher (keyword + TF-IDF + vector) as robust fallback
- SearchService for traditional keyword-based filtering as final fallback
"""
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import Select, and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from models import Resume, ResumeAnalysis, HiringStage, HiringStageName
from analyzers.llm_matcher import (
    LLMSemanticMatcher,
    get_llm_matcher,
    LLMMatchResult,
    detect_language,
)
from analyzers.unified_matcher import (
    UnifiedSkillMatcher,
    get_unified_matcher,
    UnifiedMatchResult,
)
from services.search_service import SearchService, SearchFilters

logger = logging.getLogger(__name__)


@dataclass
class SemanticSearchFilters:
    """
    Filter configuration for semantic search.

    Extends traditional filtering with semantic-specific options.

    Attributes:
        query: Natural language query string (required)
        vacancy_id: Optional vacancy ID for job posting context
        min_semantic_score: Minimum semantic similarity score (0-1, default 0.5)
        semantic_weight: Weight for semantic scoring (0-1, default 0.7)
        keyword_weight: Weight for keyword matching (0-1, default 0.3)
        use_hybrid: Whether to use hybrid search (default True)
        language: Language code for query (en, ru, etc., auto-detect if None)
        skills: Optional list of required skills for keyword filtering
        min_experience_years: Minimum years of experience (optional)
        max_experience_years: Maximum years of experience (optional)
        location: Location filter (optional)
        education_level: Minimum education level (optional)
        skip: Number of results to skip for pagination
        limit: Maximum number of results to return
    """

    query: str
    vacancy_id: Optional[str] = None
    min_semantic_score: float = 0.5
    semantic_weight: float = 0.7
    keyword_weight: float = 0.3
    use_hybrid: bool = True
    language: Optional[str] = None

    # Traditional filters
    skills: Optional[List[str]] = None
    min_experience_years: Optional[int] = None
    max_experience_years: Optional[int] = None
    location: Optional[str] = None
    education_level: Optional[str] = None

    # Pagination
    skip: int = 0
    limit: int = 100


@dataclass
class SemanticSearchResult:
    """
    Result of semantic search with match explanations.

    Attributes:
        total: Total number of candidates found
        candidates: List of candidate dictionaries with scores
        query: The search query used
        execution_time_seconds: Time taken for search
        semantic_scores_used: Whether semantic scoring was applied
        fallback_used: Whether fallback to keyword search was used
        filters_applied: Dictionary of applied filters
    """

    total: int
    candidates: List[Dict[str, Any]]
    query: str
    execution_time_seconds: float
    semantic_scores_used: bool
    fallback_used: bool
    filters_applied: Dict[str, Any]


@dataclass
class SemanticMatchExplanation:
    """
    Explanation of why a candidate matched semantically.

    Attributes:
        resume_id: ID of the resume
        semantic_score: Overall semantic similarity score (0-1)
        skill_match_score: Skills alignment score (0-1)
        experience_relevance_score: Experience relevance score (0-1)
        context_fit_score: Overall contextual fit score (0-1)
        matched_skills: Skills that directly matched
        inferred_skills: Skills inferred from context
        transferable_skills: Transferable skills identified
        missing_skills: Skills that are clearly missing
        explanation: Human-readable explanation of the match
        used_embeddings: Whether embeddings were used for scoring
    """

    resume_id: str
    semantic_score: float
    skill_match_score: float
    experience_relevance_score: float
    context_fit_score: float
    matched_skills: List[str]
    inferred_skills: List[str]
    transferable_skills: List[str]
    missing_skills: List[str]
    explanation: str
    used_embeddings: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "resume_id": self.resume_id,
            "semantic_score": round(self.semantic_score, 4),
            "skill_match_score": round(self.skill_match_score, 4),
            "experience_relevance_score": round(self.experience_relevance_score, 4),
            "context_fit_score": round(self.context_fit_score, 4),
            "matched_skills": self.matched_skills,
            "inferred_skills": self.inferred_skills,
            "transferable_skills": self.transferable_skills,
            "missing_skills": self.missing_skills,
            "explanation": self.explanation,
            "used_embeddings": self.used_embeddings,
        }


class SemanticSearchService:
    """
    Service for LLM-powered semantic search of candidates.

    This service provides natural language query understanding and semantic
    matching using large language models. Key capabilities:

    - Natural language query parsing
    - LLM-based semantic similarity scoring
    - Hybrid search combining semantic and keyword matching
    - Multi-language support via LLM capabilities
    - Explainable match results
    - Graceful fallback to UnifiedSkillMatcher when LLM unavailable
    - Final fallback to keyword-based search

    The fallback hierarchy ensures robust operation:
    1. LLM semantic matching (primary, best results)
    2. UnifiedSkillMatcher (keyword + TF-IDF + vector, good results)
    3. Traditional keyword search (basic results)

    Example:
        >>> service = SemanticSearchService(db)
        >>> filters = SemanticSearchFilters(
        ...     query="Find senior Python developers with fintech experience"
        ... )
        >>> results = await service.semantic_search_candidates(filters)
        >>> for candidate in results.candidates:
        ...     print(f"{candidate['filename']}: {candidate['semantic_score']}")
    """

    def __init__(
        self,
        db: AsyncSession,
        llm_matcher: Optional[LLMSemanticMatcher] = None,
        unified_matcher: Optional[UnifiedSkillMatcher] = None,
    ):
        """
        Initialize the semantic search service.

        Args:
            db: Database session for executing queries
            llm_matcher: Optional LLM matcher instance (created if not provided)
            unified_matcher: Optional unified matcher for fallback (created if not provided)
        """
        self.db = db
        self.llm_matcher = llm_matcher or get_llm_matcher()
        self.unified_matcher = unified_matcher or get_unified_matcher()
        self.search_service = SearchService(db)

        # Check if LLM matcher is available
        self._llm_available = self.llm_matcher is not None
        self._unified_available = self.unified_matcher is not None

        logger.info(
            f"SemanticSearchService initialized: "
            f"llm_available={self._llm_available}, "
            f"unified_available={self._unified_available}"
        )

    async def semantic_search_candidates(
        self,
        filters: SemanticSearchFilters,
    ) -> SemanticSearchResult:
        """
        Search candidates using natural language semantic understanding.

        Args:
            filters: SemanticSearchFilters with query and optional filters

        Returns:
            SemanticSearchResult with ranked candidates and explanations

        Raises:
            ValueError: If query is empty or filters are invalid
        """
        import time
        start_time = time.time()

        try:
            # Validate query
            if not filters.query or not filters.query.strip():
                raise ValueError("Search query cannot be empty")

            logger.info(
                f"Semantic search: query='{filters.query}', "
                f"vacancy_id={filters.vacancy_id}, "
                f"use_hybrid={filters.use_hybrid}, "
                f"llm_available={self._llm_available}"
            )

            # If LLM unavailable or hybrid disabled, use unified matcher fallback
            if not self._llm_available or not filters.use_hybrid:
                logger.info("LLM unavailable or hybrid disabled, using unified matcher fallback")
                return await self._unified_fallback_search(filters)

            # Get job posting context if vacancy_id provided
            job_context = await self._get_job_context(filters.vacancy_id)

            # Get candidate pool using traditional filters
            candidates = await self._get_candidate_pool(filters)

            if not candidates:
                logger.info("No candidates found in initial pool")
                return self._empty_result(filters, time.time() - start_time)

            # Perform semantic matching on candidates with language context
            semantic_results = await self._semantic_match_candidates(
                candidates=candidates,
                query=filters.query,
                job_context=job_context,
                language=filters.language,
            )

            # Filter by minimum semantic score
            filtered_results = [
                r for r in semantic_results
                if r["semantic_score"] >= filters.min_semantic_score
            ]

            # Apply hybrid scoring if requested
            if filters.use_hybrid:
                filtered_results = self._apply_hybrid_scoring(
                    filtered_results,
                    semantic_weight=filters.semantic_weight,
                    keyword_weight=filters.keyword_weight,
                )

            # Sort by final score
            filtered_results.sort(key=lambda x: x.get("final_score", 0), reverse=True)

            # Apply pagination
            total = len(filtered_results)
            paginated_results = filtered_results[filters.skip:filters.skip + filters.limit]

            # Format results
            formatted_candidates = await self._format_semantic_results(paginated_results)

            execution_time = time.time() - start_time

            logger.info(
                f"Semantic search completed: found {total} candidates, "
                f"returned {len(formatted_candidates)} in {execution_time:.3f}s"
            )

            return SemanticSearchResult(
                total=total,
                candidates=formatted_candidates,
                query=filters.query,
                execution_time_seconds=execution_time,
                semantic_scores_used=True,
                fallback_used=False,
                filters_applied=self._serialize_filters(filters),
            )

        except Exception as e:
            logger.error(f"Error during semantic search: {e}", exc_info=True)
            # Attempt fallback to unified matcher (better than keyword search)
            return await self._unified_fallback_search(filters)

    async def hybrid_search(
        self,
        query: str,
        semantic_weight: float = 0.6,
        keyword_weight: float = 0.4,
        filters: Optional[SearchFilters] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> SemanticSearchResult:
        """
        Perform hybrid search combining semantic and keyword matching.

        Args:
            query: Natural language search query
            semantic_weight: Weight for semantic score (0-1)
            keyword_weight: Weight for keyword score (0-1)
            filters: Optional traditional search filters
            skip: Number of results to skip
            limit: Maximum results to return

        Returns:
            SemanticSearchResult with hybrid-ranked candidates
        """
        semantic_filters = SemanticSearchFilters(
            query=query,
            semantic_weight=semantic_weight,
            keyword_weight=keyword_weight,
            use_hybrid=True,
            skip=skip,
            limit=limit,
            skills=filters.skills if filters else None,
            min_experience_years=filters.min_experience_years if filters else None,
            max_experience_years=filters.max_experience_years if filters else None,
            location=filters.location if filters else None,
            education_level=filters.education_level if filters else None,
        )

        return await self.semantic_search_candidates(semantic_filters)

    async def explain_match(
        self,
        query: str,
        resume_id: str,
        vacancy_id: Optional[str] = None,
    ) -> SemanticMatchExplanation:
        """
        Get detailed explanation of why a resume matches a query.

        Args:
            query: Natural language query
            resume_id: ID of the resume to explain
            vacancy_id: Optional vacancy ID for job context

        Returns:
            SemanticMatchExplanation with detailed match analysis

        Raises:
            ValueError: If LLM unavailable or resume not found
        """
        if not self._llm_available:
            raise ValueError("LLM matcher unavailable - cannot provide semantic explanations")

        # Get resume
        try:
            resume_uuid = UUID(resume_id)
        except ValueError:
            raise ValueError(f"Invalid resume_id: {resume_id}")

        stmt = select(Resume).where(Resume.id == resume_uuid)
        result = await self.db.execute(stmt)
        resume = result.scalar_one_or_none()

        if not resume:
            raise ValueError(f"Resume not found: {resume_id}")

        # Get resume analysis
        stmt = select(ResumeAnalysis).where(ResumeAnalysis.resume_id == resume_uuid)
        result = await self.db.execute(stmt)
        analysis = result.scalar_one_or_none()

        # Get job context
        job_context = await self._get_job_context(vacancy_id)

        # Build resume text
        resume_text = resume.raw_text or ""
        if analysis and analysis.raw_text:
            resume_text = analysis.raw_text

        # Detect language from resume text
        resume_language = resume.language or detect_language(resume_text, default="en")

        # Perform LLM match with language context
        llm_result = await self.llm_matcher.match(
            resume_text=resume_text,
            job_title=job_context.get("title", "") if job_context else "",
            job_description=job_context.get("description", "") if job_context else "",
            required_skills=job_context.get("skills", []) if job_context else [],
            query=query,
            language=resume_language,
        )

        # Build explanation
        explanation = SemanticMatchExplanation(
            resume_id=resume_id,
            semantic_score=llm_result.semantic_score,
            skill_match_score=llm_result.skill_match_score,
            experience_relevance_score=llm_result.experience_relevance_score,
            context_fit_score=llm_result.context_fit_score,
            matched_skills=llm_result.matched_skills,
            inferred_skills=llm_result.inferred_skills,
            transferable_skills=llm_result.transferable_skills,
            missing_skills=llm_result.missing_skills,
            explanation=llm_result.explanation,
            used_embeddings=llm_result.used_embeddings,
        )

        return explanation

    async def _get_candidate_pool(
        self,
        filters: SemanticSearchFilters,
    ) -> List[Dict[str, Any]]:
        """
        Get initial pool of candidates using traditional filters.

        Args:
            filters: SemanticSearchFilters

        Returns:
            List of candidate dictionaries with resume data
        """
        # Build base query with filters
        stmt = (
            select(Resume, ResumeAnalysis)
            .outerjoin(ResumeAnalysis, Resume.id == ResumeAnalysis.resume_id)
            .where(Resume.status == "completed")
        )

        # Apply traditional filters
        if filters.skills:
            for skill in filters.skills:
                stmt = stmt.where(
                    text("resume_analyses.skills @> :skill::jsonb")
                ).params(skill=f'["{skill}"]')

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

        if filters.location:
            stmt = stmt.where(
                or_(
                    text("resume_analyses.entities->>'locations' ILIKE :location"),
                    Resume.location.ilike(f"%{filters.location}%"),
                )
            ).params(location=f"%{filters.location}%")

        # Execute query
        result = await self.db.execute(stmt)
        rows = result.all()

        # Format candidates
        candidates = []
        for row in rows:
            resume = row[0]
            analysis = row[1]

            candidate = {
                "id": str(resume.id),
                "filename": resume.filename,
                "raw_text": resume.raw_text or "",
                "language": resume.language,
                "status": resume.status.value,
                "created_at": resume.created_at.isoformat() if resume.created_at else None,
            }

            if analysis:
                candidate["analysis_raw_text"] = analysis.raw_text or ""
                candidate["skills"] = analysis.skills or []
                candidate["total_experience_months"] = analysis.total_experience_months
                candidate["education"] = analysis.education or []

            candidates.append(candidate)

        return candidates

    async def _semantic_match_candidates(
        self,
        candidates: List[Dict[str, Any]],
        query: str,
        job_context: Optional[Dict[str, Any]] = None,
        language: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic matching on candidate pool with multi-language support.

        Args:
            candidates: List of candidate dictionaries
            query: Natural language query
            job_context: Optional job posting context
            language: Optional language code for the content

        Returns:
            List of candidates with added semantic scores
        """
        results = []

        for candidate in candidates:
            # Build resume text
            resume_text = candidate.get("analysis_raw_text") or candidate.get("raw_text", "")

            if not resume_text:
                # Skip resumes without text
                continue

            try:
                # Detect language from resume text if not specified
                # Use candidate's stored language if available
                candidate_language = language or candidate.get("language")
                if not candidate_language:
                    candidate_language = detect_language(resume_text, default="en")

                # Perform LLM semantic match with language context
                llm_result = await self.llm_matcher.match(
                    resume_text=resume_text,
                    job_title=job_context.get("title", "") if job_context else "",
                    job_description=job_context.get("description", "") if job_context else "",
                    required_skills=job_context.get("skills", []) if job_context else [],
                    query=query,
                    language=candidate_language,
                )

                # Add semantic scores to candidate
                candidate["semantic_score"] = llm_result.semantic_score
                candidate["match_result"] = llm_result.to_dict()
                candidate["detected_language"] = candidate_language

                results.append(candidate)

            except Exception as e:
                logger.warning(f"LLM semantic matching failed for candidate {candidate.get('id')}: {e}")

                # Attempt fallback to unified matcher
                if self._unified_available:
                    try:
                        resume_skills = candidate.get("skills", [])
                        required_skills = job_context.get("skills", []) if job_context else []

                        # Extract skills from query if no job context
                        if not required_skills:
                            required_skills = self._extract_skills_from_query(query, job_context)

                        unified_result = self.unified_matcher.match(
                            resume_text=resume_text,
                            resume_skills=resume_skills,
                            job_title=job_context.get("title", "") if job_context else "",
                            job_description=job_context.get("description", "") if job_context else "",
                            required_skills=required_skills,
                        )

                        candidate["semantic_score"] = unified_result.overall_score
                        candidate["match_result"] = {
                            **unified_result.to_dict(),
                            "fallback_used": "unified_matcher",
                            "llm_error": str(e),
                        }
                        candidate["detected_language"] = candidate_language
                        results.append(candidate)

                    except Exception as unified_error:
                        logger.warning(f"Unified matcher fallback also failed: {unified_error}")
                        candidate["semantic_score"] = 0.0
                        candidate["match_result"] = {
                            "error": str(e),
                            "fallback_error": str(unified_error),
                        }
                        results.append(candidate)
                else:
                    # No fallback available, add with zero score
                    candidate["semantic_score"] = 0.0
                    candidate["match_result"] = {"error": str(e)}
                    results.append(candidate)

        return results

    def _apply_hybrid_scoring(
        self,
        candidates: List[Dict[str, Any]],
        semantic_weight: float,
        keyword_weight: float,
    ) -> List[Dict[str, Any]]:
        """
        Apply hybrid scoring combining semantic and keyword scores.

        Args:
            candidates: List of candidates with semantic_score
            semantic_weight: Weight for semantic score
            keyword_weight: Weight for keyword score

        Returns:
            Candidates with added final_score
        """
        for candidate in candidates:
            semantic_score = candidate.get("semantic_score", 0.0)

            # Calculate keyword score from skill matches
            skills = candidate.get("skills", [])
            keyword_score = min(1.0, len(skills) / 10) if skills else 0.0

            # Combine scores
            final_score = (
                semantic_weight * semantic_score +
                keyword_weight * keyword_score
            )

            candidate["keyword_score"] = keyword_score
            candidate["final_score"] = round(final_score, 4)

        return candidates

    async def _format_semantic_results(
        self,
        candidates: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Format semantic search results for API response.

        Args:
            candidates: List of candidates with semantic scores

        Returns:
            Formatted candidate dictionaries
        """
        formatted = []

        for candidate in candidates:
            formatted_candidate = {
                "id": candidate.get("id"),
                "filename": candidate.get("filename"),
                "status": candidate.get("status"),
                "created_at": candidate.get("created_at"),
                "semantic_score": candidate.get("semantic_score", 0.0),
                "keyword_score": candidate.get("keyword_score", 0.0),
                "final_score": candidate.get("final_score", candidate.get("semantic_score", 0.0)),
                "skills": candidate.get("skills", []),
                "experience_years": round(
                    candidate.get("total_experience_months", 0) / 12, 1
                ) if candidate.get("total_experience_months") else None,
                "language": candidate.get("detected_language") or candidate.get("language"),
            }

            # Add match explanation if available
            match_result = candidate.get("match_result", {})
            if match_result and "error" not in match_result:
                formatted_candidate["match_explanation"] = {
                    "skill_match_score": match_result.get("skill_match_score", 0.0),
                    "experience_relevance_score": match_result.get("experience_relevance_score", 0.0),
                    "context_fit_score": match_result.get("context_fit_score", 0.0),
                    "matched_skills": match_result.get("matched_skills", []),
                    "inferred_skills": match_result.get("inferred_skills", []),
                    "transferable_skills": match_result.get("transferable_skills", []),
                    "explanation": match_result.get("explanation", ""),
                }

            formatted.append(formatted_candidate)

        return formatted

    async def _get_job_context(self, vacancy_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Get job posting context for semantic matching.

        Args:
            vacancy_id: Optional job vacancy ID

        Returns:
            Dictionary with job title, description, skills or None
        """
        if not vacancy_id:
            return None

        try:
            from models import JobVacancy

            vacancy_uuid = UUID(vacancy_id)
            stmt = select(JobVacancy).where(JobVacancy.id == vacancy_uuid)
            result = await self.db.execute(stmt)
            vacancy = result.scalar_one_or_none()

            if vacancy:
                return {
                    "title": vacancy.title or "",
                    "description": vacancy.description or "",
                    "skills": vacancy.required_skills or [],
                }
        except Exception as e:
            logger.warning(f"Failed to get job context for vacancy {vacancy_id}: {e}")

        return None

    def _extract_skills_from_query(
        self,
        query: str,
        job_context: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Extract potential skills from natural language query.

        Uses a combination of job context skills and pattern matching
        to extract required skills from the query.

        Args:
            query: Natural language query
            job_context: Optional job posting context with skills

        Returns:
            List of extracted skill names
        """
        import re

        skills = set()

        # Add skills from job context if available
        if job_context and job_context.get("skills"):
            skills.update(job_context["skills"])

        # Common programming languages and frameworks
        common_skills = {
            "python", "javascript", "typescript", "java", "c\\+\\+", "c#",
            "react", "angular", "vue", "node", "express", "django", "flask",
            "spring", "rails", "laravel", "next\\.js", "nuxt", "nestjs",
            "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
            "docker", "kubernetes", "aws", "azure", "gcp", "terraform",
            "git", "ci/cd", "agile", "scrum", "jira", "confluence",
            "linux", "unix", "windows", "macos", "android", "ios",
            "machine learning", "ml", "deep learning", "nlp", "data science",
            "graphql", "rest", "api", "microservices", "kafka", "rabbitmq",
        }

        # Case-insensitive search for common skills
        query_lower = query.lower()
        for skill in common_skills:
            pattern = r'\b' + skill + r'\b'
            if re.search(pattern, query_lower):
                # Normalize skill name (capitalize properly)
                normalized_skill = skill.replace("\\", "").replace(".", "")
                if "+" in normalized_skill:
                    normalized_skill = normalized_skill.replace("+", "Plus")
                skills.add(normalized_skill)

        # Extract quoted terms as skills
        quoted_terms = re.findall(r'"([^"]+)"', query)
        for term in quoted_terms:
            skills.add(term.strip())

        # Extract capitalized words that might be skill names
        # (excluding common words)
        common_words = {
            "find", "looking", "for", "with", "and", "or", "the", "a", "an",
            "senior", "junior", "lead", "developer", "engineer", "manager",
            "experience", "years", "team", "work", "role", "position",
        }
        capitalized = re.findall(r'\b([A-Z][a-z]+)\b', query)
        for word in capitalized:
            if word.lower() not in common_words and len(word) > 2:
                skills.add(word)

        return sorted(list(skills))

    async def _unified_fallback_match(
        self,
        candidates: List[Dict[str, Any]],
        query: str,
        job_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fallback to unified matching when LLM is unavailable.

        Uses UnifiedSkillMatcher (keyword + TF-IDF + vector matching)
        as a robust fallback when LLM API fails.

        Args:
            candidates: List of candidate dictionaries
            query: Natural language query
            job_context: Optional job posting context

        Returns:
            List of candidates with added unified match scores
        """
        if not self._unified_available:
            logger.warning("Unified matcher unavailable, cannot provide fallback")
            return candidates

        # Extract skills from query for required skills
        required_skills = self._extract_skills_from_query(query, job_context)

        # Use job context if available
        job_title = job_context.get("title", "") if job_context else ""
        job_description = job_context.get("description", "") if job_context else ""

        # If no skills extracted and no job context, derive from query
        if not required_skills and not job_title:
            # Use the first few meaningful words from query as context
            words = [w for w in query.split() if len(w) > 3]
            job_title = " ".join(words[:5]) if words else query

        logger.info(
            f"Using unified matcher fallback: "
            f"required_skills={required_skills}, "
            f"candidates={len(candidates)}"
        )

        results = []
        for candidate in candidates:
            # Build resume text
            resume_text = candidate.get("analysis_raw_text") or candidate.get("raw_text", "")
            resume_skills = candidate.get("skills", [])

            if not resume_text:
                candidate["semantic_score"] = 0.0
                candidate["unified_fallback"] = True
                results.append(candidate)
                continue

            try:
                # Use unified matcher for scoring
                unified_result: UnifiedMatchResult = self.unified_matcher.match(
                    resume_text=resume_text,
                    resume_skills=resume_skills,
                    job_title=job_title,
                    job_description=job_description,
                    required_skills=required_skills,
                )

                # Map unified score to semantic score
                # Unified overall_score is already 0-1, use it directly
                candidate["semantic_score"] = unified_result.overall_score
                candidate["unified_fallback"] = True
                candidate["unified_match_result"] = unified_result.to_dict()

                results.append(candidate)

            except Exception as e:
                logger.warning(f"Unified matching failed for candidate {candidate.get('id')}: {e}")
                candidate["semantic_score"] = 0.0
                candidate["unified_fallback"] = True
                candidate["unified_error"] = str(e)
                results.append(candidate)

        return results

    async def _unified_fallback_search(
        self,
        filters: SemanticSearchFilters,
    ) -> SemanticSearchResult:
        """
        Fallback to unified matcher when LLM service is unavailable.

        Uses UnifiedSkillMatcher (keyword + TF-IDF + vector) as a robust
        fallback that provides better results than simple keyword search.

        Args:
            filters: SemanticSearchFilters

        Returns:
            SemanticSearchResult with unified matcher scores
        """
        import time
        start_time = time.time()

        if not self._unified_available:
            logger.warning("Unified matcher unavailable, falling back to keyword search")
            return await self._fallback_search(filters)

        # Get job posting context
        job_context = await self._get_job_context(filters.vacancy_id)

        # Get candidate pool
        candidates = await self._get_candidate_pool(filters)

        if not candidates:
            logger.info("No candidates found for unified fallback")
            return self._empty_result(filters, time.time() - start_time)

        # Use unified matcher for all candidates
        results = await self._unified_fallback_match(
            candidates=candidates,
            query=filters.query,
            job_context=job_context,
        )

        # Filter by minimum score
        filtered_results = [
            r for r in results
            if r["semantic_score"] >= filters.min_semantic_score
        ]

        # Apply hybrid scoring
        if filters.use_hybrid:
            filtered_results = self._apply_hybrid_scoring(
                filtered_results,
                semantic_weight=filters.semantic_weight,
                keyword_weight=filters.keyword_weight,
            )

        # Sort by final score
        filtered_results.sort(key=lambda x: x.get("final_score", 0), reverse=True)

        # Apply pagination
        total = len(filtered_results)
        paginated_results = filtered_results[filters.skip:filters.skip + filters.limit]

        # Format results
        formatted_candidates = await self._format_semantic_results(paginated_results)

        execution_time = time.time() - start_time

        logger.info(
            f"Unified fallback search completed: found {total} candidates, "
            f"returned {len(formatted_candidates)} in {execution_time:.3f}s"
        )

        return SemanticSearchResult(
            total=total,
            candidates=formatted_candidates,
            query=filters.query,
            execution_time_seconds=execution_time,
            semantic_scores_used=False,
            fallback_used=True,
            filters_applied=self._serialize_filters(filters),
        )

    async def _fallback_search(
        self,
        filters: SemanticSearchFilters,
    ) -> SemanticSearchResult:
        """
        Fallback to traditional keyword-based search.

        Args:
            filters: SemanticSearchFilters

        Returns:
            SemanticSearchResult from traditional search
        """
        import time
        start_time = time.time()

        # Convert to traditional search filters
        search_filters = SearchFilters(
            skills=filters.skills,
            min_experience_years=filters.min_experience_years,
            max_experience_years=filters.max_experience_years,
            location=filters.location,
            education_level=filters.education_level,
        )

        # Use traditional search
        result = await self.search_service.search_candidates(
            query=filters.query,
            filters=search_filters,
            skip=filters.skip,
            limit=filters.limit,
        )

        # Convert to semantic result format
        candidates_with_scores = []
        for candidate in result.candidates:
            candidate["semantic_score"] = 0.0
            candidate["final_score"] = 0.0
            candidate["keyword_score"] = 1.0  # All results from keyword search
            candidates_with_scores.append(candidate)

        return SemanticSearchResult(
            total=result.total,
            candidates=candidates_with_scores,
            query=filters.query,
            execution_time_seconds=time.time() - start_time,
            semantic_scores_used=False,
            fallback_used=True,
            filters_applied=self._serialize_filters(filters),
        )

    def _empty_result(
        self,
        filters: SemanticSearchFilters,
        execution_time: float,
    ) -> SemanticSearchResult:
        """Return empty result set."""
        return SemanticSearchResult(
            total=0,
            candidates=[],
            query=filters.query,
            execution_time_seconds=execution_time,
            semantic_scores_used=self._llm_available or self._unified_available,
            fallback_used=False,
            filters_applied=self._serialize_filters(filters),
        )

    def _serialize_filters(self, filters: SemanticSearchFilters) -> Dict[str, Any]:
        """Serialize filters for response."""
        return {
            "query": filters.query,
            "vacancy_id": filters.vacancy_id,
            "min_semantic_score": filters.min_semantic_score,
            "semantic_weight": filters.semantic_weight,
            "keyword_weight": filters.keyword_weight,
            "use_hybrid": filters.use_hybrid,
            "language": filters.language,
            "skills": filters.skills,
            "min_experience_years": filters.min_experience_years,
            "max_experience_years": filters.max_experience_years,
            "location": filters.location,
            "education_level": filters.education_level,
        }


# Singleton instance getter for dependency injection
_semantic_search_service_instance: Optional[SemanticSearchService] = None


def get_semantic_search_service(
    db: AsyncSession,
    llm_matcher: Optional[LLMSemanticMatcher] = None,
    unified_matcher: Optional[UnifiedSkillMatcher] = None,
) -> SemanticSearchService:
    """
    Get or create a SemanticSearchService instance.

    This function is designed for use with FastAPI dependency injection.

    Args:
        db: Database session
        llm_matcher: Optional LLM matcher instance
        unified_matcher: Optional unified matcher instance for fallback

    Returns:
        SemanticSearchService instance

    Example:
        >>> from fastapi import Depends
        >>> from database import get_db
        >>> from services.semantic_search_service import get_semantic_search_service
        >>>
        >>> @router.post("/semantic-search")
        >>> async def semantic_search(
        >>>     filters: SemanticSearchFilters,
        >>>     db: AsyncSession = Depends(get_db),
        >>>     search_service: SemanticSearchService = Depends(get_semantic_search_service)
        >>> ):
        >>>     results = await search_service.semantic_search_candidates(filters)
        >>>     return results
    """
    return SemanticSearchService(db, llm_matcher, unified_matcher)
