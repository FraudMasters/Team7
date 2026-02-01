import React from 'react';
import ReactDOM from 'react-dom/client';
import { ThemeProvider as MuiThemeProvider, CssBaseline } from '@mui/material';
import { LanguageProvider } from './contexts/LanguageContext';
import { ThemeProvider, useThemeContext } from './contexts/ThemeContext';
import QueryProvider from './providers/QueryProvider';
import ErrorBoundary from './components/ErrorBoundary';
import App from './App';
import './index.css';
import './i18n'; // Initialize i18n

/**
 * Inner App Component that uses the theme context
 * This allows us to use useThemeContext inside the provider tree
 */
const AppWithTheme: React.FC = () => {
  const { theme } = useThemeContext();

  return (
    <MuiThemeProvider theme={theme}>
      <CssBaseline />
      <App />
    </MuiThemeProvider>
  );
};

ReactDOM.createRoot(document.getElementById('root')!).render(
  <ErrorBoundary
    onError={(error, errorInfo) => {
      // Log error details for debugging
      console.error('Application error caught by ErrorBoundary:', {
        error: error.toString(),
        componentStack: errorInfo.componentStack,
      });

      // In production, you could send this to an error tracking service
      // Example: Sentry.captureException(error, { extra: errorInfo });
    }}
  >
    <React.StrictMode>
      <LanguageProvider>
        <ThemeProvider>
          <QueryProvider>
            <AppWithTheme />
          </QueryProvider>
        </ThemeProvider>
      </LanguageProvider>
    </React.StrictMode>
  </ErrorBoundary>
);
