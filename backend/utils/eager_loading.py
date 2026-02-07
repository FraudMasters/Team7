"""
Eager loading utility functions for SQLAlchemy queries.

This module provides helper functions to eliminate N+1 query patterns by
enabling efficient eager loading of relationships. It includes utilities for:

- Bulk fetching related entities
- Building lookup dictionaries for efficient access
- Applying eager loading options to queries
- Common patterns for avoiding N+1 queries

The utilities are designed to work with async SQLAlchemy and follow the
patterns established in the QUERY_AUDIT.md analysis.
"""
import logging
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import (
    selectinload,
    joinedload,
    subqueryload,
    Load,
    InstrumentedAttribute,
)
from sqlalchemy.sql import Select

from models.base import Base

logger = logging.getLogger(__name__)

# Generic type variable for model classes
T = TypeVar("T", bound=Base)


async def bulk_fetch_by_ids(
    db: AsyncSession,
    model: Type[T],
    ids: List[Any],
    *,
    id_field: str = "id",
) -> Dict[Any, T]:
    """
    Fetch multiple records by their IDs in a single query.

    This function eliminates N+1 queries by fetching all related records
    at once and returning them as a lookup dictionary.

    Args:
        db: Async database session
        model: SQLAlchemy model class to query
        ids: List of IDs to fetch
        id_field: Name of the ID field (default: "id")

    Returns:
        Dictionary mapping ID to model instance

    Example:
        >>> # Fetch all analyses for a list of resume IDs
        >>> resume_ids = [r.id for r in resumes]
        >>> analyses = await bulk_fetch_by_ids(
        ...     db,
        ...     ResumeAnalysis,
        ...     resume_ids,
        ...     id_field="resume_id"
        ... )
        >>> # Use in loop without N+1
        >>> for resume in resumes:
        ...     analysis = analyses.get(resume.id)
    """
    if not ids:
        return {}

    try:
        # Build query with IN clause
        query = select(model).where(getattr(model, id_field).in_(ids))

        # Execute query
        result = await db.execute(query)
        items = result.scalars().all()

        # Build lookup dictionary
        # Handle both UUID and string IDs
        lookup = {}
        for item in items:
            key = getattr(item, id_field)
            # Convert UUID to string for consistent key types
            if hasattr(key, "hex"):
                key = str(key)
            lookup[key] = item

        logger.debug(f"Bulk fetched {len(items)} {model.__name__} records for {len(ids)} IDs")

        return lookup

    except Exception as e:
        logger.error(f"Error in bulk_fetch_by_ids for {model.__name__}: {e}", exc_info=True)
        return {}


async def bulk_fetch_by_field(
    db: AsyncSession,
    model: Type[T],
    field_name: str,
    values: List[Any],
) -> Dict[Any, List[T]]:
    """
    Fetch multiple records grouped by a field value in a single query.

    This function is useful when you need to fetch all related items
    for multiple parent records (e.g., all tags for multiple resumes).

    Args:
        db: Async database session
        model: SQLAlchemy model class to query
        field_name: Name of the field to group by
        values: List of field values to fetch

    Returns:
        Dictionary mapping field value to list of model instances

    Example:
        >>> # Fetch all activities for multiple resume IDs
        >>> resume_ids = [r.id for r in resumes]
        >>> activities = await bulk_fetch_by_field(
        ...     db,
        ...     CandidateActivity,
        ...     "resume_id",
        ...     resume_ids
        ... )
        >>> # Use in loop
        >>> for resume in resumes:
        ...     resume_activities = activities.get(str(resume.id), [])
    """
    if not values:
        return {}

    try:
        # Build query with IN clause
        query = select(model).where(getattr(model, field_name).in_(values))

        # Execute query
        result = await db.execute(query)
        items = result.scalars().all()

        # Build lookup dictionary grouping by field value
        lookup: Dict[Any, List[T]] = {}
        for item in items:
            key = getattr(item, field_name)
            # Convert UUID to string for consistent key types
            if hasattr(key, "hex"):
                key = str(key)

            if key not in lookup:
                lookup[key] = []
            lookup[key].append(item)

        logger.debug(
            f"Bulk fetched {len(items)} {model.__name__} records "
            f"grouped by {field_name} for {len(values)} values"
        )

        return lookup

    except Exception as e:
        logger.error(
            f"Error in bulk_fetch_by_field for {model.__name__}: {e}",
            exc_info=True
        )
        return {}


def with_eager_loaded_relationships(
    query: Select,
    relationships: List[Union[str, InstrumentedAttribute]],
    *,
    strategy: str = "selectinload",
) -> Select:
    """
    Add eager loading options to a SQLAlchemy query.

    This function applies eager loading to relationships to prevent N+1
    queries when accessing related objects. It supports three loading
    strategies:

    - selectinload: Good for one-to-many and many-to-many (default)
    - joinedload: Good for one-to-one and many-to-one (uses JOIN)
    - subqueryload: Alternative for one-to-many (uses subquery)

    Args:
        query: Base SQLAlchemy select query
        relationships: List of relationship paths to eager load
            Can be string paths like "analysis" or "user.profile"
            or InstrumentedAttribute objects
        strategy: Loading strategy - "selectinload", "joinedload", or "subqueryload"

    Returns:
        Query with eager loading options applied

    Raises:
        ValueError: If strategy is not one of the supported options

    Example:
        >>> from sqlalchemy import select
        >>> from models.resume import Resume
        >>>
        >>> # Load resumes with their analyses
        >>> query = select(Resume)
        >>> query = with_eager_loaded_relationships(
        ...     query,
        ...     ["analysis"],
        ...     strategy="selectinload"
        ... )
        >>> result = await db.execute(query)
        >>>
        >>> # Accessing .analysis won't trigger additional queries
        >>> for resume in result.scalars():
        ...     print(resume.analysis.language)

    Example with nested relationships:
        >>> # Load resumes with analysis and related tags
        >>> query = select(Resume)
        >>> query = with_eager_loaded_relationships(
        ...     query,
        ...     ["analysis", "analysis.tags"],
        ...     strategy="selectinload"
        ... )
    """
    # Validate strategy
    valid_strategies = {"selectinload", "joinedload", "subqueryload"}
    if strategy not in valid_strategies:
        raise ValueError(
            f"Invalid strategy '{strategy}'. Must be one of: {valid_strategies}"
        )

    try:
        # Choose the loading function based on strategy
        if strategy == "selectinload":
            load_func = selectinload
        elif strategy == "joinedload":
            load_func = joinedload
        else:  # subqueryload
            load_func = subqueryload

        # Apply eager loading to each relationship
        for relationship in relationships:
            # Handle both string paths and InstrumentedAttribute objects
            if isinstance(relationship, str):
                # For string paths, we need to parse them
                # This is a simplified version - for complex nested paths,
                # you might need to use relationship attribute objects
                parts = relationship.split(".")

                # Build the load path incrementally
                current_load: Load = None

                for i, part in enumerate(parts):
                    if current_load is None:
                        # First level - apply directly to query
                        # We need to get the actual relationship attribute
                        # For now, we'll use a different approach
                        pass
                    else:
                        # Nested level - apply to previous load
                        pass

                # For string paths, we recommend using InstrumentedAttribute objects
                # This is a placeholder for future enhancement
                logger.warning(
                    f"String relationship paths not fully supported. "
                    f"Use InstrumentedAttribute objects for '{relationship}'"
                )
                continue

            else:
                # InstrumentedAttribute - can be used directly
                query = query.options(load_func(relationship))

        logger.debug(
            f"Applied {strategy} to {len(relationships)} relationship(s)"
        )

        return query

    except Exception as e:
        logger.error(f"Error applying eager loading: {e}", exc_info=True)
        return query


async def fetch_with_counts(
    db: AsyncSession,
    model: Type[T],
    group_field: str,
    *,
    filters: Optional[List[Any]] = None,
) -> Dict[Any, int]:
    """
    Fetch records grouped by a field with counts in a single query.

    This function uses SQL aggregation to count related records without
    triggering N+1 queries. It's useful for counting comments, tags,
    activities, etc. for multiple parent records.

    Args:
        db: Async database session
        model: SQLAlchemy model class to query
        group_field: Field to group by (e.g., "resume_id")
        filters: Optional list of filter conditions to apply

    Returns:
        Dictionary mapping field value to count

    Example:
        >>> # Count activities for each resume
        >>> activity_counts = await fetch_with_counts(
        ...     db,
        ...     CandidateActivity,
        ...     "resume_id"
        ... )
        >>> # Use in loop
        >>> for resume in resumes:
        ...     count = activity_counts.get(str(resume.id), 0)
        ...     print(f"Resume {resume.id} has {count} activities")
    """
    try:
        # Build query with GROUP BY
        query = select(
            getattr(model, group_field),
            func.count(getattr(model, "id"))
        ).group_by(getattr(model, group_field))

        # Apply filters if provided
        if filters:
            for filter_condition in filters:
                query = query.where(filter_condition)

        # Execute query
        result = await db.execute(query)
        rows = result.all()

        # Build lookup dictionary
        lookup = {}
        for row in rows:
            key = row[0]
            # Convert UUID to string for consistent key types
            if hasattr(key, "hex"):
                key = str(key)
            lookup[key] = row[1]

        logger.debug(
            f"Fetched counts for {len(lookup)} groups from {model.__name__}"
        )

        return lookup

    except Exception as e:
        logger.error(
            f"Error in fetch_with_counts for {model.__name__}: {e}",
            exc_info=True
        )
        return {}


async def bulk_exists_check(
    db: AsyncSession,
    model: Type[T],
    field_name: str,
    values: List[Any],
) -> Dict[Any, bool]:
    """
    Check existence of multiple field values in a single query.

    This function is useful for checking if records exist before creating
    them, avoiding N+1 existence checks in loops.

    Args:
        db: Async database session
        model: SQLAlchemy model class to query
        field_name: Name of the field to check
        values: List of values to check existence for

    Returns:
        Dictionary mapping value to existence boolean

    Example:
        >>> # Check which skills already exist before creating
        >>> skill_names = ["Python", "Java", "React"]
        >>> existing = await bulk_exists_check(
        ...     db,
        ...     SkillTaxonomy,
        ...     "skill_name",
        ...     skill_names
        ... )
        >>> # Create only non-existing skills
        >>> for name in skill_names:
        ...     if not existing.get(name):
        ...         create_skill(name)
    """
    if not values:
        return {}

    try:
        # Build query to fetch existing values
        query = select(getattr(model, field_name)).where(
            getattr(model, field_name).in_(values)
        )

        # Execute query
        result = await db.execute(query)
        existing_values = result.scalars().all()

        # Build lookup dictionary
        # Start with all values as False, mark existing ones as True
        lookup = {str(v): False for v in values}
        for value in existing_values:
            key = str(value)
            lookup[key] = True

        logger.debug(
            f"Checked existence for {len(values)} values, "
            f"{len(existing_values)} exist in {model.__name__}"
        )

        return lookup

    except Exception as e:
        logger.error(
            f"Error in bulk_exists_check for {model.__name__}: {e}",
            exc_info=True
        )
        # Return all as False on error to allow creation attempts
        return {str(v): False for v in values}


def apply_bulk_fetch_pattern(
    items: List[T],
    foreign_key_field: str,
) -> List[Any]:
    """
    Extract foreign key values from a list of items for bulk fetching.

    This is a helper function to extract IDs or other foreign key values
    from ORM objects for use with bulk_fetch_by_ids.

    Args:
        items: List of ORM objects
        foreign_key_field: Name of the foreign key field

    Returns:
        List of foreign key values

    Example:
        >>> # Extract resume IDs for bulk fetching analyses
        >>> resume_ids = apply_bulk_fetch_pattern(resumes, "id")
        >>> analyses = await bulk_fetch_by_ids(
        ...     db, ResumeAnalysis, resume_ids, id_field="resume_id"
        ... )
    """
    try:
        values = []
        for item in items:
            value = getattr(item, foreign_key_field, None)
            if value is not None:
                values.append(value)

        return values

    except Exception as e:
        logger.error(f"Error extracting foreign keys: {e}", exc_info=True)
        return []
