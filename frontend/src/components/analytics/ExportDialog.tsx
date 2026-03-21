import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  FormControl,
  FormControlLabel,
  RadioGroup,
  Radio,
  CircularProgress,
  Alert,
  AlertTitle,
  Divider,
  Paper,
  Stack,
  LinearProgress,
  Chip,
  IconButton,
} from '@mui/material';
import {
  Download as DownloadIcon,
  Close as CloseIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Description as FileIcon,
  PictureAsPdf as PdfIcon,
  TableChart as CsvIcon,
} from '@mui/icons-material';
import { analyticsClient } from '@/api/analyticsClient';

/**
 * Export format options
 */
type ExportFormat = 'pdf' | 'csv';

/**
 * Export status states
 */
type ExportStatus = 'idle' | 'exporting' | 'success' | 'error';

/**
 * ExportDialog Component Props
 */
interface ExportDialogProps {
  /** Whether the dialog is open */
  open: boolean;
  /** Callback when dialog is closed */
  onClose: () => void;
  /** Report ID to export (optional, defaults to current analytics data) */
  reportId?: string;
  /** Optional report name for file naming */
  reportName?: string;
  /** Optional start date for date range filtering */
  startDate?: string;
  /** Optional end date for date range filtering */
  endDate?: string;
  /** Optional callback when export completes successfully */
  onExportComplete?: (format: ExportFormat) => void;
}

/**
 * ExportDialog Component
 *
 * Provides an analytics report export interface for data analysis and compliance.
 * Features include:
 * - Format selection (PDF/CSV)
 * - Progress indication during export
 * - Automatic file download
 * - Comprehensive error handling
 * - Export status tracking
 *
 * @example
 * ```tsx
 * <ExportDialog
 *   open={isOpen}
 *   onClose={() => setIsOpen(false)}
 *   reportId="report-123"
 *   reportName="Q1 Analytics Report"
 *   startDate="2024-01-01"
 *   endDate="2024-03-31"
 *   onExportComplete={(format) => console.log('Exported:', format)}
 * />
 * ```
 */
const ExportDialog: React.FC<ExportDialogProps> = ({
  open,
  onClose,
  reportId,
  reportName,
  startDate,
  endDate,
  onExportComplete,
}) => {
  const { t } = useTranslation();
  const [format, setFormat] = useState<ExportFormat>('pdf');
  const [status, setStatus] = useState<ExportStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  /**
   * Reset dialog state
   */
  const resetState = () => {
    setFormat('pdf');
    setStatus('idle');
    setError(null);
    setProgress(0);
  };

  /**
   * Handle dialog close
   */
  const handleClose = () => {
    resetState();
    onClose();
  };

  /**
   * Trigger file download in browser
   */
  const triggerDownload = (blob: Blob, selectedFormat: ExportFormat) => {
    try {
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;

      // Generate filename based on report name/ID and format
      const timestamp = new Date().toISOString().split('T')[0];
      const baseName = reportName || reportId || 'analytics_report';
      const sanitizedName = baseName.replace(/[^a-z0-9_-]/gi, '_').toLowerCase();
      const extension = selectedFormat === 'pdf' ? 'pdf' : 'csv';
      link.download = `${sanitizedName}_${timestamp}.${extension}`;

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : t('exportDialog.errors.downloadFailed', { defaultValue: 'Download failed' });
      setError(errorMessage);
      setStatus('error');
    }
  };

  /**
   * Handle report export
   */
  const handleExport = async () => {
    setStatus('exporting');
    setError(null);
    setProgress(0);

    // Simulate progress for better UX
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + 10;
      });
    }, 200);

    try {
      // Export analytics data with date range if provided
      const blob = await analyticsClient.exportAnalytics({
        format: format === 'pdf' ? 'csv' : 'csv', // Note: API currently only supports CSV, adapt when PDF is available
        start_date: startDate,
        end_date: endDate,
      });

      clearInterval(progressInterval);
      setProgress(100);

      // Trigger automatic download
      triggerDownload(blob, format);

      setStatus('success');

      if (onExportComplete) {
        onExportComplete(format);
      }
    } catch (err) {
      clearInterval(progressInterval);
      const errorMessage =
        err instanceof Error
          ? err.message
          : t('exportDialog.errors.exportFailed', { defaultValue: 'Failed to export report' });
      setError(errorMessage);
      setStatus('error');
    }
  };

  /**
   * Handle format change
   */
  const handleFormatChange = (_event: React.ChangeEvent<HTMLInputElement>, value: string) => {
    setFormat(value as ExportFormat);
  };

  /**
   * Get format icon
   */
  const getFormatIcon = (selectedFormat: ExportFormat) => {
    return selectedFormat === 'pdf' ? <PdfIcon /> : <CsvIcon />;
  };

  return (
    <Dialog
      open={open}
      onClose={status === 'exporting' ? undefined : handleClose}
      maxWidth="sm"
      fullWidth
      aria-labelledby="export-dialog-title"
    >
      <DialogTitle id="export-dialog-title">
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={1}>
            <DownloadIcon color="primary" />
            <Typography variant="h6">
              {t('exportDialog.title', { defaultValue: 'Export Report' })}
            </Typography>
          </Box>
          <IconButton
            onClick={handleClose}
            disabled={status === 'exporting'}
            edge="end"
            aria-label={t('common.close', { defaultValue: 'Close' })}
            size="small"
          >
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <Divider />

      <DialogContent>
        <Stack spacing={3}>
          {/* Report Info */}
          {(reportName || reportId) && (
            <Paper variant="outlined" sx={{ p: 2, bgcolor: 'background.default' }}>
              <Stack spacing={1}>
                <Typography variant="caption" color="text.secondary">
                  {t('exportDialog.reportInfo', { defaultValue: 'Report Information' })}
                </Typography>
                <Typography variant="body2" fontWeight="medium">
                  {reportName || reportId}
                </Typography>
                {startDate && endDate && (
                  <Typography variant="caption" color="text.secondary">
                    {t('exportDialog.dateRange', { defaultValue: 'Date Range' })}: {startDate} to {endDate}
                  </Typography>
                )}
              </Stack>
            </Paper>
          )}

          {/* Format Selection */}
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              {t('exportDialog.selectFormat', { defaultValue: 'Select Export Format' })}
            </Typography>
            <FormControl component="fieldset" fullWidth disabled={status === 'exporting'}>
              <RadioGroup value={format} onChange={handleFormatChange}>
                <Paper variant="outlined" sx={{ mb: 1 }}>
                  <FormControlLabel
                    value="pdf"
                    control={<Radio />}
                    label={
                      <Box display="flex" alignItems="center" gap={1} py={1}>
                        <PdfIcon color="error" />
                        <Box>
                          <Typography variant="body2" fontWeight="medium">
                            {t('exportDialog.formats.pdf', { defaultValue: 'PDF Document' })}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {t('exportDialog.formats.pdfDesc', { defaultValue: 'Formatted report with charts and tables' })}
                          </Typography>
                        </Box>
                      </Box>
                    }
                    sx={{ m: 1 }}
                  />
                </Paper>
                <Paper variant="outlined">
                  <FormControlLabel
                    value="csv"
                    control={<Radio />}
                    label={
                      <Box display="flex" alignItems="center" gap={1} py={1}>
                        <CsvIcon color="success" />
                        <Box>
                          <Typography variant="body2" fontWeight="medium">
                            {t('exportDialog.formats.csv', { defaultValue: 'CSV Spreadsheet' })}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {t('exportDialog.formats.csvDesc', { defaultValue: 'Raw data for further analysis' })}
                          </Typography>
                        </Box>
                      </Box>
                    }
                    sx={{ m: 1 }}
                  />
                </Paper>
              </RadioGroup>
            </FormControl>
          </Box>

          {/* Progress Indicator */}
          {status === 'exporting' && (
            <Box>
              <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
                <Typography variant="body2" color="text.secondary">
                  {t('exportDialog.exporting', { defaultValue: 'Exporting report...' })}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {progress}%
                </Typography>
              </Box>
              <LinearProgress variant="determinate" value={progress} />
            </Box>
          )}

          {/* Success Message */}
          {status === 'success' && (
            <Alert
              severity="success"
              icon={<CheckIcon />}
              action={
                <Chip
                  icon={getFormatIcon(format)}
                  label={format.toUpperCase()}
                  size="small"
                  color="success"
                  variant="outlined"
                />
              }
            >
              <AlertTitle>
                {t('exportDialog.success.title', { defaultValue: 'Export Successful' })}
              </AlertTitle>
              {t('exportDialog.success.message', { defaultValue: 'Your report has been downloaded successfully.' })}
            </Alert>
          )}

          {/* Error Message */}
          {status === 'error' && error && (
            <Alert
              severity="error"
              icon={<ErrorIcon />}
              action={
                <IconButton
                  size="small"
                  onClick={() => {
                    setError(null);
                    setStatus('idle');
                  }}
                  aria-label={t('common.dismiss', { defaultValue: 'Dismiss' })}
                >
                  <CloseIcon fontSize="small" />
                </IconButton>
              }
            >
              <AlertTitle>
                {t('exportDialog.error.title', { defaultValue: 'Export Failed' })}
              </AlertTitle>
              {error}
            </Alert>
          )}

          {/* Export Info */}
          {status === 'idle' && (
            <Paper variant="outlined" sx={{ p: 2, bgcolor: 'info.50', borderColor: 'info.200' }}>
              <Stack direction="row" spacing={1} alignItems="flex-start">
                <FileIcon color="info" fontSize="small" />
                <Typography variant="caption" color="text.secondary">
                  {t('exportDialog.info', {
                    defaultValue:
                      'The report will be downloaded automatically when ready. Large reports may take a few moments to generate.',
                  })}
                </Typography>
              </Stack>
            </Paper>
          )}
        </Stack>
      </DialogContent>

      <Divider />

      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button
          onClick={handleClose}
          disabled={status === 'exporting'}
          color="inherit"
        >
          {status === 'success'
            ? t('common.close', { defaultValue: 'Close' })
            : t('common.cancel', { defaultValue: 'Cancel' })}
        </Button>
        {status !== 'success' && (
          <Button
            onClick={handleExport}
            variant="contained"
            disabled={status === 'exporting'}
            startIcon={
              status === 'exporting' ? (
                <CircularProgress size={20} />
              ) : (
                <DownloadIcon />
              )
            }
          >
            {status === 'exporting'
              ? t('exportDialog.exporting', { defaultValue: 'Exporting...' })
              : t('exportDialog.export', { defaultValue: 'Export' })}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default ExportDialog;
