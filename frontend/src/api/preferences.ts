/**
 * User Preferences API
 *
 * Этот модуль предоставляет API функции для управления пользовательскими предпочтениями,
 * включая языковые предпочтения для локализации UI.
 *
 * @example
 * ```ts
 * import { getLanguagePreference, updateLanguagePreference } from '@/api/preferences';
 *
 * // Получение текущего языкового предпочтения
 * const preference = await getLanguagePreference();
 * console.log(preference.language); // 'en' or 'ru'
 *
 * // Обновление языкового предпочтения
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
 * Получение текущего языкового предпочтения из backend
 *
 * Получает текущий выбранный язык для UI.
 * По умолчанию 'en' (английский), если ранее не был установлен.
 *
 * @returns Promise, разрешающий в ответ о языковом предпочтении
 * @throws ApiError если запрос не удался
 *
 * @example
 * ```ts
 * const preference = await getLanguagePreference();
 * console.log(`Текущий язык: ${preference.language}`);
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
      apiError.detail || 'Не удалось получить языковое предпочтение'
    );
  }
}

/**
 * Обновление языкового предпочтения
 *
 * Устанавливает языковое предпочтение для UI. Поддерживаемые языки:
 * - 'en' (английский)
 * - 'ru' (русский)
 *
 * @param language - Код языка для установки ('en' или 'ru')
 * @returns Promise, разрешающий в обновленный ответ о языковом предпочтении
 * @throws ApiError если запрос не удался или язык не поддерживается
 *
 * @example
 * ```ts
 * await updateLanguagePreference('ru');
 * console.log('Язык обновлен на русский');
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
      apiError.detail || 'Не удалось обновить языковое предпочтение'
    );
  }
}
