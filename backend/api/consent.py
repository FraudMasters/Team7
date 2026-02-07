"""
GDPR consent management endpoints.

This module provides endpoints for:
- Recording user consent for data processing and other GDPR purposes
- Retrieving active consents for users and organizations
- Getting consent history with full audit trail
- Withdrawing previously granted consent
- Checking consent status for specific consent types

Supports complete GDPR consent lifecycle management including granular
consent types, withdrawal tracking, and comprehensive audit trails.
"""
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.consent_record import ConsentRecord, ConsentType
from services.gdpr_service import get_gdpr_service, GDPRService

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class ConsentRecordRequest(BaseModel):
    """Request model for recording consent."""
    consent_type: str = Field(..., description="Type of consent")
    granted: bool = Field(..., description="Whether consent is granted or withdrawn")
    user_id: Optional[str] = Field(None, description="User UUID")
    organization_id: Optional[str] = Field(None, description="Organization UUID")
    consent_text: Optional[str] = Field(None, description="Legal text")
    withdrawal_reason: Optional[str] = Field(None, description="Reason for withdrawal")


class ConsentRecordResponse(BaseModel):
    """Response model for a consent record."""
    id: str = Field(..., description="Consent record ID")
    consent_type: str = Field(..., description="Type of consent")
    granted: bool = Field(..., description="Whether consent was granted")
    user_id: Optional[str] = Field(None, description="User ID")
    organization_id: Optional[str] = Field(None, description="Organization ID")
    consent_version: Optional[str] = Field(None, description="Privacy policy version")
    ip_address: Optional[str] = Field(None, description="Requester IP")
    is_active: bool = Field(..., description="Whether consent is active")
    granted_at: str = Field(..., description="When granted")
    withdrawn_at: Optional[str] = Field(None, description="When withdrawn")
    withdrawal_reason: Optional[str] = Field(None, description="Withdrawal reason")


class ConsentListResponse(BaseModel):
    """Response model for list of consents."""
    total: int = Field(..., description="Total records")
    consents: List[ConsentRecordResponse] = Field(..., description="Consent records")


class ConsentStatusResponse(BaseModel):
    """Response model for consent status check."""
    has_consent: bool = Field(..., description="Has active consent")
    consent_type: str = Field(..., description="Consent type checked")
    user_id: Optional[str] = Field(None)
    organization_id: Optional[str] = Field(None)


class WithdrawConsentRequest(BaseModel):
    """Request model for withdrawing consent."""
    consent_type: str = Field(..., description="Type to withdraw")
    user_id: Optional[str] = Field(None)
    organization_id: Optional[str] = Field(None)
    reason: Optional[str] = Field(None)


def _get_client_info(request: Request) -> tuple:
    ip = request.headers.get("X-Forwarded-For", "") or request.headers.get("X-Real-IP", "") or (request.client.host if request.client else "")
    ua = request.headers.get("User-Agent", "")
    return ip, ua


def _model_to_response(consent: ConsentRecord) -> ConsentRecordResponse:
    return ConsentRecordResponse(
        id=str(consent.id),
        consent_type=consent.consent_type.value,
        granted=consent.granted,
        user_id=str(consent.user_id) if consent.user_id else None,
        organization_id=str(consent.organization_id) if consent.organization_id else None,
        consent_version=consent.consent_version,
        ip_address=consent.ip_address,
        is_active=consent.is_active(),
        granted_at=consent.created_at.isoformat(),
        withdrawn_at=consent.withdrawn_at.isoformat() if consent.withdrawn_at else None,
        withdrawal_reason=consent.withdrawal_reason,
    )


@router.post("/", response_model=ConsentRecordResponse, status_code=201, tags=["Consent"])
async def record_consent(
    request: Request,
    data: ConsentRecordRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Record consent grant or withdrawal."""
    try:
        try:
            ct = ConsentType(data.consent_type)
        except ValueError:
            raise HTTPException(400, f"Invalid consent type: {data.consent_type}")

        ip, ua = _get_client_info(request)

        from sqlalchemy.orm import Session
        sync_db = Session(bind=db.bind)
        svc = get_gdpr_service(sync_db)

        record = svc.record_consent(
            consent_type=ct,
            granted=data.granted,
            user_id=UUID(data.user_id) if data.user_id else None,
            organization_id=UUID(data.organization_id) if data.organization_id else None,
            consent_text=data.consent_text,
            ip_address=ip,
            user_agent=ua,
            withdrawal_reason=data.withdrawal_reason if not data.granted else None,
        )

        if not record:
            raise HTTPException(500, "Failed to record consent")

        logger.info(f"Recorded consent: type={data.consent_type}, granted={data.granted}")

        return JSONResponse(status_code=201, content=_model_to_response(record).model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(500, str(e))


@router.get("/", response_model=ConsentListResponse, tags=["Consent"])
async def list_consents(
    user_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    consent_type: Optional[str] = None,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """List consent records."""
    try:
        query = select(ConsentRecord)

        if user_id:
            query = query.where(ConsentRecord.user_id == UUID(user_id))
        if organization_id:
            query = query.where(ConsentRecord.organization_id == UUID(organization_id))
        if consent_type:
            try:
                query = query.where(ConsentRecord.consent_type == ConsentType(consent_type))
            except ValueError:
                raise HTTPException(400, f"Invalid type: {consent_type}")

        if active_only:
            query = query.where(and_(ConsentRecord.granted == True, ConsentRecord.withdrawn_at.is_(None)))

        from sqlalchemy import func
        total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()

        results = (await db.execute(query.order_by(ConsentRecord.created_at.desc()).offset(skip).limit(limit))).scalars().all()

        return JSONResponse(content=ConsentListResponse(
            total=total,
            consents=[_model_to_response(c) for c in results],
        ).model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(500, str(e))


@router.get("/status", response_model=ConsentStatusResponse, tags=["Consent"])
async def check_consent_status(
    consent_type: str,
    user_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Check consent status."""
    try:
        try:
            ct = ConsentType(consent_type)
        except ValueError:
            raise HTTPException(400, f"Invalid type: {consent_type}")

        from sqlalchemy.orm import Session
        sync_db = Session(bind=db.bind)
        svc = get_gdpr_service(sync_db)

        has_it = svc.has_consent(
            user_id=UUID(user_id) if user_id else None,
            organization_id=UUID(organization_id) if organization_id else None,
            consent_type=ct,
        )

        return JSONResponse(content=ConsentStatusResponse(
            has_consent=has_it,
            consent_type=consent_type,
            user_id=user_id,
            organization_id=organization_id,
        ).model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(500, str(e))


@router.post("/withdraw", response_model=ConsentRecordResponse, tags=["Consent"])
async def withdraw_consent(
    request: Request,
    data: WithdrawConsentRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Withdraw consent."""
    try:
        try:
            ct = ConsentType(data.consent_type)
        except ValueError:
            raise HTTPException(400, f"Invalid type: {data.consent_type}")

        ip, ua = _get_client_info(request)

        from sqlalchemy.orm import Session
        sync_db = Session(bind=db.bind)
        svc = get_gdpr_service(sync_db)

        record = svc.record_consent(
            consent_type=ct,
            granted=False,
            user_id=UUID(data.user_id) if data.user_id else None,
            organization_id=UUID(data.organization_id) if data.organization_id else None,
            ip_address=ip,
            user_agent=ua,
            withdrawal_reason=data.reason,
        )

        if not record:
            raise HTTPException(500, "Failed to withdraw")

        logger.info(f"Withdrew consent: type={data.consent_type}")

        return JSONResponse(content=_model_to_response(record).model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(500, str(e))
