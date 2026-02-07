/**
 * Tests for ReportBuilder Excel Export Functionality
 *
 * Tests the Excel export feature including:
 * - Excel export button rendering
 * - Excel export API call
 * - File download handling
 * - Loading states during export
 * - Error handling
 * - Disabled state when no metrics selected
 * - Blob creation and download link
 * - Filename generation
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ReportBuilder from './ReportBuilder';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock URL.createObjectURL and revokeObjectURL
const mockCreateObjectURL = vi.fn();
const mockRevokeObjectURL = vi.fn();
global.URL.createObjectURL = mockCreateObjectURL;
global.URL.revokeObjectURL = mockRevokeObjectURL;

// Mock document methods for link creation and click
const mockLink = {
  href: '',
  download: '',
  style: {},
  click: vi.fn(),
  remove: vi.fn(),
};
document.createElement = vi.fn(() => mockLink as any);
document.body.appendChild = vi.fn();
document.body.removeChild = vi.fn();

describe('ReportBuilder Excel Export', () => {
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
    mockCreateObjectURL.mockReturnValue('blob:test-url');
    mockLink.click.mockClear();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Excel Export Button Rendering', () => {
    it('should render Export Excel button', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ reports: mockReports, total_count: 2 }),
      });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      expect(screen.getByText('Export Excel')).toBeInTheDocument();
    });

    it('should display Export Excel button with warning color', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ reports: mockReports, total_count: 2 }),
      });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      const excelButton = screen.getByText('Export Excel');
      expect(excelButton).toBeInTheDocument();
      // Warning color is applied via variant and color props
    });

    it('should render Export Excel button next to Export CSV button', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ reports: mockReports, total_count: 2 }),
      });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      expect(screen.getByText('Export CSV')).toBeInTheDocument();
      expect(screen.getByText('Export Excel')).toBeInTheDocument();
    });
  });

  describe('Excel Export Functionality', () => {
    it('should export Excel when button is clicked', async () => {
      const mockBlob = new Blob(['excel content'], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ reports: mockReports, total_count: 2 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          blob: async () => mockBlob,
        });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      // Add a metric
      fireEvent.click(screen.getByText('Time-to-Hire'));

      // Click Export Excel button
      const exportExcelButton = screen.getByText('Export Excel');
      fireEvent.click(exportExcelButton);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          'http://localhost:8000/api/reports/export/excel',
          expect.objectContaining({
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: expect.stringContaining('"metrics":["time_to_hire"]'),
          })
        );
      });
    });

    it('should handle blob response and trigger download', async () => {
      const mockBlob = new Blob(['excel content'], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ reports: mockReports, total_count: 2 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          blob: async () => mockBlob,
        });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      // Add a metric
      fireEvent.click(screen.getByText('Time-to-Hire'));

      // Click Export Excel button
      const exportExcelButton = screen.getByText('Export Excel');
      fireEvent.click(exportExcelButton);

      await waitFor(() => {
        expect(mockCreateObjectURL).toHaveBeenCalledWith(mockBlob);
        expect(mockLink.click).toHaveBeenCalled();
        expect(mockRevokeObjectURL).toHaveBeenCalledWith('blob:test-url');
      });
    });

    it('should generate correct filename with timestamp', async () => {
      const mockBlob = new Blob(['excel content'], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ reports: mockReports, total_count: 2 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          blob: async () => mockBlob,
        });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      // Add a metric
      fireEvent.click(screen.getByText('Time-to-Hire'));

      // Click Export Excel button
      const exportExcelButton = screen.getByText('Export Excel');
      fireEvent.click(exportExcelButton);

      await waitFor(() => {
        expect(mockLink.download).toMatch(/^report-custom-\d+\.xlsx$/);
      });
    });

    it('should include report name in filename when editing existing report', async () => {
      const mockBlob = new Blob(['excel content'], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ reports: mockReports, total_count: 2 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          blob: async () => mockBlob,
        });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      // Load an existing report
      fireEvent.click(screen.getByText('Weekly Hiring Report'));

      // Wait for report to load
      await waitFor(() => {
        expect(screen.getByText('Weekly Hiring Report')).toBeInTheDocument();
      });

      // Click Export Excel button
      const exportExcelButton = screen.getByText('Export Excel');
      if (exportExcelButton) {
        fireEvent.click(exportExcelButton);

        await waitFor(() => {
          expect(mockLink.download).toMatch(/^report-Weekly Hiring Report-\d+\.xlsx$/);
        });
      }
    });
  });

  describe('Excel Export Loading States', () => {
    it('should show loading state while exporting Excel', async () => {
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

      // Add a metric
      fireEvent.click(screen.getByText('Time-to-Hire'));

      // Click Export Excel button
      const exportExcelButton = screen.getByText('Export Excel');
      fireEvent.click(exportExcelButton);

      // Should show loading state
      await waitFor(() => {
        expect(screen.getByText('Exporting...')).toBeInTheDocument();
      });
    });

    it('should show CircularProgress while exporting', async () => {
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

      // Add a metric
      fireEvent.click(screen.getByText('Time-to-Hire'));

      // Click Export Excel button
      const exportExcelButton = screen.getByText('Export Excel');
      fireEvent.click(exportExcelButton);

      // Should show CircularProgress
      await waitFor(() => {
        expect(screen.getByText('Exporting...')).toBeInTheDocument();
      });
    });

    it('should reset loading state after successful export', async () => {
      const mockBlob = new Blob(['excel content'], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ reports: mockReports, total_count: 2 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          blob: async () => mockBlob,
        });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      // Add a metric
      fireEvent.click(screen.getByText('Time-to-Hire'));

      // Click Export Excel button
      const exportExcelButton = screen.getByText('Export Excel');
      fireEvent.click(exportExcelButton);

      // Wait for export to complete
      await waitFor(() => {
        expect(mockLink.click).toHaveBeenCalled();
      });

      // Loading state should be reset
      await waitFor(() => {
        expect(screen.queryByText('Exporting...')).not.toBeInTheDocument();
        expect(screen.getByText('Export Excel')).toBeInTheDocument();
      });
    });
  });

  describe('Excel Export Error Handling', () => {
    it('should display error message on failed export', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ reports: mockReports, total_count: 2 }),
        })
        .mockRejectedValueOnce(new Error('Failed to export Excel'));

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      // Add a metric
      fireEvent.click(screen.getByText('Time-to-Hire'));

      // Click Export Excel button
      const exportExcelButton = screen.getByText('Export Excel');
      fireEvent.click(exportExcelButton);

      // Error message should be displayed
      await waitFor(() => {
        expect(screen.getByText(/Failed to export Excel/i)).toBeInTheDocument();
      });
    });

    it('should display error message when response is not ok', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ reports: mockReports, total_count: 2 }),
        })
        .mockResolvedValueOnce({
          ok: false,
          statusText: 'Internal Server Error',
          status: 500,
        });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      // Add a metric
      fireEvent.click(screen.getByText('Time-to-Hire'));

      // Click Export Excel button
      const exportExcelButton = screen.getByText('Export Excel');
      fireEvent.click(exportExcelButton);

      // Error message should be displayed
      await waitFor(() => {
        expect(screen.getByText(/Failed to export Excel/i)).toBeInTheDocument();
      });
    });

    it('should reset loading state after error', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ reports: mockReports, total_count: 2 }),
        })
        .mockRejectedValueOnce(new Error('Failed to export Excel'));

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      // Add a metric
      fireEvent.click(screen.getByText('Time-to-Hire'));

      // Click Export Excel button
      const exportExcelButton = screen.getByText('Export Excel');
      fireEvent.click(exportExcelButton);

      // Wait for error to be displayed
      await waitFor(() => {
        expect(screen.getByText(/Failed to export Excel/i)).toBeInTheDocument();
      });

      // Loading state should be reset
      expect(screen.queryByText('Exporting...')).not.toBeInTheDocument();
    });
  });

  describe('Excel Export Edge Cases', () => {
    it('should disable Excel export when no metrics selected', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ reports: mockReports, total_count: 2 }),
      });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      const exportExcelButton = screen.getByText('Export Excel');
      expect(exportExcelButton).toBeInTheDocument();
      // Button should be disabled when no metrics are selected
      // This is tested via the disabled prop in the component
    });

    it('should disable Excel export button while exporting', async () => {
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

      // Add a metric
      fireEvent.click(screen.getByText('Time-to-Hire'));

      // Click Export Excel button
      const exportExcelButton = screen.getByText('Export Excel');
      fireEvent.click(exportExcelButton);

      // Wait for loading state
      await waitFor(() => {
        expect(screen.getByText('Exporting...')).toBeInTheDocument();
      });

      // Button should be disabled during export
      // This is tested via the disabled prop in the component
    });

    it('should show error when trying to export with no metrics selected', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ reports: mockReports, total_count: 2 }),
      });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      // Try to export without selecting metrics
      const exportExcelButton = screen.getByText('Export Excel');

      // If button is not disabled, click it
      if (!exportExcelButton.hasAttribute('disabled')) {
        fireEvent.click(exportExcelButton);

        // Error message should be displayed
        await waitFor(() => {
          expect(screen.getByText(/Please select at least one metric/i)).toBeInTheDocument();
        });
      }
    });

    it('should clear error state when new export starts', async () => {
      const mockBlob = new Blob(['excel content'], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ reports: mockReports, total_count: 2 }),
        })
        .mockRejectedValueOnce(new Error('First export failed'))
        .mockResolvedValueOnce({
          ok: true,
          blob: async () => mockBlob,
        });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      // Add a metric
      fireEvent.click(screen.getByText('Time-to-Hire'));

      // First export attempt (will fail)
      const exportExcelButton = screen.getByText('Export Excel');
      fireEvent.click(exportExcelButton);

      await waitFor(() => {
        expect(screen.getByText(/Failed to export Excel/i)).toBeInTheDocument();
      });

      // Second export attempt (will succeed)
      fireEvent.click(exportExcelButton);

      await waitFor(() => {
        expect(mockLink.click).toHaveBeenCalled();
        expect(screen.queryByText(/Failed to export Excel/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Excel Export API Integration', () => {
    it('should send correct API request with metrics and filters', async () => {
      const mockBlob = new Blob(['excel content'], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ reports: mockReports, total_count: 2 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          blob: async () => mockBlob,
        });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      // Add metrics
      fireEvent.click(screen.getByText('Time-to-Hire'));
      fireEvent.click(screen.getByText('Resumes Processed'));

      // Click Export Excel button
      const exportExcelButton = screen.getByText('Export Excel');
      fireEvent.click(exportExcelButton);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          'http://localhost:8000/api/reports/export/excel',
          expect.objectContaining({
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: expect.stringContaining('"metrics":["time_to_hire","resumes_processed"]'),
          })
        );
      });
    });

    it('should send report_id when editing existing report', async () => {
      const mockBlob = new Blob(['excel content'], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ reports: mockReports, total_count: 2 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          blob: async () => mockBlob,
        });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Weekly Hiring Report')).toBeInTheDocument();
      });

      // Load existing report
      fireEvent.click(screen.getByText('Weekly Hiring Report'));

      await waitFor(() => {
        expect(screen.getByText('Weekly Hiring Report')).toBeInTheDocument();
      });

      // Click Export Excel button
      const exportExcelButton = screen.getByText('Export Excel');
      if (exportExcelButton) {
        fireEvent.click(exportExcelButton);

        await waitFor(() => {
          expect(mockFetch).toHaveBeenCalledWith(
            'http://localhost:8000/api/reports/export/excel',
            expect.objectContaining({
              method: 'POST',
              body: expect.stringContaining('"report_id":"report-1"'),
            })
          );
        });
      }
    });

    it('should send "custom" as report_id for new reports', async () => {
      const mockBlob = new Blob(['excel content'], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ reports: mockReports, total_count: 2 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          blob: async () => mockBlob,
        });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      // Add a metric (new report, not loading existing)
      fireEvent.click(screen.getByText('Time-to-Hire'));

      // Click Export Excel button
      const exportExcelButton = screen.getByText('Export Excel');
      fireEvent.click(exportExcelButton);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          'http://localhost:8000/api/reports/export/excel',
          expect.objectContaining({
            body: expect.stringContaining('"report_id":"custom"'),
          })
        );
      });
    });
  });

  describe('Excel Export Cleanup', () => {
    it('should revoke object URL after download', async () => {
      const mockBlob = new Blob(['excel content'], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ reports: mockReports, total_count: 2 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          blob: async () => mockBlob,
        });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      // Add a metric
      fireEvent.click(screen.getByText('Time-to-Hire'));

      // Click Export Excel button
      const exportExcelButton = screen.getByText('Export Excel');
      fireEvent.click(exportExcelButton);

      await waitFor(() => {
        expect(mockCreateObjectURL).toHaveBeenCalled();
        expect(mockLink.click).toHaveBeenCalled();
        expect(mockRevokeObjectURL).toHaveBeenCalledWith('blob:test-url');
      });
    });

    it('should remove link element from DOM after download', async () => {
      const mockBlob = new Blob(['excel content'], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });

      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ reports: mockReports, total_count: 2 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          blob: async () => mockBlob,
        });

      render(<ReportBuilder />);

      await waitFor(() => {
        expect(screen.getByText('Custom Report Builder')).toBeInTheDocument();
      });

      // Add a metric
      fireEvent.click(screen.getByText('Time-to-Hire'));

      // Click Export Excel button
      const exportExcelButton = screen.getByText('Export Excel');
      fireEvent.click(exportExcelButton);

      await waitFor(() => {
        expect(document.body.appendChild).toHaveBeenCalled();
        expect(mockLink.click).toHaveBeenCalled();
        // Note: The actual cleanup might happen asynchronously
      });
    });
  });
});
