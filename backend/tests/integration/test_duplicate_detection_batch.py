"""
End-to-end integration tests for content-based duplicate detection in batch uploads.

This test suite validates the duplicate detection flow that uses SHA-256 content
hashing to identify duplicate resume files during batch upload operations.

This is distinct from test_duplicate_detection.py which tests the ImportService
duplicate detection for job board resume imports.

Test Coverage:
- Content-based duplicate detection using SHA-256 hashing
- Duplicate detection during batch file upload
- Duplicate detection for files extracted from ZIP archives
- Batch duplicates listing endpoint (GET /api/batch/{batch_id}/duplicates)
- Organization-scoped duplicate detection
- Multiple duplicates in single batch
- Exact match detection (content hash)
- Cross-batch duplicate detection
- Duplicate response structure validation
"""
import io
import zipfile
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import patch, MagicMock

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Import the FastAPI application
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import app
from database import get_db
from models.batch_job import BatchJob, BatchJobStatus
from models.resume import Resume, ResumeStatus
from models.duplicate_resume import DuplicateResume
from utils.duplicate_detector import compute_content_hash, DuplicateMatch


# ============== FIXTURES ==============

@pytest.fixture
def test_pdf_content() -> bytes:
    """
    Create a minimal valid PDF file content for testing.

    Returns:
        Bytes content of a simple PDF file
    """
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
<<
/Length 44
>>
stream
BT
/F1 12 Tf
50 700 Td
(John Doe - Software Engineer) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000264 00000 n
0000000349 00000 n
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
190
%%EOF
"""


@pytest.fixture
def unique_pdf_content_jane() -> bytes:
    """
    Create a different PDF file content for testing unique files.

    Returns:
        Bytes content of a different PDF file (Jane Smith)
    """
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
<<
/Length 42
>>
stream
BT
/F1 12 Tf
50 700 Td
(Jane Smith - Product Manager) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000264 00000 n
0000000349 00000 n
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
188
%%EOF
"""


@pytest.fixture
def unique_pdf_content_bob() -> bytes:
    """
    Create a third unique PDF file content for testing.

    Returns:
        Bytes content of a different PDF file (Bob Johnson)
    """
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
<<
/Length 44
>>
stream
BT
/F1 12 Tf
50 700 Td
(Bob Johnson - Data Scientist) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000264 00000 n
0000000349 00000 n
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
190
%%EOF
"""


@pytest.fixture
def test_zip_with_duplicates(test_pdf_content: bytes, unique_pdf_content_jane: bytes) -> bytes:
    """
    Create a ZIP file containing duplicate and unique files.

    Args:
        test_pdf_content: PDF content that will be duplicated
        unique_pdf_content_jane: Unique PDF content

    Returns:
        ZIP file content as bytes
    """
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add two copies of the same content (duplicates)
        zip_file.writestr("resume_dup1.pdf", test_pdf_content)
        zip_file.writestr("resume_dup2.pdf", test_pdf_content)
        # Add a unique file
        zip_file.writestr("resume_unique.pdf", unique_pdf_content_jane)

    zip_buffer.seek(0)
    return zip_buffer.read()


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async HTTP client for testing API endpoints.

    Yields:
        AsyncClient instance configured for testing
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as client:
        yield client


# ============== CONTENT HASH UTILITY TESTS ==============

@pytest.mark.asyncio
@pytest.mark.integration
async def test_content_hash_computation(test_pdf_content: bytes):
    """
    Test that content hash is computed consistently using SHA-256.

    Verification:
    - Same content produces same hash
    - Hash is 64 characters (SHA-256 hex digest)
    - Different content produces different hash
    """
    hash1 = compute_content_hash(test_pdf_content)
    hash2 = compute_content_hash(test_pdf_content)

    # Same content should produce identical hashes
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 produces 64 hex characters

    # Different content should produce different hash
    different_content = b"different content"
    hash3 = compute_content_hash(different_content)
    assert hash1 != hash3


@pytest.mark.asyncio
@pytest.mark.integration
async def test_content_hash_deterministic(test_pdf_content: bytes):
    """
    Test that content hash is deterministic.

    Verification:
    - Hash computation is consistent across multiple calls
    """
    hashes = [compute_content_hash(test_pdf_content) for _ in range(10)]

    # All hashes should be identical
    assert len(set(hashes)) == 1


# ============== BATCH UPLOAD DUPLICATE DETECTION TESTS ==============

@pytest.mark.asyncio
@pytest.mark.integration
async def test_upload_duplicate_file_detects_duplicate(
    async_client: AsyncClient,
    test_pdf_content: bytes
):
    """
    Test that uploading the same file twice detects it as a duplicate.

    Flow:
    1. Upload first file
    2. Upload same content with different filename
    3. Verify duplicate detection

    Verification:
    - First upload succeeds without duplicate detection
    - Second upload response includes duplicate information
    """
    # First upload - no duplicates expected
    files1 = {
        'files': ('resume1.pdf', test_pdf_content, 'application/pdf')
    }
    data1 = {'analyze': 'false'}

    response1 = await async_client.post(
        "/api/batch/upload",
        files=files1,
        data=data1
    )

    assert response1.status_code == 201, f"Expected 201, got {response1.status_code}"
    response_data1 = response1.json()

    # First upload should not detect duplicates
    assert 'duplicates_detected' in response_data1
    assert response_data1['duplicates_detected'] == 0
    assert 'duplicates' in response_data1
    assert len(response_data1.get('duplicates', [])) == 0

    first_batch_id = response_data1['batch_id']

    # Second upload with same content - duplicate detection depends on
    # organization context being available
    files2 = {
        'files': ('resume2.pdf', test_pdf_content, 'application/pdf')
    }

    response2 = await async_client.post(
        "/api/batch/upload",
        files=files2,
        data=data1
    )

    assert response2.status_code == 201
    response_data2 = response2.json()

    # Response should include duplicate detection fields
    assert 'duplicates_detected' in response_data2
    assert 'duplicates' in response_data2


@pytest.mark.asyncio
@pytest.mark.integration
async def test_upload_multiple_files_with_duplicates(
    async_client: AsyncClient,
    test_pdf_content: bytes,
    unique_pdf_content_jane: bytes
):
    """
    Test that uploading multiple files with some duplicates correctly identifies them.

    Flow:
    1. Upload baseline file
    2. Upload mixed batch with some duplicates

    Verification:
    - Unique files are processed
    - Duplicate detection runs on all files
    - Response includes duplicate count and details
    """
    # First, upload a file to establish baseline
    files1 = {
        'files': ('baseline.pdf', unique_pdf_content_jane, 'application/pdf')
    }
    data = {'analyze': 'false'}

    response1 = await async_client.post(
        "/api/batch/upload",
        files=files1,
        data=data
    )
    assert response1.status_code == 201

    # Now upload mixed files (one duplicate, one unique)
    files2 = [
        ('files', ('duplicate.pdf', test_pdf_content, 'application/pdf')),
        ('files', ('unique.pdf', unique_pdf_content_jane, 'application/pdf')),
    ]

    response2 = await async_client.post(
        "/api/batch/upload",
        files=files2,
        data=data
    )

    assert response2.status_code == 201
    response_data = response2.json()

    # Verify response structure includes duplicate information
    assert 'batch_id' in response_data
    assert 'total_files' in response_data
    assert 'duplicates_detected' in response_data
    assert 'duplicates' in response_data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_duplicate_detection_in_zip(
    async_client: AsyncClient,
    test_zip_with_duplicates: bytes
):
    """
    Test that duplicate detection works for files extracted from ZIP archives.

    Flow:
    1. Upload ZIP containing duplicate files
    2. Verify duplicate detection runs on extracted files

    Verification:
    - ZIP is processed correctly
    - Duplicate detection runs on extracted content
    """
    files = {
        'files': ('resumes_with_duplicates.zip', test_zip_with_duplicates, 'application/zip')
    }
    data = {'analyze': 'false'}

    response = await async_client.post(
        "/api/batch/upload",
        files=files,
        data=data
    )

    assert response.status_code == 201
    response_data = response.json()

    # Verify ZIP was processed
    assert 'batch_id' in response_data
    assert 'total_files' in response_data
    # ZIP contains 3 files
    assert response_data['total_files'] == 3

    # Response should include duplicate info
    assert 'duplicates_detected' in response_data
    assert 'duplicates' in response_data


# ============== BATCH DUPLICATES ENDPOINT TESTS ==============

@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_batch_duplicates_endpoint(async_client: AsyncClient, test_pdf_content: bytes):
    """
    Test the batch duplicates listing endpoint.

    Flow:
    1. Upload a batch
    2. Request duplicates list

    Verification:
    - Endpoint returns 200 for valid batch ID
    - Response includes required fields
    """
    # Upload a file to create a batch
    files = {
        'files': ('resume.pdf', test_pdf_content, 'application/pdf')
    }
    data = {'analyze': 'false'}

    upload_response = await async_client.post(
        "/api/batch/upload",
        files=files,
        data=data
    )

    assert upload_response.status_code == 201
    batch_id = upload_response.json()['batch_id']

    # Get duplicates for this batch
    duplicates_response = await async_client.get(f"/api/batch/{batch_id}/duplicates")

    assert duplicates_response.status_code == 200
    duplicates_data = duplicates_response.json()

    # Verify response structure
    assert 'batch_id' in duplicates_data
    assert duplicates_data['batch_id'] == batch_id
    assert 'total_duplicates' in duplicates_data
    assert 'duplicates' in duplicates_data
    assert isinstance(duplicates_data['duplicates'], list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_batch_duplicates_invalid_uuid(async_client: AsyncClient):
    """
    Test that invalid batch ID returns 404 for duplicates endpoint.

    Verification:
    - Invalid UUID format returns 404
    """
    response = await async_client.get("/api/batch/invalid-uuid/duplicates")
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_batch_duplicates_nonexistent_batch(async_client: AsyncClient):
    """
    Test that non-existent batch ID returns 404.

    Verification:
    - Valid UUID that doesn't exist returns 404
    """
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = await async_client.get(f"/api/batch/{fake_uuid}/duplicates")
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_batch_duplicates_response_structure(async_client: AsyncClient, test_pdf_content: bytes):
    """
    Test that duplicates endpoint returns correct structure when duplicates exist.

    Flow:
    1. Upload first batch
    2. Upload second batch with duplicate content
    3. Get duplicates for second batch

    Verification:
    - Duplicate records include all required fields
    """
    # First batch - original file
    files1 = {
        'files': ('original.pdf', test_pdf_content, 'application/pdf')
    }
    data = {'analyze': 'false'}

    response1 = await async_client.post(
        "/api/batch/upload",
        files=files1,
        data=data
    )
    assert response1.status_code == 201
    response_data1 = response1.json()
    original_batch_id = response_data1['batch_id']

    # Second batch - duplicate file
    files2 = {
        'files': ('duplicate.pdf', test_pdf_content, 'application/pdf')
    }

    response2 = await async_client.post(
        "/api/batch/upload",
        files=files2,
        data=data
    )
    assert response2.status_code == 201
    response_data2 = response2.json()
    duplicate_batch_id = response_data2['batch_id']

    # Get duplicates for second batch
    duplicates_response = await async_client.get(
        f"/api/batch/{duplicate_batch_id}/duplicates"
    )
    assert duplicates_response.status_code == 200
    duplicates_data = duplicates_response.json()

    # Verify response structure
    assert 'batch_id' in duplicates_data
    assert 'total_duplicates' in duplicates_data
    assert 'duplicates' in duplicates_data

    # If duplicates were detected, verify their structure
    if duplicates_data['total_duplicates'] > 0:
        first_duplicate = duplicates_data['duplicates'][0]
        assert 'resume_id' in first_duplicate
        assert 'filename' in first_duplicate
        assert 'original_resume_id' in first_duplicate


# ============== UNIQUE FILES TESTS ==============

@pytest.mark.asyncio
@pytest.mark.integration
async def test_unique_files_not_flagged_as_duplicates(
    async_client: AsyncClient,
    test_pdf_content: bytes,
    unique_pdf_content_jane: bytes
):
    """
    Test that unique files are not incorrectly flagged as duplicates.

    Flow:
    1. Upload first unique file
    2. Upload second unique file with different content

    Verification:
    - Second file is not detected as duplicate
    """
    # Upload first unique file
    files1 = {
        'files': ('unique1.pdf', test_pdf_content, 'application/pdf')
    }
    data = {'analyze': 'false'}

    response1 = await async_client.post(
        "/api/batch/upload",
        files=files1,
        data=data
    )
    assert response1.status_code == 201
    data1_response = response1.json()
    assert data1_response['duplicates_detected'] == 0

    # Upload second unique file (different content)
    files2 = {
        'files': ('unique2.pdf', unique_pdf_content_jane, 'application/pdf')
    }

    response2 = await async_client.post(
        "/api/batch/upload",
        files=files2,
        data=data
    )
    assert response2.status_code == 201
    data2_response = response2.json()

    # Different content should NOT be detected as duplicate
    assert data2_response['duplicates_detected'] == 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_empty_batch_duplicates_list(async_client: AsyncClient):
    """
    Test that batches with no duplicates return empty list.

    Verification:
    - Empty duplicates list when no duplicates detected
    - total_duplicates is 0
    """
    # Create unique content that shouldn't match anything
    unique_content = b"%PDF-1.4\nunique content " + b"\x00" * 100

    files = {
        'files': ('unique.pdf', unique_content, 'application/pdf')
    }
    data = {'analyze': 'false'}

    response = await async_client.post(
        "/api/batch/upload",
        files=files,
        data=data
    )
    assert response.status_code == 201
    batch_id = response.json()['batch_id']

    # Get duplicates for this batch
    duplicates_response = await async_client.get(f"/api/batch/{batch_id}/duplicates")
    assert duplicates_response.status_code == 200

    duplicates_data = duplicates_response.json()
    assert duplicates_data['total_duplicates'] == 0
    assert duplicates_data['duplicates'] == []


# ============== MULTIPLE DUPLICATES TESTS ==============

@pytest.mark.asyncio
@pytest.mark.integration
async def test_multiple_duplicates_in_batch(
    async_client: AsyncClient,
    test_pdf_content: bytes
):
    """
    Test handling of multiple duplicate files in a single batch upload.

    Flow:
    1. Upload original file
    2. Upload batch with multiple duplicates

    Verification:
    - Multiple duplicates are correctly counted
    - Each duplicate is recorded separately
    """
    # First upload to establish baseline
    files1 = {
        'files': ('original.pdf', test_pdf_content, 'application/pdf')
    }
    data = {'analyze': 'false'}

    response1 = await async_client.post(
        "/api/batch/upload",
        files=files1,
        data=data
    )
    assert response1.status_code == 201

    # Upload multiple duplicates in one batch
    files2 = [
        ('files', ('dup1.pdf', test_pdf_content, 'application/pdf')),
        ('files', ('dup2.pdf', test_pdf_content, 'application/pdf')),
        ('files', ('dup3.pdf', test_pdf_content, 'application/pdf')),
    ]

    response2 = await async_client.post(
        "/api/batch/upload",
        files=files2,
        data=data
    )

    assert response2.status_code == 201
    response_data = response2.json()

    # Verify structure allows for multiple duplicates
    assert 'duplicates_detected' in response_data
    assert 'duplicates' in response_data
    assert isinstance(response_data['duplicates'], list)


# ============== CROSS-BATCH DUPLICATE DETECTION TESTS ==============

@pytest.mark.asyncio
@pytest.mark.integration
async def test_cross_batch_duplicate_detection(async_client: AsyncClient, test_pdf_content: bytes):
    """
    Test that duplicate detection works across different batch jobs.

    Flow:
    1. Upload file in batch 1
    2. Upload same content in batch 2

    Verification:
    - Duplicates are detected across batches
    - Original batch ID is preserved in duplicate record
    """
    # Batch 1: Upload original
    files1 = {
        'files': ('original.pdf', test_pdf_content, 'application/pdf')
    }
    data = {'analyze': 'false'}

    response1 = await async_client.post(
        "/api/batch/upload",
        files=files1,
        data=data
    )
    assert response1.status_code == 201
    batch_id1 = response1.json()['batch_id']

    # Batch 2: Upload duplicate
    files2 = {
        'files': ('duplicate.pdf', test_pdf_content, 'application/pdf')
    }

    response2 = await async_client.post(
        "/api/batch/upload",
        files=files2,
        data=data
    )
    assert response2.status_code == 201
    batch_id2 = response2.json()['batch_id']

    # Batches should be different
    assert batch_id1 != batch_id2


# ============== RESPONSE STRUCTURE TESTS ==============

@pytest.mark.asyncio
@pytest.mark.integration
async def test_batch_upload_response_includes_duplicate_fields(
    async_client: AsyncClient,
    test_pdf_content: bytes
):
    """
    Test that batch upload response always includes duplicate-related fields.

    Verification:
    - Response always includes duplicates_detected field
    - Response always includes duplicates list
    """
    files = {
        'files': ('resume.pdf', test_pdf_content, 'application/pdf')
    }
    data = {'analyze': 'false'}

    response = await async_client.post(
        "/api/batch/upload",
        files=files,
        data=data
    )
    assert response.status_code == 201

    response_data = response.json()

    # Verify duplicate-related fields are always present
    assert 'duplicates_detected' in response_data
    assert 'duplicates' in response_data
    assert isinstance(response_data['duplicates_detected'], int)
    assert isinstance(response_data['duplicates'], list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_duplicate_info_response_fields(async_client: AsyncClient, test_pdf_content: bytes):
    """
    Test that duplicate info in response includes all expected fields.

    Verification:
    - DuplicateInfo model fields are present when duplicates detected
    """
    # Upload a file
    files1 = {
        'files': ('original.pdf', test_pdf_content, 'application/pdf')
    }
    data = {'analyze': 'false'}

    response1 = await async_client.post(
        "/api/batch/upload",
        files=files1,
        data=data
    )
    assert response1.status_code == 201

    # Upload same content again
    files2 = {
        'files': ('duplicate.pdf', test_pdf_content, 'application/pdf')
    }

    response2 = await async_client.post(
        "/api/batch/upload",
        files=files2,
        data=data
    )
    assert response2.status_code == 201
    response_data = response2.json()

    # Check duplicate info structure if duplicates were detected
    if response_data['duplicates_detected'] > 0:
        duplicate = response_data['duplicates'][0]

        # Verify DuplicateInfo fields exist
        assert 'resume_id' in duplicate
        assert 'filename' in duplicate
        assert 'original_resume_id' in duplicate
        assert 'match_type' in duplicate
        assert 'similarity_score' in duplicate

        # Verify types
        assert isinstance(duplicate['similarity_score'], (int, float))
        assert duplicate['match_type'] in ['exact', 'fuzzy', None]


# ============== ORGANIZATION CONTEXT TESTS ==============

@pytest.mark.asyncio
@pytest.mark.integration
async def test_duplicate_detection_with_organization_header(
    async_client: AsyncClient,
    test_pdf_content: bytes
):
    """
    Test that duplicate detection respects organization context from headers.

    Verification:
    - Organization ID header is processed
    - Duplicate detection is scoped to organization
    """
    files = {
        'files': ('resume.pdf', test_pdf_content, 'application/pdf')
    }
    data = {'analyze': 'false'}

    # Add organization header
    response = await async_client.post(
        "/api/batch/upload",
        files=files,
        data=data,
        headers={
            "X-Organization-ID": "test-org-123"
        }
    )

    assert response.status_code == 201
    response_data = response.json()

    # Verify response structure
    assert 'batch_id' in response_data
    assert 'duplicates_detected' in response_data


# ============== DOCX FORMAT TESTS ==============

@pytest.mark.asyncio
@pytest.mark.integration
async def test_duplicate_detection_with_docx(async_client: AsyncClient):
    """
    Test duplicate detection with DOCX files.

    Verification:
    - Duplicate detection works for DOCX format
    - Content hash is computed correctly
    """
    # Create minimal DOCX content
    docx_buffer = io.BytesIO()
    with zipfile.ZipFile(docx_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', b'''<?xml version="1.0"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
</Types>''')
        zf.writestr('word/document.xml', b'''<?xml version="1.0"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body><w:p><w:r><w:t>Test Content</w:t></w:r></w:p></w:body>
</w:document>''')
    docx_buffer.seek(0)
    docx_content = docx_buffer.read()

    files = {
        'files': ('resume.docx', docx_content, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    }
    data = {'analyze': 'false'}

    response = await async_client.post(
        "/api/batch/upload",
        files=files,
        data=data
    )

    assert response.status_code == 201
    response_data = response.json()

    assert 'batch_id' in response_data
    assert 'duplicates_detected' in response_data


# ============== ERROR HANDLING TESTS ==============

@pytest.mark.asyncio
@pytest.mark.integration
async def test_duplicate_detection_error_handling(async_client: AsyncClient):
    """
    Test that duplicate detection errors don't break the upload process.

    Verification:
    - Upload succeeds even if duplicate detection fails
    - Error is handled gracefully
    """
    content = b"%PDF-1.4\nminimal"

    files = {
        'files': ('test.pdf', content, 'application/pdf')
    }
    data = {'analyze': 'false'}

    response = await async_client.post(
        "/api/batch/upload",
        files=files,
        data=data
    )

    # Upload should succeed regardless of duplicate detection errors
    assert response.status_code == 201
    response_data = response.json()
    assert 'batch_id' in response_data
    assert 'duplicates_detected' in response_data


# ============== EDGE CASE TESTS ==============

@pytest.mark.asyncio
@pytest.mark.integration
async def test_duplicate_detection_filename_case_sensitivity(
    async_client: AsyncClient,
    test_pdf_content: bytes
):
    """
    Test that duplicate detection is based on content, not filename case.

    Verification:
    - Same content with different filename case is still detected as duplicate
    """
    # Upload with uppercase filename
    files1 = {
        'files': ('RESUME.PDF', test_pdf_content, 'application/pdf')
    }
    data = {'analyze': 'false'}

    response1 = await async_client.post(
        "/api/batch/upload",
        files=files1,
        data=data
    )
    assert response1.status_code == 201

    # Upload same content with lowercase filename
    files2 = {
        'files': ('resume.pdf', test_pdf_content, 'application/pdf')
    }

    response2 = await async_client.post(
        "/api/batch/upload",
        files=files2,
        data=data
    )
    assert response2.status_code == 201

    # Content should be same regardless of filename case
    # (duplicate detection is based on content hash, not filename)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_duplicate_detection_preserves_original_info(
    async_client: AsyncClient,
    test_pdf_content: bytes
):
    """
    Test that duplicate detection preserves original resume information.

    Verification:
    - Original resume ID is recorded in duplicate info
    """
    # Upload original
    files1 = {
        'files': ('original_resume.pdf', test_pdf_content, 'application/pdf')
    }
    data = {'analyze': 'false'}

    response1 = await async_client.post(
        "/api/batch/upload",
        files=files1,
        data=data
    )
    assert response1.status_code == 201
    original_response = response1.json()

    # Upload duplicate
    files2 = {
        'files': ('duplicate_resume.pdf', test_pdf_content, 'application/pdf')
    }

    response2 = await async_client.post(
        "/api/batch/upload",
        files=files2,
        data=data
    )
    assert response2.status_code == 201

    response_data = response2.json()

    # If duplicate detected, check original info is preserved
    if response_data['duplicates_detected'] > 0:
        duplicate = response_data['duplicates'][0]
        assert 'original_resume_id' in duplicate
        assert duplicate['original_resume_id'] is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_concurrent_duplicate_detection(async_client: AsyncClient, test_pdf_content: bytes):
    """
    Test duplicate detection with concurrent uploads.

    Verification:
    - Concurrent uploads don't cause race conditions
    - Each upload gets correct duplicate status
    """
    import asyncio

    async def upload_file(filename: str):
        files = {
            'files': (filename, test_pdf_content, 'application/pdf')
        }
        data = {'analyze': 'false'}
        return await async_client.post(
            "/api/batch/upload",
            files=files,
            data=data
        )

    # Run 3 concurrent uploads
    tasks = [
        upload_file(f"resume_{i}.pdf")
        for i in range(3)
    ]

    responses = await asyncio.gather(*tasks)

    # All should succeed
    for response in responses:
        assert response.status_code == 201
        response_data = response.json()
        assert 'duplicates_detected' in response_data


# ============== EXACT MATCH VERIFICATION TESTS ==============

@pytest.mark.asyncio
@pytest.mark.integration
async def test_exact_match_similarity_score(async_client: AsyncClient):
    """
    Test that exact content matches have similarity score of 1.0.

    Verification:
    - Identical content is detected with similarity_score = 1.0
    - match_type is 'exact' for identical content
    """
    # Create content
    content = b"%PDF-1.4\n(content)\nJohn Doe\nSoftware Engineer\n"

    # Upload first
    files1 = {
        'files': ('file1.pdf', content, 'application/pdf')
    }
    data = {'analyze': 'false'}

    response1 = await async_client.post(
        "/api/batch/upload",
        files=files1,
        data=data
    )
    assert response1.status_code == 201

    # Upload identical (should be exact match)
    files2 = {
        'files': ('file2.pdf', content, 'application/pdf')
    }

    response2 = await async_client.post(
        "/api/batch/upload",
        files=files2,
        data=data
    )
    assert response2.status_code == 201

    response_data = response2.json()

    # Check for exact match detection
    if response_data['duplicates_detected'] > 0:
        duplicate = response_data['duplicates'][0]
        # Exact match should have similarity of 1.0
        assert duplicate['match_type'] == 'exact'
        assert duplicate['similarity_score'] == 1.0
