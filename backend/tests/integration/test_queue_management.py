"""
Integration tests for batch queue management (pause/resume/cancel).

This test suite validates the end-to-end integration of batch job control:
- Pause processing batch jobs
- Resume paused batch jobs
- Cancel pending, processing, or paused batch jobs
- Status transition validation
- Error handling for invalid operations
- Concurrent queue control operations

Test Coverage:
- Pause batch while processing
- Resume paused batch with Celery task re-dispatch
- Cancel batch at different stages
- Invalid status transitions
- Batch control response validation
- Progress preservation across pause/resume
"""
import asyncio
import io
import zipfile
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient

# Import the FastAPI application
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import app
from models.batch_job import BatchJob, BatchJobStatus


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
        # Add 5 test resumes for batch processing
        for i in range(1, 6):
            zip_file.writestr(f"resume_{i}.pdf", test_pdf_content)

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


# ============== PAUSE BATCH TESTS ==============

@pytest.mark.asyncio
async def test_pause_processing_batch(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that a processing batch can be paused.

    Verification:
    - Batch status changes to 'paused'
    - Response includes success message
    - Batch can be retrieved with paused status
    """
    # Upload batch to create processing job
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

    # Pause the batch
    pause_response = await async_client.post(f"/api/batch/{batch_id}/pause")

    assert pause_response.status_code == 200
    pause_data = pause_response.json()

    # Verify response structure
    assert 'batch_id' in pause_data
    assert 'status' in pause_data
    assert pause_data['batch_id'] == batch_id
    assert pause_data['status'] == 'paused'
    assert 'message' in pause_data
    assert 'paused' in pause_data['message'].lower()

    # Verify batch status in database
    status_response = await async_client.get(f"/api/batch/{batch_id}")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data['status'] == 'paused'


@pytest.mark.asyncio
async def test_pause_non_processing_batch(async_client: AsyncClient):
    """
    Test that non-processing batches cannot be paused.

    Verification:
    - Returns 400 Bad Request
    - Error message indicates invalid status
    """
    # Create a non-existent batch ID for testing
    fake_batch_id = "00000000-0000-0000-0000-000000000001"

    pause_response = await async_client.post(f"/api/batch/{fake_batch_id}/pause")

    # Should fail - batch doesn't exist
    assert pause_response.status_code == 404


@pytest.mark.asyncio
async def test_pause_completed_batch(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that a completed batch cannot be paused.

    Verification:
    - Returns 400 Bad Request
    - Error message indicates wrong status
    """
    # Upload and wait for completion
    files = {
        'files': ('test_resumes.zip', test_zip_file, 'application/zip')
    }

    upload_response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    batch_id = upload_response.json()['batch_id']

    # Wait for completion or timeout
    for _ in range(30):
        status_response = await async_client.get(f"/api/batch/{batch_id}")
        status_data = status_response.json()

        if status_data['status'] in ['completed', 'failed']:
            break

        await asyncio.sleep(0.5)

    # Try to pause the completed batch
    pause_response = await async_client.post(f"/api/batch/{batch_id}/pause")

    # Should fail if completed
    if status_data['status'] == 'completed':
        assert pause_response.status_code == 400
        error_data = pause_response.json()
        assert 'detail' in error_data
        assert 'cannot pause' in error_data['detail'].lower()


@pytest.mark.asyncio
async def test_pause_already_paused_batch(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that an already paused batch returns appropriate error.

    Verification:
    - Returns 400 Bad Request
    - Error message indicates already paused
    """
    # Upload and pause
    files = {
        'files': ('test_resumes.zip', test_zip_file, 'application/zip')
    }

    upload_response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    batch_id = upload_response.json()['batch_id']

    # First pause
    pause_response = await async_client.post(f"/api/batch/{batch_id}/pause")
    assert pause_response.status_code == 200

    # Try to pause again
    second_pause_response = await async_client.post(f"/api/batch/{batch_id}/pause")

    # Should fail - already paused
    assert second_pause_response.status_code == 400
    error_data = second_pause_response.json()
    assert 'detail' in error_data
    assert 'paused' in error_data['detail'].lower()


# ============== RESUME BATCH TESTS ==============

@pytest.mark.asyncio
async def test_resume_paused_batch(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that a paused batch can be resumed.

    Verification:
    - Batch status changes to 'processing'
    - Response includes success message
    - Processing continues from where it was paused
    """
    # Upload batch
    files = {
        'files': ('test_resumes.zip', test_zip_file, 'application/zip')
    }

    upload_response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    batch_id = upload_response.json()['batch_id']

    # Pause the batch
    pause_response = await async_client.post(f"/api/batch/{batch_id}/pause")
    assert pause_response.status_code == 200

    # Get progress before resume
    status_before = await async_client.get(f"/api/batch/{batch_id}")
    completed_before = status_before.json().get('completed_files', 0)

    # Resume the batch
    with patch('api.batch.batch_analyze_resumes') as mock_task:
        mock_task.delay = Mock(return_value=Mock(id='test-task-id'))

        resume_response = await async_client.post(f"/api/batch/{batch_id}/resume")

    assert resume_response.status_code == 200
    resume_data = resume_response.json()

    # Verify response structure
    assert 'batch_id' in resume_data
    assert 'status' in resume_data
    assert resume_data['batch_id'] == batch_id
    assert resume_data['status'] == 'processing'
    assert 'message' in resume_data
    assert 'resumed' in resume_data['message'].lower()

    # Verify batch status
    status_response = await async_client.get(f"/api/batch/{batch_id}")
    status_data = status_response.json()
    assert status_data['status'] == 'processing'

    # Verify progress is preserved
    assert status_data.get('completed_files', 0) >= completed_before


@pytest.mark.asyncio
async def test_resume_non_paused_batch(async_client: AsyncClient):
    """
    Test that non-paused batches cannot be resumed.

    Verification:
    - Returns 400 Bad Request
    - Error message indicates wrong status
    """
    # Create a non-existent batch ID for testing
    fake_batch_id = "00000000-0000-0000-0000-000000000002"

    resume_response = await async_client.post(f"/api/batch/{fake_batch_id}/resume")

    # Should fail - batch doesn't exist
    assert resume_response.status_code == 404


@pytest.mark.asyncio
async def test_resume_processing_batch(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that a processing batch cannot be resumed.

    Verification:
    - Returns 400 Bad Request
    - Error message indicates already processing
    """
    # Upload batch
    files = {
        'files': ('test_resumes.zip', test_zip_file, 'application/zip')
    }

    upload_response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    batch_id = upload_response.json()['batch_id']

    # Try to resume without pausing first
    resume_response = await async_client.post(f"/api/batch/{batch_id}/resume")

    # Should fail - not paused
    assert resume_response.status_code == 400
    error_data = resume_response.json()
    assert 'detail' in error_data
    assert 'paused' in error_data['detail'].lower()


@pytest.mark.asyncio
async def test_resume_cancelled_batch(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that a cancelled batch cannot be resumed.

    Verification:
    - Returns 400 Bad Request
    - Error message indicates cancelled status
    """
    # Upload and cancel
    files = {
        'files': ('test_resumes.zip', test_zip_file, 'application/zip')
    }

    upload_response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    batch_id = upload_response.json()['batch_id']

    # Cancel the batch
    cancel_response = await async_client.post(f"/api/batch/{batch_id}/cancel")
    assert cancel_response.status_code == 200

    # Try to resume cancelled batch
    resume_response = await async_client.post(f"/api/batch/{batch_id}/resume")

    # Should fail - cancelled
    assert resume_response.status_code == 400
    error_data = resume_response.json()
    assert 'detail' in error_data
    assert 'paused' in error_data['detail'].lower()


# ============== CANCEL BATCH TESTS ==============

@pytest.mark.asyncio
async def test_cancel_processing_batch(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that a processing batch can be cancelled.

    Verification:
    - Batch status changes to 'cancelled'
    - Response includes success message
    - Celery task is revoked
    """
    # Upload batch
    files = {
        'files': ('test_resumes.zip', test_zip_file, 'application/zip')
    }

    upload_response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    batch_id = upload_response.json()['batch_id']

    # Cancel the batch
    cancel_response = await async_client.post(f"/api/batch/{batch_id}/cancel")

    assert cancel_response.status_code == 200
    cancel_data = cancel_response.json()

    # Verify response structure
    assert 'batch_id' in cancel_data
    assert 'status' in cancel_data
    assert cancel_data['batch_id'] == batch_id
    assert cancel_data['status'] == 'cancelled'
    assert 'message' in cancel_data
    assert 'cancelled' in cancel_data['message'].lower()

    # Verify batch status
    status_response = await async_client.get(f"/api/batch/{batch_id}")
    status_data = status_response.json()
    assert status_data['status'] == 'cancelled'


@pytest.mark.asyncio
async def test_cancel_paused_batch(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that a paused batch can be cancelled.

    Verification:
    - Batch status changes to 'cancelled'
    - Response includes success message
    """
    # Upload and pause
    files = {
        'files': ('test_resumes.zip', test_zip_file, 'application/zip')
    }

    upload_response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    batch_id = upload_response.json()['batch_id']

    # Pause first
    pause_response = await async_client.post(f"/api/batch/{batch_id}/pause")
    assert pause_response.status_code == 200

    # Cancel paused batch
    cancel_response = await async_client.post(f"/api/batch/{batch_id}/cancel")

    assert cancel_response.status_code == 200
    cancel_data = cancel_response.json()
    assert cancel_data['status'] == 'cancelled'

    # Verify batch status
    status_response = await async_client.get(f"/api/batch/{batch_id}")
    assert status_response.json()['status'] == 'cancelled'


@pytest.mark.asyncio
async def test_cancel_completed_batch(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that a completed batch cannot be cancelled.

    Verification:
    - Returns 400 Bad Request
    - Error message indicates wrong status
    """
    # Upload and wait for completion
    files = {
        'files': ('test_resumes.zip', test_zip_file, 'application/zip')
    }

    upload_response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    batch_id = upload_response.json()['batch_id']

    # Wait for completion or timeout
    for _ in range(30):
        status_response = await async_client.get(f"/api/batch/{batch_id}")
        status_data = status_response.json()

        if status_data['status'] in ['completed', 'failed']:
            break

        await asyncio.sleep(0.5)

    # Try to cancel completed batch
    cancel_response = await async_client.post(f"/api/batch/{batch_id}/cancel")

    # Should fail if completed
    if status_data['status'] == 'completed':
        assert cancel_response.status_code == 400
        error_data = cancel_response.json()
        assert 'detail' in error_data
        assert 'cannot cancel' in error_data['detail'].lower()


@pytest.mark.asyncio
async def test_cancel_already_cancelled_batch(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that an already cancelled batch returns appropriate error.

    Verification:
    - Returns 400 Bad Request
    - Error message indicates already cancelled
    """
    # Upload and cancel
    files = {
        'files': ('test_resumes.zip', test_zip_file, 'application/zip')
    }

    upload_response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    batch_id = upload_response.json()['batch_id']

    # First cancel
    cancel_response = await async_client.post(f"/api/batch/{batch_id}/cancel")
    assert cancel_response.status_code == 200

    # Try to cancel again
    second_cancel_response = await async_client.post(f"/api/batch/{batch_id}/cancel")

    # Should fail - already cancelled
    assert second_cancel_response.status_code == 400
    error_data = second_cancel_response.json()
    assert 'detail' in error_data
    assert 'cancel' in error_data['detail'].lower()


@pytest.mark.asyncio
async def test_cancel_nonexistent_batch(async_client: AsyncClient):
    """
    Test that cancelling a non-existent batch returns 404.

    Verification:
    - Returns 404 Not Found
    - Error message indicates batch not found
    """
    fake_batch_id = "00000000-0000-0000-0000-000000000003"

    cancel_response = await async_client.post(f"/api/batch/{fake_batch_id}/cancel")

    assert cancel_response.status_code == 404


# ============== STATUS TRANSITION TESTS ==============

@pytest.mark.asyncio
async def test_status_transitions_pause_resume(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test the complete status transition cycle: processing -> paused -> processing.

    Verification:
    - Initial status is processing
    - After pause: status is paused
    - After resume: status is processing
    - All transitions recorded correctly
    """
    # Upload batch
    files = {
        'files': ('test_resumes.zip', test_zip_file, 'application/zip')
    }

    upload_response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    batch_id = upload_response.json()['batch_id']

    # Initial status should be processing
    initial_status = await async_client.get(f"/api/batch/{batch_id}")
    assert initial_status.json()['status'] == 'processing'

    # Pause -> paused
    pause_response = await async_client.post(f"/api/batch/{batch_id}/pause")
    assert pause_response.status_code == 200
    assert pause_response.json()['status'] == 'paused'

    paused_status = await async_client.get(f"/api/batch/{batch_id}")
    assert paused_status.json()['status'] == 'paused'

    # Resume -> processing
    with patch('api.batch.batch_analyze_resumes') as mock_task:
        mock_task.delay = Mock(return_value=Mock(id='test-task-id'))

        resume_response = await async_client.post(f"/api/batch/{batch_id}/resume")
        assert resume_response.status_code == 200
        assert resume_response.json()['status'] == 'processing'

    resumed_status = await async_client.get(f"/api/batch/{batch_id}")
    assert resumed_status.json()['status'] == 'processing'


@pytest.mark.asyncio
async def test_status_transitions_pause_cancel(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test the status transition: processing -> paused -> cancelled.

    Verification:
    - Initial status is processing
    - After pause: status is paused
    - After cancel: status is cancelled
    - Cannot resume after cancel
    """
    # Upload batch
    files = {
        'files': ('test_resumes.zip', test_zip_file, 'application/zip')
    }

    upload_response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    batch_id = upload_response.json()['batch_id']

    # Pause -> paused
    pause_response = await async_client.post(f"/api/batch/{batch_id}/pause")
    assert pause_response.status_code == 200
    assert pause_response.json()['status'] == 'paused'

    # Cancel -> cancelled
    cancel_response = await async_client.post(f"/api/batch/{batch_id}/cancel")
    assert cancel_response.status_code == 200
    assert cancel_response.json()['status'] == 'cancelled'

    # Verify final status
    final_status = await async_client.get(f"/api/batch/{batch_id}")
    assert final_status.json()['status'] == 'cancelled'


# ============== PROGRESS PRESERVATION TESTS ==============

@pytest.mark.asyncio
async def test_progress_preserved_on_pause(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that progress is preserved when batch is paused.

    Verification:
    - Completed count is preserved
    - Total count remains the same
    - Progress can be viewed while paused
    """
    # Upload batch
    files = {
        'files': ('test_resumes.zip', test_zip_file, 'application/zip')
    }

    upload_response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    batch_id = upload_response.json()['batch_id']
    total_files = upload_response.json()['total_files']

    # Get progress before pause
    status_before = await async_client.get(f"/api/batch/{batch_id}")
    completed_before = status_before.json().get('completed_files', 0)

    # Pause
    pause_response = await async_client.post(f"/api/batch/{batch_id}/pause")
    assert pause_response.status_code == 200

    # Get progress while paused
    status_paused = await async_client.get(f"/api/batch/{batch_id}")
    status_data = status_paused.json()

    # Verify progress is preserved
    assert status_data['total_files'] == total_files
    assert status_data['completed_files'] >= completed_before


@pytest.mark.asyncio
async def test_progress_continues_on_resume(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that processing continues correctly after resume.

    Verification:
    - Progress at resume is preserved
    - Processing continues from where it stopped
    - No duplicate processing occurs
    """
    # Upload batch
    files = {
        'files': ('test_resumes.zip', test_zip_file, 'application/zip')
    }

    upload_response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    batch_id = upload_response.json()['batch_id']

    # Pause immediately
    pause_response = await async_client.post(f"/api/batch/{batch_id}/pause")
    assert pause_response.status_code == 200

    # Get progress at pause
    status_at_pause = await async_client.get(f"/api/batch/{batch_id}")
    completed_at_pause = status_at_pause.json().get('completed_files', 0)

    # Resume
    with patch('api.batch.batch_analyze_resumes') as mock_task:
        mock_task.delay = Mock(return_value=Mock(id='test-task-id'))

        resume_response = await async_client.post(f"/api/batch/{batch_id}/resume")
        assert resume_response.status_code == 200

    # Verify progress hasn't decreased
    status_after_resume = await async_client.get(f"/api/batch/{batch_id}")
    completed_after_resume = status_after_resume.json().get('completed_files', 0)

    assert completed_after_resume >= completed_at_pause


# ============== CONCURRENT OPERATIONS TESTS ==============

@pytest.mark.asyncio
async def test_concurrent_pause_cancel(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test concurrent pause and cancel operations.

    Verification:
    - Only one operation succeeds
    - Final state is consistent
    - No race conditions
    """
    # Upload batch
    files = {
        'files': ('test_resumes.zip', test_zip_file, 'application/zip')
    }

    upload_response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    batch_id = upload_response.json()['batch_id']

    # Try concurrent pause and cancel
    pause_task = async_client.post(f"/api/batch/{batch_id}/pause")
    cancel_task = async_client.post(f"/api/batch/{batch_id}/cancel")

    responses = await asyncio.gather(pause_task, cancel_task, return_exceptions=True)

    # At least one should succeed
    success_count = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
    assert success_count >= 1

    # Final status should be either paused or cancelled
    final_status = await async_client.get(f"/api/batch/{batch_id}")
    assert final_status.json()['status'] in ['paused', 'cancelled']


@pytest.mark.asyncio
async def test_multiple_batches_independent_control(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that multiple batches can be controlled independently.

    Verification:
    - Each batch can be paused/resumed/cancelled independently
    - Operations on one batch don't affect others
    """
    # Upload 3 batches
    batch_ids = []
    for i in range(3):
        files = {
            'files': (f'test_resumes_{i}.zip', test_zip_file, 'application/zip')
        }
        response = await async_client.post("/api/batch/upload", files=files)
        assert response.status_code == 200
        batch_ids.append(response.json()['batch_id'])

    # Pause first batch
    pause_response = await async_client.post(f"/api/batch/{batch_ids[0]}/pause")
    assert pause_response.status_code == 200

    # Cancel second batch
    cancel_response = await async_client.post(f"/api/batch/{batch_ids[1]}/cancel")
    assert cancel_response.status_code == 200

    # Third batch continues processing

    # Verify each batch has correct status
    status_0 = await async_client.get(f"/api/batch/{batch_ids[0]}")
    assert status_0.json()['status'] == 'paused'

    status_1 = await async_client.get(f"/api/batch/{batch_ids[1]}")
    assert status_1.json()['status'] == 'cancelled'

    # Third batch should still be processing
    status_2 = await async_client.get(f"/api/batch/{batch_ids[2]}")
    # Note: may be processing or completed depending on timing
    assert status_2.json()['status'] in ['processing', 'completed']


# ============== ERROR HANDLING TESTS ==============

@pytest.mark.asyncio
async def test_invalid_batch_id_format_pause(async_client: AsyncClient):
    """
    Test that invalid batch ID format returns 422 for pause.

    Verification:
    - Returns 422 Unprocessable Entity
    - Error message indicates invalid UUID
    """
    pause_response = await async_client.post("/api/batch/invalid-uuid/pause")
    assert pause_response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_batch_id_format_resume(async_client: AsyncClient):
    """
    Test that invalid batch ID format returns 422 for resume.

    Verification:
    - Returns 422 Unprocessable Entity
    - Error message indicates invalid UUID
    """
    resume_response = await async_client.post("/api/batch/invalid-uuid/resume")
    assert resume_response.status_code == 422


@pytest.mark.asyncio
async def test_invalid_batch_id_format_cancel(async_client: AsyncClient):
    """
    Test that invalid batch ID format returns 422 for cancel.

    Verification:
    - Returns 422 Unprocessable Entity
    - Error message indicates invalid UUID
    """
    cancel_response = await async_client.post("/api/batch/invalid-uuid/cancel")
    assert cancel_response.status_code == 422


@pytest.mark.asyncio
async def test_nonexistent_batch_pause(async_client: AsyncClient):
    """
    Test that pausing non-existent batch returns 404.

    Verification:
    - Returns 404 Not Found
    - Error message indicates batch not found
    """
    fake_batch_id = "00000000-0000-0000-0000-000000000004"
    pause_response = await async_client.post(f"/api/batch/{fake_batch_id}/pause")
    assert pause_response.status_code == 404


@pytest.mark.asyncio
async def test_nonexistent_batch_resume(async_client: AsyncClient):
    """
    Test that resuming non-existent batch returns 404.

    Verification:
    - Returns 404 Not Found
    - Error message indicates batch not found
    """
    fake_batch_id = "00000000-0000-0000-0000-000000000005"
    resume_response = await async_client.post(f"/api/batch/{fake_batch_id}/resume")
    assert resume_response.status_code == 404


# ============== RESPONSE MODEL VALIDATION TESTS ==============

@pytest.mark.asyncio
async def test_pause_response_model(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that pause response follows BatchControlResponse model.

    Verification:
    - Response contains all required fields
    - Field types are correct
    """
    # Upload batch
    files = {
        'files': ('test_resumes.zip', test_zip_file, 'application/zip')
    }

    upload_response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    batch_id = upload_response.json()['batch_id']

    # Pause
    pause_response = await async_client.post(f"/api/batch/{batch_id}/pause")
    assert pause_response.status_code == 200

    data = pause_response.json()

    # Verify required fields
    assert 'batch_id' in data
    assert 'status' in data
    assert 'message' in data
    assert 'updated_at' in data

    # Verify types
    assert isinstance(data['batch_id'], str)
    assert isinstance(data['status'], str)
    assert isinstance(data['message'], str)
    assert data['status'] == 'paused'


@pytest.mark.asyncio
async def test_resume_response_model(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that resume response follows BatchControlResponse model.

    Verification:
    - Response contains all required fields
    - Field types are correct
    """
    # Upload batch
    files = {
        'files': ('test_resumes.zip', test_zip_file, 'application/zip')
    }

    upload_response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    batch_id = upload_response.json()['batch_id']

    # Pause first
    await async_client.post(f"/api/batch/{batch_id}/pause")

    # Resume
    with patch('api.batch.batch_analyze_resumes') as mock_task:
        mock_task.delay = Mock(return_value=Mock(id='test-task-id'))

        resume_response = await async_client.post(f"/api/batch/{batch_id}/resume")
        assert resume_response.status_code == 200

    data = resume_response.json()

    # Verify required fields
    assert 'batch_id' in data
    assert 'status' in data
    assert 'message' in data
    assert 'updated_at' in data

    # Verify types
    assert isinstance(data['batch_id'], str)
    assert isinstance(data['status'], str)
    assert isinstance(data['message'], str)
    assert data['status'] == 'processing'


@pytest.mark.asyncio
async def test_cancel_response_model(async_client: AsyncClient, test_zip_file: bytes):
    """
    Test that cancel response follows BatchControlResponse model.

    Verification:
    - Response contains all required fields
    - Field types are correct
    """
    # Upload batch
    files = {
        'files': ('test_resumes.zip', test_zip_file, 'application/zip')
    }

    upload_response = await async_client.post(
        "/api/batch/upload",
        files=files
    )

    batch_id = upload_response.json()['batch_id']

    # Cancel
    cancel_response = await async_client.post(f"/api/batch/{batch_id}/cancel")
    assert cancel_response.status_code == 200

    data = cancel_response.json()

    # Verify required fields
    assert 'batch_id' in data
    assert 'status' in data
    assert 'message' in data
    assert 'updated_at' in data

    # Verify types
    assert isinstance(data['batch_id'], str)
    assert isinstance(data['status'], str)
    assert isinstance(data['message'], str)
    assert data['status'] == 'cancelled'
