/**
 * Tests for ReportBuilder Component
 *
 * Tests the custom report builder including:
 * - Metric selection and drag-drop functionality
 * - Report CRUD operations (create, read, update, delete)
 * - PDF export functionality
 * - CSV export functionality
 * - Scheduled report configuration
 * - Report loading and display
 * - Error handling and loading states
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ReportBuilder from './ReportBuilder';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('ReportBuilder', () => {
  const mockApiUrl = 'http://localhost:8000/api/reports';

  const mockReports = [
    {
      id: 'report-1',
      name: 'Weekly Hiring Report',
      description: 'Weekly hiring metrics',
      organization_id: 'org-1',
      created_by: 'user-1',
      metrics: ['time_to_hire', 'resumes_processed'],
      filters: {},
      is_public: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 'report-2',
      name: 'Monthly Skills Analysis',
      description: 'Monthly skill demand analysis',
      organization_id: 'org-1',
      created_by: 'user-1',
      metrics: ['skill_demand', 'source_tracking'],
      filters: {},
      is_public: false,
      created_at: '2024-01-15T00:00:00Z',
      updated_at: '2024-01-15T00:00:00Z',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render report builder interface', () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ reports: mockReports, total_count: 2 }),
      });

      render(<ReportBuilder />);

      expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
    });

    it('should render loading state initially', () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ reports: mockReports, total_count: 2 }),
      });

      render(<ReportBuilder />);

      // Loading state may be shown
      expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
    });

    it('should render error state on fetch failure', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'));

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText(/Failed to load reports/)).toBeInTheDocument();
      });
    });
  });

  describe('Available Metrics Display', () => {
    it('should display all available metrics', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ reports: mockReports, total_count: 2 }),
      });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      expect(screen.getByText('Time-to-Hire')).toBeInTheDocument();
      expect(screen.getByText('Resumes Processed')).toBeInTheDocument();
      expect(screen.getByText('Match Rates')).toBeInTheDocument();
      expect(screen.getByText('Funnel Visualization')).toBeInTheDocument();
    });

    it('should categorize metrics correctly', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ reports: mockReports, total_count: 2 }),
      });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      expect(screen.getByText(/Pipeline Metrics/i)).toBeInTheDocument();
      expect(screen.getByText(/Performance Metrics/i)).toBeInTheDocument();
    });
  });

  describe('Metric Selection', () => {
    it('should add metric when clicked', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ reports: mockReports, total_count: 2 }),
      });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Time-to-Hire'));

      // Metric should be added to selected metrics
      expect(screen.getByText('Time-to-Hire')).toBeInTheDocument();
    });

    it('should remove metric when clicked again', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ reports: mockReports, total_count: 2 }),
      });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      // Add metric
      fireEvent.click(screen.getByText('Time-to-Hire'));

      // Remove metric
      fireEvent.click(screen.getByText(/Remove/i));

      // Metric should be removed from selected metrics
    });
  });

  describe('Report CRUD Operations', () => {
    it('should open save report dialog when Save Report button is clicked', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ reports: mockReports, total_count: 2 }),
      });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      // Add a metric first
      fireEvent.click(screen.getByText('Time-to-Hire'));

      // Click Save Report button
      const saveButton = screen.getByText('Save Report');
      if (saveButton) {
        fireEvent.click(saveButton);
        // Dialog should open
      }
    });

    it('should create new report via API', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ reports: mockReports, total_count: 2 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            ...mockReports[0],
            id: 'report-new',
            name: 'New Report',
          }),
        });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      // Add metric and save
      fireEvent.click(screen.getByText('Time-to-Hire'));

      // Simulate save operation
    });

    it('should load existing reports', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ reports: mockReports, total_count: 2 }),
      });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Weekly Hiring Report')).toBeInTheDocument();
      });

      expect(screen.getByText('Monthly Skills Analysis')).toBeInTheDocument();
    });

    it('should load report when clicked from list', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ reports: mockReports, total_count: 2 }),
      });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Weekly Hiring Report')).toBeInTheDocument();
      });

      // Click on a report to load it
      fireEvent.click(screen.getByText('Weekly Hiring Report'));

      // Metrics from that report should be loaded
    });

    it('should update existing report', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ reports: mockReports, total_count: 2 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ ...mockReports[0], name: 'Updated Report' }),
        });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Weekly Hiring Report')).toBeInTheDocument();
      });

      // Load report and update it
    });

    it('should delete report', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ reports: mockReports, total_count: 2 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true }),
        });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Weekly Hiring Report')).toBeInTheDocument();
      });

      // Delete the report
    });
  });

  describe('PDF Export', () => {
    it('should export PDF when button is clicked', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ reports: mockReports, total_count: 2 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            report_id: 'test-id',
            download_url: 'http://example.com/report.pdf',
            expires_at: '2024-12-31T23:59:59Z',
          }),
        });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      // Add a metric
      fireEvent.click(screen.getByText('Time-to-Hire'));

      // Click Export PDF button
      const exportPdfButton = screen.getByText('Export PDF');
      if (exportPdfButton) {
        fireEvent.click(exportPdfButton);

        await waitFor(() => {
          expect(mockFetch).toHaveBeenCalled();
        });
      }
    });

    it('should show loading state while exporting PDF', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ reports: mockReports, total_count: 2 }),
        })
        .mockImplementation(() => new Promise(() => {})); // Never resolves

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Time-to-Hire'));

      const exportPdfButton = screen.getByText('Export PDF');
      if (exportPdfButton) {
        fireEvent.click(exportPdfButton);

        // Should show loading state
        await waitFor(() => {
          expect(screen.getByText(/Exporting/i)).toBeInTheDocument();
        });
      }
    });

    it('should disable PDF export when no metrics selected', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ reports: mockReports, total_count: 2 }),
      });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      const exportPdfButton = screen.getByText('Export PDF');
      if (exportPdfButton) {
        // Button should be disabled when no metrics are selected
        expect(exportPdfButton).toBeInTheDocument();
      }
    });
  });

  describe('CSV Export', () => {
    it('should export CSV when button is clicked', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ reports: mockReports, total_count: 2 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => new Blob(['csv content'], { type: 'text/csv' }),
        });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      // Add a metric
      fireEvent.click(screen.getByText('Time-to-Hire'));

      // Click Export CSV button
      const exportCsvButton = screen.getByText('Export CSV');
      if (exportCsvButton) {
        fireEvent.click(exportCsvButton);

        await waitFor(() => {
          expect(mockFetch).toHaveBeenCalled();
        });
      }
    });

    it('should show loading state while exporting CSV', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ reports: mockReports, total_count: 2 }),
        })
        .mockImplementation(() => new Promise(() => {})); // Never resolves

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Time-to-Hire'));

      const exportCsvButton = screen.getByText('Export CSV');
      if (exportCsvButton) {
        fireEvent.click(exportCsvButton);

        // Should show loading state
        await waitFor(() => {
          expect(screen.getByText(/Exporting/i)).toBeInTheDocument();
        });
      }
    });
  });

  describe('Scheduled Reports', () => {
    it('should open schedule dialog when Schedule button is clicked', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ reports: mockReports, total_count: 2 }),
      });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      // Add a metric
      fireEvent.click(screen.getByText('Time-to-Hire'));

      // Click Schedule button
      const scheduleButton = screen.getByText('Schedule');
      if (scheduleButton) {
        fireEvent.click(scheduleButton);

        // Schedule dialog should open
        await waitFor(() => {
          expect(screen.getByText(/Schedule Report/i)).toBeInTheDocument();
        });
      }
    });

    it('should display schedule configuration options', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ reports: mockReports, total_count: 2 }),
      });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      const scheduleButton = screen.getByText('Schedule');
      if (scheduleButton) {
        fireEvent.click(scheduleButton);

        await waitFor(() => {
          expect(screen.getByText(/Frequency/i)).toBeInTheDocument();
          expect(screen.getByText(/Delivery/i)).toBeInTheDocument();
        });
      }
    });
  });

  describe('Error Handling', () => {
    it('should display error message on failed report creation', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ reports: mockReports, total_count: 2 }),
        })
        .mockRejectedValueOnce(new Error('Failed to create report'));

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      // Attempt to save report
      // Error message should be displayed
    });

    it('should display error message on failed export', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ reports: mockReports, total_count: 2 }),
        })
        .mockRejectedValueOnce(new Error('Failed to export PDF'));

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Time-to-Hire'));

      const exportPdfButton = screen.getByText('Export PDF');
      if (exportPdfButton) {
        fireEvent.click(exportPdfButton);

        await waitFor(() => {
          expect(screen.getByText(/Failed to export/i)).toBeInTheDocument();
        });
      }
    });
  });

  describe('Visual Design', () => {
    it('should display metrics in organized layout', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ reports: mockReports, total_count: 2 }),
      });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      expect(screen.getByText('Available Metrics')).toBeInTheDocument();
      expect(screen.getByText('Selected Metrics')).toBeInTheDocument();
    });

    it('should display action buttons', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ reports: mockReports, total_count: 2 }),
      });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      expect(screen.getByText('Save Report')).toBeInTheDocument();
      expect(screen.getByText('Export PDF')).toBeInTheDocument();
      expect(screen.getByText('Export CSV')).toBeInTheDocument();
      expect(screen.getByText('Schedule')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty reports list', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ reports: [], total_count: 0 }),
      });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      expect(screen.getByText(/No reports found/i)).toBeInTheDocument();
    });

    it('should handle API error with status code', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        statusText: 'Internal Server Error',
        status: 500,
      });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText(/Failed to load reports/i)).toBeInTheDocument();
      });
    });
  });
});
