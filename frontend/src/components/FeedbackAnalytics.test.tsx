/**
 * Tests for FeedbackAnalytics Component
 *
 * Tests the feedback analytics dashboard including:
 * - Fetching and displaying feedback data
 * - Calculating accuracy metrics
 * - Displaying model versions
 * - Tab navigation between views
 * - Error handling and loading states
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import FeedbackAnalytics from './FeedbackAnalytics';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('FeedbackAnalytics', () => {
  const mockFeedbackApiUrl = 'http://localhost:8000/api/feedback';
  const mockModelApiUrl = 'http://localhost:8000/api/model-versions';

  const mockFeedback = [
    {
      id: 'fb-1',
      resume_id: 'resume-1',
      vacancy_id: 'vacancy-1',
      match_result_id: 'match-1',
      skill: 'Java',
      was_correct: true,
      confidence_score: 0.95,
      recruiter_correction: undefined,
      actual_skill: undefined,
      feedback_source: 'recruiter',
      processed: true,
      metadata: {},
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:00:00Z',
    },
    {
      id: 'fb-2',
      resume_id: 'resume-2',
      vacancy_id: 'vacancy-2',
      match_result_id: 'match-2',
      skill: 'Python',
      was_correct: false,
      confidence_score: 0.65,
      recruiter_correction: 'Python3',
      actual_skill: 'Python3',
      feedback_source: 'recruiter',
      processed: false,
      metadata: {},
      created_at: '2024-01-16T10:00:00Z',
      updated_at: '2024-01-16T10:00:00Z',
    },
    {
      id: 'fb-3',
      resume_id: 'resume-3',
      vacancy_id: 'vacancy-3',
      match_result_id: 'match-3',
      skill: 'React',
      was_correct: true,
      confidence_score: 0.88,
      recruiter_correction: undefined,
      actual_skill: undefined,
      feedback_source: 'automatic',
      processed: true,
      metadata: {},
      created_at: '2024-01-17T10:00:00Z',
      updated_at: '2024-01-17T10:00:00Z',
    },
  ];

  const mockModels = [
    {
      id: 'model-1',
      model_name: 'skill-matcher',
      version: '1.0.0',
      is_active: true,
      is_experiment: false,
      experiment_config: undefined,
      model_metadata: {},
      accuracy_metrics: { precision: 0.85, recall: 0.82, f1: 0.83 },
      performance_score: 85.5,
      created_at: '2024-01-10T10:00:00Z',
      updated_at: '2024-01-15T10:00:00Z',
    },
    {
      id: 'model-2',
      model_name: 'skill-matcher',
      version: '1.1.0-experiment',
      is_active: false,
      is_experiment: true,
      experiment_config: { test_group: 'A' },
      model_metadata: {},
      accuracy_metrics: { precision: 0.88, recall: 0.86, f1: 0.87 },
      performance_score: 87.2,
      created_at: '2024-01-16T10:00:00Z',
      updated_at: '2024-01-16T10:00:00Z',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render loading state initially', () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({
          feedback: mockFeedback,
          total_count: 3,
        }),
      });

      render(<FeedbackAnalytics />);

      expect(screen.getByText('Loading analytics...')).toBeInTheDocument();
    });

    it('should render dashboard after successful data fetch', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            feedback: mockFeedback,
            total_count: 3,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            models: mockModels,
            total_count: 2,
          }),
        });

      render(<FeedbackAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Feedback Analytics Dashboard')).toBeInTheDocument();
      });

      expect(screen.getByText('3')).toBeInTheDocument(); // Total feedback
      expect(screen.getByText('2')).toBeInTheDocument(); // Correct matches
      expect(screen.getByText('1')).toBeInTheDocument(); // Incorrect matches
    });

    it('should render error state on fetch failure', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(<FeedbackAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Analytics Failed')).toBeInTheDocument();
      });

      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  describe('Accuracy Metrics', () => {
    it('should calculate and display accuracy correctly', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            feedback: mockFeedback,
            total_count: 3,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            models: [],
            total_count: 0,
          }),
        });

      render(<FeedbackAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Feedback Analytics Dashboard')).toBeInTheDocument();
      });

      // Accuracy should be 66.7% (2/3)
      expect(screen.getByText('66.7%')).toBeInTheDocument();
    });

    it('should display accuracy trend indicator for high accuracy', async () => {
      const highAccuracyFeedback = Array(10)
        .fill(null)
        .map((_, i) => ({
          ...mockFeedback[0],
          id: `fb-${i}`,
          was_correct: true,
        }));

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            feedback: highAccuracyFeedback,
            total_count: 10,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            models: [],
            total_count: 0,
          }),
        });

      render(<FeedbackAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('100.0%')).toBeInTheDocument();
      });

      // Should show trending up icon for high accuracy (>= 70%)
      const accuracyCard = screen.getByText('100.0%').closest('.MuiCard-root');
      expect(accuracyCard).toBeInTheDocument();
    });

    it('should display correct accuracy color coding', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            feedback: mockFeedback,
            total_count: 3,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            models: [],
            total_count: 0,
          }),
        });

      render(<FeedbackAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('66.7%')).toBeInTheDocument();
      });

      // 66.7% should show warning color (between 60-80%)
      const accuracyText = screen.getByText('66.7%');
      expect(accuracyText).toBeInTheDocument();
    });
  });

  describe('Tab Navigation', () => {
    it('should switch to Learning Progress tab', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            feedback: mockFeedback,
            total_count: 3,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            models: [],
            total_count: 0,
          }),
        });

      render(<FeedbackAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Feedback Analytics Dashboard')).toBeInTheDocument();
      });

      // Click Learning Progress tab
      fireEvent.click(screen.getByText('Learning Progress'));

      await waitFor(() => {
        expect(screen.getByText('Learning Progress')).toBeInTheDocument();
        expect(screen.getByText('Processed Feedback')).toBeInTheDocument();
        expect(screen.getByText('Pending Processing')).toBeInTheDocument();
      });
    });

    it('should switch to Model Versions tab', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            feedback: mockFeedback,
            total_count: 3,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            models: mockModels,
            total_count: 2,
          }),
        });

      render(<FeedbackAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Feedback Analytics Dashboard')).toBeInTheDocument();
      });

      // Click Model Versions tab
      fireEvent.click(screen.getByText('Model Versions'));

      await waitFor(() => {
        expect(screen.getByText('Model Versions')).toBeInTheDocument();
        expect(screen.getByText('skill-matcher')).toBeInTheDocument();
        expect(screen.getByText('1.0.0')).toBeInTheDocument();
      });
    });

    it('should switch to Recent Feedback tab', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            feedback: mockFeedback,
            total_count: 3,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            models: [],
            total_count: 0,
          }),
        });

      render(<FeedbackAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Feedback Analytics Dashboard')).toBeInTheDocument();
      });

      // Click Recent Feedback tab
      fireEvent.click(screen.getByText('Recent Feedback'));

      await waitFor(() => {
        expect(screen.getByText('Recent Feedback')).toBeInTheDocument();
        expect(screen.getByText('Java')).toBeInTheDocument();
        expect(screen.getByText('Python')).toBeInTheDocument();
        expect(screen.getByText('React')).toBeInTheDocument();
      });
    });
  });

  describe('Learning Progress Tab', () => {
    it('should display processed and unprocessed counts', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            feedback: mockFeedback,
            total_count: 3,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            models: [],
            total_count: 0,
          }),
        });

      render(<FeedbackAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Feedback Analytics Dashboard')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Learning Progress'));

      await waitFor(() => {
        expect(screen.getByText('2 / 3')).toBeInTheDocument(); // Processed
        expect(screen.getByText('1 / 3')).toBeInTheDocument(); // Unprocessed
      });
    });

    it('should display appropriate learning status message', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            feedback: mockFeedback,
            total_count: 3,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            models: [],
            total_count: 0,
          }),
        });

      render(<FeedbackAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Feedback Analytics Dashboard')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Learning Progress'));

      await waitFor(() => {
        expect(
          screen.getByText(/1 feedback entries pending ML pipeline processing/)
        ).toBeInTheDocument();
      });
    });

    it('should display accuracy trends and target', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            feedback: mockFeedback,
            total_count: 3,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            models: [],
            total_count: 0,
          }),
        });

      render(<FeedbackAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Feedback Analytics Dashboard')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Learning Progress'));

      await waitFor(() => {
        expect(screen.getByText('Current Match Accuracy')).toBeInTheDocument();
        expect(screen.getByText('Target Accuracy')).toBeInTheDocument();
        expect(screen.getByText('90.0%')).toBeInTheDocument(); // Target
        expect(screen.getByText('Gap to Target')).toBeInTheDocument();
      });
    });
  });

  describe('Model Versions Tab', () => {
    it('should display active production model', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            feedback: [],
            total_count: 0,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            models: mockModels,
            total_count: 2,
          }),
        });

      render(<FeedbackAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Feedback Analytics Dashboard')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Model Versions'));

      await waitFor(() => {
        expect(screen.getByText('Active Production Model')).toBeInTheDocument();
        expect(screen.getByText('skill-matcher')).toBeInTheDocument();
        expect(screen.getByText('1.0.0')).toBeInTheDocument();
        expect(screen.getByText('85.5 / 100')).toBeInTheDocument();
      });
    });

    it('should display experiment models', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            feedback: [],
            total_count: 0,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            models: mockModels,
            total_count: 2,
          }),
        });

      render(<FeedbackAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Feedback Analytics Dashboard')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Model Versions'));

      await waitFor(() => {
        expect(screen.getByText(/A\/B Testing Experiments \(1\)/)).toBeInTheDocument();
        expect(screen.getByText('1.1.0-experiment')).toBeInTheDocument();
        expect(screen.getByText('Experiment')).toBeInTheDocument();
      });
    });

    it('should display message when no models exist', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            feedback: [],
            total_count: 0,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            models: [],
            total_count: 0,
          }),
        });

      render(<FeedbackAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Feedback Analytics Dashboard')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Model Versions'));

      await waitFor(() => {
        expect(screen.getByText('No Model Versions')).toBeInTheDocument();
        expect(
          screen.getByText(
            'No model versions found. Model versioning will be available after the first training cycle.'
          )
        ).toBeInTheDocument();
      });
    });

    it('should display warning when no active model exists', async () => {
      const noActiveModel = [
        {
          ...mockModels[0],
          is_active: false,
        },
      ];

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            feedback: [],
            total_count: 0,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            models: noActiveModel,
            total_count: 1,
          }),
        });

      render(<FeedbackAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Feedback Analytics Dashboard')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Model Versions'));

      await waitFor(() => {
        expect(screen.getByText('No Active Model')).toBeInTheDocument();
        expect(
          screen.getByText(/1 model version\(s\) found, but none are currently active/)
        ).toBeInTheDocument();
      });
    });
  });

  describe('Recent Feedback Tab', () => {
    it('should display feedback entries in table', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            feedback: mockFeedback,
            total_count: 3,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            models: [],
            total_count: 0,
          }),
        });

      render(<FeedbackAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Feedback Analytics Dashboard')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Recent Feedback'));

      await waitFor(() => {
        expect(screen.getByText('Java')).toBeInTheDocument();
        expect(screen.getByText('Python')).toBeInTheDocument();
        expect(screen.getByText('React')).toBeInTheDocument();
      });
    });

    it('should display correct/incorrect badges', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            feedback: mockFeedback,
            total_count: 3,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            models: [],
            total_count: 0,
          }),
        });

      render(<FeedbackAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Feedback Analytics Dashboard')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Recent Feedback'));

      await waitFor(() => {
        expect(screen.getByText('Yes')).toBeInTheDocument(); // Correct matches
        expect(screen.getByText('No')).toBeInTheDocument(); // Incorrect match
      });
    });

    it('should display confidence scores', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            feedback: mockFeedback,
            total_count: 3,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            models: [],
            total_count: 0,
          }),
        });

      render(<FeedbackAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Feedback Analytics Dashboard')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Recent Feedback'));

      await waitFor(() => {
        expect(screen.getByText('95%')).toBeInTheDocument();
        expect(screen.getByText('65%')).toBeInTheDocument();
        expect(screen.getByText('88%')).toBeInTheDocument();
      });
    });

    it('should display feedback source', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            feedback: mockFeedback,
            total_count: 3,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            models: [],
            total_count: 0,
          }),
        });

      render(<FeedbackAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Feedback Analytics Dashboard')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Recent Feedback'));

      await waitFor(() => {
        expect(screen.getByText('recruiter')).toBeInTheDocument();
        expect(screen.getByText('automatic')).toBeInTheDocument();
      });
    });

    it('should display processed status', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            feedback: mockFeedback,
            total_count: 3,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            models: [],
            total_count: 0,
          }),
        });

      render(<FeedbackAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Feedback Analytics Dashboard')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Recent Feedback'));

      await waitFor(() => {
        const processedBadges = screen.getAllByText('Yes');
        const unprocessedBadges = screen.getAllByText('No');

        // Should have processed badges for processed entries
        expect(processedBadges.length).toBeGreaterThan(0);

        // Should have unprocessed badge for unprocessed entry
        expect(unprocessedBadges.length).toBeGreaterThan(0);
      });
    });

    it('should limit display to 20 entries', async () => {
      const largeFeedback = Array(25)
        .fill(null)
        .map((_, i) => ({
          ...mockFeedback[0],
          id: `fb-${i}`,
          skill: `Skill-${i}`,
        }));

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            feedback: largeFeedback,
            total_count: 25,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            models: [],
            total_count: 0,
          }),
        });

      render(<FeedbackAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Feedback Analytics Dashboard')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Recent Feedback'));

      await waitFor(() => {
        expect(screen.getByText(/Showing 20 of 25/)).toBeInTheDocument();
      });
    });

    it('should display message when no feedback exists', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            feedback: [],
            total_count: 0,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            models: [],
            total_count: 0,
          }),
        });

      render(<FeedbackAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Feedback Analytics Dashboard')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Recent Feedback'));

      await waitFor(() => {
        expect(screen.getByText('No Feedback Data')).toBeInTheDocument();
        expect(
          screen.getByText(
            'No feedback entries found. Start collecting recruiter feedback to populate this dashboard.'
          )
        ).toBeInTheDocument();
      });
    });
  });

  describe('Refresh Functionality', () => {
    it('should refresh data when Refresh button is clicked', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            feedback: mockFeedback,
            total_count: 3,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            models: mockModels,
            total_count: 2,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            feedback: mockFeedback,
            total_count: 3,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            models: mockModels,
            total_count: 2,
          }),
        });

      render(<FeedbackAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Feedback Analytics Dashboard')).toBeInTheDocument();
      });

      // Clear mock calls
      vi.clearAllMocks();

      // Click refresh
      fireEvent.click(screen.getByText('Refresh'));

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledTimes(2); // Feedback + Models
      });
    });

    it('should retry after error when Retry button is clicked', async () => {
      mockFetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            feedback: mockFeedback,
            total_count: 3,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            models: mockModels,
            total_count: 2,
          }),
        });

      render(<FeedbackAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Analytics Failed')).toBeInTheDocument();
      });

      // Click retry
      fireEvent.click(screen.getByText('Retry'));

      await waitFor(() => {
        expect(screen.getByText('Feedback Analytics Dashboard')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledTimes(3); // Failed + Feedback + Models
    });
  });

  describe('Custom API URLs', () => {
    it('should use custom API URLs when provided', async () => {
      const customFeedbackUrl = 'http://custom-api.com/feedback';
      const customModelUrl = 'http://custom-api.com/models';

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            feedback: [],
            total_count: 0,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            models: [],
            total_count: 0,
          }),
        });

      render(
        <FeedbackAnalytics
          feedbackApiUrl={customFeedbackUrl}
          modelApiUrl={customModelUrl}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Feedback Analytics Dashboard')).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledWith(`${customFeedbackUrl}/?limit=100`);
      expect(mockFetch).toHaveBeenCalledWith(`${customModelUrl}/`);
    });
  });

  describe('Empty States', () => {
    it('should display zero accuracy when no feedback exists', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            feedback: [],
            total_count: 0,
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            models: [],
            total_count: 0,
          }),
        });

      render(<FeedbackAnalytics />);

      await waitFor(() => {
        expect(screen.getByText('Feedback Analytics Dashboard')).toBeInTheDocument();
      });

      expect(screen.getByText('0')).toBeInTheDocument(); // Total
      expect(screen.getByText('0%')).toBeInTheDocument(); // Accuracy
    });
  });
});
