import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

// Layouts
import JobSeekerLayout from './layouts/JobSeekerLayout';
import RecruiterLayout from './layouts/RecruiterLayout';

// Pages - Landing
import LandingPage from './pages/LandingPage';

// Job Seeker Pages
import { JobsBrowsePage } from './pages/jobs/JobsBrowsePage';
import { JobDetailPage } from './pages/jobs/JobDetailPage';
import { ApplicationFlowPage } from './pages/jobs/ApplicationFlowPage';
import { SavedJobsPage } from './pages/jobs/SavedJobsPage';
import { MyApplicationsPage } from './pages/jobs/MyApplicationsPage';
import { CandidateProfilePage } from './pages/jobs/CandidateProfilePage';
import { ResumeUploadPage } from './pages/jobs/ResumeUploadPage';
import { ResumeResultsPage } from './pages/jobs/ResumeResultsPage';

// Recruiter Pages
import { DashboardPage } from './pages/recruiter/DashboardPage';
import { CandidatesKanbanPage } from './pages/recruiter/CandidatesKanbanPage';
import { VacanciesPage } from './pages/recruiter/VacanciesPage';
import { VacancyFormPage } from './pages/recruiter/VacancyFormPage';
import { VacancyDetailPage } from './pages/recruiter/VacancyDetailPage';
import { CandidateDetailPage } from './pages/recruiter/CandidateDetailPage';
import { WeightsPage } from './pages/recruiter/WeightsPage';

// Legacy pages (wrapped for compatibility)
import HomePage from './pages/Home';
import UploadPage from './pages/Upload';
import BatchUploadPage from './pages/BatchUpload';
import ResultsPage from './pages/Results';
import ApplicationsPage from './pages/Applications';
import ResumeDatabasePage from './pages/ResumeDatabase';
import RecruiterDashboardPage from './pages/RecruiterDashboard';
import AnalyticsDashboardPage from './pages/AnalyticsDashboard';

/**
 * Main App Component
 *
 * Dual flow architecture for job seekers and recruiters.
 * Uses React Router v6 with nested routes and layout components.
 */
function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Root route - Landing Page */}
        <Route path="/" element={<LandingPage />} />

        {/* Job Seeker Flow */}
        <Route path="/jobs" element={<JobSeekerLayout />}>
          <Route index element={<JobsBrowsePage />} />
          <Route path=":id" element={<JobDetailPage />} />
          <Route path=":id/apply" element={<ApplicationFlowPage />} />
          <Route path="saved" element={<SavedJobsPage />} />
          <Route path="applications" element={<MyApplicationsPage />} />
          <Route path="upload" element={<ResumeUploadPage />} />
          <Route path="resume-results/:id" element={<ResumeResultsPage />} />
        </Route>

        {/* Candidate Profile */}
        <Route path="/profile" element={<JobSeekerLayout />}>
          <Route index element={<CandidateProfilePage />} />
        </Route>

        {/* Recruiter Flow */}
        <Route path="/recruiter" element={<RecruiterLayout />}>
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="candidates" element={<CandidatesKanbanPage />} />
          <Route path="candidates/:id" element={<CandidateDetailPage />} />
          <Route path="vacancies">
            <Route index element={<VacanciesPage />} />
            <Route path="create" element={<VacancyFormPage />} />
            <Route path=":id" element={<VacancyDetailPage />} />
            <Route path=":id/edit" element={<VacancyFormPage />} />
          </Route>
          <Route path="weights" element={<WeightsPage />} />
          <Route path="analytics" element={<AnalyticsDashboardPage />} />
        </Route>

        {/* Legacy routes - wrapped with single layout for compatibility */}
        <Route path="legacy" element={<RecruiterLayout />}>
          <Route path="upload" element={<UploadPage />} />
          <Route path="batch-upload" element={<BatchUploadPage />} />
          <Route path="results/:id" element={<ResultsPage />} />
          <Route path="applications" element={<ApplicationsPage />} />
          <Route path="resumes" element={<ResumeDatabasePage />} />
          <Route path="analytics" element={<AnalyticsDashboardPage />} />
        </Route>

        {/* Catch-all route - redirect to landing */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
