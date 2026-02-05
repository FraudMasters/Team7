# Taxonomy Service API Documentation

## Overview

The Taxonomy Service manages skill taxonomies, synonyms, classifications, and import/export operations. It provides a centralized system for defining and managing skill definitions across different industries.

## Base URL

```
http://localhost:8005
```

Via API Gateway:
```
http://localhost:8888/api/skill-taxonomies
```

## Authentication

All endpoints require JWT authentication via the API Gateway. Include the `Authorization` header with your Bearer token:

```
Authorization: Bearer <your-jwt-token>
```

---

## Endpoints

### Create Skill Taxonomies

Create skill taxonomy entries for an industry.

**Endpoint:** `POST /api/skill-taxonomies/`

**Request Body:**
```json
{
  "industry": "technology",
  "skills": [
    {
      "name": "Python",
      "context": "programming_language",
      "variants": ["Python 3", "Python3", "py"],
      "extra_metadata": {
        "description": "General-purpose programming language",
        "category": "backend",
        "popularity": "high"
      },
      "is_active": true
    },
    {
      "name": "Django",
      "context": "web_framework",
      "variants": ["Django Framework", "Django REST Framework"],
      "extra_metadata": {
        "description": "Python web framework",
        "category": "backend"
      },
      "is_active": true
    }
  ]
}
```

**Response:** `201 Created`

```json
{
  "industry": "technology",
  "skills": [
    {
      "id": "taxonomy-1",
      "industry": "technology",
      "skill_name": "Python",
      "context": "programming_language",
      "variants": ["Python 3", "Python3", "py"],
      "extra_metadata": {
        "description": "General-purpose programming language",
        "category": "backend",
        "popularity": "high"
      },
      "is_active": true,
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total_count": 1
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `industry` | string | Yes | Industry sector (tech, healthcare, finance, etc.) |
| `skills` | array | Yes | List of skill taxonomy entries |
| `name` | string | Yes | Canonical name of the skill |
| `context` | string | No | Context category (web_framework, database, language, etc.) |
| `variants` | array | No | Alternative names/spellings for the skill |
| `extra_metadata` | object | No | Additional skill metadata |
| `is_active` | boolean | No | Whether entry is active (default: true) |

---

### List Skill Taxonomies

List skill taxonomy entries with optional filters.

**Endpoint:** `GET /api/skill-taxonomies/`

**Query Parameters:**
- `industry` (optional) - Filter by industry sector
- `is_active` (optional) - Filter by active status
- `context` (optional) - Filter by context category
- `search` (optional) - Search by skill name or variant

**Response:** `200 OK`

```json
{
  "total": 150,
  "skills": [
    {
      "id": "taxonomy-1",
      "industry": "technology",
      "skill_name": "Python",
      "context": "programming_language",
      "variants": ["Python 3", "Python3"],
      "extra_metadata": {...},
      "is_active": true,
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

**Example:**
```bash
# Get all active skills for technology industry
curl -X GET "http://localhost:8888/api/skill-taxonomies/?industry=technology&is_active=true" \
  -H "Authorization: Bearer <token>"

# Search for skills
curl -X GET "http://localhost:8888/api/skill-taxonomies/?search=Python" \
  -H "Authorization: Bearer <token>"
```

---

### Get Skill Taxonomy

Retrieve a specific skill taxonomy entry.

**Endpoint:** `GET /api/skill-taxonomies/{taxonomy_id}`

**Path Parameters:**
- `taxonomy_id` (required) - UUID of the taxonomy entry

**Response:** `200 OK`

```json
{
  "id": "taxonomy-1",
  "industry": "technology",
  "skill_name": "Python",
  "context": "programming_language",
  "variants": ["Python 3", "Python3", "py"],
  "extra_metadata": {...},
  "is_active": true,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

---

### Update Skill Taxonomy

Update an existing skill taxonomy entry.

**Endpoint:** `PUT /api/skill-taxonomies/{taxonomy_id}`

**Path Parameters:**
- `taxonomy_id` (required) - UUID of the taxonomy entry

**Request Body:**
```json
{
  "skill_name": "Python 3",
  "context": "programming_language",
  "variants": ["Python", "Python3", "py", "Python 3.x"],
  "extra_metadata": {
    "description": "Updated description",
    "category": "backend"
  },
  "is_active": true
}
```

**Response:** `200 OK`

Returns the updated taxonomy entry.

---

### Delete Skill Taxonomy

Delete a skill taxonomy entry.

**Endpoint:** `DELETE /api/skill-taxonomies/{taxonomy_id}`

**Path Parameters:**
- `taxonomy_id` (required) - UUID of the taxonomy entry

**Response:** `204 No Content`

---

## Custom Synonyms Endpoints

### Create Custom Synonyms

Create custom synonym mappings for an organization.

**Endpoint:** `POST /api/custom-synonyms`

**Request Body:**
```json
{
  "organization_id": "org-123",
  "synonyms": [
    {
      "canonical_name": "React.js",
      "variants": ["React", "ReactJS", "React JS"]
    },
    {
      "canonical_name": "PostgreSQL",
      "variants": ["Postgres", "psql"]
    }
  ]
}
```

**Response:** `201 Created`

---

### Get Custom Synonyms

Get custom synonym mappings for an organization.

**Endpoint:** `GET /api/custom-synonyms/{organization_id}`

**Path Parameters:**
- `organization_id` (required) - Organization ID

**Response:** `200 OK`

```json
{
  "organization_id": "org-123",
  "synonyms": [
    {
      "canonical_name": "React.js",
      "variants": ["React", "ReactJS", "React JS"]
    }
  ]
}
```

---

## Import/Export Endpoints

### Export Taxonomy

Export skill taxonomy to JSON format.

**Endpoint:** `GET /api/taxonomy-import-export/export`

**Query Parameters:**
- `industry` (optional) - Filter by industry
- `format` (optional, default: "json") - Export format (json, csv)

**Response:** `200 OK`

```json
{
  "industry": "technology",
  "export_date": "2025-01-15T10:30:00Z",
  "skills": [
    {
      "skill_name": "Python",
      "context": "programming_language",
      "variants": [...],
      "metadata": {...}
    }
  ]
}
```

**Example:**
```bash
curl -X GET "http://localhost:8888/api/taxonomy-import-export/export?industry=technology" \
  -H "Authorization: Bearer <token>" \
  -o taxonomy_export.json
```

---

### Import Taxonomy

Import skill taxonomy from JSON format.

**Endpoint:** `POST /api/taxonomy-import-export/import`

**Request Body:**
```json
{
  "industry": "technology",
  "format": "json",
  "data": [
    {
      "skill_name": "Python",
      "context": "programming_language",
      "variants": ["Python 3", "py"],
      "metadata": {}
    }
  ],
  "merge_strategy": "replace"
}
```

**Merge Strategies:**
- `replace` - Replace all existing entries
- `merge` - Merge with existing entries (update if exists, create if not)
- `skip` - Skip existing entries, only create new

**Response:** `201 Created`

```json
{
  "imported": 50,
  "updated": 10,
  "skipped": 5,
  "failed": 0
}
```

---

## Data Models

### Context Categories

| Category | Description | Examples |
|----------|-------------|----------|
| `programming_language` | Programming languages | Python, Java, Go |
| `web_framework` | Web frameworks | Django, Express, Spring |
| `database` | Databases | PostgreSQL, MongoDB, Redis |
| `cloud_platform` | Cloud platforms | AWS, GCP, Azure |
| `devops_tool` | DevOps tools | Docker, Kubernetes, Jenkins |
| `frontend` | Frontend technologies | React, Vue, Angular |
| `testing` | Testing frameworks | pytest, Jest, Selenium |
| `build_tool` | Build tools | Maven, Gradle, npm |
| `orm` | ORMs | SQLAlchemy, Hibernate, EF |
| `concept` | General concepts | REST, GraphQL, Microservices |

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
- `404 Not Found` - Taxonomy entry not found
- `409 Conflict` - Duplicate entry
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

---

## Rate Limiting

Via API Gateway:
- 100 requests per second
- 10,000 requests per hour

---

## gRPC Service

The Taxonomy Service also exposes a gRPC interface on port `50055`.

**Available RPC Methods:**
- `CreateSkillTaxonomy` - Create skill taxonomy entry
- `GetSkillTaxonomy` - Get taxonomy entry by ID
- `ListSkillTaxonomies` - List entries with filters
- `UpdateSkillTaxonomy` - Update taxonomy entry
- `DeleteSkillTaxonomy` - Delete taxonomy entry
- `SearchSkills` - Search skills by name/variant
- `GetSkillSynonyms` - Get synonyms for a skill
- `ImportTaxonomy` - Import taxonomy data
- `ExportTaxonomy` - Export taxonomy data

See `protos/taxonomy.proto` for the complete service definition.
