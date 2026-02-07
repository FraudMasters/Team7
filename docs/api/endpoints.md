# API Endpoints Reference

Complete reference for all AgentHR API endpoints.

## Base URL

```
https://api.agenthr.com/api
```

## Table of Contents

- [Candidates](#candidates)
- [Resumes](#resumes)
- [Vacancies](#vacancies)
- [Ranking](#ranking)
- [Analytics](#analytics)
- [Matching](#matching)
- [Webhooks](#webhooks)
- [Workflows](#workflows)
- [Plugins](#plugins)
- [API Keys](#api-keys)

---

## Candidates

Manage candidate profiles throughout the recruitment pipeline.

### List Candidates

```http
GET /candidates
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| skip | integer | No | Number of results to skip (default: 0) |
| limit | integer | No | Max results to return (default: 50, max: 100) |
| stage | string | No | Filter by pipeline stage |
| vacancy_id | string | No | Filter by vacancy UUID |

**Scopes:** `read:candidates`

**Example Request:**
```bash
curl -X GET "https://api.agenthr.com/api/candidates?limit=10&stage=interview" \
  -H "X-API-Key: your_api_key"
```

**Response (200):**
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Jane Smith",
      "email": "jane.smith@example.com",
      "stage": "interview",
      "vacancy_id": "vacancy_uuid_here",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 150,
  "skip": 0,
  "limit": 10
}
```

### Get Candidate

```http
GET /candidates/{candidate_id}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| candidate_id | string (UUID) | Candidate ID |

**Scopes:** `read:candidates`

**Example Request:**
```bash
curl -X GET "https://api.agenthr.com/api/candidates/123e4567-e89b-12d3-a456-426614174000" \
  -H "X-API-Key: your_api_key"
```

**Response (200):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Jane Smith",
  "email": "jane.smith@example.com",
  "phone": "+1-555-0123",
  "stage": "interview",
  "vacancy_id": "vacancy_uuid_here",
  "resume_id": "resume_uuid_here",
  "tags": ["senior", "python-expert"],
  "notes": "Strong technical background",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-16T14:20:00Z"
}
```

### Move Candidate Stage

```http
PUT /candidates/{candidate_id}/stage
```

**Scopes:** `write:candidates`

**Request Body:**
```json
{
  "stage": "offer",
  "vacancy_id": "optional_vacancy_uuid",
  "notes": "Candidate accepted offer"
}
```

**Response (200):**
```json
{
  "id": "candidate_id",
  "stage": "offer",
  "previous_stage": "interview",
  "updated_at": "2024-01-17T10:00:00Z"
}
```

### Bulk Move Candidates

```http
POST /candidates/bulk-move
```

**Scopes:** `write:candidates`

**Request Body:**
```json
{
  "candidate_ids": ["uuid1", "uuid2", "uuid3"],
  "stage": "interview",
  "vacancy_id": "vacancy_uuid",
  "notes": "Batch interview scheduling"
}
```

**Response (200):**
```json
{
  "moved": 3,
  "failed": 0,
  "errors": []
}
```

### Update Candidate

```http
PUT /candidates/{candidate_id}
```

**Scopes:** `write:candidates`

**Request Body:**
```json
{
  "name": "Updated Name",
  "email": "newemail@example.com",
  "phone": "+1-555-9999",
  "notes": "Updated notes"
}
```

### Delete Candidate

```http
DELETE /candidates/{candidate_id}
```

**Scopes:** `delete:candidates`

**Response (204):** No content

---

## Resumes

Handle resume uploads, parsing, and management.

### Upload Resume

```http
POST /resumes/upload
```

**Scopes:** `write:resumes`

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|------|------|----------|-------------|
| file | file | Yes | Resume file (PDF, DOCX, DOC) |
| vacancy_id | string | No | Associate with vacancy |

**Example Request:**
```bash
curl -X POST "https://api.agenthr.com/api/resumes/upload" \
  -H "X-API-Key: your_api_key" \
  -F "file=@resume.pdf" \
  -F "vacancy_id=vacancy_uuid"
```

**Response (201):**
```json
{
  "id": "resume_uuid",
  "filename": "resume.pdf",
  "status": "processing",
  "parsed_data": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-555-0123",
    "skills": ["Python", "FastAPI", "React"],
    "experience_years": 5
  },
  "created_at": "2024-01-15T10:30:00Z"
}
```

### List Resumes

```http
GET /resumes
```

**Scopes:** `read:resumes`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| skip | integer | Results to skip |
| limit | integer | Max results |
| status | string | Filter by status (processing, completed, failed) |

**Response (200):**
```json
{
  "items": [
    {
      "id": "resume_uuid",
      "filename": "resume.pdf",
      "status": "completed",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 50
}
```

### Get Resume

```http
GET /resumes/{resume_id}
```

**Scopes:** `read:resumes`

**Response (200):**
```json
{
  "id": "resume_uuid",
  "filename": "resume.pdf",
  "status": "completed",
  "parsed_data": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-555-0123",
    "skills": ["Python", "FastAPI"],
    "education": [
      {
        "degree": "BS Computer Science",
        "school": "MIT",
        "year": 2018
      }
    ],
    "experience": [
      {
        "title": "Senior Developer",
        "company": "Tech Corp",
        "years": 3
      }
    ]
  },
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Update Resume Status

```http
PATCH /resumes/{resume_id}
```

**Scopes:** `write:resumes`

**Request Body:**
```json
{
  "status": "approved"
}
```

---

## Vacancies

Manage job vacancies and postings.

### List Vacancies

```http
GET /vacancies
```

**Scopes:** `read:vacancies`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| skip | integer | Results to skip |
| limit | integer | Max results |
| is_active | boolean | Filter by active status |

**Response (200):**
```json
{
  "items": [
    {
      "id": "vacancy_uuid",
      "title": "Senior Python Developer",
      "description": "We are looking for...",
      "location": "Remote",
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 25
}
```

### Get Vacancy

```http
GET /vacancies/{vacancy_id}
```

**Scopes:** `read:vacancies`

**Response (200):**
```json
{
  "id": "vacancy_uuid",
  "title": "Senior Python Developer",
  "description": "Job description...",
  "required_skills": ["Python", "FastAPI", "PostgreSQL"],
  "min_experience": 5,
  "location": "Remote",
  "salary_min": 100000,
  "salary_max": 150000,
  "work_format": "remote",
  "employment_type": "full-time",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Create Vacancy

```http
POST /vacancies
```

**Scopes:** `write:vacancies`

**Request Body:**
```json
{
  "title": "Senior Python Developer",
  "description": "We are looking for an experienced Python developer...",
  "required_skills": ["Python", "FastAPI", "PostgreSQL"],
  "min_experience": 5,
  "location": "Remote",
  "salary_min": 100000,
  "salary_max": 150000,
  "work_format": "remote",
  "employment_type": "full-time"
}
```

**Response (201):**
```json
{
  "id": "vacancy_uuid",
  "title": "Senior Python Developer",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Update Vacancy

```http
PUT /vacancies/{vacancy_id}
```

**Scopes:** `write:vacancies`

**Request Body:**
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "is_active": false
}
```

### Delete Vacancy

```http
DELETE /vacancies/{vacancy_id}
```

**Scopes:** `delete:vacancies`

**Response (204):** No content

---

## Ranking

AI-powered candidate ranking and matching.

### Rank Candidate

```http
POST /ranking/candidates/{candidate_id}/rank
```

**Scopes:** `write:candidates`

**Request Body:**
```json
{
  "vacancy_id": "vacancy_uuid",
  "use_fairness": true
}
```

**Response (200):**
```json
{
  "candidate_id": "candidate_uuid",
  "vacancy_id": "vacancy_uuid",
  "score": 85.5,
  "rank": 3,
  "match_reasons": [
    "Required skills match: 90%",
    "Experience level: suitable",
    "Education: meets requirements"
  ],
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Get Ranked Candidates

```http
GET /ranking/vacancies/{vacancy_id}/ranked
```

**Scopes:** `read:candidates`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| limit | integer | Max results (default: 10) |

**Response (200):**
```json
{
  "items": [
    {
      "candidate_id": "uuid1",
      "score": 92.5,
      "rank": 1,
      "name": "Jane Smith"
    },
    {
      "candidate_id": "uuid2",
      "score": 88.0,
      "rank": 2,
      "name": "John Doe"
    }
  ]
}
```

---

## Analytics

Recruitment analytics and reporting.

### Get Key Metrics

```http
GET /analytics/metrics/key
```

**Scopes:** `read:analytics`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| start_date | string | ISO 8601 date |
| end_date | string | ISO 8601 date |

**Response (200):**
```json
{
  "time_to_hire_days": 42,
  "resumes_processed": 1250,
  "match_rate": 0.73,
  "interview_rate": 0.35,
  "offer_acceptance_rate": 0.85
}
```

### Get Funnel Metrics

```http
GET /analytics/funnel
```

**Scopes:** `read:analytics`

**Response (200):**
```json
{
  "stages": [
    {"stage": "applied", "count": 500, "conversion_rate": 1.0},
    {"stage": "screening", "count": 250, "conversion_rate": 0.5},
    {"stage": "interview", "count": 100, "conversion_rate": 0.2},
    {"stage": "offer", "count": 30, "conversion_rate": 0.06},
    {"stage": "hired", "count": 25, "conversion_rate": 0.05}
  ]
}
```

### Get Source Tracking

```http
GET /analytics/sources
```

**Scopes:** `read:analytics`

**Response (200):**
```json
{
  "sources": [
    {"source": "linkedin", "count": 150, "conversion_rate": 0.12},
    {"source": "referral", "count": 80, "conversion_rate": 0.35},
    {"source": "website", "count": 200, "conversion_rate": 0.08}
  ]
}
```

---

## Matching

Candidate-vacancy matching using AI.

### Find Matches

```http
POST /matching/find
```

**Scopes:** `read:candidates`

**Request Body:**
```json
{
  "vacancy_id": "vacancy_uuid",
  "limit": 10,
  "min_score": 70
}
```

**Response (200):**
```json
{
  "matches": [
    {
      "candidate_id": "uuid1",
      "score": 92.5,
      "name": "Jane Smith",
      "matched_skills": ["Python", "FastAPI"],
      "experience_match": true
    }
  ]
}
```

---

## Webhooks

Manage webhook subscriptions for real-time events.

For detailed webhook documentation, see [Webhooks Guide](./webhooks.md).

### Create Subscription

```http
POST /webhooks/subscribe
```

**Scopes:** `write:webhooks`

**Request Body:**
```json
{
  "url": "https://your-app.com/webhooks",
  "events": ["candidate.created", "stage.changed"],
  "secret": "optional_hmac_secret"
}
```

### List Subscriptions

```http
GET /webhooks
```

**Scopes:** `read:webhooks`

### Delete Subscription

```http
DELETE /webhooks/{subscription_id}
```

**Scopes:** `delete:webhooks`

---

## Workflows

Manage workflow automations.

### Create Workflow

```http
POST /workflows
```

**Scopes:** `write:workflows`

**Request Body:**
```json
{
  "name": "New Candidate Notification",
  "description": "Send Slack notification when candidate is created",
  "trigger_type": "webhook",
  "trigger_config": {
    "event": "candidate.created"
  },
  "actions": [
    {
      "type": "send_slack",
      "channel": "#recruiting",
      "message": "New candidate: {{candidate.name}}"
    }
  ]
}
```

### List Workflows

```http
GET /workflows
```

**Scopes:** `read:workflows`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | Filter by status (active, paused, draft) |
| is_active | boolean | Filter by active status |

### Execute Workflow

```http
POST /workflows/{workflow_id}/execute
```

**Scopes:** `write:workflows`

**Request Body:**
```json
{
  "trigger_data": {}
}
```

---

## Plugins

Plugin marketplace and management.

### List Plugins

```http
GET /plugins
```

**Scopes:** `read:plugins`

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| category | string | Filter by category |
| is_official | boolean | Show only official plugins |
| search | string | Search in name/description |

**Response (200):**
```json
{
  "items": [
    {
      "id": "plugin_uuid",
      "name": "Slack Integration",
      "slug": "slack-integration",
      "version": "1.2.0",
      "category": "integration",
      "description": "Send notifications to Slack",
      "author": "AgentHR",
      "is_official": true,
      "install_count": 1250,
      "average_rating": 4.8
    }
  ]
}
```

### Install Plugin

```http
POST /plugins/{plugin_id}/install
```

**Scopes:** `write:plugins`

**Request Body:**
```json
{
  "config": {
    "slack_webhook_url": "https://hooks.slack.com/..."
  }
}
```

### Uninstall Plugin

```http
DELETE /plugins/{installation_id}
```

**Scopes:** `delete:plugins`

---

## API Keys

Manage API keys for programmatic access.

### Generate API Key

```http
POST /api-keys/generate
```

**Scopes:** `write:api_keys`

**Request Body:**
```json
{
  "name": "Production Integration",
  "scopes": ["read:candidates", "write:candidates"],
  "rate_limit": {
    "requests_per_minute": 60
  }
}
```

**Response (201):**
```json
{
  "id": "key_uuid",
  "name": "Production Integration",
  "api_key": "aghr_1a2b3c4d...",
  "scopes": ["read:candidates", "write:candidates"]
}
```

### List API Keys

```http
GET /api-keys/
```

**Scopes:** `read:api_keys`

### Revoke API Key

```http
POST /api-keys/{key_id}/revoke
```

**Scopes:** `delete:api_keys`

---

## Error Codes

| Code | Description |
|------|-------------|
| `INVALID_API_KEY` | API key is invalid or revoked |
| `KEY_EXPIRED` | API key has expired |
| `INSUFFICIENT_SCOPES` | API key lacks required permissions |
| `RATE_LIMIT_EXCEEDED` | Rate limit has been exceeded |
| `INVALID_REQUEST` | Request body validation failed |
| `NOT_FOUND` | Resource not found |
| `DUPLICATE_RESOURCE` | Resource already exists |

---

## SDK Examples

### Python

```python
from agenthr import Client

client = Client(api_key="your_api_key")

# List candidates
candidates = client.candidates.list(limit=10)

# Create vacancy
vacancy = client.vacancies.create(
    title="Senior Python Developer",
    required_skills=["Python", "FastAPI"]
)

# Upload resume
resume = client.resumes.upload(
    file="resume.pdf",
    vacancy_id=vacancy.id
)
```

### JavaScript

```javascript
const { AgentHRClient } = require('@agenthr/sdk');

const client = new AgentHRClient({
  apiKey: 'your_api_key'
});

// List candidates
const candidates = await client.candidates.list({ limit: 10 });

// Create vacancy
const vacancy = await client.vacancies.create({
  title: 'Senior Python Developer',
  requiredSkills: ['Python', 'FastAPI']
});
```

For more information:
- [Authentication Guide](./authentication.md)
- [Webhooks Guide](./webhooks.md)
- [Code Examples](../examples/)
