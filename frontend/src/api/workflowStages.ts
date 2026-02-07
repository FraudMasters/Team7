/**
 * Workflow Stages API Client
 *
 * Этот модуль предоставляет клиент для управления специфичными для организации
 * этапами workflow найма, включая создание, чтение, обновление и удаление
 * конфигураций этапов workflow.
 *
 * @example
 * ```ts
 * import { workflowStagesClient } from '@/api/workflowStages';
 *
 * // Получение всех этапов workflow для организации
 * const stages = await workflowStagesClient.listStages('org-123');
 *
 * // Создание нового этапа workflow
 * const newStage = await workflowStagesClient.createStage({
 *   organization_id: 'org-123',
 *   stage_name: 'Техническое собеседование',
 *   stage_order: 3,
 *   is_active: true,
 *   color: '#3B82F6',
 *   description: 'Техническая оценка с командой инженеров'
 * });
 *
 * // Обновление этапа workflow
 * const updated = await workflowStagesClient.updateStage('stage-id', {
 *   stage_name: 'Обновленное техническое собеседование',
 *   is_active: false
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  WorkflowStageCreate,
  WorkflowStageUpdate,
  WorkflowStageResponse,
  WorkflowStageListResponse,
  ApiError,
} from '@/types/api';

/**
 * Конфигурация по умолчанию для клиента этапов workflow
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 10000, // 10 секунд
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для работы с этапами workflow
 *
 * Предоставляет методы для управления конфигурациями этапов workflow с proper
 * обработкой ошибок и типобезопасностью.
 */
export class WorkflowStagesClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента этапов workflow
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
      409: 'Этап workflow с таким названием уже существует.',
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
   * Создание этапа workflow для организации
   *
   * @param request - Запрос на создание с деталями этапа workflow
   * @returns Созданный этап workflow
   * @throws ApiError если создание не удалось
   *
   * @example
   * ```ts
   * const stage = await workflowStagesClient.createStage({
   *   organization_id: 'org-123',
   *   stage_name: 'Техническое собеседование',
   *   stage_order: 3,
   *   is_active: true,
   *   color: '#3B82F6',
   *   description: 'Техническая оценка с командой инженеров'
   * });
   * ```
   */
  async createStage(request: WorkflowStageCreate): Promise<WorkflowStageResponse> {
    try {
      const response: AxiosResponse<WorkflowStageResponse> = await this.client.post(
        '/api/workflow-stages/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение списка этапов workflow с опциональными фильтрами
   *
   * @param organizationId - Опциональный фильтр по ID организации
   * @param isActive - Опциональный фильтр по активному статусу
   * @param isDefault - Опциональный фильтр по статусу по умолчанию
   * @returns Список этапов workflow
   * @throws ApiError если получение списка не удалось
   *
   * @example
   * ```ts
   * // Получение всех этапов для организации
   * const stages = await workflowStagesClient.listStages('org-123');
   *
   * // Получение только активных этапов
   * const activeStages = await workflowStagesClient.listStages('org-123', true);
   * ```
   */
  async listStages(
    organizationId?: string,
    isActive?: boolean,
    isDefault?: boolean
  ): Promise<WorkflowStageListResponse> {
    try {
      const params: Record<string, string | boolean> = {};
      if (organizationId) params.organization_id = organizationId;
      if (isActive !== undefined) params.is_active = isActive;
      if (isDefault !== undefined) params.is_default = isDefault;

      const response: AxiosResponse<WorkflowStageListResponse> = await this.client.get(
        '/api/workflow-stages/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение конкретного этапа workflow по ID
   *
   * @param stageId - ID этапа workflow
   * @returns Детали этапа workflow
   * @throws ApiError если этап не найден
   *
   * @example
   * ```ts
   * const stage = await workflowStagesClient.getStage('stage-uuid');
   * ```
   */
  async getStage(stageId: string): Promise<WorkflowStageResponse> {
    try {
      const response: AxiosResponse<WorkflowStageResponse> = await this.client.get(
        `/api/workflow-stages/${stageId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Обновление этапа workflow
   *
   * @param stageId - ID этапа workflow
   * @param request - Запрос на обновление с полями для изменения
   * @returns Обновленный этап workflow
   * @throws ApiError если обновление не удалось
   *
   * @example
   * ```ts
   * const updated = await workflowStagesClient.updateStage('stage-uuid', {
   *   stage_name: 'Обновленное техническое собеседование',
   *   is_active: false
   * });
   * ```
   */
  async updateStage(
    stageId: string,
    request: WorkflowStageUpdate
  ): Promise<WorkflowStageResponse> {
    try {
      const response: AxiosResponse<WorkflowStageResponse> = await this.client.put(
        `/api/workflow-stages/${stageId}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Удаление этапа workflow
   *
   * @param stageId - ID этапа workflow
   * @throws ApiError если удаление не удалось
   *
   * @example
   * ```ts
   * await workflowStagesClient.deleteStage('stage-uuid');
   * ```
   */
  async deleteStage(stageId: string): Promise<void> {
    try {
      await this.client.delete(`/api/workflow-stages/${stageId}`);
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
 * Экземпляр клиента этапов workflow по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех операций с этапами workflow.
 */
export const workflowStagesClient = new WorkflowStagesClient();

/**
 * Экспорт класса этапов workflow для создания кастомных экземпляров
 */
export default WorkflowStagesClient;
