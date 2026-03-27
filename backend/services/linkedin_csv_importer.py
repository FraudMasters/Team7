"""
LinkedIn CSV Import Service

This module provides LinkedIn CSV parsing and import capabilities for candidate data.

Features:
- Parse LinkedIn Recruiter CSV export files
- Extract candidate profile information (name, email, headline, location, etc.)
- Validate CSV format and required fields
- Handle multiple LinkedIn CSV export formats
- Comprehensive error reporting and validation

The service supports standard LinkedIn Recruiter CSV exports including:
- Profile exports (candidates, connections)
- Search results exports
- InMail recipient lists
"""
import csv
import logging
from dataclasses import dataclass, field
from io import StringIO
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class LinkedInProfileData:
    """
    Parsed LinkedIn profile data from CSV row.

    Attributes:
        first_name: Candidate first name
        last_name: Candidate last name
        email: Email address (may be None if not available)
        headline: LinkedIn headline/job title
        location: Geographic location
        current_company: Current company name
        current_position: Current job title
        profile_url: LinkedIn profile URL
        summary: Profile summary/about section
        skills: List of skills (parsed from comma-separated string)
        experience: Work experience details
        education: Education details
        connections: Number of LinkedIn connections
        raw_data: Dictionary of all raw CSV fields
    """

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    headline: Optional[str] = None
    location: Optional[str] = None
    current_company: Optional[str] = None
    current_position: Optional[str] = None
    profile_url: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = field(default_factory=list)
    experience: Optional[str] = None
    education: Optional[str] = None
    connections: Optional[int] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CSVParseResult:
    """
    Result of CSV parsing operation.

    Attributes:
        success: Whether parsing was successful
        total_rows: Total number of rows in CSV (excluding header)
        valid_profiles: Number of valid profiles parsed
        invalid_profiles: Number of profiles that failed validation
        profiles: List of parsed profile data
        errors: List of error messages encountered
        warnings: List of warning messages
        detected_format: Detected LinkedIn CSV format type
    """

    success: bool
    total_rows: int = 0
    valid_profiles: int = 0
    invalid_profiles: int = 0
    profiles: List[LinkedInProfileData] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    detected_format: Optional[str] = None


class LinkedInCSVImporter:
    """
    Service for parsing LinkedIn CSV exports and extracting candidate data.

    This service handles various LinkedIn CSV export formats and normalizes
    the data into a consistent structure for import into the ATS.

    LinkedIn CSV formats supported:
    - Profile search results export
    - Saved candidates export
    - Connection list export
    - InMail recipient export
    """

    # Common field name mappings across different LinkedIn CSV formats
    FIELD_MAPPINGS = {
        # First Name variants
        "first_name": ["First Name", "FirstName", "first name", "Given Name"],
        # Last Name variants
        "last_name": ["Last Name", "LastName", "last name", "Surname", "Family Name"],
        # Email variants
        "email": ["Email", "Email Address", "email", "E-mail"],
        # Headline variants
        "headline": ["Headline", "Title", "Job Title", "Current Title"],
        # Location variants
        "location": ["Location", "Geographic Location", "City", "Region"],
        # Company variants
        "current_company": [
            "Company",
            "Current Company",
            "Organization",
            "Current Organization",
        ],
        # Position variants
        "current_position": [
            "Position",
            "Current Position",
            "Current Title",
            "Job Title",
        ],
        # Profile URL variants
        "profile_url": ["Profile URL", "LinkedIn URL", "URL", "Link"],
        # Summary variants
        "summary": ["Summary", "About", "Profile Summary", "Bio"],
        # Skills variants
        "skills": ["Skills", "Top Skills", "Skill Set"],
        # Experience variants
        "experience": ["Experience", "Work Experience", "Employment History"],
        # Education variants
        "education": ["Education", "Schools", "Academic Background"],
        # Connections variants
        "connections": ["Connections", "Number of Connections", "Connection Count"],
    }

    # Required fields for valid profile import
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def __init__(self):
        """Initialize the LinkedIn CSV importer service."""
        logger.info("Initialized LinkedInCSVImporter")

    def parse_csv_file(self, file_path: str, encoding: str = "utf-8") -> CSVParseResult:
        """
        Parse a LinkedIn CSV file from disk.

        Args:
            file_path: Path to the CSV file
            encoding: File encoding (default: utf-8)

        Returns:
            CSVParseResult with parsed profiles and metadata

        Raises:
            FileNotFoundError: If file does not exist
            PermissionError: If file cannot be read
        """
        try:
            logger.info(f"Parsing LinkedIn CSV file: {file_path}")

            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()

            return self.parse_csv_content(content)

        except FileNotFoundError as e:
            logger.error(f"CSV file not found: {file_path}")
            raise FileNotFoundError(f"CSV file not found: {file_path}") from e

        except PermissionError as e:
            logger.error(f"Permission denied reading CSV file: {file_path}")
            raise PermissionError(f"Cannot read CSV file: {file_path}") from e

        except Exception as e:
            logger.error(f"Error reading CSV file: {e}", exc_info=True)
            return CSVParseResult(
                success=False,
                errors=[f"Failed to read CSV file: {str(e)}"],
            )

    def parse_csv_content(self, content: str) -> CSVParseResult:
        """
        Parse LinkedIn CSV content from a string.

        Args:
            content: CSV content as string

        Returns:
            CSVParseResult with parsed profiles and metadata
        """
        try:
            logger.info("Parsing LinkedIn CSV content")

            # Parse CSV content
            csv_file = StringIO(content)
            reader = csv.DictReader(csv_file)

            # Detect CSV format and create field mapping
            if reader.fieldnames is None:
                logger.error("CSV file has no headers")
                return CSVParseResult(
                    success=False,
                    errors=["CSV file has no headers or is empty"],
                )

            field_mapping = self._create_field_mapping(reader.fieldnames)
            detected_format = self._detect_csv_format(reader.fieldnames)

            logger.info(f"Detected CSV format: {detected_format}")
            logger.debug(f"Field mapping: {field_mapping}")

            # Parse each row
            profiles = []
            errors = []
            warnings = []
            row_number = 1  # Start at 1 (header is row 0)

            for row in reader:
                row_number += 1
                try:
                    profile = self._parse_csv_row(row, field_mapping)

                    # Validate required fields
                    validation_result = self._validate_profile(profile)
                    if validation_result["valid"]:
                        profiles.append(profile)
                    else:
                        errors.append(
                            f"Row {row_number}: {validation_result['error']}"
                        )
                        warnings.append(
                            f"Skipping row {row_number} due to validation errors"
                        )

                except Exception as e:
                    logger.warning(f"Error parsing row {row_number}: {e}")
                    errors.append(f"Row {row_number}: {str(e)}")

            total_rows = row_number - 1  # Exclude header
            valid_profiles = len(profiles)
            invalid_profiles = total_rows - valid_profiles

            logger.info(
                f"Parsed {total_rows} rows: {valid_profiles} valid, "
                f"{invalid_profiles} invalid"
            )

            return CSVParseResult(
                success=True,
                total_rows=total_rows,
                valid_profiles=valid_profiles,
                invalid_profiles=invalid_profiles,
                profiles=profiles,
                errors=errors,
                warnings=warnings,
                detected_format=detected_format,
            )

        except Exception as e:
            logger.error(f"Error parsing CSV content: {e}", exc_info=True)
            return CSVParseResult(
                success=False,
                errors=[f"Failed to parse CSV: {str(e)}"],
            )

    def _create_field_mapping(
        self, headers: List[str]
    ) -> Dict[str, Optional[str]]:
        """
        Create mapping from standard field names to actual CSV headers.

        Args:
            headers: List of CSV header names

        Returns:
            Dictionary mapping standard field names to actual CSV headers
        """
        mapping = {}

        for standard_field, variants in self.FIELD_MAPPINGS.items():
            # Try to find matching header
            matched_header = None
            for variant in variants:
                if variant in headers:
                    matched_header = variant
                    break

            mapping[standard_field] = matched_header

        logger.debug(f"Created field mapping for {len(mapping)} fields")
        return mapping

    def _detect_csv_format(self, headers: List[str]) -> str:
        """
        Detect the type of LinkedIn CSV export based on headers.

        Args:
            headers: List of CSV header names

        Returns:
            String identifying the detected format type
        """
        headers_lower = [h.lower() for h in headers]

        # Check for specific format indicators
        if "saved search" in " ".join(headers_lower):
            return "saved_search_export"
        elif "inmail" in " ".join(headers_lower):
            return "inmail_export"
        elif "connection" in " ".join(headers_lower):
            return "connections_export"
        elif any("first name" in h for h in headers_lower):
            return "profile_search_export"
        else:
            return "unknown_format"

    def _parse_csv_row(
        self, row: Dict[str, str], field_mapping: Dict[str, Optional[str]]
    ) -> LinkedInProfileData:
        """
        Parse a single CSV row into LinkedInProfileData.

        Args:
            row: Dictionary of CSV row data (header -> value)
            field_mapping: Mapping from standard fields to CSV headers

        Returns:
            LinkedInProfileData object with parsed data
        """
        profile = LinkedInProfileData(raw_data=dict(row))

        # Extract each field using the mapping
        for standard_field, csv_header in field_mapping.items():
            if csv_header is None:
                continue

            value = row.get(csv_header, "").strip()

            if not value:
                continue

            # Parse based on field type
            if standard_field == "first_name":
                profile.first_name = value
            elif standard_field == "last_name":
                profile.last_name = value
            elif standard_field == "email":
                profile.email = value if value else None
            elif standard_field == "headline":
                profile.headline = value
            elif standard_field == "location":
                profile.location = value
            elif standard_field == "current_company":
                profile.current_company = value
            elif standard_field == "current_position":
                profile.current_position = value
            elif standard_field == "profile_url":
                profile.profile_url = value
            elif standard_field == "summary":
                profile.summary = value
            elif standard_field == "skills":
                # Parse comma-separated skills
                profile.skills = [
                    s.strip() for s in value.split(",") if s.strip()
                ]
            elif standard_field == "experience":
                profile.experience = value
            elif standard_field == "education":
                profile.education = value
            elif standard_field == "connections":
                # Parse connection count (handle "500+" format)
                try:
                    connections_str = value.replace("+", "").replace(",", "")
                    profile.connections = int(connections_str)
                except (ValueError, TypeError):
                    logger.debug(f"Could not parse connections: {value}")
                    profile.connections = None

        return profile

    def _validate_profile(self, profile: LinkedInProfileData) -> Dict[str, Any]:
        """
        Validate that a profile has required fields.

        Args:
            profile: LinkedInProfileData to validate

        Returns:
            Dictionary with 'valid' boolean and optional 'error' message
        """
        missing_fields = []

        for required_field in self.REQUIRED_FIELDS:
            value = getattr(profile, required_field, None)
            if not value:
                missing_fields.append(required_field)

        if missing_fields:
            return {
                "valid": False,
                "error": f"Missing required fields: {', '.join(missing_fields)}",
            }

        return {"valid": True}

    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported LinkedIn CSV formats.

        Returns:
            List of supported format names
        """
        return [
            "profile_search_export",
            "saved_search_export",
            "connections_export",
            "inmail_export",
        ]

    def validate_csv_headers(self, headers: List[str]) -> Dict[str, Any]:
        """
        Validate that CSV headers contain minimum required fields.

        Args:
            headers: List of CSV header names

        Returns:
            Dictionary with validation results
        """
        field_mapping = self._create_field_mapping(headers)

        # Check for required fields
        missing_required = []
        for required_field in self.REQUIRED_FIELDS:
            if field_mapping.get(required_field) is None:
                missing_required.append(required_field)

        if missing_required:
            return {
                "valid": False,
                "error": f"CSV missing required fields: {', '.join(missing_required)}",
                "detected_fields": list(field_mapping.keys()),
            }

        # Check for at least one contact method (email or profile URL)
        has_contact = (
            field_mapping.get("email") is not None
            or field_mapping.get("profile_url") is not None
        )

        if not has_contact:
            return {
                "valid": False,
                "error": "CSV must contain at least Email or Profile URL field",
                "detected_fields": list(field_mapping.keys()),
            }

        return {
            "valid": True,
            "detected_fields": list(field_mapping.keys()),
            "detected_format": self._detect_csv_format(headers),
        }
