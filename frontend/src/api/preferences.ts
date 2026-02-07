/**
 * Preferences API Client
 *
 * Этот модуль предоставляет клиент для работы с пользовательскими предпочтениями.
 * Поддерживает управление языковыми настройками для локализации интерфейса.
 *
 * @example
 * ```ts
 * import { preferencesClient, PreferencesClient } from '@/api/preferences';
 *
 * // Получение текущего языкового предпочтения
 * const preference = await preferencesClient.getLanguagePreference();
 * console.log(preference.language); // 'en' or 'ru'
 *
 * // Обновление языкового предпочтения
 * await preferencesClient.updateLanguagePreference('ru');
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  LanguagePreferenceUpdate,
  LanguagePreferenceResponse,
  ApiError,
} from '@/types/api';

/**
 * Переэкспорт типов для удобства использования
 */
export type {
  LanguagePreferenceUpdate,
  LanguagePreferenceResponse,
};

/**
 * Конфигурация по умолчанию для клиента предпочтений
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_GATEWAY_URL ?? 'http://localhost:8888',
  timeout: 10000, // 10 секунд
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для работы с пользовательскими предпочтениями
 *
 * Предоставляет методы для получения и обновления пользовательских настроек,
 * таких как язык интерфейса.
 */
export class PreferencesClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента предпочтений
   *
   * @param config - Опциональные переопределения конфигурации
   */
  constructor(config: Partial<typeof DEFAULT_CONFIG> = {}) {
    const finalConfig = { ...DEFAULT_CONFIG, ...config };

    this.client = axios.create(finalConfig);

    // Интерцептор ответов для обработки ошибок
    this.client.interceptors.response.use(
      (response) => response,
      (error) => Promise.reject(this.transformError(error))
    );
  }

  /**
   * Преобразование ошибки Axios в стандартизированную ошибку API
   *
   * @param error - Ошибка Axios
   * @returns Преобразованная ошибка API
   */
  private transformError(error: unknown): ApiError {
    const axiosError = error as AxiosError<{ detail?: string }>;

    // Ошибка сети (нет ответа)
    if (!axiosError.response) {
      if (axiosError.code === 'ECONNABORTED') {
        return {
          detail: 'Таймаут запроса. Проверьте соединение и попробуйте снова.',
          status: 408,
        };
      }
      return {
        detail: 'Ошибка сети. Проверьте соединение и попробуйте снова.',
        status: 0,
      };
    }

    // Сервер вернул ошибку
    const status = axiosError.response.status;
    const data = axiosError.response.data;

    // Используем сообщение об ошибке от сервера, если доступно
    if (data?.detail) {
      return { detail: data.detail, status };
    }

    // Сообщения об ошибках по умолчанию для разных кодов статуса
    const defaultMessages: Record<number, string> = {
      400: 'Неверный запрос. Проверьте введенные данные.',
      401: 'Не авторизован. Войдите в систему.',
      403: 'Доступ запрещен. У вас нет прав для выполнения этого действия.',
      404: 'Предпочтение не найдено.',
      422: 'Ошибка валидации. Проверьте формат данных.',
      429: 'Слишком много запросов. Попробуйте позже.',
      500: 'Ошибка сервера. Попробуйте позже.',
      502: 'Ошибка шлюза. Попробуйте позже.',
      503: 'Сервис недоступен. Попробуйте позже.',
    };

    return {
      detail: data?.detail || defaultMessages[status] || 'Произошла непредвиденная ошибка.',
      status,
    };
  }

  /**
   * Получение текущего языкового предпочтения
   *
   * Возвращает текущий выбранный язык для пользовательского интерфейса.
   * По умолчанию 'en' (английский), если ранее не был установлен другой.
   *
   * @returns Данные о языковом предпочтении
   * @throws ApiError если получение предпочтения не удалось
   *
   * @example
   * ```ts
   * const preference = await preferencesClient.getLanguagePreference();
   * console.log(`Текущий язык: ${preference.language}`);
   * ```
   */
  async getLanguagePreference(): Promise<LanguagePreferenceResponse> {
    try {
      const response: AxiosResponse<LanguagePreferenceResponse> = await this.client.get(
        '/api/preferences/language'
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Обновление языкового предпочтения
   *
   * Устанавливает языковое предпочтение для пользовательского интерфейса.
   * Поддерживаемые языки:
   * - 'en' (английский)
   * - 'ru' (русский)
   *
   * @param language - Код языка для установки ('en' или 'ru')
   * @returns Обновленные данные о языковом предпочтении
   * @throws ApiError если обновление не удалось или язык не поддерживается
   *
   * @example
   * ```ts
   * // Установка русского языка
   * const updated = await preferencesClient.updateLanguagePreference('ru');
   * console.log(`Язык обновлен: ${updated.language}`);
   *
   * // Установка английского языка
   * await preferencesClient.updateLanguagePreference('en');
   * ```
   */
  async updateLanguagePreference(language: string): Promise<LanguagePreferenceResponse> {
    try {
      const request: LanguagePreferenceUpdate = { language };

      const response: AxiosResponse<LanguagePreferenceResponse> = await this.client.put(
        '/api/preferences/language',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение базового экземпляра Axios
   *
   * Полезно для выполнения кастомных запросов, не покрытых методами клиента.
   *
   * @returns Экземпляр Axios
   */
  getAxiosInstance(): AxiosInstance {
    return this.client;
  }
}

/**
 * Экземпляр клиента предпочтений по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех операций с предпочтениями.
 */
export const preferencesClient = new PreferencesClient();

/**
 * Экспорт класса для создания кастомных экземпляров
 */
export default PreferencesClient;
