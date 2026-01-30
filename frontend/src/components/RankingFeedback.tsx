import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  IconButton,
  Chip,
  Stack,
  Alert,
  CircularProgress,
  Tooltip,
  Divider,
  Card,
  CardContent,
  Collapse,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  ThumbUp as ThumbUpIcon,
  ThumbUpOutlined as ThumbUpOutlinedIcon,
  ThumbDown as ThumbDownIcon,
  ThumbDownOutlined as ThumbDownOutlinedIcon,
  Send as SendIcon,
  Edit as EditIcon,
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
  Feedback as FeedbackIcon,
  Psychology as AIIcon,
  Star as StarIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import {
  RankingFeedbackRequest,
  RankingFeedbackResponse,
  RankedCandidate,
} from '../types/api';

interface RankingFeedbackProps {
  candidate: RankedCandidate;
  vacancyId: string;
  onFeedbackSubmitted?: (feedback: RankingFeedbackResponse) => void;
  disabled?: boolean;
  compact?: boolean;
}

/**
 * RankingFeedback Component
 *
 * Allows recruiters to approve or correct AI rankings with thumbs up/down
 * buttons and detailed comments. Supports both inline and dialog modes.
 */
const RankingFeedback: React.FC<RankingFeedbackProps> = ({
  candidate,
  vacancyId,
  onFeedbackSubmitted,
  disabled = false,
  compact = false,
}) => {
  const { t } = useTranslation();
  const [feedback, setFeedback] = useState<'approved' | 'rejected' | null>(null);
  const [comments, setComments] = useState('');
  const [correctedScore, setCorrectedScore] = useState<number | null>(null);
  const [correctedPosition, setCorrectedPosition] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const handleFeedbackSelect = (type: 'approved' | 'rejected') => {
    setFeedback(type);
    setError(null);
    if (!compact) {
      setExpanded(true);
    } else {
      setDialogOpen(true);
    }
  };

  const handleSubmitFeedback = async () => {
    if (!feedback) return;

    setSubmitting(true);
    setError(null);

    const feedbackRequest: RankingFeedbackRequest = {
      resume_id: candidate.resume_id,
      vacancy_id: vacancyId,
      was_correct: feedback === 'approved',
      recruiter_comments: comments || undefined,
      recruiter_corrected_score: correctedScore || undefined,
      recruiter_corrected_position: correctedPosition || undefined,
      feedback_reason: feedback === 'approved' ? 'ranking_correct' : 'ranking_incorrect',
    };

    try {
      const response = await axios.post<RankingFeedbackResponse>(
        '/api/ranking/feedback',
        feedbackRequest
      );

      setSubmitted(true);
      onFeedbackSubmitted?.(response.data);

      if (compact) {
        setDialogOpen(false);
      }
    } catch (err: any) {
      console.error('Error submitting ranking feedback:', err);
      setError(err.response?.data?.detail || t('feedback.submitError'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleReset = () => {
    setFeedback(null);
    setComments('');
    setCorrectedScore(null);
    setCorrectedPosition(null);
    setSubmitted(false);
    setError(null);
  };

  const getFeedbackContent = () => (
    <Stack spacing={2}>
      {/* Score Adjustment */}
      {feedback === 'rejected' && (
        <Box>
          <Typography variant="subtitle2" gutterBottom fontWeight={600}>
            {t('feedback.correctedScore')}
          </Typography>
          <Stack direction="row" spacing={2} alignItems="center">
            <TextField
              type="number"
              label={t('feedback.newScore')}
              value={correctedScore ?? ''}
              onChange={(e) => setCorrectedScore(e.target.value ? Number(e.target.value) : null)}
              inputProps={{ min: 0, max: 100 }}
              size="small"
              fullWidth
            />
            <Typography variant="body2" color="text.secondary">
              {t('feedback.originalScore')}: {Math.round(candidate.ranking_score)}
            </Typography>
          </Stack>
        </Box>
      )}

      {/* Position Adjustment */}
      {feedback === 'rejected' && (
        <Box>
          <Typography variant="subtitle2" gutterBottom fontWeight={600}>
            {t('feedback.correctedPosition')}
          </Typography>
          <TextField
            type="number"
            label={t('feedback.newPosition')}
            value={correctedPosition ?? ''}
            onChange={(e) => setCorrectedPosition(e.target.value ? Number(e.target.value) : null)}
            inputProps={{ min: 1 }}
            size="small"
            fullWidth
          />
        </Box>
      )}

      {/* Comments */}
      <Box>
        <Typography variant="subtitle2" gutterBottom fontWeight={600}>
          {t('feedback.comments')}
          <Typography component="span" variant="caption" color="text.secondary" sx={{ ml: 1 }}>
            ({t('feedback.optional')})
          </Typography>
        </Typography>
        <TextField
          multiline
          rows={3}
          placeholder={
            feedback === 'approved'
              ? t('feedback.approvalPlaceholder')
              : t('feedback.rejectionPlaceholder')
          }
          value={comments}
          onChange={(e) => setComments(e.target.value)}
          fullWidth
          size="small"
          disabled={submitting}
        />
      </Box>

      {/* Error Display */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Actions */}
      <Stack direction="row" spacing={1} justifyContent="flex-end">
        <Button
          onClick={() => {
            if (compact) {
              setDialogOpen(false);
            } else {
              setExpanded(false);
            }
            handleReset();
          }}
          disabled={submitting}
          size="small"
          color="inherit"
        >
          {t('feedback.cancel')}
        </Button>
        <Button
          onClick={handleSubmitFeedback}
          disabled={submitting || !feedback}
          variant="contained"
          startIcon={submitting ? <CircularProgress size={16} /> : <SendIcon />}
          size="small"
          color={feedback === 'approved' ? 'success' : 'warning'}
        >
          {t('feedback.submit')}
        </Button>
      </Stack>
    </Stack>
  );

  // Success state
  if (submitted) {
    return (
      <Paper
        sx={{
          p: 2,
          bgcolor: 'success.50',
          borderLeft: 4,
          borderColor: 'success.main',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CheckIcon color="success" />
          <Typography variant="body2" color="success.main" fontWeight={600}>
            {t('feedback.thankYou')}
          </Typography>
        </Box>
      </Paper>
    );
  }

  // Compact mode (opens dialog)
  if (compact) {
    return (
      <>
        <Stack direction="row" spacing={1} alignItems="center">
          <Tooltip title={t('feedback.approveRanking')}>
            <IconButton
              size="small"
              onClick={() => handleFeedbackSelect('approved')}
              disabled={disabled}
              color={feedback === 'approved' ? 'success' : 'default'}
            >
              {feedback === 'approved' ? (
                <ThumbUpIcon fontSize="small" />
              ) : (
                <ThumbUpOutlinedIcon fontSize="small" />
              )}
            </IconButton>
          </Tooltip>
          <Tooltip title={t('feedback.disagreeRanking')}>
            <IconButton
              size="small"
              onClick={() => handleFeedbackSelect('rejected')}
              disabled={disabled}
              color={feedback === 'rejected' ? 'error' : 'default'}
            >
              {feedback === 'rejected' ? (
                <ThumbDownIcon fontSize="small" />
              ) : (
                <ThumbDownOutlinedIcon fontSize="small" />
              )}
            </IconButton>
          </Tooltip>
        </Stack>

        <Dialog
          open={dialogOpen}
          onClose={() => {
            setDialogOpen(false);
            handleReset();
          }}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <FeedbackIcon />
              <Typography variant="h6">
                {feedback === 'approved'
                  ? t('feedback.approveTitle')
                  : t('feedback.correctTitle')}
              </Typography>
            </Box>
          </DialogTitle>
          <DialogContent>
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary">
                {t('feedback.candidate')}: <strong>{candidate.candidate_name}</strong>
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('feedback.currentScore')}: <strong>{Math.round(candidate.ranking_score)}</strong>
              </Typography>
            </Box>
            {getFeedbackContent()}
          </DialogContent>
        </Dialog>
      </>
    );
  }

  // Full inline mode
  return (
    <Card
      elevation={1}
      sx={{
        transition: 'all 0.2s',
        '&:hover': { elevation: 2 },
      }}
    >
      <CardContent>
        {/* Header */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            mb: expanded ? 2 : 0,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <FeedbackIcon color={feedback ? (feedback === 'approved' ? 'success' : 'warning') : 'action'} />
            <Typography variant="subtitle2" fontWeight={600}>
              {t('feedback.rankReview')}
            </Typography>
            {feedback && (
              <Chip
                icon={feedback === 'approved' ? <CheckIcon /> : <EditIcon />}
                label={feedback === 'approved' ? t('feedback.approved') : t('feedback.needsCorrection')}
                size="small"
                color={feedback === 'approved' ? 'success' : 'warning'}
              />
            )}
          </Box>

          <Stack direction="row" spacing={1} alignItems="center">
            <Tooltip title={t('feedback.approveRanking')}>
              <IconButton
                size="small"
                onClick={() => handleFeedbackSelect('approved')}
                disabled={disabled}
                color={feedback === 'approved' ? 'success' : 'default'}
                sx={{
                  bgcolor: feedback === 'approved' ? 'success.50' : 'action.hover',
                  '&:hover': { bgcolor: feedback === 'approved' ? 'success.100' : 'action.selected' },
                }}
              >
                {feedback === 'approved' ? (
                  <ThumbUpIcon fontSize="small" />
                ) : (
                  <ThumbUpOutlinedIcon fontSize="small" />
                )}
              </IconButton>
            </Tooltip>
            <Tooltip title={t('feedback.disagreeRanking')}>
              <IconButton
                size="small"
                onClick={() => handleFeedbackSelect('rejected')}
                disabled={disabled}
                color={feedback === 'rejected' ? 'error' : 'default'}
                sx={{
                  bgcolor: feedback === 'rejected' ? 'error.50' : 'action.hover',
                  '&:hover': { bgcolor: feedback === 'rejected' ? 'error.100' : 'action.selected' },
                }}
              >
                {feedback === 'rejected' ? (
                  <ThumbDownIcon fontSize="small" />
                ) : (
                  <ThumbDownOutlinedIcon fontSize="small" />
                )}
              </IconButton>
            </Tooltip>
          </Stack>
        </Box>

        {/* Expandable Content */}
        <Collapse in={expanded} timeout="auto" unmountOnExit>
          <Divider sx={{ mb: 2 }} />
          {getFeedbackContent()}
        </Collapse>
      </CardContent>
    </Card>
  );
};

export default RankingFeedback;
