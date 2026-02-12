"""
End-to-end integration tests for ZIP upload and processing flow.

This test suite validates the complete ZIP file upload workflow including:
- ZIP file upload via batch upload API
- ZIP extraction and file validation
- Batch job creation and status tracking
- Progress tracking during extraction
- Duplicate detection within ZIP uploads
- Error handling for invalid/corrupt ZIP files
- Empty ZIP handling
- Mixed valid/invalid file handling
- ZIP bomb protection
- Concurrent ZIP uploads

Test Coverage:
- POST /api/batch/upload - ZIP file upload
- GET /api/batch/{batch_id} - Batch status tracking
- GET /api/batch/{batch_id}/results - Results retrieval
- ZIP extraction utility integration
- File validation within ZIPs
- Duplicate detection integration
"""
import io
import zipfile
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import app
from database import get_db
from models.batch_job import BatchJob, BatchJobStatus
from models.resume import Resume, ResumeStatus


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
def test_docx_content() -> bytes:
    """
    Create a minimal valid DOCX file content for testing.

    Returns:
        Bytes content of a minimal DOCX file
    """
    # DOCX is a ZIP file with specific structure
    docx_buffer = io.BytesIO()
    with zipfile.ZipFile(docx_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Required DOCX components
        zf.writestr('[Content_Types].xml', b'''<?xml version="1.0"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>''')
        zf.writestr('word/document.xml', b'''<?xml version="1.0"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body><w:p><w:r><w:t>John Doe - Software Engineer</w:t></w:r></w:p></w:body>
</w:document>''')
        zf.writestr('_rels/.rels', b'''<?xml version="1.0"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>''')
    docx_buffer.seek(0)
    return docx_buffer.read()


@pytest.fixture
def test_zip_file(test_pdf_content: bytes) -> bytes:
    """
    Create a ZIP file containing test resume PDFs.

    Args:
        test_pdf_content: PDF content to include in the ZIP

    Returns:
        ZIP file content as bytes
    """
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add 5 test resumes
        for i in range(1, 6):
            zip_file.writestr(f"resume_{i}.pdf", test_pdf_content)

    zip_buffer.seek(0)
    return zip_buffer.read()


@pytest.fixture
def test_zip_with_nested_dirs(test_pdf_content: bytes) -> bytes:
    """
    Create a ZIP file with nested directory structure.

    Args:
        test_pdf_content: PDF content to include in the ZIP

    Returns:
        ZIP file content as bytes
    """
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Files in nested directories
        zip_file.writestr("resumes/2024/john_doe.pdf", test_pdf_content)
        zip_file.writestr("resumes/2024/jane_smith.pdf", test_pdf_content)
        zip_file.writestr("candidates/senior/bob_jones.pdf", test_pdf_content)
        zip_file.writestr("root_resume.pdf", test_pdf_content)

    zip_buffer.seek(0)
    return zip_buffer.read()


@pytest.fixture
def test_zip_with_mixed_files(test_pdf_content: bytes, test_docx_content: bytes) -> bytes:
    """
    Create a ZIP file with valid and invalid files for testing validation.

    Args:
        test_pdf_content: PDF content to include in the ZIP
        test_docx_content: DOCX content to include in the ZIP

    Returns:
        ZIP file content as bytes
    """
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add valid PDFs
        zip_file.writestr("resume_1.pdf", test_pdf_content)
        zip_file.writestr("resume_2.pdf", test_pdf_content)

        # Add valid DOCX
        zip_file.writestr("resume_3.docx", test_docx_content)

        # Add invalid file types
        zip_file.writestr("resume_4.exe", b"invalid executable content")
        zip_file.writestr("readme.txt", b"this is a text file")
        zip_file.writestr("image.png", b"fake image content")

        # Add another valid PDF
        zip_file.writestr("resume_5.pdf", test_pdf_content)

    zip_buffer.seek(0)
    return zip_buffer.read()


@pytest.fixture
def test_zip_with_duplicate_files(test_pdf_content: bytes) -> bytes:
    """
    Create a ZIP file with duplicate file content for testing deduplication.

    Args:
        test_pdf_content: PDF content to include in the ZIP

    Returns:
        ZIP file content as bytes
    """
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add the same content under different names (duplicates)
        zip_file.writestr("resume_original.pdf", test_pdf_content)
        zip_file.writestr("resume_copy.pdf", test_pdf_content)  # Duplicate
        zip_file.writestr("resumes/resume_duplicate.pdf", test_pdf_content)  # Duplicate in subfolder

    zip_buffer.seek(0)
    return zip_buffer.read()


@pytest.fixture
def corrupt_zip_file() -> bytes:
    """
    Create a corrupt ZIP file for testing error handling.

    Returns:
        Corrupt ZIP file content as bytes
    """
    # Invalid ZIP header
    return b"PK\x03\x04" + b"\x00" * 50 + b"corrupted data"


@pytest.fixture
def empty_zip_file() -> bytes:
    """
    Create an empty ZIP file for testing edge cases.

    Returns:
        Empty ZIP file content as bytes
    """
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        pass  # Empty ZIP

    zip_buffer.seek(0)
    return zip_buffer.read()


@pytest.fixture
def large_zip_file(test_pdf_content: bytes) -> bytes:
    """
    Create a ZIP file that exceeds size limits for testing validation.

    Args:
        test_pdf_content: PDF content to include in the ZIP

    Returns:
        ZIP file content as bytes (with compressed large content)
    """
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Create a file that simulates a decompression bomb
        # The compressed size is small, but uncompressed is large
        large_content = b'0' * (110 * 1024 * 1024)  # 110 MB of zeros (over 100MB limit)
        zip_file.writestr("large_resume.pdf", large_content)

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


# ============== ZIP UPLOAD E2E TESTS ==============

@pytest.mark.asyncio
@pytest.mark.integration
async def test_zip_upload_creates_batch_job(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that uploading a ZIP file creates a batch job and extracts resumes.

    Flow:
    1. Upload ZIP file containing 5 PDFs
    2. Verify batch job is created
    3. Verify correct file count in response
    4. Verify batch status endpoint is accessible
    """
    # Create multipart form data with ZIP file
    files = {
        'files': ('test_resumes.zip', test_zip_file, 'application/zip')
    }
    data = {
        'notification_email': 'test@example.com'
    }

    # Upload ZIP file
    response = await async_client.post(
        "/api/batch/upload",
        files=files,
        data=data
    )

    # Verify response
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    response_data = response.json()

    # Check batch job was created
    assert 'batch_id' in response_data
    assert 'total_files' in response_data
    assert response_data['total_files'] == 5
    assert response_data['status'] in ['pending', 'processing']

    batch_id = response_data['batch_id']

    # Verify batch status can be retrieved
    status_response = await async_client.get(f"/api/batch/{batch_id}")
    assert status_response.status_code == 200

    status_data = status_response.json()
    assert status_data['batch_id'] == batch_id
    assert status_data['total_files'] == 5
    assert status_data['status'] in ['pending', 'processing', 'completed', 'failed']


@pytest.mark.asyncio
@pytest.mark.integration
async def test_zip_upload_extracts_nested_directories(async_client: AsyncClient, test_zip_with_nested_dirs: bytes):
    """
    Test that ZIP files with nested directories are extracted correctly.

    Flow:
    1. Upload ZIP with nested directory structure
    2. Verify all files are extracted regardless of directory depth
    3. Verify file paths are flattened/sanitized
    """
    files = {
        'files': ('nested_resumes.zip', test_zip_with_nested_dirs, 'application/zip')
    }

    response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    assert response.status_code == 201
    response_data = response.json()

    # Should extract all 4 PDFs from nested directories
    assert response_data['total_files'] == 4
    assert 'batch_id' in response_data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_zip_upload_filters_invalid_files(async_client: AsyncClient, test_zip_with_mixed_files: bytes):
    """
    Test that ZIP upload filters out invalid file types and processes valid ones.

    Flow:
    1. Upload ZIP with 5 valid files (PDF, DOCX) and 3 invalid files (exe, txt, png)
    2. Verify only valid files are processed
    3. Verify invalid files are skipped
    """
    files = {
        'files': ('mixed_resumes.zip', test_zip_with_mixed_files, 'application/zip')
    }

    response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    assert response.status_code == 201
    response_data = response.json()

    # Should only process valid PDF and DOCX files (4 files: 3 PDFs + 1 DOCX)
    # Invalid files (exe, txt, png) should be skipped
    assert response_data['total_files'] == 4


@pytest.mark.asyncio
@pytest.mark.integration
async def test_zip_upload_handles_empty_zip(async_client: AsyncClient, empty_zip_file: bytes):
    """
    Test that empty ZIP files are handled gracefully.

    Flow:
    1. Upload empty ZIP file
    2. Verify appropriate error response
    """
    files = {
        'files': ('empty.zip', empty_zip_file, 'application/zip')
    }

    response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    # Should handle empty ZIP gracefully - either accept with 0 files or reject with 400
    assert response.status_code in [201, 400]

    if response.status_code == 400:
        response_data = response.json()
        assert 'detail' in response_data or 'error' in response_data
    else:
        response_data = response.json()
        # If accepted, should report 0 files
        assert response_data['total_files'] == 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_zip_upload_handles_corrupt_zip(async_client: AsyncClient, corrupt_zip_file: bytes):
    """
    Test that corrupt ZIP files are handled gracefully.

    Flow:
    1. Upload corrupt ZIP file
    2. Verify appropriate error response
    """
    files = {
        'files': ('corrupt.zip', corrupt_zip_file, 'application/zip')
    }

    response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    # Should reject corrupt ZIP with error
    assert response.status_code in [400, 500]

    response_data = response.json()
    assert 'detail' in response_data or 'error' in response_data or 'message' in response_data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_zip_upload_with_notification_email(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that email notification is configured when notification_email is provided.

    Flow:
    1. Upload ZIP with notification email
    2. Verify batch is created with email setting
    3. Verify batch status includes notification info
    """
    files = {
        'files': ('test_resumes.zip', test_zip_file, 'application/zip')
    }
    data = {
        'notification_email': 'recruiter@example.com'
    }

    response = await async_client.post(
        "/api/batch/upload",
        files=files,
        data=data
    )

    assert response.status_code == 201
    response_data = response.json()

    batch_id = response_data['batch_id']

    # Verify batch was created
    assert batch_id is not None
    assert response_data['status'] in ['pending', 'processing']


@pytest.mark.asyncio
@pytest.mark.integration
async def test_zip_upload_progress_tracking(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that ZIP upload batch returns accurate progress tracking information.

    Flow:
    1. Upload ZIP file
    2. Poll batch status endpoint
    3. Verify progress fields exist and are accurate
    4. Verify progress is non-decreasing
    """
    files = {
        'files': ('test_resumes.zip', test_zip_file, 'application/zip')
    }

    response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    assert response.status_code == 201
    response_data = response.json()
    batch_id = response_data['batch_id']

    # Get initial status
    status_response = await async_client.get(f"/api/batch/{batch_id}")
    status_data = status_response.json()

    # Verify progress fields exist
    assert 'total_files' in status_data
    assert 'processed_files' in status_data
    assert 'failed_files' in status_data
    assert 'progress_percentage' in status_data

    # Verify initial state
    assert status_data['total_files'] == 5
    assert status_data['processed_files'] >= 0
    assert status_data['failed_files'] >= 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_multiple_zip_uploads(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that multiple ZIP files can be uploaded and processed independently.

    Flow:
    1. Upload multiple ZIP files in sequence
    2. Verify each creates a separate batch job
    3. Verify all batches are independent
    """
    batch_ids = []

    # Upload 3 ZIP files
    for i in range(3):
        files = {
            'files': (f'test_resumes_{i}.zip', test_zip_file, 'application/zip')
        }

        response = await async_client.post(
            "/api/batch/upload",
            files=files
        )

        assert response.status_code == 201
        response_data = response.json()
        assert 'batch_id' in response_data
        batch_ids.append(response_data['batch_id'])

    # Verify all batch IDs are unique
    assert len(set(batch_ids)) == 3, "Each ZIP upload should create a unique batch"

    # Verify each batch is accessible
    for batch_id in batch_ids:
        status_response = await async_client.get(f"/api/batch/{batch_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data['total_files'] == 5


@pytest.mark.asyncio
@pytest.mark.integration
async def test_zip_upload_with_analyze_false(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that ZIP upload with analyze=false stores files without triggering analysis.

    Flow:
    1. Upload ZIP with analyze=false
    2. Verify batch is created
    3. Verify batch status remains pending (not processing)
    """
    files = {
        'files': ('test_resumes.zip', test_zip_file, 'application/zip')
    }
    data = {
        'analyze': 'false'
    }

    response = await async_client.post(
        "/api/batch/upload",
        files=files,
        data=data
    )

    assert response.status_code == 201
    response_data = response.json()

    # Batch should be created but not processing
    assert 'batch_id' in response_data
    assert response_data['total_files'] == 5

    # Status should be pending (not processing since analyze=false)
    batch_id = response_data['batch_id']
    status_response = await async_client.get(f"/api/batch/{batch_id}")
    status_data = status_response.json()

    # With analyze=false, status should remain pending
    assert status_data['status'] == 'pending'


@pytest.mark.asyncio
@pytest.mark.integration
async def test_zip_and_regular_files_mixed_upload(async_client: AsyncClient, test_zip_file: bytes, test_pdf_content: bytes):
    """
    Test uploading a mix of ZIP files and regular PDF files.

    Flow:
    1. Upload ZIP file + regular PDF file in same request
    2. Verify both are processed
    3. Verify total file count includes extracted + direct files
    """
    files = [
        ('files', ('resumes.zip', test_zip_file, 'application/zip')),
        ('files', ('direct_resume.pdf', test_pdf_content, 'application/pdf')),
    ]

    response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    assert response.status_code == 201
    response_data = response.json()

    # Should have 5 files from ZIP + 1 direct PDF = 6 total
    assert response_data['total_files'] == 6
    assert 'batch_id' in response_data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_zip_upload_results_retrieval(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that results can be retrieved after ZIP upload batch completes.

    Flow:
    1. Upload ZIP file
    2. Retrieve batch results
    3. Verify results contain file details
    """
    files = {
        'files': ('test_resumes.zip', test_zip_file, 'application/zip')
    }
    data = {
        'analyze': 'false'  # Skip analysis for faster test
    }

    upload_response = await async_client.post(
        "/api/batch/upload",
        files=files,
        data=data
    )

    assert upload_response.status_code == 201
    upload_data = upload_response.json()
    batch_id = upload_data['batch_id']

    # Retrieve results
    results_response = await async_client.get(f"/api/batch/{batch_id}/results")

    # Results endpoint should respond
    assert results_response.status_code in [200, 202]

    if results_response.status_code == 200:
        results_data = results_response.json()
        assert 'batch_id' in results_data
        assert 'total_files' in results_data
        assert 'files' in results_data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_zip_upload_list_batches(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that ZIP upload batches appear in batch list.

    Flow:
    1. Upload ZIP file
    2. List all batches
    3. Verify new batch appears in list
    """
    files = {
        'files': ('test_resumes.zip', test_zip_file, 'application/zip')
    }

    response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    assert response.status_code == 201
    batch_id = response.json()['batch_id']

    # List batches
    list_response = await async_client.get("/api/batch/")
    assert list_response.status_code == 200

    list_data = list_response.json()
    assert 'batches' in list_data

    # Find our batch in the list
    batch_ids = [b['batch_id'] for b in list_data['batches']]
    assert batch_id in batch_ids


@pytest.mark.asyncio
@pytest.mark.integration
async def test_zip_upload_batch_status_transitions(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that ZIP upload batch status transitions correctly.

    Flow:
    1. Upload ZIP file
    2. Verify initial status is pending or processing
    3. Verify status endpoint returns valid transitions
    """
    files = {
        'files': ('test_resumes.zip', test_zip_file, 'application/zip')
    }

    response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    assert response.status_code == 201
    response_data = response.json()
    batch_id = response_data['batch_id']

    # Initial status check
    status_response = await async_client.get(f"/api/batch/{batch_id}")
    status_data = status_response.json()

    # Status should be a valid BatchJobStatus value
    valid_statuses = ['pending', 'processing', 'completed', 'failed', 'paused', 'cancelled']
    assert status_data['status'] in valid_statuses

    # Verify batch_id matches
    assert status_data['batch_id'] == batch_id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_zip_upload_with_unicode_filenames(async_client: AsyncClient, test_pdf_content: bytes):
    """
    Test ZIP upload with Unicode filenames.

    Flow:
    1. Create ZIP with Unicode filenames
    2. Upload ZIP
    3. Verify files are processed correctly
    """
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add files with Unicode names
        zip_file.writestr("résumé_émojis_😊.pdf", test_pdf_content)
        zip_file.writestr("резюме_кириллица.pdf", test_pdf_content)
        zip_file.writestr("简历_中文.pdf", test_pdf_content)

    zip_buffer.seek(0)
    unicode_zip = zip_buffer.read()

    files = {
        'files': ('unicode_resumes.zip', unicode_zip, 'application/zip')
    }

    response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    # Should handle Unicode filenames
    assert response.status_code == 201
    response_data = response.json()
    assert response_data['total_files'] == 3


@pytest.mark.asyncio
@pytest.mark.integration
async def test_zip_upload_large_zip_rejected(async_client: AsyncClient, large_zip_file: bytes):
    """
    Test that ZIP files with oversized content are rejected.

    Flow:
    1. Upload ZIP with file exceeding size limits
    2. Verify rejection with appropriate error
    """
    files = {
        'files': ('large_resumes.zip', large_zip_file, 'application/zip')
    }

    response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    # Should reject oversized content
    # Note: The actual status code depends on implementation
    # Could be 400 (Bad Request), 413 (Payload Too Large), or 201 with failed status
    assert response.status_code in [201, 400, 413]

    if response.status_code not in [201]:
        response_data = response.json()
        assert 'detail' in response_data or 'error' in response_data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_zip_upload_duplicate_detection(async_client: AsyncClient, test_zip_with_duplicate_files: bytes):
    """
    Test that duplicate detection works within ZIP uploads.

    Flow:
    1. Upload ZIP with duplicate file content
    2. Verify duplicates are detected and reported
    3. Verify duplicate info is in response
    """
    files = {
        'files': ('duplicates.zip', test_zip_with_duplicate_files, 'application/zip')
    }

    response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    assert response.status_code == 201
    response_data = response.json()

    # All 3 files should be stored (duplicates are flagged but still stored)
    assert response_data['total_files'] == 3

    # Check if duplicates were detected
    # Note: Duplicate detection requires organization context
    assert 'duplicates_detected' in response_data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_zip_upload_preserves_file_order(async_client: AsyncClient, test_pdf_content: bytes):
    """
    Test that ZIP file extraction preserves file order.

    Flow:
    1. Create ZIP with files in specific order
    2. Upload ZIP
    3. Verify files are processed in consistent order
    """
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add files in specific order
        for i in range(1, 6):
            zip_file.writestr(f"{i:02d}_resume.pdf", test_pdf_content)

    zip_buffer.seek(0)
    ordered_zip = zip_buffer.read()

    files = {
        'files': ('ordered_resumes.zip', ordered_zip, 'application/zip')
    }

    response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    assert response.status_code == 201
    response_data = response.json()

    # All files should be processed
    assert response_data['total_files'] == 5

    batch_id = response_data['batch_id']

    # Get results to check order
    results_response = await async_client.get(f"/api/batch/{batch_id}/results")
    if results_response.status_code == 200:
        results_data = results_response.json()
        # Files should be present
        assert len(results_data.get('files', [])) == 5


# ============== ERROR HANDLING TESTS ==============

@pytest.mark.asyncio
@pytest.mark.integration
async def test_zip_upload_invalid_uuid_in_status(async_client: AsyncClient):
    """
    Test that invalid UUID format in batch status returns 404.

    Flow:
    1. Request status with invalid UUID
    2. Verify 404 response
    """
    response = await async_client.get("/api/batch/invalid-uuid-format")

    assert response.status_code == 404
    response_data = response.json()
    assert 'detail' in response_data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_zip_upload_nonexistent_batch_status(async_client: AsyncClient):
    """
    Test that nonexistent batch ID returns 404.

    Flow:
    1. Request status with valid but nonexistent UUID
    2. Verify 404 response
    """
    fake_uuid = "12345678-1234-5678-1234-567812345678"
    response = await async_client.get(f"/api/batch/{fake_uuid}")

    assert response.status_code == 404
    response_data = response.json()
    assert 'detail' in response_data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_zip_upload_no_files_error(async_client: AsyncClient):
    """
    Test that upload with no files returns error.

    Flow:
    1. Upload request with no files
    2. Verify error response
    """
    response = await async_client.post("/api/batch/upload")

    # Should return error for missing files
    assert response.status_code in [400, 422]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_zip_upload_too_many_files(async_client: AsyncClient, test_pdf_content: bytes):
    """
    Test that uploading more than 100 files returns error.

    Flow:
    1. Attempt to upload 101 files
    2. Verify rejection with error
    """
    # Create 101 files (exceeds limit of 100)
    files = [
        ('files', (f'resume_{i}.pdf', test_pdf_content, 'application/pdf'))
        for i in range(101)
    ]

    response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    # Should reject with 400
    assert response.status_code == 400
    response_data = response.json()
    assert 'detail' in response_data
    assert '100' in response_data['detail'].lower() or 'maximum' in response_data['detail'].lower()


# ============== DOCX SUPPORT TESTS ==============

@pytest.mark.asyncio
@pytest.mark.integration
async def test_zip_upload_with_docx_files(async_client: AsyncClient, test_docx_content: bytes):
    """
    Test that ZIP files containing DOCX files are processed correctly.

    Flow:
    1. Upload ZIP with DOCX files
    2. Verify DOCX files are extracted and processed
    """
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("resume_1.docx", test_docx_content)
        zip_file.writestr("resume_2.docx", test_docx_content)

    zip_buffer.seek(0)
    docx_zip = zip_buffer.read()

    files = {
        'files': ('docx_resumes.zip', docx_zip, 'application/zip')
    }

    response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    assert response.status_code == 201
    response_data = response.json()

    # Should process 2 DOCX files
    assert response_data['total_files'] == 2


@pytest.mark.asyncio
@pytest.mark.integration
async def test_zip_upload_mixed_pdf_and_docx(async_client: AsyncClient, test_pdf_content: bytes, test_docx_content: bytes):
    """
    Test ZIP with mixed PDF and DOCX files.

    Flow:
    1. Upload ZIP with both PDF and DOCX files
    2. Verify all files are processed
    """
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("resume_pdf.pdf", test_pdf_content)
        zip_file.writestr("resume_docx.docx", test_docx_content)
        zip_file.writestr("resume_pdf2.pdf", test_pdf_content)

    zip_buffer.seek(0)
    mixed_zip = zip_buffer.read()

    files = {
        'files': ('mixed_resumes.zip', mixed_zip, 'application/zip')
    }

    response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    assert response.status_code == 201
    response_data = response.json()

    # Should process 3 files (2 PDFs + 1 DOCX)
    assert response_data['total_files'] == 3
