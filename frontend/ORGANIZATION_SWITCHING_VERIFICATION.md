# Organization Switching - Verification Guide

## Overview

This document provides step-by-step instructions for verifying that organization switching works correctly in the frontend application.

## Prerequisites

1. Backend server running with multi-tenant support
2. Frontend development server running on `http://localhost:5173`
3. At least two organizations created in the database
4. Candidates/resumes uploaded to different organizations

## Implementation Summary

The following changes were made to enable organization switching:

### 1. Organization Context Integration

- **File**: `frontend/src/main.tsx`
- **Change**: Added `OrganizationProvider` to the provider tree
- **Purpose**: Manages current organization state across the application

### 2. Organization-Scoped API Fetch Helper

- **File**: `frontend/src/api/organizationScopedFetch.ts` (NEW)
- **Purpose**: Provides `orgScopedFetch()` helper that automatically adds `X-Organization-ID` header to API requests
- **Features**:
  - Reads current organization from localStorage
  - Adds `X-Organization-ID` header to all requests
  - Supports both `fetch` and `axios` instances

### 3. Candidates Page Integration

- **File**: `frontend/src/pages/CandidatesKanbanPage.tsx`
- **Changes**:
  - Added `useOrganizationContext()` hook to access current organization
  - Updated `fetchCandidates()` to use `orgScopedFetch()`
  - Added `useEffect` to refetch candidates when organization changes
  - Added "No Organization Selected" empty state message

### 4. Organization Switcher Component

- **File**: `frontend/src/components/OrganizationSwitcher.tsx`
- **Status**: Already implemented in previous subtask (subtask-5-4)
- **Features**:
  - Displays current organization name
  - Dropdown menu with all available organizations
  - Updates organization context on selection

## Verification Steps

### Step 1: Start Development Servers

```bash
# Terminal 1 - Backend
cd backend
source .venv/bin/activate
python run.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### Step 2: Create Test Organizations

1. Open `http://localhost:5173/organizations` in your browser
2. Create two organizations:
   - Organization A: "TechCorp Inc"
   - Organization B: "Startup Labs"

### Step 3: Upload Candidates to Different Organizations

You'll need to use the API directly to upload candidates to specific organizations:

```bash
# Upload candidate to Organization A
curl -X POST http://localhost:8000/api/resumes/upload \
  -H "X-Organization-ID: <org-a-id>" \
  -F "file=@/path/to/resume1.pdf"

# Upload candidate to Organization B
curl -X POST http://localhost:8000/api/resumes/upload \
  -H "X-Organization-ID: <org-b-id>" \
  -F "file=@/path/to/resume2.pdf"
```

### Step 4: Verify Organization Switcher

1. Open `http://localhost:5173`
2. Look at the header for the organization switcher button (next to Quick Search)
3. **Expected**: The switcher should show the current organization name with a business icon

### Step 5: Test Organization Switching

#### Test 5.1: Initial State - No Organization Selected

1. Clear localStorage: Open DevTools → Application → Local Storage → Remove `app-current-organization`
2. Refresh the page
3. Navigate to Candidates page
4. **Expected**:
   - See "No Organization Selected" message with Business icon
   - Button to "Manage Organizations" is visible
   - No candidates are displayed

#### Test 5.2: Select Organization A

1. Click the organization switcher in the header
2. Select "TechCorp Inc" from the dropdown
3. **Expected**:
   - Switcher button now shows "TechCorp Inc"
   - Candidates page automatically refreshes
   - Only candidates from TechCorp Inc are displayed
   - Check browser DevTools Network tab:
     - Request to `/api/candidates/` includes header `X-Organization-ID: <org-a-id>`

#### Test 5.3: Switch to Organization B

1. Click the organization switcher again
2. Select "Startup Labs" from the dropdown
3. **Expected**:
   - Switcher button now shows "Startup Labs"
   - Candidates page automatically refreshes
   - Only candidates from Startup Labs are displayed
   - Check browser DevTools Network tab:
     - Request to `/api/candidates/` includes header `X-Organization-ID: <org-b-id>`
     - Response contains different candidates (from org B, not org A)

#### Test 5.4: Verify Data Isolation

1. Upload 3 candidates to Organization A
2. Upload 2 candidates to Organization B
3. Switch between organizations and verify:
   - When on Org A: See 3 candidates
   - When on Org B: See 2 candidates
   - No candidates from other org are visible

### Step 6: Verify Persistence

1. Select an organization
2. Close the browser tab
3. Open a new tab to `http://localhost:5173`
4. **Expected**:
   - The same organization is still selected
   - Candidates load immediately for that organization

### Step 7: Check Network Requests

Open DevTools → Network tab and verify:

1. **Request Headers** include:
   ```
   X-Organization-ID: <current-org-id>
   ```

2. **Response Data** contains only candidates from that organization

## Troubleshooting

### Issue: "No Organization Selected" message always shows

**Solution**:
- Check localStorage for `app-current-organization` key
- Ensure organizations are created in the database
- Check browser console for errors

### Issue: Candidates from all organizations are shown

**Solution**:
- Verify backend middleware is working: Check backend logs for X-Organization-ID header
- Verify `orgScopedFetch` is being called in CandidatesKanbanPage
- Check Network tab in DevTools to confirm header is present

### Issue: Organization switcher not visible

**Solution**:
- Ensure you're logged in as a recruiter
- Check that RecruiterLayout is being used
- Verify OrganizationSwitcher component is imported in RecruiterLayout

### Issue: Candidates don't refresh when switching organizations

**Solution**:
- Check that `useEffect` has `currentOrganization` in its dependency array
- Verify `setCurrentOrganization` is being called when organization is selected
- Check browser console for React warnings about missing dependencies

## Success Criteria

✅ Organization switcher shows all user's organizations
✅ Switching organization updates data display
✅ Candidate list updates to show only selected org's candidates
✅ X-Organization-ID header is present in all API requests
✅ Data isolation is maintained (no cross-org data leakage)
✅ Organization selection persists across page refreshes

## Additional Testing

### Test Error Handling

1. Try to access candidates page with no organization selected
2. **Expected**: See helpful "No Organization Selected" message

### Test Multiple Users

1. Create two different users
2. Add each user to different organizations
3. Verify each user only sees their own organizations in the switcher

### Test Organization Management

1. Create a new organization
2. Switch to it immediately
3. **Expected**: Organization appears in switcher and can be selected
4. Upload candidates to new org
5. **Expected**: Candidates are visible when that org is selected
