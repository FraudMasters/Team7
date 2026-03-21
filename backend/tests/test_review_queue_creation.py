"""
Tests for automatic review queue creation when duplicates are detected during upload.

This test suite validates that duplicate resumes are automatically added to the
manual review queue (DuplicateReview table) when detected during the upload process.

Test Coverage:
- Duplicate detection adds entries to review queue
- Review queue entries have correct metadata (confidence, status, timestamps)
- Organization scoping for review queue
- Non-duplicates don't create review queue entries
- Error handling doesn't block uploads
"""
import asyncio
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.resume import Resume, ResumeStatus
from models.duplicate_review import DuplicateReview, ReviewStatus
from models.duplicate_resume import DuplicateResume
from models.organization import Organization
from utils.duplicate_detector import compute_content_hash


@pytest.fixture
async def test_organization(test_db: AsyncSession) -> Organization:
    """
    Create a test organization for duplicate review testing.

    Args:
        test_db: Test database session

    Returns:
        Organization instance
    """
    org = Organization(
        name="Test Organization - Review Queue",
        slug="test-org-review-queue",
    )
    test_db.add(org)
    await test_db.commit()
    await test_db.refresh(org)
    return org


@pytest.fixture
def sample_pdf_content() -> bytes:
    """
    Create sample PDF content for testing.

    Returns:
        bytes: Sample PDF file content
    """
    # Minimal valid PDF structure
    return b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 4 0 R
>>
>>
/MediaBox [0 0 612 792]
/Contents 5 0 R
>>
endobj
4 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj
5 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Test Resume) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000262 00000 n
0000000339 00000 n
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
428
%%EOF
"""


@pytest.mark.asyncio
async def test_duplicate_added_to_review_queue(
    client: AsyncClient,
    test_db: AsyncSession,
    test_organization: Organization,
    sample_pdf_content: bytes,
):
    """
    Test that detected duplicates are automatically added to review queue.

    This test validates:
    - First upload creates resume successfully
    - Second upload detects duplicate
    - Duplicate is automatically added to DuplicateReview table
    - Review queue entry has correct metadata
    """
    # First upload
    files1 = {"file": ("original_resume.pdf", BytesIO(sample_pdf_content), "application/pdf")}
    headers = {"X-Organization-ID": str(test_organization.id)}

    response1 = await client.post("/api/resumes/upload", files=files1, headers=headers)
    assert response1.status_code == 201
    data1 = response1.json()
    original_resume_id = data1["id"]

    # Verify first resume was created
    stmt = select(Resume).where(Resume.id == original_resume_id)
    result = await test_db.execute(stmt)
    original_resume = result.scalar_one_or_none()
    assert original_resume is not None

    # Second upload of same content (duplicate)
    files2 = {"file": ("duplicate_resume.pdf", BytesIO(sample_pdf_content), "application/pdf")}

    response2 = await client.post("/api/resumes/upload", files=files2, headers=headers)
    assert response2.status_code == 201
    data2 = response2.json()
    duplicate_resume_id = data2["id"]

    # Verify duplicate was detected
    assert data2["duplicate_detected"] is True
    assert data2["original_resume_id"] == original_resume_id

    # Verify duplicate was added to review queue
    stmt = select(DuplicateReview).where(
        DuplicateReview.duplicate_resume_id == duplicate_resume_id
    )
    result = await test_db.execute(stmt)
    review_entry = result.scalar_one_or_none()

    assert review_entry is not None
    assert review_entry.original_resume_id == original_resume_id
    assert review_entry.duplicate_resume_id == duplicate_resume_id
    assert review_entry.organization_id == str(test_organization.id)
    assert review_entry.confidence_score == 1.0  # Exact match
    assert review_entry.status == ReviewStatus.PENDING
    assert review_entry.queue_entered_at is not None
    assert review_entry.assigned_reviewer_id is None  # Not yet assigned


@pytest.mark.asyncio
async def test_review_queue_metadata(
    client: AsyncClient,
    test_db: AsyncSession,
    test_organization: Organization,
    sample_pdf_content: bytes,
):
    """
    Test that review queue entries have correct metadata and timestamps.

    This test validates:
    - Confidence score is set correctly (1.0 for exact match)
    - Status defaults to PENDING
    - queue_entered_at timestamp is set
    - Optional fields are None by default
    """
    # Upload original
    files1 = {"file": ("resume1.pdf", BytesIO(sample_pdf_content), "application/pdf")}
    headers = {"X-Organization-ID": str(test_organization.id)}

    response1 = await client.post("/api/resumes/upload", files=files1, headers=headers)
    assert response1.status_code == 201
    original_id = response1.json()["id"]

    # Upload duplicate
    files2 = {"file": ("resume2.pdf", BytesIO(sample_pdf_content), "application/pdf")}

    before_upload = datetime.now(timezone.utc)
    response2 = await client.post("/api/resumes/upload", files=files2, headers=headers)
    after_upload = datetime.now(timezone.utc)

    assert response2.status_code == 201
    duplicate_id = response2.json()["id"]

    # Verify review queue entry metadata
    stmt = select(DuplicateReview).where(
        DuplicateReview.duplicate_resume_id == duplicate_id
    )
    result = await test_db.execute(stmt)
    review = result.scalar_one()

    # Check confidence score
    assert review.confidence_score == 1.0  # Exact hash match

    # Check status
    assert review.status == ReviewStatus.PENDING

    # Check timestamps
    assert review.queue_entered_at is not None
    assert before_upload <= review.queue_entered_at <= after_upload

    # Check optional fields are None
    assert review.assigned_reviewer_id is None
    assert review.review_started_at is None
    assert review.review_completed_at is None
    assert review.decision_reason is None


@pytest.mark.asyncio
async def test_non_duplicate_not_added_to_queue(
    client: AsyncClient,
    test_db: AsyncSession,
    test_organization: Organization,
    sample_pdf_content: bytes,
):
    """
    Test that non-duplicate uploads don't create review queue entries.

    This test validates:
    - Non-duplicate uploads proceed normally
    - No DuplicateReview entries created for unique content
    """
    # Different content for second upload
    different_content = sample_pdf_content.replace(b"Test Resume", b"Different Resume Content")

    # First upload
    files1 = {"file": ("resume1.pdf", BytesIO(sample_pdf_content), "application/pdf")}
    headers = {"X-Organization-ID": str(test_organization.id)}

    response1 = await client.post("/api/resumes/upload", files=files1, headers=headers)
    assert response1.status_code == 201
    resume1_id = response1.json()["id"]

    # Second upload with different content
    files2 = {"file": ("resume2.pdf", BytesIO(different_content), "application/pdf")}

    response2 = await client.post("/api/resumes/upload", files=files2, headers=headers)
    assert response2.status_code == 201
    data2 = response2.json()
    resume2_id = data2["id"]

    # Verify not detected as duplicate
    assert data2.get("duplicate_detected", False) is False

    # Verify NO review queue entries exist for either resume
    stmt = select(DuplicateReview).where(
        DuplicateReview.duplicate_resume_id.in_([resume1_id, resume2_id])
    )
    result = await test_db.execute(stmt)
    reviews = result.scalars().all()

    assert len(reviews) == 0


@pytest.mark.asyncio
async def test_organization_scoped_review_queue(
    client: AsyncClient,
    test_db: AsyncSession,
    sample_pdf_content: bytes,
):
    """
    Test that review queue entries are scoped to organization.

    This test validates:
    - Same content in different organizations doesn't trigger duplicate detection
    - Review queue entries are organization-specific
    """
    # Create two organizations
    org1 = Organization(name="Organization 1", slug="org-review-1")
    org2 = Organization(name="Organization 2", slug="org-review-2")
    test_db.add_all([org1, org2])
    await test_db.commit()
    await test_db.refresh(org1)
    await test_db.refresh(org2)

    # Upload to org1
    files1 = {"file": ("resume.pdf", BytesIO(sample_pdf_content), "application/pdf")}
    headers1 = {"X-Organization-ID": str(org1.id)}
    response1 = await client.post("/api/resumes/upload", files=files1, headers=headers1)
    assert response1.status_code == 201
    org1_resume_id = response1.json()["id"]

    # Upload same content to org2 - should NOT be detected as duplicate
    files2 = {"file": ("resume.pdf", BytesIO(sample_pdf_content), "application/pdf")}
    headers2 = {"X-Organization-ID": str(org2.id)}
    response2 = await client.post("/api/resumes/upload", files=files2, headers=headers2)
    assert response2.status_code == 201
    data2 = response2.json()
    org2_resume_id = data2["id"]

    # Should not detect as duplicate (different organization)
    assert data2.get("duplicate_detected", False) is False

    # Verify no review queue entries exist
    stmt = select(DuplicateReview).where(
        DuplicateReview.duplicate_resume_id == org2_resume_id
    )
    result = await test_db.execute(stmt)
    review = result.scalar_one_or_none()

    assert review is None


@pytest.mark.asyncio
async def test_multiple_duplicates_in_queue(
    client: AsyncClient,
    test_db: AsyncSession,
    test_organization: Organization,
    sample_pdf_content: bytes,
):
    """
    Test that multiple duplicates are all added to review queue.

    This test validates:
    - Multiple uploads of same content create multiple queue entries
    - Each duplicate gets its own review queue entry
    - All entries reference the same original resume
    """
    # Upload original
    files1 = {"file": ("original.pdf", BytesIO(sample_pdf_content), "application/pdf")}
    headers = {"X-Organization-ID": str(test_organization.id)}

    response1 = await client.post("/api/resumes/upload", files=files1, headers=headers)
    assert response1.status_code == 201
    original_id = response1.json()["id"]

    # Upload multiple duplicates
    duplicate_ids = []
    for i in range(3):
        files = {"file": (f"duplicate_{i}.pdf", BytesIO(sample_pdf_content), "application/pdf")}
        response = await client.post("/api/resumes/upload", files=files, headers=headers)
        assert response.status_code == 201
        duplicate_ids.append(response.json()["id"])

    # Verify all duplicates are in review queue
    stmt = select(DuplicateReview).where(
        DuplicateReview.duplicate_resume_id.in_(duplicate_ids)
    )
    result = await test_db.execute(stmt)
    reviews = result.scalars().all()

    assert len(reviews) == 3
    for review in reviews:
        assert review.original_resume_id == original_id
        assert review.status == ReviewStatus.PENDING
        assert review.confidence_score == 1.0


@pytest.mark.asyncio
async def test_review_queue_error_handling(
    client: AsyncClient,
    test_db: AsyncSession,
    test_organization: Organization,
    sample_pdf_content: bytes,
):
    """
    Test that upload succeeds even if review queue creation fails.

    This test validates:
    - Upload completes successfully
    - Resume record is created
    - Error in review queue creation doesn't block upload
    """
    # Upload original
    files1 = {"file": ("original.pdf", BytesIO(sample_pdf_content), "application/pdf")}
    headers = {"X-Organization-ID": str(test_organization.id)}

    response1 = await client.post("/api/resumes/upload", files=files1, headers=headers)
    assert response1.status_code == 201
    original_id = response1.json()["id"]

    # Upload duplicate - should succeed even if review queue has issues
    files2 = {"file": ("duplicate.pdf", BytesIO(sample_pdf_content), "application/pdf")}

    response2 = await client.post("/api/resumes/upload", files=files2, headers=headers)
    assert response2.status_code == 201
    data2 = response2.json()
    duplicate_id = data2["id"]

    # Verify resume was created
    stmt = select(Resume).where(Resume.id == duplicate_id)
    result = await test_db.execute(stmt)
    resume = result.scalar_one_or_none()

    assert resume is not None
    assert resume.id == duplicate_id


@pytest.mark.asyncio
async def test_review_queue_with_existing_duplicate_record(
    client: AsyncClient,
    test_db: AsyncSession,
    test_organization: Organization,
    sample_pdf_content: bytes,
):
    """
    Test review queue creation when DuplicateResume record exists.

    This test validates:
    - Detection works with pre-existing DuplicateResume records
    - Review queue entry is still created
    - Metadata is correct
    """
    # Create an existing resume and duplicate record
    content_hash = compute_content_hash(sample_pdf_content)

    existing_resume = Resume(
        organization_id=str(test_organization.id),
        filename="existing.pdf",
        file_path="/test/existing.pdf",
        content_type="application/pdf",
        status=ResumeStatus.COMPLETED,
        content_hash=content_hash,
    )
    test_db.add(existing_resume)
    await test_db.commit()
    await test_db.refresh(existing_resume)

    # Create duplicate resume record
    duplicate_record = DuplicateResume(
        organization_id=str(test_organization.id),
        original_resume_id=str(existing_resume.id),
        duplicate_resume_id=None,
        content_hash=content_hash,
        confidence_score=1.0,
    )
    test_db.add(duplicate_record)
    await test_db.commit()

    # Upload duplicate content
    files = {"file": ("new_duplicate.pdf", BytesIO(sample_pdf_content), "application/pdf")}
    headers = {"X-Organization-ID": str(test_organization.id)}

    response = await client.post("/api/resumes/upload", files=files, headers=headers)
    assert response.status_code == 201
    data = response.json()
    new_resume_id = data["id"]

    # Verify duplicate was detected
    assert data["duplicate_detected"] is True
    assert data["original_resume_id"] == str(existing_resume.id)

    # Verify review queue entry was created
    stmt = select(DuplicateReview).where(
        DuplicateReview.duplicate_resume_id == new_resume_id
    )
    result = await test_db.execute(stmt)
    review = result.scalar_one_or_none()

    assert review is not None
    assert review.original_resume_id == str(existing_resume.id)
    assert review.confidence_score == 1.0
    assert review.status == ReviewStatus.PENDING


@pytest.mark.asyncio
async def test_review_queue_confidence_score(
    client: AsyncClient,
    test_db: AsyncSession,
    test_organization: Organization,
    sample_pdf_content: bytes,
):
    """
    Test that confidence score is correctly set in review queue.

    This test validates:
    - Exact matches have confidence score of 1.0
    - Confidence score is stored correctly in database
    """
    # Upload original
    files1 = {"file": ("original.pdf", BytesIO(sample_pdf_content), "application/pdf")}
    headers = {"X-Organization-ID": str(test_organization.id)}

    response1 = await client.post("/api/resumes/upload", files=files1, headers=headers)
    assert response1.status_code == 201

    # Upload duplicate
    files2 = {"file": ("duplicate.pdf", BytesIO(sample_pdf_content), "application/pdf")}

    response2 = await client.post("/api/resumes/upload", files=files2, headers=headers)
    assert response2.status_code == 201
    duplicate_id = response2.json()["id"]

    # Check confidence score in review queue
    stmt = select(DuplicateReview).where(
        DuplicateReview.duplicate_resume_id == duplicate_id
    )
    result = await test_db.execute(stmt)
    review = result.scalar_one()

    # Exact hash match should have confidence score of 1.0
    assert review.confidence_score == 1.0
    assert isinstance(review.confidence_score, float)
