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
} from '@mui/material';
import {
  Download as DownloadIcon,
  Close as CloseIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Description as FileIcon,
} from '@mui/icons-material';
import { gdprClient } from '@/api/gdpr';
import type { PersonalDataExport } from '@/types/api';

/**
 * Export format options
 */
type ExportFormat = 'json' | 'csv';

/**
 * Export status states
 */
type ExportStatus = 'idle' | 'exporting' | 'success' | 'error';

/**
 * DataExportDialog Component Props
 */
interface DataExportDialogProps {
  /** Whether the dialog is open */
  open: boolean;
  /** Callback when dialog is closed */
  onClose: () => void;
  /** Resume ID to export data for */
  resumeId: string;
  /** Optional callback when export completes successfully */
  onExportComplete?: (data: PersonalDataExport) => void;
  /** Optional organization ID for organization-wide export */
  organizationId?: string;
}

/**
 * DataExportDialog Component
 *
 * Provides a GDPR-compliant data export interface implementing the right to portability.
 * Features include:
 * - Format selection (JSON/CSV)
 * - Progress indication during export
 * - Automatic file download
 * - Comprehensive error handling
 * - Export history and status
 *
 * @example
 * ```tsx
 * <DataExportDialog
 *   open={isOpen}
 *   onClose={() => setIsOpen(false)}
 *   resumeId="resume-123"
 *   onExportComplete={(data) => console.log('Exported:', data)}
 * />
 * ```
 */
const DataExportDialog: React.FC<DataExportDialogProps> = ({
  open,
  onClose,
  resumeId,
  onExportComplete,
  organizationId,
}) => {
  const { t } = useTranslation();
  const [format, setFormat] = useState<ExportFormat>('json');
  const [status, setStatus] = useState<ExportStatus>('idle');
  const [exportData, setExportData] = useState<PersonalDataExport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  /**
   * Reset dialog state
   */
  const resetState = () => {
    setFormat('json');
    setStatus('idle');
    setExportData(null);
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
  const triggerDownload = (data: PersonalDataExport, selectedFormat: ExportFormat) => {
    try {
      let content: string;
      let mimeType: string;
      let filename: string;

      if (selectedFormat === 'json') {
        // Create JSON content with all export data
        const jsonContent = {
          resume_id: data.resume_id,
          export_date: new Date().toISOString(),
          resume: {
            filename: data.filename,
            raw_text: data.raw_text,
            language: data.language,
            status: data.status,
            created_at: data.created_at,
            updated_at: data.updated_at,
          },
          hiring_stages: data.hiring_stages,
          notes: data.notes,
          tags: data.tags,
          activities: data.activities,
        };
        content = JSON.stringify(jsonContent, null, 2);
        mimeType = 'application/json';
        filename = `export_${data.resume_id}_${new Date().toISOString().split('T')[0]}.json`;
      } else {
        // Create CSV content
        const csvRows: string[] = [];

        // Header
        csvRows.push('Type,ID,Date,Description');

        // Hiring stages
        data.hiring_stages.forEach((stage) => {
          csvRows.push(
            `HiringStage,${stage.id},${stage.created_at},"${stage.stage_name} - ${stage.vacancy_id}"`
          );
        });

        // Notes
        data.notes.forEach((note) => {
          const escapedContent = note.content.replace(/"/g, '""');
          csvRows.push(`Note,${note.id},${note.created_at},"${escapedContent}"`);
        });

        // Tags
        data.tags.forEach((tag) => {
          csvRows.push(`Tag,${tag.id},${tag.created_at},"${tag.tag_name}"`);
        });

        // Activities
        data.activities.forEach((activity) => {
          csvRows.push(
            `Activity,${activity.id},${activity.created_at},"${activity.activity_type} - ${activity.description}"`
          );
        });

        content = csvRows.join('\n');
        mimeType = 'text/csv';
        filename = `export_${data.resume_id}_${new Date().toISOString().split('T')[0]}.csv`;
      }

      // Create blob and download link
      const blob = new Blob([content], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : t('dataExport.errors.downloadFailed');
      setError(errorMessage);
      setStatus('error');
    }
  };

  /**
   * Handle data export
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
      const data = await gdprClient.exportPersonalData(resumeId, format);

      clearInterval(progressInterval);
      setProgress(100);

      setExportData(data);
      setStatus('success');

      // Trigger automatic download
      triggerDownload(data, format);

      if (onExportComplete) {
        onExportComplete(data);
      }
    } catch (err) {
      clearInterval(progressInterval);
      const errorMessage =
        err instanceof Error ? err.message : t('dataExport.errors.exportFailed');
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
              {t('dataExport.title')}
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
            <AlertTitle>{t('dataExport.infoTitle')}</AlertTitle>
            <Typography variant="body2">{t('dataExport.infoMessage')}</Typography>
          </Alert>

          {/* Format Selection */}
          {status === 'idle' && (
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                {t('dataExport.formatLabel')}
              </Typography>
              <FormControl component="fieldset">
                <RadioGroup value={format} onChange={handleFormatChange}>
                  <FormControlLabel
                    value="json"
                    control={<Radio />}
                    label={
                      <Box>
                        <Typography variant="body2" fontWeight={500}>
                          JSON {t('dataExport.format')}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {t('dataExport.jsonDescription')}
                        </Typography>
                      </Box>
                    }
                  />
                  <FormControlLabel
                    value="csv"
                    control={<Radio />}
                    label={
                      <Box>
                        <Typography variant="body2" fontWeight={500}>
                          CSV {t('dataExport.format')}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {t('dataExport.csvDescription')}
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
                {t('dataExport.exporting')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('dataExport.exportingMessage')}
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
          {status === 'success' && exportData && (
            <Alert severity="success" variant="filled">
              <AlertTitle>{t('dataExport.successTitle')}</AlertTitle>
              <Typography variant="body2">{t('dataExport.successMessage')}</Typography>
              <Box sx={{ mt: 2 }}>
                <Chip
                  icon={<CheckIcon />}
                  label={`${format.toUpperCase()} ${t('dataExport.fileReady')}`}
                  color="success"
                  size="small"
                />
              </Box>
            </Alert>
          )}

          {/* Error State */}
          {status === 'error' && (
            <Alert severity="error">
              <AlertTitle>{t('dataExport.errorTitle')}</AlertTitle>
              <Typography variant="body2">{error}</Typography>
            </Alert>
          )}

          {/* Data Summary (shown when success) */}
          {status === 'success' && exportData && (
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                {t('dataExport.dataSummary')}
              </Typography>
              <Stack spacing={1}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">
                    {t('dataExport.hiringStages')}
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>
                    {exportData.hiring_stages.length}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">
                    {t('dataExport.notes')}
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>
                    {exportData.notes.length}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">
                    {t('dataExport.tags')}
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>
                    {exportData.tags.length}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">
                    {t('dataExport.activities')}
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>
                    {exportData.activities.length}
                  </Typography>
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
              {t('common.cancel')}
            </Button>
            <Button
              variant="contained"
              onClick={handleExport}
              disabled={status === 'exporting'}
              startIcon={<DownloadIcon />}
            >
              {t('dataExport.exportButton')}
            </Button>
          </>
        )}

        {status === 'success' && (
          <Button variant="outlined" onClick={handleClose} startIcon={<CheckIcon />}>
            {t('common.done')}
          </Button>
        )}

        {status === 'error' && (
          <>
            <Button onClick={handleClose}>{t('common.close')}</Button>
            <Button
              variant="contained"
              onClick={handleExport}
              startIcon={<DownloadIcon />}
            >
              {t('dataExport.retryButton')}
            </Button>
          </>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default DataExportDialog;
