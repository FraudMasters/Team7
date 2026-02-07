"""
gRPC сервер для Сервиса Обработки Резюме (Resume Processing Service)

Этот модуль предоставляет gRPC сервер для межсервисного взаимодействия,
обработки запросов от других микросервисов (Matching, Candidate, etc.).

Функциональность:
- CreateResume: Создание новой записи о резюме
- GetResume: Получение данных резюме по ID
- ListResumes: Получение списка резюме с пагинацией
- DeleteResume: Удаление резюме
- AnalyzeResume: Запуск анализа резюме
- GetResumeAnalysis: Получение результатов анализа
- GetWorkExperience: Получение опыта работы
- GetResumeText: Получение текста резюме

This module provides the gRPC server for inter-service communication,
handling requests from other microservices (Matching, Candidate, etc.).

Features:
- CreateResume: Create new resume entry
- GetResume: Get resume data by ID
- ListResumes: Get paginated list of resumes
- DeleteResume: Delete resume
- AnalyzeResume: Trigger resume analysis
- GetResumeAnalysis: Get analysis results
- GetWorkExperience: Get work experience
- GetResumeText: Get resume text
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

import grpc
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

# Импорт сгенерированных protobuf модулей
# Import generated protobuf modules
# Эти файлы будут сгенерированы при компиляции .proto файлов:
# These files will be generated when compiling .proto files:
# python -m grpc_tools.protoc --python_out=. --grpc_python_out=. --proto_path=. protos/resume.proto
import sys
from pathlib import Path

# Добавляем корневую директорию в path для импорта protobuf
# Add root directory to path for protobuf import
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
        ResumeServiceServicer = object

from database import async_session_maker
from models.resume import Resume, ResumeStatus
from models.analysis_result import AnalysisResult

logger = logging.getLogger(__name__)


# Mapping between proto and model ResumeStatus
# Маппинг между proto и моделью ResumeStatus
PROTO_STATUS_TO_MODEL = {
    resume_pb2.ResumeStatus.PENDING: ResumeStatus.PENDING,
    resume_pb2.ResumeStatus.PROCESSING: ResumeStatus.PROCESSING,
    resume_pb2.ResumeStatus.COMPLETED: ResumeStatus.COMPLETED,
    resume_pb2.ResumeStatus.FAILED: ResumeStatus.FAILED,
    resume_pb2.ResumeStatus.NEW: ResumeStatus.NEW,
    resume_pb2.ResumeStatus.REVIEWED: ResumeStatus.REVIEWED,
    resume_pb2.ResumeStatus.INTERVIEW: ResumeStatus.INTERVIEW,
    resume_pb2.ResumeStatus.OFFERED: ResumeStatus.OFFERED,
    resume_pb2.ResumeStatus.HIRED: ResumeStatus.HIRED,
}

MODEL_STATUS_TO_PROTO = {
    ResumeStatus.PENDING: resume_pb2.ResumeStatus.PENDING,
    ResumeStatus.PROCESSING: resume_pb2.ResumeStatus.PROCESSING,
    ResumeStatus.COMPLETED: resume_pb2.ResumeStatus.COMPLETED,
    ResumeStatus.FAILED: resume_pb2.ResumeStatus.FAILED,
    ResumeStatus.NEW: resume_pb2.ResumeStatus.NEW,
    ResumeStatus.REVIEWED: resume_pb2.ResumeStatus.REVIEWED,
    ResumeStatus.INTERVIEW: resume_pb2.ResumeStatus.INTERVIEW,
    ResumeStatus.OFFERED: resume_pb2.ResumeStatus.OFFERED,
    ResumeStatus.HIRED: resume_pb2.ResumeStatus.HIRED,
}


def _model_resume_to_proto(resume: Resume) -> resume_pb2.Resume:
    """
    Конвертировать модель Resume в protobuf сообщение Resume.
    Convert Resume model to protobuf Resume message.

    Args:
        resume: Модель SQLAlchemy Resume / SQLAlchemy Resume model

    Returns:
        resume_pb2.Resume: Protobuf сообщение резюме / Protobuf resume message
    """
    proto_resume = resume_pb2.Resume()
    proto_resume.id = str(resume.id)
    proto_resume.filename = resume.filename
    proto_resume.file_path = resume.file_path
    proto_resume.content_type = resume.content_type
    proto_resume.status = MODEL_STATUS_TO_PROTO.get(
        resume.status, resume_pb2.ResumeStatus.PENDING
    )

    if resume.raw_text:
        proto_resume.raw_text = resume.raw_text
    if resume.language:
        proto_resume.language = resume.language
    if resume.error_message:
        proto_resume.error_message = resume.error_message

    if resume.created_at:
        proto_resume.created_at = int(resume.created_at.timestamp() * 1000)
    if resume.updated_at:
        proto_resume.updated_at = int(resume.updated_at.timestamp() * 1000)

    return proto_resume


def _proto_status_to_model_filter(proto_status) -> Optional[ResumeStatus]:
    """
    Конвертировать protobuf статус в статус модели Resume.
    Convert protobuf status to Resume model status.

    Args:
        proto_status: Protobuf статус ResumeStatus / Protobuf ResumeStatus enum

    Returns:
        Optional[ResumeStatus]: Статус модели или None / Model status or None
    """
    return PROTO_STATUS_TO_MODEL.get(proto_status)


class ResumeServiceServicer(resume_pb2_grpc.ResumeServiceServicer):
    """
    gRPC сервис для обработки резюме / gRPC service for resume processing

    Этот класс реализует все RPC методы, определённые в resume.proto.
    Методы работают с базой данных через AsyncSession.

    This class implements all RPC methods defined in resume.proto.
    Methods work with database through AsyncSession.
    """

    def __init__(self):
        """
        Инициализация сервис-вера.
        Initialize servicer.
        """
        logger.info("ResumeServiceServicer initialized")

    async def CreateResume(
        self,
        request: resume_pb2.CreateResumeRequest,
        context: grpc.aio.ServicerContext,
    ) -> resume_pb2.CreateResumeResponse:
        """
        Создать новую запись о резюме.
        Create new resume entry.

        Args:
            request: CreateResumeRequest с данными файла резюме
                     / CreateResumeRequest with resume file data
            context: gRPC контекст / gRPC context

        Returns:
            CreateResumeResponse с созданным резюме
            / CreateResumeResponse with created resume
        """
        logger.info(f"CreateResume called: filename={request.filename}")

        async with async_session_maker() as session:
            try:
                # TODO: Сохранить файл на диск и получить путь
                # TODO: Save file to disk and get path

                resume = Resume(
                    filename=request.filename,
                    file_path=f"/path/to/uploads/{request.filename}",  # Заглушка / Placeholder
                    content_type=request.content_type,
                    status=ResumeStatus.PENDING,
                    language=request.language if request.language else None,
                )

                session.add(resume)
                await session.commit()
                await session.refresh(resume)

                response = resume_pb2.CreateResumeResponse()
                response.resume.CopyFrom(_model_resume_to_proto(resume))
                response.success = True
                response.message = "Resume created successfully / Резюме создано успешно"

                logger.info(f"Resume created: id={resume.id}")
                return response

            except Exception as e:
                logger.error(f"Error creating resume: {e}", exc_info=True)
                response = resume_pb2.CreateResumeResponse()
                response.success = False
                response.message = f"Error: {str(e)}"
                return response

    async def GetResume(
        self,
        request: resume_pb2.GetResumeRequest,
        context: grpc.aio.ServicerContext,
    ) -> resume_pb2.GetResumeResponse:
        """
        Получить резюме по ID.
        Get resume by ID.

        Args:
            request: GetResumeRequest с ID резюме / GetResumeRequest with resume ID
            context: gRPC контекст / gRPC context

        Returns:
            GetResumeResponse с данными резюме / GetResumeResponse with resume data
        """
        logger.info(f"GetResume called: id={request.id}")

        async with async_session_maker() as session:
            try:
                resume_uuid = UUID(request.id)
                result = await session.execute(select(Resume).where(Resume.id == resume_uuid))
                resume = result.scalar_one_or_none()

                response = resume_pb2.GetResumeResponse()
                if resume:
                    response.resume.CopyFrom(_model_resume_to_proto(resume))
                    response.found = True
                    logger.info(f"Resume found: id={request.id}")
                else:
                    response.found = False
                    logger.warning(f"Resume not found: id={request.id}")

                return response

            except ValueError:
                logger.error(f"Invalid UUID: {request.id}")
                response = resume_pb2.GetResumeResponse()
                response.found = False
                return response
            except Exception as e:
                logger.error(f"Error getting resume: {e}", exc_info=True)
                response = resume_pb2.GetResumeResponse()
                response.found = False
                return response

    async def ListResumes(
        self,
        request: resume_pb2.ListResumesRequest,
        context: grpc.aio.ServicerContext,
    ) -> resume_pb2.ListResumesResponse:
        """
        Получить список резюме с пагинацией и фильтрами.
        Get list of resumes with pagination and filters.

        Args:
            request: ListResumesRequest с параметрами страницы и фильтрами
                     / ListResumesRequest with page params and filters
            context: gRPC контекст / gRPC context

        Returns:
            ListResumesResponse со списком резюме / ListResumesResponse with resume list
        """
        logger.info(f"ListResumes called: page={request.page}, page_size={request.page_size}")

        async with async_session_maker() as session:
            try:
                query = select(Resume)

                # Применить фильтр по статусу / Apply status filter
                if request.status and request.status != 0:  # 0 = PENDING (default)
                    model_status = _proto_status_to_model_filter(request.status)
                    if model_status:
                        query = query.where(Resume.status == model_status)

                # Применить фильтр по языку / Apply language filter
                if request.language:
                    query = query.where(Resume.language == request.language)

                # Получить общее количество / Get total count
                count_result = await session.execute(select(Resume.id).select_from(query.alias()))
                total = len(count_result.all())

                # Применить сортировку и пагинацию / Apply sorting and pagination
                query = query.order_by(Resume.created_at.desc())

                page = max(1, request.page) if request.page > 0 else 1
                page_size = min(max(1, request.page_size), 100) if request.page_size > 0 else 20
                offset = (page - 1) * page_size

                query = query.offset(offset).limit(page_size)

                result = await session.execute(query)
                resumes = result.scalars().all()

                response = resume_pb2.ListResumesResponse()
                response.total = total
                response.page = page
                response.page_size = page_size

                for resume in resumes:
                    response.resumes.add().CopyFrom(_model_resume_to_proto(resume))

                logger.info(f"ListResumes: returned {len(resumes)} resumes")
                return response

            except Exception as e:
                logger.error(f"Error listing resumes: {e}", exc_info=True)
                response = resume_pb2.ListResumesResponse()
                response.total = 0
                return response

    async def DeleteResume(
        self,
        request: resume_pb2.DeleteResumeRequest,
        context: grpc.aio.ServicerContext,
    ) -> resume_pb2.DeleteResumeResponse:
        """
        Удалить резюме по ID.
        Delete resume by ID.

        Args:
            request: DeleteResumeRequest с ID резюме / DeleteResumeRequest with resume ID
            context: gRPC контекст / gRPC context

        Returns:
            DeleteResumeResponse с результатом удаления
            / DeleteResumeResponse with deletion result
        """
        logger.info(f"DeleteResume called: id={request.id}")

        async with async_session_maker() as session:
            try:
                resume_uuid = UUID(request.id)

                # Проверить существование резюме / Check resume existence
                result = await session.execute(select(Resume).where(Resume.id == resume_uuid))
                resume = result.scalar_one_or_none()

                if not resume:
                    response = resume_pb2.DeleteResumeResponse()
                    response.success = False
                    response.message = "Resume not found / Резюме не найдено"
                    return response

                # Удалить файл с диска / Delete file from disk
                # TODO: Удалить файл из файловой системы / Delete file from filesystem

                # Удалить из базы данных / Delete from database
                await session.execute(delete(Resume).where(Resume.id == resume_uuid))
                await session.commit()

                response = resume_pb2.DeleteResumeResponse()
                response.success = True
                response.message = "Resume deleted successfully / Резюме удалено успешно"

                logger.info(f"Resume deleted: id={request.id}")
                return response

            except ValueError:
                logger.error(f"Invalid UUID: {request.id}")
                response = resume_pb2.DeleteResumeResponse()
                response.success = False
                response.message = "Invalid resume ID / Неверный ID резюме"
                return response
            except Exception as e:
                logger.error(f"Error deleting resume: {e}", exc_info=True)
                response = resume_pb2.DeleteResumeResponse()
                response.success = False
                response.message = f"Error: {str(e)}"
                return response

    async def AnalyzeResume(
        self,
        request: resume_pb2.AnalyzeResumeRequest,
        context: grpc.aio.ServicerContext,
    ) -> resume_pb2.AnalyzeResumeResponse:
        """
        Запустить анализ резюме.
        Trigger resume analysis.

        Args:
            request: AnalyzeResumeRequest с ID резюме и флагом принудительного анализа
                     / AnalyzeResumeRequest with resume ID and force refresh flag
            context: gRPC контекст / gRPC context

        Returns:
            AnalyzeResumeResponse с результатами анализа
            / AnalyzeResumeResponse with analysis results
        """
        logger.info(f"AnalyzeResume called: resume_id={request.resume_id}, force_refresh={request.force_refresh}")

        async with async_session_maker() as session:
            try:
                resume_uuid = UUID(request.resume_id)
                result = await session.execute(select(Resume).where(Resume.id == resume_uuid))
                resume = result.scalar_one_or_none()

                if not resume:
                    response = resume_pb2.AnalyzeResumeResponse()
                    response.success = False
                    response.message = "Resume not found / Резюме не найдено"
                    return response

                # TODO: Запустить асинхронную задачу анализа через Celery
                # TODO: Run async analysis task via Celery

                response = resume_pb2.AnalyzeResumeResponse()
                response.success = True
                response.message = "Analysis task started / Задача анализа запущена"

                logger.info(f"Analysis task started for resume: {request.resume_id}")
                return response

            except ValueError:
                logger.error(f"Invalid UUID: {request.resume_id}")
                response = resume_pb2.AnalyzeResumeResponse()
                response.success = False
                response.message = "Invalid resume ID / Неверный ID резюме"
                return response
            except Exception as e:
                logger.error(f"Error analyzing resume: {e}", exc_info=True)
                response = resume_pb2.AnalyzeResumeResponse()
                response.success = False
                response.message = f"Error: {str(e)}"
                return response

    async def GetResumeAnalysis(
        self,
        request: resume_pb2.GetResumeAnalysisRequest,
        context: grpc.aio.ServicerContext,
    ) -> resume_pb2.GetResumeAnalysisResponse:
        """
        Получить результаты анализа резюме.
        Get resume analysis results.

        Args:
            request: GetResumeAnalysisRequest с ID резюме
                     / GetResumeAnalysisRequest with resume ID
            context: gRPC контекст / gRPC context

        Returns:
            GetResumeAnalysisResponse с данными анализа
            / GetResumeAnalysisResponse with analysis data
        """
        logger.info(f"GetResumeAnalysis called: resume_id={request.resume_id}")

        async with async_session_maker() as session:
            try:
                resume_uuid = UUID(request.resume_id)

                # Получить результат анализа / Get analysis result
                result = await session.execute(
                    select(AnalysisResult).where(AnalysisResult.resume_id == resume_uuid)
                )
                analysis = result.scalar_one_or_none()

                response = resume_pb2.GetResumeAnalysisResponse()
                if analysis:
                    # Конвертировать анализ в protobuf формат
                    # Convert analysis to protobuf format
                    proto_analysis = resume_pb2.ResumeAnalysis()
                    proto_analysis.id = str(analysis.id)
                    proto_analysis.resume_id = str(analysis.resume_id)

                    if analysis.skills:
                        proto_analysis.skills.extend(analysis.skills)
                    if analysis.keywords:
                        for kw in analysis.keywords:
                            kw_proto = proto_analysis.keywords.add()
                            kw_proto.text = kw.get("text", "")
                            kw_proto.score = kw.get("score", 0.0)
                    if analysis.entities:
                        for k, v in analysis.entities.items():
                            proto_analysis.entities[k] = str(v)
                    if analysis.errors:
                        for err in analysis.errors:
                            err_proto = proto_analysis.grammar_issues.add()
                            err_proto.message = str(err)

                    if analysis.created_at:
                        proto_analysis.created_at = int(analysis.created_at.timestamp() * 1000)
                    if analysis.updated_at:
                        proto_analysis.updated_at = int(analysis.updated_at.timestamp() * 1000)

                    response.analysis.CopyFrom(proto_analysis)
                    response.found = True
                    logger.info(f"Analysis found: resume_id={request.resume_id}")
                else:
                    response.found = False
                    logger.warning(f"Analysis not found: resume_id={request.resume_id}")

                return response

            except ValueError:
                logger.error(f"Invalid UUID: {request.resume_id}")
                response = resume_pb2.GetResumeAnalysisResponse()
                response.found = False
                return response
            except Exception as e:
                logger.error(f"Error getting analysis: {e}", exc_info=True)
                response = resume_pb2.GetResumeAnalysisResponse()
                response.found = False
                return response

    async def GetWorkExperience(
        self,
        request: resume_pb2.GetWorkExperienceRequest,
        context: grpc.aio.ServicerContext,
    ) -> resume_pb2.GetWorkExperienceResponse:
        """
        Получить опыт работы из резюме.
        Get work experience from resume.

        Args:
            request: GetWorkExperienceRequest с ID резюме
                     / GetWorkExperienceRequest with resume ID
            context: gRPC контекст / gRPC context

        Returns:
            GetWorkExperienceResponse с опытом работы
            / GetWorkExperienceResponse with work experience
        """
        logger.info(f"GetWorkExperience called: resume_id={request.resume_id}")

        async with async_session_maker() as session:
            try:
                resume_uuid = UUID(request.resume_id)

                # Получить анализ и извлечь опыт работы
                # Get analysis and extract work experience
                result = await session.execute(
                    select(AnalysisResult).where(AnalysisResult.resume_id == resume_uuid)
                )
                analysis = result.scalar_one_or_none()

                response = resume_pb2.GetWorkExperienceResponse()
                response.found = False

                if analysis and analysis.experience_summary:
                    # TODO: Парсить experience_summary и создавать WorkExperience сообщения
                    # TODO: Parse experience_summary and create WorkExperience messages
                    # experience_summary содержит JSON с данными об опыте
                    # experience_summary contains JSON with experience data

                    response.found = True
                    logger.info(f"Work experience found: resume_id={request.resume_id}")
                else:
                    logger.warning(f"Work experience not found: resume_id={request.resume_id}")

                return response

            except ValueError:
                logger.error(f"Invalid UUID: {request.resume_id}")
                response = resume_pb2.GetWorkExperienceResponse()
                response.found = False
                return response
            except Exception as e:
                logger.error(f"Error getting work experience: {e}", exc_info=True)
                response = resume_pb2.GetWorkExperienceResponse()
                response.found = False
                return response

    async def GetResumeText(
        self,
        request: resume_pb2.GetResumeRequest,
        context: grpc.aio.ServicerContext,
    ) -> resume_pb2.GetResumeTextResponse:
        """
        Получить текст резюме для дополнительных сервисов.
        Get resume text for additional services.

        Этот метод используется другими сервисами (например, Matching)
        для получения исходного текста резюме без полной структуры.

        This method is used by other services (e.g., Matching)
        to get raw resume text without full structure.

        Args:
            request: GetResumeRequest с ID резюме / GetResumeRequest with resume ID
            context: gRPC контекст / gRPC context

        Returns:
            GetResumeTextResponse с текстом резюме / GetResumeTextResponse with resume text
        """
        logger.info(f"GetResumeText called: id={request.id}")

        async with async_session_maker() as session:
            try:
                resume_uuid = UUID(request.id)
                result = await session.execute(select(Resume).where(Resume.id == resume_uuid))
                resume = result.scalar_one_or_none()

                response = resume_pb2.GetResumeTextResponse()
                if resume:
                    response.resume_id = str(resume.id)
                    response.found = True
                    if resume.raw_text:
                        response.raw_text = resume.raw_text
                    if resume.language:
                        response.language = resume.language
                    logger.info(f"Resume text found: id={request.id}, length={len(resume.raw_text) if resume.raw_text else 0}")
                else:
                    response.found = False
                    logger.warning(f"Resume not found: id={request.id}")

                return response

            except ValueError:
                logger.error(f"Invalid UUID: {request.id}")
                response = resume_pb2.GetResumeTextResponse()
                response.found = False
                return response
            except Exception as e:
                logger.error(f"Error getting resume text: {e}", exc_info=True)
                response = resume_pb2.GetResumeTextResponse()
                response.found = False
                return response


async def serve(
    host: str = "0.0.0.0",
    port: int = 50051,
    max_workers: int = 10,
) -> grpc.aio.Server:
    """
    Запустить gRPC сервер для Resume Processing Service.
    Start gRPC server for Resume Processing Service.

    Args:
        host: Хост для привязки / Host to bind to
        port: Порт для привязки / Port to bind to
        max_workers: Максимальное количество воркеров / Maximum number of workers

    Returns:
        grpc.aio.Server: Запущенный gRPC сервер / Started gRPC server

    Example:
        >>> server = await serve(host="0.0.0.0", port=50051)
        >>> await server.wait_for_termination()
    """
    server = grpc.aio.server(max_workers)

    # Регистрируем сервис-вер / Register servicer
    resume_pb2_grpc.add_ResumeServiceServicer_to_server(
        ResumeServiceServicer(), server
    )

    # Привязываем сервер к адресу / Bind server to address
    server_address = f"{host}:{port}"
    server.add_insecure_port(server_address)

    # Запускаем сервер / Start server
    await server.start()

    logger.info(
        f"gRPC server started on {server_address} "
        f"(max_workers={max_workers}) / "
        f"gRPC сервер запущен на {server_address}"
    )

    return server


async def main():
    """
    Точка входа для запуска gRPC сервера.
    Entry point for starting gRPC server.

    Пример использования / Usage example:
        python -m grpc_server
    """
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    server = await serve()

    logger.info("gRPC server is running. Press Ctrl+C to stop.")
    logger.info("gRPC сервер работает. Нажмите Ctrl+C для остановки.")

    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server / Остановка gRPC сервера...")
        await server.stop(5)  # 5 seconds grace period / 5 секунд на завершение


if __name__ == "__main__":
    asyncio.run(main())
