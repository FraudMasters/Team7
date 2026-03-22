"""
Integration tests for LinkedIn CSV import functionality.

Tests cover the complete CSV import flow:
1. CSV file parsing and validation
2. Field mapping detection across different CSV formats
3. Profile data extraction and normalization
4. Error handling and validation
5. Bulk import operations
"""
import csv
import logging
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch

import pytest

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.linkedin_csv_importer import (
    LinkedInCSVImporter,
    LinkedInProfileData,
    CSVParseResult,
)


class TestStep1CSVFileParsing:
    """Test Step 1: Parse CSV file and extract candidate data."""

    @pytest.fixture
    def importer(self):
        """Create a LinkedInCSVImporter instance."""
        return LinkedInCSVImporter()

    @pytest.fixture
    def sample_csv_path(self):
        """Return path to sample CSV fixture."""
        return str(Path(__file__).parent / "fixtures" / "linkedin_sample.csv")

    def test_parse_valid_csv_file(self, importer, sample_csv_path):
        """Test parsing a valid LinkedIn CSV file."""
        result = importer.parse_csv_file(sample_csv_path)

        # Verify successful parsing
        assert result.success is True
        assert result.total_rows == 6  # 6 candidate rows
        assert result.valid_profiles == 6
        assert result.invalid_profiles == 0
        assert len(result.profiles) == 6
        assert len(result.errors) == 0

    def test_parse_csv_extracts_all_fields(self, importer, sample_csv_path):
        """Test that all fields are correctly extracted from CSV."""
        result = importer.parse_csv_file(sample_csv_path)

        # Check first profile (John Doe)
        profile = result.profiles[0]
        assert profile.first_name == "John"
        assert profile.last_name == "Doe"
        assert profile.email == "john.doe@example.com"
        assert profile.headline == "Senior Software Engineer at Tech Corp"
        assert profile.location == "San Francisco Bay Area"
        assert profile.current_company == "Tech Corp"
        assert profile.current_position == "Senior Software Engineer"
        assert profile.profile_url == "https://www.linkedin.com/in/johndoe"
        assert "Python" in profile.skills
        assert "JavaScript" in profile.skills
        assert len(profile.skills) == 10
        assert profile.connections == 500

    def test_parse_csv_handles_missing_optional_fields(self, importer, sample_csv_path):
        """Test that parser handles missing optional fields (like email)."""
        result = importer.parse_csv_file(sample_csv_path)

        # Check profile with missing email (David Rodriguez)
        profile = result.profiles[4]
        assert profile.first_name == "David"
        assert profile.last_name == "Rodriguez"
        assert profile.email is None  # Email is optional
        assert profile.headline == "DevOps Engineer | Cloud Infrastructure Specialist"
        assert profile.location == "Remote"

    def test_parse_csv_file_not_found(self, importer):
        """Test that FileNotFoundError is raised for non-existent file."""
        with pytest.raises(FileNotFoundError):
            importer.parse_csv_file("/path/to/nonexistent.csv")

    def test_parse_csv_content_directly(self, importer):
        """Test parsing CSV content from string."""
        csv_content = """First Name,Last Name,Email,Headline
John,Doe,john@example.com,Software Engineer
Jane,Smith,jane@example.com,Product Manager"""

        result = importer.parse_csv_content(csv_content)

        assert result.success is True
        assert result.total_rows == 2
        assert result.valid_profiles == 2
        assert len(result.profiles) == 2

        # Verify first profile
        profile = result.profiles[0]
        assert profile.first_name == "John"
        assert profile.last_name == "Doe"
        assert profile.email == "john@example.com"


class TestStep2FieldMappingDetection:
    """Test Step 2: Detect and map CSV fields to standard field names."""

    @pytest.fixture
    def importer(self):
        """Create a LinkedInCSVImporter instance."""
        return LinkedInCSVImporter()

    def test_field_mapping_standard_format(self, importer):
        """Test field mapping for standard LinkedIn export format."""
        headers = [
            "First Name",
            "Last Name",
            "Email",
            "Headline",
            "Location",
            "Company",
        ]

        mapping = importer._create_field_mapping(headers)

        assert mapping["first_name"] == "First Name"
        assert mapping["last_name"] == "Last Name"
        assert mapping["email"] == "Email"
        assert mapping["headline"] == "Headline"
        assert mapping["location"] == "Location"
        assert mapping["current_company"] == "Company"

    def test_field_mapping_alternative_names(self, importer):
        """Test field mapping with alternative field names."""
        headers = [
            "Given Name",  # Alternative for First Name
            "Surname",  # Alternative for Last Name
            "E-mail",  # Alternative for Email
            "Job Title",  # Alternative for Headline
            "City",  # Alternative for Location
        ]

        mapping = importer._create_field_mapping(headers)

        assert mapping["first_name"] == "Given Name"
        assert mapping["last_name"] == "Surname"
        assert mapping["email"] == "E-mail"
        assert mapping["headline"] == "Job Title"
        assert mapping["location"] == "City"

    def test_field_mapping_missing_optional_fields(self, importer):
        """Test field mapping when optional fields are missing."""
        headers = ["First Name", "Last Name"]  # Only required fields

        mapping = importer._create_field_mapping(headers)

        assert mapping["first_name"] == "First Name"
        assert mapping["last_name"] == "Last Name"
        assert mapping["email"] is None
        assert mapping["headline"] is None
        assert mapping["skills"] is None


class TestStep3CSVFormatDetection:
    """Test Step 3: Detect type of LinkedIn CSV export."""

    @pytest.fixture
    def importer(self):
        """Create a LinkedInCSVImporter instance."""
        return LinkedInCSVImporter()

    def test_detect_profile_search_export(self, importer):
        """Test detection of profile search export format."""
        headers = ["First Name", "Last Name", "Email", "Headline", "Location"]

        detected_format = importer._detect_csv_format(headers)

        assert detected_format == "profile_search_export"

    def test_detect_connections_export(self, importer):
        """Test detection of connections export format."""
        headers = ["First Name", "Last Name", "Connection Date", "Email"]

        detected_format = importer._detect_csv_format(headers)

        assert detected_format == "connections_export"

    def test_detect_inmail_export(self, importer):
        """Test detection of InMail recipient export format."""
        headers = ["First Name", "Last Name", "InMail Status", "Email"]

        detected_format = importer._detect_csv_format(headers)

        assert detected_format == "inmail_export"

    def test_detect_unknown_format(self, importer):
        """Test detection of unknown CSV format."""
        headers = ["Column A", "Column B", "Column C"]

        detected_format = importer._detect_csv_format(headers)

        assert detected_format == "unknown_format"


class TestStep4ProfileValidation:
    """Test Step 4: Validate profile data and required fields."""

    @pytest.fixture
    def importer(self):
        """Create a LinkedInCSVImporter instance."""
        return LinkedInCSVImporter()

    def test_validate_valid_profile(self, importer):
        """Test validation of a valid profile with all required fields."""
        profile = LinkedInProfileData(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            headline="Software Engineer",
        )

        validation_result = importer._validate_profile(profile)

        assert validation_result["valid"] is True
        assert "error" not in validation_result

    def test_validate_profile_missing_first_name(self, importer):
        """Test validation fails when first name is missing."""
        profile = LinkedInProfileData(
            first_name=None,  # Missing required field
            last_name="Doe",
            email="john@example.com",
        )

        validation_result = importer._validate_profile(profile)

        assert validation_result["valid"] is False
        assert "first_name" in validation_result["error"]

    def test_validate_profile_missing_last_name(self, importer):
        """Test validation fails when last name is missing."""
        profile = LinkedInProfileData(
            first_name="John",
            last_name=None,  # Missing required field
            email="john@example.com",
        )

        validation_result = importer._validate_profile(profile)

        assert validation_result["valid"] is False
        assert "last_name" in validation_result["error"]

    def test_validate_profile_missing_both_required_fields(self, importer):
        """Test validation fails when both required fields are missing."""
        profile = LinkedInProfileData(
            first_name=None,
            last_name=None,
            email="john@example.com",
        )

        validation_result = importer._validate_profile(profile)

        assert validation_result["valid"] is False
        assert "first_name" in validation_result["error"]
        assert "last_name" in validation_result["error"]

    def test_validate_profile_missing_email_is_ok(self, importer):
        """Test validation passes even when optional email field is missing."""
        profile = LinkedInProfileData(
            first_name="John",
            last_name="Doe",
            email=None,  # Email is optional
        )

        validation_result = importer._validate_profile(profile)

        assert validation_result["valid"] is True


class TestStep5SkillsParsing:
    """Test Step 5: Parse and extract skills from CSV data."""

    @pytest.fixture
    def importer(self):
        """Create a LinkedInCSVImporter instance."""
        return LinkedInCSVImporter()

    def test_parse_comma_separated_skills(self, importer):
        """Test parsing comma-separated skills."""
        csv_content = """First Name,Last Name,Skills
John,Doe,"Python, JavaScript, React, Node.js"
"""

        result = importer.parse_csv_content(csv_content)
        profile = result.profiles[0]

        assert len(profile.skills) == 4
        assert "Python" in profile.skills
        assert "JavaScript" in profile.skills
        assert "React" in profile.skills
        assert "Node.js" in profile.skills

    def test_parse_skills_with_extra_spaces(self, importer):
        """Test parsing skills with extra whitespace."""
        csv_content = """First Name,Last Name,Skills
John,Doe,"Python,  JavaScript,   React  ,Node.js"
"""

        result = importer.parse_csv_content(csv_content)
        profile = result.profiles[0]

        # Verify whitespace is trimmed
        assert "Python" in profile.skills
        assert "JavaScript" in profile.skills
        assert "React" in profile.skills
        assert "Node.js" in profile.skills
        # Check no skills have extra spaces
        for skill in profile.skills:
            assert skill == skill.strip()

    def test_parse_empty_skills(self, importer):
        """Test parsing profile with no skills."""
        csv_content = """First Name,Last Name,Skills
John,Doe,
"""

        result = importer.parse_csv_content(csv_content)
        profile = result.profiles[0]

        assert len(profile.skills) == 0


class TestStep6ConnectionsParsing:
    """Test Step 6: Parse LinkedIn connections count."""

    @pytest.fixture
    def importer(self):
        """Create a LinkedInCSVImporter instance."""
        return LinkedInCSVImporter()

    def test_parse_exact_connection_count(self, importer):
        """Test parsing exact connection count."""
        csv_content = """First Name,Last Name,Connections
John,Doe,250
"""

        result = importer.parse_csv_content(csv_content)
        profile = result.profiles[0]

        assert profile.connections == 250

    def test_parse_500_plus_connections(self, importer):
        """Test parsing 500+ connection format."""
        csv_content = """First Name,Last Name,Connections
John,Doe,500+
"""

        result = importer.parse_csv_content(csv_content)
        profile = result.profiles[0]

        # "500+" should be parsed as 500
        assert profile.connections == 500

    def test_parse_connections_with_comma(self, importer):
        """Test parsing connection count with comma separator."""
        csv_content = """First Name,Last Name,Connections
John,Doe,"1,234"
"""

        result = importer.parse_csv_content(csv_content)
        profile = result.profiles[0]

        assert profile.connections == 1234

    def test_parse_invalid_connections_format(self, importer):
        """Test parsing invalid connection count format."""
        csv_content = """First Name,Last Name,Connections
John,Doe,many
"""

        result = importer.parse_csv_content(csv_content)
        profile = result.profiles[0]

        # Invalid format should result in None
        assert profile.connections is None


class TestStep7ErrorHandling:
    """Test Step 7: Error handling and edge cases."""

    @pytest.fixture
    def importer(self):
        """Create a LinkedInCSVImporter instance."""
        return LinkedInCSVImporter()

    def test_parse_empty_csv(self, importer):
        """Test parsing empty CSV content."""
        csv_content = ""

        result = importer.parse_csv_content(csv_content)

        assert result.success is False
        assert len(result.errors) > 0
        assert "no headers" in result.errors[0].lower() or "empty" in result.errors[0].lower()

    def test_parse_csv_with_only_headers(self, importer):
        """Test parsing CSV with only header row."""
        csv_content = "First Name,Last Name,Email\n"

        result = importer.parse_csv_content(csv_content)

        assert result.success is True
        assert result.total_rows == 0
        assert result.valid_profiles == 0
        assert len(result.profiles) == 0

    def test_parse_csv_with_invalid_rows(self, importer):
        """Test parsing CSV with some invalid rows (missing required fields)."""
        csv_content = """First Name,Last Name,Email
John,Doe,john@example.com
,Smith,jane@example.com
Michael,,michael@example.com
Sarah,Johnson,sarah@example.com
"""

        result = importer.parse_csv_content(csv_content)

        # Should have 4 total rows, but only 2 valid (row 2 and 3 missing required fields)
        assert result.success is True
        assert result.total_rows == 4
        assert result.valid_profiles == 2
        assert result.invalid_profiles == 2
        assert len(result.profiles) == 2
        assert len(result.errors) == 2  # Two validation errors

    def test_parse_csv_missing_required_headers(self, importer):
        """Test parsing CSV that's missing required headers."""
        csv_content = """Email,Headline,Location
john@example.com,Software Engineer,San Francisco
"""

        result = importer.parse_csv_content(csv_content)

        # CSV missing First Name and Last Name - all rows should fail validation
        assert result.success is True
        assert result.total_rows == 1
        assert result.valid_profiles == 0
        assert result.invalid_profiles == 1
        assert len(result.errors) >= 1


class TestStep8HeaderValidation:
    """Test Step 8: Validate CSV headers before parsing."""

    @pytest.fixture
    def importer(self):
        """Create a LinkedInCSVImporter instance."""
        return LinkedInCSVImporter()

    def test_validate_headers_with_required_fields(self, importer):
        """Test header validation with all required fields present."""
        headers = ["First Name", "Last Name", "Email", "Profile URL"]

        validation_result = importer.validate_csv_headers(headers)

        assert validation_result["valid"] is True
        assert "detected_format" in validation_result
        assert "detected_fields" in validation_result

    def test_validate_headers_missing_required_field(self, importer):
        """Test header validation fails when required field is missing."""
        headers = ["First Name", "Email", "Location"]  # Missing Last Name

        validation_result = importer.validate_csv_headers(headers)

        assert validation_result["valid"] is False
        assert "last_name" in validation_result["error"]

    def test_validate_headers_missing_contact_info(self, importer):
        """Test header validation requires at least email or profile URL."""
        headers = ["First Name", "Last Name", "Location"]  # No email or profile URL

        validation_result = importer.validate_csv_headers(headers)

        assert validation_result["valid"] is False
        assert "email" in validation_result["error"].lower() or "profile url" in validation_result["error"].lower()

    def test_validate_headers_with_email_only(self, importer):
        """Test header validation passes with email (no profile URL)."""
        headers = ["First Name", "Last Name", "Email"]

        validation_result = importer.validate_csv_headers(headers)

        assert validation_result["valid"] is True

    def test_validate_headers_with_profile_url_only(self, importer):
        """Test header validation passes with profile URL (no email)."""
        headers = ["First Name", "Last Name", "Profile URL"]

        validation_result = importer.validate_csv_headers(headers)

        assert validation_result["valid"] is True


class TestStep9SupportedFormats:
    """Test Step 9: Verify supported CSV formats."""

    @pytest.fixture
    def importer(self):
        """Create a LinkedInCSVImporter instance."""
        return LinkedInCSVImporter()

    def test_get_supported_formats(self, importer):
        """Test that importer reports supported formats."""
        formats = importer.get_supported_formats()

        assert isinstance(formats, list)
        assert len(formats) > 0
        assert "profile_search_export" in formats
        assert "connections_export" in formats
        assert "inmail_export" in formats


class TestStep10RawDataStorage:
    """Test Step 10: Verify raw CSV data is preserved."""

    @pytest.fixture
    def importer(self):
        """Create a LinkedInCSVImporter instance."""
        return LinkedInCSVImporter()

    def test_raw_data_stored_in_profile(self, importer):
        """Test that raw CSV row data is stored in profile."""
        csv_content = """First Name,Last Name,Email,Custom Field
John,Doe,john@example.com,Custom Value
"""

        result = importer.parse_csv_content(csv_content)
        profile = result.profiles[0]

        # Verify raw data is stored
        assert profile.raw_data is not None
        assert isinstance(profile.raw_data, dict)
        assert profile.raw_data["First Name"] == "John"
        assert profile.raw_data["Last Name"] == "Doe"
        assert profile.raw_data["Email"] == "john@example.com"
        assert profile.raw_data["Custom Field"] == "Custom Value"

    def test_raw_data_includes_all_fields(self, importer):
        """Test that raw data includes all CSV fields, even unmapped ones."""
        csv_content = """First Name,Last Name,Email,Unmapped Field 1,Unmapped Field 2
John,Doe,john@example.com,Value 1,Value 2
"""

        result = importer.parse_csv_content(csv_content)
        profile = result.profiles[0]

        # Verify all fields are in raw data
        assert len(profile.raw_data) == 5
        assert "Unmapped Field 1" in profile.raw_data
        assert "Unmapped Field 2" in profile.raw_data
        assert profile.raw_data["Unmapped Field 1"] == "Value 1"
        assert profile.raw_data["Unmapped Field 2"] == "Value 2"


class TestStep11BulkImport:
    """Test Step 11: Bulk import operations with large CSV files."""

    @pytest.fixture
    def importer(self):
        """Create a LinkedInCSVImporter instance."""
        return LinkedInCSVImporter()

    def test_import_large_csv(self, importer):
        """Test importing CSV with many candidates."""
        # Generate CSV with 100 candidates
        rows = ["First Name,Last Name,Email"]
        for i in range(100):
            rows.append(f"Person{i},Lastname{i},person{i}@example.com")

        csv_content = "\n".join(rows)

        result = importer.parse_csv_content(csv_content)

        assert result.success is True
        assert result.total_rows == 100
        assert result.valid_profiles == 100
        assert result.invalid_profiles == 0
        assert len(result.profiles) == 100

    def test_import_reports_statistics(self, importer, sample_csv_path=None):
        """Test that import result includes detailed statistics."""
        csv_content = """First Name,Last Name,Email
John,Doe,john@example.com
,Smith,jane@example.com
Michael,Chen,michael@example.com
"""

        result = importer.parse_csv_content(csv_content)

        # Verify statistics
        assert hasattr(result, "total_rows")
        assert hasattr(result, "valid_profiles")
        assert hasattr(result, "invalid_profiles")
        assert result.total_rows == 3
        assert result.valid_profiles == 2
        assert result.invalid_profiles == 1


class TestStep12IntegrationWithSampleFile:
    """Test Step 12: Integration tests with actual sample CSV fixture."""

    @pytest.fixture
    def importer(self):
        """Create a LinkedInCSVImporter instance."""
        return LinkedInCSVImporter()

    @pytest.fixture
    def sample_csv_path(self):
        """Return path to sample CSV fixture."""
        return str(Path(__file__).parent / "fixtures" / "linkedin_sample.csv")

    def test_import_sample_csv_all_profiles_valid(self, importer, sample_csv_path):
        """Test that all profiles in sample CSV are valid."""
        result = importer.parse_csv_file(sample_csv_path)

        assert result.success is True
        assert result.valid_profiles == result.total_rows
        assert result.invalid_profiles == 0

    def test_import_sample_csv_profile_data_quality(self, importer, sample_csv_path):
        """Test data quality of imported profiles from sample CSV."""
        result = importer.parse_csv_file(sample_csv_path)

        # Verify all profiles have required fields
        for profile in result.profiles:
            assert profile.first_name is not None
            assert profile.last_name is not None
            assert len(profile.first_name) > 0
            assert len(profile.last_name) > 0

        # Verify at least some profiles have optional enrichment data
        profiles_with_skills = [p for p in result.profiles if p.skills]
        profiles_with_headlines = [p for p in result.profiles if p.headline]
        profiles_with_locations = [p for p in result.profiles if p.location]

        assert len(profiles_with_skills) > 0
        assert len(profiles_with_headlines) > 0
        assert len(profiles_with_locations) > 0

    def test_import_sample_csv_format_detection(self, importer, sample_csv_path):
        """Test that sample CSV format is correctly detected."""
        result = importer.parse_csv_file(sample_csv_path)

        assert result.detected_format is not None
        assert result.detected_format == "profile_search_export"

    def test_import_sample_csv_diverse_profiles(self, importer, sample_csv_path):
        """Test that sample CSV contains diverse profile types."""
        result = importer.parse_csv_file(sample_csv_path)

        # Verify we have different types of professionals
        roles = [p.headline for p in result.profiles if p.headline]
        locations = [p.location for p in result.profiles if p.location]

        # Should have multiple different roles and locations
        assert len(set(roles)) >= 4  # At least 4 different roles
        assert len(set(locations)) >= 4  # At least 4 different locations

        # Verify variety in skills
        all_skills = []
        for profile in result.profiles:
            all_skills.extend(profile.skills)

        unique_skills = set(all_skills)
        assert len(unique_skills) >= 20  # At least 20 unique skills across all profiles
