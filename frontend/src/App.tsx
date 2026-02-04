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
import { RecommendedJobsPage } from './pages/jobs/RecommendedJobsPage';
import { SkillAssessmentPage } from './pages/jobs/SkillAssessmentPage';
import { LearningPage } from './pages/jobs/LearningPage';
import { SalaryCalculatorPage } from './pages/jobs/SalaryCalculatorPage';
import { InterviewTipsPage } from './pages/jobs/InterviewTipsPage';
import { JobAlertsPage } from './pages/jobs/JobAlertsPage';
import { SettingsPage } from './pages/jobs/SettingsPage';

// Recruiter Pages
import { DashboardPage } from './pages/recruiter/DashboardPage';
import { CandidatesKanbanPage } from './pages/recruiter/CandidatesKanbanPage';
import { VacanciesPage } from './pages/recruiter/VacanciesPage';
import { VacancyFormPage } from './pages/recruiter/VacancyFormPage';
import { VacancyDetailPage } from './pages/recruiter/VacancyDetailPage';
import { CandidateDetailPage } from './pages/recruiter/CandidateDetailPage';
import { WeightsPage } from './pages/recruiter/WeightsPage';
import { SearchPage } from './pages/recruiter/SearchPage';
import { SavedSearchesPage } from './pages/recruiter/SavedSearchesPage';

// Additional Recruiter Pages
import ComparePage from './pages/Compare';
import SkillGapAnalysisPage from './pages/SkillGapAnalysis';
import BackupsPage from './pages/Backups';
import WorkflowBoardPage from './pages/WorkflowBoard';
import UploadPage from './pages/Upload';
import BatchUploadPage from './pages/BatchUpload';
import ApplicationsPage from './pages/Applications';
import ResumeDatabasePage from './pages/ResumeDatabase';
import AnalyticsDashboardPage from './pages/AnalyticsDashboard';
import ResultsPage from './pages/Results';

// LinkedIn Integration Pages
import LinkedInAuthPage from './pages/recruiter/LinkedInAuthPage';
import LinkedInImportPage from './pages/recruiter/LinkedInImportPage';
import LinkedInSearchPage from './pages/recruiter/LinkedInSearchPage';

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
          <Route path="recommended" element={<RecommendedJobsPage />} />
          <Route path="assessment" element={<SkillAssessmentPage />} />
          <Route path="learning" element={<LearningPage />} />
          <Route path="salary" element={<SalaryCalculatorPage />} />
          <Route path="tips" element={<InterviewTipsPage />} />
          <Route path="alerts" element={<JobAlertsPage />} />
          <Route path="settings" element={<SettingsPage />} />
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
          <Route path="search" element={<SearchPage />} />
          <Route path="saved-searches" element={<SavedSearchesPage />} />
          <Route path="applications" element={<ApplicationsPage />} />
          <Route path="resumes" element={<ResumeDatabasePage />} />
          <Route path="upload" element={<UploadPage />} />
          <Route path="batch-upload" element={<BatchUploadPage />} />
          <Route path="compare" element={<ComparePage />} />
          <Route path="skill-gap" element={<SkillGapAnalysisPage />} />
          <Route path="backups" element={<BackupsPage />} />
          <Route path="workflow" element={<WorkflowBoardPage />} />
          <Route path="results/:id" element={<ResultsPage />} />
          <Route path="vacancies">
            <Route index element={<VacanciesPage />} />
            <Route path="create" element={<VacancyFormPage />} />
            <Route path=":id" element={<VacancyDetailPage />} />
            <Route path=":id/edit" element={<VacancyFormPage />} />
          </Route>
          <Route path="weights" element={<WeightsPage />} />
          <Route path="analytics" element={<AnalyticsDashboardPage />} />
          <Route path="linkedin">
            <Route path="auth" element={<LinkedInAuthPage />} />
            <Route path="import" element={<LinkedInImportPage />} />
            <Route path="search" element={<LinkedInSearchPage />} />
          </Route>
        </Route>

        {/* Catch-all route - redirect to landing */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
