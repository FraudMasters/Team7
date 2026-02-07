# ATS Simulation Service API Documentation

## Overview

The ATS (Applicant Tracking System) Simulation Service provides LLM-powered resume evaluation similar to commercial ATS systems. It scores resumes against job requirements, identifies missing keywords, detects formatting issues, and provides actionable feedback.

## Base URL

```
http://localhost:8007
```

Via API Gateway:
```
http://localhost:8888/api/ats
```

## Authentication

All endpoints require JWT authentication via the API Gateway. Include the `Authorization` header with your Bearer token:

```
Authorization: Bearer <your-jwt-token>
```

---

## Endpoints

### Simulate ATS Evaluation

Evaluate a resume against a job vacancy using ATS simulation.

**Endpoint:** `POST /api/ats/simulate`

**Request Body:**
```json
{
  "resume_text": "John Doe\nSenior Python Developer\n\nExperience:\n- 5 years at Tech Corp as Python Developer\n- Built Django REST APIs\n- Used PostgreSQL for data storage\n\nSkills:\n- Python, Django, PostgreSQL, Docker\n\nEducation:\n- BS Computer Science, MIT",
  "job_title": "Senior Python Developer",
  "job_description": "We are looking for a Senior Python Developer with experience in Django, PostgreSQL, and Docker. Knowledge of Kubernetes is a plus.",
  "required_skills": ["Python", "Django", "PostgreSQL", "Docker"],
  "use_llm": true
}
```

**Response:** `200 OK`

```json
{
  "passed": true,
  "overall_score": 0.75,
  "keyword_score": 0.8,
  "experience_score": 0.7,
  "education_score": 0.8,
  "fit_score": 0.7,
  "looks_professional": true,
  "disqualified": false,
  "visual_issues": [],
  "ats_issues": [],
  "missing_keywords": ["Kubernetes"],
  "suggestions": [
    "Add Kubernetes experience to match job requirements",
    "Include metrics for project impact"
  ],
  "feedback": "Strong candidate with relevant experience in Python development. Good match for the Senior Python Developer position. Consider adding Kubernetes experience to fully meet requirements.",
  "provider": "zai",
  "model": "glm-4.7",
  "processing_time_ms": 1250.5
}
```

**Score Descriptions:**

| Score | Range | Description |
|-------|-------|-------------|
| `overall_score` | 0-1 | Overall ATS score (passed if ≥ 0.6) |
| `keyword_score` | 0-1 | Keyword matching score |
| `experience_score` | 0-1 | Relevance of work experience |
| `education_score` | 0-1 | Education match score |
| `fit_score` | 0-1 | Overall candidate fit |

**Example:**
```bash
curl -X POST "http://localhost:8888/api/ats/simulate" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "John Doe\nSenior Python Developer...",
    "job_title": "Senior Python Developer",
    "required_skills": ["Python", "Django"],
    "use_llm": true
  }'
```

---

### Simulate ATS by IDs

Evaluate a resume against a vacancy using their IDs.

**Endpoint:** `POST /api/ats/simulate-by-ids`

**Request Body:**
```json
{
  "resume_id": "resume-abc-123",
  "vacancy_id": "vacancy-xyz-456",
  "use_llm": true
}
```

**Response:** `200 OK`

Same response format as `POST /api/ats/simulate`.

---

### Batch ATS Evaluation

Evaluate multiple resumes against a job vacancy.

**Endpoint:** `POST /api/ats/batch-simulate`

**Request Body:**
```json
{
  "job_title": "Senior Python Developer",
  "job_description": "We are looking for a Senior Python Developer...",
  "required_skills": ["Python", "Django", "PostgreSQL"],
  "resume_texts": [
    "Resume 1 text...",
    "Resume 2 text...",
    "Resume 3 text..."
  ],
  "use_llm": true
}
```

**Response:** `200 OK`

```json
{
  "job_title": "Senior Python Developer",
  "results": [
    {
      "resume_index": 0,
      "passed": true,
      "overall_score": 0.75,
      "keyword_score": 0.8,
      "feedback": "Strong candidate..."
    },
    {
      "resume_index": 1,
      "passed": false,
      "overall_score": 0.45,
      "keyword_score": 0.5,
      "feedback": "Insufficient experience..."
    }
  ],
  "summary": {
    "total_evaluated": 3,
    "passed": 1,
    "failed": 2,
    "average_score": 0.6
  }
}
```

---

### Get ATS Result

Retrieve a stored ATS evaluation result.

**Endpoint:** `GET /api/ats/results/{result_id}`

**Path Parameters:**
- `result_id` (required) - ID of the ATS evaluation result

**Response:** `200 OK`

```json
{
  "id": "ats-result-1",
  "resume_id": "resume-abc-123",
  "vacancy_id": "vacancy-xyz-456",
  "passed": true,
  "overall_score": 0.75,
  "keyword_score": 0.8,
  "experience_score": 0.7,
  "education_score": 0.8,
  "fit_score": 0.7,
  "missing_keywords": ["Kubernetes"],
  "suggestions": ["Add Kubernetes experience"],
  "feedback": "Strong candidate...",
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

## Screening Questions Endpoints

### Get Screening Questions

Get screening questions for a vacancy.

**Endpoint:** `GET /api/screening/questions`

**Query Parameters:**
- `vacancy_id` (optional) - Filter by vacancy ID

**Response:** `200 OK`

```json
{
  "questions": [
    {
      "id": "question-1",
      "vacancy_id": "vacancy-123",
      "question": "What is your experience with Python?",
      "question_type": "text",
      "required": true,
      "order": 1
    },
    {
      "id": "question-2",
      "vacancy_id": "vacancy-123",
      "question": "Do you have experience with Docker?",
      "question_type": "yes_no",
      "required": true,
      "order": 2
    }
  ]
}
```

---

### Submit Screening Response

Submit screening questionnaire responses.

**Endpoint:** `POST /api/screening/submit`

**Request Body:**
```json
{
  "vacancy_id": "vacancy-123",
  "candidate_id": "candidate-456",
  "responses": [
    {
      "question_id": "question-1",
      "answer": "5 years of experience with Python"
    },
    {
      "question_id": "question-2",
      "answer": "yes"
    }
  ]
}
```

**Response:** `201 Created`

```json
{
  "id": "screening-response-1",
  "vacancy_id": "vacancy-123",
  "candidate_id": "candidate-456",
  "submitted_at": "2025-01-15T10:30:00Z",
  "score": 0.8,
  "passed": true
}
```

---

## Data Models

### ATS Evaluation Scores

| Score | Range | Description |
|-------|-------|-------------|
| `0.0 - 0.3` | Poor | Not recommended |
| `0.3 - 0.5` | Fair | Weak match |
| `0.5 - 0.7` | Good | Potential candidate |
| `0.7 - 0.9` | Excellent | Strong match |
| `0.9 - 1.0` | Outstanding | Exceptional match |

### Visual Issues

Common visual issues detected:
- `missing_sections` - Missing key resume sections
- `poor_formatting` - Inconsistent formatting
- `no_bullet_points` - Lacks bullet points for readability
- `inconsistent_dates` - Date format inconsistencies

### ATS Issues

Common ATS issues detected:
- `tables_detected` - Tables may not parse correctly
- `images_detected` - Images may not be processed
- `special_characters` - Special characters causing issues
- `no_keywords` - Missing critical keywords

---

## LLM Providers

The service supports multiple LLM providers:

| Provider | Model | Description |
|----------|-------|-------------|
| `zai` | glm-4.7 | Primary provider (Z.ai) |
| `openai` | gpt-4 | OpenAI GPT-4 |
| `anthropic` | claude-3-opus | Anthropic Claude |
| `rule-based` | fallback | Rule-based fallback |

**Note:** If `use_llm` is false or no LLM API key is configured, the service falls back to rule-based evaluation.

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
- `404 Not Found` - Result or vacancy not found
- `422 Unprocessable Entity` - Validation error (e.g., resume text too short)
- `500 Internal Server Error` - ATS evaluation failed

---

## Rate Limiting

Via API Gateway:
- 100 requests per second
- 10,000 requests per hour

---

## gRPC Service

The ATS Simulation Service also exposes a gRPC interface on port `50057`.

**Available RPC Methods:**
- `SimulateATS` - Run ATS simulation
- `BatchSimulateATS` - Batch ATS evaluation
- `GetATSResult` - Get stored result
- `GetScreeningQuestions` - Get screening questions
- `SubmitScreeningResponse` - Submit screening responses

See `protos/ats.proto` for the complete service definition.
