/**
 * API Client для резюме и вакансий
 *
 * Этот модуль предоставляет типизированный Axios клиент для взаимодействия с
 * backend сервисами. Обрабатывает загрузку резюме, анализ, сравнение с вакансиями,
 * работу с таксономиями навыков, кастомными синонимами, обратной связью,
 * версиями моделей, сравнениями резюме и проверку работоспособности.
 *
 * @example
 * ```ts
 * import { apiClient } from '@/api/client';
 *
 * // Загрузка резюме
 * const uploadResult = await apiClient.uploadResume(file);
 *
 * // Анализ резюме
 * const analysis = await apiClient.analyzeResume(uploadResult.id);
 *
 * // Сравнение с вакансией
 * const match = await apiClient.compareWithVacancy(resumeId, vacancyData);
 *
 * // Сравнение нескольких резюме
 * const comparison = await apiClient.compareMultipleResumes({
 *   vacancy_id: 'vacancy-123',
 *   resume_ids: ['resume1', 'resume2', 'resume3'],
 * });
 *
 * // Создание кастомных синонимов
 * const synonyms = await apiClient.createCustomSynonyms({
 *   organization_id: 'org123',
 *   synonyms: [{ canonical_skill: 'React', custom_synonyms: ['ReactJS'], is_active: true }],
 * });
 *
 * // Отправка обратной связи
 * const feedback = await apiClient.submitMatchFeedback({
 *   match_id: 'match123',
 *   skill: 'React',
 *   was_correct: true,
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import {
  trackApiCall,
  logMetricsSummary,
  getPerformanceStats as getPerformanceStatsUtil,
  type PerformanceStats,
} from '@/utils/performanceTracker';
import type {
  ResumeUploadResponse,
  AnalysisRequest,
  AnalysisResponse,
  JobVacancy,
  MatchResponse,
  HealthResponse,
  UploadProgressCallback,
  ApiClientConfig,
  ApiError,
  SkillTaxonomyCreate,
  SkillTaxonomyUpdate,
  SkillTaxonomyResponse,
  SkillTaxonomyListResponse,
  CustomSynonymCreate,
  CustomSynonymUpdate,
  CustomSynonymResponse,
  CustomSynonymListResponse,
  FeedbackCreate,
  FeedbackUpdate,
  FeedbackResponse,
  FeedbackListResponse,
  ModelVersionCreate,
  ModelVersionUpdate,
  ModelVersionResponse,
  ModelVersionListResponse,
  MatchFeedbackRequest,
  MatchFeedbackResponse,
  ComparisonCreate,
  ComparisonUpdate,
  ComparisonResponse,
  ComparisonListResponse,
  CompareMultipleRequest,
  ComparisonMatrixData,
  KeyMetricsResponse,
  FunnelMetricsResponse,
  SkillDemandResponse,
  SourceTrackingResponse,
  RecruiterPerformanceResponse,
  LanguagePreferenceUpdate,
  LanguagePreferenceResponse,
  MatchingWeightsProfile,
  MatchingWeightsCreate,
  MatchingWeightsUpdate,
  MatchingWeightsListResponse,
  PresetProfile,
  PresetsResponse,
  WeightVersionEntry,
  VersionHistoryResponse,
  NormalizeWeightsRequest,
  NormalizedWeightsResponse,
  ApplyWeightsRequest,
  ApplyWeightsResponse,
  ATSEvaluationRequest,
  ATSEvaluationResponse,
  BatchATSEvaluationRequest,
  BatchATSEvaluationResponse,
  ATSConfigResponse,
  ATSResultListResponse,
  WorkflowStageCreate,
  WorkflowStageUpdate,
  WorkflowStageResponse,
  WorkflowStageListResponse,
  CandidateListItem,
  MoveCandidateRequest,
  MoveCandidateResponse,
} from '@/types/api';

/**
 * Конфигурация API по умолчанию
 *
 * API Gateway работает на порту 8888 для агрегации сервисов
 */
const DEFAULT_CONFIG: ApiClientConfig = {
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8888',
  timeout: 120000, // 2 минуты для длительного анализа
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс API клиента
 *
 * Предоставляет методы для всех endpoint'ов backend API с proper обработкой ошибок,
 * типобезопасностью и отслеживанием прогресса загрузки файлов.
 */
export class ApiClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра API клиента
   *
   * @param config - Опциональные переопределения конфигурации
   */
  constructor(config: ApiClientConfig = {}) {
    const finalConfig = { ...DEFAULT_CONFIG, ...config };

    this.client = axios.create(finalConfig);

    // Интерцептор запросов
    this.client.interceptors.request.use(
      (config) => {
        // Добавление метки времени для отладки
        config.metadata = { startTime: Date.now() };
        return config;
      },
      (error) => {
        return Promise.reject(this.transformError(error));
      }
    );

    // Интерцептор ответов
    this.client.interceptors.response.use(
      (response) => {
        // Вычисление длительности запроса
        const duration = Date.now() - (response.config.metadata?.startTime || 0);
        response.config.metadata = { ...response.config.metadata, duration };

        // Отслеживание метрик производительности
        trackApiCall({
          endpoint: response.config.url || '',
          method: (response.config.method?.toUpperCase() || 'GET'),
          duration,
          status: response.status,
          success: true,
          timestamp: Date.now(),
          responseSize: response.headers['content-length']
            ? parseInt(response.headers['content-length'], 10)
            : undefined,
        });

        return response;
      },
      (error) => {
        // Вычисление длительности запроса для неудачных запросов
        const duration = Date.now() - (error.config?.metadata?.startTime || 0);

        // Отслеживание метрик неудачных запросов
        if (error.config) {
          trackApiCall({
            endpoint: error.config.url || '',
            method: (error.config.method?.toUpperCase() || 'GET'),
            duration,
            status: error.response?.status || 0,
            success: false,
            timestamp: Date.now(),
            error: error.message,
          });
        }

        return Promise.reject(this.transformError(error));
      }
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
      403: 'Доступ запрещен. У вас нет прав.',
      404: 'Ресурс не найден.',
      413: 'Файл слишком большой. Загрузите файл меньшего размера.',
      415: 'Неподдерживаемый тип файла. Загрузите PDF или DOCX.',
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
   * Загрузка файла резюме
   *
   * @param file - Файл резюме (PDF или DOCX)
   * @param onProgress - Опциональный колбэк прогресса (0-100)
   * @returns Ответ загрузки с ID резюме
   * @throws ApiError если загрузка не удалась
   *
   * @example
   * ```ts
   * const result = await apiClient.uploadResume(file, (progress) => {
   *   console.log(`Прогресс загрузки: ${progress}%`);
   * });
   * ```
   */
  async uploadResume(
    file: File,
    onProgress?: UploadProgressCallback
  ): Promise<ResumeUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response: AxiosResponse<ResumeUploadResponse> = await this.client.post(
        '/api/resumes/upload',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total && onProgress) {
              const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
              onProgress(progress);
            }
          },
        }
      );

      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Анализ резюме
   *
   * @param request - Запрос на анализ с ID резюме и опциями
   * @returns Результаты анализа с ключевыми словами, сущностями, грамматикой и опытом
   * @throws ApiError если анализ не удался
   *
   * @example
   * ```ts
   * const analysis = await apiClient.analyzeResume({
   *   resume_id: 'abc-123',
   *   extract_experience: true,
   *   check_grammar: true,
   * });
   * ```
   */
  async analyzeResume(request: AnalysisRequest): Promise<AnalysisResponse> {
    try {
      const response: AxiosResponse<AnalysisResponse> = await this.client.post(
        '/api/resumes/analyze',
        request
      );

      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Сравнение резюме с вакансией
   *
   * @param resumeId - ID резюме для сравнения
   * @param vacancy - Данные вакансии
   * @returns Результаты сравнения с процентом мэтча и детализацией по навыкам
   * @throws ApiError если сравнение не удалось
   *
   * @example
   * ```ts
   * const match = await apiClient.compareWithVacancy('abc-123', {
   *   data: {
   *     position: 'Java Developer',
   *     mandatory_requirements: ['Java', 'Spring', 'SQL'],
   *   },
   * });
   * ```
   */
  async compareWithVacancy(resumeId: string, vacancy: JobVacancy): Promise<MatchResponse> {
    try {
      const response: AxiosResponse<MatchResponse> = await this.client.post(
        '/api/matching/compare',
        {
          resume_id: resumeId,
          vacancy_data: vacancy,
        }
      );

      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Проверка работоспособности backend
   *
   * @returns Статус работоспособности
   * @throws ApiError если проверка не удалась
   */
  async healthCheck(): Promise<HealthResponse> {
    try {
      const response: AxiosResponse<HealthResponse> = await this.client.get('/health');
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Проверка готовности backend
   *
   * @returns Статус готовности
   * @throws ApiError если проверка не удалась
   */
  async readyCheck(): Promise<{ status: string }> {
    try {
      const response: AxiosResponse<{ status: string }> = await this.client.get('/ready');
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

  /**
   * Получение статистики производительности API
   *
   * Возвращает метрики производительности для всех API вызовов через этот клиент.
   * Полезно для мониторинга и отладки проблем с производительностью.
   *
   * @returns Статистика производительности
   *
   * @example
   * ```ts
   * const stats = apiClient.getPerformanceStats();
   * console.log(`Средняя длительность: ${stats.averageDuration}мс`);
   * console.log(`Всего вызовов: ${stats.totalCalls}`);
   * ```
   */
  getPerformanceStats(): PerformanceStats {
    return getPerformanceStatsUtil();
  }

  /**
   * Вывод сводки производительности API в консоль
   *
   * Выводит форматированную сводку всех метрик производительности API в консоль.
   * Полезно для разработки и отладки.
   *
   * @example
   * ```ts
   * apiClient.logPerformanceSummary();
   * // Вывод:
   * // [Сводка производительности API]
   * // Всего вызовов: 45
   * // Средняя длительность: 245мс
   * ```
   */
  logPerformanceSummary(): void {
    logMetricsSummary();
  }

  /**
   * Generic POST запрос для кастомных endpoint'ов
   *
   * @param url - URL endpoint'а
   * @param data - Тело запроса
   * @returns Данные ответа
   * @throws ApiError если запрос не удался
   */
  async post<T = unknown>(url: string, data?: unknown): Promise<AxiosResponse<T>> {
    try {
      return await this.client.post<T>(url, data);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Таксономии навыков ====================

  /**
   * Создание записей таксономии навыков для индустрии
   *
   * @param request - Запрос на создание с индустрией и списком навыков
   * @returns Созданные записи таксономии
   * @throws ApiError если создание не удалось
   *
   * @example
   * ```ts
   * const result = await apiClient.createSkillTaxonomies({
   *   industry: 'tech',
   *   skills: [
   *     {
   *       name: 'React',
   *       context: 'web_framework',
   *       variants: ['React', 'ReactJS', 'React.js'],
   *       is_active: true,
   *     },
   *   ],
   * });
   * ```
   */
  async createSkillTaxonomies(
    request: SkillTaxonomyCreate
  ): Promise<SkillTaxonomyListResponse> {
    try {
      const response: AxiosResponse<SkillTaxonomyListResponse> = await this.client.post(
        '/api/skill-taxonomies/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение списка таксономий навыков с опциональными фильтрами
   *
   * @param industry - Опциональный фильтр по индустрии
   * @param isActive - Опциональный фильтр по статусу активности
   * @returns Список записей таксономии навыков
   * @throws ApiError если получение списка не удалось
   */
  async listSkillTaxonomies(
    industry?: string,
    isActive?: boolean
  ): Promise<SkillTaxonomyListResponse[]> {
    try {
      const params: Record<string, string | boolean> = {};
      if (industry) params.industry = industry;
      if (isActive !== undefined) params.is_active = isActive;

      const response: AxiosResponse<SkillTaxonomyListResponse[]> =
        await this.client.get('/api/skill-taxonomies/', { params });
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение конкретной записи таксономии навыков по ID
   *
   * @param id - ID записи таксономии
   * @returns Запись таксономии навыков
   * @throws ApiError если запись не найдена
   */
  async getSkillTaxonomy(id: string): Promise<SkillTaxonomyResponse> {
    try {
      const response: AxiosResponse<SkillTaxonomyResponse> = await this.client.get(
        `/api/skill-taxonomies/${id}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Обновление записи таксономии навыков
   *
   * @param id - ID записи таксономии
   * @param request - Запрос на обновление
   * @returns Обновленная запись таксономии
   * @throws ApiError если обновление не удалось
   */
  async updateSkillTaxonomy(
    id: string,
    request: SkillTaxonomyUpdate
  ): Promise<SkillTaxonomyResponse> {
    try {
      const response: AxiosResponse<SkillTaxonomyResponse> = await this.client.put(
        `/api/skill-taxonomies/${id}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Удаление конкретной записи таксономии навыков
   *
   * @param id - ID записи таксономии
   * @throws ApiError если удаление не удалось
   */
  async deleteSkillTaxonomy(id: string): Promise<void> {
    try {
      await this.client.delete(`/api/skill-taxonomies/${id}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Удаление всех таксономий навыков для индустрии
   *
   * @param industry - Сектор индустрии
   * @throws ApiError если удаление не удалось
   */
  async deleteSkillTaxonomiesByIndustry(industry: string): Promise<void> {
    try {
      await this.client.delete(`/api/skill-taxonomies/industry/${industry}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Кастомные синонимы ====================

  /**
   * Создание записей кастомных синонимов для организации
   *
   * @param request - Запрос на создание с organization_id и списком синонимов
   * @returns Созданные записи синонимов
   * @throws ApiError если создание не удалось
   *
   * @example
   * ```ts
   * const result = await apiClient.createCustomSynonyms({
   *   organization_id: 'org123',
   *   created_by: 'user456',
   *   synonyms: [
   *     {
   *       canonical_skill: 'React',
   *       custom_synonyms: ['ReactJS', 'React.js', 'React Framework'],
   *       context: 'web_framework',
   *       is_active: true,
   *     },
   *   ],
   * });
   * ```
   */
  async createCustomSynonyms(
    request: CustomSynonymCreate
  ): Promise<CustomSynonymListResponse> {
    try {
      const response: AxiosResponse<CustomSynonymListResponse> = await this.client.post(
        '/api/custom-synonyms/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение списка кастомных синонимов с опциональными фильтрами
   *
   * @param organizationId - Опциональный фильтр по ID организации
   * @param canonicalSkill - Опциональный фильтр по каноническому навыку
   * @param isActive - Опциональный фильтр по статусу активности
   * @returns Список записей кастомных синонимов
   * @throws ApiError если получение списка не удалось
   */
  async listCustomSynonyms(
    organizationId?: string,
    canonicalSkill?: string,
    isActive?: boolean
  ): Promise<CustomSynonymListResponse[]> {
    try {
      const params: Record<string, string | boolean> = {};
      if (organizationId) params.organization_id = organizationId;
      if (canonicalSkill) params.canonical_skill = canonicalSkill;
      if (isActive !== undefined) params.is_active = isActive;

      const response: AxiosResponse<CustomSynonymListResponse[]> =
        await this.client.get('/api/custom-synonyms/', { params });
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение конкретной записи кастомных синонимов по ID
   *
   * @param id - ID записи синонимов
   * @returns Запись кастомных синонимов
   * @throws ApiError если запись не найдена
   */
  async getCustomSynonym(id: string): Promise<CustomSynonymResponse> {
    try {
      const response: AxiosResponse<CustomSynonymResponse> = await this.client.get(
        `/api/custom-synonyms/${id}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Обновление записи кастомных синонимов
   *
   * @param id - ID записи синонимов
   * @param request - Запрос на обновление
   * @returns Обновленная запись синонимов
   * @throws ApiError если обновление не удалось
   */
  async updateCustomSynonym(
    id: string,
    request: CustomSynonymUpdate
  ): Promise<CustomSynonymResponse> {
    try {
      const response: AxiosResponse<CustomSynonymResponse> = await this.client.put(
        `/api/custom-synonyms/${id}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Удаление конкретной записи кастомных синонимов
   *
   * @param id - ID записи синонимов
   * @throws ApiError если удаление не удалось
   */
  async deleteCustomSynonym(id: string): Promise<void> {
    try {
      await this.client.delete(`/api/custom-synonyms/${id}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Удаление всех кастомных синонимов для организации
   *
   * @param organizationId - ID организации
   * @throws ApiError если удаление не удалось
   */
  async deleteCustomSynonymsByOrganization(organizationId: string): Promise<void> {
    try {
      await this.client.delete(`/api/custom-synonyms/organization/${organizationId}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Обратная связь ====================

  /**
   * Создание записей обратной связи
   *
   * @param request - Запрос на создание со списком записей обратной связи
   * @returns Созданные записи обратной связи
   * @throws ApiError если создание не удалось
   *
   * @example
   * ```ts
   * const result = await apiClient.createFeedback({
   *   feedback: [
   *     {
   *       resume_id: 'abc123',
   *       vacancy_id: 'vac456',
   *       skill: 'React',
   *       was_correct: true,
   *       confidence_score: 0.95,
   *       feedback_source: 'frontend',
   *     },
   *   ],
   * });
   * ```
   */
  async createFeedback(request: FeedbackCreate): Promise<FeedbackListResponse> {
    try {
      const response: AxiosResponse<FeedbackListResponse> = await this.client.post(
        '/api/feedback/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение списка записей обратной связи с опциональными фильтрами
   *
   * @param resumeId - Опциональный фильтр по ID резюме
   * @param vacancyId - Опциональный фильтр по ID вакансии
   * @param skill - Опциональный фильтр по навыку
   * @param wasCorrect - Опциональный фильтр по правильности
   * @param processed - Опциональный фильтр по статусу обработки
   * @param feedbackSource - Опциональный фильтр по источнику обратной связи
   * @returns Список записей обратной связи
   * @throws ApiError если получение списка не удалось
   */
  async listFeedback(
    resumeId?: string,
    vacancyId?: string,
    skill?: string,
    wasCorrect?: boolean,
    processed?: boolean,
    feedbackSource?: string
  ): Promise<FeedbackListResponse> {
    try {
      const params: Record<string, string | boolean> = {};
      if (resumeId) params.resume_id = resumeId;
      if (vacancyId) params.vacancy_id = vacancyId;
      if (skill) params.skill = skill;
      if (wasCorrect !== undefined) params.was_correct = wasCorrect;
      if (processed !== undefined) params.processed = processed;
      if (feedbackSource) params.feedback_source = feedbackSource;

      const response: AxiosResponse<FeedbackListResponse> = await this.client.get(
        '/api/feedback/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение конкретной записи обратной связи по ID
   *
   * @param id - ID записи обратной связи
   * @returns Запись обратной связи
   * @throws ApiError если запись не найдена
   */
  async getFeedback(id: string): Promise<FeedbackResponse> {
    try {
      const response: AxiosResponse<FeedbackResponse> = await this.client.get(
        `/api/feedback/${id}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Обновление записи обратной связи
   *
   * @param id - ID записи обратной связи
   * @param request - Запрос на обновление
   * @returns Обновленная запись обратной связи
   * @throws ApiError если обновление не удалось
   */
  async updateFeedback(
    id: string,
    request: FeedbackUpdate
  ): Promise<FeedbackResponse> {
    try {
      const response: AxiosResponse<FeedbackResponse> = await this.client.put(
        `/api/feedback/${id}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Удаление записи обратной связи
   *
   * @param id - ID записи обратной связи
   * @throws ApiError если удаление не удалось
   */
  async deleteFeedback(id: string): Promise<void> {
    try {
      await this.client.delete(`/api/feedback/${id}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Версии моделей ====================

  /**
   * Создание записей версий моделей
   *
   * @param request - Запрос на создание со списком версий моделей
   * @returns Созданные записи версий моделей
   * @throws ApiError если создание не удалось
   *
   * @example
   * ```ts
   * const result = await apiClient.createModelVersions({
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
   * @param isActive - Опциональный фильтр по статусу активности
   * @param isExperiment - Опциональный фильтр по статусу эксперимента
   * @returns Список записей версий моделей
   * @throws ApiError если получение списка не удалось
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
   * Получение активной модели по имени
   *
   * @param modelName - Имя модели
   * @returns Активная версия модели
   * @throws ApiError если модель не найдена
   */
  async getActiveModel(modelName: string): Promise<ModelVersionResponse> {
    try {
      const response: AxiosResponse<ModelVersionResponse> = await this.client.get(
        `/api/model-versions/active`,
        { params: { model_name: modelName } }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение конкретной версии модели по ID
   *
   * @param id - ID версии модели
   * @returns Запись версии модели
   * @throws ApiError если запись не найдена
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
   * Удаление конкретной версии модели
   *
   * @param id - ID версии модели
   * @throws ApiError если удаление не удалось
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
   * @param id - ID версии модели
   * @returns Обновленная версия модели
   * @throws ApiError если активация не удалась
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

  // ==================== Обратная связь по мэтчингу ====================

  /**
   * Отправка обратной связи на результат мэтчинга навыка
   *
   * @param request - Запрос обратной связи с match_id, skill и правильностью
   * @returns Созданная запись обратной связи
   * @throws ApiError если отправка не удалась
   *
   * @example
   * ```ts
   * const result = await apiClient.submitMatchFeedback({
   *   match_id: 'match123',
   *   skill: 'React',
   *   was_correct: true,
   *   confidence_score: 0.95,
   * });
   * ```
   */
  async submitMatchFeedback(request: MatchFeedbackRequest): Promise<MatchFeedbackResponse> {
    try {
      const response: AxiosResponse<MatchFeedbackResponse> = await this.client.post(
        '/api/matching/feedback',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Сравнения ====================

  /**
   * Создание нового представления сравнения резюме
   *
   * @param request - Запрос на создание с vacancy_id, resume_ids и опциональными настройками
   * @returns Созданное сравнение с результатами
   * @throws ApiError если создание не удалось
   *
   * @example
   * ```ts
   * const result = await apiClient.createComparison({
   *   vacancy_id: 'vacancy-123',
   *   resume_ids: ['resume1', 'resume2', 'resume3'],
   *   name: 'Senior Developer Candidates',
   *   filters: { min_match_percentage: 50 },
   * });
   * ```
   */
  async createComparison(request: ComparisonCreate): Promise<ComparisonResponse> {
    try {
      const response: AxiosResponse<ComparisonResponse> = await this.client.post(
        '/api/comparisons/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение списка представлений сравнений с фильтрами и сортировкой
   *
   * @param vacancyId - Опциональный фильтр по ID вакансии
   * @param createdBy - Опциональный фильтр по ID создателя
   * @param minMatchPercentage - Опциональный фильтр минимального процента мэтча
   * @param maxMatchPercentage - Опциональный фильтр максимального процента мэтча
   * @param sortBy - Поле сортировки - created_at, match_percentage, name или updated_at
   * @param order - Порядок сортировки - asc или desc
   * @param limit - Максимум результатов для возврата (default: 50, max: 100)
   * @param offset - Количество результатов для пропуска (default: 0)
   * @returns Список представлений сравнений
   * @throws ApiError если получение списка не удалось
   *
   * @example
   * ```ts
   * const result = await apiClient.listComparisons(
   *   'vacancy-123',
   *   undefined,
   *   50,
   *   90,
   *   'match_percentage',
   *   'desc',
   *   10,
   *   0
   * );
   * ```
   */
  async listComparisons(
    vacancyId?: string,
    createdBy?: string,
    minMatchPercentage?: number,
    maxMatchPercentage?: number,
    sortBy?: string,
    order?: string,
    limit?: number,
    offset?: number
  ): Promise<ComparisonListResponse> {
    try {
      const params: Record<string, string | number> = {};
      if (vacancyId) params.vacancy_id = vacancyId;
      if (createdBy) params.created_by = createdBy;
      if (minMatchPercentage !== undefined) params.min_match_percentage = minMatchPercentage;
      if (maxMatchPercentage !== undefined) params.max_match_percentage = maxMatchPercentage;
      if (sortBy) params.sort_by = sortBy;
      if (order) params.order = order;
      if (limit !== undefined) params.limit = limit;
      if (offset !== undefined) params.offset = offset;

      const response: AxiosResponse<ComparisonListResponse> = await this.client.get(
        '/api/comparisons/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение сравнения по ID
   *
   * @param id - ID сравнения
   * @returns Детали сравнения с результатами
   * @throws ApiError если сравнение не найдено
   *
   * @example
   * ```ts
   * const comparison = await apiClient.getComparison('comp-123');
   * ```
   */
  async getComparison(id: string): Promise<ComparisonResponse> {
    try {
      const response: AxiosResponse<ComparisonResponse> = await this.client.get(
        `/api/comparisons/${id}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Обновление сравнения
   *
   * @param id - ID сравнения
   * @param request - Запрос на обновление с полями для изменения
   * @returns Обновленное сравнение
   * @throws ApiError если обновление не удалось
   *
   * @example
   * ```ts
   * const updated = await apiClient.updateComparison('comp-123', {
   *   name: 'Updated Comparison Name',
   * });
   * ```
   */
  async updateComparison(
    id: string,
    request: ComparisonUpdate
  ): Promise<ComparisonResponse> {
    try {
      const response: AxiosResponse<ComparisonResponse> = await this.client.put(
        `/api/comparisons/${id}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Удаление сравнения
   *
   * @param id - ID сравнения
   * @throws ApiError если удаление не удалось
   *
   * @example
   * ```ts
   * await apiClient.deleteComparison('comp-123');
   * ```
   */
  async deleteComparison(id: string): Promise<void> {
    try {
      await this.client.delete(`/api/comparisons/${id}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Сравнение нескольких резюме с вакансией
   *
   * Выполняет интеллектуальное сопоставление навыков каждого резюме
   * с требованиями вакансии, обрабатывая синонимы и релевантность опыта.
   *
   * @param request - Запрос на сравнение с vacancy_id и resume_ids
   * @returns Матрица сравнения с ранжированными результатами
   * @throws ApiError если сравнение не удалось
   *
   * @example
   * ```ts
   * const result = await apiClient.compareMultipleResumes({
   *   vacancy_id: 'vacancy-123',
   *   resume_ids: ['resume1', 'resume2', 'resume3'],
   * });
   * ```
   */
  async compareMultipleResumes(request: CompareMultipleRequest): Promise<ComparisonMatrixData> {
    try {
      const response: AxiosResponse<ComparisonMatrixData> = await this.client.post(
        '/api/comparisons/compare-multiple',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Аналитика ====================

  /**
   * Получение ключевых метрик найма
   *
   * @param startDate - Опциональная начальная дата для фильтрации (ISO 8601 формат)
   * @param endDate - Опциональная конечная дата для фильтрации (ISO 8601 формат)
   * @returns Ключевые метрики включая time-to-hire, обработку резюме и rates мэтчинга
   * @throws ApiError если запрос не удался
   *
   * @example
   * ```ts
   * const metrics = await apiClient.getKeyMetrics();
   * ```
   */
  async getKeyMetrics(
    startDate?: string,
    endDate?: string
  ): Promise<KeyMetricsResponse> {
    try {
      const params: Record<string, string> = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const response: AxiosResponse<KeyMetricsResponse> = await this.client.get(
        '/api/analytics/key-metrics',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение метрик воронки визуализации
   *
   * @param startDate - Опциональная начальная дата для фильтрации (ISO 8601 формат)
   * @param endDate - Опциональная конечная дата для фильтрации (ISO 8601 формат)
   * @returns Метрики воронки показывающие прогресс кандидатов через pipeline
   * @throws ApiError если запрос не удался
   */
  async getFunnelMetrics(
    startDate?: string,
    endDate?: string
  ): Promise<FunnelMetricsResponse> {
    try {
      const params: Record<string, string> = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const response: AxiosResponse<FunnelMetricsResponse> = await this.client.get(
        '/api/analytics/funnel',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение аналитики спроса на навыки
   *
   * @param startDate - Опциональная начальная дата для фильтрации (ISO 8601 формат)
   * @param endDate - Опциональная конечная дата для фильтрации (ISO 8601 формат)
   * @param limit - Опциональное максимальное количество навыков для возврата (1-100, default 20)
   * @returns Данные спроса на навыки с трендовыми навыками
   * @throws ApiError если запрос не удался
   */
  async getSkillDemand(
    startDate?: string,
    endDate?: string,
    limit?: number
  ): Promise<SkillDemandResponse> {
    try {
      const params: Record<string, string | number> = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      if (limit !== undefined) params.limit = limit;

      const response: AxiosResponse<SkillDemandResponse> = await this.client.get(
        '/api/analytics/skill-demand',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение аналитики отслеживания источников
   *
   * @param startDate - Опциональная начальная дата для фильтрации (ISO 8601 формат)
   * @param endDate - Опциональная конечная дата для фильтрации (ISO 8601 формат)
   * @returns Данные отслеживания источников с распределением вакансий по источникам
   * @throws ApiError если запрос не удался
   */
  async getSourceTracking(
    startDate?: string,
    endDate?: string
  ): Promise<SourceTrackingResponse> {
    try {
      const params: Record<string, string> = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const response: AxiosResponse<SourceTrackingResponse> = await this.client.get(
        '/api/analytics/source-tracking',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение метрик производительности рекрутеров
   *
   * @param startDate - Опциональная начальная дата для фильтрации (ISO 8601 формат)
   * @param endDate - Опциональная конечная дата для фильтрации (ISO 8601 формат)
   * @param limit - Опциональное максимальное количество рекрутеров для возврата (1-100, default 20)
   * @returns Данные сравнения производительности рекрутеров
   * @throws ApiError если запрос не удался
   */
  async getRecruiterPerformance(
    startDate?: string,
    endDate?: string,
    limit?: number
  ): Promise<RecruiterPerformanceResponse> {
    try {
      const params: Record<string, string | number> = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      if (limit !== undefined) params.limit = limit;

      const response: AxiosResponse<RecruiterPerformanceResponse> = await this.client.get(
        '/api/analytics/recruiter-performance',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Обновление языковых предпочтений
   *
   * @param language - Код языка для установки как предпочтения
   * @returns Ответ языковых предпочтений
   */
  async updateLanguagePreference(language: string): Promise<LanguagePreferenceResponse> {
    try {
      const response: AxiosResponse<LanguagePreferenceResponse> = await this.client.post(
        '/api/preferences/language',
        { language }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Веса мэтчинга ====================

  /**
   * Получение всех профилей весов мэтчинга
   *
   * @param organizationId - Опциональный фильтр по ID организации
   * @param vacancyId - Опциональный фильтр по ID вакансии
   * @param isPreset - Опциональный фильтр по статусу пресета
   * @param isActive - Опциональный фильтр по статусу активности (default: true)
   * @returns Список профилей весов
   * @throws ApiError если получение списка не удалось
   */
  async listWeightProfiles(
    organizationId?: string,
    vacancyId?: string,
    isPreset?: boolean,
    isActive: boolean = true,
  ): Promise<MatchingWeightsListResponse> {
    try {
      const params: Record<string, string | boolean> = {};
      if (organizationId) params.organization_id = organizationId;
      if (vacancyId) params.vacancy_id = vacancyId;
      if (isPreset !== undefined) params.is_preset = isPreset;
      params.is_active = isActive;

      const response: AxiosResponse<MatchingWeightsListResponse> = await this.client.get(
        '/api/matching-weights/profiles',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение пресетных профилей весов
   *
   * Возвращает системные пресетные профили (Technical, Creative, Executive, Balanced).
   *
   * @returns Пресетные профили
   * @throws ApiError если запрос не удался
   */
  async getPresetProfiles(): Promise<PresetsResponse> {
    try {
      const response: AxiosResponse<PresetsResponse> = await this.client.get(
        '/api/matching-weights/profiles/presets'
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение конкретного профиля весов по ID
   *
   * @param id - ID профиля
   * @returns Детали профиля весов
   * @throws ApiError если профиль не найден
   */
  async getWeightProfile(id: string): Promise<MatchingWeightsProfile> {
    try {
      const response: AxiosResponse<MatchingWeightsProfile> = await this.client.get(
        `/api/matching-weights/profiles/${id}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Создание кастомного профиля весов
   *
   * @param request - Запрос на создание с весами и метаданными
   * @returns Созданный профиль весов
   * @throws ApiError если создание не удалось
   */
  async createWeightProfile(request: MatchingWeightsCreate): Promise<MatchingWeightsProfile> {
    try {
      const response: AxiosResponse<MatchingWeightsProfile> = await this.client.post(
        '/api/matching-weights/profiles',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Обновление профиля весов
   *
   * @param id - ID профиля
   * @param request - Запрос на обновление с полями для изменения
   * @returns Обновленный профиль весов
   * @throws ApiError если обновление не удалось
   */
  async updateWeightProfile(
    id: string,
    request: MatchingWeightsUpdate,
  ): Promise<MatchingWeightsProfile> {
    try {
      const response: AxiosResponse<MatchingWeightsProfile> = await this.client.put(
        `/api/matching-weights/profiles/${id}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Удаление кастомного профиля весов
   *
   * @param id - ID профиля
   * @throws ApiError если удаление не удалось
   */
  async deleteWeightProfile(id: string): Promise<void> {
    try {
      await this.client.delete(`/api/matching-weights/profiles/${id}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение истории версий для профиля весов
   *
   * @param id - ID профиля
   * @returns Записи истории версий
   * @throws ApiError если запрос не удался
   */
  async getWeightProfileHistory(id: string): Promise<VersionHistoryResponse> {
    try {
      const response: AxiosResponse<VersionHistoryResponse> = await this.client.get(
        `/api/matching-weights/profiles/${id}/history`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Нормализация весов так, чтобы они суммировались до 1.0
   *
   * @param request - Веса для нормализации
   * @returns Нормализованные веса
   * @throws ApiError если запрос не удался
   */
  async normalizeWeights(request: NormalizeWeightsRequest): Promise<NormalizedWeightsResponse> {
    try {
      const response: AxiosResponse<NormalizedWeightsResponse> = await this.client.post(
        '/api/matching-weights/normalize',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Применение кастомных весов к вакансии
   *
   * @param request - Запрос на применение с ID вакансии и весами
   * @returns Результат применения
   * @throws ApiError если применение не удалось
   */
  async applyWeights(request: ApplyWeightsRequest): Promise<ApplyWeightsResponse> {
    try {
      const response: AxiosResponse<ApplyWeightsResponse> = await this.client.post(
        '/api/matching-weights/apply',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== ATS симуляция ====================

  /**
   * Оценка резюме против вакансии с использованием ATS симуляции
   *
   * @param request - Запрос ATS оценки с resume_id, vacancy_id и опциональным флагом use_llm
   * @returns Комплексные результаты ATS оценки
   * @throws ApiError если оценка не удалась
   */
  async evaluateATS(request: ATSEvaluationRequest): Promise<ATSEvaluationResponse> {
    try {
      const response: AxiosResponse<ATSEvaluationResponse> = await this.client.post(
        '/api/ats/evaluate',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение кэшированного результата ATS оценки для пары резюме-вакансия
   *
   * @param resumeId - ID резюме
   * @param vacancyId - ID вакансии
   * @returns Кэшированный результат ATS оценки
   * @throws ApiError если результат не найден
   */
  async getATSResult(resumeId: string, vacancyId: string): Promise<ATSEvaluationResponse> {
    try {
      const response: AxiosResponse<ATSEvaluationResponse> = await this.client.get(
        `/api/ats/results/${resumeId}/${vacancyId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Оценка нескольких резюме против одной вакансии
   *
   * @param request - Batch запрос оценки с vacancy_id и списком resume_ids
   * @returns Batch результаты оценки с сводной статистикой
   * @throws ApiError если оценка не удалась
   */
  async batchEvaluateATS(request: BatchATSEvaluationRequest): Promise<BatchATSEvaluationResponse> {
    try {
      const response: AxiosResponse<BatchATSEvaluationResponse> = await this.client.post(
        '/api/ats/batch-evaluate',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение текущей конфигурации ATS симуляции
   *
   * @returns Конфигурация ATS включая провайдер, модель, threshold и веса
   * @throws ApiError если запрос не удался
   */
  async getATSConfig(): Promise<ATSConfigResponse> {
    try {
      const response: AxiosResponse<ATSConfigResponse> = await this.client.get(
        '/api/ats/config'
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение списка результатов ATS с опциональными фильтрами
   *
   * @param resumeId - Опциональный фильтр по ID резюме
   * @param vacancyId - Опциональный фильтр по ID вакансии
   * @param passed - Опциональный фильтр по статусу passed
   * @param minScore - Опциональный фильтр минимального общего балла
   * @param limit - Максимум результатов для возврата
   * @param offset - Количество результатов для пропуска
   * @returns Список результатов ATS с общим количеством
   * @throws ApiError если получение списка не удалось
   */
  async listATSResults(
    resumeId?: string,
    vacancyId?: string,
    passed?: boolean,
    minScore?: number,
    limit: number = 50,
    offset: number = 0
  ): Promise<ATSResultListResponse> {
    try {
      const params: Record<string, string | number | boolean> = {};
      if (resumeId) params.resume_id = resumeId;
      if (vacancyId) params.vacancy_id = vacancyId;
      if (passed !== undefined) params.passed = passed;
      if (minScore !== undefined) params.min_score = minScore;
      params.limit = limit;
      params.offset = offset;

      const response: AxiosResponse<ATSResultListResponse> = await this.client.get(
        '/api/ats/results',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Кандидаты ====================

  /**
   * Получение списка всех кандидатов (резюме) с их текущими этапами workflow
   *
   * @param stageId - Опциональный фильтр по ID или имени этапа workflow
   * @param vacancyId - Опциональный фильтр по ID вакансии
   * @param skip - Количество записей для пропуска (пагинация)
   * @param limit - Максимум количества записей для возврата
   * @returns Список кандидатов с их текущими этапами
   * @throws ApiError если получение списка не удалось
   */
  async listCandidates(
    stageId?: string,
    vacancyId?: string,
    skip: number = 0,
    limit: number = 100
  ): Promise<CandidateListItem[]> {
    try {
      const params: Record<string, string | number> = { skip, limit };
      if (stageId) params.stage_id = stageId;
      if (vacancyId) params.vacancy_id = vacancyId;

      const response: AxiosResponse<CandidateListItem[]> = await this.client.get(
        '/api/candidates/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение конкретной информации об этапе кандидата
   *
   * @param candidateId - UUID резюме
   * @returns Детали кандидата с текущим этапом
   * @throws ApiError если кандидат не найден
   */
  async getCandidate(candidateId: string): Promise<CandidateListItem> {
    try {
      const response: AxiosResponse<CandidateListItem> = await this.client.get(
        `/api/candidates/${candidateId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Перемещение кандидата на другой этап workflow
   *
   * Создает новую запись этапа найма для отслеживания переходов этапов.
   * Это позволяет поддерживать полную историю прогресса кандидата.
   *
   * @param candidateId - UUID резюме
   * @param request - Детали перемещения этапа (stage_id, опциональный vacancy_id, опциональные notes)
   * @returns Новая информация об этапе
   * @throws ApiError если перемещение не удалось
   */
  async moveCandidate(
    candidateId: string,
    request: MoveCandidateRequest
  ): Promise<MoveCandidateResponse> {
    try {
      const response: AxiosResponse<MoveCandidateResponse> = await this.client.put(
        `/api/candidates/${candidateId}/stage`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Этапы workflow ====================

  /**
   * Создание этапа workflow для организации
   *
   * @param request - Запрос на создание с деталями этапа workflow
   * @returns Созданный этап workflow
   * @throws ApiError если создание не удалось
   */
  async createWorkflowStage(request: WorkflowStageCreate): Promise<WorkflowStageResponse> {
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
   * @param isActive - Опциональный фильтр по статусу активности
   * @param isDefault - Опциональный фильтр по статусу default
   * @returns Список этапов workflow
   * @throws ApiError если получение списка не удалось
   */
  async listWorkflowStages(
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
   */
  async getWorkflowStage(stageId: string): Promise<WorkflowStageResponse> {
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
   */
  async updateWorkflowStage(
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
   */
  async deleteWorkflowStage(stageId: string): Promise<void> {
    try {
      await this.client.delete(`/api/workflow-stages/${stageId}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }
}

// Расширение AxiosRequestConfig для включения metadata
declare module 'axios' {
  interface AxiosRequestConfig {
    metadata?: {
      startTime?: number;
      duration?: number;
    };
  }
}

/**
 * Экземпляр API клиента по умолчанию
 *
 * Используйте этот singleton экземпляр для всех API вызовов.
 */
export const apiClient = new ApiClient();

/**
 * Экспорт класса API клиента для кастомных экземпляров
 */
export default ApiClient;
