import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useSkillFeedback } from '@/hooks/useSkillFeedback';
import {
  Box,
  IconButton,
  Tooltip,
  Snackbar,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  CircularProgress,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';

/**
 * Skill feedback widget props
 */
export interface SkillFeedbackWidgetProps {
  /** Resume ID for feedback submission */
  resumeId: string;
  /** Vacancy ID for feedback submission */
  vacancyId: string;
  /** The skill being evaluated */
  skill: string;
  /** Match result ID if available */
  matchResultId?: string;
  /** Confidence score from the ML model (0-1) */
  confidenceScore?: number;
  /** Callback fired after successful feedback submission */
  onFeedbackSubmitted?: () => void;
  /** Optional recruiter ID (if not using auth context) */
  recruiterId?: string;
  /** Compact mode - shows smaller buttons */
  compact?: boolean;
  /** Show labels on buttons */
  showLabels?: boolean;
}

/**
 * SkillFeedbackWidget Component
 *
 * Provides inline controls for recruiters to give feedback on skill detection:
 * - Thumbs up: Skill was correctly detected
 * - Thumbs down: Skill was incorrectly detected
 * - Plus button: Add a missing skill that the AI failed to extract
 *
 * Feedback is submitted to the backend API and can trigger model retraining.
 *
 * @example
 * ```tsx
 * <SkillFeedbackWidget
 *   resumeId="resume-123"
 *   vacancyId="vacancy-456"
 *   skill="Python"
 *   confidenceScore={0.95}
 * />
 * ```
 */
const SkillFeedbackWidget: React.FC<SkillFeedbackWidgetProps> = ({
  resumeId,
  vacancyId,
  skill,
  matchResultId,
  confidenceScore,
  onFeedbackSubmitted,
  recruiterId = 'default-recruiter', // TODO: Get from auth context
  compact = false,
  showLabels = false,
}) => {
  const { t } = useTranslation();
  const { submitFeedback, loading } = useSkillFeedback(undefined, undefined, false);

  // Snackbar state for success/error messages
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error'>('success');

  // Dialog state for adding missing skills
  const [dialogOpen, setDialogOpen] = useState(false);
  const [missingSkillName, setMissingSkillName] = useState('');
  const [submitting, setSubmitting] = useState(false);

  /**
   * Handle thumbs up click (skill correctly detected)
   */
  const handleThumbsUp = async () => {
    try {
      setSubmitting(true);

      await submitFeedback({
        feedback: [
          {
            resume_id: resumeId,
            vacancy_id: vacancyId,
            skill,
            was_correct: true,
            confidence_score: confidenceScore,
            feedback_source: 'recruiter_inline_widget',
            ...(matchResultId && { match_result_id: matchResultId }),
          },
        ],
      });

      setSnackbarMessage(t('skillFeedback.success.correctSkill', { skill }));
      setSnackbarSeverity('success');
      setSnackbarOpen(true);

      if (onFeedbackSubmitted) {
        onFeedbackSubmitted();
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : t('skillFeedback.error.submitFailed');
      setSnackbarMessage(errorMessage);
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Handle thumbs down click (skill incorrectly detected)
   */
  const handleThumbsDown = async () => {
    try {
      setSubmitting(true);

      await submitFeedback({
        feedback: [
          {
            resume_id: resumeId,
            vacancy_id: vacancyId,
            skill,
            was_correct: false,
            confidence_score: confidenceScore,
            feedback_source: 'recruiter_inline_widget',
            recruiter_correction: `Skill "${skill}" was incorrectly detected`,
            ...(matchResultId && { match_result_id: matchResultId }),
          },
        ],
      });

      setSnackbarMessage(t('skillFeedback.success.incorrectSkill', { skill }));
      setSnackbarSeverity('success');
      setSnackbarOpen(true);

      if (onFeedbackSubmitted) {
        onFeedbackSubmitted();
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : t('skillFeedback.error.submitFailed');
      setSnackbarMessage(errorMessage);
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Handle add missing skill dialog open
   */
  const handleOpenDialog = () => {
    setDialogOpen(true);
    setMissingSkillName('');
  };

  /**
   * Handle add missing skill dialog close
   */
  const handleCloseDialog = () => {
    setDialogOpen(false);
    setMissingSkillName('');
  };

  /**
   * Handle missing skill submission
   */
  const handleAddMissingSkill = async () => {
    if (!missingSkillName.trim()) {
      setSnackbarMessage(t('skillFeedback.error.emptySkillName'));
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
      return;
    }

    try {
      setSubmitting(true);

      await submitFeedback({
        feedback: [
          {
            resume_id: resumeId,
            vacancy_id: vacancyId,
            skill: missingSkillName.trim(),
            was_correct: false,
            confidence_score: 0.0, // Model completely missed this skill
            feedback_source: 'recruiter_manual_addition',
            recruiter_correction: `Missing skill "${missingSkillName.trim()}" was added by recruiter`,
            actual_skill: missingSkillName.trim(),
            ...(matchResultId && { match_result_id: matchResultId }),
          },
        ],
      });

      setSnackbarMessage(t('skillFeedback.success.addedSkill', { skill: missingSkillName }));
      setSnackbarSeverity('success');
      setSnackbarOpen(true);

      handleCloseDialog();

      if (onFeedbackSubmitted) {
        onFeedbackSubmitted();
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : t('skillFeedback.error.submitFailed');
      setSnackbarMessage(errorMessage);
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Handle snackbar close
   */
  const handleSnackbarClose = () => {
    setSnackbarOpen(false);
  };

  const buttonSize = compact ? 'small' : 'medium';
  const iconSize = compact ? 'small' : 'medium';

  return (
    <>
      <Box
        sx={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: compact ? 0.5 : 1,
        }}
      >
        {/* Thumbs Up Button */}
        <Tooltip title={t('skillFeedback.tooltip.correctSkill')}>
          <span>
            <IconButton
              onClick={handleThumbsUp}
              disabled={submitting || loading}
              size={buttonSize}
              color="success"
              aria-label={t('skillFeedback.aria.correctSkill', { skill })}
            >
              {submitting ? (
                <CircularProgress size={iconSize === 'small' ? 16 : 20} />
              ) : (
                <Icon name="thumbs-up" size={iconSize} />
              )}
            </IconButton>
          </span>
        </Tooltip>

        {/* Thumbs Down Button */}
        <Tooltip title={t('skillFeedback.tooltip.incorrectSkill')}>
          <span>
            <IconButton
              onClick={handleThumbsDown}
              disabled={submitting || loading}
              size={buttonSize}
              color="error"
              aria-label={t('skillFeedback.aria.incorrectSkill', { skill })}
            >
              {submitting ? (
                <CircularProgress size={iconSize === 'small' ? 16 : 20} />
              ) : (
                <Icon name="thumbs-down" size={iconSize} />
              )}
            </IconButton>
          </span>
        </Tooltip>

        {/* Add Missing Skill Button */}
        <Tooltip title={t('skillFeedback.tooltip.addMissingSkill')}>
          <span>
            <IconButton
              onClick={handleOpenDialog}
              disabled={submitting || loading}
              size={buttonSize}
              color="primary"
              aria-label={t('skillFeedback.aria.addMissingSkill')}
            >
              <Icon name="plus-circle" size={iconSize} />
            </IconButton>
          </span>
        </Tooltip>

        {showLabels && (
          <Typography variant="caption" sx={{ ml: 1, color: 'text.secondary' }}>
            {t('skillFeedback.label.giveFeedback')}
          </Typography>
        )}
      </Box>

      {/* Add Missing Skill Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>{t('skillFeedback.dialog.addMissingSkill')}</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
            {t('skillFeedback.dialog.description')}
          </Typography>
          <TextField
            autoFocus
            fullWidth
            label={t('skillFeedback.dialog.skillNameLabel')}
            placeholder={t('skillFeedback.dialog.skillNamePlaceholder')}
            value={missingSkillName}
            onChange={(e) => setMissingSkillName(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && missingSkillName.trim()) {
                handleAddMissingSkill();
              }
            }}
            disabled={submitting}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog} disabled={submitting}>
            {t('common.cancel')}
          </Button>
          <Button
            onClick={handleAddMissingSkill}
            variant="contained"
            color="primary"
            disabled={submitting || !missingSkillName.trim()}
          >
            {submitting ? <CircularProgress size={20} /> : t('common.add')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success/Error Snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={4000}
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleSnackbarClose} severity={snackbarSeverity} sx={{ width: '100%' }}>
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </>
  );
};

/**
 * Display name for debugging
 */
SkillFeedbackWidget.displayName = 'SkillFeedbackWidget';

export default SkillFeedbackWidget;
