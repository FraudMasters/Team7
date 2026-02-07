# GDPR Data Export Flow - End-to-End Test Documentation

## Overview

This document describes the end-to-end testing approach for the GDPR Data Export functionality, implementing the **Right to Portability** (GDPR Article 15). These tests verify that candidates can export their personal data in a structured, machine-readable format.

**Test File:** `frontend/e2e/gdpr-data-export-flow.spec.ts`
**Test Runner:** `frontend/scripts/test-gdpr-data-export-flow.sh`

---

## Test Coverage

### 1. Frontend UI Tests (Desktop)
- ✅ Display data export dialog on privacy settings page
- ✅ Open data export dialog via quick action card
- ✅ Display info about right to portability
- ✅ Display format selection options (JSON/CSV)
- ✅ Allow selecting JSON format
- ✅ Allow selecting CSV format
- ✅ Disable export button when format not selected

### 2. API Integration Tests
- ✅ Send export request to backend API with JSON format
- ✅ Send export request to backend API with CSV format
- ⏸️ Handle API errors gracefully (requires API mocking)

### 3. File Download Tests
- ✅ Download JSON file after successful export
- ✅ Download CSV file after successful export
- ✅ Verify JSON file content structure
- ✅ Verify CSV file content structure
- ✅ Show data summary after export

### 4. Mobile Responsive Tests
- ✅ Display export dialog correctly on mobile (375x667)
- ✅ Allow exporting data on mobile

### 5. Complete End-to-End Tests
- ✅ Complete export flow with JSON format
- ✅ Complete export flow with CSV format

---

## Manual Testing Steps

If automated tests fail or for additional verification, follow these manual testing steps:

### Prerequisites
1. Backend API running at `http://localhost:8000`
2. Frontend dev server running at `http://localhost:5173`
3. Test candidate data in database (use TEST_RESUME_ID)

### Test Case 1: JSON Export

**Step 1: Navigate to Privacy Settings**
```
1. Open browser to http://localhost:5173
2. Accept cookie banner if shown
3. Navigate to http://localhost:5173/settings/privacy
4. Verify "Privacy Settings" heading is visible
```

**Step 2: Open Data Export Dialog**
```
1. Click "Export My Data" quick action card
2. Verify dialog opens with title about data export
3. Verify info alert mentions "Right to Portability" or "GDPR Article 15"
```

**Step 3: Select JSON Format**
```
1. Locate format selection (radio buttons or cards)
2. Click "JSON" format option
3. Verify JSON option is selected (checked)
4. Read format description (should mention structured, hierarchical data)
```

**Step 4: Initiate Export**
```
1. Click "Export" or "Download" button
2. Wait for progress indicator (circular or linear progress bar)
3. Observe progress percentage (0% to 100%)
4. Do NOT close dialog during export
```

**Step 5: Verify File Download**
```
1. Browser should automatically download file
2. Check filename format: export_{resume_id}_{date}.json
3. Verify file is in Downloads folder
4. File size should be > 0 bytes
```

**Step 6: Verify JSON Content**
```
1. Open downloaded JSON file in text editor
2. Verify JSON is valid (use JSON validator)
3. Verify metadata fields exist:
   - export_timestamp (ISO 8601 format)
   - resume_id (UUID format)
   - format (value: "json")
   - total_records (integer)
4. Verify data sections exist (may be empty for test data):
   - resume (filename, raw_text, language, status, timestamps)
   - hiring_stages (array of stage objects)
   - notes (array of note objects)
   - tags (array of tag objects)
   - activities (array of activity objects)
```

**Step 7: Verify PII Data**
```
1. Check if resume object contains personal information:
   - Email addresses
   - Phone numbers
   - Names (if present in parsed resume)
   - Location/address
   - Skills (from parsed resume)
   - Work experience
   - Education
2. Verify all PII is included in export
```

**Step 8: Verify Success Message**
```
1. Dialog should show success alert
2. Message should say "Export successful" or similar
3. Display data summary (number of records exported)
4. Show file ready confirmation
5. Dialog may remain open for additional exports
```

### Test Case 2: CSV Export

**Steps 1-3: Same as JSON Export**
Follow steps 1-3 from Test Case 1, but select CSV format in Step 3.

**Step 4: Initiate Export**
```
1. Click "Export" or "Download" button
2. Wait for progress indicator
3. Observe progress percentage
```

**Step 5: Verify File Download**
```
1. Browser should automatically download file
2. Check filename format: export_{resume_id}_{date}.csv
3. Verify file is in Downloads folder
4. File size should be > 0 bytes
```

**Step 6: Verify CSV Content**
```
1. Open downloaded CSV file in spreadsheet software
2. Verify CSV structure:
   - First row contains headers
   - Each subsequent row represents a record
   - record_type column indicates record category
3. Verify columns include PII fields:
   - email, phone, name (if available)
   - skills, work_experience, education
   - stage_name, note_content, tag_name, etc.
4. Verify no truncated or corrupted data
```

**Step 7: Verify Machine-Readable Format**
```
1. Try importing CSV into Excel/Google Sheets
2. Verify data imports correctly without parsing errors
3. Verify special characters are properly escaped
4. Verify dates/timestamps are in ISO format
```

### Test Case 3: Error Handling

**Step 1: Simulate Network Error**
```
1. Open browser DevTools (F12)
2. Go to Network tab
3. Enable "Offline" mode or block API requests
4. Attempt export
5. Verify error message displays
6. Verify "Retry" button appears
7. Go back online and retry
8. Verify export succeeds
```

**Step 2: Invalid Resume ID**
```
1. Open browser console
2. Manually trigger export with invalid resume_id
3. Verify backend returns 404 error
4. Verify frontend displays error message
5. Verify dialog shows error, not success
```

### Test Case 4: Mobile Responsive

**Step 1: Open Mobile DevTools**
```
1. Open Chrome DevTools (F12)
2. Click device toolbar icon (Ctrl+Shift+M)
3. Select device: iPhone SE or custom (375x667)
```

**Step 2: Test Export on Mobile**
```
1. Navigate to /settings/privacy
2. Verify page is responsive (no horizontal scroll)
3. Tap "Export My Data" card
4. Verify dialog fits on screen
5. Select JSON or CSV format
6. Tap "Export" button
7. Verify progress indicator
8. Verify file downloads
9. Verify success message
```

### Test Case 5: Data Verification

**Step 1: Create Test Candidate with Full Data**
```
1. Use backend API or admin panel to create candidate with:
   - Resume with personal info
   - Multiple hiring stages
   - Several notes
   - Multiple tags
   - Activity history
2. Note the resume_id for export testing
```

**Step 2: Export and Verify Completeness**
```
1. Export data as JSON
2. Count records in each section:
   - Resume: 1
   - Hiring stages: N (actual count)
   - Notes: N (actual count)
   - Tags: N (actual count)
   - Activities: N (actual count)
3. Compare with database counts
4. Verify all records are present
5. Verify no PII is missing
```

---

## Expected Behavior

### Right to Portability (GDPR Article 15)

The data export functionality MUST:

1. **Provide All Personal Data**
   - Export MUST include all PII stored about the candidate
   - Includes resume, parsed resume, hiring stages, notes, tags, activities
   - Includes consent records and audit trail

2. **Machine-Readable Format**
   - JSON: Hierarchical, structured format preserving relationships
   - CSV: Flattened tabular format with record_type discriminator
   - Both formats MUST be parseable by standard libraries/tools

3. **Complete and Accurate**
   - No data truncation
   - No data loss during export
   - Accurate timestamps and metadata
   - All fields properly escaped and formatted

4. **User-Friendly**
   - Clear format selection with descriptions
   - Progress indication during export
   - Automatic file download
   - Success confirmation with data summary
   - Error handling with retry option

### Data Exported

#### JSON Format Structure
```json
{
  "export_timestamp": "2026-02-03T12:00:00Z",
  "resume_id": "uuid",
  "filename": "resume.pdf",
  "format": "json",
  "total_records": 10,
  "includes_analytics": true,
  "resume": {
    "id": "uuid",
    "filename": "resume.pdf",
    "content_type": "application/pdf",
    "status": "active",
    "raw_text": "...",
    "language": "en",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-15T00:00:00Z"
  },
  "parsed_resume": {
    "email": "candidate@example.com",
    "phone": "+1234567890",
    "name": "John Doe",
    "location": "New York, USA",
    "links": ["https://linkedin.com/in/johndoe"],
    "skills": ["Python", "React", "SQL"],
    "work_experience": [...],
    "education": [...],
    "languages": [{"language": "English", "level": "Native"}]
  },
  "hiring_stages": [
    {
      "id": "uuid",
      "vacancy_id": "uuid",
      "stage_name": "Applied",
      "notes": "Initial application",
      "created_at": "2026-01-01T00:00:00Z"
    }
  ],
  "notes": [
    {
      "id": "uuid",
      "content": "Strong candidate",
      "created_by": "recruiter@example.com",
      "created_at": "2026-01-02T00:00:00Z"
    }
  ],
  "tags": [
    {
      "id": "uuid",
      "tag_name": "Senior Developer",
      "color": "#FF0000",
      "created_at": "2026-01-01T00:00:00Z"
    }
  ],
  "activities": [
    {
      "id": "uuid",
      "activity_type": "viewed",
      "activity_data": {...},
      "created_at": "2026-01-03T00:00:00Z"
    }
  ]
}
```

#### CSV Format Structure
```csv
record_type,id,filename,email,phone,stage_name,note_content,tag_name,created_at
resume,uuid,resume.pdf,candidate@example.com,+1234567890,,,,2026-01-01T00:00:00Z
hiring_stage,uuid,,,Applied,Initial application,,2026-01-01T00:00:00Z
note,uuid,,,,Strong candidate,,2026-01-02T00:00:00Z
tag,uuid,,,,,Senior Developer,2026-01-01T00:00:00Z
```

---

## Success Criteria

A test is considered **PASSING** when:

1. ✅ Export dialog opens and displays correctly
2. ✅ Format selection works (JSON/CSV)
3. ✅ Export button triggers API call
4. ✅ Progress indicator displays during export
5. ✅ File downloads automatically with correct filename
6. ✅ Downloaded file has valid structure (JSON or CSV)
7. ✅ File contains all candidate PII data
8. ✅ File is machine-readable and parseable
9. ✅ Success message displays after export
10. ✅ No console errors or warnings

---

## Troubleshooting

### Common Issues

**Issue 1: Download not triggered**
- Check browser popup blocker settings
- Verify backend returns correct Content-Type header
- Verify backend returns Content-Disposition header
- Check browser console for errors

**Issue 2: Empty or corrupted file**
- Verify backend export service is working
- Check backend logs for errors
- Verify resume_id exists in database
- Check if candidate has any data to export

**Issue 3: JSON parsing error**
- Verify JSON is valid using JSON validator
- Check for special characters not properly escaped
- Verify UTF-8 encoding
- Check backend JSON serialization

**Issue 4: CSV import error**
- Verify CSV delimiter is comma (,)
- Check for unescaped commas in field values
- Verify line endings (CRLF vs LF)
- Check for special characters (quotes, newlines)

**Issue 5: Tests timeout**
- Increase timeout in test (default 15s for download)
- Verify backend is responsive
- Check network latency
- Verify database queries are optimized

---

## GDPR Compliance Checklist

The data export functionality complies with:

- ✅ **GDPR Article 15 - Right of Access**: Candidates can access all personal data
- ✅ **GDPR Article 20 - Right to Data Portability**: Data provided in structured, machine-readable format
- ✅ **Complete Data Export**: All PII from all related tables included
- ✅ **Common Format**: JSON and CSV are widely supported formats
- ✅ **Machine-Readable**: Both formats can be processed by automated systems
- ✅ **User-Friendly**: Clear interface with progress indication
- ✅ **No Data Loss**: All records exported accurately
- ✅ **Metadata Included**: Export timestamp, record counts, format info
- ✅ **Audit Trail**: Export operation logged for accountability

---

## Related Files

- **Component**: `frontend/src/components/DataExportDialog.tsx`
- **API Client**: `frontend/src/api/gdpr.ts`
- **Backend Service**: `backend/services/export_service.py`
- **Backend API**: `backend/api/data_export.py`
- **Privacy Settings**: `frontend/src/pages/jobs/PrivacySettingsPage.tsx`

---

## Test Execution

### Run All Tests
```bash
cd frontend
npm run test:e2e gdpr-data-export-flow
```

### Run Specific Test Suite
```bash
cd frontend
npx playwright test gdpr-data-export-flow.spec.ts --project=chromium
```

### Run with UI Mode
```bash
cd frontend
npx playwright test gdpr-data-export-flow.spec.ts --ui
```

### Run with Debug Mode
```bash
cd frontend
npx playwright test gdpr-data-export-flow.spec.ts --debug
```

---

## Notes

- Test resume ID can be set via environment variable: `TEST_RESUME_ID`
- Tests create downloads in default browser Downloads folder
- Clean up downloaded files after testing
- Some tests may be skipped if database access is not available
- Mobile tests use specific viewport (375x667 for iPhone SE)

---

**Last Updated:** 2026-02-03
**Test Version:** 1.0
**Coverage:** Frontend UI, API Integration, File Download, Content Verification, Mobile Responsive
