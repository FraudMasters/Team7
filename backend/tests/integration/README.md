# Integration Tests

This directory contains integration tests for the resume analysis system.

## Overview

These integration tests validate the complete end-to-end flow of the resume analysis system, including:

- **Resume Upload** → File storage and validation
- **Text Extraction** → PDF/DOCX parsing using data_extractor service
- **ML/NLP Analysis** → Keyword extraction, NER, grammar checking
- **Job Matching** → Skill comparison with synonym handling
- **Error Handling** → Invalid files, missing files, edge cases

## Test Structure

### `test_resume_flow.py`

Main integration test suite with 687 lines covering:

- `TestResumeUploadFlow` - Tests for file upload endpoint
- `TestResumeAnalysisFlow` - Tests for analysis pipeline
- `TestJobMatchingFlow` - Tests for job matching with skill synonyms
- `TestEndToEndWorkflows` - Complete user workflows
- `TestErrorHandling` - Edge cases and error scenarios
- `TestHealthChecks` - Health and readiness endpoints

## Running the Tests

### Run all integration tests:
```bash
cd backend
pytest tests/integration/ -v
```

### Run specific test class:
```bash
pytest tests/integration/test_resume_flow.py::TestResumeUploadFlow -v
```

### Run specific test:
```bash
pytest tests/integration/test_resume_flow.py::TestResumeUploadFlow::test_upload_valid_pdf -v
```

### Skip slow tests:
```bash
pytest tests/integration/ -v -m "not slow"
```

### With coverage:
```bash
pytest tests/integration/ -v --cov=api --cov-report=term-missing
```

## Requirements

The integration tests require:

1. **FastAPI application** running or TestClient available
2. **Data extractor service** accessible via sys.path
3. **ML/NLP models** (KeyBERT, SpaCy) - mocked or cached
4. **Upload directory** (`data/uploads/`) writable
5. **Test fixtures** - sample PDF/DOCX files in `services/data_extractor/test_samples/`

## Fixtures

### `test_pdf_file`
Returns bytes of a minimal valid PDF file for testing.

### `test_docx_file`
Returns bytes of a DOCX file (from test_samples).

### `sample_vacancy_data`
Returns dictionary with sample job vacancy requirements.

### `uploaded_file_id`
Uploads a test file and returns its ID for use in subsequent tests.

### `client`
FastAPI TestClient instance for making HTTP requests.

## Cleanup

Tests automatically clean up uploaded files using the `cleanup_uploaded_files` autouse fixture.

## Markers

- `@pytest.mark.slow` - Tests that take >5 seconds (ML model loading, analysis)
- `@pytest.mark.integration` - All integration tests

## Notes

- Tests use `TestClient` from FastAPI for HTTP simulation
- ML models are cached to avoid reload on each test
- Files are uploaded to `data/uploads/` and cleaned up after tests
- Some tests validate error handling with corrupted/malformed files
- Grammar checking is disabled in most tests for faster execution

## Troubleshooting

### Tests fail with "File not found"
Ensure `services/data_extractor/test_samples/sample.pdf` exists.

### Tests fail with import errors
Run from the `backend/` directory to ensure correct module paths.

### Tests timeout
Increase timeout or skip slow tests: `pytest -m "not slow"`

### Port already in error
Ensure no other instance of the application is running.
