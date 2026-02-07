# User Invitation and Organization Membership Workflow - Verification Instructions

This document provides instructions for verifying the user invitation and organization membership workflow implementation.

## Overview

The user invitation workflow tests verify that:
1. Organization admin users can be created
2. New organizations can be created
3. Users can be invited to organizations via email
4. New user accounts are auto-created when inviting non-existent users
5. Invited users can access their organization's data
6. Users cannot see data from organizations they're not members of (data isolation)

## Prerequisites

1. **Backend server running** on `http://localhost:8000`
   ```bash
   cd backend
   source .venv/bin/activate  # If using virtual environment
   python run.py
   ```

2. **Database migrations applied**
   ```bash
   cd backend
   alembic upgrade head
   ```

3. **Required Python packages installed**
   ```bash
   cd backend
   pip install requests pytest pytest-asyncio
   ```

## Verification Methods

### Method 1: Automated Pytest Tests (Recommended)

Run the complete integration test suite:

```bash
cd backend
pytest tests/integration/test_user_invitation_workflow.py -v -s
```

**Expected output:**
- All tests should pass (PASS indicator)
- No failures or errors
- Test summary shows 10+ tests passed

**Key test cases:**
- `test_create_organization_admin_user` - Creates admin user
- `test_create_new_organization` - Creates organization
- `test_invite_user_to_organization_as_member` - Invites user via email
- `test_verify_user_can_access_organization_data` - Verifies user access
- `test_verify_user_cannot_see_other_organizations` - **Critical isolation test**
- `test_invite_existing_user_to_organization` - Multi-org membership
- `test_duplicate_invition_fails` - Duplicate prevention
- `test_invite_with_invalid_role_fails` - Role validation
- `test_invite_to_nonexistent_organization_fails` - Error handling
- `test_get_user_organizations` - Query user memberships

### Method 2: Standalone Verification Script

Run the standalone Python script:

```bash
cd backend
python scripts/test_user_invitation_workflow.py
```

**With custom URL:**
```bash
python scripts/test_user_invitation_workflow.py --url http://localhost:8000
```

**Expected output:**
```
============================================================
User Invitation and Organization Membership Workflow Tests
============================================================

============================================================
Step 1: Create Organization Admin User
============================================================
✓ Admin user created: admin@companya.com
  User ID: abc-123...
  Name: Alice Admin
  Role: admin

============================================================
Step 2: Create New Organization
============================================================
✓ Organization created: Company A
  Organization ID: def-456...
  Slug: company-a
  Active: True

============================================================
Step 3: Invite User to Organization as Member
============================================================
✓ User invited to organization: bob@companya.com
  User ID: 789-ghi...
  Name: bob
  Organization: Company A
  Role: member
  Member since: 2026-02-03T...

============================================================
Step 4: Verify User Can Access Organization Data
============================================================
✓ User has access to 1 organization(s)
  - Company A (member)
✓ User can access their organization's data

============================================================
Step 5: Verify User Cannot See Other Organizations
============================================================
✓ Created Organization B: Company B
✓ Invited Charlie to Organization B
✓ Bob can only see his own organization (Company A)
  Bob's organizations: ['Company A']
✓ CROSS-ORGANIZATION LEAKAGE PREVENTED ✓

============================================================
Test Summary
============================================================
  Create Admin User: PASS
  Create Organization: PASS
  Invite User: PASS
  Verify User Access: PASS
  Verify Organization Isolation: PASS

Results: 5/5 tests passed
ALL TESTS PASSED ✓
```

### Method 3: Manual API Testing with cURL

Test each step manually using cURL:

#### Step 1: Create Admin User
```bash
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@test.com",
    "name": "Admin User",
    "role": "admin",
    "is_active": true
  }'
```

**Expected:** 201 Created with user ID

#### Step 2: Create Organization
```bash
curl -X POST http://localhost:8000/api/organizations/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Organization",
    "slug": "test-org"
  }'
```

**Expected:** 201 Created with organization ID

#### Step 3: Invite User to Organization
Replace `{ORG_ID}` with the organization ID from Step 2:
```bash
curl -X POST http://localhost:8000/api/organizations/{ORG_ID}/invite \
  -H "Content-Type: application/json" \
  -d '{
    "email": "member@test.com",
    "role": "member"
  }'
```

**Expected:** 201 Created with user and membership details

#### Step 4: Verify User Access
Replace `{USER_ID}` with the user ID from Step 3:
```bash
curl http://localhost:8000/api/users/{USER_ID}/organizations
```

**Expected:** 200 OK with list of organizations (should include the invited org)

#### Step 5: Verify Isolation
Create two organizations and invite different users, then verify each user sees only their organization.

## Troubleshooting

### Issue: "Connection refused" error
**Solution:** Ensure backend server is running on `http://localhost:8000`

### Issue: "404 Not Found" on invite endpoint
**Solution:** Verify organizations router is registered in `backend/main.py`

### Issue: "User already a member" error
**Solution:** This is expected behavior when inviting the same user twice. Use a different email for testing.

### Issue: Tests fail with database errors
**Solution:** Run database migrations:
```bash
cd backend
alembic upgrade head
```

### Issue: Pytest not found
**Solution:** Install pytest:
```bash
cd backend
pip install pytest pytest-asyncio
```

## Success Criteria

The implementation is successful when:

- [x] Admin users can be created via `/api/users/` POST endpoint
- [x] Organizations can be created via `/api/organizations/` POST endpoint
- [x] Users can be invited via `/api/organizations/{org_id}/invite` endpoint
- [x] New user accounts are auto-created for non-existent emails
- [x] Invited users can see their organization in `/api/users/{user_id}/organizations`
- [x] **Critical:** Users cannot see data from organizations they're not members of
- [x] Duplicate invitations are rejected (400 Bad Request)
- [x] Invalid roles are rejected (400 Bad Request)
- [x] Invitations to non-existent organizations fail (404 Not Found)

## Related Files

- **Test suite:** `backend/tests/integration/test_user_invitation_workflow.py`
- **Verification script:** `backend/scripts/test_user_invitation_workflow.py`
- **Organizations API:** `backend/api/organizations.py`
- **Users API:** `backend/api/users.py`
- **Models:** `backend/models/organization.py`, `backend/models/user.py`, `backend/models/organization_user.py`

## Next Steps

After successful verification:
1. Review test coverage and add edge cases if needed
2. Run performance tests for large user counts
3. Test concurrent invitation scenarios
4. Verify frontend integration (subtask-6-3)
