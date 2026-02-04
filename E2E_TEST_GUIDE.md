# End-to-End Test Guide
## Subtask 6-1: Comment Creation and Display Flow

### Overview
This guide provides step-by-step instructions for manually testing the team comments feature end-to-end.

### Prerequisites
1. **Backend Server**: Running on `http://localhost:8000`
2. **Frontend Dev Server**: Running on `http://localhost:5173`
3. **Database**: PostgreSQL running and accessible
4. **Test Data**: At least one candidate/resume in the database

### Automated API Testing

Run the automated test script:
```bash
python test_e2e_team_comments.py
```

This will test:
- ✓ Comment creation via API
- ✓ Comment retrieval (GET by ID)
- ✓ Comment listing (GET with filters)
- ✓ Reply creation (threaded comments)
- ✓ Comment updates
- ✓ Soft delete functionality
- ✓ Database integrity
- ✓ Frontend component file verification

### Manual Browser Testing

#### Test Case 1: Navigate to Candidate Detail Page
1. Open browser to `http://localhost:5173`
2. Login with valid credentials
3. Navigate to Candidates page
4. Click on any candidate to view detail page
5. **Expected**: TeamComments component should be visible on the page

#### Test Case 2: Add a New Comment
1. On candidate detail page, locate the comments section
2. In the comment input field, type: "This candidate has strong React skills"
3. Click "Post Comment" or "Add Comment" button
4. **Expected Results**:
   - Comment appears immediately in the comment list
   - Comment shows your avatar/initials
   - Comment shows timestamp (e.g., "Just now")
   - Comment input field clears after posting
   - Success message or notification appears

#### Test Case 3: Verify Comment in Thread
1. After adding comment, observe the comment list
2. **Expected Results**:
   - Comment displays with full content
   - Author information visible
   - Timestamp visible and accurate
   - Comment has action buttons (Reply, Edit, Delete)
   - Comment is not marked as resolved

#### Test Case 4: Reply to Existing Comment
1. Find the comment you just created
2. Click "Reply" button
3. A reply form should appear below the parent comment
4. Type: "I agree, their portfolio is impressive"
5. Click "Post Reply" or "Reply" button
6. **Expected Results**:
   - Reply appears nested under parent comment
   - Reply is indented to show hierarchy
   - Reply has its own action buttons
   - Parent comment shows reply count (e.g., "1 reply")

#### Test Case 5: Verify Reply Nested Structure
1. Observe the comment thread structure
2. **Expected Results**:
   - Reply is visually nested (indented) under parent
   - Left border or visual indicator shows thread depth
   - Reply can be collapsed/expanded if thread has many replies
   - Parent comment shows "replies" indicator

#### Test Case 6: Check Database Records
1. Open database client or psql:
   ```bash
   psql -U postgres -d agenthr
   ```
2. Query team_comments table:
   ```sql
   SELECT id, resume_id, author_id, content,
          parent_comment_id, is_resolved, is_deleted,
          edits_count, created_at
   FROM team_comments
   ORDER BY created_at DESC
   LIMIT 10;
   ```
3. **Expected Results**:
   - Parent comment has `parent_comment_id = NULL`
   - Reply comment has `parent_comment_id = <parent_comment_id>`
   - Both comments have `is_deleted = FALSE`
   - Both comments have `edits_count = 0` (unless edited)
   - Created timestamps are recent
   - Resume IDs match your test candidate

#### Test Case 7: Edit Comment (Within 5 Minutes)
1. Click "Edit" button on your comment
2. Edit form should appear with current content
3. Modify text to: "This candidate has strong React and TypeScript skills"
4. Click "Save" or "Update" button
5. **Expected Results**:
   - Comment content updates immediately
   - "Edited" indicator appears (e.g., "Edited 1 time")
   - Edit timestamp recorded
   - Success message appears

#### Test Case 8: Delete Comment
1. Click "Delete" button on your reply comment
2. Confirm deletion if prompted
3. **Expected Results**:
   - Reply is removed from display OR marked as deleted
   - If soft delete is visible, comment shows "Deleted" label
   - Parent comment reply count updates

#### Test Case 9: Resolve Comment Thread
1. On the parent comment, click "Resolve" or "Mark as Resolved"
2. **Expected Results**:
   - Comment is visually marked as resolved (strikethrough or badge)
   - "Resolved" chip/badge appears
   - Button changes to "Reopen"
   - Resolved comments can be filtered

### Verification Checklist

Use this checklist to track test completion:

- [ ] Backend API responds to GET /api/team-comments/
- [ ] Backend API responds to POST /api/team-comments/
- [ ] Frontend TeamComments component renders
- [ ] New comment can be created
- [ ] Comment appears in list immediately
- [ ] Comment displays author info
- [ ] Comment displays timestamp
- [ ] Reply can be created
- [ ] Reply appears nested under parent
- [ ] Thread structure is visually clear
- [ ] Comment can be edited within 5 minutes
- [ ] Comment can be deleted (soft delete)
- [ ] Comment can be marked as resolved
- [ ] Database records are correct
- [ ] Foreign key relationships work
- [ ] No console errors in browser
- [ ] No console errors in backend logs

### Database Verification Queries

```sql
-- Check all comments for a resume
SELECT
    id,
    content,
    parent_comment_id,
    is_resolved,
    is_deleted,
    edits_count,
    created_at
FROM team_comments
WHERE resume_id = '<your_resume_id>'
ORDER BY created_at DESC;

-- Count comments by resume
SELECT
    resume_id,
    COUNT(*) as total_comments,
    COUNT(CASE WHEN parent_comment_id IS NULL THEN 1 END) as top_level,
    COUNT(CASE WHEN parent_comment_id IS NOT NULL THEN 1 END) as replies
FROM team_comments
GROUP BY resume_id;

-- Check comment mentions
SELECT
    cm.id,
    tc.content,
    r.username as mentioned_user,
    cm.is_read,
    cm.read_at
FROM comment_mentions cm
JOIN team_comments tc ON cm.comment_id = tc.id
JOIN recruiters r ON cm.mentioned_user_id = r.id;

-- Verify thread structure
WITH RECURSIVE comment_tree AS (
    SELECT
        id,
        content,
        parent_comment_id,
        0 as depth,
        ARRAY[id] as path
    FROM team_comments
    WHERE parent_comment_id IS NULL

    UNION ALL

    SELECT
        tc.id,
        tc.content,
        tc.parent_comment_id,
        ct.depth + 1,
        ct.path || tc.id
    FROM team_comments tc
    JOIN comment_tree ct ON tc.parent_comment_id = ct.id
)
SELECT
    id,
    LEFT(content, 50) as content_preview,
    depth,
    path
FROM comment_tree
ORDER BY path;
```

### Troubleshooting

#### Backend not responding
```bash
# Check if backend is running
curl http://localhost:8000/docs

# Start backend if needed
cd backend && python main.py
```

#### Frontend not loading
```bash
# Check if frontend is running
curl http://localhost:5173

# Start frontend if needed
cd frontend && npm run dev
```

#### Database connection issues
```bash
# Check database is running
docker ps | grep postgres

# Or check PostgreSQL
psql -U postgres -c "SELECT 1"
```

#### Comments not appearing in UI
- Check browser console for errors (F12)
- Check network tab for API responses
- Verify API is returning correct data
- Check frontend component is mounted correctly

#### Replies not nesting properly
- Verify `parent_comment_id` is set in database
- Check frontend component handles parent-child relationships
- Look for JavaScript errors in console

### Expected Results Summary

When all tests pass, you should observe:

1. **API Functionality**:
   - All CRUD endpoints work (Create, Read, Update, Delete, List)
   - Proper HTTP status codes (201, 200, 404, etc.)
   - Threading support via `parent_comment_id`

2. **Frontend Functionality**:
   - TeamComments component renders without errors
   - CommentThread component displays nested replies
   - Real-time updates after API calls
   - Proper error handling and user feedback

3. **Database Integrity**:
   - Comments stored with proper foreign keys
   - Soft delete preserves records
   - Thread structure maintained via parent_comment_id
   - Timestamps and edit counts tracked correctly

4. **User Experience**:
   - Intuitive comment creation
   - Clear visual hierarchy for threads
   - Responsive interface
   - Appropriate feedback messages

### Test Report Template

After completing tests, fill out this report:

```
Date: ________________________
Tester: ________________________

AUTOMATED TESTS:
[ ] Passed  [ ] Failed
Total: _____ passed, _____ failed

MANUAL TESTS:
[ ] Test 1: Navigate to candidate detail - PASSED / FAILED
[ ] Test 2: Add new comment - PASSED / FAILED
[ ] Test 3: Verify comment in thread - PASSED / FAILED
[ ] Test 4: Reply to comment - PASSED / FAILED
[ ] Test 5: Verify nested structure - PASSED / FAILED
[ ] Test 6: Check database records - PASSED / FAILED
[ ] Test 7: Edit comment - PASSED / FAILED
[ ] Test 8: Delete comment - PASSED / FAILED
[ ] Test 9: Resolve thread - PASSED / FAILED

ISSUES FOUND:
1. _________________________________________________
2. _________________________________________________
3. _________________________________________________

OVERALL RESULT: [ ] PASSED [ ] FAILED

Notes:
_____________________________________________________
_____________________________________________________
_____________________________________________________
```

### Success Criteria

The e2e test is considered **PASSED** when:

1. All automated API tests pass (100% pass rate)
2. At least 80% of manual browser tests pass
3. No critical bugs or errors in browser console
4. Database records match API responses
5. Thread structure works correctly (parent-child relationships)
6. Edit and delete functionality work as expected

### Sign-off

Once tests are complete and successful:

1. Update implementation_plan.json:
   - Set subtask-6-1 status to "completed"
   - Add test results to notes field

2. Commit changes:
   ```bash
   git add test_e2e_team_comments.py E2E_TEST_GUIDE.md
   git commit -m "auto-claude: subtask-6-1 - End-to-end test of comment creation and display flow"
   ```

3. Update build-progress.txt with test results
