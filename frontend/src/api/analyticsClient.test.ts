/**
 * Tests for Analytics API Client
 *
 * Tests the Axios-based analytics API client for key metrics, funnel metrics,
 * skill demand, source tracking, and recruiter performance.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { AnalyticsClient } from './analyticsClient';
import axios from 'axios';
import type {
  KeyMetricsResponse,
  FunnelMetricsResponse,
  SkillDemandResponse,
  SourceTrackingResponse,
  RecruiterPerformanceResponse,
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
      get: vi.fn(),
    })),
  },
}));

describe('AnalyticsClient', () => {
  let analyticsClient: AnalyticsClient;
  let mockAxiosInstance: any;

  beforeEach(() => {
    // Create mock axios instance
    mockAxiosInstance = {
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
      get: vi.fn(),
    };

    // Mock axios.create to return our mock instance
    vi.mocked(axios.create).mockReturnValue(mockAxiosInstance as any);

    // Create analytics client with mock
    analyticsClient = new AnalyticsClient({ baseURL: 'http://test.com' });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Constructor', () => {
    it('should create client with default config', () => {
      const client = new AnalyticsClient();
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
      const client = new AnalyticsClient({
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

  describe('getKeyMetrics', () => {
    it('should get key metrics successfully', async () => {
      const mockResponse: KeyMetricsResponse = {
        time_to_hire: {
          average_days: 25,
          median_days: 20,
          min_days: 5,
          max_days: 60,
        },
        resumes: {
          total_processed: 1500,
          successful_analyses: 1450,
          failed_analyses: 50,
          success_rate: 96.67,
        },
        match_rates: {
          overall_match_rate: 72.5,
          average_match_score: 68.3,
          high_match_count: 850,
        },
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await analyticsClient.getKeyMetrics();

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/analytics/key-metrics',
        { params: {} }
      );
    });

    it('should get key metrics with date filters', async () => {
      const mockResponse: KeyMetricsResponse = {
        time_to_hire: {
          average_days: 22,
          median_days: 18,
          min_days: 4,
          max_days: 55,
        },
        resumes: {
          total_processed: 500,
          successful_analyses: 485,
          failed_analyses: 15,
          success_rate: 97.0,
        },
        match_rates: {
          overall_match_rate: 75.0,
          average_match_score: 70.5,
          high_match_count: 300,
        },
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await analyticsClient.getKeyMetrics('2024-01-01', '2024-12-31');

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/analytics/key-metrics', {
        params: { start_date: '2024-01-01', end_date: '2024-12-31' },
      });
    });

    it('should handle 404 error', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Analytics data not found' },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(analyticsClient.getKeyMetrics()).rejects.toEqual({
        detail: 'Analytics data not found',
        status: 404,
      });
    });
  });

  describe('getFunnelMetrics', () => {
    it('should get funnel metrics successfully', async () => {
      const mockResponse: FunnelMetricsResponse = {
        stages: [
          {
            stage_name: 'Applied',
            count: 1000,
            conversion_rate: 100.0,
            drop_off_count: 0,
          },
          {
            stage_name: 'Screening',
            count: 700,
            conversion_rate: 70.0,
            drop_off_count: 300,
          },
          {
            stage_name: 'Interview',
            count: 350,
            conversion_rate: 50.0,
            drop_off_count: 350,
          },
          {
            stage_name: 'Offer',
            count: 175,
            conversion_rate: 50.0,
            drop_off_count: 175,
          },
          {
            stage_name: 'Hired',
            count: 150,
            conversion_rate: 85.7,
            drop_off_count: 25,
          },
        ],
        overall_hire_rate: 15.0,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await analyticsClient.getFunnelMetrics();

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/analytics/funnel',
        { params: {} }
      );
    });

    it('should get funnel metrics with date filters', async () => {
      const mockResponse: FunnelMetricsResponse = {
        stages: [
          {
            stage_name: 'Applied',
            count: 500,
            conversion_rate: 100.0,
            drop_off_count: 0,
          },
        ],
        overall_hire_rate: 12.0,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await analyticsClient.getFunnelMetrics('2024-06-01', '2024-12-31');

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/analytics/funnel', {
        params: { start_date: '2024-06-01', end_date: '2024-12-31' },
      });
    });

    it('should handle 500 error', async () => {
      const error = {
        response: {
          status: 500,
          data: {},
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(analyticsClient.getFunnelMetrics()).rejects.toEqual({
        detail: 'Ошибка сервера. Попробуйте позже.',
        status: 500,
      });
    });
  });

  describe('getSkillDemand', () => {
    it('should get skill demand successfully', async () => {
      const mockResponse: SkillDemandResponse = {
        total_postings_analyzed: 5000,
        skills: [
          {
            skill_name: 'JavaScript',
            demand_count: 2500,
            trend_percentage: 15.5,
            rank: 1,
          },
          {
            skill_name: 'Python',
            demand_count: 2000,
            trend_percentage: 12.3,
            rank: 2,
          },
          {
            skill_name: 'React',
            demand_count: 1800,
            trend_percentage: 10.8,
            rank: 3,
          },
        ],
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await analyticsClient.getSkillDemand();

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/analytics/skill-demand',
        { params: {} }
      );
    });

    it('should get skill demand with filters', async () => {
      const mockResponse: SkillDemandResponse = {
        total_postings_analyzed: 2000,
        skills: [
          {
            skill_name: 'TypeScript',
            demand_count: 800,
            trend_percentage: 20.0,
            rank: 1,
          },
        ],
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await analyticsClient.getSkillDemand('2024-01-01', '2024-12-31', 30);

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/analytics/skill-demand', {
        params: { start_date: '2024-01-01', end_date: '2024-12-31', limit: 30 },
      });
    });

    it('should handle 400 error', async () => {
      const error = {
        response: {
          status: 400,
          data: { detail: 'Invalid date range' },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(
        analyticsClient.getSkillDemand('invalid-date', '2024-12-31')
      ).rejects.toEqual({
        detail: 'Invalid date range',
        status: 400,
      });
    });
  });

  describe('getSourceTracking', () => {
    it('should get source tracking successfully', async () => {
      const mockResponse: SourceTrackingResponse = {
        total_vacancies: 500,
        sources: [
          {
            source_name: 'LinkedIn',
            vacancy_count: 200,
            percentage: 40.0,
            average_time_to_fill: 25,
          },
          {
            source_name: 'Indeed',
            vacancy_count: 150,
            percentage: 30.0,
            average_time_to_fill: 30,
          },
          {
            source_name: 'Referral',
            vacancy_count: 100,
            percentage: 20.0,
            average_time_to_fill: 15,
          },
          {
            source_name: 'Career Site',
            vacancy_count: 50,
            percentage: 10.0,
            average_time_to_fill: 35,
          },
        ],
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await analyticsClient.getSourceTracking();

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/analytics/source-tracking',
        { params: {} }
      );
    });

    it('should get source tracking with date filters', async () => {
      const mockResponse: SourceTrackingResponse = {
        total_vacancies: 200,
        sources: [
          {
            source_name: 'LinkedIn',
            vacancy_count: 80,
            percentage: 40.0,
            average_time_to_fill: 22,
          },
        ],
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await analyticsClient.getSourceTracking('2024-01-01', '2024-06-30');

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/analytics/source-tracking', {
        params: { start_date: '2024-01-01', end_date: '2024-06-30' },
      });
    });

    it('should handle network error', async () => {
      const error = {
        code: 'ECONNABORTED',
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(analyticsClient.getSourceTracking()).rejects.toEqual({
        detail: 'Таймаут запроса. Проверьте соединение и попробуйте снова.',
        status: 408,
      });
    });
  });

  describe('getRecruiterPerformance', () => {
    it('should get recruiter performance successfully', async () => {
      const mockResponse: RecruiterPerformanceResponse = {
        period_start_date: '2024-01-01',
        period_end_date: '2024-12-31',
        recruiters: [
          {
            recruiter_id: 'recruiter-1',
            recruiter_name: 'Alice Johnson',
            hires: 45,
            interviews_conducted: 120,
            average_time_to_hire: 22,
            offer_acceptance_rate: 85.5,
          },
          {
            recruiter_id: 'recruiter-2',
            recruiter_name: 'Bob Smith',
            hires: 38,
            interviews_conducted: 100,
            average_time_to_hire: 25,
            offer_acceptance_rate: 82.0,
          },
          {
            recruiter_id: 'recruiter-3',
            recruiter_name: 'Carol White',
            hires: 32,
            interviews_conducted: 90,
            average_time_to_hire: 28,
            offer_acceptance_rate: 78.5,
          },
        ],
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await analyticsClient.getRecruiterPerformance();

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/analytics/recruiter-performance',
        { params: {} }
      );
    });

    it('should get recruiter performance with filters', async () => {
      const mockResponse: RecruiterPerformanceResponse = {
        period_start_date: '2024-06-01',
        period_end_date: '2024-12-31',
        recruiters: [
          {
            recruiter_id: 'recruiter-1',
            recruiter_name: 'Alice Johnson',
            hires: 25,
            interviews_conducted: 60,
            average_time_to_hire: 20,
            offer_acceptance_rate: 88.0,
          },
        ],
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await analyticsClient.getRecruiterPerformance(
        '2024-06-01',
        '2024-12-31',
        10
      );

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/analytics/recruiter-performance',
        { params: { start_date: '2024-06-01', end_date: '2024-12-31', limit: 10 } }
      );
    });

    it('should handle 403 error', async () => {
      const error = {
        response: {
          status: 403,
          data: {},
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(analyticsClient.getRecruiterPerformance()).rejects.toEqual({
        detail: 'Доступ запрещен. У вас нет прав для выполнения этого действия.',
        status: 403,
      });
    });
  });

  describe('getAxiosInstance', () => {
    it('should return the underlying Axios instance', () => {
      const instance = analyticsClient.getAxiosInstance();
      expect(instance).toBe(mockAxiosInstance);
    });
  });

  describe('Error transformation', () => {
    it('should transform 401 error with default message', async () => {
      const error = {
        response: {
          status: 401,
          data: {},
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(analyticsClient.getKeyMetrics()).rejects.toEqual({
        detail: 'Не авторизован. Войдите в систему.',
        status: 401,
      });
    });

    it('should transform 429 error with default message', async () => {
      const error = {
        response: {
          status: 429,
          data: {},
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(analyticsClient.getFunnelMetrics()).rejects.toEqual({
        detail: 'Слишком много запросов. Попробуйте позже.',
        status: 429,
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

      await expect(analyticsClient.getSkillDemand()).rejects.toEqual({
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

      await expect(analyticsClient.getSourceTracking()).rejects.toEqual({
        detail: 'Сервис недоступен. Попробуйте позже.',
        status: 503,
      });
    });

    it('should use server error message when available', async () => {
      const customMessage = 'Custom analytics error from server';
      const error = {
        response: {
          status: 500,
          data: { detail: customMessage },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(analyticsClient.getRecruiterPerformance()).rejects.toEqual({
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

      await expect(analyticsClient.getKeyMetrics()).rejects.toEqual({
        detail: 'Произошла непредвиденная ошибка.',
        status: 418,
      });
    });

    it('should handle network error without response', async () => {
      const error = {
        code: 'NETWORK_ERROR',
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(analyticsClient.getKeyMetrics()).rejects.toEqual({
        detail: 'Ошибка сети. Проверьте соединение и попробуйте снова.',
        status: 0,
      });
    });
  });

  describe('Response interceptor', () => {
    it('should set up response error handler', async () => {
      // Get the response interceptor error handler
      const responseInterceptorCall =
        mockAxiosInstance.interceptors.response.use.mock.calls[0];
      const errorHandler = responseInterceptorCall[1];

      // Call error handler with an error
      const error = {
        response: {
          status: 404,
          data: { detail: 'Not found' },
        },
      };

      const result = errorHandler(error);

      // Should reject with transformed error
      await expect(result).rejects.toEqual({
        detail: 'Not found',
        status: 404,
      });
    });
  });
});
