# Role-Based Access Control (RBAC) Testing Guide

This guide provides comprehensive testing instructions for verifying role-based access control (RBAC) in the AgentHR authentication system.

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Automated Testing](#automated-testing)
- [Manual Browser Testing](#manual-browser-testing)
- [API Endpoint Testing](#api-endpoint-testing)
- [Verification Checklist](#verification-checklist)
- [Troubleshooting](#troubleshooting)
- [Test Data Cleanup](#test-data-cleanup)

## Overview

The RBAC system has three roles with different permission levels:

### Role Hierarchy
1. **Admin (Level 1)** - Full system access
   - User management (create, read, update, delete users)
   - Role assignment
   - All recruiting features
   - Analytics and reports
   - System settings
   - Backup management

2. **Recruiter (Level 2)** - Recruiting access
   - Candidate management (create, read, update, delete)
   - Job vacancy management (create, read, update, no delete)
   - Analytics (read-only)
   - Reports (create, read)
   - NO access to: user management, settings, backups

3. **Viewer (Level 3)** - Read-only access
   - View candidates (read-only)
   - View vacancies (read-only)
   - View analytics (read-only)
   - NO access to: create, update, delete operations

### Permissions Matrix

| Feature | Admin | Recruiter | Viewer |
|---------|-------|-----------|--------|
| User Management | ✅ Full | ❌ None | ❌ None |
| Candidates (CRUD) | ✅ Full | ✅ Full | 📖 Read Only |
| Vacancies (CRUD) | ✅ Full | ✅ CRU (no D) | 📖 Read Only |
| Analytics | ✅ Full | 📖 Read Only | 📖 Read Only |
| Reports | ✅ Full | 📖 Create/Read | 📖 Read Only |
| Settings | ✅ Full | ❌ None | ❌ None |
| Backups | ✅ Full | ❌ None | ❌ None |

## Prerequisites

### 1. Database Setup
Ensure PostgreSQL is running and the database has been migrated:

```bash
cd backend
alembic upgrade head
```

### 2. Backend Service
Start the FastAPI backend:

```bash
cd backend
python main.py
```

Verify backend is running:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "service": "AgentHR Backend",
  "status": "healthy",
  "version": "0.1.0"
}
```

### 3. Frontend Service (Optional)
For manual browser testing:

```bash
cd frontend
npm run dev
```

## Automated Testing

### Running the Automated Test Script

The automated test script (`test_role_based_access.py`) performs comprehensive RBAC testing:

```bash
cd backend
python test_role_based_access.py
```

### Test Scenarios Covered

1. **Backend Health Check**
   - Verifies backend service is running

2. **Create Test Users**
   - Creates Admin, Recruiter, and Viewer users
   - Registers and logs in each user
   - Obtains JWT tokens for each role

3. **Update User Roles (Optional)**
   - Updates user roles via admin API (if admin exists)
   - Ensures proper role assignment

4. **Admin Access Tests**
   - ✅ Can access `/api/users/` (list users)
   - ✅ Can access `/api/users/{id}` (get user)
   - ✅ Can access `/api/backups/` (list backups)
   - ✅ Can access analytics endpoints
   - ✅ Can update user roles

5. **Recruiter Access Tests**
   - ❌ Cannot access admin endpoints (`/api/users/`, `/api/backups/`)
   - ✅ Can access recruiting endpoints (`/api/candidates/`, `/api/vacancies/`)
   - ✅ Can view analytics (read-only)

6. **Viewer Access Tests**
   - ✅ Can read data (`GET` requests work)
   - ❌ Cannot create data (`POST` requests denied)
   - ❌ Cannot access admin endpoints
   - ✅ Read access to candidates, vacancies, analytics

7. **Permission Enforcement**
   - Admin can update user roles
   - Recruiter cannot update user roles
   - Viewer cannot create backups
   - Cross-role isolation verified

### Expected Output

```
======================================================================
  ROLE-BASED ACCESS CONTROL - END-TO-END TEST
======================================================================
ℹ Backend URL: http://localhost:8000
ℹ Test users: admin, recruiter, viewer

======================================================================
  1. Backend Health Check
======================================================================
✓ Backend is running: AgentHR Backend
ℹ Version: 0.1.0

...

======================================================================
  TEST SUMMARY
======================================================================
✓ PASS: backend_health
✓ PASS: create_test_users
✓ PASS: admin_access
✓ PASS: recruiter_no_admin_access
✓ PASS: recruiter_can_recruit
✓ PASS: viewer_read_only
✓ PASS: viewer_no_admin
✓ PASS: permissions_enforced
✓ PASS: cross_role_isolation

======================================================================
✓ ALL TESTS PASSED!
======================================================================
ℹ Role-based access control is working correctly.
```

## Manual Browser Testing

### Test Case 1: Admin User Access

**Objective**: Verify Admin user can access admin-only features

**Steps**:
1. Navigate to `http://localhost:5173/login`
2. Log in as Admin user:
   - Email: `test_admin@example.com`
   - Password: `TestPass123`
3. Verify successful login and redirect to dashboard
4. Try to access:
   - `/recruiter/candidates` - Should load
   - `/recruiter/vacancies` - Should load
   - `/recruiter/analytics` - Should load
   - `/recruiter/backups` - Should load (admin endpoint)

**Expected Result**:
- ✅ All pages accessible
- ✅ User menu shows "Admin" role
- ✅ No access denied errors

### Test Case 2: Recruiter User Access

**Objective**: Verify Recruiter can access recruiting features but not admin features

**Steps**:
1. Logout (if logged in)
2. Navigate to `http://localhost:5173/login`
3. Log in as Recruiter user:
   - Email: `test_recruiter@example.com`
   - Password: `TestPass123`
4. Verify successful login and redirect to dashboard
5. Try to access:
   - `/recruiter/candidates` - Should load
   - `/recruiter/vacancies` - Should load
   - `/recruiter/analytics` - Should load (read-only)
   - `/recruiter/backups` - Should redirect or show error

**Expected Result**:
- ✅ Recruiting pages accessible
- ❌ Admin pages (backups) show access denied
- ✅ User menu shows "Recruiter" role
- ✅ Can create/edit candidates and vacancies

### Test Case 3: Viewer User Access

**Objective**: Verify Viewer has read-only access

**Steps**:
1. Logout (if logged in)
2. Navigate to `http://localhost:5173/login`
3. Log in as Viewer user:
   - Email: `test_viewer@example.com`
   - Password: `TestPass123`
4. Verify successful login and redirect to dashboard
5. Try to access:
   - `/recruiter/candidates` - Should load (read-only mode)
   - `/recruiter/vacancies` - Should load (read-only mode)
   - `/recruiter/analytics` - Should load
   - Try to create a candidate - Should be disabled or show error
   - Try to edit a candidate - Should be disabled or show error

**Expected Result**:
- ✅ Can view all data
- ❌ Cannot create new candidates/vacancies
- ❌ Cannot edit existing data
- ✅ User menu shows "Viewer" role
- ✅ Create/Edit buttons disabled or hidden

### Test Case 4: Cross-Role Isolation

**Objective**: Verify users cannot access other users' data improperly

**Steps**:
1. Log in as Recruiter
2. Try to access User Management page (if available in UI)
3. Try to access Settings page
4. Logout and log in as Viewer
5. Try to access Admin-only pages

**Expected Result**:
- ❌ Recruiter cannot access User Management
- ❌ Recruiter cannot access Settings
- ❌ Viewer cannot access any admin pages
- ✅ Access denied messages or redirects shown

### Test Case 5: Role-Based UI Elements

**Objective**: Verify UI elements are shown/hidden based on role

**Steps**:
1. Log in as Admin
2. Note which menu items and buttons are visible
3. Logout
4. Log in as Recruiter
5. Compare visible elements
6. Logout
7. Log in as Viewer
8. Compare visible elements

**Expected Result**:
- Admin: All menu items, all buttons visible
- Recruiter: No admin menu items (Users, Settings, Backups)
- Viewer: No create/edit buttons, view-only mode

## API Endpoint Testing

### Test Case 1: Admin Access to User Management

**Objective**: Verify Admin can list and manage users

```bash
# Log in as Admin and get token
ADMIN_TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test_admin@example.com", "password": "TestPass123"}' \
  | jq -r '.access_token')

# List all users (should work)
curl -X GET http://localhost:8000/api/users/ \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq

# Expected: 200 OK with list of users
```

### Test Case 2: Recruiter Cannot Access Users

**Objective**: Verify Recruiter is denied access to user management

```bash
# Log in as Recruiter and get token
RECRUITER_TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test_recruiter@example.com", "password": "TestPass123"}' \
  | jq -r '.access_token')

# Try to list users (should fail)
curl -X GET http://localhost:8000/api/users/ \
  -H "Authorization: Bearer $RECRUITER_TOKEN" \
  -i

# Expected: 403 Forbidden
```

### Test Case 3: Viewer Read-Only Access

**Objective**: Verify Viewer can read but cannot write

```bash
# Log in as Viewer and get token
VIEWER_TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test_viewer@example.com", "password": "TestPass123"}' \
  | jq -r '.access_token')

# Read candidates (should work)
curl -X GET http://localhost:8000/api/candidates/ \
  -H "Authorization: Bearer $VIEWER_TOKEN" \
  -i

# Expected: 200 OK or 404 (if no data)

# Try to create candidate (should fail)
curl -X POST http://localhost:8000/api/candidates/ \
  -H "Authorization: Bearer $VIEWER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Candidate"}' \
  -i

# Expected: 403 Forbidden
```

### Test Case 4: Analytics Access by Role

```bash
# Admin accessing analytics (should work)
curl -X GET http://localhost:8000/api/analytics/key-metrics \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -i

# Expected: 200 OK

# Recruiter accessing analytics (should work - read only)
curl -X GET http://localhost:8000/api/analytics/key-metrics \
  -H "Authorization: Bearer $RECRUITER_TOKEN" \
  -i

# Expected: 200 OK

# Viewer accessing analytics (should work - read only)
curl -X GET http://localhost:8000/api/analytics/key-metrics \
  -H "Authorization: Bearer $VIEWER_TOKEN" \
  -i

# Expected: 200 OK
```

### Test Case 5: Backup Access by Role

```bash
# Admin creating backup (should work)
curl -X POST http://localhost:8000/api/backups/ \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}' \
  -i

# Expected: 200 OK or 201 Created

# Recruiter trying to create backup (should fail)
curl -X POST http://localhost:8000/api/backups/ \
  -H "Authorization: Bearer $RECRUITER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}' \
  -i

# Expected: 403 Forbidden

# Viewer trying to list backups (should fail)
curl -X GET http://localhost:8000/api/backups/ \
  -H "Authorization: Bearer $VIEWER_TOKEN" \
  -i

# Expected: 403 Forbidden
```

## Verification Checklist

### Backend Verification
- [ ] Backend service is running (`/health` returns 200)
- [ ] Database tables exist: `users`, `roles`, `refresh_tokens`
- [ ] Default roles exist in database (Admin, Recruiter, Viewer)
- [ ] Auth dependencies are working (`get_current_user`, `require_role`)
- [ ] JWT tokens are generated correctly
- [ ] Role permissions are stored in `roles.permissions` JSONB field

### Access Control Verification
- [ ] Admin can access `/api/users/` endpoint (200 OK)
- [ ] Recruiter cannot access `/api/users/` endpoint (403 Forbidden)
- [ ] Viewer cannot access `/api/users/` endpoint (403 Forbidden)
- [ ] Admin can access `/api/backups/` endpoint (200 OK)
- [ ] Recruiter cannot access `/api/backups/` endpoint (403 Forbidden)
- [ ] Viewer cannot access `/api/backups/` endpoint (403 Forbidden)
- [ ] All roles can access `/api/analytics/key-metrics` (200 OK)

### Read-Only Verification
- [ ] Viewer can GET `/api/candidates/` (200 OK)
- [ ] Viewer cannot POST `/api/candidates/` (403 Forbidden)
- [ ] Viewer cannot PUT `/api/candidates/{id}` (403 Forbidden)
- [ ] Viewer cannot DELETE `/api/candidates/{id}` (403 Forbidden)
- [ ] Recruiter can POST `/api/candidates/` (200 OK)
- [ ] Admin can POST `/api/candidates/` (200 OK)

### Frontend Verification
- [ ] Login page accepts all test users
- [ ] JWT tokens stored in localStorage after login
- [ ] User role displayed in UI correctly
- [ ] Protected routes redirect unauthenticated users to `/login`
- [ ] Protected routes show access denied for wrong roles
- [ ] UI elements hidden/shown based on user role
- [ ] Logout functionality works for all roles

### Security Verification
- [ ] Passwords are hashed with bcrypt in database
- [ ] JWT tokens are signed correctly
- [ ] Tokens expire after configured time
- [ ] Refresh tokens work correctly
- [ ] Revoked tokens cannot be used
- [ ] SQL injection protection working
- [ ] No sensitive data in JWT payload

## Troubleshooting

### Issue: "Cannot connect to backend"

**Solution**:
```bash
# Check if backend is running
curl http://localhost:8000/health

# If not running, start it:
cd backend
python main.py
```

### Issue: "401 Unauthorized" for all requests

**Possible Causes**:
1. JWT token not included in request
2. JWT token expired
3. JWT token invalid

**Solution**:
```bash
# Check if token is valid
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"

# If expired, log in again to get new token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test_admin@example.com", "password": "TestPass123"}'
```

### Issue: "403 Forbidden" for admin user

**Possible Causes**:
1. User doesn't actually have Admin role
2. Role not properly assigned in database

**Solution**:
```sql
-- Check user's role in database
SELECT u.email, u.name, r.name as role, r.level
FROM users u
JOIN roles r ON u.role_id = r.id
WHERE u.email = 'test_admin@example.com';

-- If role is wrong, update it:
UPDATE users
SET role_id = (SELECT id FROM roles WHERE name = 'Admin')
WHERE email = 'test_admin@example.com';
```

### Issue: "User already registered" error

**Solution**:
```bash
# This is expected if users were created in previous tests
# Just log in with existing credentials
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test_admin@example.com", "password": "TestPass123"}'
```

### Issue: Role not updating via API

**Possible Causes**:
1. Admin token not valid
2. User ID not found
3. Role ID not found

**Solution**:
```bash
# First, list all users to get correct IDs
curl -X GET http://localhost:8000/api/users/ \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq

# Then update role with correct IDs
curl -X PUT http://localhost:8000/api/users/{user_id}/role \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role_id": "role-uuid-here"}'
```

### Issue: Test script fails to create users

**Possible Causes**:
1. Backend not running
2. Database not migrated
3. Email already exists (this is OK)

**Solution**:
```bash
# Check backend health
curl http://localhost:8000/health

# Check database tables
psql -d agenthr -c "\dt"

# If tables don't exist, run migrations:
cd backend
alembic upgrade head
```

## Test Data Cleanup

### Clean up test users from database:

```sql
-- Delete test users
DELETE FROM users
WHERE email IN (
  'test_admin@example.com',
  'test_recruiter@example.com',
  'test_viewer@example.com'
);

-- Or delete all non-admin test users
DELETE FROM users
WHERE email LIKE 'test_%@example.com';

-- Verify cleanup
SELECT email, name, role
FROM users
WHERE email LIKE 'test_%@example.com';
```

### Clean up via API (if admin exists):

```bash
# Get admin token
ADMIN_TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "your_admin@email.com", "password": "YourPassword"}' \
  | jq -r '.access_token')

# Get all users
curl -X GET http://localhost:8000/api/users/ \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq '.users[] | select(.email | contains("test_")) | .id'

# Delete each test user (replace {user_id})
curl -X DELETE http://localhost:8000/api/users/{user_id} \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## Summary

This comprehensive RBAC testing ensures that:

✅ **Admin users** have full system access
✅ **Recruiter users** can manage candidates and vacancies but cannot access admin features
✅ **Viewer users** have read-only access to data
✅ **Role permissions** are properly enforced at both API and UI levels
✅ **Cross-role isolation** prevents unauthorized access
✅ **Security measures** protect sensitive operations

Run the automated test script for quick verification, or perform manual testing for detailed validation of specific scenarios.
