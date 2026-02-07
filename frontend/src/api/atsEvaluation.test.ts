/**
 * Tests for ATS Evaluation API Client
 *
 * Tests the Axios-based API client for ATS simulation, evaluation, and batch processing.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { AtsEvaluationClient } from './atsEvaluation';
import axios from 'axios';
import type {
  ATSEvaluationRequest,
  ATSEvaluationResponse,
  BatchATSEvaluationRequest,
  BatchATSEvaluationResponse,
  ATSConfigResponse,
  ATSResultListResponse,
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

describe('AtsEvaluationClient', () => {
  let atsClient: AtsEvaluationClient;
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

    // Create ATS client with mock
    atsClient = new AtsEvaluationClient({ baseURL: 'http://test.com' });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Constructor', () => {
    it('should create client with default config', () => {
      const client = new AtsEvaluationClient();
      expect(axios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          baseURL: expect.any(String),
          timeout: 60000,
          headers: {
            'Content-Type': 'application/json',
          },
        })
      );
    });

    it('should create client with custom config', () => {
      const client = new AtsEvaluationClient({
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

  describe('evaluateATS', () => {
    it('should evaluate resume for vacancy successfully', async () => {
      const mockRequest: ATSEvaluationRequest = {
        resume_id: 'resume-123',
        vacancy_id: 'vacancy-456',
        use_llm: true,
      };

      const mockResponse: ATSEvaluationResponse = {
        resume_id: 'resume-123',
        vacancy_id: 'vacancy-456',
        passed: true,
        overall_score: 0.85,
        keyword_score: 0.9,
        experience_score: 0.8,
        education_score: 0.7,
        fit_score: 0.75,
        looks_professional: true,
        disqualified: false,
        visual_issues: [],
        ats_issues: [],
        missing_keywords: [],
        suggestions: ['Strong candidate with relevant experience'],
        feedback: 'Good match',
        provider: 'openai',
        model: 'gpt-4',
        processing_time_ms: 1500,
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await atsClient.evaluateATS(mockRequest);

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/ats/evaluate',
        mockRequest
      );
    });

    it('should evaluate with missing keywords', async () => {
      const mockRequest: ATSEvaluationRequest = {
        resume_id: 'resume-123',
        vacancy_id: 'vacancy-456',
        use_llm: false,
      };

      const mockResponse: ATSEvaluationResponse = {
        resume_id: 'resume-123',
        vacancy_id: 'vacancy-456',
        passed: false,
        overall_score: 0.45,
        keyword_score: 0.5,
        experience_score: 0.4,
        education_score: 0.5,
        fit_score: 0.4,
        looks_professional: true,
        disqualified: false,
        visual_issues: [],
        ats_issues: [],
        missing_keywords: ['Docker', 'Kubernetes', 'AWS'],
        suggestions: ['Consider gaining experience with containerization'],
        feedback: 'Not enough keywords',
        provider: 'openai',
        model: 'gpt-4',
        processing_time_ms: 1200,
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await atsClient.evaluateATS(mockRequest);

      expect(result.passed).toBe(false);
      expect(result.missing_keywords).toEqual(['Docker', 'Kubernetes', 'AWS']);
    });

    it('should handle evaluation error with not found', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Resume not found' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        atsClient.evaluateATS({
          resume_id: 'invalid-id',
          vacancy_id: 'vacancy-456',
        })
      ).rejects.toEqual({
        detail: 'Resume not found',
        status: 404,
      });
    });

    it('should handle evaluation error with validation error', async () => {
      const error = {
        response: {
          status: 422,
          data: { detail: 'Invalid resume ID format' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        atsClient.evaluateATS({
          resume_id: 'invalid-id',
          vacancy_id: 'vacancy-456',
        })
      ).rejects.toEqual({
        detail: 'Invalid resume ID format',
        status: 422,
      });
    });

    it('should handle network error', async () => {
      const error = {
        code: 'ECONNABORTED',
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        atsClient.evaluateATS({
          resume_id: 'resume-123',
          vacancy_id: 'vacancy-456',
        })
      ).rejects.toEqual({
        detail: 'Таймаут запроса. Проверьте соединение и попробуйте снова.',
        status: 408,
      });
    });
  });

  describe('getATSResult', () => {
    it('should get cached ATS result successfully', async () => {
      const mockResponse: ATSEvaluationResponse = {
        resume_id: 'resume-123',
        vacancy_id: 'vacancy-456',
        passed: true,
        overall_score: 0.85,
        keyword_score: 0.9,
        experience_score: 0.8,
        education_score: 0.75,
        fit_score: 0.8,
        looks_professional: true,
        disqualified: false,
        visual_issues: [],
        ats_issues: [],
        missing_keywords: [],
        suggestions: ['Strong candidate'],
        feedback: 'Good match',
        provider: 'openai',
        model: 'gpt-4',
        processing_time_ms: 1000,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await atsClient.getATSResult('resume-123', 'vacancy-456');

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/ats/results/resume-123/vacancy-456'
      );
    });

    it('should handle result not found', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Result not found' },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(
        atsClient.getATSResult('resume-123', 'vacancy-456')
      ).rejects.toEqual({
        detail: 'Result not found',
        status: 404,
      });
    });
  });

  describe('batchEvaluateATS', () => {
    it('should batch evaluate multiple resumes successfully', async () => {
      const mockRequest: BatchATSEvaluationRequest = {
        vacancy_id: 'vacancy-456',
        resume_ids: ['resume-1', 'resume-2', 'resume-3'],
        use_llm: true,
      };

      const mockResponse: BatchATSEvaluationResponse = {
        vacancy_id: 'vacancy-456',
        results: [
          {
            resume_id: 'resume-1',
            passed: true,
            overall_score: 0.85,
            keyword_score: 0.9,
            experience_score: 0.8,
            education_score: 0.75,
            fit_score: 0.8,
            looks_professional: true,
            disqualified: false,
            visual_issues: [],
            ats_issues: [],
            missing_keywords: [],
            suggestions: [],
            feedback: 'Good',
            provider: 'openai',
            model: 'gpt-4',
          },
          {
            resume_id: 'resume-2',
            passed: false,
            overall_score: 0.55,
            keyword_score: 0.6,
            experience_score: 0.5,
            education_score: 0.5,
            fit_score: 0.5,
            looks_professional: true,
            disqualified: false,
            visual_issues: [],
            ats_issues: [],
            missing_keywords: ['Docker'],
            suggestions: [],
            feedback: 'Poor',
            provider: 'openai',
            model: 'gpt-4',
          },
          {
            resume_id: 'resume-3',
            passed: true,
            overall_score: 0.75,
            keyword_score: 0.8,
            experience_score: 0.7,
            education_score: 0.7,
            fit_score: 0.7,
            looks_professional: true,
            disqualified: false,
            visual_issues: [],
            ats_issues: [],
            missing_keywords: [],
            suggestions: [],
            feedback: 'Good',
            provider: 'openai',
            model: 'gpt-4',
          },
        ],
        total_count: 3,
        passed_count: 2,
        processing_time_ms: 5200,
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await atsClient.batchEvaluateATS(mockRequest);

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/ats/batch-evaluate',
        mockRequest
      );
    });

    it('should handle batch evaluation error', async () => {
      const error = {
        response: {
          status: 422,
          data: { detail: 'At least 2 resumes required' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        atsClient.batchEvaluateATS({
          vacancy_id: 'vacancy-456',
          resume_ids: ['resume-1'],
        })
      ).rejects.toEqual({
        detail: 'At least 2 resumes required',
        status: 422,
      });
    });
  });

  describe('getATSConfig', () => {
    it('should get ATS configuration successfully', async () => {
      const mockResponse: ATSConfigResponse = {
        llm_configured: true,
        provider: 'openai',
        model: 'gpt-4',
        threshold: 0.6,
        weights: {
          keyword: 0.4,
          experience: 0.2,
          education: 0.1,
          fit: 0.3,
        },
        visual_check_enabled: true,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await atsClient.getATSConfig();

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/ats/config');
    });

    it('should handle config fetch error', async () => {
      const error = {
        response: {
          status: 503,
          data: { detail: 'Service unavailable' },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(atsClient.getATSConfig()).rejects.toEqual({
        detail: 'Service unavailable',
        status: 503,
      });
    });
  });

  describe('listATSResults', () => {
    it('should list results with default parameters', async () => {
      const mockResponse: ATSResultListResponse = {
        results: [
          {
            id: 'result-1',
            resume_id: 'resume-1',
            vacancy_id: 'vacancy-456',
            passed: true,
            overall_score: 0.85,
            keyword_score: 0.9,
            experience_score: 0.8,
            education_score: 0.75,
            fit_score: 0.8,
            looks_professional: true,
            disqualified: false,
            visual_issues: null,
            ats_issues: null,
            missing_keywords: null,
            suggestions: null,
            feedback: 'Good match',
            provider: 'openai',
            model: 'gpt-4',
            raw_response: null,
            created_at: '2024-01-25T00:00:00Z',
            updated_at: '2024-01-25T00:00:00Z',
          },
        ],
        total_count: 1,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await atsClient.listATSResults();

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/ats/results', {
        params: expect.objectContaining({
          limit: 50,
          offset: 0,
        }),
      });
    });

    it('should list results with filters', async () => {
      const mockResponse: ATSResultListResponse = {
        results: [],
        total_count: 0,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await atsClient.listATSResults(
        'resume-123',
        'vacancy-456',
        true,
        0.7,
        100,
        10
      );

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/ats/results', {
        params: {
          resume_id: 'resume-123',
          vacancy_id: 'vacancy-456',
          passed: true,
          min_score: 0.7,
          limit: 100,
          offset: 10,
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

      await expect(atsClient.listATSResults()).rejects.toEqual({
        detail: 'Database query failed',
        status: 500,
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

      await expect(
        atsClient.evaluateATS({
          resume_id: 'test',
          vacancy_id: 'test',
        })
      ).rejects.toEqual({
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

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        atsClient.evaluateATS({
          resume_id: 'test',
          vacancy_id: 'test',
        })
      ).rejects.toEqual({
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

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        atsClient.evaluateATS({
          resume_id: 'test',
          vacancy_id: 'test',
        })
      ).rejects.toEqual({
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

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        atsClient.evaluateATS({
          resume_id: 'test',
          vacancy_id: 'test',
        })
      ).rejects.toEqual({
        detail: 'Слишком много запросов. Попробуйте позже.',
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

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        atsClient.evaluateATS({
          resume_id: 'test',
          vacancy_id: 'test',
        })
      ).rejects.toEqual({
        detail: 'Ошибка сервера. Попробуйте позже.',
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
        atsClient.evaluateATS({
          resume_id: 'test',
          vacancy_id: 'test',
        })
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
        atsClient.evaluateATS({
          resume_id: 'test',
          vacancy_id: 'test',
        })
      ).rejects.toEqual({
        detail: 'Произошла непредвиденная ошибка.',
        status: 418,
      });
    });

    it('should handle network error without response', async () => {
      const error = {};

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        atsClient.evaluateATS({
          resume_id: 'test',
          vacancy_id: 'test',
        })
      ).rejects.toEqual({
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

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        atsClient.evaluateATS({
          resume_id: 'test',
          vacancy_id: 'test',
        })
      ).rejects.toEqual({
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

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        atsClient.evaluateATS({
          resume_id: 'test',
          vacancy_id: 'test',
        })
      ).rejects.toEqual({
        detail: 'Сервис недоступен. Попробуйте позже.',
        status: 503,
      });
    });
  });
});
