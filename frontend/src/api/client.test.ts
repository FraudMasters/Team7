/**
 * Tests for API Client
 *
 * Tests the Axios-based API client for resume upload, analysis, and job matching.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ApiClient } from './client';
import axios from 'axios';
import type {
  ResumeUploadResponse,
  AnalysisResponse,
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

  describe('uploadResume', () => {
    it('should upload resume file successfully', async () => {
      const mockFile = new File(['test content'], 'resume.pdf', {
        type: 'application/pdf',
      });

      const mockResponse: ResumeUploadResponse = {
        id: 'test-resume-id',
        filename: 'resume.pdf',
        status: 'uploaded',
        message: 'Resume uploaded successfully',
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await apiClient.uploadResume(mockFile);

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/resumes/upload',
        expect.any(FormData),
        expect.objectContaining({
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })
      );
    });

    it('should call progress callback during upload', async () => {
      const mockFile = new File(['test'], 'resume.pdf', {
        type: 'application/pdf',
      });

      const mockResponse: ResumeUploadResponse = {
        id: 'test-id',
        filename: 'resume.pdf',
        status: 'uploaded',
        message: 'Success',
      };

      let progressCallback = vi.fn();
      mockAxiosInstance.post.mockImplementation((url, data, config) => {
        // Simulate progress event
        if (config.onUploadProgress) {
          config.onUploadProgress({ loaded: 50, total: 100 });
        }
        return Promise.resolve({ data: mockResponse });
      });

      await apiClient.uploadResume(mockFile, progressCallback);

      expect(progressCallback).toHaveBeenCalledWith(50);
    });

    it('should handle upload error with invalid file type', async () => {
      const mockFile = new File(['test'], 'resume.txt');
      const error = {
        response: {
          status: 415,
          data: { detail: 'Unsupported file type' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(apiClient.uploadResume(mockFile)).rejects.toEqual({
        detail: 'Unsupported file type',
        status: 415,
      });
    });

    it('should handle upload error with file too large', async () => {
      const mockFile = new File(['test'], 'resume.pdf', {
        type: 'application/pdf',
      });
      const error = {
        response: {
          status: 413,
          data: { detail: 'File size exceeds limit' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(apiClient.uploadResume(mockFile)).rejects.toEqual({
        detail: 'File size exceeds limit',
        status: 413,
      });
    });

    it('should handle network error', async () => {
      const mockFile = new File(['test'], 'resume.pdf', {
        type: 'application/pdf',
      });
      const error = {
        code: 'ECONNABORTED',
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(apiClient.uploadResume(mockFile)).rejects.toEqual({
        detail: 'Request timeout. Please check your connection and try again.',
        status: 408,
      });
    });
  });

  describe('analyzeResume', () => {
    it('should analyze resume successfully', async () => {
      const mockRequest = {
        resume_id: 'test-id',
        extract_experience: true,
        check_grammar: true,
      };

      const mockResponse: AnalysisResponse = {
        resume_id: 'test-id',
        filename: 'resume.pdf',
        processing_time_seconds: 2.5,
        keywords: {
          keywords: ['Java', 'Python', 'SQL'],
          keyphrases: ['machine learning', 'web development'],
          scores: [0.9, 0.8, 0.7],
        },
        entities: {
          organizations: ['Google', 'Microsoft'],
          dates: ['2020-01', '2022-05'],
          technical_skills: ['Java', 'React', 'SQL'],
        },
        grammar: {
          total_errors: 2,
          errors_by_category: { spelling: 1, grammar: 1 },
          errors_by_severity: { warning: 2 },
          errors: [],
        },
        experience: {
          total_experience_months: 48,
          total_experience_summary: '4 years',
          experiences: [],
        },
        language_detected: 'en',
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await apiClient.analyzeResume(mockRequest);

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/resumes/analyze',
        mockRequest
      );
    });

    it('should handle analysis error with not found', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Resume not found' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        apiClient.analyzeResume({ resume_id: 'invalid-id' })
      ).rejects.toEqual({
        detail: 'Resume not found',
        status: 404,
      });
    });

    it('should handle analysis error with validation error', async () => {
      const error = {
        response: {
          status: 422,
          data: { detail: 'Invalid resume ID format' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        apiClient.analyzeResume({ resume_id: 'invalid-id' })
      ).rejects.toEqual({
        detail: 'Invalid resume ID format',
        status: 422,
      });
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

  describe('Error transformation', () => {
    it('should transform 400 error with default message', async () => {
      const error = {
        response: {
          status: 400,
          data: {},
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(apiClient.analyzeResume({ resume_id: 'test' })).rejects.toEqual({
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

      await expect(apiClient.analyzeResume({ resume_id: 'test' })).rejects.toEqual({
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

      await expect(apiClient.analyzeResume({ resume_id: 'test' })).rejects.toEqual({
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

      await expect(apiClient.analyzeResume({ resume_id: 'test' })).rejects.toEqual({
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

      await expect(apiClient.analyzeResume({ resume_id: 'test' })).rejects.toEqual({
        detail: 'An unexpected error occurred.',
        status: 418,
      });
    });
  });

  describe('Request/Response interceptors', () => {
    it('should add start time metadata to requests', async () => {
      const mockRequest = { resume_id: 'test' };
      const mockResponse: AnalysisResponse = {
        resume_id: 'test',
        filename: 'test.pdf',
        processing_time_seconds: 1,
        keywords: { keywords: [], keyphrases: [], scores: [] },
        entities: { organizations: [], dates: [], technical_skills: [] },
        language_detected: 'en',
      };

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

    it('should calculate duration in response interceptor', async () => {
      const mockRequest = { resume_id: 'test' };
      const mockResponse: AnalysisResponse = {
        resume_id: 'test',
        filename: 'test.pdf',
        processing_time_seconds: 1,
        keywords: { keywords: [], keyphrases: [], scores: [] },
        entities: { organizations: [], dates: [], technical_skills: [] },
        language_detected: 'en',
      };

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
