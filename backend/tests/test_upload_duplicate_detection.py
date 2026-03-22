"""
Tests for duplicate detection during resume upload.

This test suite validates that the duplicate detection system is properly
integrated into the resume upload workflow to prevent duplicate uploads.

Test Coverage:
- Duplicate detection runs automatically on upload
- Duplicate matches are returned in upload response
- Non-duplicate uploads proceed normally
- Content hash is computed and stored
- Organization-scoped duplicate detection
"""
import asyncio
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.resume import Resume, ResumeStatus
from models.duplicate_resume import DuplicateResume
from models.organization import Organization
from utils.duplicate_detector import compute_content_hash


@pytest.fixture
async def test_organization(test_db: AsyncSession) -> Organization:
    """
    Create a test organization for duplicate detection testing.

    Args:
        test_db: Test database session

    Returns:
        Organization instance
    """
    org = Organization(
        name="Test Organization",
        slug="test-org-duplicate",
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
async def test_duplicate_detection_runs_on_upload(
    client: AsyncClient,
    test_db: AsyncSession,
    test_organization: Organization,
    sample_pdf_content: bytes,
):
    """
    Test that duplicate detection runs automatically during resume upload.

    This test validates:
    - Duplicate detection is triggered on upload
    - First upload creates resume successfully
    - Second upload of same content is detected as duplicate
    - Duplicate information is returned in response
    """
    # First upload should succeed
    files = {"file": ("test_resume.pdf", BytesIO(sample_pdf_content), "application/pdf")}

    response1 = await client.post("/api/resumes/upload", files=files)
    assert response1.status_code == 201
    data1 = response1.json()

    assert "id" in data1
    assert data1["filename"] == "test_resume.pdf"
    assert data1["status"] == "pending"

    # Verify resume was created in database
    resume_id = data1["id"]
    stmt = select(Resume).where(Resume.id == resume_id)
    result = await test_db.execute(stmt)
    resume1 = result.scalar_one_or_none()
    assert resume1 is not None
    assert resume1.content_hash is not None

    # Second upload of same content should detect duplicate
    files2 = {"file": ("test_resume_copy.pdf", BytesIO(sample_pdf_content), "application/pdf")}

    response2 = await client.post("/api/resumes/upload", files=files2)
    assert response2.status_code == 201
    data2 = response2.json()

    # Should indicate duplicate was detected
    assert "duplicate_detected" in data2
    assert data2["duplicate_detected"] is True
    assert "original_resume_id" in data2
    assert data2["original_resume_id"] == resume_id
    assert "content_hash" in data2


@pytest.mark.asyncio
async def test_non_duplicate_upload_proceeds_normally(
    client: AsyncClient,
    test_db: AsyncSession,
    test_organization: Organization,
    sample_pdf_content: bytes,
):
    """
    Test that non-duplicate uploads proceed normally.

    This test validates:
    - Uploads with different content proceed normally
    - No duplicate detection warnings for unique content
    - Content hash is still computed and stored
    """
    # Different content for second upload
    different_content = sample_pdf_content.replace(b"Test Resume", b"Different Resume")

    # First upload
    files1 = {"file": ("resume1.pdf", BytesIO(sample_pdf_content), "application/pdf")}
    response1 = await client.post("/api/resumes/upload", files=files1)
    assert response1.status_code == 201
    data1 = response1.json()

    # Second upload with different content
    files2 = {"file": ("resume2.pdf", BytesIO(different_content), "application/pdf")}
    response2 = await client.post("/api/resumes/upload", files=files2)
    assert response2.status_code == 201
    data2 = response2.json()

    # Should not indicate duplicate
    assert data2.get("duplicate_detected", False) is False
    assert "original_resume_id" not in data2

    # Both resumes should exist in database
    stmt = select(Resume).where(Resume.id.in_([data1["id"], data2["id"]]))
    result = await test_db.execute(stmt)
    resumes = result.scalars().all()
    assert len(resumes) == 2


@pytest.mark.asyncio
async def test_content_hash_is_computed_and_stored(
    client: AsyncClient,
    test_db: AsyncSession,
    test_organization: Organization,
    sample_pdf_content: bytes,
):
    """
    Test that content hash is computed and stored during upload.

    This test validates:
    - Content hash is computed from file content
    - Hash is stored in Resume record
    - Hash matches expected SHA-256 value
    """
    files = {"file": ("test_resume.pdf", BytesIO(sample_pdf_content), "application/pdf")}

    response = await client.post("/api/resumes/upload", files=files)
    assert response.status_code == 201
    data = response.json()

    # Verify resume has content_hash
    stmt = select(Resume).where(Resume.id == data["id"])
    result = await test_db.execute(stmt)
    resume = result.scalar_one()

    assert resume.content_hash is not None
    assert len(resume.content_hash) == 64  # SHA-256 produces 64-char hex string

    # Verify hash matches expected value
    expected_hash = compute_content_hash(sample_pdf_content)
    assert resume.content_hash == expected_hash


@pytest.mark.asyncio
async def test_organization_scoped_duplicate_detection(
    client: AsyncClient,
    test_db: AsyncSession,
    sample_pdf_content: bytes,
):
    """
    Test that duplicate detection is scoped to organization.

    This test validates:
    - Same content in different organizations is not detected as duplicate
    - Duplicate detection respects organization boundaries
    """
    # Create two organizations
    org1 = Organization(name="Organization 1", slug="org-1")
    org2 = Organization(name="Organization 2", slug="org-2")
    test_db.add(org1)
    test_db.add(org2)
    await test_db.commit()
    await test_db.refresh(org1)
    await test_db.refresh(org2)

    # Upload same content to org1
    files1 = {"file": ("resume.pdf", BytesIO(sample_pdf_content), "application/pdf")}
    headers1 = {"X-Organization-ID": str(org1.id)}
    response1 = await client.post("/api/resumes/upload", files=files1, headers=headers1)
    assert response1.status_code == 201

    # Upload same content to org2 - should NOT be detected as duplicate
    files2 = {"file": ("resume.pdf", BytesIO(sample_pdf_content), "application/pdf")}
    headers2 = {"X-Organization-ID": str(org2.id)}
    response2 = await client.post("/api/resumes/upload", files=files2, headers=headers2)
    assert response2.status_code == 201
    data2 = response2.json()

    # Should not detect as duplicate (different organization)
    assert data2.get("duplicate_detected", False) is False


@pytest.mark.asyncio
async def test_duplicate_detection_with_existing_duplicate_record(
    client: AsyncClient,
    test_db: AsyncSession,
    test_organization: Organization,
    sample_pdf_content: bytes,
):
    """
    Test duplicate detection when DuplicateResume record already exists.

    This test validates:
    - Detection works with pre-existing DuplicateResume records
    - Matches against DuplicateResume table entries
    """
    # Create an existing resume and duplicate record
    content_hash = compute_content_hash(sample_pdf_content)

    existing_resume = Resume(
        organization_id=str(test_organization.id),
        filename="original.pdf",
        file_path="/test/original.pdf",
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

    # Upload same content - should detect as duplicate
    files = {"file": ("new_resume.pdf", BytesIO(sample_pdf_content), "application/pdf")}
    response = await client.post("/api/resumes/upload", files=files)
    assert response.status_code == 201
    data = response.json()

    assert data["duplicate_detected"] is True
    assert data["original_resume_id"] == str(existing_resume.id)


@pytest.mark.asyncio
async def test_duplicate_detection_error_handling(
    client: AsyncClient,
    test_db: AsyncSession,
    test_organization: Organization,
):
    """
    Test that upload doesn't fail if duplicate detection encounters an error.

    This test validates:
    - Upload proceeds even if duplicate detection fails
    - Errors are logged but don't block upload
    """
    # Upload with invalid/empty content that might cause detection errors
    # This should still complete the upload
    minimal_content = b"%PDF-1.4\n%%EOF\n"
    files = {"file": ("empty.pdf", BytesIO(minimal_content), "application/pdf")}

    response = await client.post("/api/resumes/upload", files=files)

    # Should succeed even if duplicate detection has issues
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
