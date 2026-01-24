# Data Extractor Service

Resume text extraction service for PDF and DOCX files with robust error handling.

## Features

- **PDF Extraction**: Dual-library support (PyPDF2 + pdfplumber fallback)
- **DOCX Extraction**: Full support including table-based layouts
- **Error Handling**: Graceful handling of malformed, empty, and corrupted files
- **Validation**: Pre-extraction validation for file integrity
- **Comprehensive Tests**: Full test suite with edge case coverage

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Requirements

- Python 3.9+
- PyPDF2==3.0.1
- python-docx==1.1.2
- pdfplumber==0.11.4
- pytest==8.3.3 (for testing)

## Usage

### Basic PDF Extraction

```python
from extract import extract_text_from_pdf

result = extract_text_from_pdf("resume.pdf")

print(result["text"])      # Extracted text
print(result["method"])    # 'pypdf2' or 'pdfplumber'
print(result["pages"])     # Number of pages
print(result["error"])     # None if successful
```

### Basic DOCX Extraction

```python
from extract import extract_text_from_docx

result = extract_text_from_docx("resume.docx")

print(result["text"])         # Extracted text
print(result["paragraphs"])   # Number of paragraphs
print(result["error"])        # None if successful
```

### With Validation

```python
from extract import validate_pdf_file, extract_text_from_pdf

# Validate first
validation = validate_pdf_file("resume.pdf")
if validation["valid"]:
    result = extract_text_from_pdf("resume.pdf")
else:
    print(f"Invalid file: {validation['reason']}")
```

## Running Tests

### Using pytest (recommended)

```bash
cd services/data_extractor
pytest tests/test_extract.py -v
```

### Run specific test class

```bash
pytest tests/test_extract.py::TestPDFExtraction -v
pytest tests/test_extract.py::TestDOCXExtraction -v
pytest tests/test_extract.py::TestErrorHandling -v
```

### With coverage

```bash
pytest tests/test_extract.py -v --cov=. --cov-report=term-missing
```

## Test Structure

```
tests/
├── __init__.py
└── test_extract.py
    ├── TestPDFExtraction      # PDF extraction tests
    ├── TestDOCXExtraction     # DOCX extraction tests
    └── TestErrorHandling      # Edge case and error tests
```

### Test Coverage

- **Valid files**: Normal PDF/DOCX files
- **Invalid files**: Wrong extensions, non-existent files
- **Empty files**: Files with no content
- **Corrupted files**: Malformed file structures
- **Special characters**: Unicode and multilingual text
- **Tables**: DOCX files with table-based layouts
- **Large files**: Multi-page documents

## Sample Files

Sample test files are provided in `test_samples/`:

- `sample.pdf` - Sample resume in PDF format
- `sample.docx` - Sample resume in DOCX format

These files are used by the test suite for validation.

## API Reference

### PDF Functions

#### `extract_text_from_pdf(file_path, use_fallback=True)`

Extract text from PDF with dual-library support.

**Parameters:**
- `file_path` (str|Path): Path to PDF file
- `use_fallback` (bool): Try pdfplumber if PyPDF2 fails (default: True)

**Returns:** Dictionary with keys:
- `text` (str|None): Extracted text content
- `method` (str|None): 'pypdf2', 'pdfplumber', or None
- `pages` (int): Number of pages
- `error` (str|None): Error message if failed

**Raises:**
- `FileNotFoundError`: If file doesn't exist
- `ValueError`: If file is not a PDF

#### `validate_pdf_file(file_path)`

Validate PDF file before extraction.

**Returns:** Dictionary with keys:
- `valid` (bool): True if file is valid
- `reason` (str|None): Explanation if invalid

### DOCX Functions

#### `extract_text_from_docx(file_path)`

Extract text from DOCX including table contents.

**Parameters:**
- `file_path` (str|Path): Path to DOCX file

**Returns:** Dictionary with keys:
- `text` (str|None): Extracted text content
- `method` (str|None): 'python-docx' or None
- `paragraphs` (int): Number of paragraphs
- `error` (str|None): Error message if failed

**Raises:**
- `FileNotFoundError`: If file doesn't exist
- `ValueError`: If file is not a DOCX

#### `validate_docx_file(file_path)`

Validate DOCX file before extraction.

**Returns:** Dictionary with keys:
- `valid` (bool): True if file is valid
- `reason` (str|None): Explanation if invalid

## Error Handling

The service handles various error conditions gracefully:

### File Not Found
```python
extract_text_from_pdf("missing.pdf")
# Raises: FileNotFoundError("File not found: missing.pdf")
```

### Invalid File Type
```python
extract_text_from_pdf("document.txt")
# Raises: ValueError("File is not a PDF: document.txt")
```

### Malformed Files
```python
result = extract_text_from_pdf("corrupted.pdf")
# Returns: {"text": None, "error": "...", ...}
```

### Empty Files
```python
validation = validate_pdf_file("empty.pdf")
# Returns: {"valid": False, "reason": "File is empty"}
```

## Development

### Code Style

This project follows standard Python conventions:
- Type hints for all function parameters
- Comprehensive docstrings
- Logging for debugging
- PEP 8 formatting

### Testing Guidelines

1. **Use fixtures** for reusable test data
2. **Test both success and failure cases**
3. **Verify error messages are helpful**
4. **Test edge cases** (empty, corrupted, large files)
5. **Use tmp_path** for temporary test files

## Troubleshooting

### Tests fail with "ModuleNotFoundError"

Ensure you're running from the correct directory:
```bash
cd services/data_extractor
pytest tests/test_extract.py -v
```

### PDF extraction returns minimal text

Try enabling fallback mode (default):
```python
result = extract_text_from_pdf("file.pdf", use_fallback=True)
```

### DOCX extraction misses table content

The service automatically extracts table contents. If missing, ensure:
- File is not corrupted
- Tables are properly formatted in the DOCX

## License

MIT License - See LICENSE file for details
