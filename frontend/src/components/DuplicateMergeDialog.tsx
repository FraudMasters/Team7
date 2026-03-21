import React, { useState, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  CircularProgress,
  Alert,
  AlertTitle,
  Divider,
  Paper,
  Stack,
  RadioGroup,
  FormControlLabel,
  Radio,
  Chip,
  Grid,
  Card,
  CardContent,
  IconButton,
  Collapse,
} from '@mui/material';
import {
  MergeType as MergeIcon,
  Close as CloseIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  SwapHoriz as SwapIcon,
  Article as FileIcon,
} from '@mui/icons-material';
import { duplicatesClient } from '@/api/duplicates';
import type { DuplicateResumeItem, MergeCandidatesResponse } from '@/api/duplicates';

/**
 * Merge status states
 */
type MergeStatus = 'idle' | 'merging' | 'success' | 'error';

/**
 * DuplicateMergeDialog Component Props
 */
interface DuplicateMergeDialogProps {
  /** Whether the dialog is open */
  open: boolean;
  /** Callback when dialog is closed */
  onClose: () => void;
  /** Duplicate item to merge */
  duplicate: DuplicateResumeItem | null;
  /** Optional callback when merge completes successfully */
  onMergeComplete?: (result: MergeCandidatesResponse) => void;
  /** Optional custom merge reason */
  defaultReason?: string;
}

/**
 * Helper to format timestamp
 */
const formatTimestamp = (timestamp: string): string => {
  try {
    const date = new Date(timestamp);
    return new Intl.DateTimeFormat('ru-RU', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  } catch (e) {
    return timestamp;
  }
};

/**
 * DuplicateMergeDialog Component
 *
 * Provides an interface for merging duplicate candidate profiles with:
 * - Side-by-side comparison of both profiles
 * - Selection of primary profile to keep
 * - Preview of merge operation
 * - Merge execution with progress indication
 * - Success/error handling and feedback
 *
 * @example
 * ```tsx
 * <DuplicateMergeDialog
 *   open={isOpen}
 *   onClose={() => setIsOpen(false)}
 *   duplicate={duplicateItem}
 *   onMergeComplete={(result) => console.log('Merged:', result)}
 * />
 * ```
 */
const DuplicateMergeDialog: React.FC<DuplicateMergeDialogProps> = ({
  open,
  onClose,
  duplicate,
  onMergeComplete,
  defaultReason = 'Объединение профилей дубликатов через интерфейс',
}) => {
  const [primaryId, setPrimaryId] = useState<string>('original');
  const [status, setStatus] = useState<MergeStatus>('idle');
  const [mergeResult, setMergeResult] = useState<MergeCandidatesResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  /**
   * Reset dialog state
   */
  const resetState = useCallback(() => {
    setPrimaryId('original');
    setStatus('idle');
    setMergeResult(null);
    setError(null);
    setShowDetails(false);
  }, []);

  /**
   * Handle dialog close
   */
  const handleClose = useCallback(() => {
    if (status !== 'merging') {
      resetState();
      onClose();
    }
  }, [status, resetState, onClose]);

  /**
   * Handle primary profile selection change
   */
  const handlePrimaryChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setPrimaryId(event.target.value);
    setError(null);
  }, []);

  /**
   * Handle merge execution
   */
  const handleMerge = useCallback(async () => {
    if (!duplicate) {
      setError('Не указан дубликат для объединения');
      return;
    }

    setStatus('merging');
    setError(null);
    setMergeResult(null);

    try {
      // Determine which ID is primary and which is duplicate
      const primary = primaryId === 'original'
        ? duplicate.original_resume_id
        : duplicate.duplicate_resume_id;
      const duplicateId = primaryId === 'original'
        ? duplicate.duplicate_resume_id
        : duplicate.original_resume_id;

      const result = await duplicatesClient.mergeCandidates({
        primary_id: primary,
        duplicate_id: duplicateId,
        reason: defaultReason,
      });

      setMergeResult(result);
      setStatus('success');

      // Notify parent component
      if (onMergeComplete) {
        onMergeComplete(result);
      }

      // Auto-close after successful merge (after 2 seconds)
      setTimeout(() => {
        handleClose();
      }, 2000);
    } catch (err: any) {
      const errorMessage = err?.detail || err?.message || 'Не удалось выполнить слияние профилей';
      setError(errorMessage);
      setStatus('error');
    }
  }, [duplicate, primaryId, defaultReason, onMergeComplete, handleClose]);

  /**
   * Toggle details visibility
   */
  const handleToggleDetails = useCallback(() => {
    setShowDetails((prev) => !prev);
  }, []);

  // Return null if no duplicate
  if (!duplicate) {
    return null;
  }

  const originalFilename = duplicate.original_filename || 'Неизвестный файл';
  const duplicateFilename = duplicate.duplicate_filename || 'Неизвестный файл';
  const detectionTime = formatTimestamp(duplicate.detection_timestamp);

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      disableEscapeKeyDown={status === 'merging'}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <MergeIcon sx={{ mr: 1.5, fontSize: 28, color: 'primary.main' }} />
            <Box>
              <Typography variant="h6" fontWeight={600}>
                Объединение профилей
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Обнаружено: {detectionTime}
              </Typography>
            </Box>
          </Box>
          <IconButton
            onClick={handleClose}
            disabled={status === 'merging'}
            size="small"
            sx={{ color: 'text.secondary' }}
          >
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <Divider />

      <DialogContent sx={{ pt: 3 }}>
        {/* Info Alert */}
        <Alert severity="info" icon={<InfoIcon />} sx={{ mb: 3 }}>
          <AlertTitle>Выберите основной профиль</AlertTitle>
          <Typography variant="body2">
            Основной профиль будет сохранен, а данные из дубликата будут объединены с ним.
            Дубликат будет помечен как объединенный.
          </Typography>
        </Alert>

        {/* Profile Selection */}
        <RadioGroup value={primaryId} onChange={handlePrimaryChange}>
          <Grid container spacing={2} sx={{ mb: 3 }}>
            {/* Original Resume */}
            <Grid item xs={12} md={6}>
              <Card
                sx={{
                  cursor: status === 'merging' ? 'not-allowed' : 'pointer',
                  border: 2,
                  borderColor: primaryId === 'original' ? 'primary.main' : 'divider',
                  bgcolor: primaryId === 'original' ? 'primary.50' : 'background.paper',
                  transition: 'all 0.2s ease-in-out',
                  '&:hover': status !== 'merging'
                    ? {
                        boxShadow: 4,
                        transform: 'translateY(-2px)',
                      }
                    : undefined,
                }}
                onClick={() => status !== 'merging' && setPrimaryId('original')}
              >
                <CardContent>
                  <Stack spacing={2}>
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <FileIcon sx={{ mr: 1, color: 'text.secondary' }} />
                        <Typography variant="subtitle2" fontWeight={600}>
                          Оригинальное резюме
                        </Typography>
                      </Box>
                      <FormControlLabel
                        value="original"
                        control={<Radio size="small" />}
                        label=""
                        disabled={status === 'merging'}
                        sx={{ m: 0 }}
                      />
                    </Box>

                    <Divider />

                    <Box>
                      <Typography variant="body2" fontWeight={600} gutterBottom>
                        {originalFilename}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                        ID: {duplicate.original_resume_id.substring(0, 12)}...
                      </Typography>
                    </Box>

                    {primaryId === 'original' && (
                      <Chip
                        label="Основной профиль"
                        color="primary"
                        size="small"
                        icon={<CheckIcon />}
                      />
                    )}
                  </Stack>
                </CardContent>
              </Card>
            </Grid>

            {/* Duplicate Resume */}
            <Grid item xs={12} md={6}>
              <Card
                sx={{
                  cursor: status === 'merging' ? 'not-allowed' : 'pointer',
                  border: 2,
                  borderColor: primaryId === 'duplicate' ? 'primary.main' : 'divider',
                  bgcolor: primaryId === 'duplicate' ? 'primary.50' : 'background.paper',
                  transition: 'all 0.2s ease-in-out',
                  '&:hover': status !== 'merging'
                    ? {
                        boxShadow: 4,
                        transform: 'translateY(-2px)',
                      }
                    : undefined,
                }}
                onClick={() => status !== 'merging' && setPrimaryId('duplicate')}
              >
                <CardContent>
                  <Stack spacing={2}>
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <FileIcon sx={{ mr: 1, color: 'text.secondary' }} />
                        <Typography variant="subtitle2" fontWeight={600}>
                          Дубликат резюме
                        </Typography>
                      </Box>
                      <FormControlLabel
                        value="duplicate"
                        control={<Radio size="small" />}
                        label=""
                        disabled={status === 'merging'}
                        sx={{ m: 0 }}
                      />
                    </Box>

                    <Divider />

                    <Box>
                      <Typography variant="body2" fontWeight={600} gutterBottom>
                        {duplicateFilename}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                        ID: {duplicate.duplicate_resume_id.substring(0, 12)}...
                      </Typography>
                    </Box>

                    {primaryId === 'duplicate' && (
                      <Chip
                        label="Основной профиль"
                        color="primary"
                        size="small"
                        icon={<CheckIcon />}
                      />
                    )}
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </RadioGroup>

        {/* Swap Button */}
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
          <Button
            size="small"
            startIcon={<SwapIcon />}
            onClick={() => setPrimaryId((prev) => (prev === 'original' ? 'duplicate' : 'original'))}
            disabled={status === 'merging'}
            variant="outlined"
          >
            Поменять местами
          </Button>
        </Box>

        {/* Details Section */}
        <Paper sx={{ p: 2, bgcolor: 'grey.50', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="subtitle2" fontWeight={600}>
              Детали обнаружения
            </Typography>
            <Button size="small" onClick={handleToggleDetails}>
              {showDetails ? 'Скрыть' : 'Показать'}
            </Button>
          </Box>
          <Collapse in={showDetails}>
            <Divider sx={{ my: 1 }} />
            <Stack spacing={1}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="caption" color="text.secondary">
                  Хеш содержимого:
                </Typography>
                <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                  {duplicate.content_hash.substring(0, 24)}...
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="caption" color="text.secondary">
                  Время обнаружения:
                </Typography>
                <Typography variant="caption">
                  {detectionTime}
                </Typography>
              </Box>
              {duplicate.batch_job_id && (
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="caption" color="text.secondary">
                    ID пакетного задания:
                  </Typography>
                  <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                    {duplicate.batch_job_id.substring(0, 16)}...
                  </Typography>
                </Box>
              )}
            </Stack>
          </Collapse>
        </Paper>

        {/* Error Alert */}
        {error && (
          <Alert severity="error" icon={<WarningIcon />} sx={{ mb: 2 }}>
            <AlertTitle>Ошибка слияния</AlertTitle>
            <Typography variant="body2">{error}</Typography>
          </Alert>
        )}

        {/* Success Alert */}
        {status === 'success' && mergeResult && (
          <Alert severity="success" icon={<CheckIcon />}>
            <AlertTitle>Слияние выполнено успешно</AlertTitle>
            <Typography variant="body2">
              Профили объединены. ID слияния: {mergeResult.merge_id.substring(0, 12)}...
            </Typography>
            {mergeResult.can_undo && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Это слияние можно отменить в истории операций
              </Typography>
            )}
          </Alert>
        )}

        {/* Warning Alert */}
        {status === 'idle' && (
          <Alert severity="warning" icon={<WarningIcon />}>
            <Typography variant="body2">
              <strong>Внимание:</strong> Это действие объединит выбранные профили.
              Убедитесь, что выбран правильный основной профиль.
            </Typography>
          </Alert>
        )}
      </DialogContent>

      <Divider />

      <DialogActions sx={{ p: 2, gap: 1 }}>
        <Button
          onClick={handleClose}
          disabled={status === 'merging'}
          color="secondary"
          variant="outlined"
        >
          {status === 'success' ? 'Закрыть' : 'Отмена'}
        </Button>
        <Button
          onClick={handleMerge}
          disabled={status === 'merging' || status === 'success'}
          variant="contained"
          color="primary"
          startIcon={status === 'merging' ? <CircularProgress size={16} /> : <MergeIcon />}
        >
          {status === 'merging' ? 'Объединение...' : 'Объединить профили'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default DuplicateMergeDialog;
