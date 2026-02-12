/**
 * Evaluation Summary Component
 *
 * Displays comprehensive evaluation results for hiring managers showing
 * recruiter feedback, team consensus, and match scores to help make
 * informed approval/rejection decisions.
 */

import React from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Stack,
  Divider,
  Grid,
  LinearProgress,
  Alert,
  AlertTitle,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Collapse,
  IconButton,
  Tooltip,
  Avatar,
  AvatarGroup,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';
import type {
  EvaluationSummaryResponse,
  FeedbackSummary,
  ConsensusDetails,
  RecruiterFeedback,
} from '@/api/hiringManager';

interface EvaluationSummaryProps {
  evaluation: EvaluationSummaryResponse;
  showActions?: boolean;
}

/**
 * Get consensus color based on consensus type
 */
function getConsensusColor(consensus: string | null): 'success' | 'warning' | 'error' | 'default' {
  if (!consensus) return 'default';
  if (consensus === 'approve' || consensus === 'strong_approve') return 'success';
  if (consensus === 'mixed' || consensus === 'maybe') return 'warning';
  if (consensus === 'reject' || consensus === 'strong_reject') return 'error';
  return 'default';
}

/**
 * Get match score color based on value
 */
function getScoreColor(score: number): 'success' | 'warning' | 'error' {
  if (score >= 0.7) return 'success';
  if (score >= 0.5) return 'warning';
  return 'error';
}

/**
 * Get rating display component
 */
function RatingDisplay({ rating }: { rating: number | null }) {
  const { t } = useTranslation();

  if (rating === null) {
    return (
      <Typography variant="caption" color="secondary">
        {t('evaluation.noRating', { defaultValue: 'Not rated' })}
      </Typography>
    );
  }

  const stars = [];
  for (let i = 1; i <= 5; i++) {
    const filled = i <= Math.round(rating);
    stars.push(
      <Icon
        key={i}
        name={filled ? 'star' : 'star'}
        size="small"
        color={filled ? 'warning' : 'muted'}
        style={{ opacity: filled ? 1 : 0.3 }}
      />
    );
  }

  return (
    <Box display="flex" alignItems="center" gap={0.5}>
      {stars}
      <Typography variant="caption" color="secondary" sx={{ ml: 0.5 }}>
        ({rating.toFixed(1)})
      </Typography>
    </Box>
  );
}

/**
 * Consensus Summary Card Component
 */
interface ConsensusCardProps {
  consensus: ConsensusDetails;
}

function ConsensusCard({ consensus }: ConsensusCardProps) {
  const { t } = useTranslation();
  const consensusColor = getConsensusColor(consensus.consensus);

  const getConsensusLabel = (consensusType: string | null): string => {
    if (!consensusType) return t('evaluation.noConsensus', { defaultValue: 'No Consensus' });

    const labels: Record<string, string> = {
      strong_approve: t('evaluation.strongApprove', { defaultValue: 'Strong Approve' }),
      approve: t('evaluation.approve', { defaultValue: 'Approve' }),
      maybe: t('evaluation.maybe', { defaultValue: 'Maybe' }),
      mixed: t('evaluation.mixed', { defaultValue: 'Mixed' }),
      reject: t('evaluation.reject', { defaultValue: 'Reject' }),
      strong_reject: t('evaluation.strongReject', { defaultValue: 'Strong Reject' }),
    };

    return labels[consensusType] || consensusType;
  };

  return (
    <Paper
      sx={{
        p: 2,
        textAlign: 'center',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <Box display="flex" alignItems="center" justifyContent="center" mb={1}>
        {consensus.unanimous ? (
          <Icon name="users" color="success" />
        ) : (
          <Icon name="users" color="muted" />
        )}
      </Box>
      <Chip
        label={getConsensusLabel(consensus.consensus)}
        color={consensusColor}
        size="small"
        sx={{ mb: 1 }}
      />
      <Typography variant="caption" color="secondary" gutterBottom>
        {t('evaluation.teamConsensus', { defaultValue: 'Team Consensus' })}
      </Typography>
      <Box sx={{ mt: 'auto' }}>
        <Grid container spacing={1}>
          <Grid item xs={6}>
            <Typography variant="body2" color="success.main">
              {Math.round(consensus.approval_rate * 100)}%
            </Typography>
            <Typography variant="caption" color="secondary">
              {t('evaluation.approve', { defaultValue: 'Approve' })}
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="body2" color="error.main">
              {Math.round(consensus.rejection_rate * 100)}%
            </Typography>
            <Typography variant="caption" color="secondary">
              {t('evaluation.reject', { defaultValue: 'Reject' })}
            </Typography>
          </Grid>
        </Grid>
      </Box>
    </Paper>
  );
}

/**
 * Match Score Card Component
 */
interface MatchScoreCardProps {
  matchScore: number | null;
  screeningTier: string | null;
}

function MatchScoreCard({ matchScore, screeningTier }: MatchScoreCardProps) {
  const { t } = useTranslation();

  if (matchScore === null) {
    return (
      <Paper
        sx={{
          p: 2,
          textAlign: 'center',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <Typography variant="h4" color="secondary">
          --
        </Typography>
        <Typography variant="caption" color="secondary">
          {t('evaluation.noScore', { defaultValue: 'No Score' })}
        </Typography>
      </Paper>
    );
  }

  const percentage = Math.round(matchScore * 100);
  const color = getScoreColor(matchScore);

  return (
    <Paper
      sx={{
        p: 2,
        textAlign: 'center',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <Box display="flex" alignItems="center" justifyContent="center" mb={1}>
        <Icon name="target" color={color} />
      </Box>
      <Typography variant="h4" color={`${color}.main`}>
        {percentage}%
      </Typography>
      <Typography variant="caption" color="secondary" gutterBottom>
        {t('evaluation.matchScore', { defaultValue: 'Match Score' })}
      </Typography>
      {screeningTier && (
        <Chip
          label={screeningTier}
          size="small"
          variant="outlined"
          sx={{ mt: 1 }}
        />
      )}
      <LinearProgress
        variant="determinate"
        value={percentage}
        color={color}
        sx={{ mt: 'auto', pt: 1 }}
      />
    </Paper>
  );
}

/**
 * Recommendations Breakdown Card
 */
interface RecommendationsCardProps {
  feedbackSummary: FeedbackSummary;
}

function RecommendationsCard({ feedbackSummary }: RecommendationsCardProps) {
  const { t } = useTranslation();
  const { recommendations_breakdown } = feedbackSummary;
  const total = Object.values(recommendations_breakdown).reduce((a, b) => a + b, 0);

  if (total === 0) {
    return (
      <Paper sx={{ p: 2, textAlign: 'center' }}>
        <Typography variant="caption" color="secondary">
          {t('evaluation.noRecommendations', { defaultValue: 'No recommendations yet' })}
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="subtitle2" gutterBottom>
        {t('evaluation.recommendations', { defaultValue: 'Recommendations Breakdown' })}
      </Typography>
      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
        <Chip
          icon={<Icon name="thumbs-up" size="small" />}
          label={`${t('evaluation.approve', { defaultValue: 'Approve' })}: ${recommendations_breakdown.approve}`}
          color="success"
          size="small"
          variant={recommendations_breakdown.approve > 0 ? 'filled' : 'outlined'}
        />
        <Chip
          icon={<Icon name="help-circle" size="small" />}
          label={`${t('evaluation.maybe', { defaultValue: 'Maybe' })}: ${recommendations_breakdown.maybe}`}
          color="warning"
          size="small"
          variant={recommendations_breakdown.maybe > 0 ? 'filled' : 'outlined'}
        />
        <Chip
          icon={<Icon name="thumbs-down" size="small" />}
          label={`${t('evaluation.reject', { defaultValue: 'Reject' })}: ${recommendations_breakdown.reject}`}
          color="error"
          size="small"
          variant={recommendations_breakdown.reject > 0 ? 'filled' : 'outlined'}
        />
      </Stack>
    </Paper>
  );
}

/**
 * Expandable Feedback Section Component
 */
interface FeedbackSectionProps {
  title: string;
  icon: React.ReactNode;
  itemCount: number;
  children: React.ReactNode;
  defaultExpanded?: boolean;
}

function FeedbackSection({
  title,
  icon,
  itemCount,
  children,
  defaultExpanded = false,
}: FeedbackSectionProps) {
  const [expanded, setExpanded] = React.useState(defaultExpanded);

  return (
    <Paper sx={{ p: 2 }}>
      <Box
        display="flex"
        alignItems="center"
        justifyContent="space-between"
        onClick={() => setExpanded(!expanded)}
        sx={{ cursor: 'pointer' }}
      >
        <Box display="flex" alignItems="center" gap={1}>
          {icon}
          <Typography variant="subtitle2">
            {title} {itemCount > 0 && `(${itemCount})`}
          </Typography>
        </Box>
        <IconButton size="small">
          <Icon name={expanded ? 'chevron-up' : 'chevron-down'} />
        </IconButton>
      </Box>
      <Collapse in={expanded}>
        <Box sx={{ mt: 2 }}>
          {children}
        </Box>
      </Collapse>
    </Paper>
  );
}

/**
 * Individual Feedback Item Component
 */
interface FeedbackItemProps {
  feedback: RecruiterFeedback;
}

function FeedbackItem({ feedback }: FeedbackItemProps) {
  const { t } = useTranslation();
  const formattedDate = new Date(feedback.created_at).toLocaleDateString();

  const getRecommendationIcon = (recommendation: string | null): React.ReactNode => {
    if (!recommendation) return <Icon name="minus-circle" color="muted" size="small" />;

    const icons: Record<string, React.ReactNode> = {
      approve: <Icon name="thumbs-up" color="success" size="small" />,
      maybe: <Icon name="help-circle" color="warning" size="small" />,
      reject: <Icon name="thumbs-down" color="error" size="small" />,
    };

    return icons[recommendation] || <Icon name="minus-circle" color="muted" size="small" />;
  };

  return (
    <Card variant="outlined" sx={{ mb: 1 }}>
      <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box flex={1}>
            <Box display="flex" alignItems="center" gap={1} mb={0.5}>
              <Avatar sx={{ width: 24, height: 24, fontSize: '0.75rem' }}>
                {feedback.recruiter_name.charAt(0).toUpperCase()}
              </Avatar>
              <Typography variant="subtitle2">
                {feedback.recruiter_name}
              </Typography>
              <Typography variant="caption" color="secondary">
                {formattedDate}
              </Typography>
            </Box>
            <Box display="flex" alignItems="center" gap={2}>
              {getRecommendationIcon(feedback.recommendation)}
              <RatingDisplay rating={feedback.rating} />
            </Box>
            {feedback.notes && (
              <Typography variant="body2" color="secondary" sx={{ mt: 1 }}>
                {feedback.notes}
              </Typography>
            )}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

/**
 * Tags Section Component
 */
interface TagsSectionProps {
  tags: string[];
}

function TagsSection({ tags }: TagsSectionProps) {
  const { t } = useTranslation();

  if (tags.length === 0) return null;

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="subtitle2" gutterBottom>
        {t('evaluation.tags', { defaultValue: 'Tags' })}
      </Typography>
      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
        {tags.map((tag) => (
          <Chip
            key={tag}
            label={tag}
            size="small"
            variant="outlined"
          />
        ))}
      </Stack>
    </Paper>
  );
}

/**
 * Evaluation Summary Component
 */
export function EvaluationSummary({ evaluation, showActions = true }: EvaluationSummaryProps) {
  const { t } = useTranslation();

  const {
    candidate_name,
    vacancy_title,
    match_score,
    feedback_summary,
    consensus_details,
    screening_tier,
    tags,
    evaluation_date,
  } = evaluation;

  const hasConsensus = consensus_details.consensus !== null;
  const isPositiveConsensus = ['approve', 'strong_approve'].includes(consensus_details.consensus ?? '');
  const isNegativeConsensus = ['reject', 'strong_reject'].includes(consensus_details.consensus ?? '');

  const formattedEvalDate = new Date(evaluation_date).toLocaleDateString();

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper sx={{ p: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={8}>
            <Typography variant="h6">
              {t('evaluation.title', { defaultValue: 'Evaluation Summary' })}
            </Typography>
            {vacancy_title && (
              <Typography variant="body2" color="secondary">
                {t('evaluation.forPosition', { defaultValue: 'For position' })}: {vacancy_title}
              </Typography>
            )}
          </Grid>
          <Grid item xs={12} sm={4} sx={{ textAlign: { xs: 'left', sm: 'right' } }}>
            <Typography variant="caption" color="secondary">
              {t('evaluation.evaluatedOn', { defaultValue: 'Evaluated on' })}: {formattedEvalDate}
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      {/* Consensus Alert */}
      {hasConsensus && (
        <Alert
          severity={isPositiveConsensus ? 'success' : isNegativeConsensus ? 'error' : 'warning'}
          icon={
            isPositiveConsensus
              ? <Icon name="check-circle" />
              : isNegativeConsensus
                ? <Icon name="x-circle" />
                : <Icon name="alert-triangle" />
          }
        >
          <AlertTitle>
            {isPositiveConsensus
              ? t('evaluation.positiveConsensus', { defaultValue: 'Team Recommends Approval' })
              : isNegativeConsensus
                ? t('evaluation.negativeConsensus', { defaultValue: 'Team Recommends Rejection' })
                : t('evaluation.mixedConsensus', { defaultValue: 'Team Has Mixed Opinions' })}
          </AlertTitle>
          <Typography variant="body2">
            {consensus_details.unanimous
              ? t('evaluation.unanimousDecision', {
                  defaultValue: 'All {{count}} reviewers agree',
                  count: consensus_details.total_reviewers,
                })
              : t('evaluation.splitDecision', {
                  defaultValue: '{{approve}}% approve, {{reject}}% reject',
                  approve: Math.round(consensus_details.approval_rate * 100),
                  reject: Math.round(consensus_details.rejection_rate * 100),
                })}
          </Typography>
        </Alert>
      )}

      {/* Score Cards Grid */}
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6} md={4}>
          <MatchScoreCard matchScore={match_score} screeningTier={screening_tier} />
        </Grid>
        <Grid item xs={12} sm={6} md={4}>
          <ConsensusCard consensus={consensus_details} />
        </Grid>
        <Grid item xs={12} sm={12} md={4}>
          <Paper
            sx={{
              p: 2,
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
            }}
          >
            <Typography variant="subtitle2" gutterBottom>
              {t('evaluation.averageRating', { defaultValue: 'Average Rating' })}
            </Typography>
            {feedback_summary.average_rating !== null ? (
              <>
                <Box display="flex" alignItems="center" gap={1} mb={1}>
                  <Typography variant="h4" color="warning.main">
                    {feedback_summary.average_rating.toFixed(1)}
                  </Typography>
                  <Icon name="star" color="warning" />
                </Box>
                <Typography variant="caption" color="secondary">
                  {t('evaluation.basedOn', {
                    defaultValue: 'Based on {{count}} reviews',
                    count: feedback_summary.total_feedback_count,
                  })}
                </Typography>
              </>
            ) : (
              <Typography variant="body2" color="secondary">
                {t('evaluation.noRatings', { defaultValue: 'No ratings available' })}
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Recommendations Breakdown */}
      <RecommendationsCard feedbackSummary={feedback_summary} />

      {/* Recruiter Feedback List */}
      {feedback_summary.feedback_list.length > 0 && (
        <FeedbackSection
          title={t('evaluation.recruiterFeedback', { defaultValue: 'Recruiter Feedback' })}
          icon={<Icon name="message-square" color="info" />}
          itemCount={feedback_summary.feedback_list.length}
          defaultExpanded={feedback_summary.feedback_list.length <= 3}
        >
          <Stack spacing={1}>
            {feedback_summary.feedback_list.map((feedback, index) => (
              <FeedbackItem key={`${feedback.recruiter_name}-${index}`} feedback={feedback} />
            ))}
          </Stack>
        </FeedbackSection>
      )}

      {/* Tags Section */}
      {tags.length > 0 && <TagsSection tags={tags} />}

      {/* Reviewer Avatars Summary */}
      <Card variant="outlined">
        <CardContent sx={{ py: 1 }}>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box display="flex" alignItems="center" gap={1}>
              <AvatarGroup max={5} sx={{ '& .MuiAvatar-root': { width: 24, height: 24, fontSize: '0.75rem' } }}>
                {feedback_summary.feedback_list.map((feedback, index) => (
                  <Avatar key={index} alt={feedback.recruiter_name}>
                    {feedback.recruiter_name.charAt(0).toUpperCase()}
                  </Avatar>
                ))}
              </AvatarGroup>
              <Typography variant="caption" color="secondary">
                {t('evaluation.reviewedBy', {
                  defaultValue: '{{count}} reviewers',
                  count: consensus_details.total_reviewers,
                })}
              </Typography>
            </Box>
            {consensus_details.unanimous && (
              <Chip
                icon={<Icon name="check" size="small" />}
                label={t('evaluation.unanimous', { defaultValue: 'Unanimous' })}
                color="success"
                size="small"
                variant="outlined"
              />
            )}
          </Box>
        </CardContent>
      </Card>

      {/* Help Text */}
      <Alert severity="info" variant="outlined">
        <AlertTitle>{t('evaluation.aboutScoring', { defaultValue: 'About This Evaluation' })}</AlertTitle>
        <Typography variant="body2">
          {t('evaluation.scoringDesc', {
            defaultValue: 'This evaluation aggregates feedback from the recruitment team. The consensus reflects the majority opinion, while individual ratings and notes provide additional context for your decision.',
          })}
        </Typography>
      </Alert>
    </Stack>
  );
}

/**
 * Compact Evaluation Badge Component
 */
interface EvaluationBadgeProps {
  evaluation: EvaluationSummaryResponse;
  showDetails?: boolean;
}

export function EvaluationBadge({ evaluation, showDetails = false }: EvaluationBadgeProps) {
  const { t } = useTranslation();
  const consensusColor = getConsensusColor(evaluation.consensus_details.consensus);

  const getConsensusShortLabel = (consensus: string | null): string => {
    if (!consensus) return '--';
    const labels: Record<string, string> = {
      strong_approve: '++',
      approve: '+',
      maybe: '?',
      mixed: '~',
      reject: '-',
      strong_reject: '--',
    };
    return labels[consensus] || consensus.charAt(0).toUpperCase();
  };

  const matchScoreDisplay = evaluation.match_score !== null
    ? `${Math.round(evaluation.match_score * 100)}%`
    : '--';

  const tooltipContent = showDetails
    ? `${t('evaluation.matchScore', { defaultValue: 'Match' })}: ${matchScoreDisplay}, ` +
      `${t('evaluation.teamConsensus', { defaultValue: 'Consensus' })}: ${evaluation.consensus_details.consensus || 'None'}, ` +
      `${t('evaluation.averageRating', { defaultValue: 'Avg Rating' })}: ${evaluation.feedback_summary.average_rating?.toFixed(1) || 'N/A'}`
    : t('evaluation.evaluationSummary', { defaultValue: 'Evaluation Summary' });

  return (
    <Tooltip title={tooltipContent}>
      <Box display="flex" alignItems="center" gap={1}>
        <Chip
          icon={<Icon name="target" />}
          label={matchScoreDisplay}
          color={evaluation.match_score !== null ? getScoreColor(evaluation.match_score) : 'default'}
          size={showDetails ? 'medium' : 'small'}
          variant="outlined"
        />
        <Chip
          icon={<Icon name="users" />}
          label={getConsensusShortLabel(evaluation.consensus_details.consensus)}
          color={consensusColor}
          size={showDetails ? 'medium' : 'small'}
        />
      </Box>
    </Tooltip>
  );
}

export default EvaluationSummary;
