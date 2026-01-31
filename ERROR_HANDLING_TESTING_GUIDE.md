# Error Handling Testing Guide

## Overview

This guide provides comprehensive instructions for testing user-friendly error handling throughout the application. The goal is to ensure that all errors provide actionable guidance and no browser `alert()` dialogs are used.

## Testing Environment Setup

### Required Tools
- **Browser:** Chrome, Firefox, Safari, or Edge
- **DevTools:** Open with F12 or right-click → Inspect
- **Network Tab:** For simulating network failures
- **Console Tab:** For detecting errors and verifying no alerts

### Browser DevTools Setup

#### Network Throttling
1. Open DevTools (F12)
2. Go to **Network** tab
3. Click **Online** dropdown
4. Select **Offline** to simulate network disconnection

#### Console Monitoring
1. Open DevTools (F12)
2. Go to **Console** tab
3. Filter for "Errors" if needed
4. Keep this open during testing to catch any console errors

---

## Test Categories

### Part 1: File Upload Errors (Upload Page)

#### Test 1.1: Invalid File Type Error
**Steps:**
1. Navigate to `/upload`
2. Click the upload area or "Choose File" button
3. Select a file with invalid type (e.g., `.txt`, `.jpg`, `.exe`)
4. **Expected Result:**
   - ✅ ErrorMessage component appears (not browser alert)
   - ✅ Error message title: "Invalid File Type" or similar
   - ✅ Error explains: "The file you uploaded is not supported"
   - ✅ Error provides solution: Lists allowed types (PDF, DOCX)
   - ✅ Action button: "Choose Another File" or "Close"
   - ✅ No `alert()` dialog appears
   - ✅ Error auto-hides after 6 seconds

**Pass:** □ | **Fail:** □

---

#### Test 1.2: File Size Limit Error
**Steps:**
1. Navigate to `/upload`
2. Create or find a file larger than 10MB
3. Upload the large file
4. **Expected Result:**
   - ✅ ErrorMessage appears (not browser alert)
   - ✅ Error message title: "File Too Large" or similar
   - ✅ Error explains: "The file you uploaded exceeds the size limit"
   - ✅ Error provides solution: "Compress your file or choose a smaller file (max 10MB)"
   - ✅ Action button: "Choose Another File"
   - ✅ No `alert()` dialog appears
   - ✅ Error auto-hides after 6 seconds

**Pass:** □ | **Fail:** □

---

#### Test 1.3: Network Upload Error
**Steps:**
1. Open DevTools → Network tab
2. Set throttling to "Offline"
3. Navigate to `/upload`
4. Try to upload a valid PDF file
5. **Expected Result:**
   - ✅ ErrorMessage appears (not browser alert)
   - ✅ Error message title: "Connection Error" or "Network Error"
   - ✅ Error explains: "Unable to connect to the server"
   - ✅ Error provides solution: "Check your internet connection, verify server is running, try refreshing the page"
   - ✅ Action button: "Retry" (reloads page)
   - ✅ No `alert()` dialog appears
   - ✅ Error does NOT auto-hide (stays visible until dismissed)

**Pass:** □ | **Fail:** □

---

#### Test 1.4: Upload Failure (Server Error)
**Steps:**
1. Navigate to `/upload`
2. Upload a file that will fail server-side validation
3. **Expected Result:**
   - ✅ ErrorMessage appears (not browser alert)
   - ✅ Error message explains what failed
   - ✅ Error provides actionable next steps
   - ✅ Retry or fix action available
   - ✅ No `alert()` dialog appears

**Pass:** □ | **Fail:** □

---

### Part 2: Validation Errors (Candidate Search)

#### Test 2.1: Search Without Vacancy Selection
**Steps:**
1. Navigate to `/recruiter/search`
2. Do NOT select a vacancy from dropdown
3. Click "Search" button
4. **Expected Result:**
   - ✅ ErrorMessage appears (not browser alert)
   - ✅ Severity: "warning" (yellow/amber color)
   - ✅ Message: "Please select a vacancy first"
   - ✅ Error appears at bottom-right or bottom-center
   - ✅ No `alert()` dialog appears
   - ✅ Error auto-hides after 6 seconds

**Pass:** □ | **Fail:** □

---

#### Test 2.2: Form Validation Errors (Vacancy Creation)
**Steps:**
1. Navigate to `/recruiter/vacancies/create`
2. Leave required fields empty
3. Click "Create" or "Save" button
4. **Expected Result:**
   - ✅ Inline validation errors appear below each invalid field
   - ✅ Error text in red color
   - ✅ Error messages are specific (e.g., "This field is required")
   - ✅ No `alert()` dialog appears
   - ✅ User can fix errors and retry

**Pass:** □ | **Fail:** □

---

### Part 3: Network Errors

#### Test 3.1: Backend Unreachable (All Pages)
**Steps:**
1. Stop the backend server or block network requests
2. Navigate to any page that loads data (e.g., `/recruiter/vacancies`)
3. **Expected Result:**
   - ✅ ErrorMessage appears (if page shows errors)
   - ✅ Error title: "Connection Error" or "Network Error"
   - ✅ Error explains: "Unable to connect to the server"
   - ✅ Error provides solution steps
   - ✅ Action button: "Retry" (reloads page)
   - ✅ No `alert()` dialog appears
   - ✅ Page remains functional (doesn't crash)

**Pass:** □ | **Fail:** □

---

#### Test 3.2: API Error Responses
**Steps:**
1. Use browser DevTools to simulate API errors
2. Trigger an action that calls the API
3. **Expected Result:**
   - ✅ ErrorMessage appears with appropriate severity
   - ✅ For 401 errors: Suggests logging in
   - ✅ For 403 errors: Explains permission denied
   - ✅ For 404 errors: Suggests checking the URL
   - ✅ For 500 errors: Suggests retrying later
   - ✅ All errors provide actionable guidance

**Pass:** □ | **Fail:** □

---

### Part 4: Error Message Structure

#### Test 4.1: Error Message Includes "What Went Wrong"
**Steps:**
1. Trigger any error (e.g., upload invalid file)
2. Read the error message
3. **Expected Result:**
   - ✅ Error has a clear title (e.g., "Invalid File Type")
   - ✅ Error describes what happened in plain language
   - ✅ Title is bold or visually distinct
   - ✅ Description provides context

**Pass:** □ | **Fail:** □

---

#### Test 4.2: Error Message Includes "Why It Happened"
**Steps:**
1. Trigger any error
2. Look for "Why:" or reason section
3. **Expected Result:**
   - ✅ Error explains the root cause
   - ✅ For file type error: "This file type is not accepted"
   - ✅ For network error: "A network error occurred while communicating"
   - ✅ For size error: "The system has a maximum file size limit"

**Pass:** □ | **Fail:** □

---

#### Test 4.3: Error Message Includes "How to Fix It"
**Steps:**
1. Trigger any error
2. Look for solution or "How to fix:" section
3. **Expected Result:**
   - ✅ Error provides actionable steps
   - ✅ Steps are numbered or bulleted
   - ✅ Steps are clear and specific
   - ✅ Examples:
     - "Upload a PDF or DOCX file"
     - "Check your internet connection"
     - "Select a vacancy before searching"

**Pass:** □ | **Fail:** □

---

#### Test 4.4: Error Action Buttons
**Steps:**
1. Trigger a network or server error
2. Look for action buttons in error message
3. **Expected Result:**
   - ✅ Action buttons are present for appropriate errors
   - ✅ Common actions: "Retry", "Choose Another File", "Close", "Go Back"
   - ✅ Buttons are styled consistently (outlined variant)
   - ✅ Buttons are clickable and responsive
   - ✅ Actions perform expected behavior

**Pass:** □ | **Fail:** □

---

### Part 5: No Alert Dialogs

#### Test 5.1: Verify No Browser Alerts
**Steps:**
1. Open Console tab in DevTools
2. Add this code to monitor for alerts:
   ```javascript
   window.alert = function() {
     console.error('ALERT DETECTED!', ...arguments);
     throw new Error('Browser alert() was called');
   };
   ```
3. Trigger various errors (upload invalid file, search without vacancy, etc.)
4. **Expected Result:**
   - ✅ No alert dialogs appear
   - ✅ Console shows no "ALERT DETECTED!" messages
   - ✅ All errors use Material UI components (Snackbar/Alert)

**Pass:** □ | **Fail:** □

---

#### Test 5.2: Verify Material UI Components Used
**Steps:**
1. Trigger any error
2. Inspect the error element in DevTools
3. **Expected Result:**
   - ✅ Error uses `.MuiSnackbar-root` class
   - ✅ Error uses `.MuiAlert-root` class
   - ✅ Error uses `.MuiAlert-filledError` or similar severity class
   - ✅ No native browser alert dialog in DOM

**Pass:** □ | **Fail:** □

---

### Part 6: Error Recovery

#### Test 6.1: Close Error Message
**Steps:**
1. Trigger any error
2. Click the "X" close button or action button
3. **Expected Result:**
   - ✅ Error message closes smoothly
   - ✅ No console errors when closing
   - ✅ Page remains functional after closing
   - ✅ User can trigger the error again

**Pass:** □ | **Fail:** □

---

#### Test 6.2: Auto-Hide Behavior
**Steps:**
1. Trigger a simple validation error (e.g., file type error)
2. Start a timer
3. **Expected Result:**
   - ✅ Error auto-hides after ~6 seconds
   - ✅ Error message fades out smoothly
   - ✅ No abrupt disappearance

**Pass:** □ | **Fail:** □

---

#### Test 6.3: Persistent Errors with Actions
**Steps:**
1. Trigger a network error (has action buttons)
2. Wait 10+ seconds
3. **Expected Result:**
   - ✅ Error remains visible (doesn't auto-hide)
   - ✅ User can click action buttons anytime
   - ✅ Error only closes when user dismisses it

**Pass:** □ | **Fail:** □

---

### Part 7: Accessibility

#### Test 7.1: Keyboard Navigation
**Steps:**
1. Trigger any error
2. Press Tab key to navigate
3. **Expected Result:**
   - ✅ Error message is keyboard accessible
   - ✅ Close button receives focus
   - ✅ Action buttons receive focus
   - ✅ Enter/Space activates focused button
   - ✅ Esc closes error message

**Pass:** □ | **Fail:** □

---

#### Test 7.2: ARIA Attributes
**Steps:**
1. Trigger any error
2. Inspect error element in DevTools
3. **Expected Result:**
   - ✅ Error has `role="alert"` attribute
   - ✅ Error has appropriate `aria-label` or `aria-describedby`
   - ✅ Buttons have proper aria labels

**Pass:** □ | **Fail:** □

---

#### Test 7.3: Screen Reader Compatibility
**Steps:**
1. Enable screen reader (NVDA, JAWS, or VoiceOver)
2. Trigger an error
3. **Expected Result:**
   - ✅ Screen reader announces error message
   - ✅ Error title is read first
   - ✅ Error description is read
   - ✅ Action buttons are announced
   - ✅ All text is readable

**Pass:** □ | **Fail:** □

---

### Part 8: Dark Mode Compatibility

#### Test 8.1: Error Messages in Dark Mode
**Steps:**
1. Toggle dark mode on (click theme switcher in navigation)
2. Trigger various errors
3. **Expected Result:**
   - ✅ Error messages are visible in dark mode
   - ✅ Text contrast is sufficient (WCAG AA)
   - ✅ Action buttons are visible
   - ✅ Close icon is visible
   - ✅ No color clashes with dark background
   - ✅ Error severity colors (red, yellow) are visible

**Pass:** □ | **Fail:** □

---

### Part 9: Mobile Responsiveness

#### Test 9.1: Error Messages on Mobile
**Steps:**
1. Open DevTools → Device Toolbar (Ctrl+Shift+M / Cmd+Shift+M)
2. Select mobile device (e.g., iPhone 12 - 390x844)
3. Navigate to `/upload`
4. Trigger file type error
5. **Expected Result:**
   - ✅ Error message is visible on mobile
   - ✅ Error message fits within screen width (no horizontal scroll)
   - ✅ Text is readable at mobile size
   - ✅ Action buttons are tappable (at least 44x44px)
   - ✅ Close button is tappable
   - ✅ Error appears at appropriate position (bottom)

**Pass:** □ | **Fail:** □

---

#### Test 9.2: Touch Interactions on Mobile
**Steps:**
1. Use mobile viewport (390x844)
2. Trigger an error
3. Tap various parts of error message
4. **Expected Result:**
   - ✅ Close button responds to touch
   - ✅ Action buttons respond to touch
   - ✅ No accidental clicks
   - ✅ Touch targets are large enough

**Pass:** □ | **Fail:** □

---

### Part 10: Edge Cases

#### Test 10.1: Multiple Errors in Sequence
**Steps:**
1. Trigger one error
2. Before it disappears, trigger another error
3. **Expected Result:**
   - ✅ New error replaces old error
   - ✅ No visual glitches
   - ✅ No error overlap
   - ✅ Both errors display correctly (sequentially)

**Pass:** □ | **Fail:** □

---

#### Test 10.2: Rapid Error Triggering
**Steps:**
1. Rapidly trigger the same error multiple times
2. **Expected Result:**
   - ✅ No duplicate error messages
   - ✅ No memory leaks
   - ✅ Errors update smoothly
   - ✅ No console errors

**Pass:** □ | **Fail:** □

---

#### Test 10.3: Errors During Page Navigation
**Steps:**
1. Trigger an error
2. Immediately navigate to another page
3. **Expected Result:**
   - ✅ Error closes or transitions smoothly
   - ✅ No error persists on new page
   - ✅ No console errors
   - ✅ Navigation completes successfully

**Pass:** □ | **Fail:** □

---

## Test Results Summary

### Overall Results
- **Total Tests:** 30
- **Passed:** _____
- **Failed:** _____
- **Skipped:** _____

### Breakdown by Category
- Part 1 (File Upload Errors): ____ / 4 passed
- Part 2 (Validation Errors): ____ / 2 passed
- Part 3 (Network Errors): ____ / 2 passed
- Part 4 (Error Structure): ____ / 4 passed
- Part 5 (No Alerts): ____ / 2 passed
- Part 6 (Error Recovery): ____ / 3 passed
- Part 7 (Accessibility): ____ / 3 passed
- Part 8 (Dark Mode): ____ / 1 passed
- Part 9 (Mobile): ____ / 2 passed
- Part 10 (Edge Cases): ____ / 3 passed

---

## Common Issues to Check

### Issue 1: Browser Alerts Still Appear
**Symptom:** `alert()` dialog appears instead of ErrorMessage
**Check:**
- Search codebase for `alert(` calls
- Replace with `ErrorMessage` component
- Use `setErrorMessage()` state updates

### Issue 2: Error Messages Not User-Friendly
**Symptom:** Technical jargon or unclear error text
**Check:**
- Use plain language
- Explain what, why, and how to fix
- Provide actionable next steps
- Add action buttons when appropriate

### Issue 3: Errors Not Visible in Dark Mode
**Symptom:** Poor contrast in dark theme
**Check:**
- Verify Material UI theme colors
- Test in both light and dark modes
- Ensure WCAG AA contrast ratios

### Issue 4: Auto-Hide Too Fast/Slow
**Symptom:** Errors disappear too quickly or stay too long
**Check:**
- Simple errors: 6 seconds auto-hide
- Errors with actions: No auto-hide (persistent)
- Adjust `autoHideDuration` in ErrorMessage component

---

## Quick Checklist

Before marking testing complete, verify:

- [ ] No `alert()` dialogs appear anywhere in the app
- [ ] All errors use Material UI Snackbar/Alert components
- [ ] Error messages include: what went wrong, why, how to fix
- [ ] Action buttons provided for appropriate errors
- [ ] Errors auto-hide (simple) or persist (with actions)
- [ ] Errors are keyboard accessible
- [ ] Errors are screen reader compatible
- [ ] Errors work in dark mode
- [ ] Errors work on mobile (touch-friendly)
- [ ] Errors provide clear guidance for users

---

## Notes and Observations

Use this section to document any issues found, edge cases discovered, or improvements needed during testing.

**Date:** _____
**Tester:** _____
**Build Version:** _____

### Issues Found:
1.
2.
3.

### Suggestions for Improvement:
1.
2.
3.

### Overall Assessment:
- [ ] Pass - All error handling is user-friendly and actionable
- [ ] Pass with Minor Issues - Mostly good, small improvements needed
- [ ] Fail - Significant issues with error handling
