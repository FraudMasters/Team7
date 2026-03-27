"""
Integration tests for Indeed XML import functionality.

Tests cover the complete XML import flow:
1. XML file parsing and validation
2. Field mapping detection across different XML formats
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

from services.indeed_xml_importer import (
    IndeedXMLImporter,
    IndeedApplicationData,
    XMLParseResult,
)


class TestStep1XMLFileParsing:
    """Test Step 1: Parse XML file and extract application data."""

    @pytest.fixture
    def importer(self):
        """Create an IndeedXMLImporter instance."""
        return IndeedXMLImporter()

    @pytest.fixture
    def sample_xml_path(self):
        """Return path to sample XML fixture."""
        return str(Path(__file__).parent / "fixtures" / "indeed_sample.xml")

    def test_parse_valid_xml_file(self, importer, sample_xml_path):
        """Test parsing a valid Indeed XML file."""
        result = importer.parse_xml_file(sample_xml_path)

        # Verify successful parsing
        assert result.success is True
        assert result.total_records == 6  # 6 application records
        assert result.valid_applications == 6
        assert result.invalid_applications == 0
        assert len(result.applications) == 6
        assert len(result.errors) == 0

    def test_parse_xml_extracts_all_fields(self, importer, sample_xml_path):
        """Test that all fields are correctly extracted from XML."""
        result = importer.parse_xml_file(sample_xml_path)

        # Check first application (Sarah Williams)
        app = result.applications[0]
        assert app.applicant_id == "IND-2024-001"
        assert app.first_name == "Sarah"
        assert app.last_name == "Williams"
        assert app.email == "sarah.williams@example.com"
        assert app.phone == "+1-555-0101"
        assert app.job_title == "Senior Software Engineer"
        assert app.application_date == "2024-02-15"
        assert app.status == "Applied"
        assert app.location == "San Francisco, CA"
        assert app.resume_url == "https://indeed.com/resumes/sarah-williams-123456"
        assert "Senior Software Engineer with 8+ years" in app.resume_text
        assert "excited to apply" in app.cover_letter
        assert app.indeed_profile_url == "https://indeed.com/profile/sarah-williams-123456"

    def test_parse_xml_handles_missing_optional_fields(self, importer, sample_xml_path):
        """Test that parser handles missing optional fields (like phone, cover letter)."""
        result = importer.parse_xml_file(sample_xml_path)

        # Check application with missing phone (Emily Rodriguez)
        app = result.applications[2]
        assert app.first_name == "Emily"
        assert app.last_name == "Rodriguez"
        assert app.email == "emily.rodriguez@example.com"
        assert app.phone is None  # Phone is optional
        assert app.job_title == "UX Designer"

        # Check application without cover letter (Michael Chen)
        app2 = result.applications[1]
        assert app2.first_name == "Michael"
        assert app2.cover_letter is None  # Cover letter is optional

    def test_parse_xml_file_not_found(self, importer):
        """Test that FileNotFoundError is raised for non-existent file."""
        with pytest.raises(FileNotFoundError):
            importer.parse_xml_file("/path/to/nonexistent.xml")

    def test_parse_xml_content_directly(self, importer):
        """Test parsing XML content from string."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<IndeedApplications>
    <Application>
        <FirstName>John</FirstName>
        <LastName>Doe</LastName>
        <Email>john@example.com</Email>
        <JobTitle>Software Engineer</JobTitle>
    </Application>
    <Application>
        <FirstName>Jane</FirstName>
        <LastName>Smith</LastName>
        <Email>jane@example.com</Email>
        <JobTitle>Product Manager</JobTitle>
    </Application>
</IndeedApplications>"""

        result = importer.parse_xml_content(xml_content)

        assert result.success is True
        assert result.total_records == 2
        assert result.valid_applications == 2
        assert len(result.applications) == 2

        # Verify first application
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
        assert "FirstName" in app.raw_data or "first_name" in app.raw_data.values()


class TestStep2FieldMapping:
    """Test Step 2: Map XML elements to standard field names."""

    @pytest.fixture
    def importer(self):
        """Create an IndeedXMLImporter instance."""
        return IndeedXMLImporter()

    def test_field_mapping_standard_elements(self, importer):
        """Test field mapping for standard Indeed XML element names."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Application>
    <FirstName>John</FirstName>
    <LastName>Doe</LastName>
    <Email>john@example.com</Email>
    <Phone>555-0100</Phone>
    <JobTitle>Engineer</JobTitle>
</Application>"""

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
<Applicant>
    <givenName>John</givenName>
    <surname>Doe</surname>
    <EmailAddress>john@example.com</EmailAddress>
    <PhoneNumber>555-0100</PhoneNumber>
    <positionTitle>Engineer</positionTitle>
</Applicant>"""

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
<Application>
    <Candidate>
        <FirstName>John</FirstName>
        <LastName>Doe</LastName>
        <Contact>
            <Email>john@example.com</Email>
            <Phone>555-0100</Phone>
        </Contact>
    </Candidate>
    <JobTitle>Engineer</JobTitle>
</Application>"""

        result = importer.parse_xml_content(xml_content)
        app = result.applications[0]

        assert app.first_name == "John"
        assert app.last_name == "Doe"
        assert app.email == "john@example.com"
        assert app.phone == "555-0100"


class TestStep3FormatDetection:
    """Test Step 3: Detect type of Indeed XML export."""

    @pytest.fixture
    def importer(self):
        """Create an IndeedXMLImporter instance."""
        return IndeedXMLImporter()

    def test_detect_bulk_applications_export(self, importer):
        """Test detection of bulk applications export format."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<IndeedApplications>
    <Application>
        <Email>test@example.com</Email>
    </Application>
</IndeedApplications>"""

        root = ET.fromstring(xml_content)
        detected_format = importer._detect_xml_format(root)

        assert detected_format == "bulk_applications_export"

    def test_detect_single_application_export(self, importer):
        """Test detection of single application export format."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Application>
    <FirstName>John</FirstName>
    <Email>test@example.com</Email>
</Application>"""

        root = ET.fromstring(xml_content)
        detected_format = importer._detect_xml_format(root)

        assert detected_format == "single_application_export"

    def test_detect_resume_export(self, importer):
        """Test detection of resume export format."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<IndeedResumes>
    <Resume>
        <Email>test@example.com</Email>
    </Resume>
</IndeedResumes>"""

        root = ET.fromstring(xml_content)
        detected_format = importer._detect_xml_format(root)

        assert detected_format == "resume_export"

    def test_detect_indeed_application_export(self, importer):
        """Test detection of Indeed branded application export format."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<IndeedExport>
    <Application>
        <Email>test@example.com</Email>
    </Application>
</IndeedExport>"""

        root = ET.fromstring(xml_content)
        detected_format = importer._detect_xml_format(root)

        assert detected_format == "indeed_application_export"

    def test_format_detection_in_parse_result(self, importer):
        """Test that detected format is included in parse result."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<IndeedApplications>
    <Application>
        <Email>test@example.com</Email>
    </Application>
</IndeedApplications>"""

        result = importer.parse_xml_content(xml_content)

        assert result.detected_format == "bulk_applications_export"


class TestStep4DataExtraction:
    """Test Step 4: Extract and normalize application data."""

    @pytest.fixture
    def importer(self):
        """Create an IndeedXMLImporter instance."""
        return IndeedXMLImporter()

    def test_extract_complete_application_data(self, importer):
        """Test extraction of complete application with all fields."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Application>
    <ApplicantId>IND-001</ApplicantId>
    <FirstName>John</FirstName>
    <LastName>Doe</LastName>
    <Email>john@example.com</Email>
    <Phone>555-0100</Phone>
    <JobTitle>Software Engineer</JobTitle>
    <ApplicationDate>2024-02-15</ApplicationDate>
    <Status>Applied</Status>
    <Location>San Francisco</Location>
    <ResumeUrl>https://indeed.com/resume/123</ResumeUrl>
    <ResumeText>Experienced engineer...</ResumeText>
    <CoverLetter>I am excited...</CoverLetter>
    <ProfileUrl>https://indeed.com/profile/123</ProfileUrl>
</Application>"""

        result = importer.parse_xml_content(xml_content)
        app = result.applications[0]

        assert app.applicant_id == "IND-001"
        assert app.first_name == "John"
        assert app.last_name == "Doe"
        assert app.email == "john@example.com"
        assert app.phone == "555-0100"
        assert app.job_title == "Software Engineer"
        assert app.application_date == "2024-02-15"
        assert app.status == "Applied"
        assert app.location == "San Francisco"
        assert app.resume_url == "https://indeed.com/resume/123"
        assert app.resume_text == "Experienced engineer..."
        assert app.cover_letter == "I am excited..."
        assert app.indeed_profile_url == "https://indeed.com/profile/123"

    def test_extract_minimal_application_data(self, importer):
        """Test extraction of minimal application with only required fields."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Application>
    <FirstName>Jane</FirstName>
    <LastName>Smith</LastName>
    <Email>jane@example.com</Email>
</Application>"""

        result = importer.parse_xml_content(xml_content)

        assert result.success is True
        assert result.valid_applications == 1

        app = result.applications[0]
        assert app.first_name == "Jane"
        assert app.last_name == "Smith"
        assert app.email == "jane@example.com"
        assert app.phone is None
        assert app.job_title is None

    def test_parse_full_name_field(self, importer):
        """Test parsing when name is provided as single full name field."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Application>
    <Name>John Michael Doe</Name>
    <Email>john@example.com</Email>
</Application>"""

        result = importer.parse_xml_content(xml_content)
        app = result.applications[0]

        assert app.first_name == "John"
        assert app.last_name == "Michael Doe"
        assert app.email == "john@example.com"

    def test_multiple_applications_extraction(self, importer):
        """Test extraction of multiple applications from single XML."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<IndeedApplications>
    <Application>
        <FirstName>John</FirstName>
        <Email>john@example.com</Email>
    </Application>
    <Application>
        <FirstName>Jane</FirstName>
        <Email>jane@example.com</Email>
    </Application>
    <Application>
        <FirstName>Bob</FirstName>
        <Email>bob@example.com</Email>
    </Application>
</IndeedApplications>"""

        result = importer.parse_xml_content(xml_content)

        assert result.total_records == 3
        assert result.valid_applications == 3
        assert len(result.applications) == 3

        assert result.applications[0].first_name == "John"
        assert result.applications[1].first_name == "Jane"
        assert result.applications[2].first_name == "Bob"


class TestStep5Validation:
    """Test Step 5: Validate application data and required fields."""

    @pytest.fixture
    def importer(self):
        """Create an IndeedXMLImporter instance."""
        return IndeedXMLImporter()

    def test_validation_passes_with_required_fields(self, importer):
        """Test that validation passes when required fields are present."""
        app = IndeedApplicationData(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
        )

        result = importer._validate_application(app)

        assert result["valid"] is True

    def test_validation_fails_without_email(self, importer):
        """Test that validation fails when email is missing."""
        app = IndeedApplicationData(
            first_name="John",
            last_name="Doe",
        )

        result = importer._validate_application(app)

        assert result["valid"] is False
        assert "email" in result["error"].lower()

    def test_invalid_applications_are_skipped(self, importer):
        """Test that invalid applications are skipped during parsing."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<IndeedApplications>
    <Application>
        <FirstName>John</FirstName>
        <Email>john@example.com</Email>
    </Application>
    <Application>
        <FirstName>Jane</FirstName>
        <!-- Missing email - should be invalid -->
    </Application>
    <Application>
        <FirstName>Bob</FirstName>
        <Email>bob@example.com</Email>
    </Application>
</IndeedApplications>"""

        result = importer.parse_xml_content(xml_content)

        assert result.total_records == 3
        assert result.valid_applications == 2
        assert result.invalid_applications == 1
        assert len(result.applications) == 2
        assert len(result.errors) == 1

        # Valid applications should be John and Bob
        assert result.applications[0].first_name == "John"
        assert result.applications[1].first_name == "Bob"

    def test_validation_result_includes_error_messages(self, importer):
        """Test that validation errors include descriptive messages."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Application>
    <FirstName>John</FirstName>
    <!-- Missing email -->
</Application>"""

        result = importer.parse_xml_content(xml_content)

        assert result.invalid_applications == 1
        assert len(result.errors) > 0
        assert "email" in result.errors[0].lower()

    def test_validate_xml_structure(self, importer):
        """Test XML structure validation method."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<IndeedApplications>
    <Application>
        <Email>test@example.com</Email>
    </Application>
</IndeedApplications>"""

        root = ET.fromstring(xml_content)
        validation = importer.validate_xml_structure(root)

        assert validation["valid"] is True
        assert validation["application_count"] == 1
        assert validation["detected_format"] == "bulk_applications_export"


class TestStep6ErrorHandling:
    """Test Step 6: Error handling and edge cases."""

    @pytest.fixture
    def importer(self):
        """Create an IndeedXMLImporter instance."""
        return IndeedXMLImporter()

    def test_parse_invalid_xml_syntax(self, importer):
        """Test parsing XML with syntax errors."""
        invalid_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Application>
    <FirstName>John</FirstName>
    <Email>john@example.com
    <!-- Missing closing tag -->
</Application>"""

        result = importer.parse_xml_content(invalid_xml)

        assert result.success is False
        assert len(result.errors) > 0
        assert "xml" in result.errors[0].lower()

    def test_parse_empty_xml(self, importer):
        """Test parsing empty XML file."""
        empty_xml = """<?xml version="1.0" encoding="UTF-8"?>
<IndeedApplications>
</IndeedApplications>"""

        result = importer.parse_xml_content(empty_xml)

        assert result.success is True
        assert result.total_records == 0
        assert result.valid_applications == 0
        assert len(result.applications) == 0
        assert len(result.warnings) > 0

    def test_parse_xml_with_whitespace(self, importer):
        """Test that whitespace in XML elements is handled correctly."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Application>
    <FirstName>  John  </FirstName>
    <LastName>
        Doe
    </LastName>
    <Email>  john@example.com  </Email>
</Application>"""

        result = importer.parse_xml_content(xml_content)
        app = result.applications[0]

        assert app.first_name == "John"
        assert app.last_name == "Doe"
        assert app.email == "john@example.com"

    def test_parse_xml_with_special_characters(self, importer):
        """Test parsing XML with special characters and encoding."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Application>
    <FirstName>José</FirstName>
    <LastName>García-López</LastName>
    <Email>jose@example.com</Email>
    <ResumeText>Experience with C++ &amp; Python</ResumeText>
</Application>"""

        result = importer.parse_xml_content(xml_content)
        app = result.applications[0]

        assert app.first_name == "José"
        assert app.last_name == "García-López"
        assert "C++ & Python" in app.resume_text

    def test_parse_xml_missing_root_element(self, importer):
        """Test parsing XML without proper root element."""
        invalid_xml = """<?xml version="1.0" encoding="UTF-8"?>
<FirstName>John</FirstName>
<Email>john@example.com</Email>"""

        result = importer.parse_xml_content(invalid_xml)

        # Should fail to parse due to multiple root elements
        assert result.success is False
        assert len(result.errors) > 0

    def test_get_supported_formats(self, importer):
        """Test getting list of supported XML formats."""
        formats = importer.get_supported_formats()

        assert isinstance(formats, list)
        assert len(formats) > 0
        assert "bulk_applications_export" in formats
        assert "single_application_export" in formats
        assert "resume_export" in formats


class TestStep7IntegrationScenarios:
    """Test Step 7: Real-world integration scenarios."""

    @pytest.fixture
    def importer(self):
        """Create an IndeedXMLImporter instance."""
        return IndeedXMLImporter()

    @pytest.fixture
    def sample_xml_path(self):
        """Return path to sample XML fixture."""
        return str(Path(__file__).parent / "fixtures" / "indeed_sample.xml")

    def test_bulk_import_workflow(self, importer, sample_xml_path):
        """Test complete bulk import workflow with sample data."""
        result = importer.parse_xml_file(sample_xml_path)

        # Verify successful bulk import
        assert result.success is True
        assert result.total_records == 6
        assert result.valid_applications == 6
        assert result.invalid_applications == 0

        # Verify variety of data is captured
        emails = [app.email for app in result.applications]
        assert len(set(emails)) == 6  # All unique emails

        job_titles = [app.job_title for app in result.applications]
        assert "Senior Software Engineer" in job_titles
        assert "Product Manager" in job_titles
        assert "UX Designer" in job_titles

    def test_parse_and_filter_by_status(self, importer, sample_xml_path):
        """Test parsing and filtering applications by status."""
        result = importer.parse_xml_file(sample_xml_path)

        # Filter applications by status
        applied = [app for app in result.applications if app.status == "Applied"]
        under_review = [app for app in result.applications if app.status == "Under Review"]
        interviewing = [app for app in result.applications if app.status == "Interviewing"]

        assert len(applied) >= 1
        assert len(under_review) >= 1
        assert len(interviewing) >= 1

    def test_parse_and_extract_contact_info(self, importer, sample_xml_path):
        """Test extracting contact information for outreach."""
        result = importer.parse_xml_file(sample_xml_path)

        # Verify all applications have email
        for app in result.applications:
            assert app.email is not None
            assert "@" in app.email

        # Some should have phone numbers
        apps_with_phone = [app for app in result.applications if app.phone]
        assert len(apps_with_phone) >= 2

    def test_parse_and_validate_resume_content(self, importer, sample_xml_path):
        """Test that resume content is properly extracted."""
        result = importer.parse_xml_file(sample_xml_path)

        # Verify resume text is captured
        apps_with_resume = [app for app in result.applications if app.resume_text]
        assert len(apps_with_resume) >= 5

        # Verify resume URLs are captured
        apps_with_url = [app for app in result.applications if app.resume_url]
        assert len(apps_with_url) >= 5

    def test_error_recovery_in_batch_processing(self, importer):
        """Test that one invalid record doesn't break entire batch."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<IndeedApplications>
    <Application>
        <FirstName>John</FirstName>
        <Email>john@example.com</Email>
    </Application>
    <Application>
        <FirstName>Invalid</FirstName>
        <!-- Missing email - invalid -->
    </Application>
    <Application>
        <FirstName>Jane</FirstName>
        <Email>jane@example.com</Email>
    </Application>
    <Application>
        <!-- Malformed application -->
    </Application>
    <Application>
        <FirstName>Bob</FirstName>
        <Email>bob@example.com</Email>
    </Application>
</IndeedApplications>"""

        result = importer.parse_xml_content(xml_content)

        # Should successfully process valid records despite errors
        assert result.success is True
        assert result.valid_applications == 3
        assert result.invalid_applications == 2
        assert len(result.applications) == 3

        # Verify the valid applications were processed
        names = [app.first_name for app in result.applications]
        assert "John" in names
        assert "Jane" in names
        assert "Bob" in names


class TestStep8DataTypeConversion:
    """Test Step 8: Data type handling and conversion."""

    @pytest.fixture
    def importer(self):
        """Create an IndeedXMLImporter instance."""
        return IndeedXMLImporter()

    def test_handle_empty_string_values(self, importer):
        """Test handling of empty string values in XML."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Application>
    <FirstName></FirstName>
    <LastName>Doe</LastName>
    <Email>john@example.com</Email>
    <Phone></Phone>
</Application>"""

        result = importer.parse_xml_content(xml_content)
        app = result.applications[0]

        # Empty strings should be treated as None
        assert app.first_name is None or app.first_name == ""
        assert app.phone is None or app.phone == ""

    def test_handle_cdata_sections(self, importer):
        """Test handling of CDATA sections in XML."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Application>
    <FirstName>John</FirstName>
    <Email>john@example.com</Email>
    <ResumeText><![CDATA[Senior Engineer with 10+ years experience.
Skills include Python, Java, and C++.]]></ResumeText>
</Application>"""

        result = importer.parse_xml_content(xml_content)
        app = result.applications[0]

        assert "Senior Engineer with 10+ years" in app.resume_text
        assert "Python" in app.resume_text

    def test_application_data_dataclass(self, importer):
        """Test IndeedApplicationData dataclass initialization."""
        app = IndeedApplicationData(
            applicant_id="IND-001",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="555-0100",
        )

        assert app.applicant_id == "IND-001"
        assert app.first_name == "John"
        assert app.last_name == "Doe"
        assert app.email == "john@example.com"
        assert app.phone == "555-0100"
        assert isinstance(app.raw_data, dict)

    def test_xml_parse_result_dataclass(self, importer):
        """Test XMLParseResult dataclass initialization."""
        result = XMLParseResult(
            success=True,
            total_records=5,
            valid_applications=4,
            invalid_applications=1,
            detected_format="bulk_applications_export",
        )

        assert result.success is True
        assert result.total_records == 5
        assert result.valid_applications == 4
        assert result.invalid_applications == 1
        assert result.detected_format == "bulk_applications_export"
        assert isinstance(result.applications, list)
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)
