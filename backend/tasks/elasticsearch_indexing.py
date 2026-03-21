"""
Elasticsearch indexing tasks for bulk resume indexing.

This module provides Celery tasks for indexing existing resumes into Elasticsearch
for full-text search capabilities. It handles bulk indexing operations with proper
batching, error handling, and progress tracking.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import async_session_maker
from models import Resume, ResumeAnalysis, ResumeStatus
from services.elasticsearch_service import ElasticsearchService

logger = logging.getLogger(__name__)
settings = get_settings()


@shared_task(
    name="tasks.elasticsearch_indexing.bulk_index_resumes",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def bulk_index_resumes(
    self,
    organization_id: Optional[str] = None,
    batch_size: int = 100,
    resume_status: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Bulk index existing resumes into Elasticsearch.

    This Celery task indexes all resumes (or filtered by organization/status) into
    Elasticsearch for full-text search. It processes resumes in batches to avoid
    memory issues and provides detailed progress tracking.

    Task Workflow:
    1. Query resumes and resume analyses from database
    2. Transform data into Elasticsearch document format
    3. Index documents in batches using bulk API
    4. Track success/failure counts and detailed errors
    5. Return comprehensive indexing statistics

    Args:
        self: Celery task instance (bind=True)
        organization_id: Optional organization ID to filter resumes (default: all)
        batch_size: Number of resumes to process per batch (default: 100)
        resume_status: Optional status filter (e.g., "COMPLETED") (default: all)

    Returns:
        Dictionary containing indexing results:
        - status: Task status (completed/failed/partial)
        - total_resumes: Total number of resumes found
        - batches_processed: Number of batches processed
        - total_indexed: Total successfully indexed
        - total_failed: Total failed to index
        - processing_time_ms: Total processing time
        - errors: List of error details (if any)
        - organization_id: Organization filter (if applied)

    Raises:
        SoftTimeLimitExceeded: If task exceeds soft time limit
        Exception: For database or Elasticsearch errors

    Example:
        >>> # Index all resumes
        >>> result = bulk_index_resumes.delay()
        >>> print(result.get())
        {'status': 'completed', 'total_indexed': 1500, 'total_failed': 0}

        >>> # Index resumes for specific organization
        >>> result = bulk_index_resumes.delay(
        ...     organization_id="org-123",
        ...     batch_size=50
        ... )
        >>> print(result.get())
        {'status': 'completed', 'total_indexed': 250, 'organization_id': 'org-123'}
    """
    import time
    import asyncio
    start_time = time.time()

    logger.info(
        f"Starting bulk indexing of resumes "
        f"(organization_id={organization_id}, batch_size={batch_size}, "
        f"status={resume_status})"
    )

    try:
        # Run async indexing operations in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                _bulk_index_resumes_async(
                    organization_id=organization_id,
                    batch_size=batch_size,
                    resume_status=resume_status,
                )
            )
        finally:
            loop.close()

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(
            f"Bulk indexing completed: {result['total_indexed']} indexed, "
            f"{result['total_failed']} failed in {processing_time}ms"
        )

        result["processing_time_ms"] = processing_time
        return result

    except SoftTimeLimitExceeded:
        logger.error("Bulk indexing task timed out")
        return {
            "status": "failed",
            "error": "Task timed out",
            "processing_time_ms": int((time.time() - start_time) * 1000),
        }

    except Exception as e:
        logger.error(
            f"Failed to bulk index resumes: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=300 * (2 ** self.request.retries))

        return {
            "status": "failed",
            "error": str(e),
            "processing_time_ms": int((time.time() - start_time) * 1000),
        }


@shared_task(
    name="tasks.elasticsearch_indexing.index_single_resume",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def index_single_resume(
    self,
    resume_id: str,
) -> Dict[str, Any]:
    """
    Index a single resume into Elasticsearch.

    This Celery task indexes one resume document into Elasticsearch. It's typically
    triggered after a new resume is uploaded or when a resume is updated.

    Task Workflow:
    1. Retrieve resume and resume analysis from database
    2. Transform data into Elasticsearch document format
    3. Index document into Elasticsearch
    4. Return indexing status

    Args:
        self: Celery task instance (bind=True)
        resume_id: UUID of the resume to index

    Returns:
        Dictionary containing indexing results:
        - resume_id: ID of the indexed resume
        - status: Task status (indexed/failed/skipped)
        - processing_time_ms: Total processing time
        - error: Error message (if failed)

    Raises:
        SoftTimeLimitExceeded: If task exceeds soft time limit
        Exception: For database or Elasticsearch errors

    Example:
        >>> result = index_single_resume.delay(resume_id="uuid-123")
        >>> print(result.get())
        {'resume_id': 'uuid-123', 'status': 'indexed'}
    """
    import time
    import asyncio
    start_time = time.time()

    logger.info(f"Indexing resume {resume_id} into Elasticsearch")

    try:
        # Run async indexing operations in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                _index_single_resume_async(resume_id)
            )
        finally:
            loop.close()

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(
            f"Resume {resume_id} indexing {result['status']} in {processing_time}ms"
        )

        result["processing_time_ms"] = processing_time
        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Resume indexing task timed out for resume_id={resume_id}")
        return {
            "resume_id": resume_id,
            "status": "failed",
            "error": "Task timed out",
            "processing_time_ms": int((time.time() - start_time) * 1000),
        }

    except Exception as e:
        logger.error(
            f"Failed to index resume {resume_id}: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        return {
            "resume_id": resume_id,
            "status": "failed",
            "error": str(e),
            "processing_time_ms": int((time.time() - start_time) * 1000),
        }


async def _bulk_index_resumes_async(
    organization_id: Optional[str] = None,
    batch_size: int = 100,
    resume_status: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Async implementation of bulk resume indexing.

    Args:
        organization_id: Optional organization ID to filter resumes
        batch_size: Number of resumes to process per batch
        resume_status: Optional status filter

    Returns:
        Dictionary with indexing statistics
    """
    total_indexed = 0
    total_failed = 0
    batches_processed = 0
    errors = []

    # Initialize Elasticsearch service
    es_service = ElasticsearchService()
    await es_service.initialize()
    await es_service.ensure_index()

    try:
        async with async_session_maker() as session:
            # Build query for resumes with analyses
            query = (
                select(Resume, ResumeAnalysis)
                .join(ResumeAnalysis, Resume.id == ResumeAnalysis.resume_id)
                .order_by(Resume.created_at)
            )

            # Apply filters
            if organization_id:
                query = query.where(Resume.organization_id == organization_id)

            if resume_status:
                try:
                    status_enum = ResumeStatus(resume_status)
                    query = query.where(Resume.status == status_enum)
                except ValueError:
                    logger.warning(f"Invalid resume status: {resume_status}")

            # Execute query
            result = await session.execute(query)
            rows = result.all()
            total_resumes = len(rows)

            logger.info(f"Found {total_resumes} resumes to index")

            # Process in batches
            for i in range(0, total_resumes, batch_size):
                batch = rows[i:i + batch_size]
                documents = []

                for resume, analysis in batch:
                    try:
                        # Transform resume and analysis into Elasticsearch document
                        doc = _transform_resume_to_document(resume, analysis)
                        documents.append(doc)
                    except Exception as e:
                        logger.error(
                            f"Failed to transform resume {resume.id}: {e}",
                            exc_info=True,
                        )
                        total_failed += 1
                        errors.append({
                            "resume_id": str(resume.id),
                            "error": str(e),
                            "stage": "transformation",
                        })

                # Bulk index the batch
                if documents:
                    try:
                        stats = await es_service.bulk_index(documents, refresh=False)
                        total_indexed += stats["success"]
                        total_failed += stats["failed"]
                        batches_processed += 1

                        logger.info(
                            f"Batch {batches_processed}: indexed {stats['success']}, "
                            f"failed {stats['failed']}"
                        )

                    except Exception as e:
                        logger.error(
                            f"Failed to bulk index batch {batches_processed + 1}: {e}",
                            exc_info=True,
                        )
                        total_failed += len(documents)
                        errors.append({
                            "batch": batches_processed + 1,
                            "error": str(e),
                            "stage": "indexing",
                            "document_count": len(documents),
                        })

            # Refresh index to make documents searchable
            await es_service.refresh_index()

            status = "completed"
            if total_failed > 0:
                status = "partial" if total_indexed > 0 else "failed"

            return {
                "status": status,
                "total_resumes": total_resumes,
                "batches_processed": batches_processed,
                "total_indexed": total_indexed,
                "total_failed": total_failed,
                "errors": errors[:10],  # Limit to first 10 errors
                "organization_id": organization_id,
            }

    finally:
        await es_service.close()


async def _index_single_resume_async(resume_id: str) -> Dict[str, Any]:
    """
    Async implementation of single resume indexing.

    Args:
        resume_id: UUID of the resume to index

    Returns:
        Dictionary with indexing status
    """
    # Initialize Elasticsearch service
    es_service = ElasticsearchService()
    await es_service.initialize()
    await es_service.ensure_index()

    try:
        async with async_session_maker() as session:
            # Query resume with analysis
            query = (
                select(Resume, ResumeAnalysis)
                .join(ResumeAnalysis, Resume.id == ResumeAnalysis.resume_id)
                .where(Resume.id == resume_id)
            )

            result = await session.execute(query)
            row = result.first()

            if not row:
                logger.warning(f"Resume {resume_id} not found or has no analysis")
                return {
                    "resume_id": resume_id,
                    "status": "skipped",
                    "error": "Resume not found or no analysis available",
                }

            resume, analysis = row

            # Transform and index
            doc = _transform_resume_to_document(resume, analysis)
            await es_service.index_resume(resume_id, doc)

            return {
                "resume_id": resume_id,
                "status": "indexed",
            }

    finally:
        await es_service.close()


def _transform_resume_to_document(
    resume: Resume,
    analysis: ResumeAnalysis,
) -> Dict[str, Any]:
    """
    Transform Resume and ResumeAnalysis models into Elasticsearch document.

    Args:
        resume: Resume model instance
        analysis: ResumeAnalysis model instance

    Returns:
        Dictionary in the format expected by Elasticsearch

    Example document format:
        {
            "id": "resume-uuid",
            "resume_id": "resume-uuid",
            "raw_text": "Resume text content...",
            "skills": ["Python", "Django", "PostgreSQL"],
            "experience_years": 5,
            "education": "Bachelor's in Computer Science",
            "location": "San Francisco, CA",
            "languages": ["English", "Spanish"],
            "indexed_at": "2024-03-21T10:30:00"
        }
    """
    # Calculate experience in years from months
    experience_years = 0
    if analysis.total_experience_months:
        experience_years = analysis.total_experience_months // 12

    # Extract location from entities if available
    location = None
    if analysis.entities and isinstance(analysis.entities, dict):
        locations = analysis.entities.get("locations", [])
        if locations and isinstance(locations, list):
            location = locations[0] if locations else None

    # Extract education text
    education = None
    if analysis.education and isinstance(analysis.education, list):
        # Join education entries into a single text field
        education = " | ".join([
            str(edu) if isinstance(edu, str) else str(edu.get("degree", ""))
            for edu in analysis.education
        ])

    # Extract languages
    languages = []
    if analysis.entities and isinstance(analysis.entities, dict):
        languages = analysis.entities.get("languages", [])

    # Build document
    return {
        "id": str(resume.id),
        "resume_id": str(resume.id),
        "raw_text": analysis.raw_text or resume.raw_text or "",
        "skills": analysis.skills or [],
        "experience_years": experience_years,
        "education": education or "",
        "location": location or "",
        "languages": languages if isinstance(languages, list) else [],
        "indexed_at": datetime.utcnow().isoformat(),
    }
