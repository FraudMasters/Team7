# Subtask 5-1: Verify Saved Search with Vacancy Filters

## Purpose

This verification tests that the saved searches API can create and retrieve saved searches with vacancy-specific filters (work_format, employment_type, salary_min, etc.).

## What Gets Tested

1. **POST /api/saved-searches/** - Create a saved search with vacancy filters
2. **GET /api/saved-searches/{id}** - Retrieve the saved search
3. **Filter Preservation** - Verify that vacancy filters are correctly stored and retrieved
4. **DELETE /api/saved-searches/{id}** - Cleanup test data

## Test Data

The verification creates a saved search with the following data:

```json
{
  "name": "Remote Full-Time Vacancies",
  "query": "software engineer",
  "filters": {
    "work_format": "remote",
    "employment_type": "full-time",
    "salary_min": 80000
  }
}
```

## Prerequisites

1. **Backend server running** on `http://localhost:8000`
2. **Python 3** with `requests` library installed
3. **Database connection** (for saved searches storage)

## How to Run

### Option 1: Using the shell script (recommended)

```bash
./backend/verify_saved_search_vacancy_filters.sh
```

The shell script will:
- Check Python version
- Verify requests library is installed
- Confirm backend server is running
- Run the verification script
- Report pass/fail status

### Option 2: Direct Python execution

```bash
cd backend
python verify_saved_search_vacancy_filters.py
```

### Option 3: Manual curl testing

```bash
# Create saved search
curl -X POST http://localhost:8000/api/saved-searches/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Remote Full-Time Vacancies",
    "query": "software engineer",
    "filters": {
      "work_format": "remote",
      "employment_type": "full-time",
      "salary_min": 80000
    }
  }'

# Expected response: HTTP 201 with JSON containing saved search object including "id" field
```

## Expected Output

When successful, the script will output:

```
======================================================================
Subtask 5-1: Test Creating Saved Search with Vacancy Filters
======================================================================

✓ Backend server is running on http://localhost:8000

Creating saved search...
URL: POST http://localhost:8000/api/saved-searches/
Payload: {
  "name": "Remote Full-Time Vacancies",
  "query": "software engineer",
  "filters": {
    "work_format": "remote",
    "employment_type": "full-time",
    "salary_min": 80000
  }
}
Response status: 201
✓ Saved search created successfully

✓ Created saved search with ID: 123

Retrieving saved search (ID: 123)...
✓ Saved search retrieved successfully

Verifying filters...
✓ work_format: remote
✓ employment_type: full-time
✓ salary_min: 80000

Cleaning up: deleting saved search (ID: 123)...
✓ Saved search deleted successfully

======================================================================
✓ VERIFICATION PASSED
Saved search with vacancy filters works correctly!
======================================================================

✓ Verification completed successfully
```

## Troubleshooting

### Backend server not running

**Error:** `✗ Cannot connect to backend server`

**Solution:** Start the backend server:
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

### Missing requests library

**Error:** `ModuleNotFoundError: No module named 'requests'`

**Solution:** Install requests:
```bash
pip install requests
```

### HTTP 404 on /api/saved-searches/

**Error:** `Response status: 404`

**Cause:** The saved_searches router is not registered

**Solution:** Verify that `backend/api/__init__.py` exports `saved_searches` in both the import statement and `__all__` list. This was fixed in commit f567a06.

### HTTP 422 Validation Error

**Error:** `Response status: 422`

**Cause:** Request body validation failed

**Solution:** Check that the request body matches the expected Pydantic model for `SavedSearchCreate`. Verify all required fields are present.

### HTTP 500 Internal Server Error

**Error:** `Response status: 500`

**Cause:** Server-side error (database connection, missing fields, etc.)

**Solution:** Check backend server logs for detailed error message:
```bash
# If running with uvicorn, logs will be in the terminal
# Check database connection and configuration
```

## Verification Criteria

The verification is considered **PASSED** when:

1. ✓ POST request to `/api/saved-searches/` returns HTTP 201
2. ✓ Response includes an `id` field for the created saved search
3. ✓ GET request to `/api/saved-searches/{id}` returns HTTP 200
4. ✓ Retrieved saved search contains the exact same filter values as submitted
5. ✓ All three vacancy filters (work_format, employment_type, salary_min) are preserved

## Technical Details

### API Endpoints Tested

- **POST /api/saved-searches/**
  - Request body: `SavedSearchCreate` model
  - Response: `SavedSearchResponse` model (HTTP 201)
  - Purpose: Create a new saved search with vacancy filters

- **GET /api/saved-searches/{id}**
  - Response: `SavedSearchResponse` model (HTTP 200)
  - Purpose: Retrieve saved search by ID

- **DELETE /api/saved-searches/{id}**
  - Response: HTTP 200 or 204
  - Purpose: Cleanup test data

### Filter Fields Tested

| Field | Type | Example | Purpose |
|-------|------|---------|---------|
| work_format | string | "remote" | Filter by work arrangement (remote/office/hybrid) |
| employment_type | string | "full-time" | Filter by employment type (full-time/part-time/contract) |
| salary_min | integer | 80000 | Filter by minimum salary |

### Related Code

- **Backend API:** `backend/api/saved_searches.py`
- **API Router:** `backend/api/__init__.py` (exports saved_searches)
- **Main App:** `backend/main.py` (registers all routers)
- **Data Model:** `SavedSearchCreate` with `filters: Dict[str, Any]`

## Next Steps

After this verification passes:

1. **subtask-5-2** - Test vacancy search endpoint with multiple filters
2. **subtask-5-3** - Verify frontend can create saved vacancy searches and retrieve them
3. **QA Sign-off** - Mark implementation plan as complete
