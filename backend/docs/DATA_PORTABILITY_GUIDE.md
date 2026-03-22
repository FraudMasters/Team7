# Data Portability Guide

**Version:** 1.0
**Last Updated:** 2026-03-22
**Purpose:** Comprehensive guide for importing and exporting candidate data across multiple formats

---

## Table of Contents

1. [Overview](#overview)
2. [Export Functionality](#export-functionality)
3. [Import Functionality](#import-functionality)
4. [Supported Formats](#supported-formats)
5. [API Reference](#api-reference)
6. [Security & Privacy](#security--privacy)
7. [Duplicate Detection](#duplicate-detection)
8. [Error Handling](#error-handling)
9. [Troubleshooting](#troubleshooting)
10. [Examples](#examples)

---

## Overview

### What is Data Portability?

Data portability is a GDPR-mandated right (Article 20) that allows individuals to:
- **Receive their personal data** in a structured, commonly used, machine-readable format
- **Transfer their data** to another service provider without hindrance

The AgentHR Data Portability Suite provides:
- **Export Tools:** Export candidate data in JSON, CSV, or XML formats
- **Import Tools:** Import candidates from LinkedIn CSV, Indeed XML, HR-XML, and major ATS platforms
- **Migration Assistant:** Seamless migration from Greenhouse, Lever, Workable, and other ATS systems
- **Automated Backups:** Scheduled exports to S3-compatible storage

---

### Key Benefits

**For Candidates:**
- ✅ Own your data regardless of platform choice
- ✅ Transfer data between platforms without re-entering information
- ✅ Comply with GDPR Article 20 (Right to Data Portability)

**For Organizations:**
- ✅ Avoid vendor lock-in
- ✅ Reduce switching costs when migrating from other ATS platforms
- ✅ Maintain historical candidate data during migrations
- ✅ Backup critical recruitment data regularly

---

## Export Functionality

### Supported Export Formats

AgentHR supports three standard export formats:

1. **JSON** - Structured data with full hierarchy preservation
2. **CSV** - Tabular data for spreadsheet applications
3. **XML** - Hierarchical data for enterprise integrations

---

### Export Data Coverage

Each export includes:

#### Resume Data
- Resume ID, filename, content type
- Upload status and processing state
- Raw text content
- Language detection
- Created/updated timestamps

#### Parsed Resume Data
- Contact information (name, email, phone, location)
- Skills and expertise
- Work experience history
- Education background
- Languages
- Social/professional links

#### Hiring Pipeline Data
- Hiring stage history
- Vacancy associations
- Stage notes and feedback
- Timeline of stage transitions

#### Candidate Activities
- Activity type (email, call, interview, etc.)
- Activity descriptions
- Activity timestamps

#### Candidate Notes
- Note content
- Note author
- Created/updated timestamps

#### Tags & Labels
- Tag names and colors
- Tag creation dates

#### Consent Records
- Consent type and status
- Grant/withdrawal timestamps
- Consent version tracking
- IP address and user agent

#### Candidate Feedback
- Language and tone analysis
- Match scores
- Grammar feedback
- Skills assessment
- Experience evaluation
- Recommendations
- View/download status

#### Work Experience
- Company and job title
- Start/end dates
- Job descriptions

#### Resume Analysis
- Language detection
- Skills extraction
- Keyword analysis
- Entity recognition
- Total experience calculation
- Education parsing
- Contact info extraction
- Grammar quality assessment
- Quality scoring
- Processing metrics

---

### How to Export Data

#### Via API

**Export as JSON:**
```bash
curl -X POST http://localhost:8000/api/export/resume/{resume_id} \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "json",
    "include_analytics": false
  }'
```

**Export as CSV:**
```bash
curl -X POST http://localhost:8000/api/export/resume/{resume_id} \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "csv",
    "include_analytics": false
  }'
```

**Export as XML:**
```bash
curl -X POST http://localhost:8000/api/export/resume/{resume_id} \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "xml",
    "include_analytics": false
  }'
```

**Response Structure:**
```json
{
  "format": "json",
  "data": {
    "resume": {...},
    "parsed_resume": {...},
    "hiring_stages": [...],
    "activities": [...],
    "notes": [...],
    "tags": [...],
    "consent_records": [...],
    "feedback": [...],
    "work_experience": [...],
    "resume_analyses": [...]
  },
  "metadata": {
    "export_timestamp": "2026-03-22T10:30:00Z",
    "resume_id": "123e4567-e89b-12d3-a456-426614174000",
    "filename": "john_doe_resume.pdf",
    "format": "json",
    "total_records": 45,
    "includes_analytics": false
  }
}
```

---

#### Via Python Service

```python
from services.export_service import get_export_service
from database import get_db
from uuid import UUID

# Get database session
async with get_db() as db:
    # Initialize export service
    export_service = get_export_service(db)

    # Export as JSON
    result = await export_service.export_candidate_data(
        resume_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
        export_format="json",
        include_analytics=False
    )

    # Access exported data
    print(f"Format: {result['format']}")
    print(f"Total records: {result['metadata']['total_records']}")
    print(f"Data: {result['data']}")
```

---

### Export Format Specifications

#### JSON Format

**Structure:**
- Preserves full data hierarchy
- Nested objects for related data
- ISO 8601 timestamps
- UTF-8 encoding

**Example:**
```json
{
  "resume": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "filename": "john_doe_resume.pdf",
    "status": "parsed",
    "created_at": "2026-03-15T10:00:00Z"
  },
  "parsed_resume": {
    "email": "john.doe@example.com",
    "phone": "+1-555-0100",
    "name": "John Doe",
    "skills": ["Python", "React", "PostgreSQL"]
  },
  "hiring_stages": [
    {
      "stage_name": "Applied",
      "created_at": "2026-03-15T10:05:00Z"
    }
  ]
}
```

---

#### CSV Format

**Structure:**
- Flattened records with `record_type` column
- One record per row
- Header row with column names
- Nested objects serialized as JSON strings

**Example:**
```csv
record_type,id,filename,email,name,created_at
main,123e4567...,john_doe_resume.pdf,john.doe@example.com,John Doe,2026-03-15T10:00:00Z
hiring_stage,456e7890...,,,Applied,2026-03-15T10:05:00Z
activity,789e0123...,,,Email sent,2026-03-16T14:20:00Z
```

---

#### XML Format

**Structure:**
- Hierarchical XML elements
- Root element: `<candidate_export>`
- Child elements for each data category
- UTF-8 encoding with XML declaration

**Example:**
```xml
<?xml version='1.0' encoding='utf-8'?>
<candidate_export>
  <resume>
    <id>123e4567-e89b-12d3-a456-426614174000</id>
    <filename>john_doe_resume.pdf</filename>
    <status>parsed</status>
    <created_at>2026-03-15T10:00:00Z</created_at>
  </resume>
  <parsed_resume>
    <email>john.doe@example.com</email>
    <phone>+1-555-0100</phone>
    <name>John Doe</name>
  </parsed_resume>
  <hiring_stages>
    <hiring_stage>
      <stage_name>Applied</stage_name>
      <created_at>2026-03-15T10:05:00Z</created_at>
    </hiring_stage>
  </hiring_stages>
</candidate_export>
```

---

## Import Functionality

### Supported Import Sources

AgentHR supports importing candidate data from:

1. **LinkedIn Recruiter CSV** - Export from LinkedIn Talent Solutions
2. **Indeed XML** - Indeed ATS integration format
3. **HR-XML** - Industry standard HR data exchange format
4. **Greenhouse** - Greenhouse ATS export
5. **Lever** - Lever ATS export
6. **Workable** - Workable ATS export
7. **Custom JSON** - AgentHR JSON export format
8. **Custom CSV** - Custom CSV with field mapping

---

### Import Process Overview

```
┌─────────────────────┐
│ Upload Import File  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Create Import Job   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Validate File       │
│ Format & Structure  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Parse Records       │
│ Extract Candidates  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Duplicate Detection │
│ (Email, External ID)│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Import Candidates   │
│ Create Resume       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Update Import Job   │
│ Status & Stats      │
└─────────────────────┘
```

---

### Import Job Lifecycle

**Import Job States:**

1. **PENDING** - Import job created, awaiting processing
2. **IN_PROGRESS** - File is being processed
3. **COMPLETED** - All records successfully imported
4. **PARTIALLY_COMPLETED** - Some records imported, some failed
5. **FAILED** - Import failed due to error
6. **CANCELLED** - Import cancelled by user

---

### Creating an Import Job

#### Step 1: Upload Import File

```bash
# Upload file to server
curl -X POST http://localhost:8000/api/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@linkedin_export.csv" \
  -F "type=import"
```

**Response:**
```json
{
  "file_id": "upload_123",
  "filename": "linkedin_export.csv",
  "file_path": "/uploads/imports/linkedin_export.csv",
  "file_size": 1048576,
  "status": "uploaded"
}
```

---

#### Step 2: Create Import Job

```bash
curl -X POST http://localhost:8000/api/import/jobs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "linkedin_csv",
    "original_filename": "linkedin_export.csv",
    "file_size_bytes": 1048576,
    "vacancy_id": "vacancy-uuid-here",
    "source_system": "LinkedIn Recruiter",
    "notes": "Q1 2026 sourcing campaign"
  }'
```

**Response:**
```json
{
  "id": "import-job-uuid",
  "status": "pending",
  "format": "linkedin_csv",
  "recruiter_id": "recruiter-uuid",
  "vacancy_id": "vacancy-uuid",
  "file_path": "/uploads/imports/linkedin_export.csv",
  "file_size_bytes": 1048576,
  "original_filename": "linkedin_export.csv",
  "total_records": null,
  "successful_imports": 0,
  "failed_imports": 0,
  "skipped_records": 0,
  "created_at": "2026-03-22T10:00:00Z"
}
```

---

#### Step 3: Start Import Processing

```bash
curl -X POST http://localhost:8000/api/import/jobs/{job_id}/start \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "async_processing": true
  }'
```

**Response:**
```json
{
  "job_id": "import-job-uuid",
  "status": "in_progress",
  "message": "Import job started successfully",
  "task_id": "celery-task-id"
}
```

---

#### Step 4: Monitor Import Progress

```bash
curl -X GET http://localhost:8000/api/import/jobs/{job_id} \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "id": "import-job-uuid",
  "status": "in_progress",
  "format": "linkedin_csv",
  "total_records": 100,
  "successful_imports": 75,
  "failed_imports": 5,
  "skipped_records": 20,
  "progress_percentage": 75.0,
  "error_message": null,
  "validation_errors": [
    {
      "row_number": 23,
      "field": "email",
      "error": "Invalid email format",
      "value": "invalid-email"
    }
  ]
}
```

---

### Import Field Mapping

Each import format has a specific field mapping configuration:

#### LinkedIn CSV Mapping

```json
{
  "format": "linkedin_csv",
  "field_mappings": [
    {"source_field": "First Name", "target_field": "first_name", "required": true},
    {"source_field": "Last Name", "target_field": "last_name", "required": true},
    {"source_field": "Email Address", "target_field": "email", "required": true},
    {"source_field": "Phone", "target_field": "phone", "required": false},
    {"source_field": "Current Company", "target_field": "current_company", "required": false},
    {"source_field": "Current Title", "target_field": "current_title", "required": false},
    {"source_field": "Location", "target_field": "location", "required": false},
    {"source_field": "LinkedIn URL", "target_field": "linkedin_url", "required": false},
    {"source_field": "Skills", "target_field": "skills", "required": false, "transform": "split_comma"}
  ]
}
```

---

#### Indeed XML Mapping

```json
{
  "format": "indeed_xml",
  "field_mappings": [
    {"source_field": "applicant/name", "target_field": "name", "required": true},
    {"source_field": "applicant/email", "target_field": "email", "required": true},
    {"source_field": "applicant/phone", "target_field": "phone", "required": false},
    {"source_field": "applicant/resume", "target_field": "resume_text", "required": true},
    {"source_field": "application/job_id", "target_field": "external_job_id", "required": true},
    {"source_field": "application/applied_at", "target_field": "applied_at", "required": true}
  ]
}
```

---

#### HR-XML Mapping

```json
{
  "format": "hrxml",
  "field_mappings": [
    {"source_field": "Candidate/PersonName/GivenName", "target_field": "first_name", "required": true},
    {"source_field": "Candidate/PersonName/FamilyName", "target_field": "last_name", "required": true},
    {"source_field": "Candidate/ContactMethod/InternetEmailAddress", "target_field": "email", "required": true},
    {"source_field": "Candidate/ContactMethod/Telephone", "target_field": "phone", "required": false},
    {"source_field": "Candidate/EmploymentHistory/PositionHistory", "target_field": "work_experience", "required": false},
    {"source_field": "Candidate/EducationHistory/SchoolOrInstitution", "target_field": "education", "required": false}
  ]
}
```

---

## Supported Formats

### LinkedIn Recruiter CSV

**Format Description:**
- Export from LinkedIn Talent Solutions
- CSV format with header row
- UTF-8 encoding
- Comma-delimited

**Required Fields:**
- First Name
- Last Name
- Email Address

**Optional Fields:**
- Phone
- Current Company
- Current Title
- Location
- LinkedIn URL
- Skills
- Experience Summary
- Education

**Sample File:**
```csv
First Name,Last Name,Email Address,Phone,Current Company,Current Title,Location,LinkedIn URL,Skills
John,Doe,john.doe@example.com,+1-555-0100,Tech Corp,Senior Developer,San Francisco CA,https://linkedin.com/in/johndoe,"Python,React,PostgreSQL"
Jane,Smith,jane.smith@example.com,+1-555-0200,Startup Inc,Product Manager,New York NY,https://linkedin.com/in/janesmith,"Agile,Product Strategy,User Research"
```

---

### Indeed XML

**Format Description:**
- XML format from Indeed ATS integration
- UTF-8 encoding
- Schema-based validation

**Required Elements:**
- `<applicant><name>`
- `<applicant><email>`
- `<applicant><resume>`
- `<application><job_id>`

**Optional Elements:**
- `<applicant><phone>`
- `<applicant><location>`
- `<application><cover_letter>`
- `<application><answers>`

**Sample File:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<applications>
  <application>
    <applicant>
      <name>John Doe</name>
      <email>john.doe@example.com</email>
      <phone>+1-555-0100</phone>
      <resume><![CDATA[Resume text content here...]]></resume>
    </applicant>
    <application>
      <job_id>job-12345</job_id>
      <applied_at>2026-03-15T10:00:00Z</applied_at>
    </application>
  </application>
</applications>
```

---

### HR-XML

**Format Description:**
- Industry standard for HR data exchange
- XML format following HR-XML 3.2 specification
- Structured candidate data

**Required Elements:**
- `Candidate/PersonName`
- `Candidate/ContactMethod/InternetEmailAddress`

**Optional Elements:**
- `Candidate/EmploymentHistory`
- `Candidate/EducationHistory`
- `Candidate/Competency` (skills)
- `Candidate/Licenses`

**Sample File:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<HumanResource>
  <Candidate>
    <PersonName>
      <GivenName>John</GivenName>
      <FamilyName>Doe</FamilyName>
    </PersonName>
    <ContactMethod>
      <InternetEmailAddress>john.doe@example.com</InternetEmailAddress>
      <Telephone>
        <FormattedNumber>+1-555-0100</FormattedNumber>
      </Telephone>
    </ContactMethod>
    <EmploymentHistory>
      <PositionHistory>
        <Title>Senior Developer</Title>
        <OrganizationName>Tech Corp</OrganizationName>
        <StartDate>2024-01-01</StartDate>
      </PositionHistory>
    </EmploymentHistory>
  </Candidate>
</HumanResource>
```

---

### Greenhouse ATS

**Format Description:**
- Export from Greenhouse ATS
- JSON format
- Comprehensive candidate data

**Sample File:**
```json
{
  "candidates": [
    {
      "id": "greenhouse-candidate-123",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@example.com",
      "phone": "+1-555-0100",
      "applications": [
        {
          "job_id": "job-456",
          "status": "Active",
          "applied_at": "2026-03-15T10:00:00Z",
          "source": "LinkedIn"
        }
      ],
      "attachments": [
        {
          "type": "resume",
          "url": "https://greenhouse-uploads.s3.amazonaws.com/resume.pdf"
        }
      ]
    }
  ]
}
```

---

## API Reference

### Export Endpoints

#### POST /api/export/resume/{resume_id}

Export candidate data for a specific resume.

**Path Parameters:**
- `resume_id` (UUID, required) - Resume identifier

**Request Body:**
```json
{
  "format": "json|csv|xml",
  "include_analytics": false
}
```

**Response:**
```json
{
  "format": "json",
  "data": {...},
  "metadata": {
    "export_timestamp": "2026-03-22T10:30:00Z",
    "resume_id": "resume-uuid",
    "total_records": 45
  }
}
```

**Status Codes:**
- `200 OK` - Export successful
- `400 Bad Request` - Invalid format parameter
- `404 Not Found` - Resume not found
- `500 Internal Server Error` - Export failed

---

### Import Endpoints

#### POST /api/import/jobs

Create a new import job.

**Request Body:**
```json
{
  "format": "linkedin_csv|indeed_xml|hrxml|greenhouse|lever|workable",
  "original_filename": "export.csv",
  "file_size_bytes": 1048576,
  "vacancy_id": "vacancy-uuid",
  "source_system": "LinkedIn Recruiter",
  "notes": "Q1 2026 sourcing"
}
```

**Response:**
```json
{
  "id": "import-job-uuid",
  "status": "pending",
  "format": "linkedin_csv",
  "created_at": "2026-03-22T10:00:00Z"
}
```

**Status Codes:**
- `201 Created` - Import job created
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing authentication

---

#### GET /api/import/jobs/{job_id}

Get import job status and progress.

**Path Parameters:**
- `job_id` (UUID, required) - Import job identifier

**Response:**
```json
{
  "id": "import-job-uuid",
  "status": "in_progress",
  "total_records": 100,
  "successful_imports": 75,
  "failed_imports": 5,
  "skipped_records": 20,
  "progress_percentage": 75.0,
  "validation_errors": [...]
}
```

---

#### POST /api/import/jobs/{job_id}/start

Start processing an import job.

**Path Parameters:**
- `job_id` (UUID, required) - Import job identifier

**Request Body:**
```json
{
  "async_processing": true
}
```

**Response:**
```json
{
  "job_id": "import-job-uuid",
  "status": "in_progress",
  "task_id": "celery-task-uuid"
}
```

---

#### POST /api/import/jobs/{job_id}/cancel

Cancel a running import job.

**Path Parameters:**
- `job_id` (UUID, required) - Import job identifier

**Request Body:**
```json
{
  "reason": "Incorrect file uploaded"
}
```

**Response:**
```json
{
  "job_id": "import-job-uuid",
  "status": "cancelled",
  "message": "Import job cancelled successfully"
}
```

---

#### GET /api/import/stats

Get import statistics.

**Query Parameters:**
- `job_board_id` (UUID, optional) - Filter by job board

**Response:**
```json
{
  "total_jobs": 150,
  "by_status": {
    "pending": 5,
    "in_progress": 2,
    "completed": 120,
    "failed": 10,
    "cancelled": 13
  },
  "by_format": {
    "linkedin_csv": 80,
    "indeed_xml": 40,
    "hrxml": 30
  },
  "total_records_imported": 15000,
  "total_records_failed": 250,
  "success_rate": 98.3
}
```

---

## Security & Privacy

### Data Security

**Encryption:**
- ✅ All exports encrypted at rest (AES-256)
- ✅ HTTPS/TLS for data in transit
- ✅ Encrypted database connections

**Access Control:**
- ✅ Authentication required for all export/import operations
- ✅ Role-based access control (RBAC)
- ✅ Audit logging for all data portability operations

**Data Sanitization:**
- ✅ PII scrubbing options for test exports
- ✅ Credential masking in API responses
- ✅ Secure file deletion after processing

---

### GDPR Compliance

**Right to Data Portability (Article 20):**
- ✅ Machine-readable formats (JSON, CSV, XML)
- ✅ Commonly used industry standards
- ✅ Complete personal data export
- ✅ Structured data organization

**Data Minimization:**
- ✅ Export only requested data
- ✅ Optional analytics data inclusion
- ✅ Configurable export scope

**Consent Tracking:**
- ✅ Export includes all consent records
- ✅ Consent version history
- ✅ Withdrawal timestamps

---

### File Security

**Upload Security:**
- File size limits (max 100MB per file)
- File type validation
- Virus/malware scanning
- Secure temporary storage

**Storage Security:**
- Encrypted file system
- Access-controlled directories
- Automatic cleanup of old imports
- Secure deletion (overwrite before delete)

---

## Duplicate Detection

### Detection Strategies

AgentHR uses a **3-tier duplicate detection system**:

#### Priority 1: External ID Match (Confidence: 100%)
- Exact match on `external_id` + `job_board_id`
- Most reliable detection method
- Uses source system's unique identifier

```python
# Example: Check by external ID
result = await import_service.check_duplicate(
    job_board_id="job-board-uuid",
    external_id="linkedin-candidate-12345"
)

if result.is_duplicate:
    print(f"Duplicate found: {result.duplicate_type}")
    print(f"Existing resume: {result.existing_resume_id}")
```

---

#### Priority 2: Email Match (Confidence: 95%)
- Case-insensitive email comparison
- Normalized whitespace
- High reliability for candidate identification

```python
# Example: Check by email
result = await import_service.check_duplicate(
    job_board_id="job-board-uuid",
    candidate_email="john.doe@example.com"
)
```

---

#### Priority 3: Name + Title Match (Confidence: 70-85%)
- Fuzzy name matching using Jaccard similarity
- Job title similarity
- Configurable confidence threshold (default: 0.7)

```python
# Example: Check by name and title
result = await import_service.check_duplicate(
    job_board_id="job-board-uuid",
    candidate_name="John Doe",
    job_title="Senior Software Engineer"
)
```

---

### Duplicate Handling Options

**Skip Duplicates:**
```python
# Default behavior - skip duplicate candidates
if duplicate_check.is_duplicate:
    skipped_records += 1
    continue
```

**Update Existing:**
```python
# Update existing candidate with new data
if duplicate_check.is_duplicate:
    await update_candidate(
        resume_id=duplicate_check.existing_resume_id,
        new_data=candidate_data
    )
```

**Create New Version:**
```python
# Create new resume version for existing candidate
if duplicate_check.is_duplicate:
    await create_resume_version(
        candidate_id=duplicate_check.existing_resume_id,
        new_resume=candidate_data
    )
```

---

### Duplicate Detection Statistics

```bash
# Get duplicate detection stats
curl -X GET http://localhost:8000/api/import/stats/duplicates \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "total_checks": 10000,
  "duplicates_found": 1500,
  "duplicate_rate": 15.0,
  "by_type": {
    "external_id": 800,
    "email": 500,
    "name_title": 200
  },
  "by_confidence": {
    "1.0": 800,
    "0.95": 500,
    "0.7-0.85": 200
  }
}
```

---

## Error Handling

### Common Import Errors

#### 1. Invalid File Format

**Error:**
```json
{
  "error": "Invalid file format",
  "details": "Expected CSV file with header row",
  "resolution": "Ensure file is CSV format with column headers"
}
```

**Resolution:**
- Verify file extension (.csv, .xml, .json)
- Check file encoding (must be UTF-8)
- Validate file structure matches expected format

---

#### 2. Missing Required Fields

**Error:**
```json
{
  "error": "Validation failed",
  "validation_errors": [
    {
      "row_number": 23,
      "field": "email",
      "error": "Required field missing",
      "value": null
    }
  ]
}
```

**Resolution:**
- Review field mapping configuration
- Ensure all required fields are present
- Provide default values for optional fields

---

#### 3. Invalid Email Format

**Error:**
```json
{
  "validation_errors": [
    {
      "row_number": 45,
      "field": "email",
      "error": "Invalid email format",
      "value": "not-an-email"
    }
  ]
}
```

**Resolution:**
- Validate email format: `user@domain.com`
- Remove invalid characters
- Use email normalization

---

#### 4. File Size Exceeded

**Error:**
```json
{
  "error": "File size exceeded",
  "details": "File size 150MB exceeds maximum 100MB",
  "resolution": "Split file into multiple smaller files"
}
```

**Resolution:**
- Split large files into batches
- Use bulk import for multiple files
- Contact administrator for limit increase

---

#### 5. Duplicate Candidate

**Warning (not error):**
```json
{
  "warning": "Duplicate candidate detected",
  "duplicate_type": "email",
  "existing_resume_id": "resume-uuid",
  "confidence": 0.95,
  "action": "skipped"
}
```

**Resolution:**
- Review duplicate detection settings
- Configure duplicate handling strategy
- Manually merge duplicate records

---

### Export Errors

#### 1. Resume Not Found

**Error:**
```json
{
  "error": "Resume not found",
  "resume_id": "invalid-uuid",
  "status_code": 404
}
```

**Resolution:**
- Verify resume ID is correct
- Check resume exists in database
- Ensure user has access permissions

---

#### 2. Invalid Export Format

**Error:**
```json
{
  "error": "Invalid export format: txt",
  "valid_formats": ["json", "csv", "xml"]
}
```

**Resolution:**
- Use supported format: json, csv, or xml
- Check format parameter spelling

---

### Error Recovery

**Retry Failed Imports:**
```bash
curl -X POST http://localhost:8000/api/import/jobs/{job_id}/retry \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**View Error Logs:**
```bash
curl -X GET http://localhost:8000/api/import/jobs/{job_id}/errors \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Export Error Report:**
```bash
curl -X GET http://localhost:8000/api/import/jobs/{job_id}/error-report \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o error_report.csv
```

---

## Troubleshooting

### Import Issues

**Problem:** Import job stuck in "pending" status

**Diagnosis:**
```bash
# Check Celery worker status
celery -A celery_app inspect active

# Check import job queue
celery -A celery_app inspect scheduled
```

**Solution:**
- Ensure Celery worker is running
- Restart Celery worker: `celery -A celery_app worker --restart`
- Check worker logs for errors

---

**Problem:** High failure rate during import

**Diagnosis:**
```bash
# Get import statistics
curl -X GET http://localhost:8000/api/import/jobs/{job_id} \
  -H "Authorization: Bearer YOUR_TOKEN"

# Review validation errors
curl -X GET http://localhost:8000/api/import/jobs/{job_id}/errors \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Solution:**
- Review validation error patterns
- Adjust field mapping configuration
- Enable `skip_invalid` option
- Pre-validate data before import

---

**Problem:** Duplicate detection not working

**Diagnosis:**
```python
# Test duplicate detection
from services.import_service import get_import_service

async with get_db() as db:
    import_service = get_import_service(db)

    result = await import_service.check_duplicate(
        job_board_id="job-board-uuid",
        candidate_email="test@example.com"
    )

    print(f"Duplicate found: {result.is_duplicate}")
    print(f"Type: {result.duplicate_type}")
    print(f"Confidence: {result.confidence_score}")
```

**Solution:**
- Verify job_board_id is correct UUID
- Check email normalization
- Review confidence threshold settings
- Verify database indexes on email fields

---

### Export Issues

**Problem:** Export timeout for large datasets

**Diagnosis:**
```bash
# Check export job duration
# Review server logs for timeout errors
tail -f /var/log/agenthr/export.log
```

**Solution:**
- Increase request timeout settings
- Use pagination for large exports
- Enable background export processing
- Schedule exports during off-peak hours

---

**Problem:** Export contains incomplete data

**Diagnosis:**
```python
# Verify data completeness
result = await export_service.export_candidate_data(
    resume_id=resume_uuid,
    export_format="json"
)

print(f"Total records: {result['metadata']['total_records']}")
print(f"Data sections: {list(result['data'].keys())}")
```

**Solution:**
- Check database integrity
- Verify foreign key relationships
- Review export service logs
- Test with smaller dataset

---

### Performance Optimization

**Slow Import Processing:**

1. **Enable Batch Processing:**
```python
# Process records in batches of 100
BATCH_SIZE = 100
for i in range(0, len(records), BATCH_SIZE):
    batch = records[i:i+BATCH_SIZE]
    await process_batch(batch)
```

2. **Use Async Processing:**
```python
# Process imports asynchronously
import asyncio

async def process_import_async(job_id):
    # Import processing logic
    pass

# Run in background
asyncio.create_task(process_import_async(job_id))
```

3. **Database Optimization:**
```sql
-- Add indexes for faster duplicate detection
CREATE INDEX idx_imported_resumes_email ON imported_resumes(candidate_email);
CREATE INDEX idx_imported_resumes_external_id ON imported_resumes(job_board_id, external_id);
```

---

## Examples

### Example 1: Export All Candidate Data as JSON

```python
import asyncio
from uuid import UUID
from services.export_service import get_export_service
from database import async_session_maker

async def export_candidate_json(resume_id: str):
    """Export candidate data as JSON."""
    async with async_session_maker() as db:
        export_service = get_export_service(db)

        result = await export_service.export_candidate_data(
            resume_id=UUID(resume_id),
            export_format="json",
            include_analytics=True
        )

        # Save to file
        import json
        with open(f"export_{resume_id}.json", "w") as f:
            json.dump(result["data"], f, indent=2)

        print(f"✅ Exported {result['metadata']['total_records']} records")
        print(f"📁 Saved to: export_{resume_id}.json")

# Run export
asyncio.run(export_candidate_json("123e4567-e89b-12d3-a456-426614174000"))
```

---

### Example 2: Import LinkedIn CSV with Custom Field Mapping

```python
import asyncio
from services.import_service import get_import_service
from database import async_session_maker

async def import_linkedin_csv(file_path: str, vacancy_id: str):
    """Import candidates from LinkedIn CSV export."""
    from models.import_job import ImportJob, ImportFormat, ImportJobStatus
    from uuid import uuid4

    async with async_session_maker() as db:
        # Create import job
        import_job = ImportJob(
            id=uuid4(),
            format=ImportFormat.LINKEDIN_CSV,
            recruiter_id=current_user_id,
            vacancy_id=vacancy_id,
            file_path=file_path,
            original_filename="linkedin_export.csv",
            status=ImportJobStatus.PENDING
        )

        db.add(import_job)
        await db.commit()

        # Start processing
        # This would be handled by Celery task in production
        print(f"✅ Import job created: {import_job.id}")
        print(f"📋 Status: {import_job.status.value}")

# Run import
asyncio.run(import_linkedin_csv(
    file_path="/uploads/linkedin_export.csv",
    vacancy_id="vacancy-uuid-here"
))
```

---

### Example 3: Batch Export Multiple Candidates

```python
import asyncio
from typing import List
from uuid import UUID
from services.export_service import get_export_service
from database import async_session_maker
import zipfile
import json

async def batch_export_candidates(resume_ids: List[str], output_file: str):
    """Export multiple candidates and create ZIP archive."""
    async with async_session_maker() as db:
        export_service = get_export_service(db)

        # Create ZIP file
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for resume_id in resume_ids:
                try:
                    result = await export_service.export_candidate_data(
                        resume_id=UUID(resume_id),
                        export_format="json"
                    )

                    # Add to ZIP
                    filename = f"{resume_id}.json"
                    zipf.writestr(
                        filename,
                        json.dumps(result["data"], indent=2)
                    )

                    print(f"✅ Exported: {filename}")

                except Exception as e:
                    print(f"❌ Failed to export {resume_id}: {e}")

        print(f"📦 Batch export complete: {output_file}")

# Run batch export
resume_list = [
    "123e4567-e89b-12d3-a456-426614174000",
    "223e4567-e89b-12d3-a456-426614174001",
    "323e4567-e89b-12d3-a456-426614174002"
]

asyncio.run(batch_export_candidates(resume_list, "candidates_export.zip"))
```

---

### Example 4: Duplicate Detection Before Import

```python
import asyncio
from services.import_service import get_import_service
from database import async_session_maker

async def check_and_import_candidate(
    job_board_id: str,
    candidate_data: dict
):
    """Check for duplicates before importing candidate."""
    async with async_session_maker() as db:
        import_service = get_import_service(db)

        # Check for duplicates
        duplicate_check = await import_service.check_duplicate(
            job_board_id=job_board_id,
            external_id=candidate_data.get("external_id"),
            candidate_email=candidate_data.get("email"),
            candidate_name=candidate_data.get("name"),
            job_title=candidate_data.get("title")
        )

        if duplicate_check.is_duplicate:
            print(f"⚠️  Duplicate detected!")
            print(f"   Type: {duplicate_check.duplicate_type}")
            print(f"   Confidence: {duplicate_check.confidence_score}")
            print(f"   Existing resume: {duplicate_check.existing_resume_id}")

            # Decide action based on duplicate type
            if duplicate_check.duplicate_type == "external_id":
                print("   Action: Skipping (exact match)")
                return None
            elif duplicate_check.confidence_score < 0.8:
                print("   Action: Importing as new (low confidence)")
                # Proceed with import
            else:
                print("   Action: Updating existing candidate")
                # Update existing candidate
        else:
            print("✅ No duplicate found - proceeding with import")
            # Import new candidate

# Test duplicate detection
candidate = {
    "external_id": "linkedin-12345",
    "email": "john.doe@example.com",
    "name": "John Doe",
    "title": "Senior Software Engineer"
}

asyncio.run(check_and_import_candidate(
    job_board_id="job-board-uuid",
    candidate_data=candidate
))
```

---

### Example 5: Scheduled Automated Backups

```python
from celery import shared_task
from celery.schedules import crontab
from services.export_service import get_export_service
from database import async_session_maker
import boto3
from datetime import datetime

@shared_task
def automated_backup_export():
    """
    Scheduled task for automated candidate data backups.

    Runs daily at 2 AM, exports all candidate data,
    and uploads to S3-compatible storage.
    """
    import asyncio

    async def run_backup():
        async with async_session_maker() as db:
            export_service = get_export_service(db)

            # Get all resume IDs
            from sqlalchemy import select
            from models.resume import Resume

            result = await db.execute(select(Resume.id))
            resume_ids = [row[0] for row in result]

            # Export all candidates
            exports = []
            for resume_id in resume_ids:
                try:
                    export_result = await export_service.export_candidate_data(
                        resume_id=resume_id,
                        export_format="json"
                    )
                    exports.append(export_result["data"])
                except Exception as e:
                    print(f"Failed to export {resume_id}: {e}")

            # Create backup file
            import json
            backup_data = {
                "backup_date": datetime.utcnow().isoformat(),
                "total_candidates": len(exports),
                "candidates": exports
            }

            backup_filename = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

            # Upload to S3
            s3 = boto3.client('s3')
            s3.put_object(
                Bucket='agenthr-backups',
                Key=f'daily_backups/{backup_filename}',
                Body=json.dumps(backup_data),
                ServerSideEncryption='AES256'
            )

            print(f"✅ Backup completed: {backup_filename}")
            print(f"📊 Exported {len(exports)} candidates")

    asyncio.run(run_backup())

# Schedule in Celery Beat
# Add to celeryconfig.py:
# beat_schedule = {
#     'daily-backup': {
#         'task': 'tasks.automated_backup_export',
#         'schedule': crontab(hour=2, minute=0),
#     },
# }
```

---

## Best Practices

### Export Best Practices

1. **Choose the Right Format:**
   - JSON: Full data hierarchy, API integrations
   - CSV: Spreadsheet analysis, reporting
   - XML: Enterprise integrations, legacy systems

2. **Optimize for Size:**
   - Exclude analytics data if not needed
   - Use compression (gzip) for large exports
   - Export in batches for very large datasets

3. **Security:**
   - Always use HTTPS for export downloads
   - Delete exported files after download
   - Encrypt sensitive exports at rest

4. **Performance:**
   - Schedule large exports during off-peak hours
   - Use pagination for incremental exports
   - Cache frequently accessed export data

---

### Import Best Practices

1. **Data Validation:**
   - Validate file format before upload
   - Check required fields are present
   - Verify email format and phone numbers

2. **Duplicate Prevention:**
   - Always enable duplicate detection
   - Review duplicate matches before proceeding
   - Configure appropriate confidence thresholds

3. **Error Handling:**
   - Enable `skip_invalid` for production imports
   - Review validation errors before retrying
   - Keep import error logs for debugging

4. **Performance:**
   - Process imports asynchronously
   - Use batch processing for large files
   - Split very large files into smaller chunks

---

## Support & Resources

### Documentation
- API Reference: `/docs/api-reference.md`
- GDPR Compliance: `./GDPR_TESTING_CHECKLIST.md`
- Database Schema: `/docs/database-schema.md`

### Code Examples
- Export Service: `backend/services/export_service.py`
- Import Service: `backend/services/import_service.py`
- Import Tasks: `backend/tasks/import_tasks.py`

### Testing
- E2E Tests: `frontend/e2e/gdpr-data-export-flow.spec.ts`
- Unit Tests: `backend/tests/test_export_service.py`
- Integration Tests: `backend/tests/integration/test_import_integration.py`

### Contact
- GitHub Issues: `https://github.com/agenthr/agenthr/issues`
- Documentation: `https://docs.agenthr.com`
- Support Email: `support@agenthr.com`

---

**Last Updated:** 2026-03-22
**Document Version:** 1.0
**Maintained By:** AgentHR Development Team
