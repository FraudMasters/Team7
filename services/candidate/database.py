"""
Database connection and session management for Candidate Service.

Управление подключением и сессиями базы данных для сервиса управления кандидатами.
Этот модуль предоставляет движок базы данных, фабрику сессий и внедрение зависимостей
для эндпоинтов FastAPI. Включает прослушиватели событий SQLAlchemy для мониторинга
производительности запросов.

Русские комментарии: Все функции и методы имеют описания на русском языке.
"""
import logging
import re
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy import event

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Create async engine with asyncpg driver / Создание асинхронного движка с драйвером asyncpg
engine = create_async_engine(
    settings.get_db_url_async(),
    echo=settings.log_level == "DEBUG",
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create async session factory / Создание фабрики асинхронных сессий
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models / Базовый класс для моделей
Base = declarative_base()


# Query performance monitoring / Мониторинг производительности запросов
def _extract_table_and_operation(query: str) -> tuple[str, str]:
    """
    Extract the SQL operation type and table name from a query.

    Извлечь тип SQL операции и имя таблицы из запроса.

    Args:
        query: SQL query string / Строка SQL запроса

    Returns:
        Tuple of (operation, table_name)
        - operation: SELECT, INSERT, UPDATE, DELETE, or OTHER
        - table_name: Extracted table name or 'unknown'
        Кортеж из (операция, имя_таблицы)
        - operation: SELECT, INSERT, UPDATE, DELETE или OTHER
        - table_name: Извлеченное имя таблицы или 'unknown'

    Example:
        >>> _extract_table_and_operation("SELECT * FROM candidate_notes WHERE id = 1")
        ('SELECT', 'candidate_notes')
    """
    try:
        # Remove leading/trailing whitespace and convert to uppercase for parsing
        # Удалить пробелы в начале/конце и преобразовать в верхний регистр для парсинга
        query_clean = query.strip().upper()

        # Match basic SQL operations / Найти базовые SQL операции
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
        # Резервный вариант: попытаться извлечь первое слово как операцию
        first_word = query_clean.split()[0] if query_clean.split() else "OTHER"
        return first_word, "unknown"

    except Exception as e:
        logger.debug(f"Failed to parse query: {e}")
        return "OTHER", "unknown"


# Dictionary to store query start times for each connection
# Словарь для хранения времени начала запроса для каждого подключения
_query_start_times: dict = {}


@event.listens_for(engine.sync_engine, "before_cursor_execute")
def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """
    Event listener for before cursor execution.

    Прослушиватель событий перед выполнением курсора.

    Records the start time for each query to enable performance tracking.
    This is triggered before any database query is executed.

    Регистрирует время начала каждого запроса для отслеживания производительности.
    Вызывается перед выполнением любого запроса к базе данных.

    Args:
        conn: Database connection / Подключение к базе данных
        cursor: Database cursor / Курсор базы данных
        statement: SQL statement being executed / Выполняемая SQL инструкция
        parameters: Query parameters / Параметры запроса
        context: Execution context / Контекст выполнения
        executemany: Whether executemany is being used / Используется ли executemany
    """
    import time
    _query_start_times[conn] = time.time()


@event.listens_for(engine.sync_engine, "after_cursor_execute")
def _after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """
    Event listener for after cursor execution.

    Прослушиватель событий после выполнения курсора.

    Calculates query execution time and logs performance metrics.
    This is triggered after each database query completes.

    Вычисляет время выполнения запроса и логирует метрики производительности.
    Вызывается после завершения каждого запроса к базе данных.

    Args:
        conn: Database connection / Подключение к базе данных
        cursor: Database cursor / Курсор базы данных
        statement: SQL statement that was executed / Выполненная SQL инструкция
        parameters: Query parameters / Параметры запроса
        context: Execution context / Контекст выполнения
        executemany: Whether executemany was used / Использовался ли executemany
    """
    import time

    try:
        # Get start time and calculate duration
        # Получить время начала и вычислить длительность
        start_time = _query_start_times.pop(conn, None)
        if start_time is None:
            return

        duration = time.time() - start_time

        # Extract operation and table from the query
        # Извлечь операцию и таблицу из запроса
        operation, table = _extract_table_and_operation(statement)

        logger.debug(
            f"DB query: {operation} on {table} took {duration:.3f}s"
        )

    except Exception as e:
        logger.error(f"Error recording query metrics: {e}", exc_info=True)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection for database sessions.

    Внедрение зависимостей для сессий базы данных.

    This function is used as a FastAPI dependency to provide database
    sessions to endpoints. It automatically handles session cleanup.

    Эта функция используется как зависимость FastAPI для предоставления
    сессий базы данных эндпоинтам. Автоматически управляет очисткой сессий.

    Yields:
        AsyncSession: SQLAlchemy async session / Асинхронная сессия SQLAlchemy

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

    Инициализация подключения к базе данных.

    This function can be called during application startup to verify
    database connectivity and perform any necessary setup.

    Эта функция может вызываться при запуске приложения для проверки
    подключения к базе данных и выполнения необходимой настройки.

    Raises:
        Exception: If database connection fails / Если подключение к БД не удалось
    """
    try:
        async with engine.begin() as conn:
            # Test connection / Проверить подключение
            await conn.execute("SELECT 1")
        logger.info("Candidate Service database connection established successfully")
        logger.info(f"Using database schema: {settings.candidate_db_schema}")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


async def close_db() -> None:
    """
    Close database connection pool.

    Закрытие пула подключений к базе данных.

    This function should be called during application shutdown.

    Эта функция должна вызываться при завершении работы приложения.

    Raises:
        Exception: If closing database connection fails / Если закрытие БД не удалось
    """
    try:
        await engine.dispose()
        logger.info("Candidate Service database connection pool closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")
