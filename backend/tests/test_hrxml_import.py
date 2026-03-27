"""
Integration tests for HR-XML import functionality.

Tests cover the complete XML import flow:
1. XML file parsing and validation
2. Field mapping detection across different HR-XML formats
3. Application data extraction and normalization
4. Error handling and validation
5. Bulk import operations
"""
import logging
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET

import pytest

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.hrxml_importer import (
    HRXMLImporter,
    HRXMLApplicationData,
    XMLParseResult,
)


class TestStep1XMLFileParsing:
    """Test Step 1: Parse XML file and extract application data."""

    @pytest.fixture
    def importer(self):
        """Create an HRXMLImporter instance."""
        return HRXMLImporter()

    @pytest.fixture
    def sample_xml_path(self):
        """Return path to sample XML fixture."""
        return str(Path(__file__).parent / "fixtures" / "hrxml_sample.xml")

    def test_parse_valid_xml_file(self, importer, sample_xml_path):
        """Test parsing a valid HR-XML file."""
        result = importer.parse_xml_file(sample_xml_path)

        # Verify successful parsing
        assert result.success is True
        assert result.total_records == 6  # 6 candidate records
        assert result.valid_applications == 6
        assert result.invalid_applications == 0
        assert len(result.applications) == 6
        assert len(result.errors) == 0

    def test_parse_xml_extracts_all_fields(self, importer, sample_xml_path):
        """Test that all fields are correctly extracted from XML."""
        result = importer.parse_xml_file(sample_xml_path)

        # Check first candidate (Jennifer Martinez)
        app = result.applications[0]
        assert app.candidate_id == "HRXML-2024-001"
        assert app.first_name == "Jennifer"
        assert app.last_name == "Martinez"
        assert app.email == "jennifer.martinez@example.com"
        assert app.phone == "+1-555-1001"
        assert app.job_title == "Software Architect"
        assert app.application_date == "2024-03-10"
        assert app.status == "Active"
        assert app.location == "Boston, MA"
        assert app.resume_url == "https://example.com/resumes/jennifer-martinez-001"
        assert "Software Architect with 10+ years" in app.resume_text
        assert "thrilled to apply" in app.cover_letter
        assert app.linkedin_url == "https://linkedin.com/in/jennifer-martinez"

    def test_parse_xml_handles_missing_optional_fields(self, importer, sample_xml_path):
        """Test that parser handles missing optional fields (like phone, cover letter)."""
        result = importer.parse_xml_file(sample_xml_path)

        # Check candidate with missing phone (Amanda Thompson)
        app = result.applications[2]
        assert app.first_name == "Amanda"
        assert app.last_name == "Thompson"
        assert app.email == "amanda.thompson@example.com"
        assert app.phone is None  # Phone is optional
        assert app.job_title == "Product Designer"

        # Check candidate without cover letter (Robert Johnson)
        app2 = result.applications[1]
        assert app2.first_name == "Robert"
        assert app2.cover_letter is None  # Cover letter is optional

    def test_parse_xml_file_not_found(self, importer):
        """Test that FileNotFoundError is raised for non-existent file."""
        with pytest.raises(FileNotFoundError):
            importer.parse_xml_file("/path/to/nonexistent.xml")

    def test_parse_xml_content_directly(self, importer):
        """Test parsing XML content from string."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Candidates>
    <Candidate>
        <GivenName>John</GivenName>
        <FamilyName>Doe</FamilyName>
        <Email>john@example.com</Email>
        <PositionTitle>Software Engineer</PositionTitle>
    </Candidate>
    <Candidate>
        <GivenName>Jane</GivenName>
        <FamilyName>Smith</FamilyName>
        <Email>jane@example.com</Email>
        <PositionTitle>Product Manager</PositionTitle>
    </Candidate>
</Candidates>"""

        result = importer.parse_xml_content(xml_content)

        assert result.success is True
        assert result.total_records == 2
        assert result.valid_applications == 2
        assert len(result.applications) == 2

        # Verify first candidate
        app = result.applications[0]
        assert app.first_name == "John"
        assert app.last_name == "Doe"
        assert app.email == "john@example.com"
        assert app.job_title == "Software Engineer"

    def test_parse_xml_stores_raw_data(self, importer, sample_xml_path):
        """Test that raw XML data is stored for debugging/auditing."""
        result = importer.parse_xml_file(sample_xml_path)

        app = result.applications[0]
        assert isinstance(app.raw_data, dict)
        assert len(app.raw_data) > 0
        # Check for either the raw field name or the value
        assert any("Jennifer" in str(v) for v in app.raw_data.values())


class TestStep2FieldMapping:
    """Test Step 2: Map XML elements to standard field names."""

    @pytest.fixture
    def importer(self):
        """Create an HRXMLImporter instance."""
        return HRXMLImporter()

    def test_field_mapping_standard_elements(self, importer):
        """Test field mapping for standard HR-XML element names."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Candidate>
    <GivenName>John</GivenName>
    <FamilyName>Doe</FamilyName>
    <Email>john@example.com</Email>
    <Phone>555-0100</Phone>
    <PositionTitle>Engineer</PositionTitle>
</Candidate>"""

        result = importer.parse_xml_content(xml_content)
        app = result.applications[0]

        assert app.first_name == "John"
        assert app.last_name == "Doe"
        assert app.email == "john@example.com"
        assert app.phone == "555-0100"
        assert app.job_title == "Engineer"

    def test_field_mapping_alternative_element_names(self, importer):
        """Test field mapping with alternative XML element names."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Candidate>
    <FirstName>John</FirstName>
    <LastName>Doe</LastName>
    <EmailAddress>john@example.com</EmailAddress>
    <PhoneNumber>555-0100</PhoneNumber>
    <JobTitle>Engineer</JobTitle>
</Candidate>"""

        result = importer.parse_xml_content(xml_content)
        app = result.applications[0]

        assert app.first_name == "John"
        assert app.last_name == "Doe"
        assert app.email == "john@example.com"
        assert app.phone == "555-0100"
        assert app.job_title == "Engineer"

    def test_field_mapping_nested_elements(self, importer):
        """Test field mapping with nested XML structure."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Candidate>
    <PersonName>
        <GivenName>John</GivenName>
        <FamilyName>Doe</FamilyName>
    </PersonName>
    <ContactMethod>
        <InternetEmailAddress>john@example.com</InternetEmailAddress>
        <Telephone>
            <FormattedNumber>555-0100</FormattedNumber>
        </Telephone>
    </ContactMethod>
    <PositionTitle>Engineer</PositionTitle>
</Candidate>"""

        result = importer.parse_xml_content(xml_content)
        app = result.applications[0]

        assert app.first_name == "John"
        assert app.last_name == "Doe"
        assert app.email == "john@example.com"
        assert app.phone == "555-0100"
        assert app.job_title == "Engineer"

    def test_field_mapping_with_namespaces(self, importer):
        """Test field mapping with XML namespaces."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<hrxml:Candidate xmlns:hrxml="http://ns.hr-xml.org/2007-04-15">
    <hrxml:GivenName>John</hrxml:GivenName>
    <hrxml:FamilyName>Doe</hrxml:FamilyName>
    <hrxml:Email>john@example.com</hrxml:Email>
</hrxml:Candidate>"""

        result = importer.parse_xml_content(xml_content)
        app = result.applications[0]

        assert app.first_name == "John"
        assert app.last_name == "Doe"
        assert app.email == "john@example.com"

    def test_field_mapping_full_name_parsing(self, importer):
        """Test parsing when only full name is provided."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Candidate>
    <Name>John Doe Smith</Name>
    <Email>john@example.com</Email>
</Candidate>"""

        result = importer.parse_xml_content(xml_content)
        app = result.applications[0]

        assert app.first_name == "John"
        assert app.last_name == "Doe Smith"
        assert app.email == "john@example.com"

    def test_field_mapping_resume_fields(self, importer):
        """Test mapping of resume-related fields."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Resume>
    <GivenName>Jane</GivenName>
    <FamilyName>Smith</FamilyName>
    <Email>jane@example.com</Email>
    <ResumeLink>https://example.com/resume.pdf</ResumeLink>
    <TextResume>Experienced software developer with 5 years...</TextResume>
</Resume>"""

        result = importer.parse_xml_content(xml_content)
        app = result.applications[0]

        assert app.first_name == "Jane"
        assert app.email == "jane@example.com"
        assert app.resume_url == "https://example.com/resume.pdf"
        assert "Experienced software developer" in app.resume_text


class TestStep3Validation:
    """Test Step 3: Validate extracted application data."""

    @pytest.fixture
    def importer(self):
        """Create an HRXMLImporter instance."""
        return HRXMLImporter()

    def test_validation_requires_email(self, importer):
        """Test that email is a required field."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Candidate>
    <GivenName>John</GivenName>
    <FamilyName>Doe</FamilyName>
    <PositionTitle>Engineer</PositionTitle>
</Candidate>"""

        result = importer.parse_xml_content(xml_content)

        # Should fail validation without email
        assert result.total_records == 1
        assert result.valid_applications == 0
        assert result.invalid_applications == 1
        assert len(result.errors) > 0
        assert "email" in result.errors[0].lower()

    def test_validation_accepts_minimal_valid_record(self, importer):
        """Test that record with only required fields is valid."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Candidate>
    <Email>john@example.com</Email>
</Candidate>"""

        result = importer.parse_xml_content(xml_content)

        assert result.success is True
        assert result.valid_applications == 1
        assert result.invalid_applications == 0
        assert len(result.applications) == 1

    def test_validation_reports_missing_fields(self, importer):
        """Test that validation reports which fields are missing."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Candidate>
    <GivenName>John</GivenName>
    <FamilyName>Doe</FamilyName>
</Candidate>"""

        result = importer.parse_xml_content(xml_content)

        assert result.invalid_applications == 1
        assert any("email" in error.lower() for error in result.errors)

    def test_validation_mixed_valid_invalid(self, importer):
        """Test parsing file with both valid and invalid records."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Candidates>
    <Candidate>
        <GivenName>Valid</GivenName>
        <Email>valid@example.com</Email>
    </Candidate>
    <Candidate>
        <GivenName>Invalid</GivenName>
        <FamilyName>NoEmail</FamilyName>
    </Candidate>
    <Candidate>
        <Email>another-valid@example.com</Email>
    </Candidate>
</Candidates>"""

        result = importer.parse_xml_content(xml_content)

        assert result.total_records == 3
        assert result.valid_applications == 2
        assert result.invalid_applications == 1
        assert len(result.applications) == 2


class TestStep4ErrorHandling:
    """Test Step 4: Error handling and edge cases."""

    @pytest.fixture
    def importer(self):
        """Create an HRXMLImporter instance."""
        return HRXMLImporter()

    def test_error_handling_malformed_xml(self, importer):
        """Test handling of malformed XML."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Candidates>
    <Candidate>
        <GivenName>John</GivenName>
        <Email>john@example.com
    </Candidate>
</Candidates>"""

        result = importer.parse_xml_content(xml_content)

        assert result.success is False
        assert len(result.errors) > 0
        assert "xml" in result.errors[0].lower()

    def test_error_handling_empty_xml(self, importer):
        """Test handling of empty XML content."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Candidates>
</Candidates>"""

        result = importer.parse_xml_content(xml_content)

        assert result.success is True
        assert result.total_records == 0
        assert len(result.applications) == 0
        assert len(result.warnings) > 0

    def test_error_handling_empty_string(self, importer):
        """Test handling of empty string input."""
        result = importer.parse_xml_content("")

        assert result.success is False
        assert len(result.errors) > 0

    def test_error_handling_invalid_xml_structure(self, importer):
        """Test handling of XML without candidate elements."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<SomeOtherRoot>
    <RandomElement>Data</RandomElement>
</SomeOtherRoot>"""

        result = importer.parse_xml_content(xml_content)

        assert result.success is True
        assert result.total_records == 0
        assert len(result.warnings) > 0

    def test_error_handling_whitespace_in_fields(self, importer):
        """Test that whitespace is properly trimmed from fields."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Candidate>
    <GivenName>  John  </GivenName>
    <FamilyName>  Doe  </FamilyName>
    <Email>  john@example.com  </Email>
</Candidate>"""

        result = importer.parse_xml_content(xml_content)

        app = result.applications[0]
        assert app.first_name == "John"
        assert app.last_name == "Doe"
        assert app.email == "john@example.com"

    def test_error_handling_special_characters(self, importer):
        """Test handling of special characters in XML."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Candidate>
    <GivenName>François</GivenName>
    <FamilyName>O'Brien</FamilyName>
    <Email>françois.obrien@example.com</Email>
    <ResumeText>Expert in C++ &amp; Python. Salary &gt; $100k.</ResumeText>
</Candidate>"""

        result = importer.parse_xml_content(xml_content)

        app = result.applications[0]
        assert app.first_name == "François"
        assert app.last_name == "O'Brien"
        assert "C++ & Python" in app.resume_text
        assert "> $100k" in app.resume_text


class TestStep5BulkImport:
    """Test Step 5: Bulk import operations and format detection."""

    @pytest.fixture
    def importer(self):
        """Create an HRXMLImporter instance."""
        return HRXMLImporter()

    @pytest.fixture
    def sample_xml_path(self):
        """Return path to sample XML fixture."""
        return str(Path(__file__).parent / "fixtures" / "hrxml_sample.xml")

    def test_bulk_import_parses_multiple_candidates(self, importer, sample_xml_path):
        """Test bulk import of multiple candidates."""
        result = importer.parse_xml_file(sample_xml_path)

        assert result.success is True
        assert result.total_records == 6
        assert result.valid_applications == 6
        assert len(result.applications) == 6

        # Verify all candidates were parsed
        emails = [app.email for app in result.applications]
        assert "jennifer.martinez@example.com" in emails
        assert "robert.johnson@example.com" in emails
        assert "amanda.thompson@example.com" in emails
        assert "christopher.lee@example.com" in emails
        assert "michelle.davis@example.com" in emails
        assert "daniel.garcia@example.com" in emails

    def test_format_detection_bulk_candidates(self, importer):
        """Test detection of bulk candidates export format."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Candidates>
    <Candidate>
        <Email>test1@example.com</Email>
    </Candidate>
    <Candidate>
        <Email>test2@example.com</Email>
    </Candidate>
</Candidates>"""

        result = importer.parse_xml_content(xml_content)

        assert result.detected_format == "bulk_candidates_export"

    def test_format_detection_single_candidate(self, importer):
        """Test detection of single candidate export format."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Candidate>
    <Email>test@example.com</Email>
</Candidate>"""

        result = importer.parse_xml_content(xml_content)

        assert result.detected_format == "single_candidate_export"

    def test_format_detection_resume_export(self, importer):
        """Test detection of resume export format."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Resume>
    <Email>test@example.com</Email>
    <TextResume>Resume content here...</TextResume>
</Resume>"""

        result = importer.parse_xml_content(xml_content)

        assert result.detected_format == "single_resume_export"

    def test_format_detection_with_namespace(self, importer):
        """Test detection of HR-XML format with namespace."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<hrxml:HrXml xmlns:hrxml="http://ns.hr-xml.org/2007-04-15">
    <hrxml:Candidate>
        <hrxml:Email>test@example.com</hrxml:Email>
    </hrxml:Candidate>
</hrxml:HrXml>"""

        result = importer.parse_xml_content(xml_content)

        assert "hrxml" in result.detected_format

    def test_get_supported_formats(self, importer):
        """Test retrieval of supported formats list."""
        formats = importer.get_supported_formats()

        assert isinstance(formats, list)
        assert len(formats) > 0
        assert "bulk_candidates_export" in formats
        assert "single_candidate_export" in formats
        assert "resume_export" in formats

    def test_validate_xml_structure_valid(self, importer):
        """Test XML structure validation for valid input."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Candidates>
    <Candidate>
        <Email>test@example.com</Email>
    </Candidate>
</Candidates>"""

        root = ET.fromstring(xml_content)
        validation = importer.validate_xml_structure(root)

        assert validation["valid"] is True
        assert validation["application_count"] == 1
        assert "detected_format" in validation

    def test_validate_xml_structure_no_candidates(self, importer):
        """Test XML structure validation for XML without candidates."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<SomeOtherRoot>
    <Data>Not a candidate</Data>
</SomeOtherRoot>"""

        root = ET.fromstring(xml_content)
        validation = importer.validate_xml_structure(root)

        assert validation["valid"] is False
        assert "error" in validation

    def test_validate_xml_structure_missing_required_fields(self, importer):
        """Test XML structure validation when first candidate missing required fields."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Candidates>
    <Candidate>
        <GivenName>John</GivenName>
        <FamilyName>Doe</FamilyName>
    </Candidate>
</Candidates>"""

        root = ET.fromstring(xml_content)
        validation = importer.validate_xml_structure(root)

        assert validation["valid"] is False
        assert "error" in validation
        assert "validation" in validation["error"].lower()


class TestStep6IntegrationScenarios:
    """Test Step 6: Real-world integration scenarios."""

    @pytest.fixture
    def importer(self):
        """Create an HRXMLImporter instance."""
        return HRXMLImporter()

    def test_scenario_complete_candidate_profile(self, importer):
        """Test importing a complete candidate profile with all fields."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Candidate>
    <CandidateId>CAND-123</CandidateId>
    <GivenName>Alice</GivenName>
    <FamilyName>Johnson</FamilyName>
    <Email>alice@example.com</Email>
    <Phone>555-1234</Phone>
    <PositionTitle>Senior Engineer</PositionTitle>
    <ApplicationDate>2024-03-20</ApplicationDate>
    <Status>Active</Status>
    <Location>San Francisco, CA</Location>
    <ResumeLink>https://example.com/resume.pdf</ResumeLink>
    <TextResume>Senior Engineer with 10 years experience...</TextResume>
    <CoverLetter>I am excited to apply...</CoverLetter>
    <LinkedInURL>https://linkedin.com/in/alice-johnson</LinkedInURL>
</Candidate>"""

        result = importer.parse_xml_content(xml_content)

        assert result.success is True
        assert result.valid_applications == 1

        app = result.applications[0]
        assert app.candidate_id == "CAND-123"
        assert app.first_name == "Alice"
        assert app.last_name == "Johnson"
        assert app.email == "alice@example.com"
        assert app.phone == "555-1234"
        assert app.job_title == "Senior Engineer"
        assert app.application_date == "2024-03-20"
        assert app.status == "Active"
        assert app.location == "San Francisco, CA"
        assert app.resume_url == "https://example.com/resume.pdf"
        assert app.resume_text is not None
        assert app.cover_letter is not None
        assert app.linkedin_url == "https://linkedin.com/in/alice-johnson"

    def test_scenario_minimal_candidate_profile(self, importer):
        """Test importing minimal candidate profile with only email."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Candidate>
    <Email>minimal@example.com</Email>
</Candidate>"""

        result = importer.parse_xml_content(xml_content)

        assert result.success is True
        assert result.valid_applications == 1

        app = result.applications[0]
        assert app.email == "minimal@example.com"
        assert app.first_name is None
        assert app.last_name is None

    def test_scenario_mixed_quality_data(self, importer):
        """Test importing mix of complete and incomplete candidate records."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Candidates>
    <Candidate>
        <GivenName>Complete</GivenName>
        <FamilyName>Candidate</FamilyName>
        <Email>complete@example.com</Email>
        <Phone>555-0001</Phone>
        <PositionTitle>Engineer</PositionTitle>
    </Candidate>
    <Candidate>
        <Email>minimal@example.com</Email>
    </Candidate>
    <Candidate>
        <GivenName>Invalid</GivenName>
        <FamilyName>NoEmail</FamilyName>
    </Candidate>
    <Candidate>
        <GivenName>Another</GivenName>
        <Email>another@example.com</Email>
        <PositionTitle>Designer</PositionTitle>
    </Candidate>
</Candidates>"""

        result = importer.parse_xml_content(xml_content)

        assert result.total_records == 4
        assert result.valid_applications == 3
        assert result.invalid_applications == 1
        assert len(result.applications) == 3
        assert len(result.errors) > 0

    def test_scenario_file_encoding_utf8(self, importer, tmp_path):
        """Test importing file with UTF-8 encoding."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Candidate>
    <GivenName>José</GivenName>
    <FamilyName>García</FamilyName>
    <Email>jose@example.com</Email>
</Candidate>"""

        # Create temporary file
        temp_file = tmp_path / "test_utf8.xml"
        temp_file.write_text(xml_content, encoding="utf-8")

        result = importer.parse_xml_file(str(temp_file))

        assert result.success is True
        app = result.applications[0]
        assert app.first_name == "José"
        assert app.last_name == "García"

    def test_scenario_large_resume_text(self, importer):
        """Test importing candidate with large resume text."""
        large_resume = "Experience: " + ("Software engineer with extensive background. " * 100)
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Candidate>
    <Email>large-resume@example.com</Email>
    <TextResume>{large_resume}</TextResume>
</Candidate>"""

        result = importer.parse_xml_content(xml_content)

        assert result.success is True
        app = result.applications[0]
        assert len(app.resume_text) > 1000
        assert "Software engineer" in app.resume_text
