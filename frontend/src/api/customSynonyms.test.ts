/**
 * Tests for Custom Synonyms API Client
 *
 * Tests the Axios-based API client for custom synonym CRUD operations.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { CustomSynonymsClient } from './customSynonyms';
import axios from 'axios';
import type {
  CustomSynonymCreate,
  CustomSynonymUpdate,
  CustomSynonymResponse,
  CustomSynonymListResponse,
  ApiError,
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
      post: vi.fn(),
      get: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
    })),
  },
}));

describe('CustomSynonymsClient', () => {
  let client: CustomSynonymsClient;
  let mockAxiosInstance: any;

  beforeEach(() => {
    // Create mock axios instance
    mockAxiosInstance = {
      interceptors: {
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
    client = new CustomSynonymsClient({ baseURL: 'http://test.com' });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Constructor', () => {
    it('should create client with default config', () => {
      const customClient = new CustomSynonymsClient();
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
      const customClient = new CustomSynonymsClient({
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

  describe('createCustomSynonyms', () => {
    it('should create custom synonyms successfully', async () => {
      const mockRequest: CustomSynonymCreate = {
        organization_id: 'org123',
        created_by: 'user456',
        synonyms: [
          {
            canonical_skill: 'React',
            custom_synonyms: ['ReactJS', 'React.js', 'React Framework'],
            context: 'web_framework',
            is_active: true,
          },
        ],
      };

      const mockResponse: CustomSynonymListResponse = {
        organization_id: 'org123',
        synonyms: [
          {
            id: 'synonym-123',
            organization_id: 'org123',
            canonical_skill: 'React',
            custom_synonyms: ['ReactJS', 'React.js', 'React Framework'],
            context: 'web_framework',
            created_by: 'user456',
            is_active: true,
            created_at: '2024-01-25T00:00:00Z',
            updated_at: '2024-01-25T00:00:00Z',
          },
        ],
        total_count: 1,
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await client.createCustomSynonyms(mockRequest);

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/custom-synonyms/',
        mockRequest
      );
    });

    it('should handle creation error with validation failure', async () => {
      const mockRequest: CustomSynonymCreate = {
        organization_id: 'org123',
        synonyms: [],
      };

      const error = {
        response: {
          status: 422,
          data: { detail: 'At least one synonym entry is required' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(client.createCustomSynonyms(mockRequest)).rejects.toEqual({
        detail: 'At least one synonym entry is required',
        status: 422,
      });
    });

    it('should handle network error during creation', async () => {
      const mockRequest: CustomSynonymCreate = {
        organization_id: 'org123',
        synonyms: [
          {
            canonical_skill: 'React',
            custom_synonyms: ['ReactJS'],
            is_active: true,
          },
        ],
      };

      const error = {
        code: 'ECONNABORTED',
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(client.createCustomSynonyms(mockRequest)).rejects.toEqual({
        detail: 'Request timeout. Please check your connection and try again.',
        status: 408,
      });
    });
  });

  describe('listCustomSynonyms', () => {
    it('should list all custom synonyms successfully', async () => {
      const mockResponse: CustomSynonymListResponse[] = [
        {
          organization_id: 'org123',
          synonyms: [
            {
              id: 'synonym-1',
              organization_id: 'org123',
              canonical_skill: 'React',
              custom_synonyms: ['ReactJS', 'React.js'],
              is_active: true,
              created_at: '2024-01-25T00:00:00Z',
              updated_at: '2024-01-25T00:00:00Z',
            },
          ],
          total_count: 1,
        },
      ];

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await client.listCustomSynonyms();

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/custom-synonyms/',
        { params: {} }
      );
    });

    it('should list custom synonyms with organization filter', async () => {
      const mockResponse: CustomSynonymListResponse[] = [
        {
          organization_id: 'org123',
          synonyms: [],
          total_count: 0,
        },
      ];

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await client.listCustomSynonyms({ organization_id: 'org123' });

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/custom-synonyms/', {
        params: { organization_id: 'org123' },
      });
    });

    it('should list custom synonyms with multiple filters', async () => {
      const mockResponse: CustomSynonymListResponse[] = [];

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await client.listCustomSynonyms({
        organization_id: 'org123',
        canonical_skill: 'React',
        is_active: true,
      });

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/custom-synonyms/', {
        params: {
          organization_id: 'org123',
          canonical_skill: 'React',
          is_active: true,
        },
      });
    });

    it('should handle list error with not found', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Organization not found' },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(
        client.listCustomSynonyms({ organization_id: 'invalid-org' })
      ).rejects.toEqual({
        detail: 'Organization not found',
        status: 404,
      });
    });
  });

  describe('getCustomSynonym', () => {
    it('should get custom synonym by ID successfully', async () => {
      const mockResponse: CustomSynonymResponse = {
        id: 'synonym-123',
        organization_id: 'org123',
        canonical_skill: 'React',
        custom_synonyms: ['ReactJS', 'React.js'],
        context: 'web_framework',
        created_by: 'user456',
        is_active: true,
        created_at: '2024-01-25T00:00:00Z',
        updated_at: '2024-01-25T00:00:00Z',
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await client.getCustomSynonym('synonym-123');

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/custom-synonyms/synonym-123'
      );
    });

    it('should handle not found error', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Custom synonym not found' },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.getCustomSynonym('invalid-id')).rejects.toEqual({
        detail: 'Custom synonym not found',
        status: 404,
      });
    });

    it('should handle network error', async () => {
      const error = {
        code: 'ECONNABORTED',
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.getCustomSynonym('synonym-123')).rejects.toEqual({
        detail: 'Request timeout. Please check your connection and try again.',
        status: 408,
      });
    });
  });

  describe('updateCustomSynonym', () => {
    it('should update custom synonym successfully', async () => {
      const mockRequest: CustomSynonymUpdate = {
        canonical_skill: 'React',
        custom_synonyms: ['ReactJS', 'React.js', 'React Framework'],
        is_active: true,
      };

      const mockResponse: CustomSynonymResponse = {
        id: 'synonym-123',
        organization_id: 'org123',
        canonical_skill: 'React',
        custom_synonyms: ['ReactJS', 'React.js', 'React Framework'],
        context: 'web_framework',
        created_by: 'user456',
        is_active: true,
        created_at: '2024-01-25T00:00:00Z',
        updated_at: '2024-01-25T01:00:00Z',
      };

      mockAxiosInstance.put.mockResolvedValue({ data: mockResponse });

      const result = await client.updateCustomSynonym('synonym-123', mockRequest);

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.put).toHaveBeenCalledWith(
        '/api/custom-synonyms/synonym-123',
        mockRequest
      );
    });

    it('should handle update error with not found', async () => {
      const mockRequest: CustomSynonymUpdate = {
        canonical_skill: 'React',
      };

      const error = {
        response: {
          status: 404,
          data: { detail: 'Custom synonym not found' },
        },
      };

      mockAxiosInstance.put.mockRejectedValue(error);

      await expect(
        client.updateCustomSynonym('invalid-id', mockRequest)
      ).rejects.toEqual({
        detail: 'Custom synonym not found',
        status: 404,
      });
    });

    it('should handle validation error during update', async () => {
      const mockRequest: CustomSynonymUpdate = {
        custom_synonyms: [],
      };

      const error = {
        response: {
          status: 422,
          data: { detail: 'At least one custom synonym is required' },
        },
      };

      mockAxiosInstance.put.mockRejectedValue(error);

      await expect(
        client.updateCustomSynonym('synonym-123', mockRequest)
      ).rejects.toEqual({
        detail: 'At least one custom synonym is required',
        status: 422,
      });
    });
  });

  describe('deleteCustomSynonym', () => {
    it('should delete custom synonym successfully', async () => {
      mockAxiosInstance.delete.mockResolvedValue({});

      await expect(
        client.deleteCustomSynonym('synonym-123')
      ).resolves.toBeUndefined();
      expect(mockAxiosInstance.delete).toHaveBeenCalledWith(
        '/api/custom-synonyms/synonym-123'
      );
    });

    it('should handle delete error with not found', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Custom synonym not found' },
        },
      };

      mockAxiosInstance.delete.mockRejectedValue(error);

      await expect(client.deleteCustomSynonym('invalid-id')).rejects.toEqual({
        detail: 'Custom synonym not found',
        status: 404,
      });
    });

    it('should handle forbidden error', async () => {
      const error = {
        response: {
          status: 403,
          data: {},
        },
      };

      mockAxiosInstance.delete.mockRejectedValue(error);

      await expect(client.deleteCustomSynonym('synonym-123')).rejects.toEqual({
        detail: 'Forbidden. You do not have permission.',
        status: 403,
      });
    });
  });

  describe('deleteCustomSynonymsByOrganization', () => {
    it('should delete all custom synonyms for organization successfully', async () => {
      mockAxiosInstance.delete.mockResolvedValue({});

      await expect(
        client.deleteCustomSynonymsByOrganization('org123')
      ).resolves.toBeUndefined();
      expect(mockAxiosInstance.delete).toHaveBeenCalledWith(
        '/api/custom-synonyms/organization/org123'
      );
    });

    it('should handle delete by organization error with not found', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Organization not found' },
        },
      };

      mockAxiosInstance.delete.mockRejectedValue(error);

      await expect(
        client.deleteCustomSynonymsByOrganization('invalid-org')
      ).rejects.toEqual({
        detail: 'Organization not found',
        status: 404,
      });
    });

    it('should handle network error during delete by organization', async () => {
      const error = {};

      mockAxiosInstance.delete.mockRejectedValue(error);

      await expect(
        client.deleteCustomSynonymsByOrganization('org123')
      ).rejects.toEqual({
        detail: 'Network error. Please check your connection and try again.',
        status: 0,
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

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        client.createCustomSynonyms({
          organization_id: 'org123',
          synonyms: [],
        })
      ).rejects.toEqual({
        detail: 'Invalid request. Please check your input.',
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

      await expect(client.getCustomSynonym('synonym-123')).rejects.toEqual({
        detail: 'Unauthorized. Please log in.',
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

      await expect(client.deleteCustomSynonym('synonym-123')).rejects.toEqual({
        detail: 'Forbidden. You do not have permission.',
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

      await expect(client.listCustomSynonyms()).rejects.toEqual({
        detail: 'Too many requests. Please try again later.',
        status: 429,
      });
    });

    it('should transform 500 error', async () => {
      const error = {
        response: {
          status: 500,
          data: {},
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.getCustomSynonym('synonym-123')).rejects.toEqual({
        detail: 'Server error. Please try again later.',
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

      await expect(client.getCustomSynonym('synonym-123')).rejects.toEqual({
        detail: 'Bad gateway. Please try again later.',
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

      await expect(client.getCustomSynonym('synonym-123')).rejects.toEqual({
        detail: 'Service unavailable. Please try again later.',
        status: 503,
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

      await expect(client.getCustomSynonym('synonym-123')).rejects.toEqual({
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

      await expect(client.getCustomSynonym('synonym-123')).rejects.toEqual({
        detail: 'An unexpected error occurred.',
        status: 418,
      });
    });

    it('should transform timeout error', async () => {
      const error = {
        code: 'ECONNABORTED',
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.getCustomSynonym('synonym-123')).rejects.toEqual({
        detail: 'Request timeout. Please check your connection and try again.',
        status: 408,
      });
    });

    it('should transform network error without response', async () => {
      const error = {};

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.getCustomSynonym('synonym-123')).rejects.toEqual({
        detail: 'Network error. Please check your connection and try again.',
        status: 0,
      });
    });
  });
});
