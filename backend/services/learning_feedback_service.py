"""
Learning feedback service for aggregating corrections and identifying patterns.

This module provides a service layer for processing parsing corrections and
identifying common patterns to improve parser accuracy, enabling:
- Aggregation of corrections into learning feedback
- Pattern identification across multiple corrections
- Confidence scoring based on frequency and consistency
- Tracking of parser improvements over time

The service supports:
- Async database operations with SQLAlchemy
- Comprehensive error handling and logging
- Pattern analysis and classification
- Singleton pattern for service reuse
"""
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from models.parsing_correction import ParsingCorrection
from models.learning_feedback import LearningFeedback

logger = logging.getLogger(__name__)

# Global learning feedback service instance
_learning_feedback_service: Optional["LearningFeedbackService"] = None


class LearningFeedbackService:
    """
    Service for aggregating corrections and identifying patterns for parser improvement.

    This class provides methods for analyzing user corrections to identify common
    parsing errors and generate learning feedback that can be used to improve
    the resume parser's accuracy over time.

    Attributes:
        db_session: SQLAlchemy database session (sync or async)

    Example:
        >>> service = LearningFeedbackService(db_session)
        >>> feedback = await service.process_correction(correction)
        >>> patterns = await service.get_patterns_by_field("skills")
    """

    # Pattern types for classifying learning feedback
    PATTERN_TYPE_EXTRACTION = "extraction"
    PATTERN_TYPE_CLASSIFICATION = "classification"
    PATTERN_TYPE_FORMATTING = "formatting"
    PATTERN_TYPE_MERGE = "merge"
    PATTERN_TYPE_SPLIT = "split"

    # Threshold for minimum corrections before creating a pattern
    MIN_CORRECTIONS_FOR_PATTERN = 3

    # Confidence score thresholds
    CONFIDENCE_HIGH = 0.8
    CONFIDENCE_MEDIUM = 0.5
    CONFIDENCE_LOW = 0.3

    # Maximum number of examples to store per pattern
    MAX_EXAMPLES_PER_PATTERN = 10

    def __init__(self, db_session: Optional[Session] = None) -> None:
        """
        Initialize the learning feedback service.

        Args:
            db_session: SQLAlchemy database session. Can be sync Session
                       or async AsyncSession.
        """
        self.db_session = db_session
        self._is_async = isinstance(db_session, AsyncSession)

        logger.debug(
            f"LearningFeedbackService initialized "
            f"(async_mode={self._is_async})"
        )

    async def process_correction(
        self,
        correction: ParsingCorrection,
        parser_version: Optional[str] = None,
    ) -> Optional[LearningFeedback]:
        """
        Process a single correction and generate/update learning feedback.

        Analyzes the correction to determine if it represents a new pattern
        or contributes to an existing pattern, then creates or updates
        the learning feedback accordingly.

        Args:
            correction: ParsingCorrection record to process
            parser_version: Optional version string of the parser

        Returns:
            Created or updated LearningFeedback record, or None if no pattern

        Example:
            >>> service = LearningFeedbackService(db_session)
            >>> correction = await correction_service.save_correction(...)
            >>> feedback = await service.process_correction(correction)
        """
        if not self.db_session:
            raise ValueError("Database session is required for processing corrections")

        try:
            # Analyze the correction for patterns
            pattern_type, error_pattern, suggestion = self._analyze_correction(correction)

            if not error_pattern:
                logger.debug(
                    f"No significant pattern identified for correction {correction.id}"
                )
                return None

            # Check if a similar pattern already exists
            existing_feedback = await self._find_similar_pattern(
                field_name=correction.field_name,
                error_pattern=error_pattern,
                pattern_type=pattern_type,
            )

            if existing_feedback:
                # Update existing pattern with new example
                return await self._update_pattern(existing_feedback, correction)
            else:
                # Check if we have enough similar corrections to create a pattern
                similar_count = await self._count_similar_corrections(
                    field_name=correction.field_name,
                    reason=correction.reason,
                )

                if similar_count >= self.MIN_CORRECTIONS_FOR_PATTERN:
                    # Create new pattern
                    return await self._create_pattern(
                        correction=correction,
                        error_pattern=error_pattern,
                        suggestion=suggestion,
                        pattern_type=pattern_type,
                        parser_version=parser_version,
                    )
                else:
                    logger.debug(
                        f"Not enough similar corrections ({similar_count}) "
                        f"to create pattern for field '{correction.field_name}'"
                    )
                    return None

        except Exception as e:
            logger.error(
                f"Error processing correction {correction.id}: {e}",
                exc_info=True
            )
            raise

    def _analyze_correction(
        self,
        correction: ParsingCorrection,
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Analyze a correction to identify patterns.

        Determines the pattern type, error pattern description, and
        suggested improvement based on the correction details.

        Args:
            correction: ParsingCorrection record to analyze

        Returns:
            Tuple of (pattern_type, error_pattern, suggestion)
        """
        pattern_type = None
        error_pattern = None
        suggestion = None

        # Determine pattern type based on correction reason
        reason = correction.reason or ""

        if "incorrect" in reason.lower() or "wrong" in reason.lower():
            pattern_type = self.PATTERN_TYPE_CLASSIFICATION
            error_pattern = f"Incorrect {correction.field_name} extracted"
            suggestion = f"Review {correction.field_name} extraction logic"

        elif "missing" in reason.lower():
            pattern_type = self.PATTERN_TYPE_EXTRACTION
            error_pattern = f"Missing {correction.field_name} in extraction"
            suggestion = f"Improve {correction.field_name} detection patterns"

        elif "format" in reason.lower():
            pattern_type = self.PATTERN_TYPE_FORMATTING
            error_pattern = f"Formatting issue with {correction.field_name}"
            suggestion = f"Update {correction.field_name} formatting rules"

        elif "merge" in reason.lower():
            pattern_type = self.PATTERN_TYPE_MERGE
            error_pattern = f"Failed to merge {correction.field_name} entries"
            suggestion = f"Update {correction.field_name} merge logic"

        elif "split" in reason.lower():
            pattern_type = self.PATTERN_TYPE_SPLIT
            error_pattern = f"Failed to split {correction.field_name} entry"
            suggestion = f"Update {correction.field_name} split logic"

        # If no specific pattern identified, create generic one
        if not pattern_type:
            pattern_type = self.PATTERN_TYPE_EXTRACTION
            error_pattern = f"General error with {correction.field_name}"
            suggestion = f"Review {correction.field_name} parsing"

        # Enhance error pattern with original/corrected value analysis
        if correction.original_value and correction.corrected_value:
            original = correction.original_value.get("value", "")
            corrected = correction.corrected_value.get("value", "")

            if original and corrected:
                error_pattern = f"{error_pattern}: '{original}' -> '{corrected}'"

        return pattern_type, error_pattern, suggestion

    async def _find_similar_pattern(
        self,
        field_name: str,
        error_pattern: str,
        pattern_type: str,
    ) -> Optional[LearningFeedback]:
        """
        Find an existing learning feedback with a similar pattern.

        Args:
            field_name: Field name to search for
            error_pattern: Error pattern to match
            pattern_type: Pattern type to match

        Returns:
            Matching LearningFeedback record or None
        """
        try:
            query = select(LearningFeedback).where(
                and_(
                    LearningFeedback.field_name == field_name,
                    LearningFeedback.pattern_type == pattern_type,
                    LearningFeedback.is_applied == False,  # noqa: E712
                )
            )

            if self._is_async:
                result = await self.db_session.execute(query)
            else:
                result = self.db_session.execute(query)

            feedbacks = list(result.scalars().all())

            # Look for similar error pattern (fuzzy match)
            for feedback in feedbacks:
                if feedback.error_pattern and error_pattern in feedback.error_pattern:
                    return feedback

            return None

        except Exception as e:
            logger.error(f"Error finding similar pattern: {e}")
            return None

    async def _count_similar_corrections(
        self,
        field_name: str,
        reason: Optional[str],
    ) -> int:
        """
        Count corrections with similar characteristics.

        Args:
            field_name: Field name to count corrections for
            reason: Optional reason to filter by

        Returns:
            Count of similar corrections
        """
        try:
            query = select(func.count(ParsingCorrection.id)).where(
                ParsingCorrection.field_name == field_name
            )

            if reason:
                query = query.where(ParsingCorrection.reason == reason)

            if self._is_async:
                result = await self.db_session.execute(query)
            else:
                result = self.db_session.execute(query)

            return result.scalar() or 0

        except Exception as e:
            logger.error(f"Error counting similar corrections: {e}")
            return 0

    async def _create_pattern(
        self,
        correction: ParsingCorrection,
        error_pattern: str,
        suggestion: str,
        pattern_type: str,
        parser_version: Optional[str] = None,
    ) -> LearningFeedback:
        """
        Create a new learning feedback pattern.

        Args:
            correction: ParsingCorrection that triggered this pattern
            error_pattern: Description of the error pattern
            suggestion: Suggested improvement
            pattern_type: Type of pattern
            parser_version: Optional parser version

        Returns:
            Created LearningFeedback record
        """
        # Get all similar corrections for examples
        similar_corrections = await self._get_similar_corrections(
            field_name=correction.field_name,
            reason=correction.reason,
            limit=self.MAX_EXAMPLES_PER_PATTERN,
        )

        # Build examples list
        examples = []
        for corr in similar_corrections:
            examples.append({
                "original_value": corr.original_value,
                "corrected_value": corr.corrected_value,
                "reason": corr.reason,
                "created_at": corr.created_at.isoformat() if corr.created_at else None,
            })

        # Calculate initial confidence
        sample_count = len(similar_corrections)
        confidence_score = self._calculate_confidence(sample_count)

        feedback = LearningFeedback(
            correction_id=correction.id,
            field_name=correction.field_name,
            error_pattern=error_pattern,
            suggestion=suggestion,
            pattern_type=pattern_type,
            confidence_score=confidence_score,
            sample_count=sample_count,
            examples=examples,
            parser_version=parser_version,
            is_applied=False,
        )

        if self._is_async:
            self.db_session.add(feedback)
            await self.db_session.flush()
            await self.db_session.refresh(feedback)
        else:
            self.db_session.add(feedback)
            self.db_session.flush()
            self.db_session.refresh(feedback)

        logger.info(
            f"Created learning feedback pattern for field '{correction.field_name}', "
            f"type '{pattern_type}', confidence {confidence_score:.2f}"
        )

        return feedback

    async def _update_pattern(
        self,
        feedback: LearningFeedback,
        correction: ParsingCorrection,
    ) -> LearningFeedback:
        """
        Update an existing learning feedback pattern with a new example.

        Args:
            feedback: Existing LearningFeedback record to update
            correction: New correction to add as an example

        Returns:
            Updated LearningFeedback record
        """
        # Update sample count
        feedback.sample_count = (feedback.sample_count or 0) + 1

        # Recalculate confidence
        feedback.confidence_score = self._calculate_confidence(feedback.sample_count)

        # Add new example if we haven't reached max
        examples = feedback.examples or []
        if len(examples) < self.MAX_EXAMPLES_PER_PATTERN:
            examples.append({
                "original_value": correction.original_value,
                "corrected_value": correction.corrected_value,
                "reason": correction.reason,
                "created_at": correction.created_at.isoformat() if correction.created_at else None,
            })
            feedback.examples = examples

        if self._is_async:
            await self.db_session.flush()
            await self.db_session.refresh(feedback)
        else:
            self.db_session.flush()
            self.db_session.refresh(feedback)

        logger.info(
            f"Updated learning feedback pattern {feedback.id}, "
            f"sample_count={feedback.sample_count}, confidence={feedback.confidence_score:.2f}"
        )

        return feedback

    def _calculate_confidence(self, sample_count: int) -> float:
        """
        Calculate confidence score based on sample count.

        Uses a logarithmic scale that caps at 1.0.

        Args:
            sample_count: Number of samples contributing to this pattern

        Returns:
            Confidence score between 0.0 and 1.0
        """
        if sample_count <= 0:
            return 0.0

        # Logarithmic scale: log2(n) / 10 capped at 1.0
        import math
        confidence = min(1.0, math.log2(sample_count + 1) / 3)

        return round(confidence, 2)

    async def _get_similar_corrections(
        self,
        field_name: str,
        reason: Optional[str],
        limit: int = 10,
    ) -> List[ParsingCorrection]:
        """
        Get corrections similar to the given criteria.

        Args:
            field_name: Field name to filter by
            reason: Optional reason to filter by
            limit: Maximum number of corrections to return

        Returns:
            List of matching ParsingCorrection records
        """
        try:
            query = select(ParsingCorrection).where(
                ParsingCorrection.field_name == field_name
            )

            if reason:
                query = query.where(ParsingCorrection.reason == reason)

            query = query.order_by(ParsingCorrection.created_at.desc()).limit(limit)

            if self._is_async:
                result = await self.db_session.execute(query)
            else:
                result = self.db_session.execute(query)

            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Error getting similar corrections: {e}")
            return []

    async def get_patterns_by_field(
        self,
        field_name: str,
        min_confidence: Optional[float] = None,
        applied_only: bool = False,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[LearningFeedback]:
        """
        Retrieve learning feedback patterns for a specific field.

        Args:
            field_name: Field name to get patterns for
            min_confidence: Optional minimum confidence threshold
            applied_only: If True, only return applied patterns
            limit: Maximum number of patterns to return
            offset: Number of patterns to skip for pagination

        Returns:
            List of LearningFeedback records for the field

        Example:
            >>> service = LearningFeedbackService(db_session)
            >>> patterns = await service.get_patterns_by_field("skills")
            >>> for pattern in patterns:
            ...     print(f"{pattern.error_pattern}: {pattern.confidence_score}")
        """
        if not self.db_session:
            raise ValueError("Database session is required for retrieving patterns")

        try:
            query = select(LearningFeedback).where(
                LearningFeedback.field_name == field_name
            )

            if min_confidence is not None:
                query = query.where(
                    LearningFeedback.confidence_score >= min_confidence
                )

            if applied_only:
                query = query.where(LearningFeedback.is_applied == True)  # noqa: E712

            query = query.order_by(
                LearningFeedback.confidence_score.desc(),
                LearningFeedback.sample_count.desc()
            )

            if offset > 0:
                query = query.offset(offset)

            if limit:
                query = query.limit(limit)

            if self._is_async:
                result = await self.db_session.execute(query)
            else:
                result = self.db_session.execute(query)

            patterns = list(result.scalars().all())

            logger.debug(
                f"Retrieved {len(patterns)} patterns for field '{field_name}'"
            )

            return patterns

        except Exception as e:
            logger.error(
                f"Error retrieving patterns for field '{field_name}': {e}"
            )
            raise

    async def get_pattern_by_id(
        self,
        pattern_id: UUID,
    ) -> Optional[LearningFeedback]:
        """
        Retrieve a specific learning feedback pattern by its ID.

        Args:
            pattern_id: UUID of the pattern to retrieve

        Returns:
            LearningFeedback record or None if not found

        Example:
            >>> service = LearningFeedbackService(db_session)
            >>> pattern = await service.get_pattern_by_id(UUID("xyz-789"))
            >>> if pattern:
            ...     print(f"Pattern: {pattern.error_pattern}")
        """
        if not self.db_session:
            raise ValueError("Database session is required for retrieving patterns")

        try:
            query = select(LearningFeedback).where(
                LearningFeedback.id == pattern_id
            )

            if self._is_async:
                result = await self.db_session.execute(query)
            else:
                result = self.db_session.execute(query)

            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error retrieving pattern {pattern_id}: {e}")
            raise

    async def get_high_confidence_patterns(
        self,
        limit: int = 50,
    ) -> List[LearningFeedback]:
        """
        Retrieve all high-confidence patterns that haven't been applied.

        These are patterns that are ready to be used to improve the parser.

        Args:
            limit: Maximum number of patterns to return

        Returns:
            List of high-confidence LearningFeedback records

        Example:
            >>> service = LearningFeedbackService(db_session)
            >>> patterns = await service.get_high_confidence_patterns()
            >>> print(f"Found {len(patterns)} patterns ready for application")
        """
        if not self.db_session:
            raise ValueError("Database session is required for retrieving patterns")

        try:
            query = select(LearningFeedback).where(
                and_(
                    LearningFeedback.confidence_score >= self.CONFIDENCE_HIGH,
                    LearningFeedback.is_applied == False,  # noqa: E712
                )
            ).order_by(
                LearningFeedback.confidence_score.desc(),
                LearningFeedback.sample_count.desc()
            ).limit(limit)

            if self._is_async:
                result = await self.db_session.execute(query)
            else:
                result = self.db_session.execute(query)

            patterns = list(result.scalars().all())

            logger.debug(
                f"Retrieved {len(patterns)} high-confidence patterns"
            )

            return patterns

        except Exception as e:
            logger.error(f"Error retrieving high-confidence patterns: {e}")
            raise

    async def mark_pattern_applied(
        self,
        pattern_id: UUID,
    ) -> bool:
        """
        Mark a learning feedback pattern as applied to the parser.

        Args:
            pattern_id: UUID of the pattern to mark as applied

        Returns:
            True if successful, False if pattern not found

        Example:
            >>> service = LearningFeedbackService(db_session)
            >>> success = await service.mark_pattern_applied(UUID("xyz-789"))
            >>> print(f"Pattern applied: {success}")
        """
        if not self.db_session:
            raise ValueError("Database session is required for updating patterns")

        try:
            pattern = await self.get_pattern_by_id(pattern_id)

            if not pattern:
                logger.warning(f"Pattern {pattern_id} not found")
                return False

            pattern.is_applied = True

            if self._is_async:
                await self.db_session.flush()
            else:
                self.db_session.flush()

            logger.info(f"Marked pattern {pattern_id} as applied")
            return True

        except Exception as e:
            logger.error(f"Error marking pattern {pattern_id} as applied: {e}")
            raise

    async def get_pattern_summary(
        self,
    ) -> Dict[str, Any]:
        """
        Get a summary of all learning feedback patterns.

        Returns statistics about patterns by field, type, and confidence.

        Returns:
            Dictionary with pattern summary statistics

        Example:
            >>> service = LearningFeedbackService(db_session)
            >>> summary = await service.get_pattern_summary()
            >>> print(f"Total patterns: {summary['total_count']}")
        """
        if not self.db_session:
            raise ValueError("Database session is required for pattern summary")

        try:
            # Get all patterns
            query = select(LearningFeedback)
            if self._is_async:
                result = await self.db_session.execute(query)
            else:
                result = self.db_session.execute(query)

            patterns = list(result.scalars().all())

            # Aggregate statistics
            by_field: Dict[str, int] = defaultdict(int)
            by_type: Dict[str, int] = defaultdict(int)
            by_confidence = {
                "high": 0,
                "medium": 0,
                "low": 0,
            }
            applied_count = 0
            total_samples = 0

            for pattern in patterns:
                by_field[pattern.field_name] += 1

                if pattern.pattern_type:
                    by_type[pattern.pattern_type] += 1

                if pattern.confidence_score:
                    if pattern.confidence_score >= self.CONFIDENCE_HIGH:
                        by_confidence["high"] += 1
                    elif pattern.confidence_score >= self.CONFIDENCE_MEDIUM:
                        by_confidence["medium"] += 1
                    else:
                        by_confidence["low"] += 1

                if pattern.is_applied:
                    applied_count += 1

                if pattern.sample_count:
                    total_samples += pattern.sample_count

            return {
                "total_count": len(patterns),
                "applied_count": applied_count,
                "pending_count": len(patterns) - applied_count,
                "total_samples": total_samples,
                "by_field": dict(by_field),
                "by_type": dict(by_type),
                "by_confidence": by_confidence,
            }

        except Exception as e:
            logger.error(f"Error getting pattern summary: {e}")
            raise

    async def get_recent_patterns(
        self,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> List[LearningFeedback]:
        """
        Retrieve recent learning feedback patterns.

        Args:
            limit: Maximum number of patterns to return (default 100)
            since: Optional datetime to filter patterns after this time

        Returns:
            List of recent LearningFeedback records

        Example:
            >>> service = LearningFeedbackService(db_session)
            >>> patterns = await service.get_recent_patterns(limit=50)
            >>> print(f"Found {len(patterns)} recent patterns")
        """
        if not self.db_session:
            raise ValueError("Database session is required for retrieving patterns")

        try:
            query = select(LearningFeedback)

            if since:
                query = query.where(LearningFeedback.created_at >= since)

            query = query.order_by(
                LearningFeedback.created_at.desc()
            ).limit(limit)

            if self._is_async:
                result = await self.db_session.execute(query)
            else:
                result = self.db_session.execute(query)

            patterns = list(result.scalars().all())

            logger.debug(f"Retrieved {len(patterns)} recent patterns")
            return patterns

        except Exception as e:
            logger.error(f"Error retrieving recent patterns: {e}")
            raise

    async def delete_pattern(
        self,
        pattern_id: UUID,
    ) -> bool:
        """
        Delete a specific learning feedback pattern.

        Args:
            pattern_id: UUID of the pattern to delete

        Returns:
            True if successful, False if pattern not found

        Example:
            >>> service = LearningFeedbackService(db_session)
            >>> deleted = await service.delete_pattern(UUID("xyz-789"))
            >>> print(f"Deleted: {deleted}")
        """
        if not self.db_session:
            raise ValueError("Database session is required for deleting patterns")

        try:
            pattern = await self.get_pattern_by_id(pattern_id)

            if not pattern:
                logger.warning(f"Pattern {pattern_id} not found for deletion")
                return False

            if self._is_async:
                await self.db_session.delete(pattern)
                await self.db_session.flush()
            else:
                self.db_session.delete(pattern)
                self.db_session.flush()

            logger.info(f"Deleted pattern {pattern_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting pattern {pattern_id}: {e}")
            raise

    async def aggregate_field_patterns(
        self,
        field_name: str,
    ) -> List[LearningFeedback]:
        """
        Aggregate all corrections for a field and create/update patterns.

        This is a batch operation that processes all corrections for a field
        and generates learning feedback patterns.

        Args:
            field_name: Field name to aggregate patterns for

        Returns:
            List of created or updated LearningFeedback records

        Example:
            >>> service = LearningFeedbackService(db_session)
            >>> patterns = await service.aggregate_field_patterns("skills")
            >>> print(f"Created/updated {len(patterns)} patterns")
        """
        if not self.db_session:
            raise ValueError("Database session is required for aggregation")

        try:
            # Get all corrections for this field
            query = select(ParsingCorrection).where(
                ParsingCorrection.field_name == field_name
            ).order_by(ParsingCorrection.created_at.asc())

            if self._is_async:
                result = await self.db_session.execute(query)
            else:
                result = self.db_session.execute(query)

            corrections = list(result.scalars().all())

            logger.info(
                f"Aggregating {len(corrections)} corrections for field '{field_name}'"
            )

            # Process each correction
            created_patterns = []
            for correction in corrections:
                try:
                    feedback = await self.process_correction(correction)
                    if feedback:
                        created_patterns.append(feedback)
                except Exception as e:
                    logger.warning(
                        f"Failed to process correction {correction.id}: {e}"
                    )
                    continue

            logger.info(
                f"Created/updated {len(created_patterns)} patterns for field '{field_name}'"
            )

            return created_patterns

        except Exception as e:
            logger.error(
                f"Error aggregating patterns for field '{field_name}': {e}"
            )
            raise


def get_learning_feedback_service(
    db_session: Optional[Session] = None,
) -> LearningFeedbackService:
    """
    Get or create a learning feedback service instance.

    If db_session is provided, returns a new service with that session.
    Otherwise, returns a global instance (which requires session to be set later).

    Args:
        db_session: Optional SQLAlchemy database session

    Returns:
        LearningFeedbackService instance

    Example:
        >>> from database import get_db
        >>> async with get_db() as session:
        ...     service = get_learning_feedback_service(session)
        ...     patterns = await service.get_high_confidence_patterns()
    """
    if db_session:
        return LearningFeedbackService(db_session=db_session)

    global _learning_feedback_service
    if _learning_feedback_service is None:
        _learning_feedback_service = LearningFeedbackService()

    return _learning_feedback_service
