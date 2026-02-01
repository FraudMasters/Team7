# AgentHR Backend API Reference

Complete API reference documentation for the AgentHR Recruitment Automation Platform backend.

**Base URL:** `http://localhost:8000` (development)

**API Version:** 1.0.0

**Content-Type:** `application/json`

---

## Table of Contents

1. [Authentication](#authentication)
2. [Resumes](#resumes)
3. [Resume Analysis](#resume-analysis)
4. [Job Matching](#job-matching)
5. [Candidates](#candidates)
6. [Vacancies](#vacancies)
7. [Search](#search)
8. [Comparisons](#comparisons)
9. [Candidate Notes](#candidate-notes)
10. [Candidate Tags](#candidate-tags)
11. [Workflow Stages](#workflow-stages)
12. [Skill Taxonomies](#skill-taxonomies)
13. [Custom Synonyms](#custom-synonyms)
14. [Reports](#reports)
15. [Model Versions](#model-versions)
16. [Matching Weights](#matching-weights)
17. [Feedback](#feedback)
18. [Ranking](#ranking)
19. [Skill Gap Analysis](#skill-gap-analysis)
20. [Batch Operations](#batch-operations)

---

## Authentication

All API requests must include the `Accept-Language` header for internationalization support.

**Headers:**
```http
Accept-Language: en | ru
```

---

## Resumes

Upload and manage resume files (PDF, DOCX).

### Upload Resume

**Endpoint:** `POST /api/resumes/upload`

**Request:** `multipart/form-data`
- `file`: Resume file (PDF or DOCX, max 10MB)

**Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "resume.pdf",
  "status": "processing",
  "message": "Resume uploaded successfully"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/resumes/upload \
  -F 'file=@resume.pdf' \
  -H 'Accept-Language: en'
```

---

### Get All Resumes

**Endpoint:** `GET /api/resumes/`

**Query Parameters:**
- `skip` (optional): Number of results to skip (default: 0)
- `limit` (optional): Maximum results to return (default: 100, max: 200)

**Response:** `200 OK`
```json
{
  "total": 150,
  "resumes": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "resume.pdf",
      "status": "completed",
      "created_at": "2026-01-15T10:30:00Z",
      "language": "en"
    }
  ]
}
```

---

### Get Resume by ID

**Endpoint:** `GET /api/resumes/{resume_id}`

**Path Parameters:**
- `resume_id`: Resume UUID

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "resume.pdf",
  "status": "completed",
  "file_path": "/data/uploads/resume.pdf",
  "created_at": "2026-01-15T10:30:00Z",
  "updated_at": "2026-01-15T10:35:00Z",
  "language": "en"
}
```

---

### Delete Resume

**Endpoint:** `DELETE /api/resumes/{resume_id}`

**Path Parameters:**
- `resume_id`: Resume UUID

**Response:** `204 No Content`

---

### List Resume Stages

**Endpoint:** `GET /api/resumes/stages`

**Response:** `200 OK`
```json
{
  "stages": [
    {"id": "applied", "name": "Applied"},
    {"id": "screening", "name": "Screening"},
    {"id": "interview", "name": "Interview"},
    {"id": "offer", "name": "Offer"},
    {"id": "hired", "name": "Hired"},
    {"id": "rejected", "name": "Rejected"}
  ]
}
```

---

## Resume Analysis

Analyze resumes using ML/NLP for keyword extraction, NER, grammar checking, and experience calculation.

### Analyze Resume

**Endpoint:** `POST /api/resumes/analyze`

**Request:**
```json
{
  "resume_id": "550e8400-e29b-41d4-a716-446655440000",
  "extract_experience": true,
  "check_grammar": true
}
```

**Response:** `200 OK`
```json
{
  "resume_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "keyword_analysis": {
    "keywords": ["Python", "Django", "PostgreSQL"],
    "keyphrases": "machine learning engineer",
    "scores": [0.95, 0.88, 0.82]
  },
  "entity_analysis": {
    "organizations": ["Google", "Microsoft"],
    "dates": ["2020-01", "2023-12"],
    "persons": ["John Smith"],
    "locations": ["San Francisco", "New York"],
    "technical_skills": ["Python", "TensorFlow", "Keras"]
  },
  "grammar_analysis": {
    "total_errors": 3,
    "errors_by_category": {
      "spelling": 1,
      "grammar": 2,
      "punctuation": 0
    },
    "errors": [
      {
        "type": "spelling",
        "severity": "warning",
        "message": "Possible spelling mistake",
        "context": "recieved",
        "suggestions": ["received"],
        "position": {"line": 5, "column": 12}
      }
    ]
  },
  "experience_analysis": {
    "total_experience_months": 48,
    "total_experience_years": 4.0,
    "work_history": [
      {
        "company": "Google",
        "title": "Software Engineer",
        "duration_months": 24,
        "start_date": "2020-01-01",
        "end_date": "2022-01-01"
      }
    ]
  },
  "processing_time_ms": 1234.56
}
```

---

## Job Matching

Compare resumes against job vacancies with skill synonym support.

### Compare Resume to Vacancy

**Endpoint:** `POST /api/matching/compare`

**Request:**
```json
{
  "resume_id": "550e8400-e29b-41d4-a716-446655440000",
  "vacancy_data": {
    "title": "Senior Python Developer",
    "required_skills": ["Python", "Django", "PostgreSQL"],
    "additional_requirements": ["Docker", "Kubernetes"],
    "min_experience_months": 36
  }
}
```

**Response:** `200 OK`
```json
{
  "resume_id": "550e8400-e29b-41d4-a716-446655440000",
  "vacancy_title": "Senior Python Developer",
  "match_percentage": 100.0,
  "required_skills_match": [
    {
      "skill": "Python",
      "status": "matched",
      "matched_as": "Python",
      "highlight": "green"
    },
    {
      "skill": "Django",
      "status": "matched",
      "matched_as": "Django REST Framework",
      "highlight": "green"
    },
    {
      "skill": "PostgreSQL",
      "status": "matched",
      "matched_as": "PostgreSQL",
      "highlight": "green"
    }
  ],
  "additional_skills_match": [
    {
      "skill": "Docker",
      "status": "matched",
      "matched_as": "Docker",
      "highlight": "green"
    },
    {
      "skill": "Kubernetes",
      "status": "missing",
      "matched_as": null,
      "highlight": "red"
    }
  ],
  "experience_verification": {
    "required_months": 36,
    "actual_months": 48,
    "meets_requirement": true,
    "summary": "48 months (4 years) of experience"
  },
  "processing_time_ms": 123.45
}
```

---

## Candidates

Manage candidates and workflow stages (kanban-style board).

### List All Candidates

**Endpoint:** `GET /api/candidates/`

**Query Parameters:**
- `skip` (optional): Number of results to skip (default: 0)
- `limit` (optional): Maximum results to return (default: 100)
- `stage_id` (optional): Filter by workflow stage ID
- `vacancy_id` (optional): Filter by vacancy ID

**Response:** `200 OK`
```json
{
  "total": 50,
  "candidates": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "resume.pdf",
      "current_stage": "screening",
      "stage_name": "Screening",
      "vacancy_id": "650e8400-e29b-41d4-a716-446655440000",
      "created_at": "2026-01-15T10:30:00Z",
      "updated_at": "2026-01-15T14:20:00Z",
      "notes": "Promising candidate",
      "tags": [
        {
          "id": "750e8400-e29b-41d4-a716-446655440000",
          "tag_name": "Senior Level",
          "color": "#FF5733",
          "organization_id": "org123"
        }
      ],
      "notes_count": 3,
      "latest_activity": {
        "activity_type": "stage_changed",
        "created_at": "2026-01-15T14:20:00Z"
      }
    }
  ]
}
```

---

### Move Candidate to Stage

**Endpoint:** `POST /api/candidates/{resume_id}/move`

**Request:**
```json
{
  "stage_id": "interview",
  "vacancy_id": "650e8400-e29b-41d4-a716-446655440000",
  "notes": "Ready for technical interview"
}
```

**Response:** `200 OK`
```json
{
  "id": "850e8400-e29b-41d4-a716-446655440000",
  "resume_id": "550e8400-e29b-41d4-a716-446655440000",
  "previous_stage": "screening",
  "new_stage": "interview",
  "message": "Candidate moved to interview stage"
}
```

---

### Bulk Move Candidates

**Endpoint:** `POST /api/candidates/bulk-move`

**Request:**
```json
{
  "resume_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440001"
  ],
  "stage_id": "interview",
  "vacancy_id": "650e8400-e29b-41d4-a716-446655440000",
  "notes": "Batch move to interview"
}
```

**Response:** `200 OK`
```json
{
  "total_requested": 2,
  "successful": 2,
  "failed": 0,
  "results": [
    {
      "resume_id": "550e8400-e29b-41d4-a716-446655440000",
      "success": true,
      "previous_stage": "screening",
      "new_stage": "interview",
      "message": "Successfully moved to interview"
    },
    {
      "resume_id": "550e8400-e29b-41d4-a716-446655440001",
      "success": true,
      "previous_stage": "applied",
      "new_stage": "interview",
      "message": "Successfully moved to interview"
    }
  ]
}
```

---

### Get Ranked Candidates for Vacancy

**Endpoint:** `GET /api/candidates/vacancy/{vacancy_id}/ranked`

**Path Parameters:**
- `vacancy_id`: Vacancy UUID

**Query Parameters:**
- `limit` (optional): Maximum number of ranked candidates to return (default: 10)

**Response:** `200 OK`
```json
{
  "vacancy_id": "650e8400-e29b-41d4-a716-446655440000",
  "total_candidates": 25,
  "candidates": [
    {
      "resume_id": "550e8400-e29b-41d4-a716-446655440000",
      "vacancy_id": "650e8400-e29b-41d4-a716-446655440000",
      "rank_score": 0.92,
      "rank_position": 1,
      "recommendation": "highly_recommended",
      "confidence": 0.88,
      "feature_contributions": {
        "skills_match": 0.45,
        "experience": 0.30,
        "education": 0.15,
        "keywords": 0.10
      },
      "ranking_factors": {
        "skills_score": 95,
        "experience_score": 88,
        "education_score": 75,
        "location_match": true
      }
    }
  ]
}
```

---

### Get Stage Metrics

**Endpoint:** `GET /api/candidates/stages/{stage_id}/metrics`

**Path Parameters:**
- `stage_id`: Workflow stage ID or name

**Response:** `200 OK`
```json
{
  "stage_id": "interview",
  "stage_name": "Interview",
  "total_candidates": 15,
  "time_metrics": {
    "average_days": 5.2,
    "median_days": 4.0,
    "min_days": 1.0,
    "max_days": 14.0
  },
  "conversion_rate": 0.67
}
```

---

## Vacancies

Create and manage job vacancy requests.

### Create Vacancy

**Endpoint:** `POST /api/vacancies/`

**Request:**
```json
{
  "title": "Senior Python Developer",
  "description": "We are looking for a Senior Python Developer...",
  "required_skills": ["Python", "Django", "PostgreSQL"],
  "min_experience_months": 48,
  "additional_requirements": ["Docker", "Kubernetes", "Redis"],
  "industry": "Technology",
  "work_format": "remote",
  "location": "Remote",
  "salary_min": 80000,
  "salary_max": 120000,
  "english_level": "B2",
  "employment_type": "full-time",
  "external_id": "EXT-12345",
  "source": "manual"
}
```

**Response:** `201 Created`
```json
{
  "id": "650e8400-e29b-41d4-a716-446655440000",
  "title": "Senior Python Developer",
  "description": "We are looking for a Senior Python Developer...",
  "required_skills": ["Python", "Django", "PostgreSQL"],
  "min_experience_months": 48,
  "additional_requirements": ["Docker", "Kubernetes", "Redis"],
  "industry": "Technology",
  "work_format": "remote",
  "location": "Remote",
  "salary_min": 80000,
  "salary_max": 120000,
  "english_level": "B2",
  "employment_type": "full-time",
  "external_id": "EXT-12345",
  "source": "manual",
  "created_at": "2026-01-15T10:30:00Z",
  "updated_at": "2026-01-15T10:30:00Z"
}
```

---

### List All Vacancies

**Endpoint:** `GET /api/vacancies/`

**Query Parameters:**
- `skip` (optional): Number of results to skip (default: 0)
- `limit` (optional): Maximum results to return (default: 100)

**Response:** `200 OK`
```json
{
  "total": 25,
  "vacancies": [
    {
      "id": "650e8400-e29b-41d4-a716-446655440000",
      "title": "Senior Python Developer",
      "description": "We are looking for...",
      "required_skills": ["Python", "Django"],
      "min_experience_months": 48,
      "additional_requirements": ["Docker"],
      "created_at": "2026-01-15T10:30:00Z"
    }
  ]
}
```

---

### Get Vacancy by ID

**Endpoint:** `GET /api/vacancies/{vacancy_id}`

**Path Parameters:**
- `vacancy_id`: Vacancy UUID

**Response:** `200 OK`
```json
{
  "id": "650e8400-e29b-41d4-a716-446655440000",
  "title": "Senior Python Developer",
  "description": "We are looking for...",
  "required_skills": ["Python", "Django", "PostgreSQL"],
  "min_experience_months": 48,
  "additional_requirements": ["Docker", "Kubernetes"],
  "industry": "Technology",
  "work_format": "remote",
  "location": "Remote",
  "salary_min": 80000,
  "salary_max": 120000,
  "english_level": "B2",
  "employment_type": "full-time",
  "external_id": "EXT-12345",
  "source": "manual",
  "created_at": "2026-01-15T10:30:00Z",
  "updated_at": "2026-01-15T10:30:00Z"
}
```

---

### Update Vacancy

**Endpoint:** `PUT /api/vacancies/{vacancy_id}`

**Path Parameters:**
- `vacancy_id`: Vacancy UUID

**Request:** (Partial update - all fields optional)
```json
{
  "title": "Lead Python Developer",
  "salary_min": 90000,
  "salary_max": 130000
}
```

**Response:** `200 OK`
```json
{
  "id": "650e8400-e29b-41d4-a716-446655440000",
  "title": "Lead Python Developer",
  "description": "We are looking for...",
  "required_skills": ["Python", "Django"],
  "min_experience_months": 48,
  "salary_min": 90000,
  "salary_max": 130000,
  "updated_at": "2026-01-15T11:30:00Z"
}
```

---

### Delete Vacancy

**Endpoint:** `DELETE /api/vacancies/{vacancy_id}`

**Path Parameters:**
- `vacancy_id`: Vacancy UUID

**Response:** `204 No Content`

---

## Search

Advanced candidate search with full-text search and boolean operators.

### Search Candidates

**Endpoint:** `POST /api/search/candidates`

**Request:**
```json
{
  "query": "Python AND Django NOT Flask",
  "filters": {
    "skills": ["Python", "Django"],
    "min_experience_years": 3,
    "max_experience_years": 10,
    "location": "Remote",
    "education_level": "Bachelor",
    "languages": ["English", "Russian"],
    "min_match_score": 70,
    "date_from": "2026-01-01T00:00:00Z",
    "date_to": "2026-12-31T23:59:59Z",
    "vacancy_id": "650e8400-e29b-41d4-a716-446655440000",
    "stage_id": "interview"
  },
  "skip": 0,
  "limit": 50,
  "sort_by": "relevance"
}
```

**Boolean Query Examples:**
- `"Python AND Django"` - Candidates with both Python and Django
- `"Python OR Django"` - Candidates with either Python or Django
- `"Python NOT Flask"` - Candidates with Python but not Flask
- `"Python Django"` - Implicit AND (same as "Python AND Django")

**Response:** `200 OK`
```json
{
  "total": 42,
  "candidates": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "resume.pdf",
      "status": "completed",
      "created_at": "2026-01-15T10:30:00Z",
      "updated_at": "2026-01-15T14:20:00Z",
      "current_stage": "interview",
      "vacancy_id": "650e8400-e29b-41d4-a716-446655440000",
      "skills": ["Python", "Django", "PostgreSQL"],
      "total_experience_months": 60,
      "experience_years": 5.0,
      "education": [
        {
          "degree": "Bachelor of Science",
          "field": "Computer Science",
          "institution": "MIT"
        }
      ],
      "language": "en",
      "quality_score": 85.5
    }
  ],
  "query": "Python AND Django NOT Flask",
  "filters_applied": {
    "skills": ["Python", "Django"],
    "min_experience_years": 3
  },
  "execution_time_seconds": 0.234,
  "skip": 0,
  "limit": 50
}
```

---

### Get Search History

**Endpoint:** `GET /api/search/history`

**Query Parameters:**
- `skip` (optional): Number of results to skip (default: 0)
- `limit` (optional): Maximum results to return (default: 50)

**Response:** `200 OK`
```json
{
  "total": 120,
  "history": [
    {
      "id": "950e8400-e29b-41d4-a716-446655440000",
      "query": "Python AND Django",
      "filters": {
        "skills": ["Python"],
        "min_experience_years": 3
      },
      "results_count": 42,
      "execution_time_seconds": 0.234,
      "created_at": "2026-01-15T14:30:00Z",
      "recruiter_id": "user123"
    }
  ],
  "skip": 0,
  "limit": 50
}
```

---

## Comparisons

Save and manage candidate-vacancy comparisons.

### Create Comparison

**Endpoint:** `POST /api/comparisons/`

**Request:**
```json
{
  "resume_id": "550e8400-e29b-41d4-a716-446655440000",
  "vacancy_id": "650e8400-e29b-41d4-a716-446655440000",
  "comparison_data": {
    "match_percentage": 85.5,
    "required_skills_match": [...],
    "additional_skills_match": [...],
    "experience_verification": {...}
  },
  "name": "Python Developer Comparison",
  "notes": "Strong match, recommend interview"
}
```

**Response:** `201 Created`

---

### List All Comparisons

**Endpoint:** `GET /api/comparisons/`

**Query Parameters:**
- `skip` (optional): Number of results to skip (default: 0)
- `limit` (optional): Maximum results to return (default: 100)

**Response:** `200 OK`

---

### Get Comparison by ID

**Endpoint:** `GET /api/comparisons/{comparison_id}`

**Response:** `200 OK`

---

### Update Comparison

**Endpoint:** `PUT /api/comparisons/{comparison_id}`

**Response:** `200 OK`

---

### Delete Comparison

**Endpoint:** `DELETE /api/comparisons/{comparison_id}`

**Response:** `204 No Content`

---

### Compare Multiple Candidates

**Endpoint:** `POST /api/comparisons/compare-multiple`

**Request:**
```json
{
  "vacancy_id": "650e8400-e29b-41d4-a716-446655440000",
  "resume_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "550e8400-e29b-41d4-a716-446655440001"
  ]
}
```

**Response:** `200 OK`

---

### Get Shared Comparison

**Endpoint:** `GET /api/comparisons/shared/{share_id}`

**Response:** `200 OK`

---

## Candidate Notes

Add and manage notes for candidates.

### Create Note

**Endpoint:** `POST /api/notes/`

**Request:**
```json
{
  "resume_id": "550e8400-e29b-41d4-a716-446655440000",
  "content": "Strong technical skills, good cultural fit",
  "note_type": "general"
}
```

**Response:** `201 Created`

---

### List All Notes

**Endpoint:** `GET /api/notes/`

**Query Parameters:**
- `resume_id` (optional): Filter by resume ID
- `skip` (optional): Number of results to skip (default: 0)
- `limit` (optional): Maximum results to return (default: 100)

**Response:** `200 OK`

---

### Get Note by ID

**Endpoint:** `GET /api/notes/{note_id}`

**Response:** `200 OK`

---

### Update Note

**Endpoint:** `PUT /api/notes/{note_id}`

**Response:** `200 OK`

---

### Delete Note

**Endpoint:** `DELETE /api/notes/{note_id}`

**Response:** `204 No Content`

---

## Candidate Tags

Tag candidates for organization and filtering.

### Create Tag

**Endpoint:** `POST /api/tags/`

**Request:**
```json
{
  "tag_name": "Senior Level",
  "color": "#FF5733",
  "organization_id": "org123"
}
```

**Response:** `201 Created`

---

### List All Tags

**Endpoint:** `GET /api/tags/`

**Query Parameters:**
- `organization_id` (optional): Filter by organization ID

**Response:** `200 OK`
```json
{
  "total": 15,
  "tags": [
    {
      "id": "750e8400-e29b-41d4-a716-446655440000",
      "tag_name": "Senior Level",
      "color": "#FF5733",
      "organization_id": "org123",
      "created_at": "2026-01-15T10:30:00Z"
    }
  ]
}
```

---

### Get Tag by ID

**Endpoint:** `GET /api/tags/{tag_id}`

**Response:** `200 OK`

---

### Update Tag

**Endpoint:** `PUT /api/tags/{tag_id}`

**Response:** `200 OK`

---

### Delete Tag

**Endpoint:** `DELETE /api/tags/{tag_id}`

**Response:** `204 No Content`

---

### Assign Tag to Candidate

**Endpoint:** `POST /api/tags/resume/{resume_id}/assign`

**Request:**
```json
{
  "tag_id": "750e8400-e29b-41d4-a716-446655440000"
}
```

**Response:** `200 OK`

---

### Remove Tag from Candidate

**Endpoint:** `DELETE /api/tags/resume/{resume_id}/tags/{tag_id}`

**Response:** `204 No Content`

---

### Get Tags for Candidate

**Endpoint:** `GET /api/tags/resume/{resume_id}`

**Response:** `200 OK`
```json
{
  "resume_id": "550e8400-e29b-41d4-a716-446655440000",
  "tags": [
    {
      "id": "750e8400-e29b-41d4-a716-446655440000",
      "tag_name": "Senior Level",
      "color": "#FF5733"
    }
  ]
}
```

---

## Workflow Stages

Manage customizable workflow stages for candidate pipeline.

### List All Stages

**Endpoint:** `GET /api/stages/`

**Response:** `200 OK`
```json
{
  "total": 6,
  "stages": [
    {
      "id": "applied",
      "name": "Applied",
      "order": 1,
      "is_default": true
    },
    {
      "id": "screening",
      "name": "Screening",
      "order": 2,
      "is_default": true
    }
  ]
}
```

---

### Create Stage

**Endpoint:** `POST /api/stages/`

**Request:**
```json
{
  "name": "Technical Assessment",
  "order": 3,
  "is_default": false
}
```

**Response:** `201 Created`

---

### Get Stage by ID

**Endpoint:** `GET /api/stages/{stage_id}`

**Response:** `200 OK`

---

### Update Stage

**Endpoint:** `PUT /api/stages/{stage_id}`

**Response:** `200 OK`

---

### Delete Stage

**Endpoint:** `DELETE /api/stages/{stage_id}`

**Response:** `204 No Content`

---

## Skill Taxonomies

Manage skill taxonomies for different industries.

### List All Taxonomies

**Endpoint:** `GET /api/taxonomies/`

**Response:** `200 OK`
```json
{
  "total": 5,
  "taxonomies": [
    {
      "id": "tax1",
      "name": "IT Industry Skills",
      "industry": "Technology",
      "skills_count": 250,
      "created_at": "2026-01-15T10:30:00Z"
    }
  ]
}
```

---

### Create Taxonomy

**Endpoint:** `POST /api/taxonomies/`

**Request:**
```json
{
  "name": "Finance Industry Skills",
  "industry": "Finance",
  "skills": ["Accounting", "Financial Analysis", "Excel"]
}
```

**Response:** `201 Created`

---

### Get Taxonomy by ID

**Endpoint:** `GET /api/taxonomies/{taxonomy_id}`

**Response:** `200 OK`

---

### Update Taxonomy

**Endpoint:** `PUT /api/taxonomies/{taxonomy_id}`

**Response:** `200 OK`

---

### Delete Taxonomy

**Endpoint:** `DELETE /api/taxonomies/{taxonomy_id}`

**Response:** `204 No Content`

---

### Load IT Taxonomy

**Endpoint:** `POST /api/taxonomies/load/it`

**Response:** `200 OK`
```json
{
  "message": "IT taxonomy loaded successfully",
  "skills_count": 250
}
```

---

### Load Industry Taxonomy

**Endpoint:** `POST /api/taxonomies/load/industry/{industry}`

**Path Parameters:**
- `industry`: Industry name (e.g., "finance", "healthcare")

**Response:** `200 OK`

---

### Delete Industry Taxonomy

**Endpoint:** `DELETE /api/taxonomies/industry/{industry}`

**Response:** `204 No Content`

---

## Custom Synonyms

Define custom skill synonym mappings for organizations.

### List All Custom Synonyms

**Endpoint:** `GET /api/synonyms/`

**Query Parameters:**
- `organization_id` (optional): Filter by organization ID

**Response:** `200 OK`
```json
{
  "total": 10,
  "synonyms": [
    {
      "id": "syn1",
      "canonical_name": "JavaScript",
      "synonyms": ["JS", "JavaScript", "ECMAScript"],
      "organization_id": "org123"
    }
  ]
}
```

---

### Create Custom Synonym

**Endpoint:** `POST /api/synonyms/`

**Request:**
```json
{
  "canonical_name": "JavaScript",
  "synonyms": ["JS", "JavaScript", "ECMAScript"],
  "organization_id": "org123"
}
```

**Response:** `201 Created`

---

### Get Synonym by ID

**Endpoint:** `GET /api/synonyms/{synonym_id}`

**Response:** `200 OK`

---

### Update Synonym

**Endpoint:** `PUT /api/synonyms/{synonym_id}`

**Response:** `200 OK`

---

### Delete Synonym

**Endpoint:** `DELETE /api/synonyms/{synonym_id}`

**Response:** `204 No Content`

---

### Delete All Organization Synonyms

**Endpoint:** `DELETE /api/synonyms/organization/{organization_id}`

**Response:** `204 No Content`

---

## Reports

Generate and schedule reports.

### Create Report

**Endpoint:** `POST /api/reports/`

**Request:**
```json
{
  "name": "Weekly Hiring Report",
  "report_type": "hiring_metrics",
  "parameters": {
    "date_from": "2026-01-01T00:00:00Z",
    "date_to": "2026-01-07T23:59:59Z",
    "vacancy_ids": ["vac1", "vac2"]
  }
}
```

**Response:** `201 Created`

---

### List All Reports

**Endpoint:** `GET /api/reports/`

**Response:** `200 OK`

---

### Get Report by ID

**Endpoint:** `GET /api/reports/{report_id}`

**Response:** `200 OK`

---

### Update Report

**Endpoint:** `PUT /api/reports/{report_id}`

**Response:** `200 OK`

---

### Delete Report

**Endpoint:** `DELETE /api/reports/{report_id}`

**Response:** `204 No Content`

---

### Export Report as CSV

**Endpoint:** `POST /api/reports/export/csv`

**Request:**
```json
{
  "report_id": "rep1"
}
```

**Response:** `200 OK` (CSV file)

---

### Export Report as PDF

**Endpoint:** `POST /api/reports/export/pdf`

**Request:**
```json
{
  "report_id": "rep1"
}
```

**Response:** `200 OK` (PDF file)

---

### Schedule Report

**Endpoint:** `POST /api/reports/schedule`

**Request:**
```json
{
  "report_id": "rep1",
  "schedule": "weekly",
  "recipients": ["admin@example.com"]
}
```

**Response:** `200 OK`

---

### Delete Organization Reports

**Endpoint:** `DELETE /api/reports/organization/{organization_id}`

**Response:** `204 No Content`

---

## Model Versions

Manage ML model versions and deployments.

### List All Model Versions

**Endpoint:** `GET /api/models/`

**Response:** `200 OK`
```json
{
  "total": 5,
  "models": [
    {
      "id": "model1",
      "name": "ranking_model_v2",
      "version": "2.0.0",
      "is_active": true,
      "accuracy": 0.92,
      "created_at": "2026-01-15T10:30:00Z"
    }
  ]
}
```

---

### Get Active Model Version

**Endpoint:** `GET /api/models/active`

**Response:** `200 OK`

---

### Create Model Version

**Endpoint:** `POST /api/models/`

**Request:**
```json
{
  "name": "ranking_model_v3",
  "version": "3.0.0",
  "model_path": "/models/ranking_v3.pkl"
}
```

**Response:** `201 Created`

---

### Get Model Version by ID

**Endpoint:** `GET /api/models/{version_id}`

**Response:** `200 OK`

---

### Update Model Version

**Endpoint:** `PUT /api/models/{version_id}`

**Response:** `200 OK`

---

### Delete Model Version

**Endpoint:** `DELETE /api/models/{version_id}`

**Response:** `204 No Content`

---

### Activate Model Version

**Endpoint:** `POST /api/models/{version_id}/activate`

**Response:** `200 OK`

---

### Deactivate Model Version

**Endpoint:** `POST /api/models/{version_id}/deactivate`

**Response:** `200 OK`

---

### Retrain Model

**Endpoint:** `POST /api/models/retrain`

**Request:**
```json
{
  "model_type": "ranking",
  "training_data_params": {...}
}
```

**Response:** `200 OK`

---

### Rollback Model

**Endpoint:** `POST /api/models/rollback`

**Request:**
```json
{
  "target_version_id": "model1"
}
```

**Response:** `200 OK`

---

## Matching Weights

Configure custom weights for matching calculations.

### List All Weight Profiles

**Endpoint:** `GET /api/matching-weights/`

**Response:** `200 OK`
```json
{
  "total": 3,
  "profiles": [
    {
      "id": "weight1",
      "name": "Senior Developer Profile",
      "organization_id": "org123",
      "weights": {
        "skills": 0.5,
        "experience": 0.3,
        "education": 0.15,
        "location": 0.05
      }
    }
  ]
}
```

---

### Create Weight Profile

**Endpoint:** `POST /api/matching-weights/`

**Request:**
```json
{
  "name": "Junior Developer Profile",
  "organization_id": "org123",
  "weights": {
    "skills": 0.4,
    "experience": 0.2,
    "education": 0.3,
    "location": 0.1
  }
}
```

**Response:** `201 Created`

---

### Get Weight Profile by ID

**Endpoint:** `GET /api/matching-weights/{profile_id}`

**Response:** `200 OK`

---

### Update Weight Profile

**Endpoint:** `PUT /api/matching-weights/{profile_id}`

**Response:** `200 OK`

---

### Delete Weight Profile

**Endpoint:** `DELETE /api/matching-weights/{profile_id}`

**Response:** `204 No Content`

---

### Compare Using Custom Weights

**Endpoint:** `POST /api/matching-weights/compare`

**Request:**
```json
{
  "profile_id": "weight1",
  "resume_id": "resume1",
  "vacancy_id": "vacancy1"
}
```

**Response:** `200 OK`

---

### Rematch with Custom Weights

**Endpoint:** `POST /api/matching-weights/{profile_id}/rematch`

**Request:**
```json
{
  "vacancy_id": "vacancy1"
}
```

**Response:** `200 OK`

---

## Feedback

Collect feedback for ML model improvement.

### Submit Feedback

**Endpoint:** `POST /api/feedback/`

**Request:**
```json
{
  "resume_id": "resume1",
  "vacancy_id": "vacancy1",
  "feedback_type": "hiring_decision",
  "outcome": "hired",
  "rating": 5,
  "comments": "Excellent match, hired successfully"
}
```

**Response:** `201 Created`

---

### List All Feedback

**Endpoint:** `GET /api/feedback/`

**Query Parameters:**
- `resume_id` (optional): Filter by resume ID
- `vacancy_id` (optional): Filter by vacancy ID

**Response:** `200 OK`

---

### Get Feedback by ID

**Endpoint:** `GET /api/feedback/{feedback_id}`

**Response:** `200 OK`

---

### Update Feedback

**Endpoint:** `PUT /api/feedback/{feedback_id}`

**Response:** `200 OK`

---

### Delete Feedback

**Endpoint:** `DELETE /api/feedback/{feedback_id}`

**Response:** `204 No Content`

---

## Ranking

AI-powered candidate ranking for vacancies.

### Rank Candidates for Vacancy

**Endpoint:** `POST /api/ranking/rank`

**Request:**
```json
{
  "vacancy_id": "vacancy1",
  "limit": 20
}
```

**Response:** `200 OK`
```json
{
  "vacancy_id": "vacancy1",
  "total_candidates": 50,
  "ranked_candidates": [
    {
      "resume_id": "resume1",
      "rank": 1,
      "score": 0.95,
      "recommendation": "highly_recommended",
      "confidence": 0.92
    }
  ]
}
```

---

### Get Ranking Factors

**Endpoint:** `GET /api/ranking/factors/{resume_id}/{vacancy_id}`

**Response:** `200 OK`
```json
{
  "resume_id": "resume1",
  "vacancy_id": "vacancy1",
  "factors": {
    "skills_match": 0.45,
    "experience": 0.30,
    "education": 0.15,
    "location": 0.05,
    "keywords": 0.05
  }
}
```

---

## Skill Gap Analysis

Analyze skill gaps between candidates and requirements.

### Analyze Skill Gaps

**Endpoint:** `POST /api/skill-gap/analyze`

**Request:**
```json
{
  "resume_id": "resume1",
  "vacancy_id": "vacancy1"
}
```

**Response:** `200 OK`
```json
{
  "resume_id": "resume1",
  "vacancy_id": "vacancy1",
  "missing_skills": [
    {
      "skill": "Kubernetes",
      "priority": "high",
      "recommendation": "Consider candidates with K8s experience"
    }
  ],
  "surplus_skills": [
    {
      "skill": "GraphQL",
      "relevance": "medium"
    }
  ]
}
```

---

## Batch Operations

Perform bulk operations on multiple candidates.

### Bulk Export Candidates

**Endpoint:** `POST /api/batch/export`

**Request:**
```json
{
  "resume_ids": ["resume1", "resume2", "resume3"],
  "format": "csv",
  "include_analysis": true
}
```

**Response:** `200 OK` (CSV file)

---

### Bulk Tag Candidates

**Endpoint:** `POST /api/batch/tag`

**Request:**
```json
{
  "resume_ids": ["resume1", "resume2"],
  "tag_id": "tag1"
}
```

**Response:** `200 OK`

---

### Bulk Add to Pipeline

**Endpoint:** `POST /api/batch/add-to-pipeline`

**Request:**
```json
{
  "resume_ids": ["resume1", "resume2"],
  "vacancy_id": "vacancy1",
  "stage_id": "screening"
}
```

**Response:** `200 OK`

---

## Error Responses

All endpoints may return error responses in the following format:

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": "Validation error: resume_id is required"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error",
  "error_id": "err_abc123"
}
```

---

## Rate Limiting

API requests are rate limited:

- **Default Limit:** 1000 requests per hour per IP
- **Authenticated Users:** 5000 requests per hour per user

Rate limit headers are included in all responses:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1642248000
```

---

## Pagination

List endpoints support pagination using `skip` and `limit` parameters:

- `skip`: Number of items to skip (default: 0)
- `limit`: Maximum items to return (default: 100, max: 200)

Pagination metadata is included in responses:
```json
{
  "total": 250,
  "skip": 0,
  "limit": 100,
  "items": [...]
}
```

---

## Internationalization

All endpoints support the `Accept-Language` header for translated error messages and responses:

```http
Accept-Language: en
```

Supported languages:
- `en` - English
- `ru` - Russian

---

## API Versioning

The API is versioned using URL paths. The current version is `v1`:

```
http://localhost:8000/api/v1/...
```

---

## Webhooks

Webhooks can be configured to receive notifications about events:

### Supported Events:
- `resume.uploaded`
- `resume.analyzed`
- `candidate.stage_changed`
- `vacancy.created`

### Webhook Configuration

Contact system administrator to configure webhook endpoints.

---

## OpenAPI/Swagger

Interactive API documentation is available at:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`

---

## Support

For API support and questions:
- **Documentation:** `http://localhost:8000/docs`
- **Email:** support@agenthr.com
- **Issues:** Create issue in project repository

---

**Document Version:** 1.0.0
**Last Updated:** 2026-01-15
**API Version:** 1.0.0
