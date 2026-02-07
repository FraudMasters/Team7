/**
 * Tests for Model Versions API Client
 *
 * Tests the Axios-based API client for model version management.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ModelVersionsClient, modelVersionsClient } from './modelVersions';
import axios from 'axios';
import type {
  ModelVersionCreate,
  ModelVersionUpdate,
  ModelVersionResponse,
  ModelVersionListResponse,
} from '@/types/api';

// Mock Axios
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      interceptors: {
        request: {
          use: vi.fn(),
        },
        response: {
          use: vi.fn(),
        },
      },
      post: vi.fn(),
      get: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    })),
  },
}));

describe('ModelVersionsClient', () => {
  let client: ModelVersionsClient;
  let mockAxiosInstance: any;

  beforeEach(() => {
    // Create mock axios instance
    mockAxiosInstance = {
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
      post: vi.fn(),
      get: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    };

    // Mock axios.create to return our mock instance
    vi.mocked(axios.create).mockReturnValue(mockAxiosInstance as any);

    // Create client with mock
    client = new ModelVersionsClient({ baseURL: 'http://test.com' });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Constructor', () => {
    it('should create client with default config', () => {
      const testClient = new ModelVersionsClient();
      expect(axios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          baseURL: expect.any(String),
          timeout: 30000,
          headers: {
            'Content-Type': 'application/json',
          },
        })
      );
    });

    it('should create client with custom config', () => {
      const testClient = new ModelVersionsClient({
        baseURL: 'http://custom.com',
        timeout: 60000,
      });

      expect(axios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          baseURL: 'http://custom.com',
          timeout: 60000,
        })
      );
    });

    it('should set up response interceptor', () => {
      expect(mockAxiosInstance.interceptors.response.use).toHaveBeenCalled();
    });
  });

  describe('createModelVersions', () => {
    it('should create model versions successfully', async () => {
      const mockRequest: ModelVersionCreate = {
        models: [
          {
            model_name: 'skill_matching',
            version: 'v2.0.0',
            is_active: false,
            is_experiment: true,
            experiment_config: { traffic_percentage: 20 },
            performance_score: 92.5,
          },
        ],
      };

      const mockResponse: ModelVersionListResponse = {
        models: [
          {
            id: 'version-123',
            model_name: 'skill_matching',
            version: 'v2.0.0',
            is_active: false,
            is_experiment: true,
            experiment_config: { traffic_percentage: 20 },
            performance_score: 92.5,
            created_at: '2024-01-25T00:00:00Z',
            updated_at: '2024-01-25T00:00:00Z',
          },
        ],
        total_count: 1,
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await client.createModelVersions(mockRequest);

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/model-versions/',
        mockRequest
      );
    });

    it('should handle creation error with validation error', async () => {
      const error = {
        response: {
          status: 422,
          data: { detail: 'Invalid model version format' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        client.createModelVersions({ models: [] })
      ).rejects.toEqual({
        detail: 'Invalid model version format',
        status: 422,
      });
    });

    it('should handle network error during creation', async () => {
      const error = {
        code: 'ECONNABORTED',
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        client.createModelVersions({ models: [] })
      ).rejects.toEqual({
        detail: 'Таймаут запроса. Проверьте соединение и попробуйте снова.',
        status: 408,
      });
    });
  });

  describe('listModelVersions', () => {
    it('should list all model versions', async () => {
      const mockResponse: ModelVersionListResponse = {
        models: [
          {
            id: 'version-1',
            model_name: 'skill_matching',
            version: 'v1.0.0',
            is_active: true,
            is_experiment: false,
            created_at: '2024-01-25T00:00:00Z',
            updated_at: '2024-01-25T00:00:00Z',
          },
          {
            id: 'version-2',
            model_name: 'skill_matching',
            version: 'v2.0.0',
            is_active: false,
            is_experiment: true,
            created_at: '2024-01-25T00:00:00Z',
            updated_at: '2024-01-25T00:00:00Z',
          },
        ],
        total_count: 2,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await client.listModelVersions();

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/model-versions/', {
        params: {},
      });
    });

    it('should list model versions with filters', async () => {
      const mockResponse: ModelVersionListResponse = {
        models: [
          {
            id: 'version-1',
            model_name: 'skill_matching',
            version: 'v1.0.0',
            is_active: true,
            is_experiment: false,
            created_at: '2024-01-25T00:00:00Z',
            updated_at: '2024-01-25T00:00:00Z',
          },
        ],
        total_count: 1,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await client.listModelVersions('skill_matching', true, false);

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/model-versions/', {
        params: {
          model_name: 'skill_matching',
          is_active: true,
          is_experiment: false,
        },
      });
    });

    it('should handle list error', async () => {
      const error = {
        response: {
          status: 500,
          data: { detail: 'Database query failed' },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.listModelVersions()).rejects.toEqual({
        detail: 'Database query failed',
        status: 500,
      });
    });
  });

  describe('getActiveModel', () => {
    it('should get active model successfully', async () => {
      const mockResponse: ModelVersionResponse = {
        id: 'version-123',
        model_name: 'skill_matching',
        version: 'v1.0.0',
        is_active: true,
        is_experiment: false,
        performance_score: 88.5,
        created_at: '2024-01-25T00:00:00Z',
        updated_at: '2024-01-25T00:00:00Z',
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await client.getActiveModel('skill_matching');

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/model-versions/active', {
        params: { model_name: 'skill_matching' },
      });
    });

    it('should handle not found error', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Active model not found' },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.getActiveModel('unknown_model')).rejects.toEqual({
        detail: 'Active model not found',
        status: 404,
      });
    });
  });

  describe('getModelVersion', () => {
    it('should get model version by ID successfully', async () => {
      const mockResponse: ModelVersionResponse = {
        id: 'version-123',
        model_name: 'skill_matching',
        version: 'v2.0.0',
        is_active: false,
        is_experiment: true,
        experiment_config: { traffic_percentage: 20 },
        performance_score: 92.5,
        created_at: '2024-01-25T00:00:00Z',
        updated_at: '2024-01-25T00:00:00Z',
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await client.getModelVersion('version-123');

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/model-versions/version-123'
      );
    });

    it('should handle not found error', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Model version not found' },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.getModelVersion('invalid-id')).rejects.toEqual({
        detail: 'Model version not found',
        status: 404,
      });
    });
  });

  describe('updateModelVersion', () => {
    it('should update model version successfully', async () => {
      const mockRequest: ModelVersionUpdate = {
        performance_score: 95.0,
        is_experiment: false,
      };

      const mockResponse: ModelVersionResponse = {
        id: 'version-123',
        model_name: 'skill_matching',
        version: 'v2.0.0',
        is_active: false,
        is_experiment: false,
        performance_score: 95.0,
        created_at: '2024-01-25T00:00:00Z',
        updated_at: '2024-01-25T01:00:00Z',
      };

      mockAxiosInstance.put.mockResolvedValue({ data: mockResponse });

      const result = await client.updateModelVersion('version-123', mockRequest);

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.put).toHaveBeenCalledWith(
        '/api/model-versions/version-123',
        mockRequest
      );
    });

    it('should handle update error with not found', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Model version not found' },
        },
      };

      mockAxiosInstance.put.mockRejectedValue(error);

      await expect(
        client.updateModelVersion('invalid-id', { performance_score: 90.0 })
      ).rejects.toEqual({
        detail: 'Model version not found',
        status: 404,
      });
    });

    it('should handle validation error during update', async () => {
      const error = {
        response: {
          status: 422,
          data: { detail: 'Invalid performance score value' },
        },
      };

      mockAxiosInstance.put.mockRejectedValue(error);

      await expect(
        client.updateModelVersion('version-123', { performance_score: -10 })
      ).rejects.toEqual({
        detail: 'Invalid performance score value',
        status: 422,
      });
    });
  });

  describe('deleteModelVersion', () => {
    it('should delete model version successfully', async () => {
      mockAxiosInstance.delete.mockResolvedValue({});

      await expect(client.deleteModelVersion('version-123')).resolves.toBeUndefined();
      expect(mockAxiosInstance.delete).toHaveBeenCalledWith(
        '/api/model-versions/version-123'
      );
    });

    it('should handle delete error with not found', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Model version not found' },
        },
      };

      mockAxiosInstance.delete.mockRejectedValue(error);

      await expect(client.deleteModelVersion('invalid-id')).rejects.toEqual({
        detail: 'Model version not found',
        status: 404,
      });
    });

    it('should handle conflict error when deleting active version', async () => {
      const error = {
        response: {
          status: 409,
          data: { detail: 'Cannot delete active model version' },
        },
      };

      mockAxiosInstance.delete.mockRejectedValue(error);

      await expect(client.deleteModelVersion('version-123')).rejects.toEqual({
        detail: 'Cannot delete active model version',
        status: 409,
      });
    });
  });

  describe('activateModelVersion', () => {
    it('should activate model version successfully', async () => {
      const mockResponse: ModelVersionResponse = {
        id: 'version-123',
        model_name: 'skill_matching',
        version: 'v2.0.0',
        is_active: true,
        is_experiment: false,
        created_at: '2024-01-25T00:00:00Z',
        updated_at: '2024-01-25T01:00:00Z',
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await client.activateModelVersion('version-123');

      expect(result).toEqual(mockResponse);
      expect(result.is_active).toBe(true);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/model-versions/version-123/activate',
        {}
      );
    });

    it('should handle activation error with not found', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Model version not found' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(client.activateModelVersion('invalid-id')).rejects.toEqual({
        detail: 'Model version not found',
        status: 404,
      });
    });
  });

  describe('deactivateModelVersion', () => {
    it('should deactivate model version successfully', async () => {
      const mockResponse: ModelVersionResponse = {
        id: 'version-123',
        model_name: 'skill_matching',
        version: 'v2.0.0',
        is_active: false,
        is_experiment: true,
        created_at: '2024-01-25T00:00:00Z',
        updated_at: '2024-01-25T01:00:00Z',
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await client.deactivateModelVersion('version-123');

      expect(result).toEqual(mockResponse);
      expect(result.is_active).toBe(false);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/model-versions/version-123/deactivate',
        {}
      );
    });

    it('should handle deactivation error with not found', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Model version not found' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(client.deactivateModelVersion('invalid-id')).rejects.toEqual({
        detail: 'Model version not found',
        status: 404,
      });
    });
  });

  describe('getAxiosInstance', () => {
    it('should return the underlying Axios instance', () => {
      const instance = client.getAxiosInstance();
      expect(instance).toBe(mockAxiosInstance);
    });
  });

  describe('Error transformation', () => {
    it('should transform 400 error with default message', async () => {
      const error = {
        response: {
          status: 400,
          data: {},
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.getModelVersion('test-id')).rejects.toEqual({
        detail: 'Неверный запрос. Проверьте введенные данные.',
        status: 400,
      });
    });

    it('should transform 401 error', async () => {
      const error = {
        response: {
          status: 401,
          data: {},
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.getModelVersion('test-id')).rejects.toEqual({
        detail: 'Не авторизован. Войдите в систему.',
        status: 401,
      });
    });

    it('should transform 403 error', async () => {
      const error = {
        response: {
          status: 403,
          data: {},
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.getModelVersion('test-id')).rejects.toEqual({
        detail: 'Доступ запрещен. У вас нет прав для выполнения этого действия.',
        status: 403,
      });
    });

    it('should transform 429 error', async () => {
      const error = {
        response: {
          status: 429,
          data: {},
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.getModelVersion('test-id')).rejects.toEqual({
        detail: 'Слишком много запросов. Попробуйте позже.',
        status: 429,
      });
    });

    it('should use server error message when available', async () => {
      const customMessage = 'Custom error from server';
      const error = {
        response: {
          status: 500,
          data: { detail: customMessage },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.getModelVersion('test-id')).rejects.toEqual({
        detail: customMessage,
        status: 500,
      });
    });

    it('should handle unknown status codes', async () => {
      const error = {
        response: {
          status: 418,
          data: {},
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.getModelVersion('test-id')).rejects.toEqual({
        detail: 'Произошла непредвиденная ошибка.',
        status: 418,
      });
    });

    it('should handle network error without response', async () => {
      const error = {};

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.getModelVersion('test-id')).rejects.toEqual({
        detail: 'Ошибка сети. Проверьте соединение и попробуйте снова.',
        status: 0,
      });
    });

    it('should transform 502 error', async () => {
      const error = {
        response: {
          status: 502,
          data: {},
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.getModelVersion('test-id')).rejects.toEqual({
        detail: 'Ошибка шлюза. Попробуйте позже.',
        status: 502,
      });
    });

    it('should transform 503 error', async () => {
      const error = {
        response: {
          status: 503,
          data: {},
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.getModelVersion('test-id')).rejects.toEqual({
        detail: 'Сервис недоступен. Попробуйте позже.',
        status: 503,
      });
    });
  });

  describe('Response interceptor', () => {
    it('should set up response interceptor for error transformation', () => {
      const responseInterceptorCall =
        mockAxiosInstance.interceptors.response.use.mock.calls[0];
      const errorHandler = responseInterceptorCall[1];

      expect(errorHandler).toBeDefined();
    });
  });
});

describe('modelVersionsClient singleton', () => {
  it('should export a default instance', () => {
    expect(modelVersionsClient).toBeInstanceOf(ModelVersionsClient);
  });
});
