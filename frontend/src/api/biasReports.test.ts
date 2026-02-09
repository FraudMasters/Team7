/**
 * Tests for Bias Reports API Client
 *
 * Tests the Axios-based bias reports API client for report operations,
 * including listing, retrieving, generating, and exporting bias reports.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { BiasReportsClient } from './biasReports';
import axios from 'axios';
import type {
  BiasReport,
  BiasReportListResponse,
  FairnessScorecard,
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
      post: vi.fn(),
    })),
  },
}));

describe('BiasReportsClient', () => {
  let biasReportsClient: BiasReportsClient;
  let mockAxiosInstance: any;

  beforeEach(() => {
    // Create mock axios instance
    mockAxiosInstance = {
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
      get: vi.fn(),
      post: vi.fn(),
    };

    // Mock axios.create to return our mock instance
    vi.mocked(axios.create).mockReturnValue(mockAxiosInstance as any);

    // Create bias reports client with mock
    biasReportsClient = new BiasReportsClient({ baseURL: 'http://test.com' });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Constructor', () => {
    it('should create client with default config', () => {
      const client = new BiasReportsClient();
      expect(axios.create).toHaveBeenCalledWith(
        expect.objectContaining({
          baseURL: expect.any(String),
          timeout: 120000,
        })
      );
    });

    it('should create client with custom config', () => {
      const client = new BiasReportsClient({
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
  });

  describe('getReports', () => {
    it('should get reports successfully', async () => {
      const mockResponse: BiasReportListResponse = {
        reports: [
          {
            report_id: '2024-01-25_v1.0',
            model_name: 'ranking',
            model_version: 'v1.0',
            report_type: 'system-wide',
            protected_attributes: ['gender', 'age'],
            overall_fairness_score: 85.5,
            bias_detected: false,
            severity_level: null,
            findings: [],
            recommendations: [],
            generated_at: '2024-01-25T10:00:00Z',
          },
        ],
        total_count: 1,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await biasReportsClient.getReports();

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/fairness/reports');
    });

    it('should get reports with filters', async () => {
      const mockResponse: BiasReportListResponse = {
        reports: [
          {
            report_id: '2024-01-25_v1.0',
            model_name: 'ranking',
            model_version: 'v1.0',
            report_type: 'individual',
            protected_attributes: ['gender'],
            overall_fairness_score: 65.0,
            bias_detected: true,
            severity_level: 'high',
            findings: [
              {
                demographic_group: 'female',
                disparate_impact_ratio: 0.65,
                statistical_parity_difference: 0.25,
                severity: 'high',
              },
            ],
            recommendations: ['Consider retraining the model'],
            generated_at: '2024-01-25T10:00:00Z',
          },
        ],
        total_count: 1,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await biasReportsClient.getReports({
        model_name: 'ranking',
        severity_level: 'high',
        bias_detected: true,
        limit: 20,
      });

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/fairness/reports?model_name=ranking&severity_level=high&bias_detected=true&limit=20');
    });

    it('should handle 404 error', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Reports not found' },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(biasReportsClient.getReports()).rejects.toEqual({
        detail: 'Reports not found',
        status: 404,
      });
    });
  });

  describe('getReport', () => {
    it('should get a specific report by ID', async () => {
      const mockReport: BiasReport = {
        report_id: '2024-01-25_v1.0',
        model_name: 'ranking',
        model_version: 'v1.0',
        report_type: 'system-wide',
        protected_attributes: ['gender', 'age'],
        overall_fairness_score: 85.5,
        bias_detected: false,
        severity_level: null,
        findings: [],
        recommendations: [],
        generated_at: '2024-01-25T10:00:00Z',
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockReport });

      const result = await biasReportsClient.getReport('2024-01-25_v1.0');

      expect(result).toEqual(mockReport);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/fairness/reports/2024-01-25_v1.0');
    });

    it('should handle 404 error for non-existent report', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Report not found' },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(biasReportsClient.getReport('invalid-id')).rejects.toEqual({
        detail: 'Report not found',
        status: 404,
      });
    });
  });

  describe('generateReport', () => {
    it('should generate a new report', async () => {
      const mockReport: BiasReport = {
        report_id: '2024-01-25_v1.0',
        model_name: 'ranking',
        model_version: 'v1.0',
        report_type: 'system-wide',
        protected_attributes: ['gender', 'age'],
        overall_fairness_score: 85.5,
        bias_detected: false,
        severity_level: null,
        findings: [],
        recommendations: [],
        generated_at: '2024-01-25T10:00:00Z',
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockReport });

      const result = await biasReportsClient.generateReport({
        model_name: 'ranking',
        report_type: 'system-wide',
      });

      expect(result).toEqual(mockReport);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/fairness/reports/generate?model_name=ranking&report_type=system-wide'
      );
    });

    it('should generate report with all options', async () => {
      const mockReport: BiasReport = {
        report_id: '2024-01-25_v1.0.0',
        model_name: 'ranking',
        model_version: 'v1.0.0',
        report_type: 'individual',
        protected_attributes: ['gender'],
        overall_fairness_score: 75.0,
        bias_detected: true,
        severity_level: 'medium',
        findings: [],
        recommendations: [],
        generated_at: '2024-01-25T10:00:00Z',
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockReport });

      const result = await biasReportsClient.generateReport({
        model_name: 'ranking',
        model_version: 'v1.0.0',
        report_type: 'individual',
      });

      expect(result).toEqual(mockReport);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/fairness/reports/generate?model_name=ranking&model_version=v1.0.0&report_type=individual'
      );
    });

    it('should handle 422 error for invalid request', async () => {
      const error = {
        response: {
          status: 422,
          data: { detail: 'Invalid model name' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        biasReportsClient.generateReport({ model_name: '' })
      ).rejects.toEqual({
        detail: 'Invalid model name',
        status: 422,
      });
    });
  });

  describe('getScorecard', () => {
    it('should get fairness scorecard', async () => {
      const mockScorecard: FairnessScorecard = {
        vacancy_id: 'vacancy-123',
        vacancy_title: 'Software Engineer',
        fairness_score: 85,
        score_breakdown: {
          disparate_impact_score: 45,
          statistical_parity_score: 25,
          alert_penalty: 0,
          final_score: 85,
        },
        metrics_by_demographic: [],
        bias_sources: [],
        alerts_summary: {
          critical: 0,
          high: 0,
          medium: 0,
          low: 0,
          total: 0,
        },
        recommendations: [],
        analyzed_at: '2024-01-25T10:00:00Z',
        total_sample_size: 100,
        demographics_analyzed: ['gender', 'age'],
        model_version: 'v1.0',
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockScorecard });

      const result = await biasReportsClient.getScorecard({
        vacancy_id: 'vacancy-123',
      });

      expect(result).toEqual(mockScorecard);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/fairness/scorecard?vacancy_id=vacancy-123');
    });

    it('should get scorecard without filters', async () => {
      const mockScorecard: FairnessScorecard = {
        fairness_score: 90,
        score_breakdown: {
          disparate_impact_score: 48,
          statistical_parity_score: 27,
          alert_penalty: 0,
          final_score: 90,
        },
        metrics_by_demographic: [],
        bias_sources: [],
        alerts_summary: {
          critical: 0,
          high: 0,
          medium: 0,
          low: 0,
          total: 0,
        },
        recommendations: [],
        analyzed_at: '2024-01-25T10:00:00Z',
        total_sample_size: 200,
        demographics_analyzed: ['gender'],
        model_version: 'v1.0',
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockScorecard });

      const result = await biasReportsClient.getScorecard();

      expect(result).toEqual(mockScorecard);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/fairness/scorecard');
    });
  });

  describe('exportReport', () => {
    it('should export report as PDF', async () => {
      const mockBlob = new Blob(['PDF content'], { type: 'application/pdf' });

      mockAxiosInstance.post.mockResolvedValue({ data: mockBlob });

      const result = await biasReportsClient.exportReport('2024-01-25_v1.0', 'pdf');

      expect(result).toEqual(mockBlob);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/fairness/reports/2024-01-25_v1.0/export?format=pdf',
        undefined,
        { responseType: 'blob' }
      );
    });

    it('should export report as CSV', async () => {
      const mockBlob = new Blob(['CSV content'], { type: 'text/csv' });

      mockAxiosInstance.post.mockResolvedValue({ data: mockBlob });

      const result = await biasReportsClient.exportReport('2024-01-25_v1.0', 'csv');

      expect(result).toEqual(mockBlob);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/fairness/reports/2024-01-25_v1.0/export?format=csv',
        undefined,
        { responseType: 'blob' }
      );
    });

    it('should default to PDF format', async () => {
      const mockBlob = new Blob(['PDF content'], { type: 'application/pdf' });

      mockAxiosInstance.post.mockResolvedValue({ data: mockBlob });

      const result = await biasReportsClient.exportReport('2024-01-25_v1.0');

      expect(result).toEqual(mockBlob);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/fairness/reports/2024-01-25_v1.0/export?format=pdf',
        undefined,
        { responseType: 'blob' }
      );
    });

    it('should handle 404 error for non-existent report', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Report not found' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        biasReportsClient.exportReport('invalid-id', 'pdf')
      ).rejects.toEqual({
        detail: 'Report not found',
        status: 404,
      });
    });
  });

  describe('getModelReports', () => {
    it('should get reports for a specific model', async () => {
      const mockResponse: BiasReportListResponse = {
        reports: [
          {
            report_id: '2024-01-25_v1.0',
            model_name: 'ranking',
            model_version: 'v1.0',
            report_type: 'system-wide',
            protected_attributes: ['gender'],
            overall_fairness_score: 80.0,
            bias_detected: false,
            severity_level: null,
            findings: [],
            recommendations: [],
            generated_at: '2024-01-25T10:00:00Z',
          },
        ],
        total_count: 1,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await biasReportsClient.getModelReports('ranking', {
        severity_level: 'high',
      });

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/fairness/reports?model_name=ranking&severity_level=high'
      );
    });
  });

  describe('getCriticalReports', () => {
    it('should get critical severity reports', async () => {
      const mockResponse: BiasReportListResponse = {
        reports: [
          {
            report_id: '2024-01-25_v1.0',
            model_name: 'ranking',
            model_version: 'v1.0',
            report_type: 'system-wide',
            protected_attributes: ['gender'],
            overall_fairness_score: 45.0,
            bias_detected: true,
            severity_level: 'critical',
            findings: [],
            recommendations: [],
            generated_at: '2024-01-25T10:00:00Z',
          },
        ],
        total_count: 1,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await biasReportsClient.getCriticalReports();

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/fairness/reports?severity_level=critical&bias_detected=true&limit=100'
      );
    });
  });

  describe('getRecentReports', () => {
    it('should get recent reports with default limit', async () => {
      const mockResponse: BiasReportListResponse = {
        reports: [],
        total_count: 0,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await biasReportsClient.getRecentReports();

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/fairness/reports?limit=20');
    });

    it('should get recent reports with custom limit', async () => {
      const mockResponse: BiasReportListResponse = {
        reports: [],
        total_count: 0,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await biasReportsClient.getRecentReports({ limit: 50 });

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/fairness/reports?limit=50');
    });
  });

  describe('getAxiosInstance', () => {
    it('should return the underlying Axios instance', () => {
      const instance = biasReportsClient.getAxiosInstance();
      expect(instance).toBe(mockAxiosInstance);
    });
  });

  describe('Error transformation', () => {
    it('should transform 401 error', async () => {
      const error = {
        response: {
          status: 401,
          data: {},
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(biasReportsClient.getReports()).rejects.toEqual({
        detail: 'Unknown error',
        status: 401,
      });
    });

    it('should use server error message when available', async () => {
      const customMessage = 'Custom bias reports error from server';
      const error = {
        response: {
          status: 500,
          data: { detail: customMessage },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(biasReportsClient.getReports()).rejects.toEqual({
        detail: customMessage,
        status: 500,
      });
    });

    it('should handle network error without response', async () => {
      const error = {
        message: 'Network Error',
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(biasReportsClient.getReports()).rejects.toEqual({
        detail: 'Network Error',
        status: undefined,
      });
    });
  });
});
