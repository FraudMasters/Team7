# Frontend Vacancy Saved Search Verification

This document describes the verification script for frontend vacancy saved search functionality.

## Purpose

Verifies that the frontend can:
1. Search vacancies with filters using `vacancySearchClient`
2. Save a search with vacancy filters using `savedSearchesClient`
3. Retrieve the saved search
4. Verify filters are preserved and correctly typed

## Prerequisites

1. **Backend server running** on `localhost:8000`
   ```bash
   cd backend
   source ../.venv/bin/activate
   python -m uvicorn main:app --reload --port 8000
   ```

2. **Node.js and TypeScript** installed
   ```bash
   node --version  # Should be v18+
   npm --version
   ```

3. **Install tsx** (TypeScript executor)
   ```bash
   npm install -g tsx
   ```

## Running the Verification

### Option 1: Using npm script (Recommended)

From the `frontend` directory:

```bash
npm run verify:vacancy-saved-search
```

This will automatically use `npx tsx` to run the verification script.

### Option 2: Using shell script (With prerequisites check)

From the `frontend` directory:

```bash
./verify_vacancy_saved_search.sh
```

This script will:
- Check if Node.js is installed (v18+)
- Check if the backend server is running
- Run the verification
- Report clear success/failure messages

### Option 3: Direct execution

From the `frontend` directory:

```bash
npx tsx verify_vacancy_saved_search.ts
```

Or with tsx installed globally:

```bash
tsx verify_vacancy_saved_search.ts
```

## Expected Output

### Success Case

```
============================================================
Frontend Vacancy Saved Search Verification
============================================================

=== Step 1: Search Vacancies with Filters ===

ℹ Searching vacancies with filters: {
  "work_format": "remote",
  "employment_type": "full-time",
  "salary_min": 80000,
  "salary_max": 120000,
  "location": "New York"
}
✓ Vacancy search completed successfully
ℹ Found X vacancies
ℹ Query executed: "software engineer"
ℹ Filters applied: {...}
ℹ Execution time: X.XXXs

=== Step 2: Create Saved Search with Vacancy Filters ===

ℹ Creating saved search: {...}
✓ Saved search created successfully
ℹ Saved search ID: uuid-here
ℹ Name: "Test Vacancy Search - Remote Full-Time"
ℹ Query: "software engineer"
ℹ Filters: {...}

=== Step 3: Retrieve Saved Search ===

ℹ Retrieving saved search with ID: uuid-here
✓ Saved search retrieved successfully
ℹ ID: uuid-here
ℹ Name: "Test Vacancy Search - Remote Full-Time"
ℹ Query: "software engineer"
ℹ Filters: {...}
ℹ Created at: 2026-02-04T...
ℹ Updated at: 2026-02-04T...

=== Step 4: Verify Filters are Preserved ===

ℹ Original filters:
{...}
ℹ Retrieved filters:
{...}
✓ work_format: remote (preserved correctly)
✓ employment_type: full-time (preserved correctly)
✓ salary_min: 80000 (preserved correctly)
✓ salary_max: 120000 (preserved correctly)

ℹ Verifying TypeScript types...
✓ work_format is string (correct type)
✓ employment_type is string (correct type)
✓ salary_min is number (correct type)
✓ salary_max is number (correct type)
✓ All filters preserved and correctly typed!

=== Cleanup: Delete Test Saved Search ===

ℹ Deleting saved search: uuid-here
✓ Test saved search deleted successfully

=== Verification Complete ===

✓ All verification steps passed successfully! ✓

Frontend can create saved vacancy searches and retrieve them correctly.
```

## What Gets Tested

### 1. Vacancy Search with Filters
- Uses `vacancySearchClient.searchVacancies()` from `frontend/src/api/vacancies.ts`
- Tests all vacancy-specific filters:
  - `work_format`
  - `employment_type`
  - `salary_min`
  - `salary_max`
  - `location`
- Verifies search response structure

### 2. Create Saved Search
- Uses `savedSearchesClient.createSavedSearch()` from `frontend/src/api/savedSearches.ts`
- Creates a saved search with vacancy filters
- Verifies response includes ID and all fields

### 3. Retrieve Saved Search
- Uses `savedSearchesClient.getSavedSearch()` from `frontend/src/api/savedSearches.ts`
- Retrieves the created saved search
- Verifies all fields are present

### 4. Filter Preservation
- Compares original filters with retrieved filters
- Verifies each filter field value matches
- Verifies TypeScript types are correct (string/number)

## Troubleshooting

### Backend not accessible
```
✗ Failed to create saved search: Network error. Please check your connection and try again.
```
**Solution:** Ensure backend server is running on `localhost:8000`

### TypeScript errors
```
✗ Unexpected error: Cannot find module '@/api/vacancies'
```
**Solution:** Ensure you're running from the `frontend` directory

### Cleanup failure
```
✗ Failed to delete saved search: ...
ℹ You may need to manually delete the saved search
```
**Solution:** Manually delete via API or database. The saved search ID is logged in the output.

## Manual Testing

You can also manually test the functionality:

```typescript
import { vacancySearchClient } from '@/api/vacancies';
import { savedSearchesClient } from '@/api/savedSearches';

// 1. Search vacancies
const results = await vacancySearchClient.searchVacancies({
  query: 'software engineer',
  filters: {
    work_format: 'remote',
    employment_type: 'full-time',
    salary_min: 80000,
    salary_max: 120000
  }
});

// 2. Save the search
const saved = await savedSearchesClient.createSavedSearch({
  name: 'Remote Full-Time Engineers',
  query: 'software engineer',
  filters: {
    work_format: 'remote',
    employment_type: 'full-time',
    salary_min: 80000,
    salary_max: 120000
  }
});

// 3. Retrieve the saved search
const retrieved = await savedSearchesClient.getSavedSearch(saved.id);

// 4. Verify filters
console.log(retrieved.filters); // Should match original filters
```

## Related Files

- `frontend/src/api/vacancies.ts` - Vacancy search client
- `frontend/src/api/savedSearches.ts` - Saved searches client
- `frontend/src/types/api.ts` - TypeScript type definitions
- `backend/api/saved_searches.py` - Backend saved searches API
- `backend/api/vacancies.py` - Backend vacancy search API
