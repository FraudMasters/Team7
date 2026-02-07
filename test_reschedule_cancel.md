# Reschedule/Cancel Workflow Testing Guide

This guide provides manual testing steps for the interview reschedule and cancel workflow. Use this guide to verify that the complete workflow works correctly end-to-end.

## Prerequisites

Before starting the tests, ensure you have:

1. **Backend Server Running**
   ```bash
   cd backend
   python -m uvicorn main:app --reload --port 8000
   ```

2. **Celery Worker Running** (for background calendar tasks)
   ```bash
   cd backend
   celery -A tasks.celery_app worker --loglevel=info
   ```

3. **Test Data Available**
   - At least one candidate in the database
   - At least one recruiter in the database
   - (Optional) Recruiter with connected Google/Outlook calendar for full testing

4. **API Access**
   - API endpoint: `http://localhost:8000`
   - Use tools like `curl`, `httpie`, or Postman for API requests

## Test Scenarios

### Test 1: Create Interview

**Purpose:** Verify that an interview can be created successfully with calendar event creation.

**Steps:**

1. Get test candidate ID:
   ```bash
   curl http://localhost:8000/api/candidates/?limit=1
   ```
   Note the `id` from the first candidate in `items`.

2. Get test recruiter ID:
   ```bash
   curl http://localhost:8000/api/recruiters/?limit=1
   ```
   Note the `id` from the first recruiter in `items`.

3. Create interview for tomorrow at 10 AM UTC:
   ```bash
   curl -X POST http://localhost:8000/api/interviews/ \
     -H "Content-Type: application/json" \
     -d '{
       "candidate_id": "CANDIDATE_ID_HERE",
       "scheduled_start": "2024-01-15T10:00:00Z",
       "duration_minutes": 60,
       "interview_type": "video",
       "title": "Test Interview - Reschedule/Cancel",
       "description": "This interview will be rescheduled and cancelled",
       "participant_ids": ["RECRUITER_ID_HERE"]
     }'
   ```

**Expected Results:**
- ✅ Status code: 200
- ✅ Response contains interview `id`
- ✅ Response contains `scheduled_start` matching the request
- ✅ If calendar connected: `calendar_event_id` is present
- ✅ If calendar connected: `calendar_provider` is "google" or "outlook"
- ✅ Celery task log shows: `Calendar event creation task queued for interview {id}`

**Troubleshooting:**
- If no `calendar_event_id`: Check if recruiter has active calendar connection
- If task not queued: Check Celery worker is running
- If error: Check backend logs for detailed error messages

---

### Test 2: Reschedule Interview

**Purpose:** Verify that an interview can be rescheduled and the calendar event is updated.

**Steps:**

1. Get the interview ID from Test 1.

2. Reschedule to 2 PM UTC:
   ```bash
   curl -X PUT http://localhost:8000/api/interviews/INTERVIEW_ID_HERE \
     -H "Content-Type: application/json" \
     -d '{
       "scheduled_start": "2024-01-15T14:00:00Z"
     }'
   ```

**Expected Results:**
- ✅ Status code: 200
- ✅ Response contains updated `scheduled_start`: "2024-01-15T14:00:00Z"
- ✅ If calendar event existed: Celery task log shows update task queued
- ✅ Wait 2-3 seconds, check calendar provider (Google/Outlook) - event should be updated

**Verification Steps:**

1. Fetch the interview again:
   ```bash
   curl http://localhost:8000/api/interviews/INTERVIEW_ID_HERE
   ```

2. Verify `scheduled_start` is "2024-01-15T14:00:00Z"

3. Check Celery worker logs for:
   ```
   Updating calendar event {event_id} for interview_id={id} using {provider} provider
   Calendar event updated successfully
   ```

4. If Google Calendar connected:
   - Open Google Calendar
   - Find the event
   - Verify time is now 2 PM UTC

5. If Outlook connected:
   - Open Outlook Calendar
   - Find the event
   - Verify time is now 2 PM UTC

**Troubleshooting:**
- If time not updated: Check backend logs for errors
- If calendar event not updated: Check Celery worker logs
- If 404 error: Interview ID may be incorrect

---

### Test 3: Verify Calendar Event Updated

**Purpose:** Confirm that the calendar provider actually updated the event.

**Steps:**

1. Check the interview details again:
   ```bash
   curl http://localhost:8000/api/interviews/INTERVIEW_ID_HERE
   ```

2. Note the `calendar_event_id` from the response.

3. For **Google Calendar**:
   - Use Google Calendar API to fetch the event:
     ```bash
     curl https://www.googleapis.com/calendar/v3/calendars/primary/events/EVENT_ID \
       -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
     ```
   - Verify the `start.dateTime` field shows the new time

4. For **Outlook**:
   - Use Microsoft Graph API to fetch the event:
     ```bash
     curl https://graph.microsoft.com/v1.0/me/events/EVENT_ID \
       -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
     ```
   - Verify the `start.dateTime` field shows the new time

**Expected Results:**
- ✅ Calendar event time matches the rescheduled time
- ✅ Event title is still the same
- ✅ Event description is preserved
- ✅ Attendees list is preserved

---

### Test 4: Cancel Interview

**Purpose:** Verify that an interview can be cancelled and the calendar event is removed.

**Steps:**

1. Cancel the interview:
   ```bash
   curl -X DELETE http://localhost:8000/api/interviews/INTERVIEW_ID_HERE
   ```

**Expected Results:**
- ✅ Status code: 200
- ✅ Response contains: `"message": "Interview deleted successfully"`
- ✅ If calendar event existed: Celery task log shows deletion task queued
- ✅ Wait 2-3 seconds, check calendar provider - event should be removed

**Verification Steps:**

1. Try to fetch the interview again:
   ```bash
   curl http://localhost:8000/api/interviews/INTERVIEW_ID_HERE
   ```

2. Expected: 404 Not Found

3. Check Celery worker logs for:
   ```
   Deleting calendar event {event_id} for interview_id={id} using {provider} provider
   Calendar event deleted successfully
   ```

4. Check the calendar provider:
   - For Google Calendar: Event should be deleted/cancelled
   - For Outlook: Event should be deleted/cancelled

---

### Test 5: Verify Calendar Event Removed

**Purpose:** Confirm that the calendar provider actually removed the event.

**Steps:**

1. Check the interview is deleted:
   ```bash
   curl -i http://localhost:8000/api/interviews/INTERVIEW_ID_HERE
   ```

2. Expected: HTTP 404 Not Found

3. For **Google Calendar**:
   - Try to fetch the event using the API (should return 404 or 410)
   - Or check Google Calendar web UI - event should not appear

4. For **Outlook**:
   - Try to fetch the event using the API (should return 404)
   - Or check Outlook web UI - event should not appear

**Expected Results:**
- ✅ Interview returns 404 Not Found
- ✅ Calendar event is deleted from the provider
- ✅ No error logs in backend or Celery worker

---

### Test 6: Verify Notifications Sent

**Purpose:** Verify that notification emails are sent for reschedule and cancel actions.

**Note:** This requires email service integration. Check your email service logs.

**Steps:**

1. Check email logs for the following events:

   **After reschedule:**
   - Subject: "Interview Rescheduled: [Interview Title]"
   - Recipients: Candidate, Interviewers
   - Body contains: New interview time, location/meeting link

   **After cancellation:**
   - Subject: "Interview Cancelled: [Interview Title]"
   - Recipients: Candidate, Interviewers
   - Body contains: Cancellation notice, original time

**Expected Results:**
- ✅ Email notification sent for reschedule
- ✅ Email notification sent for cancellation
- ✅ Recipients received the emails
- ✅ Email content is correct (time, location, participants)

---

### Test 7: List Interviews (History)

**Purpose:** Verify that interview history can be retrieved even after cancellation.

**Steps:**

1. List all interviews for the candidate:
   ```bash
   curl "http://localhost:8000/api/interviews/?candidate_id=CANDIDATE_ID_HERE"
   ```

**Expected Results:**
- ✅ Status code: 200
- ✅ `total` count reflects created interviews
- ✅ `items` array includes interview records
- ✅ Each interview has correct `candidate_id`, `scheduled_start`, `status`

**Note:** Depending on your soft-delete policy, cancelled interviews may or may not appear in the list.

---

## Automated Testing

For automated testing, run the provided test script:

```bash
python test_reschedule_cancel.py
```

This script will:
1. Fetch test data from the API
2. Create an interview
3. Reschedule it to a different time
4. Verify the reschedule
5. Cancel the interview
6. Verify the cancellation
7. List interviews to check history

**Prerequisites for automated testing:**
- Backend server running on localhost:8000
- Celery worker running
- At least one candidate and recruiter in the database

---

## Common Issues and Solutions

### Issue: "No calendar connection found"

**Cause:** Recruiter doesn't have a connected calendar.

**Solution:** Either:
- Connect a calendar via the CalendarConnectionManager UI
- Use a recruiter that has a connected calendar
- Continue testing without calendar integration (interviews will still work)

### Issue: "Celery task not queued"

**Cause:** Celery worker is not running.

**Solution:**
```bash
cd backend
celery -A tasks.celery_app worker --loglevel=info
```

### Issue: "Calendar event not updated/deleted"

**Cause:** Task is queued but not processed.

**Solution:**
- Check Celery worker is running: `celery -A tasks.celery_app active`
- Check Celery logs for errors
- Verify calendar API credentials are valid

### Issue: "404 Not Found when fetching interview"

**Cause:** Interview was successfully deleted (this is expected after cancellation).

**Solution:** This is the correct behavior. Verify the deletion was successful.

### Issue: "Status 500 when creating interview"

**Cause:** Database or validation error.

**Solution:**
- Check backend logs for detailed error
- Verify UUID format is correct
- Ensure candidate and recruiter IDs exist in database

---

## Success Criteria

The reschedule/cancel workflow is working correctly if:

✅ Interviews can be created successfully
✅ Interviews can be rescheduled to different times
✅ Calendar events are updated when interviews are rescheduled (if calendar connected)
✅ Interview data persists correctly after reschedule
✅ Interviews can be cancelled
✅ Calendar events are deleted when interviews are cancelled (if calendar connected)
✅ Deleted interviews return 404 Not Found
✅ Interview history can be retrieved
✅ No error logs in backend or Celery worker
✅ Notification emails are sent (if email integration configured)

---

## Additional Testing

### Error Handling Tests

1. **Test rescheduling non-existent interview:**
   ```bash
   curl -X PUT http://localhost:8000/api/interviews/00000000-0000-0000-0000-000000000000 \
     -H "Content-Type: application/json" \
     -d '{"scheduled_start": "2024-01-15T14:00:00Z"}'
   ```
   Expected: 404 Not Found

2. **Test cancelling non-existent interview:**
   ```bash
   curl -X DELETE http://localhost:8000/api/interviews/00000000-0000-0000-0000-000000000000
   ```
   Expected: 404 Not Found

3. **Test with invalid UUID format:**
   ```bash
   curl -X PUT http://localhost:8000/api/interviews/invalid-uuid \
     -H "Content-Type: application/json" \
     -d '{"scheduled_start": "2024-01-15T14:00:00Z"}'
   ```
   Expected: 400 Bad Request

### Edge Case Tests

1. **Reschedule to same time:**
   - Should succeed but be a no-op

2. **Reschedule multiple times:**
   - Should update calendar event each time

3. **Cancel already cancelled interview:**
   - Should return 404 Not Found

4. **Reschedule cancelled interview:**
   - Should fail with 404 Not Found

---

## Checklist

Use this checklist to track your testing progress:

- [ ] Test 1: Create Interview
- [ ] Test 2: Reschedule Interview
- [ ] Test 3: Verify Calendar Event Updated
- [ ] Test 4: Cancel Interview
- [ ] Test 5: Verify Calendar Event Removed
- [ ] Test 6: Verify Notifications Sent
- [ ] Test 7: List Interviews (History)
- [ ] Error Handling Tests
- [ ] Edge Case Tests

---

## Notes

- Times in this guide are in UTC. Adjust for your local timezone.
- Calendar event IDs are provider-specific and may be in different formats.
- Celery tasks run asynchronously, so there may be a slight delay before calendar updates.
- If testing without a connected calendar, interviews will still be created/updated/deleted in the database.
