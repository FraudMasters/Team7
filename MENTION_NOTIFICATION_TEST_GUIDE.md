# @Mention Notification Flow - Testing Guide

## Overview

This guide provides comprehensive testing procedures for the @mention notification feature in team comments.

## Feature Flow

```
1. User creates comment with @mention
   ↓
2. API extracts mentions using regex
   ↓
3. CommentMention records created in database
   ↓
4. Celery tasks triggered asynchronously
   ↓
5. Notifications sent to mentioned users
```

## Pre-Test Setup

### 1. Start Services

```bash
# Terminal 1: Start backend server
cd backend
python main.py

# Terminal 2: Start Celery worker
cd backend
celery -A app.celery worker --loglevel=info

# Terminal 3: Run tests
python test_mention_notification_flow.py
```

### 2. Create Test Data

```sql
-- Create test resume
INSERT INTO resumes (id, filename, file_path, status, created_at, updated_at)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'john_developer.pdf',
    '/test/john_developer.pdf',
    'processed',
    NOW(),
    NOW()
);

-- Create test recruiters (author and mentioned user)
INSERT INTO recruiters (id, email, name, created_at, updated_at)
VALUES
    (
        '11111111-1111-1111-1111-111111111111',
        'author@example.com',
        'Author User',
        NOW(),
        NOW()
    ),
    (
        '22222222-2222-2222-2222-222222222222',
        'mentioned@example.com',
        'Mentioned User',
        NOW(),
        NOW()
    ),
    (
        '33333333-3333-3333-3333-333333333333',
        'another@example.com',
        'Another Mentioned',
        NOW(),
        NOW()
    );
```

## Automated Testing

### Run the Test Script

```bash
python test_mention_notification_flow.py
```

### Run Integration Tests

```bash
cd backend
pytest tests/integration/test_mention_notifications.py -v
```

## Manual Testing Procedures

### Test 1: Single @mention

**Steps:**

1. Create a comment with a single @mention:

```bash
curl -X POST http://localhost:8000/api/team-comments/ \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "00000000-0000-0000-0000-000000000001",
    "author_id": "11111111-1111-1111-1111-111111111111",
    "content": "@mentioned what do you think about this candidate?",
    "is_resolved": false
  }'
```

2. Verify response (should return 201):

```json
{
  "id": "comment-uuid",
  "resume_id": "...",
  "author_id": "...",
  "content": "@mentioned what do you think about this candidate?",
  "is_resolved": false,
  "is_deleted": false,
  "edits_count": 0,
  "created_at": "2025-02-03T...",
  "updated_at": "2025-02-03T..."
}
```

3. Check CommentMention record in database:

```sql
SELECT
    id,
    comment_id,
    mentioned_user_id,
    is_read,
    created_at
FROM comment_mentions
WHERE comment_id = 'comment-uuid';
```

**Expected Result:** 1 CommentMention record with `is_read = false`

4. Check Celery worker logs:

```bash
# Should see log like:
# INFO Triggered mention notification for user: mentioned@example.com
# INFO Task [task-id]: Formatting mention notification email
# INFO Task [task-id]: Sending mention notification email
```

5. Check notification logs (or email):

```
Subject: 💭 You were mentioned in a comment about John Developer
To: mentioned@example.com
Body:
  You were mentioned in a team comment

  Candidate: John Developer
  Author: Author User (author@example.com)
  Time: 2025-02-03T...

  Comment:
    @mentioned what do you think about this candidate?
```

---

### Test 2: Multiple @mentions

**Steps:**

1. Create comment with multiple @mentions:

```bash
curl -X POST http://localhost:8000/api/team-comments/ \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "00000000-0000-0000-0000-000000000001",
    "author_id": "11111111-1111-1111-1111-111111111111",
    "content": "@mentioned and @another should review this candidate together",
    "is_resolved": false
  }'
```

2. Verify CommentMention records:

```sql
SELECT * FROM comment_mentions WHERE comment_id = 'comment-uuid';
```

**Expected Result:** 2 CommentMention records (one for each mentioned user)

3. Check Celery logs:

```
# Should see 2 task executions:
INFO Triggered mention notification for user: mentioned@example.com
INFO Triggered mention notification for user: another@example.com
```

4. Verify notifications sent to both users.

---

### Test 3: Self-Mention Exclusion

**Steps:**

1. Create comment where author mentions themselves:

```bash
curl -X POST http://localhost:8000/api/team-comments/ \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "00000000-0000-0000-0000-000000000001",
    "author_id": "11111111-1111-1111-1111-111111111111",
    "content": "I agree with @author on this point",
    "is_resolved": false
  }'
```

2. Verify CommentMention records:

```sql
SELECT * FROM comment_mentions WHERE comment_id = 'comment-uuid';
```

**Expected Result:** 0 CommentMention records (self-mention excluded)

3. Check Celery logs:

```
# Should NOT see any mention notification tasks
```

---

### Test 4: Invalid Username

**Steps:**

1. Create comment with non-existent username:

```bash
curl -X POST http://localhost:8000/api/team-comments/ \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "00000000-0000-0000-0000-000000000001",
    "author_id": "11111111-1111-1111-1111-111111111111",
    "content": "What does @nonexistentuser think?",
    "is_resolved": false
  }'
```

2. Verify comment is created successfully (should not fail).

3. Verify CommentMention records:

```sql
SELECT * FROM comment_mentions WHERE comment_id = 'comment-uuid';
```

**Expected Result:** 0 CommentMention records (user not found)

---

### Test 5: Reply with @mention

**Steps:**

1. Create parent comment:

```bash
curl -X POST http://localhost:8000/api/team-comments/ \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "00000000-0000-0000-0000-000000000001",
    "author_id": "11111111-1111-1111-1111-111111111111",
    "content": "This is the parent comment",
    "is_resolved": false
  }'
```

2. Create reply with @mention:

```bash
curl -X POST http://localhost:8000/api/team-comments/ \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "00000000-0000-0000-0000-000000000001",
    "author_id": "11111111-1111-1111-1111-111111111111",
    "parent_comment_id": "parent-comment-uuid",
    "content": "@mentioned what is your opinion?",
    "is_resolved": false
  }'
```

3. Verify both mention and reply notifications are triggered.

---

## Database Verification Queries

### Check all mentions for a comment

```sql
SELECT
    cm.id,
    cm.comment_id,
    tc.content,
    cm.mentioned_user_id,
    r.email AS mentioned_email,
    r.name AS mentioned_name,
    cm.is_read,
    cm.read_at,
    cm.created_at
FROM comment_mentions cm
JOIN team_comments tc ON cm.comment_id = tc.id
JOIN recruiters r ON cm.mentioned_user_id = r.id
WHERE tc.id = 'comment-uuid'
ORDER BY cm.created_at;
```

### Count mentions per comment

```sql
SELECT
    tc.id,
    tc.content,
    COUNT(cm.id) AS mention_count
FROM team_comments tc
LEFT JOIN comment_mentions cm ON tc.id = cm.comment_id
GROUP BY tc.id
ORDER BY mention_count DESC;
```

### Check unread mentions for a user

```sql
SELECT
    cm.id,
    tc.content,
    tc.resume_id,
    r.name AS author_name,
    cm.created_at
FROM comment_mentions cm
JOIN team_comments tc ON cm.comment_id = tc.id
JOIN recruiters r ON tc.author_id = r.id
WHERE cm.mentioned_user_id = 'user-uuid'
  AND cm.is_read = false
ORDER BY cm.created_at DESC;
```

---

## Celery Task Verification

### Check Celery worker status

```bash
celery -A app.celery inspect active
```

### View Celery logs

```bash
# Real-time log monitoring
tail -f celery.log

# Search for mention notification tasks
grep "send_comment_mention_notification" celery.log

# Check for errors
grep -i "error\|exception" celery.log
```

### Monitor task execution

```bash
celery -A app.celery events
```

---

## Troubleshooting

### Issue: CommentMention records not created

**Check:**
1. API logs for errors during mention extraction
2. Verify `get_recruiter_by_username()` is finding users
3. Check database foreign key constraints

**Solution:**
```python
# In team_comments.py, ensure mentions are extracted
mentions = extract_mentions(request.content)
logger.info(f"Extracted mentions: {mentions}")
```

---

### Issue: Celery tasks not triggered

**Check:**
1. Celery worker is running
2. Task import is working (`from tasks.comment_notifications import ...`)
3. `.delay()` is being called (not `.apply_async()`)

**Solution:**
```bash
# Check Celery worker status
celery -A app.celery inspect active

# Restart worker if needed
pkill -f celery
celery -A app.celery worker --loglevel=info
```

---

### Issue: Notifications not sent

**Check:**
1. Email service configuration
2. SMTP settings in config
3. Notification logs for errors

**Solution:**
```python
# In comment_notifications.py, check email sending
logger.info(f"Email prepared: {email_message}")

# If using placeholder, notification will succeed but email won't send
# Check logs for: "Email prepared: from=..., subject=..., to=N recipients"
```

---

## Expected Test Results

### Success Criteria

✅ **Test 1 - Single @mention:**
- Comment created (201 status)
- 1 CommentMention record created
- 1 Celery task triggered
- 1 notification sent

✅ **Test 2 - Multiple @mentions:**
- Comment created (201 status)
- 2 CommentMention records created
- 2 Celery tasks triggered
- 2 notifications sent

✅ **Test 3 - Self-Mention Exclusion:**
- Comment created (201 status)
- 0 CommentMention records created
- 0 Celery tasks triggered
- 0 notifications sent

✅ **Test 4 - Invalid Username:**
- Comment created (201 status)
- 0 CommentMention records created
- 0 Celery tasks triggered
- 0 notifications sent

✅ **Test 5 - Reply with @mention:**
- Reply created (201 status)
- 1 CommentMention record created
- 1 mention notification sent
- 1 reply notification sent (to parent author)

---

## Performance Benchmarks

Expected timings (on local development machine):

- Comment creation: < 100ms
- Mention extraction: < 1ms
- CommentMention record creation: < 10ms
- Celery task triggering: < 50ms (async)
- Notification sending: 100-500ms (async, non-blocking)

Total API response time: < 200ms

---

## Security Considerations

✅ **Mention injection prevented:**
- Only valid usernames (alphanumeric + underscore)
- No SQL injection possible
- No code execution through mentions

✅ **Access control:**
- Only authenticated users can create comments
- Notifications only sent to valid recruiters
- Email addresses not exposed to unauthorized users

✅ **Privacy:**
- Self-mentions excluded (no spam)
- Invalid usernames handled silently
- No notification if user not found

---

## Next Steps

After verification:

1. ✅ Mark subtask-6-2 as complete
2. ✅ Update implementation_plan.json
3. ✅ Commit changes with test files
4. ➡️ Move to subtask-6-3 (comment editing and deletion tests)

---

## Appendix: Test SQL Scripts

### Reset test data

```sql
-- Delete test comments
DELETE FROM comment_mentions WHERE comment_id IN (
    SELECT id FROM team_comments
    WHERE resume_id = '00000000-0000-0000-0000-000000000001'
);

DELETE FROM team_comments
WHERE resume_id = '00000000-0000-0000-0000-000000000001';

-- Delete test recruiters
DELETE FROM recruiters
WHERE id IN (
    '11111111-1111-1111-1111-111111111111',
    '22222222-2222-2222-2222-222222222222',
    '33333333-3333-3333-3333-333333333333'
);

-- Delete test resume
DELETE FROM resumes
WHERE id = '00000000-0000-0000-0000-000000000001';
```

### Bulk create test data

```sql
-- Create 10 test comments with various mention scenarios
INSERT INTO team_comments (id, resume_id, author_id, content, is_resolved, is_deleted, edits_count, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'resume-1', 'author-1', '@user1 review this', false, false, 0, NOW(), NOW()),
    (gen_random_uuid(), 'resume-1', 'author-1', '@user1 and @user2 discuss', false, false, 0, NOW(), NOW()),
    (gen_random_uuid(), 'resume-1', 'author-2', 'No mention here', false, false, 0, NOW(), NOW()),
    -- ... more test cases
;
```

---

**Document Version:** 1.0
**Last Updated:** 2025-02-03
**Author:** Auto-Claude
