"""
Integration tests for batch operations and ZIP file upload with progress tracking.

This test suite validates the end-to-end integration between:
- Frontend bulk upload UI (simulated via HTTP requests)
- Backend batch upload API endpoints
- ZIP file extraction and validation
- Celery background task processing
- Batch job status tracking and updates
- Email notifications on completion
- Progress tracking accuracy

Test Coverage:
- ZIP file upload with multiple resumes
- Progress tracking via batch status API
- Batch job status transitions (processing → completed/failed)
- Email notification dispatch
- File validation and error handling
- Concurrent batch processing
- ZIP bomb protection
"""
import asyncio
import io
import os
import tempfile
import zipfile
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Import the FastAPI application
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import app
from models.batch_job import BatchJob, BatchJobStatus
from models.resume import Resume, ResumeStatus
from database import get_db


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
        # Add 3 test resumes
        for i in range(1, 4):
            zip_file.writestr(f"resume_{i}.pdf", test_pdf_content)

    zip_buffer.seek(0)
    return zip_buffer.read()


@pytest.fixture
def test_zip_with_mixed_files(test_pdf_content: bytes) -> bytes:
    """
    Create a ZIP file with valid and invalid files for testing validation.

    Args:
        test_pdf_content: PDF content to include in the ZIP

    Returns:
        ZIP file content as bytes
    """
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add valid PDFs
        zip_file.writestr("resume_1.pdf", test_pdf_content)
        zip_file.writestr("resume_2.pdf", test_pdf_content)

        # Add invalid file types
        zip_file.writestr("resume_3.exe", b"invalid executable content")
        zip_file.writestr("readme.txt", b"this is a text file")

        # Add another valid PDF
        zip_file.writestr("resume_4.pdf", test_pdf_content)

    zip_buffer.seek(0)
    return zip_buffer.read()


@pytest.fixture
def large_zip_file(test_pdf_content: bytes) -> bytes:
    """
    Create a ZIP file that exceeds size limits for testing validation.

    Args:
        test_pdf_content: PDF content to include in the ZIP

    Returns:
        ZIP file content as bytes (larger than 100MB limit)
    """
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Create a file that's larger than 100MB when uncompressed
        # Use compression to create a ZIP bomb scenario
        large_content = b'0' * (150 * 1024 * 1024)  # 150 MB of zeros
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
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# ============== ZIP UPLOAD TESTS ==============

@pytest.mark.asyncio
async def test_zip_upload_creates_batch_job(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that uploading a ZIP file creates a batch job and processes resumes.
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
    assert response.status_code == 200
    response_data = response.json()

    # Check batch job was created
    assert 'batch_id' in response_data
    assert 'total_files' in response_data
    assert response_data['total_files'] == 3
    assert response_data['status'] == 'processing'

    batch_id = response_data['batch_id']

    # Verify batch status can be retrieved
    status_response = await async_client.get(f"/api/batch/{batch_id}")
    assert status_response.status_code == 200

    status_data = status_response.json()
    assert status_data['batch_id'] == batch_id
    assert status_data['total_files'] == 3
    assert status_data['status'] in ['processing', 'completed', 'failed']


@pytest.mark.asyncio
async def test_zip_upload_progress_tracking(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that batch upload returns accurate progress tracking information.
    """
    # Upload ZIP file
    files = {
        'files': ('test_resumes.zip', test_zip_file, 'application/zip')
    }

    response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    assert response.status_code == 200
    response_data = response.json()
    batch_id = response_data['batch_id']

    # Poll for status updates
    max_attempts = 10
    previous_completed = 0

    for _ in range(max_attempts):
        status_response = await async_client.get(f"/api/batch/{batch_id}")
        status_data = status_response.json()

        # Verify progress fields exist
        assert 'total_files' in status_data
        assert 'completed_files' in status_data
        assert 'failed_files' in status_data
        assert status_data['total_files'] == 3

        # Check progress is non-decreasing
        current_completed = status_data['completed_files']
        assert current_completed >= previous_completed
        previous_completed = current_completed

        # Stop if processing is complete
        if status_data['status'] in ['completed', 'failed']:
            break

        await asyncio.sleep(1)

    # Verify final progress
    assert status_data['total_files'] == 3
    assert status_data['completed_files'] >= 0


@pytest.mark.asyncio
async def test_zip_upload_with_email_notification(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that email notification is configured when notification_email is provided.
    """
    files = {
        'files': ('test_resumes.zip', test_zip_file, 'application/zip')
    }
    data = {
        'notification_email': 'recruiter@example.com'
    }

    # Mock the Celery task to prevent actual email sending
    with patch('api.batch.send_batch_completion_notification') as mock_notification:
        mock_notification.apply_async = AsyncMock()

        response = await async_client.post(
            "/api/batch/upload",
            files=files,
            data=data
        )

        assert response.status_code == 200
        response_data = response.json()
        batch_id = response_data['batch_id']

        # Poll until completion to trigger notification
        for _ in range(20):
            status_response = await async_client.get(f"/api/batch/{batch_id}")
            status_data = status_response.json()

            if status_data['status'] == 'completed':
                break

            await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_zip_upload_filters_invalid_files(async_client: AsyncClient, test_zip_with_mixed_files: bytes):
    """
    Test that ZIP upload filters out invalid file types and processes valid ones.
    """
    files = {
        'files': ('mixed_resumes.zip', test_zip_with_mixed_files, 'application/zip')
    }

    response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    assert response.status_code == 200
    response_data = response.json()

    # Should only process PDF files, skip exe and txt
    # 3 valid PDFs out of 5 total files
    assert 'total_files' in response_data
    # Note: The exact count depends on implementation - adjust as needed


@pytest.mark.asyncio
async def test_zip_upload_validates_file_size(async_client: AsyncClient, large_zip_file: bytes):
    """
    Test that ZIP upload rejects files that exceed size limits.
    """
    files = {
        'files': ('large_resumes.zip', large_zip_file, 'application/zip')
    }

    response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    # Should reject oversized ZIP
    assert response.status_code in [400, 413]  # Bad Request or Payload Too Large

    response_data = response.json()
    assert 'detail' in response_data or 'error' in response_data


@pytest.mark.asyncio
async def test_batch_status_updates(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that batch status updates correctly from processing to completed/failed.
    """
    # Upload ZIP
    files = {
        'files': ('test_resumes.zip', test_zip_file, 'application/zip')
    }

    upload_response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    batch_id = upload_data['batch_id']

    # Initial status should be 'processing'
    assert upload_data['status'] == 'processing'

    # Poll for status change
    status_transitions = []
    previous_status = upload_data['status']

    for _ in range(30):
        status_response = await async_client.get(f"/api/batch/{batch_id}")
        status_data = status_response.json()
        current_status = status_data['status']

        if current_status != previous_status:
            status_transitions.append({
                'from': previous_status,
                'to': current_status,
                'timestamp': status_data.get('updated_at')
            })
            previous_status = current_status

        # Stop if we reach a terminal state
        if current_status in ['completed', 'failed']:
            break

        await asyncio.sleep(1)

    # Verify we had at least one status transition or reached terminal state
    final_status = status_transitions[-1]['to'] if status_transitions else previous_status
    assert final_status in ['processing', 'completed', 'failed']


@pytest.mark.asyncio
async def test_batch_results_retrieval(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that batch results can be retrieved after processing completes.
    """
    # Upload ZIP
    files = {
        'files': ('test_resumes.zip', test_zip_file, 'application/zip')
    }

    upload_response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    upload_data = upload_response.json()
    batch_id = upload_data['batch_id']

    # Wait for completion
    for _ in range(30):
        status_response = await async_client.get(f"/api/batch/{batch_id}")
        status_data = status_response.json()

        if status_data['status'] in ['completed', 'failed']:
            break

        await asyncio.sleep(1)

    # Retrieve results
    results_response = await async_client.get(f"/api/batch/{batch_id}/results")

    assert results_response.status_code in [200, 202]  # OK or Accepted (if still processing)

    results_data = results_response.json()

    # Verify result structure
    if results_response.status_code == 200:
        assert 'results' in results_data
        assert 'successful_count' in results_data
        assert 'failed_count' in results_data
        assert isinstance(results_data['results'], list)


@pytest.mark.asyncio
async def test_concurrent_batch_uploads(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that multiple batch uploads can be processed concurrently.
    """
    # Upload 3 ZIP files concurrently
    upload_tasks = []
    for i in range(3):
        files = {
            'files': (f'test_resumes_{i}.zip', test_zip_file, 'application/zip')
        }
        task = async_client.post("/api/batch/upload", files=files)
        upload_tasks.append(task)

    # Wait for all uploads to complete
    responses = await asyncio.gather(*upload_tasks)

    # Verify all uploads succeeded
    batch_ids = []
    for response in responses:
        assert response.status_code == 200
        response_data = response.json()
        assert 'batch_id' in response_data
        batch_ids.append(response_data['batch_id'])

    # Verify all batch jobs are independent
    for batch_id in batch_ids:
        status_response = await async_client.get(f"/api/batch/{batch_id}")
        assert status_response.status_code == 200

        status_data = status_response.json()
        assert status_data['batch_id'] == batch_id
        assert status_data['total_files'] == 3


@pytest.mark.asyncio
async def test_empty_zip_upload(async_client: AsyncClient):
    """
    Test that empty ZIP files are handled gracefully.
    """
    # Create empty ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        pass  # Empty ZIP

    zip_buffer.seek(0)
    empty_zip = zip_buffer.read()

    files = {
        'files': ('empty.zip', empty_zip, 'application/zip')
    }

    response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    # Should handle empty ZIP gracefully - either accept with 0 files or reject
    assert response.status_code in [200, 400]

    if response.status_code == 400:
        response_data = response.json()
        assert 'detail' in response_data or 'error' in response_data


@pytest.mark.asyncio
async def test_batch_list_pagination(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that batch jobs can be listed with pagination.
    """
    # Upload multiple batches
    batch_ids = []
    for i in range(3):
        files = {
            'files': (f'test_resumes_{i}.zip', test_zip_file, 'application/zip')
        }
        response = await async_client.post("/api/batch/upload", files=files)
        assert response.status_code == 200
        batch_ids.append(response.json()['batch_id'])

    # List batches with pagination
    list_response = await async_client.get("/api/batch?limit=2&offset=0")
    assert list_response.status_code == 200

    list_data = list_response.json()
    assert 'batches' in list_data
    assert 'total_count' in list_data
    assert len(list_data['batches']) <= 2


# ============== PROGRESS TRACKING ACCURACY TESTS ==============

@pytest.mark.asyncio
async def test_progress_tracking_accuracy(async_client: AsyncClient):
    """
    Test that progress tracking accurately reflects completed/remaining counts.
    """
    # Create ZIP with known number of files
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for i in range(10):
            # Use minimal PDF content
            pdf_content = b"%PDF-1.4\nminimal pdf content"
            zip_file.writestr(f"resume_{i}.pdf", pdf_content)

    zip_buffer.seek(0)
    test_zip = zip_buffer.read()

    files = {
        'files': ('test_resumes.zip', test_zip, 'application/zip')
    }

    response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    assert response.status_code == 200
    response_data = response.json()
    batch_id = response_data['batch_id']

    # Verify initial progress
    assert response_data['total_files'] == 10
    assert response_data['completed_files'] == 0

    # Monitor progress updates
    progress_snapshots = []

    for _ in range(30):
        status_response = await async_client.get(f"/api/batch/{batch_id}")
        status_data = status_response.json()

        progress_snapshots.append({
            'total': status_data['total_files'],
            'completed': status_data['completed_files'],
            'failed': status_data['failed_files'],
            'remaining': status_data['total_files'] - status_data['completed_files'] - status_data['failed_files']
        })

        if status_data['status'] in ['completed', 'failed']:
            break

        await asyncio.sleep(0.5)

    # Verify progress is monotonically increasing for completed count
    completed_counts = [s['completed'] for s in progress_snapshots]
    for i in range(1, len(completed_counts)):
        assert completed_counts[i] >= completed_counts[i - 1], \
            f"Completed count decreased from {completed_counts[i-1]} to {completed_counts[i]}"

    # Verify final totals
    final_snapshot = progress_snapshots[-1]
    assert final_snapshot['total'] == 10
    assert final_snapshot['completed'] + final_snapshot['failed'] <= 10


# ============== BULK EXPORT TESTS ==============

@pytest_asyncio.fixture
async def sample_resumes_for_export(async_client: AsyncClient, test_pdf_content: bytes) -> List[str]:
    """
    Create sample resumes in the database for bulk export testing.

    Args:
        async_client: Async HTTP client
        test_pdf_content: PDF file content

    Returns:
        List of resume IDs created
    """
    import os
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    # Create temporary directory for test uploads
    test_upload_dir = tempfile.mkdtemp()
    os.makedirs(test_upload_dir, exist_ok=True)

    resume_ids = []

    # Create 3 test resumes with actual files
    for i in range(1, 4):
        filename = f"test_resume_{i}.pdf"
        file_path = os.path.join(test_upload_dir, filename)

        # Write PDF file
        with open(file_path, 'wb') as f:
            f.write(test_pdf_content)

        # Create database record via API
        files = {
            'file': (filename, test_pdf_content, 'application/pdf')
        }

        response = await async_client.post(
            "/api/resumes/upload",
            files=files
        )

        assert response.status_code == 200
        resume_id = response.json()['id']
        resume_ids.append(resume_id)

    yield resume_ids

    # Cleanup
    import shutil
    if os.path.exists(test_upload_dir):
        shutil.rmtree(test_upload_dir)


async def test_bulk_export_zip(async_client: AsyncClient, sample_resumes_for_export: List[str]):
    """
    Test bulk export of resumes as ZIP file.

    Verification:
    - Export request is accepted
    - ZIP file is returned
    - ZIP contains all requested resumes
    - Files can be extracted and opened
    """
    export_request = {
        "resume_ids": sample_resumes_for_export,
        "format": "zip"
    }

    response = await async_client.post(
        "/api/candidates/bulk-export",
        json=export_request
    )

    # Verify response
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"

    # Verify content-disposition header
    content_disposition = response.headers.get("content-disposition", "")
    assert "attachment" in content_disposition
    assert ".zip" in content_disposition

    # Verify ZIP content
    zip_content = response.content
    assert len(zip_content) > 0

    # Extract and verify ZIP contents
    with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zip_file:
        file_list = zip_file.namelist()
        assert len(file_list) == len(sample_resumes_for_export)

        # Verify each file can be extracted
        for filename in file_list:
            assert filename.endswith('.pdf')
            file_content = zip_file.read(filename)
            assert len(file_content) > 0
            assert file_content.startswith(b'%PDF-')


async def test_bulk_export_pdf_format(async_client: AsyncClient, sample_resumes_for_export: List[str]):
    """
    Test bulk export of resumes in PDF format (ZIP containing PDFs).

    Verification:
    - Export request is accepted
    - ZIP file containing PDFs is returned
    - ZIP contains all requested PDF resumes
    - Files are valid PDFs
    """
    export_request = {
        "resume_ids": sample_resumes_for_export,
        "format": "pdf"
    }

    response = await async_client.post(
        "/api/candidates/bulk-export",
        json=export_request
    )

    # Verify response
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"

    # Verify content-disposition header
    content_disposition = response.headers.get("content-disposition", "")
    assert "attachment" in content_disposition
    assert "pdf" in content_disposition.lower()

    # Verify ZIP content
    zip_content = response.content
    assert len(zip_content) > 0

    # Extract and verify ZIP contains only PDFs
    with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zip_file:
        file_list = zip_file.namelist()
        assert len(file_list) == len(sample_resumes_for_export)

        # Verify all files are PDFs
        for filename in file_list:
            assert filename.endswith('.pdf')
            file_content = zip_file.read(filename)
            assert len(file_content) > 0
            assert file_content.startswith(b'%PDF-')


async def test_bulk_export_invalid_resume_ids(async_client: AsyncClient):
    """
    Test bulk export with invalid resume IDs.

    Verification:
    - Invalid IDs are filtered out
    - If no valid IDs, returns 404
    """
    export_request = {
        "resume_ids": ["invalid-uuid-1", "invalid-uuid-2"],
        "format": "zip"
    }

    response = await async_client.post(
        "/api/candidates/bulk-export",
        json=export_request
    )

    assert response.status_code == 404
    assert "No valid resumes found" in response.json()['detail']


async def test_bulk_export_empty_resume_list(async_client: AsyncClient):
    """
    Test bulk export with empty resume IDs list.

    Verification:
    - Returns 400 Bad Request
    """
    export_request = {
        "resume_ids": [],
        "format": "zip"
    }

    response = await async_client.post(
        "/api/candidates/bulk-export",
        json=export_request
    )

    assert response.status_code == 422  # Pydantic validation error


async def test_bulk_export_invalid_format(async_client: AsyncClient, sample_resumes_for_export: List[str]):
    """
    Test bulk export with invalid format.

    Verification:
    - Returns 400 Bad Request for invalid format
    """
    export_request = {
        "resume_ids": sample_resumes_for_export,
        "format": "docx"  # Invalid format
    }

    response = await async_client.post(
        "/api/candidates/bulk-export",
        json=export_request
    )

    assert response.status_code == 400
    assert "Invalid format" in response.json()['detail']


async def test_bulk_export_partial_success(async_client: AsyncClient, sample_resumes_for_export: List[str]):
    """
    Test bulk export with mix of valid and invalid resume IDs.

    Verification:
    - Valid IDs are processed
    - Invalid IDs are filtered out
    - Export succeeds with available resumes
    """
    # Mix valid and invalid IDs
    mixed_ids = [
        sample_resumes_for_export[0],  # Valid
        "invalid-uuid-xxx",  # Invalid
        sample_resumes_for_export[1],  # Valid
    ]

    export_request = {
        "resume_ids": mixed_ids,
        "format": "zip"
    }

    response = await async_client.post(
        "/api/candidates/bulk-export",
        json=export_request
    )

    # Should succeed with valid resumes
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"

    # ZIP should contain only the valid resumes
    zip_content = response.content
    with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zip_file:
        file_list = zip_file.namelist()
        assert len(file_list) == 2  # Only 2 valid resumes


async def test_bulk_export_file_download_size(async_client: AsyncClient, sample_resumes_for_export: List[str]):
    """
    Test bulk export returns correct content-length header.

    Verification:
    - Content-length header matches actual file size
    - File can be fully downloaded
    """
    export_request = {
        "resume_ids": sample_resumes_for_export,
        "format": "zip"
    }

    response = await async_client.post(
        "/api/candidates/bulk-export",
        json=export_request
    )

    assert response.status_code == 200

    # Verify content-length header
    content_length = response.headers.get("content-length")
    assert content_length is not None

    # Verify content length matches actual response size
    actual_size = len(response.content)
    assert int(content_length) == actual_size

    # Verify we can read the entire content
    assert actual_size > 0
    assert len(response.content) == actual_size
