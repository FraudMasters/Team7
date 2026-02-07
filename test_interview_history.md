# Interview History Tracking Testing Guide

This guide provides manual testing steps for verifying interview history tracking in the candidate timeline. Use this guide to ensure that all interviews are properly logged and displayed in the candidate's activity history.

## Prerequisites

Before starting the tests, ensure you have:

1. **Backend Server Running**
   ```bash
   cd backend
   python -m uvicorn main:app --reload --port 8000
   ```

2. **Test Data Available**
   - At least one candidate in the database
   - At least one recruiter in the database

3. **API Access**
   - API endpoint: `http://localhost:8000`
   - Use tools like `curl`, `httpie`, or Postman for API requests

## Test Scenarios

### Test 1: Schedule Multiple Interviews

**Purpose:** Verify that multiple interviews can be scheduled for the same candidate.

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

3. Create first interview (Phone Screen) for tomorrow at 10 AM UTC:
   ```bash
   curl -X POST http://localhost:8000/api/interviews/ \
     -H "Content-Type: application/json" \
     -d '{
       "candidate_id": "CANDIDATE_ID_HERE",
       "scheduled_start": "2024-01-16T10:00:00Z",
       "duration_minutes": 30,
       "interview_type": "phone",
       "title": "Initial Phone Screen",
       "description": "Initial screening call to assess candidate fit",
       "participant_ids": ["RECRUITER_ID_HERE"]
     }'
   ```

4. Create second interview (Technical Interview) for day after tomorrow at 2 PM UTC:
   ```bash
   curl -X POST http://localhost:8000/api/interviews/ \
     -H "Content-Type: application/json" \
     -d '{
       "candidate_id": "CANDIDATE_ID_HERE",
       "scheduled_start": "2024-01-17T14:00:00Z",
       "duration_minutes": 60,
       "interview_type": "video",
       "title": "Technical Interview",
       "description": "Deep technical assessment with senior engineer",
       "participant_ids": ["RECRUITER_ID_HERE"]
     }'
   ```

5. Create third interview (Onsite Panel) for three days later at 11 AM UTC:
   ```bash
   curl -X POST http://localhost:8000/api/interviews/ \
     -H "Content-Type: application/json" \
     -d '{
       "candidate_id": "CANDIDATE_ID_HERE",
       "scheduled_start": "2024-01-18T11:00:00Z",
       "duration_minutes": 90,
       "interview_type": "onsite",
       "title": "Onsite Panel Interview",
       "description": "In-person panel interview with team members",
       "participant_ids": ["RECRUITER_ID_HERE"]
     }'
   ```

**Expected Results:**
- ✅ All three interviews return status code 200
- ✅ Each interview has a unique `id`
- ✅ All interviews have the same `candidate_id`
- ✅ Each interview has different `scheduled_start` times
- ✅ Interview types are different (phone, video, onsite)
- ✅ Durations match the requests (30, 60, 90 minutes)

**Troubleshooting:**
- If error 404: Verify candidate_id and recruiter_id are valid
- If error 400: Check JSON syntax and required fields
- If error 500: Check backend logs for detailed error messages

---

### Test 2: Retrieve Candidate Activity Timeline

**Purpose:** Verify that all scheduled interviews appear in the candidate's activity timeline.

**Steps:**

1. Get all activities for the candidate:
   ```bash
   curl "http://localhost:8000/api/candidate-activities/?resume_id=CANDIDATE_ID_HERE&limit=100"
   ```

2. Filter for interview activities only:
   ```bash
   curl "http://localhost:8000/api/candidate-activities/?resume_id=CANDIDATE_ID_HERE&activity_type=interview_scheduled&limit=100"
   ```

**Expected Results:**
- ✅ Status code: 200
- ✅ Response contains `activities` array
- ✅ Response contains `total_count` field
- ✅ At least 3 activities with `activity_type: "interview_scheduled"`
- ✅ Activities are sorted by `created_at` descending (newest first)
- ✅ Each activity has:
  - `id`: Unique activity ID
  - `activity_type`: "interview_scheduled"
  - `candidate_id`: Matches the candidate ID
  - `created_at`: Timestamp when activity was created
  - `activity_data`: Metadata object with interview details

**Example Response:**
```json
{
  "resume_id": "abc-123",
  "activities": [
    {
      "id": "act-1",
      "activity_type": "interview_scheduled",
      "candidate_id": "abc-123",
      "vacancy_id": null,
      "from_stage": null,
      "to_stage": null,
      "note_id": null,
      "tag_id": null,
      "recruiter_id": null,
      "activity_data": {
        "interview_id": "int-1",
        "interview_title": "Onsite Panel Interview",
        "scheduled_start": "2024-01-18T11:00:00Z",
        "duration_minutes": 90,
        "interview_type": "onsite"
      },
      "reason": null,
      "created_at": "2024-01-15T10:30:00Z"
    },
    // ... more activities
  ],
  "total_count": 3
}
```

**Troubleshooting:**
- If no activities found: Check if interviews were created successfully in Test 1
- If wrong count: Verify `activity_type=interview_scheduled` filter is working
- If missing metadata: Check backend interview creation code for activity logging

---

### Test 3: Verify Interview Details in Activity Metadata

**Purpose:** Verify that interview details are correctly stored in activity metadata.

**Steps:**

1. Get interview_scheduled activities:
   ```bash
   curl "http://localhost:8000/api/candidate-activities/?resume_id=CANDIDATE_ID_HERE&activity_type=interview_scheduled" | jq '.activities[].activity_data'
   ```

2. For each activity, verify the metadata contains all required fields:
   - `interview_id`: UUID of the interview
   - `interview_title`: Title of the interview
   - `scheduled_start`: ISO 8601 timestamp
   - `duration_minutes`: Duration in minutes (number)
   - `interview_type`: Type of interview (phone/video/onsite/technical/panel)

3. Cross-reference with interview details:
   ```bash
   # Get interview ID from activity metadata
   INTERVIEW_ID="from_activity_metadata"

   # Fetch interview details
   curl http://localhost:8000/api/interviews/$INTERVIEW_ID
   ```

**Expected Results:**
- ✅ All activities have non-null `activity_data` field
- ✅ All required fields present in metadata:
  - `interview_id`: Valid UUID format
  - `interview_title`: Non-empty string
  - `scheduled_start`: Valid ISO 8601 timestamp
  - `duration_minutes`: Positive integer (30, 60, 90, etc.)
  - `interview_type`: One of (phone, video, onsite, technical, panel)
- ✅ Metadata matches interview details from `/api/interviews/{id}` endpoint
- ✅ `scheduled_start` timestamps are different for each interview
- ✅ `duration_minutes` matches the interview type (30 for phone, 60 for video, 90 for onsite)

**Verification Example:**
```bash
# Extract and format metadata for inspection
curl -s "http://localhost:8000/api/candidate-activities/?resume_id=CANDIDATE_ID&activity_type=interview_scheduled" \
  | jq '.activities[] | {
      title: .activity_data.interview_title,
      type: .activity_data.interview_type,
      scheduled: .activity_data.scheduled_start,
      duration: .activity_data.duration_minutes
    }'
```

**Expected Output:**
```json
{
  "title": "Initial Phone Screen",
  "type": "phone",
  "scheduled": "2024-01-16T10:00:00Z",
  "duration": 30
}
{
  "title": "Technical Interview",
  "type": "video",
  "scheduled": "2024-01-17T14:00:00Z",
  "duration": 60
}
{
  "title": "Onsite Panel Interview",
  "type": "onsite",
  "scheduled": "2024-01-18T11:00:00Z",
  "duration": 90
}
```

**Troubleshooting:**
- If metadata missing: Verify backend interview creation code creates CandidateActivity
- If field types wrong: Check Pydantic schema serialization in backend
- If timestamps invalid: Verify datetime formatting using `.isoformat()`
- If mismatch with interview details: Check activity creation uses correct interview object

---

### Test 4: List Interviews via Interviews API

**Purpose:** Verify that interviews can be listed via the dedicated interviews API endpoint.

**Steps:**

1. List all interviews for the candidate:
   ```bash
   curl "http://localhost:8000/api/interviews/?candidate_id=CANDIDATE_ID_HERE&limit=100"
   ```

2. Verify the count matches activity timeline:
   ```bash
   # Count via activities API
   ACTIVITY_COUNT=$(curl -s "http://localhost:8000/api/candidate-activities/?resume_id=CANDIDATE_ID&activity_type=interview_scheduled" \
     | jq '.total_count')

   # Count via interviews API
   INTERVIEW_COUNT=$(curl -s "http://localhost:8000/api/interviews/?candidate_id=CANDIDATE_ID" \
     | jq '.total')

   echo "Activities: $ACTIVITY_COUNT, Interviews: $INTERVIEW_COUNT"
   ```

**Expected Results:**
- ✅ Status code: 200
- ✅ Response contains `items` array with interviews
- ✅ Response contains `total` count
- ✅ Count matches activity timeline count (both should be 3)
- ✅ Each interview has all fields populated:
  - `id`: Interview UUID
  - `title`: Interview title
  - `status`: "scheduled" (default)
  - `interview_type`: phone/video/onsite/technical/panel
  - `scheduled_start`: ISO timestamp
  - `duration_minutes`: Duration in minutes
  - `description`: Interview description
  - `participants`: Array of participant objects

**Example Response:**
```json
{
  "items": [
    {
      "id": "int-1",
      "candidate_id": "abc-123",
      "vacancy_id": null,
      "recruiter_id": "recruiter-1",
      "title": "Initial Phone Screen",
      "description": "Initial screening call...",
      "scheduled_start": "2024-01-16T10:00:00Z",
      "scheduled_end": "2024-01-16T10:30:00Z",
      "duration_minutes": 30,
      "interview_type": "phone",
      "status": "scheduled",
      "location": null,
      "meeting_link": null,
      "meeting_room": null,
      "calendar_event_id": null,
      "calendar_provider": null,
      "participants": [
        {
          "id": "part-1",
          "interview_id": "int-1",
          "recruiter_id": "recruiter-1",
          "role": "interviewer",
          "status": "pending"
        }
      ],
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:00:00Z"
    },
    // ... more interviews
  ],
  "total": 3,
  "limit": 100,
  "offset": 0
}
```

**Troubleshooting:**
- If count mismatch: Some interviews may not have activities logged (check backend code)
- If missing participants: Verify participant creation in interview endpoint
- If status wrong: Check default status in Interview model

---

### Test 5: Chronological Ordering

**Purpose:** Verify that activities are ordered chronologically (newest first).

**Steps:**

1. Get activities and extract timestamps:
   ```bash
   curl -s "http://localhost:8000/api/candidate-activities/?resume_id=CANDIDATE_ID&activity_type=interview_scheduled" \
     | jq '.activities[] | .created_at'
   ```

2. Verify timestamps are in descending order (newest to oldest)

**Expected Results:**
- ✅ Activities are sorted by `created_at` descending
- ✅ First activity has the most recent timestamp
- ✅ Last activity has the oldest timestamp
- ✅ Order matches interview creation order (last created = first in list)

**Verification Script:**
```bash
# Check if timestamps are in descending order
TIMESTAMPS=$(curl -s "http://localhost:8000/api/candidate-activities/?resume_id=CANDIDATE_ID&activity_type=interview_scheduled" \
  | jq -r '.activities[].created_at')

# Convert to epochs and check descending
echo "$TIMESTAMPS" | while read timestamp; do
  date -d "$timestamp" +%s
done | awk '
  NR == 1 { prev = $0; next }
  { if ($0 > prev) { print "ERROR: Not in descending order"; exit 1 } }
  END { print "OK: Descending order verified" }'
```

**Troubleshooting:**
- If not descending: Check API query uses `order_by(desc(CandidateActivity.created_at))`
- If all same timestamp: Verify system clock or use different timestamps for each test

---

### Test 6: Frontend Timeline Display

**Purpose:** Verify that the frontend displays interview activities correctly in the candidate timeline component.

**Prerequisites:**
- Frontend server running on localhost:3000
- Backend API accessible from frontend

**Steps:**

1. Navigate to candidate detail page in browser:
   ```
   http://localhost:3000/candidate/CANDIDATE_ID_HERE
   ```

2. If the timeline is on a separate tab, navigate to the timeline/activities tab

3. Verify interview activities are visible

**Expected Results:**
- ✅ Timeline component loads without errors
- ✅ Interview activities displayed with "Interview Scheduled" label
- ✅ Each interview shows:
  - Event icon (calendar/event icon)
  - Activity type chip: "Interview Scheduled" (green/success color)
  - Timestamp (e.g., "2h ago", "1d ago")
  - Description: "Someone scheduled an interview"
  - Author info (recruiter who created the interview)
- ✅ Activities are in chronological order (newest first)
- ✅ No console errors in browser dev tools

**Frontend Component Verification:**

The `CandidateActivityTimeline` component should display:
- Activity type icon: `<EventAvailableIcon />`
- Color chip: `success` (green)
- Label: "Interview Scheduled"

Example rendering:
```tsx
<Box>
  <Chip icon={<EventAvailableIcon />} label="Interview Scheduled" color="success" />
  <Typography variant="body2">
    John Doe scheduled an interview
  </Typography>
  <Typography variant="caption" color="text.secondary">
    2h ago
  </Typography>
</Box>
```

**Troubleshooting:**
- If component not rendering: Check React console for errors
- If no activities: Verify API call is made to `/api/candidate-activities/`
- If wrong format: Check ActivityItem TypeScript types match API response
- If no styling: Verify Material-UI components imported correctly

---

## Success Criteria

All tests are considered passing when:

1. ✅ Multiple interviews can be created for the same candidate
2. ✅ All interviews appear in activity timeline with `activity_type: "interview_scheduled"`
3. ✅ Activity metadata contains all required fields:
   - `interview_id`
   - `interview_title`
   - `scheduled_start`
   - `duration_minutes`
   - `interview_type`
4. ✅ Metadata values match actual interview details
5. ✅ Activities are sorted chronologically (newest first)
6. ✅ Interview count matches between activities API and interviews API
7. ✅ Frontend timeline displays interview activities correctly

## Cleanup

After testing, you may want to clean up test data:

```bash
# Delete test interviews (update IDs)
curl -X DELETE http://localhost:8000/api/interviews/INTERVIEW_ID_1
curl -X DELETE http://localhost:8000/api/interviews/INTERVIEW_ID_2
curl -X DELETE http://localhost:8000/api/interviews/INTERVIEW_ID_3
```

## Common Issues and Solutions

### Issue: Activities not created when interview is scheduled

**Solution:** Verify that `backend/api/interviews.py` creates a `CandidateActivity` in the `create_interview` function:

```python
activity = CandidateActivity(
    candidate_id=interview_data.candidate_id,
    activity_type=CandidateActivityType.INTERVIEW_SCHEDULED,
    metadata={
        "interview_id": str(interview.id),
        "interview_title": interview_data.title,
        "scheduled_start": interview.scheduled_start.isoformat(),
        "duration_minutes": interview_data.duration_minutes,
        "interview_type": interview_data.interview_type,
    },
)
db.add(activity)
await db.commit()
```

### Issue: Activity metadata is null or empty

**Solution:** Check that the `metadata` field (not `activity_data`) is being set. The model uses `metadata` but the API response may serialize it as `activity_data`.

### Issue: Frontend not displaying activities

**Solution:** Verify:
1. API endpoint returns data in correct format
2. TypeScript types match API response structure
3. `CandidateActivityTimeline` component is imported and rendered
4. No console errors in browser dev tools

### Issue: Wrong activity count

**Solution:** Check:
1. All interviews were created successfully (no errors)
2. Database transactions were committed
3. No duplicate activities (check for duplicate interview IDs)

## Additional Verification Queries

For database-level verification (if you have direct database access):

```sql
-- Count interview_scheduled activities for a candidate
SELECT COUNT(*)
FROM candidate_activities
WHERE activity_type = 'interview_scheduled'
  AND candidate_id = 'CANDIDATE_ID_HERE';

-- View interview activity details
SELECT
  id,
  candidate_id,
  created_at,
  metadata->>'interview_title' as title,
  metadata->>'interview_type' as type,
  metadata->>'scheduled_start' as scheduled,
  metadata->>'duration_minutes' as duration
FROM candidate_activities
WHERE activity_type = 'interview_scheduled'
  AND candidate_id = 'CANDIDATE_ID_HERE'
ORDER BY created_at DESC;

-- Verify activities match interviews
SELECT
  ca.id as activity_id,
  ca.metadata->>'interview_id' as interview_id,
  i.title as interview_title,
  i.scheduled_start as interview_scheduled
FROM candidate_activities ca
LEFT JOIN interviews i ON i.id = ca.metadata->>'interview_id'
WHERE ca.activity_type = 'interview_scheduled'
  AND ca.candidate_id = 'CANDIDATE_ID_HERE';
```

---

**End of Testing Guide**
