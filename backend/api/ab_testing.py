"""
A/B testing endpoints for comparing different weight configurations.

This module provides endpoints for creating, managing, and tracking A/B tests
that compare different matching algorithm weight configurations to optimize
hiring outcomes.
"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.ab_test import ABTest, ABTestStatus
from models.ab_test_result import ABTestResult

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class ABTestCreate(BaseModel):
    """Request model for creating an A/B test."""

    organization_id: str = Field(..., description="Organization identifier")
    name: str = Field(..., description="Human-readable name for the experiment", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Description of experiment goals and hypothesis", max_length=2000)
    variant_a_profile_id: str = Field(..., description="Weight profile ID for variant A")
    variant_b_profile_id: str = Field(..., description="Weight profile ID for variant B")
    created_by: Optional[str] = Field(None, description="User ID who is creating this test")


class ABTestUpdate(BaseModel):
    """Request model for updating an A/B test."""

    name: Optional[str] = Field(None, description="Human-readable name for the experiment", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Description of experiment goals and hypothesis", max_length=2000)
    status: Optional[ABTestStatus] = Field(None, description="Test status (draft/running/completed/paused)")


class ABTestResponse(BaseModel):
    """Response model for a single A/B test."""

    id: str = Field(..., description="Unique identifier for the test")
    organization_id: str = Field(..., description="Organization identifier")
    name: str = Field(..., description="Human-readable name for the experiment")
    description: Optional[str] = Field(None, description="Description of experiment goals")
    variant_a_profile_id: str = Field(..., description="Weight profile ID for variant A")
    variant_b_profile_id: str = Field(..., description="Weight profile ID for variant B")
    status: str = Field(..., description="Current status of the test")
    start_date: Optional[str] = Field(None, description="When the test started running")
    end_date: Optional[str] = Field(None, description="When the test ended")
    created_by: Optional[str] = Field(None, description="User ID who created this test")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class ABTestListResponse(BaseModel):
    """Response model for listing A/B tests."""

    organization_id: Optional[str] = Field(None, description="Organization ID filter used")
    tests: List[ABTestResponse] = Field(..., description="List of A/B tests")
    total_count: int = Field(..., description="Total number of tests")


class AssignVariantRequest(BaseModel):
    """Request model for assigning a variant to a vacancy/resume pair."""

    vacancy_id: str = Field(..., description="Vacancy ID")
    resume_id: str = Field(..., description="Resume ID")


class AssignVariantResponse(BaseModel):
    """Response model for variant assignment."""

    ab_test_id: str = Field(..., description="A/B test ID")
    vacancy_id: str = Field(..., description="Vacancy ID")
    resume_id: str = Field(..., description="Resume ID")
    variant_assigned: str = Field(..., description="Variant assigned (a or b)")
    profile_id: str = Field(..., description="Weight profile ID to use for matching")


class RecordResultRequest(BaseModel):
    """Request model for recording an A/B test result."""

    vacancy_id: str = Field(..., description="Vacancy ID")
    resume_id: str = Field(..., description="Resume ID")
    match_result_id: str = Field(..., description="Match result ID from matching service")
    variant_assigned: str = Field(..., description="Variant that was used (a or b)", pattern="^[ab]$")
    outcome: Optional[str] = Field(None, description="Hiring outcome (hired/rejected/pending/shortlisted)", max_length=20)


class RecordResultResponse(BaseModel):
    """Response model for recording a result."""

    id: str = Field(..., description="Result record ID")
    ab_test_id: str = Field(..., description="A/B test ID")
    vacancy_id: str = Field(..., description="Vacancy ID")
    resume_id: str = Field(..., description="Resume ID")
    variant_assigned: str = Field(..., description="Variant used")
    outcome: Optional[str] = Field(None, description="Hiring outcome")
    created_at: str = Field(..., description="Timestamp when result was recorded")


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/", response_model=ABTestResponse, status_code=status.HTTP_201_CREATED)
async def create_ab_test(
    test_data: ABTestCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new A/B test to compare two weight configurations.

    Args:
        test_data: A/B test creation data
        db: Database session

    Returns:
        Created A/B test record

    Raises:
        HTTPException: If variant profile IDs are invalid or test creation fails
    """
    try:
        # Validate that variant_a and variant_b are different
        if test_data.variant_a_profile_id == test_data.variant_b_profile_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Variant A and Variant B must use different weight profiles",
            )

        # Create new A/B test
        new_test = ABTest(
            id=uuid4(),
            organization_id=test_data.organization_id,
            name=test_data.name,
            description=test_data.description,
            variant_a_profile_id=UUID(test_data.variant_a_profile_id),
            variant_b_profile_id=UUID(test_data.variant_b_profile_id),
            status=ABTestStatus.DRAFT,
            created_by=test_data.created_by,
        )

        db.add(new_test)
        await db.commit()
        await db.refresh(new_test)

        logger.info(f"Created A/B test {new_test.id} for organization {test_data.organization_id}")

        return ABTestResponse(
            id=str(new_test.id),
            organization_id=new_test.organization_id,
            name=new_test.name,
            description=new_test.description,
            variant_a_profile_id=str(new_test.variant_a_profile_id),
            variant_b_profile_id=str(new_test.variant_b_profile_id),
            status=new_test.status.value,
            start_date=new_test.start_date.isoformat() if new_test.start_date else None,
            end_date=new_test.end_date.isoformat() if new_test.end_date else None,
            created_by=new_test.created_by,
            created_at=new_test.created_at.isoformat(),
            updated_at=new_test.updated_at.isoformat(),
        )

    except ValueError as e:
        logger.error(f"Invalid UUID in A/B test creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid profile ID format: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error creating A/B test: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create A/B test: {str(e)}",
        )


@router.get("/{test_id}", response_model=ABTestResponse)
async def get_ab_test(
    test_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get details of a specific A/B test.

    Args:
        test_id: A/B test ID
        db: Database session

    Returns:
        A/B test details

    Raises:
        HTTPException: If test not found
    """
    try:
        test_uuid = UUID(test_id)
        query = select(ABTest).where(ABTest.id == test_uuid)
        result = await db.execute(query)
        ab_test = result.scalar_one_or_none()

        if not ab_test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"A/B test {test_id} not found",
            )

        return ABTestResponse(
            id=str(ab_test.id),
            organization_id=ab_test.organization_id,
            name=ab_test.name,
            description=ab_test.description,
            variant_a_profile_id=str(ab_test.variant_a_profile_id),
            variant_b_profile_id=str(ab_test.variant_b_profile_id),
            status=ab_test.status.value,
            start_date=ab_test.start_date.isoformat() if ab_test.start_date else None,
            end_date=ab_test.end_date.isoformat() if ab_test.end_date else None,
            created_by=ab_test.created_by,
            created_at=ab_test.created_at.isoformat(),
            updated_at=ab_test.updated_at.isoformat(),
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid test ID format",
        )
    except Exception as e:
        logger.error(f"Error retrieving A/B test {test_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve A/B test: {str(e)}",
        )


@router.get("/", response_model=ABTestListResponse)
async def list_ab_tests(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    status_filter: Optional[ABTestStatus] = Query(None, description="Filter by test status"),
    db: AsyncSession = Depends(get_db),
):
    """
    List A/B tests with optional filtering.

    Args:
        organization_id: Optional organization ID filter
        status_filter: Optional status filter
        db: Database session

    Returns:
        List of A/B tests matching filters
    """
    try:
        query = select(ABTest)

        # Apply filters
        if organization_id:
            query = query.where(ABTest.organization_id == organization_id)
        if status_filter:
            query = query.where(ABTest.status == status_filter)

        # Order by creation date (newest first)
        query = query.order_by(ABTest.created_at.desc())

        result = await db.execute(query)
        tests = result.scalars().all()

        test_responses = [
            ABTestResponse(
                id=str(test.id),
                organization_id=test.organization_id,
                name=test.name,
                description=test.description,
                variant_a_profile_id=str(test.variant_a_profile_id),
                variant_b_profile_id=str(test.variant_b_profile_id),
                status=test.status.value,
                start_date=test.start_date.isoformat() if test.start_date else None,
                end_date=test.end_date.isoformat() if test.end_date else None,
                created_by=test.created_by,
                created_at=test.created_at.isoformat(),
                updated_at=test.updated_at.isoformat(),
            )
            for test in tests
        ]

        return ABTestListResponse(
            organization_id=organization_id,
            tests=test_responses,
            total_count=len(test_responses),
        )

    except Exception as e:
        logger.error(f"Error listing A/B tests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list A/B tests: {str(e)}",
        )


@router.patch("/{test_id}", response_model=ABTestResponse)
async def update_ab_test(
    test_id: str,
    update_data: ABTestUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update an A/B test's details or status.

    When status is changed to 'running', the start_date is automatically set.
    When status is changed to 'completed', the end_date is automatically set.

    Args:
        test_id: A/B test ID
        update_data: Fields to update
        db: Database session

    Returns:
        Updated A/B test

    Raises:
        HTTPException: If test not found or update fails
    """
    try:
        test_uuid = UUID(test_id)

        # Get existing test
        query = select(ABTest).where(ABTest.id == test_uuid)
        result = await db.execute(query)
        ab_test = result.scalar_one_or_none()

        if not ab_test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"A/B test {test_id} not found",
            )

        # Update fields
        if update_data.name is not None:
            ab_test.name = update_data.name
        if update_data.description is not None:
            ab_test.description = update_data.description
        if update_data.status is not None:
            old_status = ab_test.status
            ab_test.status = update_data.status

            # Set timestamps when status changes
            if update_data.status == ABTestStatus.RUNNING and old_status != ABTestStatus.RUNNING:
                ab_test.start_date = datetime.now()
            elif update_data.status == ABTestStatus.COMPLETED and old_status != ABTestStatus.COMPLETED:
                ab_test.end_date = datetime.now()

        await db.commit()
        await db.refresh(ab_test)

        logger.info(f"Updated A/B test {test_id}")

        return ABTestResponse(
            id=str(ab_test.id),
            organization_id=ab_test.organization_id,
            name=ab_test.name,
            description=ab_test.description,
            variant_a_profile_id=str(ab_test.variant_a_profile_id),
            variant_b_profile_id=str(ab_test.variant_b_profile_id),
            status=ab_test.status.value,
            start_date=ab_test.start_date.isoformat() if ab_test.start_date else None,
            end_date=ab_test.end_date.isoformat() if ab_test.end_date else None,
            created_by=ab_test.created_by,
            created_at=ab_test.created_at.isoformat(),
            updated_at=ab_test.updated_at.isoformat(),
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid test ID format",
        )
    except Exception as e:
        logger.error(f"Error updating A/B test {test_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update A/B test: {str(e)}",
        )


@router.post("/{test_id}/assign-variant", response_model=AssignVariantResponse)
async def assign_variant(
    test_id: str,
    request: AssignVariantRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Assign a variant (A or B) to a vacancy/resume pair for an A/B test.

    Uses a simple hash-based assignment to ensure consistent variant assignment
    for the same vacancy/resume pair. This ensures that the same candidate
    always sees the same variant for a given test.

    Args:
        test_id: A/B test ID
        request: Vacancy and resume IDs
        db: Database session

    Returns:
        Assigned variant and profile ID to use

    Raises:
        HTTPException: If test not found or not running
    """
    try:
        test_uuid = UUID(test_id)

        # Get test
        query = select(ABTest).where(ABTest.id == test_uuid)
        result = await db.execute(query)
        ab_test = result.scalar_one_or_none()

        if not ab_test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"A/B test {test_id} not found",
            )

        if ab_test.status != ABTestStatus.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A/B test must be in 'running' status to assign variants (current status: {ab_test.status.value})",
            )

        # Simple hash-based variant assignment
        # Combine vacancy_id and resume_id for consistent assignment
        assignment_key = f"{request.vacancy_id}:{request.resume_id}:{test_id}"
        hash_value = hash(assignment_key)
        variant = "a" if hash_value % 2 == 0 else "b"

        # Get the corresponding profile ID
        profile_id = ab_test.variant_a_profile_id if variant == "a" else ab_test.variant_b_profile_id

        logger.info(f"Assigned variant {variant} for test {test_id}, vacancy {request.vacancy_id}, resume {request.resume_id}")

        return AssignVariantResponse(
            ab_test_id=test_id,
            vacancy_id=request.vacancy_id,
            resume_id=request.resume_id,
            variant_assigned=variant,
            profile_id=str(profile_id),
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid test ID format",
        )
    except Exception as e:
        logger.error(f"Error assigning variant for test {test_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign variant: {str(e)}",
        )


@router.post("/{test_id}/results", response_model=RecordResultResponse, status_code=status.HTTP_201_CREATED)
async def record_result(
    test_id: str,
    result_data: RecordResultRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Record the result of a matching operation during an A/B test.

    This endpoint stores the match result and any hiring outcome for analysis.
    Results are used to compare the effectiveness of variant A vs variant B.

    Args:
        test_id: A/B test ID
        result_data: Match result details
        db: Database session

    Returns:
        Created result record

    Raises:
        HTTPException: If test not found or result recording fails
    """
    try:
        test_uuid = UUID(test_id)

        # Verify test exists
        query = select(ABTest).where(ABTest.id == test_uuid)
        result = await db.execute(query)
        ab_test = result.scalar_one_or_none()

        if not ab_test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"A/B test {test_id} not found",
            )

        # Create result record
        new_result = ABTestResult(
            id=uuid4(),
            ab_test_id=test_uuid,
            vacancy_id=UUID(result_data.vacancy_id),
            resume_id=UUID(result_data.resume_id),
            match_result_id=UUID(result_data.match_result_id),
            variant_assigned=result_data.variant_assigned,
            outcome=result_data.outcome,
        )

        db.add(new_result)
        await db.commit()
        await db.refresh(new_result)

        logger.info(f"Recorded result for A/B test {test_id}, variant {result_data.variant_assigned}")

        return RecordResultResponse(
            id=str(new_result.id),
            ab_test_id=test_id,
            vacancy_id=result_data.vacancy_id,
            resume_id=result_data.resume_id,
            variant_assigned=new_result.variant_assigned,
            outcome=new_result.outcome,
            created_at=new_result.created_at.isoformat(),
        )

    except ValueError as e:
        logger.error(f"Invalid UUID in result recording: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ID format: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error recording result for test {test_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record result: {str(e)}",
        )
