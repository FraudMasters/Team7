import React, { useEffect, useState, useRef } from 'react';
import ReactDOM from 'react-dom/client';
import { ThemeProvider as MuiThemeProvider, CssBaseline } from '@mui/material';
import { LanguageProvider } from './contexts/LanguageContext';
import { ThemeProvider, useThemeContext } from './contexts/ThemeContext';
import QueryProvider from './providers/QueryProvider';
import ErrorBoundary from './components/ErrorBoundary';
import App from './App';
import './index.css';
import './i18n'; // Initialize i18n

// Import variable fonts
import '@fontsource-variable/inter';
import '@fontsource/space-grotesk';

// Import service worker registration for PWA
// This is a virtual module provided by vite-plugin-pwa
import { registerSW } from 'virtual:pwa-register';

/**
 * ServiceWorkerRegistration Component
 *
 * Handles Progressive Web App service worker registration and update lifecycle.
 * Registers the service worker on mount and manages update notifications.
 *
 * Features:
 * - Automatically registers service worker on app load
 * - Detects when a new service worker version is available
 * - Prompts user to refresh when updates are ready
 * - Handles registration errors gracefully
 * - Only active in production (disabled in development)
 *
 * Behavior:
 * - Service worker is registered automatically on component mount
 * - When a new version is detected, a refresh prompt is shown
 * - User can click "Reload" to activate the new version immediately
 * - If dismissed, the new version activates on next page load
 *
 * @example
 * ```tsx
 * // Placed in main.tsx to register SW on app startup
 * <ServiceWorkerRegistration />
 * ```
 */
const ServiceWorkerRegistration: React.FC = () => {
  const [showReload, setShowReload] = useState(false);
  const [waitingWorker, setWaitingWorker] = useState<ServiceWorker | null>(
    null
  );
  const registrationRef = useRef<ServiceWorkerRegistration | null>(null);

  /**
   * Register service worker and setup update handling
   *
   * Uses vite-plugin-pwa's registerSW function which provides:
   * - Automatic service worker registration
   * - Update detection via service worker lifecycle
   * - Callbacks for registration events
   */
  useEffect(() => {
    const updateSW = registerSW({
      /**
       * Handle service worker registration success
       */
      onRegistered(registration) {
        // Store registration for later use
        registrationRef.current = registration;

        // Periodically check for updates (every hour)
        if (registration) {
          setInterval(() => {
            registration.update();
          }, 60 * 60 * 1000);
        }
      },

      /**
       * Handle service worker registration error
       */
      onRegisterError(error) {
        // Only log in development, silently fail in production
        if (import.meta.env.DEV) {
          console.error('Service worker registration failed:', error);
        }
      },

      /**
       * Handle when a new service worker is ready
       *
       * This is called when a new version has been downloaded and is waiting
       * to be activated. We store the registration and show a reload prompt.
       */
      onNeedRefresh() {
        setShowReload(true);
        setWaitingWorker(
          registrationRef.current?.active ||
            navigator.serviceWorker.controller
        );
      },

      /**
       * Handle when offline content is ready
       *
       * Called when the service worker has cached all necessary content
       * for offline functionality.
       */
      onOfflineReady() {
        // Optionally show a notification that app works offline
        if (import.meta.env.DEV) {
          console.info('Application ready to work offline');
        }
      },
    });

    // Cleanup function to unregister callbacks
    return () => {
      // Note: unregisterSW function is returned by registerSW
      // We don't want to unregister on unmount, just cleanup callbacks
    };
  }, []);

  /**
   * Handle reload button click
   *
   * Skips waiting for the new service worker to activate and reloads the page
   * to apply the update immediately.
   */
  const handleReload = () => {
    if (waitingWorker) {
      // Send skip waiting message to the waiting service worker
      waitingWorker.postMessage({ type: 'SKIP_WAITING' });
    }

    // Reload the page to apply updates
    setShowReload(false);
    window.location.reload();
  };

  /**
   * Handle close button click
   *
   * Dismisses the reload prompt. The new service worker will activate
   * automatically on the next page load.
   */
  const handleClose = () => {
    setShowReload(false);
  };

  // Don't render if no update is available
  if (!showReload) {
    return null;
  }

  return (
    <div
      style={{
        position: 'fixed',
        bottom: 16,
        right: 16,
        left: 16,
        maxWidth: 400,
        margin: '0 auto',
        zIndex: 9999,
      }}
    >
      <div
        style={{
          backgroundColor: '#1976d2',
          color: 'white',
          padding: '16px',
          borderRadius: '8px',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '12px',
          flexWrap: 'wrap',
        }}
      >
        <div style={{ flex: 1, minWidth: '200px' }}>
          <div style={{ fontWeight: 600, marginBottom: '4px' }}>
            New Version Available
          </div>
          <div style={{ fontSize: '14px', opacity: 0.9 }}>
            A new version of the app is ready. Click reload to update.
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={handleClose}
            style={{
              backgroundColor: 'transparent',
              border: '1px solid rgba(255, 255, 255, 0.5)',
              color: 'white',
              padding: '8px 16px',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: 500,
            }}
          >
            Later
          </button>
          <button
            onClick={handleReload}
            style={{
              backgroundColor: 'white',
              border: 'none',
              color: '#1976d2',
              padding: '8px 16px',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: 600,
            }}
          >
            Reload
          </button>
        </div>
      </div>
    </div>
  );
};

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
      <ServiceWorkerRegistration />
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
