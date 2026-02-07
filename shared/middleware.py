"""
Модуль middleware для распределенной трассировки HTTP-запросов.

Этот модуль предоставляет middleware для автоматической трассировки всех
HTTP-запросов в микросервисах. Middleware создает спаны для каждого запроса,
добавляет атрибуты и обрабатывает исключения для полных трасс.

Возможности:
- Автоматическое создание спанов для входящих запросов
- Извлечение и распространение traceparent заголовков
- Добавление атрибутов запроса (method, path, user agent)
- Запись исключений и ошибок в спаны
- Интеграция с FastAPI и Starlette

Пример использования:
    >>> from fastapi import FastAPI
    >>> from shared.middleware import TracingMiddleware
    >>> app = FastAPI()
    >>> app.add_middleware(TracingMiddleware, service_name="resume_processing")
"""
import logging
import time
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from opentelemetry import trace
from opentelemetry.propagate import extract
from opentelemetry.trace import Status, StatusCode
from opentelemetry.sdk.trace import TracerProvider

# Получаем логгер
logger = logging.getLogger(__name__)

# Имена заголовков для распределенной трассировки
TRACEPARENT_HEADER = "traceparent"
TRACESTATE_HEADER = "tracestate"


class TracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware для автоматической трассировки HTTP-запросов.

    Это middleware создает спан для каждого входящего HTTP-запроса,
    автоматически извлекает контекст трассировки из заголовков запроса
    и добавляет соответствующие атрибуты к спану.

    Attributes:
        service_name: Имя сервиса для идентификации в трассах
        exclude_paths: Список путей, которые не нужно трассировать
        exclude_health_check: Исключить /health и /ready из трассировки

    Example:
        >>> from fastapi import FastAPI
        >>> from shared.middleware import TracingMiddleware
        >>> app = FastAPI()
        >>> app.add_middleware(
        ...     TracingMiddleware,
        ...     service_name="resume_processing",
        ...     exclude_health_check=True
        ... )
    """

    def __init__(
        self,
        app: ASGIApp,
        service_name: str = "microservice",
        exclude_paths: Optional[list[str]] = None,
        exclude_health_check: bool = True,
    ):
        """
        Инициализировать middleware трассировки.

        Args:
            app: ASGI приложение (обычно FastAPI)
            service_name: Имя сервиса для метаданных трассировки
            exclude_paths: Список путей для исключения из трассировки
            exclude_health_check: Исключить health check endpoints

        Example:
            >>> middleware = TracingMiddleware(
            ...     app,
            ...     service_name="matching_service",
            ...     exclude_paths=["/metrics", "/status"]
            ... )
        """
        super().__init__(app)
        self.service_name = service_name
        self.exclude_paths = set(exclude_paths or [])
        self.exclude_health_check = exclude_health_check

        # Добавляем стандартные health check пути
        if exclude_health_check:
            self.exclude_paths.update(["/health", "/ready", "/live", "/healthz"])

        # Получаем трассировщик
        self.tracer = trace.get_tracer(f"{service_name}.middleware")

        logger.info(
            f"TracingMiddleware инициализирован для сервиса '{service_name}' "
            f"(исключенные пути: {self.exclude_paths})"
        )

    def _should_trace(self, request: Request) -> bool:
        """
        Проверить, нужно ли трассировать этот запрос.

        Args:
            request: Входящий HTTP-запрос

        Returns:
            True, если запрос нужно трассировать, иначе False

        Example:
            >>> middleware = TracingMiddleware(app)
            >>> should_trace = middleware._should_trace(request)
        """
        # Проверяем путь
        if request.url.path in self.exclude_paths:
            return False

        # Проверяем, что путь не начинается с исключенных префиксов
        for excluded in self.exclude_paths:
            if excluded.endswith("*") and request.url.path.startswith(excluded[:-1]):
                return False

        return True

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Обработать запрос и создать спан трассировки.

        Этот метод:
        1. Проверяет, нужно ли трассировать запрос
        2. Извлекает контекст трассировки из заголовков
        3. Создает спан для HTTP-запроса
        4. Добавляет атрибуты запроса к спану
        5. Выполняет запрос
        6. Добавляет атрибуты ответа к спану
        7. Обрабатывает исключения

        Args:
            request: Входящий HTTP-запрос
            call_next: Следующий middleware или обработчик маршрута

        Returns:
            HTTP-ответ с добавленными заголовками трассировки

        Example:
            >>> response = await middleware.dispatch(request, call_next)
        """
        # Проверяем, нужно ли трассировать этот запрос
        if not self._should_trace(request):
            return await call_next(request)

        # Запоминаем время начала запроса
        start_time = time.time()

        # Имя спана на основе метода и пути
        span_name = f"{request.method} {request.url.path}"

        # Извлекаем контекст трассировки из заголовков
        # Это позволяет связывать трассы между сервисами
        carrier = {
            k.lower(): v
            for k, v in request.headers.items()
            if k.lower() in [TRACEPARENT_HEADER, TRACESTATE_HEADER]
        }

        ctx = extract(carrier)

        # Создаем спан для запроса
        with self.tracer.start_as_current_span(
            span_name,
            kind=trace.SpanKind.SERVER,
            context=ctx,
            attributes={
                "http.method": request.method,
                "http.url": str(request.url),
                "http.scheme": request.url.scheme,
                "http.host": request.url.hostname,
                "http.target": request.url.path,
                "http.route": getattr(
                    request.scope.get("route", {}), "path", request.url.path
                ),
                "http.user_agent": request.headers.get("user-agent", "unknown"),
                "http.client_ip": request.client.host if request.client else "unknown",
                "service.name": self.service_name,
                "net.host.name": request.url.hostname,
                "net.host.port": str(request.url.port or (443 if request.url.scheme == "https" else 80)),
            },
        ) as span:
            try:
                # Выполняем запрос
                response = await call_next(request)

                # Вычисляем длительность запроса
                duration_ms = (time.time() - start_time) * 1000

                # Добавляем атрибуты ответа к спану
                span.set_attribute("http.status_code", response.status_code)
                span.set_attribute("http.status_text", getattr(response, "status_text", ""))
                span.set_attribute("http.response.duration_ms", duration_ms)

                # Устанавливаем статус спана на основе кода ответа
                if response.status_code >= 500:
                    span.set_status(Status(StatusCode.ERROR, f"HTTP {response.status_code}"))
                elif response.status_code >= 400:
                    span.set_status(Status(StatusCode.ERROR, f"HTTP {response.status_code}"))
                else:
                    span.set_status(Status(StatusCode.OK))

                # Добавляем traceparent заголовок в ответ для клиента
                current_span = trace.get_current_span()
                if current_span and current_span.is_recording():
                    span_context = current_span.get_span_context()
                    if span_context.is_valid:
                        trace_parent = f"00-{span_context.trace_id:032x}-{span_context.span_id:016x}-0{span_context.trace_flags:01x}"
                        response.headers[TRACEPARENT_HEADER] = trace_parent

                logger.debug(
                    f"Request traced: {request.method} {request.url.path} "
                    f"[status={response.status_code}, duration={duration_ms:.2f}ms]"
                )

                return response

            except Exception as exc:
                # Вычисляем длительность до исключения
                duration_ms = (time.time() - start_time) * 1000

                # Записываем исключение в спан
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                span.set_attribute("error.message", str(exc))
                span.set_attribute("error.type", type(exc).__name__)
                span.set_attribute("http.response.duration_ms", duration_ms)

                # Логируем ошибку с контекстом трассировки
                logger.error(
                    f"Request error: {request.method} {request.url.path} "
                    f"[duration={duration_ms:.2f}ms] - {exc}",
                    exc_info=True,
                )

                # Пробрасываем исключение дальше
                raise


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware для логирования всех HTTP-запросов.

    Дополнительно к трассировке, этот middleware логирует базовую
    информацию о каждом запросе для удобства отладки.

    Attributes:
        service_name: Имя сервиса для логов

    Example:
        >>> from fastapi import FastAPI
        >>> from shared.middleware import RequestLoggingMiddleware
        >>> app = FastAPI()
        >>> app.add_middleware(RequestLoggingMiddleware, service_name="candidate_service")
    """

    def __init__(self, app: ASGIApp, service_name: str = "microservice"):
        """
        Инициализировать middleware логирования.

        Args:
            app: ASGI приложение
            service_name: Имя сервиса для логов

        Example:
            >>> middleware = RequestLoggingMiddleware(app, service_name="analytics")
        """
        super().__init__(app)
        self.service_name = service_name
        logger.info(f"RequestLoggingMiddleware инициализирован для '{service_name}'")

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Логировать запрос и выполнить его.

        Args:
            request: Входящий HTTP-запрос
            call_next: Следующий middleware или обработчик

        Returns:
            HTTP-ответ

        Example:
            >>> response = await middleware.dispatch(request, call_next)
        """
        start_time = time.time()

        # Логируем запрос
        logger.info(
            f"[{self.service_name}] {request.method} {request.url.path} "
            f"[client={request.client.host if request.client else 'unknown'}]"
        )

        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            # Логируем успешный ответ
            logger.info(
                f"[{self.service_name}] {request.method} {request.url.path} "
                f"[status={response.status_code}, duration={duration_ms:.2f}ms]"
            )

            return response

        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000

            # Логируем ошибку
            logger.error(
                f"[{self.service_name}] {request.method} {request.url.path} "
                f"[error={exc}, duration={duration_ms:.2f}ms]",
                exc_info=True,
            )
            raise


def get_trace_id_from_request(request: Request) -> Optional[str]:
    """
    Получить trace ID из запроса.

    Args:
        request: HTTP-запрос

    Returns:
        Trace ID или None

    Example:
        >>> trace_id = get_trace_id_from_request(request)
        >>> print(f"Trace ID: {trace_id}")
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        span_context = current_span.get_span_context()
        if span_context and span_context.is_valid:
            return format(span_context.trace_id, "032x")
    return None


def add_span_attribute(key: str, value: str):
    """
    Добавить атрибут к текущему спану.

    Удобная функция для добавления атрибутов из обработчиков запросов.

    Args:
        key: Ключ атрибута
        value: Значение атрибута

    Example:
        >>> from shared.middleware import add_span_attribute
        >>> @app.get("/api/resumes/{id}")
        >>> async def get_resume(id: str):
        ...     add_span_attribute("resume.id", id)
        ...     return resume
    """
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_attribute(key, value)
