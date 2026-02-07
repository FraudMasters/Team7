# Team Comments - End-to-End Integration Tests

This directory contains end-to-end integration tests for the Team Comments feature.

## Prerequisites

Before running the tests, ensure:

1. **Backend server is running:**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. **Database is set up and migrations applied:**
   ```bash
   cd backend
   alembic upgrade head
   ```

3. **Test data exists in database:**
   - At least one Resume record
   - At least one Recruiter record

   You can create test data using database seed scripts or manually.

## Running the Tests

### Run all end-to-end tests:

```bash
cd backend
python tests/integration/test_comment_e2e.py
```

### Expected Output:

The test suite will:
1. Check backend health
2. List comments (initial state)
3. Create a new comment
4. Verify comment appears in thread
5. Get comment by ID
6. Create a reply to the comment
7. Verify reply appears nested under parent
8. Check database records
9. Update comment
10. Mark comment as resolved

## Test Coverage

The end-to-end test covers the following acceptance criteria:

- ✅ Users can add comments to any candidate profile
- ✅ Users can reply to comments creating threaded discussions
- ✅ Comments are timestamped and attributed to authors
- ✅ Comment history is preserved (verified via database)
- ✅ Comments can be edited
- ✅ Comments can be marked as resolved

## Manual Verification Steps

If you prefer to test manually via the frontend:

1. **Navigate to candidate detail page**
   - Open frontend: http://localhost:5173
   - Navigate to a candidate/resume detail page

2. **Add a new comment via frontend**
   - Find the Team Comments section
   - Type a comment in the text area
   - Click "Post Comment" or similar button
   - Verify comment appears in the thread

3. **Reply to existing comment**
   - Click "Reply" on a comment
   - Type your reply in the reply form
   - Click "Post Reply"
   - Verify reply appears nested under parent comment (indented)

4. **Check database for comment records**
   ```bash
   psql -U agenthr -d agenthr
   SELECT id, resume_id, author_id, content, parent_comment_id, created_at
   FROM team_comments
   ORDER BY created_at DESC
   LIMIT 10;
   ```

## Troubleshooting

### Backend not running
Start the backend server:
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### Database connection errors
Check DATABASE_URL in test_comment_e2e.py matches your setup:
```python
DATABASE_URL = "postgresql+asyncpg://agenthr:agenthr@localhost:agenthr"
```

### No test data found
Create test resumes and recruiters in the database, or run your seed script.

### Permission errors
Ensure you have proper file permissions for the backend/tests directory.

## Test Files

- `test_comment_e2e.py` - Main end-to-end test suite
- `README.md` - This file

## Cleanup

The test script automatically cleans up test data after running. Comments starting with "E2E Test:" are deleted.

To manually clean up:
```bash
psql -U agenthr -d agenthr
DELETE FROM team_comments WHERE content LIKE 'E2E Test:%';
```
