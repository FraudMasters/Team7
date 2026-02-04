import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  IconButton,
  CircularProgress,
  Alert,
  Chip,
  Fade,
  Grid,
} from '@mui/material';
import {
  Close as CloseIcon,
  PictureAsPdf as PdfIcon,
  Refresh as RefreshIcon,
  Schedule as TimeIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import DateRangeFilter, { DateRangeFilter as DateRangeFilterType } from '@components/analytics/DateRangeFilter';
import FunnelVisualization from '@components/analytics/FunnelVisualization';
import RecruiterPerformance from '@components/analytics/RecruiterPerformance';
import SourceTracking from '@components/analytics/SourceTracking';
import ReportBuilder from '@components/analytics/ReportBuilder';

/**
 * Advanced Analytics Dashboard Page (Recruiter Module)
 *
 * Shows advanced hiring metrics and analytics with:
 * - Hiring velocity insights (time-to-hire trends, bottlenecks)
 * - Funnel analysis (conversion rates at each stage)
 * - Recruiter performance metrics
 * - Source tracking and ROI analysis
 * - Configurable date range filtering
 * - Real-time data refresh
 */
const AdvancedAnalyticsPage: React.FC = () => {
  const { t } = useTranslation();
  const [dateRange, setDateRange] = useState<DateRangeFilterType>({
    startDate: '',
    endDate: '',
    preset: 'last_30_days',
  });
  const [reportDialogOpen, setReportDialogOpen] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);

  // Real-time refresh state
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastRefreshTime, setLastRefreshTime] = useState<Date>(new Date());
  const [refreshKey, setRefreshKey] = useState(0);
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const REFRESH_INTERVAL = 60000; // 60 seconds

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
   * Trigger refresh of all dashboard components
   */
  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      // Increment refresh key to trigger child component updates
      setRefreshKey((prev) => prev + 1);
      setLastRefreshTime(new Date());

      // Simulate refresh delay for visual feedback
      await new Promise<void>((resolve) => setTimeout(resolve, 500));
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  /**
   * Toggle auto-refresh
   */
  const toggleAutoRefresh = useCallback(() => {
    setAutoRefreshEnabled((prev) => !prev);
  }, []);

  /**
   * Setup auto-refresh polling
   */
  useEffect(() => {
    if (!autoRefreshEnabled) {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
        refreshIntervalRef.current = null;
      }
      return;
    }

    refreshIntervalRef.current = setInterval(() => {
      handleRefresh();
    }, REFRESH_INTERVAL);

    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [autoRefreshEnabled, handleRefresh]);

  /**
   * Initial data fetch on mount
   */
  useEffect(() => {
    handleRefresh();
  }, []);

  return (
    <>
      <Container maxWidth="xl" sx={{ py: 4 }} className="advanced-analytics-dashboard">
        {/* Header */}
        <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h4" component="h1" fontWeight={700} gutterBottom>
              Advanced Analytics
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 1 }}>
              Deep dive into hiring performance, velocity, and source effectiveness
            </Typography>

            {/* Refresh Status Indicator */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2 }}>
              <Chip
                icon={autoRefreshEnabled ? <PlayIcon fontSize="small" /> : <PauseIcon fontSize="small" />}
                label={autoRefreshEnabled ? 'Auto-refresh enabled' : 'Auto-refresh paused'}
                size="small"
                color={autoRefreshEnabled ? 'success' : 'default'}
                variant="outlined"
              />
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <TimeIcon fontSize="small" color="action" />
                <Typography variant="caption" color="text.secondary">
                  Last updated: {lastRefreshTime.toLocaleTimeString()}
                </Typography>
              </Box>
              {isRefreshing && (
                <Fade in={isRefreshing}>
                  <CircularProgress size={16} sx={{ ml: 1 }} />
                </Fade>
              )}
            </Box>
          </Box>

          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Button
              variant={autoRefreshEnabled ? 'contained' : 'outlined'}
              startIcon={autoRefreshEnabled ? <PauseIcon /> : <PlayIcon />}
              onClick={toggleAutoRefresh}
              color={autoRefreshEnabled ? 'primary' : 'default'}
              size="small"
              sx={{ minWidth: 120 }}
            >
              {autoRefreshEnabled ? 'Auto-refresh' : 'Paused'}
            </Button>
            <Button
              variant="outlined"
              startIcon={isRefreshing ? <CircularProgress size={16} /> : <RefreshIcon />}
              onClick={handleRefresh}
              disabled={isRefreshing}
              size="small"
            >
              Refresh All
            </Button>
            <Button
              variant="contained"
              startIcon={<PdfIcon />}
              onClick={handleOpenReportBuilder}
              color="primary"
            >
              Generate Report
            </Button>
          </Box>
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

        {/* Advanced Analytics Grid */}
        <Grid container spacing={3}>
          {/* Funnel Visualization */}
          <Grid item xs={12}>
            <Box sx={{ mb: 3 }}>
              <FunnelVisualization
                startDate={dateRange.startDate}
                endDate={dateRange.endDate}
                refreshKey={refreshKey}
              />
            </Box>
          </Grid>

          {/* Recruiter Performance */}
          <Grid item xs={12} lg={6}>
            <Box sx={{ height: '100%' }}>
              <RecruiterPerformance
                startDate={dateRange.startDate}
                endDate={dateRange.endDate}
                refreshKey={refreshKey}
              />
            </Box>
          </Grid>

          {/* Source Tracking */}
          <Grid item xs={12} lg={6}>
            <Box sx={{ height: '100%' }}>
              <SourceTracking
                startDate={dateRange.startDate}
                endDate={dateRange.endDate}
                refreshKey={refreshKey}
              />
            </Box>
          </Grid>
        </Grid>
      </Container>

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
              Generate Advanced Analytics Report
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              <Button
                variant="contained"
                startIcon={generatingReport ? <CircularProgress size={16} /> : <PdfIcon />}
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
                <CloseIcon />
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
          .advanced-analytics-dashboard .MuiButton-root:not([data-print-include]) {
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

export default AdvancedAnalyticsPage;
