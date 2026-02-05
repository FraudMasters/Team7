/**
 * Industry Classifier API Client
 *
 * Этот модуль предоставляет типизированный клиент для взаимодействия с
 * backend сервисом классификации индустрии. Обрабатывает определение индустрии
 * из должностей и описаний вакансий, а также предложения навыков
 * на основе контекста индустрии.
 *
 * @example
 * ```ts
 * import { industryClassifier } from '@/api/industryClassifier';
 *
 * // Классификация индустрии из должности
 * const classification = await industryClassifier.classifyIndustry({
 *   title: 'Senior Registered Nurse',
 *   description: 'Ищем опытную медсестру с опытом работы в отделении интенсивной терапии...',
 * });
 *
 * // Получение предложений навыков для конкретной индустрии
 * const suggestions = await industryClassifier.getSuggestions({
 *   industry: 'healthcare',
 *   title: 'Senior Registered Nurse',
 *   description: 'Отделение интенсивной терапии, уход за пациентами, медицинские записи...',
 *   limit: 20,
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  IndustryClassificationRequest,
  IndustryClassificationResponse,
  SkillSuggestionRequest,
  SkillSuggestionResponse,
  ApiError,
} from '@/types/api';

/**
 * Конфигурация API по умолчанию для классификатора индустрии
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 30000, // 30 секунд для классификации
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API классификатора индустрии
 *
 * Предоставляет методы для классификации индустрии и предложений навыков
 * с proper обработкой ошибок и типобезопасностью.
 */
export class IndustryClassifierClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента классификатора индустрии
   *
   * @param config - Опциональные переопределения конфигурации
   */
  constructor(config: Partial<typeof DEFAULT_CONFIG> = {}) {
    const finalConfig = {
      ...DEFAULT_CONFIG,
      ...config,
      headers: {
        ...DEFAULT_CONFIG.headers,
        ...config.headers,
      },
    };

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
   * Классификация индустрии из должности и опционального описания
   *
   * @param request - Запрос на классификацию с должностью и опциональным описанием
   * @returns Классификация индустрии с оценкой уверенности
   * @throws ApiError если классификация не удалась
   *
   * @example
   * ```ts
   * const result = await industryClassifier.classifyIndustry({
   *   title: 'Senior Java Developer',
   *   description: 'Ищем backend разработчика с опытом Spring...',
   * });
   * // Returns: { industry: 'tech', confidence: 0.95, ... }
   * ```
   */
  async classifyIndustry(
    request: IndustryClassificationRequest
  ): Promise<IndustryClassificationResponse> {
    try {
      const response: AxiosResponse<IndustryClassificationResponse> = await this.client.post(
        '/api/industry-classifier/classify',
        request
      );

      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение предложений навыков на основе индустрии и контекста работы
   *
   * @param request - Запрос предложений с индустрией, должностью, описанием и лимитом
   * @returns Предложения навыков с оценками релевантности
   * @throws ApiError если получение предложений не удалось
   *
   * @example
   * ```ts
   * const suggestions = await industryClassifier.getSuggestions({
   *   industry: 'healthcare',
   *   title: 'Senior Registered Nurse',
   *   description: 'Отделение интенсивной терапии, уход за пациентами, медицинские записи...',
   *   limit: 20,
   * });
   * // Returns: { industry: 'healthcare', suggested_skills: [...], total_count: 15 }
   * ```
   */
  async getSuggestions(
    request: SkillSuggestionRequest
  ): Promise<SkillSuggestionResponse> {
    try {
      const response: AxiosResponse<SkillSuggestionResponse> = await this.client.post(
        '/api/skill-suggestions/suggest',
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
 * Экземпляр клиента классификатора индустрии по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех вызовов классификации индустрии.
 */
export const industryClassifier = new IndustryClassifierClient();

/**
 * Экспорт класса клиента классификатора индустрии для создания кастомных экземпляров
 */
export default IndustryClassifierClient;
