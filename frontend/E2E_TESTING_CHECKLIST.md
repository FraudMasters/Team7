# E2E Testing Checklist
## User Flow Separation - Candidate and Recruiter Flows

This checklist provides comprehensive manual testing scenarios for validating the complete candidate and recruiter flows.

---

## Prerequisites

- [ ] Backend API running at `http://localhost:8000`
- [ ] Frontend dev server running at `http://localhost:5173`
- [ ] Test data available in database (sample jobs, candidates, vacancies)
- [ ] Browser DevTools open for console error checking
- [ ] Mobile device or responsive mode available

---

## Part 1: Candidate Flow (Job Seeker)

### 1.1 Landing Page to Candidate Flow

**Test 1.1.1: Role Selection**
- [ ] Navigate to `http://localhost:5173`
- [ ] Verify landing page loads with AgentHR branding
- [ ] Verify role selection options are visible (Candidate vs Recruiter)
- [ ] Click "Candidate" or "Job Seeker" option
- [ ] Verify navigation to `/jobs` or candidate flow entry point

**Test 1.1.2: Direct URL Access**
- [ ] Navigate directly to `http://localhost:5173/jobs`
- [ ] Verify page loads without errors
- [ ] Verify JobSeekerLayout is active (bottom navigation or appropriate layout)
- [ ] Check browser console for no errors

### 1.2 Candidate Navigation

**Test 1.2.1: Browse Jobs Page**
- [ ] Navigate to `/jobs`
- [ ] Verify page heading displays "Browse Jobs" or similar
- [ ] Verify search functionality is present
- [ ] Verify job cards display (if data available) or empty state shown
- [ ] Check responsive layout on desktop (grid layout)
- [ ] Check responsive layout on mobile (stacked cards)

**Test 1.2.2: Saved Jobs Page**
- [ ] Navigate to `/jobs/saved`
- [ ] Verify page heading displays "Saved Jobs"
- [ ] Verify search input is present
- [ ] Verify bookmark/save icon is visible
- [ ] Verify empty state message when no saved jobs
- [ ] Test search functionality by typing in search box
- [ ] Verify job cards display saved jobs (if data available)

**Test 1.2.3: My Applications Page**
- [ ] Navigate to `/jobs/applications`
- [ ] Verify page heading displays "My Applications"
- [ ] Verify search input is present
- [ ] Verify status filter dropdown is present
- [ ] Verify status summary section displays counts
- [ ] Test status filter (select "Pending", "Interview", etc.)
- [ ] Verify empty state message when no applications
- [ ] Check ApplicationCard components display correctly

**Test 1.2.4: Candidate Profile Page**
- [ ] Navigate to `/profile`
- [ ] Verify page heading displays "Profile" or "My Profile"
- [ ] Verify profile sections are visible (Contact, Skills, Experience, Education)
- [ ] Click "Edit" button
- [ ] Verify edit mode activates (input fields appear, Save/Cancel buttons visible)
- [ ] Edit a field (e.g., Bio)
- [ ] Click "Cancel" to exit edit mode
- [ ] Verify changes are reverted
- [ ] Click "Edit" again
- [ ] Edit a field and click "Save"
- [ ] Verify save button shows loading state if applicable
- [ ] Verify changes are saved (if backend connected)

### 1.3 Candidate Resume Flow

**Test 1.3.1: Resume Upload Page**
- [ ] Navigate to `/jobs/upload`
- [ ] Verify page heading displays "Upload Resume"
- [ ] Verify stepper shows 3 steps (Upload, Processing, Complete)
- [ ] Verify drag-and-drop area is visible
- [ ] Verify "Browse Files" button is present
- [ ] Verify file format info is displayed (PDF, DOCX)
- [ ] Verify info cards show (Accepted Formats, Processing Time, What's Next)
- [ ] Test file selection (choose a PDF file)
- [ ] Verify file name displays after selection

**Test 1.3.2: Resume Results Page**
- [ ] Navigate to `/jobs/resume-results/test-resume-123`
- [ ] Verify page loads (may show error without valid resume ID)
- [ ] Check for loading state initially
- [ ] Check for error state if resume not found
- [ ] Verify analysis results display (if valid ID)
- [ ] Check for skill extraction display
- [ ] Check for error detection display
- [ ] Check for job matching recommendations

### 1.4 Candidate Flow Complete Journey

**Test 1.4.1: Complete Application Flow**
- [ ] Start at `/jobs`
- [ ] Browse available jobs
- [ ] Click on a job to view details (`/jobs/:id`)
- [ ] Verify JobDetailPage displays job information
- [ ] Click "Apply Now" or similar button
- [ ] Verify navigation to application form (`/jobs/:id/apply`)
- [ ] Fill out application form fields
- [ ] Submit application
- [ ] Verify success message or navigation
- [ ] Navigate to `/jobs/applications`
- [ ] Verify submitted application appears in list

**Test 1.4.2: Browser Navigation**
- [ ] Navigate to `/jobs`
- [ ] Navigate to `/jobs/saved`
- [ ] Navigate to `/jobs/applications`
- [ ] Click browser back button
- [ ] Verify return to `/jobs/saved`
- [ ] Click browser back button again
- [ ] Verify return to `/jobs`
- [ ] Click browser forward button
- [ ] Verify navigation to `/jobs/saved`

**Test 1.4.3: Bookmark/Save Job Flow**
- [ ] Navigate to `/jobs`
- [ ] Find a job card
- [ ] Click bookmark/save icon
- [ ] Verify icon changes to filled/saved state
- [ ] Navigate to `/jobs/saved`
- [ ] Verify saved job appears in list
- [ ] Remove job from saved
- [ ] Verify job is removed from list

### 1.5 Candidate Mobile Responsiveness

**Test 1.5.1: Mobile Layout (375px)**
- [ ] Set browser viewport to 375x667 (iPhone SE)
- [ ] Navigate to `/jobs`
- [ ] Verify no horizontal scrolling
- [ ] Verify bottom navigation is visible
- [ ] Verify job cards stack vertically
- [ ] Test navigation to `/jobs/saved`
- [ ] Verify smooth page transition
- [ ] Test navigation to `/jobs/applications`
- [ ] Verify smooth page transition
- [ ] Test navigation to `/profile`
- [ ] Verify smooth page transition

**Test 1.5.2: Touch Interactions on Mobile**
- [ ] On mobile viewport, tap navigation items
- [ ] Verify responsive taps (no delay)
- [ ] Verify buttons are easily tappable (min 44x44px)
- [ ] Test swipe gestures if implemented
- [ ] Verify all interactive elements work

---

## Part 2: Recruiter Flow

### 2.1 Landing Page to Recruiter Flow

**Test 2.1.1: Role Selection**
- [ ] Navigate to `http://localhost:5173`
- [ ] Verify landing page loads with AgentHR branding
- [ ] Verify role selection options are visible
- [ ] Click "Recruiter" or "Employer" option
- [ ] Verify navigation to `/recruiter/dashboard` or recruiter entry point

**Test 2.1.2: Direct URL Access**
- [ ] Navigate directly to `http://localhost:5173/recruiter/dashboard`
- [ ] Verify page loads without errors
- [ ] Verify RecruiterLayout is active (sidebar navigation)
- [ ] Check browser console for no errors

### 2.2 Recruiter Navigation

**Test 2.2.1: Dashboard Page**
- [ ] Navigate to `/recruiter/dashboard`
- [ ] Verify page heading displays "Dashboard"
- [ ] Verify dashboard widgets/metrics display
- [ ] Verify summary statistics (vacancies, candidates, applications)
- [ ] Verify navigation menu items are highlighted correctly

**Test 2.2.2: Vacancies Page**
- [ ] Navigate to `/recruiter/vacancies`
- [ ] Verify page heading displays "Vacancies" or "Job Postings"
- [ ] Verify "Create Vacancy" or "Add Job" button is present
- [ ] Verify vacancy cards display (if data available)
- [ ] Verify grid layout on desktop
- [ ] Check filters and search functionality

**Test 2.2.3: Vacancy Detail Page**
- [ ] Navigate to `/recruiter/vacancies`
- [ ] Click on a vacancy card to view details
- [ ] Verify navigation to `/recruiter/vacancies/:id`
- [ ] Verify VacancyDetailPage displays:
  - [ ] Job title and description
  - [ ] Location, industry, work format
  - [ ] Salary range (if available)
  - [ ] Required skills as chips
  - [ ] Action buttons (View Candidates, Edit Vacancy)
- [ ] Click "View Candidates" button
- [ ] Verify navigation to `/recruiter/candidates`

**Test 2.2.4: Candidates Page**
- [ ] Navigate to `/recruiter/candidates`
- [ ] Verify page heading displays "Candidates"
- [ ] Verify kanban board layout (columns for stages)
- [ ] Verify stage columns: Applied, Shortlisted, Interview, Offered, Rejected
- [ ] Verify candidate cards display in columns
- [ ] Test drag-and-drop functionality (move card between columns)
- [ ] Verify card updates position

**Test 2.2.5: Candidate Detail Page**
- [ ] Navigate to `/recruiter/candidates`
- [ ] Click on a candidate card to view details
- [ ] Verify navigation to `/recruiter/candidates/:id`
- [ ] Verify CandidateDetailPage displays:
  - [ ] Candidate name and contact information
  - [ ] Skills section
  - [ ] Experience section
  - [ ] Education section
  - [ ] Match score or analysis results
- [ ] Verify tabs for different information views
- [ ] Test tab navigation

**Test 2.2.6: Analytics Page**
- [ ] Navigate to `/recruiter/analytics`
- [ ] Verify page heading displays "Analytics"
- [ ] Verify charts/graphs display
- [ ] Verify metrics and statistics
- [ ] Check data visualizations are responsive

**Test 2.2.7: Weights Page**
- [ ] Navigate to `/recruiter/weights`
- [ ] Verify page heading displays "Weights" or "Customize Matching"
- [ ] Verify weight sliders display (Keyword, TF-IDF, Vector)
- [ ] Verify progress bars show current weight distribution
- [ ] Verify total weight equals 100%
- [ ] Test slider adjustments:
  - [ ] Adjust Keyword slider
  - [ ] Verify progress bars update
  - [ ] Check validation warning if total != 100%
  - [ ] Click "Normalize" button
  - [ ] Verify weights adjust to sum to 100%
- [ ] Test tabs:
  - [ ] Click "Presets" tab
  - [ ] Verify preset cards display (Technical, Creative, Executive, Balanced)
  - [ ] Click a preset card
  - [ ] Verify weights update to preset configuration
  - [ ] Click "Custom" tab
  - [ ] Verify sliders are interactive
  - [ ] Click "Saved Profiles" tab
  - [ ] Verify saved profiles display (if any)
- [ ] Test save profile:
  - [ ] Adjust weights
  - [ ] Click "Save Profile" button
  - [ ] Verify dialog appears
  - [ ] Enter profile name and description
  - [ ] Click "Save"
  - [ ] Verify profile saved (check in Saved Profiles tab)

### 2.3 Recruiter Flow Complete Journey

**Test 2.3.1: Complete Vacancy Management Flow**
- [ ] Start at `/recruiter/dashboard`
- [ ] Navigate to `/recruiter/vacancies`
- [ ] Click "Create Vacancy" button
- [ ] Fill out vacancy form (title, description, skills, etc.)
- [ ] Submit form
- [ ] Verify navigation back to vacancies list
- [ ] Verify new vacancy appears in list
- [ ] Click on vacancy to view details
- [ ] Verify VacancyDetailPage displays correctly
- [ ] Click "Edit Vacancy"
- [ ] Make changes to form
- [ ] Save changes
- [ ] Verify updates are reflected

**Test 2.3.2: Complete Candidate Review Flow**
- [ ] Start at `/recruiter/dashboard`
- [ ] Navigate to `/recruiter/candidates`
- [ ] Verify kanban board displays
- [ ] Find candidate in "Applied" column
- [ ] Drag candidate card to "Shortlisted" column
- [ ] Verify card moves to new column
- [ ] Click on candidate card
- [ ] Verify CandidateDetailPage displays
- [ ] Review candidate information
- [ ] Navigate back to kanban board
- [ ] Drag candidate to "Interview" column
- [ ] Verify stage update

**Test 2.3.3: Complete Weight Customization Flow**
- [ ] Start at `/recruiter/dashboard`
- [ ] Navigate to `/recruiter/weights`
- [ ] Review current weight distribution
- [ ] Click "Presets" tab
- [ ] Select "Technical" preset
- [ ] Verify weights update (higher keyword weight)
- [ ] Navigate to Candidates page
- [ ] Search for candidates
- [ ] Verify match scores use new weights
- [ ] Return to Weights page
- [ ] Click "Custom" tab
- [ ] Adjust sliders to custom values
- [ ] Click "Normalize" if needed
- [ ] Click "Save Profile"
- [ ] Enter profile name "Custom Technical"
- [ ] Save profile
- [ ] Navigate to "Saved Profiles" tab
- [ ] Verify saved profile appears
- [ ] Load saved profile
- [ ] Verify weights apply correctly

### 2.4 Recruiter Mobile Responsiveness

**Test 2.4.1: Mobile Layout (375px)**
- [ ] Set browser viewport to 375x667 (iPhone SE)
- [ ] Navigate to `/recruiter/dashboard`
- [ ] Verify hamburger menu is visible
- [ ] Click hamburger menu to open drawer
- [ ] Verify navigation items appear
- [ ] Verify sidebar is not visible (drawer behavior)
- [ ] Close drawer
- [ ] Navigate to `/recruiter/vacancies`
- [ ] Verify grid layout collapses to single column
- [ ] Navigate to `/recruiter/candidates`
- [ ] Verify kanban columns stack vertically
- [ ] Verify candidate cards are still draggable
- [ ] Navigate to `/recruiter/weights`
- [ ] Verify sliders are touch-friendly
- [ ] Verify tabs are easily tappable

**Test 2.4.2: Tablet Layout (768px)**
- [ ] Set browser viewport to 768x1024 (iPad)
- [ ] Navigate to `/recruiter/dashboard`
- [ ] Verify layout adapts to tablet size
- [ ] Check if hamburger menu still visible (may depend on breakpoint)
- [ ] Navigate to `/recruiter/vacancies`
- [ ] Verify grid uses 2 columns
- [ ] Navigate to `/recruiter/candidates`
- [ ] Verify kanban board fits on screen

**Test 2.4.3: Desktop Layout (1920px)**
- [ ] Set browser viewport to 1920x1080
- [ ] Navigate to `/recruiter/dashboard`
- [ ] Verify sidebar navigation is visible
- [ ] Verify hamburger menu is not visible
- [ ] Navigate to `/recruiter/vacancies`
- [ ] Verify grid uses 3-4 columns
- [ ] Navigate to `/recruiter/candidates`
- [ ] Verify kanban board displays all columns horizontally

---

## Part 3: Cross-Flow Validation

### 3.1 Flow Separation

**Test 3.1.1: Candidate Flow Isolation**
- [ ] Navigate to `/jobs` (candidate flow)
- [ ] Verify JobSeekerLayout is active
- [ ] Verify NO recruiter sidebar is visible
- [ ] Verify NO "Weights" navigation item
- [ ] Verify NO "Analytics" navigation item
- [ ] Verify candidate-specific navigation is present (Saved, Applications, Profile)

**Test 3.1.2: Recruiter Flow Isolation**
- [ ] Navigate to `/recruiter/dashboard`
- [ ] Verify RecruiterLayout is active
- [ ] Verify NO candidate bottom navigation is visible
- [ ] Verify NO "Saved Jobs" navigation item
- [ ] Verify NO "My Applications" navigation item
- [ ] Verify recruiter-specific navigation is present (Vacancies, Candidates, Analytics, Weights)

**Test 3.1.3: No Cross-Flow Navigation**
- [ ] In candidate flow, verify cannot navigate to recruiter pages via nav
- [ ] In recruiter flow, verify cannot navigate to candidate pages via nav
- [ ] Verify direct URL access to both flows works
- [ ] Verify flows remain visually distinct

### 3.2 Error Handling

**Test 3.2.1: Invalid Job/Vacancy IDs**
- [ ] Navigate to `/jobs/nonexistent-job-id`
- [ ] Verify error page or redirect
- [ ] Check browser console for errors (should be none)
- [ ] Navigate to `/recruiter/vacancies/nonexistent-id`
- [ ] Verify error page or redirect
- [ ] Check browser console for errors

**Test 3.2.2: Invalid Candidate IDs**
- [ ] Navigate to `/recruiter/candidates/nonexistent-id`
- [ ] Verify error page or redirect
- [ ] Verify graceful error handling
- [ ] Check browser console for errors

**Test 3.2.3: Network Errors**
- [ ] Turn off backend API (if possible)
- [ ] Navigate to candidate pages
- [ ] Verify loading states display
- [ ] Verify error states display gracefully
- [ ] Verify no browser crashes
- [ ] Navigate to recruiter pages
- [ ] Verify loading states display
- [ ] Verify error states display gracefully

### 3.3 Accessibility

**Test 3.3.1: Keyboard Navigation**
- [ ] Use Tab key to navigate through candidate pages
- [ ] Verify focus order is logical
- [ ] Verify focus indicators are visible
- [ ] Use Enter key to activate buttons/links
- [ ] Repeat for recruiter pages

**Test 3.3.2: Screen Reader Support**
- [ ] Enable screen reader (NVDA, JAWS, or VoiceOver)
- [ ] Navigate to `/jobs`
- [ ] Verify page announcements
- [ ] Verify landmark regions (nav, main, etc.)
- [ ] Verify form labels are announced
- [ ] Repeat for recruiter pages

**Test 3.3.3: Color Contrast**
- [ ] Check all text has sufficient contrast (WCAG AA minimum)
- [ ] Verify interactive elements are distinguishable
- [ ] Check error messages have adequate contrast
- [ ] Verify status badges are readable

### 3.4 Performance

**Test 3.4.1: Page Load Times**
- [ ] Check page load time for `/jobs` (should be < 2s)
- [ ] Check page load time for `/recruiter/dashboard` (should be < 2s)
- [ ] Check page load time for `/jobs/applications` (should be < 2s)
- [ ] Check page load time for `/recruiter/candidates` (should be < 2s)

**Test 3.4.2: Navigation Transitions**
- [ ] Navigate between candidate pages
- [ ] Verify smooth transitions (no jarring layout shifts)
- [ ] Check for page transition animations
- [ ] Repeat for recruiter pages

---

## Part 4: Automated E2E Test Execution

### 4.1 Run Candidate Flow E2E Tests

```bash
cd frontend
npm run test:e2e -- candidate-flow.spec.ts
```

Verify:
- [ ] All candidate flow tests pass
- [ ] No console errors in test output
- [ ] Screenshots captured for failures (if any)

### 4.2 Run Recruiter Flow E2E Tests

```bash
cd frontend
npm run test:e2e -- recruiter-flow.spec.ts
```

Verify:
- [ ] All recruiter flow tests pass
- [ ] No console errors in test output
- [ ] Screenshots captured for failures (if any)

### 4.3 Run All E2E Tests

```bash
cd frontend
npm run test:e2e
```

Verify:
- [ ] All E2E tests pass
- [ ] Test coverage report generated (if configured)
- [ ] No critical failures

---

## Part 5: Bug Reporting

### Issues Found

Document any issues discovered during testing:

| Issue | Severity | Page | Steps to Reproduce | Expected | Actual |
|-------|----------|------|-------------------|----------|--------|
|       |          |      |                   |          |        |

### Severity Levels

- **Critical**: Blocks core functionality, prevents flow completion
- **High**: Significant issue, major functionality broken
- **Medium**: Issue present but workaround exists
- **Low**: Minor UI/UX issue, cosmetic problem

---

## Part 6: Sign-off

### Tester Information

- **Tester Name**: ___________________
- **Test Date**: ___________________
- **Browser**: ___________________ (Chrome, Firefox, Safari, Edge)
- **Browser Version**: ___________________
- **Device**: ___________________ (Desktop, Mobile, Tablet)
- **OS**: ___________________

### Test Results Summary

- **Total Tests**: _____
- **Passed**: _____
- **Failed**: _____
- **Skipped**: _____
- **Pass Rate**: _____%

### Approval

- [ ] All critical issues resolved
- [ ] All high-priority issues resolved or documented
- [ ] Flow separation verified
- [ ] Mobile responsiveness verified
- [ ] Accessibility requirements met
- [ ] Performance acceptable

**Tester Signature**: ___________________

**Date**: ___________________

---

## Appendix: Test Data Requirements

### Candidate Flow Test Data

- Sample job postings (3-5)
- Sample applications (2-3)
- Sample saved jobs (2-3)
- Sample resume file (PDF or DOCX)

### Recruiter Flow Test Data

- Sample vacancies (3-5)
- Sample candidates (10-15)
- Sample applications in various stages
- Existing weight profiles (2-3)

### Test Accounts

- Candidate user account (if auth implemented)
- Recruiter user account (if auth implemented)
- Admin account (if needed)

---

**End of E2E Testing Checklist**
