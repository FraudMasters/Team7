# Candidate Service API Documentation

## Overview

The Candidate Service manages all candidate-related operations including CRUD operations, notes, tags, activities, and status tracking. It provides endpoints for managing the hiring pipeline from initial contact through hiring.

## Base URL

```
http://localhost:8003
```

Via API Gateway:
```
http://localhost:8888/api/candidates
```

## Authentication

All endpoints require JWT authentication via the API Gateway. Include the `Authorization` header with your Bearer token:

```
Authorization: Bearer <your-jwt-token>
```

---

## Endpoints

### List Candidates

Get a paginated list of candidates with filtering support.

**Endpoint:** `GET /api/candidates/`

**Query Parameters:**
- `status_filter` (optional) - Filter by CandidateStatus enum (NEW, INTERVIEW, HIRED, etc.)
- `search` (optional) - Search by name or email
- `is_active` (optional, default: true) - Filter by active status
- `skip` (optional, default: 0) - Records to skip for pagination
- `limit` (optional, default: 100, max: 200) - Maximum records to return

**Response:** `200 OK`

```json
{
  "total": 150,
  "candidates": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "full_name": "Ivan Ivanov",
      "email": "ivan@example.com",
      "current_position": "Senior Python Developer",
      "current_company": "Tech Corp",
      "status": "INTERVIEW",
      "rating": 5,
      "tags": [
        {
          "id": "tag-1",
          "tag_name": "Senior Level",
          "color": "#FF5722"
        }
      ],
      "notes_count": 3,
      "latest_activity": {
        "activity_type": "stage_changed",
        "created_at": "2025-01-15T10:30:00Z"
      },
      "created_at": "2025-01-10T09:00:00Z",
      "updated_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

**Example:**
```bash
# Get all active candidates
curl -X GET "http://localhost:8888/api/candidates/" \
  -H "Authorization: Bearer <token>"

# Filter by status
curl -X GET "http://localhost:8888/api/candidates/?status_filter=INTERVIEW" \
  -H "Authorization: Bearer <token>"

# Search by name
curl -X GET "http://localhost:8888/api/candidates/?search=Ivan" \
  -H "Authorization: Bearer <token>"
```

---

### Get Candidate Details

Retrieve detailed information about a specific candidate.

**Endpoint:** `GET /api/candidates/{candidate_id}`

**Path Parameters:**
- `candidate_id` (required) - UUID of the candidate

**Response:** `200 OK`

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "full_name": "Ivan Ivanov",
  "email": "ivan@example.com",
  "phone": "+7 999 123 4567",
  "current_position": "Senior Python Developer",
  "current_company": "Tech Corp",
  "status": "INTERVIEW",
  "rating": 5,
  "tags": [...],
  "notes_count": 3,
  "latest_activity": {...},
  "years_of_experience": 7,
  "expected_salary": "250000-300000 RUB",
  "location": "Moscow, Russia",
  "linkedin_url": "https://linkedin.com/in/ivanivanov",
  "portfolio_url": "https://github.com/ivanivanov",
  "source": "LinkedIn",
  "is_active": true,
  "resume_id": "resume-abc-123",
  "created_at": "2025-01-10T09:00:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

**Errors:**
- `404 Not Found` - Candidate not found
- `422 Unprocessable Entity` - Invalid candidate ID format

---

### Create Candidate

Create a new candidate profile.

**Endpoint:** `POST /api/candidates/`

**Request Body:**
```json
{
  "resume_id": "resume-abc-123",
  "full_name": "Ivan Ivanov",
  "email": "ivan@example.com",
  "phone": "+7 999 123 4567",
  "current_position": "Senior Python Developer",
  "current_company": "Tech Corp",
  "years_of_experience": 7,
  "expected_salary": "250000-300000 RUB",
  "location": "Moscow, Russia",
  "linkedin_url": "https://linkedin.com/in/ivanivanov",
  "portfolio_url": "https://github.com/ivanivanov",
  "source": "LinkedIn",
  "status": "NEW"
}
```

**Response:** `201 Created`

Returns the created candidate object (same format as Get Candidate Details).

**Notes:**
- If a candidate already exists for the given resume_id, the existing candidate will be reactivated
- An activity record is automatically created when a candidate is created

---

### Update Candidate

Update candidate information.

**Endpoint:** `PUT /api/candidates/{candidate_id}`

**Path Parameters:**
- `candidate_id` (required) - UUID of the candidate

**Request Body:**
```json
{
  "full_name": "Ivan Ivanovich",
  "rating": 5,
  "expected_salary": "300000-350000 RUB"
}
```

**Response:** `200 OK`

Returns the updated candidate object.

---

### Delete Candidate

Soft delete a candidate (sets is_active=False).

**Endpoint:** `DELETE /api/candidates/{candidate_id}`

**Path Parameters:**
- `candidate_id` (required) - UUID of the candidate

**Response:** `204 No Content`

**Note:** This is a soft delete - the record is not removed from the database, just marked as inactive.

---

### Update Candidate Status

Update candidate status for Kanban board workflow.

**Endpoint:** `PATCH /api/candidates/{candidate_id}/status`

**Path Parameters:**
- `candidate_id` (required) - UUID of the candidate

**Request Body:**
```json
{
  "status": "INTERVIEW",
  "reason": "Passed initial screening"
}
```

**Valid Status Values:**
- `NEW` - New candidate
- `SCREENING` - Under screening
- `INTERVIEW` - Interview scheduled
- `OFFER` - Offer made
- `HIRED` - Candidate hired
- `REJECTED` - Candidate rejected
- `WITHDRAWN` - Candidate withdrew

**Response:** `200 OK`

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "previous_status": "SCREENING",
  "new_status": "INTERVIEW",
  "message": "Candidate status updated successfully"
}
```

---

## Notes Endpoints

### Create Note

Create a note for a candidate.

**Endpoint:** `POST /api/candidate-notes/`

**Request Body:**
```json
{
  "candidate_id": "candidate-123",
  "content": "Excellent technical skills, good cultural fit",
  "is_private": false,
  "is_pinned": true
}
```

**Response:** `201 Created`

```json
{
  "id": "note-456",
  "candidate_id": "candidate-123",
  "recruiter_id": "recruiter-789",
  "content": "Excellent technical skills, good cultural fit",
  "is_private": false,
  "is_pinned": true,
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

### List Notes

Get notes with filtering support.

**Endpoint:** `GET /api/candidate-notes/`

**Query Parameters:**
- `candidate_id` (optional) - Filter by candidate ID
- `is_private` (optional) - Filter by private status
- `is_pinned` (optional) - Filter by pinned status
- `recruiter_id` (optional) - Filter by recruiter ID
- `skip` (optional) - Records to skip
- `limit` (optional) - Maximum records to return

---

### Update Note

Update an existing note.

**Endpoint:** `PUT /api/candidate-notes/{note_id}`

**Request Body:**
```json
{
  "content": "Updated note content",
  "is_pinned": false
}
```

---

### Delete Note

Delete a note.

**Endpoint:** `DELETE /api/candidate-notes/{note_id}`

**Response:** `204 No Content`

---

## Tags Endpoints

### Create Tag

Create a new tag for organization-wide use.

**Endpoint:** `POST /api/candidate-tags/`

**Request Body:**
```json
{
  "tag_name": "Senior Level",
  "color": "#FF5722",
  "description": "Senior level candidates"
}
```

**Response:** `201 Created`

```json
{
  "id": "tag-1",
  "tag_name": "Senior Level",
  "color": "#FF5722",
  "description": "Senior level candidates",
  "created_at": "2025-01-15T10:00:00Z"
}
```

---

### List Tags

Get all tags with optional filtering.

**Endpoint:** `GET /api/candidate-tags/`

**Query Parameters:**
- `is_active` (optional) - Filter by active status

---

### Get Candidate Tags

Get tags assigned to a specific candidate.

**Endpoint:** `GET /api/candidate-tags/candidate/{candidate_id}`

---

### Assign Tag to Candidate

Assign a tag to a candidate.

**Endpoint:** `POST /api/candidate-tags/candidate/{candidate_id}/assign`

**Request Body:**
```json
{
  "tag_id": "tag-1"
}
```

---

### Remove Tag from Candidate

Remove a tag from a candidate.

**Endpoint:** `DELETE /api/candidate-tags/candidate/{candidate_id}/tags/{tag_id}`

---

## Activities Endpoints

### Get Activity Timeline

Get the activity timeline for candidates.

**Endpoint:** `GET /api/candidate-activities/`

**Query Parameters:**
- `candidate_id` (optional) - Filter by candidate ID
- `activity_type` (optional) - Filter by activity type
- `skip` (optional) - Records to skip
- `limit` (optional) - Maximum records to return

**Response:** `200 OK`

```json
{
  "total": 25,
  "activities": [
    {
      "id": "activity-1",
      "activity_type": "stage_changed",
      "candidate_id": "candidate-123",
      "recruiter_id": "recruiter-789",
      "from_stage": "SCREENING",
      "to_stage": "INTERVIEW",
      "reason": "Passed technical interview",
      "created_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

---

### Get Activity Types

List all available activity types.

**Endpoint:** `GET /api/candidate-activities/types`

**Response:** `200 OK`

```json
{
  "activity_types": [
    "status_updated",
    "stage_changed",
    "note_created",
    "tag_assigned",
    "contact_made"
  ]
}
```

---

## Data Models

### CandidateStatus Enum

| Status | Description |
|--------|-------------|
| `NEW` | New candidate |
| `SCREENING` | Under screening |
| `INTERVIEW` | Interview stage |
| `OFFER` | Offer made |
| `HIRED` | Candidate hired |
| `REJECTED` | Candidate rejected |
| `WITHDRAWN` | Candidate withdrew |

### CandidateActivityType Enum

| Type | Description |
|------|-------------|
| `STATUS_UPDATED` | Candidate status was updated |
| `STAGE_CHANGED` | Hiring stage changed |
| `NOTE_CREATED` | Note was created |
| `NOTE_UPDATED` | Note was updated |
| `TAG_ASSIGNED` | Tag was assigned |
| `TAG_REMOVED` | Tag was removed |
| `CONTACT_MADE` | Contact was made with candidate |

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
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

---

## Rate Limiting

Via API Gateway:
- 100 requests per second
- 10,000 requests per hour

---

## gRPC Service

The Candidate Service also exposes a gRPC interface on port `50053`.

**Available RPC Methods:**
- `CreateNote` - Create candidate note
- `GetNotes` - Get candidate notes
- `UpdateNote` - Update note
- `DeleteNote` - Delete note
- `CreateTag` - Create tag
- `GetTags` - Get tags
- `UpdateTag` - Update tag
- `DeleteTag` - Delete tag
- `AddTagToResume` - Assign tag to candidate
- `RemoveTagFromResume` - Remove tag from candidate
- `GetResumeTags` - Get candidate tags
- `LogActivity` - Log activity
- `GetActivities` - Get activities
- `UpdateStatus` - Update status
- `GetStatus` - Get status
- `AddFeedback` - Add feedback
- `GetFeedback` - Get feedback

See `protos/candidate.proto` for the complete service definition.
