# Pagination Testing Guide

This document provides instructions for testing vacancy pagination with a large dataset.

## Overview

Subtask 3-1 requires testing pagination with 50+ test vacancies to verify:
- All vacancies load correctly without errors
- Pagination works across multiple pages
- No duplicates or missing vacancies
- Edge cases are handled properly

## Prerequisites

1. Backend server running on `http://localhost:8000`
2. Frontend server running on `http://localhost:5173` (for browser testing)
3. Database connection configured

## Step 1: Create Test Vacancies

### Option A: Using the Python Script (Recommended)

```bash
# Create 55 test vacancies
cd backend
python scripts/create_test_vacancies.py --count 55

# Check existing vacancies count
python scripts/create_test_vacancies.py --count-existing

# Clear test vacancies when done
python scripts/create_test_vacancies.py --clear
```

### Option B: Using the API Directly

```bash
# Create a test vacancy via API
curl -X POST http://localhost:8000/api/vacancies/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Vacancy 1",
    "description": "Test description for pagination testing",
    "required_skills": ["Python", "SQL"],
    "min_experience_months": 12,
    "work_format": "remote",
    "location": "Moscow"
  }'
```

Repeat this 50+ times with different data, or use a script to automate.

## Step 2: Run Automated Tests

### Option A: Using Bash Script

```bash
cd backend
./scripts/test_pagination_manual.sh
```

This will run a comprehensive test suite:
- ✅ Total count verification
- ✅ Page size limits
- ✅ Skip offset (no overlap)
- ✅ Parameter validation
- ✅ Scrolling through all pages
- ✅ Edge cases

### Option B: Using pytest

```bash
cd backend
pytest tests/integration/test_vacancy_pagination.py -v -s
```

This runs the integration test suite that:
- Creates 55 test vacancies
- Tests pagination with various parameters
- Verifies no duplicates across pages
- Tests edge cases and validation

## Step 3: Manual Browser Testing

### 3.1 Open the Vacancies Page

Navigate to: `http://localhost:5173/vacancies`

### 3.2 Verify Initial Load

- [ ] Page loads without errors
- [ ] Initial vacancies display (should be 20)
- [ ] Check browser console (F12) - no errors
- [ ] Check Network tab - see initial API call with `limit=20`

### 3.3 Test Infinite Scroll

- [ ] Scroll slowly to the bottom of the vacancy list
- [ ] Verify "Loading more vacancies..." spinner appears
- [ ] Verify new vacancies load automatically
- [ ] Continue scrolling until all vacancies are loaded
- [ ] Verify "All vacancies loaded" message appears
- [ ] Check Network tab - see multiple API calls with increasing `skip` values

### 3.4 Test with Different Page Sizes

Open API directly in browser or use curl:

```bash
# Test with limit=10
curl "http://localhost:8000/api/vacancies/?skip=0&limit=10"

# Test with limit=50
curl "http://localhost:8000/api/vacancies/?skip=0&limit=50"

# Test second page
curl "http://localhost:8000/api/vacancies/?skip=20&limit=20"
```

### 3.5 Test Edge Cases

```bash
# Request beyond total (should return empty list)
curl "http://localhost:8000/api/vacancies/?skip=1000&limit=20"

# Invalid limit (should return 422)
curl "http://localhost:8000/api/vacancies/?limit=1000"

# Negative skip (should return 422)
curl "http://localhost:8000/api/vacancies/?skip=-10"
```

## Step 4: Verify Data Integrity

### 4.1 Check for Duplicates

When scrolling through all pages, ensure:
- No vacancy appears twice
- All vacancies from the database are accessible
- Order is consistent (newest first by default)

### 4.2 Verify Response Format

Each API response should have:
```json
{
  "total": 55,
  "vacancies": [
    {
      "id": "...",
      "title": "...",
      "description": "...",
      "required_skills": [...],
      "created_at": "...",
      ...
    }
  ]
}
```

## Step 5: Performance Verification

### 5.1 Check Initial Load Time

- Initial page load should be fast (<1 second for 20 items)
- Network tab shows single request with `limit=20`

### 5.2 Check Subsequent Loads

- Each pagination request should be fast (<500ms)
- Only 20 items loaded per request (not all vacancies)
- No performance degradation when scrolling

## Troubleshooting

### Backend Not Running

```bash
# Start backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Not Running

```bash
# Start frontend
cd frontend
npm run dev
```

### Database Empty

```bash
# Create test vacancies
cd backend
python scripts/create_test_vacancies.py --count 55
```

### Pagination Not Working

1. Check backend logs for errors
2. Verify API returns `total` and `vacancies` fields
3. Check browser console for JavaScript errors
4. Verify frontend is using updated API format

## Success Criteria

✅ **All tests pass:**
- [ ] Bash script completes without errors
- [ ] pytest integration tests pass
- [ ] Browser manual testing works smoothly
- [ ] 50+ vacancies can be scrolled through
- [ ] No duplicates or missing vacancies
- [ ] Edge cases handled correctly
- [ ] No errors in browser console
- [ ] Performance is acceptable

## Cleanup

After testing is complete:

```bash
# Remove test vacancies
cd backend
python scripts/create_test_vacancies.py --clear

# Or delete manually via API
curl -X DELETE http://localhost:8000/api/vacancies/{vacancy_id}
```

## Test Files Created

1. **`backend/tests/integration/test_vacancy_pagination.py`**
   - Comprehensive pytest integration test
   - Creates 55 test vacancies
   - Tests all pagination scenarios
   - Validates data integrity

2. **`backend/scripts/create_test_vacancies.py`**
   - Standalone script to create test vacancies
   - Can create any number of vacancies
   - Includes cleanup functionality

3. **`backend/scripts/test_pagination_manual.sh`**
   - Bash script for manual API testing
   - Tests all pagination parameters
   - No dependencies (just curl)

## Next Steps

After completing this subtask:
1. Mark subtask-3-1 as completed in `implementation_plan.json`
2. Proceed to subtask-3-2: Test infinite scroll with filters applied
3. Continue to subtask-3-3: Verify performance improvements
