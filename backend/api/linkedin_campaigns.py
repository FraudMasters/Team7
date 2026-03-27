"""
LinkedIn campaign management endpoints.

This module provides endpoints for:
- Creating and managing LinkedIn outreach campaigns
- Tracking campaign performance (sends, responses)
- Recording individual outreach messages
- Analyzing campaign effectiveness

Enables recruiters to organize LinkedIn sourcing efforts and track ROI.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.linkedin_campaign import LinkedInCampaign, LinkedInCampaignStatus
from models.linkedin_outreach import LinkedInOutreach, LinkedInOutreachResponseStatus

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class CampaignCreateRequest(BaseModel):
    """Request model for creating a new LinkedIn campaign."""

    name: str = Field(..., min_length=1, max_length=255, description="Campaign name")
    vacancy_id: Optional[UUID] = Field(None, description="Associated job vacancy ID")
    description: Optional[str] = Field(None, description="Campaign description/notes")
    target_count: Optional[int] = Field(
        None, ge=0, description="Target number of candidates to reach"
    )
    recruiter_id: UUID = Field(..., description="Recruiter who owns this campaign")


class CampaignUpdateRequest(BaseModel):
    """Request model for updating a campaign."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Campaign name")
    status: Optional[LinkedInCampaignStatus] = Field(None, description="Campaign status")
    description: Optional[str] = Field(None, description="Campaign description/notes")
    target_count: Optional[int] = Field(None, ge=0, description="Target number of candidates")


class CampaignResponse(BaseModel):
    """Response model for a campaign."""

    id: UUID = Field(..., description="Campaign ID")
    name: str = Field(..., description="Campaign name")
    recruiter_id: UUID = Field(..., description="Recruiter ID")
    vacancy_id: Optional[UUID] = Field(None, description="Associated vacancy ID")
    status: LinkedInCampaignStatus = Field(..., description="Campaign status")
    target_count: int = Field(..., description="Target candidate count")
    sent_count: int = Field(..., description="Number of messages sent")
    response_count: int = Field(..., description="Number of responses received")
    response_rate: float = Field(..., description="Response rate (0-100)")
    description: Optional[str] = Field(None, description="Campaign description")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class CampaignListResponse(BaseModel):
    """Response model for campaign list."""

    total: int = Field(..., description="Total number of campaigns")
    campaigns: List[CampaignResponse] = Field(..., description="List of campaigns")


class OutreachCreateRequest(BaseModel):
    """Request model for recording an outreach message."""

    linkedin_profile_id: UUID = Field(..., description="LinkedIn profile ID being contacted")
    recruiter_id: UUID = Field(..., description="Recruiter sending the message")
    message_subject: Optional[str] = Field(
        None, max_length=255, description="Message subject (for InMail)"
    )
    message_body: Optional[str] = Field(None, description="Message content")
    message_sent_at: Optional[datetime] = Field(
        None, description="When the message was sent (defaults to now)"
    )


class OutreachUpdateRequest(BaseModel):
    """Request model for updating an outreach record."""

    response_status: Optional[LinkedInOutreachResponseStatus] = Field(
        None, description="Response status"
    )
    response_text: Optional[str] = Field(None, description="Response text from candidate")
    response_received_at: Optional[datetime] = Field(
        None, description="When response was received (defaults to now if status changes)"
    )


class OutreachResponse(BaseModel):
    """Response model for an outreach record."""

    id: UUID = Field(..., description="Outreach ID")
    campaign_id: UUID = Field(..., description="Campaign ID")
    linkedin_profile_id: UUID = Field(..., description="LinkedIn profile ID")
    recruiter_id: Optional[UUID] = Field(None, description="Recruiter ID")
    message_subject: Optional[str] = Field(None, description="Message subject")
    message_body: Optional[str] = Field(None, description="Message body")
    message_sent_at: Optional[datetime] = Field(None, description="Message sent timestamp")
    response_received_at: Optional[datetime] = Field(None, description="Response received timestamp")
    response_status: LinkedInOutreachResponseStatus = Field(..., description="Response status")
    response_text: Optional[str] = Field(None, description="Response text")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class CampaignStatsResponse(BaseModel):
    """Response model for campaign statistics."""

    campaign_id: UUID = Field(..., description="Campaign ID")
    total_outreach: int = Field(..., description="Total outreach messages sent")
    responses: int = Field(..., description="Number of responses received")
    response_rate: float = Field(..., description="Response rate (0-100)")
    interested: int = Field(..., description="Number of interested responses")
    not_interested: int = Field(..., description="Number of not interested responses")
    no_response: int = Field(..., description="Number with no response")
    by_status: Dict[str, int] = Field(..., description="Breakdown by response status")


@router.post(
    "/campaigns",
    response_model=CampaignResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["LinkedIn Campaigns"],
)
async def create_campaign(
    request: CampaignCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a new LinkedIn outreach campaign.

    This endpoint creates a new campaign to organize and track LinkedIn sourcing
    efforts for a specific job vacancy. Campaigns help recruiters measure the
    effectiveness of their outreach messages and track response rates.

    Args:
        request: Campaign creation request with name, vacancy_id, and other details
        db: Database session (injected)

    Returns:
        JSON response with created campaign details

    Raises:
        HTTPException(400): If request validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/linkedin/campaigns",
        ...     json={
        ...         "name": "Senior Python Developers - Q1 2026",
        ...         "vacancy_id": "123e4567-e89b-12d3-a456-426614174000",
        ...         "recruiter_id": "987fcdeb-51a2-43f7-8765-123456789abc",
        ...         "target_count": 50,
        ...         "description": "Targeting Python devs with 5+ years experience"
        ...     }
        ... )
        >>> campaign = response.json()
        >>> print(campaign["name"])
        Senior Python Developers - Q1 2026
    """
    try:
        logger.info(f"Creating new LinkedIn campaign: {request.name}")

        # Create campaign instance
        campaign = LinkedInCampaign(
            name=request.name,
            recruiter_id=request.recruiter_id,
            vacancy_id=request.vacancy_id,
            description=request.description,
            target_count=request.target_count or 0,
            status=LinkedInCampaignStatus.DRAFT,
            sent_count=0,
            response_count=0,
        )

        db.add(campaign)
        await db.commit()
        await db.refresh(campaign)

        logger.info(f"Successfully created campaign {campaign.id}")

        # Calculate response rate
        response_rate = (
            (campaign.response_count / campaign.sent_count * 100)
            if campaign.sent_count > 0
            else 0.0
        )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": str(campaign.id),
                "name": campaign.name,
                "recruiter_id": str(campaign.recruiter_id),
                "vacancy_id": str(campaign.vacancy_id) if campaign.vacancy_id else None,
                "status": campaign.status.value,
                "target_count": campaign.target_count,
                "sent_count": campaign.sent_count,
                "response_count": campaign.response_count,
                "response_rate": response_rate,
                "description": campaign.description,
                "created_at": campaign.created_at.isoformat(),
                "updated_at": campaign.updated_at.isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Error creating campaign: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create campaign: {str(e)}",
        )


@router.get(
    "/campaigns",
    response_model=CampaignListResponse,
    tags=["LinkedIn Campaigns"],
)
async def list_campaigns(
    recruiter_id: Optional[UUID] = Query(None, description="Filter by recruiter ID"),
    vacancy_id: Optional[UUID] = Query(None, description="Filter by vacancy ID"),
    status: Optional[LinkedInCampaignStatus] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List LinkedIn campaigns with optional filters.

    This endpoint retrieves a list of LinkedIn campaigns, optionally filtered by
    recruiter, vacancy, or status. Supports pagination for large result sets.

    Args:
        recruiter_id: Optional recruiter ID filter
        vacancy_id: Optional vacancy ID filter
        status: Optional status filter
        limit: Maximum number of results (1-100)
        offset: Number of results to skip for pagination
        db: Database session (injected)

    Returns:
        JSON response with list of campaigns and total count

    Raises:
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> # Get all active campaigns
        >>> response = requests.get(
        ...     "http://localhost:8000/api/linkedin/campaigns",
        ...     params={"status": "active", "limit": 10}
        ... )
        >>> data = response.json()
        >>> print(f"Found {data['total']} active campaigns")
        >>>
        >>> # Get campaigns for specific recruiter
        >>> response = requests.get(
        ...     "http://localhost:8000/api/linkedin/campaigns",
        ...     params={"recruiter_id": "987fcdeb-51a2-43f7-8765-123456789abc"}
        ... )
    """
    try:
        logger.info(f"Listing campaigns - recruiter: {recruiter_id}, vacancy: {vacancy_id}, status: {status}")

        # Build query with filters
        query = select(LinkedInCampaign)
        count_query = select(func.count()).select_from(LinkedInCampaign)

        filters = []
        if recruiter_id:
            filters.append(LinkedInCampaign.recruiter_id == recruiter_id)
        if vacancy_id:
            filters.append(LinkedInCampaign.vacancy_id == vacancy_id)
        if status:
            filters.append(LinkedInCampaign.status == status)

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Order by created_at descending (newest first)
        query = query.order_by(desc(LinkedInCampaign.created_at))

        # Apply pagination
        query = query.limit(limit).offset(offset)

        # Execute queries
        result = await db.execute(query)
        campaigns = result.scalars().all()

        count_result = await db.execute(count_query)
        total = count_result.scalar()

        logger.info(f"Found {total} campaigns, returning {len(campaigns)}")

        # Convert to response format
        campaigns_data = []
        for campaign in campaigns:
            response_rate = (
                (campaign.response_count / campaign.sent_count * 100)
                if campaign.sent_count > 0
                else 0.0
            )
            campaigns_data.append({
                "id": str(campaign.id),
                "name": campaign.name,
                "recruiter_id": str(campaign.recruiter_id),
                "vacancy_id": str(campaign.vacancy_id) if campaign.vacancy_id else None,
                "status": campaign.status.value,
                "target_count": campaign.target_count,
                "sent_count": campaign.sent_count,
                "response_count": campaign.response_count,
                "response_rate": response_rate,
                "description": campaign.description,
                "created_at": campaign.created_at.isoformat(),
                "updated_at": campaign.updated_at.isoformat(),
            })

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total": total,
                "campaigns": campaigns_data,
            },
        )

    except Exception as e:
        logger.error(f"Error listing campaigns: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list campaigns: {str(e)}",
        )


@router.get(
    "/campaigns/{campaign_id}",
    response_model=CampaignResponse,
    tags=["LinkedIn Campaigns"],
)
async def get_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get details of a specific campaign.

    This endpoint retrieves detailed information about a single LinkedIn campaign,
    including current statistics and performance metrics.

    Args:
        campaign_id: UUID of the campaign to retrieve
        db: Database session (injected)

    Returns:
        JSON response with campaign details

    Raises:
        HTTPException(404): If campaign not found
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> campaign_id = "123e4567-e89b-12d3-a456-426614174000"
        >>> response = requests.get(
        ...     f"http://localhost:8000/api/linkedin/campaigns/{campaign_id}"
        ... )
        >>> campaign = response.json()
        >>> print(f"Campaign: {campaign['name']}, Response Rate: {campaign['response_rate']}%")
    """
    try:
        logger.info(f"Retrieving campaign {campaign_id}")

        # Query campaign
        result = await db.execute(
            select(LinkedInCampaign).where(LinkedInCampaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()

        if not campaign:
            logger.warning(f"Campaign {campaign_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign {campaign_id} not found",
            )

        logger.info(f"Found campaign: {campaign.name}")

        # Calculate response rate
        response_rate = (
            (campaign.response_count / campaign.sent_count * 100)
            if campaign.sent_count > 0
            else 0.0
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(campaign.id),
                "name": campaign.name,
                "recruiter_id": str(campaign.recruiter_id),
                "vacancy_id": str(campaign.vacancy_id) if campaign.vacancy_id else None,
                "status": campaign.status.value,
                "target_count": campaign.target_count,
                "sent_count": campaign.sent_count,
                "response_count": campaign.response_count,
                "response_rate": response_rate,
                "description": campaign.description,
                "created_at": campaign.created_at.isoformat(),
                "updated_at": campaign.updated_at.isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving campaign: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve campaign: {str(e)}",
        )


@router.put(
    "/campaigns/{campaign_id}",
    response_model=CampaignResponse,
    tags=["LinkedIn Campaigns"],
)
async def update_campaign(
    campaign_id: UUID,
    request: CampaignUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update a campaign.

    This endpoint updates campaign details such as name, status, or target count.
    Used to activate campaigns, pause them, or mark them as completed.

    Args:
        campaign_id: UUID of the campaign to update
        request: Update request with fields to modify
        db: Database session (injected)

    Returns:
        JSON response with updated campaign details

    Raises:
        HTTPException(404): If campaign not found
        HTTPException(500): If database update fails

    Examples:
        >>> import requests
        >>> campaign_id = "123e4567-e89b-12d3-a456-426614174000"
        >>> response = requests.put(
        ...     f"http://localhost:8000/api/linkedin/campaigns/{campaign_id}",
        ...     json={"status": "active"}
        ... )
        >>> campaign = response.json()
        >>> print(f"Campaign status: {campaign['status']}")
    """
    try:
        logger.info(f"Updating campaign {campaign_id}")

        # Query campaign
        result = await db.execute(
            select(LinkedInCampaign).where(LinkedInCampaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()

        if not campaign:
            logger.warning(f"Campaign {campaign_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign {campaign_id} not found",
            )

        # Update fields
        if request.name is not None:
            campaign.name = request.name
        if request.status is not None:
            campaign.status = request.status
        if request.description is not None:
            campaign.description = request.description
        if request.target_count is not None:
            campaign.target_count = request.target_count

        await db.commit()
        await db.refresh(campaign)

        logger.info(f"Successfully updated campaign {campaign_id}")

        # Calculate response rate
        response_rate = (
            (campaign.response_count / campaign.sent_count * 100)
            if campaign.sent_count > 0
            else 0.0
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(campaign.id),
                "name": campaign.name,
                "recruiter_id": str(campaign.recruiter_id),
                "vacancy_id": str(campaign.vacancy_id) if campaign.vacancy_id else None,
                "status": campaign.status.value,
                "target_count": campaign.target_count,
                "sent_count": campaign.sent_count,
                "response_count": campaign.response_count,
                "response_rate": response_rate,
                "description": campaign.description,
                "created_at": campaign.created_at.isoformat(),
                "updated_at": campaign.updated_at.isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating campaign: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update campaign: {str(e)}",
        )


@router.post(
    "/campaigns/{campaign_id}/outreach",
    response_model=OutreachResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["LinkedIn Campaigns"],
)
async def create_outreach(
    campaign_id: UUID,
    request: OutreachCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Record a new outreach message for a campaign.

    This endpoint tracks individual LinkedIn messages (InMail or connection requests)
    sent to candidates as part of a campaign. Automatically updates campaign statistics.

    Args:
        campaign_id: UUID of the campaign
        request: Outreach details including profile ID and message content
        db: Database session (injected)

    Returns:
        JSON response with created outreach record

    Raises:
        HTTPException(404): If campaign not found
        HTTPException(400): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> campaign_id = "123e4567-e89b-12d3-a456-426614174000"
        >>> response = requests.post(
        ...     f"http://localhost:8000/api/linkedin/campaigns/{campaign_id}/outreach",
        ...     json={
        ...         "linkedin_profile_id": "987fcdeb-51a2-43f7-8765-123456789abc",
        ...         "recruiter_id": "111e2222-e33b-44d5-a666-777788889999",
        ...         "message_subject": "Exciting Python Developer Opportunity",
        ...         "message_body": "Hi! I saw your profile and thought you'd be a great fit..."
        ...     }
        ... )
        >>> outreach = response.json()
        >>> print(f"Outreach recorded: {outreach['id']}")
    """
    try:
        logger.info(f"Creating outreach for campaign {campaign_id}")

        # Verify campaign exists
        result = await db.execute(
            select(LinkedInCampaign).where(LinkedInCampaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()

        if not campaign:
            logger.warning(f"Campaign {campaign_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign {campaign_id} not found",
            )

        # Create outreach record
        outreach = LinkedInOutreach(
            campaign_id=campaign_id,
            linkedin_profile_id=request.linkedin_profile_id,
            recruiter_id=request.recruiter_id,
            message_subject=request.message_subject,
            message_body=request.message_body,
            message_sent_at=request.message_sent_at or datetime.utcnow(),
            response_status=LinkedInOutreachResponseStatus.NO_RESPONSE,
        )

        db.add(outreach)

        # Update campaign sent_count
        campaign.sent_count = (campaign.sent_count or 0) + 1

        await db.commit()
        await db.refresh(outreach)
        await db.refresh(campaign)

        logger.info(
            f"Successfully created outreach {outreach.id} for campaign {campaign_id}. "
            f"Campaign sent_count now: {campaign.sent_count}"
        )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": str(outreach.id),
                "campaign_id": str(outreach.campaign_id),
                "linkedin_profile_id": str(outreach.linkedin_profile_id),
                "recruiter_id": str(outreach.recruiter_id) if outreach.recruiter_id else None,
                "message_subject": outreach.message_subject,
                "message_body": outreach.message_body,
                "message_sent_at": outreach.message_sent_at.isoformat() if outreach.message_sent_at else None,
                "response_received_at": outreach.response_received_at.isoformat() if outreach.response_received_at else None,
                "response_status": outreach.response_status.value,
                "response_text": outreach.response_text,
                "created_at": outreach.created_at.isoformat(),
                "updated_at": outreach.updated_at.isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating outreach: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create outreach: {str(e)}",
        )


@router.put(
    "/campaigns/{campaign_id}/outreach/{outreach_id}",
    response_model=OutreachResponse,
    tags=["LinkedIn Campaigns"],
)
async def update_outreach(
    campaign_id: UUID,
    outreach_id: UUID,
    request: OutreachUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update an outreach record (typically to record a response).

    This endpoint updates the response status of an outreach message. When a candidate
    responds, automatically updates campaign response statistics.

    Args:
        campaign_id: UUID of the campaign
        outreach_id: UUID of the outreach record to update
        request: Update request with response details
        db: Database session (injected)

    Returns:
        JSON response with updated outreach record

    Raises:
        HTTPException(404): If campaign or outreach not found
        HTTPException(500): If database update fails

    Examples:
        >>> import requests
        >>> campaign_id = "123e4567-e89b-12d3-a456-426614174000"
        >>> outreach_id = "987fcdeb-51a2-43f7-8765-123456789abc"
        >>> response = requests.put(
        ...     f"http://localhost:8000/api/linkedin/campaigns/{campaign_id}/outreach/{outreach_id}",
        ...     json={
        ...         "response_status": "interested",
        ...         "response_text": "Yes, I'd love to learn more about this opportunity!"
        ...     }
        ... )
        >>> outreach = response.json()
        >>> print(f"Response status: {outreach['response_status']}")
    """
    try:
        logger.info(f"Updating outreach {outreach_id} for campaign {campaign_id}")

        # Query outreach
        result = await db.execute(
            select(LinkedInOutreach).where(
                and_(
                    LinkedInOutreach.id == outreach_id,
                    LinkedInOutreach.campaign_id == campaign_id,
                )
            )
        )
        outreach = result.scalar_one_or_none()

        if not outreach:
            logger.warning(f"Outreach {outreach_id} not found for campaign {campaign_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Outreach {outreach_id} not found",
            )

        # Track if we're changing from no_response to a response
        old_status = outreach.response_status
        status_changed_to_response = (
            old_status == LinkedInOutreachResponseStatus.NO_RESPONSE
            and request.response_status
            and request.response_status != LinkedInOutreachResponseStatus.NO_RESPONSE
        )

        # Update fields
        if request.response_status is not None:
            outreach.response_status = request.response_status
        if request.response_text is not None:
            outreach.response_text = request.response_text
        if request.response_received_at is not None:
            outreach.response_received_at = request.response_received_at
        elif request.response_status is not None and request.response_status != LinkedInOutreachResponseStatus.NO_RESPONSE:
            # Auto-set response_received_at if status changed to a response status
            outreach.response_received_at = datetime.utcnow()

        # Update campaign response_count if status changed from no_response to a response
        if status_changed_to_response:
            result = await db.execute(
                select(LinkedInCampaign).where(LinkedInCampaign.id == campaign_id)
            )
            campaign = result.scalar_one_or_none()
            if campaign:
                campaign.response_count = (campaign.response_count or 0) + 1
                logger.info(
                    f"Incremented campaign {campaign_id} response_count to {campaign.response_count}"
                )

        await db.commit()
        await db.refresh(outreach)

        logger.info(f"Successfully updated outreach {outreach_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(outreach.id),
                "campaign_id": str(outreach.campaign_id),
                "linkedin_profile_id": str(outreach.linkedin_profile_id),
                "recruiter_id": str(outreach.recruiter_id) if outreach.recruiter_id else None,
                "message_subject": outreach.message_subject,
                "message_body": outreach.message_body,
                "message_sent_at": outreach.message_sent_at.isoformat() if outreach.message_sent_at else None,
                "response_received_at": outreach.response_received_at.isoformat() if outreach.response_received_at else None,
                "response_status": outreach.response_status.value,
                "response_text": outreach.response_text,
                "created_at": outreach.created_at.isoformat(),
                "updated_at": outreach.updated_at.isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating outreach: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update outreach: {str(e)}",
        )


@router.get(
    "/campaigns/{campaign_id}/outreach",
    tags=["LinkedIn Campaigns"],
)
async def list_outreach(
    campaign_id: UUID,
    response_status: Optional[LinkedInOutreachResponseStatus] = Query(
        None, description="Filter by response status"
    ),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List outreach messages for a campaign.

    This endpoint retrieves all outreach messages sent as part of a campaign,
    optionally filtered by response status.

    Args:
        campaign_id: UUID of the campaign
        response_status: Optional filter by response status
        limit: Maximum number of results (1-100)
        offset: Number of results to skip for pagination
        db: Database session (injected)

    Returns:
        JSON response with list of outreach messages and total count

    Raises:
        HTTPException(404): If campaign not found
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> campaign_id = "123e4567-e89b-12d3-a456-426614174000"
        >>> # Get all outreach messages
        >>> response = requests.get(
        ...     f"http://localhost:8000/api/linkedin/campaigns/{campaign_id}/outreach"
        ... )
        >>> data = response.json()
        >>> print(f"Total outreach messages: {data['total']}")
        >>>
        >>> # Get only interested responses
        >>> response = requests.get(
        ...     f"http://localhost:8000/api/linkedin/campaigns/{campaign_id}/outreach",
        ...     params={"response_status": "interested"}
        ... )
    """
    try:
        logger.info(f"Listing outreach for campaign {campaign_id}, status filter: {response_status}")

        # Verify campaign exists
        result = await db.execute(
            select(LinkedInCampaign).where(LinkedInCampaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()

        if not campaign:
            logger.warning(f"Campaign {campaign_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign {campaign_id} not found",
            )

        # Build query
        query = select(LinkedInOutreach).where(LinkedInOutreach.campaign_id == campaign_id)
        count_query = select(func.count()).select_from(LinkedInOutreach).where(
            LinkedInOutreach.campaign_id == campaign_id
        )

        if response_status:
            query = query.where(LinkedInOutreach.response_status == response_status)
            count_query = count_query.where(LinkedInOutreach.response_status == response_status)

        # Order by message_sent_at descending (newest first)
        query = query.order_by(desc(LinkedInOutreach.message_sent_at))

        # Apply pagination
        query = query.limit(limit).offset(offset)

        # Execute queries
        result = await db.execute(query)
        outreach_list = result.scalars().all()

        count_result = await db.execute(count_query)
        total = count_result.scalar()

        logger.info(f"Found {total} outreach messages for campaign {campaign_id}, returning {len(outreach_list)}")

        # Convert to response format
        outreach_data = []
        for outreach in outreach_list:
            outreach_data.append({
                "id": str(outreach.id),
                "campaign_id": str(outreach.campaign_id),
                "linkedin_profile_id": str(outreach.linkedin_profile_id),
                "recruiter_id": str(outreach.recruiter_id) if outreach.recruiter_id else None,
                "message_subject": outreach.message_subject,
                "message_body": outreach.message_body,
                "message_sent_at": outreach.message_sent_at.isoformat() if outreach.message_sent_at else None,
                "response_received_at": outreach.response_received_at.isoformat() if outreach.response_received_at else None,
                "response_status": outreach.response_status.value,
                "response_text": outreach.response_text,
                "created_at": outreach.created_at.isoformat(),
                "updated_at": outreach.updated_at.isoformat(),
            })

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total": total,
                "outreach": outreach_data,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing outreach: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list outreach: {str(e)}",
        )


@router.get(
    "/campaigns/{campaign_id}/stats",
    response_model=CampaignStatsResponse,
    tags=["LinkedIn Campaigns"],
)
async def get_campaign_stats(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get detailed statistics for a campaign.

    This endpoint provides comprehensive analytics for a campaign including
    response rates, status breakdowns, and engagement metrics.

    Args:
        campaign_id: UUID of the campaign
        db: Database session (injected)

    Returns:
        JSON response with detailed campaign statistics

    Raises:
        HTTPException(404): If campaign not found
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> campaign_id = "123e4567-e89b-12d3-a456-426614174000"
        >>> response = requests.get(
        ...     f"http://localhost:8000/api/linkedin/campaigns/{campaign_id}/stats"
        ... )
        >>> stats = response.json()
        >>> print(f"Response rate: {stats['response_rate']}%")
        >>> print(f"Interested: {stats['interested']}, Not interested: {stats['not_interested']}")
    """
    try:
        logger.info(f"Getting stats for campaign {campaign_id}")

        # Verify campaign exists
        result = await db.execute(
            select(LinkedInCampaign).where(LinkedInCampaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()

        if not campaign:
            logger.warning(f"Campaign {campaign_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign {campaign_id} not found",
            )

        # Get outreach statistics
        stats_query = select(
            LinkedInOutreach.response_status,
            func.count(LinkedInOutreach.id).label("count"),
        ).where(
            LinkedInOutreach.campaign_id == campaign_id
        ).group_by(
            LinkedInOutreach.response_status
        )

        result = await db.execute(stats_query)
        status_counts = dict(result.all())

        # Build statistics
        total_outreach = sum(status_counts.values())
        responses = sum(
            count
            for status, count in status_counts.items()
            if status != LinkedInOutreachResponseStatus.NO_RESPONSE
        )
        response_rate = (responses / total_outreach * 100) if total_outreach > 0 else 0.0

        by_status = {
            status.value: status_counts.get(status, 0)
            for status in LinkedInOutreachResponseStatus
        }

        logger.info(
            f"Campaign {campaign_id} stats: {total_outreach} total, "
            f"{responses} responses ({response_rate:.1f}%)"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "campaign_id": str(campaign_id),
                "total_outreach": total_outreach,
                "responses": responses,
                "response_rate": round(response_rate, 2),
                "interested": status_counts.get(LinkedInOutreachResponseStatus.INTERESTED, 0),
                "not_interested": status_counts.get(LinkedInOutreachResponseStatus.NOT_INTERESTED, 0),
                "no_response": status_counts.get(LinkedInOutreachResponseStatus.NO_RESPONSE, 0),
                "by_status": by_status,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting campaign stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get campaign stats: {str(e)}",
        )
