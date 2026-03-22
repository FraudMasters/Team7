/**
 * Tests for Comparisons API Client
 *
 * Tests the ComparisonsClient for creating, listing, getting, updating, deleting comparisons,
 * and comparing multiple resumes.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ComparisonsClient } from './comparisons';
import axios from 'axios';
import type {
  ComparisonCreate,
  ComparisonUpdate,
  ComparisonResponse,
  ComparisonListResponse,
  CompareMultipleRequest,
  ComparisonMatrixData,
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

describe('ComparisonsClient', () => {
  let comparisonsClient: ComparisonsClient;
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

    // Create comparisons client with mock
    comparisonsClient = new ComparisonsClient({ baseURL: 'http://test.com' });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Constructor', () => {
    it('should create client with default config', () => {
      const client = new ComparisonsClient();
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
      const client = new ComparisonsClient({
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

  describe('createComparison', () => {
    it('should create comparison successfully', async () => {
      const mockRequest: ComparisonCreate = {
        vacancy_id: 'vacancy-123',
        resume_ids: ['resume-1', 'resume-2', 'resume-3'],
        name: 'Top Candidates for Senior Developer',
      };

      const mockResponse: ComparisonResponse = {
        id: 'comparison-123',
        vacancy_id: 'vacancy-123',
        resume_ids: ['resume-1', 'resume-2', 'resume-3'],
        name: 'Top Candidates for Senior Developer',
        created_by: 'user-456',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await comparisonsClient.createComparison(mockRequest);

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/comparisons/',
        mockRequest
      );
    });

    it('should create comparison with optional filters', async () => {
      const mockRequest: ComparisonCreate = {
        vacancy_id: 'vacancy-123',
        resume_ids: ['resume-1', 'resume-2'],
        name: 'Filtered Comparison',
        filters: { min_experience: 5 },
      };

      const mockResponse: ComparisonResponse = {
        id: 'comparison-123',
        vacancy_id: 'vacancy-123',
        resume_ids: ['resume-1', 'resume-2'],
        name: 'Filtered Comparison',
        filters: { min_experience: 5 },
        created_by: 'user-456',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await comparisonsClient.createComparison(mockRequest);

      expect(result.filters).toEqual({ min_experience: 5 });
    });

    it('should handle validation error', async () => {
      const mockRequest: ComparisonCreate = {
        vacancy_id: '',
        resume_ids: [],
        name: '',
      };

      const error = {
        response: {
          status: 422,
          data: { detail: 'Vacancy ID and at least one resume ID are required' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(comparisonsClient.createComparison(mockRequest)).rejects.toEqual({
        detail: 'Vacancy ID and at least one resume ID are required',
        status: 422,
      });
    });

    it('should handle network error during creation', async () => {
      const mockRequest: ComparisonCreate = {
        vacancy_id: 'vacancy-123',
        resume_ids: ['resume-1'],
        name: 'Test',
      };

      const error = {
        code: 'ECONNABORTED',
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(comparisonsClient.createComparison(mockRequest)).rejects.toEqual({
        detail: 'Таймаут запроса. Проверьте соединение и попробуйте снова.',
        status: 408,
      });
    });
  });

  describe('listComparisons', () => {
    it('should list all comparisons successfully', async () => {
      const mockResponse: ComparisonListResponse = {
        comparisons: [
          {
            id: 'comparison-1',
            vacancy_id: 'vacancy-123',
            resume_ids: ['resume-1', 'resume-2'],
            name: 'Comparison 1',
            created_by: 'user-456',
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
          {
            id: 'comparison-2',
            vacancy_id: 'vacancy-456',
            resume_ids: ['resume-3', 'resume-4'],
            name: 'Comparison 2',
            created_by: 'user-789',
            created_at: '2024-01-02T00:00:00Z',
            updated_at: '2024-01-02T00:00:00Z',
          },
        ],
        total_count: 2,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await comparisonsClient.listComparisons();

      expect(result).toEqual(mockResponse);
      expect(result.comparisons).toHaveLength(2);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/comparisons/', {
        params: {},
      });
    });

    it('should filter comparisons by vacancy_id', async () => {
      const mockResponse: ComparisonListResponse = {
        comparisons: [
          {
            id: 'comparison-1',
            vacancy_id: 'vacancy-123',
            resume_ids: ['resume-1', 'resume-2'],
            name: 'Comparison 1',
            created_by: 'user-456',
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
        ],
        total_count: 1,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await comparisonsClient.listComparisons('vacancy-123');

      expect(result.comparisons).toHaveLength(1);
      expect(result.comparisons[0].vacancy_id).toBe('vacancy-123');
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/comparisons/', {
        params: { vacancy_id: 'vacancy-123' },
      });
    });

    it('should filter by match percentage range', async () => {
      const mockResponse: ComparisonListResponse = {
        comparisons: [],
        total_count: 0,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      await comparisonsClient.listComparisons(
        undefined,
        undefined,
        80,
        100
      );

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/comparisons/', {
        params: {
          min_match_percentage: 80,
          max_match_percentage: 100,
        },
      });
    });

    it('should apply sorting and pagination', async () => {
      const mockResponse: ComparisonListResponse = {
        comparisons: [],
        total_count: 0,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      await comparisonsClient.listComparisons(
        undefined,
        undefined,
        undefined,
        undefined,
        'match_percentage',
        'desc',
        10,
        20
      );

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/comparisons/', {
        params: {
          sort_by: 'match_percentage',
          order: 'desc',
          limit: 10,
          offset: 20,
        },
      });
    });

    it('should apply all filters together', async () => {
      const mockResponse: ComparisonListResponse = {
        comparisons: [],
        total_count: 0,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      await comparisonsClient.listComparisons(
        'vacancy-123',
        'user-456',
        75,
        95,
        'created_at',
        'asc',
        5,
        0
      );

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/comparisons/', {
        params: {
          vacancy_id: 'vacancy-123',
          created_by: 'user-456',
          min_match_percentage: 75,
          max_match_percentage: 95,
          sort_by: 'created_at',
          order: 'asc',
          limit: 5,
          offset: 0,
        },
      });
    });

    it('should handle empty list', async () => {
      const mockResponse: ComparisonListResponse = {
        comparisons: [],
        total_count: 0,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await comparisonsClient.listComparisons();

      expect(result.comparisons).toHaveLength(0);
      expect(result.total_count).toBe(0);
    });

    it('should handle server error', async () => {
      const error = {
        response: {
          status: 500,
          data: { detail: 'Internal server error' },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(comparisonsClient.listComparisons()).rejects.toEqual({
        detail: 'Internal server error',
        status: 500,
      });
    });
  });

  describe('getComparison', () => {
    it('should get comparison by id successfully', async () => {
      const mockResponse: ComparisonResponse = {
        id: 'comparison-123',
        vacancy_id: 'vacancy-123',
        resume_ids: ['resume-1', 'resume-2', 'resume-3'],
        name: 'Top Candidates',
        created_by: 'user-456',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await comparisonsClient.getComparison('comparison-123');

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/comparisons/comparison-123'
      );
    });

    it('should handle comparison not found', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Comparison not found' },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(
        comparisonsClient.getComparison('nonexistent')
      ).rejects.toEqual({
        detail: 'Comparison not found',
        status: 404,
      });
    });

    it('should handle unauthorized access', async () => {
      const error = {
        response: {
          status: 403,
          data: { detail: 'Access denied' },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(
        comparisonsClient.getComparison('comparison-123')
      ).rejects.toEqual({
        detail: 'Access denied',
        status: 403,
      });
    });
  });

  describe('updateComparison', () => {
    it('should update comparison successfully', async () => {
      const mockRequest: ComparisonUpdate = {
        name: 'Updated Comparison Name',
      };

      const mockResponse: ComparisonResponse = {
        id: 'comparison-123',
        vacancy_id: 'vacancy-123',
        resume_ids: ['resume-1', 'resume-2'],
        name: 'Updated Comparison Name',
        created_by: 'user-456',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      };

      mockAxiosInstance.put.mockResolvedValue({ data: mockResponse });

      const result = await comparisonsClient.updateComparison(
        'comparison-123',
        mockRequest
      );

      expect(result).toEqual(mockResponse);
      expect(result.name).toBe('Updated Comparison Name');
      expect(mockAxiosInstance.put).toHaveBeenCalledWith(
        '/api/comparisons/comparison-123',
        mockRequest
      );
    });

    it('should update comparison with filters', async () => {
      const mockRequest: ComparisonUpdate = {
        filters: { min_experience: 7 },
      };

      const mockResponse: ComparisonResponse = {
        id: 'comparison-123',
        vacancy_id: 'vacancy-123',
        resume_ids: ['resume-1', 'resume-2'],
        name: 'Comparison',
        filters: { min_experience: 7 },
        created_by: 'user-456',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      };

      mockAxiosInstance.put.mockResolvedValue({ data: mockResponse });

      const result = await comparisonsClient.updateComparison(
        'comparison-123',
        mockRequest
      );

      expect(result.filters).toEqual({ min_experience: 7 });
    });

    it('should update shared_with list', async () => {
      const mockRequest: ComparisonUpdate = {
        shared_with: ['user-1', 'user-2'],
      };

      const mockResponse: ComparisonResponse = {
        id: 'comparison-123',
        vacancy_id: 'vacancy-123',
        resume_ids: ['resume-1'],
        name: 'Comparison',
        shared_with: ['user-1', 'user-2'],
        created_by: 'user-456',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      };

      mockAxiosInstance.put.mockResolvedValue({ data: mockResponse });

      const result = await comparisonsClient.updateComparison(
        'comparison-123',
        mockRequest
      );

      expect(result.shared_with).toEqual(['user-1', 'user-2']);
    });

    it('should handle update validation error', async () => {
      const mockRequest: ComparisonUpdate = {
        name: '',
      };

      const error = {
        response: {
          status: 422,
          data: { detail: 'Name cannot be empty' },
        },
      };

      mockAxiosInstance.put.mockRejectedValue(error);

      await expect(
        comparisonsClient.updateComparison('comparison-123', mockRequest)
      ).rejects.toEqual({
        detail: 'Name cannot be empty',
        status: 422,
      });
    });

    it('should handle comparison not found during update', async () => {
      const mockRequest: ComparisonUpdate = {
        name: 'Updated Name',
      };

      const error = {
        response: {
          status: 404,
          data: {},
        },
      };

      mockAxiosInstance.put.mockRejectedValue(error);

      await expect(
        comparisonsClient.updateComparison('nonexistent', mockRequest)
      ).rejects.toEqual({
        detail: 'Сравнение не найдено.',
        status: 404,
      });
    });
  });

  describe('deleteComparison', () => {
    it('should delete comparison successfully', async () => {
      mockAxiosInstance.delete.mockResolvedValue({ data: {} });

      await expect(
        comparisonsClient.deleteComparison('comparison-123')
      ).resolves.toBeUndefined();

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith(
        '/api/comparisons/comparison-123'
      );
    });

    it('should handle comparison not found during deletion', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Comparison not found' },
        },
      };

      mockAxiosInstance.delete.mockRejectedValue(error);

      await expect(
        comparisonsClient.deleteComparison('nonexistent')
      ).rejects.toEqual({
        detail: 'Comparison not found',
        status: 404,
      });
    });

    it('should handle unauthorized deletion', async () => {
      const error = {
        response: {
          status: 403,
          data: {},
        },
      };

      mockAxiosInstance.delete.mockRejectedValue(error);

      await expect(
        comparisonsClient.deleteComparison('comparison-123')
      ).rejects.toEqual({
        detail: 'Доступ запрещен. У вас нет прав для выполнения этого действия.',
        status: 403,
      });
    });
  });

  describe('compareMultipleResumes', () => {
    it('should compare multiple resumes successfully', async () => {
      const mockRequest: CompareMultipleRequest = {
        vacancy_id: 'vacancy-123',
        resume_ids: ['resume-1', 'resume-2', 'resume-3'],
      };

      const mockResponse: ComparisonMatrixData = {
        vacancy_id: 'vacancy-123',
        vacancy_title: 'Senior Developer',
        comparison_results: [
          {
            resume_id: 'resume-1',
            match_percentage: 95.0,
            matched_skills: ['React', 'TypeScript', 'Node.js'],
            missing_skills: ['GraphQL'],
            rank: 1,
          },
          {
            resume_id: 'resume-2',
            match_percentage: 87.5,
            matched_skills: ['React', 'TypeScript'],
            missing_skills: ['Node.js', 'GraphQL'],
            rank: 2,
          },
          {
            resume_id: 'resume-3',
            match_percentage: 72.0,
            matched_skills: ['React'],
            missing_skills: ['TypeScript', 'Node.js', 'GraphQL'],
            rank: 3,
          },
        ],
        total_resumes: 3,
        processing_time_ms: 250,
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await comparisonsClient.compareMultipleResumes(mockRequest);

      expect(result).toEqual(mockResponse);
      expect(result.comparison_results).toHaveLength(3);
      expect(result.comparison_results[0].rank).toBe(1);
      expect(result.comparison_results[0].match_percentage).toBe(95.0);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/comparisons/compare-multiple',
        mockRequest
      );
    });

    it('should handle comparison with two resumes', async () => {
      const mockRequest: CompareMultipleRequest = {
        vacancy_id: 'vacancy-123',
        resume_ids: ['resume-1', 'resume-2'],
      };

      const mockResponse: ComparisonMatrixData = {
        vacancy_id: 'vacancy-123',
        vacancy_title: 'Developer',
        comparison_results: [
          {
            resume_id: 'resume-1',
            match_percentage: 90.0,
            matched_skills: ['React', 'TypeScript'],
            missing_skills: [],
            rank: 1,
          },
          {
            resume_id: 'resume-2',
            match_percentage: 85.0,
            matched_skills: ['React'],
            missing_skills: ['TypeScript'],
            rank: 2,
          },
        ],
        total_resumes: 2,
        processing_time_ms: 150,
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await comparisonsClient.compareMultipleResumes(mockRequest);

      expect(result.total_resumes).toBe(2);
      expect(result.comparison_results).toHaveLength(2);
    });

    it('should handle vacancy not found', async () => {
      const mockRequest: CompareMultipleRequest = {
        vacancy_id: 'nonexistent',
        resume_ids: ['resume-1'],
      };

      const error = {
        response: {
          status: 404,
          data: { detail: 'Vacancy not found' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        comparisonsClient.compareMultipleResumes(mockRequest)
      ).rejects.toEqual({
        detail: 'Vacancy not found',
        status: 404,
      });
    });

    it('should handle validation error for insufficient resumes', async () => {
      const mockRequest: CompareMultipleRequest = {
        vacancy_id: 'vacancy-123',
        resume_ids: [],
      };

      const error = {
        response: {
          status: 422,
          data: { detail: 'At least one resume ID is required' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        comparisonsClient.compareMultipleResumes(mockRequest)
      ).rejects.toEqual({
        detail: 'At least one resume ID is required',
        status: 422,
      });
    });

    it('should handle timeout error', async () => {
      const mockRequest: CompareMultipleRequest = {
        vacancy_id: 'vacancy-123',
        resume_ids: ['resume-1', 'resume-2'],
      };

      const error = {
        code: 'ECONNABORTED',
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        comparisonsClient.compareMultipleResumes(mockRequest)
      ).rejects.toEqual({
        detail: 'Таймаут запроса. Проверьте соединение и попробуйте снова.',
        status: 408,
      });
    });

    it('should handle large batch comparison', async () => {
      const mockRequest: CompareMultipleRequest = {
        vacancy_id: 'vacancy-123',
        resume_ids: Array.from({ length: 10 }, (_, i) => `resume-${i + 1}`),
      };

      const mockResponse: ComparisonMatrixData = {
        vacancy_id: 'vacancy-123',
        vacancy_title: 'Senior Developer',
        comparison_results: Array.from({ length: 10 }, (_, i) => ({
          resume_id: `resume-${i + 1}`,
          match_percentage: 90 - i * 5,
          matched_skills: ['React'],
          missing_skills: [],
          rank: i + 1,
        })),
        total_resumes: 10,
        processing_time_ms: 500,
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await comparisonsClient.compareMultipleResumes(mockRequest);

      expect(result.total_resumes).toBe(10);
      expect(result.comparison_results).toHaveLength(10);
    });
  });

  describe('Error Handling', () => {
    it('should handle network error without response', async () => {
      const error = {
        code: 'NETWORK_ERROR',
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(
        comparisonsClient.getComparison('comparison-123')
      ).rejects.toEqual({
        detail: 'Ошибка сети. Проверьте соединение и попробуйте снова.',
        status: 0,
      });
    });

    it('should handle 400 bad request', async () => {
      const error = {
        response: {
          status: 400,
          data: {},
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(
        comparisonsClient.getComparison('comparison-123')
      ).rejects.toEqual({
        detail: 'Неверный запрос. Проверьте введенные данные.',
        status: 400,
      });
    });

    it('should handle 401 unauthorized', async () => {
      const error = {
        response: {
          status: 401,
          data: {},
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(
        comparisonsClient.getComparison('comparison-123')
      ).rejects.toEqual({
        detail: 'Не авторизован. Войдите в систему.',
        status: 401,
      });
    });

    it('should handle 429 rate limit', async () => {
      const error = {
        response: {
          status: 429,
          data: {},
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(
        comparisonsClient.createComparison({
          vacancy_id: 'vacancy-123',
          resume_ids: ['resume-1'],
          name: 'Test',
        })
      ).rejects.toEqual({
        detail: 'Слишком много запросов. Попробуйте позже.',
        status: 429,
      });
    });

    it('should handle 502 bad gateway', async () => {
      const error = {
        response: {
          status: 502,
          data: {},
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(comparisonsClient.listComparisons()).rejects.toEqual({
        detail: 'Ошибка шлюза. Попробуйте позже.',
        status: 502,
      });
    });

    it('should handle 503 service unavailable', async () => {
      const error = {
        response: {
          status: 503,
          data: {},
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(comparisonsClient.listComparisons()).rejects.toEqual({
        detail: 'Сервис недоступен. Попробуйте позже.',
        status: 503,
      });
    });

    it('should handle unknown status code with server detail', async () => {
      const error = {
        response: {
          status: 418,
          data: { detail: 'I am a teapot' },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(
        comparisonsClient.getComparison('comparison-123')
      ).rejects.toEqual({
        detail: 'I am a teapot',
        status: 418,
      });
    });

    it('should handle unknown status code without server detail', async () => {
      const error = {
        response: {
          status: 418,
          data: {},
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(
        comparisonsClient.getComparison('comparison-123')
      ).rejects.toEqual({
        detail: 'Произошла непредвиденная ошибка.',
        status: 418,
      });
    });
  });
});
