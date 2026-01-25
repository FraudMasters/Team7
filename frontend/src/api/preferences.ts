/**
 * User Preferences API
 *
 * This module provides API functions for managing user preferences,
 * including language preference for UI localization.
 *
 * @example
 * ```ts
 * import { getLanguagePreference, updateLanguagePreference } from '@/api/preferences';
 *
 * // Get current language preference
 * const preference = await getLanguagePreference();
 * console.log(preference.language); // 'en' or 'ru'
 *
 * // Update language preference
 * await updateLanguagePreference('ru');
 * ```
 */

import { apiClient } from '@/api/client';
import type {
  LanguagePreferenceResponse,
  LanguagePreferenceUpdate,
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
