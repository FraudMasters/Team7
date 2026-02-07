# Candidate Source Attribution Endpoint - Manual Testing Guide

## Endpoint Details
- **URL**: `/api/analytics/candidate-source-attribution`
- **Method**: `GET`
- **Description**: Returns analytics about candidate sources with conversion rates, time-to-hire, and stage distribution

## Test Scenarios

### 1. Basic Functionality Test
**Command:**
```bash
curl -X GET "http://localhost:8000/api/analytics/candidate-source-attribution" \
  -H "accept: application/json"
```

**Expected Result:**
- HTTP Status: 200
- Response contains:
  - `sources`: array of source objects
  - `total_candidates`: integer count
  - `date_range`: null or string

**Validation:**
- [ ] Response returns HTTP 200
- [ ] Response is valid JSON
- [ ] All required fields present
- [ ] `total_candidates` equals sum of all source `candidate_count` values

### 2. Response Structure Validation
**Sample Response:**
```json
{
  "sources": [
    {
      "source": "linkedin",
      "candidate_count": 100,
      "hired_count": 15,
      "conversion_rate": 0.15,
      "average_time_to_hire_days": 28.5,
      "stage_distribution": [
        {"stage_name": "applied", "count": 30, "percentage": 0.3},
        {"stage_name": "screening", "count": 25, "percentage": 0.25},
        {"stage_name": "interview", "count": 20, "percentage": 0.2},
        {"stage_name": "offered", "count": 10, "percentage": 0.1},
        {"stage_name": "hired", "count": 15, "percentage": 0.15}
      ]
    }
  ],
  "total_candidates": 100,
  "date_range": null
}
```

**Validation Checklist:**
- [ ] Each source has all required fields:
  - [ ] `source` (string)
  - [ ] `candidate_count` (int >= 0)
  - [ ] `hired_count` (int >= 0, <= candidate_count)
  - [ ] `conversion_rate` (float 0-1)
  - [ ] `average_time_to_hire_days` (float >= 0)
  - [ ] `stage_distribution` (array)
- [ ] Each stage has:
  - [ ] `stage_name` (string)
  - [ ] `count` (int >= 0)
  - [ ] `percentage` (float 0-1)

### 3. Conversion Rate Calculation Test
**Validation Formula:**
```
conversion_rate = hired_count / candidate_count
```

**Test Steps:**
1. Extract `hired_count` and `candidate_count` for each source
2. Calculate expected conversion rate manually
3. Compare with reported `conversion_rate`
4. Allow tolerance of ±0.001 for floating point precision

**Example:**
- Source: "linkedin"
- candidate_count: 100
- hired_count: 15
- Expected conversion_rate: 15/100 = 0.15
- Reported conversion_rate: 0.15 ✓

**Checklist:**
- [ ] All conversion rates match formula: hired_count / candidate_count
- [ ] All conversion rates between 0 and 1
- [ ] hired_count <= candidate_count for all sources
- [ ] conversion_rate = 0 when hired_count = 0
- [ ] conversion_rate = 1.0 when hired_count = candidate_count

### 4. Stage Distribution Percentage Test
**Validation Formula:**
```
sum of all stage percentages = 1.0 (allow ±0.01 tolerance)
```

**Test Steps:**
1. For each source, sum all `stage_distribution[].percentage`
2. Verify sum ≈ 1.0
3. Verify each percentage >= 0 and <= 1

**Example:**
- Stage percentages: [0.3, 0.25, 0.2, 0.1, 0.15]
- Sum: 1.0 ✓

**Checklist:**
- [ ] Stage percentages sum to 1.0 (±0.01 tolerance)
- [ ] All percentages between 0 and 1
- [ ] All counts are non-negative integers

### 5. Date Filtering Test
**Test Case 1: Valid date range**
```bash
curl -X GET "http://localhost:8000/api/analytics/candidate-source-attribution?start_date=2024-01-01&end_date=2024-12-31"
```
- [ ] HTTP Status: 200
- [ ] Response includes only data from date range
- [ ] `date_range` field populated

**Test Case 2: ISO 8601 datetime format**
```bash
curl -X GET "http://localhost:8000/api/analytics/candidate-source-attribution?start_date=2024-01-01T00:00:00Z&end_date=2024-12-31T23:59:59Z"
```
- [ ] HTTP Status: 200
- [ ] Date parsing works correctly

**Test Case 3: Invalid date format**
```bash
curl -X GET "http://localhost:8000/api/analytics/candidate-source-attribution?start_date=invalid-date"
```
- [ ] HTTP Status: 400
- [ ] Error message indicates invalid date format

**Test Case 4: Empty date range**
```bash
curl -X GET "http://localhost:8000/api/analytics/candidate-source-attribution?start_date=2020-01-01&end_date=2020-01-31"
```
- [ ] HTTP Status: 200
- [ ] Returns empty sources array or minimal data
- [ ] Response structure still valid

### 6. Sorting Test
**Validation:**
- [ ] Sources sorted by `candidate_count` descending
- [ ] Source with highest count appears first
- [ ] Source with lowest count appears last

**Test:**
```bash
# Compare candidate_count of consecutive sources
# sources[0].candidate_count >= sources[1].candidate_count >= sources[2].candidate_count...
```

### 7. Average Time-to-Hire Test
**Validation:**
- [ ] `average_time_to_hire_days` >= 0
- [ ] When `hired_count = 0`, `average_time_to_hire_days = 0.0`
- [ ] When `hired_count > 0`, `average_time_to_hire_days > 0` (usually)
- [ ] Values are reasonable (e.g., not negative, not extremely high like 99999)

### 8. Edge Cases Test

**Empty Dataset:**
- [ ] Returns 200 with empty sources array
- [ ] total_candidates = 0
- [ ] No errors or crashes

**Single Source:**
- [ ] Works with only one source
- [ ] Conversion rate calculated correctly
- [ ] Stage distribution valid

**Zero Conversions:**
- [ ] Sources with hired_count = 0 show conversion_rate = 0.0
- [ ] No division by zero errors

**All Hired:**
- [ ] Sources with hired_count = candidate_count show conversion_rate = 1.0

### 9. Performance Test
**Response Time:**
- [ ] Response time < 2 seconds for normal datasets
- [ ] Response time < 5 seconds for large datasets (1000+ candidates)

**Data Accuracy:**
- [ ] All calculations mathematically correct
- [ ] No rounding errors that significantly affect results
- [ ] Precision maintained (3 decimal places for rates)

## Automated Test Script

Run the comprehensive test script:
```bash
cd backend
chmod +x test_candidate_source_attribution.py
# Ensure server is running first, then:
./test_candidate_source_attribution.py
```

## Unit Tests

Run pytest unit tests:
```bash
cd backend
pytest tests/api/test_analytics.py::TestCandidateSourceAttributionEndpoint -v
```

Expected output:
- All tests should PASS
- 13 test cases covering all scenarios

## Integration with Frontend

**Frontend Component:** `frontend/src/components/analytics/CandidateSourceAttribution.tsx`

**Test Steps:**
1. Start backend: `cd backend && python -m uvicorn main:app --reload`
2. Start frontend: `cd frontend && npm start`
3. Navigate to: `http://localhost:3000/recruiter/analytics/candidate-source-attribution`
4. Verify:
   - [ ] Component loads without errors
   - [ ] Data displays correctly from backend
   - [ ] Summary cards show correct totals
   - [ ] Source list displays all sources
   - [ ] Conversion rates displayed with color coding
   - [ ] Time-to-hire displayed with appropriate formatting
   - [ ] Stage distribution bars render correctly
   - [ ] Date range filtering works
   - [ ] Auto-refresh functions (60s interval)

## Test Results Summary

### Test Execution Date: ____________

### Backend API Tests:
- [ ] Test 1: Endpoint Availability - PASS/FAIL
- [ ] Test 2: Response Structure - PASS/FAIL
- [ ] Test 3: Conversion Rate Calculation - PASS/FAIL
- [ ] Test 4: Stage Distribution Percentages - PASS/FAIL
- [ ] Test 5: Date Filtering - PASS/FAIL
- [ ] Test 6: Empty Dataset Handling - PASS/FAIL
- [ ] Test 7: Source Sorting - PASS/FAIL
- [ ] Test 8: Average Time-to-Hire - PASS/FAIL

### Manual Validation:
- [ ] Response format matches OpenAPI spec
- [ ] Metrics are mathematically correct
- [ ] Date filtering works properly
- [ ] Error cases return appropriate HTTP status codes

### Frontend Integration:
- [ ] Component renders without console errors
- [ ] Data displays correctly from backend API
- [ ] Date range filtering works
- [ ] Responsive layout adapts to screen size

### Overall Result: PASS / FAIL

### Notes:
_____________________________________________________________________________
_____________________________________________________________________________
_____________________________________________________________________________

### Tester: ____________
### Date: ____________
