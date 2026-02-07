/**
 * Tests for Preferences API Client
 *
 * Tests the Axios-based preferences client for language preference management.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { PreferencesClient } from './preferences';
import axios from 'axios';
import type {
  LanguagePreferenceResponse,
  LanguagePreferenceUpdate,
} from '@/types/api';

// Mock Axios
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      interceptors: {
        response: {
          use: vi.fn(),
        },
      },
      get: vi.fn(),
      put: vi.fn(),
    })),
  },
}));

describe('PreferencesClient', () => {
  let preferencesClient: PreferencesClient;
  let mockAxiosInstance: any;

  beforeEach(() => {
    // Create mock axios instance
    mockAxiosInstance = {
      interceptors: {
        response: { use: vi.fn() },
      },
      get: vi.fn(),
      put: vi.fn(),
    };

    // Mock axios.create to return our mock instance
    vi.mocked(axios.create).mockReturnValue(mockAxiosInstance as any);

    // Create preferences client with mock
    preferencesClient = new PreferencesClient({ baseURL: 'http://test.com' });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Constructor', () => {
    it('should create client with default config', () => {
      const client = new PreferencesClient();
      expect(axios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          baseURL: expect.any(String),
          timeout: 10000,
          headers: {
            'Content-Type': 'application/json',
          },
        })
      );
    });

    it('should create client with custom config', () => {
      const client = new PreferencesClient({
        baseURL: 'http://custom.com',
        timeout: 30000,
      });

      expect(axios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          baseURL: 'http://custom.com',
          timeout: 30000,
        })
      );
    });

    it('should set up response interceptor', () => {
      expect(mockAxiosInstance.interceptors.response.use).toHaveBeenCalled();
    });
  });

  describe('getLanguagePreference', () => {
    it('should get language preference successfully', async () => {
      const mockResponse: LanguagePreferenceResponse = {
        language: 'en',
        updated_at: '2024-01-25T10:00:00Z',
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await preferencesClient.getLanguagePreference();

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/preferences/language'
      );
    });

    it('should get Russian language preference', async () => {
      const mockResponse: LanguagePreferenceResponse = {
        language: 'ru',
        updated_at: '2024-01-25T10:00:00Z',
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await preferencesClient.getLanguagePreference();

      expect(result).toEqual(mockResponse);
      expect(result.language).toBe('ru');
    });

    it('should handle not found error', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Preference not found' },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(preferencesClient.getLanguagePreference()).rejects.toEqual({
        detail: 'Preference not found',
        status: 404,
      });
    });

    it('should handle network timeout error', async () => {
      const error = {
        code: 'ECONNABORTED',
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(preferencesClient.getLanguagePreference()).rejects.toEqual({
        detail: 'Таймаут запроса. Проверьте соединение и попробуйте снова.',
        status: 408,
      });
    });

    it('should handle generic network error', async () => {
      const error = {};

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(preferencesClient.getLanguagePreference()).rejects.toEqual({
        detail: 'Ошибка сети. Проверьте соединение и попробуйте снова.',
        status: 0,
      });
    });

    it('should handle unauthorized error', async () => {
      const error = {
        response: {
          status: 401,
          data: {},
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(preferencesClient.getLanguagePreference()).rejects.toEqual({
        detail: 'Не авторизован. Войдите в систему.',
        status: 401,
      });
    });
  });

  describe('updateLanguagePreference', () => {
    it('should update language preference to English successfully', async () => {
      const mockResponse: LanguagePreferenceResponse = {
        language: 'en',
        updated_at: '2024-01-25T11:00:00Z',
      };

      mockAxiosInstance.put.mockResolvedValue({ data: mockResponse });

      const result = await preferencesClient.updateLanguagePreference('en');

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.put).toHaveBeenCalledWith(
        '/api/preferences/language',
        { language: 'en' }
      );
    });

    it('should update language preference to Russian successfully', async () => {
      const mockResponse: LanguagePreferenceResponse = {
        language: 'ru',
        updated_at: '2024-01-25T11:00:00Z',
      };

      mockAxiosInstance.put.mockResolvedValue({ data: mockResponse });

      const result = await preferencesClient.updateLanguagePreference('ru');

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.put).toHaveBeenCalledWith(
        '/api/preferences/language',
        { language: 'ru' }
      );
    });

    it('should handle validation error with invalid language', async () => {
      const error = {
        response: {
          status: 422,
          data: { detail: 'Unsupported language code' },
        },
      };

      mockAxiosInstance.put.mockRejectedValue(error);

      await expect(
        preferencesClient.updateLanguagePreference('invalid')
      ).rejects.toEqual({
        detail: 'Unsupported language code',
        status: 422,
      });
    });

    it('should handle bad request error', async () => {
      const error = {
        response: {
          status: 400,
          data: {},
        },
      };

      mockAxiosInstance.put.mockRejectedValue(error);

      await expect(
        preferencesClient.updateLanguagePreference('en')
      ).rejects.toEqual({
        detail: 'Неверный запрос. Проверьте введенные данные.',
        status: 400,
      });
    });

    it('should handle forbidden error', async () => {
      const error = {
        response: {
          status: 403,
          data: {},
        },
      };

      mockAxiosInstance.put.mockRejectedValue(error);

      await expect(
        preferencesClient.updateLanguagePreference('ru')
      ).rejects.toEqual({
        detail: 'Доступ запрещен. У вас нет прав для выполнения этого действия.',
        status: 403,
      });
    });

    it('should handle too many requests error', async () => {
      const error = {
        response: {
          status: 429,
          data: {},
        },
      };

      mockAxiosInstance.put.mockRejectedValue(error);

      await expect(
        preferencesClient.updateLanguagePreference('en')
      ).rejects.toEqual({
        detail: 'Слишком много запросов. Попробуйте позже.',
        status: 429,
      });
    });

    it('should handle server error', async () => {
      const error = {
        response: {
          status: 500,
          data: {},
        },
      };

      mockAxiosInstance.put.mockRejectedValue(error);

      await expect(
        preferencesClient.updateLanguagePreference('en')
      ).rejects.toEqual({
        detail: 'Ошибка сервера. Попробуйте позже.',
        status: 500,
      });
    });

    it('should handle bad gateway error', async () => {
      const error = {
        response: {
          status: 502,
          data: {},
        },
      };

      mockAxiosInstance.put.mockRejectedValue(error);

      await expect(
        preferencesClient.updateLanguagePreference('en')
      ).rejects.toEqual({
        detail: 'Ошибка шлюза. Попробуйте позже.',
        status: 502,
      });
    });

    it('should handle service unavailable error', async () => {
      const error = {
        response: {
          status: 503,
          data: {},
        },
      };

      mockAxiosInstance.put.mockRejectedValue(error);

      await expect(
        preferencesClient.updateLanguagePreference('en')
      ).rejects.toEqual({
        detail: 'Сервис недоступен. Попробуйте позже.',
        status: 503,
      });
    });

    it('should use custom server error message when available', async () => {
      const customMessage = 'Custom language update error';
      const error = {
        response: {
          status: 500,
          data: { detail: customMessage },
        },
      };

      mockAxiosInstance.put.mockRejectedValue(error);

      await expect(
        preferencesClient.updateLanguagePreference('en')
      ).rejects.toEqual({
        detail: customMessage,
        status: 500,
      });
    });

    it('should handle network timeout during update', async () => {
      const error = {
        code: 'ECONNABORTED',
      };

      mockAxiosInstance.put.mockRejectedValue(error);

      await expect(
        preferencesClient.updateLanguagePreference('en')
      ).rejects.toEqual({
        detail: 'Таймаут запроса. Проверьте соединение и попробуйте снова.',
        status: 408,
      });
    });

    it('should handle generic network error during update', async () => {
      const error = {};

      mockAxiosInstance.put.mockRejectedValue(error);

      await expect(
        preferencesClient.updateLanguagePreference('en')
      ).rejects.toEqual({
        detail: 'Ошибка сети. Проверьте соединение и попробуйте снова.',
        status: 0,
      });
    });
  });

  describe('Error transformation', () => {
    it('should use server error message when available', async () => {
      const customMessage = 'Custom error from server';
      const error = {
        response: {
          status: 500,
          data: { detail: customMessage },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(preferencesClient.getLanguagePreference()).rejects.toEqual({
        detail: customMessage,
        status: 500,
      });
    });

    it('should use default message for unknown status code', async () => {
      const error = {
        response: {
          status: 418,
          data: {},
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(preferencesClient.getLanguagePreference()).rejects.toEqual({
        detail: 'Произошла непредвиденная ошибка.',
        status: 418,
      });
    });
  });

  describe('getAxiosInstance', () => {
    it('should return the underlying Axios instance', () => {
      const instance = preferencesClient.getAxiosInstance();
      expect(instance).toBe(mockAxiosInstance);
    });
  });

  describe('Response interceptor', () => {
    it('should pass through successful responses', async () => {
      const mockResponse: LanguagePreferenceResponse = {
        language: 'en',
        updated_at: '2024-01-25T10:00:00Z',
      };

      // Get the response interceptor handlers
      const responseInterceptorCall =
        mockAxiosInstance.interceptors.response.use.mock.calls[0];
      const successHandler = responseInterceptorCall[0];
      const errorHandler = responseInterceptorCall[1];

      // Test success handler
      const response = { data: mockResponse };
      const result = successHandler(response);
      expect(result).toEqual(response);

      // Test error handler transforms errors
      const error = {
        response: {
          status: 404,
          data: { detail: 'Test error' },
        },
      };

      const transformedError = errorHandler(error);
      expect(transformedError).toEqual({
        detail: 'Test error',
        status: 404,
      });
    });
  });
});
