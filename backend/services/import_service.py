"""
Import Service for Resume Duplicate Detection and Import Management

This module provides duplicate detection capabilities to prevent importing
the same resume multiple times from job boards.

Features:
- Duplicate detection by external ID and job board
- Duplicate detection by candidate email
- Duplicate detection by candidate name and job title
- Import tracking and management
- Support for multiple job board integrations

The service ensures data integrity by preventing duplicate resume imports
while maintaining traceability of import sources.
"""
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Resume, ImportedResume, JobBoardIntegration

logger = logging.getLogger(__name__)


@dataclass
class DuplicateCheckResult:
    """
    Result of duplicate detection check.

    Attributes:
        is_duplicate: Whether a duplicate was detected
        duplicate_type: Type of duplicate found (external_id, email, name)
        existing_resume_id: ID of the existing duplicate resume
        existing_import_id: ID of the existing import record
        confidence_score: Confidence score of duplicate match (0-1)
        details: Additional details about the duplicate detection
    """

    is_duplicate: bool
    duplicate_type: Optional[str] = None
    existing_resume_id: Optional[str] = None
    existing_import_id: Optional[str] = None
    confidence_score: Optional[float] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class ImportResult:
    """
    Result of resume import operation.

    Attributes:
        success: Whether the import was successful
        resume_id: ID of the created/resolved resume
        import_id: ID of the created import record
        status: Import status (completed, skipped, failed)
        message: Status message or error details
    """

    success: bool
    resume_id: Optional[str] = None
    import_id: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None


class ImportService:
    """
    Service for resume import management and duplicate detection.

    This service provides intelligent duplicate detection using multiple
    strategies to prevent importing the same resume multiple times:
    - Exact match by external ID and job board
    - Exact match by candidate email
    - Fuzzy match by candidate name and job title
    """

    # Duplicate type constants
    DUPLICATE_EXTERNAL_ID = "external_id"
    DUPLICATE_EMAIL = "email"
    DUPLICATE_NAME_TITLE = "name_title"

    def __init__(self, db: AsyncSession):
        """
        Initialize the import service.

        Args:
            db: Database session for executing queries
        """
        self.db = db

    async def check_duplicate(
        self,
        job_board_id: str,
        external_id: Optional[str] = None,
        candidate_email: Optional[str] = None,
        candidate_name: Optional[str] = None,
        job_title: Optional[str] = None,
    ) -> DuplicateCheckResult:
        """
        Check if a resume is a duplicate based on multiple criteria.

        Args:
            job_board_id: UUID of the job board integration
            external_id: External resume ID from job board (optional)
            candidate_email: Candidate email address (optional)
            candidate_name: Candidate full name (optional)
            job_title: Job title from the resume (optional)

        Returns:
            DuplicateCheckResult with duplicate detection information

        Raises:
            ValueError: If job_board_id is invalid
        """
        try:
            logger.info(
                f"Checking for duplicates - job_board_id: {job_board_id}, "
                f"external_id: {external_id}, email: {candidate_email}"
            )

            # Validate job_board_id
            try:
                job_board_uuid = UUID(job_board_id)
            except ValueError as e:
                logger.error(f"Invalid job_board_id format: {job_board_id}")
                raise ValueError(f"Invalid job_board_id format: {job_board_id}") from e

            # Priority 1: Check by external_id + job_board_id (exact match)
            if external_id:
                result = await self._check_by_external_id(job_board_uuid, external_id)
                if result.is_duplicate:
                    logger.info(f"Duplicate found by external_id: {external_id}")
                    return result

            # Priority 2: Check by candidate_email (exact match)
            if candidate_email:
                result = await self._check_by_email(candidate_email)
                if result.is_duplicate:
                    logger.info(f"Duplicate found by email: {candidate_email}")
                    return result

            # Priority 3: Check by candidate_name + job_title (fuzzy match)
            if candidate_name and job_title:
                result = await self._check_by_name_and_title(
                    candidate_name, job_title
                )
                if result.is_duplicate:
                    logger.info(
                        f"Potential duplicate found by name+title: {candidate_name} - {job_title}"
                    )
                    return result

            logger.info("No duplicates found")
            return DuplicateCheckResult(is_duplicate=False)

        except Exception as e:
            logger.error(f"Error during duplicate check: {e}", exc_info=True)
            raise ValueError(f"Duplicate check failed: {str(e)}") from e

    async def _check_by_external_id(
        self, job_board_id: UUID, external_id: str
    ) -> DuplicateCheckResult:
        """
        Check for duplicate by external ID and job board.

        This is the most reliable duplicate detection method as it uses
        the unique identifier from the source system.

        Args:
            job_board_id: UUID of the job board integration
            external_id: External resume ID from job board

        Returns:
            DuplicateCheckResult with detection results
        """
        query = (
            select(ImportedResume)
            .where(
                and_(
                    ImportedResume.job_board_id == job_board_id,
                    ImportedResume.external_id == external_id,
                    ImportedResume.is_active == True,
                )
            )
            .order_by(ImportedResume.created_at.desc())
            .limit(1)
        )

        result = await self.db.execute(query)
        import_record = result.scalar_one_or_none()

        if import_record:
            return DuplicateCheckResult(
                is_duplicate=True,
                duplicate_type=self.DUPLICATE_EXTERNAL_ID,
                existing_resume_id=str(import_record.resume_id),
                existing_import_id=str(import_record.id),
                confidence_score=1.0,
                details={
                    "external_id": external_id,
                    "job_board_id": str(job_board_id),
                    "imported_at": import_record.created_at.isoformat()
                    if import_record.created_at
                    else None,
                },
            )

        return DuplicateCheckResult(is_duplicate=False)

    async def _check_by_email(self, email: str) -> DuplicateCheckResult:
        """
        Check for duplicate by candidate email.

        Email addresses are unique identifiers for candidates. If the same
        email appears in multiple imports, they likely refer to the same person.

        Args:
            email: Candidate email address

        Returns:
            DuplicateCheckResult with detection results
        """
        # Normalize email for comparison
        email_normalized = email.strip().lower()

        query = (
            select(ImportedResume)
            .where(
                and_(
                    func.lower(ImportedResume.candidate_email) == email_normalized,
                    ImportedResume.is_active == True,
                )
            )
            .order_by(ImportedResume.created_at.desc())
            .limit(1)
        )

        result = await self.db.execute(query)
        import_record = result.scalar_one_or_none()

        if import_record:
            return DuplicateCheckResult(
                is_duplicate=True,
                duplicate_type=self.DUPLICATE_EMAIL,
                existing_resume_id=str(import_record.resume_id),
                existing_import_id=str(import_record.id),
                confidence_score=0.95,
                details={
                    "email": email,
                    "candidate_name": import_record.candidate_name,
                    "imported_at": import_record.created_at.isoformat()
                    if import_record.created_at
                    else None,
                },
            )

        return DuplicateCheckResult(is_duplicate=False)

    async def _check_by_name_and_title(
        self, candidate_name: str, job_title: str
    ) -> DuplicateCheckResult:
        """
        Check for duplicate by candidate name and job title (fuzzy match).

        This is a less reliable method but can catch duplicates when
        emails or external IDs are not available.

        Args:
            candidate_name: Candidate full name
            job_title: Job title from resume

        Returns:
            DuplicateCheckResult with detection results
        """
        # Normalize inputs
        name_normalized = candidate_name.strip().lower()
        title_normalized = job_title.strip().lower()

        # Build query with similarity matching
        # Using ILIKE for case-insensitive partial matching
        query = (
            select(ImportedResume)
            .where(
                and_(
                    func.lower(ImportedResume.candidate_name).ilike(f"%{name_normalized}%"),
                    func.lower(ImportedResume.job_title).ilike(f"%{title_normalized}%"),
                    ImportedResume.is_active == True,
                )
            )
            .order_by(ImportedResume.created_at.desc())
            .limit(1)
        )

        result = await self.db.execute(query)
        import_record = result.scalar_one_or_none()

        if import_record:
            # Calculate confidence based on match quality
            confidence = self._calculate_name_similarity(
                name_normalized, import_record.candidate_name or ""
            )

            # Only return as duplicate if confidence is above threshold
            if confidence >= 0.7:
                return DuplicateCheckResult(
                    is_duplicate=True,
                    duplicate_type=self.DUPLICATE_NAME_TITLE,
                    existing_resume_id=str(import_record.resume_id),
                    existing_import_id=str(import_record.id),
                    confidence_score=confidence,
                    details={
                        "candidate_name": candidate_name,
                        "job_title": job_title,
                        "matched_name": import_record.candidate_name,
                        "matched_title": import_record.job_title,
                        "imported_at": import_record.created_at.isoformat()
                        if import_record.created_at
                        else None,
                    },
                )

        return DuplicateCheckResult(is_duplicate=False)

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two names using simple heuristics.

        Args:
            name1: First name (normalized)
            name2: Second name (normalized)

        Returns:
            Similarity score between 0 and 1
        """
        if not name1 or not name2:
            return 0.0

        # Exact match
        if name1 == name2:
            return 1.0

        # Check if one name contains the other
        if name1 in name2 or name2 in name1:
            return 0.85

        # Split into parts and check overlap
        parts1 = set(name1.split())
        parts2 = set(name2.split())

        if not parts1 or not parts2:
            return 0.0

        # Calculate Jaccard similarity
        intersection = len(parts1 & parts2)
        union = len(parts1 | parts2)

        if union == 0:
            return 0.0

        return intersection / union

    async def get_import_stats(
        self, job_board_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about imported resumes.

        Args:
            job_board_id: Optional filter by job board integration

        Returns:
            Dictionary with import statistics
        """
        try:
            # Base query
            query = select(func.count()).select_from(ImportedResume)

            # Apply job board filter if provided
            if job_board_id:
                try:
                    job_board_uuid = UUID(job_board_id)
                    query = query.where(ImportedResume.job_board_id == job_board_uuid)
                except ValueError:
                    logger.warning(f"Invalid job_board_id in stats: {job_board_id}")

            # Get total count
            total_result = await self.db.execute(query)
            total = total_result.scalar() or 0

            # Get count by status
            status_query = select(
                ImportedResume.import_status,
                func.count().label("count"),
            ).group_by(ImportedResume.import_status)

            if job_board_id:
                try:
                    job_board_uuid = UUID(job_board_id)
                    status_query = status_query.where(
                        ImportedResume.job_board_id == job_board_uuid
                    )
                except ValueError:
                    pass

            status_result = await self.db.execute(status_query)
            status_counts = {row.import_status.value: row.count for row in status_result}

            return {
                "total_imports": total,
                "by_status": status_counts,
                "active_imports": status_counts.get("completed", 0)
                + status_counts.get("synced", 0),
            }

        except Exception as e:
            logger.error(f"Error getting import stats: {e}", exc_info=True)
            return {
                "total_imports": 0,
                "by_status": {},
                "active_imports": 0,
            }


# Singleton instance getter for dependency injection
_import_service_instance: Optional[ImportService] = None


def get_import_service(db: AsyncSession) -> ImportService:
    """
    Get or create an ImportService instance.

    This function is designed for use with FastAPI dependency injection.

    Args:
        db: Database session

    Returns:
        ImportService instance

    Example:
        >>> from fastapi import Depends
        >>> from database import get_db
        >>> from services.import_service import get_import_service
        >>>
        >>> @router.post("/import")
        >>> async def import_resume(
        >>>     data: ImportRequest,
        >>>     db: AsyncSession = Depends(get_db),
        >>>     import_service: ImportService = Depends(get_import_service)
        >>> ):
        >>>     duplicate_check = await import_service.check_duplicate(...)
        >>>     return duplicate_check
    """
    return ImportService(db)
