/**
 * Resume Builder API Client
 *
 * Этот модуль предоставляет клиент для работы с конструктором резюме.
 * Поддерживает создание, редактирование, экспорт резюме, AI-предложения
 * по улучшению, ATS-оптимизацию и анализ пробелов в навыках.
 *
 * @example
 * ```ts
 * import { resumeBuilderClient, ResumeBuilderClient } from '@/api/resumeBuilder';
 *
 * // Создание нового резюме
 * const resume = await resumeBuilderClient.createResume({
 *   title: 'My Resume',
 *   is_draft: true,
 * });
 *
 * // Получение AI-предложений
 * const suggestions = await resumeBuilderClient.getAISuggestions(resume.id);
 *
 * // Экспорт в PDF
 * const exportResult = await resumeBuilderClient.exportResume(resume.id, 'pdf');
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type { ApiError } from '@/types/api';
import type {
  BuiltResumeCreate,
  BuiltResumeUpdate,
  BuiltResumeResponse,
  BuiltResumeListResponse,
  AISuggestionsResponse,
  ApplySuggestionRequest,
  ATSScoreResponse,
  ResumeSkillGapAnalysisResponse,
  ExportFormat,
  ExportResponse,
  ResumeTemplateListResponse,
  ResumeVersionHistoryResponse,
} from '@/types/resumeBuilder';

/**
 * Параметры для списка резюме
 */
export interface ResumeListParams {
  /** Номер страницы (начиная с 1) */
  page?: number;
  /** Размер страницы */
  page_size?: number;
  /** Фильтр по черновикам */
  is_draft?: boolean;
}

/**
 * Переэкспорт типов для удобства использования
 */
export type {
  BuiltResumeCreate,
  BuiltResumeUpdate,
  BuiltResumeResponse,
  BuiltResumeListResponse,
  AISuggestionsResponse,
  ApplySuggestionRequest,
  ATSScoreResponse,
  ResumeSkillGapAnalysisResponse,
  ExportFormat,
  ExportResponse,
  ResumeTemplateListResponse,
  ResumeVersionHistoryResponse,
  ResumeListParams,
};

/**
 * Конфигурация по умолчанию для клиента конструктора резюме
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_GATEWAY_URL ?? 'http://localhost:8888',
  timeout: 60000, // 60 секунд (AI-операции могут занимать больше времени)
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для конструктора резюме
 *
 * Предоставляет методы для создания, редактирования и экспорта резюме
 * с proper обработкой ошибок и типобезопасностью.
 */
export class ResumeBuilderClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента конструктора резюме
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
      404: 'Резюме не найдено.',
      409: 'Конфликт. Резюме с таким названием уже существует.',
      413: 'Файл слишком большой. Максимальный размер: 10 МБ.',
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

  // =============================================================================
  // CRUD Operations
  // =============================================================================

  /**
   * Создание нового резюме
   *
   * @param data - Данные для создания резюме
   * @returns Созданное резюме
   * @throws ApiError если создание не удалось
   *
   * @example
   * ```ts
   * const resume = await resumeBuilderClient.createResume({
   *   title: 'My Resume',
   *   is_draft: true,
   *   template_id: 'template-123',
   * });
   * ```
   */
  async createResume(data: BuiltResumeCreate): Promise<BuiltResumeResponse> {
    const response: AxiosResponse<BuiltResumeResponse> = await this.client.post(
      '/api/resume-builder/',
      data
    );
    return response.data;
  }

  /**
   * Получение списка резюме пользователя
   *
   * @param params - Параметры пагинации и фильтрации
   * @returns Список резюме с пагинацией
   * @throws ApiError если запрос не удался
   *
   * @example
   * ```ts
   * const result = await resumeBuilderClient.listResumes({ page: 1, page_size: 10 });
   * console.log(`Найдено ${result.total} резюме`);
   * ```
   */
  async listResumes(params?: ResumeListParams): Promise<BuiltResumeListResponse> {
    const response: AxiosResponse<BuiltResumeListResponse> = await this.client.get(
      '/api/resume-builder/',
      { params }
    );
    return response.data;
  }

  /**
   * Получение резюме по ID
   *
   * @param id - ID резюме
   * @returns Резюме с полными данными
   * @throws ApiError если резюме не найдено
   *
   * @example
   * ```ts
   * const resume = await resumeBuilderClient.getResume('resume-123');
   * console.log(resume.title, resume.ats_score);
   * ```
   */
  async getResume(id: string): Promise<BuiltResumeResponse> {
    const response: AxiosResponse<BuiltResumeResponse> = await this.client.get(
      `/api/resume-builder/${id}`
    );
    return response.data;
  }

  /**
   * Обновление резюме
   *
   * @param id - ID резюме
   * @param data - Данные для обновления
   * @returns Обновленное резюме
   * @throws ApiError если обновление не удалось
   *
   * @example
   * ```ts
   * const updated = await resumeBuilderClient.updateResume('resume-123', {
   *   title: 'Updated Title',
   *   is_draft: false,
   * });
   * ```
   */
  async updateResume(id: string, data: BuiltResumeUpdate): Promise<BuiltResumeResponse> {
    const response: AxiosResponse<BuiltResumeResponse> = await this.client.put(
      `/api/resume-builder/${id}`,
      data
    );
    return response.data;
  }

  /**
   * Удаление резюме
   *
   * @param id - ID резюме
   * @throws ApiError если удаление не удалось
   *
   * @example
   * ```ts
   * await resumeBuilderClient.deleteResume('resume-123');
   * ```
   */
  async deleteResume(id: string): Promise<void> {
    await this.client.delete(`/api/resume-builder/${id}`);
  }

  /**
   * Дублирование резюме
   *
   * @param id - ID резюме для дублирования
   * @returns Новое скопированное резюме
   * @throws ApiError если дублирование не удалось
   *
   * @example
   * ```ts
   * const copy = await resumeBuilderClient.duplicateResume('resume-123');
   * console.log(`Создана копия: ${copy.title}`);
   * ```
   */
  async duplicateResume(id: string): Promise<BuiltResumeResponse> {
    const response: AxiosResponse<BuiltResumeResponse> = await this.client.post(
      `/api/resume-builder/${id}/duplicate`
    );
    return response.data;
  }

  // =============================================================================
  // AI Features
  // =============================================================================

  /**
   * Получение AI-предложений по улучшению резюме
   *
   * @param id - ID резюме
   * @returns Список предложений с приоритетами и оценкой влияния
   * @throws ApiError если получение не удалось
   *
   * @example
   * ```ts
   * const suggestions = await resumeBuilderClient.getAISuggestions('resume-123');
   * console.log(`ATS Score Impact: ${suggestions.ats_score_potential}`);
   * suggestions.suggestions.forEach(s => console.log(s.suggested_text));
   * ```
   */
  async getAISuggestions(id: string): Promise<AISuggestionsResponse> {
    const response: AxiosResponse<AISuggestionsResponse> = await this.client.get(
      `/api/resume-builder/${id}/suggestions`
    );
    return response.data;
  }

  /**
   * Применение AI-предложения к резюме
   *
   * @param id - ID резюме
   * @param data - Данные предложения для применения
   * @returns Обновленное резюме
   * @throws ApiError если применение не удалось
   *
   * @example
   * ```ts
   * const updated = await resumeBuilderClient.applySuggestion('resume-123', {
   *   suggestion_id: 'suggestion-456',
   * });
   * ```
   */
  async applySuggestion(
    id: string,
    data: ApplySuggestionRequest
  ): Promise<BuiltResumeResponse> {
    const response: AxiosResponse<BuiltResumeResponse> = await this.client.post(
      `/api/resume-builder/${id}/suggestions/apply`,
      data
    );
    return response.data;
  }

  /**
   * Расчет ATS-оценки резюме
   *
   * @param id - ID резюме
   * @returns ATS-оценка с детальным анализом
   * @throws ApiError если расчет не удался
   *
   * @example
   * ```ts
   * const atsResult = await resumeBuilderClient.calculateATSScore('resume-123');
   * console.log(`ATS Score: ${atsResult.score}`);
   * console.log(`Missing keywords: ${atsResult.keywords_missing.join(', ')}`);
   * ```
   */
  async calculateATSScore(id: string): Promise<ATSScoreResponse> {
    const response: AxiosResponse<ATSScoreResponse> = await this.client.get(
      `/api/resume-builder/${id}/ats-score`
    );
    return response.data;
  }

  /**
   * Анализ пробелов в навыках относительно целевой вакансии
   *
   * @param id - ID резюме
   * @param targetJobId - ID целевой вакансии
   * @returns Анализ пробелов с рекомендациями по обучению
   * @throws ApiError если анализ не удался
   *
   * @example
   * ```ts
   * const analysis = await resumeBuilderClient.analyzeSkillGaps('resume-123', 'vacancy-456');
   * console.log(`Match: ${analysis.match_percentage}%`);
   * analysis.missing_skills.forEach(skill => console.log(skill.skill_name));
   * ```
   */
  async analyzeSkillGaps(
    id: string,
    targetJobId: string
  ): Promise<ResumeSkillGapAnalysisResponse> {
    const response: AxiosResponse<ResumeSkillGapAnalysisResponse> = await this.client.get(
      `/api/resume-builder/${id}/skill-gap`,
      { params: { target_job_id: targetJobId } }
    );
    return response.data;
  }

  // =============================================================================
  // Export
  // =============================================================================

  /**
   * Экспорт резюме в указанный формат
   *
   * @param id - ID резюме
   * @param format - Формат экспорта (pdf, docx, json)
   * @returns Информация о скачанном файле
   * @throws ApiError если экспорт не удался
   *
   * @example
   * ```ts
   * // Экспорт в PDF
   * const pdfExport = await resumeBuilderClient.exportResume('resume-123', 'pdf');
   * window.open(pdfExport.download_url);
   *
   * // Экспорт в DOCX
   * const docxExport = await resumeBuilderClient.exportResume('resume-123', 'docx');
   * ```
   */
  async exportResume(id: string, format: ExportFormat): Promise<ExportResponse> {
    const response: AxiosResponse<ExportResponse> = await this.client.post(
      `/api/resume-builder/${id}/export`,
      { format }
    );
    return response.data;
  }

  // =============================================================================
  // Version Management
  // =============================================================================

  /**
   * Получение истории версий резюме
   *
   * @param id - ID резюме
   * @returns История версий резюме
   * @throws ApiError если получение не удалось
   *
   * @example
   * ```ts
   * const history = await resumeBuilderClient.getVersionHistory('resume-123');
   * console.log(`Current version: ${history.current_version}`);
   * history.versions.forEach(v => console.log(`v${v.version}: ${v.title}`));
   * ```
   */
  async getVersionHistory(id: string): Promise<ResumeVersionHistoryResponse> {
    const response: AxiosResponse<ResumeVersionHistoryResponse> = await this.client.get(
      `/api/resume-builder/${id}/versions`
    );
    return response.data;
  }

  // =============================================================================
  // Templates
  // =============================================================================

  /**
   * Получение списка доступных шаблонов резюме
   *
   * @returns Список шаблонов с превью
   * @throws ApiError если получение не удалось
   *
   * @example
   * ```ts
   * const templates = await resumeBuilderClient.getTemplates();
   * templates.items.forEach(t => console.log(`${t.name} (premium: ${t.is_premium})`));
   * ```
   */
  async getTemplates(): Promise<ResumeTemplateListResponse> {
    const response: AxiosResponse<ResumeTemplateListResponse> = await this.client.get(
      '/api/resume-builder/templates'
    );
    return response.data;
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
 * Экземпляр клиента конструктора резюме по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех операций с конструктором резюме.
 */
export const resumeBuilderClient = new ResumeBuilderClient();

/**
 * Экспорт класса для создания кастомных экземпляров
 */
export default ResumeBuilderClient;
