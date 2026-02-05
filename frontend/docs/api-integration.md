# API Integration Guide

> **AgentHR Frontend API Integration Documentation**
> **Last updated:** 2026-02-05

## Overview

This guide explains how the AgentHR frontend integrates with the backend microservices architecture through the API Gateway. The frontend communicates with all backend services via a single API Gateway endpoint, simplifying client-side configuration and enabling centralized routing, authentication, and rate limiting.

## Architecture

### Microservices Architecture

The AgentHR backend is decomposed into 10 microservices:

| Service | Port | Purpose |
|---------|------|---------|
| API Gateway | 8888 | Single entry point, routing, authentication |
| Resume Processing Service | 8001 | Resume upload, parsing, analysis |
| Matching Service | 8002 | Skill matching, candidate ranking |
| Candidate Service | 8003 | Candidate CRUD, notes, tags, activities |
| Vacancy Service | 8004 | Job vacancy management |
| Taxonomy Service | 8005 | Skill taxonomies, synonyms |
| Analytics Service | 8006 | Dashboards, reports, metrics |
| ATS Simulation Service | 8007 | ATS scoring, screening |
| Notification Service | 8008 | Email, SMS, webhook notifications |
| Integration Service | 8009 | Third-party integrations |

### API Gateway

**Base URL:** `http://localhost:8888` (development)

The API Gateway handles:
- Request routing to appropriate microservices
- JWT token validation
- Rate limiting and throttling
- CORS handling
- Request/response transformation

**Important:** The frontend only needs to know the API Gateway URL. Individual service URLs are abstracted away.

## Configuration

### Environment Variables

Create a `.env` file in the frontend root directory:

```bash
# API Gateway URL (only this is needed)
VITE_API_URL=http://localhost:8888

# Optional: Override timeout (default: 120000ms = 2 minutes)
VITE_API_TIMEOUT=120000
```

### Development Proxy

For local development with Vite, the `vite.config.ts` includes a proxy configuration:

```typescript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8888',
        changeOrigin: true,
      },
    },
  },
});
```

This means all requests to `/api/*` during development are automatically proxied to the API Gateway.

## API Client

### Basic Usage

The frontend uses a typed Axios client (`apiClient`) for all API communication:

```typescript
import { apiClient } from '@/api/client';

// Upload resume
const uploadResult = await apiClient.uploadResume(file);

// Analyze resume
const analysis = await apiClient.analyzeResume({
  resume_id: uploadResult.id,
  extract_experience: true,
  check_grammar: true,
});

// Compare with job vacancy
const match = await apiClient.compareWithVacancy(resumeId, vacancyData);
```

### Error Handling

The API client automatically transforms errors into a standardized format:

```typescript
interface ApiError {
  detail: string;      // User-friendly error message
  status: number;      // HTTP status code
}

// Example usage
try {
  const result = await apiClient.uploadResume(file);
} catch (error) {
  console.error(error.detail);  // "File too large. Please upload a smaller file."
  console.error(error.status);  // 413
}
```

### Standard Error Messages

| Status | Message |
|--------|---------|
| 400 | Invalid request. Please check your input. |
| 401 | Unauthorized. Please log in. |
| 403 | Forbidden. You do not have permission. |
| 404 | Resource not found. |
| 408 | Request timeout. Please check your connection and try again. |
| 413 | File too large. Please upload a smaller file. |
| 415 | Unsupported file type. Please upload PDF or DOCX. |
| 422 | Validation error. Please check your input. |
| 429 | Too many requests. Please try again later. |
| 500 | Server error. Please try again later. |
| 502 | Bad gateway. Please try again later. |
| 503 | Service unavailable. Please try again later. |

## API Endpoints Reference

### Resume Management

#### Upload Resume

```typescript
const result = await apiClient.uploadResume(file, (progress) => {
  console.log(`Upload: ${progress}%`);
});

// Result:
interface ResumeUploadResponse {
  id: string;           // Resume UUID
  filename: string;     // Original filename
  status: string;       // "uploaded" | "processing" | "completed"
}
```

#### Analyze Resume

```typescript
const analysis = await apiClient.analyzeResume({
  resume_id: 'abc-123',
  extract_experience: true,
  check_grammar: true,
  locale: 'en',
});

// Result includes:
// - keywords: Extracted skills
// - entities: Named entities (people, companies, etc.)
// - grammar_issues: Grammar and spelling problems
// - experience: Work history with verification
```

### Candidate Management

#### List Candidates

```typescript
const candidates = await apiClient.listCandidates(
  stageId,      // Optional: filter by stage
  vacancyId,    // Optional: filter by vacancy
  skip,         // Pagination: default 0
  limit         // Pagination: default 100
);

// Result:
interface CandidateListItem {
  id: string;           // Resume UUID
  name: string;
  email: string;
  current_stage: string;
  stage_name: string;
  tags: string[];
  match_score?: number;
}
```

#### Move Candidate Stage

```typescript
const result = await apiClient.moveCandidate(candidateId, {
  stage_id: 'interview',
  vacancy_id: 'vacancy-123',  // Optional
  notes: 'Passed screening'
});

// Result:
interface MoveCandidateResponse {
  previous_stage: string;
  new_stage: string;
  hiring_stage_id: string;
}
```

### Job Matching

#### Compare Resume with Vacancy

```typescript
const match = await apiClient.compareWithVacancy(resumeId, {
  data: {
    position: 'Java Developer',
    mandatory_requirements: ['Java', 'Spring', 'SQL'],
    optional_requirements: ['Docker', 'Kubernetes'],
  }
});

// Result includes:
// - overall_score: 0-100 match percentage
// - matched_skills: Skills that match
// - missing_skills: Required skills not found
// - experience_match: Experience relevance score
```

#### Compare Multiple Resumes

```typescript
const comparison = await apiClient.compareMultipleResumes({
  vacancy_id: 'vacancy-123',
  resume_ids: ['resume1', 'resume2', 'resume3'],
});

// Result:
interface ComparisonMatrixData {
  vacancy_id: string;
  comparisons: Array<{
    resume_id: string;
    match_percentage: number;
    matched_skills: string[];
    missing_skills: string[];
  }>;
  ranking: Array<{resume_id: string; rank: number}>;
}
```

### ATS Simulation

#### Evaluate Resume

```typescript
const atsResult = await apiClient.evaluateATS({
  resume_id: 'resume-123',
  vacancy_id: 'vacancy-456',
  use_llm: true,  // Use LLM for enhanced analysis
});

// Result:
interface ATSEvaluationResponse {
  passed: boolean;          // Overall pass/fail
  overall_score: number;    // 0-1 score
  keyword_score: number;    // Keyword match score
  format_score: number;     // Format compliance score
  missing_keywords: string[];
  format_issues: string[];
  recommendations: string[];
}
```

### Analytics

#### Get Key Metrics

```typescript
const metrics = await apiClient.getKeyMetrics(
  '2024-01-01',  // Optional start date
  '2024-12-31'   // Optional end date
);

// Result:
interface KeyMetricsResponse {
  time_to_hire_days: number;
  resumes_processed: number;
  match_rate: number;
  placement_rate: number;
}
```

#### Get Funnel Metrics

```typescript
const funnel = await apiClient.getFunnelMetrics();

// Result shows candidate progression:
interface FunnelMetricsResponse {
  stages: Array<{
    stage_name: string;
    count: number;
    conversion_rate: number;
  }>;
  total_candidates: number;
}
```

### Skill Taxonomies

#### Create Skill Taxonomy

```typescript
const result = await apiClient.createSkillTaxonomies({
  industry: 'tech',
  skills: [
    {
      name: 'React',
      context: 'web_framework',
      variants: ['React', 'ReactJS', 'React.js'],
      is_active: true,
    },
  ],
});
```

#### Create Custom Synonyms

```typescript
const result = await apiClient.createCustomSynonyms({
  organization_id: 'org123',
  created_by: 'user456',
  synonyms: [
    {
      canonical_skill: 'React',
      custom_synonyms: ['ReactJS', 'React.js'],
      context: 'web_framework',
      is_active: true,
    },
  ],
});
```

### Matching Weights

#### Create Custom Weight Profile

```typescript
const profile = await apiClient.createWeightProfile({
  name: 'My Technical Profile',
  description: 'High keyword weight for technical roles',
  keyword_weight: 0.6,
  tfidf_weight: 0.25,
  vector_weight: 0.15,
});

// Apply to vacancy
await apiClient.applyWeights({
  vacancy_id: 'vacancy-123',
  profile_id: profile.id,
  re_match_candidates: true,
});
```

## Performance Tracking

The API client automatically tracks performance metrics:

```typescript
// Get performance statistics
const stats = apiClient.getPerformanceStats();
console.log(`Average duration: ${stats.averageDuration}ms`);
console.log(`Total calls: ${stats.totalCalls}`);
console.log(`Success rate: ${stats.successRate}%`);

// Log detailed summary
apiClient.logPerformanceSummary();
```

### Performance Metrics

| Metric | Description |
|--------|-------------|
| `totalCalls` | Total number of API calls |
| `successfulCalls` | Number of successful calls |
| `failedCalls` | Number of failed calls |
| `averageDuration` | Average request duration (ms) |
| `minDuration` | Minimum request duration (ms) |
| `maxDuration` | Maximum request duration (ms) |
| `successRate` | Percentage of successful calls |

## Authentication

### JWT Token Handling

The frontend uses JWT tokens for authentication. The API Gateway validates all tokens before routing requests to microservices.

```typescript
// Token is typically stored in localStorage or cookies
const token = localStorage.getItem('auth_token');

// The API client can be extended to include the token in headers:
const client = new ApiClient({
  baseURL: 'http://localhost:8888',
  headers: {
    'Authorization': `Bearer ${token}`,
  },
});
```

### Token Refresh

If using refresh tokens:

```typescript
// Axios interceptor example for token refresh
client.interceptors.response.use(
  response => response,
  async error => {
    if (error.status === 401) {
      // Token expired, refresh it
      const newToken = await refreshAuthToken();
      // Retry original request with new token
      error.config.headers.Authorization = `Bearer ${newToken}`;
      return client.request(error.config);
    }
    return Promise.reject(error);
  }
);
```

## Best Practices

### 1. Use Type-Safe API Calls

Always use the typed `apiClient` methods:

```typescript
// ✅ Good - Type-safe
const analysis = await apiClient.analyzeResume(request);

// ❌ Bad - Not type-safe
const analysis = await apiClient.post('/api/resumes/analyze', request);
```

### 2. Handle Errors Gracefully

```typescript
try {
  const result = await apiClient.uploadResume(file);
  showToast('Resume uploaded successfully', 'success');
} catch (error) {
  showToast(error.detail, 'error');
  // Log for debugging
  console.error('Upload failed:', error);
}
```

### 3. Show Loading States

```typescript
const [loading, setLoading] = useState(false);
const [progress, setProgress] = useState(0);

const handleUpload = async (file: File) => {
  setLoading(true);
  try {
    const result = await apiClient.uploadResume(file, (p) => {
      setProgress(p);
    });
    // ... handle success
  } catch (error) {
    // ... handle error
  } finally {
    setLoading(false);
  }
};
```

### 4. Cache Results When Appropriate

```typescript
import { useQuery } from '@tanstack/react-query';

const { data, isLoading, error } = useQuery({
  queryKey: ['candidates', stageId],
  queryFn: () => apiClient.listCandidates(stageId),
  staleTime: 5 * 60 * 1000, // 5 minutes
});
```

### 5. Optimize File Uploads

For large file uploads, consider chunked uploads:

```typescript
// Progress callback for UX feedback
const result = await apiClient.uploadResume(file, (progress) => {
  updateProgressBar(progress);
});
```

## Troubleshooting

### Common Issues

#### 1. CORS Errors

**Problem:** Browser blocks requests due to CORS policy.

**Solution:** Ensure API Gateway CORS is configured correctly:
- Check `VITE_API_URL` matches the API Gateway URL
- Verify API Gateway allows requests from your frontend origin

#### 2. Timeouts on Large File Uploads

**Problem:** Resume upload times out for large files.

**Solution:**
- Check `VITE_API_TIMEOUT` is set sufficiently high (default: 120000ms)
- Show progress to user during upload
- Consider compressing files before upload

#### 3. 401 Unauthorized Errors

**Problem:** All requests return 401 status.

**Solution:**
- Verify JWT token is valid and not expired
- Check token is included in request headers
- Confirm API Gateway JWT validation is working

#### 4. Service Unavailable (503)

**Problem:** API Gateway returns 503 status.

**Solution:**
- Verify microservices are running
- Check API Gateway can reach all services
- Review service health endpoints

### Debug Mode

Enable verbose logging for debugging:

```typescript
// In vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8888',
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on('proxyReq', (proxyReq) => {
            console.log('[Proxy]', proxyReq.method, proxyReq.path);
          });
        },
      },
    },
  },
});
```

## Migration from Monolith

If migrating from the monolithic backend (port 8000) to microservices (port 8888):

### Configuration Changes

```bash
# Old (monolith)
VITE_API_URL=http://localhost:8000

# New (microservices with API Gateway)
VITE_API_URL=http://localhost:8888
```

### API Compatibility

All existing API endpoints remain compatible. The API Gateway routes requests to the appropriate microservice transparently:

| Old Endpoint | New Routing |
|-------------|-------------|
| `/api/resumes/upload` | → Resume Processing Service |
| `/api/matching/compare` | → Matching Service |
| `/api/candidates/` | → Candidate Service |
| `/api/vacancies/` | → Vacancy Service |

**No code changes required** for basic API calls. The frontend automatically benefits from:
- Better scalability
- Improved fault tolerance
- Enhanced performance through service isolation

## Related Documentation

- [Frontend Architecture](architecture.md) - Overall frontend architecture
- [Component Library](components.md) - Reusable UI components
- [Backend API Documentation](../docs/api/) - Detailed backend API docs for each microservice

## Support

For issues or questions:
1. Check this guide's troubleshooting section
2. Review backend API docs for endpoint specifics
3. Check API Gateway logs for routing issues
4. Verify microservice health status
