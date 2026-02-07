"""
Общий модуль для микросервисов AgentHR.

Этот модуль предоставляет общую функциональность для всех микросервисов:
- Конфигурация сервисов с использованием переменных окружения
- Распределенная трассировка с Jaeger
- Middleware для автоматической трассировки HTTP-запросов
- Общие утилиты и помощники
"""
from shared.config import ServiceSettings, get_service_settings
from shared.tracing import (
    init_tracing,
    instrument_fastapi,
    instrument_httpx,
    instrument_sqlalchemy,
    create_span,
    set_span_attributes,
    set_span_error,
    add_span_event,
    get_trace_id,
    get_span_id,
    shutdown_tracing,
)
from shared.middleware import (
    TracingMiddleware,
    RequestLoggingMiddleware,
    get_trace_id_from_request,
    add_span_attribute,
)

__all__ = [
    # Config classes
    "ServiceSettings",
    "get_service_settings",
    # Tracing functions
    "init_tracing",
    "instrument_fastapi",
    "instrument_httpx",
    "instrument_sqlalchemy",
    "create_span",
    "set_span_attributes",
    "set_span_error",
    "add_span_event",
    "get_trace_id",
    "get_span_id",
    "shutdown_tracing",
    # Middleware classes
    "TracingMiddleware",
    "RequestLoggingMiddleware",
    # Middleware functions
    "get_trace_id_from_request",
    "add_span_attribute",
]
