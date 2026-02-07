"""
gRPC сервер для Сервиса Кандидатов (Candidate Service)

Этот модуль предоставляет gRPC сервер для межсервисного взаимодействия,
обработки запросов на управление кандидатами, включая заметки, теги,
активность и отзывы.

Функциональность:
- CreateNote, GetNotes, UpdateNote, DeleteNote: Управление заметками о кандидатах
- CreateTag, GetTags, UpdateTag, DeleteTag: Управление тегами кандидатов
- AddTagToResume, RemoveTagFromResume, GetResumeTags: Привязка тегов к резюме
- LogActivity, GetActivities: Логирование и получение активности кандидатов
- UpdateStatus, GetStatus: Обновление и получение статуса кандидата
- AddFeedback, GetFeedback: Управление обратной связью о навыках

This module provides the gRPC server for inter-service communication,
handling requests for candidate management, including notes, tags,
activities, and feedback.

Features:
- CreateNote, GetNotes, UpdateNote, DeleteNote: Candidate notes management
- CreateTag, GetTags, UpdateTag, DeleteTag: Candidate tags management
- AddTagToResume, RemoveTagFromResume, GetResumeTags: Tag-resume association
- LogActivity, GetActivities: Activity logging and retrieval
- UpdateStatus, GetStatus: Candidate status updates and retrieval
- AddFeedback, GetFeedback: Skill feedback management
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

import grpc
from sqlalchemy import select, delete, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

# Импорт сгенерированных protobuf модулей
# Import generated protobuf modules
# Эти файлы будут сгенерированы при компиляции .proto файлов:
# These files will be generated when compiling .proto files:
# python -m grpc_tools.protoc --python_out=. --grpc_python_out=. --proto_path=. protos/candidate.proto
import sys
from pathlib import Path

# Добавляем корневую директорию в path для импорта protobuf
# Add root directory to path for protobuf import
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Try to import generated protobuf files
# Пробуем импортировать сгенерированные protobuf файлы
try:
    from protos import candidate_pb2, candidate_pb2_grpc
except ImportError:
    # Если protobuf файлы ещё не сгенерированы, создаём заглушки для типов
    # If protobuf files are not generated yet, create stub types
    class MockCandidateStatus:
        """Mock CandidateStatus enum for development / Заглушка для разработки"""
        ACTIVE = 0
        CONTACTED = 1
        SCREENING = 2
        INTERVIEW = 3
        OFFER = 4
        HIRED = 5
        REJECTED = 6
        WITHDRAWN = 7
        ON_HOLD = 8

    class candidate_pb2:
        """Mock protobuf module for development / Заглушка для разработки"""

        class CandidateNote:
            pass

        class CreateNoteRequest:
            pass

        class CreateNoteResponse:
            pass

        class GetNotesRequest:
            pass

        class GetNotesResponse:
            pass

        class UpdateNoteRequest:
            pass

        class UpdateNoteResponse:
            pass

        class DeleteNoteRequest:
            pass

        class DeleteNoteResponse:
            pass

        class CandidateTag:
            pass

        class CreateTagRequest:
            pass

        class CreateTagResponse:
            pass

        class GetTagsRequest:
            pass

        class GetTagsResponse:
            pass

        class UpdateTagRequest:
            pass

        class UpdateTagResponse:
            pass

        class DeleteTagRequest:
            pass

        class DeleteTagResponse:
            pass

        class AddTagToResumeRequest:
            pass

        class AddTagToResumeResponse:
            pass

        class RemoveTagFromResumeRequest:
            pass

        class RemoveTagFromResumeResponse:
            pass

        class GetResumeTagsRequest:
            pass

        class GetResumeTagsResponse:
            pass

        class CandidateActivity:
            pass

        class LogActivityRequest:
            pass

        class LogActivityResponse:
            pass

        class GetActivitiesRequest:
            pass

        class GetActivitiesResponse:
            pass

        class GetStatusRequest:
            pass

        class GetStatusResponse:
            pass

        class UpdateStatusRequest:
            pass

        class UpdateStatusResponse:
            pass

        class SkillFeedback:
            pass

        class AddFeedbackRequest:
            pass

        class AddFeedbackResponse:
            pass

        class GetFeedbackRequest:
            pass

        class GetFeedbackResponse:
            pass

        CandidateStatus = MockCandidateStatus

    class candidate_pb2_grpc:
        """Mock grpc module for development / Заглушка для разработки"""
        CandidateServiceServicer = object

from database import async_session_maker
from models.candidate import Candidate, CandidateStatus as ModelCandidateStatus
from models.candidate_note import CandidateNote
from models.candidate_tag import CandidateTag
from models.candidate_activity import CandidateActivity, CandidateActivityType

logger = logging.getLogger(__name__)


# Mapping between proto and model CandidateStatus
# Маппинг между proto и моделью CandidateStatus
PROTO_STATUS_TO_MODEL = {
    candidate_pb2.CandidateStatus.ACTIVE: ModelCandidateStatus.NEW,
    candidate_pb2.CandidateStatus.CONTACTED: ModelCandidateStatus.CONTACTED,
    candidate_pb2.CandidateStatus.SCREENING: ModelCandidateStatus.SCREENING,
    candidate_pb2.CandidateStatus.INTERVIEW: ModelCandidateStatus.INTERVIEW,
    candidate_pb2.CandidateStatus.OFFER: ModelCandidateStatus.OFFER,
    candidate_pb2.CandidateStatus.HIRED: ModelCandidateStatus.HIRED,
    candidate_pb2.CandidateStatus.REJECTED: ModelCandidateStatus.REJECTED,
    candidate_pb2.CandidateStatus.WITHDRAWN: ModelCandidateStatus.WITHDRAWN,
    candidate_pb2.CandidateStatus.ON_HOLD: ModelCandidateStatus.ON_HOLD,
}

MODEL_STATUS_TO_PROTO = {
    ModelCandidateStatus.NEW: candidate_pb2.CandidateStatus.ACTIVE,
    ModelCandidateStatus.CONTACTED: candidate_pb2.CandidateStatus.CONTACTED,
    ModelCandidateStatus.SCREENING: candidate_pb2.CandidateStatus.SCREENING,
    ModelCandidateStatus.INTERVIEW: candidate_pb2.CandidateStatus.INTERVIEW,
    ModelCandidateStatus.OFFER: candidate_pb2.CandidateStatus.OFFER,
    ModelCandidateStatus.HIRED: candidate_pb2.CandidateStatus.HIRED,
    ModelCandidateStatus.REJECTED: candidate_pb2.CandidateStatus.REJECTED,
    ModelCandidateStatus.WITHDRAWN: candidate_pb2.CandidateStatus.WITHDRAWN,
    ModelCandidateStatus.ON_HOLD: candidate_pb2.CandidateStatus.ON_HOLD,
}


def _model_note_to_proto(note: CandidateNote) -> candidate_pb2.CandidateNote:
    """
    Конвертировать модель CandidateNote в protobuf сообщение CandidateNote.
    Convert CandidateNote model to protobuf CandidateNote message.

    Args:
        note: Модель SQLAlchemy CandidateNote / SQLAlchemy CandidateNote model

    Returns:
        candidate_pb2.CandidateNote: Protobuf сообщение заметки / Protobuf note message
    """
    proto_note = candidate_pb2.CandidateNote()
    proto_note.id = str(note.id)
    proto_note.resume_id = str(note.candidate_id)
    if note.recruiter_id:
        proto_note.recruiter_id = str(note.recruiter_id)
    proto_note.content = note.content
    proto_note.is_private = note.is_private
    if note.created_at:
        proto_note.created_at = int(note.created_at.timestamp() * 1000)
    if note.updated_at:
        proto_note.updated_at = int(note.updated_at.timestamp() * 1000)
    return proto_note


def _model_tag_to_proto(tag: CandidateTag) -> candidate_pb2.CandidateTag:
    """
    Конвертировать модель CandidateTag в protobuf сообщение CandidateTag.
    Convert CandidateTag model to protobuf CandidateTag message.

    Args:
        tag: Модель SQLAlchemy CandidateTag / SQLAlchemy CandidateTag model

    Returns:
        candidate_pb2.CandidateTag: Protobuf сообщение тега / Protobuf tag message
    """
    proto_tag = candidate_pb2.CandidateTag()
    proto_tag.id = str(tag.id)
    proto_tag.organization_id = tag.organization_id
    proto_tag.tag_name = tag.tag_name
    proto_tag.tag_order = tag.tag_order
    proto_tag.is_default = tag.is_default
    proto_tag.is_active = tag.is_active
    if tag.color:
        proto_tag.color = tag.color
    if tag.description:
        proto_tag.description = tag.description
    if tag.created_at:
        proto_tag.created_at = int(tag.created_at.timestamp() * 1000)
    if tag.updated_at:
        proto_tag.updated_at = int(tag.updated_at.timestamp() * 1000)
    return proto_tag


def _model_activity_to_proto(activity: CandidateActivity) -> candidate_pb2.CandidateActivity:
    """
    Конвертировать модель CandidateActivity в protobuf сообщение CandidateActivity.
    Convert CandidateActivity model to protobuf CandidateActivity message.

    Args:
        activity: Модель SQLAlchemy CandidateActivity / SQLAlchemy CandidateActivity model

    Returns:
        candidate_pb2.CandidateActivity: Protobuf сообщение активности / Protobuf activity message
    """
    proto_activity = candidate_pb2.CandidateActivity()
    proto_activity.id = str(activity.id)
    proto_activity.resume_id = str(activity.candidate_id)
    proto_activity.activity_type = activity.activity_type.value
    if activity.reason:
        proto_activity.description = activity.reason
    if activity.activity_data:
        for key, value in activity.activity_data.items():
            proto_activity.metadata[key] = str(value)
    if activity.recruiter_id:
        proto_activity.recruiter_id = str(activity.recruiter_id)
    if activity.created_at:
        proto_activity.created_at = int(activity.created_at.timestamp() * 1000)
    return proto_activity


class CandidateServiceServicer(candidate_pb2_grpc.CandidateServiceServicer):
    """
    gRPC сервис для управления кандидатами / gRPC service for candidate management

    Этот класс реализует все RPC методы, определённые в candidate.proto.
    Методы работают с базой данных через AsyncSession.

    This class implements all RPC methods defined in candidate.proto.
    Methods work with database through AsyncSession.
    """

    def __init__(self):
        """
        Инициализация сервис-вера.
        Initialize servicer.
        """
        logger.info("CandidateServiceServicer initialized")

    # ==========================================
    # Notes RPC methods / Заметки RPC методы
    # ==========================================

    async def CreateNote(
        self,
        request: candidate_pb2.CreateNoteRequest,
        context: grpc.aio.ServicerContext,
    ) -> candidate_pb2.CreateNoteResponse:
        """
        Создать заметку о кандидате.
        Create candidate note.

        Args:
            request: CreateNoteRequest с данными заметки
                     / CreateNoteRequest with note data
            context: gRPC контекст / gRPC context

        Returns:
            CreateNoteResponse с созданной заметкой
            / CreateNoteResponse with created note
        """
        logger.info(f"CreateNote called: resume_id={request.resume_id}")

        async with async_session_maker() as session:
            try:
                resume_uuid = UUID(request.resume_id)

                # Find candidate by resume_id
                # Найти кандидата по resume_id
                result = await session.execute(
                    select(Candidate).where(Candidate.resume_id == resume_uuid)
                )
                candidate = result.scalar_one_or_none()

                if not candidate:
                    response = candidate_pb2.CreateNoteResponse()
                    response.success = False
                    response.message = "Candidate not found / Кандидат не найден"
                    return response

                recruiter_uuid = UUID(request.recruiter_id) if request.recruiter_id else None

                note = CandidateNote(
                    candidate_id=candidate.id,
                    recruiter_id=recruiter_uuid,
                    content=request.content,
                    is_private=request.is_private,
                )

                session.add(note)
                await session.commit()
                await session.refresh(note)

                # Update cached notes count
                # Обновить кэшированное количество заметок
                await session.execute(
                    update(Candidate)
                    .where(Candidate.id == candidate.id)
                    .values(notes_count=Candidate.notes_count + 1)
                )
                await session.commit()

                response = candidate_pb2.CreateNoteResponse()
                response.note.CopyFrom(_model_note_to_proto(note))
                response.success = True
                response.message = "Note created successfully / Заметка создана успешно"

                logger.info(f"Note created: id={note.id}")
                return response

            except ValueError as e:
                logger.error(f"Invalid UUID: {e}")
                response = candidate_pb2.CreateNoteResponse()
                response.success = False
                response.message = f"Invalid ID format / Неверный формат ID: {str(e)}"
                return response
            except Exception as e:
                logger.error(f"Error creating note: {e}", exc_info=True)
                response = candidate_pb2.CreateNoteResponse()
                response.success = False
                response.message = f"Error: {str(e)}"
                return response

    async def GetNotes(
        self,
        request: candidate_pb2.GetNotesRequest,
        context: grpc.aio.ServicerContext,
    ) -> candidate_pb2.GetNotesResponse:
        """
        Получить заметки о кандидате.
        Get candidate notes.

        Args:
            request: GetNotesRequest с ID резюме и фильтрами
                     / GetNotesRequest with resume ID and filters
            context: gRPC контекст / gRPC context

        Returns:
            GetNotesResponse со списком заметок / GetNotesResponse with notes list
        """
        logger.info(f"GetNotes called: resume_id={request.resume_id}")

        async with async_session_maker() as session:
            try:
                resume_uuid = UUID(request.resume_id)

                # Find candidate by resume_id
                # Найти кандидата по resume_id
                result = await session.execute(
                    select(Candidate).where(Candidate.resume_id == resume_uuid)
                )
                candidate = result.scalar_one_or_none()

                if not candidate:
                    response = candidate_pb2.GetNotesResponse()
                    response.total = 0
                    return response

                # Build query for notes
                # Построить запрос для заметок
                query = select(CandidateNote).where(CandidateNote.candidate_id == candidate.id)

                # Filter private notes if needed
                # Фильтровать приватные заметки при необходимости
                if not request.include_private:
                    query = query.where(CandidateNote.is_private == False)
                elif request.recruiter_id:
                    # Include private notes only for the requesting recruiter
                    # Включить приватные заметки только для запрашивающего рекрутера
                    recruiter_uuid = UUID(request.recruiter_id)
                    query = query.where(
                        or_(
                            CandidateNote.is_private == False,
                            CandidateNote.recruiter_id == recruiter_uuid,
                        )
                    )

                query = query.order_by(CandidateNote.created_at.desc())

                result = await session.execute(query)
                notes = result.scalars().all()

                response = candidate_pb2.GetNotesResponse()
                for note in notes:
                    response.notes.add().CopyFrom(_model_note_to_proto(note))
                response.total = len(notes)

                logger.info(f"GetNotes: returned {len(notes)} notes")
                return response

            except ValueError as e:
                logger.error(f"Invalid UUID: {e}")
                response = candidate_pb2.GetNotesResponse()
                response.total = 0
                return response
            except Exception as e:
                logger.error(f"Error getting notes: {e}", exc_info=True)
                response = candidate_pb2.GetNotesResponse()
                response.total = 0
                return response

    async def UpdateNote(
        self,
        request: candidate_pb2.UpdateNoteRequest,
        context: grpc.aio.ServicerContext,
    ) -> candidate_pb2.UpdateNoteResponse:
        """
        Обновить заметку.
        Update note.

        Args:
            request: UpdateNoteRequest с ID заметки и новыми данными
                     / UpdateNoteRequest with note ID and new data
            context: gRPC контекст / gRPC context

        Returns:
            UpdateNoteResponse с обновленной заметкой
            / UpdateNoteResponse with updated note
        """
        logger.info(f"UpdateNote called: id={request.id}")

        async with async_session_maker() as session:
            try:
                note_uuid = UUID(request.id)

                result = await session.execute(
                    select(CandidateNote).where(CandidateNote.id == note_uuid)
                )
                note = result.scalar_one_or_none()

                if not note:
                    response = candidate_pb2.UpdateNoteResponse()
                    response.success = False
                    response.message = "Note not found / Заметка не найдена"
                    return response

                # Update fields
                # Обновить поля
                if request.content:
                    note.content = request.content
                note.is_private = request.is_private

                await session.commit()
                await session.refresh(note)

                response = candidate_pb2.UpdateNoteResponse()
                response.note.CopyFrom(_model_note_to_proto(note))
                response.success = True
                response.message = "Note updated successfully / Заметка обновлена успешно"

                logger.info(f"Note updated: id={note.id}")
                return response

            except ValueError as e:
                logger.error(f"Invalid UUID: {e}")
                response = candidate_pb2.UpdateNoteResponse()
                response.success = False
                response.message = f"Invalid ID format / Неверный формат ID: {str(e)}"
                return response
            except Exception as e:
                logger.error(f"Error updating note: {e}", exc_info=True)
                response = candidate_pb2.UpdateNoteResponse()
                response.success = False
                response.message = f"Error: {str(e)}"
                return response

    async def DeleteNote(
        self,
        request: candidate_pb2.DeleteNoteRequest,
        context: grpc.aio.ServicerContext,
    ) -> candidate_pb2.DeleteNoteResponse:
        """
        Удалить заметку.
        Delete note.

        Args:
            request: DeleteNoteRequest с ID заметки / DeleteNoteRequest with note ID
            context: gRPC контекст / gRPC context

        Returns:
            DeleteNoteResponse с результатом удаления
            / DeleteNoteResponse with deletion result
        """
        logger.info(f"DeleteNote called: id={request.id}")

        async with async_session_maker() as session:
            try:
                note_uuid = UUID(request.id)

                # Get note to find candidate_id
                # Получить заметку для нахождения candidate_id
                result = await session.execute(
                    select(CandidateNote).where(CandidateNote.id == note_uuid)
                )
                note = result.scalar_one_or_none()

                if not note:
                    response = candidate_pb2.DeleteNoteResponse()
                    response.success = False
                    response.message = "Note not found / Заметка не найдена"
                    return response

                candidate_id = note.candidate_id

                # Delete note
                # Удалить заметку
                await session.execute(
                    delete(CandidateNote).where(CandidateNote.id == note_uuid)
                )

                # Update cached notes count
                # Обновить кэшированное количество заметок
                await session.execute(
                    update(Candidate)
                    .where(Candidate.id == candidate_id)
                    .values(notes_count=max(0, Candidate.notes_count - 1))
                )
                await session.commit()

                response = candidate_pb2.DeleteNoteResponse()
                response.success = True
                response.message = "Note deleted successfully / Заметка удалена успешно"

                logger.info(f"Note deleted: id={request.id}")
                return response

            except ValueError as e:
                logger.error(f"Invalid UUID: {e}")
                response = candidate_pb2.DeleteNoteResponse()
                response.success = False
                response.message = f"Invalid ID format / Неверный формат ID: {str(e)}"
                return response
            except Exception as e:
                logger.error(f"Error deleting note: {e}", exc_info=True)
                response = candidate_pb2.DeleteNoteResponse()
                response.success = False
                response.message = f"Error: {str(e)}"
                return response

    # ==========================================
    # Tags RPC methods / Теги RPC методы
    # ==========================================

    async def CreateTag(
        self,
        request: candidate_pb2.CreateTagRequest,
        context: grpc.aio.ServicerContext,
    ) -> candidate_pb2.CreateTagResponse:
        """
        Создать тег.
        Create tag.

        Args:
            request: CreateTagRequest с данными тега / CreateTagRequest with tag data
            context: gRPC контекст / gRPC context

        Returns:
            CreateTagResponse с созданным тегом / CreateTagResponse with created tag
        """
        logger.info(f"CreateTag called: organization_id={request.organization_id}, tag_name={request.tag_name}")

        async with async_session_maker() as session:
            try:
                tag = CandidateTag(
                    organization_id=request.organization_id,
                    tag_name=request.tag_name,
                    tag_order=request.tag_order if request.tag_order > 0 else 0,
                    is_default=request.is_default,
                    color=request.color if request.color else None,
                    description=request.description if request.description else None,
                )

                session.add(tag)
                await session.commit()
                await session.refresh(tag)

                response = candidate_pb2.CreateTagResponse()
                response.tag.CopyFrom(_model_tag_to_proto(tag))
                response.success = True
                response.message = "Tag created successfully / Тег создан успешно"

                logger.info(f"Tag created: id={tag.id}")
                return response

            except Exception as e:
                logger.error(f"Error creating tag: {e}", exc_info=True)
                response = candidate_pb2.CreateTagResponse()
                response.success = False
                response.message = f"Error: {str(e)}"
                return response

    async def GetTags(
        self,
        request: candidate_pb2.GetTagsRequest,
        context: grpc.aio.ServicerContext,
    ) -> candidate_pb2.GetTagsResponse:
        """
        Получить теги организации.
        Get organization tags.

        Args:
            request: GetTagsRequest с ID организации и фильтрами
                     / GetTagsRequest with organization ID and filters
            context: gRPC контекст / gRPC context

        Returns:
            GetTagsResponse со списком тегов / GetTagsResponse with tags list
        """
        logger.info(f"GetTags called: organization_id={request.organization_id}")

        async with async_session_maker() as session:
            try:
                query = select(CandidateTag).where(
                    CandidateTag.organization_id == request.organization_id
                )

                # Filter inactive tags if needed
                # Фильтровать неактивные теги при необходимости
                if not request.include_inactive:
                    query = query.where(CandidateTag.is_active == True)

                query = query.order_by(CandidateTag.tag_order, CandidateTag.tag_name)

                result = await session.execute(query)
                tags = result.scalars().all()

                response = candidate_pb2.GetTagsResponse()
                for tag in tags:
                    response.tags.add().CopyFrom(_model_tag_to_proto(tag))
                response.total = len(tags)

                logger.info(f"GetTags: returned {len(tags)} tags")
                return response

            except Exception as e:
                logger.error(f"Error getting tags: {e}", exc_info=True)
                response = candidate_pb2.GetTagsResponse()
                response.total = 0
                return response

    async def UpdateTag(
        self,
        request: candidate_pb2.UpdateTagRequest,
        context: grpc.aio.ServicerContext,
    ) -> candidate_pb2.UpdateTagResponse:
        """
        Обновить тег.
        Update tag.

        Args:
            request: UpdateTagRequest с ID тега и новыми данными
                     / UpdateTagRequest with tag ID and new data
            context: gRPC контекст / gRPC context

        Returns:
            UpdateTagResponse с обновленным тегом
            / UpdateTagResponse with updated tag
        """
        logger.info(f"UpdateTag called: id={request.id}")

        async with async_session_maker() as session:
            try:
                tag_uuid = UUID(request.id)

                result = await session.execute(
                    select(CandidateTag).where(CandidateTag.id == tag_uuid)
                )
                tag = result.scalar_one_or_none()

                if not tag:
                    response = candidate_pb2.UpdateTagResponse()
                    response.success = False
                    response.message = "Tag not found / Тег не найден"
                    return response

                # Update fields
                # Обновить поля
                if request.tag_name:
                    tag.tag_name = request.tag_name
                if request.tag_order > 0:
                    tag.tag_order = request.tag_order
                tag.is_active = request.is_active
                if request.color:
                    tag.color = request.color
                if request.description:
                    tag.description = request.description

                await session.commit()
                await session.refresh(tag)

                response = candidate_pb2.UpdateTagResponse()
                response.tag.CopyFrom(_model_tag_to_proto(tag))
                response.success = True
                response.message = "Tag updated successfully / Тег обновлен успешно"

                logger.info(f"Tag updated: id={tag.id}")
                return response

            except ValueError as e:
                logger.error(f"Invalid UUID: {e}")
                response = candidate_pb2.UpdateTagResponse()
                response.success = False
                response.message = f"Invalid ID format / Неверный формат ID: {str(e)}"
                return response
            except Exception as e:
                logger.error(f"Error updating tag: {e}", exc_info=True)
                response = candidate_pb2.UpdateTagResponse()
                response.success = False
                response.message = f"Error: {str(e)}"
                return response

    async def DeleteTag(
        self,
        request: candidate_pb2.DeleteTagRequest,
        context: grpc.aio.ServicerContext,
    ) -> candidate_pb2.DeleteTagResponse:
        """
        Удалить тег.
        Delete tag.

        Args:
            request: DeleteTagRequest с ID тега / DeleteTagRequest with tag ID
            context: gRPC контекст / gRPC context

        Returns:
            DeleteTagResponse с результатом удаления
            / DeleteTagResponse with deletion result
        """
        logger.info(f"DeleteTag called: id={request.id}")

        async with async_session_maker() as session:
            try:
                tag_uuid = UUID(request.id)

                await session.execute(
                    delete(CandidateTag).where(CandidateTag.id == tag_uuid)
                )
                await session.commit()

                response = candidate_pb2.DeleteTagResponse()
                response.success = True
                response.message = "Tag deleted successfully / Тег удален успешно"

                logger.info(f"Tag deleted: id={request.id}")
                return response

            except ValueError as e:
                logger.error(f"Invalid UUID: {e}")
                response = candidate_pb2.DeleteTagResponse()
                response.success = False
                response.message = f"Invalid ID format / Неверный формат ID: {str(e)}"
                return response
            except Exception as e:
                logger.error(f"Error deleting tag: {e}", exc_info=True)
                response = candidate_pb2.DeleteTagResponse()
                response.success = False
                response.message = f"Error: {str(e)}"
                return response

    async def AddTagToResume(
        self,
        request: candidate_pb2.AddTagToResumeRequest,
        context: grpc.aio.ServicerContext,
    ) -> candidate_pb2.AddTagToResumeResponse:
        """
        Добавить тег резюме.
        Add tag to resume.

        Args:
            request: AddTagToResumeRequest с ID резюме и тега
                     / AddTagToResumeRequest with resume ID and tag ID
            context: gRPC контекст / gRPC context

        Returns:
            AddTagToResumeResponse с результатом операции
            / AddTagToResumeResponse with operation result
        """
        logger.info(f"AddTagToResume called: resume_id={request.resume_id}, tag_id={request.tag_id}")

        async with async_session_maker() as session:
            try:
                resume_uuid = UUID(request.resume_id)
                tag_uuid = UUID(request.tag_id)

                # Find candidate by resume_id
                # Найти кандидата по resume_id
                result = await session.execute(
                    select(Candidate).where(Candidate.resume_id == resume_uuid)
                )
                candidate = result.scalar_one_or_none()

                if not candidate:
                    response = candidate_pb2.AddTagToResumeResponse()
                    response.success = False
                    response.message = "Candidate not found / Кандидат не найден"
                    return response

                # Get current tags
                # Получить текущие теги
                tags = candidate.tags if candidate.tags else []
                tag_str = str(tag_uuid)

                if tag_str not in tags:
                    tags.append(tag_str)
                    candidate.tags = tags
                    await session.commit()

                response = candidate_pb2.AddTagToResumeResponse()
                response.success = True
                response.message = "Tag added successfully / Тег добавлен успешно"

                logger.info(f"Tag added to resume: resume_id={request.resume_id}")
                return response

            except ValueError as e:
                logger.error(f"Invalid UUID: {e}")
                response = candidate_pb2.AddTagToResumeResponse()
                response.success = False
                response.message = f"Invalid ID format / Неверный формат ID: {str(e)}"
                return response
            except Exception as e:
                logger.error(f"Error adding tag to resume: {e}", exc_info=True)
                response = candidate_pb2.AddTagToResumeResponse()
                response.success = False
                response.message = f"Error: {str(e)}"
                return response

    async def RemoveTagFromResume(
        self,
        request: candidate_pb2.RemoveTagFromResumeRequest,
        context: grpc.aio.ServicerContext,
    ) -> candidate_pb2.RemoveTagFromResumeResponse:
        """
        Удалить тег резюме.
        Remove tag from resume.

        Args:
            request: RemoveTagFromResumeRequest с ID резюме и тега
                     / RemoveTagFromResumeRequest with resume ID and tag ID
            context: gRPC контекст / gRPC context

        Returns:
            RemoveTagFromResumeResponse с результатом операции
            / RemoveTagFromResumeResponse with operation result
        """
        logger.info(f"RemoveTagFromResume called: resume_id={request.resume_id}, tag_id={request.tag_id}")

        async with async_session_maker() as session:
            try:
                resume_uuid = UUID(request.resume_id)
                tag_uuid = UUID(request.tag_id)

                # Find candidate by resume_id
                # Найти кандидата по resume_id
                result = await session.execute(
                    select(Candidate).where(Candidate.resume_id == resume_uuid)
                )
                candidate = result.scalar_one_or_none()

                if not candidate:
                    response = candidate_pb2.RemoveTagFromResumeResponse()
                    response.success = False
                    response.message = "Candidate not found / Кандидат не найден"
                    return response

                # Get current tags and remove the specified one
                # Получить текущие теги и удалить указанный
                tags = candidate.tags if candidate.tags else []
                tag_str = str(tag_uuid)

                if tag_str in tags:
                    tags.remove(tag_str)
                    candidate.tags = tags
                    await session.commit()

                response = candidate_pb2.RemoveTagFromResumeResponse()
                response.success = True
                response.message = "Tag removed successfully / Тег удален успешно"

                logger.info(f"Tag removed from resume: resume_id={request.resume_id}")
                return response

            except ValueError as e:
                logger.error(f"Invalid UUID: {e}")
                response = candidate_pb2.RemoveTagFromResumeResponse()
                response.success = False
                response.message = f"Invalid ID format / Неверный формат ID: {str(e)}"
                return response
            except Exception as e:
                logger.error(f"Error removing tag from resume: {e}", exc_info=True)
                response = candidate_pb2.RemoveTagFromResumeResponse()
                response.success = False
                response.message = f"Error: {str(e)}"
                return response

    async def GetResumeTags(
        self,
        request: candidate_pb2.GetResumeTagsRequest,
        context: grpc.aio.ServicerContext,
    ) -> candidate_pb2.GetResumeTagsResponse:
        """
        Получить теги резюме.
        Get resume tags.

        Args:
            request: GetResumeTagsRequest с ID резюме
                     / GetResumeTagsRequest with resume ID
            context: gRPC контекст / gRPC context

        Returns:
            GetResumeTagsResponse со списком тегов / GetResumeTagsResponse with tags list
        """
        logger.info(f"GetResumeTags called: resume_id={request.resume_id}")

        async with async_session_maker() as session:
            try:
                resume_uuid = UUID(request.resume_id)

                # Find candidate by resume_id
                # Найти кандидата по resume_id
                result = await session.execute(
                    select(Candidate).where(Candidate.resume_id == resume_uuid)
                )
                candidate = result.scalar_one_or_none()

                response = candidate_pb2.GetResumeTagsResponse()

                if not candidate or not candidate.tags:
                    return response

                # Get tag details for each tag ID
                # Получить детали тега для каждого ID тега
                tag_ids = [UUID(tag_id) for tag_id in candidate.tags]
                result = await session.execute(
                    select(CandidateTag).where(CandidateTag.id.in_(tag_ids))
                )
                tags = result.scalars().all()

                for tag in tags:
                    response.tags.add().CopyFrom(_model_tag_to_proto(tag))

                logger.info(f"GetResumeTags: returned {len(tags)} tags")
                return response

            except ValueError as e:
                logger.error(f"Invalid UUID: {e}")
                return candidate_pb2.GetResumeTagsResponse()
            except Exception as e:
                logger.error(f"Error getting resume tags: {e}", exc_info=True)
                return candidate_pb2.GetResumeTagsResponse()

    # ==========================================
    # Activity RPC methods / Активность RPC методы
    # ==========================================

    async def LogActivity(
        self,
        request: candidate_pb2.LogActivityRequest,
        context: grpc.aio.ServicerContext,
    ) -> candidate_pb2.LogActivityResponse:
        """
        Залогировать активность кандидата.
        Log candidate activity.

        Args:
            request: LogActivityRequest с данными активности
                     / LogActivityRequest with activity data
            context: gRPC контекст / gRPC context

        Returns:
            LogActivityResponse с созданной активностью
            / LogActivityResponse with created activity
        """
        logger.info(f"LogActivity called: resume_id={request.resume_id}, type={request.activity_type}")

        async with async_session_maker() as session:
            try:
                resume_uuid = UUID(request.resume_id)

                # Find candidate by resume_id
                # Найти кандидата по resume_id
                result = await session.execute(
                    select(Candidate).where(Candidate.resume_id == resume_uuid)
                )
                candidate = result.scalar_one_or_none()

                if not candidate:
                    response = candidate_pb2.LogActivityResponse()
                    response.success = False
                    response.message = "Candidate not found / Кандидат не найден"
                    return response

                recruiter_uuid = UUID(request.recruiter_id) if request.recruiter_id else None

                # Convert metadata dict to JSON
                # Конвертировать метаданные в JSON
                metadata = dict(request.metadata) if request.metadata else None

                activity = CandidateActivity(
                    activity_type=CandidateActivityType(request.activity_type),
                    candidate_id=candidate.id,
                    recruiter_id=recruiter_uuid,
                    activity_data=metadata,
                    reason=request.description if request.description else None,
                )

                session.add(activity)
                await session.commit()
                await session.refresh(activity)

                response = candidate_pb2.LogActivityResponse()
                response.activity.CopyFrom(_model_activity_to_proto(activity))
                response.success = True
                response.message = "Activity logged successfully / Активность залогирована успешно"

                logger.info(f"Activity logged: id={activity.id}")
                return response

            except ValueError as e:
                logger.error(f"Invalid value: {e}")
                response = candidate_pb2.LogActivityResponse()
                response.success = False
                response.message = f"Invalid value / Неверное значение: {str(e)}"
                return response
            except Exception as e:
                logger.error(f"Error logging activity: {e}", exc_info=True)
                response = candidate_pb2.LogActivityResponse()
                response.success = False
                response.message = f"Error: {str(e)}"
                return response

    async def GetActivities(
        self,
        request: candidate_pb2.GetActivitiesRequest,
        context: grpc.aio.ServicerContext,
    ) -> candidate_pb2.GetActivitiesResponse:
        """
        Получить активность кандидата.
        Get candidate activities.

        Args:
            request: GetActivitiesRequest с ID резюме и фильтрами
                     / GetActivitiesRequest with resume ID and filters
            context: gRPC контекст / gRPC context

        Returns:
            GetActivitiesResponse со списком активности
            / GetActivitiesResponse with activities list
        """
        logger.info(f"GetActivities called: resume_id={request.resume_id}")

        async with async_session_maker() as session:
            try:
                resume_uuid = UUID(request.resume_id)

                # Find candidate by resume_id
                # Найти кандидата по resume_id
                result = await session.execute(
                    select(Candidate).where(Candidate.resume_id == resume_uuid)
                )
                candidate = result.scalar_one_or_none()

                if not candidate:
                    response = candidate_pb2.GetActivitiesResponse()
                    response.total = 0
                    return response

                # Build query for activities
                # Построить запрос для активности
                query = select(CandidateActivity).where(
                    CandidateActivity.candidate_id == candidate.id
                )

                # Apply filters
                # Применить фильтры
                if request.activity_type:
                    query = query.where(CandidateActivity.activity_type == request.activity_type)

                if request.from_date > 0:
                    from_datetime = datetime.fromtimestamp(request.from_date / 1000)
                    query = query.where(CandidateActivity.created_at >= from_datetime)

                if request.to_date > 0:
                    to_datetime = datetime.fromtimestamp(request.to_date / 1000)
                    query = query.where(CandidateActivity.created_at <= to_datetime)

                # Apply limit
                # Применить лимит
                limit = min(max(1, request.limit), 1000) if request.limit > 0 else 100
                query = query.order_by(CandidateActivity.created_at.desc()).limit(limit)

                result = await session.execute(query)
                activities = result.scalars().all()

                # Get total count
                # Получить общее количество
                count_query = select(CandidateActivity.id).where(
                    CandidateActivity.candidate_id == candidate.id
                )
                count_result = await session.execute(count_query)
                total = len(count_result.all())

                response = candidate_pb2.GetActivitiesResponse()
                for activity in activities:
                    response.activities.add().CopyFrom(_model_activity_to_proto(activity))
                response.total = total

                logger.info(f"GetActivities: returned {len(activities)} activities (total: {total})")
                return response

            except ValueError as e:
                logger.error(f"Invalid value: {e}")
                response = candidate_pb2.GetActivitiesResponse()
                response.total = 0
                return response
            except Exception as e:
                logger.error(f"Error getting activities: {e}", exc_info=True)
                response = candidate_pb2.GetActivitiesResponse()
                response.total = 0
                return response

    # ==========================================
    # Status RPC methods / Статус RPC методы
    # ==========================================

    async def UpdateStatus(
        self,
        request: candidate_pb2.UpdateStatusRequest,
        context: grpc.aio.ServicerContext,
    ) -> candidate_pb2.UpdateStatusResponse:
        """
        Обновить статус кандидата.
        Update candidate status.

        Args:
            request: UpdateStatusRequest с ID резюме и новым статусом
                     / UpdateStatusRequest with resume ID and new status
            context: gRPC контекст / gRPC context

        Returns:
            UpdateStatusResponse с результатом обновления
            / UpdateStatusResponse with update result
        """
        logger.info(f"UpdateStatus called: resume_id={request.resume_id}, status={request.status}")

        async with async_session_maker() as session:
            try:
                resume_uuid = UUID(request.resume_id)

                # Find candidate by resume_id
                # Найти кандидата по resume_id
                result = await session.execute(
                    select(Candidate).where(Candidate.resume_id == resume_uuid)
                )
                candidate = result.scalar_one_or_none()

                if not candidate:
                    response = candidate_pb2.UpdateStatusResponse()
                    response.success = False
                    response.message = "Candidate not found / Кандидат не найден"
                    return response

                # Convert proto status to model status
                # Конвертировать proto статус в статус модели
                new_status = PROTO_STATUS_TO_MODEL.get(request.status)
                if not new_status:
                    response = candidate_pb2.UpdateStatusResponse()
                    response.success = False
                    response.message = f"Invalid status / Неверный статус: {request.status}"
                    return response

                old_status = candidate.status
                candidate.status = new_status

                await session.commit()
                await session.refresh(candidate)

                # Log status change activity
                # Залогировать активность изменения статуса
                recruiter_uuid = UUID(request.recruiter_id) if request.recruiter_id else None
                activity = CandidateActivity(
                    activity_type=CandidateActivityType.STATUS_UPDATED,
                    candidate_id=candidate.id,
                    recruiter_id=recruiter_uuid,
                    from_stage=old_status.value if old_status else None,
                    to_stage=new_status.value,
                    reason=request.reason if request.reason else None,
                )
                session.add(activity)
                await session.commit()

                response = candidate_pb2.UpdateStatusResponse()
                response.success = True
                response.message = "Status updated successfully / Статус обновлен успешно"
                response.current_status = request.status

                logger.info(f"Status updated: resume_id={request.resume_id}, new_status={new_status.value}")
                return response

            except ValueError as e:
                logger.error(f"Invalid value: {e}")
                response = candidate_pb2.UpdateStatusResponse()
                response.success = False
                response.message = f"Invalid value / Неверное значение: {str(e)}"
                return response
            except Exception as e:
                logger.error(f"Error updating status: {e}", exc_info=True)
                response = candidate_pb2.UpdateStatusResponse()
                response.success = False
                response.message = f"Error: {str(e)}"
                return response

    async def GetStatus(
        self,
        request: candidate_pb2.GetStatusRequest,
        context: grpc.aio.ServicerContext,
    ) -> candidate_pb2.GetStatusResponse:
        """
        Получить статус кандидата.
        Get candidate status.

        Args:
            request: GetStatusRequest с ID резюме / GetStatusRequest with resume ID
            context: gRPC контекст / gRPC context

        Returns:
            GetStatusResponse со статусом кандидата / GetStatusResponse with candidate status
        """
        logger.info(f"GetStatus called: resume_id={request.resume_id}")

        async with async_session_maker() as session:
            try:
                resume_uuid = UUID(request.resume_id)

                result = await session.execute(
                    select(Candidate).where(Candidate.resume_id == resume_uuid)
                )
                candidate = result.scalar_one_or_none()

                response = candidate_pb2.GetStatusResponse()
                response.resume_id = request.resume_id

                if candidate:
                    response.status = MODEL_STATUS_TO_PROTO.get(
                        candidate.status, candidate_pb2.CandidateStatus.ACTIVE
                    )
                    if candidate.updated_at:
                        response.updated_at = int(candidate.updated_at.timestamp() * 1000)
                    logger.info(f"Status found: resume_id={request.resume_id}, status={candidate.status.value}")
                else:
                    response.status = candidate_pb2.CandidateStatus.ACTIVE
                    logger.warning(f"Candidate not found: resume_id={request.resume_id}")

                return response

            except ValueError as e:
                logger.error(f"Invalid UUID: {e}")
                response = candidate_pb2.GetStatusResponse()
                response.resume_id = request.resume_id
                response.status = candidate_pb2.CandidateStatus.ACTIVE
                return response
            except Exception as e:
                logger.error(f"Error getting status: {e}", exc_info=True)
                response = candidate_pb2.GetStatusResponse()
                response.resume_id = request.resume_id
                response.status = candidate_pb2.CandidateStatus.ACTIVE
                return response

    # ==========================================
    # Feedback RPC methods / Обратная связь RPC методы
    # ==========================================

    async def AddFeedback(
        self,
        request: candidate_pb2.AddFeedbackRequest,
        context: grpc.aio.ServicerContext,
    ) -> candidate_pb2.AddFeedbackResponse:
        """
        Добавить обратную связь о навыке.
        Add skill feedback.

        Args:
            request: AddFeedbackRequest с данными обратной связи
                     / AddFeedbackRequest with feedback data
            context: gRPC контекст / gRPC context

        Returns:
            AddFeedbackResponse с созданной обратной связью
            / AddFeedbackResponse with created feedback
        """
        logger.info(f"AddFeedback called: resume_id={request.resume_id}, skill={request.skill}")

        # TODO: Implement when SkillFeedback model is available
        # TODO: Реализовать когда модель SkillFeedback будет доступна
        response = candidate_pb2.AddFeedbackResponse()
        response.success = False
        response.message = (
            "Feedback feature not yet implemented / "
            "Функция обратной связи пока не реализована"
        )
        return response

    async def GetFeedback(
        self,
        request: candidate_pb2.GetFeedbackRequest,
        context: grpc.aio.ServicerContext,
    ) -> candidate_pb2.GetFeedbackResponse:
        """
        Получить обратную связь о навыках.
        Get skill feedback.

        Args:
            request: GetFeedbackRequest с ID резюме и фильтрами
                     / GetFeedbackRequest with resume ID and filters
            context: gRPC контекст / gRPC context

        Returns:
            GetFeedbackResponse с обратной связью / GetFeedbackResponse with feedback
        """
        logger.info(f"GetFeedback called: resume_id={request.resume_id}")

        # TODO: Implement when SkillFeedback model is available
        # TODO: Реализовать когда модель SkillFeedback будет доступна
        response = candidate_pb2.GetFeedbackResponse()
        response.total = 0
        return response


async def serve(
    host: str = "0.0.0.0",
    port: int = 50053,
    max_workers: int = 10,
) -> grpc.aio.Server:
    """
    Запустить gRPC сервер для Candidate Service.
    Start gRPC server for Candidate Service.

    Args:
        host: Хост для привязки / Host to bind to
        port: Порт для привязки / Port to bind to
        max_workers: Максимальное количество воркеров / Maximum number of workers

    Returns:
        grpc.aio.Server: Запущенный gRPC сервер / Started gRPC server

    Example:
        >>> server = await serve(host="0.0.0.0", port=50053)
        >>> await server.wait_for_termination()
    """
    server = grpc.aio.server(max_workers)

    # Регистрируем сервис-вер / Register servicer
    candidate_pb2_grpc.add_CandidateServiceServicer_to_server(
        CandidateServiceServicer(), server
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
