# AgentHR API Usage Guide

## Executive Summary

This comprehensive guide provides practical examples and complete workflow documentation for integrating with the AgentHR Resume Analysis API. While auto-generated OpenAPI docs are available at `/docs`, this guide demonstrates real-world usage patterns and complete end-to-end workflows.

**Base URL:** `http://localhost:8000` (default) or your deployed backend URL

**Interactive API Docs:** http://localhost:8000/docs

**API Version:** 1.0.0

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication & Headers](#authentication--headers)
3. [Error Handling](#error-handling)
4. [Core Workflows](#core-workflows)
   - [Complete Recruitment Workflow](#complete-recruitment-workflow)
   - [Batch Resume Processing](#batch-resume-processing)
   - [Candidate Comparison Workflow](#candidate-comparison-workflow)
   - [Multi-Vacancy Matching](#multi-vacancy-matching)
5. [API Endpoint Categories](#api-endpoint-categories)
6. [Language Integration Examples](#language-integration-examples)
7. [Best Practices](#best-practices)
8. [Rate Limiting & Performance](#rate-limiting--performance)
9. [Advanced Features](#advanced-features)

---

## Quick Start

### 1. Health Check

Verify the API is running:

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "resume-analysis-api",
  "version": "1.0.0"
}
```

### 2. Upload Your First Resume

```bash
curl -X POST http://localhost:8000/api/resumes/upload \
  -F "file=@resume.pdf"
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "resume.pdf",
  "status": "pending",
  "message": "Resume uploaded successfully. Processing started."
}
```

### 3. Create a Job Vacancy

```bash
curl -X POST http://localhost:8000/api/vacancies/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Python Developer",
    "description": "We are looking for an experienced Python developer...",
    "required_skills": ["python", "fastapi", "postgresql"],
    "min_experience_months": 36
  }'
```

### 4. Match Resume to Vacancy

```bash
curl -X POST http://localhost:8000/api/matching/compare-unified \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "123e4567-e89b-12d3-a456-426614174000",
    "vacancy_data": {
      "id": "vacancy_uuid",
      "title": "Python Developer",
      "required_skills": ["python", "fastapi", "postgresql"]
    }
  }'
```

---

## Authentication & Headers

### Standard Headers

All API requests should include these headers:

```bash
-H "Content-Type: application/json" \
-H "Accept-Language: en"  # or "ru" for Russian
```

### Supported Languages

| Language Code | Language |
|---------------|----------|
| `en` | English |
| `ru` | Russian |

### CORS Configuration

The API supports CORS for these origins (configurable in settings):
- `http://localhost:3000` (frontend dev server)
- `http://localhost:8000` (backend API)

---

## Error Handling

### Error Response Format

All errors follow this consistent structure:

```json
{
  "error": "Error type",
  "detail": "Human-readable error message",
  "type": "error_type_code"
}
```

### Common Error Codes

| HTTP Status | Error Type | Description |
|-------------|------------|-------------|
| 400 | Bad Request | Invalid request parameters |
| 404 | Not Found | Resource not found |
| 415 | Unsupported Media Type | Invalid file format (only PDF/DOCX allowed) |
| 422 | Validation Error | Invalid data in request body |
| 500 | Internal Server Error | Server-side error |

### Example Error Handling

```bash
# Invalid file type
curl -X POST http://localhost:8000/api/resumes/upload \
  -F "file=@resume.txt"

# Response
{
  "error": "invalid_file_type",
  "detail": "File type .txt is not supported. Allowed types: .pdf, .docx",
  "type": "validation_error"
}
```

---

## Core Workflows

### Complete Recruitment Workflow

This is the most common workflow: upload resume → analyze → match → rank → feedback.

#### Step 1: Upload Resume

```bash
curl -X POST http://localhost:8000/api/resumes/upload \
  -F "file=@candidate_resume.pdf"
```

**Save the `id` from response for next steps.**

#### Step 2: Wait for Analysis (Optional)

Resume analysis happens asynchronously in the background. You can check the status:

```bash
curl http://localhost:8000/api/resumes/{resume_id}
```

#### Step 3: Create Job Vacancy

```bash
curl -X POST http://localhost:8000/api/vacancies/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Python Developer",
    "description": "Join our team to build scalable web applications...",
    "required_skills": ["python", "fastapi", "postgresql", "redis"],
    "min_experience_months": 48,
    "location": "Remote",
    "employment_type": "full-time"
  }'
```

**Save the `id` from response.**

#### Step 4: Perform Unified Matching

```bash
curl -X POST http://localhost:8000/api/matching/compare-unified \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "RESUME_UUID",
    "vacancy_data": {
      "id": "VACANCY_UUID",
      "title": "Senior Python Developer",
      "required_skills": ["python", "fastapi", "postgresql", "redis"]
    }
  }'
```

**Response:**
```json
{
  "match_score": 85.5,
  "matched_skills": ["python", "fastapi", "postgresql"],
  "missing_skills": ["redis"],
  "keyword_score": 0.75,
  "tfidf_score": 0.82,
  "vector_score": 0.88,
  "overall_match_score": 0.85
}
```

#### Step 5: Rank Candidate with ML Model

```bash
curl -X POST http://localhost:8000/api/ranking/rank \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "RESUME_UUID",
    "vacancy_id": "VACANCY_UUID",
    "use_experiment": true
  }'
```

**Response:**
```json
{
  "resume_id": "RESUME_UUID",
  "vacancy_id": "VACANCY_UUID",
  "rank_score": 0.87,
  "rank_position": 3,
  "recommendation": "good",
  "confidence": 0.85,
  "is_experiment": true,
  "experiment_group": "treatment",
  "model_version": "v2.1",
  "feature_contributions": {
    "overall_match_score": 0.45,
    "experience_months": 0.25,
    "skills_match_ratio": 0.20
  },
  "ranking_factors": {
    "skills_match_ratio": 0.75,
    "experience_months": 60,
    "experience_relevance": 0.82
  }
}
```

#### Step 6: Submit Feedback (For Model Improvement)

```bash
curl -X POST http://localhost:8000/api/ranking/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "rank_id": "RANK_UUID",
    "was_helpful": true,
    "actual_outcome": "hired",
    "rating": 5
  }'
```

#### Step 7: Move Candidate to Hiring Stage

```bash
curl -X PUT http://localhost:8000/api/candidates/{resume_id}/move \
  -H "Content-Type: application/json" \
  -d '{
    "stage_id": "interview",
    "vacancy_id": "VACANCY_UUID",
    "notes": "Strong candidate, schedule technical interview"
  }'
```

---

### Batch Resume Processing

Process multiple resumes for a single vacancy.

#### Step 1: Upload Multiple Resumes

```bash
# Upload each resume
curl -X POST http://localhost:8000/api/resumes/upload -F "file=@resume1.pdf"
curl -X POST http://localhost:8000/api/resumes/upload -F "file=@resume2.pdf"
curl -X POST http://localhost:8000/api/resumes/upload -F "file=@resume3.pdf"
```

#### Step 2: Get Ranked Candidates for Vacancy

```bash
curl -X GET "http://localhost:8000/api/ranking/vacancy/{vacancy_id}/ranked?limit=50"
```

**Response:**
```json
{
  "vacancy_id": "VACANCY_UUID",
  "total_candidates": 3,
  "ranked_candidates": [
    {
      "resume_id": "resume1_uuid",
      "rank_score": 0.92,
      "recommendation": "excellent",
      "rank_position": 1
    },
    {
      "resume_id": "resume2_uuid",
      "rank_score": 0.78,
      "recommendation": "good",
      "rank_position": 2
    },
    {
      "resume_id": "resume3_uuid",
      "rank_score": 0.45,
      "recommendation": "maybe",
      "rank_position": 3
    }
  ]
}
```

#### Step 3: Batch Move Candidates to Stage

```bash
curl -X POST http://localhost:8000/api/candidates/bulk-move \
  -H "Content-Type: application/json" \
  -d '{
    "resume_ids": ["resume1_uuid", "resume2_uuid"],
    "stage_id": "screening",
    "vacancy_id": "VACANCY_UUID"
  }'
```

---

### Candidate Comparison Workflow

Compare multiple candidates side-by-side for a single vacancy.

#### Step 1: Create Comparison

```bash
curl -X POST http://localhost:8000/api/comparisons/ \
  -H "Content-Type: application/json" \
  -d '{
    "resume_ids": ["resume1_uuid", "resume2_uuid", "resume3_uuid"],
    "vacancy_id": "VACANCY_UUID"
  }'
```

**Response:**
```json
{
  "id": "comparison_uuid",
  "vacancy_title": "Senior Python Developer",
  "comparison_results": [
    {
      "resume_id": "resume1_uuid",
      "filename": "resume1.pdf",
      "rank": 1,
      "match_percentage": 92,
      "matched_skills": ["python", "fastapi", "postgresql"],
      "missing_skills": ["redis"]
    },
    {
      "resume_id": "resume2_uuid",
      "filename": "resume2.pdf",
      "rank": 2,
      "match_percentage": 78,
      "matched_skills": ["python", "postgresql"],
      "missing_skills": ["fastapi", "redis"]
    }
  ],
  "total_resumes": 3,
  "processing_time_ms": 450
}
```

#### Step 2: Retrieve Comparison Later

```bash
curl http://localhost:8000/api/comparisons/{comparison_id}
```

---

### Multi-Vacancy Matching

Match a single resume against multiple vacancies.

```bash
# Get all vacancies
curl http://localhost:8000/api/vacancies/

# For each vacancy, perform matching
for vacancy in $(cat vacancies.json | jq -r '.[].id'); do
  curl -X POST http://localhost:8000/api/matching/compare-unified \
    -H "Content-Type: application/json" \
    -d "{
      \"resume_id\": \"RESUME_UUID\",
      \"vacancy_data\": {
        \"id\": \"$vacancy\",
        \"title\": \"Vacancy Title\",
        \"required_skills\": [\"skill1\", \"skill2\"]
      }
    }"
done
```

---

## API Endpoint Categories

### Resumes & Analysis

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/resumes/upload` | POST | Upload resume file (PDF/DOCX) |
| `/api/resumes` | GET | List all resumes |
| `/api/resumes/{id}` | GET | Get resume details |
| `/api/resumes/{id}/analyze` | POST | Trigger resume analysis |
| `/api/resumes/{id}/parse` | POST | Parse resume into structured data |

### Job Vacancies

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/vacancies/` | POST | Create new vacancy |
| `/api/vacancies/` | GET | List all vacancies |
| `/api/vacancies/{id}` | GET | Get vacancy details |
| `/api/vacancies/{id}` | PUT | Update vacancy |
| `/api/vacancies/{id}` | DELETE | Delete vacancy |
| `/api/vacancies/{id}/candidates` | GET | Get candidates for vacancy |

### Matching

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/matching/compare` | POST | Keyword-based matching |
| `/api/matching/compare-unified` | POST | **Recommended** - Unified 3-method matching |
| `/api/matching/weights` | GET | Get matching weights |
| `/api/matching/weights` | PUT | Update matching weights |

### AI Ranking

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ranking/rank` | POST | Rank single candidate for vacancy |
| `/api/ranking/vacancy/{id}/ranked` | GET | Get all ranked candidates for vacancy |
| `/api/ranking/feedback` | POST | Submit feedback on ranking |
| `/api/ranking/models/importance` | GET | Get feature importance |
| `/api/ranking/models/versions` | GET | List model versions |
| `/api/ranking/fair-rank` | POST | Fairness-aware ranking |

### Candidates & Workflow

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/candidates/` | GET | List all candidates with stages |
| `/api/candidates/{id}/move` | PUT | Move candidate to workflow stage |
| `/api/candidates/bulk-move` | POST | Bulk move candidates |
| `/api/candidates/{id}/tags` | GET | Get candidate tags |
| `/api/candidates/{id}/notes` | GET | Get candidate notes |
| `/api/candidates/{id}/activities` | GET | Get candidate activities |

### Search

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/search/candidates` | POST | **Advanced** search with filters |
| `/api/search/history` | GET | Get search history |
| `/api/search/saved` | GET | Get saved searches |
| `/api/search/saved` | POST | Save a search |

### Comparisons

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/comparisons/` | POST | Create multi-resume comparison |
| `/api/comparisons/{id}` | GET | Get comparison results |
| `/api/comparisons/` | GET | List all comparisons |

### Skill Taxonomies

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/skill-taxonomies/` | POST | Create skill taxonomy entries |
| `/api/skill-taxonomies/{industry}` | GET | Get taxonomies by industry |
| `/api/skill-taxonomies/{id}` | PUT | Update taxonomy entry |
| `/api/skill-taxonomies/{id}` | DELETE | Delete taxonomy entry |

### Analytics & Reports

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analytics/dashboard` | GET | Get dashboard statistics |
| `/api/analytics/time-to-hire` | GET | Get time-to-hire metrics |
| `/api/reports/candidates` | POST | Generate candidate report |
| `/api/reports/export` | POST | Export data to CSV |

### System & Monitoring

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/ready` | GET | Readiness check |
| `/api/backups/create` | POST | Create database backup |
| `/api/performance/metrics` | GET | Get performance metrics |

---

## Language Integration Examples

### Python (requests)

```python
import requests
from typing import Dict, List

BASE_URL = "http://localhost:8000"

class AgentHRClient:
    """Python client for AgentHR API"""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()

    def upload_resume(self, file_path: str) -> Dict:
        """Upload a resume file"""
        with open(file_path, 'rb') as f:
            response = self.session.post(
                f"{self.base_url}/api/resumes/upload",
                files={'file': f}
            )
        response.raise_for_status()
        return response.json()

    def create_vacancy(self, vacancy_data: Dict) -> Dict:
        """Create a new job vacancy"""
        response = self.session.post(
            f"{self.base_url}/api/vacancies/",
            json=vacancy_data
        )
        response.raise_for_status()
        return response.json()

    def match_candidate(self, resume_id: str, vacancy_data: Dict) -> Dict:
        """Match resume to vacancy using unified matching"""
        response = self.session.post(
            f"{self.base_url}/api/matching/compare-unified",
            json={
                "resume_id": resume_id,
                "vacancy_data": vacancy_data
            }
        )
        response.raise_for_status()
        return response.json()

    def rank_candidate(self, resume_id: str, vacancy_id: str,
                      use_experiment: bool = True) -> Dict:
        """Rank candidate for vacancy using ML model"""
        response = self.session.post(
            f"{self.base_url}/api/ranking/rank",
            json={
                "resume_id": resume_id,
                "vacancy_id": vacancy_id,
                "use_experiment": use_experiment
            }
        )
        response.raise_for_status()
        return response.json()

    def get_ranked_candidates(self, vacancy_id: str,
                             limit: int = 50) -> Dict:
        """Get all ranked candidates for a vacancy"""
        response = self.session.get(
            f"{self.base_url}/api/ranking/vacancy/{vacancy_id}/ranked",
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()

    def submit_feedback(self, rank_id: str, was_helpful: bool,
                       actual_outcome: str = None) -> Dict:
        """Submit feedback on ranking"""
        response = self.session.post(
            f"{self.base_url}/api/ranking/feedback",
            json={
                "rank_id": rank_id,
                "was_helpful": was_helpful,
                "actual_outcome": actual_outcome
            }
        )
        response.raise_for_status()
        return response.json()

# Usage Example
if __name__ == "__main__":
    client = AgentHRClient()

    # Complete workflow
    resume = client.upload_resume("resume.pdf")
    vacancy = client.create_vacancy({
        "title": "Python Developer",
        "description": "We need a Python expert...",
        "required_skills": ["python", "fastapi"],
        "min_experience_months": 36
    })

    match = client.match_candidate(
        resume['id'],
        {
            "id": vacancy['id'],
            "title": vacancy['title'],
            "required_skills": vacancy['required_skills']
        }
    )

    ranking = client.rank_candidate(resume['id'], vacancy['id'])
    print(f"Recommendation: {ranking['recommendation']}")
    print(f"Score: {ranking['rank_score']:.2f}")
```

### JavaScript (fetch)

```javascript
const BASE_URL = 'http://localhost:8000';

class AgentHRClient {
  /**
   * JavaScript client for AgentHR API
   */
  constructor(baseUrl = BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async uploadResume(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/api/resumes/upload`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    return await response.json();
  }

  async createVacancy(vacancyData) {
    const response = await fetch(`${this.baseUrl}/api/vacancies/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(vacancyData)
    });

    if (!response.ok) {
      throw new Error(`Create vacancy failed: ${response.statusText}`);
    }

    return await response.json();
  }

  async matchCandidate(resumeId, vacancyData) {
    const response = await fetch(`${this.baseUrl}/api/matching/compare-unified`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        resume_id: resumeId,
        vacancy_data: vacancyData
      })
    });

    if (!response.ok) {
      throw new Error(`Matching failed: ${response.statusText}`);
    }

    return await response.json();
  }

  async rankCandidate(resumeId, vacancyId, useExperiment = true) {
    const response = await fetch(`${this.baseUrl}/api/ranking/rank`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        resume_id: resumeId,
        vacancy_id: vacancyId,
        use_experiment: useExperiment
      })
    });

    if (!response.ok) {
      throw new Error(`Ranking failed: ${response.statusText}`);
    }

    return await response.json();
  }

  async getRankedCandidates(vacancyId, limit = 50) {
    const response = await fetch(
      `${this.baseUrl}/api/ranking/vacancy/${vacancyId}/ranked?limit=${limit}`
    );

    if (!response.ok) {
      throw new Error(`Get ranked candidates failed: ${response.statusText}`);
    }

    return await response.json();
  }

  async submitFeedback(rankId, wasHelpful, actualOutcome) {
    const response = await fetch(`${this.baseUrl}/api/ranking/feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        rank_id: rankId,
        was_helpful: wasHelpful,
        actual_outcome: actualOutcome
      })
    });

    if (!response.ok) {
      throw new Error(`Submit feedback failed: ${response.statusText}`);
    }

    return await response.json();
  }
}

// Usage Example (async/await)
(async () => {
  const client = new AgentHRClient();

  // Upload resume from file input
  const fileInput = document.getElementById('resume-file');
  const resume = await client.uploadResume(fileInput.files[0]);

  // Create vacancy
  const vacancy = await client.createVacancy({
    title: 'Python Developer',
    description: 'We need a Python expert...',
    required_skills: ['python', 'fastapi'],
    min_experience_months: 36
  });

  // Match and rank
  const match = await client.matchCandidate(resume.id, {
    id: vacancy.id,
    title: vacancy.title,
    required_skills: vacancy.required_skills
  });

  const ranking = await client.rankCandidate(resume.id, vacancy.id);

  console.log(`Recommendation: ${ranking.recommendation}`);
  console.log(`Score: ${ranking.rank_score.toFixed(2)})();

// Usage Example (React)
function useAgentHR() {
  const client = useMemo(() => new AgentHRClient(), []);

  const uploadResume = useCallback(async (file) => {
    return await client.uploadResume(file);
  }, [client]);

  const rankCandidate = useCallback(async (resumeId, vacancyId) => {
    return await client.rankCandidate(resumeId, vacancyId);
  }, [client]);

  return { uploadResume, rankCandidate };
}
```

### Node.js (axios)

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

const BASE_URL = 'http://localhost:8000';

class AgentHRClient {
  constructor(baseUrl = BASE_URL) {
    this.client = axios.create({
      baseURL: baseUrl,
      timeout: 30000
    });
  }

  async uploadResume(filePath) {
    const form = new FormData();
    form.append('file', fs.createReadStream(filePath));

    const response = await this.client.post('/api/resumes/upload', form, {
      headers: form.getHeaders()
    });

    return response.data;
  }

  async createVacancy(vacancyData) {
    const response = await this.client.post('/api/vacancies/', vacancyData);
    return response.data;
  }

  async matchCandidate(resumeId, vacancyData) {
    const response = await this.client.post('/api/matching/compare-unified', {
      resume_id: resumeId,
      vacancy_data: vacancyData
    });

    return response.data;
  }

  async rankCandidate(resumeId, vacancyId, useExperiment = true) {
    const response = await this.client.post('/api/ranking/rank', {
      resume_id: resumeId,
      vacancy_id: vacancyId,
      use_experiment: useExperiment
    });

    return response.data;
  }

  async getRankedCandidates(vacancyId, limit = 50) {
    const response = await this.client.get(
      `/api/ranking/vacancy/${vacancyId}/ranked`,
      { params: { limit } }
    );

    return response.data;
  }
}

// Usage Example
(async () => {
  const client = new AgentHRClient();

  try {
    const resume = await client.uploadResume('./resume.pdf');
    const vacancy = await client.createVacancy({
      title: 'Python Developer',
      description: 'We need a Python expert...',
      required_skills: ['python', 'fastapi'],
      min_experience_months: 36
    });

    const match = await client.matchCandidate(resume.id, {
      id: vacancy.id,
      title: vacancy.title,
      required_skills: vacancy.required_skills
    });

    const ranking = await client.rankCandidate(resume.id, vacancy.id);

    console.log(`Recommendation: ${ranking.recommendation}`);
    console.log(`Score: ${ranking.rank_score.toFixed(2)}`);
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
})();
```

---

## Best Practices

### 1. Use Unified Matching

**Always prefer** `/api/matching/compare-unified` over other matching endpoints:

```bash
# ✅ RECOMMENDED - Combines 3 matching methods
curl -X POST http://localhost:8000/api/matching/compare-unified \
  -H "Content-Type: application/json" \
  -d '{"resume_id": "...", "vacancy_data": {...}}'

# ⚠️ LESS ACCURATE - Single method only
curl -X POST http://localhost:8000/api/matching/compare \
  -H "Content-Type: application/json" \
  -d '{"resume_id": "...", "vacancy_data": {...}}'
```

**Why?** Unified matching combines:
- Keyword matching (exact skill matches)
- TF-IDF matching (weighted relevance)
- Vector similarity (semantic understanding)

### 2. Handle Resume Processing Asynchronously

Resume analysis happens in the background. Check status before matching:

```python
import time

def wait_for_analysis(resume_id, timeout=60):
    """Wait for resume analysis to complete"""
    start = time.time()
    while time.time() - start < timeout:
        resume = client.get_resume(resume_id)
        if resume['status'] == 'analyzed':
            return True
        time.sleep(2)
    raise TimeoutError("Resume analysis timeout")
```

### 3. Use Batch Operations for Multiple Resumes

```bash
# ❌ INEFFICIENT - Multiple requests
curl -X PUT http://localhost:8000/api/candidates/id1/move -d '{"stage_id": "interview"}'
curl -X PUT http://localhost:8000/api/candidates/id2/move -d '{"stage_id": "interview"}'
curl -X PUT http://localhost:8000/api/candidates/id3/move -d '{"stage_id": "interview"}'

# ✅ EFFICIENT - Single batch request
curl -X POST http://localhost:8000/api/candidates/bulk-move \
  -H "Content-Type: application/json" \
  -d '{
    "resume_ids": ["id1", "id2", "id3"],
    "stage_id": "interview"
  }'
```

### 4. Submit Feedback for Model Improvement

Always submit feedback on rankings to improve the ML model:

```bash
curl -X POST http://localhost:8000/api/ranking/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "rank_id": "RANK_UUID",
    "was_helpful": true,
    "actual_outcome": "hired",
    "rating": 5,
    "comments": "Candidate was excellent fit"
  }'
```

### 5. Implement Pagination for Large Result Sets

```python
def get_all_candidates(vacancy_id, batch_size=50):
    """Paginate through all candidates for a vacancy"""
    all_candidates = []
    skip = 0

    while True:
        batch = client.get_ranked_candidates(
            vacancy_id,
            limit=batch_size,
            skip=skip
        )

        if not batch['candidates']:
            break

        all_candidates.extend(batch['candidates'])

        if len(batch['candidates']) < batch_size:
            break

        skip += batch_size

    return all_candidates
```

### 6. Use Search for Complex Filtering

Instead of manually filtering, use the search API:

```bash
curl -X POST http://localhost:8000/api/search/candidates \
  -H "Content-Type: application/json" \
  -d '{
    "query": "python developer",
    "filters": {
      "skills": ["python", "fastapi"],
      "min_experience_years": 3,
      "min_match_score": 70
    },
    "sort_by": "relevance",
    "limit": 20
  }'
```

### 7. Cache Vacancy Data

Cache vacancy data locally to avoid repeated requests:

```python
vacancy_cache = {}

def get_vacancy(vacancy_id):
    """Get vacancy with caching"""
    if vacancy_id not in vacancy_cache:
        vacancy_cache[vacancy_id] = client.get_vacancy(vacancy_id)
    return vacancy_cache[vacancy_id]
```

### 8. Error Handling with Retries

Implement exponential backoff for transient failures:

```python
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)
```

### 9. Validate Data Before API Calls

Validate required fields before making API requests:

```python
def validate_vacancy_data(data):
    """Validate vacancy data before API call"""
    required_fields = ['title', 'description', 'required_skills']
    for field in required_fields:
        if field not in data or not data[field]:
            raise ValueError(f"Missing required field: {field}")

    if len(data['required_skills']) == 0:
        raise ValueError("At least one required skill must be specified")

    return True
```

### 10. Monitor API Health

Check health status before critical operations:

```bash
# Always check health first
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "API is healthy, proceeding with operations"
else
    echo "API is unhealthy, aborting"
    exit 1
fi
```

---

## Rate Limiting & Performance

### Current Limits

| Resource | Limit |
|----------|-------|
| Upload size | 10 MB per file |
| Concurrent requests | No hard limit (PostgreSQL connection pool) |
| Resume processing | ~5-10 seconds per resume (async) |
| Matching latency | ~500ms per match |
| Ranking latency | ~200ms per rank |

### Performance Tips

1. **Use batch operations** for multiple candidates
2. **Enable compression** in HTTP client (`Accept-Encoding: gzip`)
3. **Reuse HTTP connections** (connection pooling)
4. **Cache frequently accessed data** (vacancies, taxonomies)
5. **Monitor performance metrics** at `/api/performance/metrics`

---

## Advanced Features

### A/B Testing for Ranking Models

The ranking system supports A/B testing:

```python
# Assign candidate to experiment group
ranking = client.rank_candidate(
    resume_id="RESUME_ID",
    vacancy_id="VACANCY_ID",
    use_experiment=True  # Enable A/B testing
)

print(f"Experiment Group: {ranking['experiment_group']}")
# Output: "control" or "treatment"
```

### Fairness-Aware Ranking

Enable bias mitigation for fair hiring:

```bash
curl -X POST http://localhost:8000/api/ranking/fair-rank \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "RESUME_ID",
    "vacancy_id": "VACANCY_ID",
    "enable_fairness": true,
    "mitigation_strategy": "equal_opportunity"
  }'
```

**Available strategies:**
- `equal_opportunity` - Equalize true positive rates
- `demographic_parity` - Equalize selection rates
- `adversarial` - Adversarial debiasing

### Skill Taxonomy Management

Create and manage industry-specific skill taxonomies:

```bash
# Create taxonomy entries
curl -X POST http://localhost:8000/api/skill-taxonomies/ \
  -H "Content-Type: application/json" \
  -d '{
    "industry": "technology",
    "skills": [
      {
        "name": "Python",
        "context": "programming_language",
        "variants": ["Python", "python", "py"],
        "extra_metadata": {
          "category": "backend",
          "demand_level": "high"
        }
      },
      {
        "name": "FastAPI",
        "context": "web_framework",
        "variants": ["FastAPI", "fastapi", "Fast Api"]
      }
    ]
  }'
```

### Custom Skill Synonyms

Override default skill synonyms:

```bash
curl -X POST http://localhost:8000/api/custom-synonyms/ \
  -H "Content-Type: application/json" \
  -d '{
    "canonical_skill": "PostgreSQL",
    "synonyms": ["PostgreSQL", "postgres", "Postgres SQL", "psql"],
    "organization_id": "org_uuid"
  }'
```

### Interview Preparation

Generate interview questions based on resume and vacancy:

```bash
curl -X POST http://localhost:8000/api/interview-prep/generate \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "RESUME_ID",
    "vacancy_id": "VACANCY_ID",
    "question_count": 10
  }'
```

**Response:**
```json
{
  "questions": [
    {
      "question": "Explain your experience with FastAPI",
      "category": "technical",
      "difficulty": "intermediate",
      "related_skills": ["fastapi", "python"]
    }
  ]
}
```

### Skill Gap Analysis

Analyze skill gaps for candidates:

```bash
curl -X POST http://localhost:8000/api/skill-gap/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "RESUME_ID",
    "vacancy_id": "VACANCY_ID"
  }'
```

**Response:**
```json
{
  "missing_skills": [
    {
      "skill": "Kubernetes",
      "priority": "high",
      "learning_resources": [
        "https://kubernetes.io/docs/",
        "https://www.udemy.com/course/kubernetes"
      ]
    }
  ],
  "skill_gap_score": 0.25
}
```

### Export & Reporting

Export candidate data to CSV:

```bash
curl -X POST http://localhost:8000/api/reports/export \
  -H "Content-Type: application/json" \
  -d '{
    "vacancy_id": "VACANCY_ID",
    "format": "csv",
    "include_fields": ["filename", "skills", "experience", "rank_score"]
  }'
```

### Backup & Restore

Create database backups:

```bash
# Create backup
curl -X POST http://localhost:8000/api/backups/create \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Pre-production backup"
  }'

# List backups
curl http://localhost:8000/api/backups/
```

---

## Complete API Reference

For the complete, auto-generated OpenAPI documentation with all endpoints, request schemas, and response models, visit:

**Interactive Swagger UI:** http://localhost:8000/docs

**ReDoc Documentation:** http://localhost:8000/redoc

**OpenAPI Schema:** http://localhost:8000/openapi.json

---

## Troubleshooting

### Common Issues

#### 1. Resume Status Stuck at "pending"

**Problem:** Resume remains in "pending" status after upload.

**Solution:** Resume analysis is asynchronous. Wait 5-10 seconds, then check status again:

```bash
curl http://localhost:8000/api/resumes/{resume_id}
```

If still pending after 30 seconds, check Celery worker logs:

```bash
docker-compose logs backend -f
```

#### 2. Low Match Scores Despite Skills Matching

**Problem:** Match score is low even though skills appear to match.

**Solution:** Check for:
- Skill synonyms (e.g., "postgres" should match "PostgreSQL")
- Experience requirements (candidate may lack required experience)
- Vector similarity (semantic meaning may not align)

Use unified matching for best results.

#### 3. Ranking Returns "poor" Recommendation

**Problem:** High match score but low ranking score.

**Solution:** Ranking uses 13 features, not just skills. Check:
- Experience relevance to job requirements
- Education level
- Resume completeness
- Skill rarity

Use `/api/ranking/models/importance` to see feature weights.

#### 4. "File Not Found" Error During Matching

**Problem:** Matching fails with file not found error.

**Solution:** Verify:
- Resume ID is correct
- Resume file exists in `data/uploads/`
- Resume status is "analyzed", not "pending"

```bash
# Check resume status
curl http://localhost:8000/api/resumes/{resume_id}
```

#### 5. CORS Errors in Browser

**Problem:** Browser blocks API requests due to CORS.

**Solution:** Ensure frontend origin is in CORS settings:

```python
# In config.py
cors_origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://your-frontend-domain.com"
]
```

---

## Support & Resources

### Documentation

- **ML Pipeline:** [ML_PIPELINE.md](ML_PIPELINE.md)
- **Dataset Usage:** [docs/dataset-usage-guide.md](docs/dataset-usage-guide.md)
- **Main README:** [README.md](README.md)

### Getting Help

1. Check the interactive API docs at `/docs`
2. Review example workflows in this guide
3. Check logs: `docker-compose logs backend -f`
4. Open an issue on GitHub

### Contributing

When contributing API endpoints:
1. Add Pydantic models for request/response
2. Include docstrings with examples
3. Add error handling
4. Update this usage guide

---

## Changelog

### Version 1.0.0 (Current)

- Initial release with 33 API routers
- Unified matching system (3 methods)
- ML-based candidate ranking (13 features)
- A/B testing support
- Fairness-aware ranking
- Skill taxonomy management
- Advanced search & filtering
- Workflow stage management
- Multi-language support (EN/RU)

---

**Last Updated:** 2026-02-01

**API Version:** 1.0.0
