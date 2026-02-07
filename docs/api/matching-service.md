# Matching Service API Documentation

## Overview

The Matching Service provides intelligent skill matching between resumes and job vacancies. It uses advanced NLP techniques including context-aware matching, synonym handling, fuzzy matching, and vector similarity scoring to provide accurate match results.

## Base URL

```
http://localhost:8002
```

Via API Gateway:
```
http://localhost:8888/api/matching
```

## Authentication

All endpoints require JWT authentication via the API Gateway. Include the `Authorization` header with your Bearer token:

```
Authorization: Bearer <your-jwt-token>
```

---

## Endpoints

### Compare Resume to Vacancy

Compare a resume against a job vacancy with intelligent skill matching.

**Endpoint:** `POST /api/matching/compare`

**Request Body:**
```json
{
  "resume_id": "abc123-def456-789",
  "vacancy_data": {
    "title": "Java Developer",
    "required_skills": ["Java", "Spring", "SQL"],
    "additional_requirements": ["Docker", "Kubernetes"],
    "min_experience_months": 36
  }
}
```

**Response:** `200 OK`

```json
{
  "resume_id": "abc123-def456-789",
  "vacancy_title": "Java Developer",
  "match_percentage": 66.67,
  "required_skills_match": [
    {
      "skill": "Java",
      "status": "matched",
      "matched_as": "Java",
      "highlight": "green",
      "confidence": 1.0,
      "match_type": "direct"
    },
    {
      "skill": "Spring",
      "status": "matched",
      "matched_as": "Spring Boot",
      "highlight": "green",
      "confidence": 0.85,
      "match_type": "context"
    },
    {
      "skill": "SQL",
      "status": "matched",
      "matched_as": "PostgreSQL",
      "highlight": "green",
      "confidence": 0.75,
      "match_type": "synonym"
    }
  ],
  "additional_skills_match": [
    {
      "skill": "Docker",
      "status": "missing",
      "matched_as": null,
      "highlight": "red",
      "confidence": 0.0,
      "match_type": "none"
    }
  ],
  "experience_verification": {
    "required_months": 36,
    "actual_months": 47,
    "meets_requirement": true,
    "summary": "47 months (3 years 11 months) of experience"
  },
  "processing_time_ms": 123.45
}
```

**Features:**
- **Skill Synonym Matching**: PostgreSQL matches SQL requirement
- **Context-Aware Matching**: React.js ≈ React in web_framework context
- **Fuzzy Matching**: Handles typos and variations
- **Visual Highlighting**: green=matched, red=missing
- **Confidence Scoring**: 0.0 to 1.0 for all matches
- **Experience Verification**: Sums months across projects

**Example:**
```bash
curl -X POST "http://localhost:8888/api/matching/compare" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "abc123",
    "vacancy_data": {
      "title": "Java Developer",
      "required_skills": ["Java", "Spring", "SQL"],
      "min_experience_months": 36
    }
  }'
```

---

### Create Comparison View

Create a comparison view for 2-5 resumes side-by-side.

**Endpoint:** `POST /api/comparisons/`

**Request Body:**
```json
{
  "name": "Senior Developer Comparison",
  "vacancy_id": "vacancy-123",
  "resume_ids": ["resume-1", "resume-2", "resume-3"]
}
```

**Response:** `201 Created`

```json
{
  "id": "comp-456",
  "name": "Senior Developer Comparison",
  "vacancy_id": "vacancy-123",
  "resume_ids": ["resume-1", "resume-2", "resume-3"],
  "results": [
    {
      "resume_id": "resume-1",
      "match_score": 85.5,
      "rank": 1
    }
  ],
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

### List Comparisons

Get all comparison views with optional filtering.

**Endpoint:** `GET /api/comparisons/`

**Query Parameters:**
- `vacancy_id` (optional) - Filter by vacancy ID
- `limit` (optional, default: 50) - Maximum records to return
- `offset` (optional, default: 0) - Records to skip

**Response:** `200 OK`

```json
{
  "total": 10,
  "comparisons": [
    {
      "id": "comp-456",
      "name": "Senior Developer Comparison",
      "vacancy_id": "vacancy-123",
      "resume_count": 3,
      "created_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

---

### Get Comparison Details

Retrieve a specific comparison view with detailed results.

**Endpoint:** `GET /api/comparisons/{comparison_id}`

**Path Parameters:**
- `comparison_id` (required) - ID of the comparison

**Response:** `200 OK`

```json
{
  "id": "comp-456",
  "name": "Senior Developer Comparison",
  "vacancy_id": "vacancy-123",
  "resumes": [
    {
      "resume_id": "resume-1",
      "candidate_name": "John Doe",
      "match_score": 85.5,
      "skill_match": {
        "Java": "matched",
        "Spring": "matched",
        "SQL": "matched"
      }
    }
  ],
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

### Update Comparison

Update an existing comparison view.

**Endpoint:** `PUT /api/comparisons/{comparison_id}`

**Path Parameters:**
- `comparison_id` (required) - ID of the comparison

**Request Body:**
```json
{
  "name": "Updated Comparison Name",
  "add_resume_ids": ["resume-4"],
  "remove_resume_ids": ["resume-2"]
}
```

**Response:** `200 OK`

---

### Delete Comparison

Delete a comparison view.

**Endpoint:** `DELETE /api/comparisons/{comparison_id}`

**Path Parameters:**
- `comparison_id` (required) - ID of the comparison

**Response:** `204 No Content`

---

### Rank Candidates

Rank multiple candidates for a vacancy using weighted criteria.

**Endpoint:** `POST /api/ranking/rank`

**Request Body:**
```json
{
  "vacancy_id": "vacancy-123",
  "resume_ids": ["resume-1", "resume-2", "resume-3"],
  "weights": {
    "skill_match_weight": 0.5,
    "experience_weight": 0.3,
    "recency_weight": 0.2
  },
  "min_match_percentage": 50.0
}
```

**Response:** `200 OK`

```json
{
  "vacancy_id": "vacancy-123",
  "ranked_candidates": [
    {
      "resume_id": "resume-1",
      "rank": 1,
      "overall_score": 0.85,
      "skill_match_score": 0.90,
      "experience_score": 0.80,
      "recency_score": 0.75
    }
  ]
}
```

---

### Get Top Candidates

Get top N ranked candidates for a vacancy.

**Endpoint:** `GET /api/ranking/top-candidates/{vacancy_id}`

**Path Parameters:**
- `vacancy_id` (required) - ID of the vacancy

**Query Parameters:**
- `limit` (optional, default: 10) - Number of top candidates to return

**Response:** `200 OK`

```json
{
  "vacancy_id": "vacancy-123",
  "top_candidates": [
    {
      "resume_id": "resume-1",
      "rank": 1,
      "score": 0.85
    }
  ]
}
```

---

### Batch Compare

Compare multiple resumes against a vacancy at once.

**Endpoint:** `POST /api/comparisons/compare-multiple`

**Request Body:**
```json
{
  "vacancy_id": "vacancy-123",
  "resume_ids": ["resume-1", "resume-2", "resume-3"],
  "return_ranking": true
}
```

**Response:** `200 OK`

```json
{
  "vacancy_id": "vacancy-123",
  "results": [
    {
      "resume_id": "resume-1",
      "match_percentage": 85.5,
      "required_skills_match": [...],
      "additional_skills_match": [...]
    }
  ],
  "ranking": [
    {"resume_id": "resume-1", "rank": 1, "score": 85.5}
  ]
}
```

---

## Data Models

### Match Types

The matching service supports multiple match types:

| Match Type | Description | Confidence Range |
|------------|-------------|------------------|
| `direct` | Exact skill name match | 0.95 - 1.0 |
| `context` | Context-aware match (e.g., React ≈ React.js) | 0.75 - 0.95 |
| `synonym` | Synonym-based match (e.g., PostgreSQL ≈ SQL) | 0.60 - 0.85 |
| `fuzzy` | Fuzzy string match for typos | 0.50 - 0.80 |
| `none` | No match found | 0.0 |

### Skill Match Status

| Status | Description | Highlight Color |
|--------|-------------|-----------------|
| `matched` | Skill found in resume | green |
| `missing` | Skill not found | red |

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message",
  "type": "error_type"
}
```

Common HTTP status codes:
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Missing or invalid authentication
- `404 Not Found` - Resume file not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Matching service error

---

## Rate Limiting

Via API Gateway:
- 100 requests per second
- 10,000 requests per hour

---

## gRPC Service

The Matching Service also exposes a gRPC interface on port `50052`.

**Available RPC Methods:**
- `MatchResume` - Match resume with vacancy
- `BatchMatch` - Batch match multiple resumes
- `GetMatchResults` - Get paginated match results
- `AnalyzeSkillGap` - Analyze skill gaps
- `GetSkillGapReport` - Get skill gap report
- `CreateComparison` - Create resume comparison
- `GetComparison` - Get resume comparison
- `ListComparisons` - List comparisons
- `DeleteComparison` - Delete comparison

See `protos/matching.proto` for the complete service definition.

---

## Skill Synonyms Database

The service uses a comprehensive skill synonyms database organized by category:
- **Databases**: PostgreSQL, MySQL, MongoDB...
- **Programming Languages**: Python, Java, JavaScript, Go...
- **Web Frameworks**: Django, Flask, Express, Spring...
- **Frontend**: React, Vue, Angular...
- **DevOps**: Docker, Kubernetes, Jenkins...
- **Data Tools**: Pandas, NumPy, Spark...

Custom synonym mappings can be added via the Taxonomy Service.
