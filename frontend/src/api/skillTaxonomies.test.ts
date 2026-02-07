/**
 * Tests for Skill Taxonomies API Client
 *
 * Tests the Axios-based API client for skill taxonomy CRUD operations.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { SkillTaxonomiesClient } from './skillTaxonomies';
import axios from 'axios';
import type {
  SkillTaxonomyCreate,
  SkillTaxonomyUpdate,
  SkillTaxonomyResponse,
  SkillTaxonomyListResponse,
  ApiError,
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

describe('SkillTaxonomiesClient', () => {
  let client: SkillTaxonomiesClient;
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
    client = new SkillTaxonomiesClient({ baseURL: 'http://test.com' });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Constructor', () => {
    it('should create client with default config', () => {
      const testClient = new SkillTaxonomiesClient();
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
      const testClient = new SkillTaxonomiesClient({
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

    it('should set up response interceptor for error handling', () => {
      expect(mockAxiosInstance.interceptors.response.use).toHaveBeenCalled();
    });
  });

  describe('createSkillTaxonomies', () => {
    it('should create skill taxonomies successfully', async () => {
      const mockRequest: SkillTaxonomyCreate = {
        industry: 'healthcare',
        skills: [
          {
            name: 'Patient Care',
            context: 'clinical',
            variants: ['patient care', 'caregiving', 'patient support'],
            metadata: { category: 'clinical' },
            is_active: true,
          },
        ],
      };

      const mockResponse: SkillTaxonomyListResponse = {
        industry: 'healthcare',
        skills: [
          {
            id: 'skill-123',
            industry: 'healthcare',
            skill_name: 'Patient Care',
            context: 'clinical',
            variants: ['patient care', 'caregiving', 'patient support'],
            metadata: { category: 'clinical' },
            is_active: true,
            created_at: '2024-01-25T00:00:00Z',
            updated_at: '2024-01-25T00:00:00Z',
          },
        ],
        total_count: 1,
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await client.createSkillTaxonomies(mockRequest);

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/skill-taxonomies/',
        mockRequest
      );
    });

    it('should handle validation error', async () => {
      const mockRequest: SkillTaxonomyCreate = {
        industry: '',
        skills: [],
      };

      const error = {
        response: {
          status: 422,
          data: { detail: 'Industry cannot be empty' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(client.createSkillTaxonomies(mockRequest)).rejects.toEqual({
        detail: 'Industry cannot be empty',
        status: 422,
      });
    });

    it('should handle network error', async () => {
      const mockRequest: SkillTaxonomyCreate = {
        industry: 'healthcare',
        skills: [],
      };

      const error = {
        code: 'ECONNABORTED',
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(client.createSkillTaxonomies(mockRequest)).rejects.toEqual({
        detail: 'Request timeout. Please check your connection and try again.',
        status: 408,
      });
    });
  });

  describe('listSkillTaxonomies', () => {
    it('should list skill taxonomies with default options', async () => {
      const mockResponse: SkillTaxonomyListResponse = {
        industry: 'healthcare',
        skills: [
          {
            id: 'skill-1',
            industry: 'healthcare',
            skill_name: 'Patient Care',
            variants: ['patient care'],
            is_active: true,
            created_at: '2024-01-25T00:00:00Z',
            updated_at: '2024-01-25T00:00:00Z',
          },
        ],
        total_count: 1,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await client.listSkillTaxonomies('healthcare');

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/skill-taxonomies/', {
        params: {
          industry: 'healthcare',
          skip: 0,
          limit: 100,
        },
      });
    });

    it('should list skill taxonomies with pagination', async () => {
      const mockResponse: SkillTaxonomyListResponse = {
        industry: 'healthcare',
        skills: [],
        total_count: 50,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await client.listSkillTaxonomies('healthcare', {
        skip: 20,
        limit: 10,
      });

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/skill-taxonomies/', {
        params: {
          industry: 'healthcare',
          skip: 20,
          limit: 10,
        },
      });
    });

    it('should list skill taxonomies with active filter', async () => {
      const mockResponse: SkillTaxonomyListResponse = {
        industry: 'healthcare',
        skills: [
          {
            id: 'skill-1',
            industry: 'healthcare',
            skill_name: 'Patient Care',
            variants: ['patient care'],
            is_active: true,
            created_at: '2024-01-25T00:00:00Z',
            updated_at: '2024-01-25T00:00:00Z',
          },
        ],
        total_count: 1,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await client.listSkillTaxonomies('healthcare', {
        is_active: true,
      });

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/skill-taxonomies/', {
        params: {
          industry: 'healthcare',
          skip: 0,
          limit: 100,
          is_active: true,
        },
      });
    });

    it('should list skill taxonomies with inactive filter', async () => {
      const mockResponse: SkillTaxonomyListResponse = {
        industry: 'healthcare',
        skills: [],
        total_count: 0,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await client.listSkillTaxonomies('healthcare', {
        is_active: false,
      });

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/skill-taxonomies/', {
        params: {
          industry: 'healthcare',
          skip: 0,
          limit: 100,
          is_active: false,
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

      await expect(client.listSkillTaxonomies('healthcare')).rejects.toEqual({
        detail: 'Database query failed',
        status: 500,
      });
    });
  });

  describe('getSkillTaxonomy', () => {
    it('should get a skill taxonomy by ID successfully', async () => {
      const mockResponse: SkillTaxonomyResponse = {
        id: 'skill-123',
        industry: 'healthcare',
        skill_name: 'Patient Care',
        context: 'clinical',
        variants: ['patient care', 'caregiving'],
        metadata: { category: 'clinical' },
        is_active: true,
        created_at: '2024-01-25T00:00:00Z',
        updated_at: '2024-01-25T00:00:00Z',
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await client.getSkillTaxonomy('skill-123');

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/skill-taxonomies/skill-123'
      );
    });

    it('should handle not found error', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Skill taxonomy not found' },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(client.getSkillTaxonomy('invalid-id')).rejects.toEqual({
        detail: 'Skill taxonomy not found',
        status: 404,
      });
    });
  });

  describe('updateSkillTaxonomy', () => {
    it('should update a skill taxonomy successfully', async () => {
      const mockRequest: SkillTaxonomyUpdate = {
        skill_name: 'Advanced Patient Care',
        variants: ['advanced patient care', 'senior caregiving'],
        is_active: true,
      };

      const mockResponse: SkillTaxonomyResponse = {
        id: 'skill-123',
        industry: 'healthcare',
        skill_name: 'Advanced Patient Care',
        variants: ['advanced patient care', 'senior caregiving'],
        is_active: true,
        created_at: '2024-01-25T00:00:00Z',
        updated_at: '2024-01-25T01:00:00Z',
      };

      mockAxiosInstance.put.mockResolvedValue({ data: mockResponse });

      const result = await client.updateSkillTaxonomy('skill-123', mockRequest);

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.put).toHaveBeenCalledWith(
        '/api/skill-taxonomies/skill-123',
        mockRequest
      );
    });

    it('should handle update with not found error', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Skill taxonomy not found' },
        },
      };

      mockAxiosInstance.put.mockRejectedValue(error);

      await expect(
        client.updateSkillTaxonomy('invalid-id', { skill_name: 'New Name' })
      ).rejects.toEqual({
        detail: 'Skill taxonomy not found',
        status: 404,
      });
    });

    it('should handle validation error on update', async () => {
      const error = {
        response: {
          status: 422,
          data: { detail: 'Invalid skill name format' },
        },
      };

      mockAxiosInstance.put.mockRejectedValue(error);

      await expect(
        client.updateSkillTaxonomy('skill-123', { skill_name: '' })
      ).rejects.toEqual({
        detail: 'Invalid skill name format',
        status: 422,
      });
    });
  });

  describe('deleteSkillTaxonomy', () => {
    it('should delete a skill taxonomy successfully', async () => {
      mockAxiosInstance.delete.mockResolvedValue({});

      await expect(client.deleteSkillTaxonomy('skill-123')).resolves.toBeUndefined();
      expect(mockAxiosInstance.delete).toHaveBeenCalledWith(
        '/api/skill-taxonomies/skill-123'
      );
    });

    it('should handle delete error with not found', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Skill taxonomy not found' },
        },
      };

      mockAxiosInstance.delete.mockRejectedValue(error);

      await expect(client.deleteSkillTaxonomy('invalid-id')).rejects.toEqual({
        detail: 'Skill taxonomy not found',
        status: 404,
      });
    });
  });

  describe('deleteSkillTaxonomiesByIndustry', () => {
    it('should delete all skill taxonomies for an industry successfully', async () => {
      const mockResponse = {
        deleted_count: 25,
        industry: 'healthcare',
      };

      mockAxiosInstance.delete.mockResolvedValue({ data: mockResponse });

      const result = await client.deleteSkillTaxonomiesByIndustry('healthcare');

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.delete).toHaveBeenCalledWith(
        '/api/skill-taxonomies/industry/healthcare'
      );
    });

    it('should handle delete by industry error', async () => {
      const error = {
        response: {
          status: 500,
          data: { detail: 'Failed to delete skill taxonomies' },
        },
      };

      mockAxiosInstance.delete.mockRejectedValue(error);

      await expect(
        client.deleteSkillTaxonomiesByIndustry('healthcare')
      ).rejects.toEqual({
        detail: 'Failed to delete skill taxonomies',
        status: 500,
      });
    });

    it('should handle industry not found during deletion', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Industry not found' },
        },
      };

      mockAxiosInstance.delete.mockRejectedValue(error);

      await expect(
        client.deleteSkillTaxonomiesByIndustry('nonexistent')
      ).rejects.toEqual({
        detail: 'Industry not found',
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
    it('should transform network error with ECONNABORTED code', async () => {
      const error = {
        code: 'ECONNABORTED',
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        client.createSkillTaxonomies({ industry: 'test', skills: [] })
      ).rejects.toEqual({
        detail: 'Request timeout. Please check your connection and try again.',
        status: 408,
      });
    });

    it('should transform network error without response', async () => {
      const error = {};

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        client.createSkillTaxonomies({ industry: 'test', skills: [] })
      ).rejects.toEqual({
        detail: 'Network error. Please check your connection and try again.',
        status: 0,
      });
    });

    it('should transform 400 error with default message', async () => {
      const error = {
        response: {
          status: 400,
          data: {},
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        client.createSkillTaxonomies({ industry: 'test', skills: [] })
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

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        client.createSkillTaxonomies({ industry: 'test', skills: [] })
      ).rejects.toEqual({
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

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        client.createSkillTaxonomies({ industry: 'test', skills: [] })
      ).rejects.toEqual({
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

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        client.createSkillTaxonomies({ industry: 'test', skills: [] })
      ).rejects.toEqual({
        detail: 'Too many requests. Please try again later.',
        status: 429,
      });
    });

    it('should transform 500 error with default message', async () => {
      const error = {
        response: {
          status: 500,
          data: {},
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        client.createSkillTaxonomies({ industry: 'test', skills: [] })
      ).rejects.toEqual({
        detail: 'Server error. Please try again later.',
        status: 500,
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

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        client.createSkillTaxonomies({ industry: 'test', skills: [] })
      ).rejects.toEqual({
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

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        client.createSkillTaxonomies({ industry: 'test', skills: [] })
      ).rejects.toEqual({
        detail: 'An unexpected error occurred.',
        status: 418,
      });
    });
  });
});
