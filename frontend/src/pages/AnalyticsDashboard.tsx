import React, { useState } from 'react';
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
  Icon,
} from '@/components/ui';
import { useTranslation } from 'react-i18next';
import DateRangeFilter, { DateRangeFilter as DateRangeFilterType } from '@components/analytics/DateRangeFilter';
import KeyMetrics from '@components/analytics/KeyMetrics';
import SkillDemandChart from '@components/analytics/SkillDemandChart';
import ReportBuilder from '@components/analytics/ReportBuilder';
import AnalyticsExport from '@components/analytics/AnalyticsExport';

/**
 * Analytics Dashboard Page (Recruiter Module)
 *
 * Shows hiring metrics and analytics with:
 * - Key metrics (time-to-hire, resumes processed, match rates)
 * - Skill demand trends
 * - Configurable date range filtering
 *
 * Note: Funnel, Recruiter Performance, and Source Tracking are disabled
 * due to backend API limitations (Enum types not created in DB).
 */
const AnalyticsDashboardPage: React.FC = () => {
  const { t } = useTranslation();
  const [dateRange, setDateRange] = useState<DateRangeFilterType>({
    startDate: '',
    endDate: '',
    preset: 'last_30_days',
  });
  const [reportDialogOpen, setReportDialogOpen] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);

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

  return (
    <>
      <Container maxWidth="xl" sx={{ py: 4 }} className="analytics-dashboard">
        {/* Header */}
        <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h4" as="h1" fontWeight={700} gutterBottom>
              {t('analyticsDashboard.title')}
            </Typography>
            <Typography variant="body1" color="secondary">
              {t('analyticsDashboard.subtitle')}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <AnalyticsExport
              startDate={dateRange.startDate}
              endDate={dateRange.endDate}
              compact={true}
              onExportComplete={(config) => {
                // Export completed
              }}
            />
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

        {/* Date Range Filter */}
        <Box sx={{ mb: 4 }}>
          <DateRangeFilter
            onDateRangeChange={handleDateRangeChange}
            onApply={handleApplyFilter}
            initialDateRange={{ preset: 'last_30_days' }}
            showPresets={true}
          />
        </Box>

        {/* Key Metrics */}
        <Box sx={{ mb: 4 }}>
          <KeyMetrics startDate={dateRange.startDate} endDate={dateRange.endDate} />
        </Box>

        {/* Skill Demand */}
        <Box sx={{ mb: 4 }}>
          <SkillDemandChart startDate={dateRange.startDate} endDate={dateRange.endDate} />
        </Box>

        {/* Placeholder for disabled features */}
        <Box sx={{ mb: 4 }}>
          <Alert severity="info" sx={{ mb: 2 }}>
            Additional analytics features (Funnel, Recruiter Performance, Source Tracking)
            are temporarily disabled due to backend database migration requirements.
          </Alert>
        </Box>
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
        }
      `}</style>
    </>
  );
};

export default AnalyticsDashboardPage;
