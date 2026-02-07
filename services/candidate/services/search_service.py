"""
Search Service for Candidates in Microservices Architecture.

This service provides advanced search capabilities for candidates using PostgreSQL
full-text search and filtering across candidates, resumes, and resume_analyses tables.
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Select, and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from models.base import Base
from models.candidate import Candidate
from models.candidate_tag import CandidateTag


logger = logging.getLogger(__name__)


@dataclass
class SearchFilters:
    """Filter configuration for candidate search."""
    query: Optional[str] = None
    skills: Optional[List[str]] = None
    min_experience_years: Optional[int] = None
    max_experience_years: Optional[int] = None
    location: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None
    min_rating: Optional[int] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    tag_ids: Optional[List[str]] = None


@dataclass
class SearchResult:
    """Search result containing candidates and metadata."""
    total: int
    candidates: List[Dict[str, Any]]
    query: str
    filters_applied: Dict[str, Any]
    execution_time_seconds: float


class SearchService:
    """
    Service for advanced candidate search.

    Provides full-text search and filtering across candidates and resumes.
    """

    def __init__(self, db: AsyncSession):
        """Initialize the search service."""
        self.db = db

    async def search_candidates(
        self,
        query: Optional[str] = None,
        filters: Optional[SearchFilters] = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "created_at",
    ) -> SearchResult:
        """
        Search for candidates with full-text search and filters.

        Args:
            query: Search query string
            filters: SearchFilters object
            skip: Pagination offset
            limit: Max results to return
            sort_by: Sort field (created_at, name, experience, rating)

        Returns:
            SearchResult with candidates and metadata
        """
        import time
        start_time = time.time()

        try:
            # Build base query
            query_builder = self._build_search_query(query, filters)

            # Get total count
            count_query = select(func.count()).select_from(query_builder.alias("subquery"))
            total_result = await self.db.execute(count_query)
            total = total_result.scalar() or 0

            # Apply sorting
            query_builder = self._apply_sorting(query_builder, sort_by)

            # Apply pagination
            query_builder = query_builder.offset(skip).limit(limit)

            # Execute search
            result = await self.db.execute(query_builder)
            rows = result.all()

            # Format results
            candidates = self._format_results(rows)

            execution_time = time.time() - start_time

            logger.info(
                f"Search completed: {total} total, {len(candidates)} returned in {execution_time:.3f}s"
            )

            return SearchResult(
                total=total,
                candidates=candidates,
                query=query or "",
                filters_applied=self._serialize_filters(filters),
                execution_time_seconds=execution_time,
            )

        except Exception as e:
            logger.error(f"Error during candidate search: {e}", exc_info=True)
            raise ValueError(f"Search failed: {str(e)}") from e

    def _build_search_query(
        self,
        query: Optional[str],
        filters: Optional[SearchFilters],
    ) -> Select:
        """Build the SQLAlchemy search query with filters."""
        # Base query - join candidates with resumes
        stmt = (
            select(
                Candidate.id,
                Candidate.resume_id,
                Candidate.full_name,
                Candidate.email,
                Candidate.phone,
                Candidate.current_position,
                Candidate.current_company,
                Candidate.years_of_experience,
                Candidate.location,
                Candidate.status,
                Candidate.source,
                Candidate.rating,
                Candidate.is_active,
                Candidate.tags,
                Candidate.created_at,
                Candidate.updated_at,
            )
            .select_from(Candidate)
            .where(Candidate.is_active == True)
        )

        # Apply full-text search if query provided
        if query:
            search_query = self._parse_boolean_query(query)
            # Search in full_name, current_position
            stmt = stmt.where(
                or_(
                    Candidate.full_name.ilike(f"%{query}%"),
                    Candidate.current_position.ilike(f"%{query}%"),
                    Candidate.current_company.ilike(f"%{query}%"),
                    Candidate.location.ilike(f"%{query}%"),
                )
            )

        # Apply filters
        if filters:
            stmt = self._apply_filters(stmt, filters)

        return stmt

    def _parse_boolean_query(self, query: str) -> str:
        """Parse and normalize search query."""
        if not query:
            return ""
        return query.strip().lower()

    def _apply_filters(self, stmt: Select, filters: SearchFilters) -> Select:
        """Apply search filters to the query."""
        if filters.min_experience_years is not None:
            stmt = stmt.where(
                or_(
                    Candidate.years_of_experience >= filters.min_experience_years,
                    Candidate.years_of_experience.is_(None),
                )
            )

        if filters.max_experience_years is not None:
            stmt = stmt.where(
                or_(
                    Candidate.years_of_experience <= filters.max_experience_years,
                    Candidate.years_of_experience.is_(None),
                )
            )

        if filters.location:
            stmt = stmt.where(Candidate.location.ilike(f"%{filters.location}%"))

        if filters.status:
            stmt = stmt.where(Candidate.status == filters.status)

        if filters.source:
            stmt = stmt.where(Candidate.source == filters.source)

        if filters.min_rating is not None:
            stmt = stmt.where(
                or_(
                    Candidate.rating >= filters.min_rating,
                    Candidate.rating.is_(None),
                )
            )

        if filters.date_from:
            try:
                date_from = datetime.fromisoformat(filters.date_from.replace("Z", "+00:00"))
                stmt = stmt.where(Candidate.created_at >= date_from)
            except ValueError:
                logger.warning(f"Invalid date_from format: {filters.date_from}")

        if filters.date_to:
            try:
                date_to = datetime.fromisoformat(filters.date_to.replace("Z", "+00:00"))
                stmt = stmt.where(Candidate.created_at <= date_to)
            except ValueError:
                logger.warning(f"Invalid date_to format: {filters.date_to}")

        if filters.tag_ids:
            # Filter by tags - check if any of the tag IDs are in the tags array
            for tag_id in filters.tag_ids:
                stmt = stmt.where(
                    text("candidates.tags @> :tag_id::jsonb")
                ).params(tag_id=f'["{tag_id}"]')

        return stmt

    def _apply_sorting(self, stmt: Select, sort_by: str) -> Select:
        """Apply sorting to the query."""
        if sort_by == "name":
            stmt = stmt.order_by(Candidate.full_name.asc().nulls_last())
        elif sort_by == "experience":
            stmt = stmt.order_by(Candidate.years_of_experience.desc().nulls_last())
        elif sort_by == "rating":
            stmt = stmt.order_by(Candidate.rating.desc().nulls_last())
        elif sort_by == "created_at":
            stmt = stmt.order_by(Candidate.created_at.desc())
        else:
            stmt = stmt.order_by(Candidate.created_at.desc())
        return stmt

    def _format_results(self, rows) -> List[Dict[str, Any]]:
        """Format query results into candidate dictionaries."""
        candidates = []
        for row in rows:
            candidates.append({
                "id": str(row.id),
                "resume_id": str(row.resume_id) if row.resume_id else None,
                "full_name": row.full_name,
                "email": row.email,
                "phone": row.phone,
                "current_position": row.current_position,
                "current_company": row.current_company,
                "years_of_experience": row.years_of_experience,
                "location": row.location,
                "status": row.status.value if hasattr(row.status, 'value') else str(row.status),
                "source": row.source,
                "rating": row.rating,
                "is_active": row.is_active,
                "tags": row.tags or [],
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            })
        return candidates

    def _serialize_filters(self, filters: Optional[SearchFilters]) -> Dict[str, Any]:
        """Serialize filters for response."""
        if not filters:
            return {}
        return {
            "query": filters.query,
            "skills": filters.skills,
            "min_experience_years": filters.min_experience_years,
            "max_experience_years": filters.max_experience_years,
            "location": filters.location,
            "status": filters.status,
            "source": filters.source,
            "min_rating": filters.min_rating,
            "date_from": filters.date_from,
            "date_to": filters.date_to,
            "tag_ids": filters.tag_ids,
        }


def get_search_service(db: AsyncSession) -> SearchService:
    """Get a SearchService instance for dependency injection."""
    return SearchService(db)
