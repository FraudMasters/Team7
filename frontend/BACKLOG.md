# Frontend Development Backlog

> **Last updated:** 2026-02-01
> **Backend API version:** Current (matching main.py routes)

---

## Overview

This document lists all backend API endpoints and features that are **not yet implemented** in the frontend. The frontend currently implements ~40% of available backend functionality.

**Current frontend coverage:**
- ✅ Resumes (upload, analyze)
- ✅ Vacancies (CRUD, matching)
- ✅ Candidates (list, kanban board)
- ✅ Analytics (key-metrics, skill-demand)
- ✅ Matching (feedback, weights)
- ✅ Settings (language)

---

## Missing Modules by Priority

### 🔴 HIGH Priority (Core Recruiter Features)

#### 1. Search Module (`/api/search`)
**Backend file:** `backend/api/search.py`

**Missing frontend:**
- Search page component
- Search filters (skills, location, experience, salary)
- Search results display with match scores
- Save search functionality

**API endpoints:**
- `POST /api/search` - Search resumes by criteria
- `GET /api/search/saved` - List saved searches
- `POST /api/search/saved` - Save search criteria
- `DELETE /api/search/saved/{id}` - Delete saved search

**User stories:**
- As a recruiter, I want to search resumes by skills and location
- As a recruiter, I want to save my search criteria for later use
- As a recruiter, I want to see match scores for each search result

---

#### 2. Saved Searches Module (`/api/saved_searches`)
**Backend file:** `backend/api/saved_searches.py`

**Missing frontend:**
- Saved searches management page
- Create/edit saved search dialog
- List of saved searches with quick actions
- Auto-match notifications for new resumes

**API endpoints:**
- `GET /api/saved-searches` - List saved searches
- `POST /api/saved-searches` - Create saved search
- `PUT /api/saved-searches/{id}` - Update saved search
- `DELETE /api/saved-searches/{id}` - Delete saved search
- `POST /api/saved-searches/{id}/match` - Find matching resumes

---

#### 3. Candidate Tags Module (`/api/candidate-tags`)
**Backend file:** `backend/api/candidate_tags.py`

**Missing frontend:**
- Tag management component
- Tag selector for filtering candidates
- Tag creation/editing dialog
- Tag color coding

**API endpoints:**
- `GET /api/candidate-tags` - List all tags
- `POST /api/candidate-tags` - Create tag
- `PUT /api/candidate-tags/{id}` - Update tag
- `DELETE /api/candidate-tags/{id}` - Delete tag
- `POST /api/candidates/{id}/tags/{tag_id}` - Add tag to candidate
- `DELETE /api/candidates/{id}/tags/{tag_id}` - Remove tag from candidate

---

#### 4. Candidate Notes Module (`/api/candidate-notes`)
**Backend file:** `backend/api/candidate_notes.py`

**Missing frontend:**
- Notes component for candidate profile
- Add/edit note dialogs
- Notes timeline view
- Rich text or markdown support?

**API endpoints:**
- `GET /api/candidates/{id}/notes` - List candidate notes
- `POST /api/candidates/{id}/notes` - Add note
- `PUT /api/candidates/{id}/notes/{note_id}` - Update note
- `DELETE /api/candidates/{id}/notes/{note_id}` - Delete note

---

#### 5. Reports Module (`/api/reports`)
**Backend file:** `backend/api/reports.py`

**Missing frontend:**
- Reports generation page
- Report templates selection
- Download/export reports (PDF, Excel)
- Scheduled reports management

**API endpoints:**
- `GET /api/reports` - List reports
- `POST /api/reports` - Generate report
- `GET /api/reports/{id}` - Get report details
- `GET /api/reports/{id}/download` - Download report file
- `DELETE /api/reports/{id}` - Delete report

---

### 🟡 MEDIUM Priority (Enhancement Features)

#### 6. Ranking Module (`/api/ranking`)
**Backend file:** `backend/api/ranking.py`

**Missing frontend:**
- Candidate ranking comparison view
- Ranking feedback collection
- Top candidates display
- Ranking history

**API endpoints:**
- `GET /api/ranking` - Get candidate rankings
- `POST /api/ranking/{id}/feedback` - Submit ranking feedback
- `GET /api/ranking/{id}/history` - Ranking history

---

#### 7. Skill Gap Analysis (`/api/skill-gap`)
**Backend file:** `backend/api/skill_gap_analysis.py`

**Missing frontend:**
- Skill gap visualization
- Gap analysis report view
- Learning recommendations display
- Progress tracking

**API endpoints:**
- `POST /api/skill-gap/analyze` - Analyze skill gaps
- `GET /api/skill-gap/reports` - List gap analysis reports
- `GET /api/skill-gap/reports/{id}` - Get report details
- `POST /api/skill-gap/reports/{id}/plan` - Generate learning plan

---

#### 8. Interview Preparation (`/api/interview_prep`)
**Backend file:** `backend/api/interview_prep.py`

**Missing frontend:**
- Interview prep page for candidates
- Interview questions generator
- Tips and suggestions display

**API endpoints:**
- `POST /api/interview-prep/generate` - Generate interview questions
- `POST /api/interview-prep/tips` - Get interview tips

---

#### 9. Batch Operations (`/api/batch`)
**Backend file:** `backend/api/batch.py`

**Missing frontend:**
- Batch upload page (partially exists)
- Batch operation status tracking
- Batch results download

**API endpoints:**
- `POST /api/batch/upload` - Batch upload resumes
- `GET /api/batch/jobs/{job_id}` - Get batch job status
- `GET /api/batch/jobs/{job_id}/results` - Get batch results
- `DELETE /api/batch/jobs/{job_id}` - Cancel batch job

---

### 🟢 LOW Priority (Admin & Advanced Features)

#### 10. Taxonomy Management
**Backend files:**
- `backend/api/skill_taxonomies.py`
- `backend/api/taxonomy_import_export.py`
- `backend/api/taxonomy_sharing.py`
- `backend/api/taxonomy_versions.py`

**Missing frontend:**
- Taxonomy management page
- Import/export taxonomy UI
- Shared taxonomies view
- Version history display

---

#### 11. Custom Synonyms
**Backend file:** `backend/api/custom_synonyms.py`

**Missing frontend:**
- Synonyms management page
- Add/edit synonym UI
- Organization-level synonyms

---

#### 12. Matching Weights
**Backend file:** `backend/api/matching_weights.py`

**Missing frontend:**
- Weights configuration page
- Preset profiles selection
- Weight profile comparison

---

#### 13. Performance Monitoring
**Backend file:** `backend/api/performance_monitoring.py`

**Missing frontend:**
- Performance metrics dashboard
- System health monitoring
- ML model performance tracking

---

#### 14. Backups
**Backend file:** `backend/api/backups.py`

**Missing frontend:**
- Backup management page
- Backup scheduling UI
- Backup download/restore

---

#### 15. Fairness Monitoring
**Backend file:** `backend/api/fairness.py`

**Missing frontend:**
- Fairness metrics dashboard
- Bias detection alerts
- Fairness reports

---

#### 16. Work Experience Module (`/api/work-experiences`)
**Backend file:** `backend/api/work_experience.py`

**Missing frontend:**
- Work experience extraction display
- Experience timeline view
- Experience validation

---

#### 17. Workflow Stages Enhancement
**Backend file:** `backend/api/workflow_stages.py`

**Current state:** Partially implemented in kanban

**Missing:**
- Stage configuration page
- Custom stage creation
- Stage metrics display

---

## Page-by-Page Gap Analysis

### Existing Pages | What's Implemented | What's Missing
------------------|-------------------|------------------
`/recruiter/dashboard` | ✅ Bento metrics, basic stats | ❌ Recruiter performance chart
`/recruiter/candidates` | ✅ Kanban board | ❌ Advanced filters, bulk actions
`/recruiter/vacancies` | ✅ List, create, edit, delete | ❌ Application pipeline view
`/recruiter/analytics` | ✅ Key metrics, skill demand | ❌ Funnel, recruiter performance, source tracking
`/jobs/*` | ✅ Browse, detail, apply | ❌ Saved searches, job alerts
`/jobs/upload` | ✅ Single upload | ❌ Batch upload tracking
`/` (landing) | ✅ Landing page | ❌ Job seeker onboarding

---

## Component-Level Gaps

### Missing Components

1. **SearchComponents**
   - `SearchBar.tsx` - Unified search input
   - `SearchFilters.tsx` - Advanced filters panel
   - `SavedSearchesList.tsx` - Saved searches management
   - `SearchResults.tsx` - Results with match scores

2. **CandidateProfileComponents**
   - `CandidateNotes.tsx` - Notes timeline
   - `CandidateTags.tsx` - Tag management
   - `CandidateActivities.tsx` - Activity history
   - `CandidateComparison.tsx` - Side-by-side view

3. **ReportingComponents**
   - `ReportBuilder.tsx` - Partially exists
   - `ReportTemplates.tsx` - Template selection
   - `ReportDownload.tsx` - Export functionality

4. **AdminComponents**
   - `TaxonomyManager.tsx` - Manage skill taxonomies
   - `BackupManager.tsx` - Backup operations
   - `SystemMonitor.tsx` - Performance dashboard

---

## Technical Debt & Improvements Needed

### Build & Deployment
- [ ] Add prop-types to dependencies (partially done)
- [ ] Fix MUI circular chunk warnings
- [ ] Add proper error boundaries for all pages
- [ ] Add loading skeletons for better UX

### Code Quality
- [ ] Add TypeScript strict mode checks
- [ ] Add unit tests for components
- [ ] Add E2E tests for critical flows
- [ ] Fix CSS warnings in build

### UX Improvements
- [ ] Add toast notifications for actions
- [ ] Add optimistic updates
- [ ] Add proper empty states
- [ ] Add keyboard shortcuts
- [ ] Add pagination for large lists

---

## Dependencies Analysis

### Installed but Not Used

- `@hello-pangea/dnd` - ✅ Used in KanbanBoard
- `framer-motion` - ✅ Used in animations
- `@tanstack/react-query-devtools` - ✅ DevTools enabled
- `react-dropzone` - ✅ Used in upload
- `react-window` - Not used for virtualization
- `react-intersection-observer` - Partially used

### Missing Dependencies

Consider adding:
- `react-hook-form` - Form management
- `zod` - Schema validation
- `@tanstack/react-table` - Advanced tables
- `recharts` - Charts for analytics
- `date-fns` - Date utilities (already installed)

---

## API Integration Status

### Auth & User Management
- ❌ No auth implementation in frontend
- ❌ No user profile management
- ❌ No role-based access control

### File Operations
- ✅ Upload works (resume upload)
- ❌ No download functionality
- ❌ No file management UI

### Real-time Features
- ❌ No WebSocket connections
- ❌ No live updates
- ❌ No notification system

---

## Next Steps for Parallel Development

### Recommended First Steps (Quick Wins)

1. **Search Module** - Critical for recruiters
   - SearchBar component
   - SearchResults page
   - SavedSearches page

2. **Candidate Notes** - Essential for recruitment
   - Add notes to candidate profile
   - Notes timeline component

3. **Reports Download** - Already built in backend
   - Download button on reports
   - Report template selection

### Medium-Term Goals

4. **Candidate Comparison** - Side-by-side view
5. **Skill Gap Visualization** - Charts and reports
6. **Batch Upload Tracking** - Job status monitoring

### Long-Term Goals

7. **Full Admin Dashboard** - System management
8. **Performance Monitoring** - Health checks
9. **Fairness Dashboard** - Bias detection

---

## Notes for Developers

### Component Guidelines

When adding new modules:
1. Check `backend/api/{module}.py` for API structure
2. Add corresponding hooks in `hooks/useRecruiterData.ts` or create new
3. Follow existing patterns in `components/` directory
4. Add TypeScript types in `types/api.ts`
5. Update `api/client.ts` if adding new API methods
6. Test with backend running (docker-compose up backend)

### Database Considerations

Some endpoints fail due to missing Enum types in PostgreSQL:
- `resumestatus` - Needed for funnel analytics
- `hiringstagename` - Needed for source tracking, recruiter performance

**Migration required:** Run backend database migrations to create these types.

---

## References

- **Backend API routes:** `backend/main.py` lines 271-301
- **API client:** `frontend/src/api/client.ts`
- **Component docs:** `frontend/docs/components.md`
- **Migration guide:** `frontend/docs/migration-guide.md`
