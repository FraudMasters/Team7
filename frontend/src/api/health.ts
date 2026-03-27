/**
 * Health Check API
 *
 * This module provides API functions for monitoring system health,
 * including service status checks, dependency graph information,
 * and component-level health details.
 *
 * @example
 * ```ts
 * import {
 *   getHealthStatus,
 *   getDetailedHealth,
 *   getReadyStatus,
 *   getDependencyGraph,
 *   getComponentHealth
 * } from '@/api/health';
 *
 * // Quick health check
 * const health = await getHealthStatus();
 * console.log(health.status); // 'healthy' | 'degraded' | 'unhealthy'
 *
 * // Detailed health with all components
 * const detailed = await getDetailedHealth();
 * console.log(detailed.checks.database.status);
 *
 * // Get dependency graph
 * const deps = await getDependencyGraph();
 * console.log(deps.summary.critical_path);
 *
 * // Check specific component
 * const component = await getComponentHealth('database');
 * console.log(component.response_time_ms);
 * ```
 */

import { apiClient } from './client';
import type {
  HealthResponse,
  DetailedHealthResponse,
  ReadyCheckResponse,
  DependencyGraphResponse,
  ComponentHealthCheckResponse,
  ApiError,
} from '@/types/api';

/**
 * Get basic health status
 *
 * Returns a quick health check response with overall system status.
 * Use this for lightweight health monitoring.
 *
 * @returns Promise resolving to health status response
 * @throws ApiError if request fails
 *
 * @example
 * ```ts
 * const health = await getHealthStatus();
 * if (health.status === 'healthy') {
 *   console.log('System is healthy');
 * }
 * ```
 */
export async function getHealthStatus(): Promise<HealthResponse> {
  try {
    const response = await apiClient.getAxiosInstance().get<HealthResponse>(
      '/health'
    );
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to retrieve health status'
    );
  }
}

/**
 * Get detailed health status for all components
 *
 * Returns comprehensive health information including status of all
 * system components (database, redis, celery, ML models, external APIs).
 *
 * @returns Promise resolving to detailed health response
 * @throws ApiError if request fails
 *
 * @example
 * ```ts
 * const detailed = await getDetailedHealth();
 * console.log(`Overall: ${detailed.status}`);
 * console.log(`Health: ${detailed.overall_health_percentage}%`);
 *
 * // Check individual components
 * Object.entries(detailed.checks).forEach(([name, check]) => {
 *   console.log(`${name}: ${check.status} (${check.response_time_ms}ms)`);
 * });
 * ```
 */
export async function getDetailedHealth(): Promise<DetailedHealthResponse> {
  try {
    const response = await apiClient.getAxiosInstance().get<DetailedHealthResponse>(
      '/api/health/detailed'
    );
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to retrieve detailed health status'
    );
  }
}

/**
 * Get ready status for essential services
 *
 * Checks if essential services (database, redis, celery) are operational.
 * Returns HTTP 200 when ready, 503 when not ready.
 *
 * @returns Promise resolving to ready status response
 * @throws ApiError if request fails
 *
 * @example
 * ```ts
 * const ready = await getReadyStatus();
 * if (ready.status === 'ready') {
 *   console.log('All essential services are operational');
 * } else {
 *   console.warn('System not ready:', ready.checks);
 * }
 * ```
 */
export async function getReadyStatus(): Promise<ReadyCheckResponse> {
  try {
    const response = await apiClient.getAxiosInstance().get<ReadyCheckResponse>(
      '/ready'
    );
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to retrieve ready status'
    );
  }
}

/**
 * Get service dependency graph
 *
 * Returns the complete service dependency graph showing relationships
 * between services, including dependencies and dependents.
 *
 * @returns Promise resolving to dependency graph response
 * @throws ApiError if request fails
 *
 * @example
 * ```ts
 * const deps = await getDependencyGraph();
 * console.log(`Total services: ${deps.summary.total_services}`);
 * console.log(`Essential: ${deps.summary.essential_services}`);
 * console.log(`Critical path: ${deps.summary.critical_path.join(' -> ')}`);
 *
 * // Check service dependencies
 * const dbInfo = deps.services.database;
 * console.log(`Database dependents:`, dbInfo.dependents);
 * ```
 */
export async function getDependencyGraph(): Promise<DependencyGraphResponse> {
  try {
    const response = await apiClient.getAxiosInstance().get<DependencyGraphResponse>(
      '/api/health/dependencies'
    );
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to retrieve dependency graph'
    );
  }
}

/**
 * Get health status for a specific component
 *
 * Returns detailed health information for a single component.
 * Valid component names: database, redis, celery, ml_ner_model,
 * ml_zero_shot_model, ml_language_tools, external_api
 *
 * @param componentName - Name of the component to check
 * @returns Promise resolving to component health response
 * @throws ApiError if request fails or component not found
 *
 * @example
 * ```ts
 * const db = await getComponentHealth('database');
 * console.log(`Database: ${db.status} (${db.response_time_ms}ms)`);
 * if (db.error) {
 *   console.error(`Database error: ${db.error}`);
 * }
 * ```
 */
export async function getComponentHealth(
  componentName: string
): Promise<ComponentHealthCheckResponse> {
  try {
    const response = await apiClient.getAxiosInstance().get<ComponentHealthCheckResponse>(
      `/api/health/component/${componentName}`
    );
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || `Failed to retrieve health for component: ${componentName}`
    );
  }
}

/**
 * Get API health status
 *
 * Returns the health status from the /api/health endpoint.
 * Similar to getHealthStatus but uses the API route.
 *
 * @returns Promise resolving to health status response
 * @throws ApiError if request fails
 *
 * @example
 * ```ts
 * const apiHealth = await getAPIHealthStatus();
 * console.log(`API Status: ${apiHealth.status}`);
 * ```
 */
export async function getAPIHealthStatus(): Promise<HealthResponse> {
  try {
    const response = await apiClient.getAxiosInstance().get<HealthResponse>(
      '/api/health'
    );
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to retrieve API health status'
    );
  }
}

/**
 * Get API ready status
 *
 * Returns the ready status from the /api/health/ready endpoint.
 * Similar to getReadyStatus but uses the API route.
 *
 * @returns Promise resolving to ready status response
 * @throws ApiError if request fails
 *
 * @example
 * ```ts
 * const apiReady = await getAPIReadyStatus();
 * console.log(`API Ready: ${apiReady.status}`);
 * ```
 */
export async function getAPIReadyStatus(): Promise<ReadyCheckResponse> {
  try {
    const response = await apiClient.getAxiosInstance().get<ReadyCheckResponse>(
      '/api/health/ready'
    );
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to retrieve API ready status'
    );
  }
}

/**
 * Health check result for polling
 *
 * Combined health and ready status for efficient polling.
 * Useful for dashboard auto-refresh functionality.
 *
 * @returns Promise resolving to combined health status
 * @throws ApiError if request fails
 *
 * @example
 * ```ts
 * // Poll every 30 seconds
 * const interval = setInterval(async () => {
 *   const status = await getHealthCheckResult();
 *   updateDashboard(status);
 * }, 30000);
 * ```
 */
export async function getHealthCheckResult(): Promise<{
  health: HealthResponse;
  detailed: DetailedHealthResponse;
  ready: ReadyCheckResponse;
}> {
  try {
    const [health, detailed, ready] = await Promise.all([
      getHealthStatus(),
      getDetailedHealth(),
      getReadyStatus(),
    ]);

    return { health, detailed, ready };
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to retrieve health check results'
    );
  }
}

/**
 * Component health status type
 */
export type ComponentHealthStatus = 'healthy' | 'degraded' | 'unhealthy';

/**
 * System health status type
 */
export type SystemHealthStatus = 'healthy' | 'degraded' | 'unhealthy';

/**
 * Valid component names for health checks
 */
export const VALID_COMPONENT_NAMES = [
  'database',
  'redis',
  'celery',
  'ml_ner_model',
  'ml_zero_shot_model',
  'ml_language_tools',
  'external_api',
] as const;

export type ComponentName = typeof VALID_COMPONENT_NAMES[number];
