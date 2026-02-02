# Navigation Testing Checklist

## Overview
This checklist is used to manually verify all navigation links work correctly in the dual-flow architecture.

**Date:** 2026-02-02
**Tester:** _______________
**Status:** _______________

---

## Job Seeker Flow Tests

### Bottom Navigation Tests

#### Test 1: Search Navigation
- [ ] From any job seeker page, click "Search" in bottom nav
- [ ] Verify: Navigates to `/jobs`
- [ ] Verify: JobsBrowsePage displays correctly
- [ ] Verify: "Search" nav item is highlighted as active
- [ ] **Result:** PASS / FAIL

#### Test 2: Saved Jobs Navigation
- [ ] From any job seeker page, click "Saved" in bottom nav
- [ ] Verify: Navigates to `/jobs/saved`
- [ ] Verify: SavedJobsPage displays correctly
- [ ] Verify: "Saved" nav item is highlighted as active
- [ ] Verify: Shows saved job count or empty state
- [ ] **Result:** PASS / FAIL

#### Test 3: Applications Navigation
- [ ] From any job seeker page, click "Applications" in bottom nav
- [ ] Verify: Navigates to `/jobs/applications`
- [ ] Verify: MyApplicationsPage displays correctly
- [ ] Verify: "Applications" nav item is highlighted as active
- [ ] Verify: Shows application list or empty state
- [ ] **Result:** PASS / FAIL

#### Test 4: Profile Navigation
- [ ] From any job seeker page, click "Profile" in bottom nav
- [ ] Verify: Navigates to `/profile`
- [ ] Verify: CandidateProfilePage displays correctly
- [ ] Verify: "Profile" nav item is highlighted as active
- [ ] **Result:** PASS / FAIL

### Job Seeker Page Navigation Tests

#### Test 5: Job Browse to Job Detail
- [ ] From JobsBrowsePage, click on a job card
- [ ] Verify: Navigates to `/jobs/:id`
- [ ] Verify: JobDetailPage displays with correct job
- [ ] Verify: Job details match the clicked job
- [ ] **Result:** PASS / FAIL

#### Test 6: Job Detail to Application Flow
- [ ] From JobDetailPage, click "Apply Now" button
- [ ] Verify: Navigates to `/jobs/:id/apply`
- [ ] Verify: ApplicationFlowPage displays
- [ ] Verify: Application form loads correctly
- [ ] **Result:** PASS / FAIL

#### Test 7: Saved Jobs to Job Detail
- [ ] From SavedJobsPage, click on a saved job card
- [ ] Verify: Navigates to `/jobs/:id`
- [ ] Verify: JobDetailPage displays with correct job
- [ ] Verify: Job details match the clicked job
- [ ] **Result:** PASS / FAIL

#### Test 8: My Applications to Job Detail
- [ ] From MyApplicationsPage, click on an application card
- [ ] Verify: Navigates to `/jobs/:vacancy_id`
- [ ] Verify: JobDetailPage displays with correct job
- [ ] Verify: Job details match the application's job
- [ ] **Result:** PASS / FAIL

#### Test 9: Profile to Resume Upload
- [ ] From CandidateProfilePage, click on resume upload link/button
- [ ] Verify: Navigates to `/jobs/upload`
- [ ] Verify: ResumeUploadPage displays
- [ ] Verify: Upload interface loads correctly
- [ ] **Result:** PASS / FAIL

#### Test 10: Resume Upload to Results
- [ ] From ResumeUploadPage, upload a resume file
- [ ] Verify: After upload, navigates to `/jobs/resume-results/:id`
- [ ] Verify: ResumeResultsPage displays with analysis
- [ ] Verify: Results match uploaded resume
- [ ] **Result:** PASS / FAIL

---

## Recruiter Flow Tests

### Sidebar Navigation Tests

#### Test 11: Dashboard Navigation
- [ ] From any recruiter page, click "Dashboard" in sidebar
- [ ] Verify: Navigates to `/recruiter/dashboard`
- [ ] Verify: DashboardPage displays correctly
- [ ] Verify: "Dashboard" nav item is highlighted as active
- [ ] **Result:** PASS / FAIL

#### Test 12: Vacancies Navigation
- [ ] From any recruiter page, click "Vacancies" in sidebar
- [ ] Verify: Navigates to `/recruiter/vacancies`
- [ ] Verify: VacanciesPage displays correctly
- [ ] Verify: "Vacancies" nav item is highlighted as active
- [ ] Verify: Shows vacancy list or empty state
- [ ] **Result:** PASS / FAIL

#### Test 13: Candidates Navigation
- [ ] From any recruiter page, click "Candidates" in sidebar
- [ ] Verify: Navigates to `/recruiter/candidates`
- [ ] Verify: CandidatesKanbanPage displays correctly
- [ ] Verify: "Candidates" nav item is highlighted as active
- [ ] Verify: Kanban board displays
- [ ] **Result:** PASS / FAIL

#### Test 14: Analytics Navigation
- [ ] From any recruiter page, click "Analytics" in sidebar
- [ ] Verify: Navigates to `/recruiter/analytics`
- [ ] Verify: AnalyticsDashboardPage displays correctly
- [ ] Verify: "Analytics" nav item is highlighted as active
- [ ] **Result:** PASS / FAIL

#### Test 15: Weights Navigation
- [ ] From any recruiter page, click "Weights" in sidebar
- [ ] Verify: Navigates to `/recruiter/weights`
- [ ] Verify: WeightsPage displays correctly
- [ ] Verify: "Weights" nav item is highlighted as active
- [ ] Verify: Weight customization interface loads
- [ ] **Result:** PASS / FAIL

### Recruiter Page Navigation Tests

#### Test 16: Vacancies List to Create Vacancy
- [ ] From VacanciesPage, click "Create Vacancy" button
- [ ] Verify: Navigates to `/recruiter/vacancies/create`
- [ ] Verify: VacancyFormPage displays in create mode
- [ ] Verify: Empty form loads correctly
- [ ] **Result:** PASS / FAIL

#### Test 17: Vacancies List to Vacancy Detail
- [ ] From VacanciesPage, click on a vacancy card
- [ ] Verify: Navigates to `/recruiter/vacancies/:id`
- [ ] Verify: VacancyDetailPage displays with correct vacancy
- [ ] Verify: Vacancy details match the clicked vacancy
- [ ] **Result:** PASS / FAIL

#### Test 18: Vacancy Detail to Edit
- [ ] From VacancyDetailPage, click "Edit Vacancy" button
- [ ] Verify: Navigates to `/recruiter/vacancies/:id/edit`
- [ ] Verify: VacancyFormPage displays in edit mode
- [ ] Verify: Form is pre-filled with vacancy data
- [ ] **Result:** PASS / FAIL

#### Test 19: Vacancy Detail to Candidates
- [ ] From VacancyDetailPage, click "View Candidates" button
- [ ] Verify: Navigates to `/recruiter/candidates`
- [ ] Verify: CandidatesKanbanPage displays
- [ ] Verify: Candidates list shows
- [ ] **Result:** PASS / FAIL

#### Test 20: Candidates Kanban to Candidate Detail
- [ ] From CandidatesKanbanPage, click on a candidate card
- [ ] Verify: Navigates to `/recruiter/candidates/:id`
- [ ] Verify: CandidateDetailPage displays with correct candidate
- [ ] Verify: Candidate information displays correctly
- [ ] **Result:** PASS / FAIL

#### Test 21: Vacancy Form Submit
- [ ] From VacancyFormPage (create mode), fill form and submit
- [ ] Verify: After submit, navigates to `/recruiter/vacancies`
- [ ] Verify: VacanciesPage displays with new vacancy
- [ ] **Result:** PASS / FAIL

#### Test 22: Vacancy Edit Submit
- [ ] From VacancyFormPage (edit mode), modify form and submit
- [ ] Verify: After submit, navigates to `/recruiter/vacancies`
- [ ] Verify: VacanciesPage displays with updated vacancy
- [ ] **Result:** PASS / FAIL

---

## Browser Navigation Tests

### Back Button Tests

#### Test 23: Job Seeker Back Navigation
- [ ] Navigate: Search → Job Detail → Application Flow
- [ ] Click browser back button
- [ ] Verify: Returns to Job Detail page
- [ ] Click back again
- [ ] Verify: Returns to JobsBrowsePage
- [ ] **Result:** PASS / FAIL

#### Test 24: Recruiter Back Navigation
- [ ] Navigate: Dashboard → Vacancies → Vacancy Detail → Edit
- [ ] Click browser back button
- [ ] Verify: Returns to Vacancy Detail page
- [ ] Click back again
- [ ] Verify: Returns to VacanciesPage
- [ ] **Result:** PASS / FAIL

### Forward Button Tests

#### Test 25: Browser Forward Navigation
- [ ] Navigate to any page
- [ ] Click back button
- [ ] Click forward button
- [ ] Verify: Returns to original page
- [ ] Verify: Page state is preserved
- [ ] **Result:** PASS / FAIL

### Direct URL Access Tests

#### Test 26: Job Seeker Direct URLs
- [ ] Enter `/jobs` directly in address bar
- [ ] Verify: JobsBrowsePage loads correctly
- [ ] Enter `/jobs/saved` directly
- [ ] Verify: SavedJobsPage loads correctly
- [ ] Enter `/jobs/applications` directly
- [ ] Verify: MyApplicationsPage loads correctly
- [ ] Enter `/profile` directly
- [ ] Verify: CandidateProfilePage loads correctly
- [ ] **Result:** PASS / FAIL

#### Test 27: Recruiter Direct URLs
- [ ] Enter `/recruiter/dashboard` directly
- [ ] Verify: DashboardPage loads correctly
- [ ] Enter `/recruiter/vacancies` directly
- [ ] Verify: VacanciesPage loads correctly
- [ ] Enter `/recruiter/candidates` directly
- [ ] Verify: CandidatesKanbanPage loads correctly
- [ ] Enter `/recruiter/weights` directly
- [ ] Verify: WeightsPage loads correctly
- [ ] **Result:** PASS / FAIL

#### Test 28: Dynamic Route URLs
- [ ] Enter `/jobs/123` (or any valid job ID)
- [ ] Verify: JobDetailPage loads for that job
- [ ] Enter `/recruiter/vacancies/456` (or any valid vacancy ID)
- [ ] Verify: VacancyDetailPage loads for that vacancy
- [ ] Enter `/recruiter/candidates/789` (or any valid candidate ID)
- [ ] Verify: CandidateDetailPage loads for that candidate
- [ ] **Result:** PASS / FAIL

---

## Mobile Responsiveness Tests

#### Test 29: Job Seeker Mobile Navigation
- [ ] Resize viewport to mobile size (< 900px)
- [ ] Verify: Bottom navigation is visible
- [ ] Verify: All 4 nav items are accessible
- [ ] Tap each nav item
- [ ] Verify: Navigation works correctly on touch
- [ ] **Result:** PASS / FAIL

#### Test 30: Recruiter Mobile Navigation
- [ ] Resize viewport to mobile size (< 900px)
- [ ] Verify: Hamburger menu appears in AppBar
- [ ] Tap hamburger menu
- [ ] Verify: Drawer opens from left
- [ ] Tap each nav item
- [ ] Verify: Navigation works and drawer closes
- [ ] **Result:** PASS / FAIL

---

## Accessibility Tests

#### Test 31: Keyboard Navigation - Job Seeker
- [ ] Use Tab key to navigate through bottom nav
- [ ] Verify: Focus is visible on each nav item
- [ ] Press Enter on focused nav item
- [ ] Verify: Navigation triggers correctly
- [ ] **Result:** PASS / FAIL

#### Test 32: Keyboard Navigation - Recruiter
- [ ] Use Tab key to navigate through sidebar
- [ ] Verify: Focus is visible on each nav item
- [ ] Press Enter on focused nav item
- [ ] Verify: Navigation triggers correctly
- [ ] **Result:** PASS / FAIL

#### Test 33: Screen Reader Support
- [ ] Enable screen reader (VoiceOver/NVDA)
- [ ] Navigate through pages
- [ ] Verify: Page titles are announced
- [ ] Verify: Navigation items are properly labeled
- [ ] Verify: Active page is indicated with "current page"
- [ ] **Result:** PASS / FAIL

#### Test 34: Skip Link Functionality
- [ ] Load any page with JobSeekerLayout or RecruiterLayout
- [ ] Press Tab key
- [ ] Verify: Skip link appears at top
- [ ] Press Enter on skip link
- [ ] Verify: Focus moves to main content
- [ ] **Result:** PASS / FAIL

---

## Flow Separation Tests

#### Test 35: No Flow Crossing
- [ ] From job seeker flow, try to access recruiter routes
- [ ] Verify: No links in job seeker pages lead to recruiter routes
- [ ] From recruiter flow, try to access job seeker routes
- [ ] Verify: No links in recruiter pages lead to job seeker routes
- [ ] Verify: Only way to switch flows is via LandingPage
- [ ] **Result:** PASS / FAIL

---

## Edge Case Tests

#### Test 36: Invalid Route Handling
- [ ] Enter `/invalid-route` in address bar
- [ ] Verify: Redirects to landing page (/)
- [ ] Enter `/jobs/invalid-id` in address bar
- [ ] Verify: Page shows error state or 404 message
- [ ] **Result:** PASS / FAIL

#### Test 37: Route Traversal Attack
- [ ] Try accessing `/../../../etc/passwd` or similar path traversal
- [ ] Verify: Handled safely (redirects to landing or shows error)
- [ ] **Result:** PASS / FAIL

---

## Summary

### Test Results
- **Total Tests:** 37
- **Passed:** _____
- **Failed:** _____
- **Skipped:** _____

### Failed Tests Details
List any failed tests with issues found:

1.
2.
3.

### Overall Status
- [ ] All critical navigation paths working
- [ ] Browser navigation (back/forward) working
- [ ] Mobile navigation working
- [ ] Accessibility requirements met
- [ ] No broken links found
- [ ] Flow separation maintained

### Tester Notes
_____________________________________________________________________________
_____________________________________________________________________________
_____________________________________________________________________________

### Sign-off
**Tester Name:** _______________
**Date:** _______________
**Status:** APPROVED / NEEDS FIXES
