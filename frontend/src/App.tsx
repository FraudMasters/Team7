import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from '@components/Layout';
import HomePage from '@pages/Home';
import UploadPage from '@pages/Upload';
import ResultsPage from '@pages/Results';
import ComparePage from '@pages/Compare';
import CompareVacancyPage from '@pages/CompareVacancy';
import AdminSynonymsPage from '@pages/AdminSynonyms';
import AdminAnalyticsPage from '@pages/AdminAnalytics';

/**
 * Main App Component
 *
 * Sets up React Router with all application routes.
 * Uses the Layout component to provide consistent navigation and structure.
 */
function App() {
  return (
    <BrowserRouter>
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

          {/* Catch-all route - redirect to home */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
