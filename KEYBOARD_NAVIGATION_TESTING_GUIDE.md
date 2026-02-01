# Keyboard Navigation Testing Guide

## Overview

This guide provides comprehensive testing instructions for verifying keyboard navigation functionality across the application. Keyboard navigation is a critical accessibility feature that enables users to navigate efficiently without using a mouse.

**Estimated Testing Time:** 30-45 minutes

**Test Coverage:**
- Global keyboard shortcuts (Ctrl+K, Ctrl+/, Alt+Home)
- CandidateSearch page list navigation
- WorkflowBoard (Kanban) navigation
- Modal interactions
- Platform-specific differences (Mac vs Windows/Linux)
- Edge cases and accessibility

---

## Test Environment Setup

### Viewports and Devices
Test keyboard navigation on these viewports:
- **Desktop:** 1920x1080 (primary focus)
- **Tablet:** 768x1024
- **Mobile:** 375x667 (limited keyboard support)

### Browsers
- Chrome/Edge (primary)
- Firefox
- Safari (Mac only)

### System Preferences
- Disable any custom keyboard shortcuts in your OS
- Ensure browser doesn't override the shortcuts we're testing
- Test on both Mac and Windows/Linux if possible

---

## Part 1: Global Shortcuts (All Pages)

### Test 1.1: Ctrl+K / Cmd+K - Navigate to Candidate Search

**Steps:**
1. Navigate to any page (e.g., Home page)
2. Press `Ctrl+K` (Windows/Linux) or `Cmd+K` (Mac)
3. Wait for navigation to complete

**Expected Results:**
- ✅ Browser navigates to `/recruiter/search`
- ✅ Page loads without errors
- ✅ URL changes to candidate search page
- ✅ No console errors

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 1.2: Ctrl+/ / Cmd+/ - Show Keyboard Shortcuts Help

**Steps:**
1. Navigate to any page
2. Press `Ctrl+/` (Windows/Linux) or `Cmd+/` (Mac)
3. Wait for dialog to appear

**Expected Results:**
- ✅ Keyboard shortcuts dialog opens
- ✅ Dialog shows keyboard icon and title
- ✅ Dialog displays table with 4 shortcuts:
  - `Ctrl+K` - Navigate to candidate search
  - `Ctrl+/` - Show keyboard shortcuts
  - `Alt+Home` - Navigate to home page
  - `Esc` - Close dialog
- ✅ Each shortcut has appropriate icon
- ✅ Shortcuts use correct modifier key for platform (Cmd on Mac, Ctrl on Windows/Linux)

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 1.3: Alt+Home - Navigate to Home Page

**Steps:**
1. Navigate to any page (e.g., `/recruiter/search`)
2. Press `Alt+Home`
3. Wait for navigation to complete

**Expected Results:**
- ✅ Browser navigates to `/` (home page)
- ✅ Page loads without errors
- ✅ URL changes to home page

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 1.4: Escape - Close Keyboard Shortcuts Dialog

**Steps:**
1. Open keyboard shortcuts dialog (`Ctrl+/` or `Cmd+/`)
2. Verify dialog is visible
3. Press `Escape` key
4. Wait for dialog to close

**Expected Results:**
- ✅ Dialog closes immediately
- ✅ Focus returns to page content
- ✅ No visual glitches

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

## Part 2: CandidateSearch Page Navigation

**Navigate to:** `http://localhost:5173/recruiter/search`

### Prerequisites
- At least one vacancy exists
- At least one candidate exists (with search results)

### Test 2.1: Keyboard Navigation Hint Display

**Steps:**
1. Navigate to CandidateSearch page
2. Wait for page to load
3. Look for keyboard navigation hint

**Expected Results:**
- ✅ Hint text displayed near candidate list
- ✅ Shows arrow icons and text: "Use arrow keys to navigate, Enter to view details"
- ✅ Hint visible only when candidates are displayed
- ✅ Hint localized correctly (English/Russian)

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 2.2: ArrowDown - Navigate Down Through Candidates

**Steps:**
1. Ensure candidate search has results
2. Click outside any input field to ensure no input is focused
3. Press `ArrowDown` key
4. Observe visual feedback on candidate cards

**Expected Results:**
- ✅ First candidate card gets visual focus indicator (border + shadow)
- ✅ Focused card has elevated appearance (boxShadow: 8)
- ✅ Border shows primary color (3px)
- ✅ Page auto-scrolls if needed to keep focused card visible
- ✅ Each subsequent ArrowDown focuses next candidate
- ✅ Stops at last candidate (doesn't wrap around)

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 2.3: ArrowUp - Navigate Up Through Candidates

**Steps:**
1. Press ArrowDown 2-3 times to focus a candidate
2. Press `ArrowUp` key
3. Observe focus moves up

**Expected Results:**
- ✅ Focus moves to previous candidate
- ✅ Visual feedback updates to new focused card
- ✅ Previous card loses focus indicator
- ✅ Stops at first candidate (doesn't wrap to bottom)
- ✅ Auto-scrolls if needed

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 2.4: J and K Keys - Vim-style Navigation

**Steps:**
1. Press `j` key (lowercase)
2. Observe focus moves down
3. Press `k` key (lowercase)
4. Observe focus moves up

**Expected Results:**
- ✅ `j` key behaves same as ArrowDown
- ✅ `k` key behaves same as ArrowUp
- ✅ Same visual feedback as arrow keys
- ✅ Works consistently throughout list

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 2.5: Enter - View Candidate Details

**Steps:**
1. Use ArrowDown to focus a candidate
2. Verify candidate has focus indicator
3. Press `Enter` key
4. Wait for navigation

**Expected Results:**
- ✅ Browser navigates to candidate details page (`/results/{candidate_id}`)
- ✅ Page loads without errors
- ✅ Correct candidate details displayed
- ✅ Focus is cleared from candidate list

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 2.6: Escape - Clear Focus

**Steps:**
1. Use ArrowDown to focus a candidate
2. Verify candidate has focus indicator
3. Press `Escape` key
4. Observe candidate cards

**Expected Results:**
- ✅ Focus indicator disappears from all cards
- ✅ All cards return to normal appearance
- ✅ No candidate is focused
- ✅ Ready for new keyboard navigation

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 2.7: Home - Jump to First Candidate

**Steps:**
1. Use ArrowDown to navigate to 3rd or 4th candidate
2. Press `Home` key
3. Observe which card is focused

**Expected Results:**
- ✅ Focus jumps to first candidate in list
- ✅ Visual feedback updates immediately
- ✅ Page scrolls to top if needed
- ✅ First candidate displays focus indicator

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 2.8: End - Jump to Last Candidate

**Steps:**
1. Focus any candidate (or none)
2. Press `End` key
3. Observe which card is focused

**Expected Results:**
- ✅ Focus jumps to last candidate in list
- ✅ Visual feedback updates immediately
- ✅ Page scrolls to bottom if needed
- ✅ Last candidate displays focus indicator

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 2.9: Input Field Exclusion

**Steps:**
1. Click in search input field or any text input
2. Verify input has focus (cursor visible)
3. Press ArrowDown, ArrowUp, or other navigation keys
4. Observe behavior

**Expected Results:**
- ✅ Arrow keys move cursor within input field
- ✅ No candidate card gets focus
- ✅ Keyboard navigation is ignored while typing
- ✅ Only keyboard shortcuts work when input is focused

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 2.10: Mouse Hover Sync

**Steps:**
1. Use keyboard (ArrowDown) to focus a candidate
2. Move mouse over a different candidate
3. Observe focus indicator

**Expected Results:**
- ✅ Mouse hover updates focused candidate
- ✅ Focus indicator moves to hovered card
- ✅ Smooth transition between keyboard and mouse
- ✅ Both interaction methods work together

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

## Part 3: WorkflowBoard (Kanban) Navigation

**Navigate to:** `http://localhost:5173/recruiter/workflow`

### Prerequisites
- At least one workflow stage exists
- At least one candidate in workflow

### Test 3.1: ArrowLeft/ArrowRight - Navigate Between Stages

**Steps:**
1. Navigate to WorkflowBoard page
2. Click outside search input
3. Press `ArrowRight` key
4. Press `ArrowLeft` key
5. Observe stage columns

**Expected Results:**
- ✅ ArrowRight moves focus to next stage column
- ✅ ArrowLeft moves focus to previous stage column
- ✅ Visual indicator shows which stage is focused
- ✅ Stops at first/last stage (no wrap-around)
- ✅ Page scrolls horizontally if needed

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 3.2: ArrowUp/ArrowDown - Navigate Within Stage

**Steps:**
1. Focus a stage (use ArrowLeft/Right if needed)
2. Press `ArrowDown` key
3. Press `ArrowUp` key
4. Observe candidate cards within stage

**Expected Results:**
- ✅ ArrowDown moves to next candidate card in stage
- ✅ ArrowUp moves to previous candidate card in stage
- ✅ Visual indicator shows focused card (border + shadow)
- ✅ Auto-scrolls if needed to keep card visible
- ✅ Handles empty stages gracefully

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 3.3: Enter - Open Candidate Details Modal

**Steps:**
1. Navigate to focus a candidate card (ArrowDown or ArrowUp)
2. Verify card has focus indicator
3. Press `Enter` key
4. Wait for modal to open

**Expected Results:**
- ✅ Candidate details modal opens
- ✅ Modal shows candidate information
- ✅ Modal is fullscreen on mobile, centered on desktop
- ✅ Focus enters modal appropriately

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 3.4: M Key - Move to Next Stage

**Steps:**
1. Focus a candidate card
2. Verify candidate is not in last stage
3. Press `m` key (lowercase)
4. Wait for API call to complete
5. Observe candidate location

**Expected Results:**
- ✅ Candidate moves to next workflow stage
- ✅ UI updates immediately (optimistic update)
- ✅ Success message shows if API call succeeds
- ✅ Error message shows if API call fails
- ✅ Candidate rolls back if error occurs
- ✅ Focus remains manageable

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 3.5: Shift+M - Move to Previous Stage

**Steps:**
1. Focus a candidate card
2. Verify candidate is not in first stage
3. Press `Shift+M` keys
4. Wait for API call to complete
5. Observe candidate location

**Expected Results:**
- ✅ Candidate moves to previous workflow stage
- ✅ UI updates immediately (optimistic update)
- ✅ Success message shows if API call succeeds
- ✅ Error message shows if API call fails
- ✅ Candidate rolls back if error occurs

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 3.6: Escape - Clear Focus

**Steps:**
1. Focus a candidate card (ArrowDown)
2. Verify focus indicator is visible
3. Press `Escape` key
4. Observe candidate cards

**Expected Results:**
- ✅ Focus indicator disappears from all cards
- ✅ All cards return to normal appearance
- ✅ No stage is focused
- ✅ Ready for new navigation

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 3.7: Search Input Exclusion

**Steps:**
1. Click in workflow board search input
2. Verify input has focus
3. Press Arrow keys
4. Observe behavior

**Expected Results:**
- ✅ Arrow keys move cursor within search input
- ✅ No candidate card gets focus
- ✅ Keyboard navigation ignored while typing
- ✅ Works normally after clicking outside input

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

## Part 4: Modal Interactions

### Test 4.1: Escape Closes Keyboard Shortcuts Dialog

**Steps:**
1. Open keyboard shortcuts dialog (`Ctrl+/` or `Cmd+/`)
2. Verify dialog is visible
3. Press `Escape` key
4. Observe dialog

**Expected Results:**
- ✅ Dialog closes immediately
- ✅ No visual glitches during close
- ✅ Focus returns to page
- ✅ Can reopen dialog with same shortcut

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 4.2: Escape Closes Candidate Details Modal

**Steps:**
1. Navigate to CandidateSearch page
2. Use keyboard to focus a candidate and press Enter (or click to open details)
3. Wait for modal to open
4. Press `Escape` key
5. Observe modal

**Expected Results:**
- ✅ Modal closes immediately
- ✅ No visual glitches
- ✅ Returns to previous page
- ✅ Focus is in sensible location

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 4.3: Escape Closes Workflow Detail Modal

**Steps:**
1. Navigate to WorkflowBoard
2. Use keyboard to focus candidate and press Enter
3. Wait for detail modal to open
4. Press `Escape` key
5. Observe modal

**Expected Results:**
- ✅ Modal closes immediately
- ✅ Returns to kanban board
- ✅ Focus state is appropriate

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 4.4: Page Shortcuts Don't Work When Modal Open

**Steps:**
1. Open keyboard shortcuts dialog
2. Try pressing `Ctrl+K` / `Cmd+K`
3. Observe behavior

**Expected Results:**
- ✅ Page does NOT navigate to candidate search
- ✅ Modal remains open
- ✅ Shortcut is "trapped" by modal
- ✅ Only Escape works to close modal

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

## Part 5: Platform-Specific Behavior

### Test 5.1: Mac - Cmd Key Instead of Ctrl

**Steps (Mac only):**
1. Navigate to any page on macOS
2. Open keyboard shortcuts dialog with `Cmd+/`
3. Check the shortcut text in dialog

**Expected Results:**
- ✅ Dialog shows "Cmd" instead of "Ctrl"
- ✅ `Cmd+K` works for navigation
- ✅ `Cmd+/` works for opening dialog
- ✅ All shortcuts use Command key on Mac

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 5.2: Windows/Linux - Ctrl Key

**Steps (Windows/Linux only):**
1. Navigate to any page
2. Open keyboard shortcuts dialog with `Ctrl+/`
3. Check the shortcut text in dialog

**Expected Results:**
- ✅ Dialog shows "Ctrl"
- ✅ `Ctrl+K` works for navigation
- ✅ `Ctrl+/` works for opening dialog
- ✅ All shortcuts use Control key

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

## Part 6: Accessibility

### Test 6.1: Visual Focus Indicators

**Steps:**
1. Navigate to CandidateSearch page
2. Use keyboard to focus a candidate (ArrowDown)
3. Observe the focused card

**Expected Results:**
- ✅ Focused card has clear visual indicator
- ✅ Border is 3px with primary color
- ✅ Elevated shadow (boxShadow: 8 or 4)
- ✅ High contrast from non-focused cards
- ✅ Visible in both light and dark modes

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 6.2: Tab Key Navigation

**Steps:**
1. Navigate to any page
2. Press `Tab` key multiple times
3. Observe focus order

**Expected Results:**
- ✅ Focus moves through interactive elements in logical order
- ✅ Each focused element has visible indicator
- ✅ Focus order matches visual layout (left-to-right, top-to-bottom)
- ✅ All buttons, links, and inputs are reachable

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 6.3: Shift+Tab Reverse Navigation

**Steps:**
1. Use Tab to move focus through several elements
2. Press `Shift+Tab`
3. Observe focus direction

**Expected Results:**
- ✅ Focus moves in reverse order
- ✅ Previous element gets focus
- ✅ Works consistently across all pages

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 6.4: Dark Mode Keyboard Indicators

**Steps:**
1. Navigate to CandidateSearch page
2. Toggle dark mode on
3. Use keyboard navigation (ArrowDown)
4. Observe focus indicators

**Expected Results:**
- ✅ Focus indicator visible in dark mode
- ✅ Sufficient contrast (WCAG AA compliant)
- ✅ No visual glitches
- ✅ Clear difference between focused and unfocused

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

## Part 7: Edge Cases

### Test 7.1: Empty Lists

**Steps:**
1. Navigate to CandidateSearch with no results
2. Try keyboard navigation (ArrowDown, ArrowUp, j, k)

**Expected Results:**
- ✅ No crashes or errors
- ✅ Navigation gracefully ignored
- ✅ No visual glitches
- ✅ Keyboard hint not shown (no candidates)

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 7.2: Rapid Key Presses

**Steps:**
1. Navigate to CandidateSearch with results
2. Rapidly press ArrowDown 10+ times
3. Rapidly press ArrowUp 10+ times

**Expected Results:**
- ✅ No crashes or performance issues
- ✅ Focus keeps up with key presses
- ✅ Smooth scrolling
- ✅ No duplicate event handling

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 7.3: Keyboard After Page Navigation

**Steps:**
1. Navigate to home page
2. Use `Ctrl+K` / `Cmd+K` to go to CandidateSearch
3. Immediately press ArrowDown
4. Observe behavior

**Expected Results:**
- ✅ Keyboard navigation works immediately after navigation
- ✅ No waiting period needed
- ✅ Event listeners properly attached

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 7.4: Keyboard After Language Switch

**Steps:**
1. Navigate to any page
2. Switch language (use language switcher)
3. Try keyboard shortcuts
4. Observe behavior

**Expected Results:**
- ✅ All shortcuts still work
- ✅ Keyboard hint updates to new language
- ✅ Shortcuts dialog shows translated text

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 7.5: Keyboard After Theme Switch

**Steps:**
1. Navigate to CandidateSearch page
2. Toggle dark mode on
3. Use keyboard navigation (ArrowDown, Enter)
4. Observe visual feedback

**Expected Results:**
- ✅ Focus indicators visible in new theme
- ✅ No visual glitches during transition
- ✅ Shortcuts continue to work

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

## Part 8: Cross-Page Consistency

### Test 8.1: Shortcuts Work on All Pages

**Steps:**
1. Test `Ctrl+K` / `Cmd+K` on:
   - Home page (`/`)
   - CandidateSearch (`/recruiter/search`)
   - VacancyList (`/recruiter/vacancies`)
   - ResumeDatabase (`/recruiter/resumes`)
   - WorkflowBoard (`/recruiter/workflow`)

**Expected Results:**
- ✅ Shortcut works on all pages
- ✅ Consistent behavior across pages
- ✅ No page-specific conflicts

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

### Test 8.2: Escape Behavior Consistency

**Steps:**
1. Open various modals/dialogs across pages
2. Press Escape to close
3. Verify behavior is consistent

**Expected Results:**
- ✅ Escape closes all modals consistently
- ✅ No page-specific Escape handling conflicts
- ✅ Predictable behavior for users

**Actual Results:**
- Pass/Fail: ___________
- Notes: ___________

---

## Common Issues to Check

### Visual Issues
- [ ] Focus indicators not visible in dark mode
- [ ] Focus indicators too subtle (low contrast)
- [ ] Visual glitches when switching focus
- [ ] Animations too slow or distracting

### Functional Issues
- [ ] Keyboard events not firing
- [ ] Shortcuts conflicting with browser/system shortcuts
- [ ] Navigation not working on certain pages
- [ ] Focus getting "stuck" in elements
- [ ] Modals not closing with Escape

### Accessibility Issues
- [ ] No visible focus indicator
- [ ] Focus order illogical
- [ ] Keyboard traps (can't exit with keyboard)
- [ ] No way to close modals without mouse

### Performance Issues
- [ ] Lag when using keyboard navigation
- [ ] Slow scrolling when moving focus
- [ ] Delayed visual feedback

---

## Test Results Summary

### Global Shortcuts
- [ ] Ctrl+K / Cmd+K: Navigate to search - Pass/Fail
- [ ] Ctrl+/ / Cmd+/: Show help - Pass/Fail
- [ ] Alt+Home: Go to home - Pass/Fail
- [ ] Escape: Close dialogs - Pass/Fail

### CandidateSearch Navigation
- [ ] ArrowDown/ArrowUp navigation - Pass/Fail
- [ ] J/K keys - Pass/Fail
- [ ] Enter to view details - Pass/Fail
- [ ] Escape to clear focus - Pass/Fail
- [ ] Home/End keys - Pass/Fail
- [ ] Input field exclusion - Pass/Fail

### WorkflowBoard Navigation
- [ ] ArrowLeft/Right stage navigation - Pass/Fail
- [ ] ArrowUp/Down card navigation - Pass/Fail
- [ ] Enter for details - Pass/Fail
- [ ] M key for move forward - Pass/Fail
- [ ] Shift+M for move backward - Pass/Fail
- [ ] Escape to clear focus - Pass/Fail

### Accessibility
- [ ] Visible focus indicators - Pass/Fail
- [ ] Proper focus order - Pass/Fail
- [ ] Dark mode compatibility - Pass/Fail
- [ ] No keyboard traps - Pass/Fail

### Overall Assessment
- **Total Tests:** _____
- **Passed:** _____
- **Failed:** _____
- **Blocked:** _____

**Notes:**
___________
___________
___________

---

## Automated Testing

In addition to this manual testing, run the automated E2E tests:

```bash
cd frontend
npm run test:e2e -- keyboard-navigation.spec.ts
```

The automated tests cover:
- Global shortcut functionality
- CandidateSearch keyboard navigation
- WorkflowBoard keyboard navigation
- Modal interactions
- Platform-specific behavior
- Edge cases

Automated tests complement manual testing by catching regressions quickly, while manual testing ensures visual feedback and user experience are optimal.
