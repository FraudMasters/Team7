/**
 * Tests for Saved Jobs API Client
 *
 * Tests the Axios-based API client for saved jobs functionality.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { SavedJobsClient } from './savedJobs';
import axios from 'axios';
import type {
  SaveJobRequest,
  SavedJobResponse,
  SavedJobsListResponse,
  CheckJobSavedResponse,
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
      delete: vi.fn(),
    })),
  },
}));

describe('SavedJobsClient', () => {
  let client: SavedJobsClient;
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
      delete: vi.fn(),
    };

    // Mock axios.create to return our mock instance
    vi.mocked(axios.create).mockReturnValue(mockAxiosInstance as any);

    // Create client with mock
    client = new SavedJobsClient({ baseURL: 'http://test.com' });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Constructor', () => {
    it('should create client with default config', () => {
      const testClient = new SavedJobsClient();
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
      const testClient = new SavedJobsClient({
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

  describe('saveJob', () => {
    const mockSavedJob: SavedJobResponse = {
      id: 'saved-123',
      user_id: 'user-456',
      vacancy_id: 'vacancy-789',
      vacancy_title: 'Senior Python Developer',
      vacancy_description: 'We are looking for a senior Python developer...',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    it('should save a job', async () => {
      const request: SaveJobRequest = {
        vacancy_id: 'vacancy-789',
        user_id: 'user-456',
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockSavedJob });

      const result = await client.saveJob(request);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/saved-jobs/save',
        request
      );
      expect(result).toEqual(mockSavedJob);
    });

    it('should save a job with UUID format IDs', async () => {
      const request: SaveJobRequest = {
        vacancy_id: '550e8400-e29b-41d4-a716-446655440000',
        user_id: '550e8400-e29b-41d4-a716-446655440001',
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockSavedJob });

      const result = await client.saveJob(request);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/saved-jobs/save',
        request
      );
      expect(result).toEqual(mockSavedJob);
    });
  });

  describe('getSavedJobs', () => {
    const mockSavedJob: SavedJobResponse = {
      id: 'saved-123',
      user_id: 'user-456',
      vacancy_id: 'vacancy-789',
      vacancy_title: 'Senior Python Developer',
      vacancy_description: 'We are looking for a senior Python developer...',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    const mockListResponse: SavedJobsListResponse = {
      total: 1,
      saved_jobs: [mockSavedJob],
    };

    it('should get saved jobs with default pagination', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: mockListResponse });

      const result = await client.getSavedJobs('user-456');

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/saved-jobs/', {
        params: { user_id: 'user-456', skip: 0, limit: 100 },
      });
      expect(result).toEqual(mockListResponse);
    });

    it('should get saved jobs with custom pagination', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: mockListResponse });

      const result = await client.getSavedJobs('user-456', 20, 50);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/saved-jobs/', {
        params: { user_id: 'user-456', skip: 20, limit: 50 },
      });
      expect(result).toEqual(mockListResponse);
    });

    it('should get saved jobs with UUID format user ID', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: mockListResponse });

      const result = await client.getSavedJobs('550e8400-e29b-41d4-a716-446655440000');

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/saved-jobs/', {
        params: {
          user_id: '550e8400-e29b-41d4-a716-446655440000',
          skip: 0,
          limit: 100,
        },
      });
      expect(result).toEqual(mockListResponse);
    });

    it('should return empty list when no saved jobs', async () => {
      mockAxiosInstance.get.mockResolvedValue({
        data: { total: 0, saved_jobs: [] },
      });

      const result = await client.getSavedJobs('user-456');

      expect(result.total).toBe(0);
      expect(result.saved_jobs).toEqual([]);
    });
  });

  describe('checkJobSaved', () => {
    const mockCheckSaved: CheckJobSavedResponse = {
      is_saved: true,
      saved_job_id: 'saved-123',
    };

    it('should check if job is saved (true)', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: mockCheckSaved });

      const result = await client.checkJobSaved('vacancy-789', 'user-456');

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/saved-jobs/check', {
        params: { vacancy_id: 'vacancy-789', user_id: 'user-456' },
      });
      expect(result.is_saved).toBe(true);
      expect(result.saved_job_id).toBe('saved-123');
    });

    it('should check if job is saved (false)', async () => {
      const mockNotSaved: CheckJobSavedResponse = {
        is_saved: false,
        saved_job_id: null,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockNotSaved });

      const result = await client.checkJobSaved('vacancy-789', 'user-456');

      expect(result.is_saved).toBe(false);
      expect(result.saved_job_id).toBeNull();
    });

    it('should check with UUID format IDs', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: mockCheckSaved });

      await client.checkJobSaved(
        '550e8400-e29b-41d4-a716-446655440000',
        '550e8400-e29b-41d4-a716-446655440001'
      );

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/saved-jobs/check', {
        params: {
          vacancy_id: '550e8400-e29b-41d4-a716-446655440000',
          user_id: '550e8400-e29b-41d4-a716-446655440001',
        },
      });
    });
  });

  describe('unsaveJob', () => {
    it('should unsave job by ID', async () => {
      mockAxiosInstance.delete.mockResolvedValue({});

      await client.unsaveJob('saved-123');

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/api/saved-jobs/saved-123');
    });

    it('should unsave job with UUID format ID', async () => {
      mockAxiosInstance.delete.mockResolvedValue({});

      await client.unsaveJob('550e8400-e29b-41d4-a716-446655440000');

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith(
        '/api/saved-jobs/550e8400-e29b-41d4-a716-446655440000'
      );
    });
  });

  describe('unsaveJobByVacancy', () => {
    it('should unsave job by vacancy and user ID', async () => {
      mockAxiosInstance.delete.mockResolvedValue({});

      await client.unsaveJobByVacancy('vacancy-789', 'user-456');

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/api/saved-jobs/unsave', {
        params: { vacancy_id: 'vacancy-789', user_id: 'user-456' },
      });
    });

    it('should unsave job by vacancy with UUID format IDs', async () => {
      mockAxiosInstance.delete.mockResolvedValue({});

      await client.unsaveJobByVacancy(
        '550e8400-e29b-41d4-a716-446655440000',
        '550e8400-e29b-41d4-a716-446655440001'
      );

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/api/saved-jobs/unsave', {
        params: {
          vacancy_id: '550e8400-e29b-41d4-a716-446655440000',
          user_id: '550e8400-e29b-41d4-a716-446655440001',
        },
      });
    });
  });

  describe('Error Handling', () => {
    it('should transform network timeout errors', async () => {
      const networkError = new Error('Network Error');
      (networkError as any).code = 'ECONNABORTED';
      mockAxiosInstance.post.mockRejectedValue(networkError);

      await expect(
        client.saveJob({ vacancy_id: 'test', user_id: 'test' })
      ).rejects.toMatchObject({
        detail: 'Таймаут запроса. Проверьте соединение и попробуйте снова.',
        status: 408,
      });
    });

    it('should transform general network errors', async () => {
      const networkError = new Error('Network Error');
      mockAxiosInstance.post.mockRejectedValue(networkError);

      await expect(
        client.saveJob({ vacancy_id: 'test', user_id: 'test' })
      ).rejects.toMatchObject({
        detail: 'Ошибка сети. Проверьте соединение и попробуйте снова.',
        status: 0,
      });
    });

    it('should transform HTTP errors with server detail', async () => {
      const httpError = {
        response: {
          status: 400,
          data: { detail: 'Invalid UUID format' },
        },
      };
      mockAxiosInstance.post.mockRejectedValue(httpError);

      await expect(
        client.saveJob({ vacancy_id: 'invalid', user_id: 'test' })
      ).rejects.toMatchObject({
        detail: 'Invalid UUID format',
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
      mockAxiosInstance.delete.mockRejectedValue(httpError);

      await expect(client.unsaveJob('nonexistent')).rejects.toMatchObject({
        detail: 'Сохраненная вакансия не найдена.',
        status: 404,
      });
    });

    it('should use default error message for 409 (already saved)', async () => {
      const httpError = {
        response: {
          status: 409,
          data: { detail: 'Job already saved by this user' },
        },
      };
      mockAxiosInstance.post.mockRejectedValue(httpError);

      await expect(
        client.saveJob({ vacancy_id: 'vacancy-123', user_id: 'user-456' })
      ).rejects.toMatchObject({
        detail: 'Job already saved by this user',
        status: 409,
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

      await expect(
        client.saveJob({ vacancy_id: 'test', user_id: 'test' })
      ).rejects.toMatchObject({
        detail: 'Ошибка сервера. Попробуйте позже.',
        status: 500,
      });
    });

    it('should transform 422 validation errors', async () => {
      const httpError = {
        response: {
          status: 422,
          data: { detail: 'Validation error: user_id is required' },
        },
      };
      mockAxiosInstance.post.mockRejectedValue(httpError);

      await expect(
        client.saveJob({ vacancy_id: 'vacancy-123', user_id: 'invalid' })
      ).rejects.toMatchObject({
        detail: 'Validation error: user_id is required',
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
    it('should export SavedJobsClient class', () => {
      expect(SavedJobsClient).toBeDefined();
      expect(typeof SavedJobsClient).toBe('function');
    });
  });
});
