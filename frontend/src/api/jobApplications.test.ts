/**
 * Tests for Job Applications API Client
 *
 * Tests the Axios-based API client for job application functionality.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { JobApplicationsClient } from './jobApplications';
import axios from 'axios';
import type {
  JobApplicationSubmitRequest,
  JobApplicationResponse,
  JobApplicationsListResponse,
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

describe('JobApplicationsClient', () => {
  let client: JobApplicationsClient;
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
    client = new JobApplicationsClient({ baseURL: 'http://test.com' });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Constructor', () => {
    it('should create client with default config', () => {
      const testClient = new JobApplicationsClient();
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
      const testClient = new JobApplicationsClient({
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

  describe('submitApplication', () => {
    const mockApplicationResponse: JobApplicationResponse = {
      id: 'app-123',
      vacancy_id: 'vacancy-456',
      vacancy_title: 'Senior Python Developer',
      resume_id: 'resume-789',
      email: 'candidate@example.com',
      phone: '+1234567890',
      cover_letter: 'I am interested in this position',
      status: 'submitted',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    it('should submit application with all fields', async () => {
      const request: JobApplicationSubmitRequest = {
        vacancy_id: 'vacancy-456',
        resume_id: 'resume-789',
        email: 'candidate@example.com',
        phone: '+1234567890',
        cover_letter: 'I am interested in this position',
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockApplicationResponse });

      const result = await client.submitApplication(request);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/job-applications/submit',
        request
      );
      expect(result).toEqual(mockApplicationResponse);
    });

    it('should submit application without resume', async () => {
      const request: JobApplicationSubmitRequest = {
        vacancy_id: 'vacancy-456',
        email: 'guest@example.com',
        phone: '+9876543210',
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockApplicationResponse });

      const result = await client.submitApplication(request);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/job-applications/submit',
        request
      );
      expect(result).toEqual(mockApplicationResponse);
    });

    it('should submit application with only required fields', async () => {
      const request: JobApplicationSubmitRequest = {
        vacancy_id: 'vacancy-456',
        email: 'minimal@example.com',
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockApplicationResponse });

      const result = await client.submitApplication(request);

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/job-applications/submit',
        request
      );
      expect(result).toEqual(mockApplicationResponse);
    });
  });

  describe('getMyApplications', () => {
    const mockApplication: JobApplicationResponse = {
      id: 'app-123',
      vacancy_id: 'vacancy-456',
      vacancy_title: 'Senior Python Developer',
      resume_id: 'resume-789',
      email: 'candidate@example.com',
      phone: '+1234567890',
      cover_letter: 'I am interested',
      status: 'submitted',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    const mockListResponse: JobApplicationsListResponse = {
      applications: [mockApplication],
      total: 1,
      limit: 10,
      skip: 0,
    };

    it('should get applications with default pagination', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: mockListResponse });

      const result = await client.getMyApplications();

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/job-applications/my-applications', {
        params: { skip: 0, limit: 10 },
      });
      expect(result).toEqual(mockListResponse);
    });

    it('should get applications with custom pagination', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: mockListResponse });

      const result = await client.getMyApplications(20, 50);

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/job-applications/my-applications', {
        params: { skip: 20, limit: 50 },
      });
      expect(result).toEqual(mockListResponse);
    });

    it('should get applications with status filter', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: mockListResponse });

      const result = await client.getMyApplications(0, 10, 'under_review');

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/job-applications/my-applications', {
        params: { skip: 0, limit: 10, status_filter: 'under_review' },
      });
      expect(result).toEqual(mockListResponse);
    });

    it('should get applications with all parameters', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: mockListResponse });

      const result = await client.getMyApplications(10, 25, 'accepted');

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/job-applications/my-applications', {
        params: { skip: 10, limit: 25, status_filter: 'accepted' },
      });
      expect(result).toEqual(mockListResponse);
    });
  });

  describe('getApplication', () => {
    const mockApplication: JobApplicationResponse = {
      id: 'app-123',
      vacancy_id: 'vacancy-456',
      vacancy_title: 'Senior Python Developer',
      resume_id: 'resume-789',
      email: 'candidate@example.com',
      phone: '+1234567890',
      cover_letter: 'I am interested',
      status: 'submitted',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    it('should get application by ID', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: mockApplication });

      const result = await client.getApplication('app-123');

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/job-applications/app-123');
      expect(result).toEqual(mockApplication);
    });

    it('should get application with UUID format ID', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: mockApplication });

      const result = await client.getApplication('550e8400-e29b-41d4-a716-446655440000');

      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/job-applications/550e8400-e29b-41d4-a716-446655440000'
      );
      expect(result).toEqual(mockApplication);
    });
  });

  describe('Error Handling', () => {
    it('should transform network timeout errors', async () => {
      const networkError = new Error('Network Error');
      (networkError as any).code = 'ECONNABORTED';
      mockAxiosInstance.post.mockRejectedValue(networkError);

      await expect(
        client.submitApplication({ vacancy_id: 'test', email: 'test@example.com' })
      ).rejects.toMatchObject({
        detail: 'Таймаут запроса. Проверьте соединение и попробуйте снова.',
        status: 408,
      });
    });

    it('should transform general network errors', async () => {
      const networkError = new Error('Network Error');
      mockAxiosInstance.post.mockRejectedValue(networkError);

      await expect(
        client.submitApplication({ vacancy_id: 'test', email: 'test@example.com' })
      ).rejects.toMatchObject({
        detail: 'Ошибка сети. Проверьте соединение и попробуйте снова.',
        status: 0,
      });
    });

    it('should transform HTTP errors with server detail', async () => {
      const httpError = {
        response: {
          status: 400,
          data: { detail: 'Invalid application data' },
        },
      };
      mockAxiosInstance.post.mockRejectedValue(httpError);

      await expect(
        client.submitApplication({ vacancy_id: 'test', email: 'test@example.com' })
      ).rejects.toMatchObject({
        detail: 'Invalid application data',
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

      await expect(client.getApplication('nonexistent')).rejects.toMatchObject({
        detail: 'Заявка не найдена.',
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

      await expect(
        client.submitApplication({ vacancy_id: 'test', email: 'test@example.com' })
      ).rejects.toMatchObject({
        detail: 'Ошибка сервера. Попробуйте позже.',
        status: 500,
      });
    });

    it('should transform 401 unauthorized errors', async () => {
      const httpError = {
        response: {
          status: 401,
          data: { detail: 'Authentication required' },
        },
      };
      mockAxiosInstance.get.mockRejectedValue(httpError);

      await expect(client.getMyApplications()).rejects.toMatchObject({
        detail: 'Authentication required',
        status: 401,
      });
    });

    it('should transform 403 forbidden errors', async () => {
      const httpError = {
        response: {
          status: 403,
          data: { detail: 'You do not have permission to view this application' },
        },
      };
      mockAxiosInstance.get.mockRejectedValue(httpError);

      await expect(client.getApplication('app-123')).rejects.toMatchObject({
        detail: 'You do not have permission to view this application',
        status: 403,
      });
    });

    it('should handle "already applied" error', async () => {
      const httpError = {
        response: {
          status: 400,
          data: { detail: 'You have already applied for this vacancy' },
        },
      };
      mockAxiosInstance.post.mockRejectedValue(httpError);

      await expect(
        client.submitApplication({ vacancy_id: 'vacancy-123', email: 'test@example.com' })
      ).rejects.toMatchObject({
        detail: 'You have already applied for this vacancy',
        status: 400,
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
    it('should export JobApplicationsClient class', () => {
      expect(JobApplicationsClient).toBeDefined();
      expect(typeof JobApplicationsClient).toBe('function');
    });
  });
});
