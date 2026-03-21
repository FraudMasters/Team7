/**
 * Tests for ExportDialog Component
 *
 * Tests the analytics report export dialog including:
 * - Dialog open/close functionality
 * - Format selection (PDF/CSV)
 * - Export progress indication
 * - Success state handling
 * - Error state handling
 * - File download trigger
 * - Callback invocation
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ExportDialog from './ExportDialog';
import { analyticsClient } from '@/api/analyticsClient';

// Mock the analytics client
vi.mock('@/api/analyticsClient', () => ({
  analyticsClient: {
    exportAnalytics: vi.fn(),
  },
}));

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, options?: { defaultValue?: string }) => options?.defaultValue || key,
  }),
}));

// Mock URL.createObjectURL and revokeObjectURL
global.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
global.URL.revokeObjectURL = vi.fn();

describe('ExportDialog', () => {
  const mockOnClose = vi.fn();
  const mockOnExportComplete = vi.fn();

  const defaultProps = {
    open: true,
    onClose: mockOnClose,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render export dialog when open', () => {
      render(<ExportDialog {...defaultProps} />);

      expect(screen.getByText('Export Report')).toBeInTheDocument();
    });

    it('should not render dialog when closed', () => {
      render(<ExportDialog {...defaultProps} open={false} />);

      expect(screen.queryByText('Export Report')).not.toBeInTheDocument();
    });

    it('should display report information when provided', () => {
      render(
        <ExportDialog
          {...defaultProps}
          reportId="report-123"
          reportName="Q1 Analytics Report"
          startDate="2024-01-01"
          endDate="2024-03-31"
        />
      );

      expect(screen.getByText('Q1 Analytics Report')).toBeInTheDocument();
      expect(screen.getByText(/2024-01-01 to 2024-03-31/)).toBeInTheDocument();
    });

    it('should display only report ID when name is not provided', () => {
      render(
        <ExportDialog
          {...defaultProps}
          reportId="report-123"
        />
      );

      expect(screen.getByText('report-123')).toBeInTheDocument();
    });

    it('should render format selection options', () => {
      render(<ExportDialog {...defaultProps} />);

      expect(screen.getByText('PDF Document')).toBeInTheDocument();
      expect(screen.getByText('CSV Spreadsheet')).toBeInTheDocument();
    });

    it('should render export and cancel buttons', () => {
      render(<ExportDialog {...defaultProps} />);

      expect(screen.getByText('Export')).toBeInTheDocument();
      expect(screen.getByText('Cancel')).toBeInTheDocument();
    });

    it('should render info message in idle state', () => {
      render(<ExportDialog {...defaultProps} />);

      expect(screen.getByText(/The report will be downloaded automatically/)).toBeInTheDocument();
    });
  });

  describe('Format Selection', () => {
    it('should default to PDF format', () => {
      render(<ExportDialog {...defaultProps} />);

      const pdfRadio = screen.getByRole('radio', { name: /PDF Document/ });
      expect(pdfRadio).toBeChecked();
    });

    it('should allow switching to CSV format', () => {
      render(<ExportDialog {...defaultProps} />);

      const csvRadio = screen.getByRole('radio', { name: /CSV Spreadsheet/ });
      fireEvent.click(csvRadio);

      expect(csvRadio).toBeChecked();
    });

    it('should allow switching back to PDF format', () => {
      render(<ExportDialog {...defaultProps} />);

      const csvRadio = screen.getByRole('radio', { name: /CSV Spreadsheet/ });
      const pdfRadio = screen.getByRole('radio', { name: /PDF Document/ });

      fireEvent.click(csvRadio);
      expect(csvRadio).toBeChecked();

      fireEvent.click(pdfRadio);
      expect(pdfRadio).toBeChecked();
    });
  });

  describe('Export Functionality', () => {
    it('should call exportAnalytics with correct parameters', async () => {
      const mockBlob = new Blob(['test data'], { type: 'text/csv' });
      vi.mocked(analyticsClient.exportAnalytics).mockResolvedValue(mockBlob);

      render(
        <ExportDialog
          {...defaultProps}
          startDate="2024-01-01"
          endDate="2024-03-31"
          onExportComplete={mockOnExportComplete}
        />
      );

      fireEvent.click(screen.getByText('Export'));

      await waitFor(() => {
        expect(analyticsClient.exportAnalytics).toHaveBeenCalledWith({
          format: 'csv',
          start_date: '2024-01-01',
          end_date: '2024-03-31',
        });
      });
    });

    it('should show progress during export', async () => {
      const mockBlob = new Blob(['test data'], { type: 'text/csv' });
      vi.mocked(analyticsClient.exportAnalytics).mockImplementation(() => {
        return new Promise((resolve) => setTimeout(() => resolve(mockBlob), 100));
      });

      render(<ExportDialog {...defaultProps} />);

      fireEvent.click(screen.getByText('Export'));

      expect(screen.getByText('Exporting...')).toBeInTheDocument();
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('should show success message after export', async () => {
      const mockBlob = new Blob(['test data'], { type: 'text/csv' });
      vi.mocked(analyticsClient.exportAnalytics).mockResolvedValue(mockBlob);

      render(<ExportDialog {...defaultProps} />);

      fireEvent.click(screen.getByText('Export'));

      await waitFor(() => {
        expect(screen.getByText('Export Successful')).toBeInTheDocument();
      });
    });

    it('should trigger download on successful export', async () => {
      const mockBlob = new Blob(['test data'], { type: 'text/csv' });
      vi.mocked(analyticsClient.exportAnalytics).mockResolvedValue(mockBlob);

      const createElementSpy = vi.spyOn(document, 'createElement');
      const appendChildSpy = vi.spyOn(document.body, 'appendChild');
      const removeChildSpy = vi.spyOn(document.body, 'removeChild');

      render(<ExportDialog {...defaultProps} reportName="Test Report" />);

      fireEvent.click(screen.getByText('Export'));

      await waitFor(() => {
        expect(createElementSpy).toHaveBeenCalledWith('a');
        expect(appendChildSpy).toHaveBeenCalled();
        expect(removeChildSpy).toHaveBeenCalled();
        expect(global.URL.createObjectURL).toHaveBeenCalledWith(mockBlob);
        expect(global.URL.revokeObjectURL).toHaveBeenCalled();
      });
    });

    it('should generate correct filename with report name', async () => {
      const mockBlob = new Blob(['test data'], { type: 'text/csv' });
      vi.mocked(analyticsClient.exportAnalytics).mockResolvedValue(mockBlob);

      const linkClickSpy = vi.fn();
      const createElementSpy = vi.spyOn(document, 'createElement').mockReturnValue({
        click: linkClickSpy,
        href: '',
        download: '',
      } as unknown as HTMLAnchorElement);

      render(<ExportDialog {...defaultProps} reportName="Q1 Analytics Report" />);

      fireEvent.click(screen.getByText('Export'));

      await waitFor(() => {
        const anchor = createElementSpy.mock.results[0]?.value as HTMLAnchorElement;
        expect(anchor.download).toMatch(/^q1_analytics_report_\d{4}-\d{2}-\d{2}\.pdf$/);
      });
    });

    it('should call onExportComplete callback on success', async () => {
      const mockBlob = new Blob(['test data'], { type: 'text/csv' });
      vi.mocked(analyticsClient.exportAnalytics).mockResolvedValue(mockBlob);

      render(<ExportDialog {...defaultProps} onExportComplete={mockOnExportComplete} />);

      fireEvent.click(screen.getByText('Export'));

      await waitFor(() => {
        expect(mockOnExportComplete).toHaveBeenCalledWith('pdf');
      });
    });

    it('should show error message on export failure', async () => {
      vi.mocked(analyticsClient.exportAnalytics).mockRejectedValue(
        new Error('Network error')
      );

      render(<ExportDialog {...defaultProps} />);

      fireEvent.click(screen.getByText('Export'));

      await waitFor(() => {
        expect(screen.getByText('Export Failed')).toBeInTheDocument();
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });
    });

    it('should not call onExportComplete on failure', async () => {
      vi.mocked(analyticsClient.exportAnalytics).mockRejectedValue(
        new Error('Network error')
      );

      render(<ExportDialog {...defaultProps} onExportComplete={mockOnExportComplete} />);

      fireEvent.click(screen.getByText('Export'));

      await waitFor(() => {
        expect(screen.getByText('Export Failed')).toBeInTheDocument();
      });

      expect(mockOnExportComplete).not.toHaveBeenCalled();
    });

    it('should allow dismissing error message', async () => {
      vi.mocked(analyticsClient.exportAnalytics).mockRejectedValue(
        new Error('Network error')
      );

      render(<ExportDialog {...defaultProps} />);

      fireEvent.click(screen.getByText('Export'));

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });

      const dismissButton = screen.getByLabelText('Dismiss');
      fireEvent.click(dismissButton);

      expect(screen.queryByText('Network error')).not.toBeInTheDocument();
    });
  });

  describe('Dialog Controls', () => {
    it('should close dialog on cancel button click', () => {
      render(<ExportDialog {...defaultProps} />);

      fireEvent.click(screen.getByText('Cancel'));

      expect(mockOnClose).toHaveBeenCalled();
    });

    it('should close dialog on close icon click', () => {
      render(<ExportDialog {...defaultProps} />);

      const closeButton = screen.getByLabelText('Close');
      fireEvent.click(closeButton);

      expect(mockOnClose).toHaveBeenCalled();
    });

    it('should show Close button instead of Cancel after success', async () => {
      const mockBlob = new Blob(['test data'], { type: 'text/csv' });
      vi.mocked(analyticsClient.exportAnalytics).mockResolvedValue(mockBlob);

      render(<ExportDialog {...defaultProps} />);

      fireEvent.click(screen.getByText('Export'));

      await waitFor(() => {
        expect(screen.getByText('Close')).toBeInTheDocument();
        expect(screen.queryByText('Cancel')).not.toBeInTheDocument();
      });
    });

    it('should disable close button during export', async () => {
      const mockBlob = new Blob(['test data'], { type: 'text/csv' });
      vi.mocked(analyticsClient.exportAnalytics).mockImplementation(() => {
        return new Promise((resolve) => setTimeout(() => resolve(mockBlob), 100));
      });

      render(<ExportDialog {...defaultProps} />);

      fireEvent.click(screen.getByText('Export'));

      const cancelButton = screen.getByText('Cancel');
      expect(cancelButton).toBeDisabled();
    });

    it('should disable format selection during export', async () => {
      const mockBlob = new Blob(['test data'], { type: 'text/csv' });
      vi.mocked(analyticsClient.exportAnalytics).mockImplementation(() => {
        return new Promise((resolve) => setTimeout(() => resolve(mockBlob), 100));
      });

      render(<ExportDialog {...defaultProps} />);

      fireEvent.click(screen.getByText('Export'));

      const pdfRadio = screen.getByRole('radio', { name: /PDF Document/ });
      const csvRadio = screen.getByRole('radio', { name: /CSV Spreadsheet/ });

      expect(pdfRadio).toBeDisabled();
      expect(csvRadio).toBeDisabled();
    });

    it('should reset state when closing dialog', async () => {
      const mockBlob = new Blob(['test data'], { type: 'text/csv' });
      vi.mocked(analyticsClient.exportAnalytics).mockResolvedValue(mockBlob);

      const { rerender } = render(<ExportDialog {...defaultProps} />);

      // Switch to CSV format
      const csvRadio = screen.getByRole('radio', { name: /CSV Spreadsheet/ });
      fireEvent.click(csvRadio);

      // Export successfully
      fireEvent.click(screen.getByText('Export'));

      await waitFor(() => {
        expect(screen.getByText('Export Successful')).toBeInTheDocument();
      });

      // Close dialog
      fireEvent.click(screen.getByText('Close'));

      // Reopen dialog
      rerender(<ExportDialog {...defaultProps} open={false} />);
      rerender(<ExportDialog {...defaultProps} open={true} />);

      // Should be back to default state
      const pdfRadio = screen.getByRole('radio', { name: /PDF Document/ });
      expect(pdfRadio).toBeChecked();
      expect(screen.queryByText('Export Successful')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<ExportDialog {...defaultProps} />);

      expect(screen.getByRole('dialog')).toHaveAttribute('aria-labelledby', 'export-dialog-title');
      expect(screen.getByLabelText('Close')).toBeInTheDocument();
    });

    it('should prevent closing during export', () => {
      const mockBlob = new Blob(['test data'], { type: 'text/csv' });
      vi.mocked(analyticsClient.exportAnalytics).mockImplementation(() => {
        return new Promise((resolve) => setTimeout(() => resolve(mockBlob), 100));
      });

      render(<ExportDialog {...defaultProps} />);

      fireEvent.click(screen.getByText('Export'));

      const closeButton = screen.getByLabelText('Close');
      expect(closeButton).toBeDisabled();
    });
  });
});
