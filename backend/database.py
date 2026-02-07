"""
Database connection and session management for async SQLAlchemy.

This module provides the database engine, session factory, and dependency
injection for FastAPI endpoints. It also includes SQLAlchemy event listeners
for automatic query performance monitoring.
"""
import logging
import re
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy import event

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
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle,
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

# Dictionary to store connection checkout start times
_checkout_start_times: dict = {}


@event.listens_for(engine.sync_engine, "checkout")
def _receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """
    Event listener for connection checkout from pool.

    Records the start time when a connection is checked out from the pool
    to track checkout duration. Also updates pool metrics.

    Args:
        dbapi_conn: DBAPI connection
        connection_record: Connection record
        connection_proxy: Connection proxy
    """
    import time
    _checkout_start_times[connection_record] = time.time()


    # Update pool metrics
    _update_pool_metrics()


@event.listens_for(engine.sync_engine, "checkin")
def _receive_checkin(dbapi_conn, connection_record):
    """
    Event listener for connection checkin to pool.

    Records checkout duration metrics when a connection is returned to the pool.
    Also updates pool metrics.

    Args:
        dbapi_conn: DBAPI connection
        connection_record: Connection record
    """
    import time

    try:
        # Get checkout start time and record duration
        start_time = _checkout_start_times.pop(connection_record, None)
        if start_time is not None:
            duration = time.time() - start_time
            metrics_registry = get_metrics_registry()
            metrics_registry.record_db_pool_checkout(duration, status="success")

        # Update pool metrics
        _update_pool_metrics()

    except Exception as e:
        logger.error(f"Error recording connection checkin metrics: {e}", exc_info=True)


def _update_pool_metrics() -> None:
    """
    Update connection pool metrics.

    Reads current pool status and updates Prometheus metrics.
    This should be called on checkout/checkin events and periodically.
    """
    try:
        pool = engine.pool
        if pool is None:
            return

        metrics_registry = get_metrics_registry()

        # Get pool status
        size = pool.size()
        overflow = pool.overflow() + getattr(pool, '_max_overflow', 0)
        checked_out = size - pool.checkedin()
        available = pool.checkedin()

        metrics_registry.update_db_pool_metrics(
            size=size,
            overflow=overflow,
            checked_out=checked_out,
            available=available,
        )

    except Exception as e:
        logger.debug(f"Error updating pool metrics: {e}")


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

        # Initialize pool metrics
        _update_pool_metrics()

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
