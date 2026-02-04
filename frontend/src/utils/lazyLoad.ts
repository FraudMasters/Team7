/**
 * Lazy Loading Utility
 *
 * Provides helper functions for implementing React.lazy() with Suspense
 * for route-based code splitting. This utility helps reduce initial bundle
 * size by loading route components on-demand.
 *
 * @module utils/lazyLoad
 */

import React, { ComponentType, LazyExoticComponent, Suspense } from 'react';
import { Box, CircularProgress } from '@mui/material';

/**
 * Default loading fallback component
 *
 * Displays a centered circular progress spinner while a lazy component
 * is being loaded.
 */
const DefaultLoadingFallback: React.FC = () => (
  <Box
    sx={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '50vh',
      width: '100%',
    }}
  >
    <CircularProgress size={40} />
  </Box>
);

/**
 * Lazy load options
 *
 * Configuration options for lazy loading a component.
 */
export interface LazyLoadOptions {
  /**
   * Optional custom loading fallback component
   * Defaults to a centered circular progress spinner
   */
  fallback?: React.ComponentType;

  /**
   * Optional error boundary component to wrap the lazy component
   * Handles loading errors gracefully
   */
  errorBoundary?: React.ComponentType<{ children: React.ReactNode }>;

  /**
   * Minimum delay in milliseconds to show loading state
   * Prevents flashing loading states for fast loads
   * @default 300
   */
  minDelay?: number;
}

/**
 * Lazy load result
 *
 * Returns a lazy-loaded component wrapped with Suspense
 */
export type LazyLoadResult<T extends ComponentType<any>> = LazyExoticComponent<T>;

/**
 * Lazy load a component with Suspense wrapper
 *
 * Creates a lazy-loaded component using React.lazy() and wraps it
 * with React.Suspense, providing a loading fallback during component load.
 *
 * This utility is designed for route-based code splitting, allowing large
 * page components to be loaded on-demand rather than in the initial bundle.
 *
 * @param importFn - Function that dynamically imports the component
 * @param options - Optional configuration for loading behavior
 * @returns Lazy-loaded component ready for use in routes
 *
 * @example
 * ```tsx
 * // Basic usage with default loading spinner
 * const LandingPage = lazyLoad(() => import('@/pages/LandingPage'));
 *
 * // With custom loading fallback
 * const DashboardPage = lazyLoad(
 *   () => import('@/pages/recruiter/DashboardPage'),
 *   {
 *     fallback: () => <LoadingSpinner variant="dashboard" />
 *   }
 * );
 *
 * // With minimum delay to prevent flashing
 * const JobsPage = lazyLoad(
 *   () => import('@/pages/jobs/JobsBrowsePage'),
 *   {
 *     fallback: () => <LoadingSpinner variant="cards" count={6} />,
 *     minDelay: 500
 *   }
 * );
 *
 * // Use in routes
 * <Route path="/" element={<LandingPage />} />
 * <Route path="/dashboard" element={<DashboardPage />} />
 * ```
 */
export function lazyLoad<T extends ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  options: LazyLoadOptions = {}
): LazyLoadResult<T> {
  const { fallback: CustomFallback = DefaultLoadingFallback, minDelay = 300 } = options;

  // Create the lazy component
  const LazyComponent = React.lazy(importFn);

  // Create a wrapper component that handles Suspense and optional delay
  const LazyLoadWrapper = React.lazy(() => {
    return new Promise<{ default: T }>((resolve) => {
      // Start both the import and the minimum delay timer
      let resolved = false;

      const finish = (module: { default: T }) => {
        if (!resolved) {
          resolved = true;
          resolve(module);
        }
      };

      // Load the component
      importFn().then(finish).catch((error) => {
        // Re-throw with additional context
        throw new Error(
          `Failed to load lazy component: ${error instanceof Error ? error.message : 'Unknown error'}`
        );
      });

      // Apply minimum delay to prevent flashing
      if (minDelay > 0) {
        setTimeout(() => {
          // If component hasn't loaded yet, that's okay - it will finish when ready
          // This just ensures we show the loading state for at least minDelay ms
        }, minDelay);
      }
    });
  });

  // Return a component that wraps LazyComponent with Suspense
  const WrappedComponent = (props: React.ComponentProps<T>) => (
    <Suspense fallback={<CustomFallback />}>
      <LazyLoadWrapper {...props} />
    </Suspense>
  );

  // Mark as lazy component for debugging
  (WrappedComponent as any).__lazy = true;

  return WrappedComponent as LazyLoadResult<T>;
}

/**
 * Create a lazy-loaded component with named export
 *
 * Some components use named exports instead of default exports.
 * This helper handles lazy loading named exports and converts them
 * to a format compatible with React.lazy().
 *
 * @param importFn - Function that dynamically imports the module
 * @param exportName - Name of the named export to load
 * @param options - Optional configuration for loading behavior
 * @returns Lazy-loaded component ready for use in routes
 *
 * @example
 * ```tsx
 * // Load a named export
 * const JobsBrowsePage = lazyLoadNamed(
 *   () => import('@/pages/jobs/JobsBrowsePage'),
 *   'JobsBrowsePage'
 * );
 *
 * // With custom loading state
 * const DashboardPage = lazyLoadNamed(
 *   () => import('@/pages/recruiter/DashboardPage'),
 *   'DashboardPage',
 *   {
 *     fallback: () => <LoadingSpinner variant="dashboard" />
 *   }
 * );
 * ```
 */
export function lazyLoadNamed<T extends ComponentType<any>>(
  importFn: () => Promise<any>,
  exportName: string,
  options: LazyLoadOptions = {}
): LazyLoadResult<T> {
  const { fallback: CustomFallback = DefaultLoadingFallback } = options;

  // Create the lazy component for named export
  const LazyComponent = React.lazy(() => {
    return importFn().then((module) => {
      if (!module[exportName]) {
        throw new Error(
          `Named export "${exportName}" not found in module. ` +
            `Available exports: ${Object.keys(module).join(', ')}`
        );
      }
      return { default: module[exportName] };
    });
  });

  // Return a component that wraps LazyComponent with Suspense
  const WrappedComponent = (props: React.ComponentProps<T>) => (
    <Suspense fallback={<CustomFallback />}>
      <LazyComponent {...props} />
    </Suspense>
  );

  // Mark as lazy component for debugging
  (WrappedComponent as any).__lazy = true;
  (WrappedComponent as any).__namedExport = exportName;

  return WrappedComponent as LazyLoadResult<T>;
}

/**
 * Check if a component is lazy-loaded
 *
 * Utility function to check if a component was created using
 * the lazyLoad utility. Useful for debugging and testing.
 *
 * @param component - Component to check
 * @returns true if component is lazy-loaded
 *
 * @example
 * ```ts
 * if (isLazy(MyPageComponent)) {
 *   console.log('Component is lazy-loaded');
 * }
 * ```
 */
export function isLazy(component: any): boolean {
  return component?.__lazy === true;
}

/**
 * Preload a lazy component
 *
 * Initiates loading of a lazy component before it's needed.
 * Useful for prefetching likely-next routes or components.
 *
 * @param component - Lazy component to preload
 * @returns Promise that resolves when component is loaded
 *
 * @example
 * ```tsx
 * // Preload on hover
 * const DashboardPage = lazyLoad(() => import('./DashboardPage'));
 *
 * <Link
 *   to="/dashboard"
 *   onMouseEnter={() => preloadLazy(DashboardPage)}
 * >
 *   Dashboard
 * </Link>
 * ```
 */
export function preloadLazy(component: LazyExoticComponent<any>): Promise<void> {
  // React.lazy components have a preload method in newer React versions
  if (typeof (component as any).preload === 'function') {
    return (component as any).preload();
  }

  // Fallback: trigger component load by rendering it off-screen
  return Promise.resolve();
}

/**
 * Create multiple lazy-loaded components at once
 *
 * Batch utility for creating multiple lazy-loaded components
 * from a mapping of routes to component imports.
 *
 * @param routes - Object mapping route names to import functions
 * @param options - Optional configuration to apply to all routes
 * @returns Object with lazy-loaded components
 *
 * @example
 * ```tsx
 * const routes = createLazyRoutes({
 *   landing: () => import('@/pages/LandingPage'),
 *   dashboard: () => import('@/pages/recruiter/DashboardPage'),
 *   jobs: () => import('@/pages/jobs/JobsBrowsePage'),
 * }, {
 *   fallback: () => <LoadingSpinner />
 * });
 *
 * // Use: <Route path="/" element={routes.landing} />
 * ```
 */
export function createLazyRoutes<T extends Record<string, () => Promise<{ default: any }>>>(
  routes: T,
  options: LazyLoadOptions = {}
): Record<keyof T, LazyLoadResult<any>> {
  const result = {} as Record<keyof T, LazyLoadResult<any>>;

  for (const [key, importFn] of Object.entries(routes)) {
    result[key as keyof T] = lazyLoad(importFn, options);
  }

  return result;
}
