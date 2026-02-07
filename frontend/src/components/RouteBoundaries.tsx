import React, { Suspense, ReactNode } from 'react';
import ErrorBoundary from './ErrorBoundary';
import PageLoader, { PageLoaderContext } from './PageLoader';

/**
 * Props for RouteBoundaries component
 */
export interface RouteBoundariesProps {
  /**
   * Child components to be wrapped by route boundaries
   * Typically a lazy-loaded route component
   */
  children: ReactNode;

  /**
   * Route context to determine the appropriate loading state
   * Maps to specific PageLoader variants for different page types
   *
   * @example
   * 'dashboard' - Shows dashboard skeleton
   * 'jobs-browse' - Shows card skeletons
   * 'vacancy-form' - Shows form skeleton
   */
  context?: PageLoaderContext;

  /**
   * Optional custom loading fallback component
   * Overrides the PageLoader for this route
   * Use this when you need a completely custom loading state
   *
   * @example
   * fallback={<CustomLoadingSpinner />}
   */
  fallback?: ReactNode;

  /**
   * Custom error boundary fallback component
   * Overrides the default error fallback UI
   * Use this for route-specific error handling
   *
   * @example
   * errorFallback={<CustomErrorMessage />}
   */
  errorFallback?: ReactNode;

  /**
   * Custom error handler function
   * Called when an error is caught in the route
   * Use this for custom error logging or reporting
   *
   * @example
   * onError={(error, errorInfo) => {
   *   logErrorToService(error, errorInfo);
   * }}
   */
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;

  /**
   * Whether to show error details (stack trace, component stack)
   * @default false (hide details in production)
   */
  showDetails?: boolean;

  /**
   * Minimum height for the loading container
   * Prevents layout shift during loading
   * @default '50vh'
   */
  minHeight?: string | number;

  /**
   * Optional custom loading message
   * Overrides the default message for the context
   *
   * @example
   * message="Loading your saved vacancies..."
   */
  message?: string;

  /**
   * Whether to show a progress indicator in addition to skeleton
   * @default false
   */
  showProgress?: boolean;

  /**
   * Size of progress indicator (when showProgress is true)
   * @default 40
   */
  progressSize?: number;
}

/**
 * RouteBoundaries Component
 *
 * A wrapper component that combines React.Suspense and ErrorBoundary to provide
 * robust loading and error handling for lazy-loaded route components.
 *
 * This component is designed specifically for route-level code splitting, where
 * each route is loaded on-demand. It ensures:
 *
 * 1. **Loading States**: Shows context-appropriate loading skeletons via PageLoader
 * 2. **Error Handling**: Catches and gracefully displays errors via ErrorBoundary
 * 3. **Performance**: Prevents layout shift with minimum height during loading
 * 4. **User Experience**: Provides meaningful feedback during route transitions
 *
 * @example
 * ```tsx
 * // Basic usage with context-aware loading
 * <RouteBoundaries context="dashboard">
 *   <DashboardPage />
 * </RouteBoundaries>
 *
 * // With lazy-loaded component
 * const DashboardPage = lazyLoad(() => import('@/pages/DashboardPage'));
 *
 * <RouteBoundaries context="dashboard">
 *   <DashboardPage />
 * </RouteBoundaries>
 *
 * // With custom loading message
 * <RouteBoundaries
 *   context="jobs-browse"
 *   message="Finding the best opportunities for you..."
 * >
 *   <JobsBrowsePage />
 * </RouteBoundaries>
 *
 * // With custom error handler
 * <RouteBoundaries
 *   context="upload"
 *   onError={(error, errorInfo) => {
 *     console.error('Upload route error:', error);
 *     trackError('upload_route_error', error);
 *   }}
 * >
 *   <UploadPage />
 * </RouteBoundaries>
 *
 * // With custom fallbacks
 * <RouteBoundaries
 *   context="analytics"
 *   fallback={<CustomAnalyticsLoader />}
 *   errorFallback={<CustomAnalyticsError />}
 * >
 *   <AnalyticsPage />
 * </RouteBoundaries>
 *
 * // With progress indicator for long-loading routes
 * <RouteBoundaries
 *   context="analytics"
 *   showProgress
 *   progressSize={60}
 *   message="Preparing your analytics dashboard..."
 * >
 *   <AnalyticsPage />
 * </RouteBoundaries>
 *
 * // In route configuration
 * const routes = [
 *   {
 *     path: '/dashboard',
 *     element: (
 *       <RouteBoundaries context="dashboard">
 *         <DashboardPage />
 *       </RouteBoundaries>
 *     )
 *   },
 *   {
 *     path: '/jobs',
 *     element: (
 *       <RouteBoundaries context="jobs-browse">
 *         <JobsBrowsePage />
 *       </RouteBoundaries>
 *     )
 *   },
 * ];
 * ```
 *
 * **Loading Behavior:**
 *
 * When a lazy-loaded component is being loaded:
 * - Suspense catches the promise and renders the fallback
 * - By default, PageLoader shows a context-appropriate skeleton
 * - Custom fallback can override the default PageLoader
 * - Minimum height prevents layout shift
 *
 * **Error Handling:**
 *
 * When an error occurs during rendering or loading:
 * - ErrorBoundary catches the error
 * - Default error UI shows with recovery options
 * - Custom errorFallback can override the default UI
 * - onError callback is invoked for custom error handling
 *
 * **Performance Considerations:**
 *
 * - Use context prop for automatic variant selection (recommended)
 * - Provide meaningful messages for better perceived performance
 * - Use showProgress for routes that typically take > 1 second
 * - Set appropriate minHeight to prevent layout shift
 *
 * **Accessibility:**
 *
 * - Loading states are announced to screen readers
 * - Error messages are accessible and actionable
 * - Recovery actions (refresh, go home) are keyboard-accessible
 */
const RouteBoundaries: React.FC<RouteBoundariesProps> = ({
  children,
  context = 'landing',
  fallback,
  errorFallback,
  onError,
  showDetails = false,
  minHeight = '50vh',
  message,
  showProgress = false,
  progressSize = 40,
}) => {
  // Determine which loading fallback to use
  const loadingFallback = fallback !== undefined
    ? fallback
    : (
      <PageLoader
        context={context}
        message={message}
        minHeight={minHeight}
        showProgress={showProgress}
        progressSize={progressSize}
      />
    );

  // ErrorBoundary props to pass through
  const errorBoundaryProps = {
    fallback: errorFallback,
    onError,
    showDetails,
  };

  return (
    <ErrorBoundary {...errorBoundaryProps}>
      <Suspense fallback={loadingFallback}>
        {children}
      </Suspense>
    </ErrorBoundary>
  );
};

export default RouteBoundaries;
