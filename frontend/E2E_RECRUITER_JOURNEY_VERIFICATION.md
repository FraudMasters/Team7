# E2E Recruiter Journey Verification Documentation

## Overview

This document describes the comprehensive E2E test suite for the Recruiter Journey in the AgentHR application. The test suite verifies all 7 verification steps required for the complete recruiter workflow.

## Test File Location

`frontend/e2e/recruiter-journey.spec.ts`

## Verification Steps Covered

### 1. View Dashboard
- **URL**: `/recruiter/dashboard`
- **What's Tested**:
  - Dashboard page renders with proper heading
  - Bento Grid metrics display
  - Candidate statistics (total candidates, active candidates)
  - Vacancy statistics (open positions, active jobs)
  - API integration with Analytics service (port 8006)
- **API Endpoint**: `/api/analytics/dashboard` → Analytics Service (8006)

### 2. Create Vacancy
- **URLs**: `/recruiter/vacancies`, `/recruiter/vacancies/create`
- **What's Tested**:
  - Vacancies list page loads
  - "Create Vacancy" button is visible and functional
  - Navigation to vacancy creation form
  - Form fields (Title, Description, Industry, Work Format, Location, Salary, Experience, Skills)
  - Form validation for required fields
  - API endpoint configuration for vacancy creation
- **API Endpoints**:
  - `GET /api/vacancies` → Vacancy Service (8004)
  - `POST /api/vacancies` → Vacancy Service (8004)

### 3. Browse Candidates
- **URL**: `/recruiter/candidates`
- **What's Tested**:
  - Kanban board displays with stage columns
  - Stage columns (New, Screening, Interview, Offer, Hired)
  - Candidate cards in columns
  - Drag-drop functionality for moving candidates
  - API integration with Candidate service
- **API Endpoint**: `/api/candidates` → Candidate Service (8003)

### 4. View Candidate Details
- **URL**: `/recruiter/candidates/:id`
- **What's Tested**:
  - Navigation to candidate detail page from kanban board
  - Candidate information display
  - Analysis tab with resume analysis results
  - Vacancy Matches tab with job compatibility scores
  - API call to fetch candidate details
- **API Endpoints**:
  - `GET /api/candidates/:id` → Candidate Service (8003)
  - `GET /api/matching/results/:id` → Matching Service (8002)

### 5. Use Candidate Search
- **URL**: `/recruiter/search`
- **What's Tested**:
  - Search page renders with search input
  - Filter sections (Skills, Experience, Location, Match Score)
  - Keyword search functionality with debouncing
  - Match score slider filter (0-100%)
  - AI ranking toggle
  - Search results display or empty state
  - Keyboard shortcuts (Ctrl+K for search focus, Ctrl+S for save)
- **API Endpoints**:
  - `POST /api/search` → Candidate Service (8003)
  - `POST /api/matching/rank` → Matching Service (8002)

### 6. Compare Candidates
- **URL**: `/recruiter/compare`
- **What's Tested**:
  - Comparison interface display
  - Candidate selection mechanism
  - Side-by-side comparison columns
  - Skill comparison
  - Match score comparison
  - API endpoint configuration for comparisons
- **API Endpoints**:
  - `POST /api/comparisons` → Matching Service (8002)
  - `POST /api/matching/compare` → Matching Service (8002)

### 7. Verify API Calls with Microservices
- **What's Tested**:
  - All API calls go through API Gateway (port 8888)
  - Vacancy Service (8004) API integration
  - Candidate Service (8003) API integration
  - Matching Service (8002) API integration
  - Analytics Service (8006) API integration
  - API Gateway as single entry point

## API Integration Matrix

| Frontend Feature | Microservice | Endpoint | Gateway Port |
|-----------------|--------------|----------|--------------|
| Dashboard metrics | Analytics (8006) | GET /api/analytics/dashboard | 8888 |
| Vacancy list | Vacancy (8004) | GET /api/vacancies | 8888 |
| Create vacancy | Vacancy (8004) | POST /api/vacancies | 8888 |
| Update vacancy | Vacancy (8004) | PUT /api/vacancies/:id | 8888 |
| Delete vacancy | Vacancy (8004) | DELETE /api/vacancies/:id | 8888 |
| Candidate list | Candidate (8003) | GET /api/candidates | 8888 |
| Candidate details | Candidate (8003) | GET /api/candidates/:id | 8888 |
| Update candidate stage | Candidate (8003) | PATCH /api/candidates/:id/stage | 8888 |
| Candidate search | Candidate (8003) | POST /api/search | 8888 |
| Candidate comparison | Matching (8002) | POST /api/comparisons | 8888 |
| Match results | Matching (8002) | GET /api/matching/results/:id | 8888 |
| AI ranking | Matching (8002) | POST /api/matching/rank | 8888 |
| Saved searches | Candidate (8003) | GET/POST /api/saved-searches | 8888 |
| Weights configuration | Matching (8002) | GET/PUT /api/weights | 8888 |

## Complete Journey Test

The `Complete Recruiter Journey - End to End` test suite verifies:

1. **Full Workflow**: Dashboard → Vacancies → Create → Candidates → Search → Compare
2. **No Console Errors**: All pages render without JavaScript errors
3. **Responsive Design**: All pages work on mobile viewport (375x667)
4. **Keyboard Navigation**: Tab navigation and search shortcuts work

## Additional Features Tested

1. **Weights Page** (`/recruiter/weights`):
   - Weight configuration sliders for matching algorithm
   - Preset selection
   - Save/restore functionality

2. **Saved Searches Page** (`/recruiter/saved-searches`):
   - List of saved searches
   - Create/edit/delete saved searches
   - Quick run saved searches

3. **Analytics Page** (`/recruiter/analytics`):
   - Hiring funnel visualization
   - Time-to-fill metrics
   - Source effectiveness
   - Quality metrics

## Error Handling Tests

The test suite includes comprehensive error handling verification:

1. **Invalid ID Handling**: Graceful error display for invalid vacancy/candidate IDs
2. **Network Error Handling**: Graceful degradation when API calls fail
3. **Offline Mode**: Basic functionality remains available offline
4. **Empty States**: Proper display when no data exists

## How to Run Tests

```bash
# Run all recruiter journey tests
cd frontend
npm run test:e2e -- recruiter-journey

# Run specific test suite
npm run test:e2e -- recruiter-journey.spec.ts

# Run with UI
npm run test:e2e -- --ui recruiter-journey.spec.ts

# Run with debug mode
npm run test:e2e -- --debug recruiter-journey.spec.ts
```

## Prerequisites

Before running tests, ensure:

1. Frontend dev server is running:
   ```bash
   cd frontend
   npm run dev
   # Runs at http://localhost:5173
   ```

2. Backend microservices are running:
   ```bash
   cd backend
   docker-compose up -d
   # API Gateway at http://localhost:8888
   # Services: Vacancy (8004), Candidate (8003), Matching (8002), Analytics (8006)
   ```

3. Or run with Playwright's webServer (configured in playwright.config.ts)

## Expected Results

When all tests pass:

✅ All 7 verification steps work correctly
✅ All API calls go through API Gateway (port 8888)
✅ All microservice endpoints are correctly configured
✅ No console errors on any page
✅ Responsive design works on mobile
✅ Keyboard navigation is functional
✅ Error handling works correctly

## Test Coverage

The test suite covers:

- **10 main test describes** for each verification step
- **50+ individual tests** covering all recruiter functionality
- **API integration verification** for all 4 microservices
- **Error handling and edge cases**
- **Complete end-to-end journey**
- **Responsive design verification**
- **Keyboard navigation verification**
- **Russian language comments** throughout the test code

## Notes

- Tests use Playwright's serial mode to ensure consistent execution order
- Some tests verify endpoint configuration without actual backend (network errors are expected)
- Tests are designed to work with or without backend running
- All comments in the test file are in Russian as per project requirements

## Related Documentation

- Applicant Journey E2E Tests: `frontend/e2e/applicant-journey.spec.ts`
- Playwright Configuration: `frontend/playwright.config.ts`
- API Documentation: `http://localhost:8888/docs` (when backend is running)
