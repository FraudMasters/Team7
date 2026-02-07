/**
 * Model Versions API Client
 *
 * Этот модуль предоставляет клиент для работы с версиями ML-моделей через API Gateway.
 * Поддерживает полный цикл управления версиями моделей: создание, просмотр списка,
 * получение активной версии, обновление, удаление, активация и деактивация.
 *
 * @example
 * ```ts
 * import { modelVersionsClient, ModelVersionsClient } from '@/api/modelVersions';
 *
 * // Получение списка всех версий моделей
 * const versions = await modelVersionsClient.listModelVersions();
 *
 * // Создание новых версий моделей
 * const created = await modelVersionsClient.createModelVersions({
 *   models: [
 *     {
 *       model_name: 'skill_matching',
 *       version: 'v2.0.0',
 *       is_active: false,
 *       is_experiment: true,
 *       experiment_config: { traffic_percentage: 20 },
 *       performance_score: 92.5,
 *     },
 *   ],
 * });
 *
 * // Получение активной модели
 * const active = await modelVersionsClient.getActiveModel('skill_matching');
 *
 * // Получение версии по ID
 * const version = await modelVersionsClient.getModelVersion('version-123');
 *
 * // Активация версии модели
 * const activated = await modelVersionsClient.activateModelVersion('version-123');
 *
 * // Деактивация версии модели
 * const deactivated = await modelVersionsClient.deactivateModelVersion('version-123');
 *
 * // Обновление версии модели
 * const updated = await modelVersionsClient.updateModelVersion('version-123', {
 *   performance_score: 95.0,
 * });
 *
 * // Удаление версии модели
 * await modelVersionsClient.deleteModelVersion('version-123');
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  ModelVersionCreate,
  ModelVersionUpdate,
  ModelVersionResponse,
  ModelVersionListResponse,
  ApiError,
} from '@/types/api';

/**
 * Переэкспорт типов для удобства использования
 */
export type {
  ModelVersionCreate,
  ModelVersionUpdate,
  ModelVersionResponse,
  ModelVersionListResponse,
};

/**
 * Конфигурация по умолчанию для клиента версий моделей
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_GATEWAY_URL ?? 'http://localhost:8888',
  timeout: 30000, // 30 секунд
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для работы с версиями моделей
 *
 * Предоставляет методы для создания, просмотра, обновления, активации,
 * деактивации и удаления версий ML-моделей с proper обработкой ошибок
 * и типобезопасностью.
 */
export class ModelVersionsClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента версий моделей
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
      404: 'Версия модели не найдена.',
      409: 'Конфликт. Вероятно, активная версия уже существует.',
      422: 'Ошибка валидации. Проверьте входные данные.',
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
   * Создание новых версий моделей
   *
   * @param request - Запрос на создание с массивом моделей
   * @returns Созданные версии моделей с метаданными
   * @throws ApiError если создание не удалось
   *
   * @example
   * ```ts
   * const result = await modelVersionsClient.createModelVersions({
   *   models: [
   *     {
   *       model_name: 'skill_matching',
   *       version: 'v2.0.0',
   *       is_active: false,
   *       is_experiment: true,
   *       experiment_config: { traffic_percentage: 20 },
   *       performance_score: 92.5,
   *     },
   *   ],
   * });
   * console.log('Создано версий:', result.total_count);
   * ```
   */
  async createModelVersions(
    request: ModelVersionCreate
  ): Promise<ModelVersionListResponse> {
    try {
      const response: AxiosResponse<ModelVersionListResponse> = await this.client.post(
        '/api/model-versions/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение списка версий моделей с опциональными фильтрами
   *
   * @param modelName - Опциональный фильтр по имени модели
   * @param isActive - Опциональный фильтр по активному статусу
   * @param isExperiment - Опциональный фильтр по экспериментальному статусу
   * @returns Список версий моделей с метаданными
   * @throws ApiError если получение списка не удалось
   *
   * @example
   * ```ts
   * // Получение всех версий
   * const allVersions = await modelVersionsClient.listModelVersions();
   *
   * // Фильтрация по имени модели
   * const skillMatching = await modelVersionsClient.listModelVersions('skill_matching');
   *
   * // Получение только активных версий
   * const activeOnly = await modelVersionsClient.listModelVersions(undefined, true);
   *
   * // Получение экспериментальных версий
   * const experiments = await modelVersionsClient.listModelVersions(undefined, undefined, true);
   * ```
   */
  async listModelVersions(
    modelName?: string,
    isActive?: boolean,
    isExperiment?: boolean
  ): Promise<ModelVersionListResponse> {
    try {
      const params: Record<string, string | boolean> = {};
      if (modelName) params.model_name = modelName;
      if (isActive !== undefined) params.is_active = isActive;
      if (isExperiment !== undefined) params.is_experiment = isExperiment;

      const response: AxiosResponse<ModelVersionListResponse> = await this.client.get(
        '/api/model-versions/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение активной версии модели по имени
   *
   * @param modelName - Имя модели
   * @returns Активная версия модели
   * @throws ApiError если активная версия не найдена
   *
   * @example
   * ```ts
   * const active = await modelVersionsClient.getActiveModel('skill_matching');
   * console.log('Активная версия:', active.version);
   * console.log('Оценка производительности:', active.performance_score);
   * ```
   */
  async getActiveModel(modelName: string): Promise<ModelVersionResponse> {
    try {
      const response: AxiosResponse<ModelVersionResponse> = await this.client.get(
        '/api/model-versions/active',
        { params: { model_name: modelName } }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение версии модели по ID
   *
   * @param id - ID версии модели
   * @returns Данные версии модели
   * @throws ApiError если версия не найдена
   *
   * @example
   * ```ts
   * const version = await modelVersionsClient.getModelVersion('version-123');
   * console.log('Версия:', version.version);
   * console.log('Активна:', version.is_active);
   * ```
   */
  async getModelVersion(id: string): Promise<ModelVersionResponse> {
    try {
      const response: AxiosResponse<ModelVersionResponse> = await this.client.get(
        `/api/model-versions/${id}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Обновление версии модели
   *
   * @param id - ID версии модели
   * @param request - Запрос на обновление
   * @returns Обновленная версия модели
   * @throws ApiError если обновление не удалось
   *
   * @example
   * ```ts
   * const updated = await modelVersionsClient.updateModelVersion('version-123', {
   *   performance_score: 95.0,
   *   is_experiment: false,
   * });
   * ```
   */
  async updateModelVersion(
    id: string,
    request: ModelVersionUpdate
  ): Promise<ModelVersionResponse> {
    try {
      const response: AxiosResponse<ModelVersionResponse> = await this.client.put(
        `/api/model-versions/${id}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Удаление версии модели
   *
   * @param id - ID версии модели
   * @throws ApiError если удаление не удалось
   *
   * @example
   * ```ts
   * await modelVersionsClient.deleteModelVersion('version-123');
   * ```
   */
  async deleteModelVersion(id: string): Promise<void> {
    try {
      await this.client.delete(`/api/model-versions/${id}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Активация версии модели
   *
   * Активирует указанную версию модели. Предыдущая активная версия
   * будет автоматически деактивирована.
   *
   * @param id - ID версии модели
   * @returns Обновленная версия модели
   * @throws ApiError если активация не удалась
   *
   * @example
   * ```ts
   * const activated = await modelVersionsClient.activateModelVersion('version-123');
   * console.log('Версия активирована:', activated.is_active);
   * ```
   */
  async activateModelVersion(id: string): Promise<ModelVersionResponse> {
    try {
      const response: AxiosResponse<ModelVersionResponse> = await this.client.post(
        `/api/model-versions/${id}/activate`,
        {}
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Деактивация версии модели
   *
   * @param id - ID версии модели
   * @returns Обновленная версия модели
   * @throws ApiError если деактивация не удалась
   *
   * @example
   * ```ts
   * const deactivated = await modelVersionsClient.deactivateModelVersion('version-123');
   * console.log('Версия деактивирована:', !deactivated.is_active);
   * ```
   */
  async deactivateModelVersion(id: string): Promise<ModelVersionResponse> {
    try {
      const response: AxiosResponse<ModelVersionResponse> = await this.client.post(
        `/api/model-versions/${id}/deactivate`,
        {}
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
 * Экземпляр клиента версий моделей по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех операций с версиями моделей.
 */
export const modelVersionsClient = new ModelVersionsClient();

/**
 * Экспорт класса для создания кастомных экземпляров
 */
export default ModelVersionsClient;
