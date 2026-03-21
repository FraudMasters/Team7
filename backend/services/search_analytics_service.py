"""
Search Analytics Service

This module provides analytics tracking and reporting for search queries.
It tracks all search queries, maintains popular search statistics, manages
per-user recent searches, and provides insights into search patterns.

Features:
- Track all search queries with performance metrics
- Maintain popular search statistics with aggregated data
- Per-user recent search history with automatic deduplication
- Zero-result search tracking for query optimization
- Click-through rate tracking for relevance tuning
- Search analytics reports and insights

The service works with three main tables:
- search_queries: Individual search query logs
- popular_searches: Aggregated popular search statistics
- recent_searches: Per-user recent search history
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models import SearchQuery, PopularSearch, RecentSearch

logger = logging.getLogger(__name__)


class SearchAnalyticsService:
    """
    Service for tracking and analyzing search queries.

    This service provides comprehensive search analytics including:
    - Query tracking with performance metrics
    - Popular search aggregation
    - Recent search management
    - Zero-result search detection
    - Click-through rate tracking
    """

    # Maximum number of recent searches to keep per user
    MAX_RECENT_SEARCHES = 50

    def __init__(self, db: AsyncSession):
        """
        Initialize the search analytics service.

        Args:
            db: Database session for executing queries
        """
        self.db = db

    async def track_search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        results_count: int = 0,
        execution_time_ms: Optional[float] = None,
        search_type: Optional[str] = None,
        recruiter_id: Optional[UUID] = None,
    ) -> SearchQuery:
        """
        Track a search query with metadata.

        This method records every search performed in the system for analytics.
        It creates a SearchQuery record and updates related analytics tables.

        Args:
            query: Search query string
            filters: Filter settings applied to the search
            results_count: Number of results returned
            execution_time_ms: Time taken to execute search in milliseconds
            search_type: Type of search (e.g., 'full_text', 'faceted', 'boolean')
            recruiter_id: ID of recruiter who performed the search

        Returns:
            SearchQuery: Created search query record

        Raises:
            ValueError: If query is empty or invalid
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            logger.info(
                f"Tracking search - query: {query}, results: {results_count}, "
                f"recruiter_id: {recruiter_id}"
            )

            # Create search query record
            search_query = SearchQuery(
                id=uuid4(),
                recruiter_id=recruiter_id,
                query=query.strip(),
                filters=filters or {},
                results_count=results_count,
                execution_time_ms=execution_time_ms,
                search_type=search_type,
                clicked_result_ids=[],
            )

            self.db.add(search_query)

            # Update popular searches in background (don't await to keep fast)
            await self._update_popular_search(query, filters, results_count)

            # Update recent searches for the user
            if recruiter_id:
                await self._update_recent_search(
                    recruiter_id, query, filters, results_count
                )

            await self.db.commit()
            await self.db.refresh(search_query)

            logger.info(f"Successfully tracked search query: {search_query.id}")
            return search_query

        except Exception as e:
            logger.error(f"Error tracking search: {e}")
            await self.db.rollback()
            raise

    async def track_click(
        self,
        search_query_id: UUID,
        clicked_resume_id: UUID,
    ) -> bool:
        """
        Track a click on a search result.

        Updates the clicked_result_ids for a search query to track which
        results were clicked, enabling click-through rate analysis.

        Args:
            search_query_id: ID of the search query
            clicked_resume_id: ID of the resume that was clicked

        Returns:
            bool: True if click was tracked successfully

        Raises:
            ValueError: If search query not found
        """
        try:
            logger.info(
                f"Tracking click - search_query_id: {search_query_id}, "
                f"resume_id: {clicked_resume_id}"
            )

            # Get the search query
            result = await self.db.execute(
                select(SearchQuery).where(SearchQuery.id == search_query_id)
            )
            search_query = result.scalar_one_or_none()

            if not search_query:
                raise ValueError(f"Search query {search_query_id} not found")

            # Update clicked results
            clicked_ids = search_query.clicked_result_ids or []
            if str(clicked_resume_id) not in clicked_ids:
                clicked_ids.append(str(clicked_resume_id))
                search_query.clicked_result_ids = clicked_ids

            await self.db.commit()
            logger.info(f"Successfully tracked click for search {search_query_id}")
            return True

        except Exception as e:
            logger.error(f"Error tracking click: {e}")
            await self.db.rollback()
            raise

    async def get_popular_searches(
        self,
        limit: int = 10,
        min_search_count: int = 2,
        days: Optional[int] = None,
    ) -> List[PopularSearch]:
        """
        Get popular search queries.

        Returns the most popular search queries based on search count,
        optionally filtered by recent activity.

        Args:
            limit: Maximum number of results to return
            min_search_count: Minimum number of times a query must be searched
            days: Only include searches from last N days (optional)

        Returns:
            List[PopularSearch]: Popular search records ordered by search count
        """
        try:
            logger.info(
                f"Getting popular searches - limit: {limit}, min_count: {min_search_count}"
            )

            query = select(PopularSearch).where(
                PopularSearch.search_count >= min_search_count
            )

            # Filter by recent activity if specified
            if days:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                query = query.where(PopularSearch.last_searched_at >= cutoff_date)

            # Order by search count descending
            query = query.order_by(PopularSearch.search_count.desc()).limit(limit)

            result = await self.db.execute(query)
            popular_searches = result.scalars().all()

            logger.info(f"Found {len(popular_searches)} popular searches")
            return list(popular_searches)

        except Exception as e:
            logger.error(f"Error getting popular searches: {e}")
            raise

    async def get_recent_searches(
        self,
        recruiter_id: UUID,
        limit: int = 10,
    ) -> List[RecentSearch]:
        """
        Get recent searches for a recruiter.

        Returns the most recent search queries performed by a specific recruiter.

        Args:
            recruiter_id: ID of the recruiter
            limit: Maximum number of results to return

        Returns:
            List[RecentSearch]: Recent search records ordered by most recent
        """
        try:
            logger.info(f"Getting recent searches for recruiter: {recruiter_id}")

            query = (
                select(RecentSearch)
                .where(RecentSearch.recruiter_id == recruiter_id)
                .order_by(RecentSearch.updated_at.desc())
                .limit(limit)
            )

            result = await self.db.execute(query)
            recent_searches = result.scalars().all()

            logger.info(
                f"Found {len(recent_searches)} recent searches for recruiter {recruiter_id}"
            )
            return list(recent_searches)

        except Exception as e:
            logger.error(f"Error getting recent searches: {e}")
            raise

    async def get_zero_result_searches(
        self,
        days: int = 7,
        limit: int = 100,
    ) -> List[SearchQuery]:
        """
        Get searches that returned zero results.

        Identifies queries that returned no results, useful for improving
        search quality and identifying gaps in the candidate database.

        Args:
            days: Number of days to look back
            limit: Maximum number of results to return

        Returns:
            List[SearchQuery]: Search queries with zero results
        """
        try:
            logger.info(f"Getting zero-result searches from last {days} days")

            cutoff_date = datetime.utcnow() - timedelta(days=days)

            query = (
                select(SearchQuery)
                .where(
                    and_(
                        SearchQuery.results_count == 0,
                        SearchQuery.created_at >= cutoff_date,
                    )
                )
                .order_by(SearchQuery.created_at.desc())
                .limit(limit)
            )

            result = await self.db.execute(query)
            zero_result_searches = result.scalars().all()

            logger.info(f"Found {len(zero_result_searches)} zero-result searches")
            return list(zero_result_searches)

        except Exception as e:
            logger.error(f"Error getting zero-result searches: {e}")
            raise

    async def get_search_analytics(
        self,
        days: int = 30,
        recruiter_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Get comprehensive search analytics.

        Provides aggregated statistics about search usage, performance,
        and patterns over a specified time period.

        Args:
            days: Number of days to include in analytics
            recruiter_id: Optional filter for specific recruiter

        Returns:
            Dict containing analytics data:
            - total_searches: Total number of searches
            - avg_results: Average number of results per search
            - zero_result_rate: Percentage of searches with zero results
            - avg_execution_time_ms: Average search execution time
            - unique_queries: Number of unique query strings
            - search_types: Breakdown by search type
        """
        try:
            logger.info(
                f"Getting search analytics for last {days} days, "
                f"recruiter_id: {recruiter_id}"
            )

            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Build base query
            base_query = select(SearchQuery).where(
                SearchQuery.created_at >= cutoff_date
            )

            if recruiter_id:
                base_query = base_query.where(SearchQuery.recruiter_id == recruiter_id)

            # Get total searches
            count_query = select(func.count()).select_from(base_query.alias())
            total_result = await self.db.execute(count_query)
            total_searches = total_result.scalar() or 0

            # Get aggregate statistics
            stats_query = select(
                func.avg(SearchQuery.results_count).label("avg_results"),
                func.avg(SearchQuery.execution_time_ms).label("avg_execution_time"),
                func.sum(
                    func.case((SearchQuery.results_count == 0, 1), else_=0)
                ).label("zero_result_count"),
                func.count(func.distinct(SearchQuery.query)).label("unique_queries"),
            ).where(SearchQuery.created_at >= cutoff_date)

            if recruiter_id:
                stats_query = stats_query.where(
                    SearchQuery.recruiter_id == recruiter_id
                )

            stats_result = await self.db.execute(stats_query)
            stats = stats_result.one()

            # Calculate zero result rate
            zero_result_rate = (
                (stats.zero_result_count / total_searches * 100)
                if total_searches > 0
                else 0
            )

            # Get search type breakdown
            type_query = (
                select(
                    SearchQuery.search_type,
                    func.count().label("count"),
                )
                .where(SearchQuery.created_at >= cutoff_date)
                .group_by(SearchQuery.search_type)
            )

            if recruiter_id:
                type_query = type_query.where(SearchQuery.recruiter_id == recruiter_id)

            type_result = await self.db.execute(type_query)
            search_types = {
                row.search_type or "unknown": row.count for row in type_result.all()
            }

            analytics = {
                "total_searches": total_searches,
                "avg_results": float(stats.avg_results or 0),
                "zero_result_rate": round(zero_result_rate, 2),
                "avg_execution_time_ms": float(stats.avg_execution_time or 0),
                "unique_queries": stats.unique_queries or 0,
                "search_types": search_types,
                "period_days": days,
            }

            logger.info(f"Search analytics: {analytics}")
            return analytics

        except Exception as e:
            logger.error(f"Error getting search analytics: {e}")
            raise

    async def _update_popular_search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]],
        results_count: int,
    ) -> None:
        """
        Update or create popular search record.

        Internal method to maintain aggregated statistics for popular searches.

        Args:
            query: Search query string
            filters: Filter settings applied
            results_count: Number of results returned
        """
        try:
            # Check if popular search exists
            result = await self.db.execute(
                select(PopularSearch).where(PopularSearch.query == query.strip())
            )
            popular_search = result.scalar_one_or_none()

            if popular_search:
                # Update existing popular search
                popular_search.search_count += 1
                popular_search.last_searched_at = datetime.utcnow()

                # Update average results count
                if popular_search.avg_results_count is None:
                    popular_search.avg_results_count = float(results_count)
                else:
                    # Calculate running average
                    total_results = (
                        popular_search.avg_results_count * (popular_search.search_count - 1)
                        + results_count
                    )
                    popular_search.avg_results_count = (
                        total_results / popular_search.search_count
                    )
            else:
                # Create new popular search
                popular_search = PopularSearch(
                    id=uuid4(),
                    query=query.strip(),
                    filters=filters or {},
                    search_count=1,
                    avg_results_count=float(results_count),
                    avg_click_through_rate=0.0,
                    last_searched_at=datetime.utcnow(),
                )
                self.db.add(popular_search)

        except Exception as e:
            logger.error(f"Error updating popular search: {e}")

    async def _update_recent_search(
        self,
        recruiter_id: UUID,
        query: str,
        filters: Optional[Dict[str, Any]],
        results_count: int,
    ) -> None:
        """
        Update or create recent search for a recruiter.

        Internal method to maintain per-user recent search history.
        Uses unique constraint to update existing entries instead of duplicating.

        Args:
            recruiter_id: ID of the recruiter
            query: Search query string
            filters: Filter settings applied
            results_count: Number of results returned
        """
        try:
            # Check if recent search exists (unique on recruiter_id + query)
            result = await self.db.execute(
                select(RecentSearch).where(
                    and_(
                        RecentSearch.recruiter_id == recruiter_id,
                        RecentSearch.query == query.strip(),
                    )
                )
            )
            recent_search = result.scalar_one_or_none()

            if recent_search:
                # Update existing recent search (updates timestamp)
                recent_search.filters = filters or {}
                recent_search.results_count = results_count
                recent_search.updated_at = datetime.utcnow()
            else:
                # Create new recent search
                recent_search = RecentSearch(
                    id=uuid4(),
                    recruiter_id=recruiter_id,
                    query=query.strip(),
                    filters=filters or {},
                    results_count=results_count,
                )
                self.db.add(recent_search)

                # Clean up old recent searches if we exceed the limit
                await self._cleanup_old_recent_searches(recruiter_id)

        except Exception as e:
            logger.error(f"Error updating recent search: {e}")

    async def _cleanup_old_recent_searches(self, recruiter_id: UUID) -> None:
        """
        Remove old recent searches if limit is exceeded.

        Keeps only the most recent MAX_RECENT_SEARCHES for a recruiter.

        Args:
            recruiter_id: ID of the recruiter
        """
        try:
            # Get count of recent searches for this recruiter
            count_query = select(func.count()).where(
                RecentSearch.recruiter_id == recruiter_id
            )
            count_result = await self.db.execute(count_query)
            count = count_result.scalar() or 0

            if count > self.MAX_RECENT_SEARCHES:
                # Get IDs of searches to delete (oldest ones)
                delete_count = count - self.MAX_RECENT_SEARCHES
                subquery = (
                    select(RecentSearch.id)
                    .where(RecentSearch.recruiter_id == recruiter_id)
                    .order_by(RecentSearch.updated_at.asc())
                    .limit(delete_count)
                )

                result = await self.db.execute(subquery)
                ids_to_delete = [row[0] for row in result.all()]

                if ids_to_delete:
                    # Delete old searches
                    from sqlalchemy import delete
                    await self.db.execute(
                        delete(RecentSearch).where(RecentSearch.id.in_(ids_to_delete))
                    )

        except Exception as e:
            logger.error(f"Error cleaning up recent searches: {e}")
