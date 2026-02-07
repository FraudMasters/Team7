import React from 'react';
import { Box, CircularProgress, Typography, useTheme, alpha, SkeletonProps } from '@mui/material';
import LoadingSpinner, { LoadingSpinnerVariant } from './LoadingSpinner';

/**
 * Route context types
 *
 * Maps route patterns to appropriate loading states for better
 * perceived performance during lazy-loaded route transitions.
 */
export type PageLoaderContext =
  | 'landing'
  | 'auth'
  | 'jobs-browse'
  | 'jobs-detail'
  | 'jobs-apply'
  | 'jobs-saved'
  | 'jobs-applications'
  | 'assessment'
  | 'learning'
  | 'salary'
  | 'tips'
  | 'alerts'
  | 'settings'
  | 'profile'
  | 'upload'
  | 'results'
  | 'recommended'
  | 'dashboard'
  | 'candidates'
  | 'candidate-detail'
  | 'vacancies'
  | 'vacancy-form'
  | 'vacancy-detail'
  | 'search'
  | 'saved-searches'
  | 'compare'
  | 'skill-gap'
  | 'weights'
  | 'backups'
  | 'workflow'
  | 'analytics'
  | 'resume-database'
  | 'batch-upload';

/**
 * PageLoader component props
 */
export interface PageLoaderProps {
  /**
   * Route context to determine the appropriate loading variant
   * Maps to specific loading states for different page types
   */
  context?: PageLoaderContext;

  /**
   * Direct variant override (skips context mapping)
   * Use this when you need a specific LoadingSpinner variant
   */
  variant?: LoadingSpinnerVariant;

  /**
   * Optional custom loading message
   * Overrides the default message for the context
   */
  message?: string;

  /**
   * Minimum height for the loading container
   * Prevents layout shift during loading
   * @default '50vh'
   */
  minHeight?: string | number;

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

  /**
   * Additional className for custom styling
   */
  className?: string;

  /**
   * Custom skeleton props to pass to LoadingSpinner
   */
  skeletonProps?: SkeletonProps;
}

/**
 * Maps route contexts to appropriate LoadingSpinner variants
 */
const CONTEXT_VARIANT_MAP: Record<PageLoaderContext, LoadingSpinnerVariant> = {
  // Job seeker routes
  'landing': 'page',
  'auth': 'form',
  'jobs-browse': 'cards',
  'jobs-detail': 'vacancy-details',
  'jobs-apply': 'form',
  'jobs-saved': 'cards',
  'jobs-applications': 'list',
  'assessment': 'analysis',
  'learning': 'cards',
  'salary': 'table',
  'tips': 'cards',
  'alerts': 'list',
  'settings': 'form',
  'profile': 'form',
  'upload': 'upload',
  'results': 'analysis',
  'recommended': 'cards',

  // Recruiter routes
  'dashboard': 'dashboard',
  'candidates': 'candidate-search',
  'candidate-detail': 'form',
  'vacancies': 'cards',
  'vacancy-form': 'form',
  'vacancy-detail': 'vacancy-details',
  'search': 'candidate-search',
  'saved-searches': 'list',
  'compare': 'table',
  'skill-gap': 'analysis',
  'weights': 'form',
  'backups': 'list',
  'workflow': 'list',
  'analytics': 'dashboard',
  'resume-database': 'candidate-search',
  'batch-upload': 'upload',
} as const;

/**
 * Default loading messages for each context
 */
const CONTEXT_MESSAGES: Partial<Record<PageLoaderContext, string>> = {
  'landing': 'Loading...',
  'jobs-browse': 'Finding opportunities...',
  'jobs-detail': 'Loading vacancy details...',
  'jobs-apply': 'Preparing application...',
  'upload': 'Preparing upload...',
  'results': 'Analyzing resume...',
  'dashboard': 'Loading dashboard...',
  'candidates': 'Searching candidates...',
  'vacancies': 'Loading vacancies...',
  'analytics': 'Preparing analytics...',
  'resume-database': 'Searching resume database...',
  'batch-upload': 'Preparing batch upload...',
};

/**
 * PageLoader Component
 *
 * A context-aware loading component designed specifically for route-level
 * lazy loading. It automatically selects the appropriate LoadingSpinner
 * variant based on the route context, providing users with meaningful
 * loading states that match the content being loaded.
 *
 * This component is intended to be used as the fallback for React.Suspense
 * when implementing route-based code splitting.
 *
 * @example
 * ```tsx
 * // Use with lazyLoad utility
 * const DashboardPage = lazyLoad(
 *   () => import('@/pages/recruiter/DashboardPage'),
 *   {
 *     fallback: () => <PageLoader context="dashboard" />
 *   }
 * );
 *
 * // Direct Suspense usage
 * <Suspense fallback={<PageLoader context="jobs-browse" />}>
 *   <JobsBrowsePage />
 * </Suspense>
 *
 * // With custom message
 * <PageLoader context="upload" message="Uploading your resume..." />
 *
 * // With progress indicator
 * <PageLoader context="analytics" showProgress />
 *
 * // Direct variant override
 * <PageLoader variant="spinner" message="Loading..." />
 *
 * // Custom minimum height
 * <PageLoader context="vacancy-detail" minHeight="80vh" />
 * ```
 */
const PageLoader: React.FC<PageLoaderProps> = ({
  context = 'landing',
  variant,
  message,
  minHeight = '50vh',
  showProgress = false,
  progressSize = 40,
  className,
  skeletonProps,
}) => {
  const theme = useTheme();

  // Determine which variant to use
  const loadingVariant: LoadingSpinnerVariant = variant || CONTEXT_VARIANT_MAP[context];

  // Get default message for context, or use custom message
  const loadingMessage = message !== undefined ? message : CONTEXT_MESSAGES[context];

  // If showProgress is enabled, render a centered spinner with optional message
  if (showProgress) {
    return (
      <Box
        className={className}
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight,
          width: '100%',
          p: 3,
        }}
      >
        <CircularProgress size={progressSize} sx={{ mb: loadingMessage ? 2 : 0 }} />
        {loadingMessage && (
          <Typography
            variant="body2"
            color="text.secondary"
            align="center"
            sx={{ maxWidth: 400 }}
          >
            {loadingMessage}
          </Typography>
        )}
      </Box>
    );
  }

  // Otherwise, use the LoadingSpinner with the context-appropriate variant
  return (
    <Box
      className={className}
      sx={{
        minHeight,
        width: '100%',
        bgcolor: alpha(theme.palette.background.default, 0.5),
      }}
    >
      <LoadingSpinner
        variant={loadingVariant}
        message={loadingMessage}
        skeletonProps={skeletonProps}
      />
    </Box>
  );
};

export default PageLoader;
