"""
Модуль распределенной трассировки с интеграцией Jaeger.

Этот модуль предоставляет функциональность распределенной трассировки (distributed tracing)
с использованием OpenTelemetry и Jaeger. Трассировка позволяет отслеживать запросы
через несколько микросервисов, что упрощает отладку и мониторинг производительности.

Возможности:
- Автоматическая трассировка HTTP-запросов
- Интеграция с Jaeger для визуализации трасс
- Поддержка распространения контекста между сервисами
- Создание пользовательских спанов для бизнес-логики
- Экспорт метрик и трасс в Jaeger

Пример использования:
    >>> from shared.tracing import init_tracing, create_span
    >>> # Инициализация трассировки
    >>> init_tracing(service_name="resume_processing")
    >>> # Использование в коде
    >>> with create_span("process_resume") as span:
    ...     # Ваш код здесь
    ...     span.set_attribute("resume.id", resume_id)
"""
import logging
import os
from contextlib import contextmanager
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.trace import Status, StatusCode
from opentelemetry.context import Context

# Получаем логгер
logger = logging.getLogger(__name__)

# Глобальные переменные для трассировки
_tracer_provider: Optional[TracerProvider] = None
_jaeger_exporter: Optional[JaegerExporter] = None


def init_tracing(
    service_name: str,
    jaeger_host: str = "localhost",
    jaeger_port: int = 6831,
    jaeger_endpoint: Optional[str] = None,
    sample_rate: float = 1.0,
    enable_console_export: bool = False,
    service_version: str = "1.0.0",
) -> trace.Tracer:
    """
    Инициализировать распределенную трассировку с Jaeger.

    Эта функция настраивает OpenTelemetry SDK для экспорта трасс в Jaeger.
    Создает провайдер трассировщика, настраивает экспортеры и возвращает трассировщик.

    Аргументы:
        service_name: Имя микросервиса для идентификации в Jaeger (например, "resume_processing")
        jaeger_host: Хост Jaeger Agent (по умолчанию: "localhost")
        jaeger_port: Порт Jaeger Agent UDP (по умолчанию: 6831)
        jaeger_endpoint: HTTP endpoint Jaeger Collector (опционально, для HTTP экспорта)
        sample_rate: Частота выборки трасс от 0.0 до 1.0 (по умолчанию: 1.0 = все трассы)
        enable_console_export: Экспортировать спаны в консоль для отладки (по умолчанию: False)
        service_version: Версия сервиса для метаданных трассировки (по умолчанию: "1.0.0")

    Возвращает:
        Настроенный объект Tracer для создания спанов

    Исключения:
        ValueError: Если sample_rate не в диапазоне [0.0, 1.0]
        ConnectionError: Если не удается подключиться к Jaeger

    Пример:
        >>> from shared.tracing import init_tracing
        >>> tracer = init_tracing(
        ...     service_name="resume_processing",
        ...     jaeger_host="localhost",
        ...     sample_rate=0.5  # Трассировать 50% запросов
        ... )
        >>> # Использование трассировщика
        >>> with tracer.start_as_current_span("process_resume"):
        ...     process_resume_data()
    """
    global _tracer_provider, _jaeger_exporter

    # Проверка sample_rate
    if not 0.0 <= sample_rate <= 1.0:
        raise ValueError(f"sample_rate должен быть в диапазоне [0.0, 1.0], получено: {sample_rate}")

    # Проверка переменных окружения для переопределения
    jaeger_host = os.getenv("JAEGER_HOST", jaeger_host)
    jaeger_port = int(os.getenv("JAEGER_PORT", str(jaeger_port)))
    jaeger_endpoint = os.getenv("JAEGER_ENDPOINT", jaeger_endpoint)
    sample_rate = float(os.getenv("TRACE_SAMPLE_RATE", str(sample_rate)))
    enable_console_export = os.getenv("TRACE_CONSOLE_EXPORT", "false").lower() == "true"

    # Создание ресурса с метаданными сервиса
    resource = Resource.create(
        {
            SERVICE_NAME: service_name,
            SERVICE_VERSION: service_version,
            "service.namespace": "agenthr",
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        }
    )

    # Создание провайдера трассировщика
    _tracer_provider = TracerProvider(resource=resource)

    # Настройка Jaeger Exporter
    try:
        if jaeger_endpoint:
            # HTTP экспорт в Jaeger Collector
            _jaeger_exporter = JaegerExporter(
                agent_host_name=jaeger_host,
                agent_port=jaeger_port,
                endpoint=jaeger_endpoint,
            )
            logger.info(f"Jaeger exporter настроен для HTTP endpoint: {jaeger_endpoint}")
        else:
            # UDP экспорт в Jaeger Agent
            _jaeger_exporter = JaegerExporter(
                agent_host_name=jaeger_host,
                agent_port=jaeger_port,
            )
            logger.info(f"Jaeger exporter настроен для UDP: {jaeger_host}:{jaeger_port}")

        # Добавление экспортера в провайдер
        span_processor = BatchSpanProcessor(_jaeger_exporter)
        _tracer_provider.add_span_processor(span_processor)

        # Опциональный консольный экспорт для отладки
        if enable_console_export:
            console_exporter = ConsoleSpanExporter()
            _tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
            logger.info("Консольный экспорт спанов включен")

    except Exception as e:
        logger.error(f"Ошибка при настройке Jaeger exporter: {e}")
        raise ConnectionError(f"Не удалось подключиться к Jaeger: {e}")

    # Установка глобального провайдера трассировщика
    trace.set_tracer_provider(_tracer_provider)

    # Получение трассировщика
    tracer = trace.get_tracer(__name__)

    logger.info(
        f"Трассировка инициализирована для сервиса '{service_name}' "
        f"(sample_rate={sample_rate}, version={service_version})"
    )

    return tracer


def instrument_fastapi(app):
    """
    Автоматически трассировать все HTTP-запросы FastAPI.

    Эта функция добавляет инструментарий к приложению FastAPI для автоматического
    создания спанов для всех входящих HTTP-запросов.

    Аргументы:
        app: Экземпляр приложения FastAPI

    Пример:
        >>> from fastapi import FastAPI
        >>> from shared.tracing import instrument_fastapi
        >>> app = FastAPI()
        >>> instrument_fastapi(app)
    """
    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumentation добавлена")
    except Exception as e:
        logger.error(f"Ошибка при добавлении FastAPI instrumentation: {e}")
        raise


def instrument_httpx():
    """
    Автоматически трассировать исходящие HTTP-запросы через httpx.

    Эта функция добавляет инструментарий к httpx для автоматического создания
    спанов для всех исходящих HTTP-запросов (например, при вызове других сервисов).

    Пример:
        >>> from shared.tracing import instrument_httpx
        >>> instrument_httpx()
        >>> # Теперь все httpx запросы автоматически трассируются
    """
    try:
        HTTPXClientInstrumentor().instrument()
        logger.info("HTTPX instrumentation добавлена")
    except Exception as e:
        logger.error(f"Ошибка при добавлении HTTPX instrumentation: {e}")
        raise


def instrument_sqlalchemy(engine):
    """
    Автоматически трассировать SQL-запросы через SQLAlchemy.

    Эта функция добавляет инструментарий к SQLAlchemy для автоматического создания
    спанов для всех SQL-запросов к базе данных.

    Аргументы:
        engine: Экземпляр асинхронного движка SQLAlchemy

    Пример:
        >>> from shared.tracing import instrument_sqlalchemy
        >>> from sqlalchemy.ext.asyncio import create_async_engine
        >>> engine = create_async_engine(database_url)
        >>> instrument_sqlalchemy(engine)
    """
    try:
        SQLAlchemyInstrumentor().instrument(engine=engine)
        logger.info("SQLAlchemy instrumentation добавлена")
    except Exception as e:
        logger.error(f"Ошибка при добавлении SQLAlchemy instrumentation: {e}")
        raise


@contextmanager
def create_span(
    name: str,
    attributes: Optional[dict] = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL,
):
    """
    Создать пользовательский спан для трассировки бизнес-логики.

    Этот контекстный менеджер создает новый спан, который автоматически
    закрывается при выходе из контекста. Полезен для трассировки
    конкретных участков кода.

    Аргументы:
        name: Имя спана (описывает выполняемую операцию)
        attributes: Атрибуты спана (ключ-значение метаданные)
        kind: Тип спана (INTERNAL, SERVER, CLIENT, PRODUCER, CONSUMER)

    Возвращает:
        Контекстный менеджер для использования в with

    Пример:
        >>> from shared.tracing import create_span
        >>> with create_span("parse_resume", {"resume_id": "123"}) as span:
        ...     try:
        ...         result = parse_resume(resume_id)
        ...         span.set_status(Status(StatusCode.OK))
        ...     except Exception as e:
        ...         span.set_status(Status(StatusCode.ERROR, str(e)))
        ...         span.record_exception(e)
        ...         raise
    """
    tracer = trace.get_tracer(__name__)
    attribute_dict = attributes or {}

    with tracer.start_as_current_span(name, kind=kind) as span:
        # Установка атрибутов спана
        for key, value in attribute_dict.items():
            span.set_attribute(key, str(value))

        yield span


def set_span_attributes(attributes: dict):
    """
    Установить атрибуты для текущего активного спана.

    Аргументы:
        attributes: Словарь атрибутов (ключ-значение)

    Пример:
        >>> from shared.tracing import set_span_attributes
        >>> set_span_attributes({
        ...     "user.id": "123",
        ...     "resume.format": "pdf"
        ... })
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        for key, value in attributes.items():
            current_span.set_attribute(key, str(value))


def set_span_error(exception: Exception):
    """
    Отметить текущий спан как содержащий ошибку.

    Аргументы:
        exception: Исключение, которое произошло

    Пример:
        >>> from shared.tracing import set_span_error
        >>> try:
        ...     process_resume()
        ... except Exception as e:
        ...     set_span_error(e)
        ...     raise
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.record_exception(exception)
        current_span.set_status(Status(StatusCode.ERROR, str(exception)))


def add_span_event(name: str, attributes: Optional[dict] = None):
    """
    Добавить событие в текущий спан.

    События полезны для отметки конкретных моментов времени
    в течение выполнения спана.

    Аргументы:
        name: Имя события
        attributes: Атрибуты события (опционально)

    Пример:
        >>> from shared.tracing import add_span_event
        >>> add_span_event("resume_downloaded", {"size": "1024"})
        >>> add_span_event("parsing_started")
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        attribute_dict = attributes or {}
        current_span.add_event(name, attribute_dict)


def get_trace_id() -> Optional[str]:
    """
    Получить ID текущей трассировки из контекста.

    Возвращает:
        ID трассировки или None, если нет активной трассы

    Пример:
        >>> from shared.tracing import get_trace_id
        >>> trace_id = get_trace_id()
        >>> print(f"Trace ID: {trace_id}")
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        span_context = current_span.get_span_context()
        if span_context:
            return format(span_context.trace_id, "032x")
    return None


def get_span_id() -> Optional[str]:
    """
    Получить ID текущего спана из контекста.

    Возвращает:
        ID спана или None, если нет активного спана

    Пример:
        >>> from shared.tracing import get_span_id
        >>> span_id = get_span_id()
        >>> print(f"Span ID: {span_id}")
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        span_context = current_span.get_span_context()
        if span_context:
            return format(span_context.span_id, "016x")
    return None


def shutdown_tracing():
    """
    Корректно завершить работу с трассировкой.

    Эта функция должна вызываться при завершении работы сервиса
    для гарантии отправки всех оставшихся спанов в Jaeger.

    Пример:
        >>> import atexit
        >>> from shared.tracing import shutdown_tracing
        >>> atexit.register(shutdown_tracing)
    """
    global _tracer_provider

    if _tracer_provider:
        logger.info("Завершение работы трассировки...")
        _tracer_provider.shutdown()
        logger.info("Трассировка остановлена")
