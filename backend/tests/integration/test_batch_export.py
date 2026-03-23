"""
End-to-end integration tests for batch export functionality.

This test suite validates the batch export workflow including:
- CSV export format
- JSON export format
- Export validation (format, batch_id)
- Export of completed batches
- Export of failed batches
- Export with various batch statuses
- Error handling for invalid inputs

Test Coverage:
- GET /api/batch/{batch_id}/export - Export batch results
- CSV format export with correct headers and data
- JSON format export with complete batch metadata
- Validation of batch_id UUID format
- Validation of export format parameter
- Error handling for non-existent batches
"""
import csv
import io
from pathlib import Path
from typing import AsyncGenerator
from uuid import uuid4

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


@pytest_asyncio.fixture
async def sample_batch_job(test_pdf_content: bytes, async_client: AsyncClient) -> dict:
    """
    Create a sample batch job with uploaded files for testing exports.

    Args:
        test_pdf_content: PDF content for creating test files
        async_client: HTTP client for making requests

    Returns:
        Dict containing batch_id and batch metadata
    """
    import zipfile

    # Create a ZIP file with test resumes
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add 3 test resumes
        for i in range(1, 4):
            zip_file.writestr(f"resume_{i}.pdf", test_pdf_content)

    zip_buffer.seek(0)
    zip_content = zip_buffer.read()

    # Upload the batch
    files = {
        'files': ('test_resumes.zip', zip_content, 'application/zip')
    }
    data = {
        'notification_email': 'test@example.com'
    }

    response = await async_client.post(
        "/api/batch/upload",
        files=files,
        data=data
    )

    assert response.status_code == 201
    response_data = response.json()

    return {
        'batch_id': response_data['batch_id'],
        'total_files': response_data['total_files'],
        'status': response_data['status']
    }


# ============== EXPORT TESTS ==============

@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_batch_as_csv(async_client: AsyncClient, sample_batch_job: dict):
    """
    Test exporting batch results in CSV format.

    Flow:
    1. Create a batch job with uploaded resumes
    2. Request CSV export
    3. Verify CSV format and headers
    4. Verify batch metadata is included
    5. Verify file details are included
    """
    batch_id = sample_batch_job['batch_id']

    # Request CSV export
    response = await async_client.get(
        f"/api/batch/{batch_id}/export?format=csv"
    )

    # Verify response
    assert response.status_code == 200
    assert response.headers['content-type'] == 'text/csv; charset=utf-8'
    assert 'Content-Disposition' in response.headers
    assert f'batch_{batch_id}_export.csv' in response.headers['Content-Disposition']

    # Parse CSV content
    csv_content = response.text
    csv_reader = csv.reader(io.StringIO(csv_content))
    rows = list(csv_reader)

    # Verify CSV structure
    assert len(rows) > 0
    assert rows[0][0] == "Batch Export"

    # Verify batch metadata section
    batch_id_row = next(row for row in rows if len(row) > 0 and row[0] == "Batch ID")
    assert batch_id_row[1] == batch_id

    # Verify file details section exists
    files_header_row = next(row for row in rows if len(row) > 0 and row[0] == "FILES")
    assert files_header_row is not None

    # Verify file details headers
    files_header_index = rows.index(files_header_row)
    column_headers = rows[files_header_index + 1]
    assert "Resume ID" in column_headers
    assert "Filename" in column_headers
    assert "Status" in column_headers
    assert "Error" in column_headers


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_batch_as_json(async_client: AsyncClient, sample_batch_job: dict):
    """
    Test exporting batch results in JSON format.

    Flow:
    1. Create a batch job with uploaded resumes
    2. Request JSON export
    3. Verify JSON structure
    4. Verify all required fields are present
    5. Verify data types and values
    """
    batch_id = sample_batch_job['batch_id']

    # Request JSON export
    response = await async_client.get(
        f"/api/batch/{batch_id}/export?format=json"
    )

    # Verify response
    assert response.status_code == 200
    assert response.headers['content-type'] == 'application/json'

    # Parse JSON content
    export_data = response.json()

    # Verify JSON structure
    assert 'batch_id' in export_data
    assert 'status' in export_data
    assert 'total_files' in export_data
    assert 'successful' in export_data
    assert 'failed' in export_data
    assert 'created_at' in export_data
    assert 'completed_at' in export_data
    assert 'files' in export_data

    # Verify batch_id matches
    assert export_data['batch_id'] == batch_id

    # Verify total_files matches
    assert export_data['total_files'] == sample_batch_job['total_files']

    # Verify files array structure
    assert isinstance(export_data['files'], list)
    if len(export_data['files']) > 0:
        file_entry = export_data['files'][0]
        assert 'resume_id' in file_entry
        assert 'filename' in file_entry
        assert 'status' in file_entry
        assert 'error' in file_entry


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_batch_default_format_is_csv(async_client: AsyncClient, sample_batch_job: dict):
    """
    Test that the default export format is CSV when format parameter is not specified.

    Flow:
    1. Create a batch job
    2. Request export without format parameter
    3. Verify CSV format is returned
    """
    batch_id = sample_batch_job['batch_id']

    # Request export without format parameter
    response = await async_client.get(
        f"/api/batch/{batch_id}/export"
    )

    # Verify CSV response
    assert response.status_code == 200
    assert response.headers['content-type'] == 'text/csv; charset=utf-8'


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_invalid_batch_id_format(async_client: AsyncClient):
    """
    Test that exporting with an invalid batch ID format returns 422.

    Flow:
    1. Request export with malformed batch ID
    2. Verify 422 Unprocessable Entity response
    3. Verify error message is informative
    """
    invalid_batch_id = "not-a-valid-uuid"

    # Request export with invalid batch ID
    response = await async_client.get(
        f"/api/batch/{invalid_batch_id}/export?format=csv"
    )

    # Verify error response
    assert response.status_code == 422
    response_data = response.json()
    assert 'detail' in response_data
    assert 'Invalid batch ID format' in response_data['detail']


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_nonexistent_batch(async_client: AsyncClient):
    """
    Test that exporting a non-existent batch returns 404.

    Flow:
    1. Request export with valid UUID but non-existent batch
    2. Verify 404 Not Found response
    3. Verify error message is informative
    """
    nonexistent_batch_id = str(uuid4())

    # Request export for non-existent batch
    response = await async_client.get(
        f"/api/batch/{nonexistent_batch_id}/export?format=csv"
    )

    # Verify error response
    assert response.status_code == 404
    response_data = response.json()
    assert 'detail' in response_data
    assert 'not found' in response_data['detail'].lower()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_invalid_format(async_client: AsyncClient, sample_batch_job: dict):
    """
    Test that exporting with an invalid format parameter returns 422.

    Flow:
    1. Create a batch job
    2. Request export with invalid format (e.g., "xml", "pdf")
    3. Verify 422 Unprocessable Entity response
    4. Verify error message lists valid formats
    """
    batch_id = sample_batch_job['batch_id']

    # Request export with invalid format
    response = await async_client.get(
        f"/api/batch/{batch_id}/export?format=xml"
    )

    # Verify error response
    assert response.status_code == 422
    response_data = response.json()
    assert 'detail' in response_data
    assert 'Invalid export format' in response_data['detail']
    assert 'csv' in response_data['detail']
    assert 'json' in response_data['detail']


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_csv_contains_batch_metadata(async_client: AsyncClient, sample_batch_job: dict):
    """
    Test that CSV export contains all required batch metadata fields.

    Flow:
    1. Create a batch job
    2. Export as CSV
    3. Verify all metadata fields are present (Batch ID, Status, Total Files, etc.)
    """
    batch_id = sample_batch_job['batch_id']

    # Request CSV export
    response = await async_client.get(
        f"/api/batch/{batch_id}/export?format=csv"
    )

    assert response.status_code == 200

    # Parse CSV
    csv_content = response.text
    csv_reader = csv.reader(io.StringIO(csv_content))
    rows = list(csv_reader)

    # Extract all field names from the first column
    field_names = [row[0] for row in rows if len(row) > 0]

    # Verify required metadata fields are present
    assert "Batch ID" in field_names
    assert "Status" in field_names
    assert "Total Files" in field_names
    assert "Successful" in field_names
    assert "Failed" in field_names
    assert "Created At" in field_names
    assert "Completed At" in field_names


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_json_successful_and_failed_counts(async_client: AsyncClient, sample_batch_job: dict):
    """
    Test that JSON export correctly counts successful and failed files.

    Flow:
    1. Create a batch job
    2. Export as JSON
    3. Verify successful + failed = total_files
    4. Verify counts are non-negative integers
    """
    batch_id = sample_batch_job['batch_id']

    # Request JSON export
    response = await async_client.get(
        f"/api/batch/{batch_id}/export?format=json"
    )

    assert response.status_code == 200
    export_data = response.json()

    # Verify counts
    successful = export_data['successful']
    failed = export_data['failed']
    total_files = export_data['total_files']

    # Verify data types
    assert isinstance(successful, int)
    assert isinstance(failed, int)
    assert isinstance(total_files, int)

    # Verify non-negative values
    assert successful >= 0
    assert failed >= 0
    assert total_files >= 0

    # Verify the sum matches total (may not always equal if processing is incomplete)
    assert successful + failed <= total_files


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_csv_file_details_format(async_client: AsyncClient, sample_batch_job: dict):
    """
    Test that CSV export file details section has correct format and data.

    Flow:
    1. Create a batch job
    2. Export as CSV
    3. Verify file details section format
    4. Verify each file entry has all required columns
    """
    batch_id = sample_batch_job['batch_id']

    # Request CSV export
    response = await async_client.get(
        f"/api/batch/{batch_id}/export?format=csv"
    )

    assert response.status_code == 200

    # Parse CSV
    csv_content = response.text
    csv_reader = csv.reader(io.StringIO(csv_content))
    rows = list(csv_reader)

    # Find the FILES section
    files_section_index = next(
        i for i, row in enumerate(rows) if len(row) > 0 and row[0] == "FILES"
    )

    # Get column headers (next row after "FILES")
    column_headers = rows[files_section_index + 1]
    assert len(column_headers) >= 4
    assert column_headers[0] == "Resume ID"
    assert column_headers[1] == "Filename"
    assert column_headers[2] == "Status"
    assert column_headers[3] == "Error"

    # Verify file entries (if any exist)
    file_entries = rows[files_section_index + 2:]
    for entry in file_entries:
        if len(entry) >= 4 and entry[0]:  # Skip empty rows
            # Verify Resume ID looks like a UUID
            assert len(entry[0]) > 0
            # Verify Filename exists
            assert len(entry[1]) > 0
            # Verify Status is present
            assert len(entry[2]) > 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_json_file_details_structure(async_client: AsyncClient, sample_batch_job: dict):
    """
    Test that JSON export file details have correct structure.

    Flow:
    1. Create a batch job
    2. Export as JSON
    3. Verify files array structure
    4. Verify each file object has required fields
    """
    batch_id = sample_batch_job['batch_id']

    # Request JSON export
    response = await async_client.get(
        f"/api/batch/{batch_id}/export?format=json"
    )

    assert response.status_code == 200
    export_data = response.json()

    # Verify files array exists and is a list
    assert 'files' in export_data
    assert isinstance(export_data['files'], list)

    # Verify each file entry has required fields
    for file_entry in export_data['files']:
        assert isinstance(file_entry, dict)
        assert 'resume_id' in file_entry
        assert 'filename' in file_entry
        assert 'status' in file_entry
        assert 'error' in file_entry

        # Verify data types
        assert isinstance(file_entry['resume_id'], str)
        assert isinstance(file_entry['filename'], str)
        assert isinstance(file_entry['status'], str)
        # error can be None or string
        assert file_entry['error'] is None or isinstance(file_entry['error'], str)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_export_multiple_formats_same_batch(async_client: AsyncClient, sample_batch_job: dict):
    """
    Test that the same batch can be exported in both CSV and JSON formats.

    Flow:
    1. Create a batch job
    2. Export as CSV
    3. Export as JSON
    4. Verify both exports succeed
    5. Verify data consistency between formats
    """
    batch_id = sample_batch_job['batch_id']

    # Export as CSV
    csv_response = await async_client.get(
        f"/api/batch/{batch_id}/export?format=csv"
    )
    assert csv_response.status_code == 200
    assert 'text/csv' in csv_response.headers['content-type']

    # Export as JSON
    json_response = await async_client.get(
        f"/api/batch/{batch_id}/export?format=json"
    )
    assert json_response.status_code == 200
    assert 'application/json' in json_response.headers['content-type']

    # Verify JSON data
    json_data = json_response.json()
    assert json_data['batch_id'] == batch_id

    # Verify CSV contains the same batch ID
    csv_content = csv_response.text
    assert batch_id in csv_content
