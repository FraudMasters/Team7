import React, { useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Alert,
  AlertTitle,
  Divider,
  Stack,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material';
import {
  Warning as WarningIcon,
  Description as FileIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material';
import type { DuplicateMatch } from '@/api/duplicates';

/**
 * DuplicateWarningDialog Component Props
 */
interface DuplicateWarningDialogProps {
  /** Whether the dialog is open */
  open: boolean;
  /** Callback when dialog is closed */
  onClose: () => void;
  /** Name of the file being uploaded */
  filename: string;
  /** List of duplicate matches */
  matches: DuplicateMatch[];
  /** Callback when user decides to proceed with upload */
  onProceed: () => void;
  /** Callback when user decides to cancel upload */
  onCancel: () => void;
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
 * Helper to get status color
 */
const getStatusColor = (status: string): 'default' | 'success' | 'warning' | 'error' => {
  switch (status.toLowerCase()) {
    case 'completed':
    case 'active':
      return 'success';
    case 'processing':
    case 'pending':
      return 'warning';
    case 'failed':
    case 'error':
      return 'error';
    default:
      return 'default';
  }
};

/**
 * Helper to get status label
 */
const getStatusLabel = (status: string): string => {
  switch (status.toLowerCase()) {
    case 'completed':
      return 'Обработано';
    case 'active':
      return 'Активно';
    case 'processing':
      return 'Обрабатывается';
    case 'pending':
      return 'Ожидает';
    case 'failed':
      return 'Ошибка';
    case 'error':
      return 'Ошибка';
    default:
      return status;
  }
};

/**
 * DuplicateWarningDialog Component
 *
 * Displays a warning dialog when a duplicate resume is detected before upload.
 * Shows information about existing matching resumes and allows the user to
 * either proceed with the upload or cancel it.
 *
 * Features:
 * - Clear warning message about duplicate detection
 * - List of existing matching resumes with filenames and timestamps
 * - Status indicators for each duplicate
 * - Proceed/Cancel action buttons
 * - Material-UI styled dialog with proper feedback
 *
 * @example
 * ```tsx
 * <DuplicateWarningDialog
 *   open={isWarningOpen}
 *   onClose={() => setIsWarningOpen(false)}
 *   filename="resume.pdf"
 *   matches={duplicateMatches}
 *   onProceed={handleProceed}
 *   onCancel={handleCancel}
 * />
 * ```
 */
const DuplicateWarningDialog: React.FC<DuplicateWarningDialogProps> = ({
  open,
  onClose,
  filename,
  matches,
  onProceed,
  onCancel,
}) => {
  /**
   * Handle proceed action
   */
  const handleProceed = useCallback(() => {
    onProceed();
    onClose();
  }, [onProceed, onClose]);

  /**
   * Handle cancel action
   */
  const handleCancel = useCallback(() => {
    onCancel();
    onClose();
  }, [onCancel, onClose]);

  const duplicateCount = matches.length;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      aria-labelledby="duplicate-warning-dialog-title"
      PaperProps={{
        sx: {
          borderRadius: 2,
        },
      }}
    >
      <DialogTitle
        id="duplicate-warning-dialog-title"
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1.5,
          pb: 2,
        }}
      >
        <WarningIcon sx={{ fontSize: 32, color: 'warning.main' }} />
        <Box>
          <Typography variant="h6" component="div" fontWeight={600}>
            Обнаружен дубликат
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Файл с таким содержимым уже существует в системе
          </Typography>
        </Box>
      </DialogTitle>

      <Divider />

      <DialogContent sx={{ py: 3 }}>
        <Stack spacing={3}>
          {/* Warning Alert */}
          <Alert severity="warning" variant="outlined">
            <AlertTitle>Возможный дубликат</AlertTitle>
            <Typography variant="body2">
              Резюме <strong>{filename}</strong> имеет идентичное содержимое с{' '}
              {duplicateCount === 1
                ? 'уже существующим файлом'
                : `${duplicateCount} существующими файлами`}
              . Загрузка дубликатов может привести к дублированию данных кандидатов.
            </Typography>
          </Alert>

          {/* Existing Files List */}
          <Box>
            <Typography variant="subtitle2" fontWeight={600} gutterBottom sx={{ mb: 2 }}>
              Существующие файлы ({duplicateCount}):
            </Typography>
            <List
              sx={{
                bgcolor: 'background.paper',
                border: 1,
                borderColor: 'divider',
                borderRadius: 1,
                py: 0,
              }}
            >
              {matches.map((match, index) => (
                <React.Fragment key={match.resume_id}>
                  {index > 0 && <Divider component="li" />}
                  <ListItem
                    sx={{
                      py: 2,
                      '&:hover': {
                        bgcolor: 'action.hover',
                      },
                    }}
                  >
                    <ListItemIcon>
                      <FileIcon sx={{ color: 'primary.main', fontSize: 28 }} />
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body1" fontWeight={500}>
                            {match.filename}
                          </Typography>
                          <Chip
                            label={getStatusLabel(match.status)}
                            size="small"
                            color={getStatusColor(match.status)}
                            sx={{ height: 20, fontSize: '0.7rem' }}
                          />
                        </Box>
                      }
                      secondary={
                        <Stack spacing={0.5} sx={{ mt: 0.5 }}>
                          <Typography variant="caption" color="text.secondary">
                            ID резюме: {match.resume_id}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Обнаружено: {formatTimestamp(match.detection_timestamp)}
                          </Typography>
                        </Stack>
                      }
                    />
                  </ListItem>
                </React.Fragment>
              ))}
            </List>
          </Box>

          {/* Recommendations */}
          <Alert severity="info" variant="outlined">
            <AlertTitle>Рекомендации</AlertTitle>
            <Typography variant="body2" component="div">
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                <li>Проверьте, не был ли этот файл уже загружен ранее</li>
                <li>
                  Если это новый кандидат, убедитесь, что файл отличается от существующих
                </li>
                <li>При необходимости можете продолжить загрузку</li>
              </ul>
            </Typography>
          </Alert>
        </Stack>
      </DialogContent>

      <Divider />

      <DialogActions sx={{ px: 3, py: 2 }}>
        <Stack direction="row" spacing={2} sx={{ width: '100%' }} justifyContent="flex-end">
          <Button onClick={handleCancel} variant="outlined" color="secondary" size="large">
            Отменить загрузку
          </Button>
          <Button
            onClick={handleProceed}
            variant="contained"
            color="warning"
            size="large"
            startIcon={<CheckIcon />}
          >
            Все равно загрузить
          </Button>
        </Stack>
      </DialogActions>
    </Dialog>
  );
};

export default DuplicateWarningDialog;
