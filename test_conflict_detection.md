# Conflict Detection Test Plan

## Overview
This document outlines the manual testing steps for verifying conflict detection in the interview scheduling system.

## Test Environment Setup

### Prerequisites
1. Backend server running on port 8000
2. Database with test recruiters and candidates
3. At least 2 recruiters with connected calendars (Google or Outlook)

### Test Data Required
- Recruiter A (has calendar connected)
- Recruiter B (has calendar connected)
- Candidate X (for scheduling)

## Test Scenarios

### Scenario 1: Schedule First Interview (No Conflict)
**Steps:**
1. Create first interview for Recruiter A at 10:00 AM
2. Use POST `/api/interviews/` with:
   ```json
   {
     "candidate_id": "<candidate_id>",
     "scheduled_start": "2024-01-15T10:00:00Z",
     "duration_minutes": 60,
     "interview_type": "video",
     "title": "First Interview - Recruiter A",
     "participant_ids": ["<recruiter_a_id>"]
   }
   ```
3. Verify response status is 200
4. Verify interview is created in database

**Expected Result:** Interview created successfully, no conflicts

### Scenario 2: Check Availability Before Scheduling
**Steps:**
1. Check availability for Recruiter A at 10:00 AM
2. Use POST `/api/calendar/check-availability` with:
   ```json
   {
     "interviewer_ids": ["<recruiter_a_id>"],
     "start_time": "2024-01-15T10:00:00Z",
     "duration_minutes": 60
   }
   ```
3. Verify response includes:
   - `is_available: false` (should now have conflict)
   - `conflicting_events: ["First Interview - Recruiter A"]`

**Expected Result:** API returns conflict with existing event

### Scenario 3: Attempt to Schedule Conflicting Interview
**Steps:**
1. Attempt to create second interview for Recruiter A at same time (10:00 AM)
2. Use POST `/api/interviews/` with:
   ```json
   {
     "candidate_id": "<candidate_id>",
     "scheduled_start": "2024-01-15T10:00:00Z",
     "duration_minutes": 60,
     "interview_type": "video",
     "title": "Conflicting Interview",
     "participant_ids": ["<recruiter_a_id>"]
   }
   ```
3. Verify frontend displays conflict warning
4. Verify user is warned before booking

**Expected Result:** Conflict warning displayed, user can still schedule but is warned

### Scenario 4: Schedule Non-Conflicting Interview
**Steps:**
1. Schedule interview for Recruiter A at different time (2:00 PM)
2. Use POST `/api/calendar/check-availability` with:
   ```json
   {
     "interviewer_ids": ["<recruiter_a_id>"],
     "start_time": "2024-01-15T14:00:00Z",
     "duration_minutes": 60
   }
   ```
3. Verify response includes `is_available: true`
4. Create interview at this time

**Expected Result:** No conflicts, interview scheduled successfully

### Scenario 5: Multiple Interviewers Availability Check
**Steps:**
1. Check availability for multiple interviewers
2. Use POST `/api/calendar/check-availability` with:
   ```json
   {
     "interviewer_ids": ["<recruiter_a_id>", "<recruiter_b_id>"],
     "start_time": "2024-01-15T10:00:00Z",
     "duration_minutes": 60
   }
   ```
3. Verify response includes availability for both interviewers
4. Verify `all_available: false` if Recruiter A has conflict

**Expected Result:** Individual availability status for each interviewer

## Frontend Testing Steps

### Using InterviewScheduler Component

1. Navigate to candidate detail page
2. Click "Schedule Interview" tab
3. Enter interview details:
   - Title: "Test Conflict Interview"
   - Date: 2024-01-15
   - Time: 10:00
   - Duration: 60 minutes
   - Interviewer ID: <recruiter_a_id>
4. Click "Check Availability" button
5. Verify availability status appears:
   - Green checkmark if available
   - Warning if conflict exists
6. Submit interview scheduling
7. Verify appropriate message displayed

## API Testing Commands

### Check Availability (No Calendar Connection)
```bash
curl -X POST http://localhost:8000/api/calendar/check-availability \
  -H "Content-Type: application/json" \
  -d '{
    "interviewer_ids": ["<recruiter_id>"],
    "start_time": "2024-01-15T10:00:00Z",
    "duration_minutes": 60
  }'
```

Expected response when no calendar connected:
```json
{
  "is_available": false,
  "has_calendar_connection": false,
  "conflicting_events": []
}
```

### Check Availability (With Calendar, No Conflict)
```bash
curl -X POST http://localhost:8000/api/calendar/check-availability \
  -H "Content-Type: application/json" \
  -d '{
    "interviewer_ids": ["<recruiter_a_id>"],
    "start_time": "2024-01-15T14:00:00Z",
    "duration_minutes": 60
  }'
```

Expected response when available:
```json
{
  "start_time": "2024-01-15T14:00:00Z",
  "end_time": "2024-01-15T15:00:00Z",
  "all_available": true,
  "interviewer_availability": [
    {
      "interviewer_id": "...",
      "is_available": true,
      "has_calendar_connection": true,
      "calendar_provider": "google",
      "conflicting_events": []
    }
  ]
}
```

### Check Availability (With Calendar, Has Conflict)
Expected response when conflict exists:
```json
{
  "start_time": "2024-01-15T10:00:00Z",
  "end_time": "2024-01-15T11:00:00Z",
  "all_available": false,
  "interviewer_availability": [
    {
      "interviewer_id": "...",
      "is_available": false,
      "has_calendar_connection": true,
      "calendar_provider": "google",
      "conflicting_events": ["First Interview - Recruiter A"]
    }
  ]
}
```

## Verification Checklist

- [ ] Backend `/api/calendar/check-availability` endpoint returns correct availability
- [ ] Backend calls calendar service's `check_conflict` method
- [ ] Conflicting events are returned in response
- [ ] Frontend displays availability status with visual indicators
- [ ] Frontend shows warning message when conflicts detected
- [ ] User can still schedule interview after being warned
- [ ] Multiple interviewers can be checked simultaneously
- [ ] Interviewers without calendar connections are marked unavailable

## Edge Cases to Test

1. **Interviewer with expired calendar token** - Should show as unavailable
2. **Interviewer with no calendar connection** - Should show as unavailable
3. **Partial overlap** - Interview from 10:00-11:00, check 10:30-11:30
4. **Exact time match** - Interview at 10:00, check 10:00-11:00
5. **Multiple conflicts** - Several events overlapping
6. **Boundary conditions** - Interview ending at 10:00, new one starting at 10:00

## Success Criteria

The conflict detection feature is working correctly when:
1. ✅ Availability check returns actual calendar conflicts (not just connection status)
2. ✅ Conflicting event titles are returned to the user
3. ✅ Frontend displays clear visual feedback (green/red indicators)
4. ✅ User is warned before scheduling conflicting interviews
5. ✅ Multiple interviewers can be checked in one request
6. ✅ Error handling is graceful when calendar API fails

## Implementation Notes

The backend now properly integrates conflict detection:
- Modified `backend/api/calendar.py` check_availability endpoint
- Added import for `get_calendar_service`
- Calls `calendar_service.check_conflict()` for each interviewer with active connection
- Returns list of conflicting event titles
- Handles errors gracefully by marking as unavailable if check fails
