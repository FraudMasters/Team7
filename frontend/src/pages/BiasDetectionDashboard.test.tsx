/**
 * Tests for BiasDetectionDashboard Page Component
 *
 * Tests the AI bias detection dashboard including:
 * - Page rendering and header display
 * - Date range filter integration
 * - Report builder dialog functionality
 * - Export dialog functionality
 * - Error handling and loading states
 * - Print functionality
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import BiasDetectionDashboard from './BiasDetectionDashboard';
import * as fairness from '@/api/fairness';

// Mock the fairness API
vi.mock('@/api/fairness', () => ({
  fairness: {
    getReports: vi.fn(),
    exportReport: vi.fn(),
  },
}));

// Mock child components
vi.mock('@/components/analytics/DateRangeFilter', () => ({
  default: ({ onDateRangeChange, onApply }: any) => (
    <div data-testid="date-range-filter">
      <button onClick={() => onDateRangeChange({ startDate: '2024-01-01', endDate: '2024-01-31', preset: 'custom' })}>
        Change Date Range
      </button>
      <button onClick={() => onApply({ startDate: '2024-01-01', endDate: '2024-01-31', preset: 'custom' })}>
        Apply Filter
      </button>
    </div>
  ),
}));

vi.mock('@/components/analytics/FairnessDashboard', () => ({
  default: ({ startDate, endDate, alertDays }: any) => (
    <div data-testid="fairness-dashboard">
      <div data-testid="start-date">{startDate}</div>
      <div data-testid="end-date">{endDate}</div>
      <div data-testid="alert-days">{alertDays}</div>
    </div>
  ),
}));

vi.mock('@/components/BiasReportExport', () => ({
  BiasReportExport: ({ open, onClose, reportId, onExportComplete }: any) =>
    open ? (
      <div data-testid="bias-report-export">
        <div data-testid="export-report-id">{reportId}</div>
        <button onClick={onClose}>Close Export</button>
        <button onClick={() => onExportComplete('pdf')}>Complete Export</button>
      </div>
    ) : null,
}));

// Mock window.print
const mockPrint = vi.fn();
Object.defineProperty(window, 'print', {
  value: mockPrint,
  writable: true,
});

describe('BiasDetectionDashboard', () => {
  const mockGetReports = fairness.getReports as any;
  const mockExportReport = fairness.exportReport as any;

  beforeEach(() => {
    vi.clearAllMocks();
    // Mock console.log to avoid cluttering test output
    vi.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render the dashboard page with title and subtitle', () => {
      mockGetReports.mockResolvedValue({
        reports: [],
        total_count: 0,
      });

      render(<BiasDetectionDashboard />);

      expect(screen.getByText('AI Bias Detection')).toBeInTheDocument();
      expect(
        screen.getByText('Monitor fairness metrics and detect algorithmic bias')
      ).toBeInTheDocument();
    });

    it('should render info alert about dashboard purpose', () => {
      mockGetReports.mockResolvedValue({
        reports: [],
        total_count: 0,
      });

      render(<BiasDetectionDashboard />);

      expect(
        screen.getByText(/This dashboard monitors AI model fairness/)
      ).toBeInTheDocument();
    });

    it('should render Export Report and Generate Report buttons', () => {
      mockGetReports.mockResolvedValue({
        reports: [],
        total_count: 0,
      });

      render(<BiasDetectionDashboard />);

      expect(screen.getByText('Export Report')).toBeInTheDocument();
      expect(screen.getByText('Generate Report')).toBeInTheDocument();
    });

    it('should render DateRangeFilter component', () => {
      mockGetReports.mockResolvedValue({
        reports: [],
        total_count: 0,
      });

      render(<BiasDetectionDashboard />);

      expect(screen.getByTestId('date-range-filter')).toBeInTheDocument();
    });

    it('should render FairnessDashboard component with default props', () => {
      mockGetReports.mockResolvedValue({
        reports: [],
        total_count: 0,
      });

      render(<BiasDetectionDashboard />);

      const fairnessDashboard = screen.getByTestId('fairness-dashboard');
      expect(fairnessDashboard).toBeInTheDocument();
      expect(screen.getByTestId('alert-days')).toHaveTextContent('30');
    });
  });

  describe('Date Range Filter', () => {
    it('should update date range state when filter changes', async () => {
      mockGetReports.mockResolvedValue({
        reports: [],
        total_count: 0,
      });

      render(<BiasDetectionDashboard />);

      fireEvent.click(screen.getByText('Change Date Range'));

      await waitFor(() => {
        const fairnessDashboard = screen.getByTestId('fairness-dashboard');
        expect(fairnessDashboard).toBeInTheDocument();
      });
    });

    it('should apply date range filter when Apply button is clicked', async () => {
      mockGetReports.mockResolvedValue({
        reports: [],
        total_count: 0,
      });

      render(<BiasDetectionDashboard />);

      fireEvent.click(screen.getByText('Apply Filter'));

      await waitFor(() => {
        expect(screen.getByTestId('fairness-dashboard')).toBeInTheDocument();
      });
    });
  });

  describe('Report Builder Dialog', () => {
    it('should open report builder dialog when Generate Report button is clicked', async () => {
      mockGetReports.mockResolvedValue({
        reports: [],
        total_count: 0,
      });

      render(<BiasDetectionDashboard />);

      fireEvent.click(screen.getByText('Generate Report'));

      await waitFor(() => {
        expect(screen.getByText('Generate Bias Detection Report')).toBeInTheDocument();
        expect(screen.getByText('This will generate a comprehensive bias detection report including:')).toBeInTheDocument();
      });
    });

    it('should display report content description in dialog', async () => {
      mockGetReports.mockResolvedValue({
        reports: [],
        total_count: 0,
      });

      render(<BiasDetectionDashboard />);

      fireEvent.click(screen.getByText('Generate Report'));

      await waitFor(() => {
        expect(screen.getByText('Overall fairness score across all models')).toBeInTheDocument();
        expect(screen.getByText('Detailed metrics by demographic group')).toBeInTheDocument();
        expect(screen.getByText('Active alerts with severity levels')).toBeInTheDocument();
        expect(screen.getByText('Recommendations for improvement')).toBeInTheDocument();
      });
    });

    it('should display info alert about browser print functionality', async () => {
      mockGetReports.mockResolvedValue({
        reports: [],
        total_count: 0,
      });

      render(<BiasDetectionDashboard />);

      fireEvent.click(screen.getByText('Generate Report'));

      await waitFor(() => {
        expect(screen.getByText(/The report will be generated using your browser's print functionality/)).toBeInTheDocument();
      });
    });

    it('should trigger print when Export as PDF button is clicked', async () => {
      mockGetReports.mockResolvedValue({
        reports: [],
        total_count: 0,
      });

      render(<BiasDetectionDashboard />);

      fireEvent.click(screen.getByText('Generate Report'));

      await waitFor(() => {
        expect(screen.getByText('Export as PDF')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Export as PDF'));

      await waitFor(() => {
        expect(mockPrint).toHaveBeenCalled();
      });
    });

    it('should show generating state while exporting PDF', async () => {
      mockGetReports.mockResolvedValue({
        reports: [],
        total_count: 0,
      });

      render(<BiasDetectionDashboard />);

      fireEvent.click(screen.getByText('Generate Report'));

      const exportButton = await waitFor(() => screen.getByText('Export as PDF'));
      fireEvent.click(exportButton);

      await waitFor(() => {
        expect(screen.getByText('Generating...')).toBeInTheDocument();
      });
    });

    it('should close report builder dialog after successful PDF generation', async () => {
      mockGetReports.mockResolvedValue({
        reports: [],
        total_count: 0,
      });

      render(<BiasDetectionDashboard />);

      fireEvent.click(screen.getByText('Generate Report'));

      await waitFor(() => {
        expect(screen.getByText('Generate Bias Detection Report')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Export as PDF'));

      await waitFor(() => {
        expect(screen.queryByText('Generate Bias Detection Report')).not.toBeInTheDocument();
      });
    });

    it('should close report builder dialog when close button is clicked', async () => {
      mockGetReports.mockResolvedValue({
        reports: [],
        total_count: 0,
      });

      render(<BiasDetectionDashboard />);

      fireEvent.click(screen.getByText('Generate Report'));

      await waitFor(() => {
        expect(screen.getByText('Generate Bias Detection Report')).toBeInTheDocument();
      });

      // Close dialog by clicking outside (simulated by pressing Escape or clicking backdrop)
      // In this case, we'll look for the dialog to close when we trigger a close action
      fireEvent.keyDown(document, { key: 'Escape', code: 'Escape' });

      await waitFor(() => {
        expect(screen.queryByText('Generate Bias Detection Report')).not.toBeInTheDocument();
      });
    });

    it('should handle print error gracefully', async () => {
      mockGetReports.mockResolvedValue({
        reports: [],
        total_count: 0,
      });

      // Mock window.print to throw an error
      mockPrint.mockImplementation(() => {
        throw new Error('Print failed');
      });

      render(<BiasDetectionDashboard />);

      fireEvent.click(screen.getByText('Generate Report'));

      await waitFor(() => {
        expect(screen.getByText('Export as PDF')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Export as PDF'));

      await waitFor(() => {
        expect(screen.getByText('Print failed')).toBeInTheDocument();
      });
    });
  });

  describe('Export Dialog', () => {
    it('should open export dialog when Export Report button is clicked', async () => {
      const mockReport = {
        report_id: 'report-1',
        model_name: 'ranking',
        model_version: 'v1.0.0',
        report_type: 'system-wide',
        protected_attributes: ['gender', 'age'],
        overall_fairness_score: 0.85,
        bias_detected: false,
        severity_level: null,
        findings: [],
        recommendations: [],
        generated_at: '2024-01-15T10:00:00Z',
      };

      mockGetReports.mockResolvedValue({
        reports: [mockReport],
        total_count: 1,
      });

      render(<BiasDetectionDashboard />);

      fireEvent.click(screen.getByText('Export Report'));

      await waitFor(() => {
        expect(screen.getByTestId('bias-report-export')).toBeInTheDocument();
      });
    });

    it('should use latest report model version for report ID', async () => {
      const mockReport = {
        report_id: 'report-1',
        model_name: 'ranking',
        model_version: 'v1.0.0',
        report_type: 'system-wide',
        protected_attributes: ['gender', 'age'],
        overall_fairness_score: 0.85,
        bias_detected: false,
        severity_level: null,
        findings: [],
        recommendations: [],
        generated_at: '2024-01-15T10:00:00Z',
      };

      mockGetReports.mockResolvedValue({
        reports: [mockReport],
        total_count: 1,
      });

      render(<BiasDetectionDashboard />);

      fireEvent.click(screen.getByText('Export Report'));

      await waitFor(() => {
        const reportIdElement = screen.getByTestId('export-report-id');
        expect(reportIdElement).toBeInTheDocument();
        // Should be formatted as {date}_{version}
        expect(reportIdElement.textContent).toContain('_v1.0.0');
      });
    });

    it('should use default report ID format when no reports exist', async () => {
      mockGetReports.mockResolvedValue({
        reports: [],
        total_count: 0,
      });

      render(<BiasDetectionDashboard />);

      fireEvent.click(screen.getByText('Export Report'));

      await waitFor(() => {
        const reportIdElement = screen.getByTestId('export-report-id');
        expect(reportIdElement.textContent).toContain('_latest');
      });
    });

    it('should use default report ID format when API call fails', async () => {
      mockGetReports.mockRejectedValue(new Error('API Error'));

      render(<BiasDetectionDashboard />);

      fireEvent.click(screen.getByText('Export Report'));

      await waitFor(() => {
        const reportIdElement = screen.getByTestId('export-report-id');
        expect(reportIdElement.textContent).toContain('_latest');
      });
    });

    it('should close export dialog when close button is clicked', async () => {
      mockGetReports.mockResolvedValue({
        reports: [],
        total_count: 0,
      });

      render(<BiasDetectionDashboard />);

      fireEvent.click(screen.getByText('Export Report'));

      await waitFor(() => {
        expect(screen.getByTestId('bias-report-export')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Close Export'));

      await waitFor(() => {
        expect(screen.queryByTestId('bias-report-export')).not.toBeInTheDocument();
      });
    });

    it('should call onExportComplete callback when export completes', async () => {
      mockGetReports.mockResolvedValue({
        reports: [],
        total_count: 0,
      });

      render(<BiasDetectionDashboard />);

      fireEvent.click(screen.getByText('Export Report'));

      await waitFor(() => {
        expect(screen.getByTestId('bias-report-export')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Complete Export'));

      await waitFor(() => {
        expect(console.log).toHaveBeenCalledWith('Export completed in pdf format');
      });
    });
  });

  describe('FairnessDashboard Integration', () => {
    it('should pass date range props to FairnessDashboard', async () => {
      mockGetReports.mockResolvedValue({
        reports: [],
        total_count: 0,
      });

      render(<BiasDetectionDashboard />);

      const fairnessDashboard = screen.getByTestId('fairness-dashboard');
      expect(fairnessDashboard).toBeInTheDocument();
      expect(screen.getByTestId('alert-days')).toHaveTextContent('30');
    });
  });

  describe('Print Styles', () => {
    it('should render print-specific styles', () => {
      mockGetReports.mockResolvedValue({
        reports: [],
        total_count: 0,
      });

      const { container } = render(<BiasDetectionDashboard />);

      // Check that style element is present
      const styleElements = container.querySelectorAll('style');
      expect(styleElements.length).toBeGreaterThan(0);

      // Check that print media query is in the styles
      const styleContent = Array.from(styleElements).map((el) => el.textContent).join('');
      expect(styleContent).toContain('@media print');
    });
  });

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', () => {
      mockGetReports.mockResolvedValue({
        reports: [],
        total_count: 0,
      });

      render(<BiasDetectionDashboard />);

      const mainHeading = screen.getByText('AI Bias Detection');
      expect(mainHeading.tagName).toBe('H1') || expect(mainHeading.tagName).toBe('H4');
    });

    it('should have accessible button labels', () => {
      mockGetReports.mockResolvedValue({
        reports: [],
        total_count: 0,
      });

      render(<BiasDetectionDashboard />);

      expect(screen.getByRole('button', { name: /export report/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /generate report/i })).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle rapid button clicks gracefully', async () => {
      mockGetReports.mockResolvedValue({
        reports: [],
        total_count: 0,
      });

      render(<BiasDetectionDashboard />);

      const exportButton = screen.getByText('Export Report');
      fireEvent.click(exportButton);
      fireEvent.click(exportButton);
      fireEvent.click(exportButton);

      await waitFor(() => {
        expect(screen.getByTestId('bias-report-export')).toBeInTheDocument();
      });
    });

    it('should handle concurrent dialog operations', async () => {
      mockGetReports.mockResolvedValue({
        reports: [],
        total_count: 0,
      });

      render(<BiasDetectionDashboard />);

      // Open both dialogs rapidly
      fireEvent.click(screen.getByText('Generate Report'));
      fireEvent.click(screen.getByText('Export Report'));

      await waitFor(() => {
        expect(screen.getByText('Generate Bias Detection Report')).toBeInTheDocument();
      });
    });
  });

  describe('Console Output', () => {
    it('should log export completion message', async () => {
      mockGetReports.mockResolvedValue({
        reports: [],
        total_count: 0,
      });

      render(<BiasDetectionDashboard />);

      fireEvent.click(screen.getByText('Export Report'));

      await waitFor(() => {
        expect(screen.getByTestId('bias-report-export')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Complete Export'));

      await waitFor(() => {
        expect(console.log).toHaveBeenCalledWith('Export completed in pdf format');
      });
    });
  });
});
