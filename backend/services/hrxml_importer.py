"""
HR-XML Import Service

This module provides HR-XML parsing and import capabilities for candidate data.

Features:
- Parse HR-XML export files (standard HR data exchange format)
- Extract candidate application information (name, email, phone, resume, etc.)
- Validate XML format and required fields
- Handle multiple HR-XML schema versions
- Comprehensive error reporting and validation

The service supports standard HR-XML formats including:
- Candidate exports (candidate profiles)
- Resume exports (candidate profiles with resume data)
- Application exports (candidate applications)
"""
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class HRXMLApplicationData:
    """
    Parsed HR-XML application data from XML.

    Attributes:
        candidate_id: Unique identifier for the candidate in HR-XML
        first_name: Candidate first name
        last_name: Candidate last name
        email: Email address
        phone: Phone number (optional)
        resume_url: URL to download resume file
        resume_text: Extracted resume text content
        job_title: Job title applied for or desired position
        application_date: Date when application was submitted
        status: Current application status
        location: Candidate location
        cover_letter: Cover letter text (optional)
        linkedin_url: Link to LinkedIn profile
        raw_data: Dictionary of all raw XML fields
    """

    candidate_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    resume_url: Optional[str] = None
    resume_text: Optional[str] = None
    job_title: Optional[str] = None
    application_date: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None
    cover_letter: Optional[str] = None
    linkedin_url: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class XMLParseResult:
    """
    Result of XML parsing operation.

    Attributes:
        success: Whether parsing was successful
        total_records: Total number of records in XML
        valid_applications: Number of valid applications parsed
        invalid_applications: Number of applications that failed validation
        applications: List of parsed application data
        errors: List of error messages encountered
        warnings: List of warning messages
        detected_format: Detected HR-XML format type
    """

    success: bool
    total_records: int = 0
    valid_applications: int = 0
    invalid_applications: int = 0
    applications: List[HRXMLApplicationData] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    detected_format: Optional[str] = None


class HRXMLImporter:
    """
    Service for parsing HR-XML exports and extracting candidate data.

    This service handles various HR-XML export formats and normalizes
    the data into a consistent structure for import into the ATS.

    HR-XML formats supported:
    - Candidate export (candidate profiles)
    - Resume export (candidate profiles with resume data)
    - Application export (candidate applications)
    """

    # XML element name mappings across different HR-XML formats
    ELEMENT_MAPPINGS = {
        # Candidate ID variants
        "candidate_id": ["CandidateId", "candidate_id", "Id", "id", "PersonId", "CandidateID"],
        # First Name variants
        "first_name": ["GivenName", "FirstName", "first_name", "firstName", "givenName"],
        # Last Name variants
        "last_name": ["FamilyName", "LastName", "last_name", "lastName", "familyName", "Surname"],
        # Email variants
        "email": ["Email", "email", "EmailAddress", "InternetEmailAddress", "ContactEmail"],
        # Phone variants
        "phone": ["Phone", "phone", "PhoneNumber", "Telephone", "Mobile", "FormattedNumber"],
        # Resume URL variants
        "resume_url": ["ResumeLink", "ResumeURL", "resume_url", "Attachment", "DocumentLink"],
        # Resume Text variants
        "resume_text": ["TextResume", "ResumeText", "resume_text", "FormattedResume", "ResumeContent"],
        # Job Title variants
        "job_title": ["PositionTitle", "JobTitle", "job_title", "Title", "DesiredJobTitle"],
        # Application Date variants
        "application_date": [
            "ApplicationDate",
            "application_date",
            "DateApplied",
            "SubmissionDate",
            "Date",
        ],
        # Status variants
        "status": ["Status", "status", "CandidateStatus", "ApplicationStatus", "StatusCode"],
        # Location variants
        "location": ["Location", "location", "City", "Municipality", "PostalAddress", "AddressLine"],
        # Cover Letter variants
        "cover_letter": [
            "CoverLetter",
            "cover_letter",
            "CoverLetterText",
            "Letter",
            "Comments",
        ],
        # LinkedIn URL variants
        "linkedin_url": [
            "LinkedInURL",
            "linkedin_url",
            "LinkedInProfile",
            "SocialMediaURL",
            "ProfileURL",
        ],
    }

    # Required fields for valid application import
    REQUIRED_FIELDS = ["email"]

    def __init__(self):
        """Initialize the HR-XML importer service."""
        logger.info("Initialized HRXMLImporter")

    def parse_xml_file(self, file_path: str, encoding: str = "utf-8") -> XMLParseResult:
        """
        Parse an HR-XML file from disk.

        Args:
            file_path: Path to the XML file
            encoding: File encoding (default: utf-8)

        Returns:
            XMLParseResult with parsed applications and metadata

        Raises:
            FileNotFoundError: If file does not exist
            PermissionError: If file cannot be read
        """
        try:
            logger.info(f"Parsing HR-XML file: {file_path}")

            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()

            return self.parse_xml_content(content)

        except FileNotFoundError as e:
            logger.error(f"XML file not found: {file_path}")
            raise FileNotFoundError(f"XML file not found: {file_path}") from e

        except PermissionError as e:
            logger.error(f"Permission denied reading XML file: {file_path}")
            raise PermissionError(f"Cannot read XML file: {file_path}") from e

        except Exception as e:
            logger.error(f"Error reading XML file: {e}", exc_info=True)
            return XMLParseResult(
                success=False,
                errors=[f"Failed to read XML file: {str(e)}"],
            )

    def parse_xml_content(self, content: str) -> XMLParseResult:
        """
        Parse HR-XML content from a string.

        Args:
            content: XML content as string

        Returns:
            XMLParseResult with parsed applications and metadata
        """
        try:
            logger.info("Parsing HR-XML content")

            # Parse XML content
            try:
                root = ET.fromstring(content)
            except ET.ParseError as e:
                logger.error(f"XML parse error: {e}")
                return XMLParseResult(
                    success=False,
                    errors=[f"Invalid XML format: {str(e)}"],
                )

            # Detect XML format
            detected_format = self._detect_xml_format(root)
            logger.info(f"Detected XML format: {detected_format}")

            # Find application/candidate elements
            application_elements = self._find_application_elements(root)

            if not application_elements:
                logger.warning("No application elements found in XML")
                return XMLParseResult(
                    success=True,
                    total_records=0,
                    valid_applications=0,
                    invalid_applications=0,
                    applications=[],
                    warnings=["No application elements found in XML"],
                    detected_format=detected_format,
                )

            # Parse each application
            applications = []
            errors = []
            warnings = []
            record_number = 0

            for element in application_elements:
                record_number += 1
                try:
                    application = self._parse_application_element(element)

                    # Validate required fields
                    validation_result = self._validate_application(application)
                    if validation_result["valid"]:
                        applications.append(application)
                    else:
                        errors.append(
                            f"Record {record_number}: {validation_result['error']}"
                        )
                        warnings.append(
                            f"Skipping record {record_number} due to validation errors"
                        )

                except Exception as e:
                    logger.warning(f"Error parsing record {record_number}: {e}")
                    errors.append(f"Record {record_number}: {str(e)}")

            total_records = record_number
            valid_applications = len(applications)
            invalid_applications = total_records - valid_applications

            logger.info(
                f"Parsed {total_records} records: {valid_applications} valid, "
                f"{invalid_applications} invalid"
            )

            return XMLParseResult(
                success=True,
                total_records=total_records,
                valid_applications=valid_applications,
                invalid_applications=invalid_applications,
                applications=applications,
                errors=errors,
                warnings=warnings,
                detected_format=detected_format,
            )

        except Exception as e:
            logger.error(f"Error parsing XML content: {e}", exc_info=True)
            return XMLParseResult(
                success=False,
                errors=[f"Failed to parse XML: {str(e)}"],
            )

    def _detect_xml_format(self, root: ET.Element) -> str:
        """
        Detect the type of HR-XML export based on root element and structure.

        Args:
            root: Root XML element

        Returns:
            String identifying the detected format type
        """
        root_tag = root.tag.lower()

        # Remove namespace prefix if present
        if "}" in root_tag:
            root_tag = root_tag.split("}")[-1]

        # Check root element name
        if "candidates" in root_tag:
            return "bulk_candidates_export"
        elif "candidate" in root_tag:
            return "single_candidate_export"
        elif "resumes" in root_tag:
            return "resume_export"
        elif "resume" in root_tag:
            return "single_resume_export"
        elif "hrxml" in root_tag or "hr-xml" in root_tag:
            # Check for child elements
            children = list(root)
            if children:
                first_child_tag = children[0].tag.lower()
                if "}" in first_child_tag:
                    first_child_tag = first_child_tag.split("}")[-1]
                if "candidate" in first_child_tag:
                    return "hrxml_candidate_export"
                elif "resume" in first_child_tag:
                    return "hrxml_resume_export"

        return "unknown_format"

    def _find_application_elements(self, root: ET.Element) -> List[ET.Element]:
        """
        Find all candidate/application elements in the XML tree.

        Args:
            root: Root XML element

        Returns:
            List of application XML elements
        """
        # Common element names for candidates/applications in HR-XML
        element_names = [
            "Candidate",
            "candidate",
            "Resume",
            "resume",
            "Application",
            "application",
            "Person",
            "person",
        ]

        elements = []

        # Check if root itself is a candidate element
        root_tag_clean = root.tag.split("}")[-1] if "}" in root.tag else root.tag
        if any(name.lower() in root_tag_clean.lower() for name in element_names):
            elements.append(root)
            return elements

        # Search for candidate elements
        for name in element_names:
            # Try direct children
            found = root.findall(name)
            if found:
                elements.extend(found)

            # Try with namespace (common in HR-XML exports)
            found = root.findall(f".//{name}")
            if found:
                elements.extend(found)

        # Remove duplicates while preserving order
        seen = set()
        unique_elements = []
        for elem in elements:
            elem_id = id(elem)
            if elem_id not in seen:
                seen.add(elem_id)
                unique_elements.append(elem)

        return unique_elements

    def _parse_application_element(self, element: ET.Element) -> HRXMLApplicationData:
        """
        Parse a single XML application element into HRXMLApplicationData.

        Args:
            element: XML element containing application data

        Returns:
            HRXMLApplicationData object with parsed data
        """
        application = HRXMLApplicationData()
        raw_data = {}

        # Extract all text content from element and its children
        for child in element.iter():
            tag = child.tag
            # Remove namespace prefix
            if "}" in tag:
                tag = tag.split("}")[-1]
            text = child.text

            if text and text.strip():
                raw_data[tag] = text.strip()

        application.raw_data = raw_data

        # Extract each field using the mapping
        for standard_field, xml_tags in self.ELEMENT_MAPPINGS.items():
            value = None

            # Try to find matching XML element
            for xml_tag in xml_tags:
                # Try direct child
                elem = element.find(xml_tag)
                if elem is not None and elem.text:
                    value = elem.text.strip()
                    break

                # Try with namespace wildcard
                elem = element.find(f".//*[local-name()='{xml_tag}']")
                if elem is not None and elem.text:
                    value = elem.text.strip()
                    break

                # Try in any descendant
                elem = element.find(f".//{xml_tag}")
                if elem is not None and elem.text:
                    value = elem.text.strip()
                    break

                # Try from raw_data
                if xml_tag in raw_data:
                    value = raw_data[xml_tag]
                    break

            if not value:
                continue

            # Set field value
            if standard_field == "candidate_id":
                application.candidate_id = value
            elif standard_field == "first_name":
                application.first_name = value
            elif standard_field == "last_name":
                application.last_name = value
            elif standard_field == "email":
                application.email = value
            elif standard_field == "phone":
                application.phone = value
            elif standard_field == "resume_url":
                application.resume_url = value
            elif standard_field == "resume_text":
                application.resume_text = value
            elif standard_field == "job_title":
                application.job_title = value
            elif standard_field == "application_date":
                application.application_date = value
            elif standard_field == "status":
                application.status = value
            elif standard_field == "location":
                application.location = value
            elif standard_field == "cover_letter":
                application.cover_letter = value
            elif standard_field == "linkedin_url":
                application.linkedin_url = value

        # If first_name and last_name not found, try to extract from a "Name" field
        if not application.first_name and not application.last_name:
            name_fields = ["Name", "name", "PersonName", "CandidateName", "FullName"]
            for name_field in name_fields:
                elem = element.find(name_field)
                if elem is not None and elem.text:
                    self._parse_full_name(application, elem.text.strip())
                    break
                elem = element.find(f".//*[local-name()='{name_field}']")
                if elem is not None and elem.text:
                    self._parse_full_name(application, elem.text.strip())
                    break
                elif name_field in raw_data:
                    self._parse_full_name(application, raw_data[name_field])
                    break

        return application

    def _parse_full_name(self, application: HRXMLApplicationData, full_name: str):
        """
        Parse a full name into first_name and last_name.

        Args:
            application: HRXMLApplicationData to update
            full_name: Full name string to parse
        """
        if not full_name:
            return

        parts = full_name.strip().split()
        if len(parts) >= 2:
            application.first_name = parts[0]
            application.last_name = " ".join(parts[1:])
        elif len(parts) == 1:
            application.first_name = parts[0]

    def _validate_application(self, application: HRXMLApplicationData) -> Dict[str, Any]:
        """
        Validate that an application has required fields.

        Args:
            application: HRXMLApplicationData to validate

        Returns:
            Dictionary with 'valid' boolean and optional 'error' message
        """
        missing_fields = []

        for required_field in self.REQUIRED_FIELDS:
            value = getattr(application, required_field, None)
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
        Get list of supported HR-XML formats.

        Returns:
            List of supported format names
        """
        return [
            "bulk_candidates_export",
            "single_candidate_export",
            "resume_export",
            "single_resume_export",
            "hrxml_candidate_export",
            "hrxml_resume_export",
        ]

    def validate_xml_structure(self, root: ET.Element) -> Dict[str, Any]:
        """
        Validate that XML structure contains minimum required elements.

        Args:
            root: Root XML element

        Returns:
            Dictionary with validation results
        """
        # Find candidate elements
        application_elements = self._find_application_elements(root)

        if not application_elements:
            return {
                "valid": False,
                "error": "No candidate/application elements found in XML",
                "detected_format": self._detect_xml_format(root),
            }

        # Check first application for required fields
        if application_elements:
            first_app = self._parse_application_element(application_elements[0])
            validation_result = self._validate_application(first_app)

            if not validation_result["valid"]:
                return {
                    "valid": False,
                    "error": f"First candidate failed validation: {validation_result['error']}",
                    "detected_format": self._detect_xml_format(root),
                }

        return {
            "valid": True,
            "detected_format": self._detect_xml_format(root),
            "application_count": len(application_elements),
        }
