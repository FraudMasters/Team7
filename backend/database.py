"""
Database connection and session management for async SQLAlchemy.

This module provides the database engine, session factory, and dependency
injection for FastAPI endpoints. It also includes SQLAlchemy event listeners
for automatic query performance monitoring and organization context helpers
for multi-tenant data isolation.

Features:
- Async database engine and session management
- Query performance monitoring with Prometheus metrics
- Organization context for multi-tenant data isolation
- Helper functions for automatic organization-based filtering

Example Usage:
    # Standard database session
    @router.get("/")
    async def get_items(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(Item))
        return result.scalars().all()

    # Database session with organization context
    @router.get("/")
    async def get_items(
        request: Request,
        db: AsyncSession = Depends(get_db_with_org_context)
    ):
        org_id = get_organization_id(db)
        result = await db.execute(
            select(Item).filter_by(organization_id=org_id)
        )
        return result.scalars().all()
"""
import logging
import re
from typing import AsyncGenerator, Optional

from fastapi import Request
from sqlalchemy import Select, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from config import get_settings
from utils.metrics import get_metrics_registry

logger = logging.getLogger(__name__)
settings = get_settings()

# Create async engine with asyncpg driver
engine = create_async_engine(
    settings.get_db_url_async(),
    echo=settings.log_level == "DEBUG",
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


# Query performance monitoring
def _extract_table_and_operation(query: str) -> tuple[str, str]:
    """
    Extract the SQL operation type and table name from a query.

    Args:
        query: SQL query string

    Returns:
        Tuple of (operation, table_name)
        - operation: SELECT, INSERT, UPDATE, DELETE, or OTHER
        - table_name: Extracted table name or 'unknown'

    Example:
        >>> _extract_table_and_operation("SELECT * FROM resumes WHERE id = 1")
        ('SELECT', 'resumes')
    """
    try:
        # Remove leading/trailing whitespace and convert to uppercase for parsing
        query_clean = query.strip().upper()

        # Match basic SQL operations
        match = re.match(
            r"^\s*(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\s+(?:.*?\s+)?(?:FROM|INTO|TABLE)?\s*([A-Z_][A-Z0-9_]*)",
            query_clean,
            re.IGNORECASE
        )

        if match:
            operation = match.group(1)
            table_name = match.group(2) if len(match.groups()) > 1 else "unknown"
            return operation, table_name.lower()

        # Fallback: try to extract first word as operation
        first_word = query_clean.split()[0] if query_clean.split() else "OTHER"
        return first_word, "unknown"

    except Exception as e:
        logger.debug(f"Failed to parse query: {e}")
        return "OTHER", "unknown"


# Dictionary to store query start times for each connection
_query_start_times: dict = {}


@event.listens_for(engine.sync_engine, "before_cursor_execute")
def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """
    Event listener for before cursor execution.

    Records the start time for each query to enable performance tracking.
    This is triggered before any database query is executed.

    Args:
        conn: Database connection
        cursor: Database cursor
        statement: SQL statement being executed
        parameters: Query parameters
        context: Execution context
        executemany: Whether executemany is being used
    """
    import time
    _query_start_times[conn] = time.time()


@event.listens_for(engine.sync_engine, "after_cursor_execute")
def _after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """
    Event listener for after cursor execution.

    Calculates query execution time and records metrics to Prometheus.
    This is triggered after each database query completes.

    Args:
        conn: Database connection
        cursor: Database cursor
        statement: SQL statement that was executed
        parameters: Query parameters
        context: Execution context
        executemany: Whether executemany was used
    """
    import time

    try:
        # Get start time and calculate duration
        start_time = _query_start_times.pop(conn, None)
        if start_time is None:
            return

        duration = time.time() - start_time

        # Extract operation and table from the query
        operation, table = _extract_table_and_operation(statement)

        # Record metrics
        metrics_registry = get_metrics_registry()
        metrics_registry.record_db_query(
            operation=operation,
            table=table,
            duration=duration,
            status="success"
        )

        logger.debug(
            f"DB query: {operation} on {table} took {duration:.3f}s"
        )

    except Exception as e:
        logger.error(f"Error recording query metrics: {e}", exc_info=True)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection for database sessions.

    This function is used as a FastAPI dependency to provide database
    sessions to endpoints. It automatically handles session cleanup.

    Yields:
        AsyncSession: SQLAlchemy async session

    Example:
        @router.get("/")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_with_org_context(
    request: Request
) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection for database sessions with organization context.

    This function provides database sessions with automatic organization context
    from the request headers. The organization_id is extracted from the request
    (set by OrganizationContextMiddleware) and stored in session.info for use
    in queries throughout the request lifecycle.

    Args:
        request: FastAPI request object with organization context

    Yields:
        AsyncSession: SQLAlchemy async session with organization context

    Example:
        @router.get("/")
        async def get_items(
            request: Request,
            db: AsyncSession = Depends(get_db_with_org_context)
        ):
            # Organization ID is available in session.info
            org_id = db.info.get("organization_id")
            result = await db.execute(
                select(Item).filter_by(organization_id=org_id)
            )
            return result.scalars().all()
    """
    # Import here to avoid circular imports
    from middleware.organization_context import get_organization_context

    # Get organization context from request
    organization_id = get_organization_context(request)

    async with async_session_maker() as session:
        # Store organization_id in session info for use in queries
        session.info["organization_id"] = organization_id

        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_organization_id(session: AsyncSession) -> Optional[str]:
    """
    Helper function to get organization ID from database session.

    This retrieves the organization_id that was stored in the session
    by get_db_with_org_context(). Returns None if not present.

    Args:
        session: SQLAlchemy async session

    Returns:
        The organization ID for this session, or None if not present

    Example:
        async def my_endpoint(db: AsyncSession = Depends(get_db_with_org_context)):
            org_id = get_organization_id(db)
            if org_id:
                # Filter by organization
                query = select(Model).filter_by(organization_id=org_id)
    """
    return session.info.get("organization_id")


def require_organization_id(session: AsyncSession) -> str:
    """
    Helper function to get organization ID from database session, raising an error if not present.

    This retrieves the organization_id that was stored in the session
    by get_db_with_org_context(). Raises ValueError if not present.

    Args:
        session: SQLAlchemy async session

    Returns:
        The organization ID for this session

    Raises:
        ValueError: If organization ID is not present in the session

    Example:
        async def my_endpoint(db: AsyncSession = Depends(get_db_with_org_context)):
            org_id = require_organization_id(db)
            # org_id is guaranteed to be a string
            query = select(Model).filter_by(organization_id=org_id)
    """
    org_id = session.info.get("organization_id")
    if org_id is None:
        raise ValueError(
            "Organization context is required but not provided. "
            "Use get_db_with_org_context dependency and ensure X-Organization-ID header is set."
        )
    return org_id


def add_org_filter(statement: Select, session: AsyncSession, org_column_name: str = "organization_id") -> Select:
    """
    Add organization filter to a SQLAlchemy select statement.

    This helper automatically adds an organization_id filter to a query
    based on the organization context stored in the session. This makes
    it easy to ensure all queries are properly scoped to the current
    organization without manual filtering.

    Args:
        statement: SQLAlchemy Select statement to filter
        session: SQLAlchemy async session with organization context
        org_column_name: Name of the organization column (default: "organization_id")

    Returns:
        Select statement with organization filter applied

    Raises:
        ValueError: If organization context is not available in the session

    Example:
        @router.get("/")
        async def get_items(db: AsyncSession = Depends(get_db_with_org_context)):
            # Automatically filter by organization_id
            query = add_org_filter(select(Item), db)
            result = await db.execute(query)
            return result.scalars().all()

        # With custom column name
        query = add_org_filter(select(Item), db, org_column_name="org_id")
    """
    org_id = require_organization_id(session)
    return statement.filter_by(**{org_column_name: org_id})


async def execute_with_org_filter(
    statement: Select,
    session: AsyncSession,
    org_column_name: str = "organization_id"
):
    """
    Execute a query with automatic organization filtering.

    This is a convenience function that combines add_org_filter and
    query execution into a single call. It automatically adds the
    organization filter and executes the query.

    Args:
        statement: SQLAlchemy Select statement to execute
        session: SQLAlchemy async session with organization context
        org_column_name: Name of the organization column (default: "organization_id")

    Returns:
        Result of executing the query

    Raises:
        ValueError: If organization context is not available in the session

    Example:
        @router.get("/")
        async def get_items(db: AsyncSession = Depends(get_db_with_org_context)):
            # Execute with automatic organization filtering
            result = await execute_with_org_filter(select(Item), db)
            return result.scalars().all()
    """
    filtered_statement = add_org_filter(statement, session, org_column_name)
    return await session.execute(filtered_statement)


async def init_db() -> None:
    """
    Initialize database connection.

    This function can be called during application startup to verify
    database connectivity and perform any necessary setup.
    """
    try:
        async with engine.begin() as conn:
            # Test connection
            await conn.execute("SELECT 1")
        logger.info("Database connection established successfully")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


async def close_db() -> None:
    """
    Close database connection pool.

    This function should be called during application shutdown.
    """
    try:
        await engine.dispose()
        logger.info("Database connection pool closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")
