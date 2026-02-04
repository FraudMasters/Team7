/**
 * User Preferences API
 *
 * This module provides API functions for managing user preferences,
 * including language preference, user profile, dashboard configuration,
 * filter preferences, and API keys management.
 *
 * @example
 * ```ts
 * import {
 *   getLanguagePreference,
 *   getUserProfile,
 *   updateDashboardConfig,
 *   listApiKeys
 * } from '@/api/preferences';
 *
 * // Get current language preference
 * const preference = await getLanguagePreference();
 * console.log(preference.language); // 'en' or 'ru'
 *
 * // Get user profile
 * const profile = await getUserProfile();
 * console.log(profile.name);
 *
 * // Update dashboard configuration
 * await updateDashboardConfig({ layout: 'grid' });
 *
 * // List API keys
 * const keys = await listApiKeys();
 * console.log(keys.api_keys);
 * ```
 */

import { apiClient } from '@/api/client';
import type {
  LanguagePreferenceResponse,
  LanguagePreferenceUpdate,
  UserProfileResponse,
  UserProfileUpdate,
  DashboardConfigResponse,
  DashboardConfigUpdate,
  FilterPreferencesResponse,
  FilterPreferencesUpdate,
  ApiKeyCreate,
  ApiKeyResponse,
  ApiKeyListResponse,
  ApiError,
} from '@/types/api';

/**
 * Get the current language preference from the backend
 *
 * Retrieves the currently selected language for the UI.
 * Default is 'en' (English) if not previously set.
 *
 * @returns Promise resolving to language preference response
 * @throws ApiError if request fails
 *
 * @example
 * ```ts
 * const preference = await getLanguagePreference();
 * console.log(`Current language: ${preference.language}`);
 * ```
 */
export async function getLanguagePreference(): Promise<LanguagePreferenceResponse> {
  try {
    const response = await apiClient.getAxiosInstance().get<LanguagePreferenceResponse>(
      '/api/preferences/language'
    );
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to retrieve language preference'
    );
  }
}

/**
 * Update the language preference
 *
 * Sets the language preference for the UI. Supported languages are:
 * - 'en' (English)
 * - 'ru' (Russian)
 *
 * @param language - Language code to set ('en' or 'ru')
 * @returns Promise resolving to updated language preference response
 * @throws ApiError if request fails or language is not supported
 *
 * @example
 * ```ts
 * await updateLanguagePreference('ru');
 * console.log('Language updated to Russian');
 * ```
 */
export async function updateLanguagePreference(
  language: 'en' | 'ru'
): Promise<LanguagePreferenceResponse> {
  try {
    const request: LanguagePreferenceUpdate = { language };
    const response = await apiClient.getAxiosInstance().put<LanguagePreferenceResponse>(
      '/api/preferences/language',
      request
    );
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to update language preference'
    );
  }
}

/**
 * Get the user profile
 *
 * Retrieves the user's profile information including name, email, role, and avatar URL.
 *
 * @returns Promise resolving to user profile response
 * @throws ApiError if request fails
 *
 * @example
 * ```ts
 * const profile = await getUserProfile();
 * console.log(`User: ${profile.name}, Role: ${profile.role}`);
 * ```
 */
export async function getUserProfile(): Promise<UserProfileResponse> {
  try {
    const response = await apiClient.getAxiosInstance().get<UserProfileResponse>(
      '/api/preferences/profile'
    );
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to retrieve user profile'
    );
  }
}

/**
 * Update the user profile
 *
 * Updates the user's profile information. Only fields that are provided will be updated.
 * Fields not provided will remain unchanged.
 *
 * @param profileData - Profile fields to update
 * @returns Promise resolving to updated user profile response
 * @throws ApiError if request fails
 *
 * @example
 * ```ts
 * await updateUserProfile({ name: 'John Doe', role: 'recruiter' });
 * console.log('Profile updated');
 * ```
 */
export async function updateUserProfile(
  profileData: UserProfileUpdate
): Promise<UserProfileResponse> {
  try {
    const response = await apiClient.getAxiosInstance().put<UserProfileResponse>(
      '/api/preferences/profile',
      profileData
    );
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to update user profile'
    );
  }
}

/**
 * Get the dashboard configuration
 *
 * Retrieves the current dashboard configuration including layout, widgets, and settings.
 *
 * @returns Promise resolving to dashboard configuration response
 * @throws ApiError if request fails
 *
 * @example
 * ```ts
 * const config = await getDashboardConfig();
 * console.log(`Layout: ${config.layout}`);
 * ```
 */
export async function getDashboardConfig(): Promise<DashboardConfigResponse> {
  try {
    const response = await apiClient.getAxiosInstance().get<DashboardConfigResponse>(
      '/api/preferences/dashboard'
    );
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to retrieve dashboard configuration'
    );
  }
}

/**
 * Update the dashboard configuration
 *
 * Updates the dashboard configuration with the provided layout, widgets, and settings.
 * Only fields that are provided will be updated. Fields not provided will remain unchanged.
 *
 * @param configData - Dashboard configuration fields to update
 * @returns Promise resolving to updated dashboard configuration response
 * @throws ApiError if request fails
 *
 * @example
 * ```ts
 * await updateDashboardConfig({
 *   layout: 'grid',
 *   widgets: { metrics: { enabled: true } }
 * });
 * ```
 */
export async function updateDashboardConfig(
  configData: DashboardConfigUpdate
): Promise<DashboardConfigResponse> {
  try {
    const response = await apiClient.getAxiosInstance().put<DashboardConfigResponse>(
      '/api/preferences/dashboard',
      configData
    );
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to update dashboard configuration'
    );
  }
}

/**
 * Get the filter preferences
 *
 * Retrieves the default filter settings that are used when searching candidates.
 *
 * @returns Promise resolving to filter preferences response
 * @throws ApiError if request fails
 *
 * @example
 * ```ts
 * const filters = await getFilterPreferences();
 * console.log('Default filters:', filters.default_filters);
 * ```
 */
export async function getFilterPreferences(): Promise<FilterPreferencesResponse> {
  try {
    const response = await apiClient.getAxiosInstance().get<FilterPreferencesResponse>(
      '/api/preferences/filters'
    );
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to retrieve filter preferences'
    );
  }
}

/**
 * Update the filter preferences
 *
 * Updates the default filter settings used when searching candidates.
 *
 * @param filtersData - Filter preferences to set
 * @returns Promise resolving to updated filter preferences response
 * @throws ApiError if request fails
 *
 * @example
 * ```ts
 * await updateFilterPreferences({
 *   default_filters: {
 *     experience_years: [0, 10],
 *     languages: ['en', 'ru']
 *   }
 * });
 * ```
 */
export async function updateFilterPreferences(
  filtersData: FilterPreferencesUpdate
): Promise<FilterPreferencesResponse> {
  try {
    const response = await apiClient.getAxiosInstance().put<FilterPreferencesResponse>(
      '/api/preferences/filters',
      filtersData
    );
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to update filter preferences'
    );
  }
}

/**
 * Create a new API key
 *
 * Adds a new API key to the user's preferences for external service integrations.
 *
 * @param keyData - API key creation data
 * @returns Promise resolving to created API key response
 * @throws ApiError if creation fails
 *
 * @example
 * ```ts
 * const newKey = await createApiKey({
 *   name: 'OpenAI',
 *   key: 'sk-test-key',
 *   service: 'openai'
 * });
 * console.log(`Created key: ${newKey.id}`);
 * ```
 */
export async function createApiKey(
  keyData: ApiKeyCreate
): Promise<ApiKeyResponse> {
  try {
    const response = await apiClient.getAxiosInstance().post<ApiKeyResponse>(
      '/api/preferences/api-keys',
      keyData
    );
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to create API key'
    );
  }
}

/**
 * List all API keys
 *
 * Returns a list of all stored API keys for external service integrations.
 * The actual key values are masked for security.
 *
 * @returns Promise resolving to API key list response
 * @throws ApiError if request fails
 *
 * @example
 * ```ts
 * const keys = await listApiKeys();
 * console.log(`Total keys: ${keys.total}`);
 * ```
 */
export async function listApiKeys(): Promise<ApiKeyListResponse> {
  try {
    const response = await apiClient.getAxiosInstance().get<ApiKeyListResponse>(
      '/api/preferences/api-keys'
    );
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to list API keys'
    );
  }
}

/**
 * Delete an API key
 *
 * Permanently removes an API key from the user's preferences.
 * This action cannot be undone.
 *
 * @param keyId - Unique identifier of the API key to delete
 * @throws ApiError if deletion fails
 *
 * @example
 * ```ts
 * await deleteApiKey('1234567890');
 * console.log('API key deleted');
 * ```
 */
export async function deleteApiKey(keyId: string): Promise<void> {
  try {
    await apiClient.getAxiosInstance().delete(`/api/preferences/api-keys/${keyId}`);
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to delete API key'
    );
  }
}
