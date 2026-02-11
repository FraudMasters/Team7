/**
 * Tests for ModelTrainingDashboard Component
 *
 * Tests the ML model training dashboard including:
 * - Pipeline health status display
 * - Training status per model
 * - Performance trends visualization
 * - Pause/resume functionality
 * - Manual retraining trigger
 * - Error handling and loading states
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ModelTrainingDashboard from '../ModelTrainingDashboard';

// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, fallback?: string) => fallback || key,
  }),
}));

import axios from 'axios';

const mockAxiosGet = axios.get as ReturnType<typeof vi.fn>;
const mockAxiosPost = axios.post as ReturnType<typeof vi.fn>;

describe('ModelTrainingDashboard', () => {
  const mockPipelineHealth = {
    total_models: 2,
    active_trainings: 0,
    failed_trainings: 0,
    completed_trainings: 5,
    overall_health: 'healthy' as const,
  };

  const mockSkillMatchingStatus = {
    model_name: 'skill_matching',
    latest_version: 'v1.0.0',
    training_status: 'completed',
    last_training_at: '2024-01-15T10:00:00Z',
    last_training_duration: 120,
    last_training_metrics: {
      accuracy: 0.85,
      precision: 0.82,
      recall: 0.88,
      f1_score: 0.85,
    },
    is_healthy: true,
    error_message: null,
  };

  const mockRankingStatus = {
    model_name: 'ranking',
    latest_version: 'v2.0.0',
    training_status: 'completed',
    last_training_at: '2024-01-14T10:00:00Z',
    last_training_duration: 180,
    last_training_metrics: {
      accuracy: 0.88,
      precision: 0.86,
      recall: 0.90,
      f1_score: 0.88,
    },
    is_healthy: true,
    error_message: null,
  };

  const mockRecentMetrics = [
    {
      id: 'metric-1',
      model_name: 'skill_matching',
      version: 'v1.0.0',
      training_status: 'completed',
      training_duration: 120,
      training_metrics: { f1_score: 0.85 },
      dataset_info: { train_size: 1000, test_size: 200 },
      started_at: '2024-01-15T08:00:00Z',
      completed_at: '2024-01-15T10:00:00Z',
      created_at: '2024-01-15T08:00:00Z',
    },
  ];

  const mockPerformanceTrends = {
    model_name: 'skill_matching',
    current_metrics: {
      accuracy: 0.85,
      precision: 0.82,
      recall: 0.88,
      f1_score: 0.85,
      auc_score: 0.87,
    },
    trend_data: [
      { timestamp: '2024-01-09T10:00:00Z', accuracy: 0.78, f1_score: 0.76 },
      { timestamp: '2024-01-10T10:00:00Z', accuracy: 0.80, f1_score: 0.79 },
      { timestamp: '2024-01-11T10:00:00Z', accuracy: 0.82, f1_score: 0.81 },
      { timestamp: '2024-01-12T10:00:00Z', accuracy: 0.81, f1_score: 0.80 },
      { timestamp: '2024-01-13T10:00:00Z', accuracy: 0.84, f1_score: 0.83 },
      { timestamp: '2024-01-14T10:00:00Z', accuracy: 0.85, f1_score: 0.85 },
    ],
    trend_direction: 'improving' as const,
    health_score: 85,
    alert_status: 'none' as const,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render loading state initially', async () => {
      mockAxiosGet.mockImplementation(() => new Promise(() => {})); // Never resolves

      render(<ModelTrainingDashboard />);

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
      expect(screen.getByText(/Загрузка/i)).toBeInTheDocument();
    });

    it('should render dashboard after successful data fetch', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth }) // health
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus }) // skill_matching status
        .mockResolvedValueOnce({ data: mockRankingStatus }) // ranking status
        .mockResolvedValueOnce({ data: { metrics: mockRecentMetrics } }) // metrics
        .mockResolvedValueOnce({ data: null }) // pause status (not paused)
        .mockResolvedValueOnce({ data: mockPerformanceTrends }); // trends

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Обучение моделей')).toBeInTheDocument();
      });

      expect(screen.getByText('СОСТОЯНИЕ ПАЙПЛАЙНА')).toBeInTheDocument();
      expect(screen.getByText('Всего моделей')).toBeInTheDocument();
    });

    it('should render no data state when health is null after fetch', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: null }) // health returns null
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText(/Нет данных/i)).toBeInTheDocument();
      });
    });
  });

  describe('Pipeline Health Display', () => {
    it('should display total models count', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('2')).toBeInTheDocument();
        expect(screen.getByText('Всего моделей')).toBeInTheDocument();
      });
    });

    it('should display active trainings count', async () => {
      const healthWithActiveTraining = {
        ...mockPipelineHealth,
        active_trainings: 1,
      };

      mockAxiosGet
        .mockResolvedValueOnce({ data: healthWithActiveTraining })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('1')).toBeInTheDocument();
        expect(screen.getByText('Активных')).toBeInTheDocument();
      });
    });

    it('should display completed trainings count', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('5')).toBeInTheDocument();
        expect(screen.getByText('Завершено')).toBeInTheDocument();
      });
    });

    it('should display failed trainings count', async () => {
      const healthWithFailures = {
        ...mockPipelineHealth,
        failed_trainings: 2,
      };

      mockAxiosGet
        .mockResolvedValueOnce({ data: healthWithFailures })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('2')).toBeInTheDocument();
        expect(screen.getByText('Ошибок')).toBeInTheDocument();
      });
    });

    it('should display healthy status correctly', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('OK')).toBeInTheDocument();
      });
    });

    it('should display degraded status correctly', async () => {
      const degradedHealth = {
        ...mockPipelineHealth,
        overall_health: 'degraded' as const,
      };

      mockAxiosGet
        .mockResolvedValueOnce({ data: degradedHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Внимание')).toBeInTheDocument();
      });
    });

    it('should display unhealthy status correctly', async () => {
      const unhealthyHealth = {
        ...mockPipelineHealth,
        overall_health: 'unhealthy' as const,
      };

      mockAxiosGet
        .mockResolvedValueOnce({ data: unhealthyHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Ошибка')).toBeInTheDocument();
      });
    });
  });

  describe('Model Selection', () => {
    it('should render model selector with both options', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByLabelText('Модель')).toBeInTheDocument();
      });

      // Open the select dropdown
      fireEvent.mouseDown(screen.getByLabelText('Модель'));

      await waitFor(() => {
        expect(screen.getByText('Skill Matching')).toBeInTheDocument();
        expect(screen.getByText('Ranking')).toBeInTheDocument();
      });
    });

    it('should switch selected model when clicking option', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Обучение моделей')).toBeInTheDocument();
      });

      // Open select and select ranking
      fireEvent.mouseDown(screen.getByLabelText('Модель'));
      await waitFor(() => {
        expect(screen.getByText('Ranking')).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText('Ranking'));

      // Should show RANKING in the training status section
      await waitFor(() => {
        expect(screen.getByText('RANKING - ПОСЛЕДНЕЕ ОБУЧЕНИЕ')).toBeInTheDocument();
      });
    });
  });

  describe('Training Status Display', () => {
    it('should display training status for selected model', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('SKILL MATCHING - ПОСЛЕДНЕЕ ОБУЧЕНИЕ')).toBeInTheDocument();
      });
    });

    it('should display completed training status', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Завершено')).toBeInTheDocument();
      });
    });

    it('should display in_progress training status', async () => {
      const inProgressStatus = {
        ...mockSkillMatchingStatus,
        training_status: 'in_progress',
      };

      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: inProgressStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('В процессе')).toBeInTheDocument();
        expect(screen.getByText('Обучение в процессе...')).toBeInTheDocument();
      });
    });

    it('should display failed training status', async () => {
      const failedStatus = {
        ...mockSkillMatchingStatus,
        training_status: 'failed',
        error_message: 'Training failed due to data issues',
      };

      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: failedStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Ошибка')).toBeInTheDocument();
        expect(screen.getByText(/Training failed due to data issues/)).toBeInTheDocument();
      });
    });

    it('should display model version chip', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('v1.0.0')).toBeInTheDocument();
      });
    });

    it('should display training metrics', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('85%')).toBeInTheDocument(); // Accuracy
        expect(screen.getByText('Точность')).toBeInTheDocument();
      });
    });

    it('should display training duration', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('120s')).toBeInTheDocument();
      });
    });
  });

  describe('Performance Trends Display', () => {
    it('should display performance trends section', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('ТРЕНДЫ ПРОИЗВОДИТЕЛЬНОСТИ')).toBeInTheDocument();
      });
    });

    it('should display current metrics summary cards', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Accuracy')).toBeInTheDocument();
        expect(screen.getByText('Precision')).toBeInTheDocument();
        expect(screen.getByText('Recall')).toBeInTheDocument();
        expect(screen.getByText('F1 Score')).toBeInTheDocument();
      });
    });

    it('should display trend direction chip', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Улучшается')).toBeInTheDocument();
      });
    });

    it('should display declining trend correctly', async () => {
      const decliningTrends = {
        ...mockPerformanceTrends,
        trend_direction: 'declining' as const,
      };

      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: decliningTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Ухудшается')).toBeInTheDocument();
      });
    });

    it('should display stable trend correctly', async () => {
      const stableTrends = {
        ...mockPerformanceTrends,
        trend_direction: 'stable' as const,
      };

      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: stableTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Стабильно')).toBeInTheDocument();
      });
    });

    it('should display health score progress bar', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('85%')).toBeInTheDocument();
      });
    });

    it('should display alert status when not none', async () => {
      const warningTrends = {
        ...mockPerformanceTrends,
        alert_status: 'warning' as const,
      };

      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: warningTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText(/Обнаружено снижение производительности/)).toBeInTheDocument();
      });
    });

    it('should display critical alert status', async () => {
      const criticalTrends = {
        ...mockPerformanceTrends,
        alert_status: 'critical' as const,
      };

      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: criticalTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText(/Критическое снижение производительности/)).toBeInTheDocument();
      });
    });
  });

  describe('Pause/Resume Functionality', () => {
    it('should display auto-training switch', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null }) // Not paused
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Автообучение:')).toBeInTheDocument();
      });
    });

    it('should show switch as checked when not paused', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null }) // Not paused
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        const switchElement = screen.getByRole('checkbox');
        expect(switchElement).toBeChecked();
      });
    });

    it('should show switch as unchecked when paused', async () => {
      const pausedStatus = {
        id: 'pause-1',
        model_name: 'global',
        paused: true,
        pause_reason: 'Manual pause via dashboard',
        paused_by: 'admin',
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:00:00Z',
      };

      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: pausedStatus })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        const switchElement = screen.getByRole('checkbox');
        expect(switchElement).not.toBeChecked();
      });
    });

    it('should display pause notice when paused', async () => {
      const pausedStatus = {
        id: 'pause-1',
        model_name: 'global',
        paused: true,
        pause_reason: 'Manual pause via dashboard',
        paused_by: 'admin',
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:00:00Z',
      };

      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: pausedStatus })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText(/Автоматическое обучение приостановлено/)).toBeInTheDocument();
      });
    });

    it('should call resume API when toggling from paused', async () => {
      const pausedStatus = {
        id: 'pause-1',
        model_name: 'global',
        paused: true,
        pause_reason: 'Manual pause via dashboard',
        paused_by: 'admin',
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:00:00Z',
      };

      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: pausedStatus })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      mockAxiosPost.mockResolvedValueOnce({ data: {} });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Обучение моделей')).toBeInTheDocument();
      });

      const switchElement = screen.getByRole('checkbox');
      fireEvent.click(switchElement);

      await waitFor(() => {
        expect(mockAxiosPost).toHaveBeenCalledWith(
          '/api/training-pipeline/config/resume',
          { model_name: 'global' }
        );
      });
    });

    it('should call pause API when toggling from not paused', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null }) // Not paused
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      mockAxiosPost.mockResolvedValueOnce({ data: {} });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Обучение моделей')).toBeInTheDocument();
      });

      const switchElement = screen.getByRole('checkbox');
      fireEvent.click(switchElement);

      await waitFor(() => {
        expect(mockAxiosPost).toHaveBeenCalledWith(
          '/api/training-pipeline/config/pause',
          {
            model_name: 'global',
            reason: 'Manual pause via dashboard',
          }
        );
      });
    });
  });

  describe('Manual Retrain Functionality', () => {
    it('should display retrain button', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Запустить обучение')).toBeInTheDocument();
      });
    });

    it('should disable retrain button when training is in progress', async () => {
      const inProgressStatus = {
        ...mockSkillMatchingStatus,
        training_status: 'in_progress',
      };

      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: inProgressStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        const retrainButton = screen.getByText('Запустить обучение').closest('button');
        expect(retrainButton).toBeDisabled();
      });
    });

    it('should call retrain API when button is clicked', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      mockAxiosPost.mockResolvedValueOnce({ data: {} });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Обучение моделей')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Запустить обучение'));

      await waitFor(() => {
        expect(mockAxiosPost).toHaveBeenCalledWith(
          '/api/model-versions/retrain',
          { model_name: 'skill_matching' }
        );
      });
    });
  });

  describe('Refresh Functionality', () => {
    it('should display refresh button', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Обновить')).toBeInTheDocument();
      });
    });

    it('should refetch data when refresh button is clicked', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Обучение моделей')).toBeInTheDocument();
      });

      // Clear call counts after initial render
      const initialCallCount = mockAxiosGet.mock.calls.length;

      // Click refresh
      fireEvent.click(screen.getByText('Обновить'));

      await waitFor(() => {
        // Should have made additional API calls
        expect(mockAxiosGet.mock.calls.length).toBeGreaterThan(initialCallCount);
      });
    });
  });

  describe('Recent Events Display', () => {
    it('should display recent training events', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: mockRecentMetrics } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('ПОСЛЕДНИЕ СОБЫТИЯ')).toBeInTheDocument();
      });
    });

    it('should display event details', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: mockRecentMetrics } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('skill_matching - v1.0.0')).toBeInTheDocument();
      });
    });

    it('should not display recent events section when no events', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Обучение моделей')).toBeInTheDocument();
      });

      expect(screen.queryByText('ПОСЛЕДНИЕ СОБЫТИЯ')).not.toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should display error alert when error state is set', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      mockAxiosPost.mockRejectedValueOnce(new Error('Retrain failed'));

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Обучение моделей')).toBeInTheDocument();
      });

      // Trigger an error by clicking retrain
      fireEvent.click(screen.getByText('Запустить обучение'));

      await waitFor(() => {
        expect(screen.getByText('Retrain failed')).toBeInTheDocument();
      });
    });

    it('should clear error when alert is closed', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      mockAxiosPost.mockRejectedValueOnce(new Error('Test error'));

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Обучение моделей')).toBeInTheDocument();
      });

      // Trigger error
      fireEvent.click(screen.getByText('Запустить обучение'));

      await waitFor(() => {
        expect(screen.getByText('Test error')).toBeInTheDocument();
      });

      // Close alert
      const closeButton = screen.getByLabelText('Close');
      fireEvent.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByText('Test error')).not.toBeInTheDocument();
      });
    });

    it('should handle API errors gracefully', async () => {
      mockAxiosGet
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      // Component should still render something, even with errors
      await waitFor(() => {
        expect(mockAxiosGet).toHaveBeenCalled();
      });
    });
  });

  describe('Fallback Mock Data', () => {
    it('should use mock data when performance trends API fails', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockRejectedValueOnce(new Error('Trends API unavailable'));

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByText('ТРЕНДЫ ПРОИЗВОДИТЕЛЬНОСТИ')).toBeInTheDocument();
        // Should display mock data (85% accuracy)
        expect(screen.getByText('85.0%')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper form controls', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByLabelText('Модель')).toBeInTheDocument();
      });

      // Check for switch element
      expect(screen.getByRole('checkbox')).toBeInTheDocument();
    });

    it('should have accessible buttons', async () => {
      mockAxiosGet
        .mockResolvedValueOnce({ data: mockPipelineHealth })
        .mockResolvedValueOnce({ data: mockSkillMatchingStatus })
        .mockResolvedValueOnce({ data: mockRankingStatus })
        .mockResolvedValueOnce({ data: { metrics: [] } })
        .mockResolvedValueOnce({ data: null })
        .mockResolvedValueOnce({ data: mockPerformanceTrends });

      render(<ModelTrainingDashboard />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Обновить/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Запустить обучение/i })).toBeInTheDocument();
      });
    });
  });
});
