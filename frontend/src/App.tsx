import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Box, Typography } from '@mui/material';

// Layouts
import JobSeekerLayout from './layouts/JobSeekerLayout';
import RecruiterLayout from './layouts/RecruiterLayout';
import HiringManagerLayout from './layouts/HiringManagerLayout';

// Authentication
import ProtectedRoute from './auth/ProtectedRoute';
import { UserRole } from './contexts/AuthContext';

// Pages - Landing
import LandingPage from './pages/LandingPage';

// Authentication Pages
import { LoginPage } from './auth/LoginPage';
import { RegisterPage } from './auth/RegisterPage';
import { CallbackPage } from './auth/CallbackPage';
import EmailVerificationPage from './pages/auth/EmailVerificationPage';
import JobSeekerRegisterPage from './pages/auth/JobSeekerRegisterPage';

// Job Seeker Pages
import { JobsBrowsePage } from './pages/jobs/JobsBrowsePage';
import { JobDetailPage } from './pages/jobs/JobDetailPage';
import { ApplicationFlowPage } from './pages/jobs/ApplicationFlowPage';
import { SavedJobsPage } from './pages/jobs/SavedJobsPage';
import { MyApplicationsPage } from './pages/jobs/MyApplicationsPage';
import { CandidateProfilePage } from './pages/jobs/CandidateProfilePage';
import { JobSeekerProfilePage } from './pages/JobSeekerProfilePage';
import { ResumeUploadPage } from './pages/jobs/ResumeUploadPage';
import { ResumeResultsPage } from './pages/jobs/ResumeResultsPage';
import { ResumeTemplatesPage } from './pages/jobs/ResumeTemplatesPage';
import { RecommendedJobsPage } from './pages/jobs/RecommendedJobsPage';
import { SkillAssessmentPage } from './pages/jobs/SkillAssessmentPage';
import { LearningPage } from './pages/jobs/LearningPage';
import { SalaryCalculatorPage } from './pages/jobs/SalaryCalculatorPage';
import { InterviewTipsPage } from './pages/jobs/InterviewTipsPage';
import { JobAlertsPage } from './pages/jobs/JobAlertsPage';
import { SettingsPage } from './pages/jobs/SettingsPage';
import { ResumeOptimizationPage } from './pages/jobs/ResumeOptimizationPage';
import { ResumeBuilderPage } from './pages/jobs/ResumeBuilderPage';

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
import { ReviewQueuePage as RecruiterReviewQueuePage } from './pages/recruiter/ReviewQueuePage';

// Hiring Manager Pages
import { DashboardPage as HiringManagerDashboardPage } from './pages/hiring-manager/DashboardPage';
import { ReviewQueuePage as HiringManagerReviewQueuePage } from './pages/hiring-manager/ReviewQueuePage';
import { CandidateDetailPage as HiringManagerCandidateDetailPage } from './pages/hiring-manager/CandidateDetailPage';
import { InterviewSchedulePage as HiringManagerInterviewSchedulePage } from './pages/hiring-manager/InterviewSchedulePage';

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
import BiasDetectionDashboardPage from './pages/BiasDetectionDashboard';
import ResultsPage from './pages/Results';
import HealthDashboard from './pages/HealthDashboard';

// Template Builder
import { TemplateBuilder } from './components/TemplateBuilder/TemplateBuilder';
import FeedbackTemplatesPage from './pages/FeedbackTemplates';
import SMSTemplateDemo from './pages/SMSTemplateDemo';

// AI Explainability Dashboard (lazy loaded)
import { lazy, Suspense } from 'react';
const AIExplainabilityDashboard = lazy(
  () => import('./pages/admin/AIExplainabilityDashboard')
);

/**
 * Protected Recruiter Layout Wrapper
 *
 * Wraps the RecruiterLayout with role-based access control.
 * Only users with Recruiter or Admin roles can access recruiter routes.
 */
function ProtectedRecruiterLayout() {
  return (
    <ProtectedRoute requiredRoles={[UserRole.Recruiter, UserRole.Admin]} redirectTo="/auth/login">
      <RecruiterLayout />
    </ProtectedRoute>
  );
}

/**
 * Protected Hiring Manager Layout Wrapper
 *
 * Wraps the HiringManagerLayout with role-based access control.
 * Only users with HiringManager, Recruiter, or Admin roles can access hiring manager routes.
 */
function ProtectedHiringManagerLayout() {
  return (
    <ProtectedRoute
      requiredRoles={[UserRole.HiringManager, UserRole.Recruiter, UserRole.Admin]}
      redirectTo="/auth/login"
    >
      <HiringManagerLayout />
    </ProtectedRoute>
  );
}

/**
 * Placeholder component for hiring manager pages under development.
 * Displays a coming soon message with the page name.
 */
function HiringManagerPlaceholder({ title }: { title: string }) {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
        gap: 2,
      }}
    >
      <Typography variant="h4" component="h1" color="text.primary">
        {title}
      </Typography>
      <Typography variant="body1" color="text.secondary">
        This page is under development. Check back soon!
      </Typography>
    </Box>
  );
}

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

        {/* Authentication Routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/auth/login" element={<LoginPage />} />
        <Route path="/auth/register" element={<RegisterPage />} />
        <Route path="/auth/callback" element={<CallbackPage />} />
        <Route path="/verify-email" element={<EmailVerificationPage />} />

        {/* Job Seeker Authentication Routes */}
        <Route path="/job-seeker/register" element={<JobSeekerRegisterPage />} />

        {/* Job Seeker Flow */}
        <Route path="/jobs" element={<JobSeekerLayout />}>
          <Route index element={<JobsBrowsePage />} />
          <Route path=":id" element={<JobDetailPage />} />
          <Route path=":id/apply" element={<ApplicationFlowPage />} />
          <Route path="saved" element={<SavedJobsPage />} />
          <Route path="applications" element={<MyApplicationsPage />} />
          <Route path="upload" element={<ResumeUploadPage />} />
          <Route path="resume-templates" element={<ResumeTemplatesPage />} />
          <Route path="resume-builder" element={<ResumeBuilderPage />} />
          <Route path="resume-results/:id" element={<ResumeResultsPage />} />
          <Route path="recommended" element={<RecommendedJobsPage />} />
          <Route path="assessment" element={<SkillAssessmentPage />} />
          <Route path="learning" element={<LearningPage />} />
          <Route path="salary" element={<SalaryCalculatorPage />} />
          <Route path="tips" element={<InterviewTipsPage />} />
          <Route path="alerts" element={<JobAlertsPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="resume-optimization/:id" element={<ResumeOptimizationPage />} />
        </Route>

        {/* Candidate Profile */}
        <Route path="/profile" element={<JobSeekerLayout />}>
          <Route index element={<JobSeekerProfilePage />} />
        </Route>

        {/* Template Builder (standalone, no auth required for development) */}
        <Route path="/templates/builder" element={<TemplateBuilder />} />
        <Route path="/templates/sms" element={<SMSTemplateDemo />} />

        {/* Recruiter Flow - Protected with role-based access control */}
        <Route path="/recruiter" element={<ProtectedRecruiterLayout />}>
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="candidates" element={<CandidatesKanbanPage />} />
          <Route path="candidates/:id" element={<CandidateDetailPage />} />
          <Route path="review-queue" element={<RecruiterReviewQueuePage />} />
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
          <Route path="bias-detection" element={<BiasDetectionDashboardPage />} />
          <Route path="health" element={<HealthDashboard />} />
          <Route path="feedback-templates" element={<FeedbackTemplatesPage />} />
        </Route>

        {/* Hiring Manager Flow - Protected with role-based access control */}
        <Route path="/hiring-manager" element={<ProtectedHiringManagerLayout />}>
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<HiringManagerDashboardPage />} />
          <Route path="review-queue" element={<HiringManagerReviewQueuePage />} />
          <Route path="candidates/:id" element={<HiringManagerCandidateDetailPage />} />
          <Route path="approvals" element={<HiringManagerPlaceholder title="Approvals" />} />
          <Route path="schedule" element={<HiringManagerInterviewSchedulePage />} />
          <Route path="profile" element={<HiringManagerPlaceholder title="Profile" />} />
          <Route path="settings" element={<HiringManagerPlaceholder title="Settings" />} />
          <Route path="notifications" element={<HiringManagerPlaceholder title="Notifications" />} />
        </Route>

        {/* Admin Routes - AI Explainability Dashboard */}
        <Route
          path="/admin/ai-explainability"
          element={
            <Suspense fallback={<Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}><Typography>Loading...</Typography></Box>}>
              <AIExplainabilityDashboard />
            </Suspense>
          }
        />

        {/* Catch-all route - redirect to landing */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
