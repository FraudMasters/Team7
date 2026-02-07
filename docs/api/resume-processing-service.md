# Resume Processing Service API Documentation

## Overview

The Resume Processing Service handles all operations related to resume upload, parsing, text extraction, and analysis. It provides endpoints for uploading resume files (PDF, DOCX), managing resume records, and triggering AI-powered resume analysis.

## Base URL

```
http://localhost:8001
```

Via API Gateway:
```
http://localhost:8888/api/resumes
```

## Authentication

All endpoints require JWT authentication via the API Gateway. Include the `Authorization` header with your Bearer token:

```
Authorization: Bearer <your-jwt-token>
```

---

## Endpoints

### Upload Resume

Upload a new resume file for processing.

**Endpoint:** `POST /api/resumes/upload`

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (required) - Resume file (PDF or DOCX)

**Response:** `201 Created`

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "resume.pdf",
  "status": "pending",
  "message": "Resume uploaded successfully"
}
```

**Errors:**
- `415 Unsupported Media Type` - Invalid file type
- `413 Request Entity Too Large` - File size exceeds limit (default 10MB)
- `500 Internal Server Error` - Upload or database error

**Example:**
```bash
curl -X POST "http://localhost:8888/api/resumes/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@resume.pdf"
```

---

### List Resumes

Get a paginated list of all resumes.

**Endpoint:** `GET /api/resumes/`

**Query Parameters:**
- `skip` (optional, default: 0) - Number of records to skip
- `limit` (optional, default: 100, max: 1000) - Maximum records to return

**Response:** `200 OK`

```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "filename": "resume.pdf",
    "status": "completed",
    "created_at": "2025-01-15T10:30:00Z",
    "language": "en"
  }
]
```

**Example:**
```bash
curl -X GET "http://localhost:8888/api/resumes/?skip=0&limit=50" \
  -H "Authorization: Bearer <token>"
```

---

### Get Resume Details

Retrieve detailed information about a specific resume including extracted text.

**Endpoint:** `GET /api/resumes/{resume_id}`

**Path Parameters:**
- `resume_id` (required) - UUID of the resume

**Response:** `200 OK`

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "resume.pdf",
  "status": "completed",
  "raw_text": "John Doe\nSoftware Engineer...",
  "language": "en",
  "message": "Resume retrieved successfully"
}
```

**Errors:**
- `404 Not Found` - Resume not found
- `422 Unprocessable Entity` - Invalid resume ID format

**Example:**
```bash
curl -X GET "http://localhost:8888/api/resumes/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer <token>"
```

---

### Update Resume Status

Update the status of a resume (for Kanban board workflow).

**Endpoint:** `PATCH /api/resumes/{resume_id}`

**Path Parameters:**
- `resume_id` (required) - UUID of the resume

**Request Body:**
```json
{
  "status": "interview"
}
```

**Valid Status Values:**
- `new` - New candidate
- `reviewed` - Under review
- `interview` - Interview scheduled
- `offered` - Offer made
- `hired` - Candidate hired
- `pending` - Processing pending
- `completed` - Analysis completed
- `processing` - Currently processing
- `failed` - Processing failed

**Response:** `200 OK`

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "interview",
  "filename": "resume.pdf"
}
```

**Example:**
```bash
curl -X PATCH "http://localhost:8888/api/resumes/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "interview"}'
```

---

### Delete Resume

Delete a resume and its associated file.

**Endpoint:** `DELETE /api/resumes/{resume_id}`

**Path Parameters:**
- `resume_id` (required) - UUID of the resume

**Response:** `204 No Content`

**Example:**
```bash
curl -X DELETE "http://localhost:8888/api/resumes/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer <token>"
```

---

### Analyze Resume

Trigger AI-powered resume analysis (skills, entities, experience, grammar).

**Endpoint:** `POST /api/analyze`

**Request Body:**
```json
{
  "resume_id": "123e4567-e89b-12d3-a456-426614174000",
  "extract_experience": true,
  "check_grammar": true
}
```

**Response:** `200 OK`

```json
{
  "resume_id": "123e4567-e89b-12d3-a456-426614174000",
  "language": "en",
  "keywords": ["Python", "Django", "PostgreSQL"],
  "entities": {
    "technical_skills": ["Python", "Django"],
    "soft_skills": ["Leadership", "Communication"]
  },
  "experience_summary": [
    {
      "title": "Senior Developer",
      "company": "Tech Corp",
      "duration": "3 years"
    }
  ],
  "grammar_issues": [],
  "processing_time_ms": 1234.5
}
```

**Example:**
```bash
curl -X POST "http://localhost:8888/api/analyze" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "123e4567-e89b-12d3-a456-426614174000",
    "extract_experience": true,
    "check_grammar": true
  }'
```

---

### Get Analysis Results

Retrieve stored analysis results for a resume.

**Endpoint:** `GET /api/analysis/{resume_id}`

**Path Parameters:**
- `resume_id` (required) - UUID of the resume

**Response:** `200 OK`

```json
{
  "resume_id": "123e4567-e89b-12d3-a456-426614174000",
  "analysis_results": {
    "skills": ["Python", "Django"],
    "keywords": ["Python", "Django", "API"]
  }
}
```

---

## Data Models

### ResumeStatus Enum

Valid resume status values:
- `PENDING` - Awaiting processing
- `PROCESSING` - Currently being processed
- `COMPLETED` - Processing completed successfully
- `FAILED` - Processing failed
- `NEW` - New candidate (Kanban)
- `REVIEWED` - Under review (Kanban)
- `INTERVIEW` - Interview stage (Kanban)
- `OFFERED` - Offer made (Kanban)
- `HIRED` - Candidate hired (Kanban)

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong",
  "type": "error_type"
}
```

Common HTTP status codes:
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Missing or invalid authentication
- `404 Not Found` - Resource not found
- `415 Unsupported Media Type` - Invalid file type
- `422 Unprocessable Entity` - Validation error
- `413 Request Entity Too Large` - File too large
- `500 Internal Server Error` - Server error

---

## Rate Limiting

Via API Gateway:
- 100 requests per second
- 10,000 requests per hour

---

## Internationalization

The service supports multiple languages (English, Russian). Use the `Accept-Language` header:

```
Accept-Language: en
```

or

```
Accept-Language: ru
```

---

## gRPC Service

The Resume Processing Service also exposes a gRPC interface on port `50051`.

**Available RPC Methods:**
- `CreateResume` - Create a new resume entry
- `GetResume` - Fetch resume by UUID
- `ListResumes` - List resumes with pagination
- `DeleteResume` - Delete resume and file
- `AnalyzeResume` - Trigger resume analysis
- `GetResumeAnalysis` - Get analysis results
- `GetWorkExperience` - Get work experience data
- `GetResumeText` - Get raw resume text

See `protos/resume.proto` for the complete service definition.
