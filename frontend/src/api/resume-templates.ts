/**
 * Resume Templates API Client
 *
 * Этот модуль предоставляет клиент для работы с шаблонами резюме через микросервис Resume Processing Service.
 * Поддерживает полный цикл управления шаблонами: создание, просмотр списка, просмотр деталей,
 * обновление и удаление.
 *
 * @example
 * ```ts
 * import { resumeTemplatesClient, ResumeTemplatesClient } from '@/api/resume-templates';
 *
 * // Получение списка всех шаблонов
 * const templates = await resumeTemplatesClient.listResumeTemplates();
 *
 * // Создание нового шаблона
 * const created = await resumeTemplatesClient.createResumeTemplate({
 *   name: 'Modern Professional',
 *   template_type: 'modern',
 *   description: 'Clean modern design with sidebar',
 *   is_ats_compliant: true
 * });
 *
 * // Получение шаблона по ID
 * const template = await resumeTemplatesClient.getResumeTemplate('template-123');
 *
 * // Обновление шаблона
 * const updated = await resumeTemplatesClient.updateResumeTemplate('template-123', {
 *   name: 'Updated Modern Professional'
 * });
 *
 * // Удаление шаблона
 * await resumeTemplatesClient.deleteResumeTemplate('template-123');
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type { ApiError } from '@/types/api';

/**
 * Configuration for resume template layout
 */
export interface LayoutConfig {
  margins?: string;
  sections?: string[];
  spacing?: Record<string, number>;
  [key: string]: unknown;
}

/**
 * Configuration for resume template styling
 */
export interface StyleConfig {
  primary_color?: string;
  secondary_color?: string;
  font?: string;
  font_size?: number;
  heading_font?: string;
  [key: string]: unknown;
}

/**
 * Configuration for resume template sections
 */
export interface SectionConfig {
  [sectionName: string]: {
    enabled?: boolean;
    position?: string;
    order?: number;
    [key: string]: unknown;
  };
}

/**
 * Resume template create request
 */
export interface ResumeTemplateCreate {
  organization_id?: string | null;
  name: string;
  description?: string | null;
  template_type: string;
  layout_config?: LayoutConfig | null;
  style_config?: StyleConfig | null;
  section_config?: SectionConfig | null;
  preview_url?: string | null;
  is_default?: boolean;
  is_active?: boolean;
  is_ats_compliant?: boolean;
  created_by?: string | null;
}

/**
 * Resume template update request
 */
export interface ResumeTemplateUpdate {
  name?: string;
  description?: string | null;
  layout_config?: LayoutConfig | null;
  style_config?: StyleConfig | null;
  section_config?: SectionConfig | null;
  preview_url?: string | null;
  is_default?: boolean;
  is_active?: boolean;
  is_ats_compliant?: boolean;
}

/**
 * Resume template response
 */
export interface ResumeTemplateResponse {
  id: string;
  organization_id: string | null;
  name: string;
  description: string | null;
  template_type: string;
  layout_config: LayoutConfig | null;
  style_config: StyleConfig | null;
  section_config: SectionConfig | null;
  preview_url: string | null;
  is_default: boolean;
  is_active: boolean;
  is_ats_compliant: boolean;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Resume template list response
 */
export interface ResumeTemplateListResponse {
  templates: ResumeTemplateResponse[];
  total_count: number;
}

/**
 * Query parameters for listing resume templates
 */
export interface ResumeTemplateListParams {
  organization_id?: string | null;
  template_type?: string | null;
  is_default?: boolean;
  is_active?: boolean;
  is_ats_compliant?: boolean;
  limit?: number;
  offset?: number;
}

/**
 * Переэкспорт типов для удобства использования
 */
export type {
  ResumeTemplateCreate,
  ResumeTemplateUpdate,
  ResumeTemplateResponse,
  ResumeTemplateListResponse,
  ResumeTemplateListParams,
};

/**
 * Конфигурация по умолчанию для клиента шаблонов резюме
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_GATEWAY_URL ?? 'http://localhost:8888',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для работы с шаблонами резюме
 *
 * Предоставляет методы для создания, просмотра, обновления и удаления шаблонов резюме
 * с proper обработкой ошибок и типобезопасностью.
 */
export class ResumeTemplatesClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента шаблонов резюме
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
      404: 'Шаблон резюме не найден.',
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
   * Получение списка шаблонов резюме с фильтрацией и пагинацией
   *
   * @param params - Параметры фильтрации и пагинации
   * @returns Список шаблонов резюме с метаданными
   * @throws ApiError если получение списка не удалось
   *
   * @example
   * ```ts
   * // Получение всех ATS-дружественных шаблонов
   * const atsTemplates = await resumeTemplatesClient.listResumeTemplates({
   *   is_ats_compliant: true
   * });
   *
   * // Получение шаблонов определенного типа с пагинацией
   * const modernTemplates = await resumeTemplatesClient.listResumeTemplates({
   *   template_type: 'modern',
   *   limit: 10,
   *   offset: 0
   * });
   * ```
   */
  async listResumeTemplates(
    params: ResumeTemplateListParams = {}
  ): Promise<ResumeTemplateListResponse> {
    try {
      const {
        organization_id,
        template_type,
        is_default,
        is_active = true,
        is_ats_compliant,
        limit = 100,
        offset = 0,
      } = params;

      const queryParams: Record<string, string | number | boolean> = {
        limit,
        offset,
      };

      if (organization_id !== undefined) {
        queryParams.organization_id = organization_id;
      }
      if (template_type !== undefined) {
        queryParams.template_type = template_type;
      }
      if (is_default !== undefined) {
        queryParams.is_default = is_default;
      }
      if (is_active !== undefined) {
        queryParams.is_active = is_active;
      }
      if (is_ats_compliant !== undefined) {
        queryParams.is_ats_compliant = is_ats_compliant;
      }

      const response: AxiosResponse<ResumeTemplateListResponse> = await this.client.get(
        '/api/resume-templates/',
        { params: queryParams }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение шаблона резюме по ID
   *
   * @param template_id - ID шаблона резюме
   * @returns Данные шаблона резюме
   * @throws ApiError если шаблон не найден
   *
   * @example
   * ```ts
   * const template = await resumeTemplatesClient.getResumeTemplate('template-123');
   * console.log(template.name, template.template_type);
   * ```
   */
  async getResumeTemplate(template_id: string): Promise<ResumeTemplateResponse> {
    try {
      const response: AxiosResponse<ResumeTemplateResponse> = await this.client.get(
        `/api/resume-templates/${template_id}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Создание нового шаблона резюме
   *
   * Поддерживает создание кастомных шаблонов с уникальными настройками
   * layout, style и section configurations.
   *
   * @param data - Данные для создания шаблона
   * @returns Созданный шаблон резюме
   * @throws ApiError если создание не удалось
   *
   * @example
   * ```ts
   * const created = await resumeTemplatesClient.createResumeTemplate({
   *   name: 'Modern Professional',
   *   template_type: 'modern',
   *   description: 'Clean modern design with sidebar',
   *   is_ats_compliant: true,
   *   layout_config: {
   *     margins: 'normal',
   *     sections: ['header', 'experience', 'skills']
   *   },
   *   style_config: {
   *     primary_color: '#2563eb',
   *     font: 'Arial'
   *   }
   * });
   * console.log('Создан шаблон с ID:', created.id);
   * ```
   */
  async createResumeTemplate(
    data: ResumeTemplateCreate
  ): Promise<ResumeTemplateResponse> {
    try {
      const response: AxiosResponse<ResumeTemplateResponse> = await this.client.post(
        '/api/resume-templates/',
        data
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Обновление шаблона резюме
   *
   * Обновляет указанные поля шаблона резюме. Только переданные поля будут изменены.
   *
   * @param template_id - ID шаблона резюме
   * @param data - Данные для обновления шаблона
   * @returns Обновленный шаблон резюме
   * @throws ApiError если обновление не удалось
   *
   * @example
   * ```ts
   * // Обновление цвета и шрифта
   * const updated = await resumeTemplatesClient.updateResumeTemplate('template-123', {
   *   style_config: {
   *     primary_color: '#dc2626',
   *     font: 'Helvetica'
   *   }
   * });
   *
   * // Обновление названия
   * const renamed = await resumeTemplatesClient.updateResumeTemplate('template-123', {
   *   name: 'Updated Modern Professional'
   * });
   * ```
   */
  async updateResumeTemplate(
    template_id: string,
    data: ResumeTemplateUpdate
  ): Promise<ResumeTemplateResponse> {
    try {
      const response: AxiosResponse<ResumeTemplateResponse> = await this.client.put(
        `/api/resume-templates/${template_id}`,
        data
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Удаление шаблона резюме
   *
   * @param template_id - ID шаблона резюме
   * @throws ApiError если удаление не удалось
   *
   * @example
   * ```ts
   * await resumeTemplatesClient.deleteResumeTemplate('template-123');
   * ```
   */
  async deleteResumeTemplate(template_id: string): Promise<{ message: string; id: string }> {
    try {
      const response: AxiosResponse<{ message: string; id: string }> = await this.client.delete(
        `/api/resume-templates/${template_id}`
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
 * Экземпляр клиента шаблонов резюме по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех операций с шаблонами резюме.
 */
export const resumeTemplatesClient = new ResumeTemplatesClient();

/**
 * Экспорт класса для создания кастомных экземпляров
 */
export default ResumeTemplatesClient;
