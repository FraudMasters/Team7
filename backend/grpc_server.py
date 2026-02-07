"""
gRPC server for resume analysis system.

This module provides a gRPC server implementation alongside the FastAPI REST API.
It implements high-performance RPC services for candidates, vacancies, and resumes.

The gRPC server can run in a separate process or thread alongside FastAPI,
typically on port 50051.

API Authentication:
The gRPC server requires API key authentication for all requests. Clients must
provide their API key in the metadata using the 'x-api-key' key.
"""
import asyncio
import hashlib
import logging
from concurrent import futures
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Try to import gRPC dependencies - handle gracefully if not installed
try:
    import grpc
    from grpc import aio as grpc_aio
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False
    grpc = None
    grpc_aio = None
    logger.warning(
        "gRPC dependencies not installed. "
        "Install with: pip install grpcio grpcio-tools protobuf"
    )

# Try to import generated protobuf modules
try:
    from proto import candidates_pb2
    from proto import candidates_pb2_grpc
    from proto import vacancies_pb2
    from proto import vacancies_pb2_grpc
    from proto import resumes_pb2
    from proto import resumes_pb2_grpc
    PROTO_AVAILABLE = True
except ImportError:
    PROTO_AVAILABLE = False
    candidates_pb2 = None
    candidates_pb2_grpc = None
    vacancies_pb2 = None
    vacancies_pb2_grpc = None
    resumes_pb2 = None
    resumes_pb2_grpc = None
    logger.warning(
        "Proto generated modules not found. "
        "Generate with: python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/*.proto"
    )


# ============================================================================
# API Key Authentication
# ============================================================================

def hash_api_key(api_key: str) -> str:
    """
    Hash an API key using SHA-256 for secure comparison.

    Args:
        api_key: The API key to hash

    Returns:
        The SHA-256 hash of the API key as a hex string

    Example:
        >>> key = "test_key_12345"
        >>> hashed = hash_api_key(key)
        >>> len(hashed)
        64
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


async def verify_api_key(
    api_key: str,
) -> Dict[str, Any]:
    """
    Verify an API key against the database.

    Args:
        api_key: The API key to verify

    Returns:
        Dictionary with:
        - valid: bool indicating if key is valid
        - api_key_id: UUID of the API key (if valid)
        - key_prefix: First 8 characters of the key (if valid)
        - scopes: List of scopes granted to the key (if valid)
        - error: Error message (if invalid)

    Example:
        >>> result = await verify_api_key("abc123...")
        >>> if result["valid"]:
        ...     print(f"Key {result['key_prefix']} is valid")
    """
    from database import get_db
    from sqlalchemy import select
    from models.api_key import APIKey

    try:
        # Hash the provided API key
        key_hash = hash_api_key(api_key)

        # Query for the API key
        async for db in get_db():
            query = select(APIKey).where(APIKey.key_hash == key_hash)
            result = await db.execute(query)
            api_key_obj = result.scalar_one_or_none()

            if api_key_obj is None:
                return {
                    "valid": False,
                    "error": "Invalid API key",
                }

            # Check if key is active and not expired
            if not api_key_obj.is_active:
                return {
                    "valid": False,
                    "error": "API key is inactive",
                }

            if api_key_obj.expires_at and api_key_obj.expires_at < datetime.utcnow():
                return {
                    "valid": False,
                    "error": "API key has expired",
                }

            # Update last_used_at timestamp
            api_key_obj.last_used_at = datetime.utcnow()
            await db.commit()

            return {
                "valid": True,
                "api_key_id": str(api_key_obj.id),
                "key_prefix": api_key_obj.key_prefix,
                "scopes": api_key_obj.scopes,
            }

    except Exception as e:
        logger.error(f"Error verifying API key: {e}", exc_info=True)
        return {
            "valid": False,
            "error": "Error verifying API key",
        }


class AuthInterceptor:
    """
    gRPC server interceptor for API key authentication.

    This interceptor extracts the API key from the call metadata and verifies
    it against the database before allowing the request to proceed.

    Metadata key: 'x-api-key' (case-insensitive)

    Attributes:
        exclude_methods: Set of fully qualified method names to exclude from auth

    Example:
        >>> interceptor = AuthInterceptor()
        >>> server = grpc.aio.server(interceptors=[interceptor])
    """

    def __init__(self, exclude_methods: Optional[set[str]] = None) -> None:
        """
        Initialize the authentication interceptor.

        Args:
            exclude_methods: Set of method names to exclude from authentication
                            Format: "ServiceName/MethodName"
        """
        self.exclude_methods = exclude_methods or set()

    async def _intercept(
        self,
        request: Any,
        context: grpc_aio.ServicerContext,
        handler_name: str,
        handler: Callable,
    ) -> Any:
        """
        Intercept and authenticate incoming RPC calls.

        Args:
            request: The RPC request message
            context: The RPC context
            handler_name: The fully qualified method name
            handler: The RPC handler function

        Returns:
            The RPC response

        Raises:
            grpc.StatusCode.UNAUTHENTICATED: If API key is missing or invalid
        """
        # Check if method should be excluded from authentication
        if handler_name in self.exclude_methods:
            return await handler(request, context)

        # Extract API key from metadata
        metadata_dict = dict(context.invocation_metadata())
        api_key = metadata_dict.get("x-api-key") or metadata_dict.get("X-API-Key")

        if not api_key:
            logger.warning(f"Missing API key for method: {handler_name}")
            await context.abort(
                grpc.StatusCode.UNAUTHENTICATED,
                "Missing API key. Provide 'x-api-key' in metadata.",
            )

        # Verify the API key
        verification_result = await verify_api_key(api_key)

        if not verification_result["valid"]:
            logger.warning(
                f"Invalid API key for method {handler_name}: {verification_result.get('error', 'Unknown error')}"
            )
            await context.abort(
                grpc.StatusCode.UNAUTHENTICATED,
                verification_result.get("error", "Invalid API key"),
            )

        # Log successful authentication
        logger.debug(
            f"Authenticated request for {handler_name} with API key {verification_result['key_prefix']}"
        )

        # Proceed with the request
        return await handler(request, context)

    def intercept_service(
        self,
        continuation: Callable,
        handler_call_details: grpc.HandlerCallDetails,
    ) -> Any:
        """
        Intercept service calls for authentication.

        Args:
            continuation: The continuation function to proceed with the call
            handler_call_details: Details about the RPC call

        Returns:
            The RPC handler with authentication applied
        """
        handler = continuation(handler_call_details)
        method_name = handler_call_details.method

        async def _intercept_handler(request, context):
            return await self._intercept(request, context, method_name, handler)

        return _intercept_handler


# ============================================================================
# Candidate Service Implementation
# ============================================================================

if GRPC_AVAILABLE and PROTO_AVAILABLE:

    class CandidateServicer(candidates_pb2_grpc.CandidateServiceServicer):
        """
        gRPC service implementation for candidate management.

        Provides methods for listing, moving, and managing candidates
        through the hiring pipeline.
        """

        async def ListCandidates(
            self,
            request: candidates_pb2.ListCandidatesRequest,
            context: grpc_aio.ServicerContext,
        ) -> candidates_pb2.ListCandidatesResponse:
            """
            List candidates with optional filters.

            Args:
                request: List candidates request with filters
                context: gRPC context

            Returns:
                ListCandidatesResponse with matching candidates
            """
            from database import get_db
            from api.candidates import get_candidates_list

            try:
                async for db in get_db():
                    # Extract filters from request
                    stage_id = request.stage_id.value if request.stage_id else None
                    vacancy_id = request.vacancy_id.value if request.vacancy_id else None
                    search = request.search.value if request.search else None

                    candidates_data = await get_candidates_list(
                        db=db,
                        stage_id=stage_id,
                        vacancy_id=vacancy_id,
                        search=search,
                        skip=request.skip,
                        limit=request.limit,
                    )

                    # Convert to protobuf response
                    response = candidates_pb2.ListCandidatesResponse()

                    for item in candidates_data:
                        candidate = response.candidates.add()
                        candidate.id = item["id"]
                        candidate.filename = item["filename"]
                        candidate.current_stage = item["current_stage"]
                        candidate.stage_name = item["stage_name"]

                        if item.get("vacancy_id"):
                            candidate.vacancy_id.value = item["vacancy_id"]

                        if item.get("notes"):
                            candidate.notes.value = item["notes"]

                        candidate.notes_count = item.get("notes_count", 0)

                        # Add tags
                        for tag in item.get("tags", []):
                            tag_info = candidate.tags.add()
                            tag_info.id = tag["id"]
                            tag_info.tag_name = tag["tag_name"]
                            tag_info.organization_id = tag["organization_id"]
                            if tag.get("color"):
                                tag_info.color.value = tag["color"]

                        # Add latest activity
                        if item.get("latest_activity"):
                            activity = item["latest_activity"]
                            candidate.latest_activity.activity_type = activity["activity_type"]
                            # TODO: Add timestamp parsing for latest_activity

                    return response

            except Exception as e:
                logger.error(f"Error in ListCandidates: {e}", exc_info=True)
                await context.abort(grpc.StatusCode.INTERNAL, str(e))

        async def GetCandidate(
            self,
            request: candidates_pb2.GetCandidateRequest,
            context: grpc_aio.ServicerContext,
        ) -> candidates_pb2.GetCandidateResponse:
            """
            Get a specific candidate by ID.

            Args:
                request: Get candidate request with candidate_id
                context: gRPC context

            Returns:
                GetCandidateResponse with candidate details
            """
            from database import get_db
            from sqlalchemy import select
            from models.resume import Resume
            from models.hiring_stage import HiringStage, HiringStageName
            from models.workflow_stage_config import WorkflowStageConfig

            try:
                async for db in get_db():
                    # Get resume with hiring stage
                    result = await db.execute(
                        select(Resume, HiringStage, WorkflowStageConfig)
                        .outerjoin(HiringStage, HiringStage.resume_id == Resume.id)
                        .outerjoin(
                            WorkflowStageConfig,
                            (HiringStage.stage_id == WorkflowStageConfig.id) |
                            (HiringStage.stage_name == WorkflowStageConfig.stage_name)
                        )
                        .where(Resume.id == request.candidate_id)
                    )
                    row = result.first()

                    if not row:
                        await context.abort(
                            grpc.StatusCode.NOT_FOUND,
                            f"Candidate {request.candidate_id} not found"
                        )

                    resume, hiring_stage, stage_config = row

                    # Build response
                    response = candidates_pb2.GetCandidateResponse()
                    candidate = response.candidate
                    candidate.id = str(resume.id)
                    candidate.filename = resume.filename

                    if hiring_stage:
                        candidate.current_stage = hiring_stage.stage_name or ""
                        candidate.stage_name = hiring_stage.stage_name or ""

                    if stage_config:
                        candidate.stage_id = str(stage_config.id)
                        candidate.display_name = stage_config.display_name or ""

                    if hiring_stage and hiring_stage.vacancy_id:
                        candidate.vacancy_id.value = str(hiring_stage.vacancy_id)

                    if hiring_stage and hiring_stage.notes:
                        candidate.notes.value = hiring_stage.notes

                    return response

            except Exception as e:
                logger.error(f"Error in GetCandidate: {e}", exc_info=True)
                await context.abort(grpc.StatusCode.INTERNAL, str(e))

        async def MoveCandidate(
            self,
            request: candidates_pb2.MoveCandidateRequest,
            context: grpc_aio.ServicerContext,
        ) -> candidates_pb2.MoveCandidateResponse:
            """
            Move a candidate to a different stage.

            Args:
                request: Move candidate request with candidate_id, stage_id, etc.
                context: gRPC context

            Returns:
                MoveCandidateResponse with result
            """
            from database import get_db
            from api.candidates import move_candidate_internal

            try:
                async for db in get_db():
                    vacancy_id = request.vacancy_id.value if request.vacancy_id else None
                    notes = request.notes.value if request.notes else None

                    result = await move_candidate_internal(
                        db=db,
                        resume_id=request.candidate_id,
                        stage_id=request.stage_id,
                        vacancy_id=vacancy_id,
                        notes=notes,
                    )

                    response = candidates_pb2.MoveCandidateResponse()
                    response.id = str(result["id"])
                    response.resume_id = result["resume_id"]
                    response.previous_stage = result["previous_stage"]
                    response.new_stage = result["new_stage"]
                    response.message = result["message"]

                    return response

            except ValueError as e:
                logger.warning(f"Validation error in MoveCandidate: {e}")
                await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))
            except Exception as e:
                logger.error(f"Error in MoveCandidate: {e}", exc_info=True)
                await context.abort(grpc.StatusCode.INTERNAL, str(e))

        async def BulkMoveCandidates(
            self,
            request: candidates_pb2.BulkMoveCandidatesRequest,
            context: grpc_aio.ServicerContext,
        ) -> candidates_pb2.BulkMoveCandidatesResponse:
            """
            Bulk move multiple candidates to a stage.

            Args:
                request: Bulk move request with resume_ids, stage_id, etc.
                context: gRPC context

            Returns:
                BulkMoveCandidatesResponse with results
            """
            from database import get_db
            from api.candidates import bulk_move_candidates_internal

            try:
                async for db in get_db():
                    vacancy_id = request.vacancy_id.value if request.vacancy_id else None
                    notes = request.notes.value if request.notes else None

                    result = await bulk_move_candidates_internal(
                        db=db,
                        resume_ids=list(request.resume_ids),
                        stage_id=request.stage_id,
                        vacancy_id=vacancy_id,
                        notes=notes,
                    )

                    response = candidates_pb2.BulkMoveCandidatesResponse()
                    response.total_requested = result["total_requested"]
                    response.successful = result["successful"]
                    response.failed = result["failed"]

                    for item_result in result["results"]:
                        result_item = response.results.add()
                        result_item.resume_id = item_result["resume_id"]
                        result_item.success = item_result["success"]
                        result_item.message = item_result["message"]
                        if item_result.get("previous_stage"):
                            result_item.previous_stage.value = item_result["previous_stage"]
                        if item_result.get("new_stage"):
                            result_item.new_stage.value = item_result["new_stage"]

                    return response

            except Exception as e:
                logger.error(f"Error in BulkMoveCandidates: {e}", exc_info=True)
                await context.abort(grpc.StatusCode.INTERNAL, str(e))

        async def GetRankedCandidates(
            self,
            request: candidates_pb2.GetRankedCandidatesRequest,
            context: grpc_aio.ServicerContext,
        ) -> candidates_pb2.GetRankedCandidatesResponse:
            """
            Get ranked candidates for a vacancy.

            Args:
                request: Get ranked candidates request with vacancy_id
                context: gRPC context

            Returns:
                GetRankedCandidatesResponse with ranked candidates
            """
            from database import get_db
            from api.candidates import get_ranked_candidates_internal

            try:
                async for db in get_db():
                    candidates_data = await get_ranked_candidates_internal(
                        db=db,
                        vacancy_id=request.vacancy_id,
                        limit=request.limit,
                    )

                    response = candidates_pb2.GetRankedCandidatesResponse()
                    response.vacancy_id = request.vacancy_id
                    response.total_candidates = candidates_data.get("total_candidates", 0)

                    for item in candidates_data.get("candidates", []):
                        candidate = response.candidates.add()
                        candidate.resume_id = item["resume_id"]
                        candidate.vacancy_id = item["vacancy_id"]
                        candidate.rank_score = item["rank_score"]

                        if item.get("rank_position"):
                            candidate.rank_position.value = item["rank_position"]

                        candidate.recommendation = item["recommendation"]
                        candidate.confidence = item["confidence"]

                        for key, value in item.get("feature_contributions", {}).items():
                            candidate.feature_contributions[key] = value

                    return response

            except Exception as e:
                logger.error(f"Error in GetRankedCandidates: {e}", exc_info=True)
                await context.abort(grpc.StatusCode.INTERNAL, str(e))

        async def GetStageMetrics(
            self,
            request: candidates_pb2.GetStageMetricsRequest,
            context: grpc_aio.ServicerContext,
        ) -> candidates_pb2.GetStageMetricsResponse:
            """
            Get metrics for hiring stages.

            Args:
                request: Get stage metrics request with optional filters
                context: gRPC context

            Returns:
                GetStageMetricsResponse with stage metrics
            """
            from database import get_db
            from api.candidates import get_stage_metrics_internal

            try:
                async for db in get_db():
                    stage_id = request.stage_id.value if request.stage_id else None
                    start_date = request.start_date.value if request.start_date else None
                    end_date = request.end_date.value if request.end_date else None

                    metrics_data = await get_stage_metrics_internal(
                        db=db,
                        stage_id=stage_id,
                        start_date=start_date,
                        end_date=end_date,
                    )

                    response = candidates_pb2.GetStageMetricsResponse()
                    response.total_stages = metrics_data.get("total_stages", 0)

                    for item in metrics_data.get("metrics", []):
                        metric = response.metrics.add()

                        if item.get("stage_id"):
                            metric.stage_id.value = item["stage_id"]

                        metric.stage_name = item["stage_name"]

                        if item.get("display_name"):
                            metric.display_name.value = item["display_name"]

                        # Time metrics
                        time_metrics = item.get("time_metrics", {})
                        metric.time_metrics.average_days = time_metrics.get("average_days", 0.0)
                        metric.time_metrics.median_days = time_metrics.get("median_days", 0.0)
                        metric.time_metrics.min_days = time_metrics.get("min_days", 0.0)
                        metric.time_metrics.max_days = time_metrics.get("max_days", 0.0)
                        metric.time_metrics.candidate_count = time_metrics.get("candidate_count", 0)

                        # Dropoff metrics
                        dropoff = item.get("dropoff_metrics", {})
                        metric.dropoff_metrics.candidates_entered = dropoff.get("candidates_entered", 0)
                        metric.dropoff_metrics.candidates_exited = dropoff.get("candidates_exited", 0)
                        metric.dropoff_metrics.candidates_current = dropoff.get("candidates_current", 0)
                        metric.dropoff_metrics.dropoff_rate = dropoff.get("dropoff_rate", 0.0)

                    return response

            except Exception as e:
                logger.error(f"Error in GetStageMetrics: {e}", exc_info=True)
                await context.abort(grpc.StatusCode.INTERNAL, str(e))

        async def BulkAction(
            self,
            request: candidates_pb2.BulkActionRequest,
            context: grpc_aio.ServicerContext,
        ) -> candidates_pb2.BulkActionResponse:
            """
            Perform bulk action on candidates.

            Args:
                request: Bulk action request with action type and resume_ids
                context: gRPC context

            Returns:
                BulkActionResponse with results
            """
            from database import get_db
            from api.candidates import perform_bulk_action_internal

            try:
                async for db in get_db():
                    # Build request dict
                    request_dict = {
                        "action": candidates_pb2.BulkActionType.Name(request.action),
                        "resume_ids": list(request.resume_ids),
                    }

                    if request.tag_name.value:
                        request_dict["tag_name"] = request.tag_name.value
                    if request.tag_color.value:
                        request_dict["tag_color"] = request.tag_color.value
                    if request.stage_id.value:
                        request_dict["stage_id"] = request.stage_id.value
                    if request.vacancy_id.value:
                        request_dict["vacancy_id"] = request.vacancy_id.value
                    if request.notes.value:
                        request_dict["notes"] = request.notes.value
                    if request.export_format:
                        request_dict["export_format"] = request.export_format

                    result = await perform_bulk_action_internal(db=db, **request_dict)

                    response = candidates_pb2.BulkActionResponse()
                    response.action = request.action
                    response.total_requested = result["total_requested"]
                    response.successful = result["successful"]
                    response.failed = result["failed"]

                    for item_result in result.get("results", []):
                        result_item = response.results.add()
                        result_item.resume_id = item_result["resume_id"]
                        result_item.success = item_result["success"]
                        result_item.message = item_result["message"]

                    return response

            except Exception as e:
                logger.error(f"Error in BulkAction: {e}", exc_info=True)
                await context.abort(grpc.StatusCode.INTERNAL, str(e))


# ============================================================================
# Vacancy Service Implementation
# ============================================================================

    class VacancyServicer(vacancies_pb2_grpc.VacancyServiceServicer):
        """
        gRPC service implementation for vacancy management.

        Provides CRUD operations for job vacancies.
        """

        async def CreateVacancy(
            self,
            request: vacancies_pb2.CreateVacancyRequest,
            context: grpc_aio.ServicerContext,
        ) -> vacancies_pb2.CreateVacancyResponse:
            """
            Create a new vacancy.

            Args:
                request: Create vacancy request
                context: gRPC context

            Returns:
                CreateVacancyResponse with created vacancy
            """
            from database import get_db
            from api.vacancies_db import create_vacancy_internal

            try:
                async for db in get_db():
                    # Build request dict
                    request_dict = {
                        "title": request.title,
                        "description": request.description,
                        "required_skills": list(request.required_skills),
                        "additional_requirements": list(request.additional_requirements),
                    }

                    if request.min_experience_months:
                        request_dict["min_experience_months"] = request.min_experience_months.value
                    if request.industry:
                        request_dict["industry"] = request.industry.value
                    if request.work_format:
                        request_dict["work_format"] = request.work_format.value
                    if request.location:
                        request_dict["location"] = request.location.value
                    if request.salary_min:
                        request_dict["salary_min"] = request.salary_min.value
                    if request.salary_max:
                        request_dict["salary_max"] = request.salary_max.value
                    if request.english_level:
                        request_dict["english_level"] = request.english_level.value
                    if request.employment_type:
                        request_dict["employment_type"] = request.employment_type.value
                    if request.external_id:
                        request_dict["external_id"] = request.external_id.value
                    if request.source:
                        request_dict["source"] = request.source.value

                    vacancy = await create_vacancy_internal(db=db, **request_dict)

                    response = vacancies_pb2.CreateVacancyResponse()
                    _populate_vacancy_proto(response.vacancy, vacancy)

                    return response

            except Exception as e:
                logger.error(f"Error in CreateVacancy: {e}", exc_info=True)
                await context.abort(grpc.StatusCode.INTERNAL, str(e))

        async def ListVacancies(
            self,
            request: vacancies_pb2.ListVacanciesRequest,
            context: grpc_aio.ServicerContext,
        ) -> vacancies_pb2.ListVacanciesResponse:
            """
            List vacancies with optional filters.

            Args:
                request: List vacancies request with filters
                context: gRPC context

            Returns:
                ListVacanciesResponse with vacancies
            """
            from database import get_db
            from api.vacancies_db import list_vacancies_internal

            try:
                async for db in get_db():
                    search = request.search.value if request.search else None
                    industry = request.industry.value if request.industry else None
                    work_format = request.work_format.value if request.work_format else None

                    vacancies_data = await list_vacancies_internal(
                        db=db,
                        search=search,
                        industry=industry,
                        work_format=work_format,
                        skip=request.skip,
                        limit=request.limit,
                    )

                    response = vacancies_pb2.ListVacanciesResponse()
                    response.total_count = vacancies_data.get("total_count", 0)

                    for vacancy in vacancies_data.get("vacancies", []):
                        vacancy_proto = response.vacancies.add()
                        _populate_vacancy_proto(vacancy_proto, vacancy)

                    return response

            except Exception as e:
                logger.error(f"Error in ListVacancies: {e}", exc_info=True)
                await context.abort(grpc.StatusCode.INTERNAL, str(e))

        async def GetVacancy(
            self,
            request: vacancies_pb2.GetVacancyRequest,
            context: grpc_aio.ServicerContext,
        ) -> vacancies_pb2.GetVacancyResponse:
            """
            Get a specific vacancy by ID.

            Args:
                request: Get vacancy request with vacancy_id
                context: gRPC context

            Returns:
                GetVacancyResponse with vacancy details
            """
            from database import get_db
            from api.vacancies_db import get_vacancy_internal

            try:
                async for db in get_db():
                    vacancy = await get_vacancy_internal(
                        db=db,
                        vacancy_id=request.vacancy_id,
                    )

                    response = vacancies_pb2.GetVacancyResponse()
                    _populate_vacancy_proto(response.vacancy, vacancy)

                    return response

            except ValueError as e:
                logger.warning(f"Vacancy not found: {e}")
                await context.abort(grpc.StatusCode.NOT_FOUND, str(e))
            except Exception as e:
                logger.error(f"Error in GetVacancy: {e}", exc_info=True)
                await context.abort(grpc.StatusCode.INTERNAL, str(e))

        async def UpdateVacancy(
            self,
            request: vacancies_pb2.UpdateVacancyRequest,
            context: grpc_aio.ServicerContext,
        ) -> vacancies_pb2.UpdateVacancyResponse:
            """
            Update a vacancy.

            Args:
                request: Update vacancy request
                context: gRPC context

            Returns:
                UpdateVacancyResponse with updated vacancy
            """
            from database import get_db
            from api.vacancies_db import update_vacancy_internal

            try:
                async for db in get_db():
                    # Build request dict
                    request_dict = {"vacancy_id": request.vacancy_id}

                    if request.title:
                        request_dict["title"] = request.title.value
                    if request.description:
                        request_dict["description"] = request.description.value
                    if request.required_skills:
                        request_dict["required_skills"] = list(request.required_skills)
                    if request.min_experience_months:
                        request_dict["min_experience_months"] = request.min_experience_months.value
                    if request.additional_requirements:
                        request_dict["additional_requirements"] = list(request.additional_requirements)
                    if request.industry:
                        request_dict["industry"] = request.industry.value
                    if request.work_format:
                        request_dict["work_format"] = request.work_format.value
                    if request.location:
                        request_dict["location"] = request.location.value
                    if request.salary_min:
                        request_dict["salary_min"] = request.salary_min.value
                    if request.salary_max:
                        request_dict["salary_max"] = request.salary_max.value
                    if request.english_level:
                        request_dict["english_level"] = request.english_level.value
                    if request.employment_type:
                        request_dict["employment_type"] = request.employment_type.value

                    vacancy = await update_vacancy_internal(db=db, **request_dict)

                    response = vacancies_pb2.UpdateVacancyResponse()
                    _populate_vacancy_proto(response.vacancy, vacancy)

                    return response

            except ValueError as e:
                logger.warning(f"Vacancy not found: {e}")
                await context.abort(grpc.StatusCode.NOT_FOUND, str(e))
            except Exception as e:
                logger.error(f"Error in UpdateVacancy: {e}", exc_info=True)
                await context.abort(grpc.StatusCode.INTERNAL, str(e))

        async def DeleteVacancy(
            self,
            request: vacancies_pb2.DeleteVacancyRequest,
            context: grpc_aio.ServicerContext,
        ) -> vacancies_pb2.DeleteVacancyResponse:
            """
            Delete a vacancy.

            Args:
                request: Delete vacancy request with vacancy_id
                context: gRPC context

            Returns:
                DeleteVacancyResponse with success status
            """
            from database import get_db
            from api.vacancies_db import delete_vacancy_internal

            try:
                async for db in get_db():
                    await delete_vacancy_internal(
                        db=db,
                        vacancy_id=request.vacancy_id,
                    )

                    response = vacancies_pb2.DeleteVacancyResponse()
                    response.success = True
                    response.message = f"Vacancy {request.vacancy_id} deleted successfully"

                    return response

            except ValueError as e:
                logger.warning(f"Vacancy not found: {e}")
                await context.abort(grpc.StatusCode.NOT_FOUND, str(e))
            except Exception as e:
                logger.error(f"Error in DeleteVacancy: {e}", exc_info=True)
                await context.abort(grpc.StatusCode.INTERNAL, str(e))


    def _populate_vacancy_proto(vacancy_proto, vacancy_data: dict) -> None:
        """
        Helper function to populate vacancy protobuf from dict.

        Args:
            vacancy_proto: Protobuf vacancy message
            vacancy_data: Dictionary with vacancy data
        """
        vacancy_proto.id = vacancy_data.get("id", "")
        vacancy_proto.title = vacancy_data.get("title", "")
        vacancy_proto.description = vacancy_data.get("description", "")

        for skill in vacancy_data.get("required_skills", []):
            vacancy_proto.required_skills.append(skill)

        if vacancy_data.get("min_experience_months"):
            vacancy_proto.min_experience_months.value = vacancy_data["min_experience_months"]

        for req in vacancy_data.get("additional_requirements", []):
            vacancy_proto.additional_requirements.append(req)

        if vacancy_data.get("industry"):
            vacancy_proto.industry.value = vacancy_data["industry"]
        if vacancy_data.get("work_format"):
            vacancy_proto.work_format.value = vacancy_data["work_format"]
        if vacancy_data.get("location"):
            vacancy_proto.location.value = vacancy_data["location"]
        if vacancy_data.get("salary_min"):
            vacancy_proto.salary_min.value = vacancy_data["salary_min"]
        if vacancy_data.get("salary_max"):
            vacancy_proto.salary_max.value = vacancy_data["salary_max"]
        if vacancy_data.get("english_level"):
            vacancy_proto.english_level.value = vacancy_data["english_level"]
        if vacancy_data.get("employment_type"):
            vacancy_proto.employment_type.value = vacancy_data["employment_type"]
        if vacancy_data.get("external_id"):
            vacancy_proto.external_id.value = vacancy_data["external_id"]
        if vacancy_data.get("source"):
            vacancy_proto.source.value = vacancy_data["source"]


# ============================================================================
# Resume Service Implementation
# ============================================================================

    class ResumeServicer(resumes_pb2_grpc.ResumeServiceServicer):
        """
        gRPC service implementation for resume management.

        Provides methods for uploading, listing, and retrieving resumes.
        """

        async def UploadResume(
            self,
            request: resumes_pb2.UploadResumeRequest,
            context: grpc_aio.ServicerContext,
        ) -> resumes_pb2.UploadResumeResponse:
            """
            Upload a new resume.

            Args:
                request: Upload resume request with file data
                context: gRPC context

            Returns:
                UploadResumeResponse with created resume
            """
            from database import get_db
            from api.resumes import upload_resume_internal
            import io

            try:
                async for db in get_db():
                    # Create file-like object from bytes
                    file_obj = io.BytesIO(request.file_data)
                    file_obj.name = request.filename

                    resume = await upload_resume_internal(
                        db=db,
                        file_obj=file_obj,
                        filename=request.filename,
                        content_type=request.content_type,
                    )

                    response = resumes_pb2.UploadResumeResponse()
                    _populate_resume_proto(response.resume, resume)
                    response.message = f"Resume {request.filename} uploaded successfully"

                    return response

            except Exception as e:
                logger.error(f"Error in UploadResume: {e}", exc_info=True)
                await context.abort(grpc.StatusCode.INTERNAL, str(e))

        async def ListResumes(
            self,
            request: resumes_pb2.ListResumesRequest,
            context: grpc_aio.ServicerContext,
        ) -> resumes_pb2.ListResumesResponse:
            """
            List resumes with optional filters.

            Args:
                request: List resumes request with filters
                context: gRPC context

            Returns:
                ListResumesResponse with resumes
            """
            from database import get_db
            from api.resumes import list_resumes_internal

            try:
                async for db in get_db():
                    status_filter = request.status.value if request.status else None
                    search = request.search.value if request.search else None
                    language = request.language.value if request.language else None

                    resumes_data = await list_resumes_internal(
                        db=db,
                        status=status_filter,
                        search=search,
                        language=language,
                        skip=request.skip,
                        limit=request.limit,
                    )

                    response = resumes_pb2.ListResumesResponse()
                    response.total_count = resumes_data.get("total_count", 0)

                    for resume in resumes_data.get("resumes", []):
                        resume_proto = response.resumes.add()
                        _populate_resume_proto(resume_proto, resume)

                    return response

            except Exception as e:
                logger.error(f"Error in ListResumes: {e}", exc_info=True)
                await context.abort(grpc.StatusCode.INTERNAL, str(e))

        async def GetResume(
            self,
            request: resumes_pb2.GetResumeRequest,
            context: grpc_aio.ServicerContext,
        ) -> resumes_pb2.GetResumeResponse:
            """
            Get a specific resume by ID.

            Args:
                request: Get resume request with resume_id
                context: gRPC context

            Returns:
                GetResumeResponse with resume details
            """
            from database import get_db
            from api.resumes import get_resume_internal

            try:
                async for db in get_db():
                    resume = await get_resume_internal(
                        db=db,
                        resume_id=request.resume_id,
                    )

                    response = resumes_pb2.GetResumeResponse()
                    _populate_resume_proto(response.resume, resume)

                    return response

            except ValueError as e:
                logger.warning(f"Resume not found: {e}")
                await context.abort(grpc.StatusCode.NOT_FOUND, str(e))
            except Exception as e:
                logger.error(f"Error in GetResume: {e}", exc_info=True)
                await context.abort(grpc.StatusCode.INTERNAL, str(e))

        async def GetParsedResume(
            self,
            request: resumes_pb2.GetParsedResumeRequest,
            context: grpc_aio.ServicerContext,
        ) -> resumes_pb2.GetParsedResumeResponse:
            """
            Get parsed resume data.

            Args:
                request: Get parsed resume request with resume_id
                context: gRPC context

            Returns:
                GetParsedResumeResponse with parsed data
            """
            from database import get_db
            from api.resumes import get_parsed_resume_internal

            try:
                async for db in get_db():
                    parsed_data = await get_parsed_resume_internal(
                        db=db,
                        resume_id=request.resume_id,
                    )

                    response = resumes_pb2.GetParsedResumeResponse()
                    _populate_parsed_resume_proto(response.parsed_resume, parsed_data)

                    return response

            except ValueError as e:
                logger.warning(f"Resume not found: {e}")
                await context.abort(grpc.StatusCode.NOT_FOUND, str(e))
            except Exception as e:
                logger.error(f"Error in GetParsedResume: {e}", exc_info=True)
                await context.abort(grpc.StatusCode.INTERNAL, str(e))

        async def DeleteResume(
            self,
            request: resumes_pb2.DeleteResumeRequest,
            context: grpc_aio.ServicerContext,
        ) -> resumes_pb2.DeleteResumeResponse:
            """
            Delete a resume.

            Args:
                request: Delete resume request with resume_id
                context: gRPC context

            Returns:
                DeleteResumeResponse with success status
            """
            from database import get_db
            from api.resumes import delete_resume_internal

            try:
                async for db in get_db():
                    await delete_resume_internal(
                        db=db,
                        resume_id=request.resume_id,
                    )

                    response = resumes_pb2.DeleteResumeResponse()
                    response.success = True
                    response.message = f"Resume {request.resume_id} deleted successfully"

                    return response

            except ValueError as e:
                logger.warning(f"Resume not found: {e}")
                await context.abort(grpc.StatusCode.NOT_FOUND, str(e))
            except Exception as e:
                logger.error(f"Error in DeleteResume: {e}", exc_info=True)
                await context.abort(grpc.StatusCode.INTERNAL, str(e))

        async def SearchResumesBySkills(
            self,
            request: resumes_pb2.SearchResumesBySkillsRequest,
            context: grpc_aio.ServicerContext,
        ) -> resumes_pb2.SearchResumesBySkillsResponse:
            """
            Search resumes by skills.

            Args:
                request: Search resumes request with skills list
                context: gRPC context

            Returns:
                SearchResumesBySkillsResponse with matching resumes
            """
            from database import get_db
            from api.resumes import search_resumes_by_skills_internal

            try:
                async for db in get_db():
                    operator = request.operator.value if request.operator else "or"

                    results = await search_resumes_by_skills_internal(
                        db=db,
                        skills=list(request.skills),
                        operator=operator,
                        skip=request.skip,
                        limit=request.limit,
                    )

                    response = resumes_pb2.SearchResumesBySkillsResponse()
                    response.total_count = results.get("total_count", 0)

                    for resume in results.get("resumes", []):
                        resume_proto = response.resumes.add()
                        _populate_resume_proto(resume_proto, resume)

                    return response

            except Exception as e:
                logger.error(f"Error in SearchResumesBySkills: {e}", exc_info=True)
                await context.abort(grpc.StatusCode.INTERNAL, str(e))

        async def GetResumeWorkExperiences(
            self,
            request: resumes_pb2.GetResumeWorkExperiencesRequest,
            context: grpc_aio.ServicerContext,
        ) -> resumes_pb2.GetResumeWorkExperiencesResponse:
            """
            Get work experiences for a resume.

            Args:
                request: Get work experiences request with resume_id
                context: gRPC context

            Returns:
                GetResumeWorkExperiencesResponse with work experiences
            """
            from database import get_db
            from api.work_experience import get_resume_work_experiences_internal

            try:
                async for db in get_db():
                    experiences = await get_resume_work_experiences_internal(
                        db=db,
                        resume_id=request.resume_id,
                    )

                    response = resumes_pb2.GetResumeWorkExperiencesResponse()

                    for exp in experiences:
                        exp_proto = response.work_experiences.add()
                        exp_proto.id = str(exp.get("id", ""))
                        exp_proto.resume_id = str(exp.get("resume_id", ""))
                        exp_proto.company = exp.get("company", "")
                        exp_proto.title = exp.get("title", "")

                        if exp.get("start_date"):
                            exp_proto.start_date.FromDatetime(exp["start_date"])
                        if exp.get("end_date"):
                            exp_proto.end_date.FromDatetime(exp["end_date"])
                        if exp.get("description"):
                            exp_proto.description.value = exp["description"]
                        if exp.get("confidence_score"):
                            exp_proto.confidence_score.value = exp["confidence_score"]
                        if exp.get("created_at"):
                            exp_proto.created_at.FromDatetime(exp["created_at"])
                        if exp.get("updated_at"):
                            exp_proto.updated_at.FromDatetime(exp["updated_at"])

                    return response

            except Exception as e:
                logger.error(f"Error in GetResumeWorkExperiences: {e}", exc_info=True)
                await context.abort(grpc.StatusCode.INTERNAL, str(e))


    def _populate_resume_proto(resume_proto, resume_data: dict) -> None:
        """
        Helper function to populate resume protobuf from dict.

        Args:
            resume_proto: Protobuf resume message
            resume_data: Dictionary with resume data
        """
        resume_proto.id = resume_data.get("id", "")
        resume_proto.filename = resume_data.get("filename", "")
        resume_proto.file_path = resume_data.get("file_path", "")
        resume_proto.content_type = resume_data.get("content_type", "")

        # Map status string to enum
        status_str = resume_data.get("status", "pending").lower()
        status_map = {
            "pending": resumes_pb2.RESUME_STATUS_PENDING,
            "processing": resumes_pb2.RESUME_STATUS_PROCESSING,
            "completed": resumes_pb2.RESUME_STATUS_COMPLETED,
            "failed": resumes_pb2.RESUME_STATUS_FAILED,
            "new": resumes_pb2.RESUME_STATUS_NEW,
            "reviewed": resumes_pb2.RESUME_STATUS_REVIEWED,
            "interview": resumes_pb2.RESUME_STATUS_INTERVIEW,
            "offered": resumes_pb2.RESUME_STATUS_OFFERED,
            "hired": resumes_pb2.RESUME_STATUS_HIRED,
        }
        resume_proto.status = status_map.get(status_str, resumes_pb2.RESUME_STATUS_PENDING)

        if resume_data.get("created_at"):
            resume_proto.created_at.FromDatetime(resume_data["created_at"])
        if resume_data.get("updated_at"):
            resume_proto.updated_at.FromDatetime(resume_data["updated_at"])
        if resume_data.get("raw_text"):
            resume_proto.raw_text.value = resume_data["raw_text"]
        if resume_data.get("language"):
            resume_proto.language.value = resume_data["language"]
        if resume_data.get("error_message"):
            resume_proto.error_message.value = resume_data["error_message"]


    def _populate_parsed_resume_proto(parsed_proto, parsed_data: dict) -> None:
        """
        Helper function to populate parsed resume protobuf from dict.

        Args:
            parsed_proto: Protobuf parsed resume message
            parsed_data: Dictionary with parsed resume data
        """
        if parsed_data.get("raw_text"):
            parsed_proto.raw_text.value = parsed_data["raw_text"]

        parsed_proto.language = parsed_data.get("language", "en")

        if parsed_data.get("position"):
            parsed_proto.position.value = parsed_data["position"]
        if parsed_data.get("age"):
            parsed_proto.age.value = parsed_data["age"]

        # Skills
        for skill in parsed_data.get("skills", []):
            skill_proto = parsed_proto.skills.add()
            skill_proto.name = skill.get("name", "")
            skill_proto.original_name = skill.get("original_name", skill.get("name", ""))
            if skill.get("category"):
                skill_proto.category.value = skill["category"]
            for variation in skill.get("variations", []):
                skill_proto.variations.append(variation)
            for source in skill.get("sources", []):
                skill_proto.sources.append(source)
            skill_proto.confidence = skill.get("confidence", 0.0)

        # Education
        for edu in parsed_data.get("education", []):
            edu_proto = parsed_proto.education.add()
            if edu.get("degree"):
                edu_proto.degree.value = edu["degree"]
            if edu.get("institution"):
                edu_proto.institution.value = edu["institution"]
            if edu.get("field_of_study"):
                edu_proto.field_of_study.value = edu["field_of_study"]
            if edu.get("start_date"):
                edu_proto.start_date.value = edu["start_date"]
            if edu.get("end_date"):
                edu_proto.end_date.value = edu["end_date"]
            if edu.get("gpa"):
                edu_proto.gpa.value = edu["gpa"]
            if edu.get("description"):
                edu_proto.description.value = edu["description"]

        # Work experience
        for exp in parsed_data.get("work_experience", []):
            exp_proto = parsed_proto.work_experience.add()
            if exp.get("company"):
                exp_proto.company.value = exp["company"]
            if exp.get("position"):
                exp_proto.position.value = exp["position"]
            if exp.get("start_date"):
                exp_proto.start_date.value = exp["start_date"]
            if exp.get("end_date"):
                exp_proto.end_date.value = exp["end_date"]
            if exp.get("duration_months"):
                exp_proto.duration_months.value = exp["duration_months"]
            if exp.get("description"):
                exp_proto.description.value = exp["description"]
            for skill in exp.get("skills", []):
                exp_proto.skills.append(skill)
            if exp.get("location"):
                exp_proto.location.value = exp["location"]

        # Languages
        for lang in parsed_data.get("languages", []):
            lang_proto = parsed_proto.languages.add()
            lang_proto.name = lang.get("name", "")
            if lang.get("proficiency"):
                lang_proto.proficiency.value = lang["proficiency"]
            if lang.get("certification"):
                lang_proto.certification.value = lang["certification"]

        # Experience summary
        summary = parsed_data.get("experience_summary", {})
        if summary:
            parsed_proto.experience_summary.total_months = summary.get("total_months", 0)
            parsed_proto.experience_summary.total_years = summary.get("total_years", 0.0)
            parsed_proto.experience_summary.total_years_formatted = summary.get("total_years_formatted", "")

            for key, value in summary.get("framework_specific", {}).items():
                parsed_proto.experience_summary.framework_specific[key] = value

        # Warnings
        for warning in parsed_data.get("warnings", []):
            parsed_proto.warnings.append(warning)


# ============================================================================
# Server Management
# ============================================================================

class GRPCServer:
    """
    gRPC server manager.

    Manages the lifecycle of the gRPC server, including starting,
    stopping, and graceful shutdown.
    """

    def __init__(self, port: int = 50051):
        """
        Initialize gRPC server.

        Args:
            port: Port to listen on (default: 50051)
        """
        self.port = port
        self.server: Optional[grpc_aio.Server] = None
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """
        Start the gRPC server.

        Creates and starts the async gRPC server with all registered services
        and API key authentication.
        """
        if not GRPC_AVAILABLE:
            logger.warning("gRPC server cannot start: grpc dependencies not installed")
            return

        if not PROTO_AVAILABLE:
            logger.warning("gRPC server cannot start: proto modules not generated")
            return

        logger.info(f"Starting gRPC server on port {self.port}")

        # Create authentication interceptor
        auth_interceptor = AuthInterceptor()

        # Create async server with authentication interceptor
        self.server = grpc_aio.server(
            futures.ThreadPoolExecutor(max_workers=10),
            interceptors=[auth_interceptor],
            options=[
                ("grpc.max_receive_message_length", 128 * 1024 * 1024),  # 128MB
                ("grpc.max_send_message_length", 128 * 1024 * 1024),  # 128MB
                ("grpc.keepalive_time_ms", 10000),  # 10 seconds
                ("grpc.keepalive_timeout_ms", 5000),  # 5 seconds
                ("grpc.keepalive_permit_without_calls", True),
                ("grpc.http2.min_time_between_pings_ms", 10000),  # 10 seconds
                ("grpc.http2.max_pings_without_data", 0),
            ],
        )

        # Register services
        candidates_pb2_grpc.add_CandidateServiceServicer_to_server(
            CandidateServicer(), self.server
        )
        vacancies_pb2_grpc.add_VacancyServiceServicer_to_server(
            VacancyServicer(), self.server
        )
        resumes_pb2_grpc.add_ResumeServiceServicer_to_server(
            ResumeServicer(), self.server
        )

        # Add reflection service (useful for debugging)
        try:
            from grpc_reflection.v1alpha import reflection
            reflection.enable_server_reflection(
                service_names=[
                    candidates_pb2.DESCRIPTOR.services_by_name["CandidateService"].full_name,
                    vacancies_pb2.DESCRIPTOR.services_by_name["VacancyService"].full_name,
                    resumes_pb2.DESCRIPTOR.services_by_name["ResumeService"].full_name,
                    reflection.SERVICE_NAME,
                ],
                server=self.server,
            )
            logger.info("gRPC reflection service enabled")
        except ImportError:
            logger.info("gRPC reflection not available (install grpcio-reflection for debugging)")

        # Bind to port
        listen_addr = f"[::]:{self.port}"
        self.server.add_insecure_port(listen_addr)

        # Start server
        await self.server.start()
        logger.info(f"gRPC server started on {listen_addr} with API key authentication")

    async def stop(self, grace_period: float = 5.0) -> None:
        """
        Stop the gRPC server gracefully.

        Args:
            grace_period: Grace period in seconds for existing RPCs to complete
        """
        if self.server is None:
            return

        logger.info(f"Stopping gRPC server (grace period: {grace_period}s)")
        await self.server.stop(grace_period)
        logger.info("gRPC server stopped")

    async def wait_for_termination(self) -> None:
        """Wait for the gRPC server to terminate."""
        if self.server is None:
            return
        await self.server.wait_for_termination()


# Global server instance
_grpc_server: Optional[GRPCServer] = None


async def serve(port: int = 50051) -> GRPCServer:
    """
    Start the gRPC server.

    This function creates and starts the gRPC server. It's designed to be
    called from main.py to run the gRPC server alongside FastAPI.

    Args:
        port: Port to listen on (default: 50051)

    Returns:
        GRPCServer instance

    Example:
        >>> import asyncio
        >>> from grpc_server import serve
        >>>
        >>> async def main():
        ...     server = await serve(port=50051)
        ...     await server.wait_for_termination()
        >>>
        >>> asyncio.run(main())
    """
    global _grpc_server

    if not GRPC_AVAILABLE:
        logger.warning("gRPC server not available: grpc dependencies not installed")
        logger.warning("Install with: pip install grpcio grpcio-tools protobuf")
        # Return a dummy server that does nothing
        _grpc_server = GRPCServer(port=port)
        return _grpc_server

    if not PROTO_AVAILABLE:
        logger.warning("gRPC server not available: proto modules not generated")
        logger.warning("Generate with: python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/*.proto")
        # Return a dummy server that does nothing
        _grpc_server = GRPCServer(port=port)
        return _grpc_server

    _grpc_server = GRPCServer(port=port)
    await _grpc_server.start()

    return _grpc_server


async def stop_grpc_server(grace_period: float = 5.0) -> None:
    """
    Stop the gRPC server.

    Args:
        grace_period: Grace period in seconds for existing RPCs to complete
    """
    global _grpc_server

    if _grpc_server is not None:
        await _grpc_server.stop(grace_period)
        _grpc_server = None


def get_grpc_server() -> Optional[GRPCServer]:
    """
    Get the global gRPC server instance.

    Returns:
        GRPCServer instance or None if not started
    """
    return _grpc_server


# Allow running the gRPC server standalone
if __name__ == "__main__":
    import sys

    # Configure logging
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    async def main():
        """Run the gRPC server standalone."""
        port = int(sys.argv[1]) if len(sys.argv) > 1 else 50051
        server = await serve(port=port)

        if server.server is None:
            logger.error("Failed to start gRPC server")
            sys.exit(1)

        logger.info("gRPC server running. Press Ctrl+C to stop.")
        await server.wait_for_termination()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server...")
