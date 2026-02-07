# Comment Resolution Functionality - Test Guide

## Overview

This guide provides comprehensive testing procedures for the comment resolution cascading feature. When a parent comment is marked as resolved or unresolved, this status should cascade to all child comments (replies) recursively through the entire thread.

## Feature Description

**Resolution Cascading:**
- When a top-level comment is marked as resolved, all its replies inherit the resolved status
- When a resolved comment is marked as unresolved, all its replies become unresolved
- Cascading works recursively through nested replies (multi-level threading)
- Resolved comments are visually distinguished in the UI with different background color and badge

## Prerequisites

Before testing, ensure:

1. **Backend Service Running:**
   ```bash
   cd backend
   python main.py
   ```
   Backend should be accessible at http://localhost:8000

2. **Frontend Service Running (for visual verification):**
   ```bash
   cd frontend
   npm run dev
   ```
   Frontend should be accessible at http://localhost:5173

3. **Database Running:**
   - PostgreSQL database is accessible
   - Alembic migrations have been applied

4. **Test Data Available:**
   - At least one resume/candidate exists
   - At least one recruiter/user exists

## Automated Tests

### Integration Tests

Run the integration test suite:

```bash
cd backend
pytest tests/integration/test_comment_resolution.py -v
```

**Expected Output:**
```
test_resolve_parent_cascades_to_direct_children PASSED
test_resolve_parent_cascades_to_nested_replies PASSED
test_unresolve_parent_cascades_to_children PASSED
test_cascading_affects_only_descendants PASSED
test_resolve_comment_with_no_children PASSED
test_api_endpoint_resolves_parent_and_children PASSED
```

### End-to-End Script

Run the automated e2e test script:

```bash
python test_comment_resolution_e2e.py
```

**Expected Output:**
```
================================================================================
COMMENT RESOLUTION CASCADING - END-TO-END TESTS
================================================================================

✓ API is accessible

================================================================================
TEST 1: Create Comment Thread with Replies
================================================================================

✓ Created parent comment: [uuid]
✓ Created reply 1: [uuid]
✓ Created nested reply: [uuid]
✓ Created reply 2: [uuid]
✓ Initial state verified: All comments are unresolved

================================================================================
TEST 2: Mark Parent as Resolved - Verify Cascading
================================================================================

✓ Parent comment is resolved
✓ Reply 1 ([uuid]) is resolved ✓
✓ Nested Reply ([uuid]) is resolved ✓
✓ Reply 2 ([uuid]) is resolved ✓
✓ All child comments are resolved - cascading works! ✓

================================================================================
TEST 3: Mark Parent as Unresolved - Verify Cascading
================================================================================

✓ Parent comment is unresolved
✓ Reply 1 ([uuid]) is unresolved ✓
✓ Nested Reply ([uuid]) is unresolved ✓
✓ Reply 2 ([uuid]) is unresolved ✓
✓ All child comments are also unresolved - cascading works! ✓

================================================================================
TEST 4: Visual Distinction in API Response
================================================================================

✓ API response includes 'is_resolved' field
✓ 'is_resolved' is correctly set to True
✓ Can filter comments by is_resolved status

================================================================================
TEST SUMMARY
================================================================================

✓ All tests PASSED
ℹ Comment resolution cascading is working correctly!
```

## Manual Testing Procedures

### Test 1: Create Comment Thread with Replies

**Objective:** Create a multi-level comment thread for resolution testing.

**Steps:**

1. **Get test data IDs:**
   ```bash
   # Query to get resume ID
   psql -U postgres -d agenthr -c "SELECT id, filename FROM resumes LIMIT 1;"

   # Query to get recruiter ID
   psql -U postgres -d agenthr -c "SELECT id, email FROM recruiters LIMIT 1;"
   ```

2. **Create parent comment:**
   ```bash
   curl -X POST http://localhost:8000/api/team-comments/ \
     -H "Content-Type: application/json" \
     -d '{
       "resume_id": "RESUME_UUID",
       "author_id": "AUTHOR_UUID",
       "content": "This is a test parent comment for resolution testing",
       "is_resolved": false
     }'
   ```

   **Expected Response:**
   ```json
   {
     "id": "PARENT_UUID",
     "resume_id": "RESUME_UUID",
     "author_id": "AUTHOR_UUID",
     "parent_comment_id": null,
     "content": "This is a test parent comment for resolution testing",
     "is_resolved": false,
     "is_deleted": false,
     "edits_count": 0,
     "created_at": "2026-02-03T...",
     "updated_at": "2026-02-03T..."
   }
   ```

3. **Create first-level reply:**
   ```bash
   curl -X POST http://localhost:8000/api/team-comments/ \
     -H "Content-Type: application/json" \
     -d '{
       "resume_id": "RESUME_UUID",
       "author_id": "AUTHOR_UUID",
       "content": "This is the first reply",
       "parent_comment_id": "PARENT_UUID",
       "is_resolved": false
     }'
   ```

4. **Create nested reply (second-level):**
   ```bash
   curl -X POST http://localhost:8000/api/team-comments/ \
     -H "Content-Type: application/json" \
     -d '{
       "resume_id": "RESUME_UUID",
       "author_id": "AUTHOR_UUID",
       "content": "This is a nested reply to the first reply",
       "parent_comment_id": "REPLY1_UUID",
       "is_resolved": false
     }'
   ```

5. **Create another first-level reply:**
   ```bash
   curl -X POST http://localhost:8000/api/team-comments/ \
     -H "Content-Type: application/json" \
     -d '{
       "resume_id": "RESUME_UUID",
       "author_id": "AUTHOR_UUID",
       "content": "This is a second reply to the parent",
       "parent_comment_id": "PARENT_UUID",
       "is_resolved": false
     }'
   ```

**Expected Thread Structure:**
```
Parent Comment (PARENT_UUID)
├── Reply 1 (REPLY1_UUID)
│   └── Nested Reply (NESTED_UUID)
└── Reply 2 (REPLY2_UUID)
```

**Verification:**
```bash
# Query database to verify thread structure
psql -U postgres -d agenthr -c "
SELECT
  id,
  LEFT(content, 30) as content,
  parent_comment_id,
  is_resolved
FROM team_comments
WHERE resume_id = 'RESUME_UUID'
ORDER BY created_at;
"
```

**Expected Result:** All comments should have `is_resolved = false`.

---

### Test 2: Mark Parent as Resolved

**Objective:** Verify resolution status cascades to all children when parent is resolved.

**Steps:**

1. **Mark parent comment as resolved:**
   ```bash
   curl -X PUT http://localhost:8000/api/team-comments/PARENT_UUID \
     -H "Content-Type: application/json" \
     -d '{
       "is_resolved": true
     }'
   ```

   **Expected Response:**
   ```json
   {
     "id": "PARENT_UUID",
     "is_resolved": true,
     ...
   }
   ```

2. **Verify parent is resolved:**
   ```bash
   curl http://localhost:8000/api/team-comments/PARENT_UUID
   ```

   **Expected:** `"is_resolved": true`

3. **Verify all children are resolved (cascaded):**
   ```bash
   # Check Reply 1
   curl http://localhost:8000/api/team-comments/REPLY1_UUID | jq '.is_resolved'

   # Check Nested Reply
   curl http://localhost:8000/api/team-comments/NESTED_UUID | jq '.is_resolved'

   # Check Reply 2
   curl http://localhost:8000/api/team-comments/REPLY2_UUID | jq '.is_resolved'
   ```

   **Expected:** All should return `true`

4. **Database verification:**
   ```bash
   psql -U postgres -d agenthr -c "
   SELECT
     id,
     LEFT(content, 30) as content,
     parent_comment_id,
     is_resolved
   FROM team_comments
   WHERE resume_id = 'RESUME_UUID'
   ORDER BY created_at;
   "
   ```

   **Expected Result:**
   ```
        id         |          content          | parent_comment_id | is_resolved
   ----------------+---------------------------+-------------------+-------------
    PARENT_UUID    | This is a test parent...  |                   | t
    REPLY1_UUID    | This is the first reply...| PARENT_UUID       | t
    NESTED_UUID    | This is a nested reply... | REPLY1_UUID       | t
    REPLY2_UUID    | This is a second reply... | PARENT_UUID       | t
   ```

**Success Criteria:**
- ✓ Parent comment `is_resolved = true`
- ✓ Reply 1 `is_resolved = true` (cascaded)
- ✓ Nested Reply `is_resolved = true` (cascaded)
- ✓ Reply 2 `is_resolved = true` (cascaded)

---

### Test 3: Mark Parent as Unresolved

**Objective:** Verify unresolved status cascades to all children.

**Steps:**

1. **Mark parent comment as unresolved:**
   ```bash
   curl -X PUT http://localhost:8000/api/team-comments/PARENT_UUID \
     -H "Content-Type: application/json" \
     -d '{
       "is_resolved": false
     }'
   ```

   **Expected Response:**
   ```json
   {
     "id": "PARENT_UUID",
     "is_resolved": false,
     ...
   }
   ```

2. **Verify parent is unresolved:**
   ```bash
   curl http://localhost:8000/api/team-comments/PARENT_UUID | jq '.is_resolved'
   ```

   **Expected:** `false`

3. **Verify all children are unresolved:**
   ```bash
   # Check all replies
   for id in REPLY1_UUID NESTED_UUID REPLY2_UUID; do
     echo "Checking $id:"
     curl http://localhost:8000/api/team-comments/$id | jq '.is_resolved'
   done
   ```

   **Expected:** All should return `false`

4. **Database verification:**
   ```bash
   psql -U postgres -d agenthr -c "
   SELECT
     id,
     LEFT(content, 30) as content,
     parent_comment_id,
     is_resolved
   FROM team_comments
   WHERE resume_id = 'RESUME_UUID'
   ORDER BY created_at;
   "
   ```

   **Expected Result:** All `is_resolved = false`

**Success Criteria:**
- ✓ Parent comment `is_resolved = false`
- ✓ All children `is_resolved = false` (cascaded)

---

### Test 4: Visual Distinction in Frontend

**Objective:** Verify resolved comments are visually distinguished in the UI.

**Steps:**

1. **Navigate to candidate detail page:**
   - Open browser to http://localhost:5173
   - Find and click on the candidate used for testing

2. **Observe comment section:**
   - Locate the comment thread created in Test 1

3. **Mark a comment as resolved (via UI):**
   - Find the "Resolve" button on the parent comment
   - Click "Resolve"
   - Observe the changes

**Expected Visual Changes:**
- ✓ Comment background color changes to gray/disabled background
- ✓ "Resolved" badge/chip appears with checkmark icon
- ✓ "Resolve" button changes to "Reopen"

4. **Verify all child comments also show resolved status:**
- ✓ All replies have grayed background
- ✓ All replies show "Resolved" badge
- ✓ Visual hierarchy is maintained (indentation)

5. **Reopen the thread:**
   - Click "Reopen" on parent comment
   - Verify all comments return to normal appearance

**Expected Visual Changes (Reopen):**
- ✓ All backgrounds return to white/normal
- ✓ "Resolved" badges disappear
- ✓ "Reopen" button changes back to "Resolve"

**Success Criteria:**
- ✓ Resolved comments have distinct visual appearance (background color)
- ✓ Resolved badge is visible with checkmark icon
- ✓ All child comments inherit visual distinction
- ✓ Reopen thread restores normal appearance

---

### Test 5: Cascade Does Not Affect Other Threads

**Objective:** Verify cascading only affects descendants, not unrelated comments.

**Steps:**

1. **Create two separate comment threads:**
   ```bash
   # Thread 1
   curl -X POST http://localhost:8000/api/team-comments/ \
     -H "Content-Type: application/json" \
     -d '{
       "resume_id": "RESUME_UUID",
       "author_id": "AUTHOR_UUID",
       "content": "Thread 1 - Parent",
       "is_resolved": false
     }'

   # Thread 2
   curl -X POST http://localhost:8000/api/team-comments/ \
     -H "Content-Type: application/json" \
     -d '{
       "resume_id": "RESUME_UUID",
       "author_id": "AUTHOR_UUID",
       "content": "Thread 2 - Parent",
       "is_resolved": false
     }'
   ```

2. **Add replies to each thread:**
   ```bash
   # Reply to Thread 1
   curl -X POST http://localhost:8000/api/team-comments/ \
     -H "Content-Type: application/json" \
     -d '{
       "resume_id": "RESUME_UUID",
       "author_id": "AUTHOR_UUID",
       "content": "Thread 1 - Reply",
       "parent_comment_id": "THREAD1_PARENT_UUID"
     }'

   # Reply to Thread 2
   curl -X POST http://localhost:8000/api/team-comments/ \
     -H "Content-Type: application/json" \
     -d '{
       "resume_id": "RESUME_UUID",
       "author_id": "AUTHOR_UUID",
       "content": "Thread 2 - Reply",
       "parent_comment_id": "THREAD2_PARENT_UUID"
     }'
   ```

3. **Mark Thread 1 parent as resolved:**
   ```bash
   curl -X PUT http://localhost:8000/api/team-comments/THREAD1_PARENT_UUID \
     -H "Content-Type: application/json" \
     -d '{"is_resolved": true}'
   ```

4. **Verify Thread 1 is resolved:**
   ```bash
   # Check Thread 1 parent and child
   curl http://localhost:8000/api/team-comments/THREAD1_PARENT_UUID | jq '.is_resolved'
   curl http://localhost:8000/api/team-comments/THREAD1_REPLY_UUID | jq '.is_resolved'
   ```
   **Expected:** Both return `true`

5. **Verify Thread 2 is NOT resolved:**
   ```bash
   # Check Thread 2 parent and child
   curl http://localhost:8000/api/team-comments/THREAD2_PARENT_UUID | jq '.is_resolved'
   curl http://localhost:8000/api/team-comments/THREAD2_REPLY_UUID | jq '.is_resolved'
   ```
   **Expected:** Both return `false`

**Success Criteria:**
- ✓ Thread 1 parent and child are resolved
- ✓ Thread 2 parent and child remain unresolved
- ✓ Cascading is isolated to descendants only

---

## Database Verification Queries

### Check All Comments in Thread

```sql
SELECT
  id,
  LEFT(content, 40) as content,
  parent_comment_id,
  is_resolved,
  is_deleted,
  edits_count,
  created_at
FROM team_comments
WHERE resume_id = 'YOUR_RESUME_UUID'
ORDER BY created_at;
```

### Count Resolved vs Unresolved

```sql
SELECT
  is_resolved,
  COUNT(*) as count
FROM team_comments
WHERE resume_id = 'YOUR_RESUME_UUID'
GROUP BY is_resolved;
```

### Find All Descendants of a Comment (Recursive)

```sql
WITH RECURSIVE comment_tree AS (
  -- Start with the parent comment
  SELECT id, content, parent_comment_id, is_resolved, 1 as level
  FROM team_comments
  WHERE id = 'PARENT_COMMENT_UUID'

  UNION ALL

  -- Recursively find children
  SELECT c.id, c.content, c.parent_comment_id, c.is_resolved, ct.level + 1
  FROM team_comments c
  JOIN comment_tree ct ON c.parent_comment_id = ct.id
)
SELECT
  level,
  id,
  LEFT(content, 40) as content,
  is_resolved
FROM comment_tree
ORDER BY level, created_at;
```

### Verify Foreign Key Relationships

```sql
SELECT
  tc.id as comment_id,
  LEFT(tc.content, 30) as content,
  tc.parent_comment_id,
  parent.content as parent_content,
  tc.is_resolved
FROM team_comments tc
LEFT JOIN team_comments parent ON tc.parent_comment_id = parent.id
WHERE tc.resume_id = 'YOUR_RESUME_UUID'
ORDER BY tc.created_at;
```

---

## Troubleshooting

### Issue: Cascading Not Working

**Symptoms:**
- Parent marked as resolved but children remain unresolved

**Checks:**
1. **Verify API endpoint code:**
   ```bash
   grep -A 30 "_cascade_resolution_status" backend/api/team_comments.py
   ```
   Should see the cascading logic.

2. **Check backend logs:**
   ```bash
   # Look for errors when updating comment
   tail -f backend/logs/app.log | grep -i "resolution\|cascade"
   ```

3. **Verify database state:**
   ```bash
   # Check if values actually changed in database
   psql -U postgres -d agenthr -c "
   SELECT id, is_resolved FROM team_comments WHERE id = 'CHILD_COMMENT_ID';
   "
   ```

**Solution:**
- Ensure `_cascade_resolution_status` function is being called in `update_team_comment`
- Check for database transaction issues (commit/rollback)
- Verify no errors in cascading logic

---

### Issue: Frontend Not Showing Resolved Status

**Symptoms:**
- API shows `is_resolved: true` but UI doesn't reflect it

**Checks:**
1. **Verify frontend component is reading `is_resolved`:**
   ```bash
   grep -n "is_resolved" frontend/src/components/TeamComments.tsx
   grep -n "is_resolved" frontend/src/components/CommentThread.tsx
   ```

2. **Check browser console for errors:**
   - Open DevTools (F12)
   - Look for JavaScript errors
   - Check Network tab for API responses

3. **Verify API response format:**
   ```bash
   curl http://localhost:8000/api/team-comments/COMMENT_ID | jq '.is_resolved'
   ```

**Solution:**
- Ensure frontend is calling `GET /api/team-comments/{id}` after update
- Check if React state is being updated correctly
- Verify visual styling is applied based on `is_resolved` prop

---

### Issue: Performance Problems with Large Threads

**Symptoms:**
- Resolving a comment takes a long time
- Database queries are slow

**Checks:**
1. **Check thread depth:**
   ```sql
   WITH RECURSIVE thread_depth AS (
     SELECT id, 1 as depth
     FROM team_comments
     WHERE id = 'PARENT_ID'

     UNION ALL

     SELECT tc.id, td.depth + 1
     FROM team_comments tc
     JOIN thread_depth td ON tc.parent_comment_id = td.id
   )
   SELECT MAX(depth) as max_depth FROM thread_depth;
   ```

2. **Explain query plan:**
   ```sql
   EXPLAIN ANALYZE
   SELECT * FROM team_comments
   WHERE parent_comment_id = 'SOME_UUID';
   ```

**Solution:**
- Ensure indexes exist on `parent_comment_id`
- Consider adding depth limits in UI (max 5 levels)
- Optimize recursive queries if needed

---

## Performance Benchmarks

Expected performance for resolution cascading:

| Thread Depth | Total Comments | Cascading Time | Notes |
|--------------|----------------|----------------|-------|
| 2 levels     | 3 comments     | < 50ms         | Parent + 2 direct replies |
| 3 levels     | 5 comments     | < 100ms        | Parent → Reply → Nested Reply |
| 5 levels     | 10 comments    | < 200ms        | Deep nesting |
| 10 levels    | 50 comments    | < 500ms        | Complex thread |

If times exceed these benchmarks, investigate:
- Database indexes on `parent_comment_id`
- Network latency
- Recursive query optimization

---

## Security Considerations

1. **Authorization:**
   - Only comment authors should be able to change resolution status
   - Verify authorization checks are in place

2. **Input Validation:**
   - `is_resolved` must be boolean
   - Reject invalid values

3. **SQL Injection:**
   - Use parameterized queries (SQLAlchemy handles this)
   - Never concatenate user input into SQL

---

## Expected Results Checklist

After completing all tests, verify:

- [ ] **Test 1:** Comment thread created successfully with proper parent-child relationships
- [ ] **Test 2:** Marking parent as resolved cascades to all children (direct + nested)
- [ ] **Test 3:** Marking parent as unresolved cascades to all children
- [ ] **Test 4:** Resolved comments visually distinguished in UI (background color, badge)
- [ ] **Test 5:** Cascading affects only descendants, not unrelated comments
- [ ] **Database:** All records updated correctly in `team_comments` table
- [ ] **API:** All API responses include correct `is_resolved` values
- [ ] **Frontend:** Visual updates reflect resolution status immediately
- [ ] **Performance:** Cascading completes within acceptable time limits
- [ ] **Security:** Only comment authors can change resolution status

---

## Additional Test Scenarios

### Edge Case: Resolving Comment with No Children

**Steps:**
1. Create a standalone comment (no replies)
2. Mark it as resolved

**Expected:**
- ✓ No errors occur
- ✓ Comment is marked as resolved
- ✓ Cascading function handles empty children list gracefully

### Edge Case: Deeply Nested Thread

**Steps:**
1. Create a thread 10+ levels deep
2. Mark top-level parent as resolved

**Expected:**
- ✓ All levels are marked as resolved
- ✓ Performance remains acceptable
- ✓ No maximum recursion depth errors

### Edge Case: Concurrent Updates

**Steps:**
1. User A marks parent as resolved
2. User B simultaneously marks a child as unresolved

**Expected:**
- ✓ Last write wins (or appropriate conflict resolution)
- ✓ No database corruption
- ✓ Consistent state after both updates complete

---

## Test Report Template

Use this template to document your test results:

```
COMMENT RESOLUTION TEST REPORT
Date: [TEST_DATE]
Tester: [TESTER_NAME]
Environment: [DEV/STAGING/PROD]

SUMMARY:
- Total Tests Run: [NUMBER]
- Tests Passed: [NUMBER]
- Tests Failed: [NUMBER]
- Pass Rate: [PERCENTAGE]

DETAILED RESULTS:

Test 1: Create Comment Thread
Status: [PASS/FAIL]
Notes: [OBSERVATIONS]

Test 2: Mark Parent as Resolved
Status: [PASS/FAIL]
Notes: [OBSERVATIONS]

Test 3: Mark Parent as Unresolved
Status: [PASS/FAIL]
Notes: [OBSERVATIONS]

Test 4: Visual Distinction
Status: [PASS/FAIL]
Notes: [OBSERVATIONS]

Test 5: Cascade Isolation
Status: [PASS/FAIL]
Notes: [OBSERVATIONS]

ISSUES FOUND:
1. [DESCRIPTION]
   Severity: [LOW/MEDIUM/HIGH]
   Status: [OPEN/FIXED]

PERFORMANCE NOTES:
- Average cascading time: [TIME]
- Largest thread tested: [NUMBER] comments

RECOMMENDATIONS:
- [ANY IMPROVEMENTS OR CONCERNS]
```

---

## Conclusion

The comment resolution cascading feature ensures that entire discussion threads can be marked as resolved or unresolved with a single action. This provides a better user experience and maintains consistency across threaded conversations.

For questions or issues, refer to:
- Implementation: `backend/api/team_comments.py` (lines 603-612)
- Tests: `backend/tests/integration/test_comment_resolution.py`
- Frontend: `frontend/src/components/TeamComments.tsx` (line 616)
