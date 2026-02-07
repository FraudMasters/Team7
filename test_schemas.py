#!/usr/bin/env python
"""Simple test script to verify interview schemas import correctly"""
import sys

try:
    from backend.schemas.interview_schemas import (
        InterviewCreate,
        InterviewResponse,
        InterviewUpdate,
        InterviewListResponse,
        InterviewParticipantCreate,
        InterviewParticipantUpdate,
        InterviewParticipantResponse,
        InterviewAvailabilityCheck,
        InterviewAvailabilityResponse,
        AvailabilitySlot,
        InterviewStatus,
        InterviewType,
        ParticipantRole,
        ParticipantStatus,
    )
    print("✓ All interview schemas imported successfully")
    print(f"✓ InterviewCreate: {InterviewCreate}")
    print(f"✓ InterviewResponse: {InterviewResponse}")
    print("✓ Schemas OK")
    sys.exit(0)
except Exception as e:
    print(f"✗ Error importing schemas: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
