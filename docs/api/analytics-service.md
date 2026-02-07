# Analytics Service API Documentation

## Overview

The Analytics Service provides comprehensive analytics dashboards, reports, metrics, and batch operations for tracking recruitment performance. It aggregates data from all services to provide insights into time-to-hire, resume processing, match rates, and ML model quality.

## Base URL

```
http://localhost:8006
```

Via API Gateway:
```
http://localhost:8888/api/analytics
```

## Authentication

All endpoints require JWT authentication via the API Gateway. Include the `Authorization` header with your Bearer token:

```
Authorization: Bearer <your-jwt-token>
```

---

## Endpoints

### Get Key Metrics

Get key recruitment analytics metrics.

**Endpoint:** `GET /api/analytics/key-metrics`

**Query Parameters:**
- `start_date` (optional) - Filter start date (ISO 8601 format)
- `end_date` (optional) - Filter end date (ISO 8601 format)

**Response:** `200 OK`

```json
{
  "time_to_hire": {
    "average_days": 32.5,
    "median_days": 28.0,
    "min_days": 7,
    "max_days": 90,
    "percentile_25": 21.0,
    "percentile_75": 45.0
  },
  "resumes": {
    "total_processed": 1250,
    "processed_this_month": 180,
    "processed_this_week": 42,
    "processing_rate_avg": 8.5
  },
  "match_rates": {
    "overall_match_rate": 0.78,
    "high_confidence_matches": 890,
    "low_confidence_matches": 156,
    "average_confidence": 0.72
  }
}
```

**Metric Descriptions:**

| Metric | Description |
|--------|-------------|
| `time_to_hire.average_days` | Average days from first contact to hire |
| `time_to_hire.median_days` | Median days to hire |
| `resumes.total_processed` | Total resumes processed |
| `resumes.processing_rate_avg` | Average resumes processed per day |
| `match_rates.overall_match_rate` | Overall skill match rate (0-1) |
| `match_rates.average_confidence` | Average confidence score (0-1) |

**Example:**
```bash
curl -X GET "http://localhost:8888/api/analytics/key-metrics?start_date=2025-01-01&end_date=2025-01-31" \
  -H "Authorization: Bearer <token>"
```

---

### Get Quality Metrics

Get ML/NLP model quality metrics.

**Endpoint:** `GET /api/analytics/quality-metrics`

**Query Parameters:**
- `start_date` (optional) - Filter start date (ISO 8601 format)
- `end_date` (optional) - Filter end date (ISO 8601 format)

**Response:** `200 OK`

```json
{
  "text_extraction_success_rate": 0.98,
  "avg_extraction_time_seconds": 2.5,
  "ner_accuracy": 0.85,
  "entities_per_resume_avg": 15.5,
  "avg_keywords_per_resume": 12.3,
  "keyword_relevance_avg": 0.78,
  "grammar_error_rate": 0.15,
  "matching_confidence_avg": 0.75,
  "matching_precision": 0.82,
  "matching_recall": 0.71,
  "avg_analysis_time_seconds": 5.2,
  "error_rate": 0.03,
  "total_analyzed": 1250
}
```

**Metric Descriptions:**

| Metric | Description |
|--------|-------------|
| `text_extraction_success_rate` | Success rate of PDF/DOCX text extraction |
| `ner_accuracy` | Named Entity Recognition F1 score |
| `entities_per_resume_avg` | Average entities extracted per resume |
| `avg_keywords_per_resume` | Average keywords extracted per resume |
| `matching_precision` | Precision of skill matching |
| `matching_recall` | Recall of skill matching |
| `error_rate` | Analysis error rate |

---

### Get Dashboard Data

Get comprehensive dashboard data for analytics UI.

**Endpoint:** `GET /api/analytics/dashboard`

**Query Parameters:**
- `period` (optional, default: "30d") - Time period (7d, 30d, 90d, 1y)

**Response:** `200 OK`

```json
{
  "summary": {
    "total_candidates": 450,
    "active_vacancies": 25,
    "hires_this_month": 12,
    "avg_time_to_hire": 28
  },
  "funnel": {
    "applied": 500,
    "screening": 350,
    "interview": 100,
    "offer": 25,
    "hired": 12
  },
  "trends": {
    "applications_per_day": [10, 15, 12, 18, 20, 14, 16],
    "hires_per_week": [2, 3, 1, 4, 2, 3, 2, 1]
  },
  "top_sources": [
    {"source": "LinkedIn", "count": 180},
    {"source": "Referral", "count": 95},
    {"source": "Indeed", "count": 75}
  ]
}
```

---

## Reports Endpoints

### List Reports

Get all available reports.

**Endpoint:** `GET /api/reports`

**Query Parameters:**
- `report_type` (optional) - Filter by report type
- `status` (optional) - Filter by status (generating, completed, failed)

**Response:** `200 OK`

```json
{
  "total": 15,
  "reports": [
    {
      "id": "report-1",
      "name": "Monthly Hiring Report",
      "report_type": "hiring_summary",
      "status": "completed",
      "created_at": "2025-01-15T10:00:00Z",
      "file_url": "https://storage.example.com/reports/report-1.pdf"
    }
  ]
}
```

---

### Create Report

Generate a new report.

**Endpoint:** `POST /api/reports`

**Request Body:**
```json
{
  "name": "Monthly Hiring Report",
  "report_type": "hiring_summary",
  "parameters": {
    "start_date": "2025-01-01",
    "end_date": "2025-01-31",
    "include_charts": true,
    "format": "pdf"
  }
}
```

**Report Types:**
- `hiring_summary` - Overall hiring summary
- `time_to_hire_analysis` - Time-to-hire breakdown
- `source_effectiveness` - Source effectiveness analysis
- `skill_gap_report` - Skill gap analysis
- `candidate_quality` - Candidate quality metrics

**Response:** `201 Created`

```json
{
  "id": "report-2",
  "name": "Monthly Hiring Report",
  "report_type": "hiring_summary",
  "status": "generating",
  "created_at": "2025-01-15T11:00:00Z"
}
```

---

### Get Report

Get a specific report.

**Endpoint:** `GET /api/reports/{report_id}`

**Path Parameters:**
- `report_id` (required) - ID of the report

**Response:** `200 OK`

```json
{
  "id": "report-1",
  "name": "Monthly Hiring Report",
  "report_type": "hiring_summary",
  "status": "completed",
  "parameters": {...},
  "file_url": "https://storage.example.com/reports/report-1.pdf",
  "created_at": "2025-01-15T10:00:00Z",
  "completed_at": "2025-01-15T10:05:00Z"
}
```

---

### Delete Report

Delete a report.

**Endpoint:** `DELETE /api/reports/{report_id}`

**Path Parameters:**
- `report_id` (required) - ID of the report

**Response:** `204 No Content`

---

## Batch Operations Endpoints

### Start Batch Job

Start a batch processing job.

**Endpoint:** `POST /api/batch/start`

**Request Body:**
```json
{
  "job_type": "bulk_match",
  "parameters": {
    "vacancy_id": "vacancy-123",
    "resume_ids": ["resume-1", "resume-2", "resume-3"]
  }
}
```

**Job Types:**
- `bulk_match` - Bulk match candidates to vacancy
- `bulk_analyze` - Bulk analyze resumes
- `bulk_export` - Bulk export data
- `bulk_import` - Bulk import data

**Response:** `201 Created`

```json
{
  "job_id": "job-abc-123",
  "job_type": "bulk_match",
  "status": "queued",
  "created_at": "2025-01-15T11:00:00Z"
}
```

---

### Get Job Status

Get status of a batch job.

**Endpoint:** `GET /api/batch/{job_id}/status`

**Path Parameters:**
- `job_id` (required) - ID of the batch job

**Response:** `200 OK`

```json
{
  "job_id": "job-abc-123",
  "job_type": "bulk_match",
  "status": "processing",
  "progress": 0.66,
  "total_items": 100,
  "processed_items": 66,
  "failed_items": 2,
  "started_at": "2025-01-15T11:00:00Z",
  "estimated_completion": "2025-01-15T11:05:00Z"
}
```

**Status Values:**
- `queued` - Job is queued
- `processing` - Job is processing
- `completed` - Job completed successfully
- `failed` - Job failed
- `cancelled` - Job was cancelled

---

### Cancel Job

Cancel a running batch job.

**Endpoint:** `POST /api/batch/{job_id}/cancel`

**Path Parameters:**
- `job_id` (required) - ID of the batch job

**Response:** `200 OK`

```json
{
  "job_id": "job-abc-123",
  "status": "cancelled",
  "message": "Job cancelled successfully"
}
```

---

## Data Models

### Report Status Enum

| Status | Description |
|--------|-------------|
| `generating` | Report is being generated |
| `completed` | Report generation completed |
| `failed` | Report generation failed |

### Report Format Enum

| Format | Description |
|--------|-------------|
| `pdf` | PDF format |
| `xlsx` | Excel spreadsheet |
| `csv` | CSV file |
| `json` | JSON data |

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
- `500 Internal Server Error` - Server error

---

## Rate Limiting

Via API Gateway:
- 100 requests per second
- 10,000 requests per hour

---

## gRPC Service

The Analytics Service also exposes a gRPC interface on port `50056`.

**Available RPC Methods:**
- `GetKeyMetrics` - Get key recruitment metrics
- `GetQualityMetrics` - Get ML model quality metrics
- `GetDashboardData` - Get dashboard data
- `CreateReport` - Generate new report
- `GetReport` - Get report details
- `ListReports` - List all reports
- `StartBatchJob` - Start batch processing job
- `GetJobStatus` - Get batch job status
- `CancelJob` - Cancel batch job

See `protos/analytics.proto` for the complete service definition.
