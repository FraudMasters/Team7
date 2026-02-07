#!/usr/bin/env tsx
/**
 * Verification Script: Frontend Vacancy Saved Searches
 *
 * This script verifies that the frontend can:
 * 1. Search vacancies with filters using vacancySearchClient
 * 2. Save a search with vacancy filters using savedSearchesClient
 * 3. Retrieve the saved search
 * 4. Verify filters are preserved and correctly typed
 *
 * Usage:
 *   cd frontend
 *   npx tsx verify_vacancy_saved_search.ts
 *
 * Requirements:
 *   - Backend server running on localhost:8000
 *   - Node.js with TypeScript
 *   - Install tsx: npm install -g tsx
 */

import { vacancySearchClient } from './src/api/vacancies';
import { savedSearchesClient } from './src/api/savedSearches';
import type { VacancySearchFilters, SavedSearchResponse } from './src/types/api';

// ANSI color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  bold: '\x1b[1m'
};

function log(message: string, color: keyof typeof colors = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function success(message: string) {
  log(`✓ ${message}`, 'green');
}

function error(message: string) {
  log(`✗ ${message}`, 'red');
}

function info(message: string) {
  log(`ℹ ${message}`, 'blue');
}

function section(message: string) {
  log(`\n${colors.bold}${colors.blue}=== ${message} ===${colors.reset}\n`);
}

/**
 * Verify vacancy search with filters
 */
async function verifyVacancySearch(): Promise<void> {
  section('Step 1: Search Vacancies with Filters');

  const searchFilters: VacancySearchFilters = {
    work_format: 'remote',
    employment_type: 'full-time',
    salary_min: 80000,
    salary_max: 120000,
    location: 'New York'
  };

  info(`Searching vacancies with filters: ${JSON.stringify(searchFilters, null, 2)}`);

  try {
    const searchResponse = await vacancySearchClient.searchVacancies({
      query: 'software engineer',
      filters: searchFilters,
      limit: 10
    });

    success(`Vacancy search completed successfully`);
    info(`Found ${searchResponse.total} vacancies`);
    info(`Query executed: "${searchResponse.query}"`);
    info(`Filters applied: ${JSON.stringify(searchResponse.filters_applied, null, 2)}`);
    info(`Execution time: ${searchResponse.execution_time_seconds.toFixed(3)}s`);

    if (searchResponse.total === 0) {
      info('No vacancies found (this is OK if database is empty)');
    } else {
      success(`Search returned ${searchResponse.vacancies.length} vacancies`);
    }
  } catch (err) {
    error(`Vacancy search failed: ${err instanceof Error ? err.message : String(err)}`);
    throw err;
  }
}

/**
 * Verify creating a saved search with vacancy filters
 */
async function verifyCreateSavedSearch(): Promise<SavedSearchResponse> {
  section('Step 2: Create Saved Search with Vacancy Filters');

  const vacancyFilters: VacancySearchFilters = {
    work_format: 'remote',
    employment_type: 'full-time',
    salary_min: 80000,
    salary_max: 120000
  };

  const savedSearchData = {
    name: 'Test Vacancy Search - Remote Full-Time',
    query: 'software engineer',
    filters: vacancyFilters
  };

  info(`Creating saved search: ${JSON.stringify(savedSearchData, null, 2)}`);

  try {
    const savedSearch = await savedSearchesClient.createSavedSearch(savedSearchData);

    success(`Saved search created successfully`);
    info(`Saved search ID: ${savedSearch.id}`);
    info(`Name: "${savedSearch.name}"`);
    info(`Query: "${savedSearch.query}"`);
    info(`Filters: ${JSON.stringify(savedSearch.filters, null, 2)}`);

    return savedSearch;
  } catch (err) {
    error(`Failed to create saved search: ${err instanceof Error ? err.message : String(err)}`);
    throw err;
  }
}

/**
 * Verify retrieving a saved search
 */
async function verifyGetSavedSearch(savedSearchId: string): Promise<SavedSearchResponse> {
  section('Step 3: Retrieve Saved Search');

  info(`Retrieving saved search with ID: ${savedSearchId}`);

  try {
    const retrievedSearch = await savedSearchesClient.getSavedSearch(savedSearchId);

    success(`Saved search retrieved successfully`);
    info(`ID: ${retrievedSearch.id}`);
    info(`Name: "${retrievedSearch.name}"`);
    info(`Query: "${retrievedSearch.query}"`);
    info(`Filters: ${JSON.stringify(retrievedSearch.filters, null, 2)}`);
    info(`Created at: ${retrievedSearch.created_at}`);
    info(`Updated at: ${retrievedSearch.updated_at}`);

    return retrievedSearch;
  } catch (err) {
    error(`Failed to retrieve saved search: ${err instanceof Error ? err.message : String(err)}`);
    throw err;
  }
}

/**
 * Verify filters are preserved and correctly typed
 */
async function verifyFiltersPreserved(
  originalFilters: VacancySearchFilters,
  retrievedSearch: SavedSearchResponse
): Promise<void> {
  section('Step 4: Verify Filters are Preserved');

  const retrievedFilters = retrievedSearch.filters as VacancySearchFilters;

  info('Original filters:');
  info(JSON.stringify(originalFilters, null, 2));
  info('\nRetrieved filters:');
  info(JSON.stringify(retrievedFilters, null, 2));

  const checks = [
    {
      field: 'work_format',
      expected: originalFilters.work_format,
      actual: retrievedFilters.work_format
    },
    {
      field: 'employment_type',
      expected: originalFilters.employment_type,
      actual: retrievedFilters.employment_type
    },
    {
      field: 'salary_min',
      expected: originalFilters.salary_min,
      actual: retrievedFilters.salary_min
    },
    {
      field: 'salary_max',
      expected: originalFilters.salary_max,
      actual: retrievedFilters.salary_max
    }
  ];

  let allPassed = true;

  for (const check of checks) {
    if (check.expected === check.actual) {
      success(`${check.field}: ${check.actual} (preserved correctly)`);
    } else {
      error(`${check.field}: expected ${check.expected}, got ${check.actual}`);
      allPassed = false;
    }
  }

  // Verify types
  info('\nVerifying TypeScript types...');

  const typeChecks = [
    { field: 'work_format', value: retrievedFilters.work_format, type: 'string' },
    { field: 'employment_type', value: retrievedFilters.employment_type, type: 'string' },
    { field: 'salary_min', value: retrievedFilters.salary_min, type: 'number' },
    { field: 'salary_max', value: retrievedFilters.salary_max, type: 'number' }
  ];

  for (const check of typeChecks) {
    const actualType = typeof check.value;
    if (actualType === check.type) {
      success(`${check.field} is ${check.type} (correct type)`);
    } else {
      error(`${check.field} is ${actualType}, expected ${check.type}`);
      allPassed = false;
    }
  }

  if (allPassed) {
    success('All filters preserved and correctly typed!');
  } else {
    error('Some filters were not preserved correctly');
    throw new Error('Filter preservation verification failed');
  }
}

/**
 * Cleanup test saved search
 */
async function cleanupSavedSearch(savedSearchId: string): Promise<void> {
  section('Cleanup: Delete Test Saved Search');

  info(`Deleting saved search: ${savedSearchId}`);

  try {
    await savedSearchesClient.deleteSavedSearch(savedSearchId);
    success(`Test saved search deleted successfully`);
  } catch (err) {
    error(`Failed to delete saved search: ${err instanceof Error ? err.message : String(err)}`);
    info('You may need to manually delete the saved search');
  }
}

/**
 * Main verification flow
 */
async function main(): Promise<void> {
  log('\n' + '='.repeat(60), 'bold');
  log('Frontend Vacancy Saved Search Verification', 'bold');
  log('='.repeat(60) + '\n', 'bold');

  let savedSearchId: string | null = null;
  const originalFilters: VacancySearchFilters = {
    work_format: 'remote',
    employment_type: 'full-time',
    salary_min: 80000,
    salary_max: 120000
  };

  try {
    // Step 1: Search vacancies with filters
    await verifyVacancySearch();

    // Step 2: Create saved search with vacancy filters
    const savedSearch = await verifyCreateSavedSearch();
    savedSearchId = savedSearch.id;

    // Step 3: Retrieve saved search
    const retrievedSearch = await verifyGetSavedSearch(savedSearchId);

    // Step 4: Verify filters are preserved
    await verifyFiltersPreserved(originalFilters, retrievedSearch);

    // All verifications passed
    section('Verification Complete');
    success('All verification steps passed successfully! ✓');
    log('\nFrontend can create saved vacancy searches and retrieve them correctly.', 'green');

  } catch (err) {
    section('Verification Failed');
    error(`Verification failed: ${err instanceof Error ? err.message : String(err)}`);
    process.exit(1);
  } finally {
    // Cleanup
    if (savedSearchId) {
      try {
        await cleanupSavedSearch(savedSearchId);
      } catch (err) {
        error(`Cleanup failed: ${err instanceof Error ? err.message : String(err)}`);
      }
    }
  }
}

// Run verification
main().catch((err) => {
  error(`Unexpected error: ${err.message}`);
  process.exit(1);
});
