/**
 * Hiring Manager Candidate Detail Page
 *
 * Displays detailed candidate information for hiring manager review including:
 * - Candidate profile summary
 * - Evaluation summary with recruiter feedback and team consensus
 * - Match score visualization
 * - One-click approve/reject actions
 * - Mobile-optimized design for tablet access
 */

import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Container,
  Box,
  Typography,
  Paper,
  Grid,
  Chip,
  Stack,
  Divider,
  Button,
  Avatar,
  LinearProgress,
  Card,
  CardContent,
  IconButton,
  Tooltip,
  alpha,
  useTheme,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Person as PersonIcon,
  Star as StarIcon,
  TrendingUp as TrendingUpIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Warning as WarningIcon,
  Schedule as ScheduleIcon,
  Work as WorkIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  Help as HelpIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';

import { PageTransition } from '@components/mui/PageTransition';
import { ErrorState } from '@components/mui/ErrorState';
import LoadingSpinner from '@components/LoadingSpinner';
import OneClickActions from '@components/OneClickActions';
import {
  useHiringManagerEvaluation,
  useApproveCandidate,
  useRejectCandidate,
} from '@hooks/useHiringManagerData';
import type {
  EvaluationSummaryResponse,
  OneClickActionResult,
} from '@/api/hiringManager';

/**
 * Get color for match score
 */
function getMatchScoreColor(score: number): 'success' | 'warning' | 'error' {
  if (score >= 0.8) return 'success';
  if (score >= 0.6) return 'warning';
  return 'error';
}

/**
 * Get color for consensus chip
 */
function getConsensusColor(consensus: string | null): 'success' | 'error' | 'warning' | 'default' {
  switch (consensus) {
    case 'approve':
      return 'success';
    case 'reject':
      return 'error';
    case 'mixed':
      return 'warning';
    default:
      return 'default';
  }
}

/**
 * Get screening tier color
 */
function getTierColor(tier: string | null): 'success' | 'primary' | 'warning' | 'error' | 'default' {
  switch (tier) {
    case 'tier_1':
      return 'success';
    case 'tier_2':
      return 'primary';
    case 'tier_3':
      return 'warning';
    default:
      return 'default';
  }
}

/**
 * Generate avatar color from candidate name
 */
function getAvatarColor(name: string): string {
  const colors = [
    '#f44336', '#e91e63', '#9c27b0', '#673ab7', '#3f51b5',
    '#2196f3', '#00bcd4', '#009688', '#4caf50', '#8bc34a',
    '#cddc39', '#ffeb3b', '#ffc107', '#ff9800', '#ff5722'
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}

/**
 * Get candidate initials for avatar
 */
function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
  }
  return name.substring(0, 2).toUpperCase();
}

/**
 * Match Score Card Component
 */
interface MatchScoreCardProps {
  score: number | null;
  title: string;
}

function MatchScoreCard({ score, title }: MatchScoreCardProps) {
  const theme = useTheme();
  const { t } = useTranslation();

  if (score === null) {
    return (
      <Paper sx={{ p: 2.5, height: '100%' }}>
        <Typography variant="caption" color="text.secondary">
          {title}
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ mt: 1 }}>
          {t('candidateDetail.notAvailable', 'N/A')}
        </Typography>
      </Paper>
    );
  }

  const percentage = Math.round(score * 100);
  const color = getMatchScoreColor(score);

  return (
    <Paper
      sx={{
        p: 2.5,
        height: '100%',
        border: `2px solid ${theme.palette[color].main}`,
        bgcolor: alpha(theme.palette[color].main, 0.05),
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <TrendingUpIcon color={color} />
        <Typography variant="caption" color="text.secondary">
          {title}
        </Typography>
      </Box>
      <Typography variant="h4" fontWeight={700} color={`${color}.main`}>
        {percentage}%
      </Typography>
      <LinearProgress
        variant="determinate"
        value={percentage}
        color={color}
        sx={{ mt: 1.5, height: 8, borderRadius: 4 }}
      />
    </Paper>
  );
}

/**
 * Feedback Card Component
 */
interface FeedbackCardProps {
  recruiterName: string;
  rating: number | null;
  recommendation: string | null;
  notes: string | null;
  createdAt: string;
}

function FeedbackCard({ recruiterName, rating, recommendation, notes, createdAt }: FeedbackCardProps) {
  const { t } = useTranslation();
  const theme = useTheme();

  const getRecommendationIcon = () => {
    switch (recommendation) {
      case 'approve':
        return <ThumbUpIcon color="success" fontSize="small" />;
      case 'reject':
        return <ThumbDownIcon color="error" fontSize="small" />;
      default:
        return <HelpIcon color="warning" fontSize="small" />;
    }
  };

  const getRecommendationColor = (): 'success' | 'error' | 'warning' | 'default' => {
    switch (recommendation) {
      case 'approve':
        return 'success';
      case 'reject':
        return 'error';
      case 'maybe':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <Card variant="outlined" sx={{ mb: 1.5 }}>
      <CardContent sx={{ py: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 1.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Avatar sx={{ width: 32, height: 32, bgcolor: getAvatarColor(recruiterName), fontSize: '0.8rem' }}>
              {getInitials(recruiterName)}
            </Avatar>
            <Box>
              <Typography variant="subtitle2" fontWeight={600}>
                {recruiterName}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {new Date(createdAt).toLocaleDateString()}
              </Typography>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {rating !== null && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <StarIcon sx={{ fontSize: 16, color: 'warning.main' }} />
                <Typography variant="body2" fontWeight={600}>
                  {rating}
                </Typography>
              </Box>
            )}
            {recommendation && (
              <Chip
                icon={getRecommendationIcon()}
                label={recommendation.charAt(0).toUpperCase() + recommendation.slice(1)}
                size="small"
                color={getRecommendationColor()}
                variant="outlined"
                sx={{ height: 24 }}
              />
            )}
          </Box>
        </Box>
        {notes && (
          <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
            "{notes}"
          </Typography>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Consensus Summary Component
 */
interface ConsensusSummaryProps {
  consensusDetails: EvaluationSummaryResponse['consensus_details'];
}

function ConsensusSummary({ consensusDetails }: ConsensusSummaryProps) {
  const { t } = useTranslation();
  const theme = useTheme();

  const { consensus, approval_rate, rejection_rate, total_reviewers, unanimous } = consensusDetails;

  return (
    <Paper sx={{ p: 2.5 }}>
      <Typography variant="subtitle2" fontWeight={600} gutterBottom>
        {t('candidateDetail.teamConsensus', 'Team Consensus')}
      </Typography>

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
        {consensus ? (
          <Chip
            icon={consensus === 'approve' ? <CheckCircleIcon /> : consensus === 'reject' ? <CancelIcon /> : <WarningIcon />}
            label={consensus.charAt(0).toUpperCase() + consensus.slice(1)}
            color={getConsensusColor(consensus)}
            size="medium"
            sx={{ fontWeight: 600 }}
          />
        ) : (
          <Typography variant="body2" color="text.secondary">
            {t('candidateDetail.noConsensus', 'No consensus reached')}
          </Typography>
        )}
        {unanimous && (
          <Chip
            label={t('candidateDetail.unanimous', 'Unanimous')}
            size="small"
            color="primary"
            variant="outlined"
          />
        )}
      </Box>

      <Box sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
          <Typography variant="caption" color="text.secondary">
            {t('candidateDetail.approvalRate', 'Approval Rate')}: {Math.round(approval_rate * 100)}%
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {t('candidateDetail.rejectionRate', 'Rejection Rate')}: {Math.round(rejection_rate * 100)}%
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', height: 8, borderRadius: 4, overflow: 'hidden', bgcolor: 'grey.200' }}>
          <Box
            sx={{
              width: `${approval_rate * 100}%`,
              bgcolor: 'success.main',
            }}
          />
          <Box
            sx={{
              width: `${rejection_rate * 100}%`,
              bgcolor: 'error.main',
            }}
          />
        </Box>
      </Box>

      <Typography variant="caption" color="text.secondary">
        {t('candidateDetail.totalReviewers', '{{count}} reviewers', { count: total_reviewers })}
      </Typography>
    </Paper>
  );
}

/**
 * Hiring Manager Candidate Detail Page
 */
export function CandidateDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const theme = useTheme();

  // Fetch evaluation summary
  const {
    data: evaluationData,
    isLoading,
    isError,
    error,
    refetch,
  } = useHiringManagerEvaluation(id || '');

  // Extract data
  const evaluation = evaluationData?.data || evaluationData;

  // Handle action complete
  const handleActionComplete = (result: OneClickActionResult) => {
    if (result.success) {
      // Navigate back to review queue after successful action
      setTimeout(() => {
        navigate('/hiring-manager/review-queue');
      }, 1500);
    }
  };

  // Handle action error
  const handleActionError = (errorMessage: string) => {
    // Error is displayed in the OneClickActions component
  };

  // Loading state
  if (isLoading) {
    return (
      <PageTransition>
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <LoadingSpinner variant="page" message={t('candidateDetail.loading', 'Loading candidate details...')} />
        </Container>
      </PageTransition>
    );
  }

  // Error state
  if (isError || !id) {
    return (
      <PageTransition>
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <ErrorState
            title={t('candidateDetail.errorTitle', 'Failed to Load Candidate')}
            message={error?.message || t('candidateDetail.errorMessage', 'Unable to load candidate details. Please try again.')}
            onRetry={() => refetch()}
            retryText={t('common.retry', 'Retry')}
          />
        </Container>
      </PageTransition>
    );
  }

  // No candidate data
  if (!evaluation) {
    return (
      <PageTransition>
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <ErrorState
            title={t('candidateDetail.notFoundTitle', 'Candidate Not Found')}
            message={t('candidateDetail.notFoundMessage', 'The requested candidate could not be found.')}
            onRetry={() => navigate('/hiring-manager/review-queue')}
            retryText={t('candidateDetail.backToQueue', 'Back to Review Queue')}
          />
        </Container>
      </PageTransition>
    );
  }

  const candidateName = evaluation.candidate_name || t('candidateDetail.unnamedCandidate', 'Unknown Candidate');
  const avatarColor = getAvatarColor(candidateName);

  return (
    <PageTransition>
      <Container maxWidth="lg" sx={{ py: 3 }}>
        {/* Back Button */}
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/hiring-manager/review-queue')}
          sx={{ mb: 2, minHeight: 44 }}
        >
          {t('candidateDetail.backToQueue', 'Back to Review Queue')}
        </Button>

        {/* Header Section */}
        <Paper
          sx={{
            p: 3,
            mb: 3,
            background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.05)} 0%, ${alpha(theme.palette.primary.main, 0.02)} 100%)`,
          }}
        >
          <Grid container spacing={3} alignItems="center">
            {/* Avatar and Basic Info */}
            <Grid item xs={12} md={8}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                <Avatar
                  sx={{
                    width: 80,
                    height: 80,
                    bgcolor: avatarColor,
                    fontSize: '1.8rem',
                    fontWeight: 600,
                  }}
                >
                  {getInitials(candidateName)}
                </Avatar>
                <Box>
                  <Typography variant="h4" fontWeight={700} gutterBottom>
                    {candidateName}
                  </Typography>
                  {evaluation.vacancy_title && (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <WorkIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
                      <Typography variant="body1" color="text.secondary">
                        {evaluation.vacancy_title}
                      </Typography>
                    </Box>
                  )}
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                    <Chip
                      icon={<ScheduleIcon />}
                      label={evaluation.current_stage}
                      size="small"
                      variant="outlined"
                    />
                    {evaluation.screening_tier && (
                      <Chip
                        label={evaluation.screening_tier.replace('_', ' ').toUpperCase()}
                        size="small"
                        color={getTierColor(evaluation.screening_tier)}
                      />
                    )}
                    {evaluation.tags.slice(0, 3).map((tag) => (
                      <Chip key={tag} label={tag} size="small" sx={{ bgcolor: alpha(theme.palette.grey[500], 0.1) }} />
                    ))}
                  </Box>
                </Box>
              </Box>
            </Grid>

            {/* Match Score */}
            <Grid item xs={12} md={4}>
              <MatchScoreCard
                score={evaluation.match_score}
                title={t('candidateDetail.matchScore', 'Match Score')}
              />
            </Grid>
          </Grid>
        </Paper>

        {/* Main Content Grid */}
        <Grid container spacing={3}>
          {/* Left Column - Evaluation Summary */}
          <Grid item xs={12} md={8}>
            {/* Team Consensus */}
            <ConsensusSummary consensusDetails={evaluation.consensus_details} />

            {/* Recruiter Feedback */}
            <Paper sx={{ p: 2.5, mt: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="subtitle2" fontWeight={600}>
                  {t('candidateDetail.recruiterFeedback', 'Recruiter Feedback')} ({evaluation.feedback_summary.total_feedback_count})
                </Typography>
                {evaluation.feedback_summary.average_rating !== null && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <StarIcon sx={{ fontSize: 18, color: 'warning.main' }} />
                    <Typography variant="body2" fontWeight={600}>
                      {evaluation.feedback_summary.average_rating.toFixed(1)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t('candidateDetail.avgRating', 'avg')}
                    </Typography>
                  </Box>
                )}
              </Box>

              {/* Recommendations Breakdown */}
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                {evaluation.feedback_summary.recommendations_breakdown.approve > 0 && (
                  <Chip
                    icon={<ThumbUpIcon />}
                    label={`${evaluation.feedback_summary.recommendations_breakdown.approve} Approve`}
                    size="small"
                    color="success"
                    variant="outlined"
                  />
                )}
                {evaluation.feedback_summary.recommendations_breakdown.reject > 0 && (
                  <Chip
                    icon={<ThumbDownIcon />}
                    label={`${evaluation.feedback_summary.recommendations_breakdown.reject} Reject`}
                    size="small"
                    color="error"
                    variant="outlined"
                  />
                )}
                {evaluation.feedback_summary.recommendations_breakdown.maybe > 0 && (
                  <Chip
                    icon={<HelpIcon />}
                    label={`${evaluation.feedback_summary.recommendations_breakdown.maybe} Maybe`}
                    size="small"
                    color="warning"
                    variant="outlined"
                  />
                )}
              </Box>

              <Divider sx={{ my: 2 }} />

              {/* Feedback List */}
              {evaluation.feedback_summary.feedback_list.length > 0 ? (
                <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
                  {evaluation.feedback_summary.feedback_list.map((feedback, index) => (
                    <FeedbackCard
                      key={index}
                      recruiterName={feedback.recruiter_name}
                      rating={feedback.rating}
                      recommendation={feedback.recommendation}
                      notes={feedback.notes}
                      createdAt={feedback.created_at}
                    />
                  ))}
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 3 }}>
                  {t('candidateDetail.noFeedback', 'No recruiter feedback available yet.')}
                </Typography>
              )}
            </Paper>
          </Grid>

          {/* Right Column - Actions */}
          <Grid item xs={12} md={4}>
            {/* One-Click Actions */}
            <OneClickActions
              candidateId={id}
              candidateName={candidateName}
              currentStage={evaluation.current_stage}
              onActionComplete={handleActionComplete}
              onActionError={handleActionError}
              showRationaleExpanded={false}
            />

            {/* Quick Info Card */}
            <Card variant="outlined" sx={{ mt: 2 }}>
              <CardContent>
                <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                  {t('candidateDetail.quickInfo', 'Quick Info')}
                </Typography>
                <Stack spacing={1.5}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">
                      {t('candidateDetail.candidateId', 'Candidate ID')}
                    </Typography>
                    <Typography variant="body2" fontFamily="monospace" fontSize="0.75rem">
                      {id.substring(0, 8)}...
                    </Typography>
                  </Box>
                  {evaluation.evaluation_date && (
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="text.secondary">
                        {t('candidateDetail.evaluatedOn', 'Evaluated On')}
                      </Typography>
                      <Typography variant="body2">
                        {new Date(evaluation.evaluation_date).toLocaleDateString()}
                      </Typography>
                    </Box>
                  )}
                  {evaluation.vacancy_id && (
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="text.secondary">
                        {t('candidateDetail.vacancyId', 'Vacancy ID')}
                      </Typography>
                      <Typography variant="body2" fontFamily="monospace" fontSize="0.75rem">
                        {evaluation.vacancy_id.substring(0, 8)}...
                      </Typography>
                    </Box>
                  )}
                </Stack>
              </CardContent>
            </Card>

            {/* Help Tip */}
            <Box
              sx={{
                mt: 2,
                p: 2,
                bgcolor: alpha(theme.palette.info.main, 0.1),
                borderRadius: 2,
              }}
            >
              <Typography variant="body2" color="text.secondary">
                <strong>💡 {t('candidateDetail.tip.title', 'Tip:')}</strong>{' '}
                {t(
                  'candidateDetail.tip.content',
                  'Review the recruiter feedback and team consensus before making your decision. Your decision will be recorded and the candidate will be notified.'
                )}
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Container>
    </PageTransition>
  );
}

export default CandidateDetailPage;
