# End-to-End Verification Guides

This document provides comprehensive instructions for verifying various features of the system.

---

## 1. Advanced Search & Faceted Filtering

### Overview

This guide describes how to run the comprehensive end-to-end verification tests for the advanced search and faceted filtering feature.

### Test File

**Location:** `frontend/e2e/advanced-search-e2e-integration.spec.ts`

### What This Test Verifies

The E2E integration test verifies the complete advanced search flow:

1. ✅ User builds query using visual query builder
2. ✅ Query is sent to backend with boolean operators
3. ✅ Backend parses query and searches Elasticsearch
4. ✅ Results returned with relevance scores
5. ✅ Search is tracked in analytics
6. ✅ Recent search appears in sidebar
7. ✅ Popular searches updated
8. ✅ Zero-result query tracked if no results

### Test Suites

- **End-to-End Advanced Search Flow (6 tests)**: Complete search flow, zero-result queries, boolean parsing, relevance scores, popular searches, recent searches
- **Backend Integration Verification (2 tests)**: API endpoints, Elasticsearch results
- **Query Builder to Search Flow (1 test)**: Visual query generation

### Running the Tests

```bash
cd frontend
npx playwright test advanced-search-e2e-integration.spec.ts
```

### Success Criteria

✅ All 9 E2E integration tests pass
✅ Search flow works from query builder to results
✅ Analytics tracking captures all searches
✅ Elasticsearch returns relevance scores

---

## 2. Bias Detection & Fairness Metrics

### Overview

The bias detection feature implements the following workflow:

```
1. Create Job Vacancy → Upload & Rank Candidates → Demographic Inference →
   Fairness Metrics Calculation → Bias Alert Creation → Notification →
   Admin Review → Alert Acknowledgment → Status Update
```

### Verification Methods

#### 1. Database-Level Verification (Recommended)

```bash
python backend/scripts/verify_e2e_bias_detection.py
```

#### 2. API-Based Verification

```bash
# Terminal 1: Start backend
uvicorn main:app --reload

# Terminal 2: Run verification
python backend/scripts/verify_api_e2e.py --base-url http://localhost:8000
```

#### 3. Pytest Integration Tests

```bash
pytest backend/tests/integration/test_bias_detection_e2e.py -v
```

### Manual UI Verification

1. Create Job Vacancy at `/vacancies`
2. Upload diverse candidate resumes
3. Rank candidates
4. Trigger fairness monitoring (scheduled or manual via API)
5. View Bias Detection Dashboard at `/bias-detection`
6. Review fairness trends and bias alerts
7. Acknowledge alerts and configure thresholds

### Acceptance Criteria

- [x] System detects potential bias in rankings based on gender, ethnicity, age
- [x] Fairness score (0-100) displayed for each vacancy
- [x] Flagged decisions include explanation of bias concern
- [x] Mitigation recommendations provided
- [x] Audit log tracks all bias-related actions
- [x] Configurable alerts notify admins

---

## Troubleshooting

### Advanced Search Issues
- Ensure Elasticsearch is running and indexed
- Verify backend API is running
- Check authentication state

### Bias Detection Issues
- Check Celery worker and beat are running
- Verify email configuration for notifications
- Review fairness metrics thresholds

For detailed troubleshooting, check logs in `logs/` directory.
