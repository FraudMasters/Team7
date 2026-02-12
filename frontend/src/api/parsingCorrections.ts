/**
 * Parsing Corrections API Client
 *
 * Этот модуль предоставляет клиент для работы с исправлениями парсинга резюме.
 * Поддерживает получение, создание и обновление исправлений для отслеживания
 * точности парсинга и улучшения качества распознавания.
 *
 * @example
 * ```ts
 * import { parsingCorrectionsClient, ParsingCorrectionsClient } from '@/api/parsingCorrections';
 *
 * // Получение всех исправлений для резюме
 * const corrections = await parsingCorrectionsClient.getCorrections('resume-123');
 *
 * // Создание нового исправления
 * const correction = await parsingCorrectionsClient.createCorrection('resume-123', {
 *   field_name: 'position',
 *   original_value: { position: 'Software Engineer' },
 *   corrected_value: { position: 'Senior Software Engineer' },
 *   reason: 'position_was_incorrect'
 * });
 *
 * // Обновление отдельного поля
 * const updated = await parsingCorrectionsClient.updateField('resume-123', 'position', {
 *   value: 'Senior Software Engineer',
 *   original_value: 'Software Engineer',
 *   reason: 'position_was_incorrect'
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type { ApiError } from '@/types/api';
import type {
  ParsingCorrectionResponse,
  ParsingCorrectionCreate,
  ParsingCorrectionsListResponse,
  ParsingCorrectionCreateResponse,
  FieldUpdateRequest,
  FieldUpdateResponse,
  CorrectableFieldName,
  CorrectionsQueryParams,
} from '@/types/parsingCorrection';

/**
 * Переэкспорт типов для удобства использования
 */
export type {
  ParsingCorrectionResponse,
  ParsingCorrectionCreate,
  ParsingCorrectionsListResponse,
  ParsingCorrectionCreateResponse,
  FieldUpdateRequest,
  FieldUpdateResponse,
  CorrectableFieldName,
  CorrectionsQueryParams,
};

/**
 * Конфигурация по умолчанию для клиента исправлений парсинга
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_GATEWAY_URL ?? 'http://localhost:8888',
  timeout: 15000, // 15 секунд
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для работы с исправлениями парсинга
 *
 * Предоставляет методы для получения, создания и обновления исправлений
 * с proper обработкой ошибок и типобезопасностью.
 */
export class ParsingCorrectionsClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента исправлений парсинга
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
      404: 'Исправления не найдены.',
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
   * Получение всех исправлений для конкретного резюме
   *
   * @param resumeId - ID резюме
   * @param params - Опциональные параметры фильтрации
   * @returns Список исправлений с метаданными
   * @throws ApiError если получение списка не удалось
   *
   * @example
   * ```ts
   * // Получение всех исправлений для резюме
   * const corrections = await parsingCorrectionsClient.getCorrections('resume-123');
   *
   * // Фильтрация по имени поля
   * const skillCorrections = await parsingCorrectionsClient.getCorrections('resume-123', {
   *   field_name: 'skills'
   * });
   * ```
   */
  async getCorrections(
    resumeId: string,
    params?: CorrectionsQueryParams
  ): Promise<ParsingCorrectionsListResponse> {
    try {
      const queryParams: Record<string, string | number | undefined> = {};

      if (params?.field_name) {
        queryParams.field_name = params.field_name;
      }
      if (params?.limit !== undefined) {
        queryParams.limit = params.limit;
      }
      if (params?.offset !== undefined) {
        queryParams.offset = params.offset;
      }

      const response: AxiosResponse<ParsingCorrectionsListResponse> = await this.client.get(
        `/api/parsing-corrections/${resumeId}`,
        { params: queryParams }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Создание нового исправления для резюме
   *
   * @param resumeId - ID резюме
   * @param correction - Данные исправления
   * @returns Созданное исправление
   * @throws ApiError если создание не удалось
   *
   * @example
   * ```ts
   * const correction = await parsingCorrectionsClient.createCorrection('resume-123', {
   *   field_name: 'position',
   *   original_value: { position: 'Software Engineer' },
   *   corrected_value: { position: 'Senior Software Engineer' },
   *   reason: 'position_was_incorrect'
   * });
   * ```
   */
  async createCorrection(
    resumeId: string,
    correction: ParsingCorrectionCreate
  ): Promise<ParsingCorrectionCreateResponse> {
    try {
      const response: AxiosResponse<ParsingCorrectionCreateResponse> = await this.client.post(
        `/api/parsing-corrections/${resumeId}`,
        correction
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Обновление отдельного поля с отслеживанием исправления
   *
   * @param resumeId - ID резюме
   * @param fieldName - Имя поля для обновления
   * @param update - Данные обновления
   * @returns Созданное исправление
   * @throws ApiError если обновление не удалось
   *
   * @example
   * ```ts
   * const result = await parsingCorrectionsClient.updateField('resume-123', 'position', {
   *   value: 'Senior Software Engineer',
   *   original_value: 'Software Engineer',
   *   reason: 'position_was_incorrect'
   * });
   * ```
   */
  async updateField(
    resumeId: string,
    fieldName: CorrectableFieldName,
    update: FieldUpdateRequest
  ): Promise<FieldUpdateResponse> {
    try {
      const response: AxiosResponse<FieldUpdateResponse> = await this.client.put(
        `/api/parsing-corrections/${resumeId}/fields/${fieldName}`,
        update
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Проверка наличия исправлений для резюме
   *
   * @param resumeId - ID резюме
   * @returns true если есть хотя бы одно исправление
   * @throws ApiError если запрос не удался
   *
   * @example
   * ```ts
   * const hasCorrections = await parsingCorrectionsClient.hasCorrections('resume-123');
   * if (hasCorrections) {
   *   console.log('Resume has been corrected');
   * }
   * ```
   */
  async hasCorrections(resumeId: string): Promise<boolean> {
    try {
      const response = await this.getCorrections(resumeId, { limit: 1 });
      return response.count > 0;
    } catch {
      return false;
    }
  }

  /**
   * Получение исправлений для конкретного поля
   *
   * @param resumeId - ID резюме
   * @param fieldName - Имя поля
   * @returns Список исправлений для поля
   * @throws ApiError если запрос не удался
   *
   * @example
   * ```ts
   * const skillCorrections = await parsingCorrectionsClient.getCorrectionsForField(
   *   'resume-123',
   *   'skills'
   * );
   * ```
   */
  async getCorrectionsForField(
    resumeId: string,
    fieldName: CorrectableFieldName
  ): Promise<ParsingCorrectionsListResponse> {
    return this.getCorrections(resumeId, { field_name: fieldName });
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
 * Экземпляр клиента исправлений парсинга по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех операций с исправлениями.
 */
export const parsingCorrectionsClient = new ParsingCorrectionsClient();

/**
 * Экспорт класса для создания кастомных экземпляров
 */
export default ParsingCorrectionsClient;
