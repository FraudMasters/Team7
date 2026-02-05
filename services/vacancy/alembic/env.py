"""
Конфигурация окружения Alembic для миграций базы данных.

Этот файл выполняется Alembic при запуске команд миграции.
Он настраивает подключение к базе данных и предоставляет контекст для миграций.
"""
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add the parent directory to the path to import models
# Добавляем родительскую директорию в путь для импорта моделей
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import models and base for autogenerate support
# Импортируем модели и базу для поддержки autogenerate
from models import Base  # noqa: E402
from models.vacancy import Vacancy  # noqa: E402

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set database URL from environment variable if available
# Устанавливаем URL базы данных из переменной окружения, если доступна
database_url = os.environ.get("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Add your model's MetaData object here for 'autogenerate' support
# Добавьте здесь объект MetaData вашей модели для поддержки 'autogenerate'
target_metadata = Base.metadata

# Other values from the config, defined by the needs of env.py
# can be acquired my = context.config.x.get_extension()
# for the multi-database or other needs


def run_migrations_offline() -> None:
    """
    Запустить миграции в режиме 'offline'.

    Это настраивает контекст только с URL, а не с Engine,
    хотя Engine здесь также приемлем. Пропуская создание Engine,
    нам даже не нужно, чтобы DBAPI был доступен.

    Вызовы context.execute() здесь emit данную строку в вывод скрипта.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Запустить миграции в режиме 'online'.

    В этом сценарии нам нужно создать Engine и связать подключение
    с контекстом.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
