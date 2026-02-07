"""
gRPC клиенты для межсервисного взаимодействия Analytics Service.
gRPC clients for Analytics Service inter-service communication.

Этот модуль предоставляет gRPC клиентов для вызова других микросервисов:
- Resume Processing Service для получения данных о резюме
- Matching Service для получения результатов сопоставления

This module provides gRPC clients for calling other microservices:
- Resume Processing Service to get resume data
- Matching Service to get match results
"""
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

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
    from protos import matching_pb2, matching_pb2_grpc
except ImportError:
    # Если protobuf файлы ещё не сгенерированы, создаём заглушки для типов
    # If protobuf files are not generated yet, create stub types

    # Mock resume.proto types
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
        class ResumeAnalysis:
            pass
        class Keyword:
            pass
        class Education:
            pass
        class ContactInfo:
            pass
        class GrammarIssue:
            pass
        class WorkExperience:
            pass
        class GetResumeRequest:
            pass
        class GetResumeResponse:
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
        class ListResumesRequest:
            pass
        class ListResumesResponse:
            pass
        ResumeStatus = MockResumeStatus

    class resume_pb2_grpc:
        """Mock grpc module for development / Заглушка для разработки"""
        ResumeServiceStub = object

    # Mock matching.proto types
    class matching_pb2:
        """Mock protobuf module for development / Заглушка для разработки"""
        class MatchResult:
            pass
        class SkillMatch:
            pass
        class KeywordMatch:
            pass
        class MatchRequest:
            pass
        class MatchResponse:
            pass
        class BatchMatchRequest:
            pass
        class BatchMatchResponse:
            pass
        class GetMatchResultsRequest:
            pass
        class GetMatchResultsResponse:
            pass
        class SkillGapReport:
            pass
        class AnalyzeSkillGapRequest:
            pass
        class AnalyzeSkillGapResponse:
            pass
        class GetSkillGapReportRequest:
            pass
        class GetSkillGapReportResponse:
            pass
        class ResumeComparison:
            pass
        class ComparisonResumeData:
            pass
        class CreateComparisonRequest:
            pass
        class CreateComparisonResponse:
            pass
        class GetComparisonRequest:
            pass
        class GetComparisonResponse:
            pass
        class ListComparisonsRequest:
            pass
        class ListComparisonsResponse:
            pass
        class DeleteComparisonRequest:
            pass
        class DeleteComparisonResponse:
            pass

    class matching_pb2_grpc:
        """Mock grpc module for development / Заглушка для разработки"""
        MatchingServiceStub = object

logger = logging.getLogger(__name__)


# =============================================================================
# Исключения для ошибок gRPC клиентов / gRPC client exceptions
# =============================================================================

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


class MatchingServiceClientError(Exception):
    """
    Исключение для ошибок gRPC клиента Matching Service.
    Exception for Matching Service gRPC client errors.

    Attributes:
        message: Описание ошибки / Error description
        details: Детали ошибки от gRPC / Details from gRPC error
    """
    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


# =============================================================================
# gRPC клиент для Resume Processing Service / Resume Processing Service gRPC client
# =============================================================================

class ResumeServiceClient:
    """
    gRPC клиент для Resume Processing Service.
    gRPC client for Resume Processing Service.

    Этот класс предоставляет асинхронные методы для вызова gRPC методов
    Resume Processing Service: получение резюме, анализ, текст резюме и др.

    This class provides async methods to call Resume Processing Service
    gRPC methods: get resume, analysis, resume text, etc.

    Используется Analytics Service для получения данных о резюме для аналитики.

    Used by Analytics Service to get resume data for analytics.

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

    async def list_resumes(
        self,
        page: int = 1,
        page_size: int = 50,
        status: Optional[int] = None,
        language: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Получить список резюме с пагинацией.
        Get list of resumes with pagination.

        Args:
            page: Номер страницы / Page number
            page_size: Размер страницы / Page size
            status: Фильтр по статусу (ResumeStatus enum) / Status filter
            language: Фильтр по языку / Language filter

        Returns:
            Словарь со списком резюме и метаданными пагинации
            / Dictionary with resume list and pagination metadata

        Raises:
            ResumeServiceClientError: Если запрос не удался / If request fails

        Example:
            >>> result = await client.list_resumes(page=1, page_size=10)
            >>> print(f"Total: {result['total']}")
        """
        await self._ensure_connected()

        try:
            request = resume_pb2.ListResumesRequest(
                page=page,
                page_size=page_size,
                status=status,
                language=language,
            )
            response: resume_pb2.ListResumesResponse = await self._stub.ListResumes(
                request, timeout=self.timeout
            )

            resumes_list = [
                {
                    "id": r.id,
                    "filename": r.filename,
                    "file_path": r.file_path,
                    "content_type": r.content_type,
                    "status": r.status,
                    "language": r.language if r.language else None,
                    "created_at": r.created_at,
                    "updated_at": r.updated_at,
                }
                for r in response.resumes
            ]

            result = {
                "resumes": resumes_list,
                "total": response.total,
                "page": response.page,
                "page_size": response.page_size,
            }

            logger.info(f"Retrieved {len(resumes_list)} resumes (page {page}, total={response.total})")
            return result

        except AioRpcError as e:
            logger.error(f"gRPC error listing resumes: {e.code()} - {e.details()}")
            raise ResumeServiceClientError(
                f"gRPC error listing resumes: {e.code()}", details=e.details()
            )
        except Exception as e:
            logger.error(f"Error listing resumes: {e}", exc_info=True)
            raise ResumeServiceClientError(f"Error listing resumes: {e}")

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


# =============================================================================
# gRPC клиент для Matching Service / Matching Service gRPC client
# =============================================================================

class MatchingServiceClient:
    """
    gRPC клиент для Matching Service.
    gRPC client for Matching Service.

    Этот класс предоставляет асинхронные методы для вызова gRPC методов
    Matching Service: сопоставление резюме, получение результатов, анализ пробелов.

    This class provides async methods to call Matching Service
    gRPC methods: match resumes, get results, skill gap analysis.

    Используется Analytics Service для получения данных о сопоставлении для аналитики.

    Used by Analytics Service to get matching data for analytics.

    Attributes:
        host: Хост Matching Service / Matching Service host
        port: Порт Matching Service / Matching Service port
        _channel: gRPC канал / gRPC channel
        _stub: gRPC stub для вызова методов / gRPC stub for method calls

    Example:
        >>> client = MatchingServiceClient(host="localhost", port=50052)
        >>> await client.connect()
        >>> result = await client.get_match_results(vacancy_id="uuid-here")
        >>> await client.close()
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 50052,
        timeout: float = 5.0,
    ):
        """
        Инициализировать gRPC клиент.
        Initialize gRPC client.

        Args:
            host: Хост Matching Service (default: "localhost")
                  / Matching Service host
            port: Порт Matching Service (default: 50052)
                  / Matching Service port
            timeout: Таймаут для запросов в секундах (default: 5.0)
                     / Request timeout in seconds
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self._channel: Optional[Channel] = None
        self._stub: Optional[matching_pb2_grpc.MatchingServiceStub] = None
        self._connected = False

    async def connect(self) -> None:
        """
        Установить соединение с Matching Service.
        Establish connection to Matching Service.

        Raises:
            MatchingServiceClientError: Если соединение не удалось
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

            self._stub = matching_pb2_grpc.MatchingServiceStub(self._channel)
            self._connected = True

            logger.info(f"Connected to Matching Service at {target}")

        except Exception as e:
            logger.error(f"Failed to connect to Matching Service: {e}")
            raise MatchingServiceClientError(
                f"Failed to connect to Matching Service: {e}"
            )

    async def close(self) -> None:
        """
        Закрыть соединение с Matching Service.
        Close connection to Matching Service.

        Example:
            >>> await client.close()
        """
        if self._channel and self._connected:
            await self._channel.__aexit__(None, None, None)
            self._connected = False
            logger.info(f"Disconnected from Matching Service")

    async def _ensure_connected(self) -> None:
        """
        Убедиться, что клиент подключен.
        Ensure client is connected.

        Raises:
            MatchingServiceClientError: Если клиент не подключён
                                       / If client is not connected
        """
        if not self._connected or not self._stub:
            raise MatchingServiceClientError(
                "Not connected to Matching Service. Call connect() first."
            )

    async def get_match_results(
        self,
        resume_id: Optional[str] = None,
        vacancy_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
        min_score: float = 0.0,
    ) -> Optional[Dict[str, Any]]:
        """
        Получить результаты сопоставления с фильтрами и пагинацией.
        Get match results with filters and pagination.

        Args:
            resume_id: Фильтр по ID резюме / Filter by resume ID
            vacancy_id: Фильтр по ID вакансии / Filter by vacancy ID
            page: Номер страницы / Page number
            page_size: Размер страницы / Page size
            min_score: Минимальная оценка сопоставления / Minimum match score

        Returns:
            Словарь со списком результатов и метаданными пагинации
            / Dictionary with results list and pagination metadata

        Raises:
            MatchingServiceClientError: Если запрос не удался / If request fails

        Example:
            >>> results = await client.get_match_results(vacancy_id="uuid-here", min_score=0.5)
            >>> print(f"Found {results['total']} matches")
        """
        await self._ensure_connected()

        try:
            request = matching_pb2.GetMatchResultsRequest(
                resume_id=resume_id or "",
                vacancy_id=vacancy_id or "",
                page=page,
                page_size=page_size,
                min_score=min_score,
            )
            response: matching_pb2.GetMatchResultsResponse = await self._stub.GetMatchResults(
                request, timeout=self.timeout
            )

            results_list = []
            for result in response.results:
                result_dict = {
                    "id": result.id,
                    "resume_id": result.resume_id,
                    "vacancy_id": result.vacancy_id,
                    "overall_score": result.overall_score,
                    "match_percentage": result.match_percentage,
                    "keyword_score": result.keyword_score,
                    "tfidf_score": result.tfidf_score,
                    "vector_score": result.vector_score,
                    "vector_similarity": result.vector_similarity,
                    "recommendation": result.recommendation,
                    "keyword_passed": result.keyword_passed,
                    "tfidf_passed": result.tfidf_passed,
                    "vector_passed": result.vector_passed,
                    "matched_skills": [
                        {"skill": sm.skill, "confidence": sm.confidence, "context": sm.context}
                        for sm in result.matched_skills
                    ],
                    "missing_skills": list(result.missing_skills),
                    "experience_verified": result.experience_verified,
                    "matcher_version": result.matcher_version,
                    "created_at": result.created_at,
                    "updated_at": result.updated_at,
                }
                results_list.append(result_dict)

            response_dict = {
                "results": results_list,
                "total": response.total,
                "page": response.page,
                "page_size": response.page_size,
            }

            logger.info(f"Retrieved {len(results_list)} match results (page {page}, total={response.total})")
            return response_dict

        except AioRpcError as e:
            logger.error(f"gRPC error getting match results: {e.code()} - {e.details()}")
            raise MatchingServiceClientError(
                f"gRPC error getting match results: {e.code()}", details=e.details()
            )
        except Exception as e:
            logger.error(f"Error getting match results: {e}", exc_info=True)
            raise MatchingServiceClientError(f"Error getting match results: {e}")

    async def match_resume(
        self,
        resume_id: str,
        vacancy_id: str,
        force_refresh: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Сопоставить резюме с вакансией.
        Match resume with vacancy.

        Args:
            resume_id: ID резюме / Resume ID
            vacancy_id: ID вакансии / Vacancy ID
            force_refresh: Принудительный пересчёт / Force re-calculation

        Returns:
            Словарь с результатом сопоставления или None
            / Dictionary with match result or None

        Raises:
            MatchingServiceClientError: Если запрос не удался / If request fails

        Example:
            >>> result = await client.match_resume("resume-uuid", "vacancy-uuid")
            >>> if result:
            ...     print(f"Score: {result['overall_score']}")
        """
        await self._ensure_connected()

        try:
            request = matching_pb2.MatchRequest(
                resume_id=resume_id,
                vacancy_id=vacancy_id,
                force_refresh=force_refresh,
            )
            response: matching_pb2.MatchResponse = await self._stub.MatchResume(
                request, timeout=self.timeout
            )

            if response.success and response.HasField("result"):
                result = response.result
                result_dict = {
                    "id": result.id,
                    "resume_id": result.resume_id,
                    "vacancy_id": result.vacancy_id,
                    "overall_score": result.overall_score,
                    "match_percentage": result.match_percentage,
                    "keyword_score": result.keyword_score,
                    "tfidf_score": result.tfidf_score,
                    "vector_score": result.vector_score,
                    "recommendation": result.recommendation,
                    "matched_skills": [
                        {"skill": sm.skill, "confidence": sm.confidence}
                        for sm in result.matched_skills
                    ],
                    "missing_skills": list(result.missing_skills),
                    "experience_verified": result.experience_verified,
                    "created_at": result.created_at,
                    "updated_at": result.updated_at,
                }
                logger.info(f"Matched resume {resume_id} with vacancy {vacancy_id}")
                return result_dict
            else:
                logger.warning(f"Match failed for resume {resume_id} and vacancy {vacancy_id}: {response.message}")
                return None

        except AioRpcError as e:
            logger.error(f"gRPC error matching resume: {e.code()} - {e.details()}")
            raise MatchingServiceClientError(
                f"gRPC error matching resume: {e.code()}", details=e.details()
            )
        except Exception as e:
            logger.error(f"Error matching resume: {e}", exc_info=True)
            raise MatchingServiceClientError(f"Error matching resume: {e}")

    async def batch_match(
        self,
        vacancy_id: str,
        resume_ids: List[str],
        force_refresh: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Массовое сопоставление резюме с вакансией.
        Batch match resumes with vacancy.

        Args:
            vacancy_id: ID вакансии / Vacancy ID
            resume_ids: Список ID резюме / List of resume IDs
            force_refresh: Принудительный пересчёт / Force re-calculation

        Returns:
            Словарь с результатами массового сопоставления
            / Dictionary with batch match results

        Raises:
            MatchingServiceClientError: Если запрос не удался / If request fails

        Example:
            >>> result = await client.batch_match("vacancy-uuid", ["resume1", "resume2"])
            >>> print(f"Successful: {result['successful_count']}")
        """
        await self._ensure_connected()

        try:
            request = matching_pb2.BatchMatchRequest(
                vacancy_id=vacancy_id,
                resume_ids=resume_ids,
                force_refresh=force_refresh,
            )
            response: matching_pb2.BatchMatchResponse = await self._stub.BatchMatch(
                request, timeout=self.timeout
            )

            results_list = []
            for result in response.results:
                result_dict = {
                    "id": result.id,
                    "resume_id": result.resume_id,
                    "vacancy_id": result.vacancy_id,
                    "overall_score": result.overall_score,
                    "match_percentage": result.match_percentage,
                    "recommendation": result.recommendation,
                }
                results_list.append(result_dict)

            response_dict = {
                "results": results_list,
                "total_count": response.total_count,
                "successful_count": response.successful_count,
                "failed_resume_ids": list(response.failed_resume_ids),
                "message": response.message,
            }

            logger.info(f"Batch matched {response.successful_count}/{response.total_count} resumes")
            return response_dict

        except AioRpcError as e:
            logger.error(f"gRPC error batch matching: {e.code()} - {e.details()}")
            raise MatchingServiceClientError(
                f"gRPC error batch matching: {e.code()}", details=e.details()
            )
        except Exception as e:
            logger.error(f"Error batch matching: {e}", exc_info=True)
            raise MatchingServiceClientError(f"Error batch matching: {e}")

    async def get_skill_gap_report(
        self,
        resume_id: str,
        vacancy_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Получить отчёт о пробелах в навыках.
        Get skill gap report.

        Args:
            resume_id: ID резюме / Resume ID
            vacancy_id: ID вакансии / Vacancy ID

        Returns:
            Словарь с отчётом о пробелах в навыках или None
            / Dictionary with skill gap report or None

        Raises:
            MatchingServiceClientError: Если запрос не удался / If request fails

        Example:
            >>> report = await client.get_skill_gap_report("resume-uuid", "vacancy-uuid")
            >>> if report:
            ...     print(f"Gap severity: {report['gap_severity']}")
        """
        await self._ensure_connected()

        try:
            request = matching_pb2.GetSkillGapReportRequest(
                resume_id=resume_id,
                vacancy_id=vacancy_id,
            )
            response: matching_pb2.GetSkillGapReportResponse = await self._stub.GetSkillGapReport(
                request, timeout=self.timeout
            )

            if response.found:
                report = response.report
                report_dict = {
                    "id": report.id,
                    "resume_id": report.resume_id,
                    "vacancy_id": report.vacancy_id,
                    "candidate_skills": list(report.candidate_skills),
                    "required_skills": list(report.required_skills),
                    "missing_skills": list(report.missing_skills),
                    "matched_skills": list(report.matched_skills),
                    "partial_match_skills": list(report.partial_match_skills),
                    "gap_severity": report.gap_severity,
                    "gap_percentage": report.gap_percentage,
                    "bridgeability_score": report.bridgeability_score,
                    "estimated_time_to_bridge": report.estimated_time_to_bridge,
                    "priority_ordering": list(report.priority_ordering),
                    "created_at": report.created_at,
                    "updated_at": report.updated_at,
                }
                logger.info(f"Retrieved skill gap report for resume {resume_id}")
                return report_dict
            else:
                logger.warning(f"Skill gap report not found for resume {resume_id}")
                return None

        except AioRpcError as e:
            logger.error(f"gRPC error getting skill gap report: {e.code()} - {e.details()}")
            raise MatchingServiceClientError(
                f"gRPC error getting skill gap report: {e.code()}", details=e.details()
            )
        except Exception as e:
            logger.error(f"Error getting skill gap report: {e}", exc_info=True)
            raise MatchingServiceClientError(f"Error getting skill gap report: {e}")

    async def __aenter__(self):
        """
        Контекстный менеджер для автоматического подключения.
        Context manager for automatic connection.

        Example:
            >>> async with MatchingServiceClient() as client:
            ...     results = await client.get_match_results(vacancy_id="uuid-here")
        """
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Контекстный менеджер для автоматического отключения.
        Context manager for automatic disconnection.
        """
        await self.close()


# =============================================================================
# Глобальные экземпляры клиентов для переиспользования / Global client instances for reuse
# =============================================================================

_global_resume_client: Optional[ResumeServiceClient] = None
_global_matching_client: Optional[MatchingServiceClient] = None


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
    global _global_resume_client

    if _global_resume_client is None:
        _global_resume_client = ResumeServiceClient(host=host, port=port, timeout=timeout)
        await _global_resume_client.connect()

    return _global_resume_client


async def get_matching_client(
    host: str = "localhost",
    port: int = 50052,
    timeout: float = 5.0,
) -> MatchingServiceClient:
    """
    Получить или создать глобальный gRPC клиент для Matching Service.
    Get or create global gRPC client for Matching Service.

    Эта функция создаёт единый клиент для всего приложения,
    чтобы переиспользовать gRPC соединения.

    This function creates a single client for the entire application
    to reuse gRPC connections.

    Args:
        host: Хост Matching Service / Matching Service host
        port: Порт Matching Service / Matching Service port
        timeout: Таймаут для запросов / Request timeout

    Returns:
        MatchingServiceClient: Экземпляр клиента / Client instance

    Example:
        >>> client = await get_matching_client()
        >>> results = await client.get_match_results(vacancy_id="uuid-here")
    """
    global _global_matching_client

    if _global_matching_client is None:
        _global_matching_client = MatchingServiceClient(host=host, port=port, timeout=timeout)
        await _global_matching_client.connect()

    return _global_matching_client


async def close_resume_client() -> None:
    """
    Закрыть глобальный gRPC клиент для Resume Service.
    Close global gRPC client for Resume Service.

    Следует вызывать при завершении работы приложения.
    Should be called when shutting down the application.

    Example:
        >>> await close_resume_client()
    """
    global _global_resume_client

    if _global_resume_client is not None:
        await _global_resume_client.close()
        _global_resume_client = None


async def close_matching_client() -> None:
    """
    Закрыть глобальный gRPC клиент для Matching Service.
    Close global gRPC client for Matching Service.

    Следует вызывать при завершении работы приложения.
    Should be called when shutting down the application.

    Example:
        >>> await close_matching_client()
    """
    global _global_matching_client

    if _global_matching_client is not None:
        await _global_matching_client.close()
        _global_matching_client = None


async def close_all_clients() -> None:
    """
    Закрыть все глобальные gRPC клиенты.
    Close all global gRPC clients.

    Следует вызывать при завершении работы приложения.
    Should be called when shutting down the application.

    Example:
        >>> await close_all_clients()
    """
    await close_resume_client()
    await close_matching_client()
