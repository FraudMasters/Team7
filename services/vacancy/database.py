"""
Управление подключением к базе данных для Vacancy Service.

Этот модуль предоставляет движок базы данных, фабрику сессий и внедрение зависимостей
для endpoints FastAPI. Также включает слушатели событий SQLAlchemy для автоматического
мониторинга производительности запросов.
"""
import logging
import re
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy import event

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Create async engine with asyncpg driver / Создаем асинхронный движок с драйвером asyncpg
engine = create_async_engine(
    settings.get_db_url_async(),
    echo=settings.log_level == "DEBUG",
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create async session factory / Создаем фабрику асинхронных сессий
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
    Извлечь тип операции SQL и имя таблицы из запроса.

    Args:
        query: Строка SQL запроса

    Returns:
        Кортеж (operation, table_name)
        - operation: SELECT, INSERT, UPDATE, DELETE или OTHER
        - table_name: Извлеченное имя таблицы или 'unknown'

    Example:
        >>> _extract_table_and_operation("SELECT * FROM vacancies WHERE id = 1")
        ('SELECT', 'vacancies')
    """
    try:
        # Remove leading/trailing whitespace and convert to uppercase for parsing
        # Удаляем начальные/конечные пробелы и преобразуем в верхний регистр для парсинга
        query_clean = query.strip().upper()

        # Match basic SQL operations / Сопоставляем базовые операции SQL
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
        # Резервный вариант: пытаемся извлечь первое слово как операцию
        first_word = query_clean.split()[0] if query_clean.split() else "OTHER"
        return first_word, "unknown"

    except Exception as e:
        logger.debug(f"Failed to parse query: {e}")
        return "OTHER", "unknown"


# Dictionary to store query start times for each connection
# Словарь для хранения времени начала запросов для каждого подключения
_query_start_times: dict = {}


@event.listens_for(engine.sync_engine, "before_cursor_execute")
def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """
    Слушатель событий перед выполнением курсора.

    Записывает время начала для каждого запроса для отслеживания производительности.
    Вызывается перед выполнением любого запроса к базе данных.

    Args:
        conn: Подключение к базе данных
        cursor: Курсор базы данных
        statement: Выполняемый SQL оператор
        parameters: Параметры запроса
        context: Контекст выполнения
        executemany: Используется ли executemany
    """
    import time
    _query_start_times[conn] = time.time()


@event.listens_for(engine.sync_engine, "after_cursor_execute")
def _after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """
    Слушатель событий после выполнения курсора.

    Вычисляет время выполнения запроса и логирует метрики производительности.
    Вызывается после завершения каждого запроса к базе данных.

    Args:
        conn: Подключение к базе данных
        cursor: Курсор базы данных
        statement: Выполненный SQL оператор
        parameters: Параметры запроса
        context: Контекст выполнения
        executemany: Использовался ли executemany
    """
    import time

    try:
        # Get start time and calculate duration / Получаем время начала и вычисляем длительность
        start_time = _query_start_times.pop(conn, None)
        if start_time is None:
            return

        duration = time.time() - start_time

        # Extract operation and table from the query / Извлекаем операцию и таблицу из запроса
        operation, table = _extract_table_and_operation(statement)

        logger.debug(
            f"DB query: {operation} on {table} took {duration:.3f}s"
        )

    except Exception as e:
        logger.error(f"Error recording query metrics: {e}", exc_info=True)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Внедрение зависимостей для сессий базы данных.

    Эта функция используется как зависимость FastAPI для предоставления сессий
    базы данных endpoints. Автоматически обрабатывает очистку сессий.

    Yields:
        AsyncSession: Асинхронная сессия SQLAlchemy

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
    Инициализация подключения к базе данных.

    Эта функция может быть вызвана при запуске приложения для проверки
    подключения к базе данных и выполнения необходимой настройки.
    """
    try:
        async with engine.begin() as conn:
            # Test connection / Тестируем подключение
            await conn.execute("SELECT 1")
        logger.info("Database connection established successfully")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


async def close_db() -> None:
    """
    Закрытие пула подключений к базе данных.

    Эта функция должна быть вызвана при остановке приложения.
    """
    try:
        await engine.dispose()
        logger.info("Database connection pool closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")
