/**
 * Resume API Client
 *
 * Этот модуль предоставляет клиент для работы с резюме через микросервис Resume Processing Service.
 * Поддерживает полный цикл управления резюме: загрузка, просмотр списка, просмотр деталей,
 * анализ и удаление.
 *
 * @example
 * ```ts
 * import { resumesClient, ResumesClient } from '@/api/resume';
 *
 * // Получение списка всех резюме
 * const resumes = await resumesClient.listResumes();
 *
 * // Загрузка нового резюме
 * const uploaded = await resumesClient.uploadResume(fileBlob, 'my-resume.pdf');
 *
 * // Получение резюме по ID
 * const resume = await resumesClient.getResume('resume-123');
 *
 * // Анализ резюме
 * const analyzed = await resumesClient.analyzeResume('resume-123', {
 *   extract_experience: true,
 *   check_grammar: true
 * });
 *
 * // Удаление резюме
 * await resumesClient.deleteResume('resume-123');
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  ResumeUploadResponse,
  AnalysisRequest,
  AnalysisResponse,
  ApiError,
} from '@/types/api';

/**
 * Переэкспорт типов для удобства использования
 */
export type {
  ResumeUploadResponse,
  AnalysisRequest,
  AnalysisResponse,
};

/**
 * Конфигурация по умолчанию для клиента резюме
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_GATEWAY_URL ?? 'http://localhost:8888',
  timeout: 30000, // 30 секунд (анализ может занимать больше времени)
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для работы с резюме
 *
 * Предоставляет методы для загрузки, анализа, просмотра и удаления резюме
 * с proper обработкой ошибок и типобезопасностью.
 */
export class ResumesClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента резюме
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
   * Получение списка всех резюме с пагинацией
   *
   * @param skip - Количество записей для пропуска (пагинация)
   * @param limit - Максимальное количество записей для возврата
   * @returns Список резюме с метаданными
   * @throws ApiError если получение списка не удалось
   *
   * @example
   * ```ts
   * // Получение первых 50 резюме
   * const resumes = await resumesClient.listResumes(0, 50);
   *
   * // Пагинация
   * const page2 = await resumesClient.listResumes(50, 50);
   * ```
   */
  async listResumes(
    skip: number = 0,
    limit: number = 100
  ): Promise<{ resumes: Array<{ id: string; filename: string; status: string; created_at: string }>; total_count: number }> {
    try {
      const params: Record<string, number> = { skip, limit };

      const response: AxiosResponse<{
        resumes: Array<{ id: string; filename: string; status: string; created_at: string }>;
        total_count: number;
      }> = await this.client.get(
        '/api/resumes',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение резюме по ID
   *
   * @param id - ID резюме
   * @returns Данные резюме
   * @throws ApiError если резюме не найдено
   *
   * @example
   * ```ts
   * const resume = await resumesClient.getResume('resume-123');
   * console.log(resume.filename, resume.status);
   * ```
   */
  async getResume(id: string): Promise<{ id: string; filename: string; status: string; created_at: string; updated_at: string }> {
    try {
      const response: AxiosResponse<{
        id: string;
        filename: string;
        status: string;
        created_at: string;
        updated_at: string;
      }> = await this.client.get(
        `/api/resumes/${id}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Загрузка нового резюме
   *
   * Поддерживает загрузку файлов в форматах PDF и DOCX.
   * Файл анализируется асинхронно, результат можно получить через метод analyzeResume.
   *
   * @param file - Blob или File объект для загрузки
   * @param filename - Имя файла
   * @param onUploadProgress - Опциональный колбэк для отслеживания прогресса загрузки
   * @returns Результат загрузки с ID резюме
   * @throws ApiError если загрузка не удалась
   *
   * @example
   * ```ts
   * // Загрузка с отслеживанием прогресса
   * const uploaded = await resumesClient.uploadResume(
   *   fileBlob,
   *   'my-resume.pdf',
   *   (progress) => console.log(`Загружено ${progress}%`)
   * );
   * console.log('ID резюме:', uploaded.id);
   * ```
   */
  async uploadResume(
    file: Blob,
    filename: string,
    onUploadProgress?: (progress: number) => void
  ): Promise<ResumeUploadResponse> {
    try {
      const formData = new FormData();
      formData.append('file', file, filename);

      const response: AxiosResponse<ResumeUploadResponse> = await this.client.post(
        '/api/resumes',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            if (onUploadProgress && progressEvent.total) {
              const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
              onUploadProgress(progress);
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
   * Запускает полный анализ резюме включая извлечение ключевых слов,
   * сущностей, проверку грамматики и извлечение опыта работы.
   *
   * @param id - ID резюме
   * @param options - Опции анализа
   * @returns Результаты анализа с ключевыми словами, сущностями, грамматикой и опытом
   * @throws ApiError если анализ не удался
   *
   * @example
   * ```ts
   * const analysis = await resumesClient.analyzeResume('resume-123', {
   *   extract_experience: true,
   *   check_grammar: true
   * });
   *
   * console.log('Ключевые слова:', analysis.keywords.keywords);
   * console.log('Опыт работы (месяцев):', analysis.experience?.total_experience_months);
   * console.log('Ошибок грамматики:', analysis.grammar?.total_errors);
   * ```
   */
  async analyzeResume(
    id: string,
    options: Partial<AnalysisRequest> = {}
  ): Promise<AnalysisResponse> {
    try {
      const request: AnalysisRequest = {
        resume_id: id,
        extract_experience: options.extract_experience ?? true,
        check_grammar: options.check_grammar ?? true,
      };

      const response: AxiosResponse<AnalysisResponse> = await this.client.post(
        `/api/resumes/${id}/analyze`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Удаление резюме
   *
   * @param id - ID резюме
   * @throws ApiError если удаление не удалось
   *
   * @example
   * ```ts
   * await resumesClient.deleteResume('resume-123');
   * ```
   */
  async deleteResume(id: string): Promise<void> {
    try {
      await this.client.delete(`/api/resumes/${id}`);
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
 * Экземпляр клиента резюме по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех операций с резюме.
 */
export const resumesClient = new ResumesClient();

/**
 * Экспорт класса резюме для создания кастомных экземпляров
 */
export default ResumesClient;
