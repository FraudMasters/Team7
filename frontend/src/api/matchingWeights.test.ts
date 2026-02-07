/**
 * Tests for Matching Weights API Client
 *
 * Tests the Axios-based API client for managing matching weight profiles.
 * Covers profile listing, creation, updating, deletion, presets, history,
 * normalization, and weight application to vacancies.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { MatchingWeightsClient } from './matchingWeights';
import axios from 'axios';
import type {
  MatchingWeightsProfile,
  MatchingWeightsCreate,
  MatchingWeightsUpdate,
  MatchingWeightsListResponse,
  PresetsResponse,
  VersionHistoryResponse,
  NormalizeWeightsRequest,
  NormalizedWeightsResponse,
  ApplyWeightsRequest,
  ApplyWeightsResponse,
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

describe('MatchingWeightsClient', () => {
  let client: MatchingWeightsClient;
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
    client = new MatchingWeightsClient({ baseURL: 'http://test.com' });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Constructor', () => {
    it('should create client with default config', () => {
      const testClient = new MatchingWeightsClient();
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
      const testClient = new MatchingWeightsClient({
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

    it('should set up response interceptor for error handling', () => {
      expect(mockAxiosInstance.interceptors.response.use).toHaveBeenCalled();
    });
  });

  describe('listWeightProfiles', () => {
    it('should list all active weight profiles by default', async () => {
      const mockResponse: MatchingWeightsListResponse = {
        profiles: [
          {
            id: 'profile-1',
            name: 'Technical Profile',
            description: 'High keyword weight for technical roles',
            keyword_weight: 0.6,
            tfidf_weight: 0.25,
            vector_weight: 0.15,
            weights_percentage: {
              keyword_weight: 60,
              tfidf_weight: 25,
              vector_weight: 15,
            },
            is_preset: false,
            is_active: true,
            organization_id: 'org-123',
            vacancy_id: 'vacancy-456',
            created_at: '2024-01-25T00:00:00Z',
            updated_at: '2024-01-25T00:00:00Z',
          },
        ],
        total_count: 1,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await client.listWeightProfiles();

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/matching-weights/profiles',
        {
          params: { is_active: true },
        }
      );
    });

    it('should filter profiles by organization', async () => {
      const mockResponse: MatchingWeightsListResponse = {
        profiles: [],
        total_count: 0,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      await client.listWeightProfiles('org-123');

      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/matching-weights/profiles',
        {
          params: { organization_id: 'org-123', is_active: true },
        }
      );
    });

    it('should filter profiles by vacancy', async () => {
      const mockResponse: MatchingWeightsListResponse = {
        profiles: [],
        total_count: 0,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      await client.listWeightProfiles(undefined, 'vacancy-456');

      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/matching-weights/profiles',
        {
          params: { vacancy_id: 'vacancy-456', is_active: true },
        }
      );
    });

    it('should filter presets only', async () => {
      const mockResponse: MatchingWeightsListResponse = {
        profiles: [],
        total_count: 0,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      await client.listWeightProfiles(undefined, undefined, true, true);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/matching-weights/profiles',
        {
          params: { is_preset: true, is_active: true },
        }
      );
    });

    it('should include inactive profiles when requested', async () => {
      const mockResponse: MatchingWeightsListResponse = {
        profiles: [],
        total_count: 0,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      await client.listWeightProfiles(undefined, undefined, undefined, false);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/matching-weights/profiles',
        {
          params: { is_active: false },
        }
      );
    });

    it('should handle list error', async () => {
      const error = {
        response: {
          status: 500,
          data: { detail: 'Database query failed' },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.listWeightProfiles()).rejects.toEqual({
        detail: 'Database query failed',
        status: 500,
      });
    });
  });

  describe('getPresetProfiles', () => {
    it('should get preset profiles successfully', async () => {
      const mockResponse: PresetsResponse = {
        presets: [
          {
            id: 'technical',
            name: 'Technical',
            description: 'High keyword weight for technical roles',
            use_case: 'Best for developer and engineering positions',
            keyword_weight: 0.6,
            tfidf_weight: 0.25,
            vector_weight: 0.15,
            weights_percentage: {
              keyword_weight: 60,
              tfidf_weight: 25,
              vector_weight: 15,
            },
          },
          {
            id: 'balanced',
            name: 'Balanced',
            description: 'Equal weight distribution',
            use_case: 'Good all-around profile for most roles',
            keyword_weight: 0.33,
            tfidf_weight: 0.33,
            vector_weight: 0.34,
            weights_percentage: {
              keyword_weight: 33,
              tfidf_weight: 33,
              vector_weight: 34,
            },
          },
        ],
        total_count: 2,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await client.getPresetProfiles();

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/matching-weights/profiles/presets'
      );
    });

    it('should handle preset fetch error', async () => {
      const error = {
        response: {
          status: 503,
          data: { detail: 'Service unavailable' },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.getPresetProfiles()).rejects.toEqual({
        detail: 'Service unavailable. Please try again later.',
        status: 503,
      });
    });
  });

  describe('getWeightProfile', () => {
    it('should get weight profile by ID successfully', async () => {
      const mockResponse: MatchingWeightsProfile = {
        id: 'profile-123',
        name: 'Custom Profile',
        description: 'A custom weight profile',
        keyword_weight: 0.5,
        tfidf_weight: 0.3,
        vector_weight: 0.2,
        weights_percentage: {
          keyword_weight: 50,
          tfidf_weight: 30,
          vector_weight: 20,
        },
        is_preset: false,
        is_active: true,
        organization_id: 'org-123',
        created_at: '2024-01-25T00:00:00Z',
        updated_at: '2024-01-25T00:00:00Z',
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await client.getWeightProfile('profile-123');

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/matching-weights/profiles/profile-123'
      );
    });

    it('should handle not found error', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Profile not found' },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.getWeightProfile('invalid-id')).rejects.toEqual({
        detail: 'Profile not found',
        status: 404,
      });
    });
  });

  describe('createWeightProfile', () => {
    it('should create weight profile successfully', async () => {
      const mockRequest: MatchingWeightsCreate = {
        name: 'My Custom Profile',
        description: 'A custom profile for senior roles',
        keyword_weight: 0.7,
        tfidf_weight: 0.2,
        vector_weight: 0.1,
        organization_id: 'org-123',
      };

      const mockResponse: MatchingWeightsProfile = {
        id: 'profile-new',
        name: 'My Custom Profile',
        description: 'A custom profile for senior roles',
        keyword_weight: 0.7,
        tfidf_weight: 0.2,
        vector_weight: 0.1,
        weights_percentage: {
          keyword_weight: 70,
          tfidf_weight: 20,
          vector_weight: 10,
        },
        is_preset: false,
        is_active: true,
        organization_id: 'org-123',
        created_at: '2024-01-25T00:00:00Z',
        updated_at: '2024-01-25T00:00:00Z',
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await client.createWeightProfile(mockRequest);

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/matching-weights/profiles',
        mockRequest
      );
    });

    it('should handle validation error', async () => {
      const mockRequest: MatchingWeightsCreate = {
        name: 'Invalid Profile',
        keyword_weight: -0.5,
        tfidf_weight: 0.5,
        vector_weight: 1.0,
      };

      const error = {
        response: {
          status: 422,
          data: { detail: 'Weights must be non-negative' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(client.createWeightProfile(mockRequest)).rejects.toEqual({
        detail: 'Weights must be non-negative',
        status: 422,
      });
    });

    it('should handle network error during creation', async () => {
      const mockRequest: MatchingWeightsCreate = {
        name: 'Test Profile',
        keyword_weight: 0.5,
        tfidf_weight: 0.3,
        vector_weight: 0.2,
      };

      const error = {
        code: 'ECONNABORTED',
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(client.createWeightProfile(mockRequest)).rejects.toEqual({
        detail: 'Таймаут запроса. Проверьте соединение и попробуйте снова.',
        status: 408,
      });
    });
  });

  describe('updateWeightProfile', () => {
    it('should update weight profile successfully', async () => {
      const mockRequest: MatchingWeightsUpdate = {
        keyword_weight: 0.65,
        change_reason: 'Increased keyword weight for better matching',
      };

      const mockResponse: MatchingWeightsProfile = {
        id: 'profile-123',
        name: 'Updated Profile',
        description: 'Profile with updated weights',
        keyword_weight: 0.65,
        tfidf_weight: 0.25,
        vector_weight: 0.1,
        weights_percentage: {
          keyword_weight: 65,
          tfidf_weight: 25,
          vector_weight: 10,
        },
        is_preset: false,
        is_active: true,
        organization_id: 'org-123',
        created_at: '2024-01-24T00:00:00Z',
        updated_at: '2024-01-25T01:00:00Z',
      };

      mockAxiosInstance.put.mockResolvedValue({ data: mockResponse });

      const result = await client.updateWeightProfile('profile-123', mockRequest);

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.put).toHaveBeenCalledWith(
        '/api/matching-weights/profiles/profile-123',
        mockRequest
      );
    });

    it('should handle update error with not found', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Profile not found' },
        },
      };

      mockAxiosInstance.put.mockRejectedValue(error);

      await expect(
        client.updateWeightProfile('invalid-id', { name: 'Updated' })
      ).rejects.toEqual({
        detail: 'Profile not found',
        status: 404,
      });
    });

    it('should handle validation error on update', async () => {
      const error = {
        response: {
          status: 400,
          data: { detail: 'Cannot modify preset profiles' },
        },
      };

      mockAxiosInstance.put.mockRejectedValue(error);

      await expect(
        client.updateWeightProfile('preset-1', { name: 'Updated' })
      ).rejects.toEqual({
        detail: 'Cannot modify preset profiles',
        status: 400,
      });
    });
  });

  describe('deleteWeightProfile', () => {
    it('should delete weight profile successfully', async () => {
      mockAxiosInstance.delete.mockResolvedValue({});

      await expect(client.deleteWeightProfile('profile-123')).resolves.toBeUndefined();
      expect(mockAxiosInstance.delete).toHaveBeenCalledWith(
        '/api/matching-weights/profiles/profile-123'
      );
    });

    it('should handle delete error with not found', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Profile not found' },
        },
      };

      mockAxiosInstance.delete.mockRejectedValue(error);

      await expect(client.deleteWeightProfile('invalid-id')).rejects.toEqual({
        detail: 'Profile not found',
        status: 404,
      });
    });

    it('should handle forbidden delete error', async () => {
      const error = {
        response: {
          status: 403,
          data: { detail: 'Access denied. You do not have permission to delete this profile.' },
        },
      };

      mockAxiosInstance.delete.mockRejectedValue(error);

      await expect(client.deleteWeightProfile('profile-123')).rejects.toEqual({
        detail: 'Access denied. You do not have permission to delete this profile.',
        status: 403,
      });
    });
  });

  describe('getWeightProfileHistory', () => {
    it('should get profile version history successfully', async () => {
      const mockResponse: VersionHistoryResponse = {
        profile_id: 'profile-123',
        versions: [
          {
            version: 1,
            modified_at: '2024-01-24T00:00:00Z',
            modified_by: 'user-123',
            change_reason: 'Initial creation',
            weights: {
              keyword_weight: 0.5,
              tfidf_weight: 0.3,
              vector_weight: 0.2,
            },
          },
          {
            version: 2,
            modified_at: '2024-01-25T01:00:00Z',
            modified_by: 'user-456',
            change_reason: 'Increased keyword weight',
            weights: {
              keyword_weight: 0.6,
              tfidf_weight: 0.25,
              vector_weight: 0.15,
            },
          },
        ],
        total_versions: 2,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await client.getWeightProfileHistory('profile-123');

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/matching-weights/profiles/profile-123/history'
      );
    });

    it('should handle history fetch error', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Profile not found' },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.getWeightProfileHistory('invalid-id')).rejects.toEqual({
        detail: 'Profile not found',
        status: 404,
      });
    });
  });

  describe('normalizeWeights', () => {
    it('should normalize weights successfully', async () => {
      const mockRequest: NormalizeWeightsRequest = {
        keyword_weight: 0.5,
        tfidf_weight: 0.3,
        vector_weight: 0.3, // Sum = 1.1
      };

      const mockResponse: NormalizedWeightsResponse = {
        original_sum: 1.1,
        weights_applied: {
          keyword_weight: 0.45,
          tfidf_weight: 0.27,
          vector_weight: 0.27,
        },
        weights_percentage: {
          keyword_weight: 45,
          tfidf_weight: 27,
          vector_weight: 27,
        },
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await client.normalizeWeights(mockRequest);

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/matching-weights/normalize',
        mockRequest
      );
    });

    it('should handle normalization error', async () => {
      const mockRequest: NormalizeWeightsRequest = {
        keyword_weight: -0.5,
        tfidf_weight: 0.5,
        vector_weight: 1.0,
      };

      const error = {
        response: {
          status: 422,
          data: { detail: 'Weights must be non-negative' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(client.normalizeWeights(mockRequest)).rejects.toEqual({
        detail: 'Weights must be non-negative',
        status: 422,
      });
    });
  });

  describe('applyWeights', () => {
    it('should apply existing profile to vacancy successfully', async () => {
      const mockRequest: ApplyWeightsRequest = {
        vacancy_id: 'vacancy-123',
        profile_id: 'profile-456',
        re_match_candidates: true,
      };

      const mockResponse: ApplyWeightsResponse = {
        success: true,
        message: 'Weights applied successfully',
        vacancy_id: 'vacancy-123',
        profile_id: 'profile-456',
        weights_applied: {
          keyword_weight: 0.5,
          tfidf_weight: 0.3,
          vector_weight: 0.2,
        },
        candidates_affected: 15,
        processing_time_seconds: 2.5,
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await client.applyWeights(mockRequest);

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/matching-weights/apply',
        mockRequest
      );
    });

    it('should apply custom weights to vacancy successfully', async () => {
      const mockRequest: ApplyWeightsRequest = {
        vacancy_id: 'vacancy-123',
        weights: {
          keyword_weight: 0.6,
          tfidf_weight: 0.25,
          vector_weight: 0.15,
        },
        re_match_candidates: false,
      };

      const mockResponse: ApplyWeightsResponse = {
        success: true,
        message: 'Custom weights applied successfully',
        vacancy_id: 'vacancy-123',
        weights_applied: {
          keyword_weight: 0.6,
          tfidf_weight: 0.25,
          vector_weight: 0.15,
        },
        candidates_affected: 0,
        processing_time_seconds: 0.1,
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await client.applyWeights(mockRequest);

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/matching-weights/apply',
        mockRequest
      );
    });

    it('should handle apply error with vacancy not found', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Vacancy not found' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        client.applyWeights({
          vacancy_id: 'invalid-vacancy',
          profile_id: 'profile-123',
        })
      ).rejects.toEqual({
        detail: 'Vacancy not found',
        status: 404,
      });
    });

    it('should handle apply error with profile not found', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Weight profile not found' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        client.applyWeights({
          vacancy_id: 'vacancy-123',
          profile_id: 'invalid-profile',
        })
      ).rejects.toEqual({
        detail: 'Weight profile not found',
        status: 404,
      });
    });

    it('should handle validation error when neither profile nor weights provided', async () => {
      const error = {
        response: {
          status: 422,
          data: { detail: 'Either profile_id or weights must be provided' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        client.applyWeights({ vacancy_id: 'vacancy-123' } as any)
      ).rejects.toEqual({
        detail: 'Either profile_id or weights must be provided',
        status: 422,
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

      await expect(client.listWeightProfiles()).rejects.toEqual({
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

      await expect(client.listWeightProfiles()).rejects.toEqual({
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

      mockAxiosInstance.delete.mockRejectedValue(error);

      await expect(client.deleteWeightProfile('profile-123')).rejects.toEqual({
        detail: 'Доступ запрещен. У вас нет прав для выполнения этого действия.',
        status: 403,
      });
    });

    it('should transform 422 error', async () => {
      const error = {
        response: {
          status: 422,
          data: {},
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        client.createWeightProfile({
          name: 'Test',
          keyword_weight: 0.5,
          tfidf_weight: 0.3,
          vector_weight: 0.2,
        })
      ).rejects.toEqual({
        detail: 'Ошибка валидации. Проверьте введенные данные.',
        status: 422,
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

      await expect(client.listWeightProfiles()).rejects.toEqual({
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

      await expect(client.listWeightProfiles()).rejects.toEqual({
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

      await expect(client.listWeightProfiles()).rejects.toEqual({
        detail: 'Произошла непредвиденная ошибка.',
        status: 418,
      });
    });

    it('should handle network error without response', async () => {
      const error = {};

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.listWeightProfiles()).rejects.toEqual({
        detail: 'Ошибка сети. Проверьте соединение и попробуйте снова.',
        status: 0,
      });
    });

    it('should handle timeout error', async () => {
      const error = {
        code: 'ECONNABORTED',
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.listWeightProfiles()).rejects.toEqual({
        detail: 'Таймаут запроса. Проверьте соединение и попробуйте снова.',
        status: 408,
      });
    });

    it('should transform 500 error with default message', async () => {
      const error = {
        response: {
          status: 500,
          data: {},
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.listWeightProfiles()).rejects.toEqual({
        detail: 'Ошибка сервера. Попробуйте позже.',
        status: 500,
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

      await expect(client.listWeightProfiles()).rejects.toEqual({
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

      await expect(client.listWeightProfiles()).rejects.toEqual({
        detail: 'Сервис недоступен. Попробуйте позже.',
        status: 503,
      });
    });
  });
});
