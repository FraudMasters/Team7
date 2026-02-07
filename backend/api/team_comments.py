"""
Team comment management endpoints.

This module provides endpoints for managing collaborative threaded discussions on candidates,
including CRUD operations for creating, reading, updating, and deleting comments with
support for threaded replies and resolved status tracking.
"""
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Set
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.recruiter import Recruiter
from models.resume import Resume
from models.team_comment import TeamComment
from models.comment_mention import CommentMention

logger = logging.getLogger(__name__)

router = APIRouter()


def extract_mentions(content: str) -> Set[str]:
    """
    Extract @mentions from comment content.

    This function parses the comment content to find all @mentions,
    which are username references prefixed with @ symbol.

    Args:
        content: Comment content text

    Returns:
        Set of mentioned usernames (without @ prefix)

    Examples:
        >>> extract_mentions("What do you think @john?")
        {'john'}
        >>> extract_mentions("@jane and @bob should review this")
        {'jane', 'bob'}
    """
    # Pattern to match @username (alphanumeric and underscores)
    pattern = r'@(\w+)'
    mentions = re.findall(pattern, content)
    return set(mentions)


async def get_recruiter_by_username(
    db: AsyncSession,
    username: str,
) -> Optional[Recruiter]:
    """
    Get recruiter by username/email.

    This function looks up a recruiter by their username (which is typically
    their email without the domain part).

    Args:
        db: Database session
        username: Username to look up

    Returns:
        Recruiter object if found, None otherwise
    """
    try:
        # Try to match username against email
        result = await db.execute(
            select(Recruiter).where(Recruiter.email.like(f"%{username}%"))
        )
        return result.scalar_one_or_none()
    except Exception:
        return None


async def _cascade_resolution_status(
    db: AsyncSession,
    parent_comment_id: UUID,
    is_resolved: bool,
) -> None:
    """
    Cascade resolution status to all child comments recursively.

    When a parent comment is marked as resolved or unresolved, all of its
    replies (and nested replies) inherit the same resolution status.
    This ensures that entire comment threads are consistently resolved.

    Args:
        db: Database session
        parent_comment_id: UUID of the parent comment
        is_resolved: Resolution status to cascade to children

    Returns:
        None
    """
    # Find all direct children (replies to this comment)
    children_result = await db.execute(
        select(TeamComment).where(
            TeamComment.parent_comment_id == parent_comment_id
        )
    )
    children = children_result.scalars().all()

    for child in children:
        # Update child's resolution status
        child.is_resolved = is_resolved

        # Recursively cascade to nested replies
        await _cascade_resolution_status(db, child.id, is_resolved)


class TeamCommentCreate(BaseModel):
    """Request model for creating a team comment."""

    resume_id: str = Field(..., description="Resume ID (candidate) this comment is about")
    author_id: str = Field(..., description="Recruiter ID (author) of the comment")
    parent_comment_id: Optional[str] = Field(None, description="Parent comment ID for threaded replies")
    content: str = Field(..., min_length=1, max_length=10000, description="Comment content")
    is_resolved: bool = Field(False, description="Whether the comment thread is resolved")


class TeamCommentUpdate(BaseModel):
    """Request model for updating a team comment."""

    content: Optional[str] = Field(None, min_length=1, max_length=10000, description="Comment content")
    is_resolved: Optional[bool] = Field(None, description="Whether the comment thread is resolved")


class TeamCommentResponse(BaseModel):
    """Response model for a single team comment."""

    id: str = Field(..., description="Unique identifier for the comment")
    resume_id: str = Field(..., description="Resume ID this comment is about")
    author_id: str = Field(..., description="Recruiter ID (author) of the comment")
    parent_comment_id: Optional[str] = Field(None, description="Parent comment ID for threaded replies")
    content: str = Field(..., description="Comment content")
    is_resolved: bool = Field(..., description="Whether the comment thread is resolved")
    is_deleted: bool = Field(..., description="Whether the comment is deleted (soft delete)")
    edits_count: int = Field(..., description="Number of times the comment has been edited")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class TeamCommentListResponse(BaseModel):
    """Response model for listing team comments."""

    resume_id: str = Field(..., description="Resume ID")
    comments: List[TeamCommentResponse] = Field(..., description="List of team comments")
    total_count: int = Field(..., description="Total number of comments")


@router.post(
    "/",
    response_model=TeamCommentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Team Comments"],
)
async def create_team_comment(
    request: TeamCommentCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a team comment.

    This endpoint creates a new comment for a candidate (resume), allowing team members
    to collaborate through threaded discussions. Comments can be top-level or replies
    to existing comments.

    Args:
        request: Request body containing comment details
        db: Database session

    Returns:
        JSON response with created comment details

    Raises:
        HTTPException(404): If resume is not found
        HTTPException(422): If validation fails
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/team-comments/",
        ...     json={
        ...         "resume_id": "resume-uuid",
        ...         "author_id": "recruiter-uuid",
        ...         "content": "Great candidate, strong technical skills",
        ...         "is_resolved": False
        ...     }
        ... )
        >>> response.status_code
        201
    """
    try:
        logger.info(f"Creating team comment for resume: {request.resume_id}")

        # Verify resume exists
        resume_result = await db.execute(
            select(Resume).where(Resume.id == UUID(request.resume_id))
        )
        resume = resume_result.scalar_one_or_none()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume not found: {request.resume_id}",
            )

        # Verify parent comment exists if provided
        if request.parent_comment_id:
            parent_result = await db.execute(
                select(TeamComment).where(TeamComment.id == UUID(request.parent_comment_id))
            )
            parent_comment = parent_result.scalar_one_or_none()

            if not parent_comment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Parent comment not found: {request.parent_comment_id}",
                )

        # Create new comment
        new_comment = TeamComment(
            resume_id=UUID(request.resume_id),
            author_id=UUID(request.author_id),
            parent_comment_id=UUID(request.parent_comment_id) if request.parent_comment_id else None,
            content=request.content,
            is_resolved=request.is_resolved,
            is_deleted=False,
            edits_count=0,
        )
        db.add(new_comment)
        await db.flush()

        # Extract @mentions from content and create CommentMention records
        mentions = extract_mentions(request.content)
        mentioned_recruiters = []

        for mentioned_username in mentions:
            mentioned_recruiter = await get_recruiter_by_username(db, mentioned_username)
            if mentioned_recruiter and str(mentioned_recruiter.id) != request.author_id:
                # Create CommentMention record
                mention_record = CommentMention(
                    comment_id=new_comment.id,
                    mentioned_user_id=mentioned_recruiter.id,
                    is_read=False,
                )
                db.add(mention_record)
                mentioned_recruiters.append(mentioned_recruiter)
                logger.info(f"Created mention record for user: {mentioned_username}")

        response_data = {
            "id": str(new_comment.id),
            "resume_id": str(new_comment.resume_id),
            "author_id": str(new_comment.author_id),
            "parent_comment_id": str(new_comment.parent_comment_id) if new_comment.parent_comment_id else None,
            "content": new_comment.content,
            "is_resolved": new_comment.is_resolved,
            "is_deleted": new_comment.is_deleted,
            "edits_count": new_comment.edits_count,
            "created_at": new_comment.created_at.isoformat(),
            "updated_at": new_comment.updated_at.isoformat(),
        }

        await db.commit()

        logger.info(f"Created team comment with ID: {new_comment.id}")

        # Trigger notifications asynchronously
        # Note: Import tasks here to avoid circular imports and allow task triggering after commit
        try:
            from tasks.comment_notifications import (
                send_comment_mention_notification,
                send_comment_reply_notification,
            )

            # Get author information
            author_result = await db.execute(
                select(Recruiter).where(Recruiter.id == UUID(request.author_id))
            )
            author = author_result.scalar_one_or_none()
            author_name = author.name if author else "Unknown"
            author_email = author.email if author else "unknown@example.com"

            # Get resume/candidate information
            candidate_name = resume.filename if resume else "Unknown candidate"

            # Send mention notifications for each mentioned recruiter
            for mentioned_recruiter in mentioned_recruiters:
                comment_details = {
                    "comment_id": str(new_comment.id),
                    "content": new_comment.content,
                    "author_name": author_name,
                    "author_email": author_email,
                    "resume_id": str(new_comment.resume_id),
                    "candidate_name": candidate_name,
                    "parent_comment_id": str(new_comment.parent_comment_id) if new_comment.parent_comment_id else None,
                    "created_at": new_comment.created_at.isoformat(),
                }
                # Trigger notification task asynchronously
                send_comment_mention_notification.delay(
                    comment_id=new_comment.id,
                    mentioned_user_id=mentioned_recruiter.id,
                    mentioned_user_email=mentioned_recruiter.email,
                    comment_details=comment_details,
                )
                logger.info(f"Triggered mention notification for user: {mentioned_recruiter.email}")

            # Send reply notification if this is a reply
            if new_comment.parent_comment_id:
                parent_result = await db.execute(
                    select(TeamComment).where(TeamComment.id == new_comment.parent_comment_id)
                )
                parent_comment = parent_result.scalar_one_or_none()

                if parent_comment and str(parent_comment.author_id) != request.author_id:
                    # Get parent author information
                    parent_author_result = await db.execute(
                        select(Recruiter).where(Recruiter.id == parent_comment.author_id)
                    )
                    parent_author = parent_author_result.scalar_one_or_none()

                    if parent_author:
                        comment_details = {
                            "comment_id": str(new_comment.id),
                            "content": new_comment.content,
                            "author_name": author_name,
                            "author_email": author_email,
                            "resume_id": str(new_comment.resume_id),
                            "candidate_name": candidate_name,
                            "created_at": new_comment.created_at.isoformat(),
                        }
                        # Trigger reply notification asynchronously
                        send_comment_reply_notification.delay(
                            comment_id=new_comment.id,
                            parent_comment_id=parent_comment.id,
                            parent_author_id=parent_author.id,
                            parent_author_email=parent_author.email,
                            comment_details=comment_details,
                        )
                        logger.info(f"Triggered reply notification for parent comment author: {parent_author.email}")

        except ImportError as e:
            logger.warning(f"Could not import notification tasks: {e}")
        except Exception as e:
            # Don't fail the request if notifications fail
            logger.error(f"Error triggering notifications: {e}", exc_info=True)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid UUID format",
        )
    except Exception as e:
        logger.error(f"Error creating team comment: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create team comment: {str(e)}",
        ) from e


@router.get("/", tags=["Team Comments"])
async def list_team_comments(
    resume_id: Optional[str] = Query(None, description="Filter by resume ID"),
    author_id: Optional[str] = Query(None, description="Filter by author ID"),
    is_resolved: Optional[bool] = Query(None, description="Filter by resolved status"),
    parent_comment_id: Optional[str] = Query(None, description="Filter by parent comment ID"),
    include_deleted: bool = Query(False, description="Include deleted comments"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List team comments with optional filters.

    This endpoint retrieves team comments with support for filtering
    by resume, author, resolved status, and parent comment.

    Args:
        resume_id: Optional resume ID filter
        author_id: Optional author ID filter
        is_resolved: Optional resolved status filter
        parent_comment_id: Optional parent comment ID filter
        include_deleted: Whether to include soft-deleted comments
        db: Database session

    Returns:
        JSON response with list of comments

    Raises:
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/team-comments/?resume_id=resume-uuid")
        >>> response.json()
        {
            "resume_id": "resume-uuid",
            "comments": [...],
            "total_count": 3
        }
    """
    try:
        logger.info(f"Listing team comments with filters - resume_id: {resume_id}, author_id: {author_id}, is_resolved: {is_resolved}")

        # Build query
        query = select(TeamComment)

        if resume_id:
            query = query.where(TeamComment.resume_id == UUID(resume_id))
        if author_id:
            query = query.where(TeamComment.author_id == UUID(author_id))
        if is_resolved is not None:
            query = query.where(TeamComment.is_resolved == is_resolved)
        if parent_comment_id:
            query = query.where(TeamComment.parent_comment_id == UUID(parent_comment_id))
        if not include_deleted:
            query = query.where(TeamComment.is_deleted == False)

        query = query.order_by(TeamComment.created_at.desc())

        result = await db.execute(query)
        comments = result.scalars().all()

        # If resume_id filter was provided, use it in response
        response_resume_id = resume_id if resume_id and len(comments) > 0 else "all"

        # Build response
        comments_data = []
        for comment in comments:
            comments_data.append({
                "id": str(comment.id),
                "resume_id": str(comment.resume_id),
                "author_id": str(comment.author_id),
                "parent_comment_id": str(comment.parent_comment_id) if comment.parent_comment_id else None,
                "content": comment.content,
                "is_resolved": comment.is_resolved,
                "is_deleted": comment.is_deleted,
                "edits_count": comment.edits_count,
                "created_at": comment.created_at.isoformat(),
                "updated_at": comment.updated_at.isoformat(),
            })

        response_data = {
            "resume_id": response_resume_id,
            "comments": comments_data,
            "total_count": len(comments_data),
        }

        logger.info(f"Retrieved {len(comments_data)} team comments")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid UUID format",
        )
    except Exception as e:
        logger.error(f"Error listing team comments: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list team comments: {str(e)}",
        ) from e


@router.get("/{comment_id}", tags=["Team Comments"])
async def get_team_comment(
    comment_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific team comment by ID.

    This endpoint retrieves detailed information about a single comment.

    Args:
        comment_id: UUID of the comment
        db: Database session

    Returns:
        JSON response with comment details

    Raises:
        HTTPException(404): If comment is not found
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/team-comments/comment-uuid")
        >>> response.json()
        {
            "id": "comment-uuid",
            "resume_id": "resume-uuid",
            "content": "Great candidate",
            ...
        }
    """
    try:
        logger.info(f"Retrieving team comment: {comment_id}")

        result = await db.execute(
            select(TeamComment).where(TeamComment.id == UUID(comment_id))
        )
        comment = result.scalar_one_or_none()

        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Team comment not found: {comment_id}",
            )

        response_data = {
            "id": str(comment.id),
            "resume_id": str(comment.resume_id),
            "author_id": str(comment.author_id),
            "parent_comment_id": str(comment.parent_comment_id) if comment.parent_comment_id else None,
            "content": comment.content,
            "is_resolved": comment.is_resolved,
            "is_deleted": comment.is_deleted,
            "edits_count": comment.edits_count,
            "created_at": comment.created_at.isoformat(),
            "updated_at": comment.updated_at.isoformat(),
        }

        logger.info(f"Retrieved team comment: {comment_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {comment_id}",
        )
    except Exception as e:
        logger.error(f"Error retrieving team comment: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve team comment: {str(e)}",
        ) from e


@router.put("/{comment_id}", tags=["Team Comments"])
async def update_team_comment(
    comment_id: str,
    request: TeamCommentUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update a team comment.

    This endpoint updates an existing team comment.
    Only the fields specified in the request body will be updated.
    Each edit increments the edits_count counter.

    When is_resolved is updated, the status cascades to all child comments
    (replies) recursively. This ensures entire comment threads are consistently
    resolved or unresolved.

    Args:
        comment_id: UUID of the comment
        request: Request body containing fields to update
        db: Database session

    Returns:
        JSON response with updated comment details

    Raises:
        HTTPException(404): If comment is not found
        HTTPException(422): If validation fails
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.put(
        ...     "http://localhost:8000/api/team-comments/comment-uuid",
        ...     json={
        ...         "content": "Updated comment content",
        ...         "is_resolved": True
        ...     }
        ... )
        >>> response.json()
        {
            "id": "comment-uuid",
            "content": "Updated comment content",
            "is_resolved": true,
            ...
        }
    """
    try:
        logger.info(f"Updating team comment: {comment_id}")

        # Get existing comment
        result = await db.execute(
            select(TeamComment).where(TeamComment.id == UUID(comment_id))
        )
        comment = result.scalar_one_or_none()

        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Team comment not found: {comment_id}",
            )

        # Update fields if provided
        if request.content is not None:
            # Check if comment is within the 5-minute edit window
            edit_window_minutes = 5
            now = datetime.now(timezone.utc)
            time_since_creation = now - comment.created_at

            if time_since_creation > timedelta(minutes=edit_window_minutes):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Comment can only be edited within {edit_window_minutes} minutes of creation. "
                           f"This comment was created {time_since_creation.total_seconds():.0f} seconds ago.",
                )

            comment.content = request.content
            comment.edits_count += 1
        if request.is_resolved is not None:
            comment.is_resolved = request.is_resolved

            # Cascade resolution status to all child comments (replies)
            # When a parent comment is resolved/unresolved, all replies inherit the same status
            await _cascade_resolution_status(db, comment.id, request.is_resolved)

        await db.commit()
        await db.refresh(comment)

        response_data = {
            "id": str(comment.id),
            "resume_id": str(comment.resume_id),
            "author_id": str(comment.author_id),
            "parent_comment_id": str(comment.parent_comment_id) if comment.parent_comment_id else None,
            "content": comment.content,
            "is_resolved": comment.is_resolved,
            "is_deleted": comment.is_deleted,
            "edits_count": comment.edits_count,
            "created_at": comment.created_at.isoformat(),
            "updated_at": comment.updated_at.isoformat(),
        }

        logger.info(f"Updated team comment: {comment_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {comment_id}",
        )
    except Exception as e:
        logger.error(f"Error updating team comment: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update team comment: {str(e)}",
        ) from e


@router.delete("/{comment_id}", tags=["Team Comments"])
async def delete_team_comment(
    comment_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete a team comment.

    This endpoint performs a soft delete on a team comment, marking it as deleted
    rather than removing it from the database. This action preserves comment history.

    Args:
        comment_id: UUID of the comment
        db: Database session

    Returns:
        JSON response confirming deletion

    Raises:
        HTTPException(404): If comment is not found
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8000/api/team-comments/comment-uuid")
        >>> response.json()
        {
            "message": "Team comment deleted successfully",
            "id": "comment-uuid"
        }
    """
    try:
        logger.info(f"Deleting team comment: {comment_id}")

        # Check if comment exists
        result = await db.execute(
            select(TeamComment).where(TeamComment.id == UUID(comment_id))
        )
        comment = result.scalar_one_or_none()

        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Team comment not found: {comment_id}",
            )

        # Soft delete the comment
        comment.is_deleted = True
        await db.commit()

        logger.info(f"Deleted team comment: {comment_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Team comment deleted successfully",
                "id": comment_id,
            },
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {comment_id}",
        )
    except Exception as e:
        logger.error(f"Error deleting team comment: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete team comment: {str(e)}",
        ) from e
