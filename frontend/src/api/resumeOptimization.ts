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
  resume_id: string;
  target_vacancy_id?: string;
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
  processing_time_seconds?: number;
  error?: string;
}

/**
 * Переэкспорт типов для удобства использования
 */
export type {
  OptimizationRequest,
  OptimizationSuggestion,
  OptimizationResponse,
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
   * @param targetVacancyId - Опциональный ID целевой вакансии
   * @returns Результат оптимизации с предложениями и улучшенным контентом
   * @throws ApiError если оптимизация не удалась
   *
   * @example
   * ```ts
   * // Базовая оптимизация
   * const optimization = await resumeOptimizationClient.optimizeResume('resume-123');
   *
   * // Оптимизация под конкретную вакансию
   * const targeted = await resumeOptimizationClient.optimizeResume(
   *   'resume-123',
   *   'vacancy-456'
   * );
   *
   * console.log('Предложения:', optimization.suggestions);
   * console.log('Отсутствующие ключевые слова:', optimization.missing_keywords);
   * ```
   */
  async optimizeResume(
    resumeId: string,
    targetVacancyId?: string
  ): Promise<OptimizationResponse> {
    try {
      const request: OptimizationRequest = {
        resume_id: resumeId,
        target_vacancy_id: targetVacancyId,
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
