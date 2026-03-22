/**
 * Tests for Base API Client
 *
 * Tests the Axios-based base API client for core functionality:
 * - Client initialization and configuration
 * - Request/Response interceptors
 * - Error handling and transformation
 * - Generic HTTP methods
 * - Health check endpoints
 * - Job matching endpoint
 *
 * For domain-specific tests, see:
 * - resume.test.ts - Resume upload and analysis
 * - comparisons.test.ts - Resume comparisons
 * - feedback.test.ts - Feedback operations
 * - etc.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ApiClient } from './client';
import axios from 'axios';
import type {
  MatchResponse,
  HealthResponse,
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

describe('ApiClient', () => {
  let apiClient: ApiClient;
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

    // Create API client with mock
    apiClient = new ApiClient({ baseURL: 'http://test.com' });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Constructor', () => {
    it('should create client with default config', () => {
      const client = new ApiClient();
      expect(axios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          baseURL: expect.any(String),
          timeout: 120000,
          headers: {
            'Content-Type': 'application/json',
          },
        })
      );
    });

    it('should create client with custom config', () => {
      const client = new ApiClient({
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

    it('should set up request and response interceptors', () => {
      expect(mockAxiosInstance.interceptors.request.use).toHaveBeenCalled();
      expect(mockAxiosInstance.interceptors.response.use).toHaveBeenCalled();
    });
  });

  describe('compareWithVacancy', () => {
    it('should compare resume with vacancy successfully', async () => {
      const resumeId = 'test-resume-id';
      const vacancy = {
        data: {
          position: 'Java Developer',
          mandatory_requirements: ['Java', 'Spring', 'SQL'],
        },
      };

      const mockResponse: MatchResponse = {
        resume_id: resumeId,
        match_percentage: 75,
        matched_skills: [
          { skill: 'Java', status: 'matched', highlight: 'green' },
          { skill: 'SQL', status: 'matched', highlight: 'green' },
        ],
        missing_skills: [
          { skill: 'Spring', status: 'missing', highlight: 'red' },
        ],
        experience_verification: [],
        overall_assessment: 'Good match',
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await apiClient.compareWithVacancy(resumeId, vacancy);

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/api/matching/compare', {
        resume_id: resumeId,
        vacancy_data: vacancy,
      });
    });

    it('should handle comparison error', async () => {
      const error = {
        response: {
          status: 500,
          data: { detail: 'Internal server error' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        apiClient.compareWithVacancy('test-id', { data: { position: 'Developer' } })
      ).rejects.toEqual({
        detail: 'Internal server error',
        status: 500,
      });
    });
  });

  describe('healthCheck', () => {
    it('should return health status', async () => {
      const mockResponse: HealthResponse = {
        status: 'healthy',
        version: '1.0.0',
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await apiClient.healthCheck();

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/health');
    });

    it('should handle health check error', async () => {
      const error = {
        response: {
          status: 503,
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(apiClient.healthCheck()).rejects.toEqual({
        detail: 'Service unavailable. Please try again later.',
        status: 503,
      });
    });
  });

  describe('readyCheck', () => {
    it('should return ready status', async () => {
      const mockResponse = { status: 'ready' };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await apiClient.readyCheck();

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/ready');
    });
  });

  describe('getAxiosInstance', () => {
    it('should return the underlying Axios instance', () => {
      const instance = apiClient.getAxiosInstance();
      expect(instance).toBe(mockAxiosInstance);
    });
  });

  describe('post (generic method)', () => {
    it('should make generic POST request successfully', async () => {
      const mockData = { foo: 'bar' };
      const mockResponse = { result: 'success' };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await apiClient.post('/test-endpoint', mockData);

      expect(result.data).toEqual(mockResponse);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/test-endpoint',
        mockData
      );
    });

    it('should make POST request without data', async () => {
      const mockResponse = { result: 'success' };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await apiClient.post('/test-endpoint');

      expect(result.data).toEqual(mockResponse);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/test-endpoint',
        undefined
      );
    });

    it('should handle POST request error', async () => {
      const error = {
        response: {
          status: 400,
          data: { detail: 'Bad request' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(apiClient.post('/test-endpoint')).rejects.toEqual({
        detail: 'Bad request',
        status: 400,
      });
    });

    it('should handle POST request network error', async () => {
      const error = {
        code: 'ENOTCONN',
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(apiClient.post('/test-endpoint')).rejects.toEqual({
        detail: 'Network error. Please check your connection and try again.',
        status: 0,
      });
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

      await expect(apiClient.post('/test-endpoint', {})).rejects.toEqual({
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

      await expect(apiClient.post('/test-endpoint', {})).rejects.toEqual({
        detail: 'Unauthorized. Please log in.',
        status: 401,
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

      await expect(apiClient.post('/test-endpoint', {})).rejects.toEqual({
        detail: 'Too many requests. Please try again later.',
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

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(apiClient.post('/test-endpoint', {})).rejects.toEqual({
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

      await expect(apiClient.post('/test-endpoint', {})).rejects.toEqual({
        detail: 'An unexpected error occurred.',
        status: 418,
      });
    });
  });

  describe('Request/Response interceptors', () => {
    it('should add start time metadata to requests', () => {
      // Get the request interceptor handler
      const requestInterceptorCall =
        mockAxiosInstance.interceptors.request.use.mock.calls[0];
      const requestHandler = requestInterceptorCall[0];

      // Call request handler
      const config = { url: '/test' };
      const result = requestHandler(config);

      expect(result).toHaveProperty('metadata');
      expect(result.metadata.startTime).toBeDefined();
    });

    it('should calculate duration in response interceptor', () => {
      // Get the response interceptor handler
      const responseInterceptorCall =
        mockAxiosInstance.interceptors.response.use.mock.calls[0];
      const responseHandler = responseInterceptorCall[0];

      // Call response handler
      const config = { metadata: { startTime: Date.now() - 1000 } };
      const response = { config, status: 200 };
      const result = responseHandler(response);

      expect(result.config.metadata.duration).toBeGreaterThanOrEqual(999);
    });
  });
});
