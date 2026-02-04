import React, { useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Stack,
  CircularProgress,
  Alert,
  AlertTitle,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Divider,
} from '@mui/material';
import {
  Warning as WarningIcon,
  DeleteForever as DeleteForeverIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { gdprClient } from '@/api/gdpr';
import type {
  DataDeletionRequest,
  DataDeletionRequestResponse,
  ApiError,
} from '@/types/api';

/**
 * DataDeletionRequest Component Props
 */
interface DataDeletionRequestProps {
  /** Resume ID for the candidate data to delete */
  resumeId: string;
  /** Requester email address */
  requesterEmail?: string;
  /** Callback when deletion request is submitted successfully */
  onRequestSubmitted?: (response: DataDeletionRequestResponse) => void;
  /** Whether to show the component in a dialog */
  open?: boolean;
  /** Callback when dialog is closed */
  onClose?: () => void;
  /** Whether the component is read-only (view only mode) */
  readOnly?: boolean;
}

/**
 * DataDeletionRequest Component
 *
 * GDPR-compliant data deletion request form (right to be forgotten):
 * - Displays clear warnings about permanent data deletion
 * - Requires user confirmation before submitting request
 * - Collects reason for deletion request
 * - Shows detailed information about what will be deleted
 * - Handles loading, error, and success states gracefully
 *
 * IMPORTANT: This action cannot be undone. All candidate data including:
 * - Resume and CV files
 * - Personal information (name, email, phone)
 * - Hiring stage history
 * - Notes and comments
 * - Tags and activities
 * - All associated records
 *
 * @example
 * ```tsx
 * <DataDeletionRequest
 *   resumeId="resume-uuid"
 *   requesterEmail="user@example.com"
 *   onRequestSubmitted={(response) => console.log('Request submitted:', response.id)}
 * />
 *
 * // As a dialog
 * <DataDeletionRequest
 *   resumeId="resume-uuid"
 *   open={showDialog}
 *   onClose={() => setShowDialog(false)}
 *   requesterEmail="user@example.com"
 * />
 * ```
 */
const DataDeletionRequest: React.FC<DataDeletionRequestProps> = ({
  resumeId,
  requesterEmail,
  onRequestSubmitted,
  open = false,
  onClose,
  readOnly = false,
}) => {
  const { t } = useTranslation();
  const [reason, setReason] = useState('');
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  /**
   * Reset form state
   */
  const resetForm = useCallback(() => {
    setReason('');
    setShowConfirmation(false);
    setError(null);
    setSuccessMessage(null);
  }, []);

  /**
   * Handle initiating deletion request (first step)
   */
  const handleInitiateRequest = useCallback(() => {
    if (!reason.trim()) {
      setError('Please provide a reason for the deletion request.');
      return;
    }

    setError(null);
    setShowConfirmation(true);
  }, [reason]);

  /**
   * Handle confirming and submitting deletion request
   */
  const handleSubmitRequest = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const requestData: DataDeletionRequest = {
        resume_id: resumeId,
        reason: reason.trim(),
        requester_email: requesterEmail,
      };

      const response = await gdprClient.createDataDeletionRequest(requestData);

      setSuccessMessage('Data deletion request submitted successfully.');
      onRequestSubmitted?.(response);

      // Close dialog after a delay
      setTimeout(() => {
        resetForm();
        onClose?.();
      }, 2000);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to submit deletion request. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [resumeId, reason, requesterEmail, onRequestSubmitted, resetForm, onClose]);

  /**
   * Handle canceling the request
   */
  const handleCancel = useCallback(() => {
    resetForm();
    onClose?.();
  }, [resetForm, onClose]);

  /**
   * Handle going back from confirmation dialog
   */
  const handleBack = useCallback(() => {
    setShowConfirmation(false);
  }, []);

  const formContent = (
    <Stack spacing={3}>
      {/* Error Message */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Success Message */}
      {successMessage && (
        <Alert
          severity="success"
          icon={<CheckCircleIcon fontSize="inherit" />}
          onClose={() => setSuccessMessage(null)}
        >
          {successMessage}
        </Alert>
      )}

      {/* Warning Alert */}
      {!successMessage && (
        <Alert severity="error" icon={<WarningIcon fontSize="inherit"()}>
          <AlertTitle>{t('dataDeletion.warningTitle')}</AlertTitle>
          {t('dataDeletion.warningMessage')}
        </Alert>
      )}

      {/* What will be deleted */}
      {!successMessage && (
        <Paper variant="outlined" sx={{ p: 2, bgcolor: 'error.dark', color: 'error.contrastText' }}>
          <Typography variant="subtitle2" fontWeight={600} gutterBottom>
            {t('dataDeletion.willBeDeleted')}
          </Typography>
          <Box component="ul" sx={{ pl: 2, m: 0, typography: 'body2' }}>
            <li>{t('dataDeletion.items.resume')}</li>
            <li>{t('dataDeletion.items.personalInfo')}</li>
            <li>{t('dataDeletion.items.hiringHistory')}</li>
            <li>{t('dataDeletion.items.notes')}</li>
            <li>{t('dataDeletion.items.tags')}</li>
            <li>{t('dataDeletion.items.activities')}</li>
            <li>{t('dataDeletion.items.allRecords')}</li>
          </Box>
        </Paper>
      )}

      {/* Reason Input */}
      {!successMessage && (
        <TextField
          multiline
          rows={4}
          label={t('dataDeletion.reasonLabel')}
          placeholder={t('dataDeletion.reasonPlaceholder')}
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          disabled={readOnly || loading || showConfirmation}
          fullWidth
          required
          helperText={t('dataDeletion.reasonHint')}
        />
      )}

      {/* Actions */}
      {!successMessage && !showConfirmation && (
        <Stack direction="row" spacing={2} justifyContent="flex-end">
          <Button
            variant="outlined"
            onClick={handleCancel}
            disabled={loading}
          >
            {t('dataDeletion.cancel')}
          </Button>
          <Button
            variant="contained"
            color="error"
            startIcon={<DeleteForeverIcon />}
            onClick={handleInitiateRequest}
            disabled={!reason.trim() || readOnly || loading}
          >
            {t('dataDeletion.requestDeletion')}
          </Button>
        </Stack>
      )}

      {/* Confirmation Dialog */}
      {showConfirmation && !successMessage && (
        <Alert severity="warning">
          <AlertTitle>{t('dataDeletion.confirmTitle')}</AlertTitle>
          <Typography variant="body2" gutterBottom>
            {t('dataDeletion.confirmMessage')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1, fontWeight: 500 }}>
            {t('dataDeletion.confirmWarning')}
          </Typography>
          <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
            <Button
              variant="outlined"
              size="small"
              onClick={handleBack}
              disabled={loading}
            >
              {t('dataDeletion.back')}
            </Button>
            <Button
              variant="contained"
              color="error"
              size="small"
              startIcon={loading ? <CircularProgress size={16} /> : <DeleteForeverIcon />}
              onClick={handleSubmitRequest}
              disabled={loading}
            >
              {loading ? t('dataDeletion.submitting') : t('dataDeletion.confirmDelete')}
            </Button>
          </Stack>
        </Alert>
      )}

      {/* Information about GDPR rights */}
      {!successMessage && (
        <Box sx={{ mt: 2 }}>
          <Divider sx={{ mb: 2 }} />
          <Typography variant="caption" color="text.secondary">
            {t('dataDeletion.gdprInfo')}
          </Typography>
        </Box>
      )}
    </Stack>
  );

  // If not used as a dialog, render directly
  if (!open && !onClose) {
    return (
      <Paper variant="outlined" sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <DeleteForeverIcon color="error" sx={{ mr: 1 }} />
          <Typography variant="h6" fontWeight={600}>
            {t('dataDeletion.title')}
          </Typography>
        </Box>
        {formContent}
      </Paper>
    );
  }

  // Render as dialog
  return (
    <Dialog
      open={open}
      onClose={handleCancel}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: { borderRadius: 2 }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <DeleteForeverIcon color="error" sx={{ mr: 1 }} />
          <Typography variant="h6" component="div" fontWeight={600}>
            {t('dataDeletion.title')}
          </Typography>
        </Box>
      </DialogTitle>
      <DialogContent>
        {formContent}
      </DialogContent>
    </Dialog>
  );
};

export default DataDeletionRequest;
