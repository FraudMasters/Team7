/**
 * Search History API Client
 *
 * Этот модуль предоставляет клиент для управления историей поиска,
 * включая получение и очистку записей истории поиска.
 *
 * @example
 * ```ts
 * import { searchHistoryClient } from '@/api/searchHistory';
 *
 * // Получение списка истории поиска
 * const history = await searchHistoryClient.listSearchHistory();
 *
 * // Получение истории поиска с пагинацией
 * const history = await searchHistoryClient.listSearchHistory(0, 20);
 *
 * // Очистка всей истории поиска
 * await searchHistoryClient.clearSearchHistory();
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  SearchHistoryResponse,
  ApiError,
} from '@/types/api';

/**
 * Конфигурация по умолчанию для клиента истории поиска
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 10000, // 10 секунд
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для работы с историей поиска
 *
 * Предоставляет методы для управления историей поиска с proper
 * обработкой ошибок и типобезопасностью.
 */
export class SearchHistoryClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента истории поиска
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
      404: 'Ресурс не найден.',
      422: 'Ошибка валидации. Проверьте введенные данные.',
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
   * Получение списка истории поиска с опциональной пагинацией
   *
   * @param skip - Количество записей для пропуска (пагинация)
   * @param limit - Максимальное количество записей для возврата
   * @param recruiterId - Опциональный фильтр по ID рекрутера
   * @returns Список элементов истории поиска
   * @throws ApiError если получение списка не удалось
   *
   * @example
   * ```ts
   * // Получение всей истории поиска
   * const history = await searchHistoryClient.listSearchHistory();
   *
   * // Получение первых 20 элементов
   * const history = await searchHistoryClient.listSearchHistory(0, 20);
   *
   * // Получение следующих 20 элементов
   * const history = await searchHistoryClient.listSearchHistory(20, 20);
   * ```
   */
  async listSearchHistory(
    skip: number = 0,
    limit: number = 50,
    recruiterId?: string
  ): Promise<SearchHistoryResponse> {
    try {
      const params: Record<string, number | string> = { skip, limit };
      if (recruiterId) params.recruiter_id = recruiterId;

      const response: AxiosResponse<SearchHistoryResponse> = await this.client.get(
        '/api/search/history',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Очистка всей истории поиска
   *
   * Примечание: Этот эндпоинт может быть еще не реализован в backend.
   * Если вы получаете ошибку 404, backend должен реализовать этот эндпоинт.
   *
   * @throws ApiError если очистка не удалась
   *
   * @example
   * ```ts
   * await searchHistoryClient.clearSearchHistory();
   * ```
   */
  async clearSearchHistory(): Promise<void> {
    try {
      await this.client.delete('/api/search/history');
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
 * Экземпляр клиента истории поиска по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех операций с историей поиска.
 */
export const searchHistoryClient = new SearchHistoryClient();

/**
 * Экспорт класса истории поиска для создания кастомных экземпляров
 */
export default SearchHistoryClient;
