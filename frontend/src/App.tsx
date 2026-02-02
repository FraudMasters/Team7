import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Box } from '@mui/material';
import Layout from '@components/Layout';
import LoadingSpinner from '@components/LoadingSpinner';
import ErrorBoundary from '@components/ErrorBoundary';

// Lazy load all route components for code splitting and better performance
const HomePage = lazy(() => import('@pages/Home'));
const UploadPage = lazy(() => import('@pages/Upload'));
const BatchUploadPage = lazy(() => import('@pages/BatchUpload'));
const ResultsPage = lazy(() => import('@pages/Results'));
const ComparePage = lazy(() => import('@pages/Compare'));
const CompareVacancyPage = lazy(() => import('@pages/CompareVacancy'));
const AdminSynonymsPage = lazy(() => import('@pages/AdminSynonyms'));
const AdminAnalyticsPage = lazy(() => import('@pages/AdminAnalytics'));
const AnalyticsDashboardPage = lazy(() => import('@pages/AnalyticsDashboard'));
const VacancyListPage = lazy(() => import('@pages/VacancyList'));
const CreateVacancyPage = lazy(() => import('@pages/CreateVacancy'));
const VacancyDetailsPage = lazy(() => import('@pages/VacancyDetails'));
const ApplicationsPage = lazy(() => import('@pages/Applications'));
const ResumeDatabasePage = lazy(() => import('@pages/ResumeDatabase'));
const CandidateSearchPage = lazy(() => import('@pages/CandidateSearch'));
const CandidatesKanbanPage = lazy(() => import('@pages/CandidatesKanbanPage'));
const RecruiterDashboardPage = lazy(() => import('@pages/RecruiterDashboard'));
const SkillGapAnalysisPage = lazy(() => import('@pages/SkillGapAnalysis'));
const WeightCustomizationPage = lazy(() => import('@pages/WeightCustomization'));
const IndustryTaxonomyManager = lazy(() => import('@components/IndustryTaxonomyManager'));
const TaxonomyAnalytics = lazy(() => import('@components/TaxonomyAnalytics'));
const PublicTaxonomyBrowser = lazy(() => import('@components/PublicTaxonomyBrowser'));
const LoadingSpinnerDemoPage = lazy(() => import('@pages/LoadingSpinnerDemo'));

/**
 * Loading fallback components for different page types
 *
 * Provides appropriate skeleton screens based on the content being loaded,
 * improving perceived performance and user experience.
 */

// Home page loading state
const HomeLoading = () => <LoadingSpinner variant="page" count={6} />;

// Vacancy list loading state
const VacancyListLoading = () => (
  <LoadingSpinner variant="cards" count={9} message="Loading vacancies..." />
);

// Form pages loading state (create, upload, etc.)
const FormLoading = ({ message = "Loading form..." }: { message?: string }) => (
  <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
    <LoadingSpinner variant="form" message={message} />
  </Box>
);

// Dashboard pages loading state
const DashboardLoading = () => (
  <LoadingSpinner variant="page" count={6} message="Loading dashboard..." />
);

// Results/comparison pages loading state
const ResultsLoading = () => (
  <LoadingSpinner variant="page" count={4} message="Loading results..." />
);

// List/table pages loading state (applications, resumes, candidates)
const ListLoading = ({ count = 10 }: { count?: number }) => (
  <LoadingSpinner variant="list" count={count} />
);

// Admin pages loading state
const AdminLoading = ({ message = "Loading..." }: { message?: string }) => (
  <LoadingSpinner variant="page" count={6} message={message} />
);

/**
 * Main App Component
 *
 * Sets up React Router with all application routes.
 * Uses lazy loading with React.lazy() for code splitting and better performance.
 * All route components are wrapped in Suspense with loading fallbacks.
 * Uses the Layout component to provide consistent navigation and structure.
 */
function App() {
  return (
    <BrowserRouter>
      <ErrorBoundary>
        <Suspense fallback={<DashboardLoading />}>
          <Routes>
          {/* Root route with Layout */}
          <Route path="/" element={<Layout />}>
            {/* Default home page */}
            <Route
              index
              element={
                <Suspense fallback={<HomeLoading />}>
                  <HomePage />
                </Suspense>
              }
            />

            {/* Legacy routes - kept for compatibility */}
            <Route
              path="upload"
              element={
                <Suspense fallback={<FormLoading message="Uploading resume..." />}>
                  <UploadPage />
                </Suspense>
              }
            />
            <Route
              path="results/:id"
              element={
                <Suspense fallback={<ResultsLoading />}>
                  <ResultsPage />
                </Suspense>
              }
            />
            <Route
              path="compare/:resumeId/:vacancyId"
              element={
                <Suspense fallback={<ResultsLoading />}>
                  <ComparePage />
                </Suspense>
              }
            />
            <Route
              path="compare-vacancy/:vacancyId"
              element={
                <Suspense fallback={<ResultsLoading />}>
                  <CompareVacancyPage />
                </Suspense>
              }
            />

            {/* Job Seeker Module Routes */}
            <Route path="jobs">
              <Route
                index
                element={
                  <Suspense fallback={<VacancyListLoading />}>
                    <VacancyListPage />
                  </Suspense>
                }
              />
              <Route
                path="upload"
                element={
                  <Suspense fallback={<FormLoading message="Uploading resume..." />}>
                    <UploadPage />
                  </Suspense>
                }
              />
              <Route
                path="batch-upload"
                element={
                  <Suspense fallback={<FormLoading message="Loading batch upload..." />}>
                    <BatchUploadPage />
                  </Suspense>
                }
              />
              <Route
                path="results/:id"
                element={
                  <Suspense fallback={<ResultsLoading />}>
                    <ResultsPage />
                  </Suspense>
                }
              />
              <Route
                path="applications"
                element={
                  <Suspense fallback={<ListLoading count={8} />}>
                    <ApplicationsPage />
                  </Suspense>
                }
              />
            </Route>

            {/* Recruiter Module Routes */}
            <Route path="recruiter">
              <Route
                index
                element={
                  <Suspense fallback={<DashboardLoading />}>
                    <RecruiterDashboardPage />
                  </Suspense>
                }
              />
              <Route path="vacancies">
                <Route
                  index
                  element={
                    <Suspense fallback={<VacancyListLoading />}>
                      <VacancyListPage />
                    </Suspense>
                  }
                />
                <Route
                  path="create"
                  element={
                    <Suspense fallback={<FormLoading message="Loading vacancy form..." />}>
                      <CreateVacancyPage />
                    </Suspense>
                  }
                />
                <Route
                  path=":id"
                  element={
                    <Suspense fallback={<DashboardLoading />}>
                      <VacancyDetailsPage />
                    </Suspense>
                  }
                />
              </Route>
              <Route
                path="resumes"
                element={
                  <Suspense fallback={<ListLoading count={12} />}>
                    <ResumeDatabasePage />
                  </Suspense>
                }
              />
              <Route
                path="candidates"
                element={
                  <Suspense fallback={<LoadingSpinner variant="cards" count={8} message="Loading candidates..." />}>
                    <CandidatesKanbanPage />
                  </Suspense>
                }
              />
              <Route
                path="search"
                element={
                  <Suspense fallback={<ListLoading count={10} />}>
                    <CandidateSearchPage />
                  </Suspense>
                }
              />
              <Route
                path="analytics"
                element={
                  <Suspense fallback={<DashboardLoading />}>
                    <AnalyticsDashboardPage />
                  </Suspense>
                }
              />
              <Route
                path="skill-gap"
                element={
                  <Suspense fallback={<DashboardLoading />}>
                    <SkillGapAnalysisPage />
                  </Suspense>
                }
              />
              <Route
                path="weights"
                element={
                  <Suspense fallback={<FormLoading message="Loading customization..." />}>
                    <WeightCustomizationPage />
                  </Suspense>
                }
              />
            </Route>

            {/* Admin pages */}
            <Route path="admin" element={<Navigate to="/admin/synonyms" replace />} />
            <Route
              path="admin/synonyms"
              element={
                <Suspense fallback={<AdminLoading message="Loading synonym manager..." />}>
                  <AdminSynonymsPage />
                </Suspense>
              }
            />
            <Route
              path="admin/analytics"
              element={
                <Suspense fallback={<AdminLoading message="Loading analytics..." />}>
                  <AdminAnalyticsPage />
                </Suspense>
              }
            />
            <Route
              path="admin/taxonomies"
              element={
                <Suspense fallback={<AdminLoading message="Loading taxonomy manager..." />}>
                  <IndustryTaxonomyManager />
                </Suspense>
              }
            />
            <Route
              path="admin/taxonomy-analytics"
              element={
                <Suspense fallback={<AdminLoading message="Loading taxonomy analytics..." />}>
                  <TaxonomyAnalytics />
                </Suspense>
              }
            />
            <Route
              path="admin/public-taxonomies"
              element={
                <Suspense fallback={<AdminLoading message="Loading public taxonomies..." />}>
                  <PublicTaxonomyBrowser />
                </Suspense>
              }
            />
            <Route
              path="demo/loading-spinner"
              element={
                <Suspense fallback={<AdminLoading message="Loading demo..." />}>
                  <LoadingSpinnerDemoPage />
                </Suspense>
              }
            />

            {/* Analytics dashboard */}
            <Route
              path="analytics"
              element={
                <Suspense fallback={<DashboardLoading />}>
                  <AnalyticsDashboardPage />
                </Suspense>
              }
            />

            {/* Catch-all route - redirect to home */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </Suspense>
    </ErrorBoundary>
    </BrowserRouter>
  );
}

export default App;
