# Vacancy Service API Documentation

## Overview

The Vacancy Service manages all job vacancy operations including CRUD operations, bulk operations, and database storage for job postings. It provides endpoints for creating, viewing, updating, and deleting vacancies.

## Base URL

```
http://localhost:8004
```

Via API Gateway:
```
http://localhost:8888/api/vacancies
```

## Authentication

All endpoints require JWT authentication via the API Gateway. Include the `Authorization` header with your Bearer token:

```
Authorization: Bearer <your-jwt-token>
```

---

## Endpoints

### Create Vacancy

Create a new job vacancy.

**Endpoint:** `POST /api/vacancies/`

**Request Body:**
```json
{
  "title": "Senior Python Developer",
  "description": "We are looking for an experienced Python developer to join our team...",
  "required_skills": ["Python", "Django", "PostgreSQL", "Docker"],
  "min_experience_months": 36,
  "additional_requirements": ["Kubernetes", "Redis"],
  "industry": "Technology",
  "work_format": "remote",
  "location": "Remote",
  "salary_min": 250000,
  "salary_max": 350000,
  "english_level": "B2+",
  "employment_type": "full-time",
  "external_id": "EXT-12345",
  "source": "manual"
}
```

**Response:** `201 Created`

```json
{
  "id": "vacancy-123",
  "title": "Senior Python Developer",
  "description": "We are looking for an experienced Python developer...",
  "required_skills": ["Python", "Django", "PostgreSQL", "Docker"],
  "min_experience_months": 36,
  "additional_requirements": ["Kubernetes", "Redis"],
  "industry": "Technology",
  "work_format": "remote",
  "location": "Remote",
  "salary_min": 250000,
  "salary_max": 350000,
  "english_level": "B2+",
  "employment_type": "full-time",
  "external_id": "EXT-12345",
  "source": "manual",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Job title (3-255 characters) |
| `description` | string | Yes | Job description (min 10 characters) |
| `required_skills` | array | Yes | List of required technical skills (min 1 item) |
| `min_experience_months` | integer | No | Minimum experience required in months |
| `additional_requirements` | array | No | Preferred/desirable skills |
| `industry` | string | No | Industry sector (max 100 characters) |
| `work_format` | string | No | Work format: remote, office, hybrid |
| `location` | string | No | Job location (max 255 characters) |
| `salary_min` | integer | No | Minimum salary |
| `salary_max` | integer | No | Maximum salary |
| `english_level` | string | No | Required English level |
| `employment_type` | string | No | Type: full-time, part-time, contract |
| `external_id` | string | No | External system ID |
| `source` | string | No | Source of vacancy (default: "manual") |

**Example:**
```bash
curl -X POST "http://localhost:8888/api/vacancies/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Python Developer",
    "description": "We are looking for...",
    "required_skills": ["Python", "Django"],
    "min_experience_months": 36
  }'
```

---

### List Vacancies

Get a paginated list of all vacancies.

**Endpoint:** `GET /api/vacancies/`

**Query Parameters:**
- `skip` (optional, default: 0) - Number of records to skip
- `limit` (optional, default: 100) - Maximum records to return
- `industry` (optional) - Filter by industry
- `work_format` (optional) - Filter by work format
- `location` (optional) - Filter by location

**Response:** `200 OK`

```json
[
  {
    "id": "vacancy-123",
    "title": "Senior Python Developer",
    "description": "We are looking for...",
    "required_skills": ["Python", "Django", "PostgreSQL"],
    "min_experience_months": 36,
    "additional_requirements": ["Kubernetes", "Redis"],
    "industry": "Technology",
    "work_format": "remote",
    "location": "Remote",
    "salary_min": 250000,
    "salary_max": 350000,
    "english_level": "B2+",
    "employment_type": "full-time",
    "external_id": "EXT-12345",
    "source": "manual",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z"
  }
]
```

**Example:**
```bash
# Get all vacancies
curl -X GET "http://localhost:8888/api/vacancies/" \
  -H "Authorization: Bearer <token>"

# Filter by work format
curl -X GET "http://localhost:8888/api/vacancies/?work_format=remote" \
  -H "Authorization: Bearer <token>"

# Get vacancies with pagination
curl -X GET "http://localhost:8888/api/vacancies/?skip=0&limit=20" \
  -H "Authorization: Bearer <token>"
```

---

### Get Vacancy Details

Retrieve detailed information about a specific vacancy.

**Endpoint:** `GET /api/vacancies/{vacancy_id}`

**Path Parameters:**
- `vacancy_id` (required) - UUID of the vacancy

**Response:** `200 OK`

```json
{
  "id": "vacancy-123",
  "title": "Senior Python Developer",
  "description": "We are looking for an experienced Python developer...",
  "required_skills": ["Python", "Django", "PostgreSQL", "Docker"],
  "min_experience_months": 36,
  "additional_requirements": ["Kubernetes", "Redis"],
  "industry": "Technology",
  "work_format": "remote",
  "location": "Remote",
  "salary_min": 250000,
  "salary_max": 350000,
  "english_level": "B2+",
  "employment_type": "full-time",
  "external_id": "EXT-12345",
  "source": "manual",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

**Errors:**
- `404 Not Found` - Vacancy not found
- `422 Unprocessable Entity` - Invalid vacancy ID format

**Example:**
```bash
curl -X GET "http://localhost:8888/api/vacancies/vacancy-123" \
  -H "Authorization: Bearer <token>"
```

---

### Update Vacancy

Update an existing vacancy.

**Endpoint:** `PUT /api/vacancies/{vacancy_id}`

**Path Parameters:**
- `vacancy_id` (required) - UUID of the vacancy

**Request Body:**
```json
{
  "title": "Lead Python Developer",
  "description": "Updated job description...",
  "salary_min": 300000,
  "salary_max": 400000
}
```

**Response:** `200 OK`

Returns the updated vacancy object (same format as Get Vacancy Details).

**Note:** Only include the fields you want to update. Omitted fields will remain unchanged.

**Example:**
```bash
curl -X PUT "http://localhost:8888/api/vacancies/vacancy-123" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Lead Python Developer",
    "salary_min": 300000
  }'
```

---

### Delete Vacancy

Delete a vacancy.

**Endpoint:** `DELETE /api/vacancies/{vacancy_id}`

**Path Parameters:**
- `vacancy_id` (required) - UUID of the vacancy

**Response:** `204 No Content`

**Example:**
```bash
curl -X DELETE "http://localhost:8888/api/vacancies/vacancy-123" \
  -H "Authorization: Bearer <token>"
```

---

### Bulk Create Vacancies

Create multiple vacancies in a single request.

**Endpoint:** `POST /api/vacancies/bulk`

**Request Body:**
```json
{
  "vacancies": [
    {
      "title": "Senior Python Developer",
      "description": "...",
      "required_skills": ["Python", "Django"]
    },
    {
      "title": "Java Developer",
      "description": "...",
      "required_skills": ["Java", "Spring"]
    }
  ]
}
```

**Response:** `201 Created`

```json
{
  "created": 2,
  "failed": 0,
  "vacancies": [
    {
      "id": "vacancy-123",
      "title": "Senior Python Developer",
      ...
    },
    {
      "id": "vacancy-124",
      "title": "Java Developer",
      ...
    }
  ]
}
```

---

### Bulk Update Vacancies

Update multiple vacancies in a single request.

**Endpoint:** `PUT /api/vacancies/bulk`

**Request Body:**
```json
{
  "vacancy_ids": ["vacancy-123", "vacancy-124"],
  "updates": {
    "salary_min": 300000,
    "location": "Remote"
  }
}
```

**Response:** `200 OK`

```json
{
  "updated": 2,
  "failed": 0,
  "vacancies": [...]
}
```

---

### Bulk Delete Vacancies

Delete multiple vacancies in a single request.

**Endpoint:** `DELETE /api/vacancies/bulk`

**Request Body:**
```json
{
  "vacancy_ids": ["vacancy-123", "vacancy-124"]
}
```

**Response:** `200 OK`

```json
{
  "deleted": 2,
  "failed": 0
}
```

---

## Data Models

### Employment Type Values

| Value | Description |
|-------|-------------|
| `full-time` | Full-time employment |
| `part-time` | Part-time employment |
| `contract` | Contract/contractor role |
| `internship` | Internship position |

### Work Format Values

| Value | Description |
|-------|-------------|
| `remote` | Fully remote |
| `office` | On-site at office |
| `hybrid` | Hybrid remote/office |

### English Level Values

| Value | Description |
|-------|-------------|
| `A1` | Beginner |
| `A2` | Elementary |
| `B1` | Intermediate |
| `B2` | Upper Intermediate |
| `C1` | Advanced |
| `C2` | Proficient |
| `Native` | Native speaker |

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
- `404 Not Found` - Vacancy not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

---

## Rate Limiting

Via API Gateway:
- 100 requests per second
- 10,000 requests per hour

---

## gRPC Service

The Vacancy Service also exposes a gRPC interface on port `50054`.

**Available RPC Methods:**
- `CreateVacancy` - Create new vacancy
- `GetVacancy` - Get vacancy by ID
- `ListVacancies` - List vacancies with filters
- `UpdateVacancy` - Update vacancy
- `DeleteVacancy` - Delete vacancy
- `SearchVacancies` - Search vacancies by skills/keywords

See `protos/vacancy.proto` for the complete service definition.
