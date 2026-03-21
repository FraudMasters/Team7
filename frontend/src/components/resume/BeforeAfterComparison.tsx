import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Stack,
  Grid,
  Chip,
  LinearProgress,
  Divider,
  Paper,
  Alert,
  Tooltip,
} from '@/components/ui';
import { Icon } from '@/components/ui/primitives';

/**
 * Candidate ranking data for before/after comparison
 */
interface CandidateRanking {
  resume_id: string;
  candidate_name: string;
  current_rank: number;
  current_score: number;
  predicted_rank: number;
  predicted_score: number;
  score_improvement: number;
  rank_improvement: number;
}

/**
 * BeforeAfterComparison Component Props
 */
interface BeforeAfterComparisonProps {
  /** Current candidate being analyzed */
  candidate: CandidateRanking;
  /** Total number of candidates in the pool */
  totalCandidates: number;
  /** Loading state */
  loading?: boolean;
  /** Error message */
  error?: string | null;
  /** Show detailed breakdown */
  showDetails?: boolean;
  /** Callback when user wants to view details */
  onViewDetails?: () => void;
}

/**
 * Helper to get score color
 */
const getScoreColor = (score: number): 'success' | 'warning' | 'error' => {
  if (score >= 70) return 'success';
  if (score >= 40) return 'warning';
  return 'error';
};

/**
 * Helper to get rank change color
 */
const getRankChangeColor = (improvement: number): 'success' | 'info' | 'default' => {
  if (improvement > 0) return 'success';
  if (improvement < 0) return 'error';
  return 'default';
};

/**
 * Helper to format rank display
 */
const formatRank = (rank: number, total: number): string => {
  return `#${rank} of ${total}`;
};

/**
 * Helper to get percentile
 */
const getPercentile = (rank: number, total: number): number => {
  return Math.round(((total - rank + 1) / total) * 100);
};

/**
 * BeforeAfterComparison Component
 *
 * Displays a visual before/after comparison showing how optimization suggestions
 * would impact a candidate's ranking:
 * - Current ranking and score
 * - Predicted ranking and score after optimization
 * - Visual indicators of improvement
 * - Score and rank change metrics
 *
 * @example
 * ```tsx
 * <BeforeAfterComparison
 *   candidate={{
 *     resume_id: 'resume-123',
 *     candidate_name: 'John Doe',
 *     current_rank: 15,
 *     current_score: 65,
 *     predicted_rank: 8,
 *     predicted_score: 82,
 *     score_improvement: 17,
 *     rank_improvement: 7
 *   }}
 *   totalCandidates={50}
 * />
 * ```
 */
const BeforeAfterComparison: React.FC<BeforeAfterComparisonProps> = ({
  candidate,
  totalCandidates,
  loading = false,
  error = null,
  showDetails = true,
  onViewDetails,
}) => {
  /**
   * Render loading state
   */
  if (loading) {
    return (
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', py: 4 }}>
            <Stack spacing={2} alignItems="center">
              <Box sx={{ width: 60, height: 60 }}>
                <Icon name="refresh" />
              </Box>
              <Typography variant="body2" color="text.secondary">
                Calculating ranking impact...
              </Typography>
            </Stack>
          </Box>
        </CardContent>
      </Card>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <Card>
        <CardContent>
          <Alert severity="error">
            <Typography variant="body2">{error}</Typography>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  const currentPercentile = getPercentile(candidate.current_rank, totalCandidates);
  const predictedPercentile = getPercentile(candidate.predicted_rank, totalCandidates);
  const percentileImprovement = predictedPercentile - currentPercentile;

  return (
    <Card elevation={2}>
      <CardContent>
        <Stack spacing={3}>
          {/* Header */}
          <Box>
            <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 1 }}>
              <Box
                sx={{
                  p: 1,
                  borderRadius: 1,
                  bgcolor: 'primary.main',
                  color: 'primary.contrastText',
                }}
              >
                <Icon name="bar-chart" />
              </Box>
              <Box sx={{ flex: 1 }}>
                <Typography variant="h6" fontWeight={600}>
                  Ranking Impact Prediction
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  How optimization will improve your ranking
                </Typography>
              </Box>
              {candidate.rank_improvement > 0 && (
                <Chip
                  icon={<Icon name="trending-up" />}
                  label={`+${candidate.rank_improvement} positions`}
                  color="success"
                  size="small"
                />
              )}
            </Stack>
          </Box>

          <Divider />

          {/* Before/After Comparison Grid */}
          <Grid container spacing={3}>
            {/* BEFORE - Current State */}
            <Grid item xs={12} md={6}>
              <Paper
                elevation={0}
                sx={{
                  p: 2,
                  border: '2px solid',
                  borderColor: 'divider',
                  bgcolor: 'background.default',
                }}
              >
                <Stack spacing={2}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Typography variant="subtitle2" color="text.secondary" fontWeight={600}>
                      CURRENT
                    </Typography>
                    <Chip
                      label="Before"
                      size="small"
                      variant="outlined"
                      sx={{ fontWeight: 600 }}
                    />
                  </Box>

                  {/* Current Rank */}
                  <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Ranking
                    </Typography>
                    <Stack direction="row" spacing={1} alignItems="baseline">
                      <Typography variant="h3" fontWeight={700}>
                        #{candidate.current_rank}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        of {totalCandidates}
                      </Typography>
                    </Stack>
                    <Typography variant="caption" color="text.secondary">
                      Top {currentPercentile}th percentile
                    </Typography>
                  </Box>

                  {/* Current Score */}
                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Match Score
                      </Typography>
                      <Typography variant="body2" fontWeight={600}>
                        {candidate.current_score}%
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={candidate.current_score}
                      color={getScoreColor(candidate.current_score)}
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                  </Box>
                </Stack>
              </Paper>
            </Grid>

            {/* AFTER - Predicted State */}
            <Grid item xs={12} md={6}>
              <Paper
                elevation={0}
                sx={{
                  p: 2,
                  border: '2px solid',
                  borderColor: 'success.main',
                  bgcolor: 'success.lighter',
                }}
              >
                <Stack spacing={2}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Typography variant="subtitle2" color="success.dark" fontWeight={600}>
                      PREDICTED
                    </Typography>
                    <Chip
                      label="After Optimization"
                      size="small"
                      color="success"
                      sx={{ fontWeight: 600 }}
                    />
                  </Box>

                  {/* Predicted Rank */}
                  <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Ranking
                    </Typography>
                    <Stack direction="row" spacing={1} alignItems="baseline">
                      <Typography variant="h3" fontWeight={700} color="success.dark">
                        #{candidate.predicted_rank}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        of {totalCandidates}
                      </Typography>
                      {candidate.rank_improvement > 0 && (
                        <Chip
                          icon={<Icon name="arrow-up" />}
                          label={`+${candidate.rank_improvement}`}
                          color="success"
                          size="small"
                          sx={{ ml: 1 }}
                        />
                      )}
                    </Stack>
                    <Typography variant="caption" color="success.dark">
                      Top {predictedPercentile}th percentile
                      {percentileImprovement > 0 && ` (+${percentileImprovement}%)`}
                    </Typography>
                  </Box>

                  {/* Predicted Score */}
                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Match Score
                      </Typography>
                      <Stack direction="row" spacing={1} alignItems="center">
                        <Typography variant="body2" fontWeight={600}>
                          {candidate.predicted_score}%
                        </Typography>
                        <Chip
                          label={`+${candidate.score_improvement}%`}
                          color="success"
                          size="small"
                        />
                      </Stack>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={candidate.predicted_score}
                      color={getScoreColor(candidate.predicted_score)}
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                  </Box>
                </Stack>
              </Paper>
            </Grid>
          </Grid>

          {/* Impact Summary */}
          {showDetails && (
            <Paper elevation={1} sx={{ p: 2, bgcolor: 'action.hover' }}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={4}>
                  <Stack spacing={0.5}>
                    <Typography variant="caption" color="text.secondary">
                      Score Improvement
                    </Typography>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Icon name="trending-up" />
                      <Typography variant="h6" fontWeight={600} color="success.main">
                        +{candidate.score_improvement}%
                      </Typography>
                    </Stack>
                  </Stack>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Stack spacing={0.5}>
                    <Typography variant="caption" color="text.secondary">
                      Rank Improvement
                    </Typography>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Icon name="arrow-up" />
                      <Typography variant="h6" fontWeight={600} color="success.main">
                        +{candidate.rank_improvement} positions
                      </Typography>
                    </Stack>
                  </Stack>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Stack spacing={0.5}>
                    <Typography variant="caption" color="text.secondary">
                      Percentile Change
                    </Typography>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Icon name="percent" />
                      <Typography variant="h6" fontWeight={600} color="success.main">
                        +{percentileImprovement}%
                      </Typography>
                    </Stack>
                  </Stack>
                </Grid>
              </Grid>
            </Paper>
          )}

          {/* Impact Message */}
          <Alert severity="success" icon={<Icon name="lightbulb" />}>
            <Typography variant="body2">
              By implementing the suggested optimizations, you could improve from{' '}
              <strong>#{candidate.current_rank}</strong> to{' '}
              <strong>#{candidate.predicted_rank}</strong>, potentially increasing your
              visibility to recruiters and hiring managers.
            </Typography>
          </Alert>

          {/* View Details Action */}
          {onViewDetails && (
            <Box sx={{ textAlign: 'center', pt: 1 }}>
              <Tooltip title="View detailed optimization suggestions">
                <Box
                  component="button"
                  onClick={onViewDetails}
                  sx={{
                    border: 'none',
                    background: 'none',
                    cursor: 'pointer',
                    color: 'primary.main',
                    textDecoration: 'none',
                    '&:hover': {
                      textDecoration: 'underline',
                    },
                  }}
                >
                  <Stack direction="row" spacing={0.5} alignItems="center">
                    <Typography variant="body2" fontWeight={600}>
                      View Detailed Suggestions
                    </Typography>
                    <Icon name="arrow-right" />
                  </Stack>
                </Box>
              </Tooltip>
            </Box>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
};

export default BeforeAfterComparison;
