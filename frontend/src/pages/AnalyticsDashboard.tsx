import React, { useState, useCallback } from 'react';
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
  AlertTitle,
  Icon,
  Snackbar,
  Chip,
  LinearProgress,
  Stack,
  Paper,
  Divider,
  FormControl,
  FormControlLabel,
  RadioGroup,
  Radio,
} from '@/components/ui';
import { useTranslation } from 'react-i18next';
import DashboardFilters, { DashboardFiltersState } from '@components/analytics/DashboardFilters';
import KeyMetrics from '@components/analytics/KeyMetrics';
import SkillDemandChart from '@components/analytics/SkillDemandChart';
import FunnelVisualization from '@components/analytics/FunnelVisualization';
import RecruiterPerformance from '@components/analytics/RecruiterPerformance';
import SourceTracking from '@components/analytics/SourceTracking';
import RankingAccuracyMetrics from '@components/analytics/RankingAccuracyMetrics';
import ReportBuilder from '@components/analytics/ReportBuilder';
import AnalyticsExport from '@components/analytics/AnalyticsExport';
import { useAnalyticsRealTime } from '@/hooks';
import type { AnalyticsUpdateType } from '@/types/api';
import { config } from '@/config';

/**
 * Export format options
 */
type ExportFormat = 'pdf' | 'excel' | 'csv';

/**
 * Export status states
 */
type ExportStatus = 'idle' | 'exporting' | 'success' | 'error';

/**
 * Analytics Dashboard Page (Recruiter Module)
 *
 * Shows hiring metrics and analytics with:
 * - Key metrics (time-to-hire, resumes processed, match rates)
 * - Recruitment funnel visualization
 * - Recruiter performance tracking
 * - Source tracking analytics
 * - Skill demand trends
 * - Configurable date range filtering
 * - Real-time updates via WebSocket
 * - Export functionality (PDF, Excel, CSV)
 */
const AnalyticsDashboardPage: React.FC = () => {
  const { t } = useTranslation();
  const [filters, setFilters] = useState<DashboardFiltersState>({
    dateRange: {
      startDate: '',
      endDate: '',
      preset: 'last_30_days',
    },
    recruiterId: null,
    vacancyId: null,
  });
  const [reportDialogOpen, setReportDialogOpen] = useState(false);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [exportFormat, setExportFormat] = useState<ExportFormat>('pdf');
  const [exportStatus, setExportStatus] = useState<ExportStatus>('idle');
  const [exportProgress, setExportProgress] = useState(0);
  const [exportError, setExportError] = useState<string | null>(null);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);
  const [showUpdateSnackbar, setShowUpdateSnackbar] = useState(false);
  const [updateMessage, setUpdateMessage] = useState<string>('');

  /**
   * Handle analytics updates from WebSocket
   */
  const handleAnalyticsUpdate = useCallback((updateType: AnalyticsUpdateType) => {
    // Show notification for update
    const updateTypeLabels: Record<AnalyticsUpdateType, string> = {
      key_metrics: 'Key Metrics',
      quality_metrics: 'Quality Metrics',
      stage_duration: 'Stage Duration',
      ranking_accuracy: 'Ranking Accuracy',
      predictive: 'Predictive Analytics',
    };

    setUpdateMessage(`${updateTypeLabels[updateType] || updateType} updated`);
    setShowUpdateSnackbar(true);
  }, []);

  /**
   * WebSocket real-time connection for analytics updates
   */
  const {
    isConnected,
    isConnecting,
    connectionError,
    lastUpdate,
    refreshKey,
  } = useAnalyticsRealTime({
    onUpdate: handleAnalyticsUpdate,
    onError: (error) => {
      // Silently handle connection errors - not critical for dashboard
    },
    autoReconnect: true,
    maxReconnectAttempts: 10,
  });

  /**
   * Handle filters change from DashboardFilters component
   */
  const handleFiltersChange = (newFilters: DashboardFiltersState) => {
    setFilters(newFilters);
  };

  /**
   * Handle apply button click
   */
  const handleApplyFilter = (appliedFilters: DashboardFiltersState) => {
    setFilters(appliedFilters);
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
   * Open export dialog
   */
  const handleOpenExportDialog = () => {
    setExportDialogOpen(true);
    setExportStatus('idle');
    setExportError(null);
    setExportProgress(0);
  };

  /**
   * Close export dialog
   */
  const handleCloseExportDialog = () => {
    if (exportStatus === 'exporting') {
      return;
    }
    setExportDialogOpen(false);
    setExportStatus('idle');
    setExportError(null);
    setExportProgress(0);
  };

  /**
   * Handle export format change
   */
  const handleExportFormatChange = (_event: React.ChangeEvent<HTMLInputElement>, value: string) => {
    setExportFormat(value as ExportFormat);
  };

  /**
   * Trigger file download in browser
   */
  const triggerDownload = (blob: Blob, filename: string) => {
    try {
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Download failed';
      setExportError(errorMessage);
      setExportStatus('error');
    }
  };

  /**
   * Handle analytics export
   */
  const handleExport = async () => {
    setExportStatus('exporting');
    setExportError(null);
    setExportProgress(0);

    const progressInterval = setInterval(() => {
      setExportProgress((prev) => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + 10;
      });
    }, 200);

    try {
      const timestamp = new Date().toISOString().split('T')[0];
      let blob: Blob;
      let filename: string;

      if (exportFormat === 'pdf') {
        const response = await fetch(`${config.api.url}/api/analytics/export/pdf`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            start_date: filters.dateRange.startDate,
            end_date: filters.dateRange.endDate,
            recruiter_id: filters.recruiterId,
            vacancy_id: filters.vacancyId,
          }),
        });

        if (!response.ok) {
          throw new Error(`Failed to export PDF: ${response.statusText}`);
        }

        blob = await response.blob();
        filename = `analytics_report_${timestamp}.pdf`;
      } else if (exportFormat === 'excel') {
        const response = await fetch(`${config.api.url}/api/analytics/export/excel`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            start_date: filters.dateRange.startDate,
            end_date: filters.dateRange.endDate,
            recruiter_id: filters.recruiterId,
            vacancy_id: filters.vacancyId,
          }),
        });

        if (!response.ok) {
          throw new Error(`Failed to export Excel: ${response.statusText}`);
        }

        blob = await response.blob();
        filename = `analytics_export_${timestamp}.xlsx`;
      } else {
        const response = await fetch(`${config.api.url}/api/analytics/export/csv`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            start_date: filters.dateRange.startDate,
            end_date: filters.dateRange.endDate,
            recruiter_id: filters.recruiterId,
            vacancy_id: filters.vacancyId,
          }),
        });

        if (!response.ok) {
          throw new Error(`Failed to export CSV: ${response.statusText}`);
        }

        blob = await response.blob();
        filename = `analytics_export_${timestamp}.csv`;
      }

      clearInterval(progressInterval);
      setExportProgress(100);

      triggerDownload(blob, filename);

      setExportStatus('success');
    } catch (err) {
      clearInterval(progressInterval);
      const errorMessage =
        err instanceof Error
          ? err.message
          : `Failed to export ${exportFormat.toUpperCase()}`;
      setExportError(errorMessage);
      setExportStatus('error');
    }
  };

  /**
   * Get export format icon name
   */
  const getExportFormatIcon = (format: ExportFormat): string => {
    switch (format) {
      case 'pdf':
        return 'file-text';
      case 'excel':
        return 'table';
      case 'csv':
        return 'file-spreadsheet';
      default:
        return 'file';
    }
  };

  return (
    <>
      <Container maxWidth="xl" sx={{ py: 4 }} className="analytics-dashboard">
        {/* Header */}
        <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box sx={{ flex: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
              <Typography variant="h4" as="h1" fontWeight={700}>
                {t('analyticsDashboard.title')}
              </Typography>
              {/* WebSocket Connection Status Indicator */}
              <Chip
                size="small"
                label={isConnecting ? 'Connecting...' : isConnected ? 'Live' : 'Offline'}
                color={isConnected ? 'success' : isConnecting ? 'warning' : 'default'}
                variant={isConnected ? 'filled' : 'outlined'}
                icon={
                  <Box
                    component="span"
                    sx={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      bgcolor: isConnected ? 'success.main' : isConnecting ? 'warning.main' : 'text.disabled',
                      animation: isConnecting ? 'pulse 1.5s infinite' : 'none',
                      '@keyframes pulse': {
                        '0%': { opacity: 1 },
                        '50%': { opacity: 0.4 },
                        '100%': { opacity: 1 },
                      },
                    }}
                  />
                }
                sx={{
                  '& .MuiChip-icon': {
                    ml: 0.5,
                  },
                }}
              />
            </Box>
            <Typography variant="body1" color="secondary">
              {t('analyticsDashboard.subtitle')}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="outlined"
              startIcon={<Icon name="download" size={20} />}
              onClick={handleOpenExportDialog}
              color="primary"
            >
              Export
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

        {/* Dashboard Filters */}
        <Box sx={{ mb: 4 }}>
          <DashboardFilters
            onFiltersChange={handleFiltersChange}
            onApply={handleApplyFilter}
            initialFilters={{ dateRange: { preset: 'last_30_days' } }}
            showRecruiterFilter={true}
            showVacancyFilter={true}
          />
        </Box>

        {/* Key Metrics */}
        <Box sx={{ mb: 4 }}>
          <KeyMetrics
            startDate={filters.dateRange.startDate}
            endDate={filters.dateRange.endDate}
            refreshKey={refreshKey}
          />
        </Box>

        {/* Skill Demand */}
        <Box sx={{ mb: 4 }}>
          <SkillDemandChart
            startDate={filters.dateRange.startDate}
            endDate={filters.dateRange.endDate}
            refreshKey={refreshKey}
          />
        </Box>

        {/* Funnel Visualization */}
        <Box sx={{ mb: 4 }}>
          <FunnelVisualization
            startDate={filters.dateRange.startDate}
            endDate={filters.dateRange.endDate}
            refreshKey={refreshKey}
          />
        </Box>

        {/* Recruiter Performance */}
        <Box sx={{ mb: 4 }}>
          <RecruiterPerformance
            startDate={filters.dateRange.startDate}
            endDate={filters.dateRange.endDate}
            refreshKey={refreshKey}
          />
        </Box>

        {/* Source Tracking */}
        <Box sx={{ mb: 4 }}>
          <SourceTracking
            startDate={filters.dateRange.startDate}
            endDate={filters.dateRange.endDate}
            refreshKey={refreshKey}
          />
        </Box>

        {/* Ranking Accuracy Metrics */}
        <Box sx={{ mb: 4 }}>
          <RankingAccuracyMetrics
            startDate={filters.dateRange.startDate}
            endDate={filters.dateRange.endDate}
          />
        </Box>
      </Container>

      {/* Export Dialog */}
      <Dialog
        open={exportDialogOpen}
        onClose={exportStatus === 'exporting' ? undefined : handleCloseExportDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Icon name="download" size={20} />
              <Typography variant="h6" fontWeight={600}>
                Export Analytics Data
              </Typography>
            </Box>
            {exportStatus !== 'exporting' && (
              <IconButton onClick={handleCloseExportDialog} size="small">
                <Icon name="x" size={20} />
              </IconButton>
            )}
          </Box>
        </DialogTitle>

        <Divider />

        <DialogContent sx={{ py: 3 }}>
          <Stack spacing={3}>
            {/* Description */}
            <Alert severity="info" variant="outlined">
              <AlertTitle>Export analytics report</AlertTitle>
              <Typography variant="body2">
                Choose a format to export analytics data. PDF includes visualizations and professional formatting,
                Excel provides structured data for analysis, and CSV offers raw data export.
              </Typography>
            </Alert>

            {/* Date Range Info */}
            {(filters.dateRange.startDate || filters.dateRange.endDate) && (
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                  Export Range
                </Typography>
                <Stack spacing={1}>
                  {filters.dateRange.startDate && (
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="text.secondary">
                        Start Date
                      </Typography>
                      <Typography variant="body2" fontWeight={600}>
                        {filters.dateRange.startDate}
                      </Typography>
                    </Box>
                  )}
                  {filters.dateRange.endDate && (
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="text.secondary">
                        End Date
                      </Typography>
                      <Typography variant="body2" fontWeight={600}>
                        {filters.dateRange.endDate}
                      </Typography>
                    </Box>
                  )}
                </Stack>
              </Paper>
            )}

            {/* Format Selection */}
            {exportStatus === 'idle' && (
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                  Export Format
                </Typography>
                <FormControl component="fieldset">
                  <RadioGroup value={exportFormat} onChange={handleExportFormatChange}>
                    <FormControlLabel
                      value="pdf"
                      control={<Radio />}
                      label={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Icon name="file-text" size={18} />
                          <Box>
                            <Typography variant="body2" fontWeight={500}>
                              PDF Format
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Professional report with visualizations and charts
                            </Typography>
                          </Box>
                        </Box>
                      }
                    />
                    <FormControlLabel
                      value="excel"
                      control={<Radio />}
                      label={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Icon name="table" size={18} />
                          <Box>
                            <Typography variant="body2" fontWeight={500}>
                              Excel Format (XLSX)
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Structured data with multiple sheets for analysis
                            </Typography>
                          </Box>
                        </Box>
                      }
                    />
                    <FormControlLabel
                      value="csv"
                      control={<Radio />}
                      label={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Icon name="file-spreadsheet" size={18} />
                          <Box>
                            <Typography variant="body2" fontWeight={500}>
                              CSV Format
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Raw data export for custom analysis and processing
                            </Typography>
                          </Box>
                        </Box>
                      }
                    />
                  </RadioGroup>
                </FormControl>
              </Paper>
            )}

            {/* Exporting State */}
            {exportStatus === 'exporting' && (
              <Box sx={{ textAlign: 'center', py: 3 }}>
                <CircularProgress size={60} sx={{ mb: 3 }} />
                <Typography variant="h6" gutterBottom>
                  Exporting Analytics...
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Please wait while we generate your {exportFormat.toUpperCase()} export.
                </Typography>
                <Box sx={{ width: '100%', maxWidth: 400, mx: 'auto' }}>
                  <LinearProgress variant="determinate" value={exportProgress} />
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    {exportProgress}%
                  </Typography>
                </Box>
              </Box>
            )}

            {/* Success State */}
            {exportStatus === 'success' && (
              <Alert severity="success" variant="filled">
                <AlertTitle>Export Complete!</AlertTitle>
                <Typography variant="body2">
                  Your analytics data has been exported successfully. The download should start automatically.
                </Typography>
                <Box sx={{ mt: 2 }}>
                  <Chip
                    icon={<Icon name={getExportFormatIcon(exportFormat)} size={16} />}
                    label={`${exportFormat.toUpperCase()} file ready`}
                    color="success"
                    size="small"
                  />
                </Box>
              </Alert>
            )}

            {/* Error State */}
            {exportStatus === 'error' && (
              <Alert severity="error">
                <AlertTitle>Export Failed</AlertTitle>
                <Typography variant="body2">{exportError}</Typography>
              </Alert>
            )}
          </Stack>
        </DialogContent>

        <Divider />

        <DialogActions sx={{ px: 3, py: 2 }}>
          {exportStatus === 'idle' && (
            <>
              <Button onClick={handleCloseExportDialog} disabled={exportStatus === 'exporting'}>
                Cancel
              </Button>
              <Button
                variant="contained"
                onClick={handleExport}
                disabled={exportStatus === 'exporting'}
                startIcon={<Icon name="download" size={20} />}
              >
                Export {exportFormat.toUpperCase()}
              </Button>
            </>
          )}

          {exportStatus === 'success' && (
            <Button variant="outlined" onClick={handleCloseExportDialog} startIcon={<Icon name="check" size={20} />}>
              Done
            </Button>
          )}

          {exportStatus === 'error' && (
            <>
              <Button onClick={handleCloseExportDialog}>Close</Button>
              <Button
                variant="contained"
                onClick={handleExport}
                startIcon={<Icon name="download" size={20} />}
              >
                Retry
              </Button>
            </>
          )}
        </DialogActions>
      </Dialog>

      {/* Report Builder Dialog */}
      <Dialog
        open={reportDialogOpen}
        onClose={handleCloseReportBuilder}
        maxWidth="xl"
        fullWidth
        PaperProps={{
          sx: { height: '80vh', maxHeight: '80vh' }
        }}
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6" fontWeight={600}>
              Generate Analytics Report
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
          <Box sx={{ height: '100%', overflow: 'auto' }}>
            <ReportBuilder
              onReportChange={(report) => {
                // Report configuration saved
              }}
            />
          </Box>
        </DialogContent>
      </Dialog>

      {/* Print-specific styles - only applied when printing */}
      <style>{`
        @media print {
          .analytics-dashboard button:not([data-print-include]) {
            display: none !important;
          }
          body {
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
          }
          .connection-status-chip {
            display: none !important;
          }
        }
      `}</style>

      {/* Real-time Update Notification */}
      <Snackbar
        open={showUpdateSnackbar}
        autoHideDuration={3000}
        onClose={() => setShowUpdateSnackbar(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setShowUpdateSnackbar(false)}
          severity="info"
          sx={{ width: '100%' }}
          icon={<Icon name="refresh" size={18} />}
        >
          {updateMessage}
        </Alert>
      </Snackbar>
    </>
  );
};

export default AnalyticsDashboardPage;
