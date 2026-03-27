"""
Tests for bulk duplicate scanning of existing database.

This test suite validates that the bulk duplicate scanning functionality
correctly identifies and records duplicate resumes in an existing database.

Test Coverage:
- Bulk scan detects exact duplicate resumes
- Scan handles organization scoping correctly
- Scan skips already-recorded duplicates
- Scan handles missing files gracefully
- Scan reports accurate statistics
- Scan handles empty databases
- Scan handles large batches efficiently
"""
import asyncio
import tempfile
from datetime import datetime, timezone
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
        slug="test-org-bulk-scan",
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


@pytest.fixture
def second_pdf_content() -> bytes:
    """
    Create different sample PDF content for testing.

    Returns:
        bytes: Different PDF file content
    """
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<< /Size 4 /Root 1 0 R >>
startxref
200
%%EOF
"""


async def create_test_resume_with_file(
    db: AsyncSession,
    organization_id: str,
    filename: str,
    content: bytes,
    temp_dir: Path,
) -> Resume:
    """
    Helper function to create a resume with a real file on disk.

    Args:
        db: Database session
        organization_id: Organization ID
        filename: Resume filename
        content: File content
        temp_dir: Temporary directory for storing files

    Returns:
        Resume instance
    """
    # Create file on disk
    file_path = temp_dir / filename
    file_path.write_bytes(content)

    # Compute content hash
    content_hash = compute_content_hash(content)

    # Create resume record
    resume = Resume(
        organization_id=organization_id,
        filename=filename,
        file_path=str(file_path),
        content_type="application/pdf",
        status=ResumeStatus.COMPLETED,
        content_hash=content_hash,
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    return resume


@pytest.mark.asyncio
async def test_bulk_scan_detects_duplicates(
    client: AsyncClient,
    test_db: AsyncSession,
    test_organization: Organization,
    sample_pdf_content: bytes,
    second_pdf_content: bytes,
):
    """
    Test that bulk scan detects all duplicate resumes in database.

    This test validates:
    - Scan identifies resumes with identical content hashes
    - Scan creates DuplicateResume records for each duplicate pair
    - Scan reports accurate statistics
    - Scan identifies the earliest resume as the original
    """
    # Create temporary directory for test files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create resumes: 3 with same content (duplicates), 2 with different content
        resume1 = await create_test_resume_with_file(
            test_db, str(test_organization.id), "resume1.pdf", sample_pdf_content, temp_path
        )
        resume2 = await create_test_resume_with_file(
            test_db, str(test_organization.id), "resume2.pdf", sample_pdf_content, temp_path
        )
        resume3 = await create_test_resume_with_file(
            test_db, str(test_organization.id), "resume3.pdf", sample_pdf_content, temp_path
        )
        resume4 = await create_test_resume_with_file(
            test_db, str(test_organization.id), "resume4.pdf", second_pdf_content, temp_path
        )
        resume5 = await create_test_resume_with_file(
            test_db, str(test_organization.id), "resume5.pdf", second_pdf_content, temp_path
        )

        # Run bulk scan
        response = await client.post(
            "/api/duplicates/scan-existing",
            params={"organization_id": str(test_organization.id)},
        )
        assert response.status_code == 200
        data = response.json()

        # Verify scan statistics
        assert data["total_resumes_scanned"] == 5
        assert data["duplicates_found"] == 3  # 2 duplicates of resume1 + 1 duplicate of resume4
        assert data["duplicates_recorded"] == 3
        assert data["errors"] == 0
        assert data["organization_id"] == str(test_organization.id)

        # Verify duplicate records were created
        stmt = select(DuplicateResume).where(
            DuplicateResume.organization_id == str(test_organization.id)
        )
        result = await test_db.execute(stmt)
        duplicates = result.scalars().all()
        assert len(duplicates) == 3

        # Verify correct original-duplicate relationships
        # resume1 should be original for resume2 and resume3
        duplicate_pairs = [
            (dup.original_resume_id, dup.duplicate_resume_id) for dup in duplicates
        ]

        # Check that resume1 is marked as original for resume2 and resume3
        assert (str(resume1.id), str(resume2.id)) in duplicate_pairs
        assert (str(resume1.id), str(resume3.id)) in duplicate_pairs

        # Check that resume4 is marked as original for resume5
        assert (str(resume4.id), str(resume5.id)) in duplicate_pairs


@pytest.mark.asyncio
async def test_bulk_scan_organization_scoping(
    client: AsyncClient,
    test_db: AsyncSession,
    sample_pdf_content: bytes,
):
    """
    Test that bulk scan respects organization boundaries.

    This test validates:
    - Scan only processes resumes for the specified organization
    - Duplicates are not detected across organizations
    - Each organization's duplicates are tracked separately
    """
    # Create two organizations
    org1 = Organization(name="Organization 1", slug="org-1-bulk")
    org2 = Organization(name="Organization 2", slug="org-2-bulk")
    test_db.add(org1)
    test_db.add(org2)
    await test_db.commit()
    await test_db.refresh(org1)
    await test_db.refresh(org2)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create identical resumes in both organizations
        await create_test_resume_with_file(
            test_db, str(org1.id), "resume_org1_1.pdf", sample_pdf_content, temp_path
        )
        await create_test_resume_with_file(
            test_db, str(org1.id), "resume_org1_2.pdf", sample_pdf_content, temp_path
        )
        await create_test_resume_with_file(
            test_db, str(org2.id), "resume_org2_1.pdf", sample_pdf_content, temp_path
        )
        await create_test_resume_with_file(
            test_db, str(org2.id), "resume_org2_2.pdf", sample_pdf_content, temp_path
        )

        # Scan org1
        response1 = await client.post(
            "/api/duplicates/scan-existing",
            params={"organization_id": str(org1.id)},
        )
        assert response1.status_code == 200
        data1 = response1.json()

        # Should find 1 duplicate in org1 (2 resumes with same content)
        assert data1["total_resumes_scanned"] == 2
        assert data1["duplicates_found"] == 1
        assert data1["organization_id"] == str(org1.id)

        # Scan org2
        response2 = await client.post(
            "/api/duplicates/scan-existing",
            params={"organization_id": str(org2.id)},
        )
        assert response2.status_code == 200
        data2 = response2.json()

        # Should find 1 duplicate in org2 (2 resumes with same content)
        assert data2["total_resumes_scanned"] == 2
        assert data2["duplicates_found"] == 1
        assert data2["organization_id"] == str(org2.id)

        # Verify duplicate records are organization-scoped
        stmt1 = select(DuplicateResume).where(DuplicateResume.organization_id == str(org1.id))
        result1 = await test_db.execute(stmt1)
        org1_duplicates = result1.scalars().all()
        assert len(org1_duplicates) == 1

        stmt2 = select(DuplicateResume).where(DuplicateResume.organization_id == str(org2.id))
        result2 = await test_db.execute(stmt2)
        org2_duplicates = result2.scalars().all()
        assert len(org2_duplicates) == 1


@pytest.mark.asyncio
async def test_bulk_scan_skips_already_recorded_duplicates(
    client: AsyncClient,
    test_db: AsyncSession,
    test_organization: Organization,
    sample_pdf_content: bytes,
):
    """
    Test that bulk scan doesn't re-record already detected duplicates.

    This test validates:
    - Scan checks for existing DuplicateResume records
    - Scan doesn't create duplicate records for same pair
    - Statistics reflect skipped duplicates
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create duplicate resumes
        resume1 = await create_test_resume_with_file(
            test_db, str(test_organization.id), "resume1.pdf", sample_pdf_content, temp_path
        )
        resume2 = await create_test_resume_with_file(
            test_db, str(test_organization.id), "resume2.pdf", sample_pdf_content, temp_path
        )

        # Manually create a duplicate record (simulating previous scan)
        content_hash = compute_content_hash(sample_pdf_content)
        existing_duplicate = DuplicateResume(
            organization_id=str(test_organization.id),
            original_resume_id=str(resume1.id),
            duplicate_resume_id=str(resume2.id),
            content_hash=content_hash,
            detection_timestamp=datetime.now(timezone.utc),
        )
        test_db.add(existing_duplicate)
        await test_db.commit()

        # Run bulk scan
        response = await client.post(
            "/api/duplicates/scan-existing",
            params={"organization_id": str(test_organization.id)},
        )
        assert response.status_code == 200
        data = response.json()

        # Should detect the duplicate but not record it again
        assert data["total_resumes_scanned"] == 2
        assert data["duplicates_found"] == 1
        # duplicates_recorded should be 0 because it was already recorded
        assert data["duplicates_recorded"] == 0

        # Verify only one duplicate record exists
        stmt = select(DuplicateResume).where(
            DuplicateResume.organization_id == str(test_organization.id)
        )
        result = await test_db.execute(stmt)
        duplicates = result.scalars().all()
        assert len(duplicates) == 1


@pytest.mark.asyncio
async def test_bulk_scan_handles_missing_files(
    client: AsyncClient,
    test_db: AsyncSession,
    test_organization: Organization,
    sample_pdf_content: bytes,
):
    """
    Test that bulk scan handles missing files gracefully.

    This test validates:
    - Scan continues processing even if some files are missing
    - Missing files are counted as errors
    - Other resumes are still processed correctly
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create resume with valid file
        resume1 = await create_test_resume_with_file(
            test_db, str(test_organization.id), "resume1.pdf", sample_pdf_content, temp_path
        )

        # Create resume with missing file
        missing_file_path = temp_path / "missing.pdf"
        resume2 = Resume(
            organization_id=str(test_organization.id),
            filename="missing.pdf",
            file_path=str(missing_file_path),  # File doesn't exist
            content_type="application/pdf",
            status=ResumeStatus.COMPLETED,
        )
        test_db.add(resume2)
        await test_db.commit()
        await test_db.refresh(resume2)

        # Create another resume with valid file
        resume3 = await create_test_resume_with_file(
            test_db, str(test_organization.id), "resume3.pdf", sample_pdf_content, temp_path
        )

        # Run bulk scan
        response = await client.post(
            "/api/duplicates/scan-existing",
            params={"organization_id": str(test_organization.id)},
        )
        assert response.status_code == 200
        data = response.json()

        # Should process all 3 resumes, with 1 error for missing file
        assert data["total_resumes_scanned"] == 3
        assert data["errors"] == 1  # Missing file error
        # Should still detect duplicate between resume1 and resume3
        assert data["duplicates_found"] == 1


@pytest.mark.asyncio
async def test_bulk_scan_empty_database(
    client: AsyncClient,
    test_db: AsyncSession,
    test_organization: Organization,
):
    """
    Test that bulk scan handles empty database correctly.

    This test validates:
    - Scan returns appropriate response for empty database
    - No errors occur when no resumes exist
    """
    # Run bulk scan on empty database
    response = await client.post(
        "/api/duplicates/scan-existing",
        params={"organization_id": str(test_organization.id)},
    )
    assert response.status_code == 200
    data = response.json()

    # Should report zero for all metrics
    assert data["total_resumes_scanned"] == 0
    assert data["duplicates_found"] == 0
    assert data["duplicates_recorded"] == 0
    assert data["errors"] == 0
    assert data["message"] == "No resumes found to scan"


@pytest.mark.asyncio
async def test_bulk_scan_updates_content_hash(
    client: AsyncClient,
    test_db: AsyncSession,
    test_organization: Organization,
    sample_pdf_content: bytes,
):
    """
    Test that bulk scan updates content_hash for resumes that don't have one.

    This test validates:
    - Scan computes content_hash for resumes without it
    - Resume records are updated with computed hash
    - Duplicates are still detected correctly
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create resume WITHOUT content_hash (simulating old resume before hashing was added)
        file_path = temp_path / "resume1.pdf"
        file_path.write_bytes(sample_pdf_content)

        resume1 = Resume(
            organization_id=str(test_organization.id),
            filename="resume1.pdf",
            file_path=str(file_path),
            content_type="application/pdf",
            status=ResumeStatus.COMPLETED,
            content_hash=None,  # No hash initially
        )
        test_db.add(resume1)
        await test_db.commit()
        await test_db.refresh(resume1)

        # Verify no hash initially
        assert resume1.content_hash is None

        # Create another resume with same content but WITH hash
        resume2 = await create_test_resume_with_file(
            test_db, str(test_organization.id), "resume2.pdf", sample_pdf_content, temp_path
        )
        assert resume2.content_hash is not None

        # Run bulk scan
        response = await client.post(
            "/api/duplicates/scan-existing",
            params={"organization_id": str(test_organization.id)},
        )
        assert response.status_code == 200
        data = response.json()

        # Should detect duplicate
        assert data["duplicates_found"] == 1

        # Verify resume1 now has content_hash
        await test_db.refresh(resume1)
        assert resume1.content_hash is not None
        assert resume1.content_hash == resume2.content_hash


@pytest.mark.asyncio
async def test_bulk_scan_skips_failed_resumes(
    client: AsyncClient,
    test_db: AsyncSession,
    test_organization: Organization,
    sample_pdf_content: bytes,
):
    """
    Test that bulk scan skips resumes with FAILED status.

    This test validates:
    - Scan ignores resumes with status=FAILED
    - Failed resumes are not included in scan count
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create successful resume
        resume1 = await create_test_resume_with_file(
            test_db, str(test_organization.id), "resume1.pdf", sample_pdf_content, temp_path
        )

        # Create failed resume with same content
        file_path = temp_path / "failed.pdf"
        file_path.write_bytes(sample_pdf_content)

        resume2 = Resume(
            organization_id=str(test_organization.id),
            filename="failed.pdf",
            file_path=str(file_path),
            content_type="application/pdf",
            status=ResumeStatus.FAILED,  # Failed status
            content_hash=compute_content_hash(sample_pdf_content),
        )
        test_db.add(resume2)
        await test_db.commit()

        # Run bulk scan
        response = await client.post(
            "/api/duplicates/scan-existing",
            params={"organization_id": str(test_organization.id)},
        )
        assert response.status_code == 200
        data = response.json()

        # Should only scan the successful resume (failed resume is excluded)
        assert data["total_resumes_scanned"] == 1
        assert data["duplicates_found"] == 0


@pytest.mark.asyncio
async def test_bulk_scan_missing_organization_id(
    client: AsyncClient,
    test_db: AsyncSession,
):
    """
    Test that bulk scan returns error when organization_id is missing.

    This test validates:
    - Scan requires organization_id parameter
    - Returns 400 error for missing organization_id
    """
    # Run bulk scan without organization_id
    response = await client.post("/api/duplicates/scan-existing")
    assert response.status_code == 400
    data = response.json()
    assert "organization_id is required" in data["detail"]


@pytest.mark.asyncio
async def test_bulk_scan_large_batch(
    client: AsyncClient,
    test_db: AsyncSession,
    test_organization: Organization,
    sample_pdf_content: bytes,
    second_pdf_content: bytes,
):
    """
    Test that bulk scan handles large batches efficiently.

    This test validates:
    - Scan processes large numbers of resumes
    - Correctly identifies all duplicate pairs
    - Reports accurate statistics
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create 20 resumes: 10 duplicates of content1, 5 duplicates of content2, 5 unique
        resumes_content1 = []
        for i in range(10):
            resume = await create_test_resume_with_file(
                test_db,
                str(test_organization.id),
                f"resume_batch1_{i}.pdf",
                sample_pdf_content,
                temp_path,
            )
            resumes_content1.append(resume)

        resumes_content2 = []
        for i in range(5):
            resume = await create_test_resume_with_file(
                test_db,
                str(test_organization.id),
                f"resume_batch2_{i}.pdf",
                second_pdf_content,
                temp_path,
            )
            resumes_content2.append(resume)

        # Create 5 unique resumes
        for i in range(5):
            unique_content = sample_pdf_content.replace(b"Test Resume", f"Resume {i}".encode())
            await create_test_resume_with_file(
                test_db,
                str(test_organization.id),
                f"resume_unique_{i}.pdf",
                unique_content,
                temp_path,
            )

        # Run bulk scan
        response = await client.post(
            "/api/duplicates/scan-existing",
            params={"organization_id": str(test_organization.id)},
        )
        assert response.status_code == 200
        data = response.json()

        # Verify statistics
        assert data["total_resumes_scanned"] == 20
        # 10 resumes with content1: 9 duplicates of first one
        # 5 resumes with content2: 4 duplicates of first one
        # Total: 9 + 4 = 13 duplicates
        assert data["duplicates_found"] == 13
        assert data["duplicates_recorded"] == 13
        assert data["errors"] == 0

        # Verify all duplicates were recorded
        stmt = select(DuplicateResume).where(
            DuplicateResume.organization_id == str(test_organization.id)
        )
        result = await test_db.execute(stmt)
        duplicates = result.scalars().all()
        assert len(duplicates) == 13
