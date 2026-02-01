/**
 * Performance Tracker
 *
 * Tracks API performance metrics including timing, status codes, and response sizes.
 * Provides insights into API call patterns and performance bottlenecks.
 *
 * @module utils/performanceTracker
 *
 * @example
 * ```ts
 * import { trackApiCall, getMetrics, logMetricsSummary } from '@/utils/performanceTracker';
 *
 * // Track an API call
 * trackApiCall({
 *   endpoint: '/api/candidates',
 *   method: 'GET',
 *   duration: 245,
 *   status: 200,
 *   success: true,
 * });
 *
 * // Get all metrics
 * const metrics = getMetrics();
 *
 * // Log summary to console
 * logMetricsSummary();
 * ```
 */

/**
 * API call metric entry
 */
interface ApiMetric {
  /**
   * API endpoint path
   */
  endpoint: string;

  /**
   * HTTP method (GET, POST, PUT, DELETE)
   */
  method: string;

  /**
   * Request duration in milliseconds
   */
  duration: number;

  /**
   * HTTP status code
   */
  status: number;

  /**
   * Whether the request was successful
   */
  success: boolean;

  /**
   * Timestamp of the request
   */
  timestamp: number;

  /**
   * Optional error message if request failed
   */
  error?: string;

  /**
   * Optional response size in bytes
   */
  responseSize?: number;
}

/**
 * Performance statistics summary
 */
interface PerformanceStats {
  /**
   * Total number of API calls tracked
   */
  totalCalls: number;

  /**
   * Number of successful calls
   */
  successfulCalls: number;

  /**
   * Number of failed calls
   */
  failedCalls: number;

  /**
   * Average request duration in milliseconds
   */
  averageDuration: number;

  /**
   * Minimum request duration in milliseconds
   */
  minDuration: number;

  /**
   * Maximum request duration in milliseconds
   */
  maxDuration: number;

  /**
   * 95th percentile duration in milliseconds
   */
  p95Duration: number;

  /**
   * Slowest endpoint (by average duration)
   */
  slowestEndpoint: {
    endpoint: string;
    averageDuration: number;
    callCount: number;
  } | null;

  /**
   * Most frequently called endpoint
   */
  mostCalledEndpoint: {
    endpoint: string;
    callCount: number;
    averageDuration: number;
  } | null;
}

/**
 * In-memory storage for API metrics
 * Limited to most recent 1000 calls to prevent memory issues
 */
const MAX_METRICS = 1000;
const metrics: ApiMetric[] = [];

/**
 * Flag to enable/disable logging
 * In production, this can be set to false via environment variable
 */
const ENABLE_LOGGING = import.meta.env.VITE_ENABLE_PERFORMANCE_LOGGING !== 'false';

/**
 * Track an API call metric
 *
 * @param metric - Metric data to track
 *
 * @example
 * ```ts
 * trackApiCall({
 *   endpoint: '/api/candidates',
 *   method: 'GET',
 *   duration: 245,
 *   status: 200,
 *   success: true,
 * });
 * ```
 */
export function trackApiCall(metric: ApiMetric): void {
  // Add metric to storage
  metrics.push(metric);

  // Keep only the most recent metrics
  if (metrics.length > MAX_METRICS) {
    metrics.shift();
  }

  // Log in development mode
  if (ENABLE_LOGGING && import.meta.env.DEV) {
    const statusIcon = metric.success ? '✓' : '✗';
    const durationColor = metric.duration > 1000 ? '\x1b[31m' : metric.duration > 500 ? '\x1b[33m' : '\x1b[32m';
    const reset = '\x1b[0m';

    console.log(
      `[API Performance] ${statusIcon} ${metric.method} ${metric.endpoint} - ${durationColor}${metric.duration}ms${reset} (${metric.status})`
    );
  }
}

/**
 * Get all stored metrics
 *
 * @returns Array of all stored metrics
 *
 * @example
 * ```ts
 * const allMetrics = getMetrics();
 * console.log(`Tracked ${allMetrics.length} API calls`);
 * ```
 */
export function getMetrics(): ApiMetric[] {
  return [...metrics];
}

/**
 * Get metrics filtered by endpoint
 *
 * @param endpoint - Endpoint path to filter by
 * @returns Array of metrics for the specified endpoint
 *
 * @example
 * ```ts
 * const candidateMetrics = getMetricsByEndpoint('/api/candidates');
 * console.log(`Average duration: ${getAverageDuration(candidateMetrics)}ms`);
 * ```
 */
export function getMetricsByEndpoint(endpoint: string): ApiMetric[] {
  return metrics.filter((m) => m.endpoint === endpoint);
}

/**
 * Get metrics filtered by success status
 *
 * @param success - Whether to get successful or failed metrics
 * @returns Array of metrics matching the success status
 *
 * @example
 * ```ts
 * const failedMetrics = getMetricsBySuccess(false);
 * console.log(`Failed calls: ${failedMetrics.length}`);
 * ```
 */
export function getMetricsBySuccess(success: boolean): ApiMetric[] {
  return metrics.filter((m) => m.success === success);
}

/**
 * Get metrics filtered by HTTP method
 *
 * @param method - HTTP method to filter by
 * @returns Array of metrics for the specified method
 *
 * @example
 * ```ts
 * const postMetrics = getMetricsByMethod('POST');
 * console.log(`POST calls: ${postMetrics.length}`);
 * ```
 */
export function getMetricsByMethod(method: string): ApiMetric[] {
  return metrics.filter((m) => m.method === method);
}

/**
 * Calculate performance statistics from stored metrics
 *
 * @returns Performance statistics summary
 *
 * @example
 * ```ts
 * const stats = getPerformanceStats();
 * console.log(`Average duration: ${stats.averageDuration}ms`);
 * console.log(`Success rate: ${(stats.successfulCalls / stats.totalCalls * 100).toFixed(1)}%`);
 * ```
 */
export function getPerformanceStats(): PerformanceStats {
  if (metrics.length === 0) {
    return {
      totalCalls: 0,
      successfulCalls: 0,
      failedCalls: 0,
      averageDuration: 0,
      minDuration: 0,
      maxDuration: 0,
      p95Duration: 0,
      slowestEndpoint: null,
      mostCalledEndpoint: null,
    };
  }

  const successfulCalls = metrics.filter((m) => m.success).length;
  const failedCalls = metrics.filter((m) => !m.success).length;
  const durations = metrics.map((m) => m.duration).sort((a, b) => a - b);

  const averageDuration = durations.reduce((sum, d) => sum + d, 0) / durations.length;
  const minDuration = durations[0];
  const maxDuration = durations[durations.length - 1];

  // Calculate 95th percentile
  const p95Index = Math.floor(durations.length * 0.95);
  const p95Duration = durations[p95Index];

  // Group by endpoint
  const endpointGroups: Record<string, ApiMetric[]> = {};
  metrics.forEach((m) => {
    if (!endpointGroups[m.endpoint]) {
      endpointGroups[m.endpoint] = [];
    }
    endpointGroups[m.endpoint].push(m);
  });

  // Find slowest endpoint
  let slowestEndpoint: PerformanceStats['slowestEndpoint'] = null;
  Object.entries(endpointGroups).forEach(([endpoint, endpointMetrics]) => {
    const avgDuration = endpointMetrics.reduce((sum, m) => sum + m.duration, 0) / endpointMetrics.length;
    if (!slowestEndpoint || avgDuration > slowestEndpoint.averageDuration) {
      slowestEndpoint = {
        endpoint,
        averageDuration: Math.round(avgDuration),
        callCount: endpointMetrics.length,
      };
    }
  });

  // Find most called endpoint
  let mostCalledEndpoint: PerformanceStats['mostCalledEndpoint'] = null;
  Object.entries(endpointGroups).forEach(([endpoint, endpointMetrics]) => {
    const avgDuration = endpointMetrics.reduce((sum, m) => sum + m.duration, 0) / endpointMetrics.length;
    if (!mostCalledEndpoint || endpointMetrics.length > mostCalledEndpoint.callCount) {
      mostCalledEndpoint = {
        endpoint,
        callCount: endpointMetrics.length,
        averageDuration: Math.round(avgDuration),
      };
    }
  });

  return {
    totalCalls: metrics.length,
    successfulCalls,
    failedCalls,
    averageDuration: Math.round(averageDuration),
    minDuration,
    maxDuration,
    p95Duration,
    slowestEndpoint,
    mostCalledEndpoint,
  };
}

/**
 * Calculate average duration for an array of metrics
 *
 * @param metricArray - Array of metrics to calculate average for
 * @returns Average duration in milliseconds
 *
 * @example
 * ```ts
 * const candidateMetrics = getMetricsByEndpoint('/api/candidates');
 * const avgDuration = getAverageDuration(candidateMetrics);
 * ```
 */
export function getAverageDuration(metricArray: ApiMetric[]): number {
  if (metricArray.length === 0) return 0;
  const total = metricArray.reduce((sum, m) => sum + m.duration, 0);
  return Math.round(total / metricArray.length);
}

/**
 * Clear all stored metrics
 *
 * @example
 * ```ts
 * clearMetrics();
 * console.log('All metrics cleared');
 * ```
 */
export function clearMetrics(): void {
  metrics.length = 0;
  if (ENABLE_LOGGING) {
    console.log('[API Performance] Metrics cleared');
  }
}

/**
 * Log a summary of performance metrics to console
 *
 * @example
 * ```ts
 * logMetricsSummary();
 * // Output:
 * // [API Performance Summary]
 * // Total calls: 45
 * // Successful: 42 (93.3%)
 * // Failed: 3 (6.7%)
 * // Average duration: 245ms
 * // P95 duration: 612ms
 * ```
 */
export function logMetricsSummary(): void {
  if (!ENABLE_LOGGING) return;

  const stats = getPerformanceStats();

  console.group('[API Performance Summary]');

  if (stats.totalCalls === 0) {
    console.log('No metrics recorded yet');
    console.groupEnd();
    return;
  }

  console.log(`Total calls: ${stats.totalCalls}`);
  console.log(
    `Successful: ${stats.successfulCalls} (${((stats.successfulCalls / stats.totalCalls) * 100).toFixed(1)}%)`
  );
  console.log(
    `Failed: ${stats.failedCalls} (${((stats.failedCalls / stats.totalCalls) * 100).toFixed(1)}%)`
  );
  console.log(`Average duration: ${stats.averageDuration}ms`);
  console.log(`Min duration: ${stats.minDuration}ms`);
  console.log(`Max duration: ${stats.maxDuration}ms`);
  console.log(`P95 duration: ${stats.p95Duration}ms`);

  if (stats.slowestEndpoint) {
    console.log(
      `Slowest endpoint: ${stats.slowestEndpoint.endpoint} (${stats.slowestEndpoint.averageDuration}ms avg, ${stats.slowestEndpoint.callCount} calls)`
    );
  }

  if (stats.mostCalledEndpoint) {
    console.log(
      `Most called: ${stats.mostCalledEndpoint.endpoint} (${stats.mostCalledEndpoint.callCount} calls, ${stats.mostCalledEndpoint.averageDuration}ms avg)`
    );
  }

  console.groupEnd();
}

/**
 * Log metrics grouped by endpoint
 *
 * Shows detailed statistics for each endpoint
 *
 * @example
 * ```ts
 * logMetricsByEndpoint();
 * // Output:
 * // [API Performance by Endpoint]
 * // GET /api/candidates
 * //   Calls: 15
 * //   Avg: 180ms
 * //   Min: 120ms
 * //   Max: 450ms
 * ```
 */
export function logMetricsByEndpoint(): void {
  if (!ENABLE_LOGGING) return;

  const endpointGroups: Record<string, ApiMetric[]> = {};
  metrics.forEach((m) => {
    if (!endpointGroups[m.endpoint]) {
      endpointGroups[m.endpoint] = [];
    }
    endpointGroups[m.endpoint].push(m);
  });

  console.group('[API Performance by Endpoint]');

  Object.entries(endpointGroups).forEach(([endpoint, endpointMetrics]) => {
    const durations = endpointMetrics.map((m) => m.duration).sort((a, b) => a - b);
    const avgDuration = Math.round(
      endpointMetrics.reduce((sum, m) => sum + m.duration, 0) / endpointMetrics.length
    );
    const successRate =
      (endpointMetrics.filter((m) => m.success).length / endpointMetrics.length) * 100;

    console.groupCollapsed(`${endpointMetrics[0].method} ${endpoint}`);
    console.log(`Calls: ${endpointMetrics.length}`);
    console.log(`Success rate: ${successRate.toFixed(1)}%`);
    console.log(`Avg: ${avgDuration}ms`);
    console.log(`Min: ${durations[0]}ms`);
    console.log(`Max: ${durations[durations.length - 1]}ms`);
    console.groupEnd();
  });

  console.groupEnd();
}

/**
 * Export metrics as JSON for analysis
 *
 * @returns JSON string of all metrics
 *
 * @example
 * ```ts
 * const jsonData = exportMetricsAsJson();
 * console.log(jsonData);
 * ```
 */
export function exportMetricsAsJson(): string {
  return JSON.stringify(metrics, null, 2);
}

/**
 * Get recent metrics within a time window
 *
 * @param milliseconds - Time window in milliseconds (default: 5 minutes)
 * @returns Array of recent metrics
 *
 * @example
 * ```ts
 * const recentMetrics = getRecentMetrics(60000); // Last minute
 * console.log(`Recent calls: ${recentMetrics.length}`);
 * ```
 */
export function getRecentMetrics(milliseconds: number = 5 * 60 * 1000): ApiMetric[] {
  const cutoff = Date.now() - milliseconds;
  return metrics.filter((m) => m.timestamp >= cutoff);
}
