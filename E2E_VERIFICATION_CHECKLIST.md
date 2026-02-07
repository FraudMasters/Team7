# End-to-End Verification Checklist
## User Profile and Preferences Management

**Subtask:** subtask-5-2
**Date:** 2026-02-03
**Status:** In Progress

---

## Overview

This document provides a comprehensive checklist for end-to-end verification of the user profile and preferences management feature.

---

## Prerequisites

### Required Services
- [ ] Backend server running on `http://localhost:8000`
- [ ] Frontend dev server running on `http://localhost:5173`
- [ ] PostgreSQL database accessible
- [ ] Database migrations applied

### Start Services (if not running)

**Backend:**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

---

## Phase 1: Structure Verification

### 1.1 Database Layer
- [ ] **Migration file exists:** `backend/alembic/versions/20260203_enhance_user_preferences.py`
- [ ] **Migration applied:** Run `alembic current` and verify it's at head
- [ ] **Model updated:** `backend/models/user_preferences.py` contains all fields:
  - [ ] `name` (Optional[str])
  - [ ] `email` (Optional[str])
  - [ ] `role` (Optional[str])
  - [ ] `avatar_url` (Optional[str])
  - [ ] `dashboard_config` (JSON)
  - [ ] `filter_preferences` (JSON)
  - [ ] `api_keys` (JSON)

**Verification Commands:**
```bash
cd backend
alembic current
python -c "from models.user_preferences import UserPreferences; print(UserPreferences.__table__.columns.keys())"
```

### 1.2 Backend API Layer
- [ ] **Preferences API file exists:** `backend/api/preferences.py`
- [ ] **Router registered in main.py:** Check for `app.include_router(preferences.router, prefix="/api/preferences")`
- [ ] **All endpoints implemented:**
  - [ ] `GET /api/preferences/language`
  - [ ] `PUT /api/preferences/language`
  - [ ] `GET /api/preferences/profile`
  - [ ] `PUT /api/preferences/profile`
  - [ ] `GET /api/preferences/dashboard`
  - [ ] `PUT /api/preferences/dashboard`
  - [ ] `GET /api/preferences/filters`
  - [ ] `PUT /api/preferences/filters`
  - [ ] `GET /api/preferences/api-keys`
  - [ ] `POST /api/preferences/api-keys`
  - [ ] `DELETE /api/preferences/api-keys/{key_id}`

**Verification:**
```bash
curl -s http://localhost:8000/docs | grep -o "/api/preferences/[^\"]*" | sort -u
```

### 1.3 Frontend API Client
- [ ] **API client file exists:** `frontend/src/api/preferences.ts`
- [ ] **All functions implemented:**
  - [ ] `getLanguagePreference()`
  - [ ] `updateLanguagePreference(language)`
  - [ ] `getUserProfile()`
  - [ ] `updateUserProfile(profileData)`
  - [ ] `getDashboardConfig()`
  - [ ] `updateDashboardConfig(configData)`
  - [ ] `getFilterPreferences()`
  - [ ] `updateFilterPreferences(filtersData)`
  - [ ] `createApiKey(keyData)`
  - [ ] `listApiKeys()`
  - [ ] `deleteApiKey(keyId)`

### 1.4 Frontend Components
- [ ] **ProfileEditor:** `frontend/src/components/ProfileEditor.tsx`
- [ ] **Settings page:** `frontend/src/pages/Settings.tsx`
- [ ] **ApiKeysManager:** `frontend/src/components/ApiKeysManager.tsx`
- [ ] **DashboardConfig:** `frontend/src/components/DashboardConfig.tsx`
- [ ] **UserPreferencesContext:** `frontend/src/contexts/UserPreferencesContext.tsx`
- [ ] **Route registered:** Check `frontend/src/App.tsx` for Settings route

---

## Phase 2: API Endpoint Testing

### 2.1 Language Preference Endpoints

#### Test 1: Get Current Language
```bash
curl -X GET http://localhost:8000/api/preferences/language
```
**Expected Response:**
```json
{
  "language": "en"
}
```
- [ ] Status: 200 OK
- [ ] Response contains language field

#### Test 2: Update Language to Russian
```bash
curl -X PUT http://localhost:8000/api/preferences/language \
  -H "Content-Type: application/json" \
  -d '{"language": "ru"}'
```
**Expected Response:**
```json
{
  "language": "ru"
}
```
- [ ] Status: 200 OK
- [ ] Language updated to "ru"

#### Test 3: Verify Language Persists
```bash
curl -X GET http://localhost:8000/api/preferences/language
```
**Expected Response:**
```json
{
  "language": "ru"
}
```
- [ ] Status: 200 OK
- [ ] Language is still "ru" (persistence verified)

#### Test 4: Update Language Back to English
```bash
curl -X PUT http://localhost:8000/api/preferences/language \
  -H "Content-Type: application/json" \
  -d '{"language": "en"}'
```
- [ ] Status: 200 OK

---

### 2.2 User Profile Endpoints

#### Test 1: Get Current Profile
```bash
curl -X GET http://localhost:8000/api/preferences/profile
```
**Expected Response:**
```json
{
  "name": null,
  "email": null,
  "role": null,
  "avatar_url": null
}
```
- [ ] Status: 200 OK
- [ ] All profile fields present

#### Test 2: Update Profile
```bash
curl -X PUT http://localhost:8000/api/preferences/profile \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Recruiter",
    "email": "test@example.com",
    "role": "recruiter",
    "avatar_url": "https://example.com/avatar.jpg"
  }'
```
**Expected Response:**
```json
{
  "name": "Test Recruiter",
  "email": "test@example.com",
  "role": "recruiter",
  "avatar_url": "https://example.com/avatar.jpg"
}
```
- [ ] Status: 200 OK
- [ ] All fields updated correctly

#### Test 3: Verify Profile Persists Across Refresh
```bash
# Wait 2 seconds
sleep 2
# Get profile again
curl -X GET http://localhost:8000/api/preferences/profile
```
- [ ] Status: 200 OK
- [ ] Profile data matches what was set
- [ ] Data persisted correctly

---

### 2.3 Dashboard Configuration Endpoints

#### Test 1: Get Dashboard Config
```bash
curl -X GET http://localhost:8000/api/preferences/dashboard
```
**Expected Response:**
```json
{
  "layout": null,
  "widgets": null,
  "settings": null
}
```
- [ ] Status: 200 OK

#### Test 2: Update Dashboard Config
```bash
curl -X PUT http://localhost:8000/api/preferences/dashboard \
  -H "Content-Type: application/json" \
  -d '{
    "layout": "grid",
    "widgets": {
      "metrics": {"enabled": true, "order": 1},
      "recent-candidates": {"enabled": true, "order": 2}
    },
    "settings": {"refreshInterval": 30}
  }'
```
- [ ] Status: 200 OK
- [ ] Configuration updated

#### Test 3: Verify Dashboard Config Persists
```bash
sleep 1
curl -X GET http://localhost:8000/api/preferences/dashboard
```
- [ ] Layout is "grid"
- [ ] Widgets configuration persisted
- [ ] Settings persisted

---

### 2.4 Filter Preferences Endpoints

#### Test 1: Get Filter Preferences
```bash
curl -X GET http://localhost:8000/api/preferences/filters
```
- [ ] Status: 200 OK

#### Test 2: Update Filter Preferences
```bash
curl -X PUT http://localhost:8000/api/preferences/filters \
  -H "Content-Type: application/json" \
  -d '{
    "default_filters": {
      "experience_years": [0, 10],
      "languages": ["en", "ru"],
      "location": "Remote"
    }
  }'
```
- [ ] Status: 200 OK
- [ ] Filters updated

#### Test 3: Verify Filters Persist
```bash
sleep 1
curl -X GET http://localhost:8000/api/preferences/filters
```
- [ ] Filter preferences persisted correctly
- [ ] Default filters contain the set values

---

### 2.5 API Keys Management Endpoints

#### Test 1: List API Keys (Initial)
```bash
curl -X GET http://localhost:8000/api/preferences/api-keys
```
**Expected Response:**
```json
{
  "total": 0,
  "api_keys": []
}
```
- [ ] Status: 200 OK
- [ ] Returns empty list initially

#### Test 2: Create API Key
```bash
curl -X POST http://localhost:8000/api/preferences/api-keys \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test OpenAI Key",
    "key": "sk-test-key-12345",
    "service": "openai"
  }'
```
**Expected Response:**
```json
{
  "id": "uuid-here",
  "name": "Test OpenAI Key",
  "key": "****345",
  "service": "openai",
  "created_at": "2026-02-03T..."
}
```
- [ ] Status: 200 or 201
- [ ] Key created with ID
- [ ] Key is masked (shows only last 4 chars)

#### Test 3: List API Keys (After Creation)
```bash
curl -X GET http://localhost:8000/api/preferences/api-keys
```
- [ ] Status: 200 OK
- [ ] Total count is 1
- [ ] API keys array contains the created key

#### Test 4: Delete API Key
```bash
# Extract key_id from previous response
KEY_ID="<uuid-from-creation>"
curl -X DELETE http://localhost:8000/api/preferences/api-keys/$KEY_ID
```
- [ ] Status: 200 OK
- [ ] Key deleted successfully

#### Test 5: Verify Deletion Persisted
```bash
curl -X GET http://localhost:8000/api/preferences/api-keys
```
- [ ] Total count is 0 again
- [ ] API keys array is empty

---

## Phase 3: Frontend UI Verification

### 3.1 Settings Page

#### Step 1: Navigate to Settings Page
- [ ] Open browser to `http://localhost:5173/settings`
- [ ] Page loads without 404 error
- [ ] Page title is visible

#### Step 2: Verify Page Structure
- [ ] Page header shows "Settings"
- [ ] Four tabs are visible:
  - [ ] "Profile"
  - [ ] "Notifications"
  - [ ] "Language"
  - [ ] "API Keys"

#### Step 3: Check Browser Console
- [ ] Open browser DevTools (F12)
- [ ] No JavaScript errors in console
- [ ] No network errors (failed API calls)

### 3.2 Profile Tab

#### Step 1: Open Profile Tab
- [ ] Click on "Profile" tab
- [ ] Profile editor component renders

#### Step 2: Verify Profile Editor
- [ ] Form fields are visible:
  - [ ] Name input field
  - [ ] Email input field
  - [ ] Role input field
  - [ ] Avatar URL input field
- [ ] Avatar preview visible (or placeholder icon)
- [ ] "Save" button visible
- [ ] Current profile information displayed

#### Step 3: Test Profile Update
- [ ] Enter test data in fields:
  - Name: "E2E Test User"
  - Email: "e2e@test.com"
  - Role: "recruiter"
- [ ] Click "Save" button
- [ ] Success notification appears
- [ ] Wait 2 seconds
- [ ] Refresh page (F5)
- [ ] Profile data still visible (persistence verified)

### 3.3 Language Tab

#### Step 1: Open Language Tab
- [ ] Click on "Language" tab
- [ ] Instructions for using header language switcher visible

#### Step 2: Verify Language Preference (API Level)
- [ ] Language preference can be set via API
- [ ] Language preference persists across page refresh
- [ ] Language affects UI when changed via header switcher

### 3.4 API Keys Tab

#### Step 1: Open API Keys Tab
- [ ] Click on "API Keys" tab
- [ ] API keys manager component renders
- [ ] "Add API Key" form visible
- [ ] List of existing keys visible (initially empty)

#### Step 2: Add API Key
- [ ] Click "Add API Key" button
- [ ] Fill in form:
  - Name: "Test Key"
  - Key: "sk-test-12345"
  - Service: "openai"
- [ ] Submit form
- [ ] Success notification appears
- [ ] Key appears in list with masked value

#### Step 3: Verify API Key Features
- [ ] Key is masked (shows only first 4 and last 4 chars)
- [ ] "Show/Hide" toggle button works
- [ ] Service icon displayed with correct color (OpenAI = green)
- [ ] Delete button visible for the key

#### Step 4: Delete API Key
- [ ] Click delete button for the test key
- [ ] Confirmation dialog appears
- [ ] Confirm deletion
- [ ] Key removed from list
- [ ] Success notification appears

#### Step 5: Verify Persistence
- [ ] Refresh page
- [ ] API key still deleted (not reappearing)

---

## Phase 4: Data Persistence Verification

### 4.1 Cross-Request Persistence

For each preference type, verify data persists:

- [ ] **Language Preference:**
  - [ ] Set to "ru"
  - [ ] Make immediate GET request
  - [ ] Value is "ru"
  - [ ] Wait 5 seconds
  - [ ] Make another GET request
  - [ ] Value is still "ru"

- [ ] **User Profile:**
  - [ ] Set profile data
  - [ ] Make immediate GET request
  - [ ] Data matches
  - [ ] Restart backend server
  - [ ] Make GET request
  - [ ] Data still matches (database persistence)

- [ ] **Dashboard Config:**
  - [ ] Set dashboard config
  - [ ] Wait 10 seconds
  - [ ] Make GET request
  - [ ] Config persisted

- [ ] **API Keys:**
  - [ ] Create API key
  - [ ] List keys
  - [ ] Key exists
  - [ ] Wait 5 seconds
  - [ ] List keys again
  - [ ] Key still exists
  - [ ] Delete key
  - [ ] List keys
  - [ ] Key deleted

---

## Phase 5: Integration Verification

### 5.1 Context Integration

- [ ] **UserPreferencesContext Provider:**
  - [ ] Check `frontend/src/App.tsx`
  - [ ] UserPreferencesProvider wraps the application
  - [ ] Context is available to all components

### 5.2 End-to-End Workflow

**Complete User Journey:**
1. [ ] Navigate to `http://localhost:5173/settings`
2. [ ] Update profile (name, email, role)
3. [ ] Save profile
4. [ ] Refresh page - verify profile persists
5. [ ] Change language preference (via API or header)
6. [ ] Refresh page - verify language persists
7. [ ] Configure dashboard layout
8. [ ] Save configuration
9. [ ] Refresh page - verify config persists
10. [ ] Set default filter preferences
11. [ ] Save filters
12. [ ] Refresh page - verify filters persist
13. [ ] Add API key
14. [ ] Verify key appears in list
15. [ ] Refresh page - verify key persists
16. [ ] Delete API key
17. [ ] Verify key removed
18. [ ] Refresh page - verify deletion persists

---

## Phase 6: Error Handling Verification

### 6.1 API Error Handling

- [ ] **Invalid Language:**
  ```bash
  curl -X PUT http://localhost:8000/api/preferences/language \
    -H "Content-Type: application/json" \
    -d '{"language": "invalid"}'
  ```
  - [ ] Returns validation error (422)

- [ ] **Invalid Email:**
  ```bash
  curl -X PUT http://localhost:8000/api/preferences/profile \
    -H "Content-Type: application/json" \
    -d '{"email": "not-an-email"}'
  ```
  - [ ] Returns validation error or accepts with warning

- [ ] **Duplicate API Key Name:**
  - [ ] Create API key with name "Test"
  - [ ] Try to create another with same name
  - [ ] Returns 400 error (duplicate name)

- [ ] **Delete Non-existent Key:**
  ```bash
  curl -X DELETE http://localhost:8000/api/preferences/api-keys/non-existent-id
  ```
  - [ ] Returns 404 error

### 6.2 Frontend Error Handling

- [ ] **Network Error Handling:**
  - [ ] Stop backend server
  - [ ] Try to update profile
  - [ ] User-friendly error message displayed
  - [ ] No uncaught exceptions

- [ ] **Validation Errors:**
  - [ ] Enter invalid email format
  - [ ] Appropriate validation message shown
  - [ ] Form submission prevented or shows error

---

## Automated Test Scripts

Two automated verification scripts are provided:

### 1. Bash Script (`verify_user_preferences_e2e.sh`)
```bash
./verify_user_preferences_e2e.sh
```
Tests all API endpoints using curl.

### 2. Python Script (`verify_user_preferences_e2e.py`)
```bash
python3 verify_user_preferences_e2e.py
```
Comprehensive testing with detailed reporting.

---

## Acceptance Criteria Verification

Based on the spec, verify all acceptance criteria are met:

- [ ] **Users can edit their profile (name, email, role, avatar)**
  - ProfileEditor component functional
  - API endpoints working
  - Data persists

- [ ] **Users can set language preference (English/Russian)**
  - Language preference API working
  - Preference persists across sessions

- [ ] **Users can customize notification preferences (email, in-app, frequency)**
  - Placeholder in Notifications tab
  - Backend structure ready for implementation

- [ ] **Users can save default filter preferences for candidate searches**
  - Filter preferences API working
  - Can set and retrieve default filters

- [ ] **Users can configure dashboard layout and widget order**
  - DashboardConfig component functional
  - Layout and widgets can be configured
  - Configuration persists

- [ ] **Profile changes persist across sessions**
  - Database storage verified
  - Data survives server restart
  - Frontend state management working

---

## Final Sign-off

### Summary of Verification

**Total Checks:** _____
**Passed:** _____
**Failed:** _____
**Success Rate:** _____%

### Outstanding Issues

1.
2.
3.

### Verifier Sign-off

- [ ] All automated tests pass
- [ ] All manual checks completed
- [ ] No critical issues found
- [ ] Feature ready for production

**Name:** _________________
**Date:** _________________
**Signature:** _________________

---

## Notes

- Keep this checklist with the implementation plan
- Update statuses as you complete each check
- Document any issues or workarounds found
- Take screenshots of UI verification for evidence
