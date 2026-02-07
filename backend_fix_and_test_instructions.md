# Backend Endpoint Fix and Testing Instructions

## Issue Identified and Fixed

### Problem: Forward Reference Error
The Pydantic models (`StageDistribution`, `CandidateSourceMetrics`, `CandidateSourceAttributionResponse`) were defined **AFTER** the endpoint function that referenced them. This caused a Python forward reference error that prevented the endpoint from being registered with FastAPI.

### Solution Applied
Moved the model definitions from lines 2014-2037 to lines 1510-1535, right after the `SourceTrackingResponse` model and before the endpoint definition.

**File Modified:** `backend/api/analytics.py`

**Changes:**
- Moved `StageDistribution` class to line 1512
- Moved `CandidateSourceMetrics` class to line 1519
- Moved `CandidateSourceAttributionResponse` class to line 1530
- Removed duplicate model definitions from end of file

### Verification
To verify the fix:
```bash
# The models should now be defined BEFORE the endpoint
grep -n "class CandidateSourceAttributionResponse" backend/api/analytics.py
# Should show line 1530

grep -n "@router.get.*candidate-source-attribution" backend/api/analytics.py
# Should show line 1767 (after the model definition)
```

## Server Restart Required

The backend server must be restarted for the changes to take effect.

### Option 1: If using auto-reload
The server should automatically reload when it detects file changes. Wait 5-10 seconds after saving the file.

### Option 2: Manual restart
```bash
# Stop the current server (Ctrl+C or kill process)
# Then restart:
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Testing the Endpoint

After restart, verify the endpoint is registered:

```bash
# 1. Check if endpoint is in OpenAPI spec
curl -s http://localhost:8000/openapi.json | jq '.paths | keys | .[]' | grep "candidate-source-attribution"

# 2. Test the endpoint
curl -s http://localhost:8000/api/analytics/candidate-source-attribution | jq .

# 3. Test with date filters
curl -s "http://localhost:8000/api/analytics/candidate-source-attribution?start_date=2024-01-01&end_date=2024-12-31" | jq .

# 4. Test invalid date (should return 400)
curl -s "http://localhost:8000/api/analytics/candidate-source-attribution?start_date=invalid-date" | jq .
```

## Expected Response Structure

```json
{
  "sources": [
    {
      "source": "LinkedIn",
      "candidate_count": 100,
      "hired_count": 15,
      "conversion_rate": 0.15,
      "average_time_to_hire_days": 28.5,
      "stage_distribution": [
        {
          "stage_name": "applied",
          "count": 30,
          "percentage": 0.3
        },
        {
          "stage_name": "screening",
          "count": 25,
          "percentage": 0.25
        },
        {
          "stage_name": "interview",
          "count": 20,
          "percentage": 0.2
        },
        {
          "stage_name": "offered",
          "count": 10,
          "percentage": 0.1
        },
        {
          "stage_name": "hired",
          "count": 15,
          "percentage": 0.15
        }
      ]
    }
  ],
  "total_candidates": 100,
  "date_range": null
}
```

## Running the Full Test Suite

Once the server is restarted and the endpoint is accessible:

```bash
./test_candidate_source_attribution.sh
```

This will run comprehensive tests including:
- Basic endpoint tests
- Date filtering tests
- Error handling tests
- Edge case tests
- Metric validation tests

## Troubleshooting

### Endpoint returns 404
1. Verify server has restarted: `ps aux | grep uvicorn`
2. Check file modification time: `ls -la backend/api/analytics.py`
3. Look for Python errors in server logs
4. Verify model is defined before endpoint: `grep -n "class.*Response\|@router.get.*candidate" backend/api/analytics.py`

### Endpoint returns 500 error
1. Check server logs for error details
2. Verify database connection
3. Check if AnalyticsEvent table exists and has data
4. Verify HiringStage table exists

### Empty response (no sources)
1. This is expected if no `resume_uploaded` events exist
2. Create sample data using the script in `testing_documentation.md`
3. Verify data exists in AnalyticsEvent table

## Next Steps

After confirming the endpoint works:
1. Run the full test suite
2. Document test results in `testing_documentation.md`
3. If all tests pass, update implementation_plan.json to mark subtask-3-1 as completed
4. Commit the changes

## Files Modified

1. `backend/api/analytics.py` - Fixed forward reference issue by moving models before endpoint
2. `test_candidate_source_attribution.sh` - Created comprehensive test script
3. `.auto-claude/specs/105-add-candidate-source-attribution-analytics/testing_documentation.md` - Created testing documentation
4. `backend_fix_and_test_instructions.md` - This file

## Git Commit

Once testing is complete and verified:

```bash
git add backend/api/analytics.py
git commit -m "auto-claude: subtask-3-1 - Fix forward reference error in candidate-source-attribution endpoint

- Move Pydantic models before endpoint definition to fix forward reference
- StageDistribution, CandidateSourceMetrics, CandidateSourceAttributionResponse
now defined at lines 1510-1535 (before endpoint at line 1767)
- Create comprehensive test script and documentation
- Endpoint now properly registered with FastAPI"
```
