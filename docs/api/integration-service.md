# Integration Service API Documentation

## Overview

The Integration Service manages third-party integrations with external platforms including LinkedIn, job boards, ATS systems (Greenhouse, Lever, Workday), and HRIS systems (BambooHR, Ashby). It provides endpoints for connecting to external services, syncing data, and managing integration configurations.

## Base URL

```
http://localhost:8009
```

Via API Gateway:
```
http://localhost:8888/api/integrations
```

## Authentication

All endpoints require JWT authentication via the API Gateway. Include the `Authorization` header with your Bearer token:

```
Authorization: Bearer <your-jwt-token>
```

---

## Endpoints

### List Integrations

Get all available integrations and their connection status.

**Endpoint:** `GET /api/integrations/`

**Query Parameters:**
- `type` (optional) - Filter by integration type (linkedin, job_board, ats, hris)

**Response:** `200 OK`

```json
{
  "total": 5,
  "integrations": [
    {
      "id": "linkedin",
      "name": "LinkedIn",
      "type": "linkedin",
      "description": "Import candidate profiles from LinkedIn",
      "connected": false,
      "enabled": true
    },
    {
      "id": "greenhouse",
      "name": "Greenhouse",
      "type": "ats",
      "description": "ATS integration for Greenhouse",
      "connected": false,
      "enabled": true
    },
    {
      "id": "lever",
      "name": "Lever",
      "type": "ats",
      "description": "ATS integration for Lever",
      "connected": false,
      "enabled": true
    },
    {
      "id": "bamboohr",
      "name": "BambooHR",
      "type": "hris",
      "description": "HRIS integration for BambooHR",
      "connected": false,
      "enabled": true
    },
    {
      "id": "indeed",
      "name": "Indeed",
      "type": "job_board",
      "description": "Job board integration for Indeed",
      "connected": true,
      "enabled": true
    }
  ]
}
```

**Integration Types:**
- `linkedin` - LinkedIn profile importing
- `job_board` - Job board posting/syncing
- `ats` - ATS system integration
- `hris` - HRIS system integration

**Example:**
```bash
# Get all integrations
curl -X GET "http://localhost:8888/api/integrations/" \
  -H "Authorization: Bearer <token>"

# Filter by type
curl -X GET "http://localhost:8888/api/integrations/?type=ats" \
  -H "Authorization: Bearer <token>"
```

---

### Connect Integration

Connect to an external integration service.

**Endpoint:** `POST /api/integrations/connect`

**Request Body:**
```json
{
  "type": "linkedin",
  "credentials": {
    "api_key": "your-api-key",
    "api_secret": "your-api-secret"
  },
  "settings": {
    "auto_sync": true,
    "sync_interval_hours": 24
  }
}
```

**Response:** `201 Created`

```json
{
  "id": "integration-1",
  "type": "linkedin",
  "status": "connected",
  "connected_at": "2025-01-15T10:30:00Z",
  "settings": {
    "auto_sync": true,
    "sync_interval_hours": 24
  }
}
```

**Supported Integration Types:**

| Type | Required Credentials |
|------|---------------------|
| `linkedin` | `api_key`, `api_secret` |
| `greenhouse` | `api_key`, `board_token` |
| `lever` | `api_key`, `webhook_url` |
| `workday` | `client_id`, `client_secret`, `tenant_url` |
| `bamboohr` | `api_key`, `subdomain` |
| `ashby` | `api_key` |
| `indeed` | `publisher_id`, `api_key` |
| `linkedin_jobs` | `client_id`, `client_secret` |

---

### Disconnect Integration

Disconnect an active integration.

**Endpoint:** `POST /api/integrations/{integration_id}/disconnect`

**Path Parameters:**
- `integration_id` (required) - ID of the integration

**Response:** `200 OK`

```json
{
  "id": "integration-1",
  "status": "disconnected",
  "message": "Integration disconnected successfully"
}
```

---

## LinkedIn Endpoints

### Get LinkedIn Profile

Import a candidate profile from LinkedIn.

**Endpoint:** `POST /api/linkedin/profile`

**Request Body:**
```json
{
  "profile_url": "https://linkedin.com/in/johndoe",
  "include_skills": true,
  "include_experience": true,
  "include_education": true
}
```

**Response:** `200 OK`

```json
{
  "profile": {
    "first_name": "John",
    "last_name": "Doe",
    "headline": "Senior Python Developer",
    "location": "San Francisco, CA",
    "skills": ["Python", "Django", "PostgreSQL"],
    "experience": [
      {
        "title": "Senior Python Developer",
        "company": "Tech Corp",
        "duration": "3 years"
      }
    ],
    "education": [
      {
        "school": "MIT",
        "degree": "BS Computer Science"
      }
    ]
  }
}
```

---

### Get LinkedIn Company

Import company information from LinkedIn.

**Endpoint:** `POST /api/linkedin/company`

**Request Body:**
```json
{
  "company_url": "https://linkedin.com/company/tech-corp",
  "include_employees": false
}
```

**Response:** `200 OK`

```json
{
  "company": {
    "name": "Tech Corp",
    "industry": "Technology",
    "size": "1000-5000",
    "website": "https://techcorp.com",
    "description": "Leading technology company..."
  }
}
```

---

## Job Board Integrations

### Sync Vacancy to Job Board

Sync a vacancy to an external job board.

**Endpoint:** `POST /api/job-integrations/sync`

**Request Body:**
```json
{
  "job_board": "indeed",
  "vacancy_id": "vacancy-123",
  "external_posting": {
    "reference_number": "REF-12345",
    "status": "active",
    "location": "Remote"
  }
}
```

**Supported Job Boards:**
- `indeed` - Indeed.com
- `linkedin_jobs` - LinkedIn Jobs
- `glassdoor` - Glassdoor
- `monster` - Monster.com

**Response:** `201 Created`

```json
{
  "sync_id": "sync-1",
  "job_board": "indeed",
  "vacancy_id": "vacancy-123",
  "external_id": "indeed-posting-123",
  "status": "posted",
  "posted_at": "2025-01-15T10:30:00Z"
}
```

---

### Get Sync Status

Get the sync status for job board postings.

**Endpoint:** `GET /api/job-integrations/sync/{vacancy_id}`

**Path Parameters:**
- `vacancy_id` (required) - ID of the vacancy

**Response:** `200 OK`

```json
{
  "vacancy_id": "vacancy-123",
  "syncs": [
    {
      "job_board": "indeed",
      "external_id": "indeed-posting-123",
      "status": "active",
      "posted_at": "2025-01-15T10:30:00Z",
      "last_synced_at": "2025-01-15T12:00:00Z"
    },
    {
      "job_board": "linkedin_jobs",
      "external_id": "linkedin-posting-456",
      "status": "active",
      "posted_at": "2025-01-15T10:35:00Z",
      "last_synced_at": "2025-01-15T12:00:00Z"
    }
  ]
}
```

---

### Bulk Sync to Job Boards

Sync multiple vacancies to job boards.

**Endpoint:** `POST /api/job-integrations/bulk-sync`

**Request Body:**
```json
{
  "job_board": "indeed",
  "vacancy_ids": ["vacancy-1", "vacancy-2", "vacancy-3"],
  "sync_all": false
}
```

**Response:** `201 Created`

```json
{
  "total": 3,
  "synced": 3,
  "failed": 0,
  "syncs": [
    {
      "vacancy_id": "vacancy-1",
      "external_id": "indeed-posting-1",
      "status": "posted"
    }
  ]
}
```

---

## ATS Integrations

### Sync Candidates to ATS

Sync candidates to an external ATS system.

**Endpoint:** `POST /api/ats-integrations/sync-candidates`

**Request Body:**
```json
{
  "ats_system": "greenhouse",
  "candidate_ids": ["candidate-1", "candidate-2"],
  "create_missing": true
}
```

**Supported ATS Systems:**
- `greenhouse` - Greenhouse ATS
- `lever` - Lever ATS
- `workday` - Workday ATS

**Response:** `201 Created`

```json
{
  "synced": 2,
  "created": 2,
  "updated": 0,
  "failed": 0,
  "candidates": [
    {
      "local_id": "candidate-1",
      "external_id": "greenhouse-candidate-1",
      "status": "created"
    }
  ]
}
```

---

### Get ATS Candidates

Get candidates synced from ATS system.

**Endpoint:** `GET /api/ats-integrations/candidates`

**Query Parameters:**
- `ats_system` (required) - ATS system name
- `updated_since` (optional) - Filter by update date

**Response:** `200 OK`

```json
{
  "ats_system": "greenhouse",
  "candidates": [
    {
      "local_id": "candidate-1",
      "external_id": "greenhouse-candidate-1",
      "last_synced_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

---

## HRIS Integrations

### Sync Employee to HRIS

Sync hired candidate to HRIS system.

**Endpoint:** `POST /api/hris-integrations/sync-employee`

**Request Body:**
```json
{
  "hris_system": "bamboohr",
  "candidate_id": "candidate-123",
  "employee_data": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "start_date": "2025-02-01",
    "department": "Engineering"
  }
}
```

**Supported HRIS Systems:**
- `bamboohr` - BambooHR
- `ashby` - Ashby HQ

**Response:** `201 Created`

```json
{
  "employee_id": "employee-1",
  "external_employee_id": "bamboohr-123",
  "status": "created",
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

### Get Employee Data

Get employee data from HRIS system.

**Endpoint:** `GET /api/hris-integrations/employee/{employee_id}`

**Path Parameters:**
- `employee_id` (required) - ID of the employee

**Query Parameters:**
- `hris_system` (required) - HRIS system name

**Response:** `200 OK`

```json
{
  "employee_id": "employee-1",
  "external_employee_id": "bamboohr-123",
  "data": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "department": "Engineering",
    "title": "Senior Python Developer",
    "start_date": "2025-02-01",
    "status": "active"
  }
}
```

---

## Data Models

### Integration Status Values

| Status | Description |
|--------|-------------|
| `connected` | Integration is active and connected |
| `disconnected` | Integration is disconnected |
| `error` | Integration has an error |
| `pending` | Integration connection is pending |

### Job Board Posting Status Values

| Status | Description |
|--------|-------------|
| `pending` | Posting is pending |
| `posted` | Posting is live |
| `expired` | Posting has expired |
| `removed` | Posting was removed |

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Missing or invalid authentication
- `404 Not Found` - Resource not found
| `422 Unprocessable Entity` - Validation error
- `424 Failed Dependency` - External service error
- `500 Internal Server Error` - Server error

---

## Rate Limiting

Via API Gateway:
- 100 requests per second
- 10,000 requests per hour

---

## Webhooks

External services can send webhooks to this service for real-time updates.

**Webhook Endpoint:** `POST /api/integrations/webhook/{integration_id}`

**Webhook Events:**
- ATS candidate updated
- HRIS employee updated
- Job board posting status changed

---

## gRPC Service

The Integration Service also exposes a gRPC interface on port `50059`.

**Available RPC Methods:**
- `ConnectIntegration` - Connect to external service
- `DisconnectIntegration` - Disconnect integration
- `GetLinkedInProfile` - Import LinkedIn profile
- `SyncToJobBoard` - Sync vacancy to job board
- `SyncToATS` - Sync candidates to ATS
- `SyncToHRIS` - Sync employee to HRIS
- `GetSyncStatus` - Get sync status

See `protos/integration.proto` for the complete service definition.
