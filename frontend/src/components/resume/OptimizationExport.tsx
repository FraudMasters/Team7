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
  InsertDriveFile as DocxIcon,
} from '@mui/icons-material';
import { resumeOptimizationClient } from '@/api/resumeOptimization';

/**
 * Export format options
 */
type ExportFormat = 'pdf' | 'docx';

/**
 * Export status states
 */
type ExportStatus = 'idle' | 'exporting' | 'success' | 'error';

/**
 * OptimizationExport Component Props
 */
interface OptimizationExportProps {
  /** Whether the dialog is open */
  open: boolean;
  /** Callback when dialog is closed */
  onClose: () => void;
  /** Resume ID to export optimization for */
  resumeId: string;
  /** Optional callback when export completes successfully */
  onExportComplete?: (format: ExportFormat) => void;
}

/**
 * OptimizationExport Component
 *
 * Provides a resume optimization export interface for sharing and documentation.
 * Features include:
 * - Format selection (PDF/DOCX)
 * - Progress indication during export
 * - Automatic file download
 * - Comprehensive error handling
 * - Export status tracking
 *
 * @example
 * ```tsx
 * <OptimizationExport
 *   open={isOpen}
 *   onClose={() => setIsOpen(false)}
 *   resumeId="resume-123"
 *   onExportComplete={(format) => console.log('Exported:', format)}
 * />
 * ```
 */
const OptimizationExport: React.FC<OptimizationExportProps> = ({
  open,
  onClose,
  resumeId,
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

      // Generate filename based on resume ID and format
      const timestamp = new Date().toISOString().split('T')[0];
      const extension = selectedFormat === 'pdf' ? 'pdf' : 'docx';
      link.download = `resume_optimization_${resumeId}_${timestamp}.${extension}`;

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : t('optimizationExport.errors.downloadFailed', { defaultValue: 'Download failed' });
      setError(errorMessage);
      setStatus('error');
    }
  };

  /**
   * Handle optimization export
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
      const blob = await resumeOptimizationClient.exportOptimization(resumeId, format);

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
          : t('optimizationExport.errors.exportFailed', { defaultValue: 'Failed to export optimization report' });
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
    return selectedFormat === 'pdf' ? <PdfIcon /> : <DocxIcon />;
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
              {t('optimizationExport.title', { defaultValue: 'Export Optimization Report' })}
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
            <AlertTitle>{t('optimizationExport.infoTitle', { defaultValue: 'Export optimization analysis' })}</AlertTitle>
            <Typography variant="body2">
              {t('optimizationExport.infoMessage', {
                defaultValue: 'Choose a format to export the optimization report. PDF provides a professional document with suggestions and analysis, while DOCX allows for further editing and customization.',
              })}
            </Typography>
          </Alert>

          {/* Resume Info */}
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom>
              {t('optimizationExport.resumeInfo', { defaultValue: 'Resume Information' })}
            </Typography>
            <Stack spacing={1}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="body2" color="text.secondary">
                  {t('optimizationExport.resumeId', { defaultValue: 'Resume ID' })}
                </Typography>
                <Typography variant="body2" fontWeight={600} sx={{ fontFamily: 'monospace' }}>
                  {resumeId}
                </Typography>
              </Box>
            </Stack>
          </Paper>

          {/* Format Selection */}
          {status === 'idle' && (
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                {t('optimizationExport.formatLabel', { defaultValue: 'Export Format' })}
              </Typography>
              <FormControl component="fieldset">
                <RadioGroup value={format} onChange={handleFormatChange}>
                  <FormControlLabel
                    value="pdf"
                    control={<Radio />}
                    label={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <PdfIcon color="error" fontSize="small" />
                        <Box>
                          <Typography variant="body2" fontWeight={500}>
                            PDF {t('optimizationExport.format', { defaultValue: 'Format' })}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {t('optimizationExport.pdfDescription', {
                              defaultValue: 'Professional document with suggestions, analysis, and formatting recommendations',
                            })}
                          </Typography>
                        </Box>
                      </Box>
                    }
                  />
                  <FormControlLabel
                    value="docx"
                    control={<Radio />}
                    label={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <DocxIcon color="primary" fontSize="small" />
                        <Box>
                          <Typography variant="body2" fontWeight={500}>
                            DOCX {t('optimizationExport.format', { defaultValue: 'Format' })}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {t('optimizationExport.docxDescription', {
                              defaultValue: 'Editable document for further customization and adjustments',
                            })}
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
          {status === 'exporting' && (
            <Box sx={{ textAlign: 'center', py: 3 }}>
              <CircularProgress size={60} sx={{ mb: 3 }} />
              <Typography variant="h6" gutterBottom>
                {t('optimizationExport.exporting', { defaultValue: 'Exporting Report...' })}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('optimizationExport.exportingMessage', {
                  defaultValue: 'Please wait while we generate your optimization report export.',
                })}
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
          {status === 'success' && (
            <Alert severity="success" variant="filled">
              <AlertTitle>{t('optimizationExport.successTitle', { defaultValue: 'Export Complete!' })}</AlertTitle>
              <Typography variant="body2">
                {t('optimizationExport.successMessage', {
                  defaultValue: 'Your optimization report has been exported successfully. The download should start automatically.',
                })}
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Chip
                  icon={getFormatIcon(format)}
                  label={`${format.toUpperCase()} ${t('optimizationExport.fileReady', { defaultValue: 'file ready' })}`}
                  color="success"
                  size="small"
                />
              </Box>
            </Alert>
          )}

          {/* Error State */}
          {status === 'error' && (
            <Alert severity="error">
              <AlertTitle>{t('optimizationExport.errorTitle', { defaultValue: 'Export Failed' })}</AlertTitle>
              <Typography variant="body2">{error}</Typography>
            </Alert>
          )}
        </Stack>
      </DialogContent>

      <Divider />

      <DialogActions sx={{ px: 3, py: 2 }}>
        {status === 'idle' && (
          <>
            <Button onClick={handleClose} disabled={status === 'exporting'}>
              {t('common.cancel', { defaultValue: 'Cancel' })}
            </Button>
            <Button
              variant="contained"
              onClick={handleExport}
              disabled={status === 'exporting'}
              startIcon={<DownloadIcon />}
            >
              {t('optimizationExport.exportButton', { defaultValue: 'Export Report' })}
            </Button>
          </>
        )}

        {status === 'success' && (
          <Button variant="outlined" onClick={handleClose} startIcon={<CheckIcon />}>
            {t('common.done', { defaultValue: 'Done' })}
          </Button>
        )}

        {status === 'error' && (
          <>
            <Button onClick={handleClose}>{t('common.close', { defaultValue: 'Close' })}</Button>
            <Button
              variant="contained"
              onClick={handleExport}
              startIcon={<DownloadIcon />}
            >
              {t('optimizationExport.retryButton', { defaultValue: 'Retry' })}
            </Button>
          </>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default OptimizationExport;
