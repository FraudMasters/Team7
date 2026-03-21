# End-to-End Verification Guide for Advanced Search Flow

## Overview

This guide describes how to run the comprehensive end-to-end verification tests for the advanced search and faceted filtering feature.

## Test File

**Location:** `frontend/e2e/advanced-search-e2e-integration.spec.ts`

## What This Test Verifies

The E2E integration test verifies the complete advanced search flow:

1. ✅ User builds query using visual query builder
2. ✅ Query is sent to backend with boolean operators
3. ✅ Backend parses query and searches Elasticsearch
4. ✅ Results returned with relevance scores
5. ✅ Search is tracked in analytics
6. ✅ Recent search appears in sidebar
7. ✅ Popular searches updated
8. ✅ Zero-result query tracked if no results

## Test Suites

### 1. End-to-End Advanced Search Flow (6 tests)

- **Complete search flow**: Tests the entire flow from query builder to results with analytics tracking
- **Zero-result queries**: Verifies zero-result queries are tracked in analytics
- **Boolean query parsing**: Tests complex boolean queries with AND/OR/NOT operators
- **Relevance scores**: Verifies Elasticsearch returns relevance scores
- **Popular searches**: Tests that popular searches are updated after multiple searches
- **Recent searches**: Verifies recent searches sidebar updates in real-time

### 2. Backend Integration Verification (2 tests)

- **API endpoints**: Verifies analytics API endpoints respond correctly
- **Elasticsearch results**: Verifies search API returns Elasticsearch results

### 3. Query Builder to Search Flow (1 test)

- **Visual query generation**: Tests generating and executing query from visual builder

## Prerequisites

Before running tests, ensure:

1. **Backend API** is running at `http://localhost:8000`
2. **Frontend dev server** is running at `http://localhost:5173`
3. **Elasticsearch** is running and indexed with test data
4. **User** is authenticated with recruiter role
5. **Test data** includes resumes/candidates in the database

## Running the Tests

### Run all E2E tests:
```bash
cd frontend
npx playwright test
```

### Run only the advanced search integration tests:
```bash
cd frontend
npx playwright test advanced-search-e2e-integration.spec.ts
```

### Run with UI mode (recommended for debugging):
```bash
cd frontend
npx playwright test advanced-search-e2e-integration.spec.ts --ui
```

### Run in headed mode (see browser):
```bash
cd frontend
npx playwright test advanced-search-e2e-integration.spec.ts --headed
```

### Run with debug mode:
```bash
cd frontend
npx playwright test advanced-search-e2e-integration.spec.ts --debug
```

## Expected Results

All tests should pass with green checkmarks:

```
✓ End-to-End Advanced Search Flow
  ✓ should complete full search flow from query builder to results with analytics tracking
  ✓ should track zero-result queries in analytics
  ✓ should verify backend boolean query parsing with complex queries
  ✓ should verify relevance scores are returned from Elasticsearch
  ✓ should update popular searches after multiple searches
  ✓ should verify recent searches sidebar updates in real-time

✓ Backend Integration Verification
  ✓ should verify API endpoints respond correctly
  ✓ should verify search API returns Elasticsearch results

✓ Query Builder to Search Flow
  ✓ should generate and execute query from visual builder
```

## Test Coverage

The test suite covers:

- **Frontend Components**: Query builder, search results, analytics dashboard, recent searches
- **Backend APIs**: Search API, analytics API, recent searches API
- **Elasticsearch Integration**: Query parsing, full-text search, relevance scoring
- **Analytics Tracking**: Search tracking, popular searches, zero-result queries
- **User Flows**: Complete search journeys from query building to results

## Troubleshooting

### Tests fail due to missing elements

- Ensure backend and frontend are running
- Check that test data exists in the database
- Verify Elasticsearch is running and indexed

### Timeouts

- Increase timeout values in test if needed (default is 3000ms for most checks)
- Ensure services are responsive

### Authentication issues

- Tests may require user to be logged in
- Check authentication state before running tests

## Related Test Files

- `frontend/e2e/advanced-search.spec.ts` - Tests for advanced search UI components
- `frontend/e2e/query-builder.spec.ts` - Tests for visual query builder (33 tests)
- `frontend/e2e/search-analytics.spec.ts` - Tests for analytics dashboard (64 tests)

## Manual Verification Steps

If automated tests are unavailable, perform these manual checks:

1. **Query Builder Flow**:
   - Navigate to `/candidate-search`
   - Enable advanced filters
   - Switch to visual query builder mode
   - Add filters (e.g., Skills: Python AND Experience: 5)
   - Click Search
   - Verify results appear with match scores

2. **Analytics Tracking**:
   - Perform several searches
   - Navigate to `/recruiter/search-analytics`
   - Verify search trends chart appears
   - Check popular searches section shows your searches
   - Perform a search with no results
   - Verify it appears in zero-result queries section

3. **Recent Searches**:
   - Perform multiple searches
   - Switch to "Search History" tab
   - Verify your recent searches appear
   - Click on a recent search to re-run it

4. **Boolean Queries**:
   - Enter complex query: `(Python OR Java) AND (5+ years)`
   - Verify query is parsed and executed
   - Check results match the query criteria

## Success Criteria

✅ All 9 E2E integration tests pass
✅ Search flow works from query builder to results
✅ Analytics tracking captures all searches
✅ Recent searches update in real-time
✅ Popular searches aggregate correctly
✅ Zero-result queries are tracked
✅ Elasticsearch returns relevance scores
✅ Boolean query parsing works correctly
✅ API endpoints respond as expected

## Notes

- Tests are designed to be resilient with fallback checks
- Some tests check for element visibility with timeouts to avoid flakiness
- Tests verify both successful searches and zero-result scenarios
- Network monitoring is used to verify API calls
