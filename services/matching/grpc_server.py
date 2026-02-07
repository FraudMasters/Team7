"""
gRPC сервер для Сервиса Сопоставления (Matching Service)

Этот модуль предоставляет gRPC сервер для межсервисного взаимодействия,
обработки запросов на сопоставление резюме с вакансиями.

Функциональность:
- MatchResume: Сопоставить резюме с вакансией
- BatchMatch: Массовое сопоставление резюме
- GetMatchResults: Получить результаты сопоставления
- AnalyzeSkillGap: Анализ пробелов в навыках
- GetSkillGapReport: Получить отчёт о пробелах
- CreateComparison: Создать сравнение резюме
- GetComparison: Получить сравнение резюме
- ListComparisons: Получить список сравнений
- DeleteComparison: Удалить сравнение

This module provides the gRPC server for inter-service communication,
handling requests for matching resumes with vacancies.

Features:
- MatchResume: Match resume with vacancy
- BatchMatch: Batch match resumes
- GetMatchResults: Get match results
- AnalyzeSkillGap: Analyze skill gaps
- GetSkillGapReport: Get skill gap report
- CreateComparison: Create resume comparison
- GetComparison: Get resume comparison
- ListComparisons: List comparisons
- DeleteComparison: Delete comparison
"""
import asyncio
import logging
from typing import Optional
from uuid import UUID

import grpc
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

# Импорт сгенерированных protobuf модулей
# Import generated protobuf modules
# Эти файлы будут сгенерированы при компиляции .proto файлов:
# These files will be generated when compiling .proto files:
# python -m grpc_tools.protoc --python_out=. --grpc_python_out=. --proto_path=. protos/matching.proto
import sys
from pathlib import Path

# Добавляем корневую директорию в path для импорта protobuf
# Add root directory to path for protobuf import
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Try to import generated protobuf files
# Пробуем импортировать сгенерированные protobuf файлы
try:
    from protos import matching_pb2, matching_pb2_grpc
except ImportError:
    # Если protobuf файлы ещё не сгенерированы, создаём заглушки для типов
    # If protobuf files are not generated yet, create stub types
    class matching_pb2:
        """Mock protobuf module for development / Заглушка для разработки"""

        class MatchResult:
            pass

        class SkillMatch:
            pass

        class ExperienceDetail:
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

        class MissingSkillDetail:
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

        class ComparisonFilters:
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
        MatchingServiceServicer = object

from database import async_session_maker
from models.match_result import MatchResult as MatchResultModel

logger = logging.getLogger(__name__)


def _model_match_result_to_proto(match: MatchResultModel) -> matching_pb2.MatchResult:
    """
    Конвертировать модель MatchResult в protobuf сообщение MatchResult.
    Convert MatchResult model to protobuf MatchResult message.

    Args:
        match: Модель SQLAlchemy MatchResult / SQLAlchemy MatchResult model

    Returns:
        matching_pb2.MatchResult: Protobuf сообщение результата сопоставления
                                  / Protobuf match result message
    """
    proto_match = matching_pb2.MatchResult()
    proto_match.id = str(match.id)
    proto_match.resume_id = str(match.resume_id)
    proto_match.vacancy_id = str(match.vacancy_id)

    # Legacy fields
    proto_match.match_percentage = float(match.match_percentage) if match.match_percentage else 0.0
    if match.matched_skills:
        for skill in match.matched_skills:
            skill_match = proto_match.matched_skills.add()
            skill_match.skill = skill.get("skill", "")
            skill_match.confidence = skill.get("confidence", 0.0)
            skill_match.context = skill.get("context", "")
            skill_match.experience_months = skill.get("experience_months", 0)
    if match.missing_skills:
        proto_match.missing_skills.extend(match.missing_skills)
    if match.additional_skills_matched:
        proto_match.additional_skills_matched.extend(match.additional_skills_matched)
    if match.experience_verified is not None:
        proto_match.experience_verified = match.experience_verified
    if match.experience_details:
        for skill, detail in match.experience_details.items():
            exp_detail = proto_match.experience_details[skill]
            exp_detail.total_months = detail.get("total_months", 0)
            if detail.get("projects"):
                exp_detail.projects.extend(detail["projects"])
            exp_detail.proficiency_level = detail.get("proficiency_level", 0.0)

    # Unified matching metrics
    if match.overall_score is not None:
        proto_match.overall_score = float(match.overall_score)
    if match.keyword_score is not None:
        proto_match.keyword_score = float(match.keyword_score)
    if match.tfidf_score is not None:
        proto_match.tfidf_score = float(match.tfidf_score)
    if match.vector_score is not None:
        proto_match.vector_score = float(match.vector_score)
    if match.vector_similarity is not None:
        proto_match.vector_similarity = float(match.vector_similarity)
    if match.recommendation:
        proto_match.recommendation = match.recommendation
    if match.keyword_passed is not None:
        proto_match.keyword_passed = match.keyword_passed
    if match.tfidf_passed is not None:
        proto_match.tfidf_passed = match.tfidf_passed
    if match.vector_passed is not None:
        proto_match.vector_passed = match.vector_passed
    if match.tfidf_matched:
        for kw in match.tfidf_matched:
            kw_match = proto_match.tfidf_matched.add()
            kw_match.keyword = kw.get("keyword", "")
            kw_match.score = kw.get("score", 0.0)
            kw_match.frequency = kw.get("frequency", 0.0)
    if match.tfidf_missing:
        proto_match.tfidf_missing.extend(match.tfidf_missing)
    if match.matcher_version:
        proto_match.matcher_version = match.matcher_version

    if match.created_at:
        proto_match.created_at = int(match.created_at.timestamp())
    if match.updated_at:
        proto_match.updated_at = int(match.updated_at.timestamp())

    return proto_match


class MatchingServiceServicer(matching_pb2_grpc.MatchingServiceServicer):
    """
    gRPC сервис для сопоставления резюме с вакансиями / gRPC service for resume-vacancy matching

    Этот класс реализует все RPC методы, определённые в matching.proto.
    Методы работают с базой данных через AsyncSession.

    This class implements all RPC methods defined in matching.proto.
    Methods work with database through AsyncSession.
    """

    def __init__(self):
        """
        Инициализация сервис-вера.
        Initialize servicer.
        """
        logger.info("MatchingServiceServicer initialized")

    async def MatchResume(
        self,
        request: matching_pb2.MatchRequest,
        context: grpc.aio.ServicerContext,
    ) -> matching_pb2.MatchResponse:
        """
        Сопоставить резюме с вакансией.
        Match resume with vacancy.

        Args:
            request: MatchRequest с ID резюме и вакансии
                     / MatchRequest with resume ID and vacancy ID
            context: gRPC контекст / gRPC context

        Returns:
            MatchResponse с результатом сопоставления
            / MatchResponse with match result
        """
        logger.info(
            f"MatchResume called: resume_id={request.resume_id}, "
            f"vacancy_id={request.vacancy_id}, force_refresh={request.force_refresh}"
        )

        async with async_session_maker() as session:
            try:
                resume_uuid = UUID(request.resume_id)
                vacancy_uuid = UUID(request.vacancy_id)

                # Check if match result already exists
                # Проверяем, существует ли уже результат сопоставления
                result = await session.execute(
                    select(MatchResultModel).where(
                        MatchResultModel.resume_id == resume_uuid,
                        MatchResultModel.vacancy_id == vacancy_uuid,
                    )
                )
                match = result.scalar_one_or_none()

                if match and not request.force_refresh:
                    # Return cached result
                    # Возвращаем кэшированный результат
                    response = matching_pb2.MatchResponse()
                    response.result.CopyFrom(_model_match_result_to_proto(match))
                    response.success = True
                    response.message = "Match result retrieved from cache / Результат получен из кэша"
                    logger.info(f"Retrieved cached match result: {match.id}")
                    return response

                # TODO: Trigger matching calculation
                # TODO: Запустить расчёт сопоставления
                # This would involve calling the matcher service and creating a new result
                # Это подразумевает вызов сервиса сопоставления и создание нового результата

                # For now, return not implemented
                # На данный момент возвращаем "не реализовано"
                response = matching_pb2.MatchResponse()
                response.success = False
                response.message = (
                    "Matching calculation not yet implemented via gRPC. "
                    "Use REST API endpoint. / "
                    "Расчёт сопоставления через gRPC пока не реализован. "
                    "Используйте REST API endpoint."
                )
                return response

            except ValueError as e:
                logger.error(f"Invalid UUID: {e}")
                response = matching_pb2.MatchResponse()
                response.success = False
                response.message = f"Invalid ID format / Неверный формат ID: {str(e)}"
                return response
            except Exception as e:
                logger.error(f"Error matching resume: {e}", exc_info=True)
                response = matching_pb2.MatchResponse()
                response.success = False
                response.message = f"Error: {str(e)}"
                return response

    async def BatchMatch(
        self,
        request: matching_pb2.BatchMatchRequest,
        context: grpc.aio.ServicerContext,
    ) -> matching_pb2.BatchMatchResponse:
        """
        Массовое сопоставление резюме с вакансией.
        Batch match resumes with vacancy.

        Args:
            request: BatchMatchRequest с ID вакансии и списком ID резюме
                     / BatchMatchRequest with vacancy ID and list of resume IDs
            context: gRPC контекст / gRPC context

        Returns:
            BatchMatchResponse с результатами сопоставления
            / BatchMatchResponse with match results
        """
        logger.info(
            f"BatchMatch called: vacancy_id={request.vacancy_id}, "
            f"resume_count={len(request.resume_ids)}, force_refresh={request.force_refresh}"
        )

        async with async_session_maker() as session:
            try:
                vacancy_uuid = UUID(request.vacancy_id)
                resume_uuids = [UUID(rid) for rid in request.resume_ids]

                results = []
                successful_count = 0
                failed_resume_ids = []

                for resume_uuid in resume_uuids:
                    try:
                        # Check if match result exists
                        # Проверяем, существует ли результат сопоставления
                        result = await session.execute(
                            select(MatchResultModel).where(
                                MatchResultModel.resume_id == resume_uuid,
                                MatchResultModel.vacancy_id == vacancy_uuid,
                            )
                        )
                        match = result.scalar_one_or_none()

                        if match and not request.force_refresh:
                            # Add cached result
                            # Добавляем кэшированный результат
                            results.append(_model_match_result_to_proto(match))
                            successful_count += 1
                        else:
                            # TODO: Calculate match
                            # TODO: Рассчитать сопоставление
                            failed_resume_ids.append(str(resume_uuid))

                    except Exception as e:
                        logger.error(f"Error processing resume {resume_uuid}: {e}")
                        failed_resume_ids.append(str(resume_uuid))

                response = matching_pb2.BatchMatchResponse()
                for result in results:
                    response.results.add().CopyFrom(result)
                response.total_count = len(request.resume_ids)
                response.successful_count = successful_count
                response.failed_resume_ids.extend(failed_resume_ids)
                response.message = (
                    f"Batch match completed: {successful_count}/{len(request.resume_ids)} successful. "
                    f"Массовое сопоставление завершено: {successful_count}/{len(request.resume_ids)} успешно."
                )

                logger.info(f"BatchMatch completed: {successful_count} successful, {len(failed_resume_ids)} failed")
                return response

            except ValueError as e:
                logger.error(f"Invalid UUID: {e}")
                response = matching_pb2.BatchMatchResponse()
                response.total_count = len(request.resume_ids)
                response.successful_count = 0
                response.failed_resume_ids.extend(request.resume_ids)
                response.message = f"Invalid ID format / Неверный формат ID: {str(e)}"
                return response
            except Exception as e:
                logger.error(f"Error in batch match: {e}", exc_info=True)
                response = matching_pb2.BatchMatchResponse()
                response.total_count = len(request.resume_ids)
                response.successful_count = 0
                response.failed_resume_ids.extend(request.resume_ids)
                response.message = f"Error: {str(e)}"
                return response

    async def GetMatchResults(
        self,
        request: matching_pb2.GetMatchResultsRequest,
        context: grpc.aio.ServicerContext,
    ) -> matching_pb2.GetMatchResultsResponse:
        """
        Получить результаты сопоставления.
        Get match results.

        Args:
            request: GetMatchResultsRequest с фильтрами
                     / GetMatchResultsRequest with filters
            context: gRPC контекст / gRPC context

        Returns:
            GetMatchResultsResponse с результатами сопоставления
            / GetMatchResultsResponse with match results
        """
        logger.info(
            f"GetMatchResults called: resume_id={request.resume_id}, "
            f"vacancy_id={request.vacancy_id}, page={request.page}, "
            f"page_size={request.page_size}, min_score={request.min_score}"
        )

        async with async_session_maker() as session:
            try:
                query = select(MatchResultModel)

                # Apply filters
                # Применяем фильтры
                if request.resume_id:
                    resume_uuid = UUID(request.resume_id)
                    query = query.where(MatchResultModel.resume_id == resume_uuid)

                if request.vacancy_id:
                    vacancy_uuid = UUID(request.vacancy_id)
                    query = query.where(MatchResultModel.vacancy_id == vacancy_uuid)

                if request.min_score > 0:
                    query = query.where(MatchResultModel.overall_score >= request.min_score)

                # Get total count
                # Получаем общее количество
                count_query = select(func.count()).select_from(query.alias())
                total_result = await session.execute(count_query)
                total = total_result.scalar() or 0

                # Apply pagination
                # Применяем пагинацию
                page = max(1, request.page) if request.page > 0 else 1
                page_size = min(max(1, request.page_size), 100) if request.page_size > 0 else 20
                offset = (page - 1) * page_size

                query = query.order_by(MatchResultModel.created_at.desc())
                query = query.offset(offset).limit(page_size)

                result = await session.execute(query)
                matches = result.scalars().all()

                response = matching_pb2.GetMatchResultsResponse()
                for match in matches:
                    response.results.add().CopyFrom(_model_match_result_to_proto(match))
                response.total = total
                response.page = page
                response.page_size = page_size

                logger.info(f"GetMatchResults: returned {len(matches)} results (total: {total})")
                return response

            except ValueError as e:
                logger.error(f"Invalid UUID: {e}")
                response = matching_pb2.GetMatchResultsResponse()
                response.total = 0
                return response
            except Exception as e:
                logger.error(f"Error getting match results: {e}", exc_info=True)
                response = matching_pb2.GetMatchResultsResponse()
                response.total = 0
                return response

    async def AnalyzeSkillGap(
        self,
        request: matching_pb2.AnalyzeSkillGapRequest,
        context: grpc.aio.ServicerContext,
    ) -> matching_pb2.AnalyzeSkillGapResponse:
        """
        Проанализировать пробелы в навыках.
        Analyze skill gaps.

        Args:
            request: AnalyzeSkillGapRequest с ID резюме и вакансии
                     / AnalyzeSkillGapRequest with resume ID and vacancy ID
            context: gRPC контекст / gRPC context

        Returns:
            AnalyzeSkillGapResponse с отчётом о пробелах
            / AnalyzeSkillGapResponse with gap report
        """
        logger.info(
            f"AnalyzeSkillGap called: resume_id={request.resume_id}, "
            f"vacancy_id={request.vacancy_id}, force_refresh={request.force_refresh}"
        )

        # TODO: Implement skill gap analysis
        # TODO: Реализовать анализ пробелов в навыках
        # This would require a SkillGapReport model and analysis logic
        # Это потребует модель SkillGapReport и логику анализа

        response = matching_pb2.AnalyzeSkillGapResponse()
        response.success = False
        response.message = (
            "Skill gap analysis not yet implemented via gRPC. "
            "Use REST API endpoint. / "
            "Анализ пробелов в навыках через gRPC пока не реализован. "
            "Используйте REST API endpoint."
        )
        return response

    async def GetSkillGapReport(
        self,
        request: matching_pb2.GetSkillGapReportRequest,
        context: grpc.aio.ServicerContext,
    ) -> matching_pb2.GetSkillGapReportResponse:
        """
        Получить отчёт о пробелах в навыках.
        Get skill gap report.

        Args:
            request: GetSkillGapReportRequest с ID резюме и вакансии
                     / GetSkillGapReportRequest with resume ID and vacancy ID
            context: gRPC контекст / gRPC context

        Returns:
            GetSkillGapReportResponse с отчётом о пробелах
            / GetSkillGapReportResponse with gap report
        """
        logger.info(
            f"GetSkillGapReport called: resume_id={request.resume_id}, "
            f"vacancy_id={request.vacancy_id}"
        )

        # TODO: Implement skill gap report retrieval
        # TODO: Реализовать получение отчёта о пробелах в навыках
        # This would require a SkillGapReport model
        # Это потребует модель SkillGapReport

        response = matching_pb2.GetSkillGapReportResponse()
        response.found = False
        return response

    async def CreateComparison(
        self,
        request: matching_pb2.CreateComparisonRequest,
        context: grpc.aio.ServicerContext,
    ) -> matching_pb2.CreateComparisonResponse:
        """
        Создать сравнение резюме.
        Create resume comparison.

        Args:
            request: CreateComparisonRequest с данными сравнения
                     / CreateComparisonRequest with comparison data
            context: gRPC контекст / gRPC context

        Returns:
            CreateComparisonResponse с созданным сравнением
            / CreateComparisonResponse with created comparison
        """
        logger.info(
            f"CreateComparison called: vacancy_id={request.vacancy_id}, "
            f"resume_count={len(request.resume_ids)}, name={request.name}"
        )

        # TODO: Implement comparison creation
        # TODO: Реализовать создание сравнения
        # This would require a ResumeComparison model
        # Это потребует модель ResumeComparison

        response = matching_pb2.CreateComparisonResponse()
        response.success = False
        response.message = (
            "Comparison creation not yet implemented via gRPC. "
            "Use REST API endpoint. / "
            "Создание сравнения через gRPC пока не реализовано. "
            "Используйте REST API endpoint."
        )
        return response

    async def GetComparison(
        self,
        request: matching_pb2.GetComparisonRequest,
        context: grpc.aio.ServicerContext,
    ) -> matching_pb2.GetComparisonResponse:
        """
        Получить сравнение резюме.
        Get resume comparison.

        Args:
            request: GetComparisonRequest с ID сравнения
                     / GetComparisonRequest with comparison ID
            context: gRPC контекст / gRPC context

        Returns:
            GetComparisonResponse с данными сравнения
            / GetComparisonResponse with comparison data
        """
        logger.info(f"GetComparison called: id={request.id}")

        # TODO: Implement comparison retrieval
        # TODO: Реализовать получение сравнения
        # This would require a ResumeComparison model
        # Это потребует модель ResumeComparison

        response = matching_pb2.GetComparisonResponse()
        response.found = False
        return response

    async def ListComparisons(
        self,
        request: matching_pb2.ListComparisonsRequest,
        context: grpc.aio.ServicerContext,
    ) -> matching_pb2.ListComparisonsResponse:
        """
        Получить список сравнений.
        Get comparison list.

        Args:
            request: ListComparisonsRequest с фильтрами
                     / ListComparisonsRequest with filters
            context: gRPC контекст / gRPC context

        Returns:
            ListComparisonsResponse со списком сравнений
            / ListComparisonsResponse with comparison list
        """
        logger.info(
            f"ListComparisons called: vacancy_id={request.vacancy_id}, "
            f"created_by={request.created_by}, page={request.page}, "
            f"page_size={request.page_size}"
        )

        # TODO: Implement comparison listing
        # TODO: Реализовать получение списка сравнений
        # This would require a ResumeComparison model
        # Это потребует модель ResumeComparison

        response = matching_pb2.ListComparisonsResponse()
        response.total = 0
        response.page = request.page if request.page > 0 else 1
        response.page_size = request.page_size if request.page_size > 0 else 20
        return response

    async def DeleteComparison(
        self,
        request: matching_pb2.DeleteComparisonRequest,
        context: grpc.aio.ServicerContext,
    ) -> matching_pb2.DeleteComparisonResponse:
        """
        Удалить сравнение.
        Delete comparison.

        Args:
            request: DeleteComparisonRequest с ID сравнения
                     / DeleteComparisonRequest with comparison ID
            context: gRPC контекст / gRPC context

        Returns:
            DeleteComparisonResponse с результатом удаления
            / DeleteComparisonResponse with deletion result
        """
        logger.info(f"DeleteComparison called: id={request.id}")

        # TODO: Implement comparison deletion
        # TODO: Реализовать удаление сравнения
        # This would require a ResumeComparison model
        # Это потребует модель ResumeComparison

        response = matching_pb2.DeleteComparisonResponse()
        response.success = False
        response.message = (
            "Comparison deletion not yet implemented via gRPC. "
            "Use REST API endpoint. / "
            "Удаление сравнения через gRPC пока не реализовано. "
            "Используйте REST API endpoint."
        )
        return response


async def serve(
    host: str = "0.0.0.0",
    port: int = 50052,
    max_workers: int = 10,
) -> grpc.aio.Server:
    """
    Запустить gRPC сервер для Matching Service.
    Start gRPC server for Matching Service.

    Args:
        host: Хост для привязки / Host to bind to
        port: Порт для привязки / Port to bind to
        max_workers: Максимальное количество воркеров / Maximum number of workers

    Returns:
        grpc.aio.Server: Запущенный gRPC сервер / Started gRPC server

    Example:
        >>> server = await serve(host="0.0.0.0", port=50052)
        >>> await server.wait_for_termination()
    """
    server = grpc.aio.server(max_workers)

    # Регистрируем сервис-вер / Register servicer
    matching_pb2_grpc.add_MatchingServiceServicer_to_server(
        MatchingServiceServicer(), server
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
