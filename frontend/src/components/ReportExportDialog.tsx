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
  TableChart as ExcelIcon,
  Storage as CsvIcon,
} from '@mui/icons-material';
import { apiClient } from '@/api/client';
import { createReportsClient, ReportFormat } from '@/api/reports';
import type {
  PDFExportRequest,
  PDFExportResponse,
  CSVExportRequest,
  CSVExportResponse,
} from '@/api/reports';

/**
 * Export format options
 */
type ExportFormat = 'pdf' | 'excel' | 'csv';

/**
 * Export status states
 */
type ExportStatus = 'idle' | 'exporting' | 'success' | 'error';

/**
 * ReportExportDialog Component Props
 */
interface ReportExportDialogProps {
  /** Whether the dialog is open */
  open: boolean;
  /** Callback when dialog is closed */
  onClose: () => void;
  /** Report ID to export */
  reportId: string;
  /** Report data to export */
  reportData?: Record<string, any>;
  /** Optional callback when export completes successfully */
  onExportComplete?: (downloadUrl: string) => void;
  /** Optional organization ID */
  organizationId?: string;
}

/**
 * ReportExportDialog Component
 *
 * Provides a report export interface for generating PDF, Excel, and CSV files.
 * Features include:
 * - Format selection (PDF/Excel/CSV)
 * - Progress indication during export
 * - Automatic file download
 * - Comprehensive error handling
 * - Export status tracking
 *
 * @example
 * ```tsx
 * <ReportExportDialog
 *   open={isOpen}
 *   onClose={() => setIsOpen(false)}
 *   reportId="report-123"
 *   reportData={reportData}
 *   onExportComplete={(url) => console.log('Downloaded:', url)}
 * />
 * ```
 */
const ReportExportDialog: React.FC<ReportExportDialogProps> = ({
  open,
  onClose,
  reportId,
  reportData = {},
  onExportComplete,
  organizationId,
}) => {
  const { t } = useTranslation();
  const [format, setFormat] = useState<ExportFormat>('pdf');
  const [status, setStatus] = useState<ExportStatus>('idle');
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [expiresAt, setExpiresAt] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  const reportsClient = createReportsClient(apiClient);

  /**
   * Reset dialog state
   */
  const resetState = () => {
    setFormat('pdf');
    setStatus('idle');
    setDownloadUrl(null);
    setExpiresAt(null);
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
  const triggerDownload = (url: string) => {
    try {
      const link = document.createElement('a');
      link.href = url;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : t('reportExport.errors.downloadFailed');
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
      let response: PDFExportResponse | CSVExportResponse;

      if (format === 'pdf') {
        const pdfRequest: PDFExportRequest = {
          report_id: reportId,
          data: reportData,
          format: 'A4',
        };
        response = await reportsClient.exportReportPDF(pdfRequest);
      } else if (format === 'excel') {
        // Excel format uses CSV endpoint with specific mime type
        const csvRequest: CSVExportRequest = {
          metrics: Object.keys(reportData),
          filters: reportData,
          include_headers: true,
        };
        response = await reportsClient.exportReportCSV(csvRequest);
      } else {
        // CSV format
        const csvRequest: CSVExportRequest = {
          metrics: Object.keys(reportData),
          filters: reportData,
          include_headers: true,
        };
        response = await reportsClient.exportReportCSV(csvRequest);
      }

      clearInterval(progressInterval);
      setProgress(100);

      setDownloadUrl(response.download_url);
      setExpiresAt(response.expires_at);
      setStatus('success');

      // Trigger automatic download
      triggerDownload(response.download_url);

      if (onExportComplete) {
        onExportComplete(response.download_url);
      }
    } catch (err) {
      clearInterval(progressInterval);
      const errorMessage =
        err instanceof Error ? err.message : t('reportExport.errors.exportFailed');
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
    switch (selectedFormat) {
      case 'pdf':
        return <PdfIcon />;
      case 'excel':
        return <ExcelIcon />;
      case 'csv':
        return <CsvIcon />;
      default:
        return <FileIcon />;
    }
  };

  return (
    <Dialog
      open={open}
      onClose={status === 'exporting' ? undefined : handleClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 2,
          boxShadow: (theme) => theme.shadows[10],
        },
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <FileIcon color="primary" />
            <Typography variant="h6" component="div" fontWeight={600}>
              {t('reportExport.title', 'Export Report')}
            </Typography>
          </Box>
          {status !== 'exporting' && (
            <IconButton edge="end" onClick={handleClose} size="small">
              <CloseIcon />
            </IconButton>
          )}
        </Box>
      </DialogTitle>

      <Divider />

      <DialogContent sx={{ py: 3 }}>
        <Stack spacing={3}>
          {/* Description */}
          <Alert severity="info" variant="outlined">
            <AlertTitle>{t('reportExport.infoTitle', 'Export Your Report')}</AlertTitle>
            <Typography variant="body2">
              {t(
                'reportExport.infoMessage',
                'Choose your preferred format to download the report. The file will be generated and downloaded automatically.'
              )}
            </Typography>
          </Alert>

          {/* Format Selection */}
          {status === 'idle' && (
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                {t('reportExport.formatLabel', 'Select Format')}
              </Typography>
              <FormControl component="fieldset">
                <RadioGroup value={format} onChange={handleFormatChange}>
                  <FormControlLabel
                    value="pdf"
                    control={<Radio />}
                    label={
                      <Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <PdfIcon sx={{ fontSize: 18, color: 'error.main' }} />
                          <Typography variant="body2" fontWeight={500}>
                            PDF {t('reportExport.format', 'Format')}
                          </Typography>
                        </Box>
                        <Typography variant="caption" color="text.secondary">
                          {t(
                            'reportExport.pdfDescription',
                            'Professional document format, perfect for sharing and printing'
                          )}
                        </Typography>
                      </Box>
                    }
                  />
                  <FormControlLabel
                    value="excel"
                    control={<Radio />}
                    label={
                      <Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <ExcelIcon sx={{ fontSize: 18, color: 'success.main' }} />
                          <Typography variant="body2" fontWeight={500}>
                            Excel {t('reportExport.format', 'Format')}
                          </Typography>
                        </Box>
                        <Typography variant="caption" color="text.secondary">
                          {t(
                            'reportExport.excelDescription',
                            'Spreadsheet format with data analysis capabilities'
                          )}
                        </Typography>
                      </Box>
                    }
                  />
                  <FormControlLabel
                    value="csv"
                    control={<Radio />}
                    label={
                      <Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <CsvIcon sx={{ fontSize: 18, color: 'primary.main' }} />
                          <Typography variant="body2" fontWeight={500}>
                            CSV {t('reportExport.format', 'Format')}
                          </Typography>
                        </Box>
                        <Typography variant="caption" color="text.secondary">
                          {t(
                            'reportExport.csvDescription',
                            'Simple text format, compatible with all data tools'
                          )}
                        </Typography>
                      </Box>
                    }
                  />
                </RadioGroup>
              </FormControl>
            </Paper>
          )}

          {/* Exporting State */}
          {status === 'exporting' && (
            <Box sx={{ textAlign: 'center', py: 3 }}>
              <CircularProgress size={60} sx={{ mb: 3 }} />
              <Typography variant="h6" gutterBottom>
                {t('reportExport.exporting', 'Generating Report...')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t(
                  'reportExport.exportingMessage',
                  'Please wait while we prepare your report. This may take a few moments.'
                )}
              </Typography>
              <Box sx={{ width: '100%', maxWidth: 400, mx: 'auto' }}>
                <LinearProgress variant="determinate" value={progress} />
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  {progress}%
                </Typography>
              </Box>
            </Box>
          )}

          {/* Success State */}
          {status === 'success' && downloadUrl && (
            <Alert severity="success" variant="filled">
              <AlertTitle>{t('reportExport.successTitle', 'Export Complete!')}</AlertTitle>
              <Typography variant="body2">
                {t(
                  'reportExport.successMessage',
                  'Your report has been generated and downloaded successfully.'
                )}
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Chip
                  icon={<CheckIcon />}
                  label={`${format.toUpperCase()} ${t('reportExport.fileReady', 'File Ready')}`}
                  color="success"
                  size="small"
                />
              </Box>
            </Alert>
          )}

          {/* Error State */}
          {status === 'error' && (
            <Alert severity="error">
              <AlertTitle>{t('reportExport.errorTitle', 'Export Failed')}</AlertTitle>
              <Typography variant="body2">{error}</Typography>
            </Alert>
          )}

          {/* Download Info (shown when success) */}
          {status === 'success' && downloadUrl && (
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                {t('reportExport.downloadInfo', 'Download Information')}
              </Typography>
              <Stack spacing={1}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">
                    {t('reportExport.format', 'Format')}
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>
                    {format.toUpperCase()}
                  </Typography>
                </Box>
                {expiresAt && (
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">
                      {t('reportExport.expiresAt', 'Link Expires')}
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {new Date(expiresAt).toLocaleString()}
                    </Typography>
                  </Box>
                )}
                <Box sx={{ mt: 1 }}>
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<DownloadIcon />}
                    onClick={() => downloadUrl && triggerDownload(downloadUrl)}
                    fullWidth
                  >
                    {t('reportExport.downloadAgain', 'Download Again')}
                  </Button>
                </Box>
              </Stack>
            </Paper>
          )}
        </Stack>
      </DialogContent>

      <Divider />

      <DialogActions sx={{ px: 3, py: 2 }}>
        {status === 'idle' && (
          <>
            <Button onClick={handleClose} disabled={status === 'exporting'}>
              {t('common.cancel', 'Cancel')}
            </Button>
            <Button
              variant="contained"
              onClick={handleExport}
              disabled={status === 'exporting'}
              startIcon={<DownloadIcon />}
            >
              {t('reportExport.exportButton', 'Export Report')}
            </Button>
          </>
        )}

        {status === 'success' && (
          <Button variant="outlined" onClick={handleClose} startIcon={<CheckIcon />}>
            {t('common.done', 'Done')}
          </Button>
        )}

        {status === 'error' && (
          <>
            <Button onClick={handleClose}>{t('common.close', 'Close')}</Button>
            <Button
              variant="contained"
              onClick={handleExport}
              startIcon={<DownloadIcon />}
            >
              {t('reportExport.retryButton', 'Try Again')}
            </Button>
          </>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default ReportExportDialog;
