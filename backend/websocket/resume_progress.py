"""
Resume progress updates via WebSocket.

This module provides functionality for broadcasting real-time progress updates
during resume processing operations. It integrates with Celery task progress
tracking and sends formatted WebSocket messages to connected clients.

The module defines the stages of resume processing, progress message formats,
and helper functions for sending updates to specific clients or broadcasting
to all listeners.

Key Features:
- Predefined resume processing stages
- Formatted progress message generation
- Direct messaging to specific clients
- Broadcast capabilities for batch operations
- Integration with Celery task progress tracking

Processing Stages:
1. parsing - Extracting text and metadata from resume file
2. analyzing - Running ML/NLP analysis (keywords, entities, grammar, etc.)
3. ranking - Calculating match scores and rankings
4. complete - Processing finished successfully
5. failed - Processing encountered an error

Example:
    >>> from websocket.resume_progress import send_resume_progress
    >>> # Send progress update for a single resume
    >>> await send_resume_progress(
    ...     task_id="abc-123",
    ...     resume_id="resume-456",
    ...     stage=ResumeProgressStage.ANALYZING,
    ...     progress=50,
    ...     message="Extracting keywords..."
    ... )
    >>> # Broadcast batch progress
    >>> await broadcast_resume_progress(
    ...     task_id="batch-789",
    ...     current=5,
    ...     total=10,
    ...     message="Processing batch..."
    ... )
"""
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from websocket.manager import get_manager

logger = logging.getLogger(__name__)


class ResumeProgressStage(str, Enum):
    """
    Resume processing stages for progress tracking.

    Each stage represents a distinct phase in the resume processing pipeline,
    allowing granular progress reporting to connected clients.

    Attributes:
        PARSING: Initial file parsing and text extraction
        ANALYZING: ML/NLP analysis (keywords, entities, grammar, experience)
        RANKING: Match score calculation and candidate ranking
        COMPLETE: Processing finished successfully
        FAILED: Processing encountered an error

    Example:
        >>> stage = ResumeProgressStage.ANALYZING
        >>> print(stage.value)  # "analyzing"
    """

    PARSING = "parsing"
    ANALYZING = "analyzing"
    RANKING = "ranking"
    COMPLETE = "complete"
    FAILED = "failed"


class ProgressMessage:
    """
    Formatted progress message for WebSocket transmission.

    This class provides a structured format for progress messages that
    are sent to clients via WebSocket. All messages include a timestamp,
    message type, and relevant progress data.

    Attributes:
        type: Message type identifier (e.g., "resume_progress", "batch_progress")
        timestamp: ISO format timestamp of message creation
        task_id: Unique identifier for the processing task
        resume_id: Resume identifier (optional for batch operations)
        stage: Current processing stage
        progress: Current progress percentage (0-100)
        message: Human-readable progress message
        metadata: Additional context-specific data

    Example:
        >>> msg = ProgressMessage.create(
        ...     task_id="task-123",
        ...     resume_id="resume-456",
        ...     stage=ResumeProgressStage.ANALYZING,
        ...     progress=50,
        ...     message="Extracting keywords..."
        ... )
        >>> await websocket.send_json(msg)
    """

    @staticmethod
    def create(
        task_id: str,
        stage: ResumeProgressStage,
        progress: int,
        message: str,
        resume_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        msg_type: str = "resume_progress",
    ) -> Dict[str, Any]:
        """
        Create a formatted progress message.

        Args:
            task_id: Unique identifier for the processing task
            stage: Current processing stage
            progress: Current progress percentage (0-100)
            message: Human-readable progress message
            resume_id: Optional resume identifier
            metadata: Optional additional context data
            msg_type: Message type identifier (default: "resume_progress")

        Returns:
            Formatted message dictionary ready for WebSocket transmission

        Example:
            >>> msg = ProgressMessage.create(
            ...     task_id="task-123",
            ...     stage=ResumeProgressStage.ANALYZING,
            ...     progress=50,
            ...     message="Processing..."
            ... )
        """
        msg: Dict[str, Any] = {
            "type": msg_type,
            "timestamp": datetime.utcnow().isoformat(),
            "task_id": task_id,
            "stage": stage.value,
            "progress": max(0, min(100, progress)),  # Clamp to 0-100
            "message": message,
        }

        if resume_id:
            msg["resume_id"] = resume_id

        if metadata:
            msg["metadata"] = metadata

        return msg

    @staticmethod
    def create_complete(
        task_id: str,
        resume_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a completion message.

        Args:
            task_id: Unique identifier for the processing task
            resume_id: Optional resume identifier
            metadata: Optional additional result data

        Returns:
            Formatted completion message

        Example:
            >>> msg = ProgressMessage.create_complete(
            ...     task_id="task-123",
            ...     resume_id="resume-456",
            ...     metadata={"score": 95}
            ... )
        """
        return ProgressMessage.create(
            task_id=task_id,
            stage=ResumeProgressStage.COMPLETE,
            progress=100,
            message="Resume processing complete",
            resume_id=resume_id,
            metadata=metadata,
        )

    @staticmethod
    def create_error(
        task_id: str,
        error_message: str,
        resume_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create an error message.

        Args:
            task_id: Unique identifier for the processing task
            error_message: Human-readable error description
            resume_id: Optional resume identifier
            metadata: Optional additional error context

        Returns:
            Formatted error message

        Example:
            >>> msg = ProgressMessage.create_error(
            ...     task_id="task-123",
            ...     error_message="Failed to parse PDF",
            ...     resume_id="resume-456"
            ... )
        """
        return ProgressMessage.create(
            task_id=task_id,
            stage=ResumeProgressStage.FAILED,
            progress=0,
            message=f"Error: {error_message}",
            resume_id=resume_id,
            metadata=metadata,
        )

    @staticmethod
    def create_batch_progress(
        task_id: str,
        current: int,
        total: int,
        message: str,
        completed_resumes: Optional[List[str]] = None,
        failed_resumes: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a batch processing progress message.

        Args:
            task_id: Unique identifier for the batch task
            current: Current number of processed resumes
            total: Total number of resumes to process
            message: Human-readable progress message
            completed_resumes: Optional list of completed resume IDs
            failed_resumes: Optional list of failed resume IDs
            metadata: Optional additional batch data

        Returns:
            Formatted batch progress message

        Example:
            >>> msg = ProgressMessage.create_batch_progress(
            ...     task_id="batch-123",
            ...     current=5,
            ...     total=10,
            ...     message="Processing batch...",
            ...     completed_resumes=["r1", "r2", "r3", "r4", "r5"]
            ... )
        """
        progress = int((current / total * 100)) if total > 0 else 0

        msg: Dict[str, Any] = {
            "type": "batch_progress",
            "timestamp": datetime.utcnow().isoformat(),
            "task_id": task_id,
            "stage": ResumeProgressStage.ANALYZING.value,
            "progress": progress,
            "message": message,
            "current": current,
            "total": total,
        }

        batch_metadata = metadata or {}
        if completed_resumes:
            batch_metadata["completed_resumes"] = completed_resumes
        if failed_resumes:
            batch_metadata["failed_resumes"] = failed_resumes

        if batch_metadata:
            msg["metadata"] = batch_metadata

        return msg


async def send_resume_progress(
    task_id: str,
    resume_id: str,
    stage: ResumeProgressStage,
    progress: int,
    message: str,
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Send a resume progress update to a specific user.

    This function sends a progress update message to the WebSocket connection
    for the specified user. The message includes the task ID, resume ID,
    current stage, progress percentage, and a descriptive message.

    Args:
        task_id: Unique identifier for the processing task (usually Celery task ID)
        resume_id: Unique identifier for the resume being processed
        stage: Current processing stage
        progress: Current progress percentage (0-100)
        message: Human-readable progress message
        user_id: Optional user ID to send the update to. If None, uses resume_id.
        metadata: Optional additional context data

    Returns:
        True if the message was sent successfully, False otherwise

    Example:
        >>> success = await send_resume_progress(
        ...     task_id="abc-123-def-456",
        ...     resume_id="resume-789",
        ...     stage=ResumeProgressStage.ANALYZING,
        ...     progress=75,
        ...     message="Extracting work experience..."
        ... )
    """
    try:
        manager = await get_manager()

        # Use resume_id as user_id if not provided
        target_user = user_id or resume_id

        # Create progress message
        msg = ProgressMessage.create(
            task_id=task_id,
            resume_id=resume_id,
            stage=stage,
            progress=progress,
            message=message,
            metadata=metadata,
        )

        # Send to user's resume_progress connection
        success = await manager.send_direct_message(
            client_id=target_user,
            message=msg,
            connection_type="resume_progress",
        )

        if success:
            logger.debug(
                f"Sent progress update: task={task_id}, resume={resume_id}, "
                f"stage={stage.value}, progress={progress}%"
            )
        else:
            logger.debug(
                f"No WebSocket connection for user={target_user}, "
                f"progress update not sent"
            )

        return success

    except Exception as e:
        logger.error(f"Error sending resume progress: {e}", exc_info=True)
        return False


async def broadcast_resume_progress(
    task_id: str,
    current: int,
    total: int,
    message: str,
    completed_resumes: Optional[List[str]] = None,
    failed_resumes: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> int:
    """
    Broadcast a batch processing progress update to all connected clients.

    This function broadcasts a progress update for batch resume processing
    operations to all connected WebSocket clients listening for resume
    progress updates.

    Args:
        task_id: Unique identifier for the batch processing task
        current: Current number of processed resumes
        total: Total number of resumes to process
        message: Human-readable progress message
        completed_resumes: Optional list of completed resume IDs
        failed_resumes: Optional list of failed resume IDs
        metadata: Optional additional batch data

    Returns:
        Number of clients the message was sent to

    Example:
        >>> count = await broadcast_resume_progress(
        ...     task_id="batch-abc-123",
        ...     current=5,
        ...     total=10,
        ...     message="Processing batch...",
        ...     completed_resumes=["r1", "r2", "r3", "r4", "r5"]
        ... )
        >>> print(f"Broadcast to {count} clients")
    """
    try:
        manager = await get_manager()

        # Create batch progress message
        msg = ProgressMessage.create_batch_progress(
            task_id=task_id,
            current=current,
            total=total,
            message=message,
            completed_resumes=completed_resumes,
            failed_resumes=failed_resumes,
            metadata=metadata,
        )

        # Broadcast to all resume_progress connections
        count = await manager.broadcast(
            message=msg,
            connection_type="resume_progress",
        )

        if count > 0:
            logger.debug(
                f"Broadcast batch progress: task={task_id}, "
                f"progress={current}/{total}, sent to {count} clients"
            )
        else:
            logger.debug(
                f"No WebSocket connections for batch progress broadcast"
            )

        return count

    except Exception as e:
        logger.error(f"Error broadcasting resume progress: {e}", exc_info=True)
        return 0


async def send_resume_complete(
    task_id: str,
    resume_id: str,
    result_metadata: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
) -> bool:
    """
    Send a completion message for a processed resume.

    Convenience function that sends a completion message indicating that
    resume processing has finished successfully.

    Args:
        task_id: Unique identifier for the processing task
        resume_id: Unique identifier for the resume
        result_metadata: Optional result data (e.g., analysis scores, keywords)
        user_id: Optional user ID to send the update to

    Returns:
        True if the message was sent successfully, False otherwise

    Example:
        >>> success = await send_resume_complete(
        ...     task_id="task-123",
        ...     resume_id="resume-456",
        ...     result_metadata={"score": 95, "keywords": ["Python", "Django"]}
        ... )
    """
    return await send_resume_progress(
        task_id=task_id,
        resume_id=resume_id,
        stage=ResumeProgressStage.COMPLETE,
        progress=100,
        message="Resume processing complete",
        user_id=user_id,
        metadata=result_metadata,
    )


async def send_resume_error(
    task_id: str,
    resume_id: str,
    error_message: str,
    error_metadata: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
) -> bool:
    """
    Send an error message for a failed resume processing.

    Convenience function that sends an error message indicating that
    resume processing has failed.

    Args:
        task_id: Unique identifier for the processing task
        resume_id: Unique identifier for the resume
        error_message: Human-readable error description
        error_metadata: Optional error context data
        user_id: Optional user ID to send the update to

    Returns:
        True if the message was sent successfully, False otherwise

    Example:
        >>> success = await send_resume_error(
        ...     task_id="task-123",
        ...     resume_id="resume-456",
        ...     error_message="Failed to parse PDF file"
        ... )
    """
    return await send_resume_progress(
        task_id=task_id,
        resume_id=resume_id,
        stage=ResumeProgressStage.FAILED,
        progress=0,
        message=f"Error: {error_message}",
        user_id=user_id,
        metadata=error_metadata,
    )
