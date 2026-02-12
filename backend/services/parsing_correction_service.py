"""
Parsing correction service for managing user corrections to parsed resume data.

This module provides a service layer for managing parsing corrections, enabling:
- Saving and retrieving user corrections to parsed fields
- Tracking correction history for audit purposes
- Querying corrections by resume, field, or user
- Batch operations for multiple corrections

The service supports:
- Async database operations with SQLAlchemy
- Comprehensive error handling and logging
- Flexible querying with filters
- Singleton pattern for service reuse
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from models.parsing_correction import ParsingCorrection

logger = logging.getLogger(__name__)

# Global parsing correction service instance
_parsing_correction_service: Optional["ParsingCorrectionService"] = None


class ParsingCorrectionService:
    """
    Service for managing parsing corrections to resume data.

    This class provides methods for saving, retrieving, and querying
    parsing corrections made by users to AI-parsed resume fields.

    Attributes:
        db_session: SQLAlchemy database session (sync or async)

    Example:
        >>> service = ParsingCorrectionService(db_session)
        >>> correction = await service.save_correction(
        ...     resume_id="abc-123",
        ...     field_name="position",
        ...     original_value={"value": "Software Engineer"},
        ...     corrected_value={"value": "Senior Software Engineer"},
        ...     reason="position_was_incorrect"
        ... )
    """

    # Valid field names that can be corrected
    VALID_FIELD_NAMES = frozenset([
        "position",
        "skills",
        "education",
        "work_experience",
        "languages",
        "email",
        "phone",
        "name",
        "location",
        "summary",
        "certifications",
        "projects",
    ])

    def __init__(self, db_session: Optional[Session] = None) -> None:
        """
        Initialize the parsing correction service.

        Args:
            db_session: SQLAlchemy database session. Can be sync Session
                       or async AsyncSession.
        """
        self.db_session = db_session
        self._is_async = isinstance(db_session, AsyncSession)

        logger.debug(
            f"ParsingCorrectionService initialized "
            f"(async_mode={self._is_async})"
        )

    def _validate_field_name(self, field_name: str) -> bool:
        """
        Validate that a field name is valid for correction.

        Args:
            field_name: Name of the field to validate

        Returns:
            True if valid, False otherwise
        """
        return field_name in self.VALID_FIELD_NAMES

    async def save_correction(
        self,
        resume_id: UUID,
        field_name: str,
        original_value: Optional[Dict[str, Any]] = None,
        corrected_value: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
        source_text_location: Optional[Dict[str, Any]] = None,
        corrected_by: Optional[UUID] = None,
    ) -> ParsingCorrection:
        """
        Save a new parsing correction.

        Creates a new correction record tracking the change from
        the original AI-parsed value to the user-corrected value.

        Args:
            resume_id: UUID of the resume being corrected
            field_name: Name of the field being corrected (e.g., 'position', 'skills')
            original_value: Original AI-parsed value before correction
            corrected_value: New corrected value from the user
            reason: Optional reason for the correction
            source_text_location: Optional location in source document
            corrected_by: Optional UUID of user who made the correction

        Returns:
            Created ParsingCorrection record

        Raises:
            ValueError: If field_name is invalid or db_session is not set

        Example:
            >>> service = ParsingCorrectionService(db_session)
            >>> correction = await service.save_correction(
            ...     resume_id=UUID("abc-123"),
            ...     field_name="position",
            ...     original_value={"value": "Software Engineer"},
            ...     corrected_value={"value": "Senior Software Engineer"},
            ...     reason="position_was_incorrect"
            ... )
        """
        if not self.db_session:
            raise ValueError("Database session is required for saving corrections")

        if not self._validate_field_name(field_name):
            logger.warning(f"Non-standard field name: {field_name}")

        try:
            correction = ParsingCorrection(
                resume_id=resume_id,
                field_name=field_name,
                original_value=original_value,
                corrected_value=corrected_value,
                reason=reason,
                source_text_location=source_text_location,
                corrected_by=corrected_by,
            )

            if self._is_async:
                self.db_session.add(correction)
                await self.db_session.flush()
                await self.db_session.refresh(correction)
            else:
                self.db_session.add(correction)
                self.db_session.flush()
                self.db_session.refresh(correction)

            logger.info(
                f"Saved parsing correction for resume {resume_id}, "
                f"field '{field_name}'"
            )

            return correction

        except Exception as e:
            logger.error(
                f"Error saving correction for resume {resume_id}, "
                f"field '{field_name}': {e}"
            )
            raise

    async def get_corrections_by_resume(
        self,
        resume_id: UUID,
        field_name: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[ParsingCorrection]:
        """
        Retrieve all corrections for a specific resume.

        Args:
            resume_id: UUID of the resume to get corrections for
            field_name: Optional filter by specific field name
            limit: Maximum number of corrections to return
            offset: Number of corrections to skip for pagination

        Returns:
            List of ParsingCorrection records for the resume

        Example:
            >>> service = ParsingCorrectionService(db_session)
            >>> corrections = await service.get_corrections_by_resume(
            ...     resume_id=UUID("abc-123"),
            ...     field_name="skills"
            ... )
            >>> print(f"Found {len(corrections)} corrections")
        """
        if not self.db_session:
            raise ValueError("Database session is required for retrieving corrections")

        try:
            query = select(ParsingCorrection).where(
                ParsingCorrection.resume_id == resume_id
            )

            if field_name:
                query = query.where(ParsingCorrection.field_name == field_name)

            query = query.order_by(ParsingCorrection.created_at.desc())

            if offset > 0:
                query = query.offset(offset)

            if limit:
                query = query.limit(limit)

            if self._is_async:
                result = await self.db_session.execute(query)
            else:
                result = self.db_session.execute(query)

            corrections = list(result.scalars().all())

            logger.debug(
                f"Retrieved {len(corrections)} corrections for resume {resume_id}"
            )

            return corrections

        except Exception as e:
            logger.error(
                f"Error retrieving corrections for resume {resume_id}: {e}"
            )
            raise

    async def get_correction_by_id(
        self,
        correction_id: UUID,
    ) -> Optional[ParsingCorrection]:
        """
        Retrieve a specific correction by its ID.

        Args:
            correction_id: UUID of the correction to retrieve

        Returns:
            ParsingCorrection record or None if not found

        Example:
            >>> service = ParsingCorrectionService(db_session)
            >>> correction = await service.get_correction_by_id(
            ...     correction_id=UUID("xyz-789")
            ... )
            >>> if correction:
            ...     print(f"Field: {correction.field_name}")
        """
        if not self.db_session:
            raise ValueError("Database session is required for retrieving corrections")

        try:
            query = select(ParsingCorrection).where(
                ParsingCorrection.id == correction_id
            )

            if self._is_async:
                result = await self.db_session.execute(query)
            else:
                result = self.db_session.execute(query)

            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(
                f"Error retrieving correction {correction_id}: {e}"
            )
            raise

    async def get_corrections_by_field(
        self,
        field_name: str,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[ParsingCorrection]:
        """
        Retrieve all corrections for a specific field name across all resumes.

        Useful for identifying common parsing errors and patterns.

        Args:
            field_name: Name of the field to get corrections for
            limit: Maximum number of corrections to return
            offset: Number of corrections to skip for pagination

        Returns:
            List of ParsingCorrection records for the field

        Example:
            >>> service = ParsingCorrectionService(db_session)
            >>> corrections = await service.get_corrections_by_field("position")
            >>> print(f"Found {len(corrections)} position corrections")
        """
        if not self.db_session:
            raise ValueError("Database session is required for retrieving corrections")

        try:
            query = select(ParsingCorrection).where(
                ParsingCorrection.field_name == field_name
            )

            query = query.order_by(ParsingCorrection.created_at.desc())

            if offset > 0:
                query = query.offset(offset)

            if limit:
                query = query.limit(limit)

            if self._is_async:
                result = await self.db_session.execute(query)
            else:
                result = self.db_session.execute(query)

            corrections = list(result.scalars().all())

            logger.debug(
                f"Retrieved {len(corrections)} corrections for field '{field_name}'"
            )

            return corrections

        except Exception as e:
            logger.error(
                f"Error retrieving corrections for field '{field_name}': {e}"
            )
            raise

    async def get_correction_count_by_field(
        self,
        field_name: Optional[str] = None,
    ) -> Dict[str, int]:
        """
        Get count of corrections grouped by field name.

        Useful for analytics and identifying which fields have the most errors.

        Args:
            field_name: Optional specific field to count (if None, counts all fields)

        Returns:
            Dictionary mapping field names to correction counts

        Example:
            >>> service = ParsingCorrectionService(db_session)
            >>> counts = await service.get_correction_count_by_field()
            >>> for field, count in counts.items():
            ...     print(f"{field}: {count} corrections")
        """
        if not self.db_session:
            raise ValueError("Database session is required for counting corrections")

        try:
            if field_name:
                # Count for a specific field
                query = select(func.count(ParsingCorrection.id)).where(
                    ParsingCorrection.field_name == field_name
                )

                if self._is_async:
                    result = await self.db_session.execute(query)
                else:
                    result = self.db_session.execute(query)

                count = result.scalar() or 0
                return {field_name: count}
            else:
                # Count all fields grouped
                query = select(
                    ParsingCorrection.field_name,
                    func.count(ParsingCorrection.id).label("count")
                ).group_by(ParsingCorrection.field_name)

                if self._is_async:
                    result = await self.db_session.execute(query)
                else:
                    result = self.db_session.execute(query)

                return {row.field_name: row.count for row in result.all()}

        except Exception as e:
            logger.error(f"Error counting corrections: {e}")
            raise

    async def get_corrections_by_user(
        self,
        user_id: UUID,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[ParsingCorrection]:
        """
        Retrieve all corrections made by a specific user.

        Args:
            user_id: UUID of the user who made corrections
            limit: Maximum number of corrections to return
            offset: Number of corrections to skip for pagination

        Returns:
            List of ParsingCorrection records made by the user

        Example:
            >>> service = ParsingCorrectionService(db_session)
            >>> corrections = await service.get_corrections_by_user(
            ...     user_id=UUID("user-123")
            ... )
        """
        if not self.db_session:
            raise ValueError("Database session is required for retrieving corrections")

        try:
            query = select(ParsingCorrection).where(
                ParsingCorrection.corrected_by == user_id
            )

            query = query.order_by(ParsingCorrection.created_at.desc())

            if offset > 0:
                query = query.offset(offset)

            if limit:
                query = query.limit(limit)

            if self._is_async:
                result = await self.db_session.execute(query)
            else:
                result = self.db_session.execute(query)

            corrections = list(result.scalars().all())

            logger.debug(
                f"Retrieved {len(corrections)} corrections by user {user_id}"
            )

            return corrections

        except Exception as e:
            logger.error(
                f"Error retrieving corrections by user {user_id}: {e}"
            )
            raise

    async def delete_correction(
        self,
        correction_id: UUID,
    ) -> bool:
        """
        Delete a specific correction by its ID.

        Args:
            correction_id: UUID of the correction to delete

        Returns:
            True if deletion was successful, False if correction not found

        Example:
            >>> service = ParsingCorrectionService(db_session)
            >>> deleted = await service.delete_correction(UUID("xyz-789"))
            >>> print(f"Deleted: {deleted}")
        """
        if not self.db_session:
            raise ValueError("Database session is required for deleting corrections")

        try:
            correction = await self.get_correction_by_id(correction_id)

            if not correction:
                logger.warning(f"Correction {correction_id} not found for deletion")
                return False

            if self._is_async:
                await self.db_session.delete(correction)
                await self.db_session.flush()
            else:
                self.db_session.delete(correction)
                self.db_session.flush()

            logger.info(f"Deleted correction {correction_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting correction {correction_id}: {e}")
            raise

    async def get_recent_corrections(
        self,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> List[ParsingCorrection]:
        """
        Retrieve recent corrections across all resumes.

        Useful for monitoring and analytics dashboards.

        Args:
            limit: Maximum number of corrections to return (default 100)
            since: Optional datetime to filter corrections after this time

        Returns:
            List of recent ParsingCorrection records

        Example:
            >>> service = ParsingCorrectionService(db_session)
            >>> corrections = await service.get_recent_corrections(limit=50)
            >>> print(f"Found {len(corrections)} recent corrections")
        """
        if not self.db_session:
            raise ValueError("Database session is required for retrieving corrections")

        try:
            query = select(ParsingCorrection)

            if since:
                query = query.where(ParsingCorrection.created_at >= since)

            query = query.order_by(ParsingCorrection.created_at.desc()).limit(limit)

            if self._is_async:
                result = await self.db_session.execute(query)
            else:
                result = self.db_session.execute(query)

            corrections = list(result.scalars().all())

            logger.debug(f"Retrieved {len(corrections)} recent corrections")
            return corrections

        except Exception as e:
            logger.error(f"Error retrieving recent corrections: {e}")
            raise


def get_parsing_correction_service(
    db_session: Optional[Session] = None,
) -> ParsingCorrectionService:
    """
    Get or create a parsing correction service instance.

    If db_session is provided, returns a new service with that session.
    Otherwise, returns a global instance (which requires session to be set later).

    Args:
        db_session: Optional SQLAlchemy database session

    Returns:
        ParsingCorrectionService instance

    Example:
        >>> from database import get_db
        >>> async with get_db() as session:
        ...     service = get_parsing_correction_service(session)
        ...     corrections = await service.get_corrections_by_resume(resume_id)
    """
    if db_session:
        return ParsingCorrectionService(db_session=db_session)

    global _parsing_correction_service
    if _parsing_correction_service is None:
        _parsing_correction_service = ParsingCorrectionService()

    return _parsing_correction_service
