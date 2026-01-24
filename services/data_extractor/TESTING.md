# Testing Guide

## Quick Start

```bash
# From project root
cd services/data_extractor

# Run all tests
pytest tests/test_extract.py -v

# Run with coverage
pytest tests/test_extract.py --cov=. --cov-report=html

# Run specific test class
pytest tests/test_extract.py::TestPDFExtraction -v
```

## Test Results Interpretation

### Successful Test Output

```
tests/test_extract.py::TestPDFExtraction::test_extract_text_from_valid_pdf PASSED
tests/test_extract.py::TestPDFExtraction::test_extract_text_from_pdf_with_fallback PASSED
...
======================== 20 passed in 2.45s ========================
```

### Common Issues

#### ImportError: No module named 'extract'

**Cause:** Wrong working directory

**Solution:**
```bash
cd services/data_extractor
pytest tests/test_extract.py -v
```

#### FileNotFoundError: Sample files not found

**Cause:** Sample test files missing

**Solution:**
```bash
# Verify sample files exist
ls test_samples/

# If missing, they should be:
# - test_samples/sample.pdf
# - test_samples/sample.docx
```

## Test Files

### test_extract.py Structure

```python
class TestPDFExtraction:
    """Tests for PDF text extraction"""
    - test_extract_text_from_valid_pdf
    - test_extract_text_from_pdf_with_fallback
    - test_extract_text_from_nonexistent_pdf
    - test_extract_text_from_invalid_extension
    - test_extract_text_from_empty_pdf
    - test_extract_with_corrupted_pdf
    - test_validate_valid_pdf
    - test_validate_nonexistent_pdf
    - test_validate_wrong_extension
    - test_validate_empty_pdf

class TestDOCXExtraction:
    """Tests for DOCX text extraction"""
    - test_extract_text_from_valid_docx
    - test_extract_text_from_docx_with_tables
    - test_extract_text_from_nonexistent_docx
    - test_extract_text_from_invalid_docx_extension
    - test_extract_text_from_empty_docx
    - test_extract_text_from_corrupted_docx
    - test_validate_valid_docx
    - test_validate_nonexistent_docx
    - test_validate_wrong_docx_extension
    - test_validate_empty_docx

class TestErrorHandling:
    """Tests for edge cases and error handling"""
    - test_docx_with_special_characters
    - test_pdf_with_no_extractable_text
    - test_docx_with_only_tables
```

## Fixtures

### sample_pdf_path
Returns path to `test_samples/sample.pdf`

### sample_docx_path
Returns path to `test_samples/sample.docx`

### empty_pdf_path
Creates temporary empty PDF file

### sample_docx_with_tables_path
Creates temporary DOCX with tables

### empty_docx_path
Creates temporary empty DOCX file

## Expected Test Coverage

- **Unit Tests**: 100% of extract.py functions
- **Success Cases**: Valid PDF/DOCX files
- **Error Cases**: Missing files, wrong types, corrupted files
- **Edge Cases**: Empty files, special characters, large files

## Manual Testing

### Test PDF Extraction

```python
from extract import extract_text_from_pdf

# Test valid file
result = extract_text_from_pdf("test_samples/sample.pdf")
assert result["text"] is not None
assert result["error"] is None

# Test missing file
try:
    extract_text_from_pdf("missing.pdf")
except FileNotFoundError:
    pass  # Expected
```

### Test DOCX Extraction

```python
from extract import extract_text_from_docx

# Test valid file
result = extract_text_from_docx("test_samples/sample.docx")
assert result["text"] is not None
assert "JANE SMITH" in result["text"]

# Test validation
validation = validate_docx_file("test_samples/sample.docx")
assert validation["valid"] is True
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r services/data_extractor/requirements.txt
      - run: cd services/data_extractor && pytest tests/ -v
```
