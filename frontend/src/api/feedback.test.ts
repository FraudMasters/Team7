/**
 * Tests for Feedback API Client
 *
 * Tests the FeedbackClient for creating, listing, getting, updating, and deleting feedback.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { FeedbackClient } from './feedback';
import axios from 'axios';
import type {
  FeedbackCreate,
  FeedbackUpdate,
  FeedbackResponse,
  FeedbackListResponse,
  FeedbackEntry,
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

describe('FeedbackClient', () => {
  let feedbackClient: FeedbackClient;
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

    // Create feedback client with mock
    feedbackClient = new FeedbackClient({ baseURL: 'http://test.com' });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Constructor', () => {
    it('should create client with default config', () => {
      const client = new FeedbackClient();
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
      const client = new FeedbackClient({
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

  describe('createFeedback', () => {
    it('should create feedback successfully', async () => {
      const mockRequest: FeedbackCreate = {
        feedback: [
          {
            resume_id: 'resume-123',
            vacancy_id: 'vacancy-456',
            skill: 'React',
            was_correct: true,
            confidence_score: 0.95,
            feedback_source: 'frontend',
          },
        ],
      };

      const mockResponse: FeedbackListResponse = {
        feedback: [
          {
            id: 'feedback-1',
            resume_id: 'resume-123',
            vacancy_id: 'vacancy-456',
            skill: 'React',
            was_correct: true,
            confidence_score: 0.95,
            feedback_source: 'frontend',
            processed: false,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
        ],
        total_count: 1,
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await feedbackClient.createFeedback(mockRequest);

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/api/feedback/',
        mockRequest
      );
    });

    it('should create multiple feedback items', async () => {
      const mockRequest: FeedbackCreate = {
        feedback: [
          {
            resume_id: 'resume-123',
            vacancy_id: 'vacancy-456',
            skill: 'React',
            was_correct: true,
            confidence_score: 0.95,
            feedback_source: 'frontend',
          },
          {
            resume_id: 'resume-123',
            vacancy_id: 'vacancy-456',
            skill: 'TypeScript',
            was_correct: false,
            actual_skill: 'JavaScript',
            feedback_source: 'frontend',
          },
        ],
      };

      const mockResponse: FeedbackListResponse = {
        feedback: [
          {
            id: 'feedback-1',
            resume_id: 'resume-123',
            vacancy_id: 'vacancy-456',
            skill: 'React',
            was_correct: true,
            confidence_score: 0.95,
            feedback_source: 'frontend',
            processed: false,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
          {
            id: 'feedback-2',
            resume_id: 'resume-123',
            vacancy_id: 'vacancy-456',
            skill: 'TypeScript',
            was_correct: false,
            actual_skill: 'JavaScript',
            feedback_source: 'frontend',
            processed: false,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
        ],
        total_count: 2,
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await feedbackClient.createFeedback(mockRequest);

      expect(result.feedback).toHaveLength(2);
      expect(result.total_count).toBe(2);
    });

    it('should handle validation error', async () => {
      const mockRequest: FeedbackCreate = {
        feedback: [
          {
            resume_id: 'resume-123',
            vacancy_id: 'vacancy-456',
            skill: '',
            was_correct: true,
            feedback_source: 'frontend',
          },
        ],
      };

      const error = {
        response: {
          status: 422,
          data: { detail: 'Validation error: skill cannot be empty' },
        },
      };

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(feedbackClient.createFeedback(mockRequest)).rejects.toEqual({
        detail: 'Validation error: skill cannot be empty',
        status: 422,
      });
    });

    it('should handle network error', async () => {
      const mockRequest: FeedbackCreate = {
        feedback: [
          {
            resume_id: 'resume-123',
            vacancy_id: 'vacancy-456',
            skill: 'React',
            was_correct: true,
            feedback_source: 'frontend',
          },
        ],
      };

      const error = new Error('Network Error');
      (error as any).code = 'ERR_NETWORK';

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(feedbackClient.createFeedback(mockRequest)).rejects.toEqual({
        detail: 'Ошибка сети. Проверьте соединение и попробуйте снова.',
        status: 0,
      });
    });

    it('should handle timeout error', async () => {
      const mockRequest: FeedbackCreate = {
        feedback: [
          {
            resume_id: 'resume-123',
            vacancy_id: 'vacancy-456',
            skill: 'React',
            was_correct: true,
            feedback_source: 'frontend',
          },
        ],
      };

      const error = new Error('Timeout');
      (error as any).code = 'ECONNABORTED';

      mockAxiosInstance.post.mockRejectedValue(error);

      await expect(feedbackClient.createFeedback(mockRequest)).rejects.toEqual({
        detail: 'Таймаут запроса. Проверьте соединение и попробуйте снова.',
        status: 408,
      });
    });
  });

  describe('listFeedback', () => {
    it('should list all feedback without filters', async () => {
      const mockResponse: FeedbackListResponse = {
        feedback: [
          {
            id: 'feedback-1',
            resume_id: 'resume-123',
            vacancy_id: 'vacancy-456',
            skill: 'React',
            was_correct: true,
            feedback_source: 'frontend',
            processed: false,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
        ],
        total_count: 1,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await feedbackClient.listFeedback();

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/feedback/', {
        params: {},
      });
    });

    it('should list feedback with resume and vacancy filters', async () => {
      const mockResponse: FeedbackListResponse = {
        feedback: [
          {
            id: 'feedback-1',
            resume_id: 'resume-123',
            vacancy_id: 'vacancy-456',
            skill: 'React',
            was_correct: true,
            feedback_source: 'frontend',
            processed: false,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
        ],
        total_count: 1,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await feedbackClient.listFeedback(
        'resume-123',
        'vacancy-456'
      );

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/feedback/', {
        params: {
          resume_id: 'resume-123',
          vacancy_id: 'vacancy-456',
        },
      });
    });

    it('should list feedback with all filters', async () => {
      const mockResponse: FeedbackListResponse = {
        feedback: [],
        total_count: 0,
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse });

      const result = await feedbackClient.listFeedback(
        'resume-123',
        'vacancy-456',
        'React',
        true,
        false,
        'frontend'
      );

      expect(result).toEqual(mockResponse);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/api/feedback/', {
        params: {
          resume_id: 'resume-123',
          vacancy_id: 'vacancy-456',
          skill: 'React',
          was_correct: true,
          processed: false,
          feedback_source: 'frontend',
        },
      });
    });

    it('should handle list error', async () => {
      const error = {
        response: {
          status: 500,
          data: { detail: 'Internal server error' },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(feedbackClient.listFeedback()).rejects.toEqual({
        detail: 'Internal server error',
        status: 500,
      });
    });
  });

  describe('getFeedback', () => {
    it('should get feedback by id successfully', async () => {
      const mockFeedback: FeedbackResponse = {
        id: 'feedback-123',
        resume_id: 'resume-123',
        vacancy_id: 'vacancy-456',
        skill: 'React',
        was_correct: true,
        confidence_score: 0.95,
        feedback_source: 'frontend',
        processed: false,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockFeedback });

      const result = await feedbackClient.getFeedback('feedback-123');

      expect(result).toEqual(mockFeedback);
      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/api/feedback/feedback-123'
      );
    });

    it('should handle feedback not found', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Feedback not found' },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(
        feedbackClient.getFeedback('nonexistent-id')
      ).rejects.toEqual({
        detail: 'Feedback not found',
        status: 404,
      });
    });

    it('should handle network error', async () => {
      const error = new Error('Network Error');
      (error as any).code = 'ERR_NETWORK';

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(feedbackClient.getFeedback('feedback-123')).rejects.toEqual({
        detail: 'Ошибка сети. Проверьте соединение и попробуйте снова.',
        status: 0,
      });
    });
  });

  describe('updateFeedback', () => {
    it('should update feedback successfully', async () => {
      const mockUpdate: FeedbackUpdate = {
        was_correct: false,
        recruiter_correction: 'Actually meant React.js',
        processed: true,
      };

      const mockFeedback: FeedbackResponse = {
        id: 'feedback-123',
        resume_id: 'resume-123',
        vacancy_id: 'vacancy-456',
        skill: 'React',
        was_correct: false,
        recruiter_correction: 'Actually meant React.js',
        feedback_source: 'frontend',
        processed: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T01:00:00Z',
      };

      mockAxiosInstance.put.mockResolvedValue({ data: mockFeedback });

      const result = await feedbackClient.updateFeedback(
        'feedback-123',
        mockUpdate
      );

      expect(result).toEqual(mockFeedback);
      expect(mockAxiosInstance.put).toHaveBeenCalledWith(
        '/api/feedback/feedback-123',
        mockUpdate
      );
    });

    it('should handle partial update', async () => {
      const mockUpdate: FeedbackUpdate = {
        processed: true,
      };

      const mockFeedback: FeedbackResponse = {
        id: 'feedback-123',
        resume_id: 'resume-123',
        vacancy_id: 'vacancy-456',
        skill: 'React',
        was_correct: true,
        feedback_source: 'frontend',
        processed: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T01:00:00Z',
      };

      mockAxiosInstance.put.mockResolvedValue({ data: mockFeedback });

      const result = await feedbackClient.updateFeedback(
        'feedback-123',
        mockUpdate
      );

      expect(result.processed).toBe(true);
    });

    it('should handle validation error on update', async () => {
      const mockUpdate: FeedbackUpdate = {
        confidence_score: 2.5, // Invalid: should be 0-1
      };

      const error = {
        response: {
          status: 422,
          data: { detail: 'Invalid confidence score' },
        },
      };

      mockAxiosInstance.put.mockRejectedValue(error);

      await expect(
        feedbackClient.updateFeedback('feedback-123', mockUpdate)
      ).rejects.toEqual({
        detail: 'Invalid confidence score',
        status: 422,
      });
    });

    it('should handle not found on update', async () => {
      const mockUpdate: FeedbackUpdate = {
        was_correct: false,
      };

      const error = {
        response: {
          status: 404,
          data: { detail: 'Feedback not found' },
        },
      };

      mockAxiosInstance.put.mockRejectedValue(error);

      await expect(
        feedbackClient.updateFeedback('nonexistent-id', mockUpdate)
      ).rejects.toEqual({
        detail: 'Feedback not found',
        status: 404,
      });
    });
  });

  describe('deleteFeedback', () => {
    it('should delete feedback successfully', async () => {
      mockAxiosInstance.delete.mockResolvedValue({});

      await expect(
        feedbackClient.deleteFeedback('feedback-123')
      ).resolves.not.toThrow();

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith(
        '/api/feedback/feedback-123'
      );
    });

    it('should handle not found on delete', async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: 'Feedback not found' },
        },
      };

      mockAxiosInstance.delete.mockRejectedValue(error);

      await expect(
        feedbackClient.deleteFeedback('nonexistent-id')
      ).rejects.toEqual({
        detail: 'Feedback not found',
        status: 404,
      });
    });

    it('should handle forbidden on delete', async () => {
      const error = {
        response: {
          status: 403,
          data: { detail: 'Access denied' },
        },
      };

      mockAxiosInstance.delete.mockRejectedValue(error);

      await expect(
        feedbackClient.deleteFeedback('feedback-123')
      ).rejects.toEqual({
        detail: 'Access denied',
        status: 403,
      });
    });
  });

  describe('getAxiosInstance', () => {
    it('should return the axios instance', () => {
      const instance = feedbackClient.getAxiosInstance();

      expect(instance).toBeDefined();
      expect(instance).toEqual(mockAxiosInstance);
    });
  });

  describe('Error Handling - transformError', () => {
    it('should use default message for 400 error', async () => {
      const error = {
        response: {
          status: 400,
          data: {},
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(feedbackClient.listFeedback()).rejects.toEqual({
        detail: 'Неверный запрос. Проверьте введенные данные.',
        status: 400,
      });
    });

    it('should use default message for 401 error', async () => {
      const error = {
        response: {
          status: 401,
          data: {},
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(feedbackClient.listFeedback()).rejects.toEqual({
        detail: 'Не авторизован. Войдите в систему.',
        status: 401,
      });
    });

    it('should use default message for 429 error', async () => {
      const error = {
        response: {
          status: 429,
          data: {},
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(feedbackClient.listFeedback()).rejects.toEqual({
        detail: 'Слишком много запросов. Попробуйте позже.',
        status: 429,
      });
    });

    it('should use generic message for unknown status code', async () => {
      const error = {
        response: {
          status: 418,
          data: {},
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(feedbackClient.listFeedback()).rejects.toEqual({
        detail: 'Произошла непредвиденная ошибка.',
        status: 418,
      });
    });

    it('should prioritize server detail message over default', async () => {
      const customMessage = 'Custom server error message';
      const error = {
        response: {
          status: 500,
          data: { detail: customMessage },
        },
      };

      mockAxiosInstance.get.mockRejectedValue(error);

      await expect(feedbackClient.listFeedback()).rejects.toEqual({
        detail: customMessage,
        status: 500,
      });
    });
  });
});
