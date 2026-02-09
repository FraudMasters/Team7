import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  CircularProgress,
  Alert,
  Icon,
} from '@/components/ui';
import { useTranslation } from 'react-i18next';
import DateRangeFilter, { DateRangeFilter as DateRangeFilterType } from '@components/analytics/DateRangeFilter';
import FairnessDashboard from '@components/analytics/FairnessDashboard';
import { BiasReportExport } from '@/components/BiasReportExport';
import { fairness } from '@/api/fairness';
import type { BiasReport } from '@/types/api';

/**
 * Bias Detection Dashboard Page (Recruiter Module)
 *
 * Shows AI bias detection and fairness metrics with:
 * - Overall fairness score and model monitoring
 * - Active alerts with severity levels
 * - Metrics by protected attribute
 * - Configurable date range filtering
 *
 * Helps hiring managers and compliance officers ensure fair hiring practices.
 */
const BiasDetectionDashboardPage: React.FC = () => {
  const { t } = useTranslation();
  const [dateRange, setDateRange] = useState<DateRangeFilterType>({
    startDate: '',
    endDate: '',
    preset: 'last_30_days',
  });
  const [reportDialogOpen, setReportDialogOpen] = useState(false);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);
  const [latestReport, setLatestReport] = useState<BiasReport | null>(null);

  /**
   * Handle date range change from DateRangeFilter component
   */
  const handleDateRangeChange = (newDateRange: DateRangeFilterType) => {
    setDateRange(newDateRange);
  };

  /**
   * Handle apply button click
   */
  const handleApplyFilter = (appliedDateRange: DateRangeFilterType) => {
    setDateRange(appliedDateRange);
  };

  /**
   * Open report builder dialog
   */
  const handleOpenReportBuilder = () => {
    setReportDialogOpen(true);
    setReportError(null);
  };

  /**
   * Close report builder dialog
   */
  const handleCloseReportBuilder = () => {
    setReportDialogOpen(false);
  };

  /**
   * Generate PDF report using browser print functionality
   */
  const handleGeneratePDF = async () => {
    setGeneratingReport(true);
    setReportError(null);

    try {
      await new Promise<void>((resolve) => {
        setTimeout(() => {
          window.print();
          resolve();
        }, 100);
      });

      setReportDialogOpen(false);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate report';
      setReportError(errorMessage);
    } finally {
      setGeneratingReport(false);
    }
  };

  /**
   * Open export dialog for bias report
   */
  const handleOpenExportDialog = async () => {
    try {
      // Try to get the latest report for the current date
      const today = new Date().toISOString().split('T')[0];
      const reportsResponse = await fairness.getReports({ limit: 1 });

      if (reportsResponse.reports.length > 0) {
        const report = reportsResponse.reports[0];
        setLatestReport(report);
        // Format report ID as {date}_{version}
        const reportId = `${today}_${report.model_version}`;
        setSelectedReportId(reportId);
      } else {
        // If no reports exist, use a default format
        const reportId = `${today}_latest`;
        setSelectedReportId(reportId);
      }

      setExportDialogOpen(true);
    } catch (err) {
      // If fetching reports fails, still open the dialog with a default ID
      const today = new Date().toISOString().split('T')[0];
      setSelectedReportId(`${today}_latest`);
      setExportDialogOpen(true);
    }
  };

  /**
   * Close export dialog
   */
  const handleCloseExportDialog = () => {
    setExportDialogOpen(false);
    setSelectedReportId(null);
  };

  /**
   * Handle export completion
   */
  const handleExportComplete = (format: 'pdf' | 'csv') => {
    // Optionally show a notification or log
    console.log(`Export completed in ${format} format`);
  };

  return (
    <>
      <Container maxWidth="xl" sx={{ py: 4 }} className="bias-detection-dashboard">
        {/* Header */}
        <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h4" as="h1" fontWeight={700} gutterBottom>
              {t('biasDetectionDashboard.title') || 'AI Bias Detection'}
            </Typography>
            <Typography variant="body1" color="secondary">
              {t('biasDetectionDashboard.subtitle') || 'Monitor fairness metrics and detect algorithmic bias'}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="outlined"
              startIcon={<Icon name="download" size={20} />}
              onClick={handleOpenExportDialog}
              color="primary"
            >
              Export Report
            </Button>
            <Button
              variant="contained"
              startIcon={<Icon name="file" size={20} />}
              onClick={handleOpenReportBuilder}
              color="primary"
            >
              Generate Report
            </Button>
          </Box>
        </Box>

        {/* Info Alert */}
        <Box sx={{ mb: 4 }}>
          <Alert severity="info">
            This dashboard monitors AI model fairness across demographic groups to ensure equitable hiring.
            Metrics include disparate impact ratios, statistical parity differences, and automated bias alerts.
          </Alert>
        </Box>

        {/* Date Range Filter */}
        <Box sx={{ mb: 4 }}>
          <DateRangeFilter
            onDateRangeChange={handleDateRangeChange}
            onApply={handleApplyFilter}
            initialDateRange={{ preset: 'last_30_days' }}
            showPresets={true}
          />
        </Box>

        {/* Fairness Dashboard */}
        <Box sx={{ mb: 4 }}>
          <FairnessDashboard
            startDate={dateRange.startDate}
            endDate={dateRange.endDate}
            alertDays={30}
          />
        </Box>
      </Container>

      {/* Report Builder Dialog */}
      <Dialog
        open={reportDialogOpen}
        onClose={handleCloseReportBuilder}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: { height: 'auto', maxHeight: '80vh' }
        }}
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6" fontWeight={600}>
              Generate Bias Detection Report
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              <Button
                variant="contained"
                startIcon={generatingReport ? <CircularProgress size={16} /> : <Icon name="file" size={20} />}
                onClick={handleGeneratePDF}
                disabled={generatingReport}
                color="primary"
              >
                {generatingReport ? 'Generating...' : 'Export as PDF'}
              </Button>
              <IconButton
                onClick={handleCloseReportBuilder}
                disabled={generatingReport}
                size="small"
              >
                <Icon name="x" size={20} />
              </IconButton>
            </Box>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ p: 0 }}>
          {reportError && (
            <Alert severity="error" sx={{ m: 2 }} onClose={() => setReportError(null)}>
              {reportError}
            </Alert>
          )}
          <Box sx={{ p: 3 }}>
            <Typography variant="body1" gutterBottom>
              This will generate a comprehensive bias detection report including:
            </Typography>
            <ul style={{ marginTop: '1rem', marginLeft: '1.5rem' }}>
              <li>Overall fairness score across all models</li>
              <li>Detailed metrics by demographic group</li>
              <li>Active alerts with severity levels</li>
              <li>Recommendations for improvement</li>
            </ul>
            <Alert severity="info" sx={{ mt: 3 }}>
              The report will be generated using your browser's print functionality.
              Select "Save as PDF" as the destination to create a downloadable report.
            </Alert>
          </Box>
        </DialogContent>
      </Dialog>

      {/* Bias Report Export Dialog */}
      {selectedReportId && (
        <BiasReportExport
          open={exportDialogOpen}
          onClose={handleCloseExportDialog}
          reportId={selectedReportId}
          onExportComplete={handleExportComplete}
        />
      )}

      {/* Print-specific styles - only applied when printing */}
      <style>{`
        @media print {
          .bias-detection-dashboard button:not([data-print-include]) {
            display: none !important;
          }
          body {
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
          }
        }
      `}</style>
    </>
  );
};

export default BiasDetectionDashboardPage;
