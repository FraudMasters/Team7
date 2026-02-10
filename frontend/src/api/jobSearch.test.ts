/**
 * Tests for Job Search API Client
 *
 * Tests the Axios-based API client for job search functionality.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { JobSearchClient } from './jobSearch';
import axios from 'axios';
import type {
  JobSearchRequest,
  JobSearchResponse,
  JobSearchFilters,
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
    })),
  },
}));

describe('JobSearchClient', () => {
  let client: JobSearchClient;
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
    };

    // Mock axios.create to return our mock instance
    vi.mocked(axios.create).mockReturnValue(mockAxiosInstance as any);

    // Create client with mock
    client = new JobSearchClient({ baseURL: 'http://test.com' });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Constructor', () => {
    it('should create client with default config', () => {
      const testClient = new JobSearchClient();
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
      const testClient = new JobSearchClient({
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

  describe('searchJobs', () => {
    const mockJobResult = {
      id: 'job-123',
      title: 'Senior Python Developer',
      description: 'We are looking for a senior Python developer...',
      required_skills: ['Python', 'FastAPI', 'PostgreSQL'],
      min_experience_months: 48,
      additional_requirements: ['Docker', 'Kubernetes'],
      industry: 'tech',
      work_format: 'remote',
      location: 'Remote',
      salary_min: 80000,
      salary_max: 120000,
      english_level: 'B2',
      employment_type: 'full-time',
      created_at: '2024-01-01T00:00:00Z',
    };

    const mockSearchResponse: JobSearchResponse = {
      total: 1,
      jobs: [mockJobResult],
      query: 'Python developer',
      filters_applied: {},
      execution_time_seconds: 0.05,
      skip: 0,
      limit: 20,
    };

    it('should search jobs with query only', async () => {
      const request: JobSearchRequest = {
        query: 'Python developer',
        limit: 20,
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockSearchResponse });

      const result = await client.searchJobs(request);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/job-search/search',
        {
          query: 'Python developer',
          filters: null,
          skip: 0,
          limit: 20,
          sort_by: 'date',
        }
      );
      expect(result).toEqual(mockSearchResponse);
    });

    it('should search jobs with filters', async () => {
      const filters: JobSearchFilters = {
        location: 'Remote',
        salary_min: 50000,
        salary_max: 100000,
        work_format: 'remote',
        employment_type: 'full-time',
        industry: 'tech',
        skills: ['Python', 'FastAPI'],
      };

      const request: JobSearchRequest = {
        query: 'Backend developer',
        filters,
        limit: 50,
        sort_by: 'salary_desc',
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockSearchResponse });

      const result = await client.searchJobs(request);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/job-search/search',
        {
          query: 'Backend developer',
          filters,
          skip: 0,
          limit: 50,
          sort_by: 'salary_desc',
        }
      );
      expect(result).toEqual(mockSearchResponse);
    });

    it('should search jobs with empty request (defaults)', async () => {
      mockAxiosInstance.post.mockResolvedValue({
        data: {
          ...mockSearchResponse,
          query: '',
          jobs: [],
          total: 0,
        },
      });

      const result = await client.searchJobs({});

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/job-search/search',
        {
          query: null,
          filters: null,
          skip: 0,
          limit: 100,
          sort_by: 'date',
        }
      );
      expect(result).toBeDefined();
    });

    it('should search jobs with pagination', async () => {
      const request: JobSearchRequest = {
        skip: 40,
        limit: 20,
      };

      mockAxiosInstance.post.mockResolvedValue({
        data: {
          ...mockSearchResponse,
          skip: 40,
          limit: 20,
        },
      });

      const result = await client.searchJobs(request);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/job-search/search',
        {
          query: null,
          filters: null,
          skip: 40,
          limit: 20,
          sort_by: 'date',
        }
      );
      expect(result).toBeDefined();
    });

    it('should support different sort options', async () => {
      const sortOptions: Array<'date' | 'salary_asc' | 'salary_desc' | 'relevance'> = [
        'date',
        'salary_asc',
        'salary_desc',
        'relevance',
      ];

      for (const sortBy of sortOptions) {
        mockAxiosInstance.post.mockResolvedValue({ data: mockSearchResponse });

        await client.searchJobs({ sort_by: sortBy });

        expect(mockAxiosInstance.post).toHaveBeenCalledWith(
          '/api/job-search/search',
          expect.objectContaining({
            sort_by: sortBy,
          })
        );
      }
    });
  });

  describe('searchJobsGet', () => {
    const mockJobResult = {
      id: 'job-123',
      title: 'Senior Python Developer',
      description: 'We are looking for a senior Python developer...',
      required_skills: ['Python', 'FastAPI', 'PostgreSQL'],
      min_experience_months: 48,
      additional_requirements: ['Docker', 'Kubernetes'],
      industry: 'tech',
      work_format: 'remote',
      location: 'Remote',
      salary_min: 80000,
      salary_max: 120000,
      english_level: 'B2',
      employment_type: 'full-time',
      created_at: '2024-01-01T00:00:00Z',
    };

    const mockSearchResponse: JobSearchResponse = {
      total: 1,
      jobs: [mockJobResult],
      query: 'Python developer',
      filters_applied: {},
      execution_time_seconds: 0.05,
      skip: 0,
      limit: 20,
    };

    it('should search jobs with query via GET', async () => {
      const request: JobSearchRequest = {
        query: 'Python developer',
        limit: 20,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockSearchResponse });

      const result = await client.searchJobsGet(request);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/job-search/search', {
        params: {
          query: 'Python developer',
          skip: 0,
          limit: 20,
          sort_by: 'date',
        },
      });
      expect(result).toEqual(mockSearchResponse);
    });

    it('should search jobs with filters via GET', async () => {
      const filters: JobSearchFilters = {
        location: 'Remote',
        salary_min: 50000,
        salary_max: 100000,
        work_format: 'remote',
        employment_type: 'full-time',
        industry: 'tech',
        skills: ['Python', 'FastAPI'],
      };

      const request: JobSearchRequest = {
        filters,
        limit: 50,
        sort_by: 'salary_desc',
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockSearchResponse });

      const result = await client.searchJobsGet(request);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/job-search/search', {
        params: {
          location: 'Remote',
          salary_min: 50000,
          salary_max: 100000,
          work_format: 'remote',
          employment_type: 'full-time',
          industry: 'tech',
          skills: 'Python,FastAPI',
          skip: 0,
          limit: 50,
          sort_by: 'salary_desc',
        },
      });
      expect(result).toEqual(mockSearchResponse);
    });

    it('should handle empty skills array correctly', async () => {
      const filters: JobSearchFilters = {
        skills: [],
      };

      const request: JobSearchRequest = { filters };

      mockAxiosInstance.get.mockResolvedValue({ data: mockSearchResponse });

      await client.searchJobsGet(request);

      // Skills should not be in params if empty
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/job-search/search', {
        params: {
          skip: 0,
          limit: 100,
          sort_by: 'date',
        },
      });
    });

    it('should join multiple skills with comma', async () => {
      const filters: JobSearchFilters = {
        skills: ['React', 'TypeScript', 'Node.js'],
      };

      const request: JobSearchRequest = { filters };

      mockAxiosInstance.get.mockResolvedValue({ data: mockSearchResponse });

      await client.searchJobsGet(request);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/job-search/search', {
        params: expect.objectContaining({
          skills: 'React,TypeScript,Node.js',
        }),
      });
    });
  });

  describe('Error Handling', () => {
    it('should transform network timeout errors', async () => {
      const networkError = new Error('Network Error');
      (networkError as any).code = 'ECONNABORTED';
      mockAxiosInstance.post.mockRejectedValue(networkError);

      await expect(client.searchJobs({ query: 'test' })).rejects.toMatchObject({
        detail: 'Таймаут запроса. Проверьте соединение и попробуйте снова.',
        status: 408,
      });
    });

    it('should transform general network errors', async () => {
      const networkError = new Error('Network Error');
      mockAxiosInstance.post.mockRejectedValue(networkError);

      await expect(client.searchJobs({ query: 'test' })).rejects.toMatchObject({
        detail: 'Ошибка сети. Проверьте соединение и попробуйте снова.',
        status: 0,
      });
    });

    it('should transform HTTP errors with server detail', async () => {
      const httpError = {
        response: {
          status: 400,
          data: { detail: 'Invalid search parameters' },
        },
      };
      mockAxiosInstance.post.mockRejectedValue(httpError);

      await expect(client.searchJobs({ query: 'test' })).rejects.toMatchObject({
        detail: 'Invalid search parameters',
        status: 400,
      });
    });

    it('should use default error message for 404', async () => {
      const httpError = {
        response: {
          status: 404,
          data: {},
        },
      };
      mockAxiosInstance.get.mockRejectedValue(httpError);

      await expect(client.searchJobsGet({ query: 'test' })).rejects.toMatchObject({
        detail: 'Ресурс не найден.',
        status: 404,
      });
    });

    it('should use default error message for 500', async () => {
      const httpError = {
        response: {
          status: 500,
          data: {},
        },
      };
      mockAxiosInstance.post.mockRejectedValue(httpError);

      await expect(client.searchJobs({ query: 'test' })).rejects.toMatchObject({
        detail: 'Ошибка сервера. Попробуйте позже.',
        status: 500,
      });
    });

    it('should transform 422 validation errors', async () => {
      const httpError = {
        response: {
          status: 422,
          data: { detail: 'Validation error: salary_min must be positive' },
        },
      };
      mockAxiosInstance.post.mockRejectedValue(httpError);

      await expect(client.searchJobs({ filters: { salary_min: -1 } })).rejects.toMatchObject({
        detail: 'Validation error: salary_min must be positive',
        status: 422,
      });
    });
  });

  describe('getAxiosInstance', () => {
    it('should return the underlying axios instance', () => {
      const instance = client.getAxiosInstance();
      expect(instance).toBe(mockAxiosInstance);
    });
  });

  describe('Exported Types', () => {
    it('should export JobSearchClient class', () => {
      expect(JobSearchClient).toBeDefined();
      expect(typeof JobSearchClient).toBe('function');
    });
  });
});
