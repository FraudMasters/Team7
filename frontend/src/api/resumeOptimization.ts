/**
 * Resume Optimization API Client
 *
 * Этот модуль предоставляет клиент для работы с оптимизацией резюме.
 * Поддерживает генерацию оптимизированных версий резюме на основе
 * требований вакансий и AI-предложений по улучшению.
 *
 * @example
 * ```ts
 * import { resumeOptimizationClient, ResumeOptimizationClient } from '@/api/resumeOptimization';
 *
 * // Генерация оптимизированного резюме
 * const optimization = await resumeOptimizationClient.optimizeResume('resume-123');
 *
 * // Просмотр статуса оптимизации
 * console.log(optimization.status);
 * console.log(optimization.suggestions);
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type { ApiError } from '@/types/api';

/**
 * Запрос на оптимизацию резюме
 */
export interface OptimizationRequest {
  target_job_description?: string;
  check_keywords?: boolean;
  check_formatting?: boolean;
  check_content?: boolean;
  include_ranking_prediction?: boolean;
  vacancy_id?: string;
}

/**
 * Предложение по улучшению резюме
 */
export interface OptimizationSuggestion {
  category: 'keyword' | 'formatting' | 'content' | 'structure';
  severity: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  suggestion: string;
  current_value?: string;
  suggested_value?: string;
}

/**
 * Предсказание изменения рейтинга после оптимизации
 */
export interface RankingPrediction {
  before_score: number | null;
  after_score: number | null;
  improvement_delta: number | null;
  improvement_percentage: number | null;
  before_recommendation: string | null;
  after_recommendation: string | null;
}

/**
 * Результат оптимизации резюме
 */
export interface OptimizationResponse {
  resume_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  optimized_content: string | null;
  suggestions: OptimizationSuggestion[];
  missing_keywords: string[];
  formatting_recommendations: string[];
  overall_score?: number;
  ranking_prediction?: RankingPrediction | null;
  processing_time_seconds?: number;
  error?: string;
}

/**
 * Запрос на сравнение резюме
 */
export interface ComparisonRequest {
  vacancy_id: string;
  limit?: number;
}

/**
 * Оценка кандидата
 */
export interface CandidateScore {
  resume_id: string;
  filename: string;
  overall_score: number;
  keyword_score: number;
  tfidf_score: number;
  vector_score: number;
  rank: number;
}

/**
 * Результат сравнения резюме
 */
export interface ComparisonResult {
  target_resume: CandidateScore;
  top_candidates: CandidateScore[];
  percentile: number;
  better_than_count: number;
  worse_than_count: number;
  recommendation: string;
}

/**
 * Ответ на запрос сравнения
 */
export interface ComparisonResponse {
  resume_id: string;
  vacancy_id: string;
  vacancy_title: string;
  comparison: ComparisonResult;
  processing_time_ms: number;
}

/**
 * Запрос на экспорт оптимизированного резюме
 */
export interface ExportOptimizedRequest {
  format: 'pdf' | 'docx';
  apply_suggestions?: string[];
}

/**
 * Переэкспорт типов для удобства использования
 */
export type {
  OptimizationRequest,
  OptimizationSuggestion,
  OptimizationResponse,
  RankingPrediction,
  ComparisonRequest,
  CandidateScore,
  ComparisonResult,
  ComparisonResponse,
  ExportOptimizedRequest,
};

/**
 * Конфигурация по умолчанию для клиента оптимизации
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_GATEWAY_URL ?? 'http://localhost:8888',
  timeout: 60000, // 60 секунд (оптимизация может занимать больше времени)
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для оптимизации резюме
 *
 * Предоставляет методы для генерации оптимизированных версий резюме
 * с proper обработкой ошибок и типобезопасностью.
 */
export class ResumeOptimizationClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента оптимизации
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
      413: 'Файл слишком большой. Максимальный размер: 10 МБ.',
      422: 'Ошибка валидации. Проверьте формат файла.',
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
   * Генерация оптимизированной версии резюме
   *
   * Создает оптимизированную версию резюме на основе требований вакансии
   * и лучших практик оформления резюме.
   *
   * @param resumeId - ID резюме для оптимизации
   * @param options - Опциональные параметры оптимизации
   * @returns Результат оптимизации с предложениями и улучшенным контентом
   * @throws ApiError если оптимизация не удалась
   *
   * @example
   * ```ts
   * // Базовая оптимизация
   * const optimization = await resumeOptimizationClient.optimizeResume('resume-123');
   *
   * // Оптимизация под конкретную вакансию с предсказанием рейтинга
   * const targeted = await resumeOptimizationClient.optimizeResume('resume-123', {
   *   vacancy_id: 'vacancy-456',
   *   include_ranking_prediction: true,
   *   check_keywords: true,
   *   check_formatting: true,
   *   check_content: true
   * });
   *
   * console.log('Предложения:', optimization.suggestions);
   * console.log('Отсутствующие ключевые слова:', optimization.missing_keywords);
   * console.log('Предсказание рейтинга:', optimization.ranking_prediction);
   * ```
   */
  async optimizeResume(
    resumeId: string,
    options?: OptimizationRequest
  ): Promise<OptimizationResponse> {
    try {
      const request: OptimizationRequest = {
        check_keywords: true,
        check_formatting: true,
        check_content: true,
        include_ranking_prediction: false,
        ...options,
      };

      const response: AxiosResponse<OptimizationResponse> = await this.client.post(
        `/api/resumes/${resumeId}/optimize`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Сравнение резюме с топ кандидатами
   *
   * Сравнивает резюме с лучшими кандидатами для указанной вакансии,
   * показывая относительное положение резюме в рейтинге.
   *
   * @param resumeId - ID резюме для сравнения
   * @param request - Параметры сравнения (vacancy_id и limit)
   * @returns Результаты сравнения с топ кандидатами
   * @throws ApiError если сравнение не удалось
   *
   * @example
   * ```ts
   * // Сравнить с топ-5 кандидатами
   * const comparison = await resumeOptimizationClient.compareWithTopCandidates(
   *   'resume-123',
   *   { vacancy_id: 'vacancy-456', limit: 5 }
   * );
   *
   * console.log('Рейтинг:', comparison.comparison.target_resume.rank);
   * console.log('Процентиль:', comparison.comparison.percentile);
   * console.log('Рекомендация:', comparison.comparison.recommendation);
   * ```
   */
  async compareWithTopCandidates(
    resumeId: string,
    request: ComparisonRequest
  ): Promise<ComparisonResponse> {
    try {
      const requestBody = {
        vacancy_id: request.vacancy_id,
        limit: request.limit ?? 5,
      };

      const response: AxiosResponse<ComparisonResponse> = await this.client.post(
        `/api/resumes/${resumeId}/compare-top`,
        requestBody
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Экспорт оптимизированного резюме в различных форматах
   *
   * Генерирует оптимизированное резюме в выбранном формате (PDF или DOCX)
   * с применением указанных предложений по улучшению.
   *
   * @param resumeId - ID резюме
   * @param exportData - Параметры экспорта (формат и применяемые предложения)
   * @returns Blob с данными файла для скачивания
   * @throws ApiError если экспорт не удался
   *
   * @example
   * ```ts
   * // Экспорт в PDF с применением предложений
   * const blob = await resumeOptimizationClient.exportOptimizedResume(
   *   'resume-123',
   *   { format: 'pdf', apply_suggestions: ['sugg-1', 'sugg-2'] }
   * );
   * // Используйте blob для скачивания файла
   * const url = window.URL.createObjectURL(blob);
   * const link = document.createElement('a');
   * link.href = url;
   * link.download = 'optimized_resume.pdf';
   * link.click();
   * ```
   */
  async exportOptimizedResume(
    resumeId: string,
    exportData: ExportOptimizedRequest
  ): Promise<Blob> {
    try {
      const response: AxiosResponse<Blob> = await this.client.post(
        `/api/resumes/${resumeId}/export-optimized`,
        {
          format: exportData.format,
          apply_suggestions: exportData.apply_suggestions ?? [],
        },
        {
          responseType: 'blob',
        }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * @deprecated Use exportOptimizedResume instead
   * Экспорт отчета оптимизации в различных форматах
   *
   * Генерирует файл экспорта оптимизации в выбранном формате (PDF или DOCX).
   *
   * @param resumeId - ID резюме
   * @param format - Формат экспорта ('pdf' или 'docx')
   * @returns Blob с данными файла для скачивания
   * @throws ApiError если экспорт не удался
   */
  async exportOptimization(
    resumeId: string,
    format: 'pdf' | 'docx'
  ): Promise<Blob> {
    return this.exportOptimizedResume(resumeId, { format });
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
 * Экземпляр клиента оптимизации резюме по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех операций оптимизации.
 */
export const resumeOptimizationClient = new ResumeOptimizationClient();

/**
 * Экспорт класса для создания кастомных экземпляров
 */
export default ResumeOptimizationClient;
