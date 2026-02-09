/**
 * Job Seeker Profile API Client
 *
 * Этот модуль предоставляет клиент для работы с профилями соискателей.
 * Поддерживает полное управление профилем: базовая информация, история работы,
 * образование, навыки.
 *
 * @example
 * ```ts
 * import { profilesClient, ProfilesClient } from '@/api/profiles';
 *
 * // Получение профиля текущего пользователя
 * const profile = await profilesClient.getMyProfile();
 *
 * // Создание нового профиля
 * const newProfile = await profilesClient.createMyProfile({
 *   location: 'San Francisco, CA',
 *   bio: 'Software engineer...',
 *   years_of_experience: 5
 * });
 *
 * // Обновление профиля
 * const updated = await profilesClient.updateMyProfile({
 *   current_title: 'Senior Software Engineer'
 * });
 *
 * // Получение истории работы
 * const workHistory = await profilesClient.getWorkHistory();
 *
 * // Добавление записи об образовании
 * const education = await profilesClient.createEducation({
 *   institution_name: 'MIT',
 *   degree: 'Bachelor of Science',
 *   field_of_study: 'Computer Science'
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  JobSeekerProfile,
  JobSeekerProfileCreate,
  JobSeekerProfileUpdate,
  WorkHistoryItem,
  WorkHistoryCreate,
  WorkHistoryUpdate,
  WorkHistoryListResponse,
  EducationItem,
  EducationCreate,
  EducationUpdate,
  EducationListResponse,
  SkillItem,
  SkillCreate,
  SkillUpdate,
  SkillListResponse,
  ApiError,
} from '@/types/api';

/**
 * Переэкспорт типов для удобства использования
 */
export type {
  JobSeekerProfile,
  JobSeekerProfileCreate,
  JobSeekerProfileUpdate,
  WorkHistoryItem,
  WorkHistoryCreate,
  WorkHistoryUpdate,
  EducationItem,
  EducationCreate,
  EducationUpdate,
  SkillItem,
  SkillCreate,
  SkillUpdate,
};

/**
 * Конфигурация по умолчанию для клиента профилей
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_GATEWAY_URL ?? 'http://localhost:8888',
  timeout: 10000, // 10 секунд
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для работы с профилями соискателей
 *
 * Предоставляет методы для CRUD-операций с профилями, историей работы,
 * образованием и навыками с proper обработкой ошибок и типобезопасностью.
 */
export class ProfilesClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента профилей
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
      404: 'Профиль не найден.',
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

  // ==================== Profile Methods ====================

  /**
   * Получение профиля текущего пользователя
   *
   * @returns Данные профиля
   * @throws ApiError если профиль не найден
   *
   * @example
   * ```ts
   * const profile = await profilesClient.getMyProfile();
   * console.log(profile.location, profile.current_title);
   * ```
   */
  async getMyProfile(): Promise<JobSeekerProfile> {
    try {
      const response: AxiosResponse<JobSeekerProfile> = await this.client.get(
        '/api/profiles/me'
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Создание нового профиля для текущего пользователя
   *
   * @param data - Данные для создания профиля
   * @returns Созданный профиль
   * @throws ApiError если создание не удалось
   *
   * @example
   * ```ts
   * const profile = await profilesClient.createMyProfile({
   *   location: 'San Francisco, CA',
   *   bio: 'Software engineer with 5 years experience...',
   *   years_of_experience: 5.0,
   *   current_title: 'Senior Software Engineer'
   * });
   * ```
   */
  async createMyProfile(data: JobSeekerProfileCreate): Promise<JobSeekerProfile> {
    try {
      const response: AxiosResponse<JobSeekerProfile> = await this.client.post(
        '/api/profiles/me',
        data
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Обновление профиля текущего пользователя
   *
   * @param data - Данные для обновления профиля (частичное обновление)
   * @returns Обновленный профиль
   * @throws ApiError если обновление не удалось
   *
   * @example
   * ```ts
   * const profile = await profilesClient.updateMyProfile({
   *   location: 'New York, NY',
   *   years_of_experience: 6.0
   * });
   * ```
   */
  async updateMyProfile(data: JobSeekerProfileUpdate): Promise<JobSeekerProfile> {
    try {
      const response: AxiosResponse<JobSeekerProfile> = await this.client.put(
        '/api/profiles/me',
        data
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Work History Methods ====================

  /**
   * Получение истории работы текущего пользователя
   *
   * @returns Список записей о работе
   * @throws ApiError если получение списка не удалось
   *
   * @example
   * ```ts
   * const { work_history, count } = await profilesClient.getWorkHistory();
   * console.log(`Found ${count} work history entries`);
   * ```
   */
  async getWorkHistory(): Promise<WorkHistoryListResponse> {
    try {
      const response: AxiosResponse<WorkHistoryListResponse> = await this.client.get(
        '/api/profiles/me/work-history'
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Создание новой записи о работе
   *
   * @param data - Данные о работе
   * @returns Созданная запись
   * @throws ApiError если создание не удалось
   *
   * @example
   * ```ts
   * const work = await profilesClient.createWorkHistory({
   *   company_name: 'Tech Corp',
   *   position_title: 'Senior Developer',
   *   start_date: '2020-01-01',
   *   employment_type: 'full_time'
   * });
   * ```
   */
  async createWorkHistory(data: WorkHistoryCreate): Promise<WorkHistoryItem> {
    try {
      const response: AxiosResponse<WorkHistoryItem> = await this.client.post(
        '/api/profiles/me/work-history',
        data
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение записи о работе по ID
   *
   * @param id - ID записи о работе
   * @returns Данные о работе
   * @throws ApiError если запись не найдена
   *
   * @example
   * ```ts
   * const work = await profilesClient.getWorkHistoryItem('work-id-123');
   * ```
   */
  async getWorkHistoryItem(id: string): Promise<WorkHistoryItem> {
    try {
      const response: AxiosResponse<WorkHistoryItem> = await this.client.get(
        `/api/profiles/me/work-history/${id}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Обновление записи о работе
   *
   * @param id - ID записи о работе
   * @param data - Данные для обновления
   * @returns Обновленная запись
   * @throws ApiError если обновление не удалось
   *
   * @example
   * ```ts
   * const work = await profilesClient.updateWorkHistory('work-id-123', {
   *   position_title: 'Lead Developer',
   *   end_date: '2023-12-31'
   * });
   * ```
   */
  async updateWorkHistory(id: string, data: WorkHistoryUpdate): Promise<WorkHistoryItem> {
    try {
      const response: AxiosResponse<WorkHistoryItem> = await this.client.put(
        `/api/profiles/me/work-history/${id}`,
        data
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Удаление записи о работе
   *
   * @param id - ID записи о работе
   * @throws ApiError если удаление не удалось
   *
   * @example
   * ```ts
   * await profilesClient.deleteWorkHistory('work-id-123');
   * ```
   */
  async deleteWorkHistory(id: string): Promise<void> {
    try {
      await this.client.delete(`/api/profiles/me/work-history/${id}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Education Methods ====================

  /**
   * Получение истории образования текущего пользователя
   *
   * @returns Список записей об образовании
   * @throws ApiError если получение списка не удалось
   *
   * @example
   * ```ts
   * const { education, count } = await profilesClient.getEducation();
   * console.log(`Found ${count} education entries`);
   * ```
   */
  async getEducation(): Promise<EducationListResponse> {
    try {
      const response: AxiosResponse<EducationListResponse> = await this.client.get(
        '/api/profiles/me/education'
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Создание новой записи об образовании
   *
   * @param data - Данные об образовании
   * @returns Созданная запись
   * @throws ApiError если создание не удалось
   *
   * @example
   * ```ts
   * const education = await profilesClient.createEducation({
   *   institution_name: 'MIT',
   *   degree: 'Bachelor of Science',
   *   field_of_study: 'Computer Science',
   *   start_date: '2016-09-01',
   *   end_date: '2020-05-31',
   *   degree_type: 'bachelor'
   * });
   * ```
   */
  async createEducation(data: EducationCreate): Promise<EducationItem> {
    try {
      const response: AxiosResponse<EducationItem> = await this.client.post(
        '/api/profiles/me/education',
        data
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение записи об образовании по ID
   *
   * @param id - ID записи об образовании
   * @returns Данные об образовании
   * @throws ApiError если запись не найдена
   *
   * @example
   * ```ts
   * const education = await profilesClient.getEducationItem('edu-id-123');
   * ```
   */
  async getEducationItem(id: string): Promise<EducationItem> {
    try {
      const response: AxiosResponse<EducationItem> = await this.client.get(
        `/api/profiles/me/education/${id}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Обновление записи об образовании
   *
   * @param id - ID записи об образовании
   * @param data - Данные для обновления
   * @returns Обновленная запись
   * @throws ApiError если обновление не удалось
   *
   * @example
   * ```ts
   * const education = await profilesClient.updateEducation('edu-id-123', {
   *   field_of_study: 'Computer Science and Mathematics'
   * });
   * ```
   */
  async updateEducation(id: string, data: EducationUpdate): Promise<EducationItem> {
    try {
      const response: AxiosResponse<EducationItem> = await this.client.put(
        `/api/profiles/me/education/${id}`,
        data
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Удаление записи об образовании
   *
   * @param id - ID записи об образовании
   * @throws ApiError если удаление не удалось
   *
   * @example
   * ```ts
   * await profilesClient.deleteEducation('edu-id-123');
   * ```
   */
  async deleteEducation(id: string): Promise<void> {
    try {
      await this.client.delete(`/api/profiles/me/education/${id}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Skills Methods ====================

  /**
   * Получение навыков текущего пользователя
   *
   * @returns Список навыков
   * @throws ApiError если получение списка не удалось
   *
   * @example
   * ```ts
   * const { skills, count } = await profilesClient.getSkills();
   * console.log(`Found ${count} skills`);
   * ```
   */
  async getSkills(): Promise<SkillListResponse> {
    try {
      const response: AxiosResponse<SkillListResponse> = await this.client.get(
        '/api/profiles/me/skills'
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Создание новой записи о навыке
   *
   * @param data - Данные о навыке
   * @returns Созданная запись
   * @throws ApiError если создание не удалось
   *
   * @example
   * ```ts
   * const skill = await profilesClient.createSkill({
   *   name: 'TypeScript',
   *   category: 'Programming Languages',
   *   proficiency_level: 'advanced',
   *   years_of_experience: 3
   * });
   * ```
   */
  async createSkill(data: SkillCreate): Promise<SkillItem> {
    try {
      const response: AxiosResponse<SkillItem> = await this.client.post(
        '/api/profiles/me/skills',
        data
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение записи о навыке по ID
   *
   * @param id - ID записи о навыке
   * @returns Данные о навыке
   * @throws ApiError если запись не найдена
   *
   * @example
   * ```ts
   * const skill = await profilesClient.getSkillItem('skill-id-123');
   * ```
   */
  async getSkillItem(id: string): Promise<SkillItem> {
    try {
      const response: AxiosResponse<SkillItem> = await this.client.get(
        `/api/profiles/me/skills/${id}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Обновление записи о навыке
   *
   * @param id - ID записи о навыке
   * @param data - Данные для обновления
   * @returns Обновленная запись
   * @throws ApiError если обновление не удалось
   *
   * @example
   * ```ts
   * const skill = await profilesClient.updateSkill('skill-id-123', {
   *   proficiency_level: 'expert',
   *   years_of_experience: 5
   * });
   * ```
   */
  async updateSkill(id: string, data: SkillUpdate): Promise<SkillItem> {
    try {
      const response: AxiosResponse<SkillItem> = await this.client.put(
        `/api/profiles/me/skills/${id}`,
        data
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Удаление записи о навыке
   *
   * @param id - ID записи о навыке
   * @throws ApiError если удаление не удалось
   *
   * @example
   * ```ts
   * await profilesClient.deleteSkill('skill-id-123');
   * ```
   */
  async deleteSkill(id: string): Promise<void> {
    try {
      await this.client.delete(`/api/profiles/me/skills/${id}`);
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
 * Экземпляр клиента профилей по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех операций с профилями.
 */
export const profilesClient = new ProfilesClient();

/**
 * Экспорт класса профилей для создания кастомных экземпляров
 */
export default ProfilesClient;
