# Comment Editing and Deletion - Test Guide

This guide provides comprehensive testing procedures for comment editing and deletion with time restrictions.

## Feature Overview

Comments can be edited within **5 minutes** of creation. After this window expires, only the `is_resolved` status can be changed, not the content. Comments are soft-deleted (marked as deleted but preserved in the database).

## Test Files

### 1. Integration Tests (pytest)
**File:** `backend/tests/integration/test_edit_delete_restrictions.py`

Run with:
```bash
cd backend
pytest tests/integration/test_edit_delete_restrictions.py -v
```

### 2. End-to-End Tests
**File:** `backend/tests/integration/test_edit_delete_e2e.py`

Run with:
```bash
cd backend
python tests/integration/test_edit_delete_e2e.py
```

## Test Coverage

### 1. Edit Within Time Window ✅
**Purpose:** Verify comments can be edited within 5 minutes of creation

**Steps:**
1. Create a new comment
2. Immediately edit the comment content
3. Verify edit succeeds
4. Verify `edits_count` increments

**Expected Result:**
- HTTP 200 OK
- Content updated
- `edits_count = 1`

---

### 2. Edit After Time Window ❌
**Purpose:** Verify comments cannot be edited after 5 minutes

**Steps:**
1. Create a comment with `created_at` set to 6 minutes ago
2. Attempt to edit the content
3. Verify edit fails

**Expected Result:**
- HTTP 403 Forbidden
- Error message: "Comment can only be edited within 5 minutes of creation"

---

### 3. Edit at Boundary (5 Minutes) ✅
**Purpose:** Verify the exact 5-minute boundary is inclusive

**Steps:**
1. Create a comment with `created_at` set to exactly 5 minutes ago
2. Attempt to edit the content

**Expected Result:**
- HTTP 200 OK (boundary is inclusive)
- Edit succeeds

---

### 4. Edit Just After Boundary ❌
**Purpose:** Verify edits fail immediately after the window closes

**Steps:**
1. Create a comment with `created_at` set to 5 minutes 1 second ago
2. Attempt to edit the content

**Expected Result:**
- HTTP 403 Forbidden
- Edit fails (1 second over the limit)

---

### 5. Change Resolved Status (No Time Restriction) ✅
**Purpose:** Verify resolved status can be changed anytime

**Steps:**
1. Create a comment with `created_at` set to 10 minutes ago
2. Update `is_resolved` to `true`

**Expected Result:**
- HTTP 200 OK
- `is_resolved = true`
- `edits_count` unchanged (only content changes increment edit count)

---

### 6. Soft Delete ✅
**Purpose:** Verify comments are soft-deleted

**Steps:**
1. Create a comment
2. Delete the comment
3. Check database for the comment

**Expected Result:**
- HTTP 200 OK
- Comment still exists in database
- `is_deleted = true`
- Original content preserved

---

### 7. Deleted Comments Hidden from Default List ✅
**Purpose:** Verify deleted comments don't appear in normal views

**Steps:**
1. Create and delete a comment
2. List comments without `include_deleted` flag

**Expected Result:**
- Deleted comment not in list

---

### 8. Deleted Comments Visible with Flag ✅
**Purpose:** Verify deleted comments can be viewed when requested

**Steps:**
1. Create and delete a comment
2. List comments with `include_deleted=true`

**Expected Result:**
- Deleted comment appears in list
- `is_deleted = true` in response

---

### 9. Retrieve Deleted Comment by ID ✅
**Purpose:** Verify deleted comments can still be retrieved individually

**Steps:**
1. Create and delete a comment
2. GET the comment by ID

**Expected Result:**
- HTTP 200 OK
- Comment returned
- `is_deleted = true` in response

---

### 10. Multiple Edits Within Window ✅
**Purpose:** Verify multiple edits work within the time window

**Steps:**
1. Create a comment
2. Edit it 3 times in quick succession

**Expected Result:**
- All edits succeed
- `edits_count = 3`

---

## Manual Testing with curl

### Create a Comment
```bash
curl -X POST http://localhost:8000/api/team-comments/ \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "your-resume-uuid",
    "author_id": "your-author-uuid",
    "content": "Test comment for editing",
    "is_resolved": false
  }'
```

### Edit Within Window (Immediate)
```bash
curl -X PUT http://localhost:8000/api/team-comments/{comment-id} \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Updated content"
  }'
```

### Edit After Window (Will Fail)
First, manually update the timestamp in database:
```sql
UPDATE team_comments
SET created_at = NOW() - INTERVAL '6 minutes',
    updated_at = NOW() - INTERVAL '6 minutes'
WHERE id = 'your-comment-id';
```

Then try to edit:
```bash
curl -X PUT http://localhost:8000/api/team-comments/{comment-id} \
  -H "Content-Type: application/json" \
  -d '{
    "content": "This should fail"
  }'
```

Expected: `403 Forbidden`

### Change Resolved Status (Always Works)
```bash
curl -X PUT http://localhost:8000/api/team-comments/{comment-id} \
  -H "Content-Type: application/json" \
  -d '{
    "is_resolved": true
  }'
```

### Delete Comment
```bash
curl -X DELETE http://localhost:8000/api/team-comments/{comment-id}
```

### List Comments (Default - No Deleted)
```bash
curl "http://localhost:8000/api/team-comments/?resume_id={resume-id}"
```

### List Comments (Include Deleted)
```bash
curl "http://localhost:8000/api/team-comments/?resume_id={resume-id}&include_deleted=true"
```

## Database Verification Queries

### Check Comment timestamps
```sql
SELECT
  id,
  content,
  created_at,
  updated_at,
  NOW() - created_at as time_since_creation,
  edits_count,
  is_deleted
FROM team_comments
WHERE id = 'your-comment-id';
```

### Check if comment is within edit window
```sql
SELECT
  id,
  content,
  created_at,
  NOW() - created_at as time_since_creation,
  CASE
    WHEN NOW() - created_at <= INTERVAL '5 minutes' THEN 'Editable'
    ELSE 'Not Editable'
  END as edit_status
FROM team_comments
WHERE id = 'your-comment-id';
```

### Verify soft delete
```sql
SELECT
  id,
  content,
  is_deleted,
  created_at,
  updated_at,
  edits_count
FROM team_comments
WHERE id = 'your-comment-id';
```

### List all comments including deleted
```sql
SELECT
  id,
  LEFT(content, 50) as content_preview,
  is_deleted,
  edits_count,
  created_at
FROM team_comments
WHERE resume_id = 'your-resume-id'
ORDER BY created_at DESC;
```

## Troubleshooting

### Issue: Edit succeeds even after 5 minutes
**Cause:** Timezone mismatch between application and database

**Solution:**
- Ensure both use UTC: `datetime.now(timezone.utc)`
- Check database timezone: `SHOW timezone;`
- Set to UTC if needed: `SET timezone = 'UTC';`

### Issue: Edit fails even within 5 minutes
**Cause:** Clock skew or database time ahead of application time

**Solution:**
- Synchronize system clock with NTP
- Check application time vs database time: `SELECT NOW();`

### Issue: Deleted comment still appears in list
**Cause:** Missing `include_deleted=false` filter

**Solution:**
- Verify the API endpoint filters by `is_deleted=False` by default
- Check response includes only non-deleted comments

### Issue: edits_count not incrementing
**Cause:** Only content changes should increment the counter

**Solution:**
- Verify `edits_count` only increments when `content` field changes
- Changing `is_resolved` should NOT increment `edits_count`

## Expected Test Results

All tests should pass with the following summary:

```
PASSED: Create Comment
PASSED: Edit Within 5-Minute Window
PASSED: Edit After 5-Minute Window (Should Fail)
PASSED: Change Resolved Status (No Time Restriction)
PASSED: Delete Comment (Soft Delete)
PASSED: Verify Soft Delete in Database
PASSED: Verify Not in Default List
PASSED: Verify Visible with include_deleted Flag
PASSED: Get Deleted Comment by ID

Total: 9/9 tests passed
```

## Acceptance Criteria Verification

✅ Comments can be edited within 5 minutes of posting
✅ Comments cannot be edited after 5 minutes
✅ Resolved status can be changed anytime
✅ Comments are soft-deleted (preserved in database)
✅ Deleted comments hidden from default views
✅ Deleted comments retrievable by ID
✅ edits_count tracked correctly
