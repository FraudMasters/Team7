/**
 * Organization-Scoped API Fetch Helper
 *
 * This module provides a fetch wrapper that automatically adds the X-Organization-ID header
 * to all API requests based on the current organization context.
 *
 * @example
 * ```ts
 * import { orgScopedFetch } from '@/api/organizationScopedFetch';
 *
 * // Fetch candidates scoped to current organization
 * const candidates = await orgScopedFetch('/api/candidates/');
 *
 * // With custom options
 * const data = await orgScopedFetch('/api/vacancies/', {
 *   method: 'POST',
 *   body: JSON.stringify({ title: 'Developer' }),
 * });
 * ```
 */

/**
 * Local storage key for organization persistence
 */
const ORGANIZATION_STORAGE_KEY = 'app-current-organization';

/**
 * Get current organization from localStorage
 *
 * @returns Organization ID or null if not set
 */
export const getCurrentOrganizationId = (): string | null => {
  try {
    const storedOrg = localStorage.getItem(ORGANIZATION_STORAGE_KEY);
    if (storedOrg) {
      const org = JSON.parse(storedOrg);
      return org?.id || null;
    }
  } catch (error) {
    // Invalid data in storage
    console.warn('Invalid organization data in localStorage:', error);
  }
  return null;
};

/**
 * Organization-scoped fetch wrapper
 *
 * Automatically adds X-Organization-ID header to requests based on the current
 * organization context from localStorage.
 *
 * @param url - Request URL
 * @param options - Fetch options (method, headers, body, etc.)
 * @returns Fetch response
 * @throws Error if organization is required but not set
 *
 * @example
 * ```ts
 * // Simple GET request
 * const candidates = await orgScopedFetch('/api/candidates/');
 *
 * // POST request with body
 * const result = await orgScopedFetch('/api/vacancies/', {
 *   method: 'POST',
 *   headers: {
 *     'Content-Type': 'application/json',
 *   },
 *   body: JSON.stringify({ title: 'Developer' }),
 * });
 *
 * // Request that doesn't require organization
 * const health = await orgScopedFetch('/health', null, false);
 * ```
 */
export const orgScopedFetch = async (
  url: string,
  options: RequestInit = {},
  requireOrganization: boolean = true
): Promise<Response> => {
  const orgId = getCurrentOrganizationId();

  if (requireOrganization && !orgId) {
    throw new Error(
      'No organization selected. Please select an organization to perform this action.'
    );
  }

  // Clone headers to avoid mutating the original
  const headers = new Headers(options.headers || {});

  // Add Content-Type if not present
  if (!headers.has('Content-Type') && options.body) {
    headers.set('Content-Type', 'application/json');
  }

  // Add X-Organization-ID header if organization is set
  if (orgId) {
    headers.set('X-Organization-ID', orgId);
  }

  // Perform fetch with organization header
  const response = await fetch(url, {
    ...options,
    headers,
  });

  return response;
};

/**
 * Create an axios instance with organization-scoped request interceptor
 *
 * This creates an axios instance that automatically adds the X-Organization-ID
 * header to all requests based on the current organization context.
 *
 * @param baseURL - Base URL for the axios instance
 * @returns Axios instance with organization interceptor
 *
 * @example
 * ```ts
 * import { createOrgAxiosInstance } from '@/api/organizationScopedFetch';
 * import axios from 'axios';
 *
 * const api = createOrgAxiosInstance('/api');
 *
 * // All requests automatically include X-Organization-ID header
 * const candidates = await api.get('/candidates/');
 * ```
 */
export const createOrgAxiosInstance = (baseURL: string = '') => {
  const axios = require('axios');

  const instance = axios.create({
    baseURL: baseURL || import.meta.env.VITE_API_URL || '',
    timeout: 30000,
  });

  // Request interceptor to add organization header
  instance.interceptors.request.use(
    (config: any) => {
      const orgId = getCurrentOrganizationId();

      if (orgId) {
        config.headers['X-Organization-ID'] = orgId;
      }

      return config;
    },
    (error: any) => {
      return Promise.reject(error);
    }
  );

  return instance;
};

export default orgScopedFetch;
