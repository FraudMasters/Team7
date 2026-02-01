import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from '@components/Layout';
import LoadingSpinner from '@components/LoadingSpinner';

// Lazy load all page components for code splitting and better performance
const HomePage = lazy(() => import('@pages/Home'));
const UploadPage = lazy(() => import('@pages/Upload'));
const ResultsPage = lazy(() => import('@pages/Results'));
const ComparePage = lazy(() => import('@pages/Compare'));
const CompareVacancyPage = lazy(() => import('@pages/CompareVacancy'));
const AdminSynonymsPage = lazy(() => import('@pages/AdminSynonyms'));
const AdminAnalyticsPage = lazy(() => import('@pages/AdminAnalytics'));
const AnalyticsDashboardPage = lazy(() => import('@pages/AnalyticsDashboard'));

/**
 * Loading fallback component for lazy-loaded routes
 */
const PageLoadingFallback = () => (
  <LoadingSpinner size={60} label="Loading page..." />
);

/**
 * Main App Component
 *
 * Sets up React Router with all application routes.
 * Uses React.lazy() for code splitting - each route is loaded on demand.
 * Uses the Layout component to provide consistent navigation and structure.
 *
 * Benefits of lazy loading:
 * - Smaller initial bundle size
 * - Faster initial page load
 * - Better performance on slow networks
 * - Code is loaded only when needed
 */
function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<PageLoadingFallback />}>
        <Routes>
          {/* Root route with Layout */}
          <Route path="/" element={<Layout />}>
            {/* Default home page */}
            <Route index element={<HomePage />} />

            {/* Resume upload page */}
            <Route path="upload" element={<UploadPage />} />

            {/* Analysis results page with dynamic ID parameter */}
            <Route path="results/:id" element={<ResultsPage />} />

            {/* Job comparison page with dynamic resume and vacancy ID parameters */}
            <Route path="compare/:resumeId/:vacancyId" element={<ComparePage />} />

            {/* Multi-resume comparison page for a specific vacancy */}
            <Route path="compare-vacancy/:vacancyId" element={<CompareVacancyPage />} />

            {/* Admin pages */}
            <Route path="admin" element={<Navigate to="/admin/synonyms" replace />} />
            <Route path="admin/synonyms" element={<AdminSynonymsPage />} />
            <Route path="admin/analytics" element={<AdminAnalyticsPage />} />

            {/* Analytics dashboard */}
            <Route path="analytics" element={<AnalyticsDashboardPage />} />

            {/* Catch-all route - redirect to home */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
