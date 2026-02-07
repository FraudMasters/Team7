/**
 * Health Dashboard Component Integration Tests
 *
 * Tests for verifying the frontend health dashboard shows correct status
 * for all services as specified in subtask-6-6.
 *
 * Run with: npm test -- HealthDashboard.test.tsx
 */

import { render, screen, waitFor, within } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import HealthDashboard from '@/pages/HealthDashboard';
import * as healthApi from '@/api/health';

// Mock the health API module
vi.mock('@/api/health', () => ({
  getDetailedHealth: vi.fn(),
  getDependencyGraph: vi.fn(),
  getHealthCheckResult: vi.fn(),
}));

// Mock translations
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

// Test wrapper with QueryClient
const createTestWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('HealthDashboard - Service Status Display', () => {
  const mockHealthData = {
    status: 'healthy' as const,
    timestamp: '2026-02-07T12:00:00Z',
    service: 'backend',
    version: '1.0.0',
    overall_health_percentage: 100,
    critical_issues: [],
    warnings: [],
    checks: {
      database: {
        status: 'healthy' as const,
        essential: true,
        category: 'infrastructure',
        response_time_ms: 15,
        details: { connected: true },
        error: null,
        last_check: '2026-02-07T12:00:00Z',
      },
      redis: {
        status: 'healthy' as const,
        essential: true,
        category: 'messaging',
        response_time_ms: 5,
        details: { connected: true, key_count: 100 },
        error: null,
        last_check: '2026-02-07T12:00:00Z',
      },
      celery: {
        status: 'healthy' as const,
        essential: true,
        category: 'messaging',
        response_time_ms: 50,
        details: { worker_name: 'celery@worker' },
        error: null,
        last_check: '2026-02-07T12:00:00Z',
      },
      ml_ner_model: {
        status: 'healthy' as const,
        essential: false,
        category: 'ml',
        response_time_ms: null,
        details: { models_loaded: ['ner'] },
        error: null,
        last_check: '2026-02-07T12:00:00Z',
      },
      ml_zero_shot_model: {
        status: 'degraded' as const,
        essential: false,
        category: 'ml',
        response_time_ms: null,
        details: { models_loaded: [] },
        error: null,
        last_check: '2026-02-07T12:00:00Z',
      },
      ml_language_tools: {
        status: 'healthy' as const,
        essential: false,
        category: 'ml',
        response_time_ms: null,
        details: { models_loaded: ['language_tools'] },
        error: null,
        last_check: '2026-02-07T12:00:00Z',
      },
      external_api: {
        status: 'healthy' as const,
        essential: false,
        category: 'external',
        response_time_ms: 150,
        details: { apis_available: ['languagetool'] },
        error: null,
        last_check: '2026-02-07T12:00:00Z',
      },
    },
  };

  const mockDependencyData = {
    services: {
      database: {
        name: 'database',
        display_name: 'Database',
        description: 'PostgreSQL database',
        essential: true,
        category: 'infrastructure',
        dependencies: [],
        dependents: ['backend_api'],
      },
      redis: {
        name: 'redis',
        display_name: 'Redis Cache',
        description: 'Redis cache server',
        essential: true,
        category: 'infrastructure',
        dependencies: [],
        dependents: ['celery_worker', 'backend_api'],
      },
      celery: {
        name: 'celery',
        display_name: 'Celery Workers',
        description: 'Celery task queue workers',
        essential: true,
        category: 'messaging',
        dependencies: ['redis'],
        dependents: ['backend_api'],
      },
    },
    summary: {
      total_services: 3,
      essential_services: 3,
      non_essential_services: 0,
      categories: {
        infrastructure: 2,
        messaging: 1,
      },
      services_with_most_dependents: ['redis'],
      services_with_most_dependencies: ['celery'],
      max_dependency_depth: 1,
      critical_path: ['celery', 'redis'],
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
    // Mock successful API responses
    vi.mocked(healthApi.getDetailedHealth).mockResolvedValue(mockHealthData);
    vi.mocked(healthApi.getDependencyGraph).mockResolvedValue(mockDependencyData);
  });

  describe('Service Status Indicators', () => {
    it('should render all expected service cards', async () => {
      const wrapper = createTestWrapper();
      render(<HealthDashboard />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('Database')).toBeInTheDocument();
        expect(screen.getByText('Redis Cache')).toBeInTheDocument();
        expect(screen.getByText('Celery Workers')).toBeInTheDocument();
        expect(screen.getByText('NER Model')).toBeInTheDocument();
        expect(screen.getByText('Zero-Shot Model')).toBeInTheDocument();
        expect(screen.getByText('Language Tools')).toBeInTheDocument();
        expect(screen.getByText('External APIs')).toBeInTheDocument();
      });
    });

    it('should display correct status colors for healthy services', async () => {
      const wrapper = createTestWrapper();
      render(<HealthDashboard />, { wrapper });

      await waitFor(() => {
        const healthyChips = screen.getAllByText('HEALTHY');
        expect(healthyChips.length).toBeGreaterThan(0);
      });
    });

    it('should display correct status colors for degraded services', async () => {
      const wrapper = createTestWrapper();
      render(<HealthDashboard />, { wrapper });

      await waitFor(() => {
        const degradedChips = screen.getAllByText('DEGRADED');
        expect(degradedChips.length).toBeGreaterThan(0);
      });
    });

    it('should display correct status colors for unhealthy services', async () => {
      const unhealthyData = {
        ...mockHealthData,
        status: 'unhealthy' as const,
        checks: {
          ...mockHealthData.checks,
          redis: {
            ...mockHealthData.checks.redis,
            status: 'unhealthy' as const,
            error: 'Connection refused',
          },
        },
      };
      vi.mocked(healthApi.getDetailedHealth).mockResolvedValue(unhealthyData);

      const wrapper = createTestWrapper();
      render(<HealthDashboard />, { wrapper });

      await waitFor(() => {
        const unhealthyChips = screen.getAllByText('UNHEALTHY');
        expect(unhealthyChips.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Service Details Display', () => {
    it('should show category for each service', async () => {
      const wrapper = createTestWrapper();
      render(<HealthDashboard />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('Infrastructure')).toBeInTheDocument();
        expect(screen.getByText('Messaging')).toBeInTheDocument();
        expect(screen.getByText('Machine Learning')).toBeInTheDocument();
      });
    });

    it('should show response time for services with metrics', async () => {
      const wrapper = createTestWrapper();
      render(<HealthDashboard />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText(/15ms/)).toBeInTheDocument();
        expect(screen.getByText(/5ms/)).toBeInTheDocument();
      });
    });

    it('should show essential service indicators', async () => {
      const wrapper = createTestWrapper();
      render(<HealthDashboard />, { wrapper });

      await waitFor(() => {
        const essentialChips = screen.getAllByText('Yes');
        expect(essentialChips.length).toBeGreaterThan(0);
      });
    });

    it('should display error messages for unhealthy services', async () => {
      const unhealthyData = {
        ...mockHealthData,
        checks: {
          ...mockHealthData.checks,
          redis: {
            ...mockHealthData.checks.redis,
            status: 'unhealthy' as const,
            error: 'Connection refused',
          },
        },
      };
      vi.mocked(healthApi.getDetailedHealth).mockResolvedValue(unhealthyData);

      const wrapper = createTestWrapper();
      render(<HealthDashboard />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('Connection refused')).toBeInTheDocument();
      });
    });
  });

  describe('Overall System Status', () => {
    it('should display overall system health percentage', async () => {
      const wrapper = createTestWrapper();
      render(<HealthDashboard />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText(/100%/)).toBeInTheDocument();
      });
    });

    it('should show critical issues when present', async () => {
      const criticalData = {
        ...mockHealthData,
        status: 'unhealthy' as const,
        critical_issues: ['Redis is unavailable'],
      };
      vi.mocked(healthApi.getDetailedHealth).mockResolvedValue(criticalData);

      const wrapper = createTestWrapper();
      render(<HealthDashboard />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('Critical Issues:')).toBeInTheDocument();
        expect(screen.getByText('Redis is unavailable')).toBeInTheDocument();
      });
    });

    it('should show warnings when present', async () => {
      const warningData = {
        ...mockHealthData,
        status: 'degraded' as const,
        warnings: ['ML model not loaded'],
      };
      vi.mocked(healthApi.getDetailedHealth).mockResolvedValue(warningData);

      const wrapper = createTestWrapper();
      render(<HealthDashboard />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText('Warnings:')).toBeInTheDocument();
        expect(screen.getByText('ML model not loaded')).toBeInTheDocument();
      });
    });
  });

  describe('Dependency Summary', () => {
    it('should display total services count', async () => {
      const wrapper = createTestWrapper();
      render(<HealthDashboard />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText(/Total Services/)).toBeInTheDocument();
        expect(screen.getByText('3')).toBeInTheDocument();
      });
    });

    it('should display essential services count', async () => {
      const wrapper = createTestWrapper();
      render(<HealthDashboard />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText(/Essential Services/)).toBeInTheDocument();
      });
    });

    it('should display max dependency depth', async () => {
      const wrapper = createTestWrapper();
      render(<HealthDashboard />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText(/Max Dependency Depth/)).toBeInTheDocument();
      });
    });

    it('should display critical path', async () => {
      const wrapper = createTestWrapper();
      render(<HealthDashboard />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText(/Critical Path/)).toBeInTheDocument();
      });
    });
  });

  describe('Refresh Functionality', () => {
    it('should have a refresh button', async () => {
      const wrapper = createTestWrapper();
      render(<HealthDashboard />, { wrapper });

      await waitFor(() => {
        const refreshButton = screen.getByRole('button', { name: /refresh/i });
        expect(refreshButton).toBeInTheDocument();
      });
    });

    it('should display last refresh timestamp', async () => {
      const wrapper = createTestWrapper();
      render(<HealthDashboard />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
      });
    });

    it('should refetch data when refresh button is clicked', async () => {
      const wrapper = createTestWrapper();
      render(<HealthDashboard />, { wrapper });

      await waitFor(() => {
        expect(healthApi.getDetailedHealth).toHaveBeenCalled();
      });

      const callCountBefore = vi.mocked(healthApi.getDetailedHealth).mock.calls.length;

      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      refreshButton.click();

      await waitFor(() => {
        expect(vi.mocked(healthApi.getDetailedHealth).mock.calls.length).toBeGreaterThan(callCountBefore);
      });
    });
  });

  describe('Loading and Error States', () => {
    it('should show loading state initially', () => {
      vi.mocked(healthApi.getDetailedHealth).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      const wrapper = createTestWrapper();
      render(<HealthDashboard />, { wrapper });

      expect(screen.getByText(/Loading health status/i)).toBeInTheDocument();
    });

    it('should show error state on API failure', async () => {
      vi.mocked(healthApi.getDetailedHealth).mockRejectedValue(
        new Error('Failed to fetch')
      );

      const wrapper = createTestWrapper();
      render(<HealthDashboard />, { wrapper });

      await waitFor(() => {
        expect(screen.getByText(/Failed to fetch health data/i)).toBeInTheDocument();
      });
    });
  });
});
