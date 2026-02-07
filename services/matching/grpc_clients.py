"""
gRPC клиенты для межсервисного взаимодействия.
gRPC clients for inter-service communication.

Этот модуль предоставляет gRPC клиентов для вызова других микросервисов,
в частности Resume Processing Service для получения данных о резюме.

This module provides gRPC clients for calling other microservices,
specifically Resume Processing Service to get resume data.
"""
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from uuid import UUID

import grpc
from grpc.aio import Channel, AioRpcError

# Добавляем корневую директорию в path для импорта protobuf
# Add root directory to path for protobuf import
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Try to import generated protobuf files
# Пробуем импортировать сгенерированные protobuf файлы
try:
    from protos import resume_pb2, resume_pb2_grpc
except ImportError:
    # Если protobuf файлы ещё не сгенерированы, создаём заглушки для типов
    # If protobuf files are not generated yet, create stub types
    class MockResumeStatus:
        """Mock ResumeStatus enum for development / Заглушка для разработки"""
        PENDING = 0
        PROCESSING = 1
        COMPLETED = 2
        FAILED = 3
        NEW = 4
        REVIEWED = 5
        INTERVIEW = 6
        OFFERED = 7
        HIRED = 8

    class resume_pb2:
        """Mock protobuf module for development / Заглушка для разработки"""

        class Resume:
            pass

        class CreateResumeRequest:
            pass

        class CreateResumeResponse:
            pass

        class GetResumeRequest:
            pass

        class GetResumeResponse:
            pass

        class ListResumesRequest:
            pass

        class ListResumesResponse:
            pass

        class DeleteResumeRequest:
            pass

        class DeleteResumeResponse:
            pass

        class AnalyzeResumeRequest:
            pass

        class AnalyzeResumeResponse:
            pass

        class GetResumeAnalysisRequest:
            pass

        class GetResumeAnalysisResponse:
            pass

        class GetWorkExperienceRequest:
            pass

        class GetWorkExperienceResponse:
            pass

        class GetResumeTextResponse:
            pass

        class ResumeAnalysis:
            pass

        class WorkExperience:
            pass

        class Keyword:
            pass

        class Education:
            pass

        class ContactInfo:
            pass

        class GrammarIssue:
            pass

        ResumeStatus = MockResumeStatus

    class resume_pb2_grpc:
        """Mock grpc module for development / Заглушка для разработки"""
        ResumeServiceStub = object

logger = logging.getLogger(__name__)


class ResumeServiceClientError(Exception):
    """
    Исключение для ошибок gRPC клиента Resume Service.
    Exception for Resume Service gRPC client errors.

    Attributes:
        message: Описание ошибки / Error description
        details: Детали ошибки от gRPC / Details from gRPC error
    """
    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class ResumeServiceClient:
    """
    gRPC клиент для Resume Processing Service.
    gRPC client for Resume Processing Service.

    Этот класс предоставляет асинхронные методы для вызова gRPC методов
    Resume Processing Service: получение резюме, анализ, текст резюме и др.

    This class provides async methods to call Resume Processing Service
    gRPC methods: get resume, analysis, resume text, etc.

    Attributes:
        host: Хост Resume Processing Service / Resume Processing Service host
        port: Порт Resume Processing Service / Resume Processing Service port
        _channel: gRPC канал / gRPC channel
        _stub: gRPC stub для вызова методов / gRPC stub for method calls

    Example:
        >>> client = ResumeServiceClient(host="localhost", port=50051)
        >>> await client.connect()
        >>> resume = await client.get_resume("uuid-here")
        >>> await client.close()
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 50051,
        timeout: float = 5.0,
    ):
        """
        Инициализировать gRPC клиент.
        Initialize gRPC client.

        Args:
            host: Хост Resume Processing Service (default: "localhost")
                  / Resume Processing Service host
            port: Порт Resume Processing Service (default: 50051)
                  / Resume Processing Service port
            timeout: Таймаут для запросов в секундах (default: 5.0)
                     / Request timeout in seconds
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self._channel: Optional[Channel] = None
        self._stub: Optional[resume_pb2_grpc.ResumeServiceStub] = None
        self._connected = False

    async def connect(self) -> None:
        """
        Установить соединение с Resume Processing Service.
        Establish connection to Resume Processing Service.

        Raises:
            ResumeServiceClientError: Если соединение не удалось
                                     / If connection fails

        Example:
            >>> await client.connect()
        """
        if self._connected:
            logger.warning(f"Already connected to {self.host}:{self.port}")
            return

        try:
            target = f"{self.host}:{self.port}"
            self._channel = await grpc.aio.channel(
                target,
                options=[
                    ("grpc.max_receive_message_length", 100 * 1024 * 1024),  # 100MB
                    ("grpc.max_send_message_length", 100 * 1024 * 1024),  # 100MB
                ],
            ).__aenter__()

            self._stub = resume_pb2_grpc.ResumeServiceStub(self._channel)
            self._connected = True

            logger.info(f"Connected to Resume Processing Service at {target}")

        except Exception as e:
            logger.error(f"Failed to connect to Resume Processing Service: {e}")
            raise ResumeServiceClientError(
                f"Failed to connect to Resume Processing Service: {e}"
            )

    async def close(self) -> None:
        """
        Закрыть соединение с Resume Processing Service.
        Close connection to Resume Processing Service.

        Example:
            >>> await client.close()
        """
        if self._channel and self._connected:
            await self._channel.__aexit__(None, None, None)
            self._connected = False
            logger.info(f"Disconnected from Resume Processing Service")

    async def _ensure_connected(self) -> None:
        """
        Убедиться, что клиент подключен.
        Ensure client is connected.

        Raises:
            ResumeServiceClientError: Если клиент не подключён
                                     / If client is not connected
        """
        if not self._connected or not self._stub:
            raise ResumeServiceClientError(
                "Not connected to Resume Processing Service. Call connect() first."
            )

    async def get_resume(self, resume_id: str) -> Optional[Dict[str, Any]]:
        """
        Получить резюме по ID.
        Get resume by ID.

        Args:
            resume_id: UUID резюме / Resume UUID

        Returns:
            Словарь с данными резюме или None, если не найдено
            / Dictionary with resume data or None if not found

        Raises:
            ResumeServiceClientError: Если запрос не удался / If request fails

        Example:
            >>> resume = await client.get_resume("uuid-here")
            >>> if resume:
            ...     print(f"Resume: {resume['filename']}")
        """
        await self._ensure_connected()

        try:
            request = resume_pb2.GetResumeRequest(id=resume_id)
            response: resume_pb2.GetResumeResponse = await self._stub.GetResume(
                request, timeout=self.timeout
            )

            if response.found:
                resume_dict = {
                    "id": response.resume.id,
                    "filename": response.resume.filename,
                    "file_path": response.resume.file_path,
                    "content_type": response.resume.content_type,
                    "status": response.resume.status,
                    "raw_text": response.resume.raw_text if response.resume.raw_text else None,
                    "language": response.resume.language if response.resume.language else None,
                    "error_message": response.resume.error_message if response.resume.error_message else None,
                    "created_at": response.resume.created_at,
                    "updated_at": response.resume.updated_at,
                }
                logger.info(f"Retrieved resume: {resume_id}")
                return resume_dict
            else:
                logger.warning(f"Resume not found: {resume_id}")
                return None

        except AioRpcError as e:
            logger.error(f"gRPC error getting resume {resume_id}: {e.code()} - {e.details()}")
            raise ResumeServiceClientError(
                f"gRPC error getting resume: {e.code()}", details=e.details()
            )
        except Exception as e:
            logger.error(f"Error getting resume {resume_id}: {e}", exc_info=True)
            raise ResumeServiceClientError(f"Error getting resume: {e}")

    async def get_resume_text(
        self, resume_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Получить текст резюме для анализа.
        Get resume text for analysis.

        Этот метод возвращает только текст резюме без полной структуры,
        что полезно для дополнительных сервисов анализа.

        This method returns only resume text without full structure,
        useful for additional analysis services.

        Args:
            resume_id: UUID резюме / Resume UUID

        Returns:
            Словарь с resume_id, raw_text, language или None
            / Dictionary with resume_id, raw_text, language or None

        Raises:
            ResumeServiceClientError: Если запрос не удался / If request fails

        Example:
            >>> text_data = await client.get_resume_text("uuid-here")
            >>> if text_data:
            ...     print(f"Text length: {len(text_data['raw_text'])}")
        """
        await self._ensure_connected()

        try:
            request = resume_pb2.GetResumeRequest(id=resume_id)
            response: resume_pb2.GetResumeTextResponse = await self._stub.GetResumeText(
                request, timeout=self.timeout
            )

            if response.found:
                text_data = {
                    "resume_id": response.resume_id,
                    "raw_text": response.raw_text if response.raw_text else "",
                    "language": response.language if response.language else None,
                }
                logger.info(f"Retrieved resume text: {resume_id}, length={len(text_data['raw_text'])}")
                return text_data
            else:
                logger.warning(f"Resume text not found: {resume_id}")
                return None

        except AioRpcError as e:
            logger.error(f"gRPC error getting resume text {resume_id}: {e.code()} - {e.details()}")
            raise ResumeServiceClientError(
                f"gRPC error getting resume text: {e.code()}", details=e.details()
            )
        except Exception as e:
            logger.error(f"Error getting resume text {resume_id}: {e}", exc_info=True)
            raise ResumeServiceClientError(f"Error getting resume text: {e}")

    async def get_resume_analysis(
        self, resume_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Получить результаты анализа резюме.
        Get resume analysis results.

        Args:
            resume_id: UUID резюме / Resume UUID

        Returns:
            Словарь с результатами анализа или None
            / Dictionary with analysis results or None

        Raises:
            ResumeServiceClientError: Если запрос не удался / If request fails

        Example:
            >>> analysis = await client.get_resume_analysis("uuid-here")
            >>> if analysis:
            ...     print(f"Skills: {analysis['skills']}")
        """
        await self._ensure_connected()

        try:
            request = resume_pb2.GetResumeAnalysisRequest(resume_id=resume_id)
            response: resume_pb2.GetResumeAnalysisResponse = await self._stub.GetResumeAnalysis(
                request, timeout=self.timeout
            )

            if response.found:
                analysis_dict = {
                    "id": response.analysis.id,
                    "resume_id": response.analysis.resume_id,
                    "language": response.analysis.language if response.analysis.language else None,
                    "raw_text": response.analysis.raw_text if response.analysis.raw_text else None,
                    "skills": list(response.analysis.skills),
                    "keywords": [
                        {"text": kw.text, "score": kw.score}
                        for kw in response.analysis.keywords
                    ],
                    "entities": dict(response.analysis.entities),
                    "total_experience_months": response.analysis.total_experience_months,
                    "education": [
                        {
                            "institution": edu.institution,
                            "degree": edu.degree,
                            "field_of_study": edu.field_of_study,
                            "start_date": edu.start_date,
                            "end_date": edu.end_date,
                            "description": edu.description,
                        }
                        for edu in response.analysis.education
                    ],
                    "contact_info": {
                        "email": response.analysis.contact_info.email if response.analysis.contact_info else "",
                        "phone": response.analysis.contact_info.phone if response.analysis.contact_info else "",
                        "links": list(response.analysis.contact_info.links) if response.analysis.contact_info else [],
                        "location": response.analysis.contact_info.location if response.analysis.contact_info else "",
                    } if response.analysis.contact_info else None,
                    "grammar_issues": [
                        {
                            "message": issue.message,
                            "context": issue.context,
                            "offset": issue.offset,
                            "length": issue.length,
                            "suggestions": list(issue.suggestions),
                        }
                        for issue in response.analysis.grammar_issues
                    ],
                    "warnings": list(response.analysis.warnings),
                    "quality_score": response.analysis.quality_score,
                    "processing_time_seconds": response.analysis.processing_time_seconds,
                    "analyzer_version": response.analysis.analyzer_version,
                    "created_at": response.analysis.created_at,
                    "updated_at": response.analysis.updated_at,
                }
                logger.info(f"Retrieved resume analysis: {resume_id}")
                return analysis_dict
            else:
                logger.warning(f"Resume analysis not found: {resume_id}")
                return None

        except AioRpcError as e:
            logger.error(f"gRPC error getting resume analysis {resume_id}: {e.code()} - {e.details()}")
            raise ResumeServiceClientError(
                f"gRPC error getting resume analysis: {e.code()}", details=e.details()
            )
        except Exception as e:
            logger.error(f"Error getting resume analysis {resume_id}: {e}", exc_info=True)
            raise ResumeServiceClientError(f"Error getting resume analysis: {e}")

    async def get_work_experience(
        self, resume_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Получить опыт работы из резюме.
        Get work experience from resume.

        Args:
            resume_id: UUID резюме / Resume UUID

        Returns:
            Список опыта работы или None
            / List of work experience or None

        Raises:
            ResumeServiceClientError: Если запрос не удался / If request fails

        Example:
            >>> experience = await client.get_work_experience("uuid-here")
            >>> if experience:
            ...     for exp in experience:
            ...         print(f"{exp['company']} - {exp['title']}")
        """
        await self._ensure_connected()

        try:
            request = resume_pb2.GetWorkExperienceRequest(resume_id=resume_id)
            response: resume_pb2.GetWorkExperienceResponse = await self._stub.GetWorkExperience(
                request, timeout=self.timeout
            )

            if response.found:
                experience_list = [
                    {
                        "id": exp.id,
                        "resume_id": exp.resume_id,
                        "company": exp.company,
                        "title": exp.title,
                        "start_date": exp.start_date,
                        "end_date": exp.end_date,
                        "description": exp.description,
                        "confidence_score": exp.confidence_score,
                        "created_at": exp.created_at,
                        "updated_at": exp.updated_at,
                    }
                    for exp in response.experiences
                ]
                logger.info(f"Retrieved {len(experience_list)} work experiences for resume: {resume_id}")
                return experience_list
            else:
                logger.warning(f"Work experience not found: {resume_id}")
                return None

        except AioRpcError as e:
            logger.error(f"gRPC error getting work experience {resume_id}: {e.code()} - {e.details()}")
            raise ResumeServiceClientError(
                f"gRPC error getting work experience: {e.code()}", details=e.details()
            )
        except Exception as e:
            logger.error(f"Error getting work experience {resume_id}: {e}", exc_info=True)
            raise ResumeServiceClientError(f"Error getting work experience: {e}")

    async def analyze_resume(
        self, resume_id: str, force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Запустить анализ резюме.
        Trigger resume analysis.

        Args:
            resume_id: UUID резюме / Resume UUID
            force_refresh: Принудительный пересчёт / Force re-analysis

        Returns:
            Словарь с успехом операции и сообщением
            / Dictionary with operation success and message

        Raises:
            ResumeServiceClientError: Если запрос не удался / If request fails

        Example:
            >>> result = await client.analyze_resume("uuid-here", force_refresh=True)
            >>> print(f"Success: {result['success']}")
        """
        await self._ensure_connected()

        try:
            request = resume_pb2.AnalyzeResumeRequest(
                resume_id=resume_id, force_refresh=force_refresh
            )
            response: resume_pb2.AnalyzeResumeResponse = await self._stub.AnalyzeResume(
                request, timeout=self.timeout
            )

            result = {
                "success": response.success,
                "message": response.message,
            }

            if response.success and response.HasField("analysis"):
                result["analysis"] = {
                    "id": response.analysis.id,
                    "resume_id": response.analysis.resume_id,
                }

            logger.info(f"Analysis triggered for resume: {resume_id}, success={result['success']}")
            return result

        except AioRpcError as e:
            logger.error(f"gRPC error analyzing resume {resume_id}: {e.code()} - {e.details()}")
            raise ResumeServiceClientError(
                f"gRPC error analyzing resume: {e.code()}", details=e.details()
            )
        except Exception as e:
            logger.error(f"Error analyzing resume {resume_id}: {e}", exc_info=True)
            raise ResumeServiceClientError(f"Error analyzing resume: {e}")

    async def __aenter__(self):
        """
        Контекстный менеджер для автоматического подключения.
        Context manager for automatic connection.

        Example:
            >>> async with ResumeServiceClient() as client:
            ...     resume = await client.get_resume("uuid-here")
        """
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Контекстный менеджер для автоматического отключения.
        Context manager for automatic disconnection.
        """
        await self.close()


# Глобальный экземпляр клиента для переиспользования
# Global client instance for reuse
_global_client: Optional[ResumeServiceClient] = None


async def get_resume_client(
    host: str = "localhost",
    port: int = 50051,
    timeout: float = 5.0,
) -> ResumeServiceClient:
    """
    Получить или создать глобальный gRPC клиент для Resume Service.
    Get or create global gRPC client for Resume Service.

    Эта функция создаёт единый клиент для всего приложения,
    чтобы переиспользовать gRPC соединения.

    This function creates a single client for the entire application
    to reuse gRPC connections.

    Args:
        host: Хост Resume Processing Service / Resume Processing Service host
        port: Порт Resume Processing Service / Resume Processing Service port
        timeout: Таймаут для запросов / Request timeout

    Returns:
        ResumeServiceClient: Экземпляр клиента / Client instance

    Example:
        >>> client = await get_resume_client()
        >>> resume = await client.get_resume("uuid-here")
    """
    global _global_client

    if _global_client is None:
        _global_client = ResumeServiceClient(host=host, port=port, timeout=timeout)
        await _global_client.connect()

    return _global_client


async def close_resume_client() -> None:
    """
    Закрыть глобальный gRPC клиент.
    Close global gRPC client.

    Следует вызывать при завершении работы приложения.
    Should be called when shutting down the application.

    Example:
        >>> await close_resume_client()
    """
    global _global_client

    if _global_client is not None:
        await _global_client.close()
        _global_client = None
