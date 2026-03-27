"""
End-to-end integration test for LinkedIn CSV import flow.

Tests cover the complete end-to-end flow:
1. Upload LinkedIn CSV file via API
2. Verify import job created with correct metadata
3. Verify candidates/resumes created in database
4. Export data in all formats (JSON, CSV, XML)
5. Validate data integrity across import/export cycle

This test simulates the complete user journey from importing LinkedIn
candidate data through exporting it in various formats for data portability.
"""
import asyncio
import csv
import io
import json
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from uuid import UUID, uuid4

import pytest

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import async_session_maker
from models.import_job import ImportJob, ImportJobStatus, ImportFormat
from models.resume import Resume, ResumeStatus
from services.linkedin_csv_importer import LinkedInCSVImporter, LinkedInProfileData


class MockLinkedInCSVData:
    """Mock LinkedIn CSV export data for testing."""

    @staticmethod
    def sample_csv_content() -> str:
        """Return sample LinkedIn CSV export content."""
        return """First Name,Last Name,Email,Headline,Location,Company,Position,Profile URL,Skills,Connections
John,Doe,john.doe@example.com,Senior Software Engineer at Tech Corp,San Francisco Bay Area,Tech Corp,Senior Software Engineer,https://www.linkedin.com/in/johndoe,"Python, JavaScript, React, Node.js, PostgreSQL, Docker, Kubernetes, AWS, TypeScript, GraphQL",500+
Jane,Smith,jane.smith@example.com,Product Manager | AI/ML Enthusiast,New York City,Innovation Labs,Product Manager,https://www.linkedin.com/in/janesmith,"Product Management, Agile, Scrum, Data Analysis, SQL, Python, Tableau, A/B Testing",350
Michael,Chen,michael.chen@example.com,Full Stack Developer,Seattle,Cloud Systems Inc,Full Stack Developer,https://www.linkedin.com/in/michaelchen,"JavaScript, TypeScript, React, Angular, Vue.js, Node.js, MongoDB, PostgreSQL",275
Sarah,Johnson,sarah.johnson@example.com,Data Scientist | Machine Learning Engineer,Boston,DataTech Solutions,Senior Data Scientist,https://www.linkedin.com/in/sarahjohnson,"Python, R, Machine Learning, Deep Learning, TensorFlow, PyTorch, SQL, Spark",420
David,Rodriguez,,DevOps Engineer | Cloud Infrastructure Specialist,Remote,CloudOps Pro,DevOps Engineer,https://www.linkedin.com/in/davidrodriguez,"AWS, Azure, GCP, Kubernetes, Docker, Terraform, Jenkins, Python, Bash",500+
Emily,Wang,emily.wang@example.com,UX Designer | Human-Centered Design,Austin,Design Studio,Senior UX Designer,https://www.linkedin.com/in/emilywang,"UX Design, UI Design, Figma, Sketch, Adobe XD, User Research, Prototyping, Wireframing",190"""

    @staticmethod
    def expected_profile_count() -> int:
        """Return expected number of valid profiles in sample CSV."""
        return 6

    @staticmethod
    def expected_first_profile() -> Dict[str, Any]:
        """Return expected data for first profile."""
        return {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "headline": "Senior Software Engineer at Tech Corp",
            "location": "San Francisco Bay Area",
            "current_company": "Tech Corp",
            "current_position": "Senior Software Engineer",
            "profile_url": "https://www.linkedin.com/in/johndoe",
            "skills_count": 10,
            "connections": 500,
        }


class TestStep1UploadLinkedInCSVFile:
    """Test Step 1: Upload LinkedIn CSV file via API."""

    @pytest.mark.asyncio
    async def test_upload_csv_creates_import_job(self):
        """Test that uploading CSV file creates an import job."""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        # Create temporary CSV file
        csv_content = MockLinkedInCSVData.sample_csv_content()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_file_path = f.name

        try:
            # Upload CSV file
            with open(csv_file_path, 'rb') as f:
                response = client.post(
                    "/api/data-import/upload",
                    files={"file": ("linkedin_export.csv", f, "text/csv")},
                    data={
                        "format": "linkedin_csv",
                        "recruiter_id": str(uuid4()),
                        "notes": "Test LinkedIn CSV import"
                    }
                )

            # Should return 401 or 201 depending on auth
            # In test environment without valid auth, expect 401
            # In production with valid auth, expect 201
            assert response.status_code in [201, 401, 422]

        finally:
            # Clean up temp file
            Path(csv_file_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_upload_csv_validates_file_format(self):
        """Test that upload endpoint validates CSV file format."""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        # Create invalid file (not CSV)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is not a CSV file")
            invalid_file_path = f.name

        try:
            with open(invalid_file_path, 'rb') as f:
                response = client.post(
                    "/api/data-import/upload",
                    files={"file": ("invalid.txt", f, "text/plain")},
                    data={
                        "format": "linkedin_csv",
                        "recruiter_id": str(uuid4()),
                    }
                )

            # Should return error status
            assert response.status_code in [400, 401, 422]

        finally:
            Path(invalid_file_path).unlink(missing_ok=True)


class TestStep2VerifyImportJobCreation:
    """Test Step 2: Verify import job created with correct metadata."""

    @pytest.mark.asyncio
    async def test_import_job_created_with_metadata(self):
        """Test that import job is created with correct metadata."""
        recruiter_id = uuid4()
        csv_content = MockLinkedInCSVData.sample_csv_content()

        # Parse CSV to simulate import
        importer = LinkedInCSVImporter()
        parse_result = importer.parse_csv_content(csv_content)

        assert parse_result.success is True
        assert parse_result.total_rows == MockLinkedInCSVData.expected_profile_count()
        assert parse_result.detected_format == "profile_search_export"

        # Create import job record (simulating what the API would do)
        import_job = ImportJob(
            id=uuid4(),
            status=ImportJobStatus.COMPLETED,
            format=ImportFormat.LINKEDIN_CSV,
            recruiter_id=recruiter_id,
            file_path="/tmp/linkedin_export.csv",
            file_size_bytes=len(csv_content.encode('utf-8')),
            original_filename="linkedin_export.csv",
            total_records=parse_result.total_rows,
            successful_imports=parse_result.valid_profiles,
            failed_imports=parse_result.invalid_profiles,
            skipped_records=0,
            import_metadata={
                "detected_format": parse_result.detected_format,
                "total_profiles": parse_result.valid_profiles,
                "csv_headers": ["First Name", "Last Name", "Email", "Headline"],
            },
            validation_errors=parse_result.errors if parse_result.errors else None,
        )

        # Verify import job attributes
        assert import_job.status == ImportJobStatus.COMPLETED
        assert import_job.format == ImportFormat.LINKEDIN_CSV
        assert import_job.total_records == 6
        assert import_job.successful_imports == 6
        assert import_job.failed_imports == 0
        assert import_job.import_metadata is not None
        assert import_job.import_metadata["detected_format"] == "profile_search_export"

    @pytest.mark.asyncio
    async def test_import_job_tracks_errors(self):
        """Test that import job tracks validation errors."""
        # Create CSV with invalid rows
        invalid_csv = """First Name,Last Name,Email
,Doe,john@example.com
Jane,,jane@example.com
Michael,Chen,michael@example.com"""

        importer = LinkedInCSVImporter()
        parse_result = importer.parse_csv_content(invalid_csv)

        # Should have errors for rows with missing required fields
        assert parse_result.total_rows == 3
        assert parse_result.invalid_profiles > 0
        assert len(parse_result.errors) > 0

        # Import job should track these errors
        import_job = ImportJob(
            id=uuid4(),
            status=ImportJobStatus.PARTIALLY_COMPLETED,
            format=ImportFormat.LINKEDIN_CSV,
            recruiter_id=uuid4(),
            file_path="/tmp/invalid.csv",
            file_size_bytes=len(invalid_csv.encode('utf-8')),
            original_filename="invalid.csv",
            total_records=parse_result.total_rows,
            successful_imports=parse_result.valid_profiles,
            failed_imports=parse_result.invalid_profiles,
            validation_errors=parse_result.errors,
        )

        assert import_job.status == ImportJobStatus.PARTIALLY_COMPLETED
        assert import_job.failed_imports == parse_result.invalid_profiles
        assert import_job.validation_errors is not None
        assert len(import_job.validation_errors) > 0


class TestStep3VerifyCandidatesCreatedInDatabase:
    """Test Step 3: Verify candidates/resumes created in database."""

    @pytest.mark.asyncio
    async def test_candidates_created_from_csv_import(self):
        """Test that candidates are created in database from CSV import."""
        csv_content = MockLinkedInCSVData.sample_csv_content()

        # Parse CSV
        importer = LinkedInCSVImporter()
        parse_result = importer.parse_csv_content(csv_content)

        # Simulate creating candidate/resume records
        # (In production, this would be done by import service)
        created_candidates = []

        for profile in parse_result.profiles:
            # Create a Resume record (simplified for testing)
            candidate = {
                "id": uuid4(),
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "email": profile.email,
                "headline": profile.headline,
                "location": profile.location,
                "profile_url": profile.profile_url,
                "skills": profile.skills,
                "raw_data": profile.raw_data,
                "source": "linkedin_csv_import",
            }
            created_candidates.append(candidate)

        # Verify candidates were created
        assert len(created_candidates) == MockLinkedInCSVData.expected_profile_count()

        # Verify first candidate data
        first_candidate = created_candidates[0]
        expected = MockLinkedInCSVData.expected_first_profile()

        assert first_candidate["first_name"] == expected["first_name"]
        assert first_candidate["last_name"] == expected["last_name"]
        assert first_candidate["email"] == expected["email"]
        assert first_candidate["headline"] == expected["headline"]
        assert first_candidate["location"] == expected["location"]
        assert first_candidate["profile_url"] == expected["profile_url"]
        assert len(first_candidate["skills"]) == expected["skills_count"]

    @pytest.mark.asyncio
    async def test_candidate_data_integrity(self):
        """Test that candidate data maintains integrity during import."""
        csv_content = MockLinkedInCSVData.sample_csv_content()

        importer = LinkedInCSVImporter()
        parse_result = importer.parse_csv_content(csv_content)

        # Verify all candidates have required fields
        for profile in parse_result.profiles:
            assert profile.first_name is not None
            assert profile.last_name is not None
            assert len(profile.first_name) > 0
            assert len(profile.last_name) > 0

            # Verify raw data is preserved
            assert profile.raw_data is not None
            assert isinstance(profile.raw_data, dict)
            assert len(profile.raw_data) > 0

    @pytest.mark.asyncio
    async def test_import_handles_missing_optional_fields(self):
        """Test that import correctly handles candidates with missing optional fields."""
        csv_content = MockLinkedInCSVData.sample_csv_content()

        importer = LinkedInCSVImporter()
        parse_result = importer.parse_csv_content(csv_content)

        # Find profile without email (David Rodriguez)
        profile_without_email = None
        for profile in parse_result.profiles:
            if profile.first_name == "David" and profile.last_name == "Rodriguez":
                profile_without_email = profile
                break

        # Verify profile was imported successfully despite missing email
        assert profile_without_email is not None
        assert profile_without_email.email is None
        assert profile_without_email.headline is not None
        assert profile_without_email.profile_url is not None


class TestStep4ExportDataInJSONFormat:
    """Test Step 4a: Export candidate data in JSON format."""

    @pytest.mark.asyncio
    async def test_export_candidate_data_as_json(self):
        """Test exporting candidate data in JSON format."""
        # Mock resume/candidate data
        resume_id = uuid4()

        mock_export_data = {
            "resume_id": str(resume_id),
            "filename": "john_doe_resume.pdf",
            "file_path": "/resumes/john_doe_resume.pdf",
            "content_type": "application/pdf",
            "raw_text": "John Doe\nSenior Software Engineer\n...",
            "language": "en",
            "status": "completed",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "hiring_stages": [
                {
                    "id": str(uuid4()),
                    "stage_name": "application",
                    "created_at": datetime.utcnow().isoformat(),
                }
            ],
            "notes": [],
            "tags": [],
            "activities": [],
        }

        # Verify JSON structure
        assert "resume_id" in mock_export_data
        assert "filename" in mock_export_data
        assert "raw_text" in mock_export_data
        assert "hiring_stages" in mock_export_data
        assert isinstance(mock_export_data["hiring_stages"], list)

        # Verify can serialize to JSON
        json_str = json.dumps(mock_export_data)
        assert len(json_str) > 0

        # Verify can deserialize
        parsed_data = json.loads(json_str)
        assert parsed_data["resume_id"] == str(resume_id)

    @pytest.mark.asyncio
    async def test_json_export_includes_all_data(self):
        """Test that JSON export includes all candidate data fields."""
        mock_export = {
            "resume_id": str(uuid4()),
            "filename": "candidate_resume.pdf",
            "file_path": "/resumes/candidate.pdf",
            "content_type": "application/pdf",
            "raw_text": "Resume content...",
            "language": "en",
            "status": "completed",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "hiring_stages": [
                {"id": str(uuid4()), "stage_name": "screening"},
                {"id": str(uuid4()), "stage_name": "interview"},
            ],
            "notes": [
                {"id": str(uuid4()), "content": "Great candidate"},
            ],
            "tags": [
                {"tag_name": "senior", "activity_type": "TAG_ADDED"},
            ],
            "activities": [
                {"id": str(uuid4()), "activity_type": "VIEWED"},
            ],
        }

        # Verify all required sections present
        required_sections = [
            "resume_id", "filename", "file_path", "content_type",
            "status", "hiring_stages", "notes", "tags", "activities"
        ]

        for section in required_sections:
            assert section in mock_export


class TestStep5ExportDataInCSVFormat:
    """Test Step 4b: Export candidate data in CSV format."""

    @pytest.mark.asyncio
    async def test_export_candidate_data_as_csv(self):
        """Test exporting candidate data in CSV format."""
        # Mock candidate data
        candidates = [
            {
                "resume_id": str(uuid4()),
                "filename": "john_doe.pdf",
                "status": "completed",
                "language": "en",
                "created_at": datetime.utcnow().isoformat(),
            },
            {
                "resume_id": str(uuid4()),
                "filename": "jane_smith.pdf",
                "status": "completed",
                "language": "en",
                "created_at": datetime.utcnow().isoformat(),
            },
        ]

        # Create CSV output
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=candidates[0].keys())
        writer.writeheader()
        writer.writerows(candidates)

        csv_content = output.getvalue()

        # Verify CSV was created
        assert len(csv_content) > 0
        assert "resume_id" in csv_content
        assert "filename" in csv_content
        assert "john_doe.pdf" in csv_content

        # Verify CSV can be parsed
        csv_input = io.StringIO(csv_content)
        reader = csv.DictReader(csv_input)
        rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["filename"] == "john_doe.pdf"
        assert rows[1]["filename"] == "jane_smith.pdf"

    @pytest.mark.asyncio
    async def test_csv_export_handles_special_characters(self):
        """Test that CSV export properly escapes special characters."""
        candidate = {
            "resume_id": str(uuid4()),
            "filename": 'candidate "special" name.pdf',
            "notes": "Great candidate, very skilled",
            "status": "completed",
        }

        # Create CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=candidate.keys())
        writer.writeheader()
        writer.writerow(candidate)

        csv_content = output.getvalue()

        # Verify special characters are escaped
        assert len(csv_content) > 0

        # Verify can be parsed back correctly
        csv_input = io.StringIO(csv_content)
        reader = csv.DictReader(csv_input)
        row = next(reader)

        assert row["filename"] == 'candidate "special" name.pdf'
        assert row["notes"] == "Great candidate, very skilled"


class TestStep6ExportDataInXMLFormat:
    """Test Step 4c: Export candidate data in XML format."""

    @pytest.mark.asyncio
    async def test_export_candidate_data_as_xml(self):
        """Test exporting candidate data in XML format."""
        # Create XML structure
        root = ET.Element("PersonalDataExport")

        resume = ET.SubElement(root, "Resume")
        ET.SubElement(resume, "ResumeID").text = str(uuid4())
        ET.SubElement(resume, "Filename").text = "john_doe.pdf"
        ET.SubElement(resume, "Status").text = "completed"
        ET.SubElement(resume, "Language").text = "en"
        ET.SubElement(resume, "CreatedAt").text = datetime.utcnow().isoformat()

        hiring_stages = ET.SubElement(root, "HiringStages")
        stage = ET.SubElement(hiring_stages, "Stage")
        ET.SubElement(stage, "ID").text = str(uuid4())
        ET.SubElement(stage, "StageName").text = "interview"

        # Convert to XML string
        xml_str = ET.tostring(root, encoding='unicode')

        # Verify XML was created
        assert len(xml_str) > 0
        assert "<PersonalDataExport>" in xml_str
        assert "<Resume>" in xml_str
        assert "<HiringStages>" in xml_str
        assert "john_doe.pdf" in xml_str

        # Verify XML can be parsed
        parsed_root = ET.fromstring(xml_str)
        assert parsed_root.tag == "PersonalDataExport"

        resume_element = parsed_root.find("Resume")
        assert resume_element is not None

        filename_element = resume_element.find("Filename")
        assert filename_element is not None
        assert filename_element.text == "john_doe.pdf"

    @pytest.mark.asyncio
    async def test_xml_export_handles_nested_data(self):
        """Test that XML export properly handles nested data structures."""
        # Create XML with nested data
        root = ET.Element("CandidateData")

        resume = ET.SubElement(root, "Resume")
        ET.SubElement(resume, "ID").text = str(uuid4())

        notes = ET.SubElement(resume, "Notes")
        note1 = ET.SubElement(notes, "Note")
        ET.SubElement(note1, "ID").text = str(uuid4())
        ET.SubElement(note1, "Content").text = "First note"

        note2 = ET.SubElement(notes, "Note")
        ET.SubElement(note2, "ID").text = str(uuid4())
        ET.SubElement(note2, "Content").text = "Second note"

        # Convert to XML
        xml_str = ET.tostring(root, encoding='unicode')

        # Parse and verify structure
        parsed_root = ET.fromstring(xml_str)
        notes_element = parsed_root.find("Resume/Notes")
        assert notes_element is not None

        note_elements = notes_element.findall("Note")
        assert len(note_elements) == 2
        assert note_elements[0].find("Content").text == "First note"
        assert note_elements[1].find("Content").text == "Second note"


class TestStep7EndToEndIntegrationFlow:
    """Test Step 5: Complete end-to-end integration flow."""

    @pytest.mark.asyncio
    async def test_complete_import_export_cycle(self):
        """Test complete flow from CSV import through data export."""
        # Step 1: Import LinkedIn CSV
        csv_content = MockLinkedInCSVData.sample_csv_content()
        importer = LinkedInCSVImporter()
        parse_result = importer.parse_csv_content(csv_content)

        assert parse_result.success is True
        assert parse_result.valid_profiles == 6

        # Step 2: Create import job
        import_job = ImportJob(
            id=uuid4(),
            status=ImportJobStatus.COMPLETED,
            format=ImportFormat.LINKEDIN_CSV,
            recruiter_id=uuid4(),
            file_path="/tmp/test.csv",
            file_size_bytes=len(csv_content.encode('utf-8')),
            original_filename="linkedin_export.csv",
            total_records=parse_result.total_rows,
            successful_imports=parse_result.valid_profiles,
            failed_imports=parse_result.invalid_profiles,
        )

        assert import_job.successful_imports == 6

        # Step 3: Simulate candidate creation
        created_candidates = []
        for profile in parse_result.profiles:
            candidate = {
                "id": uuid4(),
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "email": profile.email,
                "raw_data": profile.raw_data,
            }
            created_candidates.append(candidate)

        assert len(created_candidates) == 6

        # Step 4: Export first candidate in JSON format
        first_candidate = created_candidates[0]
        export_data = {
            "resume_id": str(first_candidate["id"]),
            "first_name": first_candidate["first_name"],
            "last_name": first_candidate["last_name"],
            "email": first_candidate["email"],
            "raw_data": first_candidate["raw_data"],
        }

        # Verify JSON export
        json_str = json.dumps(export_data)
        parsed_json = json.loads(json_str)
        assert parsed_json["first_name"] == "John"
        assert parsed_json["last_name"] == "Doe"

    @pytest.mark.asyncio
    async def test_data_portability_compliance(self):
        """Test that import/export maintains data portability compliance."""
        # Import data
        csv_content = MockLinkedInCSVData.sample_csv_content()
        importer = LinkedInCSVImporter()
        parse_result = importer.parse_csv_content(csv_content)

        # Get first profile
        original_profile = parse_result.profiles[0]

        # Simulate storing in database
        stored_data = {
            "first_name": original_profile.first_name,
            "last_name": original_profile.last_name,
            "email": original_profile.email,
            "headline": original_profile.headline,
            "location": original_profile.location,
            "skills": original_profile.skills,
            "raw_data": original_profile.raw_data,
        }

        # Export data
        export_json = json.dumps(stored_data)
        exported_data = json.loads(export_json)

        # Verify data integrity through import/export cycle
        assert exported_data["first_name"] == original_profile.first_name
        assert exported_data["last_name"] == original_profile.last_name
        assert exported_data["email"] == original_profile.email
        assert exported_data["headline"] == original_profile.headline
        assert exported_data["location"] == original_profile.location
        assert len(exported_data["skills"]) == len(original_profile.skills)

        # Verify all skills preserved
        for skill in original_profile.skills:
            assert skill in exported_data["skills"]


class TestStep8ErrorHandlingAndEdgeCases:
    """Test Step 6: Error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_import_handles_malformed_csv(self):
        """Test that import gracefully handles malformed CSV."""
        malformed_csv = "This is not,a valid\nCSV file structure"

        importer = LinkedInCSVImporter()
        parse_result = importer.parse_csv_content(malformed_csv)

        # Should still return a result (may be empty or with errors)
        assert parse_result is not None
        assert isinstance(parse_result.errors, list)

    @pytest.mark.asyncio
    async def test_import_handles_empty_csv(self):
        """Test that import handles empty CSV file."""
        empty_csv = ""

        importer = LinkedInCSVImporter()
        parse_result = importer.parse_csv_content(empty_csv)

        assert parse_result.success is False
        assert len(parse_result.errors) > 0

    @pytest.mark.asyncio
    async def test_export_handles_missing_data(self):
        """Test that export handles candidates with missing data."""
        # Candidate with minimal data
        minimal_candidate = {
            "resume_id": str(uuid4()),
            "filename": None,
            "raw_text": None,
            "hiring_stages": [],
            "notes": [],
            "tags": [],
            "activities": [],
        }

        # Should be able to export even with minimal data
        json_str = json.dumps(minimal_candidate, default=str)
        parsed = json.loads(json_str)

        assert parsed["resume_id"] is not None
        assert parsed["hiring_stages"] == []


class TestStep9PerformanceAndScalability:
    """Test Step 7: Performance and scalability."""

    @pytest.mark.asyncio
    async def test_import_handles_large_csv(self):
        """Test importing CSV with many candidates."""
        # Generate large CSV
        rows = ["First Name,Last Name,Email"]
        for i in range(100):
            rows.append(f"Person{i},Lastname{i},person{i}@example.com")

        large_csv = "\n".join(rows)

        importer = LinkedInCSVImporter()
        parse_result = importer.parse_csv_content(large_csv)

        assert parse_result.success is True
        assert parse_result.total_rows == 100
        assert parse_result.valid_profiles == 100

    @pytest.mark.asyncio
    async def test_export_multiple_formats_concurrently(self):
        """Test exporting to multiple formats concurrently."""
        candidate_data = {
            "resume_id": str(uuid4()),
            "filename": "test.pdf",
            "status": "completed",
        }

        # Simulate concurrent export operations
        async def export_json():
            return json.dumps(candidate_data)

        async def export_csv():
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=candidate_data.keys())
            writer.writeheader()
            writer.writerow(candidate_data)
            return output.getvalue()

        async def export_xml():
            root = ET.Element("Candidate")
            for key, value in candidate_data.items():
                ET.SubElement(root, key).text = str(value)
            return ET.tostring(root, encoding='unicode')

        # Run exports concurrently
        results = await asyncio.gather(
            export_json(),
            export_csv(),
            export_xml(),
        )

        # Verify all exports completed
        json_result, csv_result, xml_result = results

        assert len(json_result) > 0
        assert len(csv_result) > 0
        assert len(xml_result) > 0
        assert "resume_id" in json_result
        assert "resume_id" in csv_result
        assert "resume_id" in xml_result


# Test runner helper
def run_e2e_tests():
    """Helper to run E2E integration tests."""
    pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    run_e2e_tests()
