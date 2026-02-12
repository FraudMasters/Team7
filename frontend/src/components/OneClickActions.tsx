import React, { useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Chip,
  Stack,
  Divider,
  Alert,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Collapse,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
} from '@/components/ui';
import { useTranslation } from 'react-i18next';
import {
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Send as SendIcon,
  Close as CloseIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import {
  useApproveCandidate,
  useRejectCandidate,
} from '@/hooks/useHiringManagerData';
import type {
  CandidateDecisionResponse,
  CandidateApprovalRequest,
  CandidateRejectionRequest,
} from '@/api/hiringManager';

/**
 * One-click action result interface
 */
interface OneClickActionResult {
  candidateId: string;
  success: boolean;
  decision: 'approved' | 'rejected';
  message?: string;
  error?: string;
  data?: CandidateDecisionResponse;
}

/**
 * Predefined rejection reasons
 */
const REJECTION_REASONS = [
  { value: 'skills_match', label: 'Insufficient skills match' },
  { value: 'experience', label: 'Not enough experience' },
  { value: 'culture_fit', label: 'Not a culture fit' },
  { value: 'salary_expectations', label: 'Salary expectations too high' },
  { value: 'location', label: 'Location mismatch' },
  { value: 'availability', label: 'Availability concerns' },
  { value: 'other', label: 'Other' },
] as const;

/**
 * OneClickActions Component Props
 */
interface OneClickActionsProps {
  /** Unique identifier for the candidate */
  candidateId: string;
  /** Candidate's name for display purposes */
  candidateName?: string;
  /** Current stage of the candidate */
  currentStage?: string;
  /** Callback when an action completes successfully */
  onActionComplete?: (result: OneClickActionResult) => void;
  /** Callback when an action fails */
  onActionError?: (error: string) => void;
  /** Available next stages for approval (optional) */
  availableStages?: Array<{ id: string; name: string }>;
  /** Show expanded rationale section by default */
  showRationaleExpanded?: boolean;
  /** Disabled state for all actions */
  disabled?: boolean;
  /** Compact mode for smaller screens */
  compact?: boolean;
  /** Show as stacked buttons (vertical) instead of side by side */
  stacked?: boolean;
  /** Custom minimum touch target height for accessibility */
  touchTargetHeight?: number;
}

/**
 * OneClickActions Component
 *
 * Provides one-click approve/reject functionality for hiring managers:
 * - Quick approve and reject buttons with optional rationale
 * - Mobile-optimized with proper touch targets (44px minimum)
 * - Loading states and success/error feedback
 * - Optional rejection reason selection
 * - Optional next stage selection for approval
 *
 * @example
 * ```tsx
 * <OneClickActions
 *   candidateId="candidate-123"
 *   candidateName="John Doe"
 *   currentStage="Phone Screen"
 *   onActionComplete={(result) => console.log('Action completed:', result)}
 * />
 * ```
 *
 * @example
 * ```tsx
 * // Compact stacked layout for mobile
 * <OneClickActions
 *   candidateId="candidate-123"
 *   compact
 *   stacked
 *   onActionComplete={handleActionComplete}
 * />
 * ```
 */
const OneClickActions: React.FC<OneClickActionsProps> = ({
  candidateId,
  candidateName,
  currentStage,
  onActionComplete,
  onActionError,
  availableStages,
  showRationaleExpanded = false,
  disabled = false,
  compact = false,
  stacked = false,
  touchTargetHeight = 44,
}) => {
  const { t } = useTranslation();

  // State management
  const [rationaleExpanded, setRationaleExpanded] = useState(showRationaleExpanded);
  const [rationale, setRationale] = useState('');
  const [rejectionReason, setRejectionReason] = useState<string>('');
  const [nextStage, setNextStage] = useState<string>('');
  const [notifyCandidate, setNotifyCandidate] = useState(true);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [pendingAction, setPendingAction] = useState<'approve' | 'reject' | null>(null);
  const [lastResult, setLastResult] = useState<OneClickActionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Mutations
  const approveMutation = useApproveCandidate();
  const rejectMutation = useRejectCandidate();

  // Derived state
  const isLoading = approveMutation.isPending || rejectMutation.isPending;
  const isApproved = lastResult?.decision === 'approved' && lastResult?.success;
  const isRejected = lastResult?.decision === 'rejected' && lastResult?.success;

  /**
   * Reset all form state
   */
  const resetState = useCallback(() => {
    setRationale('');
    setRejectionReason('');
    setNextStage('');
    setError(null);
    setLastResult(null);
  }, []);

  /**
   * Handle approve action
   */
  const handleApprove = useCallback(async () => {
    if (disabled || isLoading) {
      return;
    }

    setPendingAction('approve');
    setError(null);

    // Show confirmation dialog if rationale is expanded or next stage is selected
    if (rationaleExpanded || nextStage) {
      setConfirmDialogOpen(true);
      return;
    }

    // Direct approval without dialog
    await executeApproval();
  }, [disabled, isLoading, rationaleExpanded, nextStage]);

  /**
   * Execute the approval mutation
   */
  const executeApproval = useCallback(async () => {
    const request: CandidateApprovalRequest = {};
    if (rationale.trim()) {
      request.rationale = rationale.trim();
    }
    if (nextStage) {
      request.next_stage = nextStage;
    }

    try {
      const result = await approveMutation.mutateAsync({
        candidateId,
        request,
      });

      const actionResult: OneClickActionResult = {
        candidateId,
        success: true,
        decision: 'approved',
        message: result.message,
        data: result,
      };

      setLastResult(actionResult);
      onActionComplete?.(actionResult);
      setConfirmDialogOpen(false);
      setPendingAction(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : t('oneClickActions.approveError');
      setError(errorMessage);
      onActionError?.(errorMessage);

      const actionResult: OneClickActionResult = {
        candidateId,
        success: false,
        decision: 'approved',
        error: errorMessage,
      };
      setLastResult(actionResult);
    }
  }, [candidateId, rationale, nextStage, approveMutation, onActionComplete, onActionError, t]);

  /**
   * Handle reject action
   */
  const handleReject = useCallback(async () => {
    if (disabled || isLoading) {
      return;
    }

    setPendingAction('reject');
    setError(null);

    // Show confirmation dialog if rationale is expanded or rejection reason selected
    if (rationaleExpanded || rejectionReason) {
      setConfirmDialogOpen(true);
      return;
    }

    // Direct rejection without dialog
    await executeRejection();
  }, [disabled, isLoading, rationaleExpanded, rejectionReason]);

  /**
   * Execute the rejection mutation
   */
  const executeRejection = useCallback(async () => {
    const request: CandidateRejectionRequest = {};
    if (rationale.trim()) {
      request.rationale = rationale.trim();
    }
    if (rejectionReason) {
      request.rejection_reason = rejectionReason as CandidateRejectionRequest['rejection_reason'];
    }
    request.notify_candidate = notifyCandidate;

    try {
      const result = await rejectMutation.mutateAsync({
        candidateId,
        request,
      });

      const actionResult: OneClickActionResult = {
        candidateId,
        success: true,
        decision: 'rejected',
        message: result.message,
        data: result,
      };

      setLastResult(actionResult);
      onActionComplete?.(actionResult);
      setConfirmDialogOpen(false);
      setPendingAction(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : t('oneClickActions.rejectError');
      setError(errorMessage);
      onActionError?.(errorMessage);

      const actionResult: OneClickActionResult = {
        candidateId,
        success: false,
        decision: 'rejected',
        error: errorMessage,
      };
      setLastResult(actionResult);
    }
  }, [candidateId, rationale, rejectionReason, notifyCandidate, rejectMutation, onActionComplete, onActionError, t]);

  /**
   * Handle confirmation dialog confirm
   */
  const handleConfirmAction = useCallback(() => {
    if (pendingAction === 'approve') {
      executeApproval();
    } else if (pendingAction === 'reject') {
      executeRejection();
    }
  }, [pendingAction, executeApproval, executeRejection]);

  /**
   * Handle confirmation dialog cancel
   */
  const handleCancelAction = useCallback(() => {
    setConfirmDialogOpen(false);
    setPendingAction(null);
  }, []);

  /**
   * Toggle rationale section
   */
  const handleToggleRationale = useCallback(() => {
    setRationaleExpanded((prev) => !prev);
  }, []);

  // Determine if action buttons should be disabled
  const canApprove = !disabled && !isLoading && !isApproved && !isRejected;
  const canReject = !disabled && !isLoading && !isApproved && !isRejected;

  // Button style for touch accessibility
  const touchButtonSx = {
    minHeight: touchTargetHeight,
    minWidth: compact ? undefined : 120,
    px: compact ? 2 : 3,
  };

  return (
    <Paper
      elevation={compact ? 0 : 1}
      sx={{
        p: compact ? 1.5 : 2.5,
        bgcolor: isApproved
          ? 'success.50'
          : isRejected
            ? 'error.50'
            : 'background.paper',
        border: isApproved
          ? '2px solid'
          : isRejected
            ? '2px solid'
            : '1px solid',
        borderColor: isApproved
          ? 'success.main'
          : isRejected
            ? 'error.main'
            : 'divider',
        transition: 'all 0.3s ease',
      }}
    >
      <Stack spacing={2}>
        {/* Header with candidate info */}
        {!compact && candidateName && (
          <Box>
            <Typography variant="subtitle2" fontWeight={600}>
              {candidateName}
            </Typography>
            {currentStage && (
              <Typography variant="caption" color="text.secondary">
                {t('oneClickActions.currentStage', 'Current: {{stage}}', { stage: currentStage })}
              </Typography>
            )}
          </Box>
        )}

        {/* Action Buttons */}
        <Stack
          direction={stacked ? 'column' : 'row'}
          spacing={1.5}
          sx={{ width: '100%' }}
        >
          {/* Approve Button */}
          <Tooltip
            title={isApproved ? t('oneClickActions.alreadyApproved') : ''}
            arrow
          >
            <span style={{ width: stacked ? '100%' : 'auto', flex: stacked ? undefined : 1 }}>
              <Button
                variant="contained"
                color="success"
                fullWidth={stacked}
                disabled={!canApprove}
                onClick={handleApprove}
                startIcon={
                  isLoading && pendingAction === 'approve' ? (
                    <CircularProgress size={18} color="inherit" />
                  ) : (
                    <CheckCircleIcon />
                  )
                }
                sx={{
                  ...touchButtonSx,
                  width: stacked ? '100%' : undefined,
                  bgcolor: isApproved ? 'success.main' : undefined,
                  '&:hover': {
                    bgcolor: isApproved ? 'success.dark' : undefined,
                  },
                }}
              >
                {isLoading && pendingAction === 'approve'
                  ? t('oneClickActions.approving', 'Approving...')
                  : isApproved
                    ? t('oneClickActions.approved', 'Approved')
                    : t('oneClickActions.approve', 'Approve')}
              </Button>
            </span>
          </Tooltip>

          {/* Reject Button */}
          <Tooltip
            title={isRejected ? t('oneClickActions.alreadyRejected') : ''}
            arrow
          >
            <span style={{ width: stacked ? '100%' : 'auto', flex: stacked ? undefined : 1 }}>
              <Button
                variant="contained"
                color="error"
                fullWidth={stacked}
                disabled={!canReject}
                onClick={handleReject}
                startIcon={
                  isLoading && pendingAction === 'reject' ? (
                    <CircularProgress size={18} color="inherit" />
                  ) : (
                    <CancelIcon />
                  )
                }
                sx={{
                  ...touchButtonSx,
                  width: stacked ? '100%' : undefined,
                  bgcolor: isRejected ? 'error.main' : undefined,
                  '&:hover': {
                    bgcolor: isRejected ? 'error.dark' : undefined,
                  },
                }}
              >
                {isLoading && pendingAction === 'reject'
                  ? t('oneClickActions.rejecting', 'Rejecting...')
                  : isRejected
                    ? t('oneClickActions.rejected', 'Rejected')
                    : t('oneClickActions.reject', 'Reject')}
              </Button>
            </span>
          </Tooltip>
        </Stack>

        {/* Rationale Toggle */}
        {!isApproved && !isRejected && (
          <Button
            variant="text"
            size="small"
            onClick={handleToggleRationale}
            endIcon={rationaleExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            sx={{
              minHeight: 36,
              color: 'text.secondary',
              '&:hover': {
                bgcolor: 'action.hover',
              },
            }}
          >
            {rationaleExpanded
              ? t('oneClickActions.hideRationale', 'Hide Options')
              : t('oneClickActions.showRationale', 'Add Rationale / Options')}
          </Button>
        )}

        {/* Expanded Rationale Section */}
        <Collapse in={rationaleExpanded && !isApproved && !isRejected}>
          <Divider sx={{ mb: 2 }} />
          <Stack spacing={2}>
            {/* Rationale Text Field */}
            <TextField
              label={t('oneClickActions.rationaleLabel', 'Rationale (optional)')}
              placeholder={t(
                'oneClickActions.rationalePlaceholder',
                'Add a reason for your decision...'
              )}
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
              multiline
              rows={3}
              fullWidth
              size="small"
              disabled={disabled || isLoading}
              helperText={t(
                'oneClickActions.rationaleHelper',
                'This will be recorded with your decision'
              )}
            />

            {/* Next Stage Selection (for approval) */}
            {availableStages && availableStages.length > 0 && (
              <FormControl size="small" fullWidth disabled={disabled || isLoading}>
                <InputLabel id="next-stage-select-label">
                  {t('oneClickActions.nextStageLabel', 'Next Stage (for approval)')}
                </InputLabel>
                <Select
                  labelId="next-stage-select-label"
                  value={nextStage}
                  onChange={(e) => setNextStage(e.target.value)}
                  label={t('oneClickActions.nextStageLabel', 'Next Stage (for approval)')}
                >
                  <MenuItem value="">
                    <em>{t('common.default', 'Default')}</em>
                  </MenuItem>
                  {availableStages.map((stage) => (
                    <MenuItem key={stage.id} value={stage.id}>
                      {stage.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}

            {/* Rejection Reason Selection */}
            <FormControl size="small" fullWidth disabled={disabled || isLoading}>
              <InputLabel id="rejection-reason-select-label">
                {t('oneClickActions.rejectionReasonLabel', 'Rejection Reason')}
              </InputLabel>
              <Select
                labelId="rejection-reason-select-label"
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                label={t('oneClickActions.rejectionReasonLabel', 'Rejection Reason')}
              >
                <MenuItem value="">
                  <em>{t('common.optional', 'Optional')}</em>
                </MenuItem>
                {REJECTION_REASONS.map((reason) => (
                  <MenuItem key={reason.value} value={reason.value}>
                    {t(`rejectionReasons.${reason.value}`, reason.label)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Notify Candidate Toggle */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Chip
                label={notifyCandidate ? t('common.yes', 'Yes') : t('common.no', 'No')}
                size="small"
                color={notifyCandidate ? 'primary' : 'default'}
                onClick={() => setNotifyCandidate(!notifyCandidate)}
                sx={{ cursor: 'pointer' }}
              />
              <Typography variant="caption" color="text.secondary">
                {t('oneClickActions.notifyCandidate', 'Notify candidate of rejection')}
              </Typography>
            </Box>
          </Stack>
        </Collapse>

        {/* Error Alert */}
        <Collapse in={!!error}>
          <Alert
            severity="error"
            onClose={() => setError(null)}
            sx={{ mt: 1 }}
          >
            <Typography variant="body2">{error}</Typography>
          </Alert>
        </Collapse>

        {/* Success Alert */}
        <Collapse in={!!lastResult?.success && !!lastResult?.message}>
          <Alert severity="success" sx={{ mt: 1 }}>
            <Typography variant="body2">
              {lastResult?.message || (isApproved
                ? t('oneClickActions.approveSuccess', 'Candidate approved successfully')
                : t('oneClickActions.rejectSuccess', 'Candidate rejected'))}
            </Typography>
          </Alert>
        </Collapse>

        {/* Info tip for mobile */}
        {compact && !isApproved && !isRejected && (
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, mt: 1 }}>
            <InfoIcon sx={{ fontSize: 16, color: 'info.main', mt: 0.25 }} />
            <Typography variant="caption" color="text.secondary">
              {t(
                'oneClickActions.quickTip',
                'Quick decision: Just tap Approve or Reject. Add rationale for detailed feedback.'
              )}
            </Typography>
          </Box>
        )}
      </Stack>

      {/* Confirmation Dialog */}
      <Dialog
        open={confirmDialogOpen}
        onClose={handleCancelAction}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {pendingAction === 'approve' ? (
              <CheckCircleIcon color="success" />
            ) : (
              <CancelIcon color="error" />
            )}
            {pendingAction === 'approve'
              ? t('oneClickActions.confirmApprove', 'Confirm Approval')
              : t('oneClickActions.confirmReject', 'Confirm Rejection')}
          </Box>
          <IconButton onClick={handleCancelAction} size="small">
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            {candidateName
              ? t(
                  pendingAction === 'approve'
                    ? 'oneClickActions.confirmApproveMessage'
                    : 'oneClickActions.confirmRejectMessage',
                  {
                    name: candidateName,
                    defaultValue:
                      pendingAction === 'approve'
                        ? 'Approve {{name}} for the next stage?'
                        : 'Reject {{name}} from consideration?',
                  }
                )
              : pendingAction === 'approve'
                ? t('oneClickActions.confirmApproveGeneric', 'Approve this candidate?')
                : t('oneClickActions.confirmRejectGeneric', 'Reject this candidate?')}
          </Typography>

          {rationale && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                {t('oneClickActions.yourRationale', 'Your rationale:')}
              </Typography>
              <Typography variant="body2">{rationale}</Typography>
            </Box>
          )}

          {pendingAction === 'reject' && rejectionReason && (
            <Box sx={{ mt: 1 }}>
              <Chip
                size="small"
                label={REJECTION_REASONS.find((r) => r.value === rejectionReason)?.label || rejectionReason}
                color="error"
                variant="outlined"
              />
            </Box>
          )}

          {pendingAction === 'approve' && nextStage && availableStages && (
            <Box sx={{ mt: 1 }}>
              <Typography variant="body2" color="text.secondary">
                {t('oneClickActions.movingToStage', 'Moving to:')}{' '}
                <strong>{availableStages.find((s) => s.id === nextStage)?.name || nextStage}</strong>
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={handleCancelAction} disabled={isLoading}>
            {t('common.cancel', 'Cancel')}
          </Button>
          <Button
            variant="contained"
            color={pendingAction === 'approve' ? 'success' : 'error'}
            onClick={handleConfirmAction}
            disabled={isLoading}
            startIcon={
              isLoading ? (
                <CircularProgress size={18} color="inherit" />
              ) : pendingAction === 'approve' ? (
                <CheckCircleIcon />
              ) : (
                <CancelIcon />
              )
            }
            sx={{ minHeight: 44 }}
          >
            {isLoading
              ? pendingAction === 'approve'
                ? t('oneClickActions.approving', 'Approving...')
                : t('oneClickActions.rejecting', 'Rejecting...')
              : pendingAction === 'approve'
                ? t('oneClickActions.confirmApproveButton', 'Yes, Approve')
                : t('oneClickActions.confirmRejectButton', 'Yes, Reject')}
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};

export default OneClickActions;

// Export types for external use
export type { OneClickActionsProps, OneClickActionResult };
